"""Validate navigation_fsm.py (run from repo root)."""
import sys
from pathlib import Path

import cv2
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tasks.project.packages.intersection_detection import StopLineDetector
from tasks.project.packages.navigation_fsm import NavigationFSM
from tasks.project.packages.navigation_types import NavState, TurnDir


def _red_frame(h=480, w=640):
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    y = int(h * 0.72)
    cv2.line(frame, (int(w * 0.1), y), (int(w * 0.9), y), (0, 0, 220), 8)
    return frame


def _trigger_stop(fsm, red, frames=2):
    for _ in range(frames):
        fsm.update(red)


def _clear_stop(fsm, blank, frames=3):
    for _ in range(frames):
        fsm.update(blank)


def main():
    det_cfg = {"confirm_frames": 2, "release_frames": 1, "min_red_ratio": 0.005}
    fsm = NavigationFSM(stop_line=StopLineDetector(det_cfg))
    red = _red_frame()
    blank = np.zeros((480, 640, 3), dtype=np.uint8)

    assert fsm.start("I_4_7", "I_12_9") == NavState.FOLLOW_LANE
    assert fsm.target_node == "I_7_7"

    _trigger_stop(fsm, red)
    if fsm.state == NavState.TURN:
        fsm.mark_turn_done()
    assert fsm.state == NavState.FOLLOW_LANE
    assert fsm.target_node == "I_12_9"

    _clear_stop(fsm, blank)
    _trigger_stop(fsm, red)
    if fsm.state == NavState.TURN:
        fsm.mark_turn_done()
    assert fsm.state == NavState.GOAL_REACHED

    fsm2 = NavigationFSM()
    assert fsm2.start("I_7_7", "I_7_7") == NavState.GOAL_REACHED

    fsm3 = NavigationFSM()
    fsm3.start()
    assert fsm3.update(blank, obstacle_stop=True) == NavState.OBSTACLE_STOP
    assert fsm3.update(blank, obstacle_stop=False) == NavState.FOLLOW_LANE

    print("navigation_fsm.py: OK")


if __name__ == "__main__":
    main()
