from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class LabelManagerConfig:
    images_dir: str
    output_dir: str
    temporary_dir: str
    label_csv_path: str | None = None
    overwrite_label_csv: bool = False
    allowed_exts: List[str] = field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".gif"]
    )
    noise_functions: Optional[List[str]] = None
    severity_range: Tuple[float, float] = (0.2, 0.95)

    image_samples: int | None = None

    shuffle_images: bool = True

    def __post_init__(self):
        if self.label_csv_path is None:
            self.label_csv_path = os.path.join(self.output_dir, "labels.csv")

        self.validate()

    def validate(self):
        self.allowed_exts = list(set(ext.lower() for ext in self.allowed_exts))

        if not os.path.isdir(self.images_dir):
            raise ValueError(f"Invalid image directory: {self.images_dir}")
        os.makedirs(self.output_dir, exist_ok=True)
        if not os.path.isdir(self.output_dir):
            raise ValueError(f"Output directory is invalid: {self.output_dir}")
