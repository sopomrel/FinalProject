from typing import Tuple
import numpy as np

def delta_phi(ticks: int, prev_ticks: int, resolution: int) -> Tuple[float, float]:
    if resolution <= 0:
        raise ValueError("resolution must be positive")
    
    # Calculate difference in ticks
    delta_ticks = ticks - prev_ticks
    
    # Radians per tick: alpha = 2π / resolution
    alpha = (2 * np.pi) / resolution
    
    # Calculate wheel rotation in radians
    rotation = delta_ticks * alpha
    
    return (float(rotation), float(ticks))

def pose_estimation(
    R: float,
    baseline: float,
    x_prev: float,
    y_prev: float,
    theta_prev: float,
    delta_phi_left: float,
    delta_phi_right: float,
) -> Tuple[float, float, float]:
    if baseline <= 0:
        raise ValueError("baseline must be positive")

    # Arc lengths traveled by each wheel
    d_l = R * delta_phi_left
    d_r = R * delta_phi_right
    
    # Distance traveled by the center of the robot
    d_A = (d_l + d_r) / 2.0
    
    # Change in heading
    # IMPORTANT: If the robot still vibrates at K_P=0.1, 
    # try swapping this to: (d_l - d_r) / baseline
    d_theta = (d_r - d_l) / baseline
    
    # Update position using the MIDPOINT heading (more stable than Euler)
    theta_mid = theta_prev + (d_theta / 2.0)
    x = x_prev + d_A * np.cos(theta_mid)
    y = y_prev + d_A * np.sin(theta_mid)
    
    # Update heading
    theta = theta_prev + d_theta

    # Force theta to stay between -pi and pi
    theta = np.arctan2(np.sin(theta), np.cos(theta))

    return (float(x), float(y), float(theta))