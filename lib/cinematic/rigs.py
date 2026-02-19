"""
Camera Rig System Module

Provides camera rig configurations using Blender constraints.
Supports tripod, dolly, crane, steadicam, and drone rigs.
Includes multi-camera composite rendering via compositor nodes.

Usage:
    from lib.cinematic.rigs import setup_camera_rig, create_multi_camera_layout
    from lib.cinematic.types import RigConfig, MultiCameraLayout

    # Setup a tripod rig
    config = RigConfig(rig_type="tripod", constraints={"position_locked": True})
    setup_camera_rig("hero_camera", config, "plumb_bob_target")

    # Create multi-camera layout
    layout = MultiCameraLayout(layout_type="grid", spacing=2.0, composite_output=True)
    cameras = create_multi_camera_layout(layout, camera_configs)
    setup_multi_camera_composite(layout, cameras)
"""

from __future__ import annotations
from typing import Optional, Any, List, Tuple, Dict
from pathlib import Path
import math

from .types import RigConfig, MultiCameraLayout, CameraConfig, Transform3D
from .preset_loader import get_rig_preset
from .camera import create_camera

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


def setup_camera_rig(
    camera_name: str,
    config: RigConfig,
    target_name: str
) -> bool:
    """
    Setup camera rig based on configuration.

    Applies Blender constraints to create rig behavior:
    - tripod: Track to target, lock position
    - tripod_orbit: Track to target only
    - dolly: Track to target, allow X-axis movement
    - dolly_curved: Track to target with path constraint
    - crane: Track to target with rotation limits
    - steadicam: Soft tracking with offset
    - drone: Track to target with low constraint influence

    Args:
        camera_name: Name of camera object
        config: RigConfig with rig type and settings
        target_name: Name of target object (plumb bob)

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Get camera object
        if camera_name not in bpy.data.objects:
            return False
        camera = bpy.data.objects[camera_name]

        # Get target object
        if target_name not in bpy.data.objects:
            return False
        target = bpy.data.objects[target_name]

        # Clear existing constraints
        clear_rig_constraints(camera_name)

        # Apply constraints based on rig type
        rig_type = config.rig_type.lower()

        if rig_type == "tripod":
            # Track to target, lock all position
            track = camera.constraints.new(type='TRACK_TO')
            track.target = target
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'
            camera.lock_location = (True, True, True)

        elif rig_type == "tripod_orbit":
            # Track to target only, position free
            track = camera.constraints.new(type='TRACK_TO')
            track.target = target
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'
            # No position lock - camera can orbit

        elif rig_type == "dolly":
            # Track to target, allow X-axis movement only
            track = camera.constraints.new(type='TRACK_TO')
            track.target = target
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'
            camera.lock_location = (False, True, True)

        elif rig_type == "dolly_curved":
            # Track to target with path following
            track = camera.constraints.new(type='TRACK_TO')
            track.target = target
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'
            # Path constraint would need a curve object
            # For now, allow X/Y movement
            camera.lock_location = (False, False, True)

        elif rig_type == "crane":
            # Track to target with rotation limits
            track = camera.constraints.new(type='TRACK_TO')
            track.target = target
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'
            # Add rotation limits
            limit_rot = camera.constraints.new(type='LIMIT_ROTATION')
            limit_rot.use_limit_x = True
            limit_rot.use_limit_y = True
            limit_rot.min_x = -math.pi / 4
            limit_rot.max_x = math.pi / 4
            limit_rot.min_y = -math.pi / 6
            limit_rot.max_y = math.pi / 6

        elif rig_type == "steadicam":
            # Soft tracking with smooth following
            copy_loc = camera.constraints.new(type='COPY_LOCATION')
            copy_loc.target = target
            copy_loc.use_offset = True
            # Get smoothing factor from config
            smoothing = config.smoothing.get("factor", 0.8)
            copy_loc.influence = smoothing

            # Track to target
            track = camera.constraints.new(type='TRACK_TO')
            track.target = target
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'
            track.influence = smoothing

        elif rig_type == "drone":
            # Track to target with very low constraint influence
            track = camera.constraints.new(type='TRACK_TO')
            track.target = target
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'
            # Low influence for floating feel
            smoothing = config.smoothing.get("factor", 0.5)
            track.influence = smoothing

        return True

    except Exception:
        return False


def create_rig_controller(
    rig_type: str,
    target_position: Tuple[float, float, float]
) -> Optional[Any]:
    """
    Create an empty object to act as rig controller.

    Args:
        rig_type: Type of rig (for naming)
        target_position: World position for controller

    Returns:
        Controller empty object or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Check context
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return None

        # Create name based on rig type
        name = f"{rig_type}_controller"

        # Check if already exists
        if name in bpy.data.objects:
            ctrl = bpy.data.objects[name]
            ctrl.location = target_position
            return ctrl

        # Create new empty
        ctrl = bpy.data.objects.new(name, None)
        ctrl.empty_display_type = 'ARROWS'
        ctrl.empty_display_size = 0.5
        ctrl.location = target_position

        # Link to scene collection
        bpy.context.scene.collection.objects.link(ctrl)

        return ctrl

    except Exception:
        return None


