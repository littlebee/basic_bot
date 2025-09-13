"""
Abstract base class for audio capture implementations.

This follows the same pattern as base_camera.py to provide a consistent
interface for audio capture across different platforms and implementations.
"""

import time
import threading
import logging
from typing import Generator, Optional, Any
import numpy as np

from basic_bot.commons.fps_stats import FpsStats

logger = logging.getLogger(__name__)

try:
    from greenlet import getcurrent as get_ident  # type: ignore
except ImportError:
    try:
        from thread import get_ident  # type: ignore
    except ImportError:
        from _thread import get_ident

class AudioEvent(object):
    """
    An Event-like class that signals all active clients when a new audio frame is
    available. Similar to CameraEvent but for audio data.
    """

    def __init__(self) -> None:
        # Dictionary mapping thread IDs to [event, timestamp] tuples
        self.events: dict[int, list[Any]] = {}

    def wait(self) -> bool:
        """Invoked from each client's thread to wait for the next audio frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self) -> None:
        """Invoked by the audio thread when a new frame is available."""
        now = time.time()
        remove: Optional[int] = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self) -> None:
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()

class BaseAudio(object):
    """
    BaseAudio is an abstract base class for audio capture implementations.
    It creates a background thread that reads audio samples and signals
    when new audio data is available.
    """

    thread: Optional[threading.Thread] = None  # background thread that reads audio
    frame: Optional[np.ndarray] = None  # current audio frame stored as numpy array

    event = AudioEvent()
    fps_stats = FpsStats()

    def __init__(self) -> None:
        """Start the background audio thread if it isn't running yet."""
        if BaseAudio.thread is None:
            # start background audio capture thread
            BaseAudio.thread = threading.Thread(target=self._thread)
            BaseAudio.thread.start()

    def get_frame(self) -> Optional[np.ndarray]:
        """Return the current audio frame as numpy array."""
        # wait for a signal from the audio thread
        BaseAudio.event.wait()
        BaseAudio.event.clear()

        return BaseAudio.frame

    @staticmethod
    def get_sample_rate() -> int:
        """Return the sample rate in Hz."""
        return 44100

    @staticmethod
    def get_channels() -> int:
        """Return the number of audio channels."""
        return 1  # Mono for robotics applications

    @staticmethod
    def get_chunk_size() -> int:
        """Return the number of samples per audio frame."""
        return 1024

    @staticmethod
    def frames() -> Generator[np.ndarray, None, None]:
        """Generator that returns audio frames as numpy arrays."""
        raise RuntimeError("Must be implemented by subclasses.")

    @classmethod
    def stats(cls) -> dict[str, float]:
        """Return the fps stats dictionary."""
        return cls.fps_stats.stats()

    @classmethod
    def _thread(cls) -> None:
        """Audio background thread."""
        logger.info("Starting audio capture thread.")

        frames_iterator = cls.frames()
        for frame in frames_iterator:
            BaseAudio.frame = frame
            BaseAudio.event.set()  # send signal to clients

            BaseAudio.fps_stats.increment()
            time.sleep(0)
