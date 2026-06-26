"""Theme and styling configuration for Sancho Mobile client."""

import flet as ft

# Mobile phone dimensions simulator (iPhone 14-like)
WINDOW_WIDTH = 390
WINDOW_HEIGHT = 844

# Theme settings
DARK_THEME_COLOR_SEED = ft.Colors.TEAL_800

def get_theme() -> ft.Theme:
    """Returns the dark theme configured for Sancho Mobile."""
    return ft.Theme(
        color_scheme_seed=DARK_THEME_COLOR_SEED,
        visual_density=ft.VisualDensity.COMFORTABLE,
        use_material3=True,
    )
