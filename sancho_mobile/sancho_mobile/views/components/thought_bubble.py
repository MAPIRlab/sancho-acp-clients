"""Thought bubble component for displaying Sancho's internal thoughts."""

import flet as ft
from datetime import datetime

class ThoughtBubble(ft.Row):
    """Custom Flet control representing the agent's thinking process with dynamic scaling."""

    def __init__(self, text: str, timestamp: str | None = None, font_scale: float = 1.0):
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")
        
        self.font_scale = font_scale
        
        self.thought_text_control = ft.Text(
            text,
            style=ft.TextStyle(italic=True, color=ft.Colors.PURPLE_100),
            size=12.5 * self.font_scale,
            selectable=True,
            no_wrap=False,
        )
        
        self.timestamp_control = ft.Text(
            timestamp,
            size=9 * self.font_scale,
            color=ft.Colors.OUTLINE,
        )
        
        self.header_icon = ft.Icon(ft.Icons.PSYCHOLOGY_ROUNDED, color=ft.Colors.PURPLE_300, size=18 * self.font_scale)
        self.header_text = ft.Text("Reasoning", size=11 * self.font_scale, color=ft.Colors.PURPLE_300, weight=ft.FontWeight.BOLD)

        super().__init__(
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            self.header_icon,
                            self.header_text,
                        ], spacing=4),
                        self.thought_text_control,
                        ft.Row([self.timestamp_control], alignment=ft.MainAxisAlignment.END),
                    ], tight=True, spacing=4),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.PURPLE_200),
                    border=ft.Border(
                        left=ft.BorderSide(3, ft.Colors.PURPLE_400),
                        top=ft.BorderSide(1, ft.Colors.with_opacity(0.05, ft.Colors.OUTLINE)),
                        right=ft.BorderSide(1, ft.Colors.with_opacity(0.05, ft.Colors.OUTLINE)),
                        bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.05, ft.Colors.OUTLINE)),
                    ),
                    border_radius=ft.BorderRadius.only(
                        top_left=4,
                        top_right=12,
                        bottom_left=4,
                        bottom_right=12,
                    ),
                    width=290,
                )
            ],
        )

    def update_thought(self, text: str):
        """Updates the thought text and refreshes the control."""
        self.thought_text_control.value = text
        try:
            self.update()
        except RuntimeError:
            pass

    def update_font_scale(self, scale: float):
        """Updates the font scale dynamically."""
        self.font_scale = scale
        self.thought_text_control.size = 12.5 * scale
        self.timestamp_control.size = 9 * scale
        self.header_icon.size = 18 * scale
        self.header_text.size = 11 * scale
        try:
            self.update()
        except RuntimeError:
            pass

def thought_bubble(text: str, timestamp: str | None = None, font_scale: float = 1.0) -> ThoughtBubble:
    """Returns a Flet Control displaying agent reasoning."""
    return ThoughtBubble(text, timestamp, font_scale)
