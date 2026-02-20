"""
Side-Scroller Camera System

Provides side-scroller camera setup, parallax layer separation,
and rendering for game asset generation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List, TYPE_CHECKING
import math

from lib.retro.isometric_types import SideScrollerConfig

if TYPE_CHECKING:
    try:
        import bpy
        from mathutils import Vector
        HAS_BLENDER = True
    except ImportError:
        HAS_BLENDER = False


# =============================================================================
# CAMERA CONFIGURATION
# =============================================================================

@dataclass
class ParallaxLayer:
    """
    A single parallax layer.

    Attributes:
        index: Layer index (0 = farthest)
        name: Layer name
        depth: Depth value (affects scroll speed)
        objects: Objects in this layer
        visible: Whether layer is visible
    """
    index: int = 0
    name: str = ""
    depth: float = 1.0
    objects: List[Any] = field(default_factory=list)
    visible: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "index": self.index,
            "name": self.name,
            "depth": self.depth,
            "visible": self.visible,
            "object_count": len(self.objects),
        }


@dataclass
class SideScrollerCameraConfig:
    """
    Camera configuration for side-scroller rendering.

    Attributes:
        name: Camera name
        location: Camera position (x, y, z)
        view_direction: View direction (side, front, top)
        orthographic: Use orthographic projection
        orthographic_scale: Orthographic scale factor
        clip_start: Near clipping distance
        clip_end: Far clipping distance
    """
    name: str = "SideScrollerCamera"
    location: Tuple[float, float, float] = (0.0, -15.0, 5.0)
    view_direction: str = "side"
    orthographic: bool = True
    orthographic_scale: float = 10.0
    clip_start: float = 0.1
    clip_end: float = 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "location": list(self.location),
            "view_direction": self.view_direction,
            "orthographic": self.orthographic,
            "orthographic_scale": self.orthographic_scale,
            "clip_start": self.clip_start,
            "clip_end": self.clip_end,
        }


# =============================================================================
# CAMERA FUNCTIONS
# =============================================================================

def create_side_scroller_camera_config(
    config: SideScrollerConfig
) -> SideScrollerCameraConfig:
    """
    Create camera configuration for side-scroller view.

    Args:
        config: Side-scroller configuration

    Returns:
        SideScrollerCameraConfig with appropriate settings
    """
    # Position camera based on view direction
    if config.view_direction == "side":
        # Side view (looking along Y axis)
        location = (0.0, -config.camera_distance, 0.0)
        rotation = (math.pi / 2, 0.0, 0.0)  # Look forward along Y
    elif config.view_direction == "front":
        # Front view (looking along X axis)
        location = (-config.camera_distance, 0.0, 0.0)
        rotation = (math.pi / 2, 0.0, math.pi / 2)  # Look along X
    elif config.view_direction == "top":
        # Top-down view (looking down Z axis)
        location = (0.0, 0.0, config.camera_distance)
        rotation = (0.0, 0.0, 0.0)  # Look down
    else:
        # Default to side view
        location = (0.0, -config.camera_distance, 0.0)
        rotation = (math.pi / 2, 0.0, 0.0)

    return SideScrollerCameraConfig(
        name="SideScrollerCamera",
        location=location,
        view_direction=config.view_direction,
        orthographic=config.orthographic,
        orthographic_scale=config.camera_distance / 2,
    )


def get_camera_rotation_for_view(view_direction: str) -> Tuple[float, float, float]:
    """
    Get camera rotation for a view direction.

    Args:
        view_direction: View direction (side, front, top)

    Returns:
        Euler angles (x, y, z) in radians
    """
    rotations = {
        "side": (math.pi / 2, 0.0, 0.0),
        "front": (math.pi / 2, 0.0, math.pi / 2),
        "top": (0.0, 0.0, 0.0),
    }
    return rotations.get(view_direction, (math.pi / 2, 0.0, 0.0))


# =============================================================================
# PARALLAX FUNCTIONS
# =============================================================================

def separate_parallax_layers(
    scene: Any,
    config: SideScrollerConfig
) -> List[ParallaxLayer]:
    """
    Separate scene into parallax layers based on depth.

    Args:
        scene: Blender scene
        config: Side-scroller configuration

    Returns:
        List of ParallaxLayer objects
    """
    layers = []

    for i in range(config.parallax_layers):
        layer = ParallaxLayer(
            index=i,
            name=config.get_layer_name(i),
            depth=config.get_layer_depth(i),
            objects=[],
        )
        layers.append(layer)

    try:
        import bpy

        # Assign objects to layers based on Z position or collection
        if config.auto_assign_depth:
            # Get Z range
            objects_3d = [obj for obj in scene.objects if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META'}]

            if objects_3d:
                z_min = min(obj.location.z for obj in objects_3d)
                z_max = max(obj.location.z for obj in objects_3d)
                z_range = z_max - z_min if z_max != z_min else 1.0

                for obj in objects_3d:
                    # Normalize Z position to layer index
                    normalized = (obj.location.z - z_min) / z_range
                    layer_index = int(normalized * (config.parallax_layers - 1))
                    layer_index = max(0, min(layer_index, config.parallax_layers - 1))

                    layers[layer_index].objects.append(obj)
        else:
            # Assign by collection
            for i, layer_name in enumerate(config.layer_names):
                collection_name = layer_name
                if collection_name in bpy.data.collections:
                    collection = bpy.data.collections[collection_name]
                    layers[i].objects = list(collection.objects)

    except ImportError:
        pass

    return layers


def calculate_parallax_offset(
    layer_depth: float,
    camera_move: float
) -> float:
    """
    Calculate parallax scroll amount for layer.

    Args:
        layer_depth: Layer depth (0.0 = far, 1.0+ = near)
        camera_move: Camera movement in world units

    Returns:
        Layer scroll offset in world units
    """
    # Deeper layers move slower
    return camera_move * (1.0 / layer_depth)


def calculate_layer_scroll_speed(
    layer_depth: float,
    base_speed: float = 1.0
) -> float:
    """
    Calculate scroll speed for a parallax layer.

    Args:
        layer_depth: Layer depth (0.0 = far, 1.0+ = near)
        base_speed: Base scroll speed

    Returns:
        Scroll speed multiplier for this layer
    """
    # Closer layers scroll faster
    return base_speed * layer_depth


def get_parallax_positions(
    layers: List[ParallaxLayer],
    camera_x: float,
    frame: int,
    total_frames: int
) -> Dict[str, float]:
    """
    Calculate parallax positions for all layers at a frame.

    Args:
        layers: List of parallax layers
        camera_x: Camera X position
        frame: Current frame number
        total_frames: Total number of frames

    Returns:
        Dict mapping layer names to X offsets
    """
    positions = {}

    for layer in layers:
        # Calculate offset based on depth
        offset = camera_x / layer.depth
        positions[layer.name] = offset

    return positions


# =============================================================================
# RENDERING FUNCTIONS
# =============================================================================

def render_parallax_layer(
    scene: Any,
    layer: ParallaxLayer,
    config: SideScrollerConfig,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Render single parallax layer.

    Args:
        scene: Blender scene
        layer: Parallax layer to render
        config: Side-scroller configuration
        output_path: Optional output path

    Returns:
        Render result dict
    """
    result = {
        "layer_name": layer.name,
        "layer_index": layer.index,
        "depth": layer.depth,
        "rendered": False,
        "path": output_path,
        "errors": [],
    }

    try:
        import bpy

        # Hide all objects
        for obj in scene.objects:
            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                obj.hide_render = True
                obj.hide_viewport = True

        # Show only objects in this layer
        for obj in layer.objects:
            obj.hide_render = False
            obj.hide_viewport = False

        # Set up camera
        camera = None
        for obj in scene.objects:
            if obj.type == 'CAMERA':
                camera = obj
                break

        if camera:
            cam_config = create_side_scroller_camera_config(config)
            camera.location = cam_config.location

            if cam_config.orthographic:
                camera.data.type = 'ORTHO'
                camera.data.ortho_scale = cam_config.orthographic_scale

            scene.camera = camera

        # Render
        if output_path:
            scene.render.filepath = output_path
            bpy.ops.render.render(write_still=True)
            result["rendered"] = True

    except ImportError:
        result["errors"].append("Blender not available")
    except Exception as e:
        result["errors"].append(str(e))

    # Restore visibility (in finally-like manner)
    try:
        import bpy
        for obj in scene.objects:
            obj.hide_render = False
            obj.hide_viewport = False
    except:
        pass

    return result


