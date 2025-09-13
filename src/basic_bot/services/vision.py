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
import os
import threading
import time

from flask import Flask, Response, abort, send_from_directory, request
from flask_cors import CORS

import cv2

from basic_bot.commons import constants as c, web_utils, log, messages, vid_utils

from basic_bot.commons.hub_state import HubState
from basic_bot.commons.hub_state_monitor import HubStateMonitor
from basic_bot.commons.base_camera import BaseCamera
from basic_bot.commons.base_audio import BaseAudio
from basic_bot.commons.recognition_provider import RecognitionProvider
from typing import Generator, Optional

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

# Load audio capture module if not disabled
audio_capture: Optional[BaseAudio] = None
if not c.BB_DISABLE_AUDIO_CAPTURE:
    try:
        audio_lib = c.BB_AUDIO_MODULE
        log.info(f"loading audio module: {audio_lib}")
        audio_module = importlib.import_module(audio_lib)
        audio_capture = audio_module.AudioCapture()  # type: ignore
    except Exception as e:
        log.error(f"Failed to load audio module: {e}")
        log.info("Audio capture disabled due to initialization error")

app = Flask(__name__)
CORS(app, supports_credentials=True)

if not c.BB_DISABLE_RECOGNITION_PROVIDER:
    recognition = RecognitionProvider(camera)

def gen_rgb_video(camera: BaseCamera) -> Generator[bytes, None, None]:
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()

        jpeg = cv2.imencode(".jpg", frame)[1].tobytes()  # type: ignore
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")

@app.route("/video_feed")
def video_feed() -> Response:
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(
        gen_rgb_video(camera), mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/stats")
def send_stats() -> Response:
    """Return the FPS and other stats of the vision service."""
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

@app.route("/pause_recognition")
def pause_recognition() -> Response:
    """Use a GET request to pause the recognition provider."""
    if c.BB_DISABLE_RECOGNITION_PROVIDER:
        return abort(404, "recognition provider disabled")

    recognition.pause()
    return web_utils.respond_ok(app)

@app.route("/resume_recognition")
def resume_recognition() -> Response:
    """Use a GET request to resume the recognition provider."""
    if c.BB_DISABLE_RECOGNITION_PROVIDER:
        return abort(404, "recognition provider disabled")

    recognition.resume()
    return web_utils.respond_ok(app)

last_recording_started_at = time.time()
last_record_duration: float = 0

@app.route("/record_video")
def record_video() -> Response:
    """Record the video feed to a file."""
    global last_recording_started_at, last_record_duration

    if time.time() - last_recording_started_at < last_record_duration:
        return web_utils.respond_not_ok(app, 304, "already recording")

    duration = float(request.args.get("duration", "10"))
    last_recording_started_at = time.time()
    last_record_duration = duration
    threading.Thread(target=record_video_thread, args=(duration,)).start()

    return web_utils.respond_ok(app)

def record_video_thread(duration: float) -> None:
    try:
        asyncio.run(
            messages.send_update_state(
                hub.connected_socket, {"vision": {"recording": True}}
            )
        )

        # Use audio/video recording if audio capture is available
        if audio_capture is not None:
            log.info("Recording video with audio")
            vid_utils.record_video_with_audio(camera, audio_capture, duration)
        else:
            log.info("Recording video only (no audio)")
            vid_utils.record_video(camera, duration)

    except Exception as e:
        log.error(f"error recording video: {e}")
    finally:
        asyncio.run(
            messages.send_update_state(
                hub.connected_socket, {"vision": {"recording": False}}
            )
        )

@app.route("/recorded_video")
def recorded_video() -> Response:
    """
    Returns json array of string filenames (without extension) of all
    recorded video files.   The filenames can be used to download the
    using a url like `http://<ip>:<port>/recorded_video/<filename>.mp4`
    or `http://<ip>:<port>/recorded_video/<filename>.jpg` for the
    thumbnail image.
    """
    return web_utils.json_response(app, vid_utils.get_recorded_videos())

@app.route("/recorded_video/<filename>")
def send_static_js(filename: str) -> Response:
    """
    Sends a recorded video file.
    """
    video_path = os.path.realpath(c.BB_VIDEO_PATH)
    log.info(f"sending recorded video file: {filename} from {video_path}")
    return send_from_directory(video_path, filename)

@app.route("/ping")
def ping() -> Response:
    return web_utils.respond_ok(app, "pong")

@app.route("/webrtc/status")
def webrtc_status() -> Response:
    """Return WebRTC capability status."""
    try:
        # Check if WebRTC dependencies are available
        from basic_bot.commons.webrtc_signaling import AIORTC_AVAILABLE

        status = {
            "webrtc_available": AIORTC_AVAILABLE,
            "audio_enabled": audio_capture is not None,
            "webrtc_port": c.BB_WEBRTC_PORT
        }

        if AIORTC_AVAILABLE:
            status["webrtc_url"] = f"http://{c.BB_VISION_HOST}:{c.BB_WEBRTC_PORT}"

        return web_utils.json_response(app, status)

    except ImportError:
        return web_utils.json_response(app, {
            "webrtc_available": False,
            "error": "WebRTC dependencies not available"
        })

class webapp:
    def thread(self) -> None:
        log.info(f"starting vision webhost on {c.BB_VISION_PORT}")
        app.run(host="0.0.0.0", port=c.BB_VISION_PORT, threaded=True)

    def start_thread(self) -> None:
        # Define a thread for flask
        thread = threading.Thread(target=self.thread)
        thread.setDaemon(False)
        thread.start()

def main() -> None:
    flask_app = webapp()
    flask_app.start_thread()

    # Start WebRTC signaling server if available
    try:
        from basic_bot.commons.webrtc_signaling import create_signaling_app, cleanup_app, AIORTC_AVAILABLE
        from aiohttp import web as aio_web

        if AIORTC_AVAILABLE:
            log.info("Starting WebRTC signaling server")

            # Create WebRTC signaling app
            webrtc_app = create_signaling_app(camera, audio_capture)

            def start_webrtc_server():
                """Start the WebRTC signaling server in a separate thread."""
                import asyncio

                async def run_server():
                    runner = aio_web.AppRunner(webrtc_app)
                    await runner.setup()

                    site = aio_web.TCPSite(runner, host="0.0.0.0", port=c.BB_WEBRTC_PORT)
                    await site.start()

                    log.info(f"WebRTC signaling server started on port {c.BB_WEBRTC_PORT}")

                    # Keep the server running
                    try:
                        while True:
                            await asyncio.sleep(1)
                    except KeyboardInterrupt:
                        log.info("Shutting down WebRTC signaling server")
                    finally:
                        await cleanup_app(webrtc_app)
                        await runner.cleanup()

                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    loop.run_until_complete(run_server())
                finally:
                    loop.close()

            # Start WebRTC server in background thread
            webrtc_thread = threading.Thread(target=start_webrtc_server)
            webrtc_thread.daemon = True
            webrtc_thread.start()

        else:
            log.warning("WebRTC dependencies not available. WebRTC streaming disabled.")

    except ImportError as e:
        log.warning(f"WebRTC not available: {e}")

if __name__ == "__main__":
    main()
