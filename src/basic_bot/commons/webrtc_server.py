import asyncio
import json
import platform
import subprocess
import time
from typing import Any, Optional
import numpy as np
import uuid

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaRelay, MediaPlayer
from aiortc.mediastreams import MediaStreamTrack
from av import VideoFrame
from fractions import Fraction

from basic_bot.commons import log, constants as c
from basic_bot.commons.base_camera import BaseCamera


class CameraStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, camera: BaseCamera):
        super().__init__()
        self.camera = camera
        self.start_time: Optional[float] = None

    async def recv(self) -> VideoFrame:
        # Initialize start time on first frame
        if self.start_time is None:
            self.start_time = time.time()

        frame_data = self.camera.get_frame()
        if frame_data is None:
            # Create a default black frame if no frame is available
            frame_array = np.zeros((480, 640, 3), dtype=np.uint8)
        else:
            # The frame from camera is actually a numpy array despite the typing
            frame_array = frame_data  # type: ignore

        video_frame = VideoFrame.from_ndarray(frame_array, format="bgr24")

        # Set PTS based on elapsed time for proper timing
        elapsed_time = time.time() - self.start_time
        video_frame.pts = int(elapsed_time * 90000)  # 90kHz timebase
        video_frame.time_base = Fraction(1, 90000)

        await asyncio.sleep(1 / 30)  # Target 30 fps
        return video_frame


