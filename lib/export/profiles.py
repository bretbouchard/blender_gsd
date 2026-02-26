"""
Export profiles for game engine and real-time applications.

Provides pre-configured export profiles for common target platforms.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path
from enum import Enum
import yaml


class ExportTarget(Enum):
    """Target platform for export."""
    UNREAL_5 = "unreal_5"
    UNREAL_4 = "unreal_4"
    UNITY = "unity"
    GODOT_4 = "godot_4"
    WEB_GL = "web_gl"
    AR_VR = "ar_vr"
    MOBILE = "mobile"


@dataclass
class ExportProfile:
    """
    Complete export profile configuration.

    Attributes:
        name: Profile name
        target: Target platform
        format: Export format (fbx, glb, usd)
        scale_factor: Scale multiplier
        forward_axis: Forward axis string
        up_axis: Up axis string
        apply_modifiers: Apply modifiers before export
        embed_textures: Embed textures in file
        texture_bake_size: Texture bake resolution
        draco_compression: Use Draco compression (GLB only)
        draco_level: Draco compression level
        include_armatures: Include armatures
        include_animations: Include animations
        include_cameras: Include cameras
        include_lights: Include lights
        custom_settings: Additional custom settings
    """
    name: str
    target: ExportTarget
    format: str = "fbx"
    scale_factor: float = 1.0
    forward_axis: str = "Y"
    up_axis: str = "Z"
    apply_modifiers: bool = True
    embed_textures: bool = False
    texture_bake_size: int = 2048
    draco_compression: bool = True
    draco_level: int = 6
    include_armatures: bool = False
    include_animations: bool = True
    include_cameras: bool = False
    include_lights: bool = False
    custom_settings: Dict[str, Any] = field(default_factory=dict)


# Default profiles
DEFAULT_PROFILES: Dict[str, ExportProfile] = {
    "unreal_5_high": ExportProfile(
        name="Unreal Engine 5.x (High Quality)",
        target=ExportTarget.UNREAL_5,
        format="fbx",
        scale_factor=100.0,  # cm to m
        forward_axis="Y",
        up_axis="Z",
        apply_modifiers=True,
        embed_textures=False,
        texture_bake_size=4096,
        include_armatures=True,
        include_animations=True,
        include_cameras=False,
        include_lights=False,
    ),
    "unreal_5_mobile": ExportProfile(
        name="Unreal Engine 5.x (Mobile)",
        target=ExportTarget.UNREAL_5,
        format="fbx",
        scale_factor=100.0,
        forward_axis="Y",
        up_axis="Z",
        apply_modifiers=True,
        embed_textures=False,
        texture_bake_size=1024,
        draco_compression=False,
        include_armatures=False,
        include_animations=True,
    ),
    "unity_web": ExportProfile(
        name="Unity WebGL",
        target=ExportTarget.UNITY,
        format="glb",
        scale_factor=1.0,
        forward_axis="Z",
        up_axis="Y",
        apply_modifiers=True,
        embed_textures=True,
        texture_bake_size=2048,
        draco_compression=True,
        draco_level=6,
        include_animations=True,
    ),
    "web_ar_vr": ExportProfile(
        name="Web AR/VR",
        target=ExportTarget.AR_VR,
        format="glb",
        scale_factor=1.0,
        forward_axis="Z",
        up_axis="Y",
        apply_modifiers=True,
        embed_textures=True,
        texture_bake_size=4096,
        draco_compression=False,  # Quality over size
        include_animations=True,
    ),
    "godot_4": ExportProfile(
        name="Godot 4.x",
        target=ExportTarget.GODOT_4,
        format="glb",
        scale_factor=1.0,
        forward_axis="Z",
        up_axis="Y",
        apply_modifiers=True,
        embed_textures=True,
        texture_bake_size=2048,
        draco_compression=True,
        draco_level=4,
    ),
    "mobile_optimized": ExportProfile(
        name="Mobile Optimized",
        target=ExportTarget.MOBILE,
        format="glb",
        scale_factor=1.0,
        forward_axis="Z",
        up_axis="Y",
        apply_modifiers=True,
        embed_textures=True,
        texture_bake_size=1024,
        draco_compression=True,
        draco_level=8,  # Maximum compression
        include_animations=True,
    ),
}


def load_export_profile(name: str) -> ExportProfile:
    """
    Load export profile by name.

    Args:
        name: Profile name (e.g., "unreal_5_high")

    Returns:
        ExportProfile instance

    Raises:
        KeyError: If profile not found

    Example:
        >>> profile = load_export_profile("unreal_5_high")
        >>> print(f"Scale: {profile.scale_factor}")
    """
    if name not in DEFAULT_PROFILES:
        raise KeyError(f"Export profile '{name}' not found. Available: {list(DEFAULT_PROFILES.keys())")
    return DEFAULT_PROFILES[name]


def save_export_profile(profile: ExportProfile, path: str) -> None:
    """
    Save export profile to file.

    Args:
        profile: ExportProfile to save
        path: Output file path (YAML)

    Example:
        >>> profile = load_export_profile("unreal_5_high")
        >>> save_export_profile(profile, "profiles/my_custom.yaml")
    """
    data = {
        'name': profile.name,
        'target': profile.target.value,
        'format': profile.format,
        'scale_factor': profile.scale_factor,
        'forward_axis': profile.forward_axis,
        'up_axis': profile.up_axis,
        'apply_modifiers': profile.apply_modifiers,
        'embed_textures': profile.embed_textures,
        'texture_bake_size': profile.texture_bake_size,
        'draco_compression': profile.draco_compression,
        'draco_level': profile.draco_level,
        'include_armatures': profile.include_armatures,
        'include_animations': profile.include_animations,
        'include_cameras': profile.include_cameras,
        'include_lights': profile.include_lights,
        'custom_settings': profile.custom_settings,
    }

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)


def load_export_profile_from_file(path: str) -> ExportProfile:
    """
    Load export profile from YAML file.

    Args:
        path: Path to YAML file

    Returns:
        ExportProfile instance

    Example:
        >>> profile = load_export_profile_from_file("profiles/custom.yaml")
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    return ExportProfile(
        name=data['name'],
        target=ExportTarget(data['target']),
        format=data['format'],
        scale_factor=data.get('scale_factor', 1.0),
        forward_axis=data.get('forward_axis', 'Y'),
        up_axis=data.get('up_axis', 'Z'),
        apply_modifiers=data.get('apply_modifiers', True),
        embed_textures=data.get('embed_textures', False),
        texture_bake_size=data.get('texture_bake_size', 2048),
        draco_compression=data.get('draco_compression', True),
        draco_level=data.get('draco_level', 6),
        include_armatures=data.get('include_armatures', False),
        include_animations=data.get('include_animations', True),
        include_cameras=data.get('include_cameras', False),
        include_lights=data.get('include_lights', False),
        custom_settings=data.get('custom_settings', {}),
    )


def list_export_profiles() -> list[str]:
    """
    List available export profile names.

    Returns:
        List of profile names

    Example:
        >>> profiles = list_export_profiles()
        >>> print(f"Available: {profiles}")
    """
    return list(DEFAULT_PROFILES.keys())
