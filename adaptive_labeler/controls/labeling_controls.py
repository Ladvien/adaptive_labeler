from typing import Callable, Literal, Optional
from adaptive_labeler.controls.instructions import Instructions
from adaptive_labeler.controls.labeling_progress import LabelingProgress
from adaptive_labeler.controls.noise_control import NoiseControl
from adaptive_labeler.label_manager import LabelManager
from adaptive_labeler.noisy_image_maker import NoisyImageMaker
import flet as ft
from image_utils.noising_operation import NosingOperation


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

        self.threshold_sliders = []

        # 🔥 If no image passed in, don't build sliders
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

        # --- Layout ---
        self.controls = [
            ft.Container(
                Instructions(color_scheme=self.color_scheme), padding=10, expand=True
            ),
            ft.Column(self.threshold_sliders, expand=True),
            ft.Container(self.progress_area, padding=10, expand=True),
        ]

    def update_progress(self):
        self.progress_area.update_progress(
            value=self.label_manager.percentage_complete(),
            progress_text=f"{self.label_manager.labeled_count()}/{self.label_manager.total()} labeled",
        )

    def get_noising_operations(self) -> dict[str, NosingOperation]:
        noising_ops: dict[str, NosingOperation] = {}
        for control in self.threshold_sliders:
            if isinstance(control, NoiseControl):
                noising_ops[control.label] = NosingOperation.from_str(
                    control.label, int(control.slider.value)
                )

        return noising_ops
