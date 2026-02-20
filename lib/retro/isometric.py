"""
Isometric Camera System

Provides isometric camera setup, projection math, and rendering
for game asset generation from 3D scenes.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List, TYPE_CHECKING
import math

from lib.retro.isometric_types import (
    IsometricConfig,
    IsometricRenderResult,
    get_isometric_angle,
    ISOMETRIC_ANGLES,
)

if TYPE_CHECKING:
    try:
        import bpy
        from mathutils import Vector, Euler, Matrix
        HAS_BLENDER = True
    except ImportError:
        HAS_BLENDER = False


# =============================================================================
# CAMERA CONFIGURATION
# =============================================================================

@dataclass
class CameraConfig:
    """
    Camera configuration for isometric rendering.

    Attributes:
        name: Camera name
        location: Camera position (x, y, z)
        rotation: Camera rotation in Euler angles (x, y, z) in radians
        orthographic_scale: Orthographic scale factor
        clip_start: Near clipping distance
        clip_end: Far clipping distance
    """
    name: str = "IsometricCamera"
    location: Tuple[float, float, float] = (10.0, -10.0, 10.0)
    rotation: Tuple[float, float, float] = (0.7854, 0.0, 0.7854)  # 45, 0, 45 degrees
    orthographic_scale: float = 10.0
    clip_start: float = 0.1
    clip_end: float = 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "location": list(self.location),
            "rotation": list(self.rotation),
            "orthographic_scale": self.orthographic_scale,
            "clip_start": self.clip_start,
            "clip_end": self.clip_end,
        }


# =============================================================================
# ISOMETRIC CAMERA FUNCTIONS
# =============================================================================

def create_isometric_camera_config(config: IsometricConfig) -> CameraConfig:
    """
    Create camera configuration for isometric view.

    Args:
        config: Isometric configuration

    Returns:
        CameraConfig with isometric settings
    """
    elevation, rotation = config.get_angles()

    # Convert to radians
    elev_rad = math.radians(elevation)
    rot_rad = math.radians(rotation)

    # Calculate camera position (looking at origin)
    distance = config.orthographic_scale * 2
    x = distance * math.cos(elev_rad) * math.sin(rot_rad)
    y = -distance * math.cos(elev_rad) * math.cos(rot_rad)
    z = distance * math.sin(elev_rad)

    # Calculate rotation
    # Camera looks down at the scene
    pitch = math.pi / 2 - elev_rad  # Pitch down
    yaw = rot_rad  # Yaw

    return CameraConfig(
        name="IsometricCamera",
        location=(x, y, z),
        rotation=(pitch, 0.0, yaw),
        orthographic_scale=config.orthographic_scale,
    )


def set_isometric_angle(camera: Any, angle_preset: str) -> None:
    """
    Set camera to isometric angle preset.

    Args:
        camera: Blender camera object
        angle_preset: Preset name (true_isometric, pixel, military, dimetric)
    """
    angle_data = get_isometric_angle(angle_preset)
    if not angle_data:
        raise ValueError(f"Unknown angle preset: {angle_preset}")

    elevation = angle_data["elevation"]
    rotation = angle_data["rotation"]

    # Convert to radians
    elev_rad = math.radians(elevation)
    rot_rad = math.radians(rotation)

    # Calculate rotation
    pitch = math.pi / 2 - elev_rad
    yaw = rot_rad

    camera.rotation_euler = (pitch, 0.0, yaw)


def calculate_isometric_rotation(elevation: float, azimuth: float) -> Tuple[float, float, float]:
    """
    Calculate Euler rotation for isometric view.

    Args:
        elevation: Elevation angle in degrees
        azimuth: Azimuth (rotation) angle in degrees

    Returns:
        Euler angles (pitch, roll, yaw) in radians
    """
    elev_rad = math.radians(elevation)
    azim_rad = math.radians(azimuth)

    pitch = math.pi / 2 - elev_rad
    roll = 0.0
    yaw = azim_rad

    return (pitch, roll, yaw)


def calculate_camera_position(
    elevation: float,
    azimuth: float,
    distance: float
) -> Tuple[float, float, float]:
    """
    Calculate camera position for isometric view.

    Args:
        elevation: Elevation angle in degrees
        azimuth: Azimuth (rotation) angle in degrees
        distance: Distance from origin

    Returns:
        Position (x, y, z)
    """
    elev_rad = math.radians(elevation)
    azim_rad = math.radians(azimuth)

    x = distance * math.cos(elev_rad) * math.sin(azim_rad)
    y = -distance * math.cos(elev_rad) * math.cos(azim_rad)
    z = distance * math.sin(elev_rad)

    return (x, y, z)


# =============================================================================
# PROJECTION FUNCTIONS
# =============================================================================

def project_to_isometric(
    point: Tuple[float, float, float],
    config: IsometricConfig
) -> Tuple[int, int]:
    """
    Project 3D point to isometric 2D coordinates.

    Args:
        point: 3D point (x, y, z)
        config: Isometric configuration

    Returns:
        2D coordinates (x, y) in pixels
    """
    x, y, z = point

    # Get angle data
    angle_data = get_isometric_angle(config.angle)
    if not angle_data:
        angle_data = ISOMETRIC_ANGLES["pixel"]

    elev_rad = math.radians(angle_data["elevation"])
    rot_rad = math.radians(angle_data["rotation"])

    # Rotate around Y axis (azimuth)
    cos_rot = math.cos(rot_rad)
    sin_rot = math.sin(rot_rad)
    x_rot = x * cos_rot - y * sin_rot
    y_rot = x * sin_rot + y * cos_rot

    # Project with elevation
    cos_elev = math.cos(elev_rad)
    sin_elev = math.sin(elev_rad)

    # Isometric projection
    screen_x = (x_rot - y_rot) * config.tile_width / 2
    screen_y = (x_rot + y_rot) * config.tile_height / 2 - z * config.tile_height

    return (int(screen_x), int(screen_y))


def project_to_screen(
    point: Tuple[float, float, float],
    elevation: float,
    rotation: float,
    tile_width: int = 32,
    tile_height: int = 16
) -> Tuple[float, float]:
    """
    Project 3D point to screen coordinates using isometric projection.

    Args:
        point: 3D point (x, y, z)
        elevation: Elevation angle in degrees
        rotation: Rotation angle in degrees
        tile_width: Tile width for scaling
        tile_height: Tile height for scaling

    Returns:
        Screen coordinates (x, y)
    """
    x, y, z = point

    elev_rad = math.radians(elevation)
    rot_rad = math.radians(rotation)

    # Rotate around Z axis
    cos_rot = math.cos(rot_rad)
    sin_rot = math.sin(rot_rad)
    x_rot = x * cos_rot - y * sin_rot
    y_rot = x * sin_rot + y * cos_rot

    # Project to 2D
    screen_x = (x_rot - y_rot) * tile_width / 2
    screen_y = (x_rot + y_rot) * tile_height / 2 - z * tile_height

    return (screen_x, screen_y)


# =============================================================================
# DEPTH SORTING
# =============================================================================

def depth_sort_objects(
    objects: List[Any],
    camera_pos: Tuple[float, float, float],
    config: Optional[IsometricConfig] = None
) -> List[Any]:
    """
    Sort objects for correct isometric rendering (painter's algorithm).

    Objects are sorted from back to front so that closer objects
    are drawn on top of farther objects.

    Args:
        objects: List of Blender objects
        camera_pos: Camera position (x, y, z)
        config: Optional isometric configuration for layer separation

    Returns:
        Sorted list of objects
    """
    def get_sort_key(obj: Any) -> Tuple[int, float]:
        # Get object center
        if hasattr(obj, 'location'):
            obj_pos = obj.location
        else:
            # Fallback for non-Blender objects
            obj_pos = (0, 0, 0)

        # Calculate distance from camera
        dx = obj_pos[0] - camera_pos[0]
        dy = obj_pos[1] - camera_pos[1]
        dz = obj_pos[2] - camera_pos[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)

        # For isometric, we also consider the "depth" in isometric space
        # Objects with lower (x + y - z) should be rendered first
        iso_depth = obj_pos[0] + obj_pos[1] - obj_pos[2]

        # Layer priority (if layer separation enabled)
        layer = 0
        if config and hasattr(obj, 'name'):
            # Check object name/collection for layer hints
            for i, layer_name in enumerate(config.layer_separation):
                if layer_name.lower() in obj.name.lower():
                    layer = i
                    break

        return (layer, iso_depth)

    return sorted(objects, key=get_sort_key)


def get_isometric_depth(position: Tuple[float, float, float]) -> float:
    """
    Calculate isometric depth for a position.

    Used for sorting - lower values should be rendered first.

    Args:
        position: 3D position (x, y, z)

    Returns:
        Isometric depth value
    """
    x, y, z = position
    return x + y - z


# =============================================================================
# GRID FUNCTIONS
# =============================================================================

def create_isometric_grid_data(
    config: IsometricConfig,
    grid_size: int = 10
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Create isometric grid line data for visualization.

    Args:
        config: Isometric configuration
        grid_size: Number of grid cells in each direction

    Returns:
        List of line segments (start_point, end_point)
    """
    lines = []
    tile_w = config.tile_width
    tile_h = config.tile_height

    # Horizontal lines (in isometric space)
    for i in range(grid_size + 1):
        # Lines going from top-left to bottom-right
        start_x = i * tile_w - grid_size * tile_w // 2
        start_y = -grid_size * tile_h // 2
        end_x = start_x - grid_size * tile_w
        end_y = grid_size * tile_h // 2

        lines.append(((start_x, start_y), (end_x, end_y)))

        # Lines going from top-right to bottom-left
        start_x = -i * tile_w - grid_size * tile_w // 2
        start_y = -grid_size * tile_h // 2
        end_x = start_x + grid_size * tile_w
        end_y = grid_size * tile_h // 2

        lines.append(((start_x, start_y), (end_x, end_y)))

    return lines


def snap_to_isometric_grid(
    position: Tuple[float, float, float],
    config: IsometricConfig
) -> Tuple[float, float, float]:
    """
    Snap a position to the isometric grid.

    Args:
        position: World position (x, y, z)
        config: Isometric configuration

    Returns:
        Snapped position
    """
    x, y, z = position

    # Get tile ratio from angle preset
    angle_data = get_isometric_angle(config.angle)
    if angle_data:
        ratio_x, ratio_y = angle_data.get("tile_ratio", (2.0, 1.0))
    else:
        ratio_x, ratio_y = (2.0, 1.0)

    # Snap to grid
    grid_x = round(x) * config.tile_width / ratio_x
    grid_y = round(y) * config.tile_height / ratio_y
    grid_z = round(z)

    return (grid_x, grid_y, grid_z)


# =============================================================================
# TILE RENDERING
# =============================================================================

def render_isometric_tile(
    scene: Any,
    config: IsometricConfig,
    output_path: Optional[str] = None
) -> IsometricRenderResult:
    """
    Render scene as isometric tile.

    Args:
        scene: Blender scene
        config: Isometric configuration
        output_path: Optional output path for render

    Returns:
        IsometricRenderResult with rendered image
    """
    result = IsometricRenderResult()
    result.camera_angles = config.get_angles()

    warnings = []

    try:
        import bpy

        # Get or create camera
        camera = None
        for obj in scene.objects:
            if obj.type == 'CAMERA':
                camera = obj
                break

        if camera:
            # Set camera to isometric view
            cam_config = create_isometric_camera_config(config)
            camera.location = cam_config.location
            camera.rotation_euler = cam_config.rotation

            # Set orthographic
            camera.data.type = 'ORTHO'
            camera.data.ortho_scale = cam_config.orthographic_scale

            scene.camera = camera

        # Set render resolution
        scene.render.resolution_x = config.tile_width
        scene.render.resolution_y = config.tile_height
        scene.render.resolution_percentage = 100

        # Render
        if output_path:
            scene.render.filepath = output_path
            bpy.ops.render.render(write_still=True)
            result.warnings.append(f"Rendered to: {output_path}")

        result.tile_count = 1

    except ImportError:
        warnings.append("Blender not available for rendering")
    except Exception as e:
        warnings.append(f"Render error: {str(e)}")

    result.warnings = warnings
    return result


def render_isometric_tile_set(
    objects: List[Any],
    config: IsometricConfig,
    output_dir: str
) -> Dict[str, Any]:
    """
    Render multiple objects as isometric tiles.

    Args:
        objects: List of Blender objects to render
        config: Isometric configuration
        output_dir: Output directory for tiles

    Returns:
        Dict with tile paths and metadata
    """
    results = {
        "tiles": [],
        "tile_count": 0,
        "errors": [],
    }

    try:
        import bpy
        import os

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Store current state
        original_selection = bpy.context.selected_objects.copy()
        original_active = bpy.context.active_object

        for obj in objects:
            try:
                # Deselect all
                bpy.ops.object.select_all(action='DESELECT')

                # Select and make active
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

                # Hide other objects
                for other in bpy.data.objects:
                    if other != obj and other.type != 'CAMERA':
                        other.hide_render = True

                # Render
                output_path = os.path.join(output_dir, f"{obj.name}.png")
                result = render_isometric_tile(bpy.context.scene, config, output_path)

                results["tiles"].append({
                    "name": obj.name,
                    "path": output_path,
                })
                results["tile_count"] += 1

                # Unhide objects
                for other in bpy.data.objects:
                    if other != obj and other.type != 'CAMERA':
                        other.hide_render = False

            except Exception as e:
                results["errors"].append(f"Error rendering {obj.name}: {str(e)}")

        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = original_active

    except ImportError:
        results["errors"].append("Blender not available for rendering")
    except Exception as e:
        results["errors"].append(f"Render error: {str(e)}")

    return results


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_tile_bounds(
    tile_x: int,
    tile_y: int,
    config: IsometricConfig
) -> Tuple[float, float, float, float]:
    """
    Get screen bounds for an isometric tile.

    Args:
        tile_x: Tile X coordinate
        tile_y: Tile Y coordinate
        config: Isometric configuration

    Returns:
        (min_x, min_y, max_x, max_y) screen coordinates
    """
    # Calculate center
    center_x = (tile_x - tile_y) * config.tile_width / 2
    center_y = (tile_x + tile_y) * config.tile_height / 2

    # Calculate bounds
    half_w = config.tile_width / 2
    half_h = config.tile_height / 2

    return (
        center_x - half_w,
        center_y - half_h,
        center_x + half_w,
        center_y + half_h,
    )


def world_to_tile(
    world_pos: Tuple[float, float, float],
    config: IsometricConfig
) -> Tuple[int, int]:
    """
    Convert world position to tile coordinates.

    Args:
        world_pos: World position (x, y, z)
        config: Isometric configuration

    Returns:
        Tile coordinates (tile_x, tile_y)
    """
    x, y, z = world_pos

    # Reverse isometric projection
    tile_x = int((x / config.tile_width + y / config.tile_height) / 2)
    tile_y = int((y / config.tile_height - x / config.tile_width) / 2)

    return (tile_x, tile_y)


def tile_to_world(
    tile_x: int,
    tile_y: int,
    config: IsometricConfig
) -> Tuple[float, float, float]:
    """
    Convert tile coordinates to world position.

    Args:
        tile_x: Tile X coordinate
        tile_y: Tile Y coordinate
        config: Isometric configuration

    Returns:
        World position (x, y, z) at tile center, z=0
    """
    world_x = (tile_x - tile_y) * config.tile_width / 2
    world_y = (tile_x + tile_y) * config.tile_height / 2
    world_z = 0.0

    return (world_x, world_y, world_z)


def calculate_tile_neighbors(tile_x: int, tile_y: int) -> List[Tuple[int, int]]:
    """
    Get neighboring tile coordinates.

    Args:
        tile_x: Tile X coordinate
        tile_y: Tile Y coordinate

    Returns:
        List of neighbor tile coordinates
    """
    return [
        (tile_x + 1, tile_y),
        (tile_x - 1, tile_y),
        (tile_x, tile_y + 1),
        (tile_x, tile_y - 1),
        (tile_x + 1, tile_y + 1),
        (tile_x - 1, tile_y - 1),
        (tile_x + 1, tile_y - 1),
        (tile_x - 1, tile_y + 1),
    ]
