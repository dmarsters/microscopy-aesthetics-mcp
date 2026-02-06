
from fastmcp import FastMCP
import json
from typing import Literal, Optional, Dict, List
import re
import numpy as np

mcp = FastMCP("microscopy-aesthetics")

# ============================================================================
# PHASE 1A: Import aesthetic-dynamics-core with graceful degradation
# ============================================================================

try:
    from aesthetic_dynamics_core import (
        _integrate_trajectory_impl,
        _compute_gradient_field_impl,
        _analyze_convergence_impl
    )
    DYNAMICS_AVAILABLE = True
except ImportError:
    # Graceful degradation if aesthetic-dynamics-core not installed
    DYNAMICS_AVAILABLE = False
    _integrate_trajectory_impl = None
    _compute_gradient_field_impl = None
    _analyze_convergence_impl = None


# ============================================================================
# SERVER METADATA (Updated for Phase 1A + Phase 2.6)
# ============================================================================

SERVER_VERSION = "1.2.0-phase1a-phase2.6"
VALIDATION_DATE = "2026-01-14"


# Profile data structure - all 7 microscopy types with aesthetic vocabulary
MICROSCOPY_PROFILES = {
    "fluorescence": {
        "display_name": "Fluorescence",
        "description": "Glowing cellular structures with luminous bodies and translucent layers",
        "structure": ["glowing cellular structures", "illuminated organelles", "highlighted features", "distinct compartments", "labeled pathways"],
        "material": ["translucent membranes", "luminous bodies", "transparent layers", "semi-permeable boundaries", "fluorescent markers"],
        "color": ["vibrant greens", "electric blues", "hot pinks", "bright cyans", "neon yellows", "intense magentas"],
        "texture": ["smooth membranes", "granular cytoplasm", "filamentous networks", "punctate signals", "diffuse glow"],
        "composition": ["layered transparency", "overlapping signals", "depth through color", "selective illumination"],
        "style": ["fluorescent microscopy", "immunofluorescence", "live cell imaging", "confocal projection"],
        "quality": ["high contrast", "selective highlighting", "brilliant colors", "precise localization"],
        "mood": ["scientific clarity", "targeted visualization", "functional mapping"],
        "examples": ["fluorescent-stained cells", "immunolabeled tissues", "GFP expression", "multi-color FISH"],
        "color_palette": {
            "scientific": ["vibrant greens", "electric blues", "hot pinks", "bright cyans", "neon yellows", "intense magentas"],
            "artistic": ["jewel tones", "ethereal glows", "luminescent accents", "chromatic intensity"],
            "monochrome": ["bright highlights on dark background", "grayscale with fluorescent whites"]
        },
        "magnification_feel": {
            "low": "tissue-level fluorescent regions with broad signal distribution",
            "medium": "cellular organelle visualization with distinct compartmentalization",
            "high": "subcellular molecular-scale localization with punctate detail"
        }
    },
    "electron": {
        "display_name": "Electron (SEM/TEM)",
        "description": "Ultra-detailed nanoscale surfaces with dramatic shadows and three-dimensional relief",
        "structure": ["ultra-detailed surfaces", "nanoscale textures", "fine filaments", "membrane ultrastructure", "crystalline arrays"],
        "material": ["metallic surfaces", "shadowed topology", "three-dimensional relief", "textured coatings", "sharp edges"],
        "color": ["grayscale gradients", "silver-white highlights", "deep blacks", "metallic sheens"],
        "texture": ["rough surfaces", "smooth membranes", "fibrous networks", "granular details", "crystalline facets"],
        "composition": ["dramatic shadows", "depth through contrast", "topographical relief", "textural emphasis"],
        "style": ["scanning electron microscopy", "transmission electron microscopy", "ultra-high resolution"],
        "quality": ["extreme detail", "nanoscale precision", "textural richness", "three-dimensional appearance"],
        "mood": ["alien landscapes", "otherworldly surfaces", "microscopic terrain"],
        "examples": ["cell surfaces", "bacterial structures", "tissue ultrastructure", "crystalline materials"],
        "color_palette": {
            "scientific": ["grayscale gradients", "silver-white highlights", "deep blacks", "metallic sheens"],
            "artistic": ["platinum whites", "shadow blacks", "metallic accents", "high-contrast drama"],
            "monochrome": ["pure grayscale", "silver-to-black gradient", "high-contrast relief"]
        },
        "magnification_feel": {
            "low": "tissue-scale topography with broad textural variation and macro relief",
            "medium": "cellular-scale ultrastructure with detailed surface features and membrane topology",
            "high": "molecular-scale atomic arrangements with crystalline precision and nanoscale texturing"
        }
    },
    "phase_contrast": {
        "display_name": "Phase Contrast",
        "description": "Transparent boundaries with refractive halos and ethereal ghost-like structures",
        "structure": ["transparent boundaries", "cellular outlines", "refractive halos", "phase shifts", "gradient edges"],
        "material": ["semi-transparent cells", "clear media", "refractive interfaces", "optical density variations"],
        "color": ["grayscale with optical halos", "subtle contrast", "light-dark boundaries"],
        "texture": ["smooth gradients", "halo effects", "edge enhancement", "translucent bodies"],
        "composition": ["overlapping transparencies", "layered optical sections", "depth through refraction"],
        "style": ["phase contrast microscopy", "differential interference contrast", "relief imaging"],
        "quality": ["natural appearance", "living cell observation", "three-dimensional relief", "halo artifacts"],
        "mood": ["ethereal", "ghost-like", "translucent", "observational"],
        "examples": ["living cells", "unstained cellular dynamics", "transparent organisms", "culture monitoring"],
        "color_palette": {
            "scientific": ["grayscale with subtle contrast", "optical halos in light tones"],
            "artistic": ["pearlescent halos", "translucent overlays", "subtle shadow depth"],
            "monochrome": ["pure grayscale with halo emphasis", "high-key luminosity"]
        },
        "magnification_feel": {
            "low": "broad cellular boundaries with subtle refractive halos across tissue regions",
            "medium": "individual cell outlines with clear phase-shift effects and optical density variation",
            "high": "subcellular membrane boundaries with fine refractive detail and edge-enhancement artifacts"
        }
    },
    "confocal": {
        "display_name": "Confocal",
        "description": "Sharp optical sections with volumetric depth and three-dimensional reconstruction clarity",
        "structure": ["sharp optical sections", "z-stack projections", "three-dimensional reconstructions", "layered imaging"],
        "material": ["optically sectioned layers", "volumetric data", "stacked focal planes", "depth-resolved structures"],
        "color": ["multiple fluorescence channels", "merged color overlays", "depth-coded colors"],
        "texture": ["crisp details", "minimal blur", "sectioned appearance", "volumetric rendering"],
        "composition": ["layered depth", "three-dimensional space", "focal plane stacking", "volumetric organization"],
        "style": ["confocal laser scanning microscopy", "optical sectioning", "3D reconstruction"],
        "quality": ["exceptional clarity", "depth resolution", "three-dimensional detail", "minimal out-of-focus light"],
        "mood": ["precise", "analytical", "spatially resolved", "architecturally detailed"],
        "examples": ["tissue architecture", "cellular 3D structure", "subcellular localization", "thick specimen imaging"],
        "color_palette": {
            "scientific": ["multiple fluorescence channels", "merged color overlays", "depth-coded color progression"],
            "artistic": ["layered chromatic depth", "volumetric color shifts", "3D-aware palettes"],
            "monochrome": ["depth-coded grayscale", "layered intensity variation"]
        },
        "magnification_feel": {
            "low": "volumetric tissue architecture with broad three-dimensional organization visible across planes",
            "medium": "cellular 3D structure with distinct focal planes revealing organelle arrangement and layering",
            "high": "subcellular molecular-scale localization with precise z-depth mapping and volumetric detail"
        }
    },
    "brightfield": {
        "display_name": "Brightfield",
        "description": "Natural tissue appearance with histological stains and recognizable anatomical features",
        "structure": ["natural tissue appearance", "histological sections", "stained preparations", "anatomical features"],
        "material": ["tissue texture", "cellular morphology", "stained components", "natural coloration"],
        "color": ["histological stains", "pinks", "purples", "blues", "natural tissue colors", "H&E appearance"],
        "texture": ["tissue grain", "cellular patterns", "fibrous structures", "glandular organization"],
        "composition": ["tissue architecture", "organ structure", "anatomical arrangement", "pathological features"],
        "style": ["brightfield microscopy", "histology", "pathology", "stained sections"],
        "quality": ["natural appearance", "diagnostic clarity", "recognizable morphology", "classical microscopy"],
        "mood": ["medical", "diagnostic", "anatomical", "educational"],
        "examples": ["H&E stained tissue", "pathology slides", "histological sections", "medical diagnosis"],
        "color_palette": {
            "scientific": ["H&E pinks", "purples", "blues", "natural tissue browns"],
            "artistic": ["warm histological tones", "rich stain colors", "subtle tissue variations"],
            "monochrome": ["sepia tones", "grayscale histological rendering"]
        },
        "magnification_feel": {
            "low": "tissue-level organ and glandular architecture with broad anatomical organization",
            "medium": "cellular morphology and tissue type identification with clear histological detail",
            "high": "subcellular features and stain localization with diagnostic precision at near-ultrastructural level"
        }
    },
    "darkfield": {
        "display_name": "Darkfield",
        "description": "Bright objects on dark background with dramatic edge illumination and scattered light",
        "structure": ["bright objects on dark background", "scattered light", "edge illumination", "suspended particles"],
        "material": ["reflective surfaces", "light-scattering bodies", "bright against black", "rim lighting"],
        "color": ["bright specimens against black void", "edge glow", "scattered light colors"],
        "texture": ["glowing edges", "bright particles", "illuminated contours", "scattered highlights"],
        "composition": ["dramatic contrast", "floating in darkness", "isolated subjects", "scattered light patterns"],
        "style": ["darkfield microscopy", "scattered light imaging", "edge enhancement"],
        "quality": ["high contrast", "dramatic lighting", "silhouette effects", "revealing transparency"],
        "mood": ["dramatic", "mysterious", "isolated", "theatrical"],
        "examples": ["microorganisms in liquid", "unstained specimens", "particle visualization", "spiral bacteria"],
        "color_palette": {
            "scientific": ["bright highlights on black", "edge glow colors", "scattered light spectrum"],
            "artistic": ["dramatic rim lighting", "neon-like glow", "theatrical shadows"],
            "monochrome": ["pure black background with bright white highlights", "extreme contrast"]
        },
        "magnification_feel": {
            "low": "suspended particles and organisms floating in dark field with broad scattered light",
            "medium": "individual microorganisms with glowing edges and scattered light patterns from cellular features",
            "high": "fine subcellular light-scattering structures with dramatic edge illumination and minimal internal detail"
        }
    },
    "multiphoton": {
        "display_name": "Multiphoton",
        "description": "Deep tissue penetration with autofluorescence and minimal phototoxicity appearance",
        "structure": ["deep tissue sections", "autofluorescent structures", "three-dimensional volumes", "intrinsic fluorescence"],
        "material": ["tissue depth", "natural fluorophores", "cellular autofluorescence", "penetrating illumination"],
        "color": ["autofluorescence tones", "infrared-excited emission", "natural tissue fluorescence"],
        "texture": ["volumetric rendering", "depth gradients", "natural fluorescence patterns", "soft glow"],
        "composition": ["deep tissue imaging", "minimal surface artifact", "volumetric depth", "layered autofluorescence"],
        "style": ["two-photon microscopy", "three-photon imaging", "deep tissue fluorescence"],
        "quality": ["deep penetration", "minimal photodamage", "autofluorescence capture", "thick tissue capability"],
        "mood": ["natural", "deep", "preserved", "gentle"],
        "examples": ["brain tissue imaging", "thick tissue sections", "living tissue", "minimal perturbation imaging"],
        "color_palette": {
            "scientific": ["autofluorescence greens", "infrared-excited blues", "natural tissue emission"],
            "artistic": ["soft natural glows", "volumetric color depth", "gentle autofluorescence"],
            "monochrome": ["depth-coded grayscale", "soft contrast gradients"]
        },
        "magnification_feel": {
            "low": "deep tissue architecture with broad autofluorescence patterns and volumetric organization",
            "medium": "cellular autofluorescence within thick tissue revealing natural fluorophore distribution",
            "high": "subcellular autofluorescence detail with minimal phototoxicity and natural emission patterns"
        }
    }
}


