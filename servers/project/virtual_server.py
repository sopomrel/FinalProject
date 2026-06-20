"""Virtual server for the project navigation task.

Exposes the same Flask endpoints as the lane-servoing server, plus:
  GET  /get_hsv          — read current red HSV bounds
  POST /update_hsv       — set one or more HSV fields live
  POST /update_roi       — set roi_y_start or min_red_ratio live
  GET  /get_lane_hsv     — read yellow/white lane HSV bounds
  POST /update_lane_hsv  — set lane HSV (saves lane_servoing_hsv_config.yaml)
  POST /update_lane_config — set p_gain / d_gain / base_speed
  POST /set_view         — switch video between nav and lane mask views
  GET  /status           — nav state machine info for the dashboard
"""

import sys
import os
import threading
import time
from typing import Optional

script_dir   = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')
sys.path.insert(0, project_root)

from flask import Flask, Response, render_template_string, request, jsonify
import cv2
import socket
import yaml

from tasks.project.packages.agent import ProjectAgent, load_navigation_config, save_navigation_config
from tasks.project.packages.road_graph import Cardinal, Intersection
from tasks.project.packages import intersection_detector as det_mod
from servers.project.visualization import create_project_visualization
from servers.visual_lane_servoing.visualization import create_lane_visualization
from servers.object_detection.visualization import draw_detections
from servers.templates.project import PROJECT_TEMPLATE as HTML_TEMPLATE

from duckiebot.wheel_driver.godot_wheels_driver import GodotWheelsDriver
from duckiebot.wheel_driver.wheels_driver_abs import WheelPWMConfiguration
from duckiebot.camera_driver.godot_camera_driver import GodotCameraDriver, GodotCameraConfig
from duckiebot.led_driver import VirtualLEDsDriver
from launcher.ports import find_available_port
from servers.common import make_frame_generator, shutdown_cleanup, suppress_http_logs

NAV_HSV_CONFIG_FILE  = os.path.join(project_root, 'config', 'navigation_hsv_config.yaml')
NAV_CONFIG_FILE      = os.path.join(project_root, 'config', 'navigation_config.yaml')
LANE_CONFIG_FILE     = os.path.join(project_root, 'config', 'lane_servoing_config.yaml')
LANE_HSV_CONFIG_FILE = os.path.join(project_root, 'config', 'lane_servoing_hsv_config.yaml')

app     = Flask(__name__)
camera  = None
wheels  = None
leds    = None
agent: ProjectAgent = None
running     = False
manual_mode = False
view_mode   = 'nav'   # 'nav' | 'lane'
stop_event  = threading.Event()

keys_pressed      = {'up': False, 'down': False, 'left': False, 'right': False}
_keys_lock        = threading.Lock()
_keys_last_update = time.time()


def _lane_hsv_module():
    from tasks.visual_lane_servoing.packages import visual_servoing_activity
    return visual_servoing_activity


# ── Manual control loop ───────────────────────────────────────────────────────

def manual_control_loop():
    global _keys_last_update
    while not stop_event.is_set():
        if not manual_mode or not wheels:
            time.sleep(0.05)
            continue

        # Zero keys if browser tab went silent for >0.5 s
        if time.time() - _keys_last_update > 0.5:
            with _keys_lock:
                for k in keys_pressed:
                    keys_pressed[k] = False

        with _keys_lock:
            kc = keys_pressed.copy()

        left = right = 0.0
        if kc['up']:
            left, right = 0.5, 0.5
        if kc['down']:
            left, right = -0.5, -0.5
        if kc['up'] and kc['left']:
            left, right = 0.2, 0.5
        elif kc['up'] and kc['right']:
            left, right = 0.5, 0.2
        elif kc['left']:
            left, right = -0.3, 0.3
        elif kc['right']:
            left, right = 0.3, -0.3

        wheels.set_wheels_speed(left, right)
        time.sleep(0.05)


# ── Visualisation callback ────────────────────────────────────────────────────

