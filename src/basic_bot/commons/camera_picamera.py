import time
from typing import Generator

# see, https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
from picamera2 import Picamera2  # type: ignore

from basic_bot.commons import log
from basic_bot.commons.base_camera import BaseCamera


class Camera(BaseCamera):
    """
    This class implements the BaseCamera interface using
    [Picamera2](https://pypi.org/project/picamera2/).


    Usage:

    ```python
    from basic_bot.commons.camera_picamera import Camera

    camera = Camera()
    # get_frame() is from BaseCamera and returns a single frame
    frame = camera.get_frame()
    # you can then used the image frame for example:
    jpeg = cv2.imencode(".jpg", frame)[1].tobytes()
    ```

    See vision service for another example usage.
    """

    @staticmethod
    def frames() -> Generator[bytes, None, None]:
        """
        Generator function that yields frames from the camera. Required by BaseCamera
        """
        camera = Picamera2()
        camera.start()

        read_error_count = 0
        while True:
            img = camera.capture_array()
            if img is None:
                read_error_count += 1
                if read_error_count > 10:
                    log.error("failed to read frame from camera 10x. Raising exception")
                    raise RuntimeError("Failed to read frame from camera 10x")
                else:
                    log.error(
                        "failed to read frame from camera. Waiting for 10 seconds"
                    )
                    time.sleep(10)
                    continue
            else:
                read_error_count = 0

            yield img
