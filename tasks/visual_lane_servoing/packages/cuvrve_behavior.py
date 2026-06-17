from typing import List, Tuple
import numpy as np


def detect_curve(
        yellow_xs: List[int],
        white_xs: List[int],
        curve_threshold: int = 25  # Pixels of horizontal shift to trigger curve mode
) -> Tuple[bool, int]:
    shifts = []

    # Check horizontal shift in yellow line
    if len(yellow_xs) >= 2:
        shifts.append(yellow_xs[-1] - yellow_xs[0])

    # Check horizontal shift in white line
    if len(white_xs) >= 2:
        shifts.append(white_xs[-1] - white_xs[0])

    if shifts:
        avg_shift = sum(shifts) / len(shifts)
        # If the shift is greater than our threshold, we are in a curve
        if abs(avg_shift) > curve_threshold:
            # Positive shift means curving right, negative means left
            direction = 1 if avg_shift > 0 else -1
            return True, direction

    return False, 0