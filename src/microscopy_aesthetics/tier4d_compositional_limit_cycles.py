"""
Tier 4D: Multi-Domain Compositional Limit Cycle Discovery
==========================================================

Discovers limit cycles that emerge when multiple aesthetic domains interact.

Key Insight:
    Individual domains have Phase 2.6 rhythmic presets.
    When domains compose, NEW rhythmic patterns can emerge:
    - Novel periods (neither domain has it)
    - Phase-locked oscillations (2:1, 3:2 frequency ratios)
    - Beat frequencies (LCM of individual periods)
    - Quasi-periodic attractors (incommensurate frequencies)

Algorithm:
    1. Load Phase 2.6 presets from each domain MCP
    2. Create compositional attractor field (combines domain flows)
    3. Sample parameter space and integrate trajectories
    4. Detect periodicity in composed trajectories
    5. Compare to individual domain periods → identify emergent cycles

Pure Layer 2 operation - 0 tokens (deterministic sampling + signal processing)

Add these functions to composition_graph_server.py
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from scipy import signal
from sklearn.cluster import DBSCAN
import json


# ============================================================================
# Phase 2.6 Preset Loading Interface
# ============================================================================

def load_domain_phase26_presets(domain_id: str) -> Optional[Dict[str, Any]]:
    """
    Load Phase 2.6 rhythmic presets from a domain MCP.
    
    This is a placeholder - in production, this would call the actual MCP.
    For now, we define expected structure.
    
    Args:
        domain_id: Domain to load presets from
    
    Returns:
        Dict with preset configurations, or None if unavailable
    
    Expected structure:
    {
        "preset_name_1": {
            "state_a_coords": {"param1": 0.5, "param2": 0.7, ...},
            "state_b_coords": {"param1": 0.8, "param2": 0.3, ...},
            "pattern": "sinusoidal",
            "num_cycles": 3,
            "steps_per_cycle": 24,
            "parameter_names": ["param1", "param2", ...]
        },
        "preset_name_2": {...}
    }
    """
    # In production: call domain MCP's list_rhythmic_presets tool
    # For now, return None to indicate "not implemented"
    return None


def generate_preset_trajectory_from_config(preset_config: Dict) -> np.ndarray:
    """
    Generate trajectory from Phase 2.6 preset configuration.
    
    Args:
        preset_config: Preset configuration dict
    
    Returns:
        Trajectory array of shape (total_steps, n_params)
    """
    state_a = preset_config["state_a_coords"]
    state_b = preset_config["state_b_coords"]
    param_names = preset_config["parameter_names"]
    pattern = preset_config["pattern"]
    num_cycles = preset_config["num_cycles"]
    steps_per_cycle = preset_config["steps_per_cycle"]
    
    total_steps = num_cycles * steps_per_cycle
    
    # Generate oscillation
    t = np.linspace(0, 2 * np.pi * num_cycles, total_steps)
    
    if pattern == "sinusoidal":
        alpha = 0.5 * (1 + np.sin(t))
    elif pattern == "triangular":
        t_norm = (t / (2 * np.pi)) % 1.0
        alpha = np.where(t_norm < 0.5, 2 * t_norm, 2 * (1 - t_norm))
    elif pattern == "square":
        t_norm = (t / (2 * np.pi)) % 1.0
        alpha = np.where(t_norm < 0.5, 0.0, 1.0)
    else:
        alpha = 0.5 * (1 + np.sin(t))  # Default to sinusoidal
    
    # Interpolate between states
    vec_a = np.array([state_a[p] for p in param_names])
    vec_b = np.array([state_b[p] for p in param_names])
    
    trajectory = np.outer(1 - alpha, vec_a) + np.outer(alpha, vec_b)
    
    return trajectory


# ============================================================================
# Compositional Attractor Field
# ============================================================================

class CompositionalAttractorField:
    """
    Gradient field where multiple domains' Phase 2.6 presets act as attractors.
    
    Each domain has preset trajectories that act as attractor manifolds in their
    parameter subspace. When domains compose, we combine their flows using
    interaction modes (mutual_influence, competitive, cooperative).
    
    This creates emergent dynamics - trajectories that exist only in composition.
    """
    
    def __init__(
        self,
        domain_preset_trajectories: Dict[str, Dict[str, np.ndarray]],
        domain_parameter_names: Dict[str, List[str]],
        interaction_mode: str = "mutual_influence",
        domain_weights: Optional[Dict[str, float]] = None,
        perpendicular_weight: float = 1.0,
        tangent_weight: float = 2.0
    ):
        """
        Initialize compositional attractor field.
        
        Args:
            domain_preset_trajectories: {
                "microscopy": {"focus_sweep": traj_array, ...},
                "nuclear": {"energy_pulse": traj_array, ...},
                ...
            }
            domain_parameter_names: {
                "microscopy": ["contrast", "saturation", ...],
                "nuclear": ["energy", "scale", ...],
                ...
            }
            interaction_mode: How domains influence each other
                - "mutual_influence": Weighted average (default)
                - "competitive": Winner-take-all
                - "cooperative": Maximize alignment
            domain_weights: Weight for each domain (default: equal)
            perpendicular_weight: Strength of pull toward trajectory curve
            tangent_weight: Strength of flow along trajectory curve
        """
        self.domain_trajectories = domain_preset_trajectories
        self.domain_param_names = domain_parameter_names
        self.interaction_mode = interaction_mode
        
        # Set domain weights
        if domain_weights is None:
            self.weights = {d: 1.0 for d in domain_preset_trajectories.keys()}
        else:
            self.weights = domain_weights
        
        # Attractor field parameters
        self.perpendicular_weight = perpendicular_weight
        self.tangent_weight = tangent_weight
        
        # Pre-compute tangent directions for each domain's presets
        self.domain_tangents = {}
        
        for domain_id, presets in domain_preset_trajectories.items():
            self.domain_tangents[domain_id] = {}
            
            for preset_name, trajectory in presets.items():
                tangents = np.zeros_like(trajectory)
                
                for i in range(len(trajectory)):
                    next_i = (i + 1) % len(trajectory)
                    tangent = trajectory[next_i] - trajectory[i]
                    norm = np.linalg.norm(tangent)
                    
                    if norm > 1e-10:
                        tangent = tangent / norm
                    
                    tangents[i] = tangent
                
                self.domain_tangents[domain_id][preset_name] = tangents
    
    def find_nearest_attractor_point_in_domain(
        self,
        domain_id: str,
        domain_state: np.ndarray
    ) -> Tuple[np.ndarray, str, int]:
        """
        Find nearest point on any preset trajectory in this domain.
        
        Args:
            domain_id: Which domain
            domain_state: Current state in domain's parameter space
        
        Returns:
            (nearest_point, preset_name, trajectory_index)
        """
        min_distance = float('inf')
        nearest_point = None
        nearest_preset = None
        nearest_index = None
        
        for preset_name, trajectory in self.domain_trajectories[domain_id].items():
            distances = np.linalg.norm(trajectory - domain_state, axis=1)
            min_idx = np.argmin(distances)
            min_dist = distances[min_idx]
            
            if min_dist < min_distance:
                min_distance = min_dist
                nearest_point = trajectory[min_idx]
                nearest_preset = preset_name
                nearest_index = min_idx
        
        return nearest_point, nearest_preset, nearest_index
    
    def compute_domain_gradient(
        self,
        domain_id: str,
        domain_state: np.ndarray
    ) -> np.ndarray:
        """
        Compute gradient for a single domain toward its nearest attractor.
        
        Combines perpendicular (pull toward curve) and tangent (flow along curve).
        
        Args:
            domain_id: Which domain
            domain_state: Current state in domain's parameter space
        
        Returns:
            Gradient vector in domain's parameter space
        """
        nearest_point, nearest_preset, nearest_index = \
            self.find_nearest_attractor_point_in_domain(domain_id, domain_state)
        
        # Perpendicular component
        perpendicular = nearest_point - domain_state
        perp_norm = np.linalg.norm(perpendicular)
        
        if perp_norm > 1e-10:
            perpendicular = perpendicular / perp_norm
        else:
            perpendicular = np.zeros_like(domain_state)
        
        # Tangent component
        tangent = self.domain_tangents[domain_id][nearest_preset][nearest_index]
        
        # Distance-dependent weighting (like microscopy implementation)
        distance_to_curve = perp_norm
        
        if distance_to_curve > 0.1:
            perp_weight = self.perpendicular_weight
            tang_weight = self.tangent_weight * 0.3
        elif distance_to_curve < 0.03:
            perp_weight = self.perpendicular_weight * 0.1
            tang_weight = self.tangent_weight * 3.0
        else:
            # Smooth transition
            t = (distance_to_curve - 0.03) / (0.1 - 0.03)
            perp_weight = self.perpendicular_weight * (0.1 + 0.9 * t)
            tang_weight = self.tangent_weight * (3.0 - 2.5 * t)
        
        gradient = perp_weight * perpendicular + tang_weight * tangent
        
        # Normalize
        norm = np.linalg.norm(gradient)
        if norm > 1e-10:
            gradient = gradient / norm
        
        return gradient
    
    def compute_gradient(
        self,
        composite_state: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        Compute compositional gradient.
        
        Args:
            composite_state: {
                "microscopy": np.array([contrast, saturation, ...]),
                "nuclear": np.array([energy, scale, ...]),
                ...
            }
        
        Returns:
            Dict of gradients per domain
        """
        # Compute gradient for each domain
        domain_gradients = {}
        
        for domain_id, domain_state in composite_state.items():
            if domain_id in self.domain_trajectories:
                gradient = self.compute_domain_gradient(domain_id, domain_state)
                domain_gradients[domain_id] = gradient
            else:
                # Domain has no presets - zero gradient
                domain_gradients[domain_id] = np.zeros_like(domain_state)
        
        # Apply interaction mode
        # IMPORTANT: Domains may have different dimensionalities (e.g., microscopy: 5D, nuclear: 4D)
        # so we cannot cross-assign or sum gradients between domains
        
        if self.interaction_mode == "mutual_influence":
            # Keep individual gradients (domains evolve independently but in parallel)
            # Weighted by domain weights
            for domain_id in domain_gradients:
                domain_gradients[domain_id] *= self.weights.get(domain_id, 1.0)
        
        elif self.interaction_mode == "competitive":
            # Strongest domain wins, others are suppressed
            strengths = {
                d: np.linalg.norm(grad) * self.weights.get(d, 1.0)
                for d, grad in domain_gradients.items()
            }
            
            if strengths:
                dominant = max(strengths, key=strengths.get)
                
                # Dominant domain keeps full gradient
                # Non-dominant domains get heavily suppressed (10% of their gradient)
                for domain_id in domain_gradients:
                    if domain_id != dominant:
                        # Suppress non-dominant domains (can't cross-assign different dimensions)
                        domain_gradients[domain_id] = domain_gradients[domain_id] * 0.1
        
        elif self.interaction_mode == "cooperative":
            # Domains try to align their directions (but stay in their own spaces)
            # Measure "cooperation" by checking if domains agree on direction toward/away
            
            # Compute center-relative directions for each domain
            domain_directions = {}
            for domain_id, grad in domain_gradients.items():
                # Check if moving toward (positive) or away (negative) from domain center
                # Use gradient magnitude as proxy for "toward attractor" (positive)
                grad_magnitude = np.linalg.norm(grad)
                domain_directions[domain_id] = grad_magnitude
            
            if domain_directions:
                # Measure alignment: all moving strongly = cooperative boost
                # Mixed directions = suppress all
                avg_magnitude = np.mean(list(domain_directions.values()))
                std_magnitude = np.std(list(domain_directions.values()))
                
                # High alignment (low std) = boost all gradients
                # Low alignment (high std) = suppress all gradients
                alignment_factor = 1.0 - min(std_magnitude / (avg_magnitude + 1e-6), 1.0)
                
                for domain_id in domain_gradients:
                    # Each domain keeps its direction but adjusts strength based on alignment
                    domain_gradients[domain_id] = domain_gradients[domain_id] * (0.5 + 0.5 * alignment_factor)
        
        return domain_gradients


# ============================================================================
# Trajectory Integration with Compositional Field
# ============================================================================

def integrate_compositional_trajectory(
    start_state: Dict[str, Dict[str, float]],
    attractor_field: CompositionalAttractorField,
    num_steps: int = 300,
    dt: float = 0.1,
    momentum: float = 0.3
) -> List[Dict[str, Dict[str, float]]]:
    """
    Integrate trajectory through compositional parameter space.
    
    Each domain evolves according to compositional attractor field.
    Momentum helps maintain orbital motion.
    
    Args:
        start_state: {
            "microscopy": {"contrast": 0.5, "saturation": 0.7, ...},
            "nuclear": {"energy": 0.8, ...},
            ...
        }
        attractor_field: CompositionalAttractorField instance
        num_steps: Integration steps
        dt: Time step size
        momentum: Momentum coefficient [0, 1]
    
    Returns:
        Trajectory as list of composite states
    """
    # Convert to arrays
    current_arrays = {}
    velocities = {}
    
    for domain_id, domain_state_dict in start_state.items():
        param_names = attractor_field.domain_param_names[domain_id]
        current_arrays[domain_id] = np.array([
            domain_state_dict[p] for p in param_names
        ])
        velocities[domain_id] = np.zeros_like(current_arrays[domain_id])
    
    trajectory = []
    
    for step in range(num_steps):
        # Record state
        state_dict = {}
        for domain_id, array in current_arrays.items():
            param_names = attractor_field.domain_param_names[domain_id]
            state_dict[domain_id] = {
                param_names[i]: float(array[i])
                for i in range(len(param_names))
            }
        trajectory.append(state_dict)
        
        # Compute gradients
        gradients = attractor_field.compute_gradient(current_arrays)
        
        # Update velocities and positions for each domain
        for domain_id, gradient in gradients.items():
            # Momentum update
            velocities[domain_id] = \
                momentum * velocities[domain_id] + (1 - momentum) * gradient
            
            # Cap velocity
            vel_norm = np.linalg.norm(velocities[domain_id])
            if vel_norm > 2.0:
                velocities[domain_id] = 2.0 * velocities[domain_id] / vel_norm
            
            # Update position
            current_arrays[domain_id] = current_arrays[domain_id] + dt * velocities[domain_id]
            
            # Clip to bounds [0, 1]
            current_arrays[domain_id] = np.clip(current_arrays[domain_id], 0.0, 1.0)
    
    return trajectory


