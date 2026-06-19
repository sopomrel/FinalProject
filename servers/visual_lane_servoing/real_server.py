import sys
import os
import signal
import threading
import time
import argparse
import socket

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')
sys.path.insert(0, project_root)

import cv2
import numpy as np
import yaml
from flask import Flask, Response, render_template_string, request, jsonify

from tasks.visual_lane_servoing.packages.agent import LaneServoingAgent
from servers.visual_lane_servoing.visualization import create_lane_visualization
from servers.templates.lane_servoing import LANE_SERVOING_TEMPLATE as HTML_TEMPLATE

from duckiebot.camera_driver import CameraDriver
from duckiebot.wheel_driver import DaguWheelsDriver
from duckiebot.wheel_driver.wheels_driver_abs import WheelPWMConfiguration
from launcher.ports import find_available_port
from servers.common import make_frame_generator, shutdown_cleanup, suppress_http_logs

LANE_CONFIG_FILE = os.path.join(project_root, 'config', 'lane_servoing_config.yaml')
LANE_HSV_CONFIG_FILE = os.path.join(project_root, 'config', 'lane_servoing_hsv_config.yaml')


def _get_student_module():
    from tasks.visual_lane_servoing.packages import visual_servoing_activity
    return visual_servoing_activity


app = Flask(__name__)
camera = None
wheels = None
agent = None
running = False
stop_event = threading.Event()


def _start_camera(max_attempts: int = 3, pause_s: float = 3.0):
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        cam = CameraDriver()
        try:
            cam.start()
            return cam
        except RuntimeError as exc:
            last_exc = exc
            try:
                cam.stop()
            except Exception:
                pass
            if attempt < max_attempts:
                print(
                    f"  Camera attempt {attempt}/{max_attempts} failed ({exc}); "
                    f"retrying in {pause_s:.0f}s..."
                )
                time.sleep(pause_s)
    raise last_exc


def visualize(frame_bgr):
    """Camera frame is BGR; agent expects RGB."""
    global running
    if agent is None or wheels is None or frame_bgr is None:
        if frame_bgr is not None:
            return frame_bgr
        return np.zeros((480, 640, 3), dtype=np.uint8)

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pwm_left, pwm_right = agent.compute_commands(frame_rgb)
    if running:
        wheels.set_wheels_speed(pwm_left, pwm_right)
    else:
        wheels.set_wheels_speed(0.0, 0.0)

    return create_lane_visualization(frame_bgr, agent.last_debug_info, pwm_left, pwm_right)


generate_frames = make_frame_generator(lambda: camera, visualize, quality=50, rgb=False)


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, config=agent, hostname=socket.gethostname())


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/reset', methods=['POST'])
def reset():
    if agent is not None:
        agent._prev_error = 0.0
        agent._filtered_error = 0.0
    if wheels is not None:
        wheels.set_wheels_speed(0.0, 0.0)
    return jsonify({'status': 'ok'})


@app.route('/update_config', methods=['POST'])
def update_config():
    data = request.json or {}
    agent.p_gain = float(data.get('k_d', agent.p_gain))
    agent.d_gain = float(data.get('k_phi', agent.d_gain))
    agent.base_speed = float(data.get('const', agent.base_speed))
    try:
        with open(LANE_CONFIG_FILE, 'r') as f:
            saved = yaml.safe_load(f) or {}
        saved['p_gain'] = agent.p_gain
        saved['d_gain'] = agent.d_gain
        saved['base_speed'] = agent.base_speed
        with open(LANE_CONFIG_FILE, 'w') as f:
            yaml.dump(saved, f, default_flow_style=False)
    except Exception as e:
        print(f"[LaneServoing] Could not save config: {e}")
    return jsonify({'status': 'ok'})


@app.route('/get_hsv')
def get_hsv():
    return jsonify(_get_student_module().get_hsv_bounds())


@app.route('/update_hsv', methods=['POST'])
def update_hsv():
    data = request.json or {}
    mod = _get_student_module()
    merged = {}
    try:
        with open(LANE_HSV_CONFIG_FILE, 'r') as f:
            merged = yaml.safe_load(f) or {}
    except FileNotFoundError:
        pass
    merged.update(mod.get_hsv_bounds())
    merged.update({k: int(v) for k, v in data.items()})
    mod.set_hsv_bounds(
        [merged['yellow_lower_h'], merged['yellow_lower_s'], merged['yellow_lower_v']],
        [merged['yellow_upper_h'], merged['yellow_upper_s'], merged['yellow_upper_v']],
        [merged['white_lower_h'], merged['white_lower_s'], merged['white_lower_v']],
        [merged['white_upper_h'], merged['white_upper_s'], merged['white_upper_v']],
    )
    try:
        with open(LANE_HSV_CONFIG_FILE, 'w') as f:
            yaml.dump(merged, f, default_flow_style=False)
    except Exception as e:
        print(f"[LaneServoing] Could not save HSV config: {e}")
    return jsonify({'status': 'ok'})


@app.route('/start', methods=['POST'])
def start():
    global running
    running = True
    print('[Control] Started')
    return jsonify({'status': 'running'})


@app.route('/stop', methods=['POST'])
def stop():
    global running
    running = False
    if wheels:
        wheels.set_wheels_speed(0.0, 0.0)
    print('[Control] Stopped')
    return jsonify({'status': 'stopped'})


@app.route('/running')
def get_running():
    return jsonify({'running': running})


@app.route('/status')
def status():
    if agent is None:
        return jsonify({'status': 'not_initialized'})
    return jsonify({
        'status': 'active',
        'running': running,
        'frame_count': agent.frame_count,
        'config': {
            'p_gain': agent.p_gain,
            'd_gain': agent.d_gain,
            'base_speed': agent.base_speed,
            'detection_threshold': agent.detection_threshold,
        },
    })


@app.route('/shutdown')
def shutdown_route():
    shutdown_cleanup(wheels, camera, stop_event)
    return jsonify({'status': 'ok'})


def main():
    global camera, wheels, agent, stop_event

    ap = argparse.ArgumentParser(description='Lane Servoing Server — Real Hardware')
    ap.add_argument('--port', type=int, default=5000)
    args = ap.parse_args()

    stop_event.clear()

    suppress_http_logs()
    print('=' * 60)
    print('LANE SERVOING SERVER — REAL HARDWARE')
    print('=' * 60)

    print('\n[1/3] Initializing wheels driver...')
    wheels = DaguWheelsDriver(WheelPWMConfiguration(), WheelPWMConfiguration())
    print('  Wheels: ok')

    time.sleep(1.0)

    print('\n[2/3] Initializing camera driver...')
    camera = _start_camera()
    print('  Camera: ok')

    print('\n[3/3] Creating lane agent...')
    agent = LaneServoingAgent()
    print(f'  p_gain={agent.p_gain}, d_gain={agent.d_gain}, base_speed={agent.base_speed}')

    def _shutdown(signum, frame):
        print('\nShutting down...')
        shutdown_cleanup(wheels, camera, stop_event)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    web_port = find_available_port(args.port)
    print('\n' + '=' * 60)
    print(f'Web Interface: http://{socket.gethostname()}.local:{web_port}')
    print('Open the root URL (not /video) for HSV sliders and mask view.')
    print('=' * 60 + '\n')

    try:
        app.run(host='0.0.0.0', port=web_port, debug=False, threaded=True)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        shutdown_cleanup(wheels, camera, stop_event)


if __name__ == '__main__':
    sys.exit(main())
