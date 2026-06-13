import time
from typing import Optional, Tuple

from tasks.project.packages.navigation_types import TurnDir

# Open-loop 90° turn calibration. The bot has no wheel encoders here, so a turn
# is timed: spin in place at TURN_SPEED for TURN_DURATION_90 to sweep ~90°.
# Re-measure these two numbers on the physical mat (battery level shifts them).
TURN_SPEED = 0.35
TURN_DURATION_90 = 1.0
_LOOP_DT = 0.05


class TurnController:
    """Timed in-place 90° turn primitive (differential drive, no encoders)."""

    def __init__(
        self,
        speed: float = TURN_SPEED,
        duration_90: float = TURN_DURATION_90,
        loop_dt: float = _LOOP_DT,
    ):
        self.speed = float(speed)
        self.duration_90 = float(duration_90)
        self.loop_dt = float(loop_dt)

    def wheel_speeds(self, turn: TurnDir) -> Tuple[float, float]:
        """(left, right) speeds to spin in place. Robot turns toward slower wheel."""
        if turn == TurnDir.LEFT:
            return -self.speed, self.speed
        if turn == TurnDir.RIGHT:
            return self.speed, -self.speed
        return 0.0, 0.0

    def _drive_for(self, wheels, left, right, duration, stop_event) -> bool:
        """Hold (left, right) for duration seconds. Returns False if interrupted."""
        wheels.set_wheels_speed(left, right)
        deadline = time.time() + duration
        while time.time() < deadline:
            if stop_event is not None:
                if stop_event.wait(self.loop_dt):
                    return False
            else:
                time.sleep(self.loop_dt)
        return True

    def execute(
        self,
        wheels,
        turn: TurnDir,
        stop_event=None,
        quarters: float = 1.0,
    ) -> bool:
        """Spin ~90°*quarters in `turn` direction, then stop.

        STRAIGHT is a no-op (FSM advances without a turn). Returns True when the
        turn ran to completion, False if stop_event fired mid-turn.
        """
        if turn == TurnDir.STRAIGHT:
            wheels.set_wheels_speed(0.0, 0.0)
            return True

        left, right = self.wheel_speeds(turn)
        completed = self._drive_for(
            wheels, left, right, self.duration_90 * float(quarters), stop_event
        )
        wheels.set_wheels_speed(0.0, 0.0)
        return completed


def turn_90(
    wheels,
    turn: TurnDir,
    stop_event=None,
    controller: Optional[TurnController] = None,
) -> bool:
    """Convenience wrapper: run one 90° turn with a default controller."""
    ctrl = controller or TurnController()
    return ctrl.execute(wheels, turn, stop_event)
