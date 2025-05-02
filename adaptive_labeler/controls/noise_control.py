from typing import Callable
import flet as ft


class NoiseControl(ft.Column):
    def __init__(
        self,
        initial_value: float = 1.0,
        min_val: float = 0.0,
        max_val: float = 1.0,
        step: float = 0.001,
        on_end_change: Callable = None,
        color_scheme: ft.ColorScheme | None = None,
    ):
        super().__init__()

        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.on_change_end = on_end_change

        self.color_scheme = color_scheme or ft.ColorScheme(
            primary="#7F00FF",
            on_primary="#FFFFFF",
            on_surface="#FFFFFF",
            on_background="#CCCCCC",
        )

        # Value label
        self.value_label = ft.Text(
            f"Noise Level: {round(initial_value * 100, 2)}%",
            text_align=ft.TextAlign.CENTER,
        )

        self.slider = ft.Slider(
            min=self.min_val,
            max=self.max_val,
            value=self._quantize(initial_value),
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

        self.spacing = 5
        self.alignment = ft.MainAxisAlignment.CENTER

    def _clamp(self, value: float) -> float:
        return min(max(value, self.min_val), self.max_val)

    def _quantize(self, value: float) -> float:
        """Snap the value to the nearest multiple of the step."""
        value = self._clamp(value)
        steps = round((value - self.min_val) / self.step)
        return round(self.min_val + steps * self.step, 6)

    def _on_slider_change(self, e: ft.ControlEvent):
        """Update label as the slider moves and quantize the value."""
        quantized_value = self._quantize(self.slider.value)
        if quantized_value != self.slider.value:
            self.slider.value = quantized_value
            self.slider.update()
        self.value_label.value = f"Noise Level: {round(quantized_value * 100, 2)}%"
        self.value_label.update()

    @property
    def value(self) -> float:
        """Current noise value."""
        return self._quantize(self.slider.value)

    @value.setter
    def value(self, new_value: float):
        quantized = self._quantize(new_value)
        self.slider.value = quantized
        self.slider.update()
        self._on_slider_change(None)

    def _on_end_change(self, e: ft.ControlEvent):
        if self.on_change_end:
            self.on_change_end(e, self.value)  # Use quantized value!
