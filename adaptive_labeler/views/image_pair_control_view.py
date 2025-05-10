import time
import random
import threading
import flet as ft
from pynput.keyboard import Key, KeyCode
from rich import print

from image_utils.noising_operation import NosingOperation
from image_utils.noisy_image_maker import NoisyImageMaker
from labeling.label_manager import LabelManager

from adaptive_labeler.controls.image_viewer_panel import ImageViewerPanel
from adaptive_labeler.controls.labeling_controls import LabelingController


class ImagePairControlView(ft.Column):
    DEBOUNCE_INTERVAL = 0.3
    MASTER_STEP = 0.01

    def __init__(
        self, label_manager: LabelManager, color_scheme=None, start_mode="labeling"
    ):
        super().__init__()

        self.label_manager = label_manager
        self.color_scheme = color_scheme or ft.ColorScheme()
        self.mode = start_mode

        # --- Data ---
        self.noisy_image_maker = self.label_manager.new_noisy_image_maker()
        self.labeled_image_pairs = self.label_manager.retrieve_records()
        self._review_index = 0

        # --- UI Controls ---
        self.image_panel = self._build_image_panel()
        self.labeling_controls = self._build_labeling_controls()
        self.feedback_overlay = ft.Container(
            bgcolor=ft.colors.GREEN_400, opacity=0.0, expand=1
        )

        self.expand = True
        self.controls = [
            self.image_panel,
            ft.Container(self.labeling_controls, padding=20, expand=5),
            self.feedback_overlay,
        ]

        # --- State ---
        self.shift_pressed = False
        self._last_action_time = 0.0

    def _build_image_panel(self) -> ImageViewerPanel:
        return ImageViewerPanel(
            original_image_name=self.noisy_image_maker.image_path.name,
            noisy_image_name=self.noisy_image_maker.image_path.name,
            original_image_base64=self.noisy_image_maker.image_path.load_as_base64(),
            noisy_image_base64=self.noisy_image_maker.noisy_base64(),
            color_scheme=self.color_scheme,
        )

    def _build_labeling_controls(self) -> LabelingController:
        controller = LabelingController(
            self.label_manager,
            "labeling",
            color_scheme=self.color_scheme,
            severity_update_callback=self._on_slider_update,
            noisy_image_maker=self.noisy_image_maker,
        )
        controller.visible = self.mode == "labeling"
        return controller

    def toggle_mode(self, e=None):
        self.mode = "review" if self.mode == "labeling" else "labeling"
        self.labeling_controls.visible = self.mode == "labeling"
        self.update()

    def _on_slider_update(self, e: ft.ControlEvent, fn_name: str, value: float):
        self._resample_noisy_image()

    def _resample_noisy_image(self):
        print(self.noisy_image_maker)
        self.labeling_controls.update_severity(self.noisy_image_maker)
        print(self.noisy_image_maker)

        self.image_panel.update_images(
            original_image_name=self.noisy_image_maker.image_path.name,
            noisy_image_name=self.noisy_image_maker.image_path.name,
            original_image_base64=self.noisy_image_maker.image_path.load_as_base64(),
            noisy_image_base64=self.noisy_image_maker.noisy_base64(),
        )

    def _label_image(self, label: str) -> None:
        self.label_manager.label_writer.record(self.noisy_image_maker, label)
        self._show_feedback(
            color=ft.colors.GREEN_400 if label == "acceptable" else ft.colors.RED_400
        )
        self.labeling_controls.update_progress()

    def _remove_label_image(self):
        self.label_manager.delete_last_label()
        self._load_next_image()

    def _load_next_image(self):
        self.noisy_image_maker = self.label_manager.new_noisy_image_maker()
        self.labeling_controls.noisy_image_maker = self.noisy_image_maker

        # Reset master slider value
        self.labeling_controls.master_slider.set_value(0.0)

        # Update all sliders to reflect new value
        self.labeling_controls.distribute_master_severity(master_value=0.0)

        # Update images and UI
        self._resample_noisy_image()
        self.labeling_controls.update_progress()

    def _review_step(self, direction: int):
        n = len(self.labeled_image_pairs)
        if n == 0:
            return
        self._review_index = (self._review_index + direction) % n
        pair = self.labeled_image_pairs[self._review_index]
        self.image_panel.update_images(
            pair.original_image_name,
            pair.noisy_image_name,
            pair.original_image_base64,
            pair.noisy_image_base64,
        )
        self.update()

    def _can_act(self) -> bool:
        now = time.time()
        if now - self._last_action_time >= self.DEBOUNCE_INTERVAL:
            self._last_action_time = now
            return True
        return False

    def _increment_master_slider(self, increment: float):
        master = self.labeling_controls.master_slider
        new_value = min(
            max(master.slider.value + increment, master.min_val), master.max_val
        )
        master.set_value(new_value)
        self.labeling_controls.distribute_master_severity(master_value=new_value)
        self._resample_noisy_image()

    def _show_feedback(self, color: str = ft.colors.GREEN_400, duration: float = 0.2):
        self.feedback_overlay.bgcolor = color
        self.feedback_overlay.opacity = 0.5
        self.update()

        def hide_overlay():
            time.sleep(duration)
            self.feedback_overlay.opacity = 0.0
            self.update()

        threading.Thread(target=hide_overlay, daemon=True).start()

    def handle_keyboard_event(self, key: Key | KeyCode) -> bool:
        if not self._can_act():
            return False

        match key:
            case Key.space:
                increment = round(random.uniform(0.0, 0.2), 3)
                self._increment_master_slider(increment)
                return True
            # case Key.right:
            #     self._label_image("acceptable")
            #     return True
            # case Key.left:
            #     self._label_image("unacceptable")
            #     return True
            case Key.up:
                self._increment_master_slider(self.MASTER_STEP)
                return True
            case Key.down:
                self._increment_master_slider(-self.MASTER_STEP)
                return True
            case Key.tab:
                self._load_next_image()
                self.labeling_controls.master_slider.set_value(0.0)
                self.labeling_controls.master_slider.update()
                self.labeling_controls.update()
                return True
            case k if isinstance(k, KeyCode) and k.char == "d":
                self._label_image("acceptable")
                return True
            case k if isinstance(k, KeyCode) and k.char == "a":
                self._label_image("unacceptable")
                return True
            case _:
                return False
