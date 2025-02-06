import os
import cv2
import random

from typing import Generator

from basic_bot.commons import log
from basic_bot.commons.base_camera import BaseCamera

log.info("Loaded basic_bot.test_helpers.camera_mock. loading images...")
this_dir = os.path.dirname(os.path.realpath(__file__))
pet_image_path = os.path.join(this_dir, "data", "pet_images")
not_pet_image_path = os.path.join(this_dir, "data", "not_pet_images")


# use cv2 to read the images from the above  into two respective lists
pet_images = [
    cv2.imread(os.path.join(pet_image_path, f))
    for f in os.listdir(pet_image_path)
    if f.endswith((".jpg", ".jpeg", ".png"))
]
not_pet_images = [
    cv2.imread(os.path.join(pet_image_path, f))
    for f in os.listdir(pet_image_path)
    if f.endswith((".jpg", ".jpeg", ".png"))
]
log.debug(
    f"Loaded {len(pet_images)} pet images and {len(not_pet_images)} non pet images."
)


class Camera(BaseCamera):
    """
    This class implements a mock of BaseCamera interface
    using a set of static images from ($cwd)/data/
    """

    @staticmethod
    def frames() -> Generator[bytes, None, None]:
        """
        Generator function that yields frames from the camera. Required by BaseCamera
        """
        frame_count = 0
        while True:
            frame_count += 1
            # for testing, half of the frames are pet images and half are not pet images
            if frame_count % 2 == 0:
                img = pet_images[random.randint(0, len(pet_images) - 1)]
            else:
                img = not_pet_images[random.randint(0, len(not_pet_images) - 1)]

            yield img  # type: ignore
