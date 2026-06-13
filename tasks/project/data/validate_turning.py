"""Validate turning.py (run from repo root)."""
import sys
import threading
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tasks.project.packages.navigation_types import TurnDir
from tasks.project.packages.turning import TurnController, turn_90


class _MockWheels:
    def __init__(self):
        self.history = []
        self.last = (0.0, 0.0)

    def set_wheels_speed(self, left, right):
        self.last = (float(left), float(right))
        self.history.append(self.last)


def main():
    ctrl = TurnController(speed=0.4, duration_90=0.05, loop_dt=0.01)
    stop = threading.Event()

    # LEFT: spins toward left (left wheel back, right wheel forward), then stops.
    wheels = _MockWheels()
    assert ctrl.execute(wheels, TurnDir.LEFT, stop) is True
    assert (-0.4, 0.4) in wheels.history
    assert wheels.last == (0.0, 0.0)

    # RIGHT: mirror direction.
    wheels = _MockWheels()
    assert ctrl.execute(wheels, TurnDir.RIGHT, stop) is True
    assert (0.4, -0.4) in wheels.history
    assert wheels.last == (0.0, 0.0)

    # STRAIGHT: no spin, just a safe stop.
    wheels = _MockWheels()
    assert ctrl.execute(wheels, TurnDir.STRAIGHT, stop) is True
    assert all(cmd == (0.0, 0.0) for cmd in wheels.history)

    # Interrupted turn: stop_event already set -> returns False, motors stopped.
    wheels = _MockWheels()
    fired = threading.Event()
    fired.set()
    assert ctrl.execute(wheels, TurnDir.LEFT, fired) is False
    assert wheels.last == (0.0, 0.0)

    # Convenience wrapper works with a default controller.
    wheels = _MockWheels()
    assert turn_90(wheels, TurnDir.STRAIGHT, stop) is True

    print("turning.py: OK")


if __name__ == "__main__":
    main()
