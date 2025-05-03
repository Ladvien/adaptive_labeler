from typing import Optional
from PIL import Image as PILImage
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from random import uniform
from uuid import uuid4
import os

from adaptive_labeler.label_manager_config import (
    LabelManagerConfig,
)
from image_utils.image_loader import ImageLoader
from image_utils.image_noiser import ImageNoiser
from image_utils.image_path import ImagePath
from image_utils.utils import load_image_as_base64


@dataclass
class LabeledImage:
    image_path: ImagePath
    output_path: ImagePath
    label: str

    def get_noisy_base64(self) -> str:
        return self.output_path.load_as_base64()


@dataclass
class LabeledImageSeed:
    image_path: ImagePath
    threshold: float
    output_path: ImagePath

    def update_threshold(self, threshold: float) -> None:
        """Update the threshold value for the labeled image."""
        if not (0 <= threshold <= 1):
            raise ValueError("Threshold must be between 0 and 1.")

        self.threshold = threshold

    def label(self, label: str) -> LabeledImage:
        """Return a labeled version of this image without writing to disk."""
        return LabeledImage(self.image_path, self.output_path, label)


@dataclass
class UnlabeledImage:
    image_path: ImagePath
    output_path: ImagePath
    _noisy_image: Optional[PILImage.Image] = None
    _noisy_base64: Optional[str] = None

    def get_noisy_image(self, severity: float) -> PILImage.Image:
        if self._noisy_image is None:
            original = self.image_path.load()
            self._noisy_image = ImageNoiser.add_jpeg_compression(original, severity)
        return self._noisy_image

    def get_noisy_base64(self, severity: float) -> str:
        if self._noisy_base64 is None:
            noisy = self.get_noisy_image(severity)
            self._noisy_base64 = load_image_as_base64(noisy)
        return self._noisy_base64

    def label(self, label: str) -> LabeledImageSeed:
        """Return a labeled version of this image without writing to disk."""
        return LabeledImageSeed(self.image_path, label, self.output_path)

    def noisy_as_base64(self, severity: float) -> str:
        image = self.image_path.load()
        noisy_image = ImageNoiser.add_jpeg_compression(image, severity=severity)
        return load_image_as_base64(noisy_image)


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

    def record_label(self, labeled_image: LabeledImage):
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

    def save_label(self, labeled_image_seed: LabeledImageSeed):
        if str(labeled_image_seed.image_path.path) in self.labeled_image_paths:
            raise Exception(
                f"This image has already been labeled: {labeled_image_seed.image_path.path}"
            )

        new_noisy_images = []

        for _ in range(self.config.samples_per_image):
            # Generate a new noisy image
            original_image = labeled_image_seed.image_path.load()

            noise_level = uniform(0, 1.0)

            print(f"Generating noisy image with severity: {noise_level}")
            print(f"Original image path: {labeled_image_seed}")
            label = (
                "acceptable"
                if labeled_image_seed.threshold > noise_level
                else "unacceptable"
            )

            noisy_image = ImageNoiser.add_jpeg_compression(
                original_image, severity=noise_level
            )

            noisy_image_path = self.config.output_dir / f"{uuid4()}.jpg"
            noisy_image.save(noisy_image_path)

            labeled_image = LabeledImage(
                labeled_image_seed.image_path,
                ImagePath(noisy_image_path),
                label,
            )

            self.label_writer.record_label(labeled_image)
            new_noisy_images.append(noisy_image_path)
            self.labeled_image_paths.append(str(labeled_image.image_path))

    def new_unlabeled(self) -> UnlabeledImage | None:
        try:
            while True:
                image_path = next(self.image_loader)
                if str(image_path.path) not in self.labeled_image_paths:
                    return UnlabeledImage(image_path, self.config.output_dir)
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

    def get_labeled_image_pairs(self) -> list[LabeledImageSeed]:
        return [
            LabeledImageSeed(
                ImagePath(row["original_image_path"]),
                ImagePath(row["noisy_image_path"]),
                row["label"],
            )
            for _, row in self.label_writer.df.iterrows()
        ]
