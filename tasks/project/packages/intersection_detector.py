"""Red stop-line detection — follows the same pattern as visual_servoing_activity.py.

Core API
========
``detect_red_stopline(image)``
    Takes a BGR image, returns a single float32 mask (0.0 / 1.0 per pixel)
    where red pixels are 1.0.  Mirrors ``detect_lane_markings()`` in
    ``visual_servoing_activity.py``.

``set_hsv_bounds(r1_lower, r1_upper, r2_lower, r2_upper)``
``get_hsv_bounds()``
    Live-update the thresholds from the dashboard without restarting.
    All values persisted to ``config/navigation_hsv_config.yaml``.

Why two ranges?
===============
Red wraps the HSV hue wheel — both 0° and 180° represent red.
Two ``cv2.inRange`` passes are OR-ed to capture the full red band:

    range-1: hue in [0,  red_upper_h_1]      (red near 0°)
    range-2: hue in [red_lower_h_2, 179]     (red near 180°)

IntersectionDetector (class)
============================
Thin stateful wrapper around ``detect_red_stopline`` that restricts
detection to a bottom-of-frame ROI, computes the red pixel ratio, and
debounces the trigger with confirm / release frame counts — the same
idea as the pixel-threshold approach in ``LaneServoingAgent``.
"""

from __future__ import annotations

import os
from typing import Tuple

import cv2
import numpy as np
import yaml

# ── Config file ───────────────────────────────────────────────────────────────

_CONFIG_FILE = os.path.normpath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'config', 'navigation_hsv_config.yaml'
))

try:
    with open(_CONFIG_FILE) as _f:
        _h = yaml.safe_load(_f) or {}
except FileNotFoundError:
    _h = {}

# ── Module-level HSV globals (same style as visual_servoing_activity.py) ──────

_r1_lower = np.array([_h.get('red_lower_h_1', 0),   _h.get('red_lower_s_1', 80),  _h.get('red_lower_v_1', 80)],  dtype=np.uint8)
_r1_upper = np.array([_h.get('red_upper_h_1', 10),  _h.get('red_upper_s_1', 255), _h.get('red_upper_v_1', 255)], dtype=np.uint8)
_r2_lower = np.array([_h.get('red_lower_h_2', 160), _h.get('red_lower_s_2', 80),  _h.get('red_lower_v_2', 80)],  dtype=np.uint8)
_r2_upper = np.array([_h.get('red_upper_h_2', 179), _h.get('red_upper_s_2', 255), _h.get('red_upper_v_2', 255)], dtype=np.uint8)

_roi_y_start:   float = _h.get('roi_y_start',   0.45)
_roi_x_margin:  float = _h.get('roi_x_margin',  0.15)
_min_red_ratio: float = _h.get('min_red_ratio',  0.012)
_confirm_frames: int  = _h.get('confirm_frames', 3)
_release_frames: int  = _h.get('release_frames', 2)


# ── Core detection function (mirrors detect_lane_markings) ────────────────────

