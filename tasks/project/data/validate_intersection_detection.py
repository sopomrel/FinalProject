"""Validate intersection_detection.py (run from repo root)."""
import sys
from pathlib import Path

import cv2
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tasks.project.packages.intersection_detection import StopLineDetector


def _frame_with_red_line(h=480, w=640) -> np.ndarray:
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    y = int(h * 0.72)
    cv2.line(frame, (int(w * 0.1), y), (int(w * 0.9), y), (0, 0, 220), 8)
    return frame


def _empty_frame(h=480, w=640) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def main():
    det = StopLineDetector(
        config={
            "confirm_frames": 3,
            "release_frames": 2,
            "min_red_ratio": 0.005,
            "roi_y_start": 0.45,
        }
    )

    empty = _empty_frame()
    red = _frame_with_red_line()

    assert det.red_ratio(empty) < det.min_red_ratio
    assert det.red_ratio(red) >= det.min_red_ratio

    assert det.update(empty) is False
    assert det.update(empty) is False
    assert det.update(red) is False
    assert det.update(red) is False
    assert det.update(red) is True

    det.reset()
    assert det.at_stop_line is False

    print("intersection_detection.py: OK")


if __name__ == "__main__":
    main()
