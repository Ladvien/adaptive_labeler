from __future__ import annotations
from collections.abc import Callable
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple
from rich import print

from image_utils.image_noiser import ImageNoiser


@dataclass
class LabelManagerConfig:
    images_dir: Path
    output_dir: Path
    temporary_dir: str
    label_csv_path: str | None = None
    overwrite_label_csv: bool = False
    allowed_exts: List[str] = field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".gif"]
    )
    noise_functions: List[Callable] = field(
        default_factory=lambda: [
            ImageNoiser.add_jpeg_compression,
            ImageNoiser.add_gaussian_noise,
        ]
    )

    severity: float = 0.0

    samples_per_image: int = 5
    image_samples: int | None = None

    shuffle_images: bool = True

    def get_noise_function(self, name: str) -> Optional[Callable]:
        for fn in self.noise_functions:
            if fn.__name__ == name:
                return fn
        return None

    def noise_function_names(self) -> List[str]:
        return [fn.__name__ for fn in self.noise_functions]

    def __post_init__(self):
        if self.label_csv_path is None:
            self.label_csv_path = os.path.join(self.output_dir, "labels.csv")

        if isinstance(self.images_dir, str):
            self.images_dir = Path(self.images_dir)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir, "train")

        self.validate()

    def validate(self):
        self.allowed_exts = list(set(ext.lower() for ext in self.allowed_exts))

        if not os.path.isdir(self.images_dir):
            raise ValueError(f"Invalid image directory: {self.images_dir}")
        os.makedirs(self.output_dir, exist_ok=True)
        if not os.path.isdir(self.output_dir):
            raise ValueError(f"Output directory is invalid: {self.output_dir}")

        if self.image_samples is not None and self.image_samples <= 0:
            raise ValueError("Image samples must be a positive integer.")
        if self.samples_per_image <= 0:
            raise ValueError("Samples per image must be a positive integer.")
        if self.severity < 0 or self.severity > 1:
            raise ValueError("Severity must be between 0 and 1.")
