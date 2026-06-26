"""Interactive Chat screen for the Sancho Mobile client."""

import flet as ft
from datetime import datetime
from acp.schema import (
    AgentMessageChunk,
    AgentThoughtChunk,
    ToolCallStart,
    ToolCallProgress,
    AgentPlanUpdate,
    SessionInfoUpdate,
    UsageUpdate,
    TextContentBlock,
    ImageContentBlock,
    AudioContentBlock,
    ResourceContentBlock,
    EmbeddedResourceContentBlock,
)

from .components.chat_bubble import chat_bubble
from .components.thought_bubble import thought_bubble
from .components.tool_card import ToolCard

def build_chat_view(app, page: ft.Page) -> ft.View:
    """Builds and returns the Chat screen view."""
    
    # 1. Base UI list log
    chat_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=10,
        auto_scroll=True,
    )
    
    # 2. Active streaming controls references
    active_agent_bubble_ref = [None]  # List wrapper to make it mutable in nested scopes
    active_agent_text_ref = [""]
    active_thought_bubble_ref = [None]
    active_thought_text_ref = [""]
    tool_cards = {}  # tool_call_id -> ToolCard

    # 3. Stream reset helper
    def clear_active_streams():
        active_agent_bubble_ref[0] = None
        active_agent_text_ref[0] = ""
        active_thought_bubble_ref[0] = None
        active_thought_text_ref[0] = ""

    # 4. System log messages helper
    def append_system_message(msg: str, is_error: bool = False, is_warning: bool = False):
        color = ft.Colors.RED_400 if is_error else ft.Colors.AMBER_400 if is_warning else ft.Colors.OUTLINE
        chat_list.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Text(msg, size=11, color=color, italic=True),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                    alignment=ft.Alignment.CENTER,
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        )
        chat_list.update()

    # 5. Connection Details Info Dialog helpers
    def close_info_dialog():
        page.pop_dialog()

    def show_connection_info():
        info_dialog = ft.AlertDialog(
            title=ft.Text("Connection Details"),
            content=ft.Column([
                ft.Text(f"Host: {app.host}:{app.port}"),
                ft.Text(f"Agent: {app.agent_name or 'Unknown'}"),
                ft.Text(f"Agent Version: {app.agent_version or 'Unknown'}"),
                ft.Text(f"Session ID: {app.session_id}"),
            ], tight=True, spacing=6),
            actions=[
                ft.TextButton("Close", on_click=lambda e: close_info_dialog())
            ],
        )
        page.show_dialog(info_dialog)

    def show_font_size_dialog():
        def set_font_scale(e):
            scale_val = float(radio_group.value)
            app.font_scale = scale_val
            for control in chat_list.controls:
                if hasattr(control, "update_font_scale"):
                    control.update_font_scale(scale_val)
            chat_list.update()

        radio_group = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="0.85", label="Small (85%)"),
                ft.Radio(value="1.0", label="Medium (100%)"),
                ft.Radio(value="1.2", label="Large (120%)"),
                ft.Radio(value="1.35", label="Extra Large (135%)"),
            ], spacing=6),
            value=str(app.font_scale),
            on_change=set_font_scale,
        )

        size_dialog = ft.AlertDialog(
            title=ft.Text("Select Font Size"),
            content=ft.Column([
                radio_group,
            ], tight=True),
            actions=[
                ft.TextButton("Close", on_click=lambda e: page.pop_dialog())
            ],
        )
        page.show_dialog(size_dialog)

    # 6. Session task disconnect and cancel handlers
    async def run_disconnect():
        status_dot.color = ft.Colors.RED_400
        status_text.value = "Disconnected"
        page.update()
        await app.disconnect()
        page.go("/connect")

    def trigger_disconnect(e=None):
        page.run_task(run_disconnect)

    async def run_cancel():
        try:
            await app.cancel_task()
            append_system_message("Cancel signal sent to agent.", is_warning=True)
        except Exception as exc:
            append_system_message(f"Cancel failed: {exc}", is_error=True)
        page.update()

    def trigger_cancel(e=None):
        page.run_task(run_cancel)

    # 7. Prompt sending handler
    async def run_send():
        text = input_field.value.strip()
        if not text:
            return
        
        # Clear field and reset streams
        input_field.value = ""
        clear_active_streams()
        
        # Add User bubble
        chat_list.controls.append(chat_bubble(text, is_user=True, font_scale=app.font_scale))
        
        # Update inputs state
        input_field.disabled = True
        send_btn.disabled = True
        cancel_btn.visible = True
        page.update()

        try:
            await app.send_prompt(text)
        except Exception as exc:
            append_system_message(f"Error: {exc}", is_error=True)
        finally:
            input_field.disabled = False
            send_btn.disabled = False
            cancel_btn.visible = False
            page.update()
            await input_field.focus()

    def trigger_send(e=None):
        page.run_task(run_send)

    # 8. Interactive inputs controls
    input_field = ft.TextField(
        hint_text="Type a message...",
        expand=True,
        border_color=ft.Colors.OUTLINE,
        focused_border_color=ft.Colors.TEAL_400,
        multiline=True,
        min_lines=1,
        max_lines=4,
        shift_enter=True,
        on_submit=trigger_send,
    )
    
    send_btn = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=ft.Colors.TEAL_400,
        tooltip="Send Message",
        on_click=trigger_send,
    )
    
    cancel_btn = ft.IconButton(
        icon=ft.Icons.STOP_CIRCLE_ROUNDED,
        icon_color=ft.Colors.RED_400,
        tooltip="Cancel execution",
        visible=False,
        on_click=trigger_cancel,
    )
    
    input_row = ft.Row(
        controls=[
            input_field,
            cancel_btn,
            send_btn,
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # 9. AppBar & info indicators
    agent_name_text = ft.Text("Sancho ACP Agent", weight=ft.FontWeight.BOLD, size=16)
    status_dot = ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREEN_400, size=10)
    status_text = ft.Text("Connected", size=11, color=ft.Colors.OUTLINE)
    
    app_bar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            on_click=trigger_disconnect,
        ),
        title=ft.Row([
            ft.CircleAvatar(
                content=ft.Icon(ft.Icons.SMART_TOY_ROUNDED, color=ft.Colors.TEAL_800),
                bgcolor=ft.Colors.TEAL_100,
                radius=18,
            ),
            ft.Column([
                agent_name_text,
                ft.Row([status_dot, status_text], spacing=4),
            ], spacing=2, tight=True)
        ], alignment=ft.MainAxisAlignment.START, spacing=8),
        actions=[
            ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(
                        content=ft.Text("Cancel Current Task"),
                        icon=ft.Icons.STOP_ROUNDED,
                        on_click=trigger_cancel,
                    ),
                    ft.PopupMenuItem(
                        content=ft.Text("Connection Details"),
                        icon=ft.Icons.INFO_ROUNDED,
                        on_click=lambda e: show_connection_info(),
                    ),
                    ft.PopupMenuItem(
                        content=ft.Text("Font Size"),
                        icon=ft.Icons.FORMAT_SIZE_ROUNDED,
                        on_click=lambda e: show_font_size_dialog(),
                    ),
                    ft.PopupMenuItem(
                        content=ft.Text("Disconnect"),
                        icon=ft.Icons.LOGOUT_ROUNDED,
                        on_click=trigger_disconnect,
                    ),
                ]
            )
        ],
        bgcolor=ft.Colors.SURFACE_CONTAINER,
    )

    # Callback registered on SanchoApp to dispatch incoming session updates to this View
    async def on_session_update(update):
        # Handle Agent text/message chunks
        if isinstance(update, AgentMessageChunk):
            content = update.content
            block_type = None
            text_content = ""
            
            if isinstance(content, TextContentBlock):
                text_content = content.text
            elif isinstance(content, ImageContentBlock):
                block_type = "image"
                text_content = "[Image Block received]"
            elif isinstance(content, AudioContentBlock):
                block_type = "audio"
                text_content = "[Audio Block received]"
            elif isinstance(content, ResourceContentBlock):
                block_type = "resource"
                text_content = getattr(content, "uri", None) or "[Resource Link]"
            elif isinstance(content, EmbeddedResourceContentBlock):
                block_type = "resource"
                text_content = "[Embedded Resource]"
            
            if text_content:
                # If streaming normal text, try to append
                if block_type is None and active_agent_bubble_ref[0] is not None:
                    active_agent_text_ref[0] += text_content
                    active_agent_bubble_ref[0].update_text(active_agent_text_ref[0])
                else:
                    # Start a new bubble
                    active_agent_text_ref[0] = text_content
                    new_bubble = chat_bubble(text_content, is_user=False, block_type=block_type, font_scale=app.font_scale)
                    
                    if block_type is None:
                        active_agent_bubble_ref[0] = new_bubble
                        active_thought_bubble_ref[0] = None  # Reset thoughts stream when agent speaks
                    
                    chat_list.controls.append(new_bubble)
                    chat_list.update()
        
        # Handle Agent reasoning thoughts
        elif isinstance(update, AgentThoughtChunk):
            content = update.content
            text_content = content.text if isinstance(content, TextContentBlock) else str(content)
            
            if text_content:
                if active_thought_bubble_ref[0] is not None:
                    active_thought_text_ref[0] += text_content
                    active_thought_bubble_ref[0].update_thought(active_thought_text_ref[0])
                else:
                    active_thought_text_ref[0] = text_content
                    new_bubble = thought_bubble(text_content, font_scale=app.font_scale)
                    active_thought_bubble_ref[0] = new_bubble
                    active_agent_bubble_ref[0] = None  # Reset speaking stream when agent thinks
                    
                    chat_list.controls.append(new_bubble)
                    chat_list.update()

        # Handle tool call starts
        elif isinstance(update, ToolCallStart):
            clear_active_streams()
            tool_name = getattr(update, "title", None) or "unknown"
            tool_call_id = getattr(update, "tool_call_id", None)
            
            card = ToolCard(tool_name, tool_call_id, font_scale=app.font_scale)
            if tool_call_id:
                tool_cards[tool_call_id] = card
                
            chat_list.controls.append(card)
            chat_list.update()

        # Handle tool call progress
        elif isinstance(update, ToolCallProgress):
            tool_call_id = getattr(update, "tool_call_id", None)
            card = tool_cards.get(tool_call_id)
            if card:
                status = getattr(update, "status", None)
                title = getattr(update, "title", None)
                
                parts = []
                content_list = getattr(update, "content", None)
                if content_list:
                    for item in content_list:
                        if getattr(item, "type", None) == "content":
                            inner = getattr(item, "content", None)
                            if isinstance(inner, TextContentBlock) and inner.text:
                                parts.append(inner.text)
                
                progress_text = " - ".join(parts) if parts else None
                raw_output = getattr(update, "raw_output", None)
                raw_output_str = str(raw_output) if raw_output is not None else None
                
                card.update_progress(
                    status=status,
                    title=title,
                    progress_text=progress_text,
                    raw_output=raw_output_str,
                )

        # Handle agent plan updates
        elif isinstance(update, AgentPlanUpdate):
            clear_active_streams()
            entries = getattr(update, "entries", None) or []
            plan_lines = []
            for entry in entries:
                title = getattr(entry, "title", None) or str(entry)
                status = getattr(entry, "status", None) or ""
                icon = "✅" if status == "done" else "⏳" if status == "in_progress" else "○"
                plan_lines.append(f"{icon} {title}")
            
            plan_text = "\n".join(plan_lines) if plan_lines else "(empty plan)"
            chat_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PLAYLIST_ADD_CHECK_ROUNDED, color=ft.Colors.BLUE_400),
                            ft.Text("Agent Plan", weight=ft.FontWeight.BOLD, size=14),
                        ], spacing=6),
                        ft.Text(plan_text, size=12),
                    ], tight=True),
                    padding=10,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_400),
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.BLUE_400)),
                    border_radius=10,
                    margin=ft.Margin.symmetric(vertical=4),
                )
            )
            chat_list.update()

        # Handle token usage
        elif isinstance(update, UsageUpdate):
            parts = []
            if getattr(update, "input_tokens", None) is not None:
                parts.append(f"Input: {update.input_tokens}")
            if getattr(update, "output_tokens", None) is not None:
                parts.append(f"Output: {update.output_tokens}")
            if parts:
                append_system_message(f"Usage: {', '.join(parts)}")

        # Handle session info updates
        elif isinstance(update, SessionInfoUpdate):
            info_text = getattr(update, "info", None) or str(update)
            append_system_message(f"Session info: {info_text}")

        # Others
        else:
            append_system_message(f"Notification: {type(update).__name__}")

    # Register on_session_update callback on app object
    app.on_session_update_view_callback = on_session_update

    return ft.View(
        route="/chat",
        controls=[
            chat_list,
            ft.Divider(height=1, color=ft.Colors.OUTLINE),
            ft.Container(
                content=input_row,
                padding=ft.Padding.only(left=10, right=10, bottom=10, top=5),
            )
        ],
        appbar=app_bar,
        bgcolor=ft.Colors.SURFACE,
    )
