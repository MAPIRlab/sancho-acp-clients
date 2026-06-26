"""Permission dialog for user approval of agent actions."""

from __future__ import annotations

import asyncio
import flet as ft
from acp.schema import (
    AllowedOutcome,
    DeniedOutcome,
    PermissionOption,
    RequestPermissionResponse,
    ToolCallUpdate,
)

async def show_permission_dialog(
    page: ft.Page,
    options: list[PermissionOption],
    tool_call: ToolCallUpdate,
) -> RequestPermissionResponse:
    """Shows a modal AlertDialog and returns the user's choice.
    
    This function blocks using an asyncio.Future until the user selects an option.
    """
    loop = asyncio.get_running_loop()
    future: asyncio.Future[RequestPermissionResponse] = loop.create_future()

    # Description of what the tool wants to do
    description = f"Tool: {getattr(tool_call, 'title', None) or tool_call.tool_call_id}"
    raw_input = getattr(tool_call, "raw_input", None)
    if raw_input:
        description += f"\nInput: {raw_input}"

    def on_option_selected(opt: PermissionOption):
        # Close the dialog
        page.pop_dialog()
        
        # Resolve the future
        if "allow" in opt.kind:
            future.set_result(
                RequestPermissionResponse(
                    outcome=AllowedOutcome(
                        outcome="selected",
                        option_id=opt.option_id,
                    )
                )
            )
        else:
            future.set_result(
                RequestPermissionResponse(
                    outcome=DeniedOutcome(outcome="cancelled")
                )
            )

    # Build option controls
    option_controls = []
    for opt in options:
        is_allow = "allow" in opt.kind
        icon = ft.Icons.CHECK_CIRCLE if is_allow else ft.Icons.CANCEL
        color = ft.Colors.GREEN_400 if is_allow else ft.Colors.RED_400
        
        option_controls.append(
            ft.ListTile(
                leading=ft.Icon(icon, color=color),
                title=ft.Text(opt.name, weight=ft.FontWeight.W_500),
                subtitle=ft.Text(f"Kind: {opt.kind}", size=11, color=ft.Colors.OUTLINE),
                on_click=lambda e, opt=opt: on_option_selected(opt),
            )
        )

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER, size=24),
            ft.Text("Permission Required", weight=ft.FontWeight.BOLD),
        ], spacing=10),
        content=ft.Column([
            ft.Text("The robotic agent wants to execute a protected action:", size=13),
            ft.Container(
                content=ft.Text(description, font_family="monospace", size=12),
                padding=8,
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                border_radius=6,
            ),
            ft.Divider(),
            ft.Text("Choose an option:", weight=ft.FontWeight.BOLD, size=12),
            ft.Column(option_controls, spacing=4, tight=True),
        ], tight=True, spacing=10),
    )

    page.show_dialog(dialog)

    try:
        return await future
    except asyncio.CancelledError:
        # Fallback to denied outcome if dialog is cancelled/closed somehow
        return RequestPermissionResponse(outcome=DeniedOutcome(outcome="cancelled"))