# ============================================================================
# PHASE 1A: Parameter Extraction for Morphospace Coordinates
# ============================================================================

def extract_microscopy_coordinates(microscopy_type: str) -> dict:
    """
    Extract quantitative parameters from microscopy profile.
    
    Creates a 5D morphospace coordinate for trajectory computation:
    - contrast_intensity: Visual contrast (0.0-1.0)
    - color_saturation: Monochrome to vibrant color (0.0-1.0)
    - structural_detail: Complexity of detail (0.0-1.0)
    - dimensional_depth: 2D surface to 3D volume (0.0-1.0)
    - illumination_mode: Background brightness (0.0-1.0)
    
    Layer 2 deterministic operation - 0 tokens
    """
    if microscopy_type not in MICROSCOPY_PROFILES:
        return None
    
    profile = MICROSCOPY_PROFILES[microscopy_type]
    
    # Contrast intensity (based on quality descriptors)
    contrast_map = {
        "fluorescence": 0.85,  # High contrast
        "electron": 0.95,      # Extreme contrast
        "phase_contrast": 0.40,  # Subtle contrast
        "confocal": 0.90,      # Exceptional clarity
        "brightfield": 0.55,   # Natural appearance
        "darkfield": 1.0,      # Maximum contrast (black background)
        "multiphoton": 0.65    # Soft contrast
    }
    
    # Color saturation (monochrome vs vibrant)
    saturation_map = {
        "fluorescence": 1.0,      # Vibrant colors
        "electron": 0.0,          # Pure grayscale
        "phase_contrast": 0.1,    # Mostly grayscale
        "confocal": 0.85,         # Multiple fluorescence channels
        "brightfield": 0.65,      # Histological stains
        "darkfield": 0.20,        # Mostly monochrome with edge glow
        "multiphoton": 0.50       # Autofluorescence tones
    }
    
    # Structural detail (complexity of detail elements)
    detail_map = {
        "fluorescence": 0.70,
        "electron": 1.0,          # Ultra-detailed
        "phase_contrast": 0.45,   # Subtle boundaries
        "confocal": 0.85,         # Sharp sections
        "brightfield": 0.60,      # Natural tissue detail
        "darkfield": 0.55,        # Edge detail
        "multiphoton": 0.70       # Volumetric detail
    }
    
    # Dimensional depth (2D vs 3D imaging)
    depth_map = {
        "fluorescence": 0.50,     # Can be 2D or 3D
        "electron": 0.20,         # Primarily surface (SEM)
        "phase_contrast": 0.35,   # Some 3D relief
        "confocal": 1.0,          # Full 3D reconstruction
        "brightfield": 0.15,      # Flat sections
        "darkfield": 0.40,        # Some depth from scattered light
        "multiphoton": 0.95       # Deep tissue 3D
    }
    
    # Illumination mode (background brightness: dark field = 0, bright field = 1)
    illumination_map = {
        "fluorescence": 0.10,     # Dark background
        "electron": 0.50,         # Neutral (grayscale)
        "phase_contrast": 0.70,   # Light background
        "confocal": 0.15,         # Dark background
        "brightfield": 1.0,       # Bright background
        "darkfield": 0.0,         # Pure dark background
        "multiphoton": 0.25       # Darker background
    }
    
    return {
        "contrast_intensity": contrast_map[microscopy_type],
        "color_saturation": saturation_map[microscopy_type],
        "structural_detail": detail_map[microscopy_type],
        "dimensional_depth": depth_map[microscopy_type],
        "illumination_mode": illumination_map[microscopy_type]
    }


