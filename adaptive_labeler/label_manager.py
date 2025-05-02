from image_utils.image_loader import ImageLoader
from image_utils.image_noiser import ImageNoiser
from image_utils.image_path import ImagePath
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from random import uniform
from uuid import uuid4
import os

from adaptive_labeler.label_manager_config import (
    LabelManagerConfig,
)


@dataclass
class LabeledImagePair:
    image_path: ImagePath
    output_path: ImagePath
    label: str

    def update_label(self, new_label: str) -> None:
        self.label = new_label


@dataclass
class UnlabeledImage:
    image_path: ImagePath

    def label(self, label: str, output_path: str) -> LabeledImagePair:
        return LabeledImagePair(self.image_path, ImagePath(output_path), label)


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

    def record_label(self, labeled_pair: LabeledImagePair):
        new_row = {
            "original_image_path": str(labeled_pair.image_path.path),
            "noisy_image_path": str(labeled_pair.output_path.path),
            "label": labeled_pair.label,
        }
        self.df.loc[len(self.df)] = new_row
        self.df.to_csv(self.path, index=False)

    def update_label(self, labeled_pair: LabeledImagePair):
        if (
            labeled_pair.original_image_path
            not in self.df["original_image_path"].values
        ):
            raise Exception(f"This image pair is not labeled. {labeled_pair}")

        self.df.loc[
            self.df["original_image_path"]
            == str(labeled_pair.original_image_path.path),
            "label",
        ] = labeled_pair.label
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
        self.total_samples = config.image_samples or self.image_loader.total()
        self.unlabeled_noisy_image_path = None

    def set_severity(self, severity: float) -> None:
        if not (0 <= severity <= 1):
            raise ValueError("Severity must be between 0 and 1.")
        self.config.severity = severity

    def severity(self) -> float:
        return self.config.severity

    def save_label(self, labeled_pair: LabeledImagePair) -> None:
        if labeled_pair.image_path in self.labeled_image_paths:
            raise Exception(f"This image pair is already labeled. {labeled_pair}")
        self.label_writer.record_label(labeled_pair)
        self.labeled_image_paths.append(labeled_pair.image_path)

    def new_unlabeled(self) -> UnlabeledImage | None:
        image_path = next(self.image_loader)
        if image_path is None:
            return self.image_loader.reset()

        self.unlabeled_noisy_image_path = os.path.join(
            self.config.output_dir, f"{image_path.name}_{uuid4()}_noisy.jpg"
        )
        return self._unlabeled_pair(image_path)

    def resample_images(self, unlabeled_pair: UnlabeledImage) -> UnlabeledImage:
        if unlabeled_pair.image_path in self.labeled_image_paths:
            raise Exception(f"This image pair is already labeled. {unlabeled_pair}")
        return self._unlabeled_pair(unlabeled_pair.image_path)

    def _unlabeled_pair(self, image_path: ImagePath) -> UnlabeledImage:
        return UnlabeledImage(image_path)

    def unlabeled_count(self) -> int:
        return self.total_samples - len(self.labeled_image_paths)

    def labeled_count(self) -> int:
        return len(self.labeled_image_paths)

    def percentage_complete(self) -> float:
        return self.labeled_count() / self.total_samples

    def total(self) -> int:
        return self.total_samples

    def get_labeled_image_pairs(self) -> list[LabeledImagePair]:
        return [
            LabeledImagePair(
                ImagePath(row["original_image_path"]),
                ImagePath(row["noisy_image_path"]),
                row["label"],
            )
            for _, row in self.label_writer.df.iterrows()
        ]
