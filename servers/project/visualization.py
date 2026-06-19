"""Dashboard frame renderer for the project navigation agent.

Layout mirrors create_lane_visualization() in visual_lane_servoing:

  ┌──────────────────┬──────────────────┐
  │  Camera + ROI    │  Red mask        │
  │  (debug_frame)   │  (COLORMAP_HOT)  │
  ├──────────────────┴──────────────────┤
  │  Status strip                       │
  └─────────────────────────────────────┘
"""

import cv2
import numpy as np


def create_project_visualization(
    image: np.ndarray,
    debug_info: dict,
    stop_line_debug: np.ndarray,
    red_mask_u8: np.ndarray,
) -> np.ndarray:
    """Compose the dashboard panel sent to the browser.

    Parameters
    ----------
    image           : original BGR camera frame
    debug_info      : dict from ProjectAgent.get_debug_info()
    stop_line_debug : output of IntersectionDetector.debug_frame(image)
    red_mask_u8     : IntersectionDetector.last_mask_red  (0/255 uint8)
    """
    display_w = 320
    h, w = image.shape[:2]
    display_h = int(h * display_w / w)

    # Panel 1 — camera with ROI box + mask overlay (already drawn by debug_frame)
    cam = cv2.resize(stop_line_debug, (display_w, display_h))

    # Panel 2 — red mask heat-map  (mirrors lane_vis / white_vis in lane servoing)
    if red_mask_u8.shape[0] > 1:
        red_vis = cv2.resize(
            cv2.applyColorMap(red_mask_u8, cv2.COLORMAP_HOT),
            (display_w, display_h),
        )
    else:
        red_vis = np.zeros((display_h, display_w, 3), dtype=np.uint8)

    font  = cv2.FONT_HERSHEY_SIMPLEX
    green = (0, 255, 0)
    cv2.putText(cam,     "Camera + ROI", (6, 18), font, 0.45, green, 1)
    cv2.putText(red_vis, "Red Mask",     (6, 18), font, 0.45, green, 1)

    top_row = np.hstack([cam, red_vis])
    strip   = _status_strip(display_w * 2, debug_info)

    return np.vstack([top_row, strip])


def _status_strip(width: int, debug_info: dict) -> np.ndarray:
    h      = 110
    canvas = np.zeros((h, width, 3), dtype=np.uint8)
    font   = cv2.FONT_HERSHEY_SIMPLEX

    state     = debug_info.get("state",           "?")
    edge      = debug_info.get("edge_name",       "?")
    goal      = debug_info.get("route_goal",      "?")
    turn      = debug_info.get("next_turn",       "—")
    red_i     = debug_info.get("red_line_index",  1)
    red_n     = debug_info.get("red_line_total",  0)
    next_stop = debug_info.get("next_stop",       "—")
    red_ratio = debug_info.get("red_ratio",       0.0)
    at_stop   = debug_info.get("at_stopline",     False)
    pwm_l     = debug_info.get("pwm_left",        0.0)
    pwm_r     = debug_info.get("pwm_right",       0.0)
    dets      = debug_info.get("detections",     0)

    stop_col = (0, 0, 255) if at_stop else (100, 100, 100)

    lines = [
        (f"State: {state}   Goal: {goal}   Red line {red_i}/{red_n} @ {next_stop}",
         (200, 200, 200)),
        (f"Next: {turn}   Segment: {edge}   Detections: {dets}", (200, 200, 200)),
        (f"Red px ratio: {red_ratio:.4f}  {'◉ STOP LINE' if at_stop else '○'}",
         stop_col),
    ]
    if debug_info.get("blind_straight"):
        lines.append(("STRAIGHT THROUGH (ignoring lane marks)", (0, 200, 255)))
    lines.append((f"PWM  L:{pwm_l:.2f}  R:{pwm_r:.2f}",                     (160, 220, 160)))

    for i, (text, colour) in enumerate(lines):
        cv2.putText(canvas, text, (10, 22 + i * 22), font, 0.42, colour, 1)

    return canvas
