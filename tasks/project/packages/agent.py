import cv2

from tasks.project.packages.navigation_fsm import NavigationFSM
from tasks.project.packages.navigation_types import NavState
from tasks.project.packages.victory import celebrate
from tasks.visual_lane_servoing.packages.agent import LaneServoingAgent

_LOOP_DT = 0.05


def _make_detector():
    """Load the object detector; fall back to lane-only if it's unavailable."""
    try:
        from tasks.object_detection.packages.agent import ObjectDetectionAgent

        return ObjectDetectionAgent()
    except Exception as exc:  # missing model / runtime — keep driving without it
        print(f"[project] object detector unavailable, lane-only: {exc}")
        return None


def _set_led_nav(leds, state: NavState) -> None:
    if not leds:
        return
    if state == NavState.FOLLOW_LANE:
        leds.set_rgb(0, [0.0, 1.0, 0.0])
        leds.set_rgb(2, [0.0, 1.0, 0.0])
    elif state == NavState.OBSTACLE_STOP:
        leds.set_rgb(0, [1.0, 0.0, 0.0])
        leds.set_rgb(2, [1.0, 0.0, 0.0])
    elif state == NavState.STOP_AT_LINE:
        leds.set_rgb(0, [1.0, 0.5, 0.0])
        leds.set_rgb(2, [1.0, 0.5, 0.0])
    elif state == NavState.TURN:
        leds.set_rgb(0, [1.0, 1.0, 0.0])
        leds.set_rgb(2, [1.0, 1.0, 0.0])
    elif state == NavState.GOAL_REACHED:
        leds.all_on()
    elif state in (NavState.VICTORY, NavState.PARKING):
        leds.set_rgb(0, [0.0, 1.0, 1.0])
        leds.set_rgb(2, [0.0, 1.0, 1.0])
        leds.set_rgb(3, [0.0, 1.0, 1.0])
        leds.set_rgb(4, [0.0, 1.0, 1.0])


def main(camera, wheels, leds, stop_event):
    lane = LaneServoingAgent()
    detector = _make_detector()
    fsm = NavigationFSM()
    fsm.start(return_to_start=True)
    celebrating = False

    try:
        while not stop_event.is_set():
            ok, frame_bgr = camera.read()
            if not ok:
                stop_event.wait(_LOOP_DT)
                continue

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            # Detector returns [] when not loaded and None on skipped frames;
            # the ObstacleHandler inside the FSM debounces both correctly.
            detections = detector.detect(frame_rgb) if detector else []
            img_h = int(frame_rgb.shape[0])
            img_w = int(frame_rgb.shape[1])

            state = fsm.update(frame_bgr, detections=detections, img_size=img_h, img_w=img_w)
            _set_led_nav(leds, state)

            if state == NavState.FOLLOW_LANE:
                left, right = lane.compute_commands(frame_rgb)
                wheels.set_wheels_speed(left, right)

            elif state == NavState.TURN:
                wheels.set_wheels_speed(0.0, 0.0)
                fsm.perform_turn(wheels, stop_event)

            elif state in (NavState.STOP_AT_LINE, NavState.OBSTACLE_STOP):
                wheels.set_wheels_speed(0.0, 0.0)

            elif state == NavState.GOAL_REACHED and not celebrating:
                wheels.set_wheels_speed(0.0, 0.0)
                celebrating = True
                celebrate(wheels, leds, stop_event)
                state = fsm.resume_after_victory()
                _set_led_nav(leds, state)
                celebrating = False

            elif state in (NavState.VICTORY, NavState.PARKING):
                wheels.set_wheels_speed(0.0, 0.0)
                break

            stop_event.wait(_LOOP_DT)

    finally:
        wheels.set_wheels_speed(0.0, 0.0)
        if leds:
            leds.all_off()