def clear_rig_constraints(camera_name: str) -> bool:
    """
    Clear all constraints from a camera and unlock transforms.

    Args:
        camera_name: Name of camera object

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if camera_name not in bpy.data.objects:
            return False

        camera = bpy.data.objects[camera_name]

        # Remove all constraints
        for constraint in camera.constraints:
            camera.constraints.remove(constraint)

        # Unlock all transforms
        camera.lock_location = (False, False, False)
        camera.lock_rotation = (False, False, False)
        camera.lock_scale = (False, False, False)

        return True

    except Exception:
        return False


def get_rig_type(camera_name: str) -> Optional[str]:
    """
    Determine rig type from camera constraints.

    Args:
        camera_name: Name of camera object

    Returns:
        Rig type string or None if not rigged
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        if camera_name not in bpy.data.objects:
            return None

        camera = bpy.data.objects[camera_name]

        # Check for constraints
        has_track_to = False
        has_copy_loc = False
        has_limit_rot = False

        for c in camera.constraints:
            if c.type == 'TRACK_TO':
                has_track_to = True
            elif c.type == 'COPY_LOCATION':
                has_copy_loc = True
            elif c.type == 'LIMIT_ROTATION':
                has_limit_rot = True

        # Check lock status
        loc_locked = all(camera.lock_location)

        # Determine rig type
        if has_track_to and loc_locked:
            return "tripod"
        elif has_track_to and not loc_locked:
            if camera.lock_location[1] and camera.lock_location[2]:
                return "dolly"
            else:
                return "tripod_orbit"
        elif has_track_to and has_limit_rot:
            return "crane"
        elif has_copy_loc:
            return "steadicam"
        elif has_track_to:
            return "tripod_orbit"

        return None

    except Exception:
        return None


