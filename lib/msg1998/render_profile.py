"""
MSG 1998 - Render Profile

Render settings for MSG 1998 output.
"""

from typing import Tuple

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

# Import from existing render module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "render"))

try:
    from lib.render.profiles import RenderProfile
    RENDER_PROFILE_AVAILABLE = True
except ImportError:
    RENDER_PROFILE_AVAILABLE = False
    RenderProfile = object

from .types import MSG1998RenderProfile


def apply_msg_profile(scene, profile: MSG1998RenderProfile = None) -> None:
    """
    Apply MSG 1998 render profile to scene.

    Args:
        scene: Blender scene
        profile: Render profile (uses default if None)
    """
    if not BLENDER_AVAILABLE:
        return

    if profile is None:
        profile = MSG1998RenderProfile()

    # Resolution
    scene.render.resolution_x = profile.resolution[0]
    scene.render.resolution_y = profile.resolution[1]
    scene.render.resolution_percentage = 100

    # Frame rate
    scene.render.fps = profile.frame_rate
    scene.render.fps_base = 1

    # Engine
    scene.render.engine = 'CYCLES'

    # Cycles settings
    if hasattr(scene, 'cycles'):
        scene.cycles.samples = profile.samples
        scene.cycles.use_denoising = profile.use_denoiser
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'

    # Color management
    if scene.view_settings:
        scene.view_settings.view_transform = 'Filmic' if profile.color_space == "ACEScg" else 'Standard'

    # Output format
    scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER' if profile.beauty_format == "OPEN_EXR" else 'PNG'
    scene.render.image_settings.color_depth = '32'
    scene.render.image_settings.exr_codec = 'ZIP'


def create_msg_profile_from_base() -> MSG1998RenderProfile:
    """
    Create MSG profile inheriting from base RenderProfile.

    Returns:
        MSG1998RenderProfile with defaults
    """
    return MSG1998RenderProfile(
        resolution=(4096, 1716),  # 2.39:1 anamorphic
        frame_rate=24,
        color_space="ACEScg",
        samples=256,
        use_denoiser=True,
        beauty_format="OPEN_EXR",
        pass_format="OPEN_EXR",
        motion_blur=False
    )


def get_aspect_ratio() -> float:
    """Get target aspect ratio (2.39:1)."""
    return 2.39


def get_resolution_for_aspect(
    width: int = 4096,
    aspect: float = 2.39
) -> Tuple[int, int]:
    """
    Calculate height for given width and aspect ratio.

    Args:
        width: Target width
        aspect: Aspect ratio (width/height)

    Returns:
        (width, height) tuple
    """
    height = int(width / aspect)
    return (width, height)


# Preset profiles for different shot types
PROFILE_PRESETS = {
    "establishing": MSG1998RenderProfile(
        resolution=(4096, 1716),
        samples=512,  # Higher quality for establishing shots
    ),
    "standard": MSG1998RenderProfile(
        resolution=(4096, 1716),
        samples=256,
    ),
    "preview": MSG1998RenderProfile(
        resolution=(2048, 858),
        samples=64,
        use_denoiser=True,
    ),
    "turnover": MSG1998RenderProfile(
        resolution=(1920, 804),
        samples=128,
    ),
}


def get_preset(name: str) -> MSG1998RenderProfile:
    """Get a preset render profile."""
    return PROFILE_PRESETS.get(name, MSG1998RenderProfile())