# Parameter names in consistent order (critical for trajectory computation)
PARAMETER_NAMES = [
    "contrast_intensity",
    "color_saturation",
    "structural_detail",
    "dimensional_depth",
    "illumination_mode"
]

# Valid parameter bounds for all dimensions
BOUNDS = [0.0, 1.0]


# ============================================================================
# LAYER 2: TRAJECTORY DYNAMICS (Phase 1A)
# ============================================================================

def _compute_trajectory_between_microscopy_types_impl(
    start_type: str,
    end_type: str,
    num_steps: int = 30,
    return_analysis: bool = True
) -> dict:
    """
    Core implementation of trajectory computation between microscopy types.
    
    Computes smooth RK4-integrated path through 5D microscopy morphospace
    from start_type to end_type.
    
    Args:
        start_type: Starting microscopy type
        end_type: Target microscopy type
        num_steps: Number of integration steps (default: 30)
        return_analysis: Include convergence analysis (default: True)
    
    Returns:
        Complete trajectory specification with convergence metrics
    
    Cost: 0 tokens (pure Layer 2 computation)
    """
    if not DYNAMICS_AVAILABLE:
        return {
            "error": "aesthetic-dynamics-core not installed",
            "message": "Install with: pip install aesthetic-dynamics-core --break-system-packages",
            "fallback": "Use map_microscopy_parameters for static parameter mapping"
        }
    
    # Validate microscopy types
    if start_type not in MICROSCOPY_PROFILES:
        return {
            "error": f"Unknown start microscopy type: {start_type}",
            "available": list(MICROSCOPY_PROFILES.keys())
        }
    
    if end_type not in MICROSCOPY_PROFILES:
        return {
            "error": f"Unknown end microscopy type: {end_type}",
            "available": list(MICROSCOPY_PROFILES.keys())
        }
    
    # Extract coordinates
    start_coords = extract_microscopy_coordinates(start_type)
    end_coords = extract_microscopy_coordinates(end_type)
    
    if start_coords is None or end_coords is None:
        return {
            "error": "Failed to extract coordinates from microscopy profiles"
        }
    
    # Check for domain-specific constraints
    # (microscopy has no forbidden combinations - all transitions valid)
    
    # Compute trajectory using aesthetic-dynamics-core
    trajectory_result = _integrate_trajectory_impl(
        start_state=start_coords,
        target_state=end_coords,
        parameter_names=PARAMETER_NAMES,
        num_steps=num_steps,
        bounds=BOUNDS,
        convergence_threshold=0.01
    )
    
    # Compute Euclidean distance for comparison

    start_vec = np.array([start_coords[p] for p in PARAMETER_NAMES])
    end_vec = np.array([end_coords[p] for p in PARAMETER_NAMES])
    euclidean_distance = float(np.linalg.norm(end_vec - start_vec))
    
    # Prepare response
    response = {
        "start_microscopy": {
            "type": start_type,
            "display_name": MICROSCOPY_PROFILES[start_type]["display_name"],
            "coordinates": start_coords
        },
        "end_microscopy": {
            "type": end_type,
            "display_name": MICROSCOPY_PROFILES[end_type]["display_name"],
            "coordinates": end_coords
        },
        "trajectory": {
            "states": trajectory_result["trajectory"],
            "num_steps": trajectory_result["num_steps"],
            "parameter_names": PARAMETER_NAMES
        },
        "convergence": {
            "converged": trajectory_result["converged"],
            "convergence_step": trajectory_result["convergence_step"],
            "final_distance": trajectory_result["final_distance"],
            "convergence_threshold": 0.01
        },
        "path_metrics": {
            "geodesic_length": trajectory_result["path_length"],
            "euclidean_distance": euclidean_distance,
            "path_efficiency": euclidean_distance / trajectory_result["path_length"] if trajectory_result["path_length"] > 0 else 1.0
        },
        "dynamics_info": {
            "integration_method": "RK4 (Runge-Kutta 4th order)",
            "bounds": str(BOUNDS),
            "morphospace_dimensions": 5,
            "cost": "0 tokens (pure Layer 2)"
        }
    }
    
    # Add convergence analysis if requested
    if return_analysis and trajectory_result["converged"]:
        analysis = _analyze_convergence_impl(
            trajectory=trajectory_result["trajectory"],
            target_state=end_coords,
            parameter_names=PARAMETER_NAMES,
            threshold=0.01
        )
        
        response["convergence_analysis"] = {
            "monotonic_decrease": analysis["monotonic_decrease"],
            "oscillation_count": analysis["oscillation_count"],
            "convergence_rate": analysis["convergence_rate"],
            "distance_reduction": analysis["distance_reduction"]
        }
    
    return response


@mcp.tool()
def compute_trajectory_between_microscopy_types(
    start_type: str,
    end_type: str,
    num_steps: int = 30,
    return_analysis: bool = True
) -> dict:
    """
    Compute smooth trajectory between two microscopy types in morphospace.
    
    NEW PHASE 1A TOOL: Uses aesthetic-dynamics-core for zero-cost trajectory
    integration via RK4. Enables visualization of smooth aesthetic transitions
    through microscopy parameter space.
    
    This answers questions like:
    - "What's the smoothest path from electron to fluorescence microscopy?"
    - "How does color saturation evolve from darkfield to brightfield?"
    - "What intermediate states exist between 2D and 3D imaging modes?"
    
    Args:
        start_type: Starting microscopy type (fluorescence, electron, etc.)
        end_type: Target microscopy type
        num_steps: Number of integration steps (default: 30)
        return_analysis: Include convergence analysis (default: True)
    
    Returns:
        Dictionary with trajectory data, convergence metrics, and transition analysis
    
    Cost: 0 tokens (pure Layer 2 deterministic computation)
    
    Example:
        >>> compute_trajectory_between_microscopy_types(
        ...     "electron",
        ...     "fluorescence",
        ...     num_steps=20
        ... )
        {
            "start_microscopy": {
                "type": "electron",
                "display_name": "Electron (SEM/TEM)",
                "coordinates": {
                    "contrast_intensity": 0.95,
                    "color_saturation": 0.0,
                    ...
                }
            },
            "end_microscopy": {...},
            "trajectory": [...],  # 21 intermediate states
            "converged": true,
            "path_metrics": {
                "geodesic_length": 1.247,
                "euclidean_distance": 1.183,
                "path_efficiency": 0.949
            }
        }
    """
    return _compute_trajectory_between_microscopy_types_impl(
        start_type, end_type, num_steps, return_analysis
    )


# ============================================================================
# LAYER 2: RHYTHMIC COMPOSITION (Phase 2.6)
# ============================================================================

