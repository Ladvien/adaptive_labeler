from typing import Callable, Optional
import flet as ft
import threading
import time


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
        debounce_seconds: float = 0.2,
    ):
        super().__init__()
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.default_value = default_value
        self.color_scheme = color_scheme or self.DEFAULT_COLOR_SCHEME

        self.value_label = ft.Text(
            self._format_label(value),
            text_align=ft.TextAlign.CENTER,
        )

        self.slider = ft.Slider(
            label=self.label,
            min=self.min_val,
            max=self.max_val,
            value=value,
            divisions=int((max_val - min_val) / step) if step else None,
            round=3,
            on_change=self._on_slider_change,
        )

        self.controls = [self.value_label, self.slider]
        self.spacing = 5
        self.alignment = ft.MainAxisAlignment.CENTER

        self._debounce_seconds = debounce_seconds
        self._last_invoked = 0.0
        self._debounce_timer = None

        self._external_callback = on_end_change

    def _format_label(self, value: float) -> str:
        return f"{self.label}: {round(value * 100, 2)}%"

    def _invoke_callback(self):
        now = time.time()
        if now - self._last_invoked >= self._debounce_seconds:
            if self._external_callback:
                self._external_callback(None, self.label, self.slider.value)
                self._last_invoked = now

    def _debounced_callback(self):
        if self._debounce_timer:
            self._debounce_timer.cancel()

        # Wait debounce period then call the actual update
        self._debounce_timer = threading.Timer(
            self._debounce_seconds, self._invoke_callback
        )
        self._debounce_timer.start()

    def _on_slider_change(self, e: ft.ControlEvent):
        value = self.slider.value
        self.value_label.value = self._format_label(value)
        self.value_label.update()
        self.slider.update()

        self._debounced_callback()
