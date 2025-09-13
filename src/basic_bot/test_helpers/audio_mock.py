"""
Mock audio capture implementation for testing.

This provides fake audio data for testing purposes, similar to camera_mock.py.
Generates sine waves and white noise for realistic audio testing.
"""

import time
import logging
import numpy as np
from typing import Generator

from basic_bot.commons.base_audio import BaseAudio

logger = logging.getLogger(__name__)

class AudioCapture(BaseAudio):
    """Mock implementation of audio capture that generates test audio signals."""

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def frames() -> Generator[np.ndarray, None, None]:
        """Generator that produces mock audio frames."""
        logger.info("Starting mock audio capture")

        sample_rate = AudioCapture.get_sample_rate()
        channels = AudioCapture.get_channels()
        chunk_size = AudioCapture.get_chunk_size()

        # Parameters for test audio generation
        frequency = 440.0  # A4 note
        amplitude = 0.3
        phase = 0.0
        noise_level = 0.05

        logger.info(f"Mock audio: {sample_rate}Hz, {channels} channel(s), chunk size {chunk_size}")
        logger.info(f"Generating {frequency}Hz sine wave with {noise_level} noise level")

        frame_count = 0

        while True:
            try:
                # Calculate time values for this chunk
                t_start = frame_count * chunk_size / sample_rate
                t_end = (frame_count + 1) * chunk_size / sample_rate
                t = np.linspace(t_start, t_end, chunk_size, endpoint=False)

                # Generate sine wave
                sine_wave = amplitude * np.sin(2 * np.pi * frequency * t + phase)

                # Add some white noise for realism
                noise = noise_level * np.random.normal(0, 1, chunk_size)
                audio_signal = sine_wave + noise

                # Convert to 16-bit integers (similar to real audio)
                audio_int16 = (audio_signal * 32767).astype(np.int16)

                # Shape for mono/stereo
                if channels == 1:
                    audio_frame = audio_int16.reshape(-1, 1)
                else:
                    # For stereo, duplicate the signal
                    audio_frame = np.column_stack([audio_int16, audio_int16])

                yield audio_frame

                frame_count += 1

                # Simulate real-time capture timing
                # Each chunk represents chunk_size/sample_rate seconds
                chunk_duration = chunk_size / sample_rate
                time.sleep(chunk_duration)

                # Vary the frequency slightly over time for more interesting test data
                if frame_count % 100 == 0:  # Every ~2.3 seconds at 44.1kHz
                    frequency = 440.0 + 50.0 * np.sin(frame_count * 0.01)
                    logger.debug(f"Adjusted frequency to {frequency:.1f}Hz")

            except Exception as e:
                logger.error(f"Error generating mock audio frame: {e}")
                break

        logger.info("Mock audio capture stopped")

# Alias for consistency with camera module pattern
Audio = AudioCapture
