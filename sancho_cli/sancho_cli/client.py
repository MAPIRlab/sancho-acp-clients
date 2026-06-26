"""ACP Client implementation for the Sancho CLI.

This module subclasses the ``acp.Client`` protocol, implementing all the
callbacks that the remote ACP agent/server can invoke on us.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from rich.console import Console

from acp import RequestError
from acp.schema import (
    AgentMessageChunk,
    AgentPlanUpdate,
    AgentThoughtChunk,
    AllowedOutcome,
    AudioContentBlock,
    AvailableCommandsUpdate,
    ConfigOptionUpdate,
    CreateTerminalResponse,
    CurrentModeUpdate,
    DeniedOutcome,
    EmbeddedResourceContentBlock,
    EnvVariable,
    ImageContentBlock,
    KillTerminalResponse,
    PermissionOption,
    ReadTextFileResponse,
    ReleaseTerminalResponse,
    RequestPermissionResponse,
    ResourceContentBlock,
    SessionInfoUpdate,
    TerminalOutputResponse,
    TextContentBlock,
    ToolCallProgress,
    ToolCallStart,
    ToolCallUpdate,
    UsageUpdate,
    UserMessageChunk,
    WaitForTerminalExitResponse,
    WriteTextFileResponse,
)

from . import display

log = logging.getLogger(__name__)


class SanchoClient:
    """Concrete ``acp.Client`` used by the Sancho CLI.

    The ACP SDK dispatches server-initiated requests/notifications to the
    methods defined here. We render everything on the terminal through the
    shared ``display`` module and handle permission requests interactively.
    """

    def __init__(self, console: Console) -> None:
        self.console = console
        # Queue for coordinating permission requests with the input loop.
        self._permission_queue: asyncio.Queue[
            tuple[
                list[PermissionOption],
                str,
                ToolCallUpdate,
                asyncio.Future[RequestPermissionResponse],
            ]
        ] = asyncio.Queue()
        # Keep track of active tool calls by ID to map progress updates to their tool name.
        self._tool_calls: dict[str, str] = {}

    @property
    def permission_queue(
        self,
    ) -> asyncio.Queue[
        tuple[
            list[PermissionOption],
            str,
            ToolCallUpdate,
            asyncio.Future[RequestPermissionResponse],
        ]
    ]:
        """Expose the queue so the app loop can drain it."""
        return self._permission_queue

    # ── session/update (notification) ───────────────────────────────────

    async def session_update(
        self,
        session_id: str,
        update: (
            UserMessageChunk
            | AgentMessageChunk
            | AgentThoughtChunk
            | ToolCallStart
            | ToolCallProgress
            | AgentPlanUpdate
            | AvailableCommandsUpdate
            | CurrentModeUpdate
            | ConfigOptionUpdate
            | SessionInfoUpdate
            | UsageUpdate
        ),
        **kwargs: Any,
    ) -> None:
        if isinstance(update, AgentMessageChunk):
            self._handle_agent_message(update)
        elif isinstance(update, AgentThoughtChunk):
            self._handle_agent_thought(update)
        elif isinstance(update, ToolCallStart):
            tool_name = getattr(update, "title", None) or "unknown"
            tool_call_id = getattr(update, "tool_call_id", None)
            if tool_call_id:
                self._tool_calls[tool_call_id] = tool_name
            display.print_tool_start(self.console, str(tool_name))
        elif isinstance(update, ToolCallProgress):
            tool_call_id = getattr(update, "tool_call_id", None)
            tool_name = self._tool_calls.get(tool_call_id, "unknown") if tool_call_id else "unknown"
            
            parts = []
            status = getattr(update, "status", None)
            if status:
                parts.append(status)
            
            title = getattr(update, "title", None)
            if title and title != tool_name:
                parts.append(title)
                
            content_list = getattr(update, "content", None)
            if content_list:
                for item in content_list:
                    if getattr(item, "type", None) == "content":
                        inner = getattr(item, "content", None)
                        if isinstance(inner, TextContentBlock) and inner.text:
                            parts.append(inner.text)
                            
            raw_output = getattr(update, "raw_output", None)
            if raw_output is not None:
                parts.append(str(raw_output))
                
            message = " - ".join(parts)
            display.print_tool_progress(self.console, tool_name, message)
        elif isinstance(update, AgentPlanUpdate):
            entries = getattr(update, "entries", None) or []
            display.print_plan(self.console, entries)
        elif isinstance(update, UsageUpdate):
            display.print_usage(self.console, update)
        elif isinstance(update, SessionInfoUpdate):
            info_text = getattr(update, "info", None) or str(update)
            display.print_info(self.console, f"Session info: {info_text}")
        else:
            # AvailableCommandsUpdate, CurrentModeUpdate, ConfigOptionUpdate, etc.
            display.print_info(self.console, f"Update: {type(update).__name__}")

    def _handle_agent_message(self, update: AgentMessageChunk) -> None:
        content = update.content
        if isinstance(content, TextContentBlock):
            display.print_agent_text(self.console, content.text)
        elif isinstance(content, ImageContentBlock):
            display.print_agent_image(self.console)
        elif isinstance(content, AudioContentBlock):
            display.print_agent_audio(self.console)
        elif isinstance(content, ResourceContentBlock):
            uri = getattr(content, "uri", None)
            display.print_agent_resource(self.console, uri)
        elif isinstance(content, EmbeddedResourceContentBlock):
            display.print_agent_resource(self.console, None)
        else:
            display.print_info(self.console, f"Content: {type(content).__name__}")

    def _handle_agent_thought(self, update: AgentThoughtChunk) -> None:
        content = update.content
        if isinstance(content, TextContentBlock):
            display.print_agent_thought(self.console, content.text)
        else:
            display.print_agent_thought(self.console, str(content))

    # ── session/request_permission (request) ────────────────────────────

    async def request_permission(
        self,
        options: list[PermissionOption],
        session_id: str,
        tool_call: ToolCallUpdate,
        **kwargs: Any,
    ) -> RequestPermissionResponse:
        """Called by the agent when it needs human authorization.

        We push the request into a queue and await the future that the
        input loop will resolve once the user makes a selection.
        """
        loop = asyncio.get_running_loop()
        future: asyncio.Future[RequestPermissionResponse] = loop.create_future()
        await self._permission_queue.put((options, session_id, tool_call, future))
        return await future

    # ── File-system operations (basic / restricted) ─────────────────────

    async def write_text_file(
        self, content: str, path: str, session_id: str, **kwargs: Any
    ) -> WriteTextFileResponse | None:
        display.print_warning(self.console, f"Agent requested write to: {path} (rejected)")
        raise RequestError.method_not_found("fs/write_text_file")

    async def read_text_file(
        self, path: str, session_id: str, limit: int | None = None, line: int | None = None, **kwargs: Any
    ) -> ReadTextFileResponse:
        display.print_warning(self.console, f"Agent requested read of: {path} (rejected)")
        raise RequestError.method_not_found("fs/read_text_file")

    # ── Terminal operations (not applicable for robotics) ───────────────

    async def create_terminal(
        self,
        command: str,
        session_id: str,
        args: list[str] | None = None,
        cwd: str | None = None,
        env: list[EnvVariable] | None = None,
        output_byte_limit: int | None = None,
        **kwargs: Any,
    ) -> CreateTerminalResponse:
        raise RequestError.method_not_found("terminal/create")

    async def terminal_output(self, session_id: str, terminal_id: str, **kwargs: Any) -> TerminalOutputResponse:
        raise RequestError.method_not_found("terminal/output")

    async def release_terminal(
        self, session_id: str, terminal_id: str, **kwargs: Any
    ) -> ReleaseTerminalResponse | None:
        raise RequestError.method_not_found("terminal/release")

    async def wait_for_terminal_exit(
        self, session_id: str, terminal_id: str, **kwargs: Any
    ) -> WaitForTerminalExitResponse:
        raise RequestError.method_not_found("terminal/wait_for_exit")

    async def kill_terminal(self, session_id: str, terminal_id: str, **kwargs: Any) -> KillTerminalResponse | None:
        raise RequestError.method_not_found("terminal/kill")

    # ── Extension methods ───────────────────────────────────────────────

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        raise RequestError.method_not_found(method)

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        display.print_info(self.console, f"Extension notification: {method}")

    # ── on_connect lifecycle hook ───────────────────────────────────────

    def on_connect(self, conn: Any) -> None:
        log.debug("Client on_connect callback fired")
