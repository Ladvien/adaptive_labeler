import time
import flet as ft
from typing import Literal
from pynput.keyboard import Key, KeyCode

from adaptive_labeler.controls.image_pair_view import ImagePairViewer
from adaptive_labeler.controls.instructions import Instructions
from adaptive_labeler.controls.labeling_progress import LabelingProgress
from adaptive_labeler.controls.noise_control import NoiseControl
from adaptive_labeler.label_manager import LabelManager, LabeledImagePair


class ImagePairControlView(ft.Column):
    def __init__(
        self,
        label_manager: LabelManager,
        color_scheme: ft.ColorScheme | None = None,
        start_mode: Literal["labeling", "review"] = "labeling",
    ):
        super().__init__()

        self.label_manager = label_manager
        self.color_scheme = color_scheme or ft.ColorScheme()
        self.mode = start_mode

        # Common viewer
        self.unlabeled_pair = self.label_manager.new_unlabeled()
        self.image_pair_viewer = ImagePairViewer(self.unlabeled_pair, self.color_scheme)

        # Labeling mode controls
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

        # Review mode controls
        self.labeled_image_pairs = label_manager.get_labeled_image_pairs()
        self._review_index = 0
        self.label_name_text = ft.Text(
            self.labeled_image_pairs[0].label if self.labeled_image_pairs else "",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=self.color_scheme.secondary,
            text_align=ft.TextAlign.RIGHT,
        )

        # Toggle button
        self.mode_toggle = ft.ElevatedButton(
            text=(
                "Switch to Review" if self.mode == "labeling" else "Switch to Labeling"
            ),
            on_click=self.toggle_mode,
        )

        # --- Build static UI once ---
        self.labeling_area = ft.Row(
            [
                ft.Container(
                    Instructions(color_scheme=self.color_scheme),
                    padding=10,
                    expand=True,
                ),
                ft.Container(self.noise_control, padding=10, expand=True),
                ft.Container(self.progress_area, padding=10, expand=True),
                ft.Container(self.mode_toggle, padding=10),
            ],
            visible=self.mode == "labeling",
        )

        self.review_area = ft.Row(
            [
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(
                                "Label:", size=20, color=self.color_scheme.secondary
                            ),
                            self.label_name_text,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    expand=True,
                ),
                ft.Container(self.mode_toggle, padding=10),
            ],
            visible=self.mode == "review",
        )

        self.expand = True
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 0

        # Single layout — static, never rebuilt!
        self.controls = [
            ft.Container(
                self.image_pair_viewer,
                bgcolor=self.color_scheme.primary,
                padding=20,
                border_radius=12,
                expand=3,
            ),
            ft.Container(
                ft.Column([self.labeling_area, self.review_area]),
                padding=20,
                expand=1,
            ),
        ]

        self._last_action_time = 0.0
        self._debounce_interval = 0.3

    # --- Mode switching ---

    def toggle_mode(self, e):
        self.mode = "review" if self.mode == "labeling" else "labeling"
        self.labeling_area.visible = self.mode == "labeling"
        self.review_area.visible = self.mode == "review"
        self.mode_toggle.text = (
            "Switch to Review" if self.mode == "labeling" else "Switch to Labeling"
        )

        # IMPORTANT: Refresh labeled images in case new ones were added
        self.labeled_image_pairs = self.label_manager.get_labeled_image_pairs()

        if self.mode == "labeling":
            # Don't grab new unlabeled — just refresh current image and progress bar
            self.image_pair_viewer.update_images(self.unlabeled_pair)
            self.progress_area.update_progress(
                value=self.label_manager.percentage_complete(),
                progress_text=f"{self.label_manager.labeled_count()}/{self.label_manager.total()} labeled",
            )
        else:
            # Clamp review index to avoid out-of-bounds
            if self._review_index >= len(self.labeled_image_pairs):
                self._review_index = max(0, len(self.labeled_image_pairs) - 1)
            self.update_review_image()

        self.update()

    # --- Labeling mode updates ---

    def update_labeling_image(self):
        self.unlabeled_pair = self.label_manager.new_unlabeled()
        self.image_pair_viewer.update_images(self.unlabeled_pair)
        self.progress_area.update_progress(
            value=self.label_manager.percentage_complete(),
            progress_text=f"{self.label_manager.labeled_count()}/{self.label_manager.total()} labeled",
        )

    def _label_image(self, label: str):
        labeled_pair = self.unlabeled_pair.label(label)
        self.label_manager.save_label(labeled_pair)
        self.update_labeling_image()

    def _resample_images(self):
        self.unlabeled_pair = self.label_manager.resample_images(self.unlabeled_pair)
        self.image_pair_viewer.update_images(self.unlabeled_pair)

    # --- Review mode updates ---

    def update_review_image(self):
        if not self.labeled_image_pairs:
            return
        pair = self.labeled_image_pairs[
            self._review_index % len(self.labeled_image_pairs)
        ]
        self.image_pair_viewer.update_images(pair)
        self.label_name_text.value = pair.label
        self.label_name_text.update()

    # --- Key handling ---

    def _can_act(self) -> bool:
        now = time.time()
        if now - self._last_action_time >= self._debounce_interval:
            self._last_action_time = now
            return True
        return False

    def handle_keyboard_event(self, key: Key | KeyCode) -> bool:
        if not isinstance(key, Key):
            return False
        if not self._can_act():
            return False

        if self.mode == "labeling":
            return self._handle_labeling_keys(key)
        else:
            return self._handle_review_keys(key)

    def _handle_labeling_keys(self, key: Key | KeyCode) -> bool:
        if key.name == "right":
            self._label_image("acceptable")
            return True
        elif key.name == "left":
            self._label_image("unacceptable")
            return True
        elif key.name == "space":
            self._resample_images()
            return True
        return False

    def _handle_review_keys(self, key: Key | KeyCode) -> bool:
        n = len(self.labeled_image_pairs)
        if n == 0:
            return False

        if key.name == "right":
            self._review_index = (self._review_index + 1) % n
            self.update_review_image()
            return True

        elif key.name == "left":
            self._review_index = (self._review_index - 1) % n
            self.update_review_image()
            return True

        return False

    # --- Noise control callbacks ---

    def on_slider_update(self, e, start_value, end_value):
        self.label_manager.set_severity_level(start_value, end_value)
        self._resample_images()

    def on_resample_click(self, e, start_value, end_value):
        self._resample_images()
