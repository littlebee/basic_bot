#!/usr/bin/env python3
"""
Provide image feed and object recognition based on open-cv for the
video capture input.  This service will provide a list of objects
and their bounding boxes in the image feed via central hub.

## MJPEG Video Feed

A Motion JPEG (MJPEG) video feed is provided via http://<ip>:<port>/video_feed that
can be used as the `src` attribute to an HTML 'img' element.
The image feed is a multipart jpeg stream (for now; TODO: reassess this).
Assuming that the vision service is running on the same host machine as the browser client
location, you can do something like:
```html
<img src="http://localhost:5001/video_feed" />
```

## WebRTC video supported

The vision service when running will respond to WebRTC offers a allow
streaming video from the robot camera.

It should not be neccessary to use both MJPEG and WebRTC streaming and
WebRTC video should be preferred for its lower latency and less overhead
needed to encode jpg frames for MJPEG streaming.

See, [webrtc_test_client.js](https://github.com/littlebee/basic_bot/blob/0808450a5d220feaa1efdfcb0738216af89f0f75/src/basic_bot/public/webrtc_test_client.js)
and associated .html for example of how to use WebRTC stream from browser.

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
import logging
import os
import signal
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response, StreamResponse
import aiohttp_cors

from basic_bot.commons import constants as c, log, messages, vid_utils
from basic_bot.commons.web_utils_aiohttp import (
    json_response,
    respond_ok,
    respond_file,
    AccessLogger,
)

from basic_bot.commons.hub_state import HubState
from basic_bot.commons.hub_state_monitor import HubStateMonitor
from basic_bot.commons.base_camera import BaseCamera
from basic_bot.commons.webrtc_server import WebrtcPeers
from basic_bot.commons.mjpeg_video import MjpegVideo, stream_mjpeg_video

if c.BB_DISABLE_RECOGNITION_PROVIDER:
    log.info("Recognition provider is disabled (BB_DISABLE_RECOGNITION_PROVIDER)")
else:
    from basic_bot.commons.recognition_provider import RecognitionProvider

# this is mainly for debugging WebRTC and aiortc
logging.basicConfig(
    # Set the level to DEBUG for maximum verbosity, but be warned, aiortc
    # makes a lot of noise when streaming
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

is_stopping = False

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
camera: BaseCamera = camera_module.Camera()

log.info("Initializing webrtc offers server")
webrtc_peers = WebrtcPeers(camera)

log.info("Initializing MJPEG streaming")
mjpeg_video = MjpegVideo(camera)

if not c.BB_DISABLE_RECOGNITION_PROVIDER:
    recognition = RecognitionProvider(camera)

script_directory = os.path.abspath(os.path.dirname(__file__))
public_directory = os.path.abspath(os.path.join(script_directory, "../public"))


# dumps the stack traces of all threads to the log
def dump_thread_stacks() -> None:
    for thread_id, frame in sys._current_frames().items():
        log.info("Thread %s:" % thread_id)
        traceback.print_stack(frame)


# listen for signal USR1 to dump thread stacks to log
signal.signal(signal.SIGUSR1, lambda _signum, _frame: dump_thread_stacks())


# @app.route("/video_feed")
async def video_feed(request: Request) -> StreamResponse:
    """Video streaming route. Put this in the src attribute of an img tag."""
    # asyncio.create_task(stream_mjpeg_video(request, camera))
    # return await mjpeg_video.stream_mjpeg_video(request, camera)

    boundary_marker = "--frame"
    response: web.StreamResponse = web.StreamResponse(
        status=200,
        reason="OK",
        headers={
            "Content-Type": f"multipart/x-mixed-replace;boundary={boundary_marker}"
        },
    )
    await response.prepare(request)

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        request.app["executor"],
        stream_mjpeg_video,
        response,
        camera,
        boundary_marker,
    )
    return response


# @app.route("/stats")
async def send_stats(_request: Request) -> Response:
    """Return the FPS and other stats of the vision service."""
    return json_response(
        200,
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
async def pause_recognition(_request: Request) -> Response:
    """Use a GET request to pause the recognition provider."""
    if c.BB_DISABLE_RECOGNITION_PROVIDER:
        return web.Response(status=404, text="recognition provider is disabled")

    recognition.pause()
    return respond_ok()


# @app.route("/resume_recognition")
async def resume_recognition(_request: Request) -> Response:
    """Use a GET request to resume the recognition provider."""
    if c.BB_DISABLE_RECOGNITION_PROVIDER:
        return web.Response(status=404, text="recognition provider disabled")
    recognition.resume()
    return respond_ok()


last_recording_started_at = time.time()
last_record_duration: float = 0


# @app.route("/record_video")
async def record_video(request: Request) -> Response:
    """Record the video feed to a file."""
    global last_recording_started_at, last_record_duration

    if time.time() - last_recording_started_at < last_record_duration:
        return web.Response(status=304, text="already recording")

    duration = float(request.rel_url.query.get("duration", "10"))
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
        if c.BB_LEGACY_RECORD_VIDEO:
            vid_utils.record_video(camera, duration)
        else:
            vid_utils.record_webrtc_video(camera, duration)

    except Exception as e:
        log.error(f"error recording video: {e}")

    finally:
        if not is_stopping:
            asyncio.run(
                messages.send_update_state(
                    hub.connected_socket, {"vision": {"recording": False}}
                )
            )


# @app.route("/recorded_video")
async def recorded_video(_request: Request) -> Response:
    """
    Returns json array of string filenames (without extension) of all
    recorded video files.   The filenames can be used to download the
    using a url like `http://<ip>:<port>/recorded_video/<filename>.mp4`
    or `http://<ip>:<port>/recorded_video/<filename>.jpg` for the
    thumbnail image.
    """
    return json_response(200, vid_utils.get_recorded_videos())


# @app.route("/recorded_video/<filename>")
async def get_recorded_video_file(request: Request) -> Response:
    """
    Sends a recorded video file.
    """
    filename = request.match_info["filename"]
    content_type = "video/mp4" if filename.endswith(".mp4") else "image/jpeg"
    video_path = os.path.realpath(c.BB_VIDEO_PATH)
    return respond_file(video_path, filename, content_type=content_type)


# @app.route("/ping")
async def ping(_request: Request) -> Response:
    return respond_ok("pong")


# @app.route("/webrtc_test")
async def get_webrtc_test_page(_request: Request) -> Response:
    return respond_file(public_directory, "webrtc_test.html", content_type="text/html")


# @app.route("/webrtc_test_client.js")
async def get_webrtc_test_client(_request: Request) -> Response:
    return respond_file(
        public_directory, "webrtc_test_client.js", content_type="application/javascript"
    )


async def on_shutdown(_app: web.Application) -> None:
    global is_stopping
    is_stopping = True
    log.info("vision service shutting down...")

    await webrtc_peers.close_all_connections()
    mjpeg_video.stop()
    if not c.BB_DISABLE_RECOGNITION_PROVIDER:
        recognition.stop()
    camera.stop()
    hub.stop()


def main() -> None:
    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app["executor"] = ThreadPoolExecutor(max_workers=3)
    # routes
    app.router.add_get("/stats", send_stats)
    app.router.add_get("/pause_recognition", pause_recognition)
    app.router.add_get("/resume_recognition", resume_recognition)
    app.router.add_get("/record_video", record_video)
    app.router.add_get("/recorded_video", recorded_video)
    app.router.add_get("/recorded_video/{filename}", get_recorded_video_file)
    # this is for handling WebRTC video handshake
    app.router.add_post("/offer", webrtc_peers.respond_to_offer)
    # this is the older and deprecated MJPEG video feed
    app.router.add_get("/video_feed", video_feed)

    # for testing only
    app.router.add_get("/", get_webrtc_test_page)
    app.router.add_get("/webrtc_test.html", get_webrtc_test_page)
    app.router.add_get("/webrtc_test_client.js", get_webrtc_test_client)
    # app.router.add_post("/offer", offer)

    # Configure CORS with a default setup for all routes.
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*",
            )
        },
    )
    for route in list(app.router.routes()):
        cors.add(route)

    log.info(f"starting vision webhost on {c.BB_VISION_PORT}")
    web.run_app(
        app,
        access_log_class=AccessLogger,
        host="0.0.0.0",
        port=c.BB_VISION_PORT,
        # ssl_context=ssl_context,
    )


if __name__ == "__main__":
    main()
