"""
Utility functions for interacting with the vision service REST_API.
"""

import requests

from basic_bot.commons import log, constants as c


def send_record_video_request(duration: float) -> requests.Response:
    """
    Send a request to the vision service to start recording video.
    """
    if c.BB_LOG_ALL_MESSAGES:
        log.info(f"Sending record video request for {duration} seconds")
    response = requests.get(
        f"{c.BB_VISION_URI}/record_video",
        params={"duration": duration},
    )
    response.raise_for_status()
    return response


def fetch_recorded_videos() -> requests.Response:
    """
    Send a request to the vision service to retrieve a list of recorded videos.

    The resonse.json() will be a list of strings, each string is a base filename
    that can be appended with ".mp4" or ".jpg" to get the video or thumbnail image.
    """
    if c.BB_LOG_ALL_MESSAGES:
        log.info(f"Sending recorded_video request to {c.BB_VISION_URI}")
    response = requests.get(f"{c.BB_VISION_URI}/recorded_video")
    response.raise_for_status()
    return response


def fetch_recorded_video(file_name: str) -> requests.Response:
    """
    Send a request to the vision service to retrieve a list of recorded videos.

    The file_name should be appended with ".mp4" or ".jpg" to get the video or
    thumbnail image.
    """
    if c.BB_LOG_ALL_MESSAGES:
        log.info(f"Sending record video request for {file_name}")
    response = requests.get(
        f"{c.BB_VISION_URI}/recorded_video/{file_name}",
    )
    response.raise_for_status()
    return response
