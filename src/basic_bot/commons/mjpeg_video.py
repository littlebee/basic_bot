import asyncio

from aiohttp import web, MultipartWriter, client_exceptions
import cv2

from basic_bot.commons import log
from basic_bot.commons.base_camera import BaseCamera


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

    def __init__(self, camera: BaseCamera):
        self.camera = camera

    def stop(self):
        log.info("stopping any MJPEG streamers")
        MjpegVideo.is_stopping = True

    #  see https://docs.aiohttp.org/en/stable/multipart.html
    async def stream_mjpeg_video(self, request, camera: BaseCamera):
        """MJPEG video streaming function."""
        boundary_marker = "--frame"
        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": f"multipart/x-mixed-replace;boundary={boundary_marker}"
            },
        )
        await response.prepare(request)
        while not MjpegVideo.is_stopping:
            frame = camera.get_frame()
            jpeg = cv2.imencode(".jpg", frame)[1].tobytes()  # type: ignore
            with MultipartWriter("image/jpeg", boundary=boundary_marker) as mpwriter:
                mpwriter.append(jpeg, {"Content-Type": "image/jpeg"})
                try:
                    await mpwriter.write(response, close_boundary=False)
                except client_exceptions.ClientConnectionResetError:
                    await mpwriter.close()
                    break
            await response.drain()
            await asyncio.sleep(1 / 30)

        return response
