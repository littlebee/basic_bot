import threading

from typing import Generator

import cv2
from flask import Flask, Response
from flask_cors import CORS


from basic_bot.commons import constants as c, log
from basic_bot.commons.base_camera import BaseCamera

# MJPEG video streaming runs on Flask becuase doing it with aiohttp
# was causing issues with the audio streaming via WebRTC when more than
# one MJPEG stream was active.  I'm pretty sure that it was because of
# asyncio starvation.  I'm convinced that running all requests, including
# ones that might block, in the same event loop is a bad idea.
flaskApp = Flask(__name__)
CORS(flaskApp, supports_credentials=True)


class MjpegVideo:
    """
    This class provides support for streaming basic_bot camera frames via
    aiohttp and their MultipartWriter class.

    Motion Jpeg (MJPEG) works as the src attribute of a plain html <img> tag,
    but it has limits such as no audio can get latency intensive.  There is
    also the need to covert each our native gbr frame to jpg before sending.

    Support for MJPEG is included in the vision service via the /video_feed
    endpoint.

    The vision service also supports WebRTC video which requires a bit more
    effort to set up on the client side, it provides features such as audio
    track and low latency and support for low bandwidth usage that make
    WebRTC a better choice for streaming video to a browser (IMO)
    """

    is_stopping = False
    camera: BaseCamera

    def __init__(self, camera: BaseCamera):
        MjpegVideo.camera = camera

    def stop(self) -> None:
        log.info("stopping any MJPEG streamers")
        MjpegVideo.is_stopping = True

    def start(self) -> None:
        log.info("starting MJPEG streamer")
        MjpegVideo.is_stopping = False

        thread = threading.Thread(target=self._flask_app_thread, daemon=True)
        thread.start()

    def _flask_app_thread(self) -> None:
        port = c.BB_MJPEG_VIDEO_PORT
        log.info(f"starting video_feed webhost on {port}")
        flaskApp.run(host="0.0.0.0", port=port, threaded=True)


def gen_rgb_video(camera: BaseCamera) -> Generator[bytes, None, None]:
    """Video streaming generator function."""
    while MjpegVideo.is_stopping is False:
        frame = camera.get_frame()

        jpeg = cv2.imencode(".jpg", frame)[1].tobytes()  # type: ignore
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")


@flaskApp.route("/video_feed")
def video_feed() -> Response:
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(
        gen_rgb_video(MjpegVideo.camera),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )
