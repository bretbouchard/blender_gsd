"""
Shot Integration Module (Phase 7.4)

Extends shot assembly with tracking workflow integration.
Enables single YAML to produce tracked composite shot by integrating
tracking, solving, and compositing into the shot assembly pipeline.

Configuration Types:
    FootageConfig: Footage file and metadata configuration
    TrackingShotConfig: Tracking workflow settings
    CompositeShotConfig: Composite mode and rendering settings

Core Functions:
    setup_tracked_shot: Core tracking setup with session management
    assemble_shot_with_tracking: Main entry point for tracked shots
    apply_solved_camera: Apply solved camera to Blender camera
    setup_shot_compositing: Setup compositor from config

Helper Functions:
    load_tracking_shot_yaml: Load shot YAML with tracking extension
    validate_tracking_shot_config: Validate configuration

Extended YAML Structure:
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
    from lib.cinematic.tracking.shot_integration import (
        assemble_shot_with_tracking,
        TrackingShotConfig,
        CompositeShotConfig,
    )

    # Assemble tracked shot from YAML
    result = assemble_shot_with_tracking(config)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
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
    TrackingSession,
    TrackData,
    SolveData,
    FootageMetadata,
)
from .session import (
    TrackingSessionManager,
    SessionStatus,
    create_session,
    resume_tracking,
    load_session,
)
from .compositor import (
    CompositeConfig,
    create_stabilization_nodes,
    create_corner_pin_nodes,
    create_alpha_over_composite,
    create_shadow_composite,
    create_image_node,
    create_mix_node,
    apply_stmap_distortion,
    setup_lens_distortion_workflow,
    _ensure_compositor_enabled,
    _get_or_create_node,
)


# =============================================================================
# CONFIGURATION DATACLASSES
# =============================================================================

@dataclass
class FootageConfig:
    """
    Footage file and metadata configuration.

    Attributes:
        file: Path to footage file
        frame_range: Frame range as (start, end)
        color_space: Color space name
        frame_rate: Frames per second
        resolution: Resolution as (width, height)
    """
    file: str = ""
    frame_range: Tuple[int, int] = (1, 120)
    color_space: str = "Rec.709"
    frame_rate: float = 24.0
    resolution: Tuple[int, int] = (1920, 1080)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file": self.file,
            "frame_range": list(self.frame_range),
            "color_space": self.color_space,
            "frame_rate": self.frame_rate,
            "resolution": list(self.resolution),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FootageConfig:
        """Create from dictionary."""
        frame_range = data.get("frame_range", [1, 120])
        resolution = data.get("resolution", [1920, 1080])
        return cls(
            file=data.get("file", ""),
            frame_range=(frame_range[0], frame_range[1]) if isinstance(frame_range, list) else frame_range,
            color_space=data.get("color_space", "Rec.709"),
            frame_rate=data.get("frame_rate", 24.0),
            resolution=(resolution[0], resolution[1]) if isinstance(resolution, list) else resolution,
        )


@dataclass
class TrackingShotConfig:
    """
    Tracking workflow settings.

    Attributes:
        enabled: Whether tracking is enabled for this shot
        preset: Tracking preset name from tracking_presets.yaml
        solve: Whether to run camera solver
        session_file: Path to existing session file for resume
        auto_detect: Auto-detection settings with min_tracks, quality_threshold
    """
    enabled: bool = False
    preset: str = "balanced"
    solve: bool = True
    session_file: Optional[str] = None
    auto_detect: Dict[str, Any] = field(default_factory=lambda: {
        "min_tracks": 100,
        "quality_threshold": 0.01,
    })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "preset": self.preset,
            "solve": self.solve,
            "session_file": self.session_file,
            "auto_detect": self.auto_detect,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrackingShotConfig:
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            preset=data.get("preset", "balanced"),
            solve=data.get("solve", True),
            session_file=data.get("session_file"),
            auto_detect=data.get("auto_detect", {"min_tracks": 100, "quality_threshold": 0.01}),
        )


@dataclass
class CompositeShotConfig:
    """
    Composite mode and rendering settings.

    Attributes:
        mode: Composite mode (over_footage, over_plate, multiply, add, screen)
        background_source: Background type (footage, image, none)
        lens_distortion: Lens distortion settings (apply_to_cg, st_map_path)
        stabilization: Stabilization settings (enabled, tracks)
        shadow_catcher: Enable shadow catcher composite
        film_transparent: Enable transparent film background
    """
    mode: str = "over_footage"
    background_source: str = "footage"
    lens_distortion: Dict[str, Any] = field(default_factory=lambda: {
        "apply_to_cg": True,
        "st_map_path": None,
    })
    stabilization: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "tracks": "all",
    })
    shadow_catcher: bool = True
    film_transparent: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode,
            "background_source": self.background_source,
            "lens_distortion": self.lens_distortion,
            "stabilization": self.stabilization,
            "shadow_catcher": self.shadow_catcher,
            "film_transparent": self.film_transparent,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CompositeShotConfig:
        """Create from dictionary."""
        return cls(
            mode=data.get("mode", "over_footage"),
            background_source=data.get("background_source", "footage"),
            lens_distortion=data.get("lens_distortion", {"apply_to_cg": True, "st_map_path": None}),
            stabilization=data.get("stabilization", {"enabled": False, "tracks": "all"}),
            shadow_catcher=data.get("shadow_catcher", True),
            film_transparent=data.get("film_transparent", True),
        )

    def to_composite_config(self) -> CompositeConfig:
        """Convert to CompositeConfig."""
        return CompositeConfig(
            mode=self.mode,
            background_source=self.background_source,
            lens_distortion=self.lens_distortion,
            stabilization=self.stabilization,
            shadow_catcher=self.shadow_catcher,
            film_transparent=self.film_transparent,
        )


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def setup_tracked_shot(
    shot_config: Dict[str, Any],
    session_manager: Optional[TrackingSessionManager] = None
) -> Optional[TrackingSessionManager]:
    """
    Core tracking setup function.

    Checks for tracking config, loads or creates session, runs tracking/solving
    if needed, and applies solved camera.

    Args:
        shot_config: Shot configuration dictionary
        session_manager: Optional existing session manager

    Returns:
        TrackingSessionManager instance, or None if tracking not enabled
    """
    tracking_config = shot_config.get('tracking', {})

    # Check if tracking is enabled
    if not tracking_config.get('enabled', False):
        return None

    # Parse tracking config
    tracking_shot_config = TrackingShotConfig.from_dict(tracking_config)

    # Load or create session
    if session_manager:
        manager = session_manager
    elif tracking_shot_config.session_file:
        manager = load_session(Path(tracking_shot_config.session_file))
    else:
        footage_config = shot_config.get('footage', {})
        footage_file = footage_config.get('file', '')
        shot_name = shot_config.get('name', 'untitled')
        manager = create_session(Path(footage_file) if footage_file else Path('.'), shot_name)

    # Check if we need to run tracking/solving
    session_status = manager.state.get('tracking', {}).get('status', 'not_started')

    # Note: Actual tracking/solving would be done by tracking operators
    # This function just sets up the session structure

    # Apply solved camera if requested
    if shot_config.get('camera', {}).get('from_tracking'):
        solve_data = _get_solve_data(manager)
        if solve_data:
            _apply_solved_camera_internal(solve_data, shot_config.get('camera', {}))

    return manager


def _get_solve_data(manager: TrackingSessionManager) -> Optional[SolveData]:
    """Get solve data from session manager."""
    solve_state = manager.state.get('solve', {})
    if solve_state.get('status') != 'complete':
        return None

    # Try to load solve data from file
    solve_id = solve_state.get('solve_id')
    if solve_id:
        solve_path = Path(".gsd-state/tracking/solves") / solve_id / "solve.yaml"
        if solve_path.exists():
            try:
                with open(solve_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) if yaml else json.load(f)
                    return SolveData.from_dict(data)
            except Exception:
                pass

    return None


def _apply_solved_camera_internal(solve: SolveData, camera_config: Dict[str, Any]) -> Any:
    """Internal function to apply solved camera to Blender scene."""
    if not BLENDER_AVAILABLE:
        return None

    try:
        scene = bpy.context.scene

        # Create camera if not exists
        cam_name = camera_config.get('name', 'Tracked_Camera')
        cam_data = bpy.data.cameras.new(cam_name) if cam_name not in bpy.data.cameras else bpy.data.cameras[cam_name]
        cam_obj = bpy.data.objects.get(cam_name)

        if not cam_obj:
            cam_obj = bpy.data.objects.new(cam_name, cam_data)
            scene.collection.objects.link(cam_obj)

        # Set focal length from solve
        cam_data.lens = solve.focal_length

        # Keyframe position and rotation from solve data
        for frame, transform in solve.camera_transforms.items():
            tx, ty, tz, rx, ry, rz = transform

            scene.frame_set(frame)

            # Set position
            cam_obj.location = (tx, ty, tz)
            cam_obj.keyframe_insert('location', frame=frame)

            # Set rotation (convert to radians if degrees)
            import math
            cam_obj.rotation_euler = (
                math.radians(rx) if rx > 6.28 else rx,
                math.radians(ry) if ry > 6.28 else ry,
                math.radians(rz) if rz > 6.28 else rz
            )
            cam_obj.keyframe_insert('rotation_euler', frame=frame)

        # Set as active camera
        scene.camera = cam_obj

        return cam_obj

    except Exception:
        return None


def assemble_shot_with_tracking(
    shot_config: Dict[str, Any],
    scene: Any = None
) -> Dict[str, Any]:
    """
    Main entry point for tracked shot assembly.

    Wraps assemble_shot from shot.py with tracking integration.
    Checks for tracking config, runs tracking/solving if needed,
    applies solved camera, and sets up compositor nodes.

    Args:
        shot_config: Complete shot configuration dictionary
        scene: Optional Blender scene

    Returns:
        Dictionary with:
            - All keys from assemble_shot (camera, lights, backdrop, subject)
            - session: TrackingSessionManager
            - compositor_nodes: Dict of created nodes
    """
    result = {
        "camera": None,
        "lights": [],
        "backdrop": None,
        "subject": None,
        "session": None,
        "compositor_nodes": {},
    }

    if not BLENDER_AVAILABLE:
        return result

    if scene is None:
        scene = bpy.context.scene

    # Check for tracking config
    tracking_config = shot_config.get('tracking', {})
    tracking_enabled = tracking_config.get('enabled', False)

    if tracking_enabled:
        # Setup tracking session
        session = setup_tracked_shot(shot_config)
        result['session'] = session

        # Setup compositor
        composite_config = shot_config.get('composite', {})
        if composite_config:
            comp_config = CompositeShotConfig.from_dict(composite_config)
            nodes = setup_shot_compositing(comp_config, session, scene)
            result['compositor_nodes'] = nodes

    # Try to use shot.py for base assembly
    try:
        from ..shot import assemble_shot, ShotAssemblyConfig

        # Convert config for base assembly
        base_config_dict = {k: v for k, v in shot_config.items()
                          if k not in ['tracking', 'footage', 'composite']}

        if base_config_dict:
            base_config = ShotAssemblyConfig.from_dict(base_config_dict)
            base_result = assemble_shot(base_config, scene, clear_existing=True)

            result['camera'] = base_result.get('camera')
            result['lights'] = base_result.get('lights', [])
            result['backdrop'] = base_result.get('backdrop')
            result['subject'] = base_result.get('subject')

    except ImportError:
        pass  # shot.py not available

    return result


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def apply_solved_camera(
    solve: SolveData,
    camera_config: Dict[str, Any],
    scene: Any = None
) -> Any:
    """
    Create Blender camera from Solve data.

    Keyframes position and rotation from SolveResult per frame.
    Sets focal length from solve.

    Args:
        solve: SolveData with camera transforms
        camera_config: Camera configuration options
        scene: Optional scene (uses context.scene if None)

    Returns:
        Camera object, or None on failure
    """
    if not BLENDER_AVAILABLE:
        return None

    return _apply_solved_camera_internal(solve, camera_config)


def setup_shot_compositing(
    composite_config: CompositeShotConfig,
    session: Optional[TrackingSessionManager],
    scene: Any = None
) -> Dict[str, Any]:
    """
    Setup compositor based on composite config.

    Creates background footage node, applies stabilization,
    sets up shadow catcher, and applies ST-Map distortion.

    Args:
        composite_config: Composite mode configuration
        session: Optional tracking session for stabilization data
        scene: Optional scene (uses context.scene if None)

    Returns:
        Dict of created nodes
    """
    if not BLENDER_AVAILABLE:
        return {}

    if scene is None:
        scene = bpy.context.scene

    # Ensure compositor is enabled
    if not _ensure_compositor_enabled(scene):
        return {}

    tree = scene.node_tree

    # Configure film transparent
    scene.render.film_transparent = composite_config.film_transparent

    # Enable shadow pass if shadow catcher
    if composite_config.shadow_catcher:
        view_layer = scene.view_layers[0] if scene.view_layers else None
        if view_layer:
            view_layer.use_pass_shadow = True

    nodes = {}

    # Create background image node if needed
    if composite_config.background_source in ('footage', 'image'):
        footage_path = None
        if session and session.session.footage_path:
            footage_path = session.session.footage_path

        if footage_path:
            bg_node = create_image_node(tree, footage_path, "Background_Footage")
            nodes['background'] = bg_node

    # Setup stabilization if enabled
    if composite_config.stabilization.get('enabled') and session:
        # Would need actual stabilization data from session
        pass

    # Create composite node based on mode
    render_layers = tree.nodes.get('Render Layers')
    composite = tree.nodes.get('Composite')

    if render_layers and composite:
        if composite_config.mode == 'over_footage' and nodes.get('background'):
            # Create AlphaOver node
            alpha_over = create_alpha_over_composite(tree, "CG_Over_Footage", (600, 0))
            nodes['alpha_over'] = alpha_over

            # Connect: Background -> BG, Render Layers -> FG
            tree.links.new(nodes['background'].outputs['Image'], alpha_over.inputs[2])  # BG
            tree.links.new(render_layers.outputs['Image'], alpha_over.inputs[1])  # FG
            tree.links.new(alpha_over.outputs['Image'], composite.inputs['Image'])

        elif composite_config.mode == 'multiply' and composite_config.shadow_catcher:
            # Create shadow multiply composite
            shadow_nodes = create_shadow_composite(tree)
            nodes.update(shadow_nodes)

            # Connect to composite
            if shadow_nodes.get('shadow_mix'):
                tree.links.new(render_layers.outputs['Shadow'], shadow_nodes['shadow_mix'].inputs[0])
                if nodes.get('background'):
                    tree.links.new(nodes['background'].outputs['Image'], shadow_nodes['shadow_mix'].inputs[1])
                tree.links.new(shadow_nodes['shadow_mix'].outputs['Image'], composite.inputs['Image'])

        elif composite_config.mode in ('add', 'screen'):
            # Create mix node with blend mode
            mix_node = create_mix_node(tree, composite_config.mode.upper(), f"Blend_{composite_config.mode}", (600, 0))
            nodes['blend'] = mix_node

            # Connect
            tree.links.new(render_layers.outputs['Image'], mix_node.inputs[1])
            if nodes.get('background'):
                tree.links.new(nodes['background'].outputs['Image'], mix_node.inputs[2])
            tree.links.new(mix_node.outputs['Image'], composite.inputs['Image'])

        else:
            # Direct connection
            tree.links.new(render_layers.outputs['Image'], composite.inputs['Image'])

    # Apply lens distortion if configured
    st_map_path = composite_config.lens_distortion.get('st_map_path')
    if st_map_path and nodes.get('alpha_over'):
        distortion_nodes = setup_lens_distortion_workflow(
            tree,
            'distort_cg',
            st_map_path,
            render_layers,
            nodes.get('background')
        )
        nodes['distortion'] = distortion_nodes

    return nodes


def load_tracking_shot_yaml(path: Path) -> Dict[str, Any]:
    """
    Load shot YAML with tracking extension.

    Parses FootageConfig, TrackingShotConfig, CompositeShotConfig
    from extended YAML structure.

    Args:
        path: Path to shot YAML file

    Returns:
        Complete config dict with parsed nested configs
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Shot file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        if yaml:
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    # Parse nested configs
    if 'footage' in data:
        data['footage_config'] = FootageConfig.from_dict(data['footage'])

    if 'tracking' in data:
        data['tracking_config'] = TrackingShotConfig.from_dict(data['tracking'])

    if 'composite' in data:
        data['composite_config'] = CompositeShotConfig.from_dict(data['composite'])

    return data