class WebrtcPeers:
    def __init__(self, camera: BaseCamera):
        self.pcs: dict[str, RTCPeerConnection] = dict()
        self.relay = MediaRelay()
        self.camera = camera
        # Audio streaming variables
        self.microphone: Optional[MediaPlayer] = None
        self.arecord_process: Optional[subprocess.Popen] = None
        self.audio_relay: Optional[MediaRelay] = None

    def _initialize_audio(self) -> Optional[MediaStreamTrack]:
        """Initialize audio streaming. Returns audio track or None if initialization fails."""
        if self.microphone is not None:
            # Audio already initialized, return existing track
            return (
                self.audio_relay.subscribe(self.microphone.audio)
                if self.audio_relay and self.microphone.audio
                else None
            )

        try:
            if c.BB_USE_ARECORD and platform.system() == "Linux":
                # Use arecord for low-latency audio capture on Linux
                log.info("Initializing arecord for audio streaming")
                self.arecord_process = subprocess.Popen(
                    [
                        "arecord",
                        "-f",
                        "S16_LE",
                        "-r",
                        str(c.BB_AUDIO_SAMPLE_RATE),
                        "-c",
                        str(c.BB_AUDIO_CHANNELS),
                        "-t",
                        "raw",
                        f"--buffer-size={c.BB_AUDIO_BUFFER_SIZE}",
                        f"--period-size={c.BB_AUDIO_PERIOD_SIZE}",
                        "--disable-resample",
                        "--disable-channels",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=0,  # Unbuffered stdout
                )
                self.microphone = MediaPlayer(
                    self.arecord_process.stdout,
                    format="s16le",
                    options={
                        "sample_rate": str(c.BB_AUDIO_SAMPLE_RATE),
                        "channels": str(c.BB_AUDIO_CHANNELS),
                        "probesize": "32",
                        "analyzeduration": "0",
                    },
                )
            else:
                # Use default system microphone via PulseAudio
                log.info("Initializing PulseAudio for audio streaming")
                if platform.system() == "Darwin":
                    self.microphone = MediaPlayer(":0", format="avfoundation")
                elif platform.system() == "Windows":
                    self.microphone = MediaPlayer("audio=Microphone", format="dshow")
                else:
                    # Linux with PulseAudio
                    self.microphone = MediaPlayer("default", format="pulse")

            # Initialize audio relay for sharing between multiple peers
            self.audio_relay = MediaRelay()
            log.info("Audio streaming initialized successfully")
            return (
                self.audio_relay.subscribe(self.microphone.audio)
                if self.microphone.audio
                else None
            )

        except Exception as e:
            log.error(f"Failed to initialize audio streaming: {e}")
            self._cleanup_audio()
            return None

    def _cleanup_audio(self) -> None:
        """Clean up audio resources."""
        if self.microphone is not None:
            try:
                if self.microphone.audio:
                    self.microphone.audio.stop()
            except Exception as e:
                log.error(f"Error stopping microphone: {e}")
            self.microphone = None

        if self.arecord_process is not None:
            try:
                self.arecord_process.terminate()
                self.arecord_process.wait()
            except Exception as e:
                log.error(f"Error terminating arecord process: {e}")
            self.arecord_process = None

        self.audio_relay = None

    async def close_all_connections(self) -> None:
        # close peer connections
        log.info("Closing all webrtc peer connections")
        promises = [pc.close() for pc in self.pcs.values()]
        await asyncio.gather(*promises)
        self.pcs.clear()

        # cleanup audio resources
        self._cleanup_audio()
        log.debug("Closed all webrtc peer connections and cleaned up audio")

    async def respond_to_offer(self, request: web.Request) -> web.Response:
        params = await request.json()
        log.info(f"Received WebRTC offer from {request.remote}; {params}")
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        pc = RTCPeerConnection()
        client_id = str(uuid.uuid4())
        self.pcs[client_id] = pc

        log.info(f"Creating webrtc answer for {request.remote}")

        @pc.on("datachannel")
        def on_datachannel(channel: Any) -> None:
            @channel.on("message")  # type: ignore
            def on_message(message: str) -> None:
                if isinstance(message, str) and message.startswith("ping"):
                    channel.send("pong" + message[4:])

        @pc.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            log.info(f"Connection state is {pc.connectionState}")
            if pc.connectionState == "failed":
                await pc.close()
                self.pcs.pop(client_id, None)

        # Add video track
        pc.addTrack(CameraStreamTrack(self.camera))

        # Add audio track
        audio_track = self._initialize_audio()
        if audio_track:
            pc.addTrack(audio_track)
            log.debug("Added audio track to WebRTC connection")
        else:
            log.error("Failed to initialize audio track for WebRTC connection")

        # handle offer
        await pc.setRemoteDescription(offer)

        # send answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {
                    "sdp": pc.localDescription.sdp,
                    "type": pc.localDescription.type,
                    "client_id": client_id,
                }
            ),
        )

    async def respond_to_ice_candidate(self, request: web.Request) -> web.Response:
        params = await request.json()
        client_id = params.get("client_id")
        candidate = params.get("candidate")
        log.info(
            f"Received ICE candidate from {request.remote}; client_id={client_id}, candidate={candidate}"
        )

        pc = self.pcs.get(client_id)
        if not pc:
            log.error(f"No peer connection found for client_id={client_id}")
            return web.Response(status=404, text="Peer connection not found")

        try:
            await pc.addIceCandidate(self.create_RTCIceCandidate(candidate))
            log.debug(f"Added ICE candidate for client_id={client_id}")
            return web.Response(status=200, text="ICE candidate added")
        except Exception as e:
            log.error(f"Error adding ICE candidate for client_id={client_id}: {e}")
            return web.Response(status=500, text="Failed to add ICE candidate")

    def create_RTCIceCandidate(self, candidate: dict) -> RTCIceCandidate:
        parts = candidate["candidate"].split(" ")
        foundation = parts[0].split(":")[1]
        component = int(parts[1])
        protocol = parts[2]
        priority = int(parts[3])
        ip = parts[4]
        port = int(parts[5])
        type = parts[7]

        return RTCIceCandidate(
            component=component,
            foundation=foundation,
            ip=ip,
            port=port,
            priority=priority,
            protocol=protocol,
            type=type,
            sdpMid=candidate["sdpMid"],
            sdpMLineIndex=candidate["sdpMLineIndex"],
        )
