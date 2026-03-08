# from typing import Dict, List


# def set_turning_leds(direction: str) -> Dict[int, List[float]]:
#     """Return LED colors indicating turning direction.

#     Duckiebot has 4 RGB LEDs with indices:
#       - 0: front-left
#       - 2: front-right
#       - 3: back-left
#       - 4: back-right
#     """
#     yellow = [1.0, 1.0, 0.0]
#     off = [0.0, 0.0, 0.0]

#     state: Dict[int, List[float]] = {
#         0: off[:],
#         2: off[:],
#         3: off[:],
#         4: off[:],
#     }

#     d = (direction or "").strip().lower()
#     if d == "left":
#         state[0] = yellow[:]
#         state[4] = yellow[:]
#     elif d == "right":
#         state[2] = yellow[:]
#         state[3] = yellow[:]
#     # Unknown/straight directions: leave all LEDs off.

#     return state
import colorsys
from typing import List, Dict


def _all_off() -> Dict[int, List[float]]:
   
    return {0: [0.0, 0.0, 0.0],
            2: [0.0, 0.0, 0.0],
            3: [0.0, 0.0, 0.0],
            4: [0.0, 0.0, 0.0]}


def set_turning_leds(direction: str) -> Dict[int, List[float]]:
   
    direction = direction.lower().strip()

    leds = _all_off()
    yellow = [1.0, 1.0, 0.0]
    red = [1.0, 0.0, 0.0]
    white = [1.0, 1.0, 1.0]

    if direction == "left":
        leds[0] = yellow  
        leds[4] = yellow  
    elif direction == "right":
        leds[2] = yellow  
        leds[3] = yellow  
    elif direction == "forward":
        leds[0] = white
        leds[2] = white
    elif direction == "stop":
        leds[3] = red
        leds[4] = red  
    else:
        leds = _all_off()
    

    return leds