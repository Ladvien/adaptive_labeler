import flet as ft


class LabelingProgress(ft.Container):
    DEFAULT_COLOR_SCHEME = ft.ColorScheme(
        on_surface="#FFFFFF",
        surface="#1E1E2F",
        secondary="#C792EA",
    )

    def __init__(
        self,
        value: float = 0.0,
        progress_text: str = "",
        expand: int = 1,
        color_scheme: ft.ColorScheme | None = None,
    ):
        super().__init__()

        self.color_scheme = color_scheme or self.DEFAULT_COLOR_SCHEME
        self._progress_value = value
        self._progress_text = progress_text

        self.text = ft.Text(
            self._progress_text,
            size=14,
            weight=ft.FontWeight.BOLD,
            color=self.color_scheme.on_surface,
            text_align=ft.TextAlign.RIGHT,
        )

        self.progress = ft.ProgressBar(
            value=self._progress_value,
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

    # --- Public API ---

    @property
    def value(self) -> float:
        return self._progress_value

    @value.setter
    def value(self, new_value: float):
        self._progress_value = new_value
        self.progress.value = new_value
        self.progress.update()

    @property
    def text_value(self) -> str:
        return self._progress_text

    @text_value.setter
    def text_value(self, new_text: str):
        self._progress_text = new_text
        self.text.value = new_text
        self.text.update()

    def update_progress(self, value: float, progress_text: str):
        """Convenience method to update both at once."""
        self.value = value
        self.text_value = progress_text
        self.update()
