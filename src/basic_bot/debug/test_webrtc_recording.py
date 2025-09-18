#!/usr/bin/env python3
"""
This diagnostic script will test WebRTC connection to the vision service and record
10 seconds of video and audio tracks to a single MP4 file.

usage:
```sh
   python -m basic_bot.debug.test_webrtc_recording
```

The script will connect to http://localhost:5801/offer and record both video and audio
tracks for 10 seconds, saving them as webrtc_recording_test_output.mp4
"""
import asyncio
import os
import time
import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder

DURATION = 10
OUTPUT_FILE = os.path.join(os.getcwd(), "webrtc_recording_test_output.mp4")
WEBRTC_ENDPOINT = "http://localhost:5801/offer"


async def record_webrtc_stream():
    """
    Connect to WebRTC endpoint and record video and audio for DURATION seconds
    """
    print(f"Connecting to WebRTC endpoint: {WEBRTC_ENDPOINT}")

    # Create RTCPeerConnection
    pc = RTCPeerConnection()

    # Single recorder for both video and audio
    recorder = None

    @pc.on("track")
    def on_track(track):
        nonlocal recorder
        print(f"Received {track.kind} track")

        if recorder is None:
            # Create recorder on first track
            recorder = MediaRecorder(OUTPUT_FILE)

        # Add track to recorder
        recorder.addTrack(track)

        @track.on("ended")
        def on_track_ended():
            print(f"{track.kind} track ended")

    try:
        # Add transceivers for receiving video and audio
        pc.addTransceiver("video", direction="recvonly")
        pc.addTransceiver("audio", direction="recvonly")

        # Create offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        # Wait for ICE gathering to complete
        while pc.iceGatheringState != "complete":
            await asyncio.sleep(0.1)

        # Send offer to server
        async with aiohttp.ClientSession() as session:
            offer_data = {
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type
            }

            headers = {"Content-Type": "application/json"}
            async with session.post(WEBRTC_ENDPOINT, json=offer_data, headers=headers) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to send offer: {response.status}")

                answer_data = await response.json()

                # Set remote description
                answer = RTCSessionDescription(
                    sdp=answer_data["sdp"],
                    type=answer_data["type"]
                )
                await pc.setRemoteDescription(answer)

        print(f"WebRTC connection established, recording for {DURATION} seconds...")

        # Wait a moment for tracks to be received
        await asyncio.sleep(1)

        # Start recording
        if recorder:
            await recorder.start()
            print("Recording started")
        else:
            print("No tracks received, cannot start recording")
            return

        # Record for specified duration
        start_time = time.time()
        while time.time() - start_time < DURATION:
            await asyncio.sleep(0.1)
            elapsed = time.time() - start_time
            print(f"Recording... {elapsed:.1f}s / {DURATION}s", end="\r")

        print(f"\nRecording completed after {DURATION} seconds")

        # Stop recording
        if recorder:
            await recorder.stop()
            print(f"Recording saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error during WebRTC recording: {e}")
        raise

    finally:
        # Close connection
        await pc.close()


async def main():
    """
    Main function to run the WebRTC recording test
    """
    try:
        await record_webrtc_stream()

        # Check if file was created
        if os.path.exists(OUTPUT_FILE):
            size = os.path.getsize(OUTPUT_FILE)
            print(f"Recording file created: {OUTPUT_FILE} ({size} bytes)")
        else:
            print(f"Recording file was not created: {OUTPUT_FILE}")

    except Exception as e:
        print(f"WebRTC recording test failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())