"""Project agent — Dijkstra route + lane following + red-line intersection stops.

Mission flow
============
1. ``plan_route(start, goal, approach_heading)`` fixes the path and every turn.
2. Lane-follow until a red line → stop → **crossing** (forward + smooth arc).
3. Turns start the moment crossing begins (no stop-then-pivot).
4. White-line guard keeps the bot inside the right lane during the arc.
5. Victory dance at the goal — forward creep, spin, flashing LEDs.

Same ``ProjectAgent`` runs in simulation (virtual server) and on hardware (real server).
"""

import time
from typing import Optional, Tuple

import cv2
import numpy as np

from tasks.object_detection.packages.agent import ObjectDetectionAgent, CLASS_NAMES
from tasks.object_detection.packages.stop_activity import should_stop, stopping_detection
from tasks.project.packages.crossing import CrossingMixin
from tasks.project.packages.intersection_detector import IntersectionDetector
from tasks.project.packages.lane_drive import LaneDriveMixin
from tasks.project.packages.led_control import (
    show_done_leds,
    show_forward_leds,
    show_stopped_leds,
    show_turn_leds,
)
from tasks.project.packages.nav_constants import (
    CROSS_SPEED,
    LOOP_DT,
    Phase,
)
from tasks.project.packages.navigation_config import (
    DEFAULT_NAV_CONFIG,
    load_navigation_config,
    save_navigation_config,
)
from tasks.project.packages.road_graph import (
    Cardinal,
    Intersection,
    RedLineStop,
    Turn,
    plan_route,
)
from tasks.project.packages.victory import VictoryMixin
from tasks.visual_lane_servoing.packages.agent import LaneServoingAgent

# Re-exported for servers and dashboard.
__all__ = [
    'ProjectAgent',
    'load_navigation_config',
    'save_navigation_config',
    'main',
]