def visualize(frame_rgb):
    """Called once per camera frame from the frame-generator thread."""
    global running
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    if agent is None or wheels is None:
        return frame_bgr

    if view_mode == 'lane':
        lane = agent._lane
        if not manual_mode and running:
            agent.tick(frame_bgr, wheels, leds, stop_event)
            pwm_left, pwm_right = agent.last_pwm
        else:
            pwm_left, pwm_right = lane.compute_commands(frame_rgb)
            if not manual_mode:
                wheels.set_wheels_speed(0.0, 0.0)
        debug = lane.last_debug_info
        return create_lane_visualization(frame_bgr, debug, pwm_left, pwm_right)

    if not manual_mode and running:
        agent.tick(frame_bgr, wheels, leds, stop_event)
    elif agent._detector is not None and agent._detector.model_loaded:
        result = agent._detector.detect(frame_rgb)
        if result is not None:
            agent._last_detections = result

    debug_info  = agent.get_debug_info()
    stop_vis    = agent._stop_line.debug_frame(frame_bgr)
    mask_u8     = agent._stop_line.last_mask_red

    if agent._detector is not None and agent._detector.model_loaded and agent._last_detections:
        draw_detections(stop_vis, agent._last_detections)

    return create_project_visualization(frame_bgr, debug_info, stop_vis, mask_u8)


generate_frames = make_frame_generator(lambda: camera, visualize, quality=50)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, hostname=socket.gethostname())


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/status')
def status():
    if agent is None:
        return jsonify({'running': running})
    info = agent.get_debug_info()
    return jsonify({
        'running':          running,
        'manual_mode':      manual_mode,
        'state':            info.get('state', '?'),
        'edge':             info.get('edge_name', '?'),
        'turn':             info.get('next_turn', '—'),
        'red_ratio':        info.get('red_ratio', 0.0),
        'at_stop':          info.get('at_stopline', False),
        'route_start':      info.get('route_start', '?'),
        'route_goal':       info.get('route_goal',  '?'),
        'approach_heading': info.get('approach_heading'),
        'num_red_lines':    info.get('num_red_lines', 0),
        'red_line_index':   info.get('red_line_index', 1),
        'red_line_total':   info.get('red_line_total', 0),
        'next_stop':        info.get('next_stop', '—'),
        'stops':            info.get('stops', []),
        'route_summary':    info.get('route_summary', ''),
        'start':            info.get('route_start'),
        'goal':             info.get('route_goal'),
        'view_mode':        view_mode,
        'lane_config': {
            'p_gain':     agent._lane.p_gain,
            'd_gain':     agent._lane.d_gain,
            'base_speed': agent._lane.base_speed,
        },
        'nav_config': agent._nav_cfg,
        'stopped_by_detection': info.get('stopped_by_detection', False),
        'stop_reason':          info.get('stop_reason', ''),
        'model_loaded':         info.get('model_loaded', False),
        'load_error':           info.get('load_error'),
        'trt_building':         info.get('trt_building', False),
        'conf_threshold':       info.get('conf_threshold', 0.5),
        'detections':           info.get('detection_list', []),
    })


@app.route('/get_nav_config')
def get_nav_config():
    if agent is not None:
        return jsonify(agent._nav_cfg)
    return jsonify(load_navigation_config())


@app.route('/update_nav_config', methods=['POST'])
def update_nav_config():
    global agent
    data = request.json or {}
    merged = load_navigation_config()
    if 'stop_wait_s' in data:
        merged['stop_wait_s'] = float(data['stop_wait_s'])
    for key in ('victory_forward_s', 'victory_spin_s'):
        if key in data:
            merged[key] = float(data[key])
    for section in ('cross_forward_s', 'forward_bias_s'):
        if section in data and isinstance(data[section], dict):
            merged[section].update(
                {k: float(v) for k, v in data[section].items()}
            )
    merged = save_navigation_config(merged)
    if agent is not None:
        agent.apply_navigation_config(merged)
    return jsonify({'status': 'ok', 'nav_config': merged})


@app.route('/get_hsv')
def get_hsv():
    return jsonify(det_mod.get_hsv_bounds())


