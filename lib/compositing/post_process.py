"""
Post-Processing Chain

Manages post-processing effects including color grading, glare,
film grain, lens effects, and tone mapping.

Implements REQ-CP-04: Post-Processing Chain.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from pathlib import Path
import json


class EffectType(Enum):
    """Post-processing effect type."""
    COLOR_CORRECTION = "color_correction"
    COLOR_BALANCE = "color_balance"
    CURVES = "curves"
    TONE_MAP = "tone_map"
    GLARE = "glare"
    BLOOM = "bloom"
    FILM_GRAIN = "film_grain"
    VIGNETTE = "vignette"
    LENS_DISTORTION = "lens_distortion"
    CHROMATIC = "chromatic_aberration"
    SHARPEN = "sharpen"
    BLUR = "blur"
    EXPOSURE = "exposure"
    GAMMA = "gamma"
    SATURATION = "saturation"
    CONTRAST = "contrast"


class ColorSpace(Enum):
    """Color space options."""
    SRGB = "srgb"
    LINEAR = "linear"
    FILMIC = "filmic"
    AGX = "agx"
    ACES = "aces"
    REC709 = "rec709"


class ToneMapper(Enum):
    """Tone mapping algorithms."""
    NONE = "none"
    FILMIC = "filmic"
    ACES = "aces"
    AGX = "agx"
    REINHARD = "reinhard"
    UNCHARTED = "uncharted"


# =============================================================================
# DEFAULT CONFIGURATIONS
# =============================================================================

DEFAULT_COLOR_GRADE: Dict[str, Any] = {
    "exposure": 0.0,
    "gamma": 1.0,
    "contrast": 0.0,
    "saturation": 1.0,
    "temperature": 0.0,
    "tint": 0.0,
    "highlights": 0.0,
    "shadows": 0.0,
    "whites": 0.0,
    "blacks": 0.0,
    "vibrance": 0.0,
}

GLARE_PRESETS: Dict[str, Dict[str, Any]] = {
    "ghost": {
        "name": "Ghost Glare",
        "type": "GHOST",
        "quality": "HIGH",
        "color_modulation": 0.0,
        "threshold": 1.0,
        "size": 8,
        "description": "Streaking lens flare effect",
    },
    "streak": {
        "name": "Streak Glare",
        "type": "STREAKS",
        "quality": "HIGH",
        "color_modulation": 0.5,
        "threshold": 0.8,
        "streaks": 4,
        "angle_offset": 45.0,
        "size": 4,
        "description": "Anamorphic streaks",
    },
    "fog_glow": {
        "name": "Fog Glow",
        "type": "FOG_GLOW",
        "quality": "HIGH",
        "threshold": 0.5,
        "size": 9,
        "description": "Soft atmospheric glow",
    },
    "simple_star": {
        "name": "Simple Star",
        "type": "SIMPLE_STAR",
        "quality": "MEDIUM",
        "threshold": 1.0,
        "fade": 0.9,
        "rotate45": True,
        "size": 6,
        "description": "4-point star pattern",
    },
}

COLOR_CORRECTION_DEFAULTS: Dict[str, Any] = {
    "master": {
        "lift": [0.0, 0.0, 0.0],
        "gamma": [1.0, 1.0, 1.0],
        "gain": [1.0, 1.0, 1.0],
    },
    "highlights": {
        "lift": [0.0, 0.0, 0.0],
        "gamma": [1.0, 1.0, 1.0],
        "gain": [1.0, 1.0, 1.0],
    },
    "midtones": {
        "lift": [0.0, 0.0, 0.0],
        "gamma": [1.0, 1.0, 1.0],
        "gain": [1.0, 1.0, 1.0],
    },
    "shadows": {
        "lift": [0.0, 0.0, 0.0],
        "gamma": [1.0, 1.0, 1.0],
        "gain": [1.0, 1.0, 1.0],
    },
    "start": 0.0,
    "end": 1.0,
}

LENS_PRESETS: Dict[str, Dict[str, Any]] = {
    "clean": {
        "name": "Clean Lens",
        "distortion": 0.0,
        "dispersion": 0.0,
        "description": "No lens effects",
    },
    "vintage": {
        "name": "Vintage Lens",
        "distortion": 0.02,
        "dispersion": 0.001,
        "vignette": 0.3,
        "description": "Slight vintage look",
    },
    "anamorphic": {
        "name": "Anamorphic",
        "distortion": -0.05,
        "dispersion": 0.002,
        "squeeze": 2.0,
        "vignette": 0.2,
        "description": "Cinematic anamorphic",
    },
    "damaged": {
        "name": "Damaged Lens",
        "distortion": 0.05,
        "dispersion": 0.003,
        "vignette": 0.5,
        "description": "Damaged/vintage look",
    },
}

FILM_LOOK_PRESETS: Dict[str, Dict[str, Any]] = {
    "neutral": {
        "name": "Neutral",
        "contrast": 0.0,
        "saturation": 1.0,
        "grain": 0.0,
        "description": "Clean digital look",
    },
    "kodak_2383": {
        "name": "Kodak 2383",
        "contrast": 0.15,
        "saturation": 1.1,
        "temperature": -0.05,
        "shadows": [0.02, 0.0, -0.02],
        "highlights": [-0.02, 0.0, 0.03],
        "grain": 0.1,
        "description": "Classic Kodak film stock",
    },
    "fuji_3510": {
        "name": "Fuji 3510",
        "contrast": 0.1,
        "saturation": 1.15,
        "temperature": 0.05,
        "shadows": [-0.01, 0.01, 0.02],
        "highlights": [0.02, 0.0, -0.01],
        "grain": 0.08,
        "description": "Fuji film emulation",
    },
    "cineon": {
        "name": "Cineon Log",
        "contrast": -0.2,
        "saturation": 0.9,
        "gamma": 0.6,
        "grain": 0.05,
        "description": "Cineon log curve",
    },
    "bleach_bypass": {
        "name": "Bleach Bypass",
        "contrast": 0.25,
        "saturation": 0.7,
        "shadows": [0.05, 0.05, 0.05],
        "description": "Desaturated high contrast",
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PostEffect:
    """
    Post-processing effect specification.

    Attributes:
        effect_id: Unique effect identifier
        effect_type: Effect type
        name: Display name
        enabled: Is effect enabled
        order: Processing order
        properties: Effect-specific properties
        input_node: Input node name
        output_node: Output node name
    """
    effect_id: str = ""
    effect_type: str = "color_correction"
    name: str = ""
    enabled: bool = True
    order: int = 0
    properties: Dict[str, Any] = field(default_factory=dict)
    input_node: str = ""
    output_node: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "effect_id": self.effect_id,
            "effect_type": self.effect_type,
            "name": self.name,
            "enabled": self.enabled,
            "order": self.order,
            "properties": self.properties,
            "input_node": self.input_node,
            "output_node": self.output_node,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostEffect":
        """Create from dictionary."""
        return cls(
            effect_id=data.get("effect_id", ""),
            effect_type=data.get("effect_type", "color_correction"),
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            order=data.get("order", 0),
            properties=data.get("properties", {}),
            input_node=data.get("input_node", ""),
            output_node=data.get("output_node", ""),
        )


@dataclass
class ColorGradeConfig:
    """
    Color grading configuration.

    Attributes:
        config_id: Unique configuration identifier
        name: Display name
        exposure: Exposure adjustment
        gamma: Gamma adjustment
        contrast: Contrast adjustment
        saturation: Saturation adjustment
        temperature: Color temperature
        tint: Green-magenta tint
        highlights: Highlights adjustment
        shadows: Shadows adjustment
        whites: Whites adjustment
        blacks: Blacks adjustment
        vibrance: Vibrance adjustment
        lift: Shadow lift (RGB)
        gamma_rgb: Midtone gamma (RGB)
        gain: Highlight gain (RGB)
        curves: RGB curve points
        use_hdr: Use HDR color management
        tone_mapper: Tone mapping algorithm
        view_transform: View transform
    """
    config_id: str = ""
    name: str = ""
    exposure: float = 0.0
    gamma: float = 1.0
    contrast: float = 0.0
    saturation: float = 1.0
    temperature: float = 0.0
    tint: float = 0.0
    highlights: float = 0.0
    shadows: float = 0.0
    whites: float = 0.0
    blacks: float = 0.0
    vibrance: float = 0.0
    lift: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    gamma_rgb: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    gain: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    curves: Dict[str, List[Tuple[float, float]]] = field(default_factory=dict)
    use_hdr: bool = True
    tone_mapper: str = "filmic"
    view_transform: str = "Filmic"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_id": self.config_id,
            "name": self.name,
            "exposure": self.exposure,
            "gamma": self.gamma,
            "contrast": self.contrast,
            "saturation": self.saturation,
            "temperature": self.temperature,
            "tint": self.tint,
            "highlights": self.highlights,
            "shadows": self.shadows,
            "whites": self.whites,
            "blacks": self.blacks,
            "vibrance": self.vibrance,
            "lift": list(self.lift),
            "gamma_rgb": list(self.gamma_rgb),
            "gain": list(self.gain),
            "curves": self.curves,
            "use_hdr": self.use_hdr,
            "tone_mapper": self.tone_mapper,
            "view_transform": self.view_transform,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColorGradeConfig":
        """Create from dictionary."""
        return cls(
            config_id=data.get("config_id", ""),
            name=data.get("name", ""),
            exposure=data.get("exposure", 0.0),
            gamma=data.get("gamma", 1.0),
            contrast=data.get("contrast", 0.0),
            saturation=data.get("saturation", 1.0),
            temperature=data.get("temperature", 0.0),
            tint=data.get("tint", 0.0),
            highlights=data.get("highlights", 0.0),
            shadows=data.get("shadows", 0.0),
            whites=data.get("whites", 0.0),
            blacks=data.get("blacks", 0.0),
            vibrance=data.get("vibrance", 0.0),
            lift=tuple(data.get("lift", [0.0, 0.0, 0.0])),
            gamma_rgb=tuple(data.get("gamma_rgb", [1.0, 1.0, 1.0])),
            gain=tuple(data.get("gain", [1.0, 1.0, 1.0])),
            curves=data.get("curves", {}),
            use_hdr=data.get("use_hdr", True),
            tone_mapper=data.get("tone_mapper", "filmic"),
            view_transform=data.get("view_transform", "Filmic"),
        )


@dataclass
class PostProcessChain:
    """
    Complete post-processing chain.

    Attributes:
        chain_id: Unique chain identifier
        name: Display name
        effects: Ordered list of effects
        color_grade: Color grading configuration
        input_format: Input color space
        output_format: Output color space
        resolution_scale: Resolution multiplier
        denoise: Enable denoising
        denoise_settings: Denoising parameters
    """
    chain_id: str = ""
    name: str = ""
    effects: List[PostEffect] = field(default_factory=list)
    color_grade: Optional[ColorGradeConfig] = None
    input_format: str = "linear"
    output_format: str = "srgb"
    resolution_scale: float = 1.0
    denoise: bool = False
    denoise_settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chain_id": self.chain_id,
            "name": self.name,
            "effects": [e.to_dict() for e in self.effects],
            "color_grade": self.color_grade.to_dict() if self.color_grade else None,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "resolution_scale": self.resolution_scale,
            "denoise": self.denoise,
            "denoise_settings": self.denoise_settings,
        }


# =============================================================================
# POST-PROCESS MANAGER CLASS
# =============================================================================

class PostProcessManager:
    """
    Manages post-processing configurations and chains.

    Provides utilities for creating color grades, effects,
    and complete post-processing chains.

    Usage:
        manager = PostProcessManager()
        grade = manager.create_color_grade("cinematic")
        chain = manager.create_chain("final", color_grade=grade)
        manager.add_effect(chain, "glare", GLARE_PRESETS["fog_glow"])
        manager.generate_compositor_setup(chain, "compositor.json")
    """

    def __init__(self):
        """Initialize post-process manager."""
        self.color_grades: Dict[str, ColorGradeConfig] = {}
        self.chains: Dict[str, PostProcessChain] = {}
        self.effects: Dict[str, PostEffect] = {}
        self._load_presets()

    def _load_presets(self) -> None:
        """Load built-in presets."""
        # Load film look presets as color grades
        for preset_id, preset_data in FILM_LOOK_PRESETS.items():
            grade = ColorGradeConfig(
                config_id=preset_id,
                name=preset_data.get("name", preset_id),
                contrast=preset_data.get("contrast", 0.0),
                saturation=preset_data.get("saturation", 1.0),
                temperature=preset_data.get("temperature", 0.0),
                gamma=preset_data.get("gamma", 1.0),
            )

            # Apply shadow/highlight tints
            shadows = preset_data.get("shadows")
            if shadows:
                grade.shadows = shadows[0] if len(shadows) > 0 else 0.0
                # Store full RGB in lift
                grade.lift = tuple(shadows)

            highlights = preset_data.get("highlights")
            if highlights:
                grade.highlights = highlights[0] if len(highlights) > 0 else 0.0
                # Store full RGB in gain
                grade.gain = tuple(h + 1.0 for h in highlights)

            self.color_grades[preset_id] = grade

    def create_color_grade(
        self,
        config_id: str,
        name: str = "",
        preset: Optional[str] = None,
        **kwargs,
    ) -> ColorGradeConfig:
        """
        Create color grade configuration.

        Args:
            config_id: Unique configuration identifier
            name: Display name
            preset: Base preset to use
            **kwargs: Additional properties

        Returns:
            Created ColorGradeConfig
        """
        if preset and preset in self.color_grades:
            base = self.color_grades[preset]
            grade = ColorGradeConfig(
                config_id=config_id,
                name=name or base.name,
                exposure=kwargs.get("exposure", base.exposure),
                gamma=kwargs.get("gamma", base.gamma),
                contrast=kwargs.get("contrast", base.contrast),
                saturation=kwargs.get("saturation", base.saturation),
                temperature=kwargs.get("temperature", base.temperature),
                tint=kwargs.get("tint", base.tint),
                highlights=kwargs.get("highlights", base.highlights),
                shadows=kwargs.get("shadows", base.shadows),
                whites=kwargs.get("whites", base.whites),
                blacks=kwargs.get("blacks", base.blacks),
                vibrance=kwargs.get("vibrance", base.vibrance),
                lift=kwargs.get("lift", base.lift),
                gamma_rgb=kwargs.get("gamma_rgb", base.gamma_rgb),
                gain=kwargs.get("gain", base.gain),
                use_hdr=kwargs.get("use_hdr", base.use_hdr),
                tone_mapper=kwargs.get("tone_mapper", base.tone_mapper),
            )
        else:
            grade = ColorGradeConfig(
                config_id=config_id,
                name=name or config_id,
                **kwargs,
            )

        self.color_grades[config_id] = grade
        return grade

    def get_color_grade(self, config_id: str) -> Optional[ColorGradeConfig]:
        """Get color grade by ID."""
        return self.color_grades.get(config_id)

    def list_color_grades(self) -> List[ColorGradeConfig]:
        """List all color grades."""
        return list(self.color_grades.values())

    def create_chain(
        self,
        chain_id: str,
        name: str = "",
        color_grade: Optional[ColorGradeConfig] = None,
    ) -> PostProcessChain:
        """
        Create post-processing chain.

        Args:
            chain_id: Unique chain identifier
            name: Display name
            color_grade: Color grade configuration

        Returns:
            Created PostProcessChain
        """
        chain = PostProcessChain(
            chain_id=chain_id,
            name=name or chain_id,
            color_grade=color_grade,
        )

        self.chains[chain_id] = chain
        return chain

    def get_chain(self, chain_id: str) -> Optional[PostProcessChain]:
        """Get chain by ID."""
        return self.chains.get(chain_id)

    def list_chains(self) -> List[PostProcessChain]:
        """List all chains."""
        return list(self.chains.values())

    def create_effect(
        self,
        effect_id: str,
        effect_type: str,
        name: str = "",
        properties: Optional[Dict[str, Any]] = None,
        order: int = 0,
    ) -> PostEffect:
        """
        Create post-processing effect.

        Args:
            effect_id: Unique effect identifier
            effect_type: Effect type
            name: Display name
            properties: Effect properties
            order: Processing order

        Returns:
            Created PostEffect
        """
        effect = PostEffect(
            effect_id=effect_id,
            effect_type=effect_type,
            name=name or effect_id,
            properties=properties or {},
            order=order,
        )

        self.effects[effect_id] = effect
        return effect

    def add_effect(
        self,
        chain: PostProcessChain,
        effect_type: str,
        properties: Optional[Dict[str, Any]] = None,
        order: Optional[int] = None,
    ) -> PostEffect:
        """
        Add effect to chain.

        Args:
            chain: Chain to modify
            effect_type: Effect type
            properties: Effect properties
            order: Processing order (auto if None)

        Returns:
            Created PostEffect
        """
        effect_id = f"{chain.chain_id}_{effect_type}_{len(chain.effects)}"
        if order is None:
            order = len(chain.effects)

        effect = self.create_effect(
            effect_id=effect_id,
            effect_type=effect_type,
            properties=properties,
            order=order,
        )

        chain.effects.append(effect)
        chain.effects.sort(key=lambda e: e.order)
        return effect

    def remove_effect(self, chain: PostProcessChain, effect_id: str) -> bool:
        """
        Remove effect from chain.

        Args:
            chain: Chain to modify
            effect_id: Effect to remove

        Returns:
            Success status
        """
        for i, effect in enumerate(chain.effects):
            if effect.effect_id == effect_id:
                chain.effects.pop(i)
                return True
        return False

    def add_glare(
        self,
        chain: PostProcessChain,
        preset: str = "fog_glow",
        threshold: float = 1.0,
    ) -> PostEffect:
        """
        Add glare effect to chain.

        Args:
            chain: Chain to modify
            preset: Glare preset name
            threshold: Brightness threshold

        Returns:
            Created PostEffect
        """
        preset_data = GLARE_PRESETS.get(preset, GLARE_PRESETS["fog_glow"])
        properties = dict(preset_data)
        properties["threshold"] = threshold

        return self.add_effect(chain, "glare", properties)

    def add_film_grain(
        self,
        chain: PostProcessChain,
        intensity: float = 0.1,
        size: float = 1.0,
    ) -> PostEffect:
        """
        Add film grain effect to chain.

        Args:
            chain: Chain to modify
            intensity: Grain intensity
            size: Grain size

        Returns:
            Created PostEffect
        """
        properties = {
            "intensity": intensity,
            "size": size,
        }

        return self.add_effect(chain, "film_grain", properties)

    def add_vignette(
        self,
        chain: PostProcessChain,
        intensity: float = 0.5,
        radius: float = 0.8,
        softness: float = 0.5,
    ) -> PostEffect:
        """
        Add vignette effect to chain.

        Args:
            chain: Chain to modify
            intensity: Vignette intensity
            radius: Vignette radius
            softness: Edge softness

        Returns:
            Created PostEffect
        """
        properties = {
            "intensity": intensity,
            "radius": radius,
            "softness": softness,
        }

        return self.add_effect(chain, "vignette", properties)

    def add_lens_distortion(
        self,
        chain: PostProcessChain,
        preset: str = "clean",
    ) -> PostEffect:
        """
        Add lens distortion effect to chain.

        Args:
            chain: Chain to modify
            preset: Lens preset name

        Returns:
            Created PostEffect
        """
        preset_data = LENS_PRESETS.get(preset, LENS_PRESETS["clean"])

        return self.add_effect(chain, "lens_distortion", preset_data)

    def generate_compositor_setup(
        self,
        chain: PostProcessChain,
        output_path: str = "",
    ) -> Dict[str, Any]:
        """
        Generate compositor node setup.

        Args:
            chain: Post-processing chain
            output_path: Output path for setup

        Returns:
            Compositor setup specification
        """
        compositor = {
            "chain_id": chain.chain_id,
            "name": chain.name,
            "nodes": [],
            "links": [],
        }

        x_pos = 0
        y_pos = 0
        x_step = 200

        # Add input node
        input_node = {
            "type": "CompositorNodeImage",
            "name": "Input",
            "location": [x_pos, y_pos],
        }
        compositor["nodes"].append(input_node)
        prev_node = "Input"

        # Add denoise if enabled
        if chain.denoise:
            x_pos += x_step
            denoise_node = {
                "type": "CompositorNodeDenoise",
                "name": "Denoise",
                "location": [x_pos, y_pos],
                "properties": chain.denoise_settings,
            }
            compositor["nodes"].append(denoise_node)

            link = {
                "from_node": prev_node,
                "from_socket": "Image",
                "to_node": "Denoise",
                "to_socket": "Image",
            }
            compositor["links"].append(link)
            prev_node = "Denoise"

        # Add color management
        if chain.color_grade:
            x_pos += x_step

            # Color balance node
            cb_node = {
                "type": "CompositorNodeColorBalance",
                "name": "Color_Balance",
                "location": [x_pos, y_pos],
                "properties": {
                    "lift": list(chain.color_grade.lift),
                    "gamma": list(chain.color_grade.gamma_rgb),
                    "gain": list(chain.color_grade.gain),
                },
            }
            compositor["nodes"].append(cb_node)

            link = {
                "from_node": prev_node,
                "from_socket": "Image",
                "to_node": "Color_Balance",
                "to_socket": "Image",
            }
            compositor["links"].append(link)
            prev_node = "Color_Balance"

            # Curves if defined
            if chain.color_grade.curves:
                x_pos += x_step
                curves_node = {
                    "type": "CompositorNodeCurveRGB",
                    "name": "RGB_Curves",
                    "location": [x_pos, y_pos],
                    "properties": {
                        "curves": chain.color_grade.curves,
                    },
                }
                compositor["nodes"].append(curves_node)

                link = {
                    "from_node": prev_node,
                    "from_socket": "Image",
                    "to_node": "RGB_Curves",
                    "to_socket": "Image",
                }
                compositor["links"].append(link)
                prev_node = "RGB_Curves"

        # Add effects in order
        for effect in sorted(chain.effects, key=lambda e: e.order):
            x_pos += x_step

            node_type_map = {
                "glare": "CompositorNodeGlare",
                "film_grain": "CompositorNodeValToRGB",
                "vignette": "CompositorNodeEllipseMask",
                "lens_distortion": "CompositorNodeLensdist",
                "color_correction": "CompositorNodeColorCorrection",
                "blur": "CompositorNodeBlur",
                "sharpen": "CompositorNodeFilter",
            }

            node_type = node_type_map.get(effect.effect_type, "CompositorNodeFilter")

            effect_node = {
                "type": node_type,
                "name": effect.name or effect.effect_id,
                "location": [x_pos, y_pos],
                "properties": effect.properties,
            }
            compositor["nodes"].append(effect_node)

            link = {
                "from_node": prev_node,
                "from_socket": "Image",
                "to_node": effect_node["name"],
                "to_socket": "Image",
            }
            compositor["links"].append(link)
            prev_node = effect_node["name"]

        # Add output node
        x_pos += x_step
        output_node = {
            "type": "CompositorNodeComposite",
            "name": "Output",
            "location": [x_pos, y_pos],
        }
        compositor["nodes"].append(output_node)

        link = {
            "from_node": prev_node,
            "from_socket": "Image",
            "to_node": "Output",
            "to_socket": "Image",
        }
        compositor["links"].append(link)

        if output_path:
            with open(output_path, "w") as f:
                json.dump(compositor, f, indent=2)

        return compositor

    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "total_color_grades": len(self.color_grades),
            "total_chains": len(self.chains),
            "total_effects": len(self.effects),
            "presets_loaded": list(FILM_LOOK_PRESETS.keys()),
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_color_grade(
    name: str,
    preset: Optional[str] = None,
    **kwargs,
) -> ColorGradeConfig:
    """
    Create color grade configuration.

    Args:
        name: Grade name
        preset: Base preset
        **kwargs: Additional properties

    Returns:
        ColorGradeConfig
    """
    manager = PostProcessManager()
    return manager.create_color_grade(
        config_id=name.lower().replace(" ", "_"),
        name=name,
        preset=preset,
        **kwargs,
    )


def create_glare_effect(
    preset: str = "fog_glow",
    threshold: float = 1.0,
) -> PostEffect:
    """
    Create glare effect.

    Args:
        preset: Glare preset
        threshold: Brightness threshold

    Returns:
        PostEffect
    """
    manager = PostProcessManager()
    return manager.create_effect(
        effect_id=f"glare_{preset}",
        effect_type="glare",
        name=f"Glare ({preset})",
        properties={"preset": preset, "threshold": threshold},
    )


def create_film_grain(
    intensity: float = 0.1,
    size: float = 1.0,
) -> PostEffect:
    """
    Create film grain effect.

    Args:
        intensity: Grain intensity
        size: Grain size

    Returns:
        PostEffect
    """
    manager = PostProcessManager()
    return manager.create_effect(
        effect_id="film_grain",
        effect_type="film_grain",
        name="Film Grain",
        properties={"intensity": intensity, "size": size},
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "EffectType",
    "ColorSpace",
    "ToneMapper",
    # Data classes
    "PostEffect",
    "ColorGradeConfig",
    "PostProcessChain",
    # Constants
    "DEFAULT_COLOR_GRADE",
    "GLARE_PRESETS",
    "COLOR_CORRECTION_DEFAULTS",
    "LENS_PRESETS",
    "FILM_LOOK_PRESETS",
    # Classes
    "PostProcessManager",
    # Functions
    "create_color_grade",
    "create_glare_effect",
    "create_film_grain",
]
