import time

# last n seconds to use for fps calc
FPS_WINDOW = 60


class FpsStats:
    """
    FpsStats - A class to track overall and floating frames per seconds.  Floating fps is
    calculated over the last 60 seconds.

    Instantiate the class to start tracking the stats. Call increment() for each frame read.
    Call stats() to get the stats.
    """

    def __init__(self) -> None:
        self._start()

    def _start(self) -> None:
        self.started_at: float = time.time()
        self.total_frames: int = 0
        self.floating_frames_count: int = 0
        self.floating_started_at: float = time.time()
        self.last_floating_fps: float = 0.0

    def increment(self) -> None:
        """Increment the frame count and calculate the floating fps"""
        self.total_frames += 1
        self.floating_frames_count += 1

        fps_time: float = time.time() - self.floating_started_at
        if fps_time > FPS_WINDOW:
            self.last_floating_fps = self.floating_frames_count / fps_time
            self.floating_started_at = time.time()
            self.floating_frames_count = 0

    def stats(self) -> dict[str, float]:
        """Return the stats as a dictionary"""
        now: float = time.time()
        total_time: float = now - self.started_at
        return {
            "totalFramesRead": self.total_frames,
            "totalTime": total_time,
            "overallFps": self.total_frames / total_time,
            "fpsStartedAt": self.floating_started_at,
            "floatingFps": self.last_floating_fps,
        }
