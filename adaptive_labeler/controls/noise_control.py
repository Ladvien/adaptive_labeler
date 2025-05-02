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
        on_resample_click: Callable = None,
        color_scheme: ft.ColorScheme | None = None,
    ):
        super().__init__()

        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.on_change_end = on_end_change
        self.on_resample_click = on_resample_click

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
            value=self._clamp(initial_value),
            divisions=int((max_val - min_val) / step) if step else None,
            round=3,
            on_change=self._on_slider_change,
            on_change_end=self._on_end_change,
            expand=True,
        )

        self.refresh_button = ft.ElevatedButton(
            "Resample",
            icon=ft.Icons.REFRESH,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
            on_click=self._on_resample_click,
        )

        self.controls = [
            self.value_label,
            self.slider,
            ft.Container(
                content=self.refresh_button,
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=8),
            ),
        ]

        self.spacing = 5
        self.alignment = ft.MainAxisAlignment.CENTER

    def _clamp(self, value: float) -> float:
        return min(max(value, self.min_val), self.max_val)

    def _on_slider_change(self, e: ft.ControlEvent):
        """Update label as the slider moves."""
        self.value_label.value = f"Noise Level: {round(self.slider.value * 100, 2)}%"
        self.value_label.update()

    @property
    def value(self) -> float:
        """Current noise value."""
        return self.slider.value

    @value.setter
    def value(self, new_value: float):
        self.slider.value = self._clamp(new_value)
        self.slider.update()
        self._on_slider_change(None)

    def _on_end_change(self, e: ft.ControlEvent):
        if self.on_change_end:
            self.on_change_end(e, self.slider.value)

    def _on_resample_click(self, e: ft.ControlEvent):
        if self.on_resample_click:
            self.on_resample_click(e, self.slider.value)
