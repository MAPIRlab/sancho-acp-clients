"""Rich-based display helpers for the Sancho ACP CLI."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# ── Agent messages ──────────────────────────────────────────────────────

def print_agent_text(console: Console, text: str) -> None:
    """Render an agent message chunk as Markdown."""
    console.print(Markdown(text))


def print_agent_thought(console: Console, text: str) -> None:
    """Render an agent thought in dim italic."""
    console.print(Text(f"💭 {text}", style="dim italic"))


def print_agent_image(console: Console) -> None:
    """Placeholder for image content blocks."""
    console.print(Text("🖼️  [image received]", style="dim"))


def print_agent_audio(console: Console) -> None:
    """Placeholder for audio content blocks."""
    console.print(Text("🔊 [audio received]", style="dim"))


def print_agent_resource(console: Console, uri: str | None) -> None:
    """Render a resource content block."""
    label = uri or "<resource>"
    console.print(Text(f"📎 {label}", style="dim cyan"))


# ── Tool calls ──────────────────────────────────────────────────────────

def print_tool_start(console: Console, tool_name: str) -> None:
    """Print when a tool call begins."""
    console.print(Text(f"⚙️  Executing tool: {tool_name}…", style="bold yellow"))


def print_tool_progress(console: Console, tool_name: str, message: str) -> None:
    """Print incremental progress for a tool call."""
    console.print(Text(f"   ↳ [{tool_name}] {message}", style="dim yellow"))


# ── Plans ───────────────────────────────────────────────────────────────

def print_plan(console: Console, entries: list[Any]) -> None:
    """Render an agent plan as a bullet list inside a panel."""
    lines: list[str] = []
    for entry in entries:
        title = getattr(entry, "title", None) or str(entry)
        status = getattr(entry, "status", None) or ""
        icon = "✅" if status == "done" else "⏳" if status == "in_progress" else "○"
        lines.append(f"  {icon} {title}")
    body = "\n".join(lines) if lines else "(empty plan)"
    console.print(Panel(body, title="📋 Agent Plan", border_style="blue"))


# ── Usage ───────────────────────────────────────────────────────────────

def print_usage(console: Console, update: Any) -> None:
    """Render token usage statistics."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="dim")
    table.add_column(style="dim cyan", justify="right")
    if hasattr(update, "input_tokens") and update.input_tokens is not None:
        table.add_row("Input tokens", str(update.input_tokens))
    if hasattr(update, "output_tokens") and update.output_tokens is not None:
        table.add_row("Output tokens", str(update.output_tokens))
    if table.row_count:
        console.print(Panel(table, title="📊 Usage", border_style="dim", expand=False))


# ── Permissions ─────────────────────────────────────────────────────────

def print_permission_prompt(
    console: Console,
    description: str,
    options: list[tuple[int, str, str]],
) -> None:
    """Display a permission request panel.

    Args:
        description: What the agent wants to do.
        options: List of ``(index, label, kind)`` tuples.
    """
    lines: list[str] = [f"  {description}", ""]
    for idx, label, kind in options:
        if "allow" in kind:
            icon = "✅"
        else:
            icon = "❌"
        lines.append(f"  [{idx}] {icon} {label}  [dim]({kind})[/dim]")

    console.print()
    console.print(
        Panel(
            "\n".join(lines),
            title="⚠️  Permission Required",
            border_style="bold yellow",
            expand=False,
        )
    )


# ── Connection info ─────────────────────────────────────────────────────

def print_connection_info(
    console: Console,
    host: str,
    port: int,
    agent_name: str | None = None,
    agent_version: str | None = None,
    session_id: str | None = None,
) -> None:
    """Show a summary panel after a successful connection."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="bold")
    table.add_column(style="cyan")
    table.add_row("Host", f"{host}:{port}")
    if agent_name:
        table.add_row("Agent", agent_name)
    if agent_version:
        table.add_row("Version", agent_version)
    if session_id:
        table.add_row("Session", session_id)
    console.print(Panel(table, title="✅ Connected", border_style="green", expand=False))


def print_status(
    console: Console,
    *,
    connected: bool,
    host: str | None = None,
    port: int | None = None,
    session_id: str | None = None,
) -> None:
    """Show the current connection status."""
    if connected:
        console.print(
            f"  [green]●[/green] Connected to [bold]{host}:{port}[/bold]"
            f"  session=[cyan]{session_id}[/cyan]"
        )
    else:
        console.print("  [red]●[/red] Not connected")


# ── Errors & info ───────────────────────────────────────────────────────

def print_error(console: Console, message: str) -> None:
    """Print an error message in a red panel."""
    console.print(Panel(message, title="❌ Error", border_style="red", expand=False))


def print_info(console: Console, message: str) -> None:
    """Print a dim informational message."""
    console.print(Text(f"  ℹ️  {message}", style="dim"))


def print_warning(console: Console, message: str) -> None:
    """Print a warning message."""
    console.print(Text(f"  ⚠️  {message}", style="yellow"))