@app.route('/update_hsv', methods=['POST'])
def update_hsv():
    data   = request.json or {}
    merged = {}
    try:
        with open(NAV_HSV_CONFIG_FILE) as f:
            merged = yaml.safe_load(f) or {}
    except FileNotFoundError:
        pass
    merged.update(det_mod.get_hsv_bounds())
    merged.update({k: int(v) for k, v in data.items()})

    det_mod.set_hsv_bounds(
        r1_lower=[merged['red_lower_h_1'], merged['red_lower_s_1'], merged['red_lower_v_1']],
        r1_upper=[merged['red_upper_h_1'], merged['red_upper_s_1'], merged['red_upper_v_1']],
        r2_lower=[merged['red_lower_h_2'], merged['red_lower_s_2'], merged['red_lower_v_2']],
        r2_upper=[merged['red_upper_h_2'], merged['red_upper_s_2'], merged['red_upper_v_2']],
    )
    try:
        with open(NAV_HSV_CONFIG_FILE, 'w') as f:
            yaml.dump(merged, f, default_flow_style=False)
    except Exception as e:
        print(f"[Project] Could not save HSV config: {e}")
    return jsonify({'status': 'ok'})


@app.route('/update_roi', methods=['POST'])
def update_roi():
    data = request.json or {}
    cur  = det_mod.get_hsv_bounds()
    y    = float(data.get('roi_y_start',   cur['roi_y_start']))
    x    = float(data.get('roi_x_margin',  cur['roi_x_margin']))
    r    = float(data.get('min_red_ratio', cur['min_red_ratio']))
    det_mod.set_roi_params(y, x, r)
    try:
        with open(NAV_HSV_CONFIG_FILE) as f:
            cfg = yaml.safe_load(f) or {}
        cfg.update({'roi_y_start': y, 'roi_x_margin': x, 'min_red_ratio': r})
        with open(NAV_HSV_CONFIG_FILE, 'w') as f:
            yaml.dump(cfg, f, default_flow_style=False)
    except Exception as e:
        print(f"[Project] Could not save ROI config: {e}")
    return jsonify({'status': 'ok'})


@app.route('/set_view', methods=['POST'])
def set_view():
    global view_mode
    view = (request.json or {}).get('view', 'nav')
    if view not in ('nav', 'lane'):
        return jsonify({'status': 'error', 'message': 'view must be nav or lane'}), 400
    view_mode = view
    print(f"[Project] View → {view_mode}")
    return jsonify({'view': view_mode})


@app.route('/get_lane_hsv')
def get_lane_hsv():
    return jsonify(_lane_hsv_module().get_hsv_bounds())


@app.route('/update_lane_hsv', methods=['POST'])
def update_lane_hsv():
    data = request.json or {}
    mod  = _lane_hsv_module()
    merged = {}
    try:
        with open(LANE_HSV_CONFIG_FILE) as f:
            merged = yaml.safe_load(f) or {}
    except FileNotFoundError:
        pass
    merged.update(mod.get_hsv_bounds())
    merged.update({k: int(v) for k, v in data.items()})
    mod.set_hsv_bounds(
        [merged['yellow_lower_h'], merged['yellow_lower_s'], merged['yellow_lower_v']],
        [merged['yellow_upper_h'], merged['yellow_upper_s'], merged['yellow_upper_v']],
        [merged['white_lower_h'],  merged['white_lower_s'],  merged['white_lower_v']],
        [merged['white_upper_h'],  merged['white_upper_s'],  merged['white_upper_v']],
    )
    try:
        with open(LANE_HSV_CONFIG_FILE, 'w') as f:
            yaml.dump(merged, f, default_flow_style=False)
    except Exception as e:
        print(f"[Project] Could not save lane HSV config: {e}")
    return jsonify({'status': 'ok'})


