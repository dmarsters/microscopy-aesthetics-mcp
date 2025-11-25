from fastmcp import FastMCP
import json
from typing import Optional

mcp = FastMCP("microscopy-aesthetics")

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
            "low": "broad particles and structures glowing against dark field with visible scatter patterns",
            "medium": "individual specimen edge illumination with clear rim lighting and defined contours",
            "high": "molecular-scale structure revealed through scattered light with fine edge detail and transparency effects"
        }
    },
    "multiphoton": {
        "display_name": "Multiphoton",
        "description": "Deep tissue penetration with autofluorescence and minimal phototoxicity appearance",
        "structure": ["deep tissue penetration", "autofluorescence structures", "intact tissue architecture", "minimal photodamage"],
        "material": ["endogenous fluorophores", "intact biological matrices", "native tissue layers", "minimal perturbation"],
        "color": ["red autofluorescence", "green intrinsic signals", "infrared penetration tones", "warm tissue glows"],
        "texture": ["natural tissue texture", "preserved architecture", "minimal blur", "native organization"],
        "composition": ["three-dimensional depth", "layered tissue", "preserved structure", "volumetric clarity"],
        "style": ["multiphoton microscopy", "two-photon excitation", "deep tissue imaging"],
        "quality": ["deep penetration", "minimal phototoxicity", "native fluorescence", "three-dimensional detail"],
        "mood": ["biological authenticity", "preserved vitality", "native structure", "gentle illumination"],
        "examples": ["in vivo imaging", "intact tissue stacks", "neuronal architecture", "vascular networks"],
        "color_palette": {
            "scientific": ["red autofluorescence", "green intrinsic signals", "warm tissue tones"],
            "artistic": ["warm biological glows", "preserved color authenticity", "soft luminescence"],
            "monochrome": ["warm grayscale", "golden-toned depth"]
        },
        "magnification_feel": {
            "low": "broad tissue architecture with deep volumetric penetration showing interconnected structures",
            "medium": "cellular and organelle detail within preserved tissue context with depth-resolved clarity",
            "high": "subcellular organelles and molecular structures within intact biological environment"
        }
    }
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
    
    Args:
        base_prompt: The original image description to enhance
        microscopy_type: Type of microscopy (fluorescence, electron, phase_contrast, confocal, brightfield, darkfield, multiphoton)
        magnification: Scale level - low (tissue), medium (cellular), high (subcellular/molecular)
        color_palette: Color mode - scientific (authentic), artistic (stylized), monochrome
        aesthetic_strength: How prominently to apply characteristics - subtle (2-3), balanced (4-5), strong (6+)
    
    Returns:
        Enhanced prompt (60-80 words) with microscopy aesthetic vocabulary
    """
    
    microscopy_type = microscopy_type.lower().replace(" ", "_")
    
    if microscopy_type not in MICROSCOPY_PROFILES:
        available = ", ".join(MICROSCOPY_PROFILES.keys())
        return f"Error: Unknown microscopy type '{microscopy_type}'. Available types: {available}"
    
    profile = MICROSCOPY_PROFILES[microscopy_type]
    
    # Select characteristics based on strength
    strength_map = {
        "subtle": 2,
        "balanced": 4,
        "strong": 6
    }
    num_characteristics = strength_map.get(aesthetic_strength.lower(), 4)
    
    # Build characteristic pool
    characteristics = []
    characteristics.extend(profile["structure"][:2])  # Always include structure
    characteristics.extend(profile["material"][:1])
    characteristics.extend(profile["color"][:1])
    characteristics.extend(profile["texture"][:1])
    
    if num_characteristics >= 5:
        characteristics.extend(profile["composition"][:1])
    if num_characteristics >= 6:
        characteristics.extend(profile["style"][:1])
    
    # Get magnification-appropriate language
    mag_key = magnification.lower()
    if mag_key not in profile["magnification_feel"]:
        mag_key = "medium"
    mag_language = profile["magnification_feel"][mag_key]
    
    # Get color palette selection
    color_key = color_palette.lower()
    if color_key not in profile["color_palette"]:
        color_key = "scientific"
    color_selection = profile["color_palette"][color_key]
    
    # Build enhanced prompt
    enhanced = f"{base_prompt}, rendered with {profile['display_name'].lower()} microscopy aesthetics. "
    enhanced += f"Features {', '.join(characteristics[:num_characteristics])}. "
    enhanced += f"Color palette emphasizes {color_selection[0]}. "
    enhanced += f"Captures {mag_language}. "
    enhanced += "Highly detailed 8k scientific visualization."
    
    # Trim to 60-80 words and ensure natural flow
    words = enhanced.split()
    if len(words) > 80:
        enhanced = " ".join(words[:80]) + "."
    
    return enhanced.strip()


@mcp.tool()
def list_microscopy_types() -> str:
    """
    List all available microscopy types with brief descriptions.
    
    Returns:
        JSON string with all available microscopy profiles
    """
    types_info = {}
    for key, profile in MICROSCOPY_PROFILES.items():
        types_info[key] = {
            "display_name": profile["display_name"],
            "description": profile["description"]
        }
    return json.dumps(types_info, indent=2)


@mcp.tool()
def get_microscopy_profile(microscopy_type: str) -> str:
    """
    Get the complete aesthetic vocabulary for a specific microscopy type.
    
    Args:
        microscopy_type: The microscopy type to inspect (e.g., 'fluorescence', 'electron')
    
    Returns:
        Complete profile with all aesthetic characteristics
    """
    microscopy_type = microscopy_type.lower().replace(" ", "_")
    
    if microscopy_type not in MICROSCOPY_PROFILES:
        available = ", ".join(MICROSCOPY_PROFILES.keys())
        return f"Error: Unknown microscopy type '{microscopy_type}'. Available types: {available}"
    
    profile = MICROSCOPY_PROFILES[microscopy_type]
    return json.dumps(profile, indent=2)


@mcp.tool()
def suggest_microscopy_type(description: str) -> str:
    """
    Suggest matching microscopy types from a natural language description.
    
    Args:
        description: Natural language description of desired aesthetic
        
    Returns:
        Ranked suggestions with match explanations
    """
    description_lower = description.lower()
    
    # Keyword mapping for suggestions
    keyword_map = {
        "fluorescence": ["glow", "luminous", "neon", "fluorescent", "bright", "vivid", "color", "channel"],
        "electron": ["detail", "ultra", "nanoscale", "texture", "rough", "metallic", "relief", "shadow"],
        "phase_contrast": ["transparent", "ghost", "ethereal", "refract", "halo", "living", "natural", "unstained"],
        "confocal": ["3d", "three-dimensional", "depth", "volumetric", "layer", "optical section", "stack", "precise"],
        "brightfield": ["tissue", "histology", "pathology", "stain", "medical", "diagnostic", "anatomy", "section"],
        "darkfield": ["contrast", "dramatic", "dark", "rim", "light", "particle", "edge", "theatrical"],
        "multiphoton": ["deep", "penetration", "intact", "native", "autofluorescence", "in vivo", "biological", "preserved"]
    }
    
    scores = {}
    for microscopy_type, keywords in keyword_map.items():
        score = sum(1 for keyword in keywords if keyword in description_lower)
        scores[microscopy_type] = score
    
    # Sort by score
    sorted_suggestions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    suggestions = []
    for microscopy_type, score in sorted_suggestions[:3]:
        if score > 0:
            profile = MICROSCOPY_PROFILES[microscopy_type]
            suggestions.append({
                "type": microscopy_type,
                "display_name": profile["display_name"],
                "confidence": "high" if score >= 3 else "medium" if score >= 1 else "low",
                "reason": f"Matched {score} aesthetic keywords"
            })
    
    if not suggestions:
        # Return default if no matches
        suggestions.append({
            "type": "brightfield",
            "display_name": "Brightfield",
            "confidence": "low",
            "reason": "No strong matches; brightfield recommended as versatile default"
        })
    
    return json.dumps(suggestions, indent=2)


if __name__ == "__main__":
    mcp.run()
