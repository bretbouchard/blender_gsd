"""
Compositor Integration Module (Phase 7.4)

Provides functions to generate Blender compositor nodes from tracking data.
Supports stabilization, corner pin, alpha over compositing, shadow catchers,
and ST-Map lens distortion workflows.

Node Creation Functions:
    create_stabilization_nodes: Create Translate->Rotate->Scale chain
    create_corner_pin_nodes: Create corner pin node from planar tracks
    create_alpha_over_composite: Create AlphaOver node for CG/footage
    create_shadow_composite: Create multiply composite for shadow passes

Utility Functions:
    create_image_node: Load footage/image for compositing
    create_mix_node: Create MixRGB node with specified blend type
    apply_stmap_distortion: Apply ST-Map for lens distortion
    setup_lens_distortion_workflow: Complete distortion workflow
    load_composite_preset: Load preset from composite_presets.yaml
    clear_compositor_tree: Clear all compositor nodes

Usage:
    from lib.cinematic.tracking.compositor import (
        create_stabilization_nodes,
        create_corner_pin_nodes,
        create_alpha_over_composite,
        CompositeConfig,
    )

    # Create stabilization chain
    nodes = create_stabilization_nodes(tree, stabilization_data, (1, 100))

    # Create corner pin
    nodes = create_corner_pin_nodes(tree, corners_per_frame, (1, 100), 1920, 1080)

    # Load composite preset
    config = load_composite_preset("over_footage")
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
import math

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

try:
    import yaml
except ImportError:
    yaml = None


# =============================================================================
# COMPOSITE CONFIGURATION
# =============================================================================

@dataclass
class CompositeConfig:
    """
    Configuration for composite mode rendering.

    Defines how CG renders composite over background footage with
    optional lens distortion, stabilization, and shadow catching.

    Attributes:
        mode: Composite mode (over_footage, over_plate, multiply, add, screen)
        background_source: Background type (footage, image, none)
        lens_distortion: Distortion settings dict with apply_to_cg, st_map_path
        stabilization: Stabilization settings dict with enabled, tracks
        shadow_catcher: Enable shadow catcher composite
        film_transparent: Enable transparent film background
    """
    mode: str = "over_footage"
    background_source: str = "footage"
    lens_distortion: Dict[str, Any] = field(default_factory=lambda: {
        "apply_to_cg": True,
        "st_map_path": None
    })
    stabilization: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "tracks": "all"
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
    def from_dict(cls, data: Dict[str, Any]) -> CompositeConfig:
        """Create from dictionary."""
        return cls(
            mode=data.get("mode", "over_footage"),
            background_source=data.get("background_source", "footage"),
            lens_distortion=data.get("lens_distortion", {"apply_to_cg": True, "st_map_path": None}),
            stabilization=data.get("stabilization", {"enabled": False, "tracks": "all"}),
            shadow_catcher=data.get("shadow_catcher", True),
            film_transparent=data.get("film_transparent", True),
        )


# =============================================================================
# COMPOSITOR UTILITIES
# =============================================================================

def _ensure_compositor_enabled(scene: Any = None) -> bool:
    """
    Enable compositor if not already enabled.

    Args:
        scene: Optional Blender scene (uses context.scene if None)

    Returns:
        True if successful, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if scene is None:
            if not hasattr(bpy, "context") or bpy.context.scene is None:
                return False
            scene = bpy.context.scene

        scene.use_nodes = True

        # Ensure Render Layers node exists
        tree = scene.node_tree
        if tree is None:
            return False

        render_layers = tree.nodes.get('Render Layers')
        if not render_layers:
            render_layers = tree.nodes.new('CompositorNodeRLayers')
            render_layers.name = 'Render Layers'

        # Ensure Composite node exists
        composite = tree.nodes.get('Composite')
        if not composite:
            composite = tree.nodes.new('CompositorNodeComposite')
            composite.name = 'Composite'

        return True

    except Exception:
        return False


