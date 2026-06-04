"""Smoke-test agent.main with mocks (run from repo root)."""
import sys
import threading
from pathlib import Path

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class _MockCamera:
    def read(self):
        return True, np.zeros((480, 640, 3), dtype=np.uint8)


class _MockWheels:
    def __init__(self):
        self.last = (0.0, 0.0)

    def set_wheels_speed(self, left, right):
        self.last = (float(left), float(right))


class _MockLeds:
    def set_rgb(self, index, color):
        pass

    def all_on(self):
        pass

    def all_off(self):
        pass


def main():
    from tasks.project.packages import agent

    stop = threading.Event()
    wheels = _MockWheels()

    thread = threading.Thread(
        target=agent.main,
        args=(_MockCamera(), wheels, _MockLeds(), stop),
        daemon=True,
    )
    thread.start()
    stop.wait(0.3)
    stop.set()
    thread.join(timeout=2.0)

    assert thread.is_alive() is False
    assert wheels.last == (0.0, 0.0)
    print("agent.py: OK")


if __name__ == "__main__":
    main()