# ============================================================================
# Periodicity Detection
# ============================================================================

def detect_periodicity_in_composite_trajectory(
    trajectory: List[Dict[str, Dict[str, float]]],
    domain_id: str,
    parameter_names: List[str],
    min_period: int = 5,
    max_period: int = 100
) -> Optional[Dict]:
    """
    Detect periodicity in one domain's trajectory within composite evolution.
    
    Args:
        trajectory: List of composite states
        domain_id: Which domain to analyze
        parameter_names: Parameters to analyze
        min_period: Minimum period
        max_period: Maximum period
    
    Returns:
        Periodicity info or None
    """
    # Extract domain trajectory
    domain_traj = []
    for state in trajectory:
        if domain_id in state:
            domain_state = state[domain_id]
            domain_traj.append([domain_state[p] for p in parameter_names])
    
    if len(domain_traj) < max_period:
        return None
    
    traj_array = np.array(domain_traj)
    n_steps = len(traj_array)
    
    # Compute autocorrelation for each dimension
    autocorrs = []
    
    for dim in range(len(parameter_names)):
        signal_1d = traj_array[:, dim]
        signal_1d = signal_1d - np.mean(signal_1d)
        
        autocorr = np.correlate(signal_1d, signal_1d, mode='full')
        autocorr = autocorr[n_steps - 1:]
        
        if autocorr[0] > 0:
            autocorr = autocorr / autocorr[0]
        
        autocorrs.append(autocorr)
    
    avg_autocorr = np.mean(autocorrs, axis=0)
    
    # Find peaks
    peaks, properties = signal.find_peaks(
        avg_autocorr[1:],
        height=0.5,
        distance=min_period
    )
    
    if len(peaks) == 0:
        return None
    
    period = peaks[0] + 1
    
    if period < min_period or period > max_period:
        return None
    
    peak_height = properties['peak_heights'][0]
    
    return {
        "domain": domain_id,
        "period": int(period),
        "autocorr_strength": float(peak_height),
        "is_periodic": peak_height > 0.5
    }


