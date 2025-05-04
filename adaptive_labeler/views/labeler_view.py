import time
from adaptive_labeler.controls.image_viewer_panel import ImageViewerPanel
from adaptive_labeler.controls.labeling_controls import LabelingControls
from adaptive_labeler.controls.review_controls import ReviewControls
import flet as ft
from typing import Literal
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

from adaptive_labeler.label_manager import LabelManager


class ImagePairControlView(ft.Column):
    def __init__(
        self,
        label_manager: LabelManager,
        color_scheme=None,
        start_mode="labeling",
        minimum_slider_value=0.01,
    ):
        super().__init__()
        self.label_manager = label_manager
        self.color_scheme = color_scheme or ft.ColorScheme()
        self.mode = start_mode
        self.minimum_slider_value = minimum_slider_value

        # Data
        self.unlabeled_pair = label_manager.new_unlabeled()
        self.labeled_image_pairs = label_manager.get_labeled_image_pairs()
        self._review_index = 0

        # Controls
        self.image_panel = ImageViewerPanel(self.unlabeled_pair, self.color_scheme)
        self.labeling_controls = LabelingControls(
            label_manager,
            self.color_scheme,
            self.toggle_mode,
            self.on_slider_update,
        )
        self.review_controls = ReviewControls(
            self.labeled_image_pairs,
            self.color_scheme,
            self.toggle_mode,
        )

        self.labeling_controls.visible = self.mode == "labeling"
        self.review_controls.visible = self.mode == "review"

        self.expand = True
        self.controls = [
            self.image_panel,
            ft.Container(
                ft.Column([self.labeling_controls, self.review_controls]),
                padding=20,
                expand=1,
            ),
        ]

        # Key state
        self.shift_pressed = False

        # Key debounce
        self._last_action_time = 0.0
        self._debounce_interval = 0.3

        # Start listener 🔥
        self._start_keyboard_listener()

    # ---------- Mode switching ----------
    def toggle_mode(self, e=None):
        self.mode = "review" if self.mode == "labeling" else "labeling"
        self.labeling_controls.visible = self.mode == "labeling"
        self.review_controls.visible = self.mode == "review"
        self.update()

    # ---------- Slider/Noise Callbacks ----------
    def on_slider_update(self, e, value):
        self.label_manager.set_severity(value)
        self._resample_images()

    # ---------- Noise adjustment ----------
    def increase_noise(self, shift: bool = False):
        severity = self.label_manager.get_severity()
        increment = 0.05 if shift else 0.01
        new_value = min(severity + increment, 1.0)
        self.label_manager.set_severity(new_value)
        self.labeling_controls.noise_control.value = new_value
        self._resample_images()

    def decrease_noise(self, shift: bool = False):
        severity = self.label_manager.get_severity()
        decrement = 0.05 if shift else 0.01
        new_value = max(severity - decrement, self.minimum_slider_value)
        self.label_manager.set_severity(new_value)
        self.labeling_controls.noise_control.value = new_value
        self._resample_images()

    # ---------- Image Updates ----------
    def _label_image(self, label: str):
        labeled_pair = self.unlabeled_pair.create_labeled(label)
        self.label_manager.save_label(labeled_pair)
        self.unlabeled_pair = self.label_manager.new_unlabeled()

        self.image_panel.update_images(self.unlabeled_pair)
        self.labeling_controls.update_progress()

    def _resample_images(self):
        self.image_panel.update_images(self.unlabeled_pair.noisy_base64())

    # ---------- Keyboard Handling ----------
    def _can_act(self) -> bool:
        now = time.time()
        if now - self._last_action_time >= self._debounce_interval:
            self._last_action_time = now
            return True
        return False

    def handle_keyboard_event(self, key: Key | KeyCode) -> bool:
        if not self._can_act():
            return False

        if key == Key.tab:
            self.toggle_mode()
            return True

        if self.mode == "labeling":
            return self._handle_labeling_keys(key)
        else:
            return self._handle_review_keys(key)

    def _handle_labeling_keys(self, key: Key | KeyCode) -> bool:
        if key == Key.right:
            self._label_image(self.label_manager.get_severity())
            return True
        elif key == Key.left:
            self._label_image(self.label_manager.get_severity())
            return True
        elif key == Key.up:
            print("Shift pressed?", self.shift_pressed)  # Debug!
            self.increase_noise(shift=self.shift_pressed)
            return True
        elif key == Key.down:
            self.decrease_noise(shift=self.shift_pressed)
            return True
        return False

    def _handle_review_keys(self, key: Key | KeyCode) -> bool:
        n = len(self.labeled_image_pairs)
        if n == 0:
            return False

        if key == Key.right:
            self._review_index = (self._review_index + 1) % n
            self._update_review_image()
            return True
        elif key == Key.left:
            self._review_index = (self._review_index - 1) % n
            self._update_review_image()
            return True
        return False

    def _update_review_image(self):
        pair = self.labeled_image_pairs[self._review_index]
        self.image_panel.update_images(pair)
        self.review_controls.update_label(pair.degradation_point)

    # ---------- Key listener methods ----------
    def _start_keyboard_listener(self):
        listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        listener.start()

    def _on_press(self, key):
        if key in (Key.shift, Key.shift_r):
            self.shift_pressed = True
        else:
            # Forward other keys to handler
            self.handle_keyboard_event(key)

    def _on_release(self, key):
        if key in (Key.shift, Key.shift_r):
            self.shift_pressed = False
