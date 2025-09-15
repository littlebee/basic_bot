import asyncio
import json
from typing import Any

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay

from basic_bot.commons import log
from basic_bot.commons.camera_stream_track import CameraStreamTrack
from basic_bot.commons.base_camera import BaseCamera


class WebrtcPeers:
    def __init__(self, camera: BaseCamera):
        self.pcs: Any = set()
        self.relay = MediaRelay()
        self.camera = camera

    async def close_all_connections(self):
        # close peer connections
        log.info("Closing all webrtc peer connections")
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()
        log.debug("Closed all webrtc peer connections")

    async def respond_to_offer(self, request):
        params = await request.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        pc = RTCPeerConnection()
        self.pcs.add(pc)

        log.info(f"Creating webrtc offer for {request.remote}")

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(message):
                if isinstance(message, str) and message.startswith("ping"):
                    channel.send("pong" + message[4:])

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
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
