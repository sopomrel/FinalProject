"""Shared navigation constants — speeds, LED colours, phase enum."""

from enum import Enum, auto

from tasks.project.packages.road_graph import Turn

LOOP_DT = 0.05

# Gentle forward arc (inner wheel slower, outer faster — no pivot-in-place).
ARC_CMDS: dict = {
    Turn.STRAIGHT: (0.18, 0.18),
    Turn.LEFT:     (0.11, 0.23),
    Turn.RIGHT:    (0.23, 0.11),
}

STRAIGHT_BLIND_SPEED = 0.18
CROSS_SPEED = 0.12
VICTORY_FORWARD_SPEED = 0.15
VICTORY_SPIN_SPEED = 0.18
BIAS_ARC_MAX = 0.35

# White-line guard during arc (right-hand lane — do not cross solid white on right).
WHITE_X_TOO_LEFT_FRAC = 0.58
WHITE_X_TOO_RIGHT_FRAC = 0.92
GUARD_PULL_LEFT = (0.05, 0.07)
GUARD_PULL_RIGHT = (0.03, 0.01)


class Phase(Enum):
    LANE_FOLLOWING = auto()
    WAIT_AT_LINE   = auto()
    CROSSING       = auto()   # forward through intersection (+ smooth arc if turning)
    OBSTACLE_STOP  = auto()
    VICTORY        = auto()   # forward creep + spin with flashing LEDs
    DONE           = auto()
