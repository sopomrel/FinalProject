import colorsys
from typing import List


def set_turning_leds(direction: str) -> dict:
    direction = str(direction).lower()

    # 1. DEFAULT: Initialize all 5 LEDs to White
    leds = {i: [1.0, 1.0, 1.0] for i in range(5)}

    # 2. LEFT: Set left-side LEDs (0 and 1) to yellow/orange
    if direction == "left":
        leds[0] = [1.0, 0.5, 0.0]
        leds[1] = [1.0, 0.5, 0.0]

    # 3. RIGHT: Set right-side LEDs (3 and 4) to yellow/orange
    elif direction == "right":
        leds[3] = [1.0, 0.5, 0.0]
        leds[4] = [1.0, 0.5, 0.0]

    # 4. BACKWARDS: Set all LEDs to Red
    # We check for "down" (what the dashboard sends) and "backwards" just in case
    elif direction in ["down", "backward", "backwards"]:
        leds = {i: [1.0, 0.0, 0.0] for i in range(5)}

    # If the direction is "none" or "up", it skips the if-statements
    # and simply returns the default white LEDs we set at the very beginning.

    return leds