def _generate_sinusoidal_oscillation(
    num_steps: int,
    num_cycles: float,
    phase_offset: float = 0.0
) -> np.ndarray:
    """
    Generate smooth sinusoidal oscillation pattern.
    
    Returns values in [0, 1] following sine wave.
    """
    t = np.linspace(0, 2 * np.pi * num_cycles, num_steps)
    # Shift and scale to [0, 1]
    oscillation = 0.5 * (1 + np.sin(t + phase_offset * 2 * np.pi))
    return oscillation


def _generate_triangular_oscillation(
    num_steps: int,
    num_cycles: float,
    phase_offset: float = 0.0
) -> np.ndarray:
    """
    Generate linear ramp (triangular wave) oscillation pattern.
    
    Returns values in [0, 1] with linear increases/decreases.
    """
    t = np.linspace(0, num_cycles, num_steps)
    t = t + phase_offset  # Apply phase offset
    
    # Triangle wave: ramp up then down per cycle
    # Compute position within cycle [0, 1]
    t_cycle = t % 1.0
    
    # Triangle wave: ramp up then down
    oscillation = np.where(t_cycle < 0.5, 2 * t_cycle, 2 * (1 - t_cycle))
    return oscillation


def _generate_square_oscillation(
    num_steps: int,
    num_cycles: float,
    phase_offset: float = 0.0
) -> np.ndarray:
    """
    Generate abrupt (square wave) oscillation pattern.
    
    Returns values that alternate between 0 and 1.
    """
    t = np.linspace(0, num_cycles, num_steps)
    t = (t + phase_offset) % 1.0  # Apply phase offset
    
    # Square wave: 0 for first half of cycle, 1 for second half
    oscillation = np.where(t < 0.5, 0.0, 1.0)
    return oscillation


def _interpolate_microscopy_states(
    state_a: Dict[str, float],
    state_b: Dict[str, float],
    alpha: float
) -> Dict[str, float]:
    """
    Linearly interpolate between two microscopy parameter states.
    
    Args:
        state_a: Starting state parameters
        state_b: Ending state parameters
        alpha: Interpolation factor [0, 1] (0 = state_a, 1 = state_b)
    
    Returns:
        Interpolated state at alpha
    """
    interpolated = {}
    for param_name in state_a.keys():
        val_a = state_a[param_name]
        val_b = state_b[param_name]
        interpolated[param_name] = (1 - alpha) * val_a + alpha * val_b
    
    return interpolated


def _detect_phase_points(
    oscillation_profile: np.ndarray,
    pattern_type: str
) -> List[Dict]:
    """
    Detect key transition moments in oscillation pattern.
    
    Args:
        oscillation_profile: Array of oscillation values [0, 1]
        pattern_type: "sinusoidal", "triangular", or "square"
    
    Returns:
        List of phase points with step, type, and state
    """
    phase_points = []
    n = len(oscillation_profile)
    
    # Start point
    phase_points.append({
        "step": 0,
        "type": "start",
        "state": "state_a" if oscillation_profile[0] < 0.5 else "state_b",
        "alpha": float(oscillation_profile[0])
    })
    
    # Find peaks and troughs
    for i in range(1, n - 1):
        prev_val = oscillation_profile[i - 1]
        curr_val = oscillation_profile[i]
        next_val = oscillation_profile[i + 1]
        
        # Peak (local maximum)
        if curr_val > prev_val and curr_val > next_val:
            if curr_val > 0.9:  # Near state_b
                phase_points.append({
                    "step": i,
                    "type": "peak",
                    "state": "state_b",
                    "alpha": float(curr_val)
                })
        
        # Trough (local minimum)
        elif curr_val < prev_val and curr_val < next_val:
            if curr_val < 0.1:  # Near state_a
                phase_points.append({
                    "step": i,
                    "type": "trough",
                    "state": "state_a",
                    "alpha": float(curr_val)
                })
        
        # Midpoint crossings
        if pattern_type == "sinusoidal":
            if (prev_val < 0.5 <= curr_val) or (prev_val > 0.5 >= curr_val):
                phase_points.append({
                    "step": i,
                    "type": "midpoint",
                    "state": "transitioning",
                    "alpha": float(curr_val)
                })
    
    # End point
    phase_points.append({
        "step": n - 1,
        "type": "end",
        "state": "state_a" if oscillation_profile[-1] < 0.5 else "state_b",
        "alpha": float(oscillation_profile[-1])
    })
    
    return phase_points


def _describe_microscopy_aesthetic_flow(
    state_a_type: str,
    state_b_type: str,
    pattern_type: str,
    num_cycles: int
) -> str:
    """
    Generate human-readable description of rhythmic microscopy flow.
    """
    pattern_descriptions = {
        "sinusoidal": "Smooth, continuous oscillation",
        "triangular": "Linear ramping transitions",
        "square": "Abrupt, step-wise changes"
    }
    
    pattern_feel = {
        "sinusoidal": "natural breathing rhythm",
        "triangular": "mechanical scanning motion",
        "square": "toggling between distinct modes"
    }
    
    return (
        f"{pattern_descriptions[pattern_type]} between {state_a_type} and {state_b_type} microscopy. "
        f"{num_cycles} complete cycle(s) with {pattern_feel[pattern_type]}. "
        f"Creates temporal imaging dynamics suitable for time-lapse visualization."
    )


def _generate_rhythmic_microscopy_sequence_impl(
    state_a_id: str,
    state_b_id: str,
    state_a_coords: Dict[str, float],
    state_b_coords: Dict[str, float],
    oscillation_pattern: str = "sinusoidal",
    num_cycles: int = 2,
    steps_per_cycle: int = 20,
    phase_offset: float = 0.0
) -> dict:
    """
    Core implementation of rhythmic microscopy sequence generation.
    
    Args:
        state_a_id: Starting microscopy type ID
        state_b_id: Alternating microscopy type ID
        state_a_coords: Parameter coordinates for state A
        state_b_coords: Parameter coordinates for state B
        oscillation_pattern: "sinusoidal", "triangular", or "square"
        num_cycles: Number of complete A→B→A cycles
        steps_per_cycle: Samples per cycle (resolution)
        phase_offset: Starting phase (0.0 = start at A, 0.5 = start at B)
    
    Returns:
        Complete rhythmic sequence with metadata
    """
    total_steps = num_cycles * steps_per_cycle
    
    # Generate oscillation profile
    if oscillation_pattern == "sinusoidal":
        oscillation = _generate_sinusoidal_oscillation(total_steps, num_cycles, phase_offset)
    elif oscillation_pattern == "triangular":
        oscillation = _generate_triangular_oscillation(total_steps, num_cycles, phase_offset)
    elif oscillation_pattern == "square":
        oscillation = _generate_square_oscillation(total_steps, num_cycles, phase_offset)
    else:
        return {
            "error": f"Unknown oscillation pattern: {oscillation_pattern}",
            "valid_patterns": ["sinusoidal", "triangular", "square"]
        }
    
    # Generate interpolated states
    sequence = []
    for alpha in oscillation:
        interpolated_state = _interpolate_microscopy_states(
            state_a_coords,
            state_b_coords,
            float(alpha)
        )
        sequence.append(interpolated_state)
    
    # Detect phase points
    phase_points = _detect_phase_points(oscillation, oscillation_pattern)
    
    # Generate flow description
    aesthetic_flow = _describe_microscopy_aesthetic_flow(
        state_a_id,
        state_b_id,
        oscillation_pattern,
        num_cycles
    )
    
    return {
        "sequence": sequence,
        "pattern_type": oscillation_pattern,
        "num_cycles": num_cycles,
        "steps_per_cycle": steps_per_cycle,
        "total_steps": total_steps,
        "phase_offset": phase_offset,
        "phase_points": phase_points,
        "aesthetic_flow": aesthetic_flow,
        "frequency": num_cycles / total_steps,
        "oscillation_profile": oscillation.tolist(),
        "state_a": {
            "id": state_a_id,
            "coordinates": state_a_coords
        },
        "state_b": {
            "id": state_b_id,
            "coordinates": state_b_coords
        }
    }


