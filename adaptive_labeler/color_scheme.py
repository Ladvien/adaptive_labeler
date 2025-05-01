import flet as ft


class LabelerColorScheme:
    """
    Dark mode color scheme: professional and cheery.
    """

    # Core colors
    PRIMARY = "#0EA5E9"  # Bright sky blue (primary action)
    SECONDARY = "#FBBF24"  # Warm amber (accents, sliders)
    BACKGROUND = "#111827"  # Deep navy gray (main background)
    SURFACE = "#1F2937"  # Slightly lighter card background
    ERROR = "#F87171"  # Soft red (for errors and alerts)

    # Text and foreground
    ON_PRIMARY = "#FFFFFF"  # Text on blue
    ON_SECONDARY = "#000000"  # Text on amber
    ON_BACKGROUND = "#F3F4F6"  # General text (light gray)
    ON_SURFACE = "#D1D5DB"  # Subdued card text

    @classmethod
    def flet_color_scheme(cls) -> ft.ColorScheme:
        return ft.ColorScheme(
            primary=cls.PRIMARY,
            secondary=cls.SECONDARY,
            background=cls.BACKGROUND,
            surface=cls.SURFACE,
            error=cls.ERROR,
            on_primary=cls.ON_PRIMARY,
            on_secondary=cls.ON_SECONDARY,
            on_background=cls.ON_BACKGROUND,
            on_surface=cls.ON_SURFACE,
        )
