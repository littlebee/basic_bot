"""
This module contains utility functions for working with OpenCV.
"""

import cv2
import os
import time


from basic_bot.commons import constants as c, log
from basic_bot.commons.camera_opencv import Camera


def record_video(camera: Camera, seconds: float) -> str:
    """
    Record a video to BB_VIDEO_PATH for a specified number of seconds.
    """
    videoPath = os.path.realpath(c.BB_VIDEO_PATH)
    os.makedirs(videoPath, exist_ok=True)

    # Filename is the current date and time in the format `YYYYMMDD-HHMMSS.mp4`.
    filename = os.path.join(videoPath, f"{time.strftime('%Y%m%d-%H%M%S')}.mp4")

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")  # type: ignore
    writer = cv2.VideoWriter(
        filename, fourcc, c.BB_CAMERA_FPS, (c.BB_VISION_WIDTH, c.BB_VISION_HEIGHT)
    )

    tstart = time.time()
    log.info(f"Recording 10 seconds of video to {filename}")
    while True:
        if time.time() - tstart > seconds:
            break
        frame = camera.get_frame()
        writer.write(frame)

    writer.release()
    return filename
