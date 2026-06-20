"""Navigation timing config — load/save ``config/navigation_config.yaml``."""

import os
from typing import Optional

import yaml

from tasks.project.packages.road_graph import Turn

NAV_CONFIG_FILE = os.path.normpath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'config', 'navigation_config.yaml'
))

DEFAULT_NAV_CONFIG = {
    'stop_wait_s': 5.0,
    'cross_forward_s': {
        'straight': 2.8,
        'left':     3.4,
        'right':    2.6,
        'goal':     0.5,
    },
    'forward_bias_s': {
        'straight': 0.0,
        'left':     0.55,
        'right':    0.20,
    },
    'victory_forward_s': 1.5,
    'victory_spin_s':    3.0,
}


def turn_key(turn: Optional[Turn]) -> str:
    if turn is None:
        return 'goal'
    return turn.value


def load_navigation_config(path: Optional[str] = None) -> dict:
    """Load intersection timing from YAML (see config/navigation_config.yaml)."""
    cfg = {
        'stop_wait_s': DEFAULT_NAV_CONFIG['stop_wait_s'],
        'cross_forward_s': dict(DEFAULT_NAV_CONFIG['cross_forward_s']),
        'forward_bias_s': dict(DEFAULT_NAV_CONFIG['forward_bias_s']),
        'victory_forward_s': DEFAULT_NAV_CONFIG['victory_forward_s'],
        'victory_spin_s': DEFAULT_NAV_CONFIG['victory_spin_s'],
    }
    file_path = path or NAV_CONFIG_FILE
    try:
        with open(file_path) as f:
            loaded = yaml.safe_load(f) or {}
        if 'stop_wait_s' in loaded:
            cfg['stop_wait_s'] = float(loaded['stop_wait_s'])
        for key in ('victory_forward_s', 'victory_spin_s'):
            if key in loaded:
                cfg[key] = float(loaded[key])
        for section in ('cross_forward_s', 'forward_bias_s'):
            if section in loaded and isinstance(loaded[section], dict):
                cfg[section].update(
                    {k: float(v) for k, v in loaded[section].items()}
                )
    except FileNotFoundError:
        pass
    return cfg


def save_navigation_config(cfg: dict, path: Optional[str] = None) -> dict:
    """Persist navigation timing to YAML and return the normalised config."""
    merged = load_navigation_config(path)
    if 'stop_wait_s' in cfg:
        merged['stop_wait_s'] = float(cfg['stop_wait_s'])
    for key in ('victory_forward_s', 'victory_spin_s'):
        if key in cfg:
            merged[key] = float(cfg[key])
    for section in ('cross_forward_s', 'forward_bias_s'):
        if section in cfg and isinstance(cfg[section], dict):
            merged[section].update(
                {k: float(v) for k, v in cfg[section].items()}
            )
    file_path = path or NAV_CONFIG_FILE
    with open(file_path, 'w') as f:
        yaml.dump(merged, f, default_flow_style=False, sort_keys=False)
    return merged
