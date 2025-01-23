#!/usr/bin/env python3
"""
    Provide image feed and object recognition based on open-cv for the
    video capture input.  This service will provide a list of objects
    and their bounding boxes in the image feed via central hub

    A vision feed is provided via http://<ip>:<port>/video_feed that
    can be used in an HTML 'img' element.  The image feed is a multipart
    jpeg stream (for now; TODO: reassess this).  Assuming that the vision
    service is running on the same host machine as the browser client
    location, you can do something like:
    ```html
    <img src="http://localhost:5001/video_feed" />
    ```

    The following data is provided to central_hug as fast as image capture and
    recognition can be done:

    ```json
    {
        "recognition": [
            {
                "bounding_box": [x1, y1, x2, y2],
                "classification": "person",
                "confidence": 0.99
            },
            {
                "bounding_box": [x1, y1, x2, y2],
                "classification": "dog",
                "confidence": 0.75
            }
        ]
    }
    ```
    The [x1, y1, x2, y2] bounding box above is actually sent as
    the numeric values of the bounding box in the image.

Origin:
    This was originally pilfered from
    https://github.com/adeept/Adeept_RaspTank/blob/a6c45e8cc7df620ad8977845eda2b839647d5a83/server/app.py

    Which looks like it was in turn pilfered from
    https://blog.miguelgrinberg.com/post/flask-video-streaming-revisited

    Thank you, @adeept and @miguelgrinberg!
"""

import os
import threading

from flask import Flask, Response, abort
from flask_cors import CORS

import cv2

from basic_bot.commons import constants as c, web_utils, log
from basic_bot.commons.base_camera import BaseCamera
from basic_bot.commons.camera_opencv import OpenCvCamera
from basic_bot.commons.recognition_provider import RecognitionProvider


app = Flask(__name__)
CORS(app, supports_credentials=True)

camera = OpenCvCamera()

if not c.BB_DISABLE_RECOGNITION_PROVIDER:
    recognition = RecognitionProvider(camera)


def gen_rgb_video(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()

        jpeg = cv2.imencode(".jpg", frame)[1].tobytes()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")


@app.route("/video_feed")
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(
        gen_rgb_video(camera), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/stats")
def send_stats():
    (cpu_temp, *rest) = [
        int(i) / 1000
        for i in os.popen("cat /sys/devices/virtual/thermal/thermal_zone*/temp")
        .read()
        .split()
    ]
    return web_utils.json_response(
        app,
        {
            "capture": BaseCamera.stats(),
            "recognition": (
                "disabled"
                if c.BB_DISABLE_RECOGNITION_PROVIDER
                else RecognitionProvider.stats()
            ),
        },
    )


@app.route("/pauseRecognition")
def pause_recognition():
    if c.BB_DISABLE_RECOGNITION_PROVIDER:
        return abort(404, "recognition provider disabled")

    recognition.pause()
    return web_utils.respond_ok(app)


@app.route("/resumeRecognition")
def resume_recognition():
    if c.BB_DISABLE_RECOGNITION_PROVIDER:
        return abort(404, "recognition provider disabled")

    recognition.resume()
    return web_utils.respond_ok(app)


@app.route("/ping")
def ping():
    return web_utils.respond_ok(app, "pong")


class webapp:
    def __init__(self):
        self.camera = camera

    def thread(self):
        log(f"starting vision webhost on {c.BB_VISION_PORT}")
        app.run(host="0.0.0.0", port=c.BB_VISION_PORT, threaded=True)

    def start_thread(self):
        # Define a thread for flask
        thread = threading.Thread(target=self.thread)
        #    'True' means it is a front thread, it would close when the mainloop() closes
        thread.setDaemon(False)
        thread.start()  # Thread starts


def main():
    flask_app = webapp()
    flask_app.start_thread()


if __name__ == "__main__":
    main()
