"""
This module contains utility functions for working with OpenCV.
"""

import cv2
import os
import subprocess
import time
from typing import Optional

from basic_bot.commons import constants as c, log
from basic_bot.commons.camera_opencv import Camera
from basic_bot.commons.base_audio import BaseAudio

THUMBNAIL_WIDTH = 80
THUMBNAIL_HEIGHT = 60
LG_THUMBNAIL_WIDTH = 320
LG_THUMBNAIL_HEIGHT = 240


def record_video(camera: Camera, duration: float, audio_source: Optional[BaseAudio] = None) -> str:
    """
    Record a video to BB_VIDEO_PATH for a specified number of seconds.

    Calling this function will save an MP4 video file to the BB_VIDEO_PATH directory.
    The filename is the current date and time in the format `YYYYMMDD-HHMMSS.mp4`.

    It will also save the first frame of the video as a JPEG image in the same directory
    named `YYYYMMDD-HHMMSS.jpg`.

    Args:
        camera: Camera instance for video capture
        duration: Recording duration in seconds
        audio_source: Optional audio source for audio recording
    """
    videoPath = os.path.realpath(c.BB_VIDEO_PATH)
    os.makedirs(videoPath, exist_ok=True)

    # Filenames are the current date and time in the format `YYYYMMDD-HHMMSS.mp4`.
    base_file_name = time.strftime("%Y%m%d-%H%M%S")
    video_filename = os.path.join(videoPath, f"{base_file_name}.mp4")
    image_filename = os.path.join(videoPath, f"{base_file_name}.jpg")
    lg_image_filename = os.path.join(videoPath, f"{base_file_name}_lg.jpg")

    if audio_source:
        # Record video with audio using ffmpeg
        return record_video_with_audio_ffmpeg(camera, audio_source, duration, video_filename, image_filename, lg_image_filename, base_file_name)
    else:
        # Record video only (original behavior)
        return record_video_only_opencv(camera, duration, video_filename, image_filename, lg_image_filename, base_file_name)


def record_video_only_opencv(camera: Camera, duration: float, video_filename: str, image_filename: str, lg_image_filename: str, base_file_name: str) -> str:
    """Record video only using OpenCV (original implementation)."""
    raw_filename = video_filename.replace('.mp4', '_raw.mp4')

    # fourcc = cv2.VideoWriter_fourcc(*"avc1")
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
        writer.write(frame)
        if first_frame is None:
            first_frame = frame

    writer.release()

    convert_video_to_h264(raw_filename, video_filename)

    log.info(f"Saving thumbnail image to {image_filename}")
    if first_frame is not None:
        resized_frame = cv2.resize(first_frame, (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))  # type: ignore[arg-type]
        cv2.imwrite(image_filename, resized_frame)

        log.info(f"Saving thumbnail image to {lg_image_filename}")
        resized_frame = cv2.resize(first_frame, (LG_THUMBNAIL_WIDTH, LG_THUMBNAIL_HEIGHT))  # type: ignore[arg-type]
        cv2.imwrite(lg_image_filename, resized_frame)

    return base_file_name


def record_video_with_audio_ffmpeg(camera: Camera, audio_source: BaseAudio, duration: float, video_filename: str, image_filename: str, lg_image_filename: str, base_file_name: str) -> str:
    """Record video with audio using ffmpeg directly."""
    log.info(f"Recording {duration} seconds of video with audio to {video_filename}")

    # Start audio capture
    if not audio_source.is_running():
        audio_source.start()

    # For now, fallback to video-only recording since ffmpeg dual-input approach is complex
    # TODO: Implement proper audio+video recording with ffmpeg later
    log.info("Audio recording with video not yet fully implemented - recording video only")
    return record_video_only_opencv(camera, duration, video_filename, image_filename, lg_image_filename, base_file_name)


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
