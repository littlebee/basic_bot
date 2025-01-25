"""
This class detects objects in frames it gets from the  camera object passed to
the constructor.

A thread is created that does the heavy lifting of detecting objects and updates
a class var that contains the last faces detected. This allows the thread providing
the video feed to stream at 30fps while detect frames lag behind
"""

import time
import threading
import asyncio
import websockets
import traceback

from basic_bot.commons import constants, messages, log
from basic_bot.commons.fps_stats import FpsStats

# TODO: decide whether to optionally use pytorch or tflite
#   Maybe do another performance test and update
# from .pytorch_detect import PytorchDetect

from .tflite_detect import TFLiteDetect

"""
See [issue #1](https://github.com/littlebee/scatbot-edge-ai-shootout/issues/1)
about support for pytorch
"""
WHICH_DETECTOR = "tflite"


class RecognitionProvider:
    thread = None  # background thread that reads frames from camera
    camera = None
    last_objects_seen = []
    fps_stats = FpsStats()
    last_frame_duration = 0
    last_dimensions = {}
    total_objects_detected = 0

    next_objects_event = threading.Event()
    pause_event = threading.Event()

    def __init__(self, camera):
        RecognitionProvider.camera = camera
        if RecognitionProvider.thread is None:
            RecognitionProvider.thread = threading.Thread(target=self._thread)
            RecognitionProvider.thread.start()

        self.resume()

    def get_objects(self):
        return RecognitionProvider.last_objects_seen

    def get_next_objects(self):
        RecognitionProvider.next_objects_event.wait()
        RecognitionProvider.next_objects_event.clear()
        return self.get_objects()

    def pause(self):
        RecognitionProvider.pause_event.clear()

    def resume(self):
        RecognitionProvider.pause_event.set()

    @classmethod
    def stats(cls):
        return {
            "last_objects_seen": cls.last_objects_seen,
            "fps": cls.fps_stats.stats(),
            "total_objects_detected": cls.total_objects_detected,
            "last_frame_duration": cls.last_frame_duration,
        }

    @classmethod
    async def provide_state(cls):
        cls.fps_stats.start()

        while True:
            try:
                detector = TFLiteDetect()

                # TODO : see https://github.com/littlebee/scatbot-edge-ai-shootout/issues/1
                # if WHICH_DETECTOR == "tflite":
                #     detector = TFLiteDetect()
                # else:
                #     detector = PytorchDetect()

                log.info(
                    f"recognition connecting to hub central at {constants.BB_HUB_URI}"
                )
                async with websockets.connect(constants.BB_HUB_URI) as websocket:
                    await messages.send_identity(websocket, "recognition")
                    while True:
                        # if not cls.pause_event.is_set():
                        #     log.info(f"recognition waiting on pause event")
                        #     cls.pause_event.wait()
                        #     log.info(f"recognition resumed")

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
    def _thread(cls):
        log.info("Starting recognition thread.")
        asyncio.run(cls.provide_state())
