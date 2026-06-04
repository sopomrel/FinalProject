from typing import List, Optional

import numpy as np

from tasks.project.packages.graph_model import RoadNetwork
from tasks.project.packages.intersection_detection import StopLineDetector
from tasks.project.packages.navigation_types import NavState, PathStep, TurnDir
from tasks.project.packages.path_planner import plan_route


class NavigationFSM:
    """Drive a planned route: lane follow → stop line → turn → next leg."""

    def __init__(
        self,
        network: Optional[RoadNetwork] = None,
        stop_line: Optional[StopLineDetector] = None,
    ):
        self.network = network or RoadNetwork.from_yaml()
        self.stop_line = stop_line or StopLineDetector()
        self.state = NavState.IDLE
        self.route: List[PathStep] = []
        self.step_index = 0
        self.current_step: Optional[PathStep] = None
        self._turn_pending = False

    def start(self, start: Optional[str] = None, goal: Optional[str] = None) -> NavState:
        self.route = plan_route(self.network, start, goal)
        self.step_index = 0
        self.stop_line.reset()
        self._turn_pending = False

        if not self.route:
            self.current_step = None
            self.state = NavState.GOAL_REACHED
            return self.state

        self.current_step = self.route[0]
        self.state = NavState.FOLLOW_LANE
        return self.state

    @property
    def next_turn(self) -> TurnDir:
        if self.current_step is None:
            return TurnDir.STRAIGHT
        return self.current_step.turn

    @property
    def target_node(self) -> Optional[str]:
        if self.current_step is None:
            return None
        return self.current_step.to_node

    def mark_turn_done(self) -> None:
        """Call after turn primitive finishes (wired in agent / turning.py)."""
        if self.state == NavState.TURN:
            self._turn_pending = False
            self._advance_step()

    def update(
        self,
        frame_bgr: Optional[np.ndarray],
        obstacle_stop: bool = False,
    ) -> NavState:
        if self.state in (NavState.IDLE, NavState.GOAL_REACHED, NavState.VICTORY, NavState.PARKING):
            return self.state

        if self.state == NavState.OBSTACLE_STOP:
            if not obstacle_stop:
                self.state = NavState.FOLLOW_LANE
            return self.state

        if obstacle_stop and self.state == NavState.FOLLOW_LANE:
            self.state = NavState.OBSTACLE_STOP
            return self.state

        if self.state == NavState.FOLLOW_LANE:
            if frame_bgr is not None:
                self.stop_line.update(frame_bgr)
            if self.stop_line.at_stop_line:
                self.state = NavState.STOP_AT_LINE
                return self._handle_stop_at_line()
            return self.state

        if self.state == NavState.STOP_AT_LINE:
            return self._handle_stop_at_line()

        if self.state == NavState.TURN:
            return self.state

        return self.state

    def _handle_stop_at_line(self) -> NavState:
        if self.current_step and self.current_step.turn != TurnDir.STRAIGHT:
            self.state = NavState.TURN
            self._turn_pending = True
        else:
            self._advance_step()
        return self.state

    def _advance_step(self) -> None:
        self.step_index += 1
        self.stop_line.reset()

        if self.step_index >= len(self.route):
            self.current_step = None
            self.state = NavState.GOAL_REACHED
            return

        self.current_step = self.route[self.step_index]
        self.state = NavState.FOLLOW_LANE
