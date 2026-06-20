from typing import List, Optional, Tuple

from .integration_activity import ALLOWED_CLASSES, MIN_SCORE, MIN_WIDTH, MIN_HEIGHT

Detection = Tuple[Tuple[int, int, int, int], float, int]

class_names = {0: 'duckie', 1: 'truck', 2: 'sign'}

Y_STOP_RATIO = 0.45  # how low object must be in image
AREA_RATIO_THRESHOLD = 0.01  # fraction of image area
CENTER_TOLERANCE = 0.35  # object must be near image center


def _stop_y(img_size: int) -> float:
    return img_size * 0.55


def stopping_detection(
    detections: List[Detection], img_size: int,
) -> Optional[Detection]:
    """Return the detection that triggered a stop, or None."""
    stop_y = _stop_y(img_size)
    best: Optional[Detection] = None
    best_y2 = -1.0
    for det in detections:
        (_, _, _, y2), _, _ = det
        if y2 > stop_y and y2 > best_y2:
            best = det
            best_y2 = y2
    return best


def should_stop(detections: List[Detection], img_size: int) -> Tuple[bool, str]:
    """Return (True, reason) to stop the bot, (False, '') to keep moving."""
    det = stopping_detection(detections, img_size)
    if det is None:
        return False, ''
    _, _, cls_id = det
    return True, class_names.get(cls_id, str(cls_id)) + ' detected close ahead'