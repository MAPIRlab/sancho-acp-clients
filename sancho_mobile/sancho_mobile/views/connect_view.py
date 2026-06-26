"""Dedicated connection screen for the Sancho Mobile client."""

import flet as ft

def build_connect_view(app, page: ft.Page) -> ft.View:
    """Builds and returns the Connection screen view."""
    
    # Text input fields
    host_field = ft.TextField(
        label="Host Address",
        value=app.host or "127.0.0.1",
        hint_text="e.g. 127.0.0.1 or sancho.isa.uma.es",
        border_color=ft.Colors.TEAL_400,
        focused_border_color=ft.Colors.TEAL_200,
        text_size=15,
        autofocus=True,
    )
    
    port_field = ft.TextField(
        label="Port",
        value=str(app.port or 9100),
        hint_text="e.g. 9100",
        border_color=ft.Colors.TEAL_400,
        focused_border_color=ft.Colors.TEAL_200,
        text_size=15,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    
    status_ring = ft.ProgressRing(width=24, height=24, stroke_width=3, visible=False)
    def show_error(msg: str):
        snack = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_800,
        )
        page.show_dialog(snack)

    async def run_connect():
        host = host_field.value.strip()
        port_str = port_field.value.strip()
        
        if not host:
            show_error("Host address cannot be empty.")
            return
        
        try:
            port = int(port_str)
        except ValueError:
            show_error("Port must be a valid number.")
            return

        # Show connecting state
        host_field.disabled = True
        port_field.disabled = True
        connect_btn.disabled = True
        status_ring.visible = True
        page.update()

        try:
            success = await app.connect(host, port)
            if success:
                # Redirect to chat
                page.go("/chat")
        except Exception as exc:
            show_error(f"Connection failed: {exc}")
        finally:
            # Reset UI state on failure/completion
            host_field.disabled = False
            port_field.disabled = False
            connect_btn.disabled = False
            status_ring.visible = False
            page.update()

    def trigger_connect(e):
        page.run_task(run_connect)

    connect_btn = ft.Button(
        content="Connect to Agent",
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.TEAL_700,
            padding=15,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        on_click=trigger_connect,
    )

    # Layout construction
    logo = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.SMART_TOY_ROUNDED, size=80, color=ft.Colors.TEAL_300),
            ft.Text(
                "SANCHO",
                size=28,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.TEAL_100,
                style=ft.TextStyle(letter_spacing=4),
            ),
            ft.Text(
                "ACP Mobile Client",
                size=12,
                color=ft.Colors.OUTLINE,
                italic=True,
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        margin=ft.Margin.only(top=60, bottom=40),
    )

    form = ft.Container(
        content=ft.Column([
            host_field,
            ft.Container(height=10),
            port_field,
            ft.Container(height=30),
            ft.Row([
                connect_btn,
                status_ring,
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
    )

    return ft.View(
        route="/connect",
        controls=[
            ft.Column([
                logo,
                form,
            ], scroll=ft.ScrollMode.ADAPTIVE, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        ],
        bgcolor=ft.Colors.SURFACE,
    )
