"""
This pytest test just verifies that open cv is installed and
an image can be read from a file.
"""

import cv2
import os

from basic_bot.test_helpers.constants import BB_IS_BLIND


def test_cv2_import():
    """Test that opencv-python is installed and can be imported"""
    assert cv2.__version__ is not None


def test_read_image():
    """Test that an image can be read from file"""

    test_img = os.path.join(os.curdir, "tests", "test_data", "images", "daphne-1.jpg")
    print(f"loading image: {test_img=}")
    test_img = cv2.imread(test_img)

    assert test_img is not None
    assert len(test_img.shape) == 3  # Height, width, channels
    assert test_img.shape[2] == 3  # RGB channels


def test_camera_capture():
    """Test that an image can be captured from a camera 0"""

    # Skip this test if running on CI/CD machine without a camera
    if BB_IS_BLIND:
        print("Skipping test_camera_capture because BB_IS_BLIND is set")
        return

    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()

    assert ret
    assert frame is not None
    assert len(frame.shape) == 3  # Height, width, channels
    assert frame.shape[2] == 3  # RGB channels
    cap.release()