def render_all_parallax_layers(
    scene: Any,
    config: SideScrollerConfig,
    output_dir: str
) -> List[Dict[str, Any]]:
    """
    Render all parallax layers.

    Args:
        scene: Blender scene
        config: Side-scroller configuration
        output_dir: Output directory

    Returns:
        List of render results
    """
    import os

    results = []
    layers = separate_parallax_layers(scene, config)

    try:
        os.makedirs(output_dir, exist_ok=True)
    except:
        pass

    for layer in layers:
        output_path = os.path.join(output_dir, f"{layer.name}.png")
        result = render_parallax_layer(scene, layer, config, output_path)
        results.append(result)

    return results


# =============================================================================
# ANIMATION FUNCTIONS
# =============================================================================

def create_parallax_animation(
    layers: List[ParallaxLayer],
    camera_move: Tuple[float, float, float],
    frames: int,
    config: SideScrollerConfig
) -> List[List[Dict[str, float]]]:
    """
    Generate animated parallax sequence.

    Args:
        layers: List of parallax layers
        camera_move: (start_x, end_x, speed) for camera movement
        frames: Number of frames
        config: Side-scroller configuration

    Returns:
        List of frame data, each containing layer positions
    """
    start_x, end_x, speed = camera_move
    sequence = []

    for frame in range(frames):
        # Calculate camera position at this frame
        t = frame / (frames - 1) if frames > 1 else 0
        camera_x = start_x + (end_x - start_x) * t

        # Calculate positions for each layer
        frame_data = {
            "frame": frame,
            "camera_x": camera_x,
            "layers": {},
        }

        for layer in layers:
            offset = calculate_parallax_offset(layer.depth, camera_x)
            frame_data["layers"][layer.name] = offset

        sequence.append(frame_data)

    return sequence


