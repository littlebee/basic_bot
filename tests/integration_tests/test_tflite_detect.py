import os
import cv2
import pytest


try:
    # first test to see if tflite_runtime is installed?
    import tflite_runtime  # type: ignore
except ImportError:
    """
    tflite_runtime is hard to install on mac and even worse on Apple Silicon.

    It does run on Ubuntu Linux and runs on the Raspberry Pi.  The CI/CD
    GitHub Actions runner is Ubuntu Linux and you should see it running there.
    """
    #
    #
    pytest.skip(
        "tflite_runtime not installed. Skipping test_flite_detect",
        allow_module_level=True,
    )

from basic_bot.commons.tflite_detect import TFLiteDetect

print(f"tflite_runtime is installed {tflite_runtime}")


class TestTFLiteDetect:

    def test_pet_detection(self):
        # Initialize detector
        detector = TFLiteDetect()

        # Get all images from test directory
        test_image_dir = "src/basic_bot/test_helpers/data/pet_images"
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
