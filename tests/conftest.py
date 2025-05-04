import pytest
from PIL import Image as PILImage
import shutil
from pathlib import Path


TEMP_ROOT = Path("tests") / "temp_data"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)

# Constants for your temp test files
TEST_DIR = Path(__file__).parent / "test_data"
TEST_DIR.mkdir(exist_ok=True)

DUMMY_IMAGE_NAME = "test_image.jpg"
DUMMY_OUTPUT_NAME = "output_image.jpg"


@pytest.fixture(scope="session")
def dummy_image():
    img_path = TEST_DIR / DUMMY_IMAGE_NAME
    if not img_path.exists():
        img = PILImage.new("RGB", (10, 10), color="blue")
        img.save(img_path)
    return str(img_path)


@pytest.fixture(scope="session")
def dummy_output():
    output_path = TEST_DIR / DUMMY_OUTPUT_NAME
    return str(output_path)


@pytest.fixture
def dummy_noise_fn():
    """A dummy noise function that just returns the original image."""
    return lambda image, severity: image


@pytest.fixture
def tmp_image_dir():
    """Create a temp directory with test images."""
    tmpdir = TEMP_ROOT / "images"
    if tmpdir.exists():
        shutil.rmtree(tmpdir)
    tmpdir.mkdir(parents=True)

    for i in range(3):
        img = PILImage.new("RGB", (100, 100), color=(i * 50, i * 50, i * 50))
        img.save(tmpdir / f"test_image_{i}.jpg")

    yield tmpdir


@pytest.fixture
def tmp_output_dir():
    """Create a temp directory for noisy output."""
    tmpdir = TEMP_ROOT / "output"
    if tmpdir.exists():
        shutil.rmtree(tmpdir)
    tmpdir.mkdir(parents=True)

    yield tmpdir