def animate_parallax_layers(
    scene: Any,
    config: SideScrollerConfig,
    start_frame: int = 1,
    end_frame: int = 60,
    camera_start: float = 0.0,
    camera_end: float = 10.0
) -> Dict[str, Any]:
    """
    Animate parallax layers over a frame range.

    Args:
        scene: Blender scene
        config: Side-scroller configuration
        start_frame: Start frame number
        end_frame: End frame number
        camera_start: Camera start X position
        camera_end: Camera end X position

    Returns:
        Animation result dict
    """
    result = {
        "animated": False,
        "frames": end_frame - start_frame + 1,
        "layers_animated": 0,
        "errors": [],
    }

    try:
        import bpy

        # Get camera
        camera = None
        for obj in scene.objects:
            if obj.type == 'CAMERA':
                camera = obj
                break

        if not camera:
            result["errors"].append("No camera found")
            return result

        # Animate camera
        scene.frame_set(start_frame)
        camera.location.x = camera_start
        camera.keyframe_insert(data_path="location", index=0)

        scene.frame_set(end_frame)
        camera.location.x = camera_end
        camera.keyframe_insert(data_path="location", index=0)

        # Separate layers and animate each
        layers = separate_parallax_layers(scene, config)

        for layer in layers:
            for obj in layer.objects:
                # Calculate parallax animation
                parallax_start = calculate_parallax_offset(layer.depth, camera_start)
                parallax_end = calculate_parallax_offset(layer.depth, camera_end)

                # Set keyframes
                scene.frame_set(start_frame)
                obj.location.x = parallax_start
                obj.keyframe_insert(data_path="location", index=0)

                scene.frame_set(end_frame)
                obj.location.x = parallax_end
                obj.keyframe_insert(data_path="location", index=0)

                result["layers_animated"] += 1

        result["animated"] = True

    except ImportError:
        result["errors"].append("Blender not available")
    except Exception as e:
        result["errors"].append(str(e))

    return result


# =============================================================================
# DEPTH ASSIGNMENT HELPERS
# =============================================================================

