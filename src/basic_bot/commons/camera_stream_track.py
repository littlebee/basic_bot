import asyncio
from aiortc.mediastreams import MediaStreamTrack
from av import VideoFrame
from fractions import Fraction

from basic_bot.commons.base_camera import BaseCamera


class CameraStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, camera: BaseCamera):
        super().__init__()
        self.frame_count = 0
        self.camera = camera

    async def recv(self):
        # Generate a simple gray frame
        # frame_data = np.full((480, 640, 3), 128, dtype=np.uint8)
        frame_data = self.camera.frame

        video_frame = VideoFrame.from_ndarray(frame_data, format="bgr24")

        # Set PTS and time_base for the frame
        self.frame_count += 1
        video_frame.pts = self.frame_count * 90000 // 30  # Assuming 30 fps
        video_frame.time_base = Fraction(1, 90000)

        await asyncio.sleep(1 / 30)  # Simulate 30 fps
        return video_frame