# Preset configurations
MICROSCOPY_RHYTHMIC_PRESETS = {
    "focus_sweep": {
        "description": "Rhythmic focus depth transitions (shallow ↔ deep)",
        "state_a_id": "brightfield",
        "state_b_id": "confocal",
        "oscillation_pattern": "sinusoidal",
        "num_cycles": 3,
        "steps_per_cycle": 24,
        "phase_offset": 0.0,
        "use_case": "Simulating focus depth scanning through thick specimens",
        "visual_effect": "Smooth transition from surface to deep tissue layers"
    },
    
    "illumination_cycle": {
        "description": "Light mode transitions (brightfield ↔ darkfield)",
        "state_a_id": "brightfield",
        "state_b_id": "darkfield",
        "oscillation_pattern": "sinusoidal",
        "num_cycles": 4,
        "steps_per_cycle": 20,
        "phase_offset": 0.0,
        "use_case": "Day/night imaging cycles for circadian rhythm studies",
        "visual_effect": "Background brightness oscillation revealing different features"
    },
    
    "magnification_zoom": {
        "description": "Zoom level oscillation (low ↔ high detail)",
        "state_a_id": "brightfield",
        "state_b_id": "electron",
        "oscillation_pattern": "triangular",
        "num_cycles": 2,
        "steps_per_cycle": 30,
        "phase_offset": 0.0,
        "use_case": "Zooming from tissue-level to subcellular ultrastructure",
        "visual_effect": "Linear zoom revealing progressively finer structural details"
    },
    
    "contrast_pulse": {
        "description": "Contrast variation (high ↔ low)",
        "state_a_id": "electron",
        "state_b_id": "phase_contrast",
        "oscillation_pattern": "sinusoidal",
        "num_cycles": 5,
        "steps_per_cycle": 16,
        "phase_offset": 0.0,
        "use_case": "Emphasizing different structural features through contrast modulation",
        "visual_effect": "Pulsing visibility of fine structures vs. overall form"
    },
    
    "imaging_mode_toggle": {
        "description": "Mode switching (2D ↔ 3D)",
        "state_a_id": "brightfield",
        "state_b_id": "multiphoton",
        "oscillation_pattern": "square",
        "num_cycles": 4,
        "steps_per_cycle": 10,
        "phase_offset": 0.0,
        "use_case": "Toggling between surface and volumetric imaging modes",
        "visual_effect": "Abrupt transitions between 2D sections and 3D reconstructions"
    }
}


@mcp.tool()
def generate_rhythmic_microscopy_sequence(
    state_a_id: str,
    state_b_id: str,
    oscillation_pattern: str = "sinusoidal",
    num_cycles: int = 2,
    steps_per_cycle: int = 20,
    phase_offset: float = 0.0
) -> dict:
    """
    Generate rhythmic oscillation between two microscopy imaging modes.
    
    PHASE 2.6 NEW TOOL: Adds temporal/rhythmic composition to microscopy aesthetics.
    Creates periodic transitions that cycle between imaging configurations.
    
    Building on Phase 1A trajectory computation, this tool enables:
    - Focus depth cycles (2D ↔ 3D imaging)
    - Illumination oscillations (bright ↔ dark field)
    - Magnification zooming (low ↔ high detail)
    - Contrast pulsing (high ↔ low)
    - Mode toggling (electron ↔ fluorescence)
    
    Pure Layer 2 deterministic operation - 0 tokens.
    
    Args:
        state_a_id: Starting microscopy type (see list_microscopy_types)
        state_b_id: Alternating microscopy type
        oscillation_pattern: Wave shape
            - "sinusoidal": Smooth, continuous (natural rhythms)
            - "triangular": Linear ramps (mechanical rhythms)
            - "square": Abrupt changes (punctuated rhythms)
        num_cycles: Number of complete A→B→A cycles
        steps_per_cycle: Samples per cycle (higher = smoother)
        phase_offset: Starting phase (0.0 = start at A, 0.5 = start at B)
    
    Returns:
        sequence: List of microscopy parameter states
        pattern_type: Echo of oscillation pattern
        num_cycles: Number of cycles completed
        phase_points: Key transition moments (peaks, troughs)
        aesthetic_flow: Human-readable flow description
        frequency: Cycles per total duration
        oscillation_profile: Raw oscillation values [0, 1]
    
    Cost: 0 tokens (pure Layer 2 computation)
    
    Example:
        >>> generate_rhythmic_microscopy_sequence(
        ...     "brightfield",
        ...     "darkfield",
        ...     oscillation_pattern="sinusoidal",
        ...     num_cycles=2,
        ...     steps_per_cycle=20
        ... )
        {
            "sequence": [
                {"contrast_intensity": 0.6, "illumination_mode": 1.0, ...},
                {"contrast_intensity": 0.58, "illumination_mode": 0.95, ...},
                ...
            ],
            "pattern_type": "sinusoidal",
            "num_cycles": 2,
            "total_steps": 40,
            "phase_points": [...],
            "aesthetic_flow": "Smooth, continuous oscillation..."
        }
    """
    # Validate microscopy types
    if state_a_id not in MICROSCOPY_PROFILES:
        return {
            "error": f"Unknown microscopy type: {state_a_id}",
            "available_types": list(MICROSCOPY_PROFILES.keys())
        }
    
    if state_b_id not in MICROSCOPY_PROFILES:
        return {
            "error": f"Unknown microscopy type: {state_b_id}",
            "available_types": list(MICROSCOPY_PROFILES.keys())
        }
    
    # Extract coordinates
    state_a_coords = extract_microscopy_coordinates(state_a_id)
    state_b_coords = extract_microscopy_coordinates(state_b_id)
    
    return _generate_rhythmic_microscopy_sequence_impl(
        state_a_id, state_b_id,
        state_a_coords, state_b_coords,
        oscillation_pattern, num_cycles, steps_per_cycle, phase_offset
    )