def assign_depth_by_z(
    objects: List[Any],
    config: SideScrollerConfig
) -> Dict[str, int]:
    """
    Assign objects to layers based on Z position.

    Args:
        objects: List of objects with location.z attribute
        config: Side-scroller configuration

    Returns:
        Dict mapping object names to layer indices
    """
    assignments = {}

    if not objects:
        return assignments

    # Get Z range
    try:
        z_values = [obj.location.z for obj in objects if hasattr(obj, 'location')]
        if not z_values:
            return assignments

        z_min = min(z_values)
        z_max = max(z_values)
        z_range = z_max - z_min if z_max != z_min else 1.0

        for obj in objects:
            if hasattr(obj, 'location'):
                # Normalize Z to layer index
                normalized = (obj.location.z - z_min) / z_range
                layer_index = int(normalized * (config.parallax_layers - 1))
                layer_index = max(0, min(layer_index, config.parallax_layers - 1))
                assignments[obj.name] = layer_index
    except:
        pass

    return assignments


def assign_depth_by_collection(
    scene: Any,
    layer_names: List[str]
) -> Dict[str, int]:
    """
    Assign collections to specific layers.

    Args:
        scene: Blender scene
        layer_names: List of collection names matching layer order

    Returns:
        Dict mapping object names to layer indices
    """
    assignments = {}

    try:
        import bpy

        for layer_index, collection_name in enumerate(layer_names):
            if collection_name in bpy.data.collections:
                collection = bpy.data.collections[collection_name]
                for obj in collection.objects:
                    assignments[obj.name] = layer_index

    except ImportError:
        pass

    return assignments


def assign_depth_by_name_pattern(
    objects: List[Any],
    patterns: Dict[str, int]
) -> Dict[str, int]:
    """
    Assign objects to layers based on name patterns.

    Args:
        objects: List of objects
        patterns: Dict mapping pattern strings to layer indices

    Returns:
        Dict mapping object names to layer indices
    """
    assignments = {}

    for obj in objects:
        name = obj.name.lower() if hasattr(obj, 'name') else ""

        for pattern, layer_index in patterns.items():
            if pattern.lower() in name:
                assignments[obj.name] = layer_index
                break

    return assignments


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_layer_visibility_at_depth(
    depth: float,
    camera_z: float,
    near_clip: float = 0.1,
    far_clip: float = 1000.0
) -> bool:
    """
    Check if a layer at given depth is visible.

    Args:
        depth: Layer depth
        camera_z: Camera Z position
        near_clip: Near clipping distance
        far_clip: Far clipping distance

    Returns:
        True if layer should be visible
    """
    distance = abs(depth - camera_z)
    return near_clip <= distance <= far_clip


def calculate_optimal_layer_count(
    scene_depth: float,
    min_separation: float = 1.0
) -> int:
    """
    Calculate optimal number of parallax layers.

    Args:
        scene_depth: Total depth of scene
        min_separation: Minimum separation between layers

    Returns:
        Recommended number of layers
    """
    # At least 2 layers, at most 8
    layers = max(2, min(8, int(scene_depth / min_separation)))
    return layers


def generate_layer_depths(
    layer_count: int,
    distribution: str = "linear"
) -> List[float]:
    """
    Generate depth values for layers.

    Args:
        layer_count: Number of layers
        distribution: Distribution type (linear, exponential, custom)

    Returns:
        List of depth values
    """
    if distribution == "linear":
        return [1.0 / (i + 1) for i in range(layer_count)]
    elif distribution == "exponential":
        return [0.5 ** i for i in range(layer_count)]
    elif distribution == "uniform":
        return [(i + 1) / layer_count for i in range(layer_count)]
    else:
        # Default to linear
        return [1.0 / (i + 1) for i in range(layer_count)]


def merge_parallax_layers(
    layer_images: List[Any],
    offsets: List[float]
) -> Any:
    """
    Merge multiple parallax layer images.

    Args:
        layer_images: List of layer images (PIL Images or numpy arrays)
        offsets: X offsets for each layer

    Returns:
        Merged image
    """
    # This is a placeholder - actual implementation would use PIL or numpy
    # to composite layers with offsets
    if not layer_images:
        return None

    # Return first layer as fallback
    return layer_images[0]