def _get_or_create_node(
    tree: Any,
    node_type: str,
    name: str,
    location: Tuple[float, float] = (0, 0)
) -> Any:
    """
    Get existing node or create new one.

    Args:
        tree: Compositor node tree
        node_type: Blender node type (e.g., 'CompositorNodeTranslate')
        name: Node name
        location: Node position (x, y)

    Returns:
        Created or existing node
    """
    existing = tree.nodes.get(name)
    if existing:
        return existing

    node = tree.nodes.new(node_type)
    node.name = name
    node.label = name
    node.location = location
    return node


def _position_node_chain(
    nodes: List[Any],
    start_x: float = 0,
    start_y: float = 0,
    spacing: float = 300
) -> None:
    """
    Position nodes in readable horizontal chain layout.

    Args:
        nodes: List of nodes to position
        start_x: Starting X position
        start_y: Starting Y position
        spacing: Horizontal spacing between nodes
    """
    for i, node in enumerate(nodes):
        node.location = (start_x + i * spacing, start_y)


def clear_compositor_tree(scene: Any = None) -> int:
    """
    Clear all compositor nodes from scene.

    Args:
        scene: Optional Blender scene (uses context.scene if None)

    Returns:
        Number of nodes removed
    """
    if not BLENDER_AVAILABLE:
        return 0

    try:
        if scene is None:
            if not hasattr(bpy, "context") or bpy.context.scene is None:
                return 0
            scene = bpy.context.scene

        if not scene.use_nodes or scene.node_tree is None:
            return 0

        tree = scene.node_tree
        count = len(tree.nodes)
        tree.nodes.clear()

        # Recreate Render Layers and Composite
        render_layers = tree.nodes.new('CompositorNodeRLayers')
        render_layers.name = 'Render Layers'

        composite = tree.nodes.new('CompositorNodeComposite')
        composite.name = 'Composite'

        return count

    except Exception:
        return 0


# =============================================================================
# NODE CREATION FUNCTIONS
# =============================================================================

def create_translate_node(
    tree: Any,
    name: str = "Translate",
    x_value: float = 0.0,
    y_value: float = 0.0,
    location: Tuple[float, float] = (0, 0)
) -> Any:
    """
    Create a translate node.

    Args:
        tree: Compositor node tree
        name: Node name
        x_value: X translation value
        y_value: Y translation value
        location: Node position

    Returns:
        Created translate node
    """
    node = _get_or_create_node(tree, 'CompositorNodeTranslate', name, location)
    node.use_relative = False  # Use absolute pixel values
    node.inputs['X'].default_value = x_value
    node.inputs['Y'].default_value = y_value
    return node


def create_rotate_node(
    tree: Any,
    name: str = "Rotate",
    angle_radians: float = 0.0,
    location: Tuple[float, float] = (300, 0)
) -> Any:
    """
    Create a rotate node.

    Args:
        tree: Compositor node tree
        name: Node name
        angle_radians: Rotation angle in radians
        location: Node position

    Returns:
        Created rotate node
    """
    node = _get_or_create_node(tree, 'CompositorNodeRotate', name, location)
    node.inputs['Angle'].default_value = angle_radians
    return node


def create_scale_node(
    tree: Any,
    name: str = "Scale",
    scale_factor: float = 1.0,
    location: Tuple[float, float] = (600, 0)
) -> Any:
    """
    Create a scale node.

    Args:
        tree: Compositor node tree
        name: Node name
        scale_factor: Scale multiplier
        location: Node position

    Returns:
        Created scale node
    """
    node = _get_or_create_node(tree, 'CompositorNodeScale', name, location)
    # Set to relative scale mode
    node.space = 'RELATIVE'
    node.inputs['X'].default_value = scale_factor
    node.inputs['Y'].default_value = scale_factor
    return node


