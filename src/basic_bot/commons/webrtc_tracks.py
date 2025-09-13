"""
WebRTC media tracks for video and audio streaming.

This module provides custom WebRTC track implementations that integrate
with basic_bot's camera and audio capture systems.
"""

import asyncio
import logging
import fractions
import numpy as np
import cv2

from basic_bot.commons.base_camera import BaseCamera
from basic_bot.commons.base_audio import BaseAudio

logger = logging.getLogger(__name__)

try:
    from aiortc import VideoStreamTrack, AudioStreamTrack  # type: ignore
    from av import VideoFrame, AudioFrame  # type: ignore
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False
    logger.warning("aiortc not available. WebRTC streaming will not work.")
    # Create dummy classes to prevent import errors

    class VideoStreamTrack:  # type: ignore
        pass

    class AudioStreamTrack:  # type: ignore
        pass


class CameraVideoStreamTrack(VideoStreamTrack):
    """
    WebRTC video track that streams frames from basic_bot camera system.

    Integrates with the existing BaseCamera infrastructure to provide
    video frames to WebRTC peer connections.
    """

    def __init__(self, camera: BaseCamera):
        if not AIORTC_AVAILABLE:
            raise ImportError("aiortc is required for WebRTC video streaming")

        super().__init__()
        self.camera = camera
        self.frame_count = 0
        logger.info("CameraVideoStreamTrack initialized")

    async def recv(self) -> VideoFrame:
        """
        Generate the next video frame for WebRTC transmission.

        Returns:
            VideoFrame: The next video frame in WebRTC format
        """
        try:
            # Get frame from camera (this blocks until frame is available)
            frame_data = await asyncio.get_event_loop().run_in_executor(
                None, self.camera.get_frame
            )

            if frame_data is None:
                logger.warning("No frame data available from camera")
                # Create a black frame as fallback
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
            else:
                # Convert JPEG bytes to numpy array
                np_array = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

                if frame is None:
                    logger.error("Failed to decode camera frame")
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Convert BGR (OpenCV) to RGB (WebRTC standard)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Create VideoFrame for aiortc
            av_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")

            # Set timing information
            av_frame.pts = self.frame_count
            av_frame.time_base = fractions.Fraction(1, 30)  # 30 FPS

            self.frame_count += 1

            return av_frame

        except Exception as e:
            logger.error(f"Error in CameraVideoStreamTrack.recv(): {e}")
            # Return black frame on error
            black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            av_frame = VideoFrame.from_ndarray(black_frame, format="rgb24")
            av_frame.pts = self.frame_count
            av_frame.time_base = fractions.Fraction(1, 30)
            self.frame_count += 1
            return av_frame


class AudioCaptureStreamTrack(AudioStreamTrack):
    """
    WebRTC audio track that streams audio from basic_bot audio capture system.

    Integrates with the BaseAudio infrastructure to provide audio frames
    to WebRTC peer connections.
    """

    def __init__(self, audio_capture: BaseAudio):
        if not AIORTC_AVAILABLE:
            raise ImportError("aiortc is required for WebRTC audio streaming")

        super().__init__()
        self.audio_capture = audio_capture
        self.sample_count = 0
        self.sample_rate = audio_capture.get_sample_rate()
        self.channels = audio_capture.get_channels()
        self.chunk_size = audio_capture.get_chunk_size()

        logger.info(f"AudioCaptureStreamTrack initialized: {self.sample_rate}Hz, "
                    f"{self.channels} channel(s), chunk size {self.chunk_size}")

    async def recv(self) -> AudioFrame:
        """
        Generate the next audio frame for WebRTC transmission.

        Returns:
            AudioFrame: The next audio frame in WebRTC format
        """
        try:
            # Get audio frame from capture system
            audio_data = await asyncio.get_event_loop().run_in_executor(
                None, self.audio_capture.get_frame
            )

            if audio_data is None:
                logger.warning("No audio data available from capture")
                # Create silence as fallback
                audio_data = np.zeros((self.chunk_size, self.channels), dtype=np.int16)

            # Ensure correct data type
            if audio_data.dtype != np.int16:
                logger.debug(f"Converting audio from {audio_data.dtype} to int16")
                audio_data = audio_data.astype(np.int16)

            # Ensure correct shape (samples, channels)
            if len(audio_data.shape) == 1:
                audio_data = audio_data.reshape(-1, 1)

            # Create AudioFrame for aiortc
            # aiortc expects (channels, samples) format
            audio_transposed = audio_data.T
            av_frame = AudioFrame.from_ndarray(audio_transposed, layout='mono' if self.channels == 1 else 'stereo')

            # Set audio properties
            av_frame.sample_rate = self.sample_rate
            av_frame.pts = self.sample_count

            self.sample_count += len(audio_data)

            return av_frame

        except Exception as e:
            logger.error(f"Error in AudioCaptureStreamTrack.recv(): {e}")
            # Return silence on error
            silence = np.zeros((self.chunk_size, self.channels), dtype=np.int16)
            silence_transposed = silence.T
            av_frame = AudioFrame.from_ndarray(silence_transposed, layout='mono' if self.channels == 1 else 'stereo')
            av_frame.sample_rate = self.sample_rate
            av_frame.pts = self.sample_count
            self.sample_count += len(silence)
            return av_frame
