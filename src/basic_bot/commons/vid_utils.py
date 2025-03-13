"""
This module contains utility functions for working with OpenCV.
"""

import cv2
import os
import subprocess
import time


from basic_bot.commons import constants as c, log
from basic_bot.commons.camera_opencv import Camera


def record_video(camera: Camera, duration: float) -> str:
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
    raw_filename = os.path.join(videoPath, "latest_raw.mp4")
    video_filename = os.path.join(videoPath, f"{base_file_name}.mp4")
    image_filename = os.path.join(videoPath, f"{base_file_name}.jpg")

    # fourcc = cv2.VideoWriter_fourcc(*"avc1")  # type: ignore
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
    writer = cv2.VideoWriter(
        raw_filename, fourcc, c.BB_CAMERA_FPS, (c.BB_VISION_WIDTH, c.BB_VISION_HEIGHT)
    )
    first_frame = None

    tstart = time.time()
    log.info(f"Recording {duration} seconds of video to {video_filename}")
    while True:
        if time.time() - tstart > duration:
            break
        frame = camera.get_frame()
        writer.write(frame)  # type: ignore
        if first_frame is None:
            first_frame = frame

    writer.release()

    convert_video_to_h264(raw_filename, video_filename)

    log.info(f"Saving thumbnail image to {image_filename}")
    cv2.resize(first_frame, (int(c.BB_VISION_WIDTH / 3), int(c.BB_VISION_HEIGHT / 3)))  # type: ignore
    cv2.imwrite(image_filename, first_frame)  # type: ignore

    return base_file_name


def convert_video_to_h264(video_file_in: str, video_file_out: str) -> None:
    """
    Sse system installed ffmpeg to convert video to h264.  This was needed to make the
    mp4 video captured using openCV compatible with web browsers.

    TODO: It would be nice to do this directly with cv2 VideoWriter, but I
    could not get it to work.  I think it is running into the same issue
    described [here in StackOverflow](https://stackoverflow.com/questions/70247344/save-video-in-opencv-with-h264-codec)
    The solution descibed however (use apt-get to install opencv python instead of pip)
    probably causes other issues :/.
    """
    log.info(f"Converting video to h264: {video_file_out}")
    command = [
        "ffmpeg",
        "-i",
        video_file_in,
        "-y",
        "-vcodec",
        "libx264",
        video_file_out,
    ]

    try:
        result = subprocess.run(command, capture_output=True, check=True, text=True)
        log.debug(result.stdout)
        os.remove(video_file_in)
    except subprocess.CalledProcessError as e:
        log.error(f"Error converting video: {e.stderr}")


def get_recorded_videos() -> list[str]:
    """
    Get a list of recorded videos in the BB_VIDEO_PATH directory.
    """
    videoPath = os.path.realpath(c.BB_VIDEO_PATH)
    videos: list[str] = []
    for file in os.listdir(videoPath):
        if file.endswith(".mp4"):
            videos.append(os.path.splitext(file)[0])

    videos.sort(reverse=True)
    return videos