@mcp.tool()
def apply_microscopy_rhythmic_preset(
    preset_name: str,
    override_params: Optional[Dict] = None
) -> dict:
    """
    Apply a curated rhythmic microscopy pattern preset.
    
    PHASE 2.6 CONVENIENCE TOOL: Pre-configured rhythmic compositions
    for common microscopy imaging use cases.
    
    Available Presets:
    
    1. **focus_sweep**
       - brightfield ↔ confocal over 3 cycles (24 steps each)
       - Surface imaging → deep tissue reconstruction
       - Sinusoidal pattern (smooth depth transitions)
    
    2. **illumination_cycle**
       - brightfield ↔ darkfield over 4 cycles (20 steps each)
       - Day/night background oscillation
       - Sinusoidal pattern
    
    3. **magnification_zoom**
       - brightfield ↔ electron over 2 cycles (30 steps each)
       - Tissue scale → nanoscale detail
       - Triangular pattern (linear zoom)
    
    4. **contrast_pulse**
       - electron ↔ phase_contrast over 5 cycles (16 steps each)
       - High → low contrast pulsing
       - Sinusoidal pattern
    
    5. **imaging_mode_toggle**
       - brightfield ↔ multiphoton over 4 cycles (10 steps each)
       - 2D section → 3D volume switching
       - Square wave (abrupt transitions)
    
    Args:
        preset_name: Name of preset configuration
        override_params: Optional dict to override preset defaults
            Keys: state_a_id, state_b_id, oscillation_pattern,
                  num_cycles, steps_per_cycle, phase_offset
    
    Returns:
        Same as generate_rhythmic_microscopy_sequence, plus:
        preset_info: Metadata about applied preset
    
    Cost: 0 tokens (pure Layer 2)
    
    Example:
        >>> apply_microscopy_rhythmic_preset("focus_sweep")
        # Returns 72-step sequence: brightfield → confocal → brightfield × 3
        
        >>> apply_microscopy_rhythmic_preset(
        ...     "illumination_cycle",
        ...     override_params={"num_cycles": 2}
        ... )
        # Returns modified preset with 2 cycles instead of 4
    """
    if preset_name not in MICROSCOPY_RHYTHMIC_PRESETS:
        return {
            "error": f"Unknown preset: {preset_name}",
            "available_presets": list(MICROSCOPY_RHYTHMIC_PRESETS.keys())
        }
    
    # Load preset configuration
    preset = MICROSCOPY_RHYTHMIC_PRESETS[preset_name].copy()
    
    # Apply overrides if provided
    if override_params:
        for key, value in override_params.items():
            if key in ["state_a_id", "state_b_id", "oscillation_pattern", 
                      "num_cycles", "steps_per_cycle", "phase_offset"]:
                preset[key] = value
    
    # Extract preset info for return
    preset_info = {
        "preset_name": preset_name,
        "description": preset["description"],
        "use_case": preset["use_case"],
        "visual_effect": preset["visual_effect"],
        "overrides_applied": override_params if override_params else None
    }
    
    # Extract coordinates
    state_a_coords = extract_microscopy_coordinates(preset["state_a_id"])
    state_b_coords = extract_microscopy_coordinates(preset["state_b_id"])
    
    # Generate sequence
    result = _generate_rhythmic_microscopy_sequence_impl(
        preset["state_a_id"],
        preset["state_b_id"],
        state_a_coords,
        state_b_coords,
        preset["oscillation_pattern"],
        preset["num_cycles"],
        preset["steps_per_cycle"],
        preset.get("phase_offset", 0.0)
    )
    
    result["preset_info"] = preset_info
    return result


@mcp.tool()
def list_microscopy_rhythmic_presets() -> dict:
    """
    List all available rhythmic microscopy presets with descriptions.
    
    Returns detailed information about each preset including:
    - State transitions
    - Pattern type
    - Number of cycles
    - Use cases
    
    Cost: 0 tokens (pure lookup)
    """
    return {
        "presets": {
            name: {
                "description": config["description"],
                "states": f"{config['state_a_id']} ↔ {config['state_b_id']}",
                "pattern": config["oscillation_pattern"],
                "cycles": config["num_cycles"],
                "steps_per_cycle": config["steps_per_cycle"],
                "use_case": config["use_case"],
                "visual_effect": config["visual_effect"]
            }
            for name, config in MICROSCOPY_RHYTHMIC_PRESETS.items()
        },
        "total_presets": len(MICROSCOPY_RHYTHMIC_PRESETS)
    }


# ============================================================================
# EXISTING LAYER 1 & 2 TOOLS (Preserved from original)
# ============================================================================

@mcp.tool()
def list_microscopy_types() -> dict:
    """List all available microscopy types with brief descriptions."""
    return {
        microscopy_type: {
            "display_name": profile["display_name"],
            "description": profile["description"]
        }
        for microscopy_type, profile in MICROSCOPY_PROFILES.items()
    }


@mcp.tool()
def get_microscopy_profile(microscopy_type: str) -> dict:
    """
    Layer 1: Retrieve complete profile data for a microscopy type.
    
    Pure taxonomy lookup - 0 tokens.
    """
    if microscopy_type not in MICROSCOPY_PROFILES:
        return {
            "error": f"Unknown microscopy type: {microscopy_type}",
            "available_types": list(MICROSCOPY_PROFILES.keys())
        }
    
    return MICROSCOPY_PROFILES[microscopy_type]


@mcp.tool()
def map_microscopy_parameters(
    microscopy_type: str,
    magnification: str = "medium",
    color_palette: str = "scientific",
    aesthetic_strength: str = "balanced"
) -> dict:
    """
    Layer 2: Deterministic mapping of microscopy parameters.
    
    Maps microscopy type + modifiers to complete aesthetic vocabulary.
    Pure taxonomy lookup + parameter selection - 0 tokens.
    """
    if microscopy_type not in MICROSCOPY_PROFILES:
        return {
            "error": f"Unknown microscopy type: {microscopy_type}",
            "available_types": list(MICROSCOPY_PROFILES.keys())
        }
    
    profile = MICROSCOPY_PROFILES[microscopy_type]
    
    # Validate parameters
    valid_magnifications = ["low", "medium", "high"]
    valid_palettes = ["scientific", "artistic", "monochrome"]
    valid_strengths = ["subtle", "balanced", "strong"]
    
    if magnification not in valid_magnifications:
        magnification = "medium"
    if color_palette not in valid_palettes:
        color_palette = "scientific"
    if aesthetic_strength not in valid_strengths:
        aesthetic_strength = "balanced"
    
    # Strength determines how many vocabulary terms to include
    strength_counts = {
        "subtle": 2,
        "balanced": 4,
        "strong": 6
    }
    count = strength_counts[aesthetic_strength]
    
    return {
        "microscopy_type": microscopy_type,
        "display_name": profile["display_name"],
        "parameters": {
            "magnification": magnification,
            "color_palette": color_palette,
            "aesthetic_strength": aesthetic_strength
        },
        "aesthetic_vocabulary": {
            "structure": profile["structure"][:count],
            "material": profile["material"][:count],
            "color": profile["color_palette"][color_palette][:count] if color_palette in profile["color_palette"] else profile["color"][:count],
            "texture": profile["texture"][:count],
            "composition": profile["composition"][:count],
            "style": profile["style"][:min(count, len(profile["style"]))],
            "quality": profile["quality"][:count],
            "mood": profile["mood"][:min(count, len(profile["mood"]))]
        },
        "magnification_feel": profile["magnification_feel"][magnification],
        "examples": profile["examples"][:2]
    }


@mcp.tool()
def enhance_prompt_with_microscopy(
    base_prompt: str,
    microscopy_type: str,
    magnification: str = "medium",
    color_palette: str = "scientific",
    aesthetic_strength: str = "balanced"
) -> str:
    """
    Enhance an image generation prompt with microscopy aesthetic vocabulary.
    
    Layer 3 interface: Returns enhanced prompt for Claude synthesis.
    """
    params = map_microscopy_parameters(
        microscopy_type, magnification, color_palette, aesthetic_strength
    )
    
    if "error" in params:
        return f"Error: {params['error']}"
    
    vocab = params["aesthetic_vocabulary"]
    mag_feel = params["magnification_feel"]
    
    # Build enhancement string
    enhancements = []
    
    # Add structure terms
    if vocab["structure"]:
        enhancements.append(", ".join(vocab["structure"][:2]))
    
    # Add material qualities
    if vocab["material"]:
        enhancements.append(", ".join(vocab["material"][:2]))
    
    # Add color/texture
    if vocab["color"]:
        enhancements.append(", ".join(vocab["color"][:2]))
    if vocab["texture"]:
        enhancements.append(vocab["texture"][0])
    
    # Add style descriptor
    if vocab["style"]:
        enhancements.append(vocab["style"][0])
    
    # Add magnification feel
    enhancements.append(mag_feel)
    
    # Combine with base prompt
    enhancement_str = ", ".join(enhancements)
    enhanced_prompt = f"{base_prompt}, {enhancement_str}"
    
    return enhanced_prompt


