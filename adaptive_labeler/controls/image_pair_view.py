import flet as ft
from adaptive_labeler.controls.image_with_label import (
    ImageWithLabel,
)


class ImagePairViewer(ft.Container):
    def __init__(
        self,
        original_image_name: str,
        noisy_image_name: str,
        original_image_base64: str,
        noisy_image_base64: str,
        color_scheme: ft.ColorScheme | None = None,
    ):
        super().__init__()

        # Use injected theme or fallback
        self.color_scheme = color_scheme or ft.ColorScheme(
            background="#1A002B",
            surface="#1A1A2E",
            on_surface="#FFFFFF",
        )

        # Create image cards
        self.original = ImageWithLabel(
            "Original",
            original_image_name,
            original_image_base64,
            color_scheme,
        )
        self.noisy = ImageWithLabel(
            "Noisy",
            noisy_image_name,
            noisy_image_base64,
            color_scheme,
        )

        # Layout
        self.content = ft.Column(
            [
                ft.Row(
                    [self.original, self.noisy],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    expand=True,
                )
            ],
            spacing=20,
            expand=True,
        )

        # Styling from theme
        self.bgcolor = self.color_scheme.surface
        self.border_radius = 16
        self.padding = ft.padding.all(20)
        self.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color="#00000080",
            offset=ft.Offset(0, 4),
        )
        self.expand = True

    def update_images(
        self,
        original_image_name: str,
        noisy_image_name: str,
        original_image_base64: str,
        noisy_image_base64: str,
    ) -> None:
        self.original.update_images(original_image_name, original_image_base64)
        self.noisy.update_images(noisy_image_name, noisy_image_base64)

        self.update()
