import flet as ft
from pynput.keyboard import Key, KeyCode
import time

from adaptive_labeler.controls.image_pair_view import (
    ImagePairViewer,
)
from adaptive_labeler.label_manager import (
    LabeledImagePair,
)


class ReviewControlView(ft.Column):
    def __init__(
        self,
        labeled_image_pairs: list[LabeledImagePair],
        color_scheme: ft.ColorScheme | None = None,
    ):
        super().__init__()
        self.labeled_image_pairs = labeled_image_pairs
        self.__index = 0
        self.image_pair_viewer = ImagePairViewer(
            self.labeled_image_pairs[self.__index],
            color_scheme,
        )

        self.color_scheme = color_scheme or ft.ColorScheme()

        self.__last_key_press_time = 0
        self.__debounce_interval = 0.2  # seconds

        self.expand = True
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 0

        self.label_name_text = ft.Text(
            self.labeled_image_pairs[0].label,
            size=14,
            weight=ft.FontWeight.BOLD,
            color=self.color_scheme.secondary,
            text_align=ft.TextAlign.RIGHT,
        )

        self.controls = [
            ft.Container(
                content=self.image_pair_viewer,
                bgcolor=self.color_scheme.primary,
                padding=20,
                border_radius=12,
                expand=3,  # Top: 3/4 screen
            ),
            ft.Container(
                content=ft.Row(
                    [
                        # 3/4 of width: Instructions + Slider
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        "Label:",
                                        size=20,
                                        color=self.color_scheme.secondary,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                    self.label_name_text,
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                # vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            expand=3,  # 3/4 widt h
                        ),
                    ],
                    expand=True,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=20,
                expand=1,  # Bottom: 1/4 screen
            ),
        ]

    def update_image_pair_viewer(self):
        print(f"Updating image pair viewer with index: {self.__index}")
        labeled_pair = self.labeled_image_pairs[self.__index]
        self.label_name_text.value = labeled_pair.label
        self.image_pair_viewer.update_images(labeled_pair)

    def handle_keyboard_event(self, key: Key | KeyCode) -> bool:
        if not isinstance(key, Key):
            return False

        if not self.__debounce_keypress():
            return False

        if key.name in ("right", "left"):
            if key.name == "right":
                self.__index += 1
            elif key.name == "left":
                self.__index -= 1

            self.update_image_pair_viewer()
            self.update()

            return True

        elif key.name == "space":

            return True

    def __debounce_keypress(self) -> bool:
        now = time.time()
        if now - self.__last_key_press_time >= self.__debounce_interval:
            self.__last_key_press_time = now
            return True
        return False
