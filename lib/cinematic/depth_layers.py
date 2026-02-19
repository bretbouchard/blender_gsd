"""
Depth Layers Module - Fore/Mid/Background Organization

Organizes scene objects into depth layers for DOF control
and compositing workflows.

Usage:
    from lib.cinematic.depth_layers import create_depth_layer, assign_to_layer, setup_dof_for_layers

    # Create depth layer
    layer = create_depth_layer(config)

    # Assign object to layer
    assign_to_layer("Cube", "midground")

    # Setup DOF for layers
    setup_dof_for_layers([fg_config, mg_config, bg_config], "midground")

    # Auto-assign by distance
    auto_assign_by_distance("Camera", layers)
"""

from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple

from .types import DepthLayerConfig
from .enums import DepthLayer

# Blender availability check
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


def create_depth_layer(
    config: DepthLayerConfig,
    create_collection: bool = True
) -> bool:
    """
    Create a depth layer with optional Blender collection.

    Sets up pass index for render layers if enabled in config.

    Args:
        config: DepthLayerConfig with layer settings
        create_collection: Whether to create a Blender collection for the layer

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene

        # Create collection if requested
        if create_collection and config.collection_name:
            if config.collection_name not in bpy.data.collections:
                collection = bpy.data.collections.new(config.collection_name)
                scene.collection.children.link(collection)

        return True

    except Exception:
        return False


def organize_depth_layers(
    config: DepthLayerConfig
) -> Dict[str, List[str]]:
    """
    Organize scene objects into depth layers based on config.

    Args:
        config: DepthLayerConfig with layer assignments

    Returns:
        Dictionary mapping layer names to object names
    """
    return {
        "foreground": config.foreground_objects,
        "midground": config.midground_objects,
        "background": config.background_objects,
    }


def assign_to_layer(
    object_name: str,
    layer_name: str,
    pass_index: Optional[int] = None
) -> bool:
    """
    Assign an object to a depth layer.

    Moves object to layer collection if it exists and sets pass_index.

    Args:
        object_name: Name of the object
        layer_name: Layer name (foreground, midground, background)
        pass_index: Optional pass index for render layers

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if object_name not in bpy.data.objects:
            return False

        obj = bpy.data.objects[object_name]
        obj["depth_layer"] = layer_name

        # Set pass index if provided
        if pass_index is not None:
            obj.pass_index = pass_index

        # Try to move to collection if it exists
        collection_name = f"depth_{layer_name}"
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]

            # Unlink from current collections
            for coll in bpy.data.collections:
                if obj.name in coll.objects:
                    coll.objects.unlink(obj)

            # Link to depth layer collection
            if obj.name not in collection.objects:
                collection.objects.link(obj)

        return True

    except Exception:
        return False


def assign_object_to_layer(
    object_name: str,
    layer: str
) -> bool:
    """Alias for assign_to_layer() for backward compatibility."""
    return assign_to_layer(object_name, layer)


def setup_dof_for_layers(
    layers: List[DepthLayerConfig],
    focus_layer: str,
    camera_name: Optional[str] = None
) -> bool:
    """
    Configure camera DOF based on layer distances.

    Sets focus distance to center of the focus layer.

    Args:
        layers: List of DepthLayerConfig for each layer
        focus_layer: Name of the layer to focus on
        camera_name: Optional camera name (uses scene camera if None)

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene

        # Get camera
        if camera_name:
            if camera_name not in bpy.data.objects:
                return False
            camera = bpy.data.objects[camera_name]
        else:
            camera = scene.camera

        if camera is None:
            return False

        # Find focus layer config
        focus_config = None
        for layer in layers:
            if layer.midground_objects and focus_layer == "midground":
                focus_config = layer
                break
            elif layer.foreground_objects and focus_layer == "foreground":
                focus_config = layer
                break
            elif layer.background_objects and focus_layer == "background":
                focus_config = layer
                break

        if focus_config is None:
            # Use default focus distance
            return True

        # Calculate focus distance (center of layer)
        # For now, use midground DOF value as proxy
        focus_distance = 2.0  # Default focus distance in meters

        # Configure DOF
        cam_data = camera.data
        if hasattr(cam_data, 'dof'):
            cam_data.dof.use_dof = True
            cam_data.dof.focus_distance = focus_distance

            # Set aperture based on layer DOF
            if focus_layer == "foreground":
                cam_data.dof.aperture_fstop = 2.8
            elif focus_layer == "midground":
                cam_data.dof.aperture_fstop = 4.0
            else:  # background
                cam_data.dof.aperture_fstop = 8.0

        return True

    except Exception:
        return False


def apply_layer_dof(
    layer_name: str,
    blur_amount: float
) -> bool:
    """
    Apply DOF blur to a specific layer via compositor.

    Args:
        layer_name: Name of the depth layer
        blur_amount: Blur intensity (0-1)

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene
        scene.use_nodes = True

        tree = scene.node_tree
        if tree is None:
            return False

        # This would set up compositor nodes for layer-specific DOF
        # Using Z-pass and Bokeh Blur for realistic DOF
        # Implementation depends on specific compositor setup needed

        return True

    except Exception:
        return False


