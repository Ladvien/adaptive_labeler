from pathlib import Path
import time
import flet as ft
from image_utils.image_noiser import ImageNoiser
from image_utils.noising_operation import NosingOperation
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
from rich import print

from adaptive_labeler.label_manager import LabelManager
from adaptive_labeler.noisy_image_maker import NoisyImageMaker
from adaptive_labeler.controls.image_viewer_panel import ImageViewerPanel
from adaptive_labeler.controls.labeling_controls import LabelingController
from adaptive_labeler.controls.review_controls import ReviewControls


class ImagePairControlView(ft.Column):
    def __init__(
        self,
        label_manager: LabelManager,
        color_scheme=None,
        start_mode="labeling",
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
        self.image_panel = ImageViewerPanel(
            original_image_name=self.noisy_image_maker.image_path.name,
            noisy_image_name=self.noisy_image_maker.image_path.name,
            original_image_base64=self.noisy_image_maker.image_path.load_as_base64(),
            noisy_image_base64=self.noisy_image_maker.noisy_base64(),
            color_scheme=self.color_scheme,
        )

        self.labeling_controls = LabelingController(
            self.label_manager,
            "labeling",
            color_scheme=self.color_scheme,
            severity_update_callback=self._on_slider_update,
            noisy_image_maker=self.noisy_image_maker,
        )

        # Visibility per mode
        self.labeling_controls.visible = self.mode == "labeling"

        self.expand = True
        self.controls = [
            self.image_panel,
            ft.Container(
                ft.Column(
                    [
                        self.labeling_controls,
                    ]
                ),
                padding=20,
                expand=1,
            ),
        ]

        # --- State ---
        self.shift_pressed = False
        self._last_action_time = 0.0
        self._debounce_interval = 0.3

        # Keyboard 🔥
        self._start_keyboard_listener()

    # ----------------------------------------------------
    # MODE TOGGLE

    def toggle_mode(self, e=None):
        self.mode = "review" if self.mode == "labeling" else "labeling"
        self.labeling_controls.visible = self.mode == "labeling"
        # self.review_controls.visible = self.mode == "review"
        self.update()

    # ----------------------------------------------------
    # SLIDER / NOISE HANDLING

    def _on_slider_update(self, e: ft.ControlEvent, fn_name: str, value: float):
        """Called when any slider changes."""
        self._resample_noisy_image()

    def _current_noising_operations(self) -> dict[str, NosingOperation]:
        """Collect thresholds from all sliders."""
        noising_ops: dict[str, NosingOperation] = {}
        for control in self.labeling_controls.threshold_sliders:
            if isinstance(control, ft.Slider):
                noising_ops[control.label] = NosingOperation.from_str(
                    control.label, control.value
                )

        return noising_ops

    def _resample_noisy_image(self):
        """Update the noisy image preview based on current thresholds."""
        updated_maker = NoisyImageMaker(
            self.noisy_image_maker.image_path,
            self.label_manager.config.output_dir,
            self._current_noising_operations(),
        )

        self.image_panel.update_images(
            original_image_name=updated_maker.image_path.name,
            noisy_image_name=updated_maker.image_path.name,
            original_image_base64=updated_maker.image_path.load_as_base64(),
            noisy_image_base64=updated_maker.noisy_base64(),
        )

    # ----------------------------------------------------
    # LABELING

    def _label_image(self):
        noisy_image_maker = self.label_manager.new_noisy_image_maker()

        self.label_manager.label_writer.record(noisy_image_maker)
        self._load_next_image()

    def _load_next_image(self):
        self.noisy_image_maker = self.label_manager.new_noisy_image_maker()
        self._resample_noisy_image()
        self.labeling_controls.update_progress()

    # ----------------------------------------------------
    # REVIEW HANDLING

    def _handle_review_keys(self, key: Key | KeyCode) -> bool:
        n = len(self.labeled_image_pairs)
        if n == 0:
            return False

        if key == Key.right:
            self._review_index = (self._review_index + 1) % n
        elif key == Key.left:
            self._review_index = (self._review_index - 1) % n
        else:
            return False

        pair = self.labeled_image_pairs[self._review_index]
        self.image_panel.update_images(
            pair.original_image_name,
            pair.noisy_image_name,
            pair.original_image_base64,
            pair.noisy_image_base64,
        )
        # self.review_controls.update_label(pair.threshold)  # Rework if needed
        return True

    # ----------------------------------------------------
    # KEYBOARD HANDLING

    def _can_act(self) -> bool:
        now = time.time()
        if now - self._last_action_time >= self._debounce_interval:
            self._last_action_time = now
            return True
        return False

    def _remove_label_image(self):
        self.label_manager.delete_last_label()
        self._load_next_image()

    def handle_keyboard_event(self, key: Key | KeyCode) -> bool:
        if not self._can_act():
            return False

        if key == Key.tab:
            self.toggle_mode()
            return True

        if self.mode == "labeling":
            if key == Key.right:
                self._label_image()
                return True
            elif key == Key.left:
                self._remove_label_image()
                return True
        else:
            return self._handle_review_keys(key)

        return False

    def _start_keyboard_listener(self):
        listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        listener.start()

    def _on_press(self, key):
        if key in (Key.shift, Key.shift_r):
            self.shift_pressed = True
        else:
            self.handle_keyboard_event(key)

    def _on_release(self, key):
        if key in (Key.shift, Key.shift_r):
            self.shift_pressed = False