def create_stabilization_nodes(
    tree: Any,
    stabilization_data: List[Dict[str, Any]],
    frame_range: Tuple[int, int],
    scene: Any = None
) -> Dict[str, Any]:
    """
    Create stabilization node chain (Translate -> Rotate -> Scale).

    Creates a chain of compositor nodes with keyframed values from
    stabilization data for per-frame 2D stabilization.

    Args:
        tree: Compositor node tree
        stabilization_data: List of per-frame stabilization dicts with keys:
            frame, translate_x, translate_y, rotation, scale
        frame_range: Frame range (start, end)
        scene: Optional scene for keyframe insertion

    Returns:
        Dict with 'translate', 'rotate', 'scale', 'input', 'output' references
    """
    if not BLENDER_AVAILABLE:
        return {}

    # Create nodes
    translate_node = create_translate_node(tree, "Stabilize_Translate", 0, 0, (0, 0))
    rotate_node = create_rotate_node(tree, "Stabilize_Rotate", 0, (300, 0))
    scale_node = create_scale_node(tree, "Stabilize_Scale", 1.0, (600, 0))

    # Keyframe stabilization values
    if scene is None and hasattr(bpy, "context"):
        scene = bpy.context.scene

    for frame_data in stabilization_data:
        frame = frame_data.get('frame', 0)

        # Get stabilization values (invert for stabilization)
        tx = -frame_data.get('translate_x', 0.0)
        ty = -frame_data.get('translate_y', 0.0)
        rot = -frame_data.get('rotation', 0.0)
        scl = 1.0 / frame_data.get('scale', 1.0) if frame_data.get('scale', 1.0) != 0 else 1.0

        if scene:
            scene.frame_set(frame)

        # Keyframe translate
        translate_node.inputs['X'].default_value = tx
        translate_node.inputs['Y'].default_value = ty
        if scene:
            translate_node.inputs['X'].keyframe_insert('default_value', frame=frame)
            translate_node.inputs['Y'].keyframe_insert('default_value', frame=frame)

        # Keyframe rotate
        rotate_node.inputs['Angle'].default_value = rot
        if scene:
            rotate_node.inputs['Angle'].keyframe_insert('default_value', frame=frame)

        # Keyframe scale
        scale_node.inputs['X'].default_value = scl
        scale_node.inputs['Y'].default_value = scl
        if scene:
            scale_node.inputs['X'].keyframe_insert('default_value', frame=frame)
            scale_node.inputs['Y'].keyframe_insert('default_value', frame=frame)

    # Connect chain: Translate -> Rotate -> Scale
    tree.links.new(translate_node.outputs['Image'], rotate_node.inputs['Image'])
    tree.links.new(rotate_node.outputs['Image'], scale_node.inputs['Image'])

    return {
        'translate': translate_node,
        'rotate': rotate_node,
        'scale': scale_node,
        'input': translate_node.inputs['Image'],
        'output': scale_node.outputs['Image'],
    }


def create_corner_pin_nodes(
    tree: Any,
    corners_per_frame: List[List[Tuple[float, float]]],
    frame_range: Tuple[int, int],
    width: int,
    height: int,
    scene: Any = None
) -> Dict[str, Any]:
    """
    Create corner pin node for planar tracking.

    Creates a corner pin node with keyframed corner positions derived
    from planar tracking data. Corners are converted from pixel to
    relative coordinates (0-1).

    Args:
        tree: Compositor node tree
        corners_per_frame: List of 4 corners [(x,y), ...] per frame in PIXEL coordinates
        frame_range: Frame range (start, end)
        width: Image width for coordinate conversion
        height: Image height for coordinate conversion
        scene: Optional scene for keyframe insertion

    Returns:
        Dict with 'corner_pin', 'input', 'output' references
    """
    if not BLENDER_AVAILABLE:
        return {}

    # Create corner pin node
    corner_pin = _get_or_create_node(
        tree, 'CompositorNodeCornerPin',
        'CornerPin', (0, 0)
    )

    # Socket mapping: Upper Left=1, Upper Right=2, Lower Right=3, Lower Left=4
    corner_sockets = [
        corner_pin.inputs[1],  # Upper Left
        corner_pin.inputs[2],  # Upper Right
        corner_pin.inputs[3],  # Lower Right
        corner_pin.inputs[4],  # Lower Left
    ]

    if scene is None and hasattr(bpy, "context"):
        scene = bpy.context.scene

    # Keyframe corners per frame
    start_frame = frame_range[0]
    for i, corners_px in enumerate(corners_per_frame):
        frame = start_frame + i

        # Convert to relative coordinates (0-1)
        corners_relative = [
            (c[0] / width, c[1] / height) for c in corners_px
        ]

        if scene:
            scene.frame_set(frame)

        # Set corner positions
        for j, (rx, ry) in enumerate(corners_relative):
            if j < len(corner_sockets):
                socket = corner_sockets[j]
                socket.default_value = (rx, ry)
                if scene:
                    socket.keyframe_insert('default_value', frame=frame)

    return {
        'corner_pin': corner_pin,
        'input': corner_pin.inputs['Image'],
        'output': corner_pin.outputs['Image'],
    }


