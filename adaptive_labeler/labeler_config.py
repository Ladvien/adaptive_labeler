from __future__ import annotations
import flet as ft
from dataclasses import dataclass

from labeling.label_manager_config import LabelManagerConfig


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
