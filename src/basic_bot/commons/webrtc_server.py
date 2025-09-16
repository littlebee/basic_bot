import asyncio
import json
from typing import Any, Optional
import numpy as np

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from aiortc.mediastreams import MediaStreamTrack
from av import VideoFrame, AudioFrame
from fractions import Fraction

from basic_bot.commons import log
from basic_bot.commons.base_camera import BaseCamera
from basic_bot.commons.base_audio import BaseAudio


class CameraStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, camera: BaseCamera):
        super().__init__()
        self.frame_count = 0
        self.camera = camera

    async def recv(self) -> VideoFrame:
        # Generate a simple gray frame
        # frame_data = np.full((480, 640, 3), 128, dtype=np.uint8)

        frame_data = self.camera.get_frame()
        if frame_data is None:
            # Create a default black frame if no frame is available
            frame_array = np.zeros((480, 640, 3), dtype=np.uint8)
        else:
            # The frame from camera is actually a numpy array despite the typing
            frame_array = frame_data  # type: ignore

        video_frame = VideoFrame.from_ndarray(frame_array, format="bgr24")

        # Set PTS and time_base for the frame
        self.frame_count += 1
        video_frame.pts = self.frame_count * 90000 // 30  # Assuming 30 fps
        video_frame.time_base = Fraction(1, 90000)

        await asyncio.sleep(1 / 30)  # Simulate 30 fps
        return video_frame


class AudioStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, audio_source: BaseAudio):
        super().__init__()
        self.frame_count = 0
        self.audio_source = audio_source

    async def recv(self) -> AudioFrame:
        # Get audio data from the audio source
        audio_data = self.audio_source.get_audio_frame()
        if audio_data is None:
            # Create silent frame if no audio data available
            sample_rate = self.audio_source.get_sample_rate()
            channels = self.audio_source.get_channels()
            # Create 20ms of silence (standard WebRTC frame size)
            samples_per_frame = sample_rate // 50  # 20ms at sample_rate
            if channels == 1:
                silence = np.zeros((samples_per_frame,), dtype=np.int16)
            else:
                silence = np.zeros((samples_per_frame, channels), dtype=np.int16)
            audio_data = silence

        # Create AudioFrame - for audio, the array should be shaped as (channels, samples)
        if self.audio_source.get_channels() == 1:
            # Mono audio: reshape from (samples,) to (1, samples)
            if audio_data.ndim == 1:
                audio_data = audio_data.reshape(1, -1)
            layout = "mono"
        else:
            # Stereo audio: reshape from (samples, 2) to (2, samples)
            if audio_data.ndim == 2 and audio_data.shape[1] == 2:
                audio_data = audio_data.T  # Transpose to (2, samples)
            layout = "stereo"

        audio_frame = AudioFrame.from_ndarray(audio_data, format="s16", layout=layout)

        # Set sample rate and time_base for the frame
        audio_frame.sample_rate = self.audio_source.get_sample_rate()
        audio_frame.time_base = Fraction(1, self.audio_source.get_sample_rate())

        # Set PTS (presentation timestamp) based on actual samples
        samples_in_frame = audio_data.shape[-1]
        audio_frame.pts = self.frame_count * samples_in_frame
        self.frame_count += 1

        # Sleep for the duration of this audio frame
        frame_duration = samples_in_frame / self.audio_source.get_sample_rate()
        await asyncio.sleep(frame_duration)
        return audio_frame


class WebrtcPeers:
    def __init__(self, camera: BaseCamera, audio_source: Optional[BaseAudio] = None):
        self.pcs: Any = set()
        self.relay = MediaRelay()
        self.camera = camera
        self.audio_source = audio_source

    async def close_all_connections(self) -> None:
        # close peer connections
        log.info("Closing all webrtc peer connections")
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()
        log.debug("Closed all webrtc peer connections")

    async def respond_to_offer(self, request: web.Request) -> web.Response:
        params = await request.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        pc = RTCPeerConnection()
        self.pcs.add(pc)

        log.info(f"Creating webrtc offer for {request.remote}")

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
                self.pcs.discard(pc)

        # bee: I think this is only needed when we care about recieving media from
        #   the web app like showing the users face on the bot display and allowing them
        #   to speak and be seen by the person or pets the bot sees.
        #
        #   For now, keeping this for reference while I focus on just sending the bots
        #   video to the webapp
        #
        # @pc.on("track")
        # def on_track(track):
        #     log_info("Track %s received", track.kind)

        #     if track.kind == "audio":
        #         pc.addTrack(player.audio)
        #         recorder.addTrack(track)
        #     elif track.kind == "video":
        #         pc.addTrack(CameraStreamTrack())
        #         if args.record_to:
        #             recorder.addTrack(relay.subscribe(track))

        #     @track.on("ended")
        #     async def on_ended():
        #         log_info("Track %s ended", track.kind)
        #         await recorder.stop()

        # the example in aiortc/examples/server (above) is waiting to
        # get a video track from the browser before adding it's transformed
        # track.  We want to add our track strait away
        pc.addTrack(CameraStreamTrack(self.camera))

        # Add audio track if audio source is available
        if self.audio_source:
            pc.addTrack(AudioStreamTrack(self.audio_source))

        # handle offer
        await pc.setRemoteDescription(offer)

        # send answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            ),
        )
