# from typing import List, Tuple

# from .integration_activity import ALLOWED_CLASSES, MIN_SCORE, MIN_WIDTH, MIN_HEIGHT

# Detection = Tuple[Tuple[int, int, int, int], float, int]

# class_names = {0: 'duckie', 1: 'truck', 2: 'sign'}

# from typing import List, Tuple

# Y_STOP_RATIO = 0.45  # how low object must be in image
# AREA_RATIO_THRESHOLD = 0.01  # fraction of image area
# CENTER_TOLERANCE = 0.35  # object must be near image center


# def should_stop(detections: List[Detection], img_size: int) -> Tuple[bool, str]:
#     """
#     Stop only if a relevant object is:
#     - confident
#     - in lower part of image (close)
#     - sufficiently large
#     - roughly in center (not roadside clutter)
#     """

#     img_area = img_size * img_size
#     center_x = img_size / 2

#     for bbox, score, pred_class in detections:
#         if score < MIN_SCORE:
#             continue

#         xmin, ymin, xmax, ymax = bbox

#         width = xmax - xmin
#         height = ymax - ymin
#         area = width * height

#         # 1. vertical proximity (object close)
#         if ymax < img_size * Y_STOP_RATIO:
#             print(f"ymax={ymax} is above stop threshold {img_size * Y_STOP_RATIO}")
#             continue

#         # 2. size filter (avoid distant / tiny detections)
#         if area < AREA_RATIO_THRESHOLD * img_area:
#             print(f"area={area} is below stop threshold {AREA_RATIO_THRESHOLD * img_area}")
#             continue

#         # 3. horizontal alignment (reject side objects)
#         box_center_x = (xmin + xmax) / 2
#         normalized_offset = abs(box_center_x - center_x) / img_size

#         if normalized_offset > CENTER_TOLERANCE:
#             print(f"box center offset {normalized_offset:.2f} exceeds tolerance {CENTER_TOLERANCE}")
#             continue

#         return True, (
#             f"stop: {class_names[pred_class]} "
#             f"score={score:.2f}, area={area}, y2={ymax}"
#         )

#     return False, ""

from typing import List, Tuple

Detection = Tuple[Tuple[int, int, int, int], float, int]

class_names = {0: 'duckie', 1: 'truck', 2: 'sign'}


def should_stop(detections: List[Detection], img_size: int) -> Tuple[bool, str]:
    """Return (True, reason) to stop the bot, (False, '') to keep moving."""
    stop_y = img_size * 0.55
    for (x1, y1, x2, y2), score, cls_id in detections:
        if y2 > stop_y:
            return True, class_names.get(cls_id, str(cls_id)) + ' detected close ahead'
    return False, ''