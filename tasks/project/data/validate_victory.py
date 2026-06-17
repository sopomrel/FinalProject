"""Validate victory.py celebration (run from repo root)."""
import sys
import threading
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tasks.project.packages.victory import VictoryCelebration, celebrate


class _MockWheels:
    def __init__(self):
        self.history = []
        self.last = (0.0, 0.0)

    def set_wheels_speed(self, left, right):
        self.last = (float(left), float(right))
        self.history.append(self.last)


class _MockLeds:
    def __init__(self):
        self.on_count = 0
        self.off_count = 0
        self.colors = {}

    def set_rgb(self, index, color):
        self.colors[index] = list(color)

    def all_on(self):
        self.on_count += 1

    def all_off(self):
        self.off_count += 1


def main():
    # Short spin so the test runs fast.
    celebration = VictoryCelebration(spin_speed=0.4, spin_duration=0.2, flash_hz=10.0, loop_dt=0.01)
    stop = threading.Event()

    wheels = _MockWheels()
    leds = _MockLeds()
    assert celebration.execute(wheels, leds, stop) is True
    # It spun (non-zero command issued) and ended stopped.
    assert any(cmd != (0.0, 0.0) for cmd in wheels.history)
    assert wheels.last == (0.0, 0.0)
    # LEDs flashed at least once and finished on.
    assert leds.off_count > 0
    assert leds.on_count > 0

    # Works with no LEDs (hardware may be missing).
    wheels = _MockWheels()
    assert celebration.execute(wheels, None, stop) is True
    assert wheels.last == (0.0, 0.0)

    # Interrupted celebration: stop_event already set -> False, motors stopped.
    wheels = _MockWheels()
    leds = _MockLeds()
    fired = threading.Event()
    fired.set()
    assert celebration.execute(wheels, leds, fired) is False
    assert wheels.last == (0.0, 0.0)

    # Convenience wrapper runs with defaults (kept short via a custom celebration).
    wheels = _MockWheels()
    assert celebrate(wheels, None, stop, celebration=celebration) is True

    print("victory.py: OK")


if __name__ == "__main__":
    main()
