"""
Render Profiles System

Provides pre-configured render profiles for different quality targets
and use cases.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
from enum import Enum
import yaml


class RenderEngine(Enum):
    """Available render engines."""
    CYCLES = "cycles"
    EEVEE = "eevee"
    WORKBENCH = "workbench"


class RenderQuality(Enum):
    """Render quality presets."""
    PREVIEW = "preview"
    FINAL = "final"
    PRODUCTION = "production"


@dataclass
class RenderProfile:
    """
    Complete render profile configuration.

    Attributes:
        name: Profile name
        engine: Render engine
        quality: Quality preset
        samples: Sample count
        max_bounces: Maximum light bounces
        resolution_x: Horizontal resolution
        resolution_y: Vertical resolution
        resolution_percentage: Resolution scale factor (0-100)
        use_motion_blur: Enable motion blur
        motion_blur_samples: Motion blur samples
        motion_blur_shutter: Motion blur shutter
        use_denoising: Use denoising
        denoiser_strength: Denoiser strength
        use_compositing: Enable compositing
        transparent_background: Transparent background
        output_format: Output format (PNG, JPEG, EXR)
        color_depth: Color depth (8, 16, 32)
        filmic_format: Filmic format (for EXR)
        custom_settings: Additional custom settings
    """
    name: str =    engine: RenderEngine = RenderEngine.CYCLES
    quality: RenderQuality = RenderQuality.FINAL
    samples: int = 128
    max_bounces: int = 128
    resolution_x: int = 1920
    resolution_y: int = 1080
    resolution_percentage: int = 100
    use_motion_blur: bool = True
    motion_blur_samples: int = 8
    motion_blur_shutter: float = 0.5
    use_denoising: bool = True
    denoiser_strength: float = 0.5
    use_compositing: bool = True
    transparent_background: bool = False
    output_format: str = "PNG"
    color_depth: int = 8
    filmic_format: Optional[str] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)


# Default profiles
DEFAULT_RENDER_PROFILES: Dict[str, RenderProfile] = {
    "preview_cycles": RenderProfile(
        name="Preview (Cycles)",
        engine=RenderEngine.CYCLES,
        quality=RenderQuality.PREVIEW,
        samples=16,
        max_bounces=16,
        resolution_x=1280,
        resolution_y=720,
        resolution_percentage=50,
        use_motion_blur=False,
        use_denoising=True,
        denoiser_strength=0.25,
        use_compositing=False,
    ),
    "preview_eevee": RenderProfile(
        name="Preview (EEVEE)",
        engine=RenderEngine.EEVEE,
        quality=RenderQuality.PREVIEW,
        samples=1,  # Not applicable
        resolution_x=1280,
        resolution_y=720,
        resolution_percentage=50,
        use_motion_blur=False,
        use_denoising=True,
        denoiser_strength=0.25,
    ),
    "final_4k": RenderProfile(
        name="Final 4K",
        engine=RenderEngine.CYCLES,
        quality=RenderQuality.FINAL,
        samples=256,
        max_bounces=256,
        resolution_x=3840,
        resolution_y=2160,
        resolution_percentage=100,
        use_motion_blur=True,
        motion_blur_samples=16,
        motion_blur_shutter=0.0,
        use_denoising=True,
        denoiser_strength=0.5,
        use_compositing=True,
    ),
    "final_8k": RenderProfile(
        name="Final 8K",
        engine=RenderEngine.CYCLES,
        quality=RenderQuality.FINAL,
        samples=512,
        max_bounces=512,
        resolution_x=7680,
        resolution_y=4320,
        resolution_percentage=100,
        use_motion_blur=True,
        motion_blur_samples=32,
        motion_blur_shutter=1.0,
        use_denoising=True,
        denoiser_strength=0.5,
        use_compositing=True,
    ),
    "production": RenderProfile(
        name="Production",
        engine=RenderEngine.CYCLES,
        quality=RenderQuality.PRODUCTION,
        samples=1024,
        max_bounces=1024,
        resolution_x=3840,
        resolution_y=2160,
        resolution_percentage=100,
        use_motion_blur=True,
        motion_blur_samples=32,
        motion_blur_shutter=1.0,
        use_denoising=True,
        denoiser_strength=0.75,
        use_compositing=True,
        output_format="EXR",
        color_depth=32,
    ),
    "turnaround_animation": RenderProfile(
        name="Turnaround Animation",
        engine=RenderEngine.CYCLES,
        quality=RenderQuality.PREVIEW,
        samples=32,
        resolution_x=1920,
        resolution_y=1080,
        resolution_percentage=50,
        use_motion_blur=False,
        use_denoising=False,
    ),
}


def load_render_profile(name: str) -> RenderProfile:
    """
    Load render profile by name.

    Args:
        name: Profile name (e.g., "final_4k")

    Returns:
        RenderProfile instance

    Raises:
        KeyError: If profile not found
    """
    if name not in DEFAULT_RENDER_PROFILES:
        raise KeyError(
            f"Render profile '{name}' not found. "
            f"Available: {list(DEFAULT_RENDER_PROFILES.keys())}"
        )
    return DEFAULT_RENDER_PROFILES[name]


def save_render_profile(profile: RenderProfile, path: str) -> None:
    """
    Save render profile to YAML file.

    Args:
        profile: RenderProfile to save
        path: Output file path
    """
    data = {
        'name': profile.name,
        'engine': profile.engine.value,
        'quality': profile.quality.value,
        'samples': profile.samples,
        'max_bounces': profile.max_bounces,
        'resolution': [profile.resolution_x, profile.resolution_y],
        'resolution_percentage': profile.resolution_percentage,
        'motion_blur': {
            'enabled': profile.use_motion_blur,
            'samples': profile.motion_blur_samples,
            'shutter': profile.motion_blur_shutter,
        },
        'denoising': {
            'enabled': profile.use_denoising,
            'strength': profile.denoiser_strength,
        },
        'compositing': {
            'enabled': profile.use_compositing,
            'transparent': profile.transparent_background,
        },
        'output': {
            'format': profile.output_format,
            'color_depth': profile.color_depth,
            'filmic': profile.filmic_format,
        },
    }

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)


def list_render_profiles() -> List[str]:
    """
    List available render profile names.

    Returns:
        List of profile names
    """
    return list(DEFAULT_RENDER_PROFILES.keys())


def apply_render_profile(
    scene: Any,
    profile: RenderProfile,
) -> Dict[str, Any]:
    """
    Apply render profile to scene.

    Args:
        scene: Blender scene
        profile: RenderProfile to apply

    Returns:
        Dictionary of applied settings
    """
    settings = {}

    try:
        import bpy
    except ImportError:
        return {'error': 'Blender not available'}

    # Resolution
    scene.render.resolution_x = profile.resolution_x
    scene.render.resolution_y = profile.resolution_y
    scene.render.resolution_percentage = profile.resolution_percentage

    settings['resolution'] = {
        'x': profile.resolution_x,
        'y': profile.resolution_y,
        'percentage': profile.resolution_percentage,
    }

    # Render engine
    scene.render.engine = profile.engine.value
    settings['engine'] = profile.engine.value

    # Samples
    if profile.engine == RenderEngine.CYCLES:
        scene.cycles.samples = profile.samples
        scene.cycles.max_bounces = profile.max_bounces
        settings['cycles'] = {
            'samples': profile.samples,
            'max_bounces': profile.max_bounces,
        }

    # Motion blur
    if profile.use_motion_blur:
        scene.render.use_motion_blur = True
        scene.render.motion_blur_samples = profile.motion_blur_samples
        scene.render.motion_blur_shutter = profile.motion_blur_shutter
        settings['motion_blur'] = {
            'enabled': True,
            'samples': profile.motion_blur_samples,
            'shutter': profile.motion_blur_shutter,
        }

    # Denoising
    scene.render.use_denoising = profile.use_denoising
    if profile.use_denoising:
        scene.view_layer.samples = 0  # Disable for render view
        scene.cycles.denoiser_strength = profile.denoiser_strength
        settings['denoising'] = {
            'enabled': True,
            'strength': profile.denoiser_strength,
        }

    # Film transparent
    if profile.transparent_background:
        scene.render.film_transparent = True
    settings['transparent'] = True

    # Output format
    scene.render.image_settings.file_format = profile.output_format
    if profile.color_depth != 8:
        scene.render.image_settings.color_depth = profile.color_depth
    settings['output'] = {
        'format': profile.output_format,
        'color_depth': profile.color_depth,
    }

    # Compositing
    if profile.use_compositing:
        scene.use_nodes = True
        settings['compositing'] = True

    return settings
