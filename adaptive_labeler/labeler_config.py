from __future__ import annotations
from adaptive_labeler.label_manager_config import LabelManagerConfig
import flet as ft
from dataclasses import dataclass


@dataclass
class LabelerConfig:
    title: str = "Binary Image Labeler"
    window_width: int = 800
    window_height: int = 700
    window_resizable: bool = True
    theme_mode: ft.ThemeMode = ft.ThemeMode.DARK

    # ImageLoaderConfig
    label_manager_config: LabelManagerConfig | None = None

    key_press_debounce_delay: float = 0.01

    def __post_init__(self):
        if self.label_manager_config is None:
            self.label_manager_config = LabelManagerConfig(
                severity_defaults={
                    "add_jpeg_compression": 0.3,
                    "add_gaussian_noise": 0.1,
                },
            )
