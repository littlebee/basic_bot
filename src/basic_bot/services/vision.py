#!/usr/bin/env python3
"""
Provide image feed and object recognition based on open-cv for the
video capture input.  This service will provide a list of objects
and their bounding boxes in the image feed via central hub.

## Video Feed

A video feed is provided via http://<ip>:<port>/video_feed that
can be used as the `src` attribute to an HTML 'img' element.
The image feed is a multipart jpeg stream (for now; TODO: reassess this).
Assuming that the vision service is running on the same host machine as the browser client
location, you can do something like:
```html
<img src="http://localhost:5001/video_feed" />
```
## Object Recognition

The following data is provided to central_hub as fast as image capture and
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

## Video Recording

To use the video recording feature, you must have the `ffmpeg` command
and the libx264-dev library installed on the host machine:

```
sudo apt install -y ffmpeg libx264-dev
```

The video feed can be recorded using the `record_video` REST API.
The video is recorded in the BB_VIDEO_PATH directory. Example:

```sh
curl http://localhost:5801/record_video
```
where
- `localhost` is replaced by the IP address of the host running the vision service.
- `5801` is the port the vision service is running on (default).  See `BB_VISION_PORT`
in the configuration docs.

Filename of the saved file is the current date and time in the format
`YYYYMMDD-HHMMSS.mp4`.

## Origin

Some of this code was originally pilfered from
https://github.com/adeept/Adeept_RaspTank/blob/a6c45e8cc7df620ad8977845eda2b839647d5a83/server/app.py

Which looks like it was in turn pilfered from
https://blog.miguelgrinberg.com/post/flask-video-streaming-revisited

Thank you, @adeept and @miguelgrinberg!
"""
import asyncio
import importlib
import json
import logging
import os
import threading
import sys
import time

from aiohttp import web

import cv2

from basic_bot.commons import constants as c, log, messages, vid_utils

from basic_bot.commons.hub_state import HubState
from basic_bot.commons.hub_state_monitor import HubStateMonitor
from basic_bot.commons.base_camera import BaseCamera
from basic_bot.commons.webrtc_offer import respond_to_offer


if not c.BB_DISABLE_RECOGNITION_PROVIDER:
    from basic_bot.commons.recognition_provider import RecognitionProvider

from typing import Generator

