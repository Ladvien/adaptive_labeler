from adaptive_labeler.label_manager import NoisyImageMaker
import flet as ft

from adaptive_labeler.controls.image_pair_view import ImagePairViewer


class ImageViewerPanel(ft.Container):

    def __init__(
        self,
        original_image_name: str,
        noisy_image_name: str,
        original_image_base64: str,
        noisy_image_base64: str,
        color_scheme: ft.ColorScheme | None = None,
    ):
        super().__init__()
        self.viewer = ImagePairViewer(
            original_image_name,
            noisy_image_name,
            original_image_base64,
            noisy_image_base64,
            color_scheme,
        )
        self.content = self.viewer
        self.bgcolor = color_scheme.primary
        self.padding = 20
        self.border_radius = 12
        self.expand = 3

    def update_images(
        self,
        original_image_name: str,
        noisy_image_name: str,
        original_image_base64: str,
        noisy_image_base64: str,
    ):
        self.viewer.update_images(
            original_image_name,
            noisy_image_name,
            original_image_base64,
            noisy_image_base64,
        )
