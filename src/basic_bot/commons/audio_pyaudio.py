"""
PyAudio-based audio capture for cross-platform microphone access.

This module provides audio capture using PyAudio, which works on Windows, macOS, and Linux.
"""

from typing import Optional, TYPE_CHECKING, Any
import numpy as np

from basic_bot.commons import log
from basic_bot.commons.base_audio import BaseAudio

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None  # type: ignore
    PYAUDIO_AVAILABLE = False
    log.error("PyAudio not available. Audio capture will be disabled.")

if TYPE_CHECKING and not PYAUDIO_AVAILABLE:
    import pyaudio  # noqa: F401


class Audio(BaseAudio):
    """PyAudio-based audio capture implementation."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_size: int = 1024):
        """
        Initialize PyAudio audio capture.

        Args:
            sample_rate: Audio sample rate in Hz (default: 16000 for WebRTC)
            channels: Number of channels (1=mono, 2=stereo)
            chunk_size: Number of frames per buffer
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16 if PYAUDIO_AVAILABLE else 0

        self._pyaudio: Any = None
        self._stream: Optional['pyaudio.Stream'] = None
        self._running = False
        self._frames_captured = 0
        self._errors = 0

        if not PYAUDIO_AVAILABLE:
            log.error("PyAudio not available - audio capture disabled")
            return

        try:
            self._pyaudio = pyaudio.PyAudio()

            # Log available audio devices for debugging
            device_count = self._pyaudio.get_device_count()
            log.info(f"PyAudio found {device_count} audio devices:")

            default_input = self._pyaudio.get_default_input_device_info()
            log.info(f"Default input device: {default_input['name']} (index: {default_input['index']})")

            # Log first few input devices
            for i in range(min(5, device_count)):
                device_info = self._pyaudio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    log.info(f"Input device {i}: {device_info['name']} (channels: {device_info['maxInputChannels']})")

            log.info(f"PyAudio initialized - Sample rate: {sample_rate}Hz, Channels: {channels}")
        except Exception as e:
            log.error(f"Failed to initialize PyAudio: {e}")
            self._pyaudio = None

    def start(self) -> None:
        """Start audio capture."""
        if not self._pyaudio:
            log.error("Cannot start audio capture - PyAudio not available")
            return

        try:
            # Use default input device explicitly
            default_device = self._pyaudio.get_default_input_device_info()
            device_index = default_device['index']

            log.info(f"Opening audio stream on device {device_index}: {default_device['name']}")

            self._stream = self._pyaudio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            self._running = True
            log.info(f"Audio capture started on device: {default_device['name']}")
        except Exception as e:
            log.error(f"Failed to start audio capture: {e}")
            self._errors += 1

    def stop(self) -> None:
        """Stop audio capture."""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
                self._running = False
                log.info("Audio capture stopped")
            except Exception as e:
                log.error(f"Error stopping audio capture: {e}")
                self._errors += 1

        if self._pyaudio:
            try:
                self._pyaudio.terminate()
                self._pyaudio = None
            except Exception as e:
                log.error(f"Error terminating PyAudio: {e}")

    def get_audio_frame(self) -> Optional[np.ndarray]:
        """
        Get the next audio frame.

        Returns:
            numpy array of int16 audio samples, or None if no frame available
        """
        if not self._running or not self._stream:
            return None

        try:
            audio_data = self._stream.read(self.chunk_size, exception_on_overflow=False)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # Debug: Log audio data characteristics on first few frames
            if self._frames_captured < 3:
                log.info(f"PyAudio frame {self._frames_captured}: raw_len={len(audio_data)}, array_shape={audio_array.shape}, dtype={audio_array.dtype}, min={audio_array.min()}, max={audio_array.max()}")

            if self.channels == 2:
                # Reshape for stereo
                audio_array = audio_array.reshape(-1, 2)

            self._frames_captured += 1
            return audio_array

        except Exception as e:
            log.error(f"Error reading audio frame: {e}")
            self._errors += 1
            return None

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
            "pyaudio_available": PYAUDIO_AVAILABLE
        }
