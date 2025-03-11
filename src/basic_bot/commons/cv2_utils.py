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

    Calling this function will save an MP4 video file to the BB_VIDEO_PATH directory.
    The filename is the current date and time in the format `YYYYMMDD-HHMMSS.mp4`.

    It will also save the first frame of the video as a JPEG image in the same directory
    named `YYYYMMDD-HHMMSS.jpg`.
    """
    videoPath = os.path.realpath(c.BB_VIDEO_PATH)
    os.makedirs(videoPath, exist_ok=True)

    # Filenames are the current date and time in the format `YYYYMMDD-HHMMSS.mp4`.
    base_file_name = time.strftime("%Y%m%d-%H%M%S")
    video_filename = os.path.join(videoPath, f"{base_file_name}.mp4")
    image_filename = os.path.join(videoPath, f"{base_file_name}.jpg")

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")  # type: ignore
    writer = cv2.VideoWriter(
        video_filename, fourcc, c.BB_CAMERA_FPS, (c.BB_VISION_WIDTH, c.BB_VISION_HEIGHT)
    )
    first_frame = None

    tstart = time.time()
    log.info(f"Recording 10 seconds of video to {video_filename}")
    while True:
        if time.time() - tstart > seconds:
            break
        frame = camera.get_frame()
        writer.write(frame)  # type: ignore
        if first_frame is None:
            first_frame = frame

    writer.release()

    log.info(f"Saving thumbnail image to {image_filename}")
    cv2.resize(first_frame, (int(c.BB_VISION_WIDTH / 3), int(c.BB_VISION_HEIGHT / 3)))  # type: ignore
    cv2.imwrite(image_filename, first_frame)  # type: ignore

    return base_file_name
