import time

import cv2

from tasks.project.packages.navigation_fsm import NavigationFSM
from tasks.project.packages.navigation_types import NavState, TurnDir
from tasks.visual_lane_servoing.packages.agent import LaneServoingAgent

_LOOP_DT = 0.05
_STUB_TURN_SEC = 1.0
_STUB_TURN_SPEED = 0.35


def _stub_turn(wheels, turn: TurnDir, stop_event, duration: float = _STUB_TURN_SEC) -> None:
    """Placeholder turn until turning.py (Phase 2)."""
    if turn == TurnDir.LEFT:
        wheels.set_wheels_speed(-_STUB_TURN_SPEED, _STUB_TURN_SPEED)
    elif turn == TurnDir.RIGHT:
        wheels.set_wheels_speed(_STUB_TURN_SPEED, -_STUB_TURN_SPEED)
    else:
        return

    deadline = time.time() + duration
    while time.time() < deadline and not stop_event.is_set():
        stop_event.wait(_LOOP_DT)


def _set_led_nav(leds, state: NavState) -> None:
    if not leds:
        return
    if state == NavState.FOLLOW_LANE:
        leds.set_rgb(0, [0.0, 1.0, 0.0])
        leds.set_rgb(2, [0.0, 1.0, 0.0])
    elif state in (NavState.STOP_AT_LINE, NavState.OBSTACLE_STOP):
        leds.set_rgb(0, [1.0, 0.5, 0.0])
        leds.set_rgb(2, [1.0, 0.5, 0.0])
    elif state == NavState.TURN:
        leds.set_rgb(0, [1.0, 1.0, 0.0])
        leds.set_rgb(2, [1.0, 1.0, 0.0])
    elif state == NavState.GOAL_REACHED:
        leds.all_on()


def main(camera, wheels, leds, stop_event):
    lane = LaneServoingAgent()
    fsm = NavigationFSM()
    fsm.start()

    turn_handled = False

    try:
        while not stop_event.is_set():
            ok, frame_bgr = camera.read()
            if not ok:
                stop_event.wait(_LOOP_DT)
                continue

            state = fsm.update(frame_bgr, obstacle_stop=False)
            _set_led_nav(leds, state)

            if state == NavState.FOLLOW_LANE:
                turn_handled = False
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                left, right = lane.compute_commands(frame_rgb)
                wheels.set_wheels_speed(left, right)

            elif state == NavState.TURN:
                wheels.set_wheels_speed(0.0, 0.0)
                if not turn_handled:
                    _stub_turn(wheels, fsm.next_turn, stop_event)
                    fsm.mark_turn_done()
                    turn_handled = True

            elif state in (NavState.STOP_AT_LINE, NavState.OBSTACLE_STOP):
                wheels.set_wheels_speed(0.0, 0.0)

            elif state == NavState.GOAL_REACHED:
                wheels.set_wheels_speed(0.0, 0.0)
                break

            stop_event.wait(_LOOP_DT)

    finally:
        wheels.set_wheels_speed(0.0, 0.0)
        if leds:
            leds.all_off()
