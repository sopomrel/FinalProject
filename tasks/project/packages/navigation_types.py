from dataclasses import dataclass
from enum import Enum


class NavState(Enum):
    IDLE = "idle"
    FOLLOW_LANE = "follow_lane"
    APPROACH_INTERSECTION = "approach_intersection"
    STOP_AT_LINE = "stop_at_line"
    TURN = "turn"
    OBSTACLE_STOP = "obstacle_stop"
    GOAL_REACHED = "goal_reached"
    PARKING = "parking"
    VICTORY = "victory"


class TurnDir(Enum):
    LEFT = "left"
    RIGHT = "right"
    STRAIGHT = "straight"


@dataclass(frozen=True)
class PathStep:
    """One edge along the route: arrive at to_node, then take turn leaving it."""

    to_node: str
    turn: TurnDir
