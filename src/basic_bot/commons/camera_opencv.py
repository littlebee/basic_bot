import os
import time
import cv2

from typing import Generator

from basic_bot.commons import constants as c, log
from basic_bot.commons.base_camera import BaseCamera


class OpenCvCamera(BaseCamera):
    """
    This class implements the BaseCamera interface using OpenCV.

    Usage:

    ```python
    camera = OpenCvCamera()
    # get_frame() is from BaseCamera and returns a single frame
    frame = camera.get_frame()
    # you can then used the image frame for example:
    jpeg = cv2.imencode(".jpg", frame)[1].tobytes()
    ```
    """

    video_source: int = 0
    img_is_none_messaged: bool = False

    def __init__(self) -> None:
        OpenCvCamera.set_video_source(c.BB_CAMERA_CHANNEL)
        super(OpenCvCamera, self).__init__()

    @staticmethod
    def set_video_source(source: int) -> None:
        log.info(f"setting video source to {source}")
        OpenCvCamera.video_source = source

    @staticmethod
    def init_camera() -> cv2.VideoCapture:
        log.info("initializing VideoCapture")

        camera = cv2.VideoCapture(
            OpenCvCamera.video_source
        )  # , apiPreference=cv2.CAP_V4L2)
        if not camera.isOpened():
            raise RuntimeError("Could not start camera.")

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, c.BB_VISION_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, c.BB_VISION_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, c.BB_CAMERA_FPS)

        fourcc = cv2.VideoWriter_fourcc("M", "J", "P", "G")  # type: ignore
        camera.set(cv2.CAP_PROP_FOURCC, fourcc)

        # Doing the rotation using cv2.rotate() was a 6-7 FPS drop
        # Unfortunately, you can't set the rotation on the v4l driver
        # on raspian bullseye before doing the opencv init above - why, idk.
        log.info(f"setting camera rotation to {c.BB_CAMERA_ROTATION}")
        if c.BB_CAMERA_ROTATION != 0:
            os.system(f"sudo v4l2-ctl --set-ctrl=rotate={c.BB_CAMERA_ROTATION}")

        return camera

    @staticmethod
    def frames() -> Generator[bytes, None, None]:
        """
        Generator function that yields frames from the camera. Required by BaseCamera
        """
        camera = OpenCvCamera.init_camera()

        read_error_count = 0
        while True:
            success, img = camera.read()
            if not success:
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

            if img is None:
                if not OpenCvCamera.img_is_none_messaged:
                    log.error(
                        "The camera has not read data, please check whether the camera can be used normally."
                    )
                    OpenCvCamera.img_is_none_messaged = True
                continue

            yield img