@app.route('/update_lane_config', methods=['POST'])
def update_lane_config():
    data = request.json or {}
    if agent is None:
        return jsonify({'status': 'error'}), 400
    lane = agent._lane
    lane.p_gain     = float(data.get('k_d',   lane.p_gain))
    lane.d_gain     = float(data.get('k_phi', lane.d_gain))
    lane.base_speed = float(data.get('const', lane.base_speed))
    try:
        with open(LANE_CONFIG_FILE) as f:
            saved = yaml.safe_load(f) or {}
        saved['p_gain']     = lane.p_gain
        saved['d_gain']     = lane.d_gain
        saved['base_speed'] = lane.base_speed
        with open(LANE_CONFIG_FILE, 'w') as f:
            yaml.dump(saved, f, default_flow_style=False)
    except Exception as e:
        print(f"[Project] Could not save lane config: {e}")
    return jsonify({'status': 'ok'})


@app.route('/set_mode', methods=['POST'])
def set_mode():
    global manual_mode, running
    mode = (request.json or {}).get('mode', 'auto')
    manual_mode = (mode == 'manual')
    if manual_mode:
        running = False          # pause auto-nav while driving manually
    if wheels and not manual_mode:
        wheels.set_wheels_speed(0.0, 0.0)
    print(f"[Project] Mode → {'manual' if manual_mode else 'auto'}")
    return jsonify({'mode': 'manual' if manual_mode else 'auto'})


@app.route('/keys', methods=['POST'])
def update_keys():
    global _keys_last_update
    data = request.json or {}
    with _keys_lock:
        for k in keys_pressed:
            keys_pressed[k] = bool(data.get(k, False))
    _keys_last_update = time.time()
    return jsonify({'status': 'ok'})


@app.route('/start', methods=['POST'])
def start():
    global running
    running = True
    print("[Project] Started")
    return jsonify({'status': 'running'})


@app.route('/stop', methods=['POST'])
def stop():
    global running
    running = False
    if wheels:
        wheels.set_wheels_speed(0.0, 0.0)
    if leds:
        try:
            leds.all_off()
        except Exception:
            pass
    print("[Project] Stopped")
    return jsonify({'status': 'stopped'})


@app.route('/running')
def get_running():
    return jsonify({'running': running})


@app.route('/reset', methods=['POST'])
def reset():
    global running
    running = False
    if wheels:
        wheels.reset_game()
    if agent:
        agent.reset_route()
    return jsonify({'status': 'ok'})


@app.route('/reset_route', methods=['POST'])
def reset_route():
    """Reset route progress only — does not move the robot in the game."""
    global running
    running = False
    if wheels:
        wheels.set_wheels_speed(0.0, 0.0)
    if agent:
        agent.reset_route()
    return jsonify({'status': 'ok'})


@app.route('/remove_objects', methods=['POST'])
def remove_objects():
    data = request.json or {}
    name_filter = data.get('filter', '')
    bbox = data.get('bbox')

    if bbox is None and agent:
        bbox = agent.obstacle_removal_bbox()

    if wheels and bbox is not None:
        wheels.remove_objects(bbox=bbox)
    elif wheels and name_filter:
        wheels.remove_objects(name_filter=name_filter)

    if agent:
        agent.clear_obstacle()
    return jsonify({'status': 'ok', 'filter': name_filter, 'bbox': bbox})


@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    value = request.json.get('value') if request.json else None
    if agent and agent._detector and value is not None:
        agent._detector.conf_threshold = float(value)
    conf = agent._detector.conf_threshold if agent and agent._detector else None
    return jsonify({'conf_threshold': conf})


def _parse_approach(raw) -> Optional[Cardinal]:
    """Parse approach heading from API/CLI value, or None for route-aligned start."""
    if raw is None or raw == '' or str(raw).lower() in ('auto', 'none', '-'):
        return None
    val = str(raw).upper()
    if val in ('N', 'NORTH'):
        return Cardinal.NORTH
    if val in ('S', 'SOUTH'):
        return Cardinal.SOUTH
    if val in ('E', 'EAST'):
        return Cardinal.EAST
    if val in ('W', 'WEST'):
        return Cardinal.WEST
    return Cardinal(val)


