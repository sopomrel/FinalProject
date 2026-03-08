from typing import Tuple
import os
import yaml
import numpy as np

# Configuration Loading
CONFIG_PATH = os.path.join("config", "modcon_config.yaml")

# Default values if YAML is missing or keys are absent
K_P = 1.0
K_I = 0.0
K_D = 0.1
MAX_OMEGA = 1.0

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
        K_P = config.get('k_P', K_P)
        K_I = config.get('k_I', K_I)
        K_D = config.get('k_D', K_D)
        MAX_OMEGA = config.get('max_omega', MAX_OMEGA)

def PIDController(
    v_0: float,
    theta_ref: float,
    theta_hat: float,
    prev_e: float,
    prev_int: float,
    delta_t: float,
) -> Tuple[float, float, float, float]:
    
    # 1. Calculate Heading Error (Always use shortest angular distance)
    # This prevents the "random" direction choice by always picking the < 180 deg path.
    e = np.arctan2(np.sin(theta_ref - theta_hat), np.cos(theta_ref - theta_hat))

    # If the error is less than 0.5 degrees, stop the motors to prevent jiggling
    if abs(e) < np.radians(0.5):
        return (float(v_0), 0.0, 0.0, float(prev_int))
    # 2. Derivative term (de/dt)
    de = 0.0
    # Safety: Only calculate if delta_t is valid and we have a previous error
    if delta_t > 0.0001 and not np.isnan(prev_e):
        de = (e - prev_e) / delta_t

    # 3. Integral term with Anti-Windup
    e_int_candidate = prev_int + e * delta_t
    
    # 4. Calculate Control Output (omega)
    # Note: K_P, K_I, K_D are loaded from your YAML config globally
    omega_raw = (K_P * e) + (K_I * e_int_candidate) + (K_D * de)
    
    # Clipping to prevent the motor from over-saturating the simulator
    omega = np.clip(omega_raw, -MAX_OMEGA, MAX_OMEGA)
    
    # Anti-windup: Only update the integral if the output wasn't saturated
    if omega == omega_raw:
        e_int_new = e_int_candidate
    else:
        e_int_new = prev_int

    return (float(v_0), float(omega), float(e), float(e_int_new))