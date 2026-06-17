from typing import List, Tuple

from .integration_activity import ALLOWED_CLASSES, MIN_SCORE, MIN_WIDTH, MIN_HEIGHT

Detection = Tuple[Tuple[int, int, int, int], float, int]

class_names = {0: 'duckie', 1: 'truck', 2: 'sign'}

from typing import List, Tuple

Y_STOP_RATIO = 0.45  # how low object must be in image
AREA_RATIO_THRESHOLD = 0.01  # fraction of image area
CENTER_TOLERANCE = 0.35  # object must be near image center


def should_stop(detections: List[Detection], img_size: int) -> Tuple[bool, str]:
    """Return (True, reason) to stop the bot, (False, '') to keep moving."""
    stop_y = img_size * 0.55
    for (x1, y1, x2, y2), score, cls_id in detections:
        if y2 > stop_y:
            return True, class_names.get(cls_id, str(cls_id)) + ' detected close ahead'
    return False, ''