@app.route('/set_route', methods=['POST'])
def set_route():
    global agent, running
    data = request.json or {}
    try:
        start_val = data.get('start', 'A').upper()
        goal_val  = data.get('goal',  'C').upper()
        if start_val == goal_val:
            return jsonify({'status': 'error', 'message': 'Start and goal must differ'}), 400
        start_node = Intersection(start_val)
        goal_node  = Intersection(goal_val)
        approach = _parse_approach(data.get('approach'))
    except (ValueError, KeyError) as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400

    running = False
    if wheels:
        wheels.set_wheels_speed(0.0, 0.0)

    agent = ProjectAgent(
        start=start_node,
        goal=goal_node,
        approach_heading=approach,
        enable_object_detection=(agent._detector is not None) if agent else True,
    )
    info = agent.get_debug_info()
    stops = info.get('stops', [])
    first_turn = stops[0]['turn'] if stops else 'straight'
    approach_label = info.get('approach_heading') or 'auto'
    print(f"[Project] Route {start_node.value}→{goal_node.value} "
          f"({info.get('num_red_lines')} red lines, approach {approach_label})")
    return jsonify({
        'status':           'ok',
        'start':            start_node.value,
        'goal':             goal_node.value,
        'approach_heading': info.get('approach_heading'),
        'num_red_lines':    info.get('num_red_lines', 0),
        'stops':            stops,
        'start_turn':       first_turn,
        'route_summary':    info.get('route_summary', ''),
    })


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    global camera, wheels, leds, agent

    import argparse
    ap = argparse.ArgumentParser(description="Virtual Project Navigation Server")
    ap.add_argument("--port",        type=int,    default=5000)
    ap.add_argument("--frame-port",  type=int,    default=5001)
    ap.add_argument("--wheel-port",  type=int,    default=5002)
    ap.add_argument("--godot-host",  type=str,    default="localhost")
    ap.add_argument("--start",       type=str,    default="A",
                    help="Start intersection (A/B/C)")
    ap.add_argument("--goal",        type=str,    default="C",
                    help="Goal intersection (A/B/C)")
    ap.add_argument("--approach",    type=str,    default=None,
                    help="Heading when crossing start line (N/S/E/W, or auto)")
    ap.add_argument("--no-detection", action="store_true",
                    help="Disable YOLO object detection")
    args = ap.parse_args()

    suppress_http_logs()
    print("=" * 60)
    print("VIRTUAL PROJECT NAVIGATION SERVER")
    print("=" * 60)

    start_node = Intersection(args.start.upper())
    goal_node  = Intersection(args.goal.upper())
    approach   = _parse_approach(args.approach)

    print(f"\n[Route] {start_node.value} → {goal_node.value}"
          + (f"  (approach {approach.value})" if approach else ""))

    print("\n[1/4] Initializing wheels driver...")
    wheels = GodotWheelsDriver(
        WheelPWMConfiguration(pwm_min=0), WheelPWMConfiguration(pwm_min=0),
        godot_host=args.godot_host,
        godot_port=args.wheel_port,
    )
    wheels.trim = 0

    print("\n[2/4] Initializing camera driver...")
    camera = GodotCameraDriver(
        godot_config=GodotCameraConfig(host="0.0.0.0", port=args.frame_port)
    )
    camera.start()
    print("  Camera: connected!")

    print("\n[3/4] Initializing virtual LED driver...")
    leds = VirtualLEDsDriver(debug=False)
    print("  LEDs: ok (virtual)")

    print("\n[4/4] Creating navigation agent...")
    agent = ProjectAgent(
        start=start_node,
        goal=goal_node,
        approach_heading=approach,
        enable_object_detection=not args.no_detection,
    )

    threading.Thread(target=manual_control_loop, daemon=True).start()

    web_port = find_available_port(args.port)
    if web_port != args.port:
        print(f"  Port {args.port} busy, using {web_port}")

    print("\n" + "=" * 60)
    print(f"Web Interface: http://localhost:{web_port}")
    print(f"  Start: {start_node.value}   Goal: {goal_node.value}")
    print("=" * 60 + "\n")

    try:
        app.run(host='127.0.0.1', port=web_port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if leds:
            try:
                leds.all_off()
                leds.release()
            except Exception:
                pass
        shutdown_cleanup(wheels, camera, stop_event)


if __name__ == "__main__":
    sys.exit(main())
