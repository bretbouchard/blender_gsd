"""
Shot Assembly Module (REQ-CINE-SHOT)

Complete shot assembly from YAML configuration. Single entry point
for creating fully-configured cinematic shots with template inheritance,
state persistence, and render capabilities.

Core Functions:
    assemble_shot: Assemble complete shot from ShotAssemblyConfig
    load_shot_yaml: Load shot definition from YAML file
    save_shot_state: Save shot state for version control
    render_shot: Render assembled shot
    create_shot_from_template: Create shot from template with inheritance
    edit_shot: Edit existing shot with partial overrides

Usage:
    from lib.cinematic.shot import (
        assemble_shot, load_shot_yaml, save_shot_state,
        render_shot, create_shot_from_template, edit_shot
    )

    # Load and assemble from YAML
    config = load_shot_yaml("shots/hero_shot.yaml")
    result = assemble_shot(config)

    # Create from template
    shot = create_shot_from_template(
        template_name="product_hero",
        subject="my_product",
        overrides={"camera": {"focal_length": 85}}
    )

    # Render the shot
    render_shot(output_path="//render/hero_shot.png")

    # Save state for versioning
    save_shot_state("hero_shot", version=1)
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import copy
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
    AnimationConfig, RigConfig, ShotState
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
    from .render import apply_quality_profile, render_frame, render_animation, get_render_metadata
    from .animation import create_orbit_animation, create_turntable_animation
    from .state_manager import StateManager, FrameStore
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


def save_shot_state(
    shot_name: str,
    version: Optional[int] = None,
    base_path: Optional[Path] = None
) -> Tuple[int, Path]:
    """
    Save complete shot state for version control.

    Captures current Blender scene state and saves it to a versioned
    directory structure for comparison and rollback.

    Args:
        shot_name: Name of the shot to save
        version: Optional version number (auto-incremented if None)
        base_path: Base path for frame storage (default: .gsd-state/cinematic/frames)

    Returns:
        Tuple of (version_number, path_to_saved_state)
    """
    if not MODULES_AVAILABLE:
        raise RuntimeError("State manager modules not available")

    if base_path is None:
        base_path = Path(".gsd-state/cinematic/frames")

    store = FrameStore(base_path)
    manager = StateManager(base_path)

    # Capture current state
    state = manager.capture_current(shot_name)

    # Save to frame store
    if version is not None:
        # Save to specific version
        shot_dir = base_path / shot_name / f"{version:03d}"
        shot_dir.mkdir(parents=True, exist_ok=True)
        state.version = version
        manager.save(state, shot_dir / "state.yaml")
        saved_version = version
    else:
        # Auto-increment version
        saved_version = store.save_frame(shot_name, state)

    return saved_version, base_path / shot_name / f"{saved_version:03d}" / "state.yaml"


def load_shot_state(
    shot_name: str,
    version: int,
    base_path: Optional[Path] = None
) -> ShotState:
    """
    Load shot state from versioned storage.

    Args:
        shot_name: Name of the shot
        version: Version number to load
        base_path: Base path for frame storage (default: .gsd-state/cinematic/frames)

    Returns:
        ShotState loaded from storage

    Raises:
        FileNotFoundError: If version doesn't exist
    """
    if not MODULES_AVAILABLE:
        raise RuntimeError("State manager modules not available")

    if base_path is None:
        base_path = Path(".gsd-state/cinematic/frames")

    store = FrameStore(base_path)
    return store.load_frame(shot_name, version)


def save_shot_yaml(config: ShotAssemblyConfig, path: Path) -> None:
    """
    Save shot configuration to YAML file.

    Args:
        config: Shot configuration to save
        path: Output file path
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.to_dict()

    with open(path, "w", encoding="utf-8") as f:
        if yaml:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            json.dump(data, f, indent=2)


def render_shot(
    config: Optional[ShotAssemblyConfig] = None,
    output_path: Optional[str] = None,
    scene: Optional[Any] = None,
    animation: bool = False,
    use_viewport: bool = False
) -> str:
    """
    Render the assembled shot.

    Args:
        config: Optional shot configuration for render settings
        output_path: Optional override output path
        scene: Optional scene override
        animation: Render animation sequence (vs single frame)
        use_viewport: Use viewport render for faster preview

    Returns:
        Output path used for rendering (empty string on failure)
    """
    if not BLENDER_AVAILABLE:
        return ""

    if scene is None:
        scene = bpy.context.scene

    # Set output path
    if output_path:
        scene.render.filepath = output_path
    elif config and config.output_path:
        scene.render.filepath = config.output_path

    # Apply render settings from config
    if config and config.render and MODULES_AVAILABLE:
        if hasattr(config.render, 'quality_tier') and config.render.quality_tier:
            apply_quality_profile(config.render.quality_tier, scene=scene)

    # Execute render
    try:
        is_animation = animation or (config and config.animation and config.animation.enabled)
        if is_animation:
            # Animation render
            if MODULES_AVAILABLE:
                return render_animation(output_path=output_path)
            else:
                bpy.ops.render.render(animation=True)
        else:
            # Single frame
            if MODULES_AVAILABLE:
                return render_frame(output_path=output_path, use_viewport=use_viewport)
            else:
                bpy.ops.render.render(write_still=True)
    except Exception:
        pass

    return scene.render.filepath


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


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Core assembly functions
    "assemble_shot",
    "load_shot_yaml",
    "save_shot_yaml",
    "save_shot_state",
    "load_shot_state",
    "render_shot",

    # Template functions
    "create_shot_from_template",
    "edit_shot",

    # Constants
    "BLENDER_AVAILABLE",
    "MODULES_AVAILABLE",
]
