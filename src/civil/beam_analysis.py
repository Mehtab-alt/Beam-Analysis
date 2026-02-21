import numpy as np
import pandas as pd
import logging

from ..utils.exceptions import AnalysisError

logger = logging.getLogger(__name__)

def _calculate_reactions_simply_supported(length, supports, loads):
    """Calculates reactions for a simply supported beam."""
    pinned_pos = next((s['position'] for s in supports if s['type'] == 'pinned'), 0)
    roller_pos = next((s['position'] for s in supports if s['type'] == 'roller'), length)
    
    total_force = 0
    total_moment_about_pin = 0
    
    for load in loads:
        if load['type'] == 'point':
            mag, pos = load['magnitude'], load['position']
            total_force += mag
            total_moment_about_pin += mag * (pos - pinned_pos)
        
        elif load['type'] == 'distributed':
            mag, start, end = load['magnitude'], load['start'], load['end']
            load_length = end - start
            resultant_force = mag * load_length
            resultant_position = start + load_length / 2
            total_force += resultant_force
            total_moment_about_pin += resultant_force * (resultant_position - pinned_pos)

    effective_length = roller_pos - pinned_pos
    if effective_length == 0:
        raise AnalysisError("Pinned and roller supports cannot be at the same position.")
        
    R_roller = -total_moment_about_pin / effective_length
    R_pin = -total_force - R_roller
    
    logger.info(f"Simply Supported: R_pin = {R_pin:.2f} N, R_roller = {R_roller:.2f} N")
    return {pinned_pos: R_pin, roller_pos: R_roller}, 0

def _calculate_reactions_cantilever(supports, loads):
    """Calculates reactions for a cantilever beam (one fixed support)."""
    fixed_pos = supports[0]['position']
    
    total_force = 0
    total_moment_about_fixed = 0
    
    for load in loads:
        if load['type'] == 'point':
            mag, pos = load['magnitude'], load['position']
            total_force += mag
            total_moment_about_fixed += mag * (pos - fixed_pos)
        
        elif load['type'] == 'distributed':
            mag, start, end = load['magnitude'], load['start'], load['end']
            load_length = end - start
            resultant_force = mag * load_length
            resultant_position = start + load_length / 2
            total_force += resultant_force
            total_moment_about_fixed += resultant_force * (resultant_position - fixed_pos)
            
    R_fixed_force = -total_force
    M_fixed_reaction = -total_moment_about_fixed
    
    logger.info(f"Cantilever: R_force = {R_fixed_force:.2f} N, M_reaction = {M_fixed_reaction:.2f} Nm")
    return {fixed_pos: R_fixed_force}, M_fixed_reaction


def solve_beam(properties, supports, loads):
    """
    Analyzes a beam for shear, moment, and deflection.
    Supports simply-supported and cantilever beams.
    """
    # --- Retrieve and Validate Beam Properties ---
    try:
        length = float(properties.get('length', 10.0))
        E = float(properties.get('E', 200e9))
        I = float(properties.get('I', 8.3e-5))
    except (ValueError, TypeError) as e:
        raise AnalysisError(f"Invalid beam property. Please ensure 'length', 'E', and 'I' are valid numbers. Error: {e}")

    num_points = int(length * 200) + 1
    x = np.linspace(0, length, num_points)
    dx = length / (num_points - 1)

    # --- 1. Identify support type and calculate reactions ---
    support_types = sorted([s['type'] for s in supports])
    is_cantilever = support_types == ['fixed'] and len(supports) == 1
    is_ss = support_types == ['pinned', 'roller']

    if is_ss:
        reactions, initial_moment = _calculate_reactions_simply_supported(length, supports, loads)
    elif is_cantilever:
        reactions, initial_moment = _calculate_reactions_cantilever(supports, loads)
    else:
        # Provide a more user-friendly error for common invalid setups
        if 'pinned' not in support_types and 'fixed' not in support_types:
            raise AnalysisError(
                "Invalid support configuration: The structure is unstable. "
                "A beam requires at least one 'pinned' or 'fixed' support to prevent horizontal movement."
            )
        
        # Generic error for other unsupported but potentially stable (statically indeterminate) cases
        raise AnalysisError(
            f"Unsupported support combination: {support_types}. The current solver only supports "
            "a single 'fixed' support (cantilever) or one 'pinned' and one 'roller' support (simply supported)."
        )

    # --- 2. Calculate Shear and Moment ---
    V = np.zeros(num_points)
    M = np.full(num_points, initial_moment, dtype=float) 
    
    for pos, mag in reactions.items():
        V += np.where(x >= pos, mag, 0)
    for load in loads:
        if load['type'] == 'point':
            V += np.where(x >= load['position'], load['magnitude'], 0)
        elif load['type'] == 'distributed':
            start, end, mag = load['start'], load['end'], load['magnitude']
            mask = (x >= start) & (x < end)
            V += np.where(mask, mag * (x - start), 0)
            V += np.where(x >= end, mag * (end - start), 0)
    
    M += np.cumsum(V) * dx

    # --- 3. Calculate Slope and Deflection by Double Integration ---
    if E is None or I is None:
        raise AnalysisError("Beam properties 'E' and 'I' must be defined for deflection analysis.")
    
    M_over_EI = M / (E * I)
    
    slope = np.cumsum(M_over_EI) * dx
    deflection = np.cumsum(slope) * dx

    # --- 4. Apply Boundary Conditions ---
    if is_cantilever:
        fixed_pos = supports[0]['position']
        if fixed_pos != 0:
            logger.warning("Deflection calculation for cantilever assumes fixed support is at position 0.")
    elif is_ss:
        pinned_pos = next(s['position'] for s in supports if s['type'] == 'pinned')
        roller_pos = next(s['position'] for s in supports if s['type'] == 'roller')
        
        idx_pin = np.argmin(np.abs(x - pinned_pos))
        idx_roller = np.argmin(np.abs(x - roller_pos))
        
        y_pin_raw = deflection[idx_pin]
        y_roller_raw = deflection[idx_roller]
        
        # Avoid division by zero if supports are at the same point
        if x[idx_roller] - x[idx_pin] == 0:
            raise AnalysisError("Cannot calculate deflection; supports are at the same position.")
            
        line_slope = (y_roller_raw - y_pin_raw) / (x[idx_roller] - x[idx_pin])
        correction_line = line_slope * (x - x[idx_pin]) + y_pin_raw
        deflection -= correction_line

    # --- 5. Assemble results into a DataFrame ---
    results_df = pd.DataFrame({
        'Position_m': x,
        'Shear_Force_N': V,
        'Bending_Moment_Nm': M,
        'Slope_rad': slope,
        'Deflection_m': deflection,
    })

    return results_df