def apply_rig_preset(
    camera_name: str,
    preset_name: str,
    target_name: str
) -> bool:
    """
    Apply rig preset to camera.

    Args:
        camera_name: Name of camera object
        preset_name: Name of preset from rig_presets.yaml
        target_name: Name of target object

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Load preset
        preset = get_rig_preset(preset_name)

        # Create config from preset
        config = RigConfig(
            rig_type=preset.get("rig_type", "tripod"),
            constraints=preset.get("constraints", {}),
            smoothing=preset.get("smoothing", {}),
            track_config=preset.get("track_config", {})
        )

        return setup_camera_rig(camera_name, config, target_name)

    except Exception:
        return False


def create_multi_camera_layout(
    config: MultiCameraLayout,
    camera_configs: List[CameraConfig]
) -> List[str]:
    """
    Create multiple cameras in a layout configuration.

    Layout types:
    - grid: Arrange in NxN grid with spacing
    - horizontal: Arrange in horizontal line
    - vertical: Arrange in vertical stack
    - circle: Arrange in circle around origin
    - arc: Arrange in 180-degree arc
    - custom: Use positions from config.positions

    Args:
        config: MultiCameraLayout with layout settings
        camera_configs: List of CameraConfig for each camera

    Returns:
        List of created camera names
    """
    if not BLENDER_AVAILABLE:
        return []

    try:
        created_cameras = []
        n = len(camera_configs)
        spacing = config.spacing

        for i, cam_config in enumerate(camera_configs):
            # Calculate position based on layout type
            if config.layout_type == "grid":
                # Calculate grid dimensions
                cols = int(math.ceil(math.sqrt(n)))
                col = i % cols
                row = i // cols
                pos = (
                    col * spacing - (cols - 1) * spacing / 2,
                    row * spacing - (math.ceil(n / cols) - 1) * spacing / 2,
                    0
                )

            elif config.layout_type == "horizontal":
                pos = (
                    i * spacing - (n - 1) * spacing / 2,
                    0,
                    0
                )

            elif config.layout_type == "vertical":
                pos = (
                    0,
                    i * spacing - (n - 1) * spacing / 2,
                    0
                )

            elif config.layout_type == "circle":
                angle = 2 * math.pi * i / n
                radius = spacing * n / (2 * math.pi)
                pos = (
                    radius * math.cos(angle),
                    radius * math.sin(angle),
                    0
                )

            elif config.layout_type == "arc":
                # 180-degree arc
                angle = math.pi * i / (n - 1) if n > 1 else 0
                radius = spacing * n / math.pi
                pos = (
                    radius * math.cos(angle),
                    radius * math.sin(angle),
                    0
                )

            elif config.layout_type == "custom":
                if i < len(config.positions):
                    pos = config.positions[i]
                else:
                    pos = (i * spacing, 0, 0)

            else:
                # Default to grid
                pos = (i * spacing, 0, 0)

            # Update transform
            cam_config.transform = Transform3D(position=pos)

            # Create camera
            cam_obj = create_camera(cam_config, set_active=False)
            if cam_obj:
                created_cameras.append(cam_config.name)

        return created_cameras

    except Exception:
        return []


def setup_multi_camera_composite(
    config: MultiCameraLayout,
    camera_names: List[str]
) -> bool:
    """
    Setup compositor for multi-camera composite rendering.

    Creates a node tree that combines all camera renders into a single grid image.
    Uses Render Layers, Translate, and Mix nodes.

    Args:
        config: MultiCameraLayout with composite settings
        camera_names: List of camera names to composite

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Check context
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene
        scene.use_nodes = True
        tree = scene.node_tree

        if tree is None:
            return False

        n = len(camera_names)
        if n == 0:
            return False

        # Calculate grid dimensions
        if config.composite_cols > 0:
            cols = config.composite_cols
            rows = (n + cols - 1) // cols
        elif config.composite_rows > 0:
            rows = config.composite_rows
            cols = (n + rows - 1) // rows
        else:
            # Auto-calculate: try to make square-ish grid
            cols = int(math.ceil(math.sqrt(n)))
            rows = (n + cols - 1) // cols

        # Get render resolution
        render_width = scene.render.resolution_x
        render_height = scene.render.resolution_y

        # Clear existing nodes (keep only essential)
        nodes_to_remove = []
        for node in tree.nodes:
            if node.name not in ['Render Layers', 'Composite']:
                nodes_to_remove.append(node)

        for node in nodes_to_remove:
            tree.nodes.remove(node)

        # Get or create composite node
        composite = tree.nodes.get('Composite')
        if not composite:
            composite = tree.nodes.new('CompositorNodeComposite')

        # Create render layers and translate nodes for each camera
        prev_output = None

        for i, cam_name in enumerate(camera_names):
            if cam_name not in bpy.data.objects:
                continue

            camera = bpy.data.objects[cam_name]
            col = i % cols
            row = i // cols

            # Create render layers node
            rl = tree.nodes.new('CompositorNodeRLayers')
            rl.name = f'RL_{cam_name}'
            rl.scene = scene

            # Create translate node
            translate = tree.nodes.new('CompositorNodeTranslate')
            translate.name = f'Translate_{cam_name}'
            translate.inputs[1].default_value = col * render_width  # X offset
            translate.inputs[2].default_value = (rows - 1 - row) * render_height  # Y offset (top-left origin)

            # Connect: RL -> Translate
            tree.links.new(rl.outputs['Image'], translate.inputs[0])

            # Combine with previous using Mix node
            if prev_output is None:
                prev_output = translate
            else:
                mix = tree.nodes.new('CompositorNodeMixRGB')
                mix.name = f'Mix_{cam_name}'
                mix.blend_type = 'ADD'
                mix.inputs['Fac'].default_value = 1.0

                tree.links.new(prev_output.outputs[0], mix.inputs[1])
                tree.links.new(translate.outputs[0], mix.inputs[2])
                prev_output = mix

        # Connect final output to composite
        if prev_output:
            tree.links.new(prev_output.outputs[0], composite.inputs['Image'])

        # Set output resolution
        scene.render.resolution_x = render_width * cols
        scene.render.resolution_y = render_height * rows

        return True

    except Exception:
        return False


def render_multi_camera_composite(
    output_path: str,
    config: MultiCameraLayout,
    camera_names: List[str]
) -> bool:
    """
    Render multi-camera composite to file.

    Args:
        output_path: Path to save the rendered image
        config: MultiCameraLayout with composite settings
        camera_names: List of camera names to composite

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Setup compositor
        if not setup_multi_camera_composite(config, camera_names):
            return False

        # Set output path
        bpy.context.scene.render.filepath = output_path

        # Render
        bpy.ops.render.render(write_still=True)

        return True

    except Exception:
        return False


def clear_multi_camera_composite() -> bool:
    """
    Remove all multi-camera composite nodes and reset resolution.

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene
        if not scene.use_nodes or scene.node_tree is None:
            return True  # Nothing to clear

        tree = scene.node_tree

        # Nodes to remove (composite-related)
        nodes_to_remove = []
        for node in tree.nodes:
            if node.name.startswith('RL_') or node.name.startswith('Translate_') or node.name.startswith('Mix_'):
                nodes_to_remove.append(node)

        for node in nodes_to_remove:
            tree.nodes.remove(node)

        # Reset to default resolution (could store original, but 2048x2048 is reasonable default)
        scene.render.resolution_x = 2048
        scene.render.resolution_y = 2048

        # Reconnect Render Layers to Composite if both exist
        render_layers = tree.nodes.get('Render Layers')
        composite = tree.nodes.get('Composite')

        if render_layers and composite:
            # Remove existing links to composite
            for link in list(tree.links):
                if link.to_node == composite:
                    tree.links.remove(link)

            # Create direct connection
            tree.links.new(render_layers.outputs['Image'], composite.inputs['Image'])

        return True

    except Exception:
        return False
