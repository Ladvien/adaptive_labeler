from typing import Callable, Optional
import flet as ft


class NoiseControl(ft.Column):
    DEFAULT_COLOR_SCHEME = ft.ColorScheme(
        primary="#7F00FF",
        on_primary="#FFFFFF",
        on_surface="#FFFFFF",
        on_background="#CCCCCC",
    )

    def __init__(
        self,
        label: str,
        value: float = 1.0,
        min_val: float = 0.0,
        max_val: float = 1.0,
        step: float = 0.001,
        default_value: float = 0.7,
        on_end_change: Optional[Callable] = None,
        color_scheme: Optional[ft.ColorScheme] = None,
    ):
        super().__init__()
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.default_value = default_value
        self.on_change_end = on_end_change
        self.color_scheme = color_scheme or self.DEFAULT_COLOR_SCHEME

        self.value_label = ft.Text(
            self._format_label(value),
            size=12,
            text_align=ft.TextAlign.CENTER,
        )

        self.slider = ft.Slider(
            label=self.label,
            min=self.min_val,
            max=self.max_val,
            value=self._quantize(value),
            divisions=int((max_val - min_val) / step) if step else None,
            round=3,
            on_change=self._on_slider_change,
            on_change_end=self._on_end_change,
            expand=True,
        )

        self.controls = [
            self.value_label,
            self.slider,
        ]
        self.spacing = 2
        self.alignment = ft.MainAxisAlignment.CENTER
        self.value = value

    def _format_label(self, value: float) -> str:
        return f"{self.label}: {round(value * 100, 2)}%"

    def _clamp(self, value: float) -> float:
        return min(max(value, self.min_val), self.max_val)

    def _quantize(self, value: float) -> float:
        if self.step <= 0:
            raise ValueError("Step must be > 0")
        value = self._clamp(value)
        steps = round((value - self.min_val) / self.step)
        return round(self.min_val + steps * self.step, 6)

    def update_display(self):
        """Update both the slider and label to reflect the current value."""
        quantized_value = self._quantize(self.slider.value)
        self.slider.value = quantized_value
        self.value_label.value = self._format_label(quantized_value)
        self.slider.update()
        self.value_label.update()

        if self.on_change_end:
            self.on_change_end(None, self.label, quantized_value)

    # --- Event handlers ---

    def _on_slider_change(self, e: ft.ControlEvent):
        self.update_display()

    def _on_end_change(self, e: ft.ControlEvent):
        if self.on_change_end:
            self.on_change_end(e, self.label, self.slider.value)

    # --- Public API ---
