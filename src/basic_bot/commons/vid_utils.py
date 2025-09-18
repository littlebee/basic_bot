"""
This module contains utility functions for working with OpenCV.
"""

import asyncio
import cv2
import os
import subprocess
import time
import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder

from basic_bot.commons import constants as c, log
from basic_bot.commons.camera_opencv import Camera

THUMBNAIL_WIDTH = 80
THUMBNAIL_HEIGHT = 60
LG_THUMBNAIL_WIDTH = 320
LG_THUMBNAIL_HEIGHT = 240


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
    raw_filename = os.path.join(videoPath, f"{base_file_name}_raw.mp4")
    video_filename = os.path.join(videoPath, f"{base_file_name}.mp4")
    image_filename = os.path.join(videoPath, f"{base_file_name}.jpg")
    lg_image_filename = os.path.join(videoPath, f"{base_file_name}_lg.jpg")

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


def record_webrtc_video(camera: Camera, duration: float) -> str:
    """
    Record video and audio via WebRTC from the vision service for a specified number of seconds.

    This function connects to the vision service's WebRTC endpoint to record both video and audio,
    while still using the provided camera to capture thumbnail frames.

    Calling this function will save an MP4 video file to the BB_VIDEO_PATH directory.
    The filename is the current date and time in the format `YYYYMMDD-HHMMSS.mp4`.

    It will also save the first frame of the video as a JPEG image in the same directory
    named `YYYYMMDD-HHMMSS.jpg`, captured from the provided camera parameter.

    Args:
        camera: Camera instance used for thumbnail generation
        duration: Recording duration in seconds

    Returns:
        Base filename (without extension) of the recorded files
    """
    videoPath = os.path.realpath(c.BB_VIDEO_PATH)
    os.makedirs(videoPath, exist_ok=True)

    # Filenames are the current date and time in the format `YYYYMMDD-HHMMSS.mp4`.
    base_file_name = time.strftime("%Y%m%d-%H%M%S")
    video_filename = os.path.join(videoPath, f"{base_file_name}.mp4")
    image_filename = os.path.join(videoPath, f"{base_file_name}.jpg")
    lg_image_filename = os.path.join(videoPath, f"{base_file_name}_lg.jpg")

    # Run the async WebRTC recording
    asyncio.run(_record_webrtc_async(video_filename, duration))

    # Capture thumbnail from camera
    log.info(f"Capturing thumbnail from camera for {image_filename}")
    first_frame = camera.get_frame()
    if first_frame is not None:
        resized_frame = cv2.resize(first_frame, (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
        cv2.imwrite(image_filename, resized_frame)

        log.info(f"Saving large thumbnail image to {lg_image_filename}")
        resized_frame = cv2.resize(
            first_frame, (LG_THUMBNAIL_WIDTH, LG_THUMBNAIL_HEIGHT)
        )
        cv2.imwrite(lg_image_filename, resized_frame)

    return base_file_name


async def _record_webrtc_async(output_file: str, duration: float) -> None:
    """
    Internal async function to handle WebRTC recording.

    Args:
        output_file: Full path to output MP4 file
        duration: Recording duration in seconds
    """
    webrtc_endpoint = "http://localhost:5801/offer"

    log.info(f"Recording {duration} seconds of WebRTC video/audio to {output_file}")

    # Create RTCPeerConnection
    pc = RTCPeerConnection()
    recorder = None

    @pc.on("track")
    def on_track(track):
        nonlocal recorder
        log.debug(f"Received {track.kind} track")

        if recorder is None:
            # Create recorder on first track
            recorder = MediaRecorder(output_file)

        # Add track to recorder
        recorder.addTrack(track)

        @track.on("ended")
        def on_track_ended():
            log.debug(f"{track.kind} track ended")

    try:
        # Add transceivers for receiving video and audio
        pc.addTransceiver("video", direction="recvonly")
        pc.addTransceiver("audio", direction="recvonly")

        # Create offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        # Wait for ICE gathering to complete
        while pc.iceGatheringState != "complete":
            await asyncio.sleep(0.1)

        # Send offer to server
        async with aiohttp.ClientSession() as session:
            offer_data = {
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type,
            }

            headers = {"Content-Type": "application/json"}
            async with session.post(
                webrtc_endpoint, json=offer_data, headers=headers
            ) as response:
                if response.status != 200:
                    raise RuntimeError(
                        f"Failed to send offer to WebRTC endpoint: {response.status}"
                    )

                answer_data = await response.json()

                # Set remote description
                answer = RTCSessionDescription(
                    sdp=answer_data["sdp"], type=answer_data["type"]
                )
                await pc.setRemoteDescription(answer)

        log.debug("WebRTC connection established, starting recording...")

        # Wait a moment for tracks to be received
        await asyncio.sleep(1)

        # Start recording
        if recorder:
            await recorder.start()
            log.debug("WebRTC recording started")
        else:
            raise RuntimeError("No WebRTC tracks received, cannot start recording")

        # Record for specified duration
        start_time = time.time()
        while time.time() - start_time < duration:
            await asyncio.sleep(0.1)

        log.debug(f"WebRTC recording completed after {duration} seconds")

        # Stop recording
        if recorder:
            await recorder.stop()
            log.debug(f"WebRTC recording saved to {output_file}")

    except Exception as e:
        log.error(f"Error during WebRTC recording: {e}")
        raise

    finally:
        # Close connection
        await pc.close()


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
