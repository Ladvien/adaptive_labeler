import time
import flet as ft
from pynput.keyboard import Key, KeyCode

from adaptive_labeler.controls.image_pair_view import (
    ImagePairViewer,
)
from adaptive_labeler.controls.instructions import Instructions
from adaptive_labeler.controls.labeling_progress import (
    LabelingProgress,
)
from adaptive_labeler.controls.noise_control import (
    NoiseControl,
)
from adaptive_labeler.label_manager import LabelManager


class ImageLabelerControlView(ft.Column):
    def __init__(
        self,
        label_manager: LabelManager,
        color_scheme: ft.ColorScheme | None = None,
    ):
        super().__init__()

        self.label_manager = label_manager
        self.color_scheme = color_scheme or ft.ColorScheme()

        self.unlabeled_pair = self.label_manager.new_unlabeled()
        self.image_pair_viewer = ImagePairViewer(
            self.unlabeled_pair,
            color_scheme,
        )

        self.expand = True
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 0

        self.noise_control = NoiseControl(
            on_end_change=self.on_slider_update,
            on_resample_click=self.on_resample_click,
            color_scheme=self.color_scheme,
        )
        self.progress_area = LabelingProgress(
            value=self.label_manager.percentage_complete(),
            progress_text=f"{self.label_manager.labeled_count()}/{self.label_manager.total()} labeled",
            color_scheme=self.color_scheme,
        )

        self.controls = [
            ft.Container(
                content=self.image_pair_viewer,
                bgcolor=self.color_scheme.primary,
                padding=20,
                border_radius=12,
                expand=3,  # Top: 3/4 screen
            ),
            ft.Container(
                content=ft.Row(
                    [
                        # 3/4 of width: Instructions + Slider
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Container(
                                        content=Instructions(
                                            color_scheme=self.color_scheme
                                        ),
                                        padding=10,
                                        expand=True,
                                        alignment=ft.alignment.center_left,
                                    ),
                                    ft.Container(
                                        content=self.noise_control,
                                        padding=10,
                                        border_radius=10,
                                        expand=True,
                                        alignment=ft.alignment.center_right,
                                    ),
                                    ft.Container(
                                        content=self.progress_area,
                                        padding=10,
                                        border_radius=10,
                                        expand=True,
                                        alignment=ft.alignment.center_right,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            expand=3,  # 3/4 width
                        ),
                    ],
                    expand=True,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=20,
                expand=1,  # Bottom: 1/4 screen
            ),
        ]

        # --- Debounce Timer
        self._last_label_time = 0.0
        self._debounce_interval = 0.5

    def on_mount(self):
        self.update_content()

    def update_content(self) -> None:
        self.unlabeled_pair = self.label_manager.new_unlabeled()
        self.image_pair_viewer.update_images(self.unlabeled_pair)
        self.progress_area.update_progress(
            value=self.label_manager.percentage_complete(),
            progress_text=f"{self.label_manager.labeled_count()}/{self.label_manager.total()} labeled",
        )

    def __label_image(self, label: str) -> None:
        labeled_pair = self.unlabeled_pair.label(label)
        self.label_manager.save_label(labeled_pair)
        self.update_content()

    def __can_label(self) -> bool:
        now = time.time()
        if now - self._last_label_time >= self._debounce_interval:
            self._last_label_time = now
            return True
        return False

    def handle_keyboard_event(self, key: Key | KeyCode) -> bool:
        if not isinstance(key, Key):
            return False

        if key.name in ("right", "left") and self.__can_label():
            self.__label_image("acceptable" if key.name == "right" else "unacceptable")
            return True

        elif key.name == "space" and self.__can_label():
            self.__resample_images()
            return True

        return False

    def on_slider_update(
        self, event: ft.ControlEvent, start_value: float, end_value: float
    ):
        self.label_manager.set_severity_level(start_value, end_value)
        self.__resample_images()

    def on_resample_click(
        self,
        event: ft.ControlEvent,
        start_value: float,
        end_value: float,
    ):
        self.__resample_images()

    def __resample_images(self) -> None:
        self.unlabeled_pair = self.label_manager.resample_images(self.unlabeled_pair)
        self.image_pair_viewer.update_images(self.unlabeled_pair)