# ============================================================================
# TOMOGRAPHIC ANALYSIS (Preserved from original)
# ============================================================================

# Strategic pattern definitions for tomographic analysis
STRATEGIC_PATTERNS = {
    "structural_clarity": {
        "clear_boundaries": {
            "pattern": r"\b(clearly defined|explicit|specific roles?|well-defined|distinct boundaries|separate|isolated|independent)\b",
            "threshold": 3,
            "confidence": 0.85
        },
        "ambiguous_structure": {
            "pattern": r"\b(overlapping|unclear|ambiguous|blurred lines|undefined|mixed|hybrid)\b",
            "threshold": 3,
            "confidence": 0.80
        }
    },
    "detail_density": {
        "high_resolution": {
            "pattern": r"\b(detailed|comprehensive|granular|fine-grained|specific|precise|thorough|meticulous)\b",
            "threshold": 4,
            "confidence": 0.85
        },
        "low_resolution": {
            "pattern": r"\b(high-level|overview|general|broad|abstract|simplified|streamlined)\b",
            "threshold": 3,
            "confidence": 0.80
        }
    },
    "dimensional_integration": {
        "layered_depth": {
            "pattern": r"\b(multi-layered|integrated|cross-functional|matrix|interconnected|holistic|systems?)\b",
            "threshold": 3,
            "confidence": 0.85
        },
        "flat_structure": {
            "pattern": r"\b(linear|sequential|step-by-step|straightforward|direct|simple hierarchy)\b",
            "threshold": 3,
            "confidence": 0.80
        }
    },
    "contrast_differentiation": {
        "role_clarity": {
            "pattern": r"\b(responsibilities|accountabilities|ownership|clear roles|defined positions)\b",
            "threshold": 2,
            "confidence": 0.85
        },
        "role_overlap": {
            "pattern": r"\b(collaborative|shared|joint|partnership|co-|collective)\b",
            "threshold": 3,
            "confidence": 0.75
        }
    },
    "observational_mode": {
        "adaptive_strategy": {
            "pattern": r"\b(adaptive|flexible|iterative|agile|responsive|dynamic|evolving|learning)\b",
            "threshold": 3,
            "confidence": 0.85
        },
        "fixed_execution": {
            "pattern": r"\b(standardized|consistent|repeatable|proven|established|fixed|rigid)\b",
            "threshold": 3,
            "confidence": 0.80
        }
    }
}


def detect_structural_clarity(text: str) -> tuple[Optional[str], float, list[str]]:
    """Detect organizational boundary definition."""
    text_lower = text.lower()
    
    # Check clear boundaries
    clear_matches = re.findall(
        STRATEGIC_PATTERNS["structural_clarity"]["clear_boundaries"]["pattern"],
        text_lower,
        re.IGNORECASE
    )
    
    # Check ambiguous structure
    ambiguous_matches = re.findall(
        STRATEGIC_PATTERNS["structural_clarity"]["ambiguous_structure"]["pattern"],
        text_lower,
        re.IGNORECASE
    )
    
    if len(clear_matches) >= STRATEGIC_PATTERNS["structural_clarity"]["clear_boundaries"]["threshold"]:
        return (
            "clear_boundaries",
            STRATEGIC_PATTERNS["structural_clarity"]["clear_boundaries"]["confidence"],
            [f"Clear structure: {clear_matches[:5]}"]
        )
    elif len(ambiguous_matches) >= STRATEGIC_PATTERNS["structural_clarity"]["ambiguous_structure"]["threshold"]:
        return (
            "ambiguous_structure",
            STRATEGIC_PATTERNS["structural_clarity"]["ambiguous_structure"]["confidence"],
            [f"Ambiguous boundaries: {ambiguous_matches[:5]}"]
        )
    
    return None, 0.0, []


def detect_detail_density(text: str) -> tuple[Optional[str], float, list[str]]:
    """Detect information granularity level."""
    text_lower = text.lower()
    
    # Check high resolution
    high_res_matches = re.findall(
        STRATEGIC_PATTERNS["detail_density"]["high_resolution"]["pattern"],
        text_lower,
        re.IGNORECASE
    )
    
    # Check low resolution
    low_res_matches = re.findall(
        STRATEGIC_PATTERNS["detail_density"]["low_resolution"]["pattern"],
        text_lower,
        re.IGNORECASE
    )
    
    if len(high_res_matches) >= STRATEGIC_PATTERNS["detail_density"]["high_resolution"]["threshold"]:
        return (
            "high_resolution",
            STRATEGIC_PATTERNS["detail_density"]["high_resolution"]["confidence"],
            [f"High detail: {high_res_matches[:5]}"]
        )
    elif len(low_res_matches) >= STRATEGIC_PATTERNS["detail_density"]["low_resolution"]["threshold"]:
        return (
            "low_resolution",
            STRATEGIC_PATTERNS["detail_density"]["low_resolution"]["confidence"],
            [f"High-level approach: {low_res_matches[:5]}"]
        )
    
    return None, 0.0, []


def detect_dimensional_integration(text: str) -> tuple[Optional[str], float, list[str]]:
    """Detect organizational integration level."""
    text_lower = text.lower()
    
    # Check layered depth
    layered_matches = re.findall(
        STRATEGIC_PATTERNS["dimensional_integration"]["layered_depth"]["pattern"],
        text_lower,
        re.IGNORECASE
    )
    
    # Check flat structure
    flat_matches = re.findall(
        STRATEGIC_PATTERNS["dimensional_integration"]["flat_structure"]["pattern"],
        text_lower,
        re.IGNORECASE
    )
    
    if len(layered_matches) >= STRATEGIC_PATTERNS["dimensional_integration"]["layered_depth"]["threshold"]:
        return (
            "layered_depth",
            STRATEGIC_PATTERNS["dimensional_integration"]["layered_depth"]["confidence"],
            [f"Multi-dimensional: {layered_matches[:5]}"]
        )
    elif len(flat_matches) >= STRATEGIC_PATTERNS["dimensional_integration"]["flat_structure"]["threshold"]:
        return (
            "flat_structure",
            STRATEGIC_PATTERNS["dimensional_integration"]["flat_structure"]["confidence"],
            [f"Linear structure: {flat_matches[:5]}"]
        )
    
    return None, 0.0, []


def detect_contrast_differentiation(text: str) -> tuple[Optional[str], float, list[str]]:
    """Detect role clarity vs collaboration emphasis."""
    text_lower = text.lower()
    
    # Check role clarity
    clarity_matches = re.findall(
        STRATEGIC_PATTERNS["contrast_differentiation"]["role_clarity"]["pattern"],
        text_lower,
        re.IGNORECASE
    )
    
    # Check role overlap
    overlap_matches = re.findall(
        STRATEGIC_PATTERNS["contrast_differentiation"]["role_overlap"]["pattern"],
        text_lower,
        re.IGNORECASE
    )
    
    if len(clarity_matches) >= STRATEGIC_PATTERNS["contrast_differentiation"]["role_clarity"]["threshold"]:
        return (
            "role_clarity",
            STRATEGIC_PATTERNS["contrast_differentiation"]["role_clarity"]["confidence"],
            [f"Role clarity: {clarity_matches[:5]}"]
        )
    elif len(overlap_matches) >= STRATEGIC_PATTERNS["contrast_differentiation"]["role_overlap"]["threshold"]:
        return (
            "role_overlap",
            STRATEGIC_PATTERNS["contrast_differentiation"]["role_overlap"]["confidence"],
            [f"Collaborative emphasis: {overlap_matches[:5]}"]
        )
    
    return None, 0.0, []


