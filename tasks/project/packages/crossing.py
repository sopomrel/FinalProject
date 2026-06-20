"""Intersection crossing — stop/wait, forward creep, smooth turn arcs."""

import time
from typing import Optional, Tuple

import numpy as np

from tasks.project.packages.nav_constants import (
    ARC_CMDS,
    BIAS_ARC_MAX,
    GUARD_PULL_LEFT,
    GUARD_PULL_RIGHT,
    Phase,
    STRAIGHT_BLIND_SPEED,
    WHITE_X_TOO_LEFT_FRAC,
    WHITE_X_TOO_RIGHT_FRAC,
)
from tasks.project.packages.navigation_config import turn_key
from tasks.project.packages.road_graph import Turn


class CrossingMixin:
    """Red-line stop sequence and intersection crossing manoeuvres."""

    _nav_cfg: dict
    _phase: Phase
    _stop_i: int
    _edge_i: int
    _timer_end: float
    _cross_start: float
    _active_stop: object
    _active_turn: Optional[Turn]
    _lane: object
    _stop_line: object
    plan: object
    _blind_straight: bool

    def _cross_forward_s(self, turn: Optional[Turn]) -> float:
        return float(self._nav_cfg['cross_forward_s'][turn_key(turn)])

    def _forward_bias_s(self, turn: Turn) -> float:
        return float(self._nav_cfg['forward_bias_s'][turn_key(turn)])

    def _stop_wait_s(self) -> float:
        return float(self._nav_cfg['stop_wait_s'])

    def _arc_strength(self, turn: Turn, elapsed: float) -> float:
        """0→1 turn strength; forward-bias phase keeps the bot straighter at first."""
        duration = self._cross_forward_s(turn)
        bias   = self._forward_bias_s(turn)
        if bias > 0.0 and elapsed < bias:
            return BIAS_ARC_MAX * (elapsed / bias)
        tail = max(duration - bias, 0.1)
        return BIAS_ARC_MAX + (1.0 - BIAS_ARC_MAX) * min(1.0, (elapsed - bias) / tail)

    def _finish_stop(self) -> None:
        """Advance past the red line we just handled."""
        self._active_stop = None
        self._active_turn = None
        self._stop_line.reset()

        if self._stop_i >= len(self.plan.stops):
            self._begin_victory()
            return

        finished = self.plan.stops[self._stop_i]
        self._stop_i += 1

        if finished.turn is None:
            print(f"[Nav] Goal {self.plan.goal.value} — mission complete")
            self._begin_victory()
            return

        if finished.segment is not None:
            self._edge_i = self.plan.edges.index(finished.segment)

        print(f"[Nav] Red line {self._stop_i}/{self.plan.num_red_lines} cleared — "
              f"lane-follow on {self._segment_name()}")
        self._phase = Phase.LANE_FOLLOWING

    def _begin_red_line(self) -> None:
        stop = self._current_stop()
        if stop is None:
            self._begin_victory()
            return

        self._active_stop = stop
        self._active_turn = stop.turn
        self._timer_end = time.monotonic() + self._stop_wait_s()
        self._phase = Phase.WAIT_AT_LINE

        if stop.turn is None:
            print(f"[Nav] Red line {self._stop_i + 1}/{self.plan.num_red_lines}: "
                  f"goal {stop.intersection.value} — stop then finish")
        else:
            print(f"[Nav] Red line {self._stop_i + 1}/{self.plan.num_red_lines}: "
                  f"{stop.intersection.value} — turn {stop.turn.value}")

    def _begin_crossing(self) -> None:
        """Start moving through the intersection; arc begins immediately if turning."""
        self._cross_start = time.monotonic()
        self._phase = Phase.CROSSING
        turn = self._active_turn
        if turn and turn is not Turn.STRAIGHT:
            print(f"[Nav] Crossing — smooth {turn.value} arc while moving forward")
        else:
            print("[Nav] Crossing — driving through")

    def _guard_white_line(
        self, frame_rgb: np.ndarray, left: float, right: float,
    ) -> Tuple[float, float]:
        """Nudge PWM so the bot stays inside the right lane (solid white on right)."""
        self._lane.compute_commands(frame_rgb)
        white_xs = self._lane.last_debug_info.get('white_xs', [])
        if not white_xs:
            return left, right

        w = frame_rgb.shape[1]
        white_x = float(np.mean(white_xs))
        if white_x < WHITE_X_TOO_LEFT_FRAC * w:
            dl, dr = GUARD_PULL_LEFT
            left  = max(0.04, left - dl)
            right = max(0.04, right - dr)
        elif white_x > WHITE_X_TOO_RIGHT_FRAC * w:
            dl, dr = GUARD_PULL_RIGHT
            left  = min(0.40, left + dl)
            right = min(0.40, right + dr)
        return left, right

    def _cross_arc_pwm(
        self, frame_rgb: np.ndarray, turn: Turn, elapsed: float,
    ) -> Tuple[float, float]:
        """Forward motion + smooth differential arc, with white-line guard."""
        factor   = self._arc_strength(turn, elapsed)
        tgt_l, tgt_r = ARC_CMDS[turn]
        cruise = ARC_CMDS[Turn.STRAIGHT]
        left  = cruise[0] + factor * (tgt_l - cruise[0])
        right = cruise[1] + factor * (tgt_r - cruise[1])
        return self._guard_white_line(frame_rgb, left, right)

    def _cross_straight_pwm(self, frame_rgb: np.ndarray) -> Tuple[float, float]:
        """Drive straight through while hugging the right lane edge."""
        left, right = self._drive_lane(frame_rgb)
        if self._blind_straight:
            left = right = STRAIGHT_BLIND_SPEED
        return self._guard_white_line(frame_rgb, left, right)

    def _crossing_done(self, elapsed: float, red_visible: bool, turn: Optional[Turn]) -> bool:
        """True when the bot has cleared the stop line and finished the manoeuvre."""
        duration = self._cross_forward_s(turn)
        if turn is None or turn is Turn.STRAIGHT:
            return not red_visible and elapsed >= duration
        return elapsed >= duration or (not red_visible and elapsed >= duration * 0.85)
