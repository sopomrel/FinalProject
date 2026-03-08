from typing import Dict, Tuple
import logging
logger = logging.getLogger(__name__)

SPEED = 1
TURN = 0.5


def get_motor_speeds(keys_pressed: Dict[str, bool]) -> Tuple[float, float]:
    """Convert key state to (left_speed, right_speed).

    Expected mapping from the notebook:
      - up:        (+0.5, +0.5)
      - down:      (-0.5, -0.5)
      - left:      (-0.3, +0.3)
      - right:     (+0.3, -0.3)
    """
    up = bool(keys_pressed.get("up", False))
    down = bool(keys_pressed.get("down", False))
    left = bool(keys_pressed.get("left", False))
    right = bool(keys_pressed.get("right", False))

    # Forward/back: both wheels same sign.
    # Notebook uses +0.5/-0.5, which is 0.5 * SPEED when SPEED=1.
    forward_dir = (1.0 if up else 0.0) - (1.0 if down else 0.0)
    forward_speed = forward_dir * (0.5 * SPEED)

    # Turn: wheels get opposite offsets.
    # For curves while moving, match the notebook's +/-0.3 behavior.
    # For turn-only spins (no up/down), reduce the magnitude so it doesn't look
    # overly fast in the simulation.
    turn_amount = (1.0 if right else 0.0) - (1.0 if left else 0.0)  # right => +, left => -
    turn_scale = 3.0 / 5.0  # makes TURN=0.5 => 0.3
    turn_offset = turn_scale * TURN  # base offset for curves: 0.3 when TURN=0.5
    spin_offset = (2.0 / 3.0) * turn_offset  # reduce turn-only spin speed to ~0.2

    effective_offset = spin_offset if forward_speed == 0.0 else turn_offset
    turn_speed = turn_amount * effective_offset
   
    left_speed = forward_speed + turn_speed
    right_speed = forward_speed - turn_speed

    # Safety clamp to Duckiebot speed API range.
    left_speed = max(-1.0, min(1.0, left_speed))
    right_speed = max(-1.0, min(1.0, right_speed))
    return left_speed, right_speed
