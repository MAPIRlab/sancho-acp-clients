"""Chat bubble component simulating mobile message bubbles."""

import flet as ft
from datetime import datetime

class ChatBubble(ft.Row):
    """Custom Flet control representing a chat bubble with dynamic scaling support."""

    def __init__(
        self,
        text: str,
        is_user: bool,
        timestamp: str | None = None,
        block_type: str | None = None,
        font_scale: float = 1.0,
    ):
        self.is_user = is_user
        self.block_type = block_type
        self.base_text = text
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        self.font_scale = font_scale

        # Build contents dynamically
        self.content_control = None
        self._build_content_control()

        self.timestamp_text = ft.Text(
            self.timestamp,
            size=9 * self.font_scale,
            color=ft.Colors.OUTLINE,
            text_align=ft.TextAlign.RIGHT,
        )

        bubble_bg = ft.Colors.PRIMARY_CONTAINER if is_user else ft.Colors.SURFACE_CONTAINER
        border_radius = ft.BorderRadius.only(
            top_left=16,
            top_right=16,
            bottom_left=4 if is_user else 16,
            bottom_right=16 if is_user else 4,
        )

        super().__init__(
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    content=ft.Column([
                        self.content_control,
                        self.timestamp_text
                    ], tight=True, spacing=4),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    bgcolor=bubble_bg,
                    border_radius=border_radius,
                    width=280,
                )
            ],
        )

    def _build_content_control(self):
        scale = self.font_scale
        text = self.base_text
        if self.block_type == "image":
            self.block_icon = ft.Icon(ft.Icons.IMAGE, color=ft.Colors.OUTLINE, size=16 * scale)
            self.block_title = ft.Text("Image Block", weight=ft.FontWeight.BOLD, size=13 * scale)
            self.block_body = ft.Text(text or "[Image Received]", italic=True, size=14 * scale)
            self.content_control = ft.Column([
                ft.Row([self.block_icon, self.block_title], alignment=ft.MainAxisAlignment.START, spacing=8),
                self.block_body,
            ], tight=True)
        elif self.block_type == "audio":
            self.block_icon = ft.Icon(ft.Icons.AUDIOTRACK, color=ft.Colors.OUTLINE, size=16 * scale)
            self.block_title = ft.Text("Audio Block", weight=ft.FontWeight.BOLD, size=13 * scale)
            self.block_body = ft.Text(text or "[Audio Received]", italic=True, size=14 * scale)
            self.content_control = ft.Column([
                ft.Row([self.block_icon, self.block_title], alignment=ft.MainAxisAlignment.START, spacing=8),
                self.block_body,
            ], tight=True)
        elif self.block_type == "resource":
            self.block_icon = ft.Icon(ft.Icons.ATTACH_FILE, color=ft.Colors.BLUE_400, size=16 * scale)
            self.block_title = ft.Text("Resource Link", weight=ft.FontWeight.BOLD, size=13 * scale)
            self.block_body = ft.Text(text or "[File URI]", size=14 * scale, color=ft.Colors.BLUE_300, selectable=True)
            self.content_control = ft.Column([
                ft.Row([self.block_icon, self.block_title], alignment=ft.MainAxisAlignment.START, spacing=8),
                self.block_body,
            ], tight=True)
        else:
            # Standard Markdown message
            self.content_control = ft.Markdown(
                text,
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                code_theme="atom-one-dark",
                md_style_sheet=ft.MarkdownStyleSheet(
                    p_text_style=ft.TextStyle(size=14 * scale)
                ),
            )

    def update_text(self, text: str):
        """Updates the message text dynamically."""
        self.base_text = text
        if isinstance(self.content_control, ft.Markdown):
            self.content_control.value = text
        else:
            self._build_content_control()
            self.controls[0].content.controls[0] = self.content_control
            
        try:
            self.update()
        except RuntimeError:
            pass

    def update_font_scale(self, scale: float):
        """Updates the text scale of the bubble dynamically."""
        self.font_scale = scale
        self.timestamp_text.size = 9 * scale
        
        if isinstance(self.content_control, ft.Markdown):
            self.content_control.md_style_sheet = ft.MarkdownStyleSheet(
                p_text_style=ft.TextStyle(size=14 * scale)
            )
        else:
            self._build_content_control()
            self.controls[0].content.controls[0] = self.content_control
            
        try:
            self.update()
        except RuntimeError:
            pass

def chat_bubble(
    text: str,
    is_user: bool,
    timestamp: str | None = None,
    block_type: str | None = None,
    font_scale: float = 1.0,
) -> ChatBubble:
    """Returns a ChatBubble Flet Control."""
    return ChatBubble(text, is_user, timestamp, block_type, font_scale)
