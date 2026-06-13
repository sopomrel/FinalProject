from typing import List, Optional, Tuple

from tasks.object_detection.packages.stop_activity import should_stop

Detection = Tuple[Tuple[int, int, int, int], float, int]


class ObstacleHandler:
    """Debounced stop signal from object detections, for the navigation FSM.

    Wraps `stop_activity.should_stop` and adds frame hysteresis so a single
    noisy frame doesn't slam the brakes (and a single clear frame doesn't
    prematurely release). Output feeds `NavigationFSM.update(obstacle_stop=...)`.
    """

    def __init__(self, confirm_frames: int = 2, release_frames: int = 3):
        self.confirm_frames = int(confirm_frames)
        self.release_frames = int(release_frames)
        self._seen_streak = 0
        self._miss_streak = 0
        self.stopped = False
        self.reason = ""

    def reset(self) -> None:
        self._seen_streak = 0
        self._miss_streak = 0
        self.stopped = False
        self.reason = ""

    def update(self, detections: Optional[List[Detection]], img_size: int) -> bool:
        """Fold one frame of detections into the debounced stop decision.

        `detections` may be None when the detector skips a frame — in that case
        the previous decision is held. Returns the stable stop flag.
        """
        if detections is None:
            return self.stopped

        stop_now, reason = should_stop(detections, img_size)

        if stop_now:
            self._seen_streak += 1
            self._miss_streak = 0
            if not self.stopped and self._seen_streak >= self.confirm_frames:
                self.stopped = True
                self.reason = reason
        else:
            self._miss_streak += 1
            self._seen_streak = 0
            if self.stopped and self._miss_streak >= self.release_frames:
                self.stopped = False
                self.reason = ""
        return self.stopped

    def update_from_frame(self, detector, frame_rgb) -> bool:
        """Run `detector.detect` on an RGB frame and update the stop decision.

        `detector` is an ObjectDetectionAgent-like object exposing
        `detect(frame_rgb) -> list[Detection] | None`. img_size is taken from
        the frame height (frames are square-ish; should_stop treats it as a scale).
        """
        if frame_rgb is None:
            return self.stopped
        detections = detector.detect(frame_rgb)
        img_size = int(frame_rgb.shape[0])
        return self.update(detections, img_size)
