"""
Render Profiles System

Profiles drive settings. Same artifact = same preview.
This module provides a unified profile system for render configuration.

Design:
- Engine-agnostic RenderProfile dataclass
- YAML-based preset loading
- Scene extraction for profile creation

Usage:
    from lib.render.profiles import get_profile, apply_profile

    # Get a preset profile
    profile = get_profile('production')
    apply_profile(profile)

    # Create custom profile
    custom = RenderProfile(
        name='custom',
        engine='CYCLES',
        resolution=(1920, 1080),
        samples=256,
    )
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import yaml
from pathlib import Path


class RenderEngine(Enum):
    """Supported render engines."""
    CYCLES = "CYCLES"
    EEVEE_NEXT = "BLENDER_EEVEE_NEXT"
    WORKBENCH = "BLENDER_WORKBENCH"


class QualityTier(Enum):
    """Quality tier identifiers."""
    PREVIEW = "preview"
    DRAFT = "draft"
    PRODUCTION = "production"
    ARCHIVE = "archive"


@dataclass
class RenderProfile:
    """
    Unified render profile for engine-agnostic configuration.

    Same profile = same render output regardless of engine.
    Engine-specific settings are handled by apply functions.

    Attributes:
        name: Profile identifier
        engine: Render engine (CYCLES, EEVEE_NEXT, WORKBENCH)
        resolution: (width, height) tuple
        samples: Render samples (Cycles) or TAA samples (EEVEE)
        quality_tier: Quality classification
        denoise: Enable denoising
        transparent_bg: Film transparent for compositing
        motion_blur: Enable motion blur
        motion_blur_shutter: Shutter opening for motion blur
        fps: Frames per second
        output_format: File format (PNG, OPEN_EXR, etc.)
        exr_codec: EXR compression codec
        passes: List of render passes to enable
        metadata: Additional engine-specific settings
    """
    name: str
    engine: str = "CYCLES"
    resolution: Tuple[int, int] = (1920, 1080)
    samples: int = 64
    quality_tier: str = "production"
    denoise: bool = True
    transparent_bg: bool = False
    motion_blur: bool = False
    motion_blur_shutter: float = 0.5
    fps: int = 24
    output_format: str = "PNG"
    exr_codec: str = "ZIP"
    passes: List[str] = field(default_factory=lambda: ["combined"])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "name": self.name,
            "engine": self.engine,
            "resolution": list(self.resolution),
            "samples": self.samples,
            "quality_tier": self.quality_tier,
            "denoise": self.denoise,
            "transparent_bg": self.transparent_bg,
            "motion_blur": self.motion_blur,
            "motion_blur_shutter": self.motion_blur_shutter,
            "fps": self.fps,
            "output_format": self.output_format,
            "exr_codec": self.exr_codec,
            "passes": self.passes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RenderProfile":
        """Create profile from dictionary."""
        resolution = data.get("resolution", [1920, 1080])
        if isinstance(resolution, list):
            resolution = tuple(resolution)

        return cls(
            name=data.get("name", "unnamed"),
            engine=data.get("engine", "CYCLES"),
            resolution=resolution,
            samples=data.get("samples", 64),
            quality_tier=data.get("quality_tier", "production"),
            denoise=data.get("denoise", True),
            transparent_bg=data.get("transparent_bg", False),
            motion_blur=data.get("motion_blur", False),
            motion_blur_shutter=data.get("motion_blur_shutter", 0.5),
            fps=data.get("fps", 24),
            output_format=data.get("output_format", "PNG"),
            exr_codec=data.get("exr_codec", "ZIP"),
            passes=data.get("passes", ["combined"]),
            metadata=data.get("metadata", {}),
        )


# =============================================================================
# BUILT-IN PROFILES
# =============================================================================

PROFILES: Dict[str, RenderProfile] = {
    # Preview profiles (fast iteration)
    "viewport": RenderProfile(
        name="viewport",
        engine="BLENDER_EEVEE_NEXT",
        resolution=(1280, 720),
        samples=1,
        quality_tier="preview",
        denoise=False,
        passes=["combined"],
        metadata={"taa_samples": 8, "raytracing": False},
    ),
    "preview": RenderProfile(
        name="preview",
        engine="BLENDER_EEVEE_NEXT",
        resolution=(1280, 720),
        samples=1,
        quality_tier="preview",
        denoise=True,
        passes=["combined"],
        metadata={"taa_samples": 16, "raytracing": False},
    ),

    # Draft profiles (quick renders)
    "draft": RenderProfile(
        name="draft",
        engine="BLENDER_EEVEE_NEXT",
        resolution=(1920, 1080),
        samples=1,
        quality_tier="draft",
        denoise=True,
        motion_blur=True,
        passes=["combined", "depth"],
        metadata={"taa_samples": 32, "raytracing": True},
    ),
    "eevee_draft": RenderProfile(
        name="eevee_draft",
        engine="BLENDER_EEVEE_NEXT",
        resolution=(1920, 1080),
        samples=1,
        quality_tier="draft",
        denoise=True,
        passes=["combined"],
        metadata={"taa_samples": 32, "raytracing": True},
    ),

    # Production profiles
    "production": RenderProfile(
        name="production",
        engine="CYCLES",
        resolution=(1920, 1080),
        samples=256,
        quality_tier="production",
        denoise=True,
        motion_blur=True,
        transparent_bg=True,
        output_format="OPEN_EXR_MULTILAYER",
        passes=["combined", "depth", "normal", "cryptomatte_object"],
        metadata={"adaptive_sampling": True, "path_guiding": True},
    ),
    "cycles_production": RenderProfile(
        name="cycles_production",
        engine="CYCLES",
        resolution=(1920, 1080),
        samples=256,
        quality_tier="production",
        denoise=True,
        motion_blur=True,
        transparent_bg=True,
        output_format="OPEN_EXR_MULTILAYER",
        exr_codec="ZIP",
        passes=["combined", "depth", "normal", "vector", "cryptomatte_object"],
        metadata={"adaptive_sampling": True, "adaptive_threshold": 0.01, "path_guiding": True},
    ),
    "eevee_production": RenderProfile(
        name="eevee_production",
        engine="BLENDER_EEVEE_NEXT",
        resolution=(1920, 1080),
        samples=1,
        quality_tier="production",
        denoise=True,
        motion_blur=True,
        transparent_bg=True,
        output_format="OPEN_EXR",
        passes=["combined", "depth", "normal"],
        metadata={"taa_samples": 64, "raytracing": True, "raytracing_samples": 4},
    ),

    # 4K Production
    "4k_production": RenderProfile(
        name="4k_production",
        engine="CYCLES",
        resolution=(3840, 2160),
        samples=512,
        quality_tier="production",
        denoise=True,
        motion_blur=True,
        transparent_bg=True,
        output_format="OPEN_EXR_MULTILAYER",
        passes=["combined", "depth", "normal", "vector", "cryptomatte_object", "cryptomatte_material"],
        metadata={"adaptive_sampling": True, "path_guiding": True},
    ),

    # Archive profile (maximum quality)
    "archive": RenderProfile(
        name="archive",
        engine="CYCLES",
        resolution=(3840, 2160),
        samples=1024,
        quality_tier="archive",
        denoise=True,
        motion_blur=True,
        transparent_bg=True,
        output_format="OPEN_EXR_MULTILAYER",
        exr_codec="PIZ",
        passes=["combined", "depth", "normal", "vector", "uv", "cryptomatte_object", "cryptomatte_material", "emission", "shadow", "ao"],
        metadata={"adaptive_sampling": True, "path_guiding": True, "volume_samples": 4},
    ),

    # Product visualization
    "product_hero": RenderProfile(
        name="product_hero",
        engine="CYCLES",
        resolution=(2048, 2048),
        samples=512,
        quality_tier="production",
        denoise=True,
        transparent_bg=True,
        output_format="OPEN_EXR",
        passes=["combined", "depth", "cryptomatte_object"],
        metadata={"adaptive_sampling": True, "caustics": True},
    ),

    # Animation
    "animation": RenderProfile(
        name="animation",
        engine="CYCLES",
        resolution=(1920, 1080),
        samples=128,
        quality_tier="production",
        denoise=True,
        motion_blur=True,
        motion_blur_shutter=0.5,
        fps=24,
        output_format="PNG",
        passes=["combined"],
        metadata={"adaptive_sampling": True},
    ),

    # Turntable
    "turntable": RenderProfile(
        name="turntable",
        engine="CYCLES",
        resolution=(2048, 2048),
        samples=256,
        quality_tier="production",
        denoise=True,
        transparent_bg=True,
        output_format="PNG",
        passes=["combined", "cryptomatte_object"],
        metadata={"adaptive_sampling": True},
    ),
}


# =============================================================================
# PROFILE FUNCTIONS
# =============================================================================

def get_profile(name: str) -> RenderProfile:
    """
    Get a render profile by name.

    Args:
        name: Profile name (e.g., 'preview', 'production', 'cycles_production')

    Returns:
        RenderProfile instance

    Raises:
        KeyError: If profile not found
    """
    if name not in PROFILES:
        available = list(PROFILES.keys())
        raise KeyError(f"Profile '{name}' not found. Available: {available}")
    return PROFILES[name]


def get_all_profiles() -> Dict[str, RenderProfile]:
    """Get all available profiles."""
    return PROFILES.copy()


def apply_profile(profile: RenderProfile) -> bool:
    """
    Apply a render profile to the current scene.

    Args:
        profile: RenderProfile instance

    Returns:
        True on success

    Raises:
        RuntimeError: If Blender is not available
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available. This function must be run from within Blender.")

    scene = bpy.context.scene

    # Set engine
    engine_map = {
        "CYCLES": "CYCLES",
        "EEVEE_NEXT": "BLENDER_EEVEE_NEXT",
        "BLENDER_EEVEE_NEXT": "BLENDER_EEVEE_NEXT",
        "WORKBENCH": "BLENDER_WORKBENCH",
        "BLENDER_WORKBENCH": "BLENDER_WORKBENCH",
    }
    scene.render.engine = engine_map.get(profile.engine, profile.engine)

    # Set resolution
    scene.render.resolution_x = profile.resolution[0]
    scene.render.resolution_y = profile.resolution[1]
    scene.render.resolution_percentage = 100

    # Set frame rate
    scene.render.fps = profile.fps

    # Motion blur
    scene.render.use_motion_blur = profile.motion_blur
    if profile.motion_blur:
        scene.render.motion_blur_shutter = profile.motion_blur_shutter

    # Film transparent
    scene.render.film_transparent = profile.transparent_bg

    # Output format
    format_map = {
        "PNG": "PNG",
        "OPEN_EXR": "OPEN_EXR",
        "OPEN_EXR_MULTILAYER": "OPEN_EXR_MULTILAYER",
        "JPEG": "JPEG",
        "TIFF": "TIFF",
    }
    scene.render.image_settings.file_format = format_map.get(profile.output_format, profile.output_format)

    if "EXR" in profile.output_format:
        scene.render.image_settings.exr_codec = profile.exr_codec
        scene.render.image_settings.color_depth = "32"

    # Engine-specific settings
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = profile.samples
        scene.cycles.use_denoising = profile.denoise

        # Adaptive sampling
        if profile.metadata.get("adaptive_sampling"):
            scene.cycles.use_adaptive_sampling = True
            scene.cycles.adaptive_threshold = profile.metadata.get("adaptive_threshold", 0.01)

        # Path guiding
        if profile.metadata.get("path_guiding"):
            scene.cycles.use_guiding = True

    elif scene.render.engine == "BLENDER_EEVEE_NEXT":
        # TAA samples
        taa_samples = profile.metadata.get("taa_samples", 16)
        scene.eevee.taa_render_samples = taa_samples

        # Raytracing
        if profile.metadata.get("raytracing"):
            scene.eevee.use_raytracing = True
            scene.eevee.raytracing_method = "PROBE"
            scene.eevee.raytracing_samples = profile.metadata.get("raytracing_samples", 4)

    # Configure passes
    view_layer = bpy.context.view_layer

    # Disable all passes first
    for attr in dir(view_layer):
        if attr.startswith("use_pass_"):
            try:
                setattr(view_layer, attr, False)
            except AttributeError:
                pass

    # Enable requested passes
    pass_map = {
        "combined": "use_pass_combined",
        "depth": "use_pass_z",
        "normal": "use_pass_normal",
        "vector": "use_pass_vector",
        "uv": "use_pass_uv",
        "emission": "use_pass_emit",
        "shadow": "use_pass_shadow",
        "ao": "use_pass_ambient_occlusion",
        "cryptomatte_object": "use_pass_cryptomatte_object",
        "cryptomatte_material": "use_pass_cryptomatte_material",
    }

    for pass_name in profile.passes:
        attr = pass_map.get(pass_name)
        if attr and hasattr(view_layer, attr):
            setattr(view_layer, attr, True)

    # Cryptomatte setup
    if any(p in profile.passes for p in ["cryptomatte_object", "cryptomatte_material"]):
        view_layer.cryptomatte_levels = 6
        view_layer.use_pass_cryptomatte_accurate = True

    return True


