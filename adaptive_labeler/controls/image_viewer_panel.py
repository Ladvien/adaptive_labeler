from adaptive_labeler.label_manager import NoisyImageMaker
import flet as ft

from adaptive_labeler.controls.image_pair_view import ImagePairViewer


class ImageViewerPanel(ft.Container):
    def __init__(self, image_pair, color_scheme):
        super().__init__()
        self.viewer = ImagePairViewer(image_pair, color_scheme)
        self.content = self.viewer
        self.bgcolor = color_scheme.primary
        self.padding = 20
        self.border_radius = 12
        self.expand = 3

    def update_images(self, unlabeled_image: NoisyImageMaker, severity: float):
        self.viewer.update_images(unlabeled_image.image_path)
        self.image_control.update()
