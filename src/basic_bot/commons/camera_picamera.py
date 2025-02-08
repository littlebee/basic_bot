import time
from typing import Generator

# see, https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
from picamera2 import Picamera2  # type: ignore

from basic_bot.commons import log, constants as c
from basic_bot.commons.base_camera import BaseCamera


class Camera(BaseCamera):
    """
    This class implements the BaseCamera interface using
    [Picamera2](https://pypi.org/project/picamera2/).

    To use the Picamera2, you need to be running on a Raspberry Pi
    Bookworm with a camera module installed.

    To use with the vision service, you need to set the environment
    variable `BB_CAMERA_MODULE=basic_bot.commons.camera_picamera`
    before the vision service is started.  By default the vision
    service uses the opencv camera module which ATM, on Bookworm
    will work for USB, but [not for ribbon cable cameras](https://github.com/opencv/opencv/issues/21653).
    See also the [Installation Guide for Bookworm](https://github.com/littlebee/basic_bot/blob/main/docs/Installation%20Guides/setup_on_pi_bookworm.md#use-picamera2-instead-of-opencv-if-using-ribbon-cable-camera).


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
        size = (c.BB_VISION_WIDTH, c.BB_VISION_HEIGHT)
        camera = Picamera2()
        camera.configure(
            camera.create_video_configuration(main={"format": "RGB888", "size": size})
        )
        camera.start()
        read_error_count = 0
        while True:
            img = camera.capture_array("main")
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