class ProjectAgent(LaneDriveMixin, CrossingMixin, VictoryMixin):
    """Drive a pre-planned route using lane servoing between red-line stops."""

    def __init__(
        self,
        start: Intersection = Intersection.A,
        goal:  Intersection = Intersection.C,
        approach_heading: Optional[Cardinal] = None,
        enable_object_detection: bool = True,
        nav_config_path: Optional[str] = None,
    ):
        self._nav_cfg = load_navigation_config(nav_config_path)
        self.plan = plan_route(start, goal, approach_heading)

        self._lane = LaneServoingAgent()
        self._stop_line = IntersectionDetector()
        self._detector: Optional[ObjectDetectionAgent] = (
            ObjectDetectionAgent() if enable_object_detection else None
        )

        self._phase = Phase.LANE_FOLLOWING
        self._stop_i = 0
        self._edge_i = 0
        self._timer_end = 0.0
        self._cross_start = 0.0
        self._victory_start = 0.0
        self._active_stop: Optional[RedLineStop] = None
        self._active_turn: Optional[Turn] = None

        self.last_pwm: Tuple[float, float] = (0.0, 0.0)
        self.last_frame: Optional[np.ndarray] = None
        self._last_detections = []
        self._stop_reason = ''
        self._blind_straight = False

        print(f"[Nav] {self.plan.summary()}")
        cfs = self._nav_cfg['cross_forward_s']
        fbs = self._nav_cfg['forward_bias_s']
        print(f"[Nav] Crossing forward: straight={cfs['straight']}s  "
              f"left={cfs['left']}s  right={cfs['right']}s  "
              f"(bias left={fbs['left']}s right={fbs['right']}s)")
        for i, stop in enumerate(self.plan.stops):
            seg = stop.segment.route_id if stop.segment else "—"
            turn = stop.turn.value if stop.turn else "DONE"
            print(f"  red line {i + 1}/{self.plan.num_red_lines}: "
                  f"{stop.intersection.value}  turn={turn}  segment={seg}")

    # ── Route progress ────────────────────────────────────────────────────

    def reset_route(self) -> None:
        """Re-run the same plan from lane-following (robot stays put)."""
        self._phase = Phase.LANE_FOLLOWING
        self._stop_i = 0
        self._edge_i = 0
        self._timer_end = 0.0
        self._cross_start = 0.0
        self._victory_start = 0.0
        self._active_stop = None
        self._active_turn = None
        self._stop_line.reset()
        self._last_detections = []
        self._stop_reason = ''
        print(f"[Nav] Reset — drive to red line 1 at {self.plan.start.value}")

    def clear_obstacle(self) -> None:
        """Resume navigation after a detected obstacle is removed from the scene."""
        if self._phase == Phase.OBSTACLE_STOP:
            self._phase = Phase.LANE_FOLLOWING
        self._last_detections = []
        self._stop_reason = ''

    def obstacle_removal_bbox(self) -> Optional[list]:
        """Bbox [x1,y1,x2,y2] of the duck blocking the robot, if any."""
        if not self._last_detections or self.last_frame is None:
            return None
        img_h = self.last_frame.shape[0]
        det = stopping_detection(self._last_detections, img_h)
        if det is None:
            det = max(self._last_detections, key=lambda d: d[0][3])
        bbox, _, _ = det
        return list(bbox)

    def apply_navigation_config(self, cfg: dict) -> None:
        """Apply timing changes live (also used after dashboard updates)."""
        self._nav_cfg = {
            'stop_wait_s': float(cfg['stop_wait_s']),
            'cross_forward_s': dict(cfg['cross_forward_s']),
            'forward_bias_s': dict(cfg['forward_bias_s']),
            'victory_forward_s': float(cfg.get(
                'victory_forward_s', DEFAULT_NAV_CONFIG['victory_forward_s'],
            )),
            'victory_spin_s': float(cfg.get(
                'victory_spin_s', DEFAULT_NAV_CONFIG['victory_spin_s'],
            )),
        }
        cfs = self._nav_cfg['cross_forward_s']
        fbs = self._nav_cfg['forward_bias_s']
        print(f"[Nav] Timing updated — cross straight={cfs['straight']}s "
              f"left={cfs['left']}s right={cfs['right']}s "
              f"bias left={fbs['left']}s right={fbs['right']}s "
              f"victory forward={self._nav_cfg['victory_forward_s']}s "
              f"spin={self._nav_cfg['victory_spin_s']}s")

    def _current_stop(self) -> Optional[RedLineStop]:
        if self._stop_i < len(self.plan.stops):
            return self.plan.stops[self._stop_i]
        return None

    def _segment_name(self) -> str:
        if self._edge_i < len(self.plan.edges):
            return self.plan.edges[self._edge_i].route_id
        return "done"

    def _next_turn_hint(self) -> str:
        stop = self._current_stop()
        if stop is None:
            return "—"
        if stop.turn is None:
            return "goal"
        return stop.turn.value

    # ── Control tick ──────────────────────────────────────────────────────

    def tick(self, frame_bgr: np.ndarray, wheels, leds, stop_event=None) -> None:
        self.last_frame = frame_bgr
        self._blind_straight = False
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        detections: list = []
        if self._detector is not None:
            result = self._detector.detect(frame_rgb)
            if result is not None:
                self._last_detections = result
            detections = self._last_detections

        now = time.monotonic()

        if self._phase == Phase.VICTORY:
            self._tick_victory(now, wheels, leds)
            return

        if self._phase == Phase.DONE:
            wheels.set_wheels_speed(0.0, 0.0)
            self.last_pwm = (0.0, 0.0)
            show_done_leds(leds)
            return

        if self._phase == Phase.OBSTACLE_STOP:
            stop, reason = should_stop(detections, frame_rgb.shape[0])
            if stop:
                self._stop_reason = reason
                wheels.set_wheels_speed(0.0, 0.0)
                self.last_pwm = (0.0, 0.0)
                show_stopped_leds(leds)
                return
            self._phase = Phase.LANE_FOLLOWING
            self._stop_reason = ''

        if detections:
            stop, reason = should_stop(detections, frame_rgb.shape[0])
            if stop:
                print(f"[Nav] Obstacle: {reason}")
                self._stop_reason = reason
                wheels.set_wheels_speed(0.0, 0.0)
                self.last_pwm = (0.0, 0.0)
                self._phase = Phase.OBSTACLE_STOP
                show_stopped_leds(leds)
                return

        if self._phase == Phase.WAIT_AT_LINE:
            wheels.set_wheels_speed(0.0, 0.0)
            self.last_pwm = (0.0, 0.0)
            show_stopped_leds(leds)
            if now >= self._timer_end:
                self._begin_crossing()
            return

        if self._phase == Phase.CROSSING:
            turn = self._active_turn
            elapsed = now - self._cross_start
            red_visible = self._stop_line.detect(frame_bgr)

            if turn is None:
                spd = CROSS_SPEED if red_visible else CROSS_SPEED * 0.7
                wheels.set_wheels_speed(spd, spd)
                self.last_pwm = (spd, spd)
                show_forward_leds(leds)
                if self._crossing_done(elapsed, red_visible, turn):
                    self._finish_stop()
                return

            if turn is Turn.STRAIGHT:
                left, right = self._cross_straight_pwm(frame_rgb)
                wheels.set_wheels_speed(left, right)
                self.last_pwm = (left, right)
                show_forward_leds(leds)
                if self._crossing_done(elapsed, red_visible, turn):
                    self._finish_stop()
                return

            left, right = self._cross_arc_pwm(frame_rgb, turn, elapsed)
            wheels.set_wheels_speed(left, right)
            self.last_pwm = (left, right)
            show_turn_leds(leds, turn.value, now)
            if self._crossing_done(elapsed, red_visible, turn):
                self._finish_stop()
            return

        # LANE_FOLLOWING — also handles the initial drive toward red line 1.
        if self._stop_line.detect(frame_bgr):
            wheels.set_wheels_speed(0.0, 0.0)
            self.last_pwm = (0.0, 0.0)
            show_stopped_leds(leds)
            self._begin_red_line()
            return

        left, right = self._drive_lane(frame_rgb)
        wheels.set_wheels_speed(left, right)
        self.last_pwm = (left, right)
        show_forward_leds(leds)

    def run(self, camera, wheels, leds, stop_event) -> None:
        try:
            while not stop_event.is_set():
                ok, frame_bgr = camera.read()
                if not ok:
                    stop_event.wait(LOOP_DT)
                    continue
                self.tick(frame_bgr, wheels, leds, stop_event)
                stop_event.wait(LOOP_DT)
        finally:
            wheels.set_wheels_speed(0.0, 0.0)
            self.last_pwm = (0.0, 0.0)
            if leds:
                try:
                    leds.all_off()
                except OSError:
                    pass

    def get_debug_info(self) -> dict:
        stop = self._current_stop()
        stop_inter = stop.intersection.value if stop else "—"
        return {
            "pwm_left":         self.last_pwm[0],
            "pwm_right":        self.last_pwm[1],
            "state":            self._phase.name,
            "route_start":      self.plan.start.value,
            "route_goal":       self.plan.goal.value,
            "approach_heading": (
                self.plan.approach_heading.value
                if self.plan.approach_heading else None
            ),
            "total_mats":       self.plan.total_mats,
            "num_red_lines":    self.plan.num_red_lines,
            "red_line_index":   self._stop_i + 1 if self._stop_i < self.plan.num_red_lines else self.plan.num_red_lines,
            "red_line_total":   self.plan.num_red_lines,
            "next_stop":        stop_inter,
            "next_turn":        self._next_turn_hint(),
            "edge_index":       self._edge_i,
            "edge_name":        self._segment_name(),
            "route_summary":    self.plan.summary(),
            "stops":            [
                {
                    "intersection": s.intersection.value,
                    "turn": s.turn.value if s.turn else "done",
                    "segment": s.segment.route_id if s.segment else None,
                }
                for s in self.plan.stops
            ],
            "detections":       len(self._last_detections),
            "detection_list":   [
                {
                    'class': CLASS_NAMES.get(c, str(c)),
                    'score': round(s, 3),
                    'bbox':  list(b),
                }
                for b, s, c in self._last_detections
            ],
            "stopped_by_detection": self._phase == Phase.OBSTACLE_STOP,
            "stop_reason":          self._stop_reason,
            "model_loaded":         (
                self._detector.model_loaded if self._detector is not None else False
            ),
            "load_error":           (
                self._detector.load_error if self._detector is not None else None
            ),
            "trt_building":         (
                getattr(self._detector, 'trt_building', False)
                if self._detector is not None else False
            ),
            "conf_threshold":       (
                self._detector.conf_threshold if self._detector is not None else 0.5
            ),
            "red_ratio":        round(self._stop_line.last_ratio, 4),
            "at_stopline":      self._stop_line._triggered,
            "blind_straight":   self._blind_straight,
            "cross_elapsed":    round(
                max(0.0, time.monotonic() - self._cross_start), 2
            ) if self._phase == Phase.CROSSING else 0.0,
            "cross_forward_s":  self._nav_cfg['cross_forward_s'],
            "forward_bias_s":   self._nav_cfg['forward_bias_s'],
            "victory_forward_s": self._victory_forward_s(),
            "victory_spin_s":    self._victory_spin_s(),
            "victory_elapsed": round(
                max(0.0, time.monotonic() - self._victory_start), 2
            ) if self._phase == Phase.VICTORY else 0.0,
        }


def main(
    camera,
    wheels,
    leds,
    stop_event,
    enable_object_detection: bool = True,
    start: Intersection = Intersection.A,
    goal:  Intersection = Intersection.C,
    approach_heading: Optional[Cardinal] = None,
) -> None:
    ProjectAgent(
        start=start,
        goal=goal,
        approach_heading=approach_heading,
        enable_object_detection=enable_object_detection,
    ).run(camera, wheels, leds, stop_event)
