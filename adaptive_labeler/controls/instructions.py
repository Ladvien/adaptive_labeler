import flet as ft


class Instructions(ft.Column):
    def __init__(self, color_scheme: ft.ColorScheme | None = None):
        super().__init__()

        # Use provided color scheme or fallback
        self.color_scheme = color_scheme or ft.ColorScheme(
            secondary="#C792EA",
            on_background="#FFFFFF",
        )

        # Styled instruction texts
        self.instructions_label = ft.Text(
            "Keyboard Shortcuts:",
            size=20,
            color=self.color_scheme.secondary,
            weight=ft.FontWeight.W_600,
        )
        self.left_arrow_label = ft.Text(
            "<- Left Arrow: Unacceptable",
            color=self.color_scheme.secondary,
        )
        self.right_arrow_label = ft.Text(
            "-> Right Arrow: Acceptable",
            color=self.color_scheme.secondary,
        )

        self.controls = [
            ft.Column(
                [
                    self.instructions_label,
                    self.left_arrow_label,
                    self.right_arrow_label,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=1,
                tight=True,
                expand=True,
            )
        ]
