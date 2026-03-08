from typing import Tuple
import numpy as np


def get_motor_left_matrix(shape: Tuple[int, int]) -> np.ndarray:
    """Left motor weight matrix: highest at bottom-left, decreasing toward top-right."""
    h, w = shape
    if h <= 0 or w <= 0:
        raise ValueError(f"Invalid shape {shape}; expected positive (height, width).")

    # Coordinate system:
    # - y: 0 at top, 1 at bottom
    # - x: 0 at left, 1 at right
    y = np.linspace(0.0, 1.0, h, dtype=np.float32).reshape(h, 1)
    x = np.linspace(0.0, 1.0, w, dtype=np.float32).reshape(1, w)

    # y - x gives:
    #   bottom-left (y=1, x=0) -> +1
    #   top-right    (y=0, x=1) -> -1
    #   linear gradient along the top-right/bottom-left diagonal.
    return (y - x).astype(np.float32, copy=False)


def get_motor_right_matrix(shape: Tuple[int, int]) -> np.ndarray:
    """Right motor weight matrix: highest at bottom-right, decreasing toward top-left."""
    h, w = shape
    if h <= 0 or w <= 0:
        raise ValueError(f"Invalid shape {shape}; expected positive (height, width).")

    y = np.linspace(0.0, 1.0, h, dtype=np.float32).reshape(h, 1)
    x = np.linspace(0.0, 1.0, w, dtype=np.float32).reshape(1, w)

    # y + x - 1 gives:
    #   bottom-right (y=1, x=1) -> +1
    #   top-left      (y=0, x=0) -> -1
    #   linear gradient along the top-left/bottom-right diagonal.
    return (y + x - 1.0).astype(np.float32, copy=False)
