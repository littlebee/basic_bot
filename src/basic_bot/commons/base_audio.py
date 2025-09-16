"""
Base audio interface for basic_bot audio capture.

This module provides the abstract base class for audio capture implementations.
Different audio backends (PyAudio, ALSA, etc.) should inherit from BaseAudio.
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class BaseAudio(ABC):
    """Abstract base class for audio capture implementations."""

    @abstractmethod
    def get_audio_frame(self) -> Optional[np.ndarray]:
        """
        Get the next audio frame.

        Returns:
            numpy array of audio samples, or None if no frame available.
            Format: int16 samples, shape depends on channels (mono: (N,), stereo: (N, 2))
        """
        pass

    @abstractmethod
    def get_sample_rate(self) -> int:
        """Get the audio sample rate in Hz."""
        pass

    @abstractmethod
    def get_channels(self) -> int:
        """Get the number of audio channels (1 for mono, 2 for stereo)."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start audio capture."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop audio capture."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if audio capture is currently running."""
        pass

    def stats(self) -> dict:
        """Return audio capture statistics."""
        return {"frames_captured": 0, "errors": 0}
