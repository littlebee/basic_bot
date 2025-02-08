import os
import cv2
import random
import time

from typing import Generator

from basic_bot.commons import log
from basic_bot.commons.base_camera import BaseCamera

log.info("Loaded basic_bot.test_helpers.camera_mock. loading images...")
this_dir = os.path.dirname(os.path.realpath(__file__))
pet_image_path = os.path.join(this_dir, "data", "pet_images")
not_pet_image_path = os.path.join(this_dir, "data", "not_pet_images")

pet_image_files = [
    os.path.join(pet_image_path, f)
    for f in os.listdir(pet_image_path)
    if f.endswith((".jpg", ".jpeg", ".png"))
]
not_pet_image_files = [
    os.path.join(not_pet_image_path, f)
    for f in os.listdir(not_pet_image_path)
    if f.endswith((".jpg", ".jpeg", ".png"))
]

# use cv2 to read the images from the above  into two respective lists
pet_images = [cv2.imread(f) for f in pet_image_files]
not_pet_images = [cv2.imread(f) for f in not_pet_image_files]


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
                index = random.randint(0, len(pet_images) - 1)
                log.debug(
                    f"camera_mock: yielding pet image: {pet_image_files[index]} frame_count: {frame_count}"
                )
                img = pet_images[index]
            else:
                index = random.randint(0, len(not_pet_images) - 1)
                log.debug(
                    f"camera_mock: yielding not pet image: {not_pet_image_files[index]} fame_count: {frame_count}"
                )
                img = not_pet_images[index]

            yield img  # type: ignore
            time.sleep(1 / 60)  # Limit supply to ~60 FPS
