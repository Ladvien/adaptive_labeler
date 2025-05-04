from typing import Callable, Literal, Optional
from adaptive_labeler.controls.instructions import Instructions
from adaptive_labeler.controls.labeling_progress import LabelingProgress
from adaptive_labeler.controls.noise_control import NoiseControl
from adaptive_labeler.label_manager import LabelManager
import flet as ft


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
    ):
        super().__init__()

        self.color_scheme = color_scheme or self.DEFAULT_COLOR_SCHEME
        self.label_manager = label_manager
        initial_value = label_manager.get_severity()

        self.noise_control = NoiseControl(
            initial_value,
            on_end_change=severity_update_callback,
            color_scheme=self.color_scheme,
        )

        self.progress_area = LabelingProgress(
            value=label_manager.percentage_complete(),
            progress_text=f"{label_manager.labeled_count()}/{label_manager.total()} labeled",
            color_scheme=self.color_scheme,
        )

        # Placeholder: uncomment when mode toggle is ready
        # self.mode_toggle = ft.ElevatedButton(
        #     text="Switch to Review",
        #     on_click=on_mode_toggle,
        # )

        self.controls = [
            ft.Container(
                Instructions(color_scheme=self.color_scheme), padding=10, expand=True
            ),
            ft.Container(self.noise_control, padding=10, expand=True),
            ft.Container(self.progress_area, padding=10, expand=True),
            # ft.Container(self.mode_toggle, padding=10),
        ]

    def update_progress(self):
        self.progress_area.update_progress(
            value=self.label_manager.percentage_complete(),
            progress_text=f"{self.label_manager.labeled_count()}/{self.label_manager.total()} labeled",
        )
