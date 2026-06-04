import os
from typing import Optional, Tuple

import cv2
import numpy as np
import yaml

_CONFIG_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "navigation_hsv_config.yaml")
)


def _load_config() -> dict:
    try:
        with open(_CONFIG_FILE) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def _red_bounds(cfg: dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    lo1 = np.array([
        cfg.get("red_lower_h_1", 0),
        cfg.get("red_lower_s_1", 80),
        cfg.get("red_lower_v_1", 80),
    ])
    hi1 = np.array([
        cfg.get("red_upper_h_1", 10),
        cfg.get("red_upper_s_1", 255),
        cfg.get("red_upper_v_1", 255),
    ])
    lo2 = np.array([
        cfg.get("red_lower_h_2", 160),
        cfg.get("red_lower_s_2", 80),
        cfg.get("red_lower_v_2", 80),
    ])
    hi2 = np.array([
        cfg.get("red_upper_h_2", 179),
        cfg.get("red_upper_s_2", 255),
        cfg.get("red_upper_v_2", 255),
    ])
    return lo1, hi1, lo2, hi2


class StopLineDetector:
    """Detect red stop line with frame hysteresis."""

    def __init__(self, config: Optional[dict] = None):
        cfg = config or _load_config()
        self._lo1, self._hi1, self._lo2, self._hi2 = _red_bounds(cfg)
        self.roi_y_start = float(cfg.get("roi_y_start", 0.45))
        self.roi_x_margin = float(cfg.get("roi_x_margin", 0.15))
        self.min_red_ratio = float(cfg.get("min_red_ratio", 0.012))
        self.confirm_frames = int(cfg.get("confirm_frames", 3))
        self.release_frames = int(cfg.get("release_frames", 2))
        self._seen_streak = 0
        self._miss_streak = 0
        self.at_stop_line = False

    def reset(self) -> None:
        self._seen_streak = 0
        self._miss_streak = 0
        self.at_stop_line = False

    def red_ratio(self, frame_bgr: np.ndarray) -> float:
        """Fraction of red pixels in the lower ROI (0..1)."""
        if frame_bgr is None or frame_bgr.size == 0:
            return 0.0
        h, w = frame_bgr.shape[:2]
        y0 = int(h * self.roi_y_start)
        x0 = int(w * self.roi_x_margin)
        x1 = int(w * (1.0 - self.roi_x_margin))
        roi = frame_bgr[y0:, x0:x1]
        if roi.size == 0:
            return 0.0

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        hsv = cv2.GaussianBlur(hsv, (5, 5), 0)
        mask = cv2.inRange(hsv, self._lo1, self._hi1) | cv2.inRange(hsv, self._lo2, self._hi2)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return float(np.count_nonzero(mask)) / float(mask.size)

    def seen_this_frame(self, frame_bgr: np.ndarray) -> bool:
        return self.red_ratio(frame_bgr) >= self.min_red_ratio

    def update(self, frame_bgr: np.ndarray) -> bool:
        """Update state; returns stable at_stop_line."""
        if self.seen_this_frame(frame_bgr):
            self._seen_streak += 1
            self._miss_streak = 0
            if not self.at_stop_line and self._seen_streak >= self.confirm_frames:
                self.at_stop_line = True
        else:
            self._miss_streak += 1
            self._seen_streak = 0
            if self.at_stop_line and self._miss_streak >= self.release_frames:
                self.at_stop_line = False
        return self.at_stop_line
