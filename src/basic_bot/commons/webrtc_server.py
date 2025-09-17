import asyncio
import json
import os
import platform
import subprocess
from typing import Any, Optional, Tuple
import numpy as np

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay, MediaPlayer
from aiortc.mediastreams import MediaStreamTrack
from av import VideoFrame
from fractions import Fraction

from basic_bot.commons import log
from basic_bot.commons.base_camera import BaseCamera


def create_minimal_alsa_config() -> None:
    """Create a minimal ALSA configuration to work around missing config files."""
    alsa_conf_content = """
pcm.!default {
    type hw
    card 0
}
ctl.!default {
    type hw
    card 0
}
"""
    # Create config in the expected location
    os.makedirs("/tmp/vendor/share/alsa", exist_ok=True)
    with open("/tmp/vendor/share/alsa/alsa.conf", "w") as f:
        f.write(alsa_conf_content)

    # Also try alternative locations
    os.makedirs("/tmp/alsa", exist_ok=True)
    with open("/tmp/alsa/alsa.conf", "w") as f:
        f.write(alsa_conf_content)

    # Set environment variables to point to our config
    os.environ["ALSA_CONF_PATH"] = "/tmp/vendor/share/alsa/alsa.conf"
    os.environ["ALSA_PCM_CARD"] = "1"  # Try USB mic as default


def check_audio_processes() -> None:
    """Check what processes might be using audio devices."""
    try:
        # Check for other arecord processes
        result = subprocess.run(["pgrep", "-f", "arecord"], capture_output=True, text=True)
        if result.stdout.strip():
            log.error(f"Found running arecord processes: {result.stdout.strip()}")
            # Kill them
            subprocess.run(["pkill", "-f", "arecord"], capture_output=True)
            log.info("Killed existing arecord processes")

        # Check what's using the audio device
        lsof_result = subprocess.run(["lsof", "/dev/snd/*"], capture_output=True, text=True)
        if lsof_result.stdout.strip():
            log.info(f"Processes using audio devices: {lsof_result.stdout}")
    except Exception as e:
        log.debug(f"Could not check audio processes: {e}")


def get_arecord_devices() -> list[tuple[str, str]]:
    """Get audio devices that arecord can see."""
    devices = []
    try:
        log.info("Discovering available audio devices...")
        result = subprocess.run(["arecord", "-l"], capture_output=True, text=True)
        log.info(f"arecord -l output: {result.stdout}")

        for line in result.stdout.split('\n'):
            if 'card' in line and 'device' in line:
                # Parse lines like "card 1: USB [USB Audio], device 0: USB Audio [USB Audio]"
                if 'card' in line:
                    card_num = line.split('card ')[1].split(':')[0]
                    device_num = "0"  # Default device 0
                    if 'device' in line:
                        try:
                            device_num = line.split('device ')[1].split(':')[0]
                        except:
                            device_num = "0"

                    device_name = f"hw:{card_num},{device_num}"
                    log.info(f"Found audio device: {device_name}")
                    devices.append((device_name, "alsa"))
                    devices.append((f"plughw:{card_num},{device_num}", "alsa"))
    except Exception as e:
        log.error(f"Could not get arecord devices: {e}")
    return devices


