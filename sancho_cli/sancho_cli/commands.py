"""Slash-command registry and dispatch for the Sancho CLI."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from rich.table import Table

from acp import PROTOCOL_VERSION, connect_to_agent, text_block
from acp.schema import ClientCapabilities, Implementation

from . import __version__, display
from .client import SanchoClient
from .transport import close_tcp, connect_tcp

if TYPE_CHECKING:
    from .app import SanchoCLI


async def cmd_connect(app: SanchoCLI, args: list[str]) -> None:
    """Connect to an ACP server over TCP.

    Usage: /connect <host> <port>
    """
    if len(args) < 2:
        display.print_error(app.console, "Usage: /connect <host> <port>")
        return

    host = args[0]
    try:
        port = int(args[1])
    except ValueError:
        display.print_error(app.console, f"Invalid port number: {args[1]}")
        return

    # Disconnect existing connection if any.
    if app.conn is not None:
        display.print_warning(app.console, "Disconnecting from current session…")
        await _do_disconnect(app)

    # Parse optional keyword arguments.
    retries = 40
    retry_delay = 0.5
    for i, arg in enumerate(args[2:], start=2):
        if arg == "--retries" and i + 1 < len(args):
            retries = int(args[i + 1])
        elif arg == "--retry-delay" and i + 1 < len(args):
            retry_delay = float(args[i + 1])

    app.console.print(f"  Connecting to [bold]{host}:{port}[/bold]…", highlight=False)

    try:
        reader, writer = await connect_tcp(host, port, retries=retries, retry_delay=retry_delay, verbose=True)
    except ConnectionError as exc:
        display.print_error(app.console, str(exc))
        return

    # Store the writer so we can close it later.
    app.tcp_writer = writer

    # Build the ACP connection through the SDK.
    client_impl = SanchoClient(app.console)
    app.acp_client = client_impl
    conn = connect_to_agent(client_impl, writer, reader)
    app.conn = conn

    # Initialize the ACP protocol handshake.
    try:
        init_resp = await conn.initialize(
            protocol_version=PROTOCOL_VERSION,
            client_capabilities=ClientCapabilities(),
            client_info=Implementation(
                name="sancho-cli",
                title="Sancho ACP CLI",
                version=__version__,
            ),
        )
    except Exception as exc:
        display.print_error(app.console, f"ACP initialization failed: {exc}")
        await _do_disconnect(app)
        return

    # Extract agent info from the response.
    agent_name = None
    agent_version = None
    if init_resp.agent_info:
        agent_name = getattr(init_resp.agent_info, "title", None) or getattr(init_resp.agent_info, "name", None)
        agent_version = getattr(init_resp.agent_info, "version", None)

    # Open a new session.
    try:
        session_resp = await conn.new_session(mcp_servers=[], cwd=os.getcwd())
        app.session_id = session_resp.session_id
    except Exception as exc:
        display.print_error(app.console, f"Failed to create session: {exc}")
        await _do_disconnect(app)
        return

    app.host = host
    app.port = port

    display.print_connection_info(
        app.console,
        host=host,
        port=port,
        agent_name=agent_name,
        agent_version=agent_version,
        session_id=app.session_id,
    )


async def cmd_disconnect(app: SanchoCLI, _args: list[str]) -> None:
    """Disconnect from the current ACP server.

    Usage: /disconnect
    """
    if app.conn is None:
        display.print_warning(app.console, "Not connected.")
        return

    await _do_disconnect(app)
    app.console.print("  [green]Disconnected.[/green]")


async def _do_disconnect(app: SanchoCLI) -> None:
    """Internal helper to tear down connection state."""
    if app.conn is not None:
        if app.session_id is not None:
            try:
                await app.conn.close_session(app.session_id)
            except Exception:
                pass  # Best-effort.
        try:
            await app.conn.close()
        except Exception:
            pass
    if app.tcp_writer is not None:
        await close_tcp(app.tcp_writer)

    app.conn = None
    app.session_id = None
    app.tcp_writer = None
    app.acp_client = None
    app.host = None
    app.port = None


async def cmd_cancel(app: SanchoCLI, _args: list[str]) -> None:
    """Cancel the current agent task.

    Usage: /cancel
    """
    if app.conn is None or app.session_id is None:
        display.print_warning(app.console, "Not connected.")
        return

    try:
        await app.conn.cancel(app.session_id)
        app.console.print("  [yellow]Cancel signal sent.[/yellow]")
    except Exception as exc:
        display.print_error(app.console, f"Cancel failed: {exc}")


async def cmd_status(app: SanchoCLI, _args: list[str]) -> None:
    """Show the current connection status.

    Usage: /status
    """
    display.print_status(
        app.console,
        connected=app.conn is not None,
        host=app.host,
        port=app.port,
        session_id=app.session_id,
    )


async def cmd_help(app: SanchoCLI, _args: list[str]) -> None:
    """Show available commands.

    Usage: /help
    """
    table = Table(title="Available Commands", show_lines=False, border_style="dim")
    table.add_column("Command", style="bold cyan", no_wrap=True)
    table.add_column("Description")

    for name, (handler, _) in sorted(COMMAND_REGISTRY.items()):
        docstring = handler.__doc__ or ""
        # Use the first non-empty line of the docstring as description.
        desc = next((line.strip() for line in docstring.splitlines() if line.strip()), "")
        table.add_row(f"/{name}", desc)

    table.add_row("[dim]<text>[/dim]", "Send a prompt to the agent")

    app.console.print()
    app.console.print(table)
    app.console.print()


async def cmd_quit(app: SanchoCLI, _args: list[str]) -> None:
    """Exit the CLI.

    Usage: /quit  or  /exit
    """
    if app.conn is not None:
        app.console.print("  Disconnecting…", highlight=False)
        await _do_disconnect(app)

    app.console.print("  [dim]Goodbye![/dim]")
    app.running = False


# ── Command registry ────────────────────────────────────────────────────

# Maps command name → (handler_coroutine, short_aliases).
# The second element is a list of alternative names.
COMMAND_REGISTRY: dict[str, tuple[..., list[str]]] = {
    "connect": (cmd_connect, []),
    "disconnect": (cmd_disconnect, []),
    "cancel": (cmd_cancel, []),
    "status": (cmd_status, []),
    "help": (cmd_help, ["h", "?"]),
    "quit": (cmd_quit, ["exit", "q"]),
}

# Build a flat lookup including aliases.
_DISPATCH: dict[str, ...] = {}
for _name, (_handler, _aliases) in COMMAND_REGISTRY.items():
    _DISPATCH[_name] = _handler
    for _alias in _aliases:
        _DISPATCH[_alias] = _handler


async def dispatch_command(line: str, app: SanchoCLI) -> None:
    """Parse and run a slash command from user input."""
    parts = line.lstrip("/").split()
    if not parts:
        return

    cmd_name = parts[0].lower()
    args = parts[1:]

    handler = _DISPATCH.get(cmd_name)
    if handler is None:
        display.print_error(app.console, f"Unknown command: /{cmd_name}. Type /help for a list.")
        return

    await handler(app, args)
