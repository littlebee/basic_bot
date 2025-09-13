"""
This module contains utility functions for working with OpenCV.
"""

import cv2
import os
import subprocess
import time

from basic_bot.commons import constants as c, log
from basic_bot.commons.camera_opencv import Camera
from basic_bot.commons.base_camera import BaseCamera
from basic_bot.commons.base_audio import BaseAudio
import numpy as np

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
    resized_frame = cv2.resize(first_frame, (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    cv2.imwrite(image_filename, resized_frame)

    log.info(f"Saving thumbnail image to {lg_image_filename}")
    resized_frame = cv2.resize(first_frame, (LG_THUMBNAIL_WIDTH, LG_THUMBNAIL_HEIGHT))
    cv2.imwrite(lg_image_filename, resized_frame)

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

def record_video_with_audio(camera: BaseCamera, audio_capture: BaseAudio, duration: float) -> str:
    """
    Record a video with audio to BB_VIDEO_PATH for a specified number of seconds.

    This function uses ffmpeg to combine video frames from the camera and audio
    from the audio capture system into a single MP4 file with H.264 video and AAC audio.

    Args:
        camera: Camera instance for video capture
        audio_capture: Audio capture instance for audio recording
        duration: Duration in seconds to record

    Returns:
        Base filename of the recorded video (without extension)
    """
    videoPath = os.path.realpath(c.BB_VIDEO_PATH)
    os.makedirs(videoPath, exist_ok=True)

    # Filenames are the current date and time in the format `YYYYMMDD-HHMMSS.mp4`.
    base_file_name = time.strftime("%Y%m%d-%H%M%S")
    video_filename = os.path.join(videoPath, f"{base_file_name}.mp4")
    image_filename = os.path.join(videoPath, f"{base_file_name}.jpg")
    lg_image_filename = os.path.join(videoPath, f"{base_file_name}_lg.jpg")

    log.info(f"Recording {duration} seconds of video with audio to {video_filename}")

    # Set up ffmpeg command for audio/video recording
    command = [
        "ffmpeg",
        "-y",  # Overwrite output file
        "-f", "rawvideo",  # Input format for video
        "-vcodec", "rawvideo",
        "-s", f"{c.BB_VISION_WIDTH}x{c.BB_VISION_HEIGHT}",  # Video size
        "-pix_fmt", "bgr24",  # Pixel format (OpenCV uses BGR)
        "-r", str(c.BB_CAMERA_FPS),  # Frame rate
        "-i", "-",  # Read video from stdin
        "-f", "s16le",  # Input format for audio (16-bit signed little-endian)
        "-ar", str(audio_capture.get_sample_rate()),  # Audio sample rate
        "-ac", str(audio_capture.get_channels()),  # Audio channels
        "-i", "-",  # Read audio from stdin
        "-c:v", "libx264",  # Video codec
        "-c:a", "aac",  # Audio codec
        "-preset", "ultrafast",  # Fast encoding for real-time
        "-t", str(duration),  # Duration
        video_filename
    ]

    try:
        # Start ffmpeg process
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if process.stdin is None:
            raise RuntimeError("Failed to create ffmpeg stdin pipe")

        first_frame = None
        tstart = time.time()
        frame_count = 0

        # Record video and audio
        while time.time() - tstart < duration:
            try:
                # Get video frame
                frame_bytes = camera.get_frame()
                if frame_bytes:
                    # Decode JPEG to numpy array
                    np_array = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

                    if frame is not None:
                        # Save first frame for thumbnail
                        if first_frame is None:
                            first_frame = frame

                        # Write raw video frame to ffmpeg
                        process.stdin.write(frame.tobytes())
                        frame_count += 1

                # Get audio frame
                audio_frame = audio_capture.get_frame()
                if audio_frame is not None:
                    # Convert to bytes and write to ffmpeg
                    audio_bytes = audio_frame.astype(np.int16).tobytes()
                    process.stdin.write(audio_bytes)

                # Control frame timing
                time.sleep(1.0 / c.BB_CAMERA_FPS)

            except Exception as e:
                log.error(f"Error capturing frame: {e}")
                break

        # Close stdin to signal end of input
        process.stdin.close()

        # Wait for ffmpeg to finish
        stdout, stderr = process.communicate(timeout=30)

        if process.returncode != 0:
            log.error(f"ffmpeg failed with return code {process.returncode}")
            log.error(f"ffmpeg stderr: {stderr.decode()}")
            raise RuntimeError("Video recording failed")

        log.info(f"Successfully recorded {frame_count} frames")

        # Save thumbnails if we have a first frame
        if first_frame is not None:
            log.info(f"Saving thumbnail image to {image_filename}")
            resized_frame = cv2.resize(first_frame, (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
            cv2.imwrite(image_filename, resized_frame)

            log.info(f"Saving large thumbnail image to {lg_image_filename}")
            resized_frame = cv2.resize(first_frame, (LG_THUMBNAIL_WIDTH, LG_THUMBNAIL_HEIGHT))
            cv2.imwrite(lg_image_filename, resized_frame)

        return base_file_name

    except subprocess.TimeoutExpired:
        log.error("ffmpeg process timed out")
        process.kill()
        raise RuntimeError("Video recording timed out")
    except Exception as e:
        log.error(f"Error recording video with audio: {e}")
        if process.poll() is None:  # Process still running
            process.terminate()
        raise

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
