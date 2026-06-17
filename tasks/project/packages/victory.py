import time
from typing import List, Optional

from tasks.project.packages.navigation_types import TurnDir
from tasks.project.packages.turning import TurnController

# Full 360° victory spin + LED flash. Re-tune on the physical bot if needed.
SPIN_SPEED = 0.35
SPIN_DURATION_FULL = 4.0  # four 90° quarters ≈ one full rotation
FLASH_HZ = 2.0
_LOOP_DT = 0.05

LED_INDICES = (0, 2, 3, 4)
_FLASH_COLORS: List[List[float]] = [
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [1.0, 1.0, 0.0],
]


class VictoryCelebration:
    """Goal celebration: spin in place while flashing corner LEDs."""

    def __init__(
        self,
        spin_speed: float = SPIN_SPEED,
        spin_duration: float = SPIN_DURATION_FULL,
        flash_hz: float = FLASH_HZ,
        loop_dt: float = _LOOP_DT,
        turner: Optional[TurnController] = None,
    ):
        self.spin_duration = float(spin_duration)
        self.flash_hz = float(flash_hz)
        self.loop_dt = float(loop_dt)
        self.turner = turner or TurnController(
            speed=spin_speed,
            duration_90=spin_duration / 4.0,
            loop_dt=loop_dt,
        )

    def _flash_leds(self, leds, phase_on: bool) -> None:
        if not leds:
            return
        if phase_on:
            for i, idx in enumerate(LED_INDICES):
                leds.set_rgb(idx, _FLASH_COLORS[i % len(_FLASH_COLORS)])
        else:
            leds.all_off()

    def execute(self, wheels, leds=None, stop_event=None) -> bool:
        """Spin ~360° with flashing LEDs. Returns False if interrupted."""
        left, right = self.turner.wheel_speeds(TurnDir.LEFT)
        wheels.set_wheels_speed(left, right)

        deadline = time.time() + self.spin_duration
        flash_period = 1.0 / max(self.flash_hz, 0.1)
        next_flash = time.time()
        lights_on = True

        while time.time() < deadline:
            if stop_event is not None:
                if stop_event.wait(self.loop_dt):
                    wheels.set_wheels_speed(0.0, 0.0)
                    if leds:
                        leds.all_off()
                    return False
            else:
                time.sleep(self.loop_dt)

            now = time.time()
            if now >= next_flash:
                self._flash_leds(leds, lights_on)
                lights_on = not lights_on
                next_flash = now + flash_period / 2.0

        wheels.set_wheels_speed(0.0, 0.0)
        if leds:
            leds.all_on()
        return True


def celebrate(wheels, leds=None, stop_event=None, celebration: Optional[VictoryCelebration] = None) -> bool:
    """Convenience wrapper for a default victory celebration."""
    return (celebration or VictoryCelebration()).execute(wheels, leds, stop_event)
