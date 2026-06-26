"""ASCII art banner for the Sancho ACP CLI."""

from __future__ import annotations

from rich.console import Console
from rich.text import Text

from . import __version__

_BANNER_LINES = [
    "   ███████╗ █████╗ ███╗   ██╗ ██████╗██╗  ██╗ ██████╗ ",
    "   ██╔════╝██╔══██╗████╗  ██║██╔════╝██║  ██║██╔═══██╗",
    "   ███████╗███████║██╔██╗ ██║██║     ███████║██║   ██║ ",
    "   ╚════██║██╔══██║██║╚██╗██║██║     ██╔══██║██║   ██║ ",
    "   ███████║██║  ██║██║ ╚████║╚██████╗██║  ██║╚██████╔╝ ",
    "   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ",
]

# Gradient from cyan to blue to purple across the banner lines.
_GRADIENT_COLORS = [
    "#00d4ff",
    "#00aaff",
    "#0088ff",
    "#4466ff",
    "#6644ff",
    "#8833dd",
]


def display_banner(console: Console) -> None:
    """Print the Sancho ASCII art banner with a vertical colour gradient."""
    console.print()
    for line, colour in zip(_BANNER_LINES, _GRADIENT_COLORS):
        console.print(Text(line, style=f"bold {colour}"))

    subtitle = Text("              ACP Client", style="bold white")
    subtitle.append(" • ", style="dim white")
    subtitle.append(f"v{__version__}", style="dim cyan")
    console.print(subtitle)
    console.print()


def show_help_hint(console: Console) -> None:
    """Print a one-liner pointing the user to /help."""
    console.print(
        "  Type [bold cyan]/help[/bold cyan] for available commands, "
        "or [bold cyan]/connect <host> <port>[/bold cyan] to start.",
        highlight=False,
    )
    console.print()