def create_image_node(
    tree: Any,
    image_path: str,
    name: str = "Image"
) -> Any:
    """
    Create image node for loading footage.

    Args:
        tree: Compositor node tree
        image_path: Path to image or video file
        name: Node name

    Returns:
        Created image node
    """
    node = _get_or_create_node(
        tree, 'CompositorNodeImage',
        name, (-600, 0)
    )

    if BLENDER_AVAILABLE and image_path:
        # Try to load existing image or create new
        image = bpy.data.images.get(name)
        if not image:
            try:
                image = bpy.data.images.load(image_path, check_existing=True)
                image.name = name
            except Exception:
                pass

        if image:
            node.image = image

    return node


def create_alpha_over_composite(
    tree: Any,
    name: str = "AlphaOver",
    location: Tuple[float, float] = (600, 0)
) -> Any:
    """
    Create AlphaOver node for CG over background compositing.

    Socket layout:
    - Fac (0): Blend factor (0=BG only, 1=FG only)
    - FG (1): Foreground (CG render)
    - BG (2): Background (footage/plate)

    Args:
        tree: Compositor node tree
        name: Node name
        location: Node position

    Returns:
        Created AlphaOver node
    """
    node = _get_or_create_node(
        tree, 'CompositorNodeAlphaOver',
        name, location
    )
    node.use_premultiply = True  # CG renders are premultiplied
    return node


def create_mix_node(
    tree: Any,
    blend_type: str,
    name: str = "Mix",
    location: Tuple[float, float] = (600, 0),
    factor: float = 1.0
) -> Any:
    """
    Create MixRGB node with specified blend type.

    Args:
        tree: Compositor node tree
        blend_type: Blend mode (MULTIPLY, ADD, SCREEN, OVERLAY, etc.)
        name: Node name
        location: Node position
        factor: Blend factor (0-1)

    Returns:
        Created MixRGB node
    """
    node = _get_or_create_node(
        tree, 'CompositorNodeMixRGB',
        name, location
    )
    node.blend_type = blend_type
    node.inputs['Fac'].default_value = factor
    return node


def create_shadow_composite(
    tree: Any,
    background_image: Optional[str] = None,
    scene: Any = None
) -> Dict[str, Any]:
    """
    Create shadow catcher composite (multiply shadow over background).

    Uses a MixRGB node with MULTIPLY blend mode to composite
    the shadow pass over the background image.

    Args:
        tree: Compositor node tree
        background_image: Optional path to background image
        scene: Optional scene reference

    Returns:
        Dict with 'background', 'shadow_mix', 'output' references
    """
    if not BLENDER_AVAILABLE:
        return {}

    # Get or create Render Layers node
    render_layers = tree.nodes.get('Render Layers')
    if not render_layers:
        render_layers = tree.nodes.new('CompositorNodeRLayers')
        render_layers.name = 'Render Layers'

    # Create background image node if provided
    bg_node = None
    if background_image:
        bg_node = create_image_node(tree, background_image, "Background_Plate")

    # Create multiply node for shadow composite
    shadow_mix = create_mix_node(
        tree, 'MULTIPLY',
        'Shadow_Multiply', (600, 0), 1.0
    )

    # Get or create Composite node
    composite = tree.nodes.get('Composite')
    if not composite:
        composite = tree.nodes.new('CompositorNodeComposite')
        composite.name = 'Composite'

    result = {
        'shadow_mix': shadow_mix,
        'render_layers': render_layers,
        'composite': composite,
        'output': shadow_mix.outputs['Image'],
    }

    if bg_node:
        result['background'] = bg_node

    return result


