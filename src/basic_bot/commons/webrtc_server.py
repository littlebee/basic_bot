#!/usr/bin/env python3
""" """
import os
import threading
from typing import Optional

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
import aiohttp_cors

from basic_bot.commons import constants as c, log
from basic_bot.commons.web_utils_aiohttp import (
    respond_file,
    AccessLogger,
)

from basic_bot.commons.base_camera import BaseCamera
from basic_bot.commons.webrtc_peers import WebrtcPeers


# # this is mainly for debugging WebRTC and aiortc
# logging.basicConfig(
#     # Set the level to DEBUG for maximum verbosity, but be warned, aiortc
#     # makes a lot of noise when streaming
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
# )
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

script_directory = os.path.abspath(os.path.dirname(__file__))
public_directory = os.path.abspath(os.path.join(script_directory, "../public"))


class WebrtcServer:

    def __init__(self, camera: BaseCamera):
        self.camera = camera
        self.is_stopping = False

        log.info("Initializing webrtc offers server")
        self.webrtc_peers = WebrtcPeers(self.camera)
        self.app: Optional[web.Application] = None

    async def stop(self, _app: web.Application) -> None:
        self.is_stopping = True
        log.info("vision service shutting down...")
        if self.app is not None:
            await self.app.shutdown()
            await self.app.cleanup()

    async def get_webrtc_test_page(self, _request: Request) -> Response:
        return respond_file(
            public_directory, "webrtc_test.html", content_type="text/html"
        )

    async def get_webrtc_test_client(self, _request: Request) -> Response:
        return respond_file(
            public_directory,
            "webrtc_test_client.js",
            content_type="application/javascript",
        )

    async def handle_shutdown(self, _app: web.Application) -> None:
        self.is_stopping = True
        log.info("vision service shutting down...")

        await self.webrtc_peers.close_all_connections()

    def start(self) -> None:
        threading.Thread(target=self._thread).start()

    def _thread(self) -> None:
        app = web.Application()
        app.on_shutdown.append(self.stop)

        # this is for handling WebRTC video handshake
        app.router.add_post("/offer", self.webrtc_peers.respond_to_offer)
        # for testing only
        app.router.add_get("/", self.get_webrtc_test_page)
        app.router.add_get("/webrtc_test.html", self.get_webrtc_test_page)
        app.router.add_get("/webrtc_test_client.js", self.get_webrtc_test_client)

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

        self.app = app

        log.info(f"starting webrtc webhost on {c.BB_WEBRTC_PORT}")
        web.run_app(
            app,
            access_log_class=AccessLogger,
            host="0.0.0.0",
            port=c.BB_WEBRTC_PORT,
            # ssl_context=ssl_context,
        )
