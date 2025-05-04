from functools import cached_property
from typing import Optional
from PIL import Image as PILImage
from adaptive_labeler.noisy_image_maker import NoisyImageMaker
import pandas as pd
from dataclasses import dataclass, field
from pathlib import Path
from random import uniform
from uuid import uuid4
import os
from rich import print

from adaptive_labeler.label_manager_config import (
    LabelManagerConfig,
)
from image_utils.image_loader import ImageLoader
from image_utils.image_noiser import ImageNoiser
from image_utils.image_path import ImagePath
from image_utils.utils import load_image_as_base64


class LabelWriter:
    def __init__(self, path: str, overwrite: bool = False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists() or overwrite:
            self.df = pd.DataFrame(
                columns=["original_image_path", "noisy_image_path", "label"]
            )
            self.df.to_csv(self.path, index=False)
        else:
            print(f"Loading existing label CSV: {self.path}")
            self.df = pd.read_csv(self.path)

    def record_label(self, labeled_image: NoisyImageMaker):
        new_row = {
            "original_image_path": str(labeled_image.image_path),
            "noisy_image_path": str(labeled_image.output_path),
            "label": labeled_image.label,
        }
        self.df.loc[len(self.df)] = new_row
        self.df.to_csv(self.path, index=False)

    def get_labels(self) -> list[str]:
        return self.df["original_image_path"].tolist()

    def num_labeled(self) -> int:
        return len(self.df)


class LabelManager:
    def __init__(self, config: LabelManagerConfig):
        self.config = config
        self.image_loader = ImageLoader(
            config.images_dir, shuffle=config.shuffle_images
        )
        self.label_writer = LabelWriter(
            config.label_csv_path, config.overwrite_label_csv
        )
        self.labeled_image_paths = self.label_writer.get_labels()
        self.total_samples = config.image_samples or len(self.image_loader)
        self.severity_value = config.severity

    def set_severity(self, severity: float) -> None:
        if not (0 <= severity <= 1):
            raise ValueError("Severity must be between 0 and 1.")
        self.severity_value = severity

    def get_severity(self) -> float:
        return self.severity_value

    def save_label(self, labeled_image_seed: NoisyImageMaker):
        if str(labeled_image_seed.image_path.path) in self.labeled_image_paths:
            raise Exception(
                f"This image has already been labeled: {labeled_image_seed.image_path.path}"
            )

        new_noisy_images = []

        for _ in range(self.config.samples_per_image):
            # Generate a new noisy image
            original_image = labeled_image_seed.image_path.load()

            noise_level = uniform(0, 1.0)
            severity = self.get_severity()

            print(f"Original image path: {labeled_image_seed}")
            print(f"Noise level: {noise_level}")
            print(f"Severity: {severity}")
            label = "acceptable" if severity > noise_level else "unacceptable"

            noisy_image = ImageNoiser.add_jpeg_compression(
                original_image, severity=noise_level
            )

            noisy_image_path = self.config.output_dir / f"{uuid4()}.jpg"
            noisy_image.save(noisy_image_path)

            labeled_image = NoisyImageMaker(
                labeled_image_seed.image_path,
                ImagePath(noisy_image_path),
                label,
            )

            print(labeled_image)
            self.label_writer.record_label(labeled_image)
            new_noisy_images.append(noisy_image_path)
            self.labeled_image_paths.append(str(labeled_image.image_path))

    def new_unlabeled(self) -> NoisyImageMaker | None:
        try:
            while True:
                image_path = next(self.image_loader)
                if str(image_path.path) not in self.labeled_image_paths:
                    return NoisyImageMaker(
                        image_path, self.config.output_dir, self.get_severity()
                    )
        except StopIteration:
            return None

    def unlabeled_count(self) -> int:
        return self.total_samples - len(self.labeled_image_paths)

    def labeled_count(self) -> int:
        return len(self.labeled_image_paths)

    def percentage_complete(self) -> float:
        if self.total_samples == 0:
            return 0.0
        return self.labeled_count() / self.total_samples

    def total(self) -> int:
        return self.total_samples

    def get_labeled_image_pairs(self) -> list[NoisyImageMaker]:
        return [
            NoisyImageMaker(
                ImagePath(row["original_image_path"]),
                ImagePath(row["noisy_image_path"]),
                row["label"],
            )
            for _, row in self.label_writer.df.iterrows()
        ]
