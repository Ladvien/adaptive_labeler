from functools import cached_property
from typing import Callable, Optional
from PIL import Image as PILImage
from dataclasses import dataclass, field
import os

from image_utils.image_noiser import ImageNoiser
from image_utils.image_path import ImagePath
from image_utils.utils import load_image_as_base64


@dataclass
class NoisyImageMaker:
    """
    Generates noisy versions of an image based on a JPEG compression threshold.

    Lazy-loaded properties:
    - `noisy_image`: Created when first accessed.
    - `noisy_base64`: Encoded to base64 when first accessed.
    """

    image_path: ImagePath
    output_path: ImagePath
    threshold: float
    name: Optional[str] = None

    def noisy_image(
        self, noise_fn: Callable[[PILImage.Image, float], PILImage.Image]
    ) -> PILImage.Image:
        original_image = self.image_path.load()
        return noise_fn(original_image, self.threshold)

    def noisy_base64(
        self, noise_fn: Callable[[PILImage.Image, float], PILImage.Image]
    ) -> str:
        return load_image_as_base64(self.noisy_image(noise_fn))

    def set_threshold(self, threshold: float) -> None:
        """Set or update the threshold."""
        if not (0 <= threshold <= 1):
            raise ValueError("Threshold must be between 0 and 1.")
        self.threshold = threshold

    def __post_init__(self):
        if self.name is None:
            self.name = os.path.basename(self.image_path.path)

        self.validate()

    def validate(self) -> bool:
        """Check if the image is valid."""
        if not isinstance(self.image_path, ImagePath):
            raise TypeError("image_path must be an instance of ImagePath")
