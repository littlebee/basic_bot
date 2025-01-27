import os
import cv2
import pytest

try:
    from tflite_support.task import core
except ImportError:
    """
    tflite_support ishard to install on mac and even worse on Apple Silicon.

    It does run on Ubuntu Linux and runs on the Raspberry Pi.  The CI/CD
    GitHub Actions runner is Ubuntu Linux and you should see it running there.
    """
    #
    #
    pytest.skip(
        "tflite_support not installed. Skipping test_flight_detect",
        allow_module_level=True,
    )

from basic_bot.commons.tflite_detect import TFLiteDetect
from basic_bot.commons import constants as c

print(f"tflite_support is installed {core=}")

TFLITE_MODEL = os.path.join(
    "src/basic_bot/created_files/models/tflite/", c.BB_TFLITE_MODEL
)


class TestTFLiteDetect:

    def test_pet_detection(self):
        # Initialize detector
        detector = TFLiteDetect(TFLITE_MODEL, False)

        # Get all images from test directory
        test_image_dir = "tests/test_data/images/pets"
        image_files = [
            f
            for f in os.listdir(test_image_dir)
            if f.endswith((".jpg", ".jpeg", ".png"))
        ]

        # Test each image
        for image_file in image_files:
            image_path = os.path.join(test_image_dir, image_file)
            img = cv2.imread(image_path)

            # Get predictions
            predictions = detector.get_prediction(img)

            # Assert we got predictions
            assert len(predictions) > 0, f"No predictions for {image_file}"

            # Check if any prediction is cat/dog with >50% confidence
            found_pet = False
            for pred in predictions:
                if (
                    pred["classification"].lower() in ["cat", "dog"]
                    and pred["confidence"] > 0.5
                ):
                    found_pet = True
                    break

            assert (
                found_pet
            ), f"No cat/dog detected with >50% confidence in {image_file} predictions: {predictions}"