def create_profile_from_scene(name: str) -> RenderProfile:
    """
    Create a profile from current scene settings.

    Args:
        name: Name for the new profile

    Returns:
        RenderProfile with current scene settings
    """
    try:
        import bpy
    except ImportError:
        raise RuntimeError("Blender (bpy) is not available.")

    scene = bpy.context.scene
    view_layer = bpy.context.view_layer

    # Determine engine
    engine = scene.render.engine
    if engine == "BLENDER_EEVEE_NEXT":
        engine = "EEVEE_NEXT"

    # Get samples based on engine
    samples = 64
    metadata = {}
    if engine == "CYCLES":
        samples = scene.cycles.samples
        metadata["adaptive_sampling"] = scene.cycles.use_adaptive_sampling
    elif engine == "EEVEE_NEXT":
        samples = 1
        metadata["taa_samples"] = scene.eevee.taa_render_samples
        metadata["raytracing"] = scene.eevee.use_raytracing

    # Detect enabled passes
    passes = []
    pass_map = {
        "use_pass_combined": "combined",
        "use_pass_z": "depth",
        "use_pass_normal": "normal",
        "use_pass_vector": "vector",
        "use_pass_uv": "uv",
        "use_pass_emit": "emission",
        "use_pass_shadow": "shadow",
        "use_pass_ambient_occlusion": "ao",
        "use_pass_cryptomatte_object": "cryptomatte_object",
        "use_pass_cryptomatte_material": "cryptomatte_material",
    }

    for attr, pass_name in pass_map.items():
        if hasattr(view_layer, attr) and getattr(view_layer, attr, False):
            passes.append(pass_name)

    return RenderProfile(
        name=name,
        engine=engine,
        resolution=(scene.render.resolution_x, scene.render.resolution_y),
        samples=samples,
        quality_tier="custom",
        denoise=scene.cycles.use_denoising if engine == "CYCLES" else False,
        transparent_bg=scene.render.film_transparent,
        motion_blur=scene.render.use_motion_blur,
        motion_blur_shutter=scene.render.motion_blur_shutter,
        fps=scene.render.fps,
        output_format=scene.render.image_settings.file_format,
        exr_codec=scene.render.image_settings.exr_codec if "EXR" in scene.render.image_settings.file_format else "ZIP",
        passes=passes,
        metadata=metadata,
    )


def load_profiles_from_yaml(path: Path) -> Dict[str, RenderProfile]:
    """
    Load profiles from a YAML file.

    Args:
        path: Path to YAML file

    Returns:
        Dictionary of profile name -> RenderProfile
    """
    if not path.exists():
        return {}

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    profiles = {}
    for name, profile_data in data.get("profiles", {}).items():
        profile_data["name"] = name
        profiles[name] = RenderProfile.from_dict(profile_data)

    return profiles


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "RenderProfile",
    "RenderEngine",
    "QualityTier",
    "get_profile",
    "get_all_profiles",
    "apply_profile",
    "create_profile_from_scene",
    "load_profiles_from_yaml",
    "PROFILES",
]
