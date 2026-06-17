from typing import Tuple
import os
import numpy as np
import cv2
import yaml

_HSV_FILE = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config', 'lane_servoing_hsv_config.yaml')
try:
    with open(_HSV_FILE) as _f:
        _h = yaml.safe_load(_f) or {}
except FileNotFoundError:
    _h = {}

_yellow_lower = np.array([_h.get('yellow_lower_h', 0),  _h.get('yellow_lower_s', 0),  _h.get('yellow_lower_v', 0)])
_yellow_upper = np.array([_h.get('yellow_upper_h', 0),  _h.get('yellow_upper_s', 0), _h.get('yellow_upper_v', 0)])

_white_lower = np.array([_h.get('white_lower_h', 0),   _h.get('white_lower_s', 0), _h.get('white_lower_v', 0)])
_white_upper = np.array([_h.get('white_upper_h', 0), _h.get('white_upper_s', 0), _h.get('white_upper_v', 0)])


def detect_lane_markings(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detects yellow and white lane markings using HSV filtering.
    """
    # 1. Convert the BGR image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 2. Create binary masks using the globally defined upper and lower bounds
    # cv2.inRange returns an array of 0s and 255s
    mask_yellow_255 = cv2.inRange(hsv_image, _yellow_lower, _yellow_upper)
    mask_white_255 = cv2.inRange(hsv_image, _white_lower, _white_upper)

    # 3. Normalize the masks to 0 and 1 so agent.py can safely multiply by 255 later
    mask_left = (mask_yellow_255 > 0).astype(np.float32)
    mask_right = (mask_white_255 > 0).astype(np.float32)

    return mask_left, mask_right

def set_hsv_bounds(yellow_lower, yellow_upper, white_lower, white_upper):
    global _yellow_lower, _yellow_upper, _white_lower, _white_upper
    _yellow_lower    = np.array(yellow_lower)
    _yellow_upper    = np.array(yellow_upper)
    _white_lower = np.array(white_lower)
    _white_upper = np.array(white_upper)

def get_hsv_bounds():
    return {
        'yellow_lower_h': int(_yellow_lower[0]),    'yellow_upper_h': int(_yellow_upper[0]),
        'yellow_lower_s': int(_yellow_lower[1]),    'yellow_upper_s': int(_yellow_upper[1]),
        'yellow_lower_v': int(_yellow_lower[2]),    'yellow_upper_v': int(_yellow_upper[2]),
        'white_lower_h':  int(_white_lower[0]), 'white_upper_h':  int(_white_upper[0]),
        'white_lower_s':  int(_white_lower[1]), 'white_upper_s':  int(_white_upper[1]),
        'white_lower_v':  int(_white_lower[2]), 'white_upper_v':  int(_white_upper[2]),
    }