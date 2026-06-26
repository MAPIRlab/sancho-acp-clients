"""Main application class orchestrating routes, connection, and SDK client callbacks."""

from __future__ import annotations

import asyncio
import logging
import os
import flet as ft

from acp import PROTOCOL_VERSION, connect_to_agent, text_block
from acp.client.connection import ClientSideConnection
from acp.schema import (
    ClientCapabilities,
    Implementation,
    PermissionOption,
    RequestPermissionResponse,
    ToolCallUpdate,
)

from .theme import get_theme, WINDOW_WIDTH, WINDOW_HEIGHT
from .client import SanchoMobileClient
from .transport import close_tcp, connect_tcp
from .views.connect_view import build_connect_view
from .views.chat_view import build_chat_view
from .views.components.permission_dialog import show_permission_dialog

log = logging.getLogger(__name__)


class SanchoApp:
    """Orchestrator for routing, state, and connecting Flet UI with the ACP SDK."""

    def __init__(self) -> None:
        self.page: ft.Page | None = None

        # Connection and Session State
        self.conn: ClientSideConnection | None = None
        self.session_id: str | None = None
        self.tcp_writer: asyncio.StreamWriter | None = None
        self.acp_client: SanchoMobileClient | None = None
        self.host: str | None = None
        self.port: int | None = None

        # Agent Information
        self.agent_name: str | None = None
        self.agent_version: str | None = None

        # Settings
        self.font_scale: float = 1.0

        # View updates callback hooks
        self.on_session_update_view_callback = None

    async def start(self, page: ft.Page) -> None:
        """Entry point called by ft.app to initialize the client window."""
        self.page = page
        page.title = "Sancho ACP Client"
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = get_theme()

        # Window dimensions simulating a smartphone
        page.window_width = WINDOW_WIDTH
        page.window_height = WINDOW_HEIGHT
        page.window_resizable = False
        page.window_maximizable = False

        self._setup_routing(page)
        page.go("/connect")

    def _setup_routing(self, page: ft.Page) -> None:
        """Configures routing rules between screen views."""
        def route_change(e):
            page.views.clear()
            if page.route == "/connect":
                page.views.append(build_connect_view(self, page))
            elif page.route == "/chat":
                page.views.append(build_chat_view(self, page))
            page.update()

        page.on_route_change = route_change

    # ── Connection methods called by views ──────────────────────────────

    async def connect(self, host: str, port: int) -> bool:
        """Establishes TCP connection and runs the ACP handshake.
        
        Returns:
            bool: True if connection, handshake, and session initialization succeed.
        """
        if self.conn is not None:
            await self.disconnect()

        # Connect TCP Stream
        reader, writer = await connect_tcp(
            host, port, retries=15, retry_delay=0.4, verbose=True
        )
        self.tcp_writer = writer

        # Create Client
        self.acp_client = SanchoMobileClient(
            on_update=self._handle_session_update_event,
            on_permission=self._handle_permission_request_event,
        )

        # Connect to SDK
        conn = connect_to_agent(self.acp_client, writer, reader)
        self.conn = conn

        # Protocol Handshake
        try:
            init_resp = await conn.initialize(
                protocol_version=PROTOCOL_VERSION,
                client_capabilities=ClientCapabilities(),
                client_info=Implementation(
                    name="sancho-mobile",
                    title="Sancho ACP Mobile",
                    version="0.1.0",
                ),
            )
        except Exception as exc:
            log.error(f"ACP initialization failed: {exc}")
            await self.disconnect()
            raise exc

        # Extract agent details
        if init_resp.agent_info:
            self.agent_name = (
                getattr(init_resp.agent_info, "title", None)
                or getattr(init_resp.agent_info, "name", None)
            )
            self.agent_version = getattr(init_resp.agent_info, "version", None)

        # Open Session
        try:
            session_resp = await conn.new_session(mcp_servers=[], cwd=os.getcwd())
            self.session_id = session_resp.session_id
        except Exception as exc:
            log.error(f"Failed to create ACP session: {exc}")
            await self.disconnect()
            raise exc

        self.host = host
        self.port = port
        return True

    async def disconnect(self) -> None:
        """Tears down session and TCP streams, clearing connection state."""
        if self.conn is not None:
            if self.session_id is not None:
                try:
                    await self.conn.close_session(self.session_id)
                except Exception:
                    pass
            try:
                await self.conn.close()
            except Exception:
                pass

        if self.tcp_writer is not None:
            await close_tcp(self.tcp_writer)

        # Clear references
        self.conn = None
        self.session_id = None
        self.tcp_writer = None
        self.acp_client = None
        self.agent_name = None
        self.agent_version = None

    async def send_prompt(self, text: str) -> None:
        """Submits user text to the agent, waiting for execution completion."""
        if self.conn is None or self.session_id is None:
            raise RuntimeError("Not connected to an active session.")

        await self.conn.prompt(
            session_id=self.session_id,
            prompt=[text_block(text)],
        )

    async def cancel_task(self) -> None:
        """Instructs the agent to cancel the active execution."""
        if self.conn is None or self.session_id is None:
            return
        await self.conn.cancel(self.session_id)

    # ── Internal SDK callbacks routing to active views ─────────────────

    async def _handle_session_update_event(self, update) -> None:
        """Helper routing notifications directly to the chat view handler."""
        if self.on_session_update_view_callback:
            await self.on_session_update_view_callback(update)

    async def _handle_permission_request_event(
        self,
        options: list[PermissionOption],
        session_id: str,
        tool_call: ToolCallUpdate,
    ) -> RequestPermissionResponse:
        """Helper showing the modal dialog and returning the selected option outcome."""
        if self.page is None:
            from acp.schema import DeniedOutcome
            return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
            
        return await show_permission_dialog(self.page, options, tool_call)
