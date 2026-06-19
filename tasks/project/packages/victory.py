"""Victory dance — forward creep, spin, flashing LEDs after mission complete."""

from __future__ import annotations

import time

from tasks.project.packages.led_control import show_victory_leds
from tasks.project.packages.nav_constants import (
    Phase,
    VICTORY_FORWARD_SPEED,
    VICTORY_SPIN_SPEED,
)
from tasks.project.packages.navigation_config import DEFAULT_NAV_CONFIG


class VictoryMixin:
    """Celebration sequence at the goal intersection."""

    _nav_cfg: dict
    _phase: Phase
    _victory_start: float
    last_pwm: tuple

    def _victory_forward_s(self) -> float:
        return float(self._nav_cfg.get(
            'victory_forward_s', DEFAULT_NAV_CONFIG['victory_forward_s'],
        ))

    def _victory_spin_s(self) -> float:
        return float(self._nav_cfg.get(
            'victory_spin_s', DEFAULT_NAV_CONFIG['victory_spin_s'],
        ))

    def _begin_victory(self) -> None:
        fwd = self._victory_forward_s()
        spin = self._victory_spin_s()
        if fwd <= 0.0 and spin <= 0.0:
            self._phase = Phase.DONE
            return
        self._victory_start = time.monotonic()
        self._phase = Phase.VICTORY
        print(f"[Nav] Victory dance — forward {fwd:.1f}s, spin {spin:.1f}s")

    def _tick_victory(self, now: float, wheels, leds) -> None:
        elapsed = now - self._victory_start
        fwd = self._victory_forward_s()
        spin = self._victory_spin_s()

        if elapsed < fwd:
            wheels.set_wheels_speed(VICTORY_FORWARD_SPEED, VICTORY_FORWARD_SPEED)
            self.last_pwm = (VICTORY_FORWARD_SPEED, VICTORY_FORWARD_SPEED)
        elif elapsed < fwd + spin:
            wheels.set_wheels_speed(-VICTORY_SPIN_SPEED, VICTORY_SPIN_SPEED)
            self.last_pwm = (-VICTORY_SPIN_SPEED, VICTORY_SPIN_SPEED)
        else:
            wheels.set_wheels_speed(0.0, 0.0)
            self.last_pwm = (0.0, 0.0)
            self._phase = Phase.DONE
            print("[Nav] Victory dance complete")
            return

        show_victory_leds(leds, now)
