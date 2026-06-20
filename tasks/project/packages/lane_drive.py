"""Lane-following helpers between intersection stops."""

from typing import Tuple

import numpy as np

from tasks.project.packages.nav_constants import STRAIGHT_BLIND_SPEED
from tasks.project.packages.road_graph import Turn


class LaneDriveMixin:
    """Lane servoing with blind-straight fallback at intersections."""

    _lane: object
    _blind_straight: bool

    def _lane_confused_at_intersection(self) -> bool:
        info = self._lane.last_debug_info
        if info.get('is_curve'):
            return True

        yellow_xs = info.get('yellow_xs', [])
        white_xs  = info.get('white_xs', [])

        if white_xs and not yellow_xs:
            return True

        if len(yellow_xs) >= 2 and len(white_xs) >= 2:
            w_shift = white_xs[-1] - white_xs[0]
            y_shift = yellow_xs[-1] - yellow_xs[0]
            thresh  = self._lane.curve_threshold
            if abs(w_shift) > thresh and abs(w_shift - y_shift) > 15:
                return True

        return False

    def _drive_lane(self, frame_rgb: np.ndarray) -> Tuple[float, float]:
        left, right = self._lane.compute_commands(frame_rgb)
        stop = self._current_stop()
        need_straight = stop is not None and stop.turn == Turn.STRAIGHT
        self._blind_straight = need_straight and self._lane_confused_at_intersection()
        if self._blind_straight:
            return STRAIGHT_BLIND_SPEED, STRAIGHT_BLIND_SPEED
        return left, right
