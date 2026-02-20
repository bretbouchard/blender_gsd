"""
Shot Assembly Module (REQ-CINE-SHOT)

Complete shot assembly from YAML configuration. Single entry point
for creating fully-configured cinematic shots with template inheritance,
state persistence, render capabilities, and tracking integration.

Core Functions:
    assemble_shot: Assemble complete shot from ShotAssemblyConfig
    assemble_tracked_shot: Assemble shot with tracking support (Phase 7.4)
    load_shot_yaml: Load shot definition from YAML file
    save_shot_state: Save shot state for version control
    render_shot: Render assembled shot
    create_shot_from_template: Create shot from template with inheritance
    edit_shot: Edit existing shot with partial overrides
    setup_shadow_catcher: Setup shadow catcher ground plane (Phase 7.4)

Extended YAML Structure (Phase 7.4):
    shot:
      name: composite_knob_hero
      footage:
        file: footage/knob_hero_4k.mp4
        frame_range: [1, 150]
      tracking:
        enabled: true
        preset: high_quality
        solve: true
      camera:
        from_tracking: true
      composite:
        mode: over_footage
        shadow_catcher: true

Usage:
    from lib.cinematic.shot import (
        assemble_shot, assemble_tracked_shot, load_shot_yaml, save_shot_state,
        render_shot, create_shot_from_template, edit_shot, setup_shadow_catcher
    )

    # Load and assemble from YAML
    config = load_shot_yaml("shots/hero_shot.yaml")
    result = assemble_shot(config)

    # Assemble with tracking (Phase 7.4)
    result = assemble_tracked_shot("shots/tracked_shot.yaml")

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

# Tracking integration (Phase 7.4)
try:
    from .tracking.shot_integration import (
        assemble_shot_with_tracking,
        TrackingShotConfig,
        CompositeShotConfig,
        FootageConfig,
    )
    TRACKING_AVAILABLE = True
except ImportError:
    TRACKING_AVAILABLE = False


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
# SHADOW CATCHER WORKFLOW (Phase 7.4)
# =============================================================================

def setup_shadow_catcher(
    config: Optional[Dict[str, Any]] = None,
    scene: Any = None
) -> Dict[str, Any]:
    """
    Setup shadow catcher workflow with ground plane.

    Creates a ground plane with shadow catcher material and configures
    render settings for transparent film and shadow pass.

    Args:
        config: Optional ShadowCatcherConfig dict with:
            - enabled: bool (default True)
            - ground_size: float (default 10.0)
            - ground_location: tuple (default (0, 0, 0))
            - receive_shadows: bool (default True)
            - shadow_only: bool (default True)
        scene: Optional scene (uses context.scene if None)

    Returns:
        Dict with 'ground_plane', 'material', 'shadow_pass_enabled'
    """
    result = {
        "ground_plane": None,
        "material": None,
        "shadow_pass_enabled": False,
    }

    if not BLENDER_AVAILABLE:
        return result

    if scene is None:
        scene = bpy.context.scene

    # Parse config
    if config is None:
        config = {}

    enabled = config.get('enabled', True)
    if not enabled:
        return result

    ground_size = config.get('ground_size', 10.0)
    ground_location = config.get('ground_location', (0, 0, 0))
    shadow_only = config.get('shadow_only', True)

    try:
        # Create ground plane
        ground_name = "ShadowCatcher_Ground"

        # Create mesh
        bpy.ops.mesh.primitive_plane_add(
            size=ground_size,
            location=ground_location
        )
        ground_plane = bpy.context.active_object
        ground_plane.name = ground_name

        # Create shadow catcher material
        mat_name = "ShadowCatcher_Material"
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True

            # Clear default nodes
            nodes = mat.node_tree.nodes
            nodes.clear()

            # Create Principled BSDF with shadow catcher settings
            principled = nodes.new('ShaderNodeBsdfPrincipled')
            principled.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1.0)
            principled.inputs['Alpha'].default_value = 0.0

            # Create output node
            output = nodes.new('ShaderNodeOutputMaterial')
            output.location = (300, 0)

            # Link nodes
            mat.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # Apply material to ground
        if ground_plane.data.materials:
            ground_plane.data.materials[0] = mat
        else:
            ground_plane.data.materials.append(mat)

        # Set shadow method for Blender 4.x
        if hasattr(mat, 'shadow_method'):
            mat.shadow_method = 'CLIP'
        if hasattr(mat, 'use_transparent_shadow'):
            mat.use_transparent_shadow = True

        # Configure render settings
        scene.render.film_transparent = True

        # Enable shadow pass
        if scene.view_layers:
            view_layer = scene.view_layers[0]
            view_layer.use_pass_shadow = True
            result["shadow_pass_enabled"] = True

        result["ground_plane"] = ground_plane
        result["material"] = mat

    except Exception:
        pass

    return result


# =============================================================================
# TRACKING INTEGRATION (Phase 7.4)
# =============================================================================

def assemble_tracked_shot(
    yaml_path: Path,
    scene: Any = None
) -> Dict[str, Any]:
    """
    Load and assemble shot with tracking support.

    Checks for tracking config and delegates to assemble_shot_with_tracking
    if tracking is enabled, otherwise falls back to standard assemble_shot.

    Args:
        yaml_path: Path to shot YAML file with tracking extension
        scene: Optional scene (uses context.scene if None)

    Returns:
        Dictionary with created objects including tracking session
    """
    path = Path(yaml_path)

    if not path.exists():
        raise FileNotFoundError(f"Shot file not found: {path}")

    # Load YAML
    with open(path, 'r', encoding='utf-8') as f:
        if yaml:
            data = yaml.safe_load(f)
        else:
            data = json.loads(f.read())

    # Check for tracking config
    tracking_config = data.get('tracking', {})
    if tracking_config.get('enabled') and TRACKING_AVAILABLE:
        # Use tracking-aware assembly
        return assemble_shot_with_tracking(data, scene)
    else:
        # Standard assembly
        config = ShotAssemblyConfig.from_dict(data)
        result = assemble_shot(config, scene)

        # Add shadow catcher if configured
        composite_config = data.get('composite', {})
        if composite_config.get('shadow_catcher'):
            result['shadow_catcher'] = setup_shadow_catcher(composite_config, scene)

        return result


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

    # Shadow catcher (Phase 7.4)
    "setup_shadow_catcher",

    # Tracking integration (Phase 7.4)
    "assemble_tracked_shot",
    "TRACKING_AVAILABLE",

    # Constants
    "BLENDER_AVAILABLE",
    "MODULES_AVAILABLE",
]
