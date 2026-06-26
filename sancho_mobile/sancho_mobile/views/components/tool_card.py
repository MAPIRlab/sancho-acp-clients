"""ToolCard component for tracking tool call execution and progress."""

import flet as ft

class ToolCard(ft.Container):
    """Custom Flet control representing a tool execution log with a premium visual design and collapsible output."""

    def __init__(self, tool_name: str, tool_call_id: str, font_scale: float = 1.0):
        self.tool_name = tool_name
        self.tool_call_id = tool_call_id
        self.font_scale = font_scale
        
        # State tracking for dynamic scaling and visibility reconstruction
        self.last_status = None
        self.last_title = None
        self.last_progress_text = None
        self.last_raw_output = None
        self.output_expanded = False # Collapsed by default
        
        # Inner controls
        self.status_icon = ft.ProgressRing(width=12 * self.font_scale, height=12 * self.font_scale, stroke_width=2)
        self.status_text = ft.Text("Executing...", size=11 * self.font_scale, italic=True, color=ft.Colors.AMBER_300)
        self.status_row = ft.Row([self.status_icon, self.status_text], spacing=6, alignment=ft.MainAxisAlignment.END)
        
        self.title_icon = ft.Icon(ft.Icons.TERMINAL_ROUNDED, color=ft.Colors.AMBER_400, size=16 * self.font_scale)
        self.title_text = ft.Text(
            f"Tool: {tool_name}", 
            weight=ft.FontWeight.BOLD, 
            size=13 * self.font_scale, 
            color=ft.Colors.AMBER_100,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
        )
        
        self.header_row = ft.Row([
            ft.Row([self.title_icon, self.title_text], spacing=6, expand=True),
            self.status_row,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        self.details_column = ft.Column(spacing=4)

        super().__init__(
            content=ft.Column([
                self.header_row,
                self.details_column
            ], tight=True, spacing=6),
            padding=12,
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.AMBER_400),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.AMBER_400)),
            border_radius=10,
            margin=ft.Margin.symmetric(vertical=6, horizontal=2),
        )

    def toggle_output_visibility(self, e):
        """Toggles the visibility state of the output block and triggers a redraw."""
        self.output_expanded = not self.output_expanded
        self.update_progress(
            status=self.last_status,
            title=self.last_title,
            progress_text=self.last_progress_text,
            raw_output=self.last_raw_output
        )

    def update_progress(self, status: str | None, title: str | None, progress_text: str | None, raw_output: str | None):
        """Updates the status, visuals, colors, and details of the tool card."""
        self.last_status = status
        self.last_title = title
        self.last_progress_text = progress_text
        self.last_raw_output = raw_output
        
        current_status = status or "in_progress"
        scale = self.font_scale
        
        # 1. Update status icons and text colors dynamically based on execution outcome
        if current_status == "completed":
            self.status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=ft.Colors.GREEN_400, size=14 * scale)
            self.status_text.value = "Completed"
            self.status_text.color = ft.Colors.GREEN_300
            
            self.bgcolor = ft.Colors.with_opacity(0.04, ft.Colors.GREEN_400)
            self.border = ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.GREEN_400))
            self.title_icon.color = ft.Colors.GREEN_400
            self.title_text.color = ft.Colors.GREEN_100
            
        elif current_status == "failed":
            self.status_icon = ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=ft.Colors.RED_400, size=14 * scale)
            self.status_text.value = "Failed"
            self.status_text.color = ft.Colors.RED_300
            
            self.bgcolor = ft.Colors.with_opacity(0.04, ft.Colors.RED_400)
            self.border = ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.RED_400))
            self.title_icon.color = ft.Colors.RED_400
            self.title_text.color = ft.Colors.RED_100
            
        else: # in_progress
            self.status_icon = ft.ProgressRing(width=12 * scale, height=12 * scale, stroke_width=2)
            self.status_text.value = "Executing..."
            self.status_text.color = ft.Colors.AMBER_300
            
            self.bgcolor = ft.Colors.with_opacity(0.04, ft.Colors.AMBER_400)
            self.border = ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.AMBER_400))
            self.title_icon.color = ft.Colors.AMBER_400
            self.title_text.color = ft.Colors.AMBER_100

        # Replace status row controls
        self.status_row.controls = [self.status_icon, self.status_text]

        # 2. Re-populate details column with clean logs and dedicated response block
        self.details_column.controls.clear()
        
        # Display progress / info messages
        logs = []
        if title and title != self.tool_name:
            logs.append(title)
        if progress_text:
            logs.append(progress_text)
            
        for log_msg in logs:
            self.details_column.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=12 * scale, color=ft.Colors.OUTLINE),
                    ft.Text(log_msg, size=11 * scale, color=ft.Colors.ON_SURFACE_VARIANT, no_wrap=False),
                ], spacing=4)
            )
            
        # Display raw output in a dedicated collapsible code box if present
        if raw_output:
            arrow_icon = ft.Icons.KEYBOARD_ARROW_UP_ROUNDED if self.output_expanded else ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED
            toggle_label = "Hide Response Output" if self.output_expanded else "Show Response Output"
            
            # Interactive toggle button container
            toggle_container = ft.Container(
                content=ft.Row([
                    ft.Icon(arrow_icon, size=14 * scale, color=ft.Colors.TEAL_400),
                    ft.Text(toggle_label, size=9.5 * scale, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_400),
                ], spacing=4),
                on_click=self.toggle_output_visibility,
                padding=ft.Padding.symmetric(vertical=4, horizontal=2),
                border_radius=4,
            )
            
            out_color = ft.Colors.GREEN_100 if current_status == "completed" else ft.Colors.RED_100 if current_status == "failed" else ft.Colors.ON_SURFACE
            output_box = ft.Container(
                content=ft.Text(
                    raw_output.strip(),
                    font_family="monospace",
                    size=10.5 * scale,
                    color=out_color,
                    selectable=True,
                    no_wrap=False,
                ),
                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                padding=8,
                border_radius=6,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.OUTLINE)),
                visible=self.output_expanded, # Bound to state
            )
            
            self.details_column.controls.extend([
                toggle_container,
                output_box
            ])
        
        try:
            self.update()
        except RuntimeError:
            pass

    def update_font_scale(self, scale: float):
        """Updates font scale and redraws internal controls with the new scale factor."""
        self.font_scale = scale
        self.title_icon.size = 16 * scale
        self.title_text.size = 13 * scale
        self.status_text.size = 11 * scale
        
        # Trigger rebuild with current progress states and new font scale applied
        self.update_progress(
            status=self.last_status,
            title=self.last_title,
            progress_text=self.last_progress_text,
            raw_output=self.last_raw_output
        )
