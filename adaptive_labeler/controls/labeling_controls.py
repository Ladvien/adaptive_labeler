from adaptive_labeler.controls.instructions import Instructions
from adaptive_labeler.controls.labeling_progress import LabelingProgress
from adaptive_labeler.controls.noise_control import NoiseControl
import flet as ft


class LabelingControls(ft.Row):
    def __init__(
        self,
        label_manager,
        color_scheme,
        on_mode_toggle,
        on_slider_update,
        on_resample_click,
    ):
        super().__init__()
        self.color_scheme = color_scheme
        self.label_manager = label_manager
        self.noise_control = NoiseControl(
            on_end_change=on_slider_update,
            on_resample_click=on_resample_click,
            color_scheme=color_scheme,
        )
        self.progress_area = LabelingProgress(
            value=label_manager.percentage_complete(),
            progress_text=f"{label_manager.labeled_count()}/{label_manager.total()} labeled",
            color_scheme=color_scheme,
        )
        self.mode_toggle = ft.ElevatedButton(
            text="Switch to Review",
            on_click=on_mode_toggle,
        )

        self.controls = [
            ft.Container(
                Instructions(color_scheme=color_scheme), padding=10, expand=True
            ),
            ft.Container(self.noise_control, padding=10, expand=True),
            ft.Container(self.progress_area, padding=10, expand=True),
            ft.Container(self.mode_toggle, padding=10),
        ]

    def update_progress(self):
        self.progress_area.update_progress(
            value=self.label_manager.percentage_complete(),
            progress_text=f"{self.label_manager.labeled_count()}/{self.label_manager.total()} labeled",
        )
