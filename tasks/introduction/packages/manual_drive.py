from typing import Dict, Tuple
import logging
logger = logging.getLogger(__name__)

SPEED = 1
TURN = 0.5


def get_motor_speeds(keys_pressed: Dict[str, bool]) -> Tuple[float, float]:
    left_speed = 0.0
    right_speed = 0.0

    # The dashboard sends 'up', 'down', 'left', 'right'
    if keys_pressed.get("up", False):
        left_speed += SPEED
        right_speed += SPEED

    if keys_pressed.get("down", False):
        left_speed -= SPEED
        right_speed -= SPEED

    if keys_pressed.get("left", False):
        left_speed -= TURN
        right_speed += TURN

    if keys_pressed.get("right", False):
        left_speed += TURN
        right_speed -= TURN

    # Clamp values to simulator limits
    left_speed = max(-1.0, min(1.0, left_speed))
    right_speed = max(-1.0, min(1.0, right_speed))

    return float(left_speed), float(right_speed)