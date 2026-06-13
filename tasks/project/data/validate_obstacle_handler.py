"""Validate obstacle_handler.py (run from repo root)."""
import sys
from pathlib import Path

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tasks.project.packages.obstacle_handler import ObstacleHandler

_IMG = 480
# y2 above stop_y (img * 0.55 = 264) -> should_stop returns True.
_CLOSE = [((100, 100, 220, 300), 0.9, 0)]
_FAR = [((100, 100, 220, 200), 0.9, 0)]


class _MockDetector:
    def __init__(self, detections):
        self.detections = detections

    def detect(self, frame_rgb):
        return self.detections


def main():
    h = ObstacleHandler(confirm_frames=2, release_frames=3)

    # One close frame is not enough (needs confirm_frames).
    assert h.update(_CLOSE, _IMG) is False
    assert h.update(_CLOSE, _IMG) is True
    assert h.reason != ""

    # None (skipped detector frame) holds the current decision.
    assert h.update(None, _IMG) is True

    # Needs release_frames of clear before it releases.
    assert h.update(_FAR, _IMG) is True
    assert h.update(_FAR, _IMG) is True
    assert h.update(_FAR, _IMG) is False
    assert h.reason == ""

    # Empty detections behave like "clear".
    assert h.update([], _IMG) is False

    h.reset()
    assert h.stopped is False

    # update_from_frame bridges an ObjectDetectionAgent-like detector.
    frame = np.zeros((_IMG, 640, 3), dtype=np.uint8)
    h2 = ObstacleHandler(confirm_frames=1, release_frames=1)
    det = _MockDetector(_CLOSE)
    assert h2.update_from_frame(det, frame) is True
    det.detections = None
    assert h2.update_from_frame(det, frame) is True

    print("obstacle_handler.py: OK")


if __name__ == "__main__":
    main()