def detect_observational_mode(text: str) -> tuple[Optional[str], float, list[str]]:
    """Detect adaptive vs fixed strategy approach."""
    text_lower = text.lower()
    
    # Check adaptive strategy
    adaptive_matches = re.findall(
        STRATEGIC_PATTERNS["observational_mode"]["adaptive_strategy"]["pattern"],
        text_lower,
        re.IGNORECASE
    )
    
    # Check fixed execution
    fixed_matches = re.findall(
        STRATEGIC_PATTERNS["observational_mode"]["fixed_execution"]["pattern"],
        text_lower,
        re.IGNORECASE
    )
    
    if len(adaptive_matches) >= STRATEGIC_PATTERNS["observational_mode"]["adaptive_strategy"]["threshold"]:
        return (
            "adaptive_strategy",
            STRATEGIC_PATTERNS["observational_mode"]["adaptive_strategy"]["confidence"],
            [f"Adaptive approach: {adaptive_matches[:5]}"]
        )
    elif len(fixed_matches) >= STRATEGIC_PATTERNS["observational_mode"]["fixed_execution"]["threshold"]:
        return (
            "fixed_execution",
            STRATEGIC_PATTERNS["observational_mode"]["fixed_execution"]["confidence"],
            [f"Fixed approach: {fixed_matches[:5]}"]
        )
    
    return None, 0.0, []


def analyze_strategy_document(strategy_text: str) -> dict:
    """
    Analyze strategy document through microscopy aesthetics dimensions.
    
    Pure deterministic pattern matching - zero LLM cost.
    
    Returns findings with dimension, pattern, confidence, evidence, categorical_family.
    """
    findings = []
    
    # Map detectors to dimensions and categorical families
    detectors = [
        ("structural_clarity", detect_structural_clarity, "objects"),
        ("detail_density", detect_detail_density, "morphisms"),
        ("dimensional_integration", detect_dimensional_integration, "morphisms"),
        ("contrast_differentiation", detect_contrast_differentiation, "constraints"),
        ("observational_mode", detect_observational_mode, "constraints"),
    ]
    
    for dimension, detector_fn, categorical_family in detectors:
        pattern, confidence, evidence = detector_fn(strategy_text)
        
        if pattern and confidence >= 0.6:  # Minimum confidence threshold
            findings.append({
                "dimension": dimension,
                "pattern": pattern,
                "confidence": confidence,
                "evidence": evidence,
                "categorical_family": categorical_family,
            })
    
    return {
        "domain": "microscopy_aesthetics",
        "findings": findings,
        "total_findings": len(findings),
        "methodology": "deterministic_pattern_matching",
        "llm_cost_tokens": 0,
    }


@mcp.tool()
def analyze_strategy_document_tool(strategy_text: str) -> str:
    """
    Analyze a strategy document through microscopy aesthetics structural lens.
    
    Zero LLM cost - pure deterministic pattern matching.
    """
    result = analyze_strategy_document(strategy_text)
    return json.dumps(result, indent=2)


# ============================================================================
# SERVER INFO (Updated for Phase 1A)
# ============================================================================

@mcp.tool()
def get_server_info() -> dict:
    """
    Get information about the Microscopy Aesthetics MCP server.
    
    Returns server metadata including Phase 1A and Phase 2.6 enhancements.
    """
    return {
        "name": "Microscopy Aesthetics",
        "version": SERVER_VERSION,
        "validation_date": VALIDATION_DATE,
        "description": "Microscopy imaging aesthetic vocabulary with trajectory dynamics and rhythmic composition",
        "microscopy_types": list(MICROSCOPY_PROFILES.keys()),
        "capabilities": {
            "layer_1_structure": [
                "list_microscopy_types - Pure taxonomy (7 types)",
                "get_microscopy_profile - Complete profile retrieval"
            ],
            "layer_2_structure": [
                "map_microscopy_parameters - Deterministic parameter mapping",
                "analyze_strategy_document - Tomographic projection",
                "compute_trajectory_between_microscopy_types - RK4 trajectory integration (Phase 1A)",
                "generate_rhythmic_microscopy_sequence - Oscillatory composition (Phase 2.6)",
                "apply_microscopy_rhythmic_preset - Curated rhythmic patterns (Phase 2.6)",
                "list_microscopy_rhythmic_presets - Available preset catalog (Phase 2.6)"
            ],
            "layer_3_structure": [
                "enhance_prompt_with_microscopy - Claude synthesis interface"
            ]
        },
        "morphospace_dimensions": {
            "contrast_intensity": "Visual contrast level (0.0-1.0)",
            "color_saturation": "Monochrome to vibrant color (0.0-1.0)",
            "structural_detail": "Complexity of detail (0.0-1.0)",
            "dimensional_depth": "2D surface to 3D volume (0.0-1.0)",
            "illumination_mode": "Background brightness (0.0-1.0)"
        },
        "compatible_bricks": [
            "aesthetic-dynamics-core - Phase 1A trajectory computation (required for dynamics)",
            "diatom-morphology-mcp - Biological structure aesthetic",
            "nuclear-aesthetic - Energy release aesthetic",
            "origami-aesthetics-mcp - Geometric fold aesthetic"
        ],
        "cost_profile": {
            "layer_1": "0 tokens (pure lookup)",
            "layer_2": "0 tokens (deterministic computation + RK4 integration + oscillation)",
            "layer_3": "~100-200 tokens (Claude synthesis)"
        },
        "phase_1a_enhancements": {
            "dynamics_available": DYNAMICS_AVAILABLE,
            "integration_method": "RK4 (Runge-Kutta 4th order)" if DYNAMICS_AVAILABLE else "Not available",
            "trajectory_features": [
                "Zero-cost morphospace navigation",
                "5D microscopy parameter space",
                "Convergence analysis",
                "Path efficiency metrics",
                "Smooth aesthetic transitions"
            ] if DYNAMICS_AVAILABLE else [],
            "validated_transitions": [
                "electron → fluorescence (monochrome → vibrant color)",
                "darkfield → brightfield (dark → bright background)",
                "phase_contrast → confocal (2D → 3D depth)"
            ] if DYNAMICS_AVAILABLE else []
        },
        "phase_2_6_enhancements": {
            "rhythmic_composition": True,
            "oscillation_patterns": ["sinusoidal", "triangular", "square"],
            "available_presets": len(MICROSCOPY_RHYTHMIC_PRESETS),
            "preset_names": list(MICROSCOPY_RHYTHMIC_PRESETS.keys()),
            "temporal_features": [
                "Focus depth cycling (shallow ↔ deep)",
                "Illumination oscillation (bright ↔ dark field)",
                "Magnification zooming (low ↔ high detail)",
                "Contrast pulsing (high ↔ low)",
                "Mode toggling (2D ↔ 3D)"
            ],
            "use_cases": [
                "Time-lapse visualization sequences",
                "Circadian rhythm studies",
                "Z-stack focus scanning",
                "Multi-modal comparison animations",
                "Dynamic contrast enhancement"
            ]
        }
    }


if __name__ == "__main__":
    mcp.run()