# ============================================================================
# Emergent Cycle Identification
# ============================================================================

def identify_emergent_cycles(
    composite_cycles: List[Dict],
    individual_domain_periods: Dict[str, List[int]]
) -> List[Dict]:
    """
    Identify which cycles are emergent (not in individual domains).
    
    Args:
        composite_cycles: Detected cycles in composed system
        individual_domain_periods: {
            "microscopy": [24, 20, 30, 16, 10],  # Phase 2.6 preset periods
            "nuclear": [15, 25, ...],
            ...
        }
    
    Returns:
        List of emergent cycles with analysis
    """
    emergent = []
    
    for cycle in composite_cycles:
        domain = cycle["domain"]
        period = cycle["period"]
        
        # Check if this period exists in individual domain
        individual_periods = individual_domain_periods.get(domain, [])
        
        # Allow ±2 tolerance for matching
        is_known = any(abs(period - known) <= 2 for known in individual_periods)
        
        if not is_known:
            # Check if it's a harmonic or beat frequency
            harmonics = []
            beats = []
            
            for known_period in individual_periods:
                # Harmonic (multiple of known period)
                if abs(period % known_period) <= 2:
                    harmonics.append(known_period)
                
                # Beat frequency (could be LCM with another domain)
                # This is more complex - skip for now
            
            emergence_type = "unknown"
            if harmonics:
                emergence_type = "harmonic"
            elif len(individual_periods) >= 2:
                # Could be beat frequency
                emergence_type = "beat_frequency"
            else:
                emergence_type = "novel"
            
            emergent.append({
                "domain": domain,
                "period": period,
                "autocorr_strength": cycle["autocorr_strength"],
                "emergence_type": emergence_type,
                "related_periods": harmonics if harmonics else None
            })
    
    return emergent


