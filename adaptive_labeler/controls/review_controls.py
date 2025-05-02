import flet as ft


class ReviewControls(ft.Row):
    def __init__(self, labeled_image_pairs, color_scheme, on_mode_toggle):
        super().__init__()
        self.color_scheme = color_scheme
        self.labeled_image_pairs = labeled_image_pairs
        self._review_index = 0

        label = labeled_image_pairs[0].label if labeled_image_pairs else ""
        self.label_name_text = ft.Text(
            label,
            size=14,
            weight=ft.FontWeight.BOLD,
            color=color_scheme.secondary,
            text_align=ft.TextAlign.RIGHT,
        )

        self.mode_toggle = ft.ElevatedButton(
            text="Switch to Labeling",
            on_click=on_mode_toggle,
        )

        self.controls = [
            ft.Container(
                ft.Column(
                    [
                        ft.Text("Label:", size=20, color=color_scheme.secondary),
                        self.label_name_text,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                expand=True,
            ),
            ft.Container(self.mode_toggle, padding=10),
        ]

    def update_label(self, label):
        self.label_name_text.value = label
        self.label_name_text.update()
