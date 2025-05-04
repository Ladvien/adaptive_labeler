import pytest
from PIL import Image as PILImage


from adaptive_labeler.noisy_image_maker import NoisyImageMaker
from image_utils.image_path import ImagePath


def test_noisy_image_creation(dummy_image, dummy_output, dummy_noise_fn):
    img_path = ImagePath(dummy_image)
    maker = NoisyImageMaker(
        image_path=img_path, output_path=ImagePath(dummy_output), threshold=0.5
    )
    noisy = maker.noisy_image(dummy_noise_fn)
    assert isinstance(noisy, PILImage.Image)
    assert noisy.size == (10, 10)


def test_noisy_base64(dummy_image, dummy_output, dummy_noise_fn, monkeypatch):
    img_path = ImagePath(dummy_image)

    TYPICAL_JPEG_BASE_64_START_STR = "/9j"

    # Patch the noisy_image method to always return a known image
    maker = NoisyImageMaker(
        image_path=img_path, output_path=ImagePath(dummy_output), threshold=0.5
    )

    monkeypatch.setattr(
        maker,
        "noisy_image",
        lambda fn=dummy_noise_fn: PILImage.new("RGB", (10, 10), color="red"),
    )

    base64_str = maker.noisy_base64(dummy_noise_fn)
    assert isinstance(base64_str, str)
    assert base64_str.startswith(TYPICAL_JPEG_BASE_64_START_STR)


def test_set_threshold_valid(dummy_image, dummy_output):
    maker = NoisyImageMaker(
        image_path=ImagePath(dummy_image),
        output_path=ImagePath(dummy_output),
        threshold=0.2,
    )
    maker.set_threshold(0.7)
    assert maker.threshold == 0.7


def test_set_threshold_invalid(dummy_image, dummy_output):
    maker = NoisyImageMaker(
        image_path=ImagePath(dummy_image),
        output_path=ImagePath(dummy_output),
        threshold=0.2,
    )
    with pytest.raises(ValueError):
        maker.set_threshold(1.5)


def test_name_defaults_to_filename(dummy_image, dummy_output):
    maker = NoisyImageMaker(
        image_path=ImagePath(dummy_image),
        output_path=ImagePath(dummy_output),
        threshold=0.2,
    )
    assert maker.name == "test_image.jpg"