# TODO : at least remove log level debug here.  this is mainly for debugging
#  WebRTC and aiortc
logging.basicConfig(
    # Set the level to DEBUG for maximum verbosity, but be warned, aiortc
    # makes a lot of noise when streaming
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


# TODO : maybe using HubStateMonitor as just a means of publishing
# state updates (without any actual monitoring) should be composed
# into a separate class, like maybe HubStatePublisher.
hub = HubStateMonitor(HubState({}), "vision", [])
hub.start()

# when running tests, assume we are headless and use the
# mock camera which provides random images that should
# be half with pet in image and half without pet in image
if c.BB_ENV == "test":
    camera_lib = "basic_bot.test_helpers.camera_mock"
else:
    camera_lib = c.BB_CAMERA_MODULE

log.info(f"loading camera module: {camera_lib}")
camera_module = importlib.import_module(camera_lib)
camera = camera_module.Camera()  # type: ignore

if not c.BB_DISABLE_RECOGNITION_PROVIDER:
    recognition = RecognitionProvider(camera)


def gen_rgb_video(camera: BaseCamera) -> Generator[bytes, None, None]:
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()

        jpeg = cv2.imencode(".jpg", frame)[1].tobytes()  # type: ignore
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")


# TODO : maybe move these to aiortc web utils file (modeled after commons/web_utils)
def json_response(status, data):
    """Return a JSON response using aiortc web."""
    return web.Response(
        status=status,
        content_type="application/json",
        text=json.dumps(data),
    )


def respond_ok(data=None):
    """Return a JSON response with status ok."""
    return json_response(200, {"status": "ok", "data": data})


def respond_file(path, filename, content_type=None):
    log.info(f"sending file: {filename} from {path}")
    try:
        content = open(os.path.join(path, filename), "br").read()
    except FileNotFoundError as e:
        log.info(f"Error: File not found. {e}")
        return web.Response(status=404, text="File not found")

    return web.Response(body=content, content_type=content_type)


# @app.route("/video_feed")
# def video_feed() -> Response:
#     """Video streaming route. Put this in the src attribute of an img tag."""
#     return web.Response(
#         gen_rgb_video(camera), mimetype="multipart/x-mixed-replace; boundary=frame"
#     )


# @app.route("/stats")
def send_stats(_request):
    """Return the FPS and other stats of the vision service."""
    return respond_ok(
        {
            "capture": BaseCamera.stats(),
            "recognition": (
                "disabled"
                if c.BB_DISABLE_RECOGNITION_PROVIDER
                else RecognitionProvider.stats()
            ),
        },
    )


# @app.route("/pause_recognition")
def pause_recognition(_request):
    """Use a GET request to pause the recognition provider."""
    if c.BB_DISABLE_RECOGNITION_PROVIDER:
        return web.Response(status=404, text="recognition provider is disabled")

    recognition.pause()
    return respond_ok()


# @app.route("/resume_recognition")
def resume_recognition(_request):
    """Use a GET request to resume the recognition provider."""
    if c.BB_DISABLE_RECOGNITION_PROVIDER:
        return web.Response(status=404, text="recognition provider disabled")

    return respond_ok()


last_recording_started_at = time.time()
last_record_duration: float = 0


# @app.route("/record_video")
def record_video(request):
    """Record the video feed to a file."""
    global last_recording_started_at, last_record_duration

    if time.time() - last_recording_started_at < last_record_duration:
        return web.Response(status=304, text="already recording")

    duration = float(request.args.get("duration", "10"))
    last_recording_started_at = time.time()
    last_record_duration = duration
    threading.Thread(target=record_video_thread, args=(duration,)).start()

    return respond_ok()


def record_video_thread(duration: float) -> None:
    try:
        asyncio.run(
            messages.send_update_state(
                hub.connected_socket, {"vision": {"recording": True}}
            )
        )
        vid_utils.record_video(camera, duration)
    except Exception as e:
        log.error(f"error recording video: {e}")
    finally:
        asyncio.run(
            messages.send_update_state(
                hub.connected_socket, {"vision": {"recording": False}}
            )
        )


# @app.route("/recorded_video")
def recorded_video(_request):
    """
    Returns json array of string filenames (without extension) of all
    recorded video files.   The filenames can be used to download the
    using a url like `http://<ip>:<port>/recorded_video/<filename>.mp4`
    or `http://<ip>:<port>/recorded_video/<filename>.jpg` for the
    thumbnail image.
    """
    return respond_ok(vid_utils.get_recorded_videos())


# @app.route("/recorded_video/<filename>")
def get_recorded_video_file(request):
    """
    Sends a recorded video file.
    """
    filename = request.match_info["filename"]
    video_path = os.path.realpath(c.BB_VIDEO_PATH)
    return respond_file(video_path, filename)


# @app.route("/ping")
def ping(_request) -> web.Response:
    return respond_ok("pong")


# @app.route("/webrtc_test")
def get_webrtc_test_page(_request):
    return respond_file("./public", "webrtc_test.html", content_type="text/html")


# @app.route("/webrtc_test_client.js")
def get_webrtc_test_client(_request):
    return respond_file(
        "./public", "webrtc_test_client.js", content_type="application/javascript"
    )


def main() -> None:
    app = web.Application()
    # app.on_shutdown.append(on_shutdown)

    # routes
    app.router.add_get("/stats", send_stats)
    app.router.add_get("/pause_recognition", pause_recognition)
    app.router.add_get("/resume_recognition", resume_recognition)
    app.router.add_get("/record_video", record_video)
    app.router.add_get("/recorded_video", recorded_video)
    app.router.add_get("/recorded_video/{filename}", get_recorded_video_file)
    app.router.add_post("/offer", respond_to_offer)

    # for testing only
    app.router.add_get("/", get_webrtc_test_page)
    app.router.add_get("/webrtc_test.html", get_webrtc_test_page)
    app.router.add_get("/webrtc_test_client.js", get_webrtc_test_client)
    # app.router.add_post("/offer", offer)

    log.info(f"starting vision webhost on {c.BB_VISION_PORT}")
    web.run_app(
        app,
        access_log=None,
        host="0.0.0.0",
        port=c.BB_VISION_PORT,
        # ssl_context=ssl_context,
    )


if __name__ == "__main__":
    main()
