"""
WebRTC signaling server for establishing peer connections.

This module handles the WebRTC signaling protocol including SDP offer/answer
exchange and ICE candidate handling. It integrates with the basic_bot
camera and audio systems to provide real-time streaming.
"""

import json
import logging
import asyncio
from typing import Set, Dict, Any, Optional
from aiohttp import web, WSMsgType

from basic_bot.commons import constants as c
from basic_bot.commons.base_camera import BaseCamera
from basic_bot.commons.base_audio import BaseAudio

logger = logging.getLogger(__name__)

try:
    from aiortc import (
        RTCPeerConnection,
        RTCSessionDescription,
        RTCConfiguration,
        RTCIceServer
    )
    from basic_bot.commons.webrtc_tracks import CameraVideoStreamTrack, AudioCaptureStreamTrack
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False
    logger.error("aiortc not available. WebRTC signaling will not work.")


class WebRTCSignalingServer:
    """
    WebRTC signaling server that handles peer connection establishment.

    This server manages WebRTC peer connections and provides the signaling
    infrastructure needed for clients to establish direct connections with
    the robot's audio/video streams.
    """

    def __init__(self, camera: BaseCamera, audio_capture: Optional[BaseAudio] = None):
        if not AIORTC_AVAILABLE:
            raise ImportError("aiortc is required for WebRTC signaling")

        self.camera = camera
        self.audio_capture = audio_capture
        self.peer_connections: Set[RTCPeerConnection] = set()
        self.websockets: Dict[str, Any] = {}

        # WebRTC configuration with STUN servers
        self.rtc_config = RTCConfiguration([
            RTCIceServer("stun:stun.l.google.com:19302"),
            RTCIceServer("stun:stun1.l.google.com:19302"),
        ])

        logger.info("WebRTC signaling server initialized")

    async def create_peer_connection(self) -> RTCPeerConnection:
        """Create and configure a new RTCPeerConnection."""
        pc = RTCPeerConnection(self.rtc_config)
        self.peer_connections.add(pc)

        # Add connection state change handler
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state changed to: {pc.connectionState}")
            if pc.connectionState in ["failed", "closed"]:
                await self.cleanup_peer_connection(pc)

        # Add ICE connection state change handler
        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"ICE connection state changed to: {pc.iceConnectionState}")

        return pc

    async def cleanup_peer_connection(self, pc: RTCPeerConnection) -> None:
        """Clean up a peer connection."""
        try:
            self.peer_connections.discard(pc)
            await pc.close()
        except Exception as e:
            logger.error(f"Error cleaning up peer connection: {e}")

    async def handle_offer(self, request: web.Request) -> web.Response:
        """Handle WebRTC offer from client."""
        try:
            params = await request.json()
            offer_sdp = params.get("sdp")
            offer_type = params.get("type")

            if not offer_sdp or offer_type != "offer":
                return web.json_response(
                    {"error": "Invalid offer"},
                    status=400
                )

            logger.info("Received WebRTC offer from client")

            # Create peer connection
            pc = await self.create_peer_connection()

            # Add video track
            video_track = CameraVideoStreamTrack(self.camera)
            pc.addTrack(video_track)
            logger.info("Added video track to peer connection")

            # Add audio track if available and not disabled
            if (self.audio_capture is not None and
                    not c.BB_DISABLE_AUDIO_CAPTURE):
                audio_track = AudioCaptureStreamTrack(self.audio_capture)
                pc.addTrack(audio_track)
                logger.info("Added audio track to peer connection")

            # Set remote description (client's offer)
            offer = RTCSessionDescription(offer_sdp, offer_type)
            await pc.setRemoteDescription(offer)

            # Create answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            logger.info("Created WebRTC answer")

            return web.json_response({
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type
            })

        except Exception as e:
            logger.error(f"Error handling WebRTC offer: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connection for signaling."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        client_id = id(ws)
        self.websockets[str(client_id)] = ws

        logger.info(f"WebSocket client connected: {client_id}")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self.handle_websocket_message(ws, data)
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON in WebSocket message")
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")
        finally:
            self.websockets.pop(str(client_id), None)
            logger.info(f"WebSocket client disconnected: {client_id}")

        return ws

    async def handle_websocket_message(self, ws: web.WebSocketResponse, data: Dict[str, Any]) -> None:
        """Handle individual WebSocket messages."""
        message_type = data.get("type")

        if message_type == "ping":
            await ws.send_str(json.dumps({"type": "pong"}))
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")

    async def cleanup_all_connections(self) -> None:
        """Clean up all peer connections."""
        logger.info("Cleaning up all WebRTC connections")

        # Close all peer connections
        cleanup_tasks = []
        for pc in list(self.peer_connections):
            cleanup_tasks.append(self.cleanup_peer_connection(pc))

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        # Close all WebSocket connections
        for ws in self.websockets.values():
            if not ws.closed:
                await ws.close()

        self.websockets.clear()
        logger.info("All WebRTC connections cleaned up")


def create_signaling_app(camera: BaseCamera, audio_capture: Optional[BaseAudio] = None) -> web.Application:
    """
    Create the aiohttp application for WebRTC signaling.

    Args:
        camera: Camera instance for video streaming
        audio_capture: Optional audio capture instance for audio streaming

    Returns:
        Configured aiohttp Application
    """
    if not AIORTC_AVAILABLE:
        raise ImportError("aiortc is required for WebRTC signaling server")

    signaling_server = WebRTCSignalingServer(camera, audio_capture)

    app = web.Application()

    # Add CORS middleware
    @web.middleware
    async def cors_handler(request, handler):
        if request.method == "OPTIONS":
            # Handle preflight request
            response = web.Response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response

        # Handle actual request
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    app.middlewares.append(cors_handler)

    # WebRTC signaling routes
    app.router.add_post("/webrtc/offer", signaling_server.handle_offer)
    app.router.add_get("/webrtc/ws", signaling_server.handle_websocket)

    # Health check endpoint
    async def health_check(request):
        return web.json_response({"status": "ok", "service": "webrtc-signaling"})

    app.router.add_get("/webrtc/health", health_check)

    # Store reference to signaling server for cleanup
    app['signaling_server'] = signaling_server

    return app


async def cleanup_app(app: web.Application) -> None:
    """Clean up application resources."""
    signaling_server = app.get('signaling_server')
    if signaling_server:
        await signaling_server.cleanup_all_connections()
