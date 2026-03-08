from typing import Tuple

# Path to the trained model weights (.onnx file).
# Relative paths resolve from the project root.
MODEL_PATH = "tasks/object_detection/models/best.onnx"

ALLOWED_CLASSES = {0,1,2}

MIN_SCORE = 0.5

MIN_WIDTH = 60
MIN_HEIGHT = 60


def NUMBER_FRAMES_SKIPPED() -> int:
    # Higher = run inference less often (cheaper).
    return 3


def filter_by_classes(pred_class: int) -> bool:
    """Return False to drop this prediction."""
    return pred_class in ALLOWED_CLASSES


def filter_by_scores(score: float) -> bool:
    """Confidence in [0.0, 1.0]. Return False to drop low-confidence boxes."""
    return score >= MIN_SCORE


def filter_by_bboxes(bbox: Tuple[int, int, int, int]) -> bool:
    """bbox is (xmin, ymin, xmax, ymax) in pixels. Return False to drop."""
    xmin, ymin, xmax, ymax = bbox
    width = xmax - xmin
    height = ymax - ymin
    area = width * height
    return area > (MIN_WIDTH * MIN_HEIGHT)