# ============================================================================
# Main Discovery Function
# ============================================================================

def discover_compositional_limit_cycles_impl(
    domain_preset_configs: Dict[str, Dict[str, Any]],
    domain_parameter_names: Dict[str, List[str]],
    interaction_mode: str = "mutual_influence",
    domain_weights: Optional[Dict[str, float]] = None,
    n_samples: int = 50,
    integration_steps: int = 300,
    min_period: int = 5,
    max_period: int = 100
) -> Dict:
    """
    Discover limit cycles in multi-domain compositional system.
    
    TIER 4D: MULTI-DOMAIN COMPOSITIONAL LIMIT CYCLES
    
    Args:
        domain_preset_configs: {
            "microscopy": {
                "focus_sweep": {preset_config},
                "illumination_cycle": {preset_config},
                ...
            },
            "nuclear": {...},
            ...
        }
        domain_parameter_names: Parameter names for each domain
        interaction_mode: How domains interact
        domain_weights: Weight for each domain
        n_samples: Number of initial conditions
        integration_steps: Steps per trajectory
        min_period: Minimum period to detect
        max_period: Maximum period to detect
    
    Returns:
        Results with emergent cycles identified
    """
    # Generate preset trajectories
    domain_trajectories = {}
    individual_periods = {}
    
    for domain_id, presets in domain_preset_configs.items():
        domain_trajectories[domain_id] = {}
        individual_periods[domain_id] = []
        
        for preset_name, config in presets.items():
            trajectory = generate_preset_trajectory_from_config(config)
            domain_trajectories[domain_id][preset_name] = trajectory
            
            # Record individual period
            period = config["num_cycles"] * config["steps_per_cycle"] // config["num_cycles"]
            individual_periods[domain_id].append(config["steps_per_cycle"])
    
    # Create compositional attractor field
    attractor_field = CompositionalAttractorField(
        domain_trajectories,
        domain_parameter_names,
        interaction_mode,
        domain_weights
    )
    
    # Sample initial conditions
    np.random.seed(42)
    
    # Build composite initial states
    initial_states = []
    
    for _ in range(n_samples):
        composite_state = {}
        
        for domain_id, param_names in domain_parameter_names.items():
            # Random initial state in [0, 1]
            state_dict = {
                p: float(np.random.rand())
                for p in param_names
            }
            composite_state[domain_id] = state_dict
        
        initial_states.append(composite_state)
    
    # Integrate trajectories
    detected_cycles = []
    
    for idx, start_state in enumerate(initial_states):
        trajectory = integrate_compositional_trajectory(
            start_state,
            attractor_field,
            num_steps=integration_steps
        )
        
        # Detect periodicity in each domain
        for domain_id in domain_parameter_names:
            periodicity = detect_periodicity_in_composite_trajectory(
                trajectory,
                domain_id,
                domain_parameter_names[domain_id],
                min_period,
                max_period
            )
            
            if periodicity and periodicity.get("is_periodic"):
                detected_cycles.append({
                    "sample_index": idx,
                    "domain": domain_id,
                    "period": periodicity["period"],
                    "autocorr_strength": periodicity["autocorr_strength"],
                    "trajectory": trajectory
                })
    
    # Identify emergent cycles
    emergent_cycles = identify_emergent_cycles(detected_cycles, individual_periods)
    
    # Summary statistics
    cycles_by_domain = {}
    for cycle in detected_cycles:
        domain = cycle["domain"]
        if domain not in cycles_by_domain:
            cycles_by_domain[domain] = []
        cycles_by_domain[domain].append(cycle["period"])
    
    return {
        "configuration": {
            "interaction_mode": interaction_mode,
            "n_samples": n_samples,
            "integration_steps": integration_steps,
            "n_domains": len(domain_parameter_names)
        },
        "individual_domain_periods": individual_periods,
        "detected_cycles": {
            "total": len(detected_cycles),
            "by_domain": {
                domain: len(cycles)
                for domain, cycles in cycles_by_domain.items()
            }
        },
        "emergent_cycles": {
            "total": len(emergent_cycles),
            "cycles": emergent_cycles
        },
        "cycles_by_domain": cycles_by_domain
    }
