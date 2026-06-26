"""Main application loop for the Sancho ACP CLI."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from rich.console import Console

from acp import text_block
from acp.client.connection import ClientSideConnection
from acp.schema import (
    AllowedOutcome,
    DeniedOutcome,
    PermissionOption,
    RequestPermissionResponse,
    ToolCallUpdate,
)

from . import display
from .banner import display_banner, show_help_hint
from .client import SanchoClient
from .commands import dispatch_command

log = logging.getLogger(__name__)


class SanchoCLI:
    """Top-level orchestrator for the Sancho ACP CLI application."""

    def __init__(self) -> None:
        self.console = Console()

        # Connection state.
        self.conn: ClientSideConnection | None = None
        self.session_id: str | None = None
        self.tcp_writer: asyncio.StreamWriter | None = None
        self.acp_client: SanchoClient | None = None
        self.host: str | None = None
        self.port: int | None = None

        # Control flag for the main loop.
        self.running: bool = True

    # ── Public entry point ──────────────────────────────────────────────

    async def run(
        self,
        auto_host: str | None = None,
        auto_port: int | None = None,
    ) -> None:
        """Launch the interactive CLI loop.

        If *auto_host* and *auto_port* are provided the CLI will attempt
        to connect immediately on startup.
        """
        display_banner(self.console)
        show_help_hint(self.console)

        # Optional auto-connect.
        if auto_host and auto_port:
            from .commands import cmd_connect
            await cmd_connect(self, [auto_host, str(auto_port)])

        # Start the permission handler as a background task.
        permission_task = asyncio.create_task(self._permission_handler())

        try:
            await self._input_loop()
        finally:
            permission_task.cancel()
            try:
                await permission_task
            except asyncio.CancelledError:
                pass

    # ── Input loop ──────────────────────────────────────────────────────

    async def _input_loop(self) -> None:
        """Read lines from the terminal and dispatch them."""
        loop = asyncio.get_running_loop()
        lines: list[str] = []

        while self.running:
            prompt = "> " if not lines else "... "
            try:
                line = await loop.run_in_executor(None, self._blocking_input, prompt)
            except (EOFError, KeyboardInterrupt):
                self.console.print()
                if lines:
                    lines.clear()
                    display.print_warning(self.console, "Multiline input cancelled.")
                    continue
                from .commands import cmd_quit
                await cmd_quit(self, [])
                break

            if line is None:
                continue

            stripped_line = line.rstrip()
            if stripped_line.endswith("\\"):
                idx = line.rfind("\\")
                lines.append(line[:idx])
                continue
            else:
                lines.append(line)
                full_input = "\n".join(lines)
                lines.clear()

            stripped = full_input.strip()
            if not stripped:
                continue

            if stripped.startswith("/"):
                await dispatch_command(stripped, self)
            elif self.conn is not None and self.session_id is not None:
                await self._send_prompt(stripped)
            else:
                display.print_warning(
                    self.console,
                    "Not connected. Use /connect <host> <port> first.",
                )

    def _blocking_input(self, prompt: str) -> str | None:
        """Blocking ``input()`` call, executed in a thread via the executor."""
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            raise

    # ── Prompt sending ──────────────────────────────────────────────────

    async def _send_prompt(self, text: str) -> None:
        """Send a user prompt to the connected agent."""
        assert self.conn is not None
        assert self.session_id is not None

        try:
            resp = await self.conn.prompt(
                session_id=self.session_id,
                prompt=[text_block(text)],
            )
            stop_reason = getattr(resp, "stop_reason", None)
            if stop_reason:
                display.print_info(self.console, f"Agent finished ({stop_reason})")
                self.console.print()
        except Exception as exc:
            display.print_error(self.console, f"Prompt failed: {exc}")

    # ── Permission handler ──────────────────────────────────────────────

    async def _permission_handler(self) -> None:
        """Background task that drains the permission queue and prompts the user.

        The ``SanchoClient.request_permission`` callback pushes items
        into the queue; this task consumes them, renders the UI, reads
        the user selection, and resolves the awaiting future.
        """
        while True:
            options, session_id, tool_call, future = await self._get_permission_request()

            # Build display-friendly option list.
            indexed_options: list[tuple[int, str, str]] = []
            for idx, opt in enumerate(options, start=1):
                indexed_options.append((idx, opt.name, opt.kind))

            # Describe what the agent wants to do.
            description = ""
            if hasattr(tool_call, "name"):
                description += f"Tool: {tool_call.name}"
            if hasattr(tool_call, "input") and tool_call.input:
                description += f"\nInput: {tool_call.input}"

            display.print_permission_prompt(self.console, description or "(no description)", indexed_options)

            # Read user choice (blocking in executor).
            loop = asyncio.get_running_loop()
            choice = await self._read_permission_choice(loop, len(options))

            if choice is None or choice < 1 or choice > len(options):
                # Treat invalid / timeout as denial.
                future.set_result(
                    RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
                )
            else:
                selected = options[choice - 1]
                kind = selected.kind
                if "allow" in kind:
                    future.set_result(
                        RequestPermissionResponse(
                            outcome=AllowedOutcome(
                                outcome="selected",
                                option_id=selected.option_id,
                            )
                        )
                    )
                else:
                    future.set_result(
                        RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
                    )

    async def _get_permission_request(
        self,
    ) -> tuple[
        list[PermissionOption],
        str,
        ToolCallUpdate,
        asyncio.Future[RequestPermissionResponse],
    ]:
        """Wait for the next permission request from the client queue."""
        if self.acp_client is None:
            # No client yet; just sleep and retry.
            await asyncio.sleep(0.5)
            return await self._get_permission_request()  # type: ignore[return-value]
        return await self.acp_client.permission_queue.get()

    async def _read_permission_choice(self, loop: asyncio.AbstractEventLoop, num_options: int) -> int | None:
        """Read the user's numeric choice for a permission prompt."""
        try:
            raw = await loop.run_in_executor(
                None,
                lambda: input(f"  Select option [1-{num_options}]: "),
            )
            return int(raw.strip())
        except (ValueError, EOFError, KeyboardInterrupt):
            return None
