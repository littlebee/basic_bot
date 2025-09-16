import time
import threading
import asyncio
import websockets
import websockets.client
import traceback

from typing import Any, List, Dict, Optional

from basic_bot.commons import constants, messages, log
from basic_bot.commons.fps_stats import FpsStats

# TODO: decide whether to optionally use pytorch or tflite
#   Maybe do another performance test and update
# from .pytorch_detect import PytorchDetect
"""
See [issue #1](https://github.com/littlebee/scatbot-edge-ai-shootout/issues/1)
about support for pytorch
"""

from .tflite_detect import TFLiteDetect

detector = TFLiteDetect()


class RecognitionProvider:
    """
    This singleton class detects objects in frames it gets from the camera
    object passed to the constructor.

    It uses the TFLiteDetect class to detect objects in the frames.

    It sends the detected objects to the central hub via a websocket connection
    using the `recognition` key

    To use, simply instantiate it:

    ```python
    from basic_bot.commons.recognition_provider import RecognitionProvider
    from basic_bot.commons.camera_opencv import OpenCvCamera

    camera = OpenCvCamera()
    recognition_provider = RecognitionProvider(camera)
    ```
    """

    thread: Optional[threading.Thread] = (
        None  # background thread that reads frames from camera
    )
    camera: Any = None
    last_objects_seen: List[Dict[str, Any]] = []
    fps_stats: FpsStats = FpsStats()
    last_frame_duration: float = 0
    last_dimensions: Dict[str, Any] = {}
    total_objects_detected: int = 0

    next_objects_event: threading.Event = threading.Event()
    pause_event: threading.Event = threading.Event()

    def __init__(self, camera: Any) -> None:
        """Constructor"""
        RecognitionProvider.camera = camera
        if RecognitionProvider.thread is None:
            RecognitionProvider.thread = threading.Thread(target=self._thread)
            RecognitionProvider.thread.start()

        self.resume()

    def get_objects(self) -> List[Dict[str, Any]]:
        """Return the last objects seen"""
        return RecognitionProvider.last_objects_seen

    def get_next_objects(self) -> List[Dict[str, Any]]:
        """Wait for and return the next objects seen"""
        RecognitionProvider.next_objects_event.wait()
        RecognitionProvider.next_objects_event.clear()
        return self.get_objects()

    def pause(self) -> None:
        """Pause the recognition thread"""
        RecognitionProvider.pause_event.clear()

    def resume(self) -> None:
        """Resume the recognition thread"""
        RecognitionProvider.pause_event.set()

    @classmethod
    def stats(cls) -> Dict[str, Any]:
        """Return the fps stats dictionary."""
        return {
            "last_objects_seen": cls.last_objects_seen,
            "fps": cls.fps_stats.stats(),
            "total_objects_detected": cls.total_objects_detected,
            "last_frame_duration": cls.last_frame_duration,
        }

    @classmethod
    async def provide_state(cls) -> None:
        previous_objects: List[dict[str, Any]] = []
        while True:
            try:
                log.info(
                    f"recognition connecting to hub central at {constants.BB_HUB_URI}"
                )
                # Handle different websockets library versions
                connect_func = getattr(websockets, 'connect', None) or websockets.client.connect
                async with connect_func(constants.BB_HUB_URI) as websocket:
                    await messages.send_identity(websocket, "recognition")
                    while True:
                        if not cls.pause_event.is_set():
                            log.info("recognition waiting on pause event")
                            cls.pause_event.wait()
                            log.info("recognition resumed")

                        frame = cls.camera.get_frame()

                        t1 = time.time()
                        new_objects = detector.get_prediction(frame)
                        cls.last_frame_duration = time.time() - t1
                        cls.last_objects_seen = new_objects
                        cls.last_dimensions = frame.shape

                        cls.fps_stats.increment()

                        num_objects = len(cls.last_objects_seen)
                        cls.next_objects_event.set()  # send signal to clients
                        cls.total_objects_detected += num_objects

                        if new_objects != previous_objects:
                            previous_objects = new_objects
                            await messages.send_update_state(
                                websocket,
                                {
                                    "recognition": new_objects,
                                },
                            )

                        await asyncio.sleep(0)

                        # time.sleep(0)
            except:
                traceback.print_exc()

            log.info("central_hub socket disconnected.  Reconnecting in 5 sec...")
            time.sleep(5)

    @classmethod
    def _thread(cls) -> None:
        log.info("Starting recognition thread.")
        asyncio.run(cls.provide_state())
