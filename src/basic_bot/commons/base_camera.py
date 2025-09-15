"""
This was originally pilfered from
https://github.com/adeept/Adeept_RaspTank/blob/a6c45e8cc7df620ad8977845eda2b839647d5a83/server/base_camera.py

Which looks like it was in turn pilfered from
https://blog.miguelgrinberg.com/post/flask-video-streaming-revisited

Thank you, @adeept and @miguelgrinberg!
"""

import time
import threading
from typing import Generator, Optional, Any

from basic_bot.commons import log
from basic_bot.commons.fps_stats import FpsStats

try:
    from greenlet import getcurrent as get_ident  # type: ignore
except ImportError:
    try:
        from thread import get_ident  # type: ignore
    except ImportError:
        from _thread import get_ident


class CameraEvent(object):
    """
    An Event-like class that signals all active clients when a new frame is
    available.
    """

    def __init__(self) -> None:
        # Dictionary mapping thread IDs to [event, timestamp] tuples
        self.events: dict[int, list[Any]] = {}

    def wait(self) -> bool:
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self) -> None:
        """Invoked by the camera thread when a new frame is available."""
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


class BaseCamera(object):
    """
    BaseCamera is an abstract base class that for camera implementations.  It
    creates a background thread that reads frames from the camera and signals
    when a new frame is available.
    """

    thread: Optional[threading.Thread] = (
        None  # background thread that reads frames from camera
    )
    frame: Optional[bytes] = None  # current frame is stored here by background thread

    event = CameraEvent()
    fps_stats = FpsStats()

    is_stopped = False

    def __init__(self) -> None:
        """Start the background camera thread if it isn't running yet."""
        if BaseCamera.thread is None:
            # start background frame thread
            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            # # wait until frames are available
            # while self.get_frame() is None:
            #     time.sleep(0)

    def get_frame(self) -> Optional[bytes]:
        """Return the current camera frame."""
        # wait for a signal from the camera thread
        BaseCamera.event.wait()
        BaseCamera.event.clear()

        return BaseCamera.frame

    def stop(self):
        BaseCamera.is_stopped = True

    @staticmethod
    def frames() -> Generator[bytes, None, None]:
        """ "Generator that returns frames from the camera."""
        raise RuntimeError("Must be implemented by subclasses.")

    @classmethod
    def stats(cls) -> dict[str, float]:
        """Return the fps stats dictionary."""
        return cls.fps_stats.stats()

    @classmethod
    def _thread(cls) -> None:
        """Camera background thread."""
        log.info("Starting camera thread.")

        frames_iterator = cls.frames()
        for frame in frames_iterator:
            if BaseCamera.is_stopped:
                log.debug("Stopping camera thread")
                break
            BaseCamera.frame = frame
            BaseCamera.event.set()  # send signal to clients

            BaseCamera.fps_stats.increment()
            time.sleep(0)

        log.info("Base camera thread stopped.")