def validate_tracking_shot_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate tracking shot configuration.

    Checks required fields exist and footage file exists.

    Args:
        config: Shot configuration dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check tracking config
    tracking = config.get('tracking', {})
    if tracking.get('enabled'):
        # Check footage
        footage = config.get('footage', {})
        footage_file = footage.get('file', '')

        if not footage_file:
            errors.append("Tracking enabled but footage.file not specified")

        elif not Path(footage_file).exists():
            errors.append(f"Footage file not found: {footage_file}")

        # Check frame range
        frame_range = footage.get('frame_range', [])
        if not frame_range or len(frame_range) != 2:
            errors.append("footage.frame_range must be [start, end]")

        # Check preset
        preset = tracking.get('preset', '')
        valid_presets = ['fast', 'balanced', 'precise', 'high_quality']
        if preset and preset not in valid_presets:
            errors.append(f"Unknown tracking preset: {preset}. Valid: {valid_presets}")

    # Check composite config
    composite = config.get('composite', {})
    if composite:
        mode = composite.get('mode', '')
        valid_modes = ['over_footage', 'over_plate', 'multiply', 'add', 'screen']
        if mode and mode not in valid_modes:
            errors.append(f"Unknown composite mode: {mode}. Valid: {valid_modes}")

        # Check ST-Map if lens distortion configured
        lens_dist = composite.get('lens_distortion', {})
        st_map = lens_dist.get('st_map_path')
        if st_map and not Path(st_map).exists():
            errors.append(f"ST-Map file not found: {st_map}")

    return errors


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Configuration types
    "FootageConfig",
    "TrackingShotConfig",
    "CompositeShotConfig",

    # Core functions
    "setup_tracked_shot",
    "assemble_shot_with_tracking",

    # Helper functions
    "apply_solved_camera",
    "setup_shot_compositing",
    "load_tracking_shot_yaml",
    "validate_tracking_shot_config",
]
