from typing import Callable, Literal, Optional
import random
import flet as ft
from image_utils.noising_operation import NosingOperation
from image_utils.noisy_image_maker import NoisyImageMaker
from labeling.label_manager import LabelManager

from adaptive_labeler.controls.instructions import Instructions
from adaptive_labeler.controls.labeling_progress import LabelingProgress
from adaptive_labeler.controls.noise_control import NoiseControl


class LabelingController(ft.Row):
    DEFAULT_COLOR_SCHEME = ft.ColorScheme(
        primary="#7F00FF",
        on_primary="#FFFFFF",
        on_surface="#FFFFFF",
        on_background="#CCCCCC",
        surface="#1A1A2E",
    )

    def __init__(
        self,
        label_manager: LabelManager,
        mode: Literal["labeling", "review"] = "labeling",
        color_scheme: Optional[ft.ColorScheme] = None,
        severity_update_callback: Optional[Callable] = None,
        noisy_image_maker: Optional[NoisyImageMaker] = None,  # 🔥 IMPORTANT
    ):
        super().__init__()

        self.color_scheme = color_scheme or self.DEFAULT_COLOR_SCHEME
        self.label_manager = label_manager
        self.mode = mode
        self.noisy_image_maker = noisy_image_maker
        self.severity_update_callback = severity_update_callback
        self.default_master_noise_value = 0.4
        self.threshold_sliders: list[NoiseControl] = []

        # --- Per-noise sliders ---
        if self.noisy_image_maker:
            for noise_op in self.noisy_image_maker.noise_operations:
                noise_name = noise_op.name
                value = noise_op.severity or 0.0

                slider = NoiseControl(
                    label=noise_name,
                    value=value,
                    color_scheme=self.color_scheme,
                    on_end_change=severity_update_callback,
                )
                self.threshold_sliders.append(slider)

        # --- Progress ---
        self.progress_area = LabelingProgress(
            value=label_manager.percentage_complete(),
            progress_text=f"{label_manager.labeled_count()}/{label_manager.total()} labeled",
            color_scheme=self.color_scheme,
        )

        # --- Master slider ---
        self.master_slider = NoiseControl(
            label="Master Control",
            value=self.default_master_noise_value,
            color_scheme=self.color_scheme,
            on_end_change=self._on_master_slider_change,
        )

        # --- Layout ---
        self.controls = [
            ft.Row(
                controls=[
                    Instructions(color_scheme=self.color_scheme),
                    self.master_slider,
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                expand=3,
            ),
            ft.Row(
                controls=[
                    ft.ListView(self.threshold_sliders, expand=True),
                    ft.Container(self.progress_area, padding=10, expand=True),
                ],
                expand=2,
            ),
        ]

    # ----------------------------------------------------------------------
    # Master slider logic

    def _on_master_slider_change(self, e, label, value):
        """When master slider changes, distribute its value randomly."""
        self.distribute_master_severity(value)

        # If caller provided a callback, trigger update (e.g., resample image)
        if self.severity_update_callback:
            self.severity_update_callback(e, label, value)

    def distribute_master_severity(self, master_value: Optional[float] = None):
        """
        Distribute severity from the master slider across all threshold sliders.

        If master_value is None, uses the current master slider value.
        """
        total = (
            master_value
            if master_value is not None
            else self.master_slider.slider.value
        )

        num_sliders = len(self.threshold_sliders)
        if num_sliders == 0 or total <= 0:
            for slider in self.threshold_sliders:
                slider.set_value(0.0)
            return

        # --- Random weights ---
        weights = [random.random() for _ in range(num_sliders)]
        total_weight = sum(weights)
        proportions = [w / total_weight for w in weights]

        # --- Assign severities ---
        for slider, proportion in zip(self.threshold_sliders, proportions):
            slider_value = round(total * proportion, 3)
            slider.set_value(slider_value)

    def did_mount(self):
        # Now that the controls are attached, we can safely update them
        self.distribute_master_severity(master_value=self.default_master_noise_value)

    # ----------------------------------------------------------------------
    # Progress bar

    def update_progress(self):
        self.progress_area.update_progress(
            value=self.label_manager.percentage_complete(),
            progress_text=f"{self.label_manager.labeled_count()}/{self.label_manager.total()} labeled",
        )

    # ----------------------------------------------------------------------
    # Extract current slider values

    def get_noising_operations(self) -> dict[str, NosingOperation]:
        noising_ops: dict[str, NosingOperation] = {}
        for noise_control in self.threshold_sliders:
            if isinstance(noise_control, NoiseControl):
                noising_ops[noise_control.label] = NosingOperation.from_str(
                    noise_control.label, float(noise_control.slider.value)
                )
        return noising_ops