def create_audio_pipe(device_name: str = "hw:1") -> Optional[Tuple[str, subprocess.Popen]]:
    """Create a RAM-based audio pipe with minimal buffering."""
    try:
        # Use /dev/shm (RAM filesystem) for zero-latency I/O
        pipe_path = "/dev/shm/audio_pipe"

        # Remove existing pipe if it exists
        if os.path.exists(pipe_path):
            os.unlink(pipe_path)

        # Create named pipe in RAM
        os.mkfifo(pipe_path)

        # First try to find working audio devices
        audio_devices = get_arecord_devices()
        if audio_devices:
            device_name = audio_devices[0][0]  # Use first discovered device
            log.info(f"Using discovered audio device: {device_name}")

        # Start arecord with minimal latency settings
        arecord_cmd = [
            "arecord",
            "-D", device_name,      # Use discovered or specified device
            "-f", "S16_LE",         # 16-bit little endian
            "-r", "48000",          # 48kHz sample rate
            "-c", "1",              # Mono
            "--buffer-size=512",    # Smaller buffer for lower latency
            "--period-size=128",    # Smaller period for lower latency
            "-N",                   # Non-blocking mode
            pipe_path
        ]

        log.info(f"Starting arecord: {' '.join(arecord_cmd)}")
        process = subprocess.Popen(arecord_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        # Minimal startup delay
        import time
        time.sleep(0.2)

        if process.poll() is None:  # Process is still running
            return pipe_path, process
        else:
            stderr_output = ""
            if process.stderr:
                stderr_output = process.stderr.read().decode()
            log.error(f"arecord failed to start: {stderr_output}")

            # Try with different device if available
            if len(audio_devices) > 1:
                log.info("Trying alternative audio device...")
                device_name = audio_devices[1][0]  # Try second device
                arecord_cmd_fallback = [
                    "arecord",
                    "-D", device_name,
                    "-f", "S16_LE",
                    "-r", "48000",
                    "-c", "1",
                    "--buffer-size=1024",
                    "--period-size=256",
                    pipe_path
                ]
            else:
                # Try with plughw instead of hw
                log.info("Trying with plughw device...")
                plughw_device = device_name.replace("hw:", "plughw:")
                arecord_cmd_fallback = [
                    "arecord",
                    "-D", plughw_device,
                    "-f", "S16_LE",
                    "-r", "48000",
                    "-c", "1",
                    "--buffer-size=1024",
                    "--period-size=256",
                    pipe_path
                ]

            log.info(f"Starting fallback arecord: {' '.join(arecord_cmd_fallback)}")
            process = subprocess.Popen(arecord_cmd_fallback, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            time.sleep(0.2)

            if process.poll() is None:
                return pipe_path, process
            else:
                if process.stderr:
                    stderr_output = process.stderr.read().decode()
                log.error(f"Fallback arecord also failed: {stderr_output}")
                return None

    except Exception as e:
        log.error(f"Failed to create audio pipe: {e}")
        return None


def get_linux_audio_devices() -> list[tuple[str, str]]:
    """Get list of potential Linux audio devices to try."""
    devices = []

    # Signal that we want to try the arecord pipe approach
    devices.append(("/dev/shm/audio_pipe", "s16le"))  # RAM-based pipe format

    # Try PulseAudio
    devices.append(("default", "pulse"))

    # Add devices found by arecord
    devices.extend(get_arecord_devices())

    # Try OSS devices (bypass ALSA entirely)
    for i in range(4):
        if os.path.exists(f"/dev/dsp{i}"):
            devices.append((f"/dev/dsp{i}", "oss"))
        if os.path.exists(f"/dev/audio{i}"):
            devices.append((f"/dev/audio{i}", "oss"))

    # Try ALSA devices with our config
    devices.extend([
        ("default", "alsa"),       # ALSA default
        ("hw:0", "alsa"),         # First hardware device
        ("hw:1", "alsa"),         # Second hardware device (USB mic)
        ("hw:2", "alsa"),         # Third hardware device
        ("plughw:0", "alsa"),     # ALSA with automatic conversion
        ("plughw:1", "alsa"),     # ALSA with automatic conversion (USB)
    ])

    return devices


def get_default_audio_device() -> tuple[str, str]:
    """Get the default audio device file and format for the current platform."""
    system = platform.system().lower()

    if system == "linux":
        return ("hw:1", "alsa")  # Try USB mic first (usually hw:1)
    elif system == "darwin":  # macOS
        return (":0", "avfoundation")
    elif system == "windows":
        return ("audio=Microphone", "dshow")
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


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


class WebrtcPeers:
    def __init__(self, camera: BaseCamera):
        self.pcs: Any = set()
        self.relay = MediaRelay()
        self.camera = camera
        self.audio_player: Optional[MediaPlayer] = None
        self.arecord_process: Optional[subprocess.Popen] = None
        self._init_audio_player()

    def _init_audio_player(self) -> None:
        """Initialize the audio player with the default microphone."""
        system = platform.system().lower()

        if system == "linux":
            # Check for conflicting audio processes
            check_audio_processes()

            # Create minimal ALSA config to work around missing files
            try:
                create_minimal_alsa_config()
                log.info("Created minimal ALSA configuration")
            except Exception as e:
                log.debug(f"Could not create ALSA config: {e}")

            # Try multiple audio devices on Linux
            devices_to_try = get_linux_audio_devices()
            log.info(f"Found {len(devices_to_try)} audio devices to try")

            for device, format_name in devices_to_try:
                try:
                    log.info(f"Trying audio device: {device}, format: {format_name}")

                    # Special handling for our audio pipe
                    if device == "/dev/shm/audio_pipe" and format_name == "s16le":
                        pipe_result = create_audio_pipe()
                        if pipe_result:
                            pipe_path, process = pipe_result
                            self.arecord_process = process
                            log.info(f"arecord process started successfully, attempting MediaPlayer with {pipe_path}")

                            # Use ultra-low latency options for MediaPlayer
                            options = {
                                "buffer_size": "512",       # Match arecord buffer
                                "probesize": "32",          # Quick probing
                                "analyzeduration": "0",     # No analysis delay
                                "fflags": "+nobuffer+flush_packets+discardcorrupt",
                                "flags": "low_delay",       # Low delay flag
                                "thread_queue_size": "1",   # Minimal queue
                                "avoid_negative_ts": "disabled",
                                "max_delay": "0",           # No buffering delay
                                "sync": "audio",            # Audio sync priority
                            }
                            self.audio_player = MediaPlayer(
                                file=pipe_path,
                                format=format_name,
                                options=options
                            )
                            log.info("MediaPlayer created successfully with audio pipe")
                        else:
                            log.error("Failed to create arecord process, skipping pipe")
                            continue
                    else:
                        self.audio_player = MediaPlayer(file=device, format=format_name)

                    log.info(f"Audio initialized successfully with {device}")
                    return
                except Exception as e:
                    log.debug(f"Failed to initialize {device}: {e}")
                    continue

            log.info("No working audio device found, continuing with video-only streaming")
            self.audio_player = None
        else:
            # For non-Linux platforms, use the original single-device approach
            try:
                device, format_name = get_default_audio_device()
                log.info(f"Initializing audio with device: {device}, format: {format_name}")
                self.audio_player = MediaPlayer(file=device, format=format_name)
                log.info("Audio initialized successfully")
            except Exception as e:
                log.info(f"Audio not available ({e}), continuing with video-only streaming")
                self.audio_player = None

    async def close_all_connections(self) -> None:
        # close peer connections
        log.info("Closing all webrtc peer connections")
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()

        # close audio player and arecord process
        if self.audio_player:
            self.audio_player = None

        if self.arecord_process:
            try:
                self.arecord_process.terminate()
                self.arecord_process.wait(timeout=5)
            except Exception as e:
                log.debug(f"Error stopping arecord process: {e}")
            self.arecord_process = None

        # Clean up audio pipe
        if os.path.exists("/dev/shm/audio_pipe"):
            try:
                os.unlink("/dev/shm/audio_pipe")
            except Exception as e:
                log.debug(f"Error removing audio pipe: {e}")

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

        # Add audio track if available
        if self.audio_player and self.audio_player.audio:
            log.info("Adding audio track to WebRTC connection")
            pc.addTrack(self.audio_player.audio)
        else:
            log.debug("Audio player not available, continuing with video-only")

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
