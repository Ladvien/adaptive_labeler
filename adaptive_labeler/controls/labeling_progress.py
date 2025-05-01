import flet as ft


class LabelingProgress(ft.Container):
    def __init__(
        self,
        value: float,
        progress_text: str,
        expand: int = 1,
        color_scheme: ft.ColorScheme | None = None,
    ):
        super().__init__()

        # Fallback theme
        self.color_scheme = color_scheme or ft.ColorScheme(
            on_surface="#FFFFFF",
            surface="#1E1E2F",
            secondary="#C792EA",
        )

        self.text = ft.Text(
            progress_text,
            size=14,
            weight=ft.FontWeight.BOLD,
            color=self.color_scheme.on_surface,
            text_align=ft.TextAlign.RIGHT,
        )

        self.progress = ft.ProgressBar(
            value=value,
            bgcolor=self.color_scheme.surface,
            color=self.color_scheme.secondary,
            height=12,
            expand=True,
        )

        self.content = ft.Column(
            [
                self.text,
                self.progress,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.expand = expand

    def update_progress(self, value: float, progress_text: str):
        self.text.value = progress_text
        self.progress.value = value
        self.update()
