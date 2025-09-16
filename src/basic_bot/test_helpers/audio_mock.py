"""
Mock audio implementation for testing purposes.

This module provides a mock audio source that generates synthetic audio data
for testing without requiring actual hardware or PyAudio.
"""

import numpy as np
from typing import Optional

from basic_bot.commons import log
from basic_bot.commons.base_audio import BaseAudio


class Audio(BaseAudio):
    """Mock audio implementation for testing."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_size: int = 1024):
        """
        Initialize mock audio source.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of channels (1=mono, 2=stereo)
            chunk_size: Number of frames per buffer
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self._running = False
        self._frames_captured = 0
        self._errors = 0
        self._phase = 0.0  # For sine wave generation

        log.info(f"Mock audio initialized - Sample rate: {sample_rate}Hz, Channels: {channels}")

    def start(self) -> None:
        """Start mock audio capture."""
        self._running = True
        log.info("Mock audio capture started")

    def stop(self) -> None:
        """Stop mock audio capture."""
        self._running = False
        log.info("Mock audio capture stopped")

    def get_audio_frame(self) -> Optional[np.ndarray]:
        """
        Generate mock audio frame with a simple sine wave.

        Returns:
            numpy array of int16 audio samples, or None if not running
        """
        if not self._running:
            return None

        # Generate a 440Hz sine wave (A note)
        frequency = 440.0
        duration = self.chunk_size / self.sample_rate

        # Generate time array for this chunk
        t = np.linspace(self._phase, self._phase + duration, self.chunk_size, endpoint=False)

        # Generate sine wave
        amplitude = 0.1  # Low amplitude to avoid loud audio during testing
        sine_wave = amplitude * np.sin(2 * np.pi * frequency * t)

        # Convert to int16 format
        audio_samples = (sine_wave * 32767).astype(np.int16)

        # Handle stereo
        if self.channels == 2:
            # Create stereo by duplicating mono signal
            audio_samples = np.column_stack((audio_samples, audio_samples))

        # Update phase for continuous waveform
        self._phase += duration
        if self._phase > 1.0:  # Reset phase periodically to avoid precision issues
            self._phase -= 1.0

        self._frames_captured += 1
        return audio_samples

    def get_sample_rate(self) -> int:
        """Get the audio sample rate in Hz."""
        return self.sample_rate

    def get_channels(self) -> int:
        """Get the number of audio channels."""
        return self.channels

    def is_running(self) -> bool:
        """Check if audio capture is currently running."""
        return self._running

    def stats(self) -> dict:
        """Return audio capture statistics."""
        return {
            "frames_captured": self._frames_captured,
            "errors": self._errors,
            "mock_audio": True,
            "sample_rate": self.sample_rate,
            "channels": self.channels
        }
