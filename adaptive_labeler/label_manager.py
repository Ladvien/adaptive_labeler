from typing import Callable
from image_utils.noising_operation import NosingOperation
from adaptive_labeler.noisy_image_maker import NoisyImageMaker
import pandas as pd
from dataclasses import dataclass, field, asdict
from pathlib import Path
from rich import print

from adaptive_labeler.label_manager_config import (
    LabelManagerConfig,
)
from image_utils.image_loader import ImageLoader
from image_utils.image_path import ImagePath


@dataclass
class ImageLabelRecord:
    original_image_path: str
    noise_operations: list[NosingOperation] = field(default_factory=list)

    def to_row(self):
        data = [self.original_image_path]
        for op in self.noise_operations:
            data.append(op.name)
            data.append(op.severity)
        return data

    def to_dict(self) -> dict:
        data = {"original_image_path": self.original_image_path}
        for idx, op in enumerate(self.noise_operations, start=1):
            data[f"fn_{idx}"] = op.name
            data[f"fn_{idx}_threshold"] = op.severity
        return data


class LabelWriter:
    def __init__(
        self,
        path: str,
        columns: list[str],
        image_path_column_name: str = "original_image_path",
        overwrite: bool = False,
        max_operations: int = 10,
    ):
        self.path = Path(path)
        self.max_operations = max_operations
        columns = ["original_image_path"]
        for i in range(1, self.max_operations + 1):
            columns.append(f"fn_{i}")
            columns.append(f"fn_{i}_threshold")

        self.columns = columns
        self.image_path_column_name = image_path_column_name
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists() or overwrite:
            self.df = pd.DataFrame(columns=self.columns)
            self.df.to_csv(self.path, index=False)
        else:
            print(f"Loading existing label CSV: {self.path}")
            self.df = pd.read_csv(self.path)

        assert list(self.df.columns) == self.columns

    def record(self, labeled_image: ImageLabelRecord):
        new_row = {col: None for col in self.columns}
        new_row.update(labeled_image.to_dict())
        self.df.loc[len(self.df)] = new_row
        self.df.to_csv(self.path, index=False)

    def get_labels(self) -> list[str]:
        return self.df[self.image_path_column_name].tolist()

    def num_labeled(self) -> int:
        return len(self.df)


class LabelManager:
    def __init__(self, config: LabelManagerConfig):
        self.config = config
        self.noise_fns = config.noise_functions

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

    # TODO: Rework to "Generate Labels"
    # def save_label(
    #     self,
    #     image_maker: NoisyImageMaker,
    # ) -> None:
    #     if str(image_maker.image_path.path) in self.labeled_image_paths:
    #         raise Exception(
    #             f"This image has already been labeled: {image_maker.image_path.path}"
    #         )

    #     new_noisy_images = []

    #     for _ in range(self.config.samples_per_image):
    #         # Generate a new noisy image
    #         noise_level = uniform(0, 1.0)
    #         severity = self.get_severity()

    #         print(f"Original image path: {image_maker}")
    #         print(f"Noise level: {noise_level}")

    #         noisy_image_path = self.config.output_dir / f"{uuid4()}.jpg"

    #         maker = NoisyImageMaker(
    #             image_maker.image_path,
    #             ImagePath(noisy_image_path),
    #             noise_level,
    #         )

    #         noisy_image = maker.noisy_image(self.noise_fns)
    #         noisy_image.save(noisy_image_path)

    #         labeled_noisy_image = LabeledImage(
    #             original_image_path=str(image_maker.image_path.path),
    #             noisy_image_path=str(noisy_image_path),
    #             severity=severity,
    #             noise_functions=[self.noise_fns.__name__],
    #         )

    #         self.label_writer.record(labeled_noisy_image)
    #         new_noisy_images.append(noisy_image_path)
    #         self.labeled_image_paths.append(str(maker.image_path))
    #         self.labeled_image_paths = list(set(self.labeled_image_paths))

    def new_unlabeled(self) -> NoisyImageMaker | None:
        try:
            while True:
                image_path = next(self.image_loader)
                if str(image_path.path) not in self.labeled_image_paths:
                    return NoisyImageMaker(
                        image_path,
                        self.config.output_dir,
                        self.get_severity(),
                        self.config.noise_functions,
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

    def get_entries(self) -> list[NoisyImageMaker]:
        entries = []
        for _, row in self.label_writer.df.iterrows():
            noise_operations = []
            for i in range(1, self.label_writer.max_operations + 1):
                fn = row.get(f"fn_{i}")
                threshold = row.get(f"fn_{i}_threshold")
                if pd.notna(fn) and pd.notna(threshold):
                    noise_operations.append(
                        NosingOperation(
                            fn=self.noise_fns[fn],  # get function from name
                            severity=threshold,
                        )
                    )
            entries.append(
                ImageLabelRecord(
                    original_image_path=row["original_image_path"],
                    noise_operations=noise_operations,
                )
            )

    def set_noise_fn(self, fn: Callable):
        self.noise_fns = fn

    def delete_last_label(self) -> bool:
        """
        Removes the last num_images labeled images from the label writer.
        Returns True if images were removed, False otherwise.
        """
        df = self.label_writer.df

        if df.empty:
            print("No images to remove.")
            return False

        safe_num_to_remove = min(self.config.samples_per_image, len(df))
        rows_to_delete = df.index[-safe_num_to_remove:]
        df = df.drop(rows_to_delete)
        df.to_csv(self.label_writer.path, index=False)
        self.label_writer.df = df
        self.labeled_image_paths = df["original_image_path"].tolist()
        print(f"Removed last {safe_num_to_remove} labeled images.")
        return True