def detect_red_stopline(image: np.ndarray) -> np.ndarray:
    """Detect red stop-line pixels in a BGR image.

    Parameters
    ----------
    image : np.ndarray
        Full-frame BGR image (any resolution).

    Returns
    -------
    mask_red : np.ndarray, float32, shape (H, W)
        1.0 where red pixels were found, 0.0 elsewhere.
        Normalised to 0/1 so callers can multiply by 255 for display,
        just like ``detect_lane_markings`` returns float32 masks.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Dual-range: red wraps the hue wheel
    mask1 = cv2.inRange(hsv, _r1_lower, _r1_upper)   # near 0°
    mask2 = cv2.inRange(hsv, _r2_lower, _r2_upper)   # near 180°
    combined = cv2.bitwise_or(mask1, mask2)           # 0 or 255

    return (combined > 0).astype(np.float32)          # normalise to 0/1


# ── HSV bounds API (identical signature to visual_servoing_activity.py) ───────

def set_hsv_bounds(
    r1_lower: list,
    r1_upper: list,
    r2_lower: list,
    r2_upper: list,
) -> None:
    """Hot-update red HSV thresholds from the dashboard (no restart needed)."""
    global _r1_lower, _r1_upper, _r2_lower, _r2_upper
    _r1_lower = np.array(r1_lower, dtype=np.uint8)
    _r1_upper = np.array(r1_upper, dtype=np.uint8)
    _r2_lower = np.array(r2_lower, dtype=np.uint8)
    _r2_upper = np.array(r2_upper, dtype=np.uint8)


def get_hsv_bounds() -> dict:
    """Return current thresholds in the same flat format as the YAML file."""
    return {
        'red_lower_h_1': int(_r1_lower[0]), 'red_lower_s_1': int(_r1_lower[1]), 'red_lower_v_1': int(_r1_lower[2]),
        'red_upper_h_1': int(_r1_upper[0]), 'red_upper_s_1': int(_r1_upper[1]), 'red_upper_v_1': int(_r1_upper[2]),
        'red_lower_h_2': int(_r2_lower[0]), 'red_lower_s_2': int(_r2_lower[1]), 'red_lower_v_2': int(_r2_lower[2]),
        'red_upper_h_2': int(_r2_upper[0]), 'red_upper_s_2': int(_r2_upper[1]), 'red_upper_v_2': int(_r2_upper[2]),
        'roi_y_start':    _roi_y_start,
        'roi_x_margin':   _roi_x_margin,
        'min_red_ratio':  _min_red_ratio,
        'confirm_frames': _confirm_frames,
        'release_frames': _release_frames,
    }


def set_roi_params(
    roi_y_start: float,
    roi_x_margin: float,
    min_red_ratio: float,
) -> None:
    """Adjust ROI and sensitivity live from the dashboard."""
    global _roi_y_start, _roi_x_margin, _min_red_ratio
    _roi_y_start   = roi_y_start
    _roi_x_margin  = roi_x_margin
    _min_red_ratio = min_red_ratio


# ── Stateful wrapper with ROI crop + debounce ─────────────────────────────────

class IntersectionDetector:
    """Wraps ``detect_red_stopline`` with a bottom-of-frame ROI and debouncing.

    Usage mirrors ``LaneServoingAgent``::

        detector = IntersectionDetector()
        while running:
            ok, frame = camera.read()
            if detector.detect(frame):
                # confirmed stop line — execute turn
    """

    def __init__(self) -> None:
        self._pos_streak: int  = 0
        self._neg_streak: int  = 0
        self._triggered:  bool = False

        # Exposed for dashboard / visualisation
        self.last_ratio:    float      = 0.0
        self.last_mask_red: np.ndarray = np.zeros((1, 1), dtype=np.uint8)

    # ── Public API ─────────────────────────────────────────────────────────

    def detect(self, image: np.ndarray) -> bool:
        """Return True when a confirmed stop line is present.

        Crops the frame to the configured ROI, runs ``detect_red_stopline``,
        computes the red-pixel ratio, then debounces with confirm/release
        frame counts — identical logic to the pixel-threshold in
        ``LaneServoingAgent._motor_commands``.
        """
        roi, y0, x0 = self._crop_roi(image)

        # Run the same mask function as the rest of the pipeline
        mask_float = detect_red_stopline(roi)                     # 0.0 / 1.0
        mask_u8    = (mask_float * 255).astype(np.uint8)          # 0 / 255

        self.last_mask_red = mask_u8

        total      = mask_float.size
        red_pixels = int(np.count_nonzero(mask_float))
        ratio      = red_pixels / total if total else 0.0
        self.last_ratio = ratio

        above = ratio >= _min_red_ratio

        if above:
            self._pos_streak += 1
            self._neg_streak  = 0
        else:
            self._neg_streak += 1
            self._pos_streak  = 0

        if not self._triggered and self._pos_streak >= _confirm_frames:
            self._triggered = True
        if self._triggered and self._neg_streak >= _release_frames:
            self._triggered = False

        return self._triggered

    def reset(self) -> None:
        """Force-clear the triggered state after executing a turn."""
        self._triggered  = False
        self._pos_streak = 0
        self._neg_streak = 0

    def debug_frame(self, image: np.ndarray) -> np.ndarray:
        """Return a BGR visualisation: camera with ROI box + red mask overlay.

        Follows the same overlay style as ``create_lane_visualization`` — the
        mask is tinted on top of the camera image so you can see exactly what
        pixels were counted.
        """
        h, w = image.shape[:2]
        y0 = int(h * _roi_y_start)
        x0 = int(w * _roi_x_margin)
        x1 = w - x0

        vis = image.copy()

        # Red mask overlay on ROI (same addWeighted blend as lane vis)
        if self.last_mask_red.shape[0] > 1:
            roi_h, roi_w = h - y0, x1 - x0
            m = cv2.resize(self.last_mask_red, (roi_w, roi_h))
            overlay = vis[y0:h, x0:x1].copy()
            overlay[m > 0] = (0, 0, 255)                              # red tint
            cv2.addWeighted(overlay, 0.45, vis[y0:h, x0:x1], 0.55, 0,
                            vis[y0:h, x0:x1])

        # ROI rectangle
        box_colour = (0, 0, 255) if self._triggered else (0, 255, 0)
        cv2.rectangle(vis, (x0, y0), (x1, h - 1), box_colour, 2)

        # Readout text
        label = f"red={self.last_ratio:.3f}  {'[STOP LINE]' if self._triggered else ''}"
        cv2.putText(vis, label, (x0 + 4, y0 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_colour, 1)

        return vis

    # ── Internal ───────────────────────────────────────────────────────────

    def _crop_roi(
        self, image: np.ndarray
    ) -> Tuple[np.ndarray, int, int]:
        """Return (roi_bgr, y0, x0) for the configured ROI slice."""
        h, w = image.shape[:2]
        y0 = int(h * _roi_y_start)
        x0 = int(w * _roi_x_margin)
        x1 = w - x0
        return image[y0:, x0:x1], y0, x0