def apply_stmap_distortion(
    tree: Any,
    stmap_image: str,
    source_node: Any
) -> Any:
    """
    Apply ST-Map distortion using MapUV node.

    ST-Maps encode UV coordinates in the RG channels for lens distortion.
    The MapUV node uses these coordinates to remap the source image.

    Args:
        tree: Compositor node tree
        stmap_image: Path to ST-Map image file
        source_node: Source node to distort

    Returns:
        Created MapUV node
    """
    if not BLENDER_AVAILABLE:
        return None

    # Create ST-Map image node
    stmap_node = create_image_node(tree, stmap_image, "ST_Map")

    # Create MapUV node
    map_uv = _get_or_create_node(
        tree, 'CompositorNodeMapUV',
        'STMap_Distort', (300, 0)
    )

    # Set filtering for quality
    map_uv.filter_type = 'BILINEAR'

    # Connect: ST-Map -> Vector input, Source -> Image input
    tree.links.new(stmap_node.outputs['Image'], map_uv.inputs['Vector'])
    tree.links.new(source_node.outputs['Image'], map_uv.inputs['Image'])

    return map_uv


def setup_lens_distortion_workflow(
    tree: Any,
    mode: str,
    stmap_path: Optional[str],
    cg_node: Any,
    footage_node: Any
) -> Dict[str, Any]:
    """
    Set up complete lens distortion workflow.

    Two modes:
    - 'distort_cg': Apply distortion to CG to match footage
    - 'undistort_footage': Remove distortion from footage

    Args:
        tree: Compositor node tree
        mode: 'distort_cg' or 'undistort_footage'
        stmap_path: Path to ST-Map file
        cg_node: CG render node
        footage_node: Footage node

    Returns:
        Dict with 'final_output' reference
    """
    if not BLENDER_AVAILABLE or not stmap_path:
        return {'final_output': None}

    if mode == 'distort_cg':
        # Apply distortion to CG
        distorted_cg = apply_stmap_distortion(tree, stmap_path, cg_node)
        return {'final_output': distorted_cg.outputs['Image'] if distorted_cg else None}

    elif mode == 'undistort_footage':
        # Remove distortion from footage (use inverse ST-Map)
        undistorted = apply_stmap_distortion(tree, stmap_path, footage_node)
        return {'final_output': undistorted.outputs['Image'] if undistorted else None}

    return {'final_output': None}


def load_composite_preset(preset_name: str) -> CompositeConfig:
    """
    Load composite preset from YAML.

    Args:
        preset_name: Name of preset (over_footage, shadow_multiply, etc.)

    Returns:
        CompositeConfig with preset values

    Raises:
        FileNotFoundError: If preset file doesn't exist
        KeyError: If preset name not found
    """
    preset_path = Path("configs/cinematic/tracking/composite_presets.yaml")
    if not preset_path.exists():
        raise FileNotFoundError(f"Preset file not found: {preset_path}")

    with open(preset_path, encoding="utf-8") as f:
        if yaml:
            data = yaml.safe_load(f)
        else:
            import json
            data = json.load(f)

    presets = data.get('presets', {})
    if preset_name not in presets:
        raise KeyError(f"Preset '{preset_name}' not found. Available: {list(presets.keys())}")

    return CompositeConfig.from_dict(presets[preset_name])


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Configuration
    "CompositeConfig",

    # Utility functions
    "clear_compositor_tree",

    # Node creation functions
    "create_translate_node",
    "create_rotate_node",
    "create_scale_node",
    "create_stabilization_nodes",
    "create_corner_pin_nodes",
    "create_image_node",
    "create_alpha_over_composite",
    "create_mix_node",
    "create_shadow_composite",

    # ST-Map workflow
    "apply_stmap_distortion",
    "setup_lens_distortion_workflow",

    # Preset loading
    "load_composite_preset",

    # Constants
    "BLENDER_AVAILABLE",
]
