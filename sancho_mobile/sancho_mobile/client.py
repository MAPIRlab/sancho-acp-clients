"""ACP Client implementation for the Sancho Mobile client.

This module subclasses the ``acp.Client`` protocol, implementing all the
callbacks that the remote ACP agent/server can invoke on us.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine

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

log = logging.getLogger(__name__)


class SanchoMobileClient:
    """Concrete ``acp.Client`` used by the Sancho Mobile app.

    The ACP SDK dispatches server-initiated requests/notifications to the
    methods defined here. We pass them along to callbacks linked to the Flet UI.
    """

    def __init__(
        self,
        on_update: Callable[[Any], Coroutine[Any, Any, None]],
        on_permission: Callable[[list[PermissionOption], str, ToolCallUpdate], Coroutine[Any, Any, RequestPermissionResponse]],
    ) -> None:
        self.on_update = on_update
        self.on_permission = on_permission
        # Keep track of active tool calls by ID to map progress updates to their tool name.
        self._tool_calls: dict[str, str] = {}

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
        if isinstance(update, ToolCallStart):
            tool_name = getattr(update, "title", None) or "unknown"
            tool_call_id = getattr(update, "tool_call_id", None)
            if tool_call_id:
                self._tool_calls[tool_call_id] = tool_name
        
        await self.on_update(update)

    async def request_permission(
        self,
        options: list[PermissionOption],
        session_id: str,
        tool_call: ToolCallUpdate,
        **kwargs: Any,
    ) -> RequestPermissionResponse:
        """Called by the agent when it needs human authorization.

        We trigger the Flet dialog callback and await the user decision.
        """
        return await self.on_permission(options, session_id, tool_call)

    # ── File-system operations (basic / restricted) ─────────────────────

    async def write_text_file(
        self, content: str, path: str, session_id: str, **kwargs: Any
    ) -> WriteTextFileResponse | None:
        log.warning("Agent requested write to: %s (rejected)", path)
        raise RequestError.method_not_found("fs/write_text_file")

    async def read_text_file(
        self, path: str, session_id: str, limit: int | None = None, line: int | None = None, **kwargs: Any
    ) -> ReadTextFileResponse:
        log.warning("Agent requested read of: %s (rejected)", path)
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
        log.info("Extension notification: %s", method)

    # ── on_connect lifecycle hook ───────────────────────────────────────

    def on_connect(self, conn: Any) -> None:
        log.debug("Client on_connect callback fired")
