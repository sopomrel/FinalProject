from typing import List, Tuple
import numpy as np


def detect_curve(
    yellow_xs: List[int],
    white_xs: List[int],
    curve_threshold: int = 350,
) -> Tuple[bool, int]:
    # # Slices are built from top-of-ROI to bottom-of-ROI; xs[-1] is the row nearer
    # # the robot, xs[0] is farther along the lane. Large |near - far| => curve.
    # shifts: List[int] = []
    # if len(yellow_xs) >= 2:
    #     shifts.append(int(yellow_xs[-1] - yellow_xs[0]))
    # if len(white_xs) >= 2:
    #     shifts.append(int(white_xs[-1] - white_xs[0]))
    # if not shifts:
    #     return False, 0

    # shift = int(round(sum(shifts) / len(shifts)))
    # if abs(shift) <= curve_threshold:
    #     return False, 0
    return False, 0