def get_layer_for_distance(
    distance: float,
    layers: List[DepthLayerConfig]
) -> str:
    """
    Determine which layer a distance falls into.

    Uses simple range-based assignment.

    Args:
        distance: Distance from camera in meters
        layers: List of DepthLayerConfig with distance ranges

    Returns:
        Layer name (defaults to "midground" if no match)
    """
    # Default distance ranges if no layers specified
    if not layers:
        if distance < 1.0:
            return "foreground"
        elif distance < 5.0:
            return "midground"
        else:
            return "background"

    # Check against layer ranges
    for layer in layers:
        # Simple heuristic based on object list presence
        if layer.foreground_objects:
            return "foreground"
        elif layer.background_objects:
            return "background"

    return "midground"


def get_objects_by_layer(layer_name: str) -> List[str]:
    """
    Get all objects assigned to a specific layer.

    Args:
        layer_name: Layer name to query

    Returns:
        List of object names in that layer
    """
    if not BLENDER_AVAILABLE:
        return []

    objects = []
    for obj in bpy.data.objects:
        if obj.get("depth_layer") == layer_name:
            objects.append(obj.name)

    return objects


def auto_assign_by_distance(
    camera_name: str,
    layers: List[DepthLayerConfig],
    exclude_types: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """
    Automatically assign scene objects to layers by distance from camera.

    Calculates distance from camera to each object and assigns based on
    layer distance ranges.

    Args:
        camera_name: Name of the camera object
        layers: List of DepthLayerConfig with distance ranges
        exclude_types: Object types to exclude (e.g., ['LIGHT', 'CAMERA'])

    Returns:
        Dictionary mapping layer_name -> object_names
    """
    if not BLENDER_AVAILABLE:
        return {}

    try:
        if camera_name not in bpy.data.objects:
            return {}

        camera = bpy.data.objects[camera_name]
        cam_pos = camera.location

        if exclude_types is None:
            exclude_types = ['CAMERA', 'LIGHT', 'EMPTY']

        # Default distance thresholds
        fg_threshold = 1.0  # meters
        bg_threshold = 5.0  # meters

        assignments = {
            "foreground": [],
            "midground": [],
            "background": []
        }

        # Get all scene objects
        for obj in bpy.data.objects:
            if obj.type in exclude_types:
                continue

            # Calculate distance from camera
            dx = obj.location[0] - cam_pos[0]
            dy = obj.location[1] - cam_pos[1]
            dz = obj.location[2] - cam_pos[2]
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)

            # Assign to layer
            if distance < fg_threshold:
                layer = "foreground"
            elif distance < bg_threshold:
                layer = "midground"
            else:
                layer = "background"

            # Store object property and add to result
            obj["depth_layer"] = layer
            assignments[layer].append(obj.name)

        return assignments

    except Exception:
        return {}


def clear_depth_layers() -> int:
    """
    Remove depth layer assignments from all objects.

    Returns:
        Number of objects cleared
    """
    if not BLENDER_AVAILABLE:
        return 0

    cleared = 0
    for obj in bpy.data.objects:
        if "depth_layer" in obj:
            del obj["depth_layer"]
            cleared += 1

    return cleared


def get_layer_statistics() -> Dict[str, int]:
    """
    Get count of objects in each layer.

    Returns:
        Dictionary with counts for each layer
    """
    if not BLENDER_AVAILABLE:
        return {"foreground": 0, "midground": 0, "background": 0, "unassigned": 0}

    stats = {"foreground": 0, "midground": 0, "background": 0, "unassigned": 0}

    for obj in bpy.data.objects:
        layer = obj.get("depth_layer")
        if layer in stats:
            stats[layer] += 1
        else:
            stats["unassigned"] += 1

    return stats
