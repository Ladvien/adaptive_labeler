from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

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
    noise_functions: Optional[List[str]] = None
    severity: float = 0.0

    samples_per_image: int = 5
    image_samples: int | None = None

    shuffle_images: bool = True

    def __post_init__(self):
        if self.label_csv_path is None:
            self.label_csv_path = os.path.join(self.output_dir, "labels.csv")

        if isinstance(self.images_dir, str):
            self.images_dir = Path(self.images_dir)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir, "train")

        if self.noise_functions is None:
            self.noise_functions = [
                ImageNoiser.add_jpeg_compression,
                # ImageNoiser.add_gaussian_noise,
                # ImageNoiser.add_salt_and_pepper_noise,
            ]

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
