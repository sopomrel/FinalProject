import json
from typing import List

# Classes the model is trained to detect.
# The index here is the class ID written into YOLO label files.
CLASSES = ['duckie', 'truck', 'sign']

# Images are resized to this square size before training.
IMAGE_SIZE = 416


def convert_labelme_json(json_path: str, img_w: int, img_h: int) -> List[str]:
    labels = []

    with open(json_path, "r") as f:
        data = json.load(f)

    for shape in data["shapes"]:
        label = shape["label"]

        # Skip unknown classes
        if label not in CLASSES:
            continue

        cls_id = CLASSES.index(label)

        # Extract rectangle corner points
        (x1, y1), (x2, y2) = shape["points"]

        xmin = min(x1, x2)
        xmax = max(x1, x2)
        ymin = min(y1, y2)
        ymax = max(y1, y2)

        # Scale to IMAGE_SIZE space
        xmin = xmin * IMAGE_SIZE / img_w
        xmax = xmax * IMAGE_SIZE / img_w
        ymin = ymin * IMAGE_SIZE / img_h
        ymax = ymax * IMAGE_SIZE / img_h

        # Convert to normalized YOLO format
        cx = (xmin + xmax) / 2 / IMAGE_SIZE
        cy = (ymin + ymax) / 2 / IMAGE_SIZE
        w = (xmax - xmin) / IMAGE_SIZE
        h = (ymax - ymin) / IMAGE_SIZE

        labels.append(
            f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"
        )

    return label