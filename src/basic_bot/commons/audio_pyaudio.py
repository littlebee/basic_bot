"""
PyAudio-based audio capture implementation for cross-platform audio support.

This implementation uses PyAudio to capture audio from the default microphone.
It works on Windows, macOS, and Linux systems.
"""

import logging
import numpy as np
from typing import Generator

from basic_bot.commons.base_audio import BaseAudio

logger = logging.getLogger(__name__)

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio not available. Audio capture will not work.")


class AudioCapture(BaseAudio):
    """PyAudio implementation of audio capture."""

    def __init__(self) -> None:
        if not PYAUDIO_AVAILABLE:
            logger.error("PyAudio is not available. Cannot initialize audio capture.")
            return

        super().__init__()

    @staticmethod
    def frames() -> Generator[np.ndarray, None, None]:
        """Generator that captures audio frames from the microphone."""
        if not PYAUDIO_AVAILABLE:
            logger.error("PyAudio is not available. Cannot capture audio frames.")
            return

        audio = None
        stream = None

        try:
            # Initialize PyAudio
            audio = pyaudio.PyAudio()

            # Get audio parameters
            sample_rate = AudioCapture.get_sample_rate()
            channels = AudioCapture.get_channels()
            chunk_size = AudioCapture.get_chunk_size()

            logger.info(f"Starting PyAudio capture: {sample_rate}Hz, {channels} channel(s), chunk size {chunk_size}")

            # Find default input device
            default_device = None
            try:
                default_device = audio.get_default_input_device_info()
                logger.info(f"Using default input device: {default_device['name']}")
            except Exception as e:
                logger.error(f"Could not get default input device: {e}")
                return

            # Open audio stream
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk_size,
                input_device_index=int(default_device['index']) if default_device else None
            )

            logger.info("Audio stream opened successfully")

            while True:
                try:
                    # Read audio data
                    audio_data = stream.read(chunk_size, exception_on_overflow=False)

                    # Convert to numpy array
                    # PyAudio returns signed 16-bit integers
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)

                    # Reshape for mono/stereo
                    if channels == 1:
                        audio_frame = audio_array.reshape(-1, 1)
                    else:
                        audio_frame = audio_array.reshape(-1, channels)

                    yield audio_frame

                except Exception as e:
                    logger.error(f"Error reading audio data: {e}")
                    break

        except Exception as e:
            logger.error(f"Error initializing PyAudio: {e}")
        finally:
            # Clean up
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                    logger.info("Audio stream closed")
                except Exception as e:
                    logger.error(f"Error closing audio stream: {e}")

            if audio:
                try:
                    audio.terminate()
                    logger.info("PyAudio terminated")
                except Exception as e:
                    logger.error(f"Error terminating PyAudio: {e}")


# Alias for consistency with camera module pattern
Audio = AudioCapture
