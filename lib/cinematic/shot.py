"""
Shot Assembly Module (REQ-CINE-SHOT)

Complete shot assembly from YAML configuration. Single entry point
for creating fully-configured cinematic shots.

Usage:
    from lib.cinematic.shot import assemble_shot, load_shot_yaml, render_shot

    # Load and assemble from YAML
    config = load_shot_yaml("shots/hero_shot.yaml")
    objects = assemble_shot(config)

    # Render
    render_shot(config, output_path="//render/hero_shot.png")
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

try:
    import yaml
except ImportError:
    yaml = None

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

from .types import (
    ShotAssemblyConfig, ShotTemplateConfig, CameraConfig, PlumbBobConfig,
    LightConfig, BackdropConfig, ColorConfig, CinematicRenderSettings,
    AnimationConfig, RigConfig
)
from .preset_loader import (
    resolve_template_inheritance, get_shot_template, get_lighting_rig_preset,
    get_infinite_curve_preset, get_gradient_preset, get_environment_preset
)

# Import other modules conditionally
try:
    from .camera import create_camera, configure_dof
    from .plumb_bob import calculate_plumb_bob
    from .lighting import create_light, apply_lighting_rig
    from .backdrops import create_backdrop
    from .color import apply_color_preset, set_view_transform
    from .render import apply_quality_profile, render_frame
    from .animation import create_orbit_animation, create_turntable_animation
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False


def load_shot_yaml(path: Path) -> ShotAssemblyConfig:
    """
    Load shot configuration from YAML file.

    Resolves template inheritance and returns complete config.

    Args:
        path: Path to shot YAML file

    Returns:
        ShotAssemblyConfig with resolved template values
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Shot file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        if yaml:
            data = yaml.safe_load(f)
        else:
            data = json.loads(f.read())

    # Get base config from dict
    config = ShotAssemblyConfig.from_dict(data)

    # Resolve template if specified
    if config.template:
        template_data = resolve_template_inheritance(config.template)
        config = _merge_template_into_config(config, template_data)

    return config


def _merge_template_into_config(
    config: ShotAssemblyConfig,
    template_data: Dict[str, Any]
) -> ShotAssemblyConfig:
    """Merge template data into shot config (config overrides template)."""
    # Create a merged dict
    merged = template_data.copy()

    # Override with non-None config values
    config_dict = config.to_dict()
    for key, value in config_dict.items():
        if value is not None and value != "" and value != {}:
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # Deep merge dicts
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value

    return ShotAssemblyConfig.from_dict(merged)


def assemble_shot(
    config: ShotAssemblyConfig,
    scene: Optional[Any] = None,
    clear_existing: bool = True
) -> Dict[str, Any]:
    """
    Assemble complete shot from configuration.

    This is the main entry point for shot assembly. It creates and
    configures all scene elements based on the shot configuration.

    Args:
        config: Complete shot configuration
        scene: Optional Blender scene (uses context.scene if None)
        clear_existing: Clear existing lights/cameras before assembly

    Returns:
        Dictionary with created objects:
        {
            "camera": camera_object,
            "lights": [light_objects...],
            "backdrop": backdrop_object,
            "subject": subject_object (if found),
        }
    """
    if not BLENDER_AVAILABLE:
        return {"camera": None, "lights": [], "backdrop": None, "subject": None}

    if scene is None:
        scene = bpy.context.scene

    result = {
        "camera": None,
        "lights": [],
        "backdrop": None,
        "subject": None,
    }

    # Clear existing if requested
    if clear_existing:
        _clear_scene_elements(scene)

    # Find subject
    if config.subject:
        result["subject"] = bpy.data.objects.get(config.subject)

    # Create camera
    if MODULES_AVAILABLE and config.camera:
        cam_config = config.camera
        result["camera"] = create_camera(
            name=f"{config.name}_camera",
            config=cam_config,
            scene=scene
        )

        # Configure DoF
        if hasattr(cam_config, 'f_stop') and cam_config.f_stop > 0:
            configure_dof(result["camera"], f_stop=cam_config.f_stop)

    # Set up plumb bob targeting
    if result["camera"] and config.plumb_bob and MODULES_AVAILABLE:
        target_pos = calculate_plumb_bob(
            config.plumb_bob,
            subject_name=config.subject
        )
        # Point camera at target
        if target_pos:
            direction = target_pos - result["camera"].location
            result["camera"].rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    # Create lighting
    if config.lighting_rig and MODULES_AVAILABLE:
        rig_lights = apply_lighting_rig(config.lighting_rig, scene=scene)
        result["lights"].extend(rig_lights)
    elif config.lights:
        for light_name, light_config in config.lights.items():
            light = create_light(name=light_name, config=light_config, scene=scene)
            if light:
                result["lights"].append(light)

    # Create backdrop
    if config.backdrop and MODULES_AVAILABLE:
        result["backdrop"] = create_backdrop(config.backdrop, scene=scene)

    # Configure color management
    if config.color and MODULES_AVAILABLE:
        set_view_transform(
            view_transform=config.color.view_transform,
            exposure=config.color.exposure,
            gamma=config.color.gamma,
            look=config.color.look
        )

    # Set up animation if configured
    if config.animation and config.animation.enabled and result["camera"] and MODULES_AVAILABLE:
        _setup_animation(result["camera"], config.animation, config)

    # Configure render settings
    if config.render and MODULES_AVAILABLE:
        apply_quality_profile(config.render.quality_tier, scene=scene)

    return result


def _clear_scene_elements(scene: Any) -> None:
    """Remove cameras and lights from scene."""
    if not BLENDER_AVAILABLE:
        return

    # Remove lights
    for obj in list(scene.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)

    # Keep cameras marked as "keep" or the active camera
    active_cam = scene.camera
    for obj in list(scene.objects):
        if obj.type == "CAMERA" and obj != active_cam:
            if not obj.get("gsd_keep", False):
                bpy.data.objects.remove(obj, do_unlink=True)


def _setup_animation(
    camera: Any,
    anim_config: AnimationConfig,
    shot_config: ShotAssemblyConfig
) -> None:
    """Set up camera animation based on config."""
    if not MODULES_AVAILABLE:
        return

    if anim_config.type == "orbit":
        # Calculate center from plumb bob or subject
        center = (0, 0, 0)
        if shot_config.plumb_bob:
            center = calculate_plumb_bob(shot_config.plumb_bob, shot_config.subject)

        create_orbit_animation(
            camera=camera,
            center=center,
            angle_range=anim_config.angle_range,
            radius=anim_config.radius,
            duration=anim_config.duration,
            start_frame=anim_config.start_frame,
            easing=anim_config.easing
        )

    elif anim_config.type == "turntable":
        # Turntable rotates subject, not camera
        if shot_config.subject:
            subject = bpy.data.objects.get(shot_config.subject)
            if subject:
                create_turntable_animation(
                    subject=subject,
                    axis=anim_config.direction,
                    angle_range=anim_config.angle_range,
                    duration=anim_config.duration,
                    start_frame=anim_config.start_frame
                )


def save_shot_state(config: ShotAssemblyConfig, path: Path) -> bool:
    """
    Save shot configuration to YAML.

    Args:
        config: Shot configuration to save
        path: Output path

    Returns:
        True on success
    """
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = config.to_dict()

        with open(path, "w", encoding="utf-8") as f:
            if yaml:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(data, f, indent=2)

        return True
    except Exception:
        return False


def load_shot_state(path: Path) -> ShotAssemblyConfig:
    """
    Load saved shot configuration.

    Args:
        path: Path to saved shot state

    Returns:
        ShotAssemblyConfig
    """
    return load_shot_yaml(path)


def render_shot(
    config: ShotAssemblyConfig,
    output_path: Optional[str] = None,
    scene: Optional[Any] = None
) -> bool:
    """
    Render the shot.

    Args:
        config: Shot configuration
        output_path: Optional override output path
        scene: Optional scene override

    Returns:
        True on success
    """
    if not BLENDER_AVAILABLE or not MODULES_AVAILABLE:
        return False

    if scene is None:
        scene = bpy.context.scene

    # Set output path
    if output_path:
        scene.render.filepath = output_path
    elif config.output_path:
        scene.render.filepath = config.output_path

    # Apply render settings
    if config.render:
        apply_quality_profile(config.render.quality_tier, scene=scene)

    # Execute render
    try:
        if config.animation and config.animation.enabled:
            # Animation render
            bpy.ops.render.render(animation=True)
        else:
            # Single frame
            bpy.ops.render.render(write_still=True)
        return True
    except Exception:
        return False


def create_shot_from_template(
    template_name: str,
    subject: str,
    overrides: Optional[Dict[str, Any]] = None
) -> ShotAssemblyConfig:
    """
    Create shot configuration from template.

    Args:
        template_name: Template to use
        subject: Subject object name
        overrides: Optional parameter overrides

    Returns:
        Configured ShotAssemblyConfig
    """
    # Resolve template
    template_data = resolve_template_inheritance(template_name)

    # Create base config from template
    config = ShotAssemblyConfig(
        name=f"{template_name}_{subject}",
        template=template_name,
        subject=subject
    )

    # Merge template data
    config = _merge_template_into_config(config, template_data)

    # Apply overrides
    if overrides:
        config = edit_shot(config, overrides)

    return config


def edit_shot(config: ShotAssemblyConfig, edits: Dict[str, Any]) -> ShotAssemblyConfig:
    """
    Apply partial edits to shot configuration.

    Args:
        config: Existing shot config
        edits: Dictionary of edits to apply

    Returns:
        Updated ShotAssemblyConfig
    """
    # Convert to dict
    config_dict = config.to_dict()

    # Deep merge edits
    for key, value in edits.items():
        if isinstance(value, dict) and key in config_dict and isinstance(config_dict[key], dict):
            config_dict[key] = {**config_dict[key], **value}
        else:
            config_dict[key] = value

    # Reconstruct config
    return ShotAssemblyConfig.from_dict(config_dict)
