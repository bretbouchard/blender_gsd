"""
Game Integration System

Handles collision setup, LOD management, NPC path generation, and export
for Unity and Unreal Engine.

Usage:
    from lib.game_integration import (
        setup_collision_for_object,
        create_lod_system,
        generate_npc_paths,
        export_for_unity,
        export_for_unreal,
    )
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass
import math
import json

# Add lib to path for blender_gsd tools
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))

try:
    import bpy
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class CollisionType(Enum):
    """Collision mesh types."""
    TRIMESH = "trimesh"           # Exact mesh collision
    CONVEX_HULL = "convex"        # Simplified convex
    BOX = "box"                   # Bounding box
    SPHERE = "sphere"             # Bounding sphere
    CAPSULE = "capsule"           # Bounding capsule
    COMPOUND = "compound"         # Multiple shapes


class LODLevel(Enum):
    """Level of Detail levels."""
    LOD0 = 0   # Highest detail, 0-100m
    LOD1 = 1   # High detail, 100-300m
    LOD2 = 2   # Medium detail, 300m-1km
    LOD3 = 3   # Low detail, 1km+


class ExportTarget(Enum):
    """Export target engines."""
    UNITY = "unity"
    UNREAL = "unreal"
    GODOT = "godot"
    GLTF = "gltf"


@dataclass
class CollisionConfig:
    """Collision configuration."""
    collision_type: CollisionType = CollisionType.TRIMESH
    simplify_level: int = 0       # 0=full, 1=decimated, 2=convex
    is_trigger: bool = False
    physics_material: str = "asphalt"


@dataclass
class LODConfig:
    """LOD configuration for a single level."""
    level: LODLevel
    screen_size: float    # Minimum screen size (0-1)
    distance: float       # Distance threshold in meters
    decimate_ratio: float # Geometry reduction ratio
    merge_materials: bool # Whether to merge similar materials


@dataclass
class NPCPathConfig:
    """NPC path configuration."""
    lane_offset: float = 0.0      # Offset from lane center
    speed_limit: float = 30.0     # km/h default
    path_width: float = 3.0       # Lane width
    direction: str = "forward"    # forward or backward


# =============================================================================
# COLLISION SETUP
# =============================================================================

def setup_collision_for_object(
    obj: bpy.types.Object,
    config: Optional[CollisionConfig] = None
) -> bpy.types.Object:
    """
    Setup collision for a game object.

    Args:
        obj: Object to setup collision for
        config: Collision configuration

    Returns:
        The collision object (may be same as input or new object)
    """
    if not BLENDER_AVAILABLE:
        return obj

    if config is None:
        config = CollisionConfig()

    # Store collision properties on the object
    obj["collision_type"] = config.collision_type.value
    obj["collision_simplify"] = config.simplify_level
    obj["is_trigger"] = config.is_trigger
    obj["physics_material"] = config.physics_material

    # For Unity export
    obj["ue_collision"] = config.collision_type.value == CollisionType.TRIMESH.value
    obj["unity_collider"] = config.collision_type.value

    # Add Blender collision modifier (for physics in Blender)
    if "Collision" not in obj.modifiers:
        try:
            obj.modifiers.new(name="Collision", type='COLLISION')
        except TypeError:
            pass  # Not all object types support collision

    return obj


def create_collision_proxy(
    source_obj: bpy.types.Object,
    collision_type: CollisionType = CollisionType.CONVEX_HULL,
    simplify_ratio: float = 0.5
) -> Optional[bpy.types.Object]:
    """
    Create a simplified collision proxy object.

    Args:
        source_obj: Source mesh object
        collision_type: Type of collision to create
        simplify_ratio: Geometry reduction ratio

    Returns:
        New collision proxy object
    """
    if not BLENDER_AVAILABLE:
        return None

    if source_obj.type != 'MESH':
        return None

    # Create copy
    collision_obj = source_obj.copy()
    collision_obj.data = source_obj.data.copy()
    collision_obj.name = f"{source_obj.name}_collision"

    # Clear modifiers except decimate
    collision_obj.modifiers.clear()

    # Add decimate for simplification
    if collision_type != CollisionType.TRIMESH:
        decimate = collision_obj.modifiers.new(name="Decimate", type='DECIMATE')
        decimate.ratio = simplify_ratio
        decimate.use_collapse_triangulate = True

    # Store metadata
    collision_obj["is_collision_proxy"] = True
    collision_obj["collision_source"] = source_obj.name
    collision_obj["collision_type"] = collision_type.value

    # Set to wireframe display (collision is invisible)
    collision_obj.display_type = 'WIRE'

    return collision_obj


def setup_road_collision(
    road_objects: List[bpy.types.Object],
    config: Optional[CollisionConfig] = None
) -> Dict[str, int]:
    """
    Setup collision for all road objects.

    Args:
        road_objects: List of road mesh objects
        config: Collision configuration

    Returns:
        Stats dict
    """
    if not BLENDER_AVAILABLE:
        return {}

    if config is None:
        config = CollisionConfig(
            collision_type=CollisionType.TRIMESH,
            physics_material="asphalt"
        )

    stats = {
        'setup': 0,
        'proxies_created': 0,
        'errors': 0,
    }

    for obj in road_objects:
        try:
            # Setup collision on object
            setup_collision_for_object(obj, config)
            stats['setup'] += 1

            # Create collision proxy for complex meshes
            if obj.type == 'MESH':
                poly_count = len(obj.data.polygons)
                if poly_count > 1000:
                    proxy = create_collision_proxy(obj, CollisionType.CONVEX_HULL, 0.3)
                    if proxy:
                        bpy.context.collection.objects.link(proxy)
                        stats['proxies_created'] += 1

        except Exception as e:
            stats['errors'] += 1

    return stats


# =============================================================================
# LOD SYSTEM
# =============================================================================

LOD_CONFIGS = {
    LODLevel.LOD0: LODConfig(
        level=LODLevel.LOD0,
        screen_size=0.5,
        distance=100.0,
        decimate_ratio=1.0,
        merge_materials=False
    ),
    LODLevel.LOD1: LODConfig(
        level=LODLevel.LOD1,
        screen_size=0.25,
        distance=300.0,
        decimate_ratio=0.5,
        merge_materials=True
    ),
    LODLevel.LOD2: LODConfig(
        level=LODLevel.LOD2,
        screen_size=0.1,
        distance=1000.0,
        decimate_ratio=0.25,
        merge_materials=True
    ),
    LODLevel.LOD3: LODConfig(
        level=LODLevel.LOD3,
        screen_size=0.05,
        distance=5000.0,
        decimate_ratio=0.1,
        merge_materials=True
    ),
}


def create_lod_object(
    source_obj: bpy.types.Object,
    lod_config: LODConfig
) -> Optional[bpy.types.Object]:
    """
    Create a LOD version of an object.

    Args:
        source_obj: Source object
        lod_config: LOD configuration

    Returns:
        New LOD object
    """
    if not BLENDER_AVAILABLE:
        return None

    if source_obj.type != 'MESH':
        return None

    # Create copy
    lod_obj = source_obj.copy()
    lod_obj.data = source_obj.data.copy()
    lod_obj.name = f"{source_obj.name}_LOD{lod_config.level.value}"

    # Apply decimation
    decimate = lod_obj.modifiers.new(name="LOD_Decimate", type='DECIMATE')
    decimate.ratio = lod_config.decimate_ratio

    # Store LOD metadata
    lod_obj["lod_level"] = lod_config.level.value
    lod_obj["lod_distance"] = lod_config.distance
    lod_obj["lod_screen_size"] = lod_config.screen_size
    lod_obj["lod_source"] = source_obj.name

    return lod_obj


def create_lod_system_for_object(
    obj: bpy.types.Object,
    levels: List[LODLevel] = None
) -> List[bpy.types.Object]:
    """
    Create full LOD system for an object.

    Args:
        obj: Source object
        levels: LOD levels to create (default: all)

    Returns:
        List of LOD objects including source as LOD0
    """
    if not BLENDER_AVAILABLE:
        return []

    if levels is None:
        levels = [LODLevel.LOD0, LODLevel.LOD1, LODLevel.LOD2, LODLevel.LOD3]

    lod_objects = []

    for level in levels:
        config = LOD_CONFIGS.get(level)
        if config is None:
            continue

        if level == LODLevel.LOD0:
            # Use source as LOD0
            obj["lod_level"] = 0
            obj["lod_distance"] = config.distance
            lod_objects.append(obj)
        else:
            # Create LOD version
            lod_obj = create_lod_object(obj, config)
            if lod_obj:
                bpy.context.collection.objects.link(lod_obj)
                lod_objects.append(lod_obj)

    # Create LOD collection
    coll_name = f"LOD_{obj.name}"
    if coll_name not in bpy.data.collections:
        coll = bpy.data.collections.new(coll_name)
        bpy.context.scene.collection.children.link(coll)

        for lod_obj in lod_objects:
            coll.objects.link(lod_obj)

    return lod_objects


def setup_scene_lod(
    object_types: List[str] = None,
    max_objects: int = 100
) -> Dict[str, int]:
    """
    Setup LOD for all appropriate objects in scene.

    Args:
        object_types: Types of objects to process
        max_objects: Maximum objects to process

    Returns:
        Stats dict
    """
    if not BLENDER_AVAILABLE:
        return {}

    if object_types is None:
        object_types = ['building', 'road', 'vehicle']

    stats = {
        'processed': 0,
        'lod_created': 0,
        'skipped': 0,
        'errors': 0,
    }

    for obj in bpy.context.scene.objects:
        if stats['processed'] >= max_objects:
            break

        # Check if object should have LOD
        obj_type = obj.get('object_type', '')
        has_lod = obj.get('has_lod', False)

        if obj_type not in object_types and not has_lod:
            continue

        if obj.type != 'MESH':
            stats['skipped'] += 1
            continue

        try:
            lod_objects = create_lod_system_for_object(obj)
            stats['lod_created'] += len(lod_objects)
            stats['processed'] += 1
        except Exception:
            stats['errors'] += 1

    return stats


# =============================================================================
# NPC PATH GENERATION
# =============================================================================

def generate_lane_centerline(
    road_curve: bpy.types.Object,
    lane_index: int,
    total_lanes: int,
    road_width: float
) -> List[Vector]:
    """
    Generate centerline points for a specific lane.

    Args:
        road_curve: Road curve object
        lane_index: Lane index (0 to total_lanes-1)
        total_lanes: Total number of lanes
        road_width: Total road width

    Returns:
        List of Vector points for lane centerline
    """
    if not BLENDER_AVAILABLE:
        return []

    if road_curve.type != 'CURVE' or not road_curve.data.splines:
        return []

    spline = road_curve.data.splines[0]
    points = [road_curve.matrix_world @ Vector(p.co[:3]) for p in spline.points]

    if len(points) < 2:
        return []

    lane_width = road_width / total_lanes
    lane_centerline = []

    for i, point in enumerate(points):
        # Calculate direction
        if i == 0:
            direction = (points[1] - points[0]).normalized()
        elif i == len(points) - 1:
            direction = (points[-1] - points[-2]).normalized()
        else:
            direction = (points[i+1] - points[i-1]).normalized()

        # Perpendicular for offset
        perpendicular = Vector((-direction.y, direction.x, 0))

        # Calculate lane offset from road center
        lane_offset = -road_width/2 + lane_width * (lane_index + 0.5)

        # Apply offset
        lane_point = point + perpendicular * lane_offset
        lane_point.z += 0.5  # Slight height offset for visibility
        lane_centerline.append(lane_point)

    return lane_centerline


def create_npc_path_curve(
    points: List[Vector],
    name: str,
    config: NPCPathConfig
) -> Optional[bpy.types.Object]:
    """
    Create a curve object for NPC path.

    Args:
        points: Path points
        name: Path name
        config: Path configuration

    Returns:
        Created curve object
    """
    if not BLENDER_AVAILABLE or len(points) < 2:
        return None

    # Create curve data
    curve_data = bpy.data.curves.new(name=f"{name}_curve", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 2

    # Create spline
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points) - 1)

    for i, point in enumerate(points):
        spline.points[i].co = (point.x, point.y, point.z, 1.0)

    # Create object
    curve_obj = bpy.data.objects.new(name, curve_data)

    # Store metadata
    curve_obj["path_type"] = "npc_lane"
    curve_obj["speed_limit"] = config.speed_limit
    curve_obj["path_width"] = config.path_width
    curve_obj["direction"] = config.direction

    return curve_obj


def generate_all_npc_paths(
    road_curves: List[bpy.types.Object],
    output_collection: str = "NPC_Paths"
) -> Dict[str, int]:
    """
    Generate NPC paths for all road lanes.

    Args:
        road_curves: List of road curve objects
        output_collection: Collection name for paths

    Returns:
        Stats dict
    """
    if not BLENDER_AVAILABLE:
        return {}

    stats = {
        'roads_processed': 0,
        'paths_created': 0,
        'total_length': 0.0,
        'errors': 0,
    }

    # Create collection
    if output_collection not in bpy.data.collections:
        coll = bpy.data.collections.new(output_collection)
        bpy.context.scene.collection.children.link(coll)
    else:
        coll = bpy.data.collections[output_collection]

    for road in road_curves:
        try:
            lanes = road.get('lanes', 2)
            road_width = road.get('road_width', 7.0)
            road_name = road.get('name', road.name)
            max_speed = road.get('maxspeed', 30)

            # Generate path for each lane
            for lane_idx in range(lanes):
                # Skip center divider for 2-way roads
                if lanes >= 2 and lane_idx == lanes // 2:
                    continue

                # Determine direction
                direction = "forward" if lane_idx < lanes/2 else "backward"

                # Generate lane centerline
                centerline = generate_lane_centerline(
                    road, lane_idx, lanes, road_width
                )

                if len(centerline) < 2:
                    continue

                # Create path configuration
                config = NPCPathConfig(
                    lane_offset=0.0,
                    speed_limit=float(max_speed) if isinstance(max_speed, (int, float)) else 30.0,
                    path_width=road_width / lanes,
                    direction=direction
                )

                # Create path curve
                path_name = f"NPC_{road_name}_Lane{lane_idx}"
                path_curve = create_npc_path_curve(centerline, path_name, config)

                if path_curve:
                    bpy.context.collection.objects.link(path_curve)
                    coll.objects.link(path_curve)
                    stats['paths_created'] += 1

                    # Calculate path length
                    length = sum(
                        (centerline[i+1] - centerline[i]).length
                        for i in range(len(centerline) - 1)
                    )
                    stats['total_length'] += length

            stats['roads_processed'] += 1

        except Exception as e:
            stats['errors'] += 1

    return stats


def export_npc_paths_json(
    npc_paths: List[bpy.types.Object],
    output_path: str
) -> bool:
    """
    Export NPC paths to JSON format for game engine.

    Args:
        npc_paths: List of NPC path curves
        output_path: Output file path

    Returns:
        Success boolean
    """
    if not BLENDER_AVAILABLE:
        return False

    paths_data = {
        "version": "1.0",
        "paths": []
    }

    for path in npc_paths:
        if path.type != 'CURVE' or not path.data.splines:
            continue

        spline = path.data.splines[0]
        points = [path.matrix_world @ Vector(p.co[:3]) for p in spline.points]

        path_data = {
            "name": path.name,
            "points": [[p.x, p.y, p.z] for p in points],
            "speed_limit": path.get("speed_limit", 30.0),
            "direction": path.get("direction", "forward"),
            "width": path.get("path_width", 3.0)
        }

        paths_data["paths"].append(path_data)

    # Write JSON
    try:
        with open(output_path, 'w') as f:
            json.dump(paths_data, f, indent=2)
        return True
    except Exception:
        return False


# =============================================================================
# EXPORT SYSTEM
# =============================================================================

def export_for_unity(
    objects: List[bpy.types.Object],
    output_dir: str,
    export_settings: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Export scene for Unity.

    Unity prefers:
    - FBX format
    - Y-up coordinate system
    - Embedded textures
    - Separate collision meshes

    Args:
        objects: Objects to export
        output_dir: Output directory
        export_settings: Additional export settings

    Returns:
        Export results dict
    """
    if not BLENDER_AVAILABLE:
        return {'error': 'Blender not available'}

    if export_settings is None:
        export_settings = {}

    results = {
        'exported_files': [],
        'errors': [],
    }

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Select objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)

    # Export FBX
    fbx_path = output_path / "charlotte_roads.fbx"

    try:
        bpy.ops.export_scene.fbx(
            filepath=str(fbx_path),
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Z',
            axis_up='Y',
            object_types={'MESH', 'CURVE'},
            use_mesh_modifiers=True,
            mesh_smooth_type='FACE',
            use_tspace=True,
            embed_textures=True,
            path_mode='COPY',
            batch_mode='OFF',
        )
        results['exported_files'].append(str(fbx_path))
    except Exception as e:
        results['errors'].append(f"FBX export failed: {e}")

    # Export collision meshes separately
    collision_objects = [obj for obj in objects if obj.get('is_collision_proxy')]
    if collision_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collision_objects:
            obj.select_set(True)

        collision_path = output_path / "charlotte_collision.fbx"
        try:
            bpy.ops.export_scene.fbx(
                filepath=str(collision_path),
                use_selection=True,
                global_scale=1.0,
                axis_forward='-Z',
                axis_up='Y',
                object_types={'MESH'},
                use_mesh_modifiers=True,
            )
            results['exported_files'].append(str(collision_path))
        except Exception as e:
            results['errors'].append(f"Collision export failed: {e}")

    # Export metadata JSON
    metadata = {
        "objects": []
    }

    for obj in objects:
        obj_meta = {
            "name": obj.name,
            "type": obj.type,
            "collision_type": obj.get("collision_type", "none"),
            "lod_level": obj.get("lod_level", 0),
            "road_name": obj.get("road_name", ""),
            "properties": {}
        }

        # Collect all custom properties
        for key, value in obj.items():
            if not key.startswith('_'):
                obj_meta["properties"][key] = str(value)

        metadata["objects"].append(obj_meta)

    metadata_path = output_path / "charlotte_metadata.json"
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        results['exported_files'].append(str(metadata_path))
    except Exception as e:
        results['errors'].append(f"Metadata export failed: {e}")

    return results


def export_for_unreal(
    objects: List[bpy.types.Object],
    output_dir: str,
    export_settings: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Export scene for Unreal Engine.

    Unreal prefers:
    - FBX format
    - Z-up coordinate system
    - Separate collision (UCX_ prefix)
    - LOD in same file

    Args:
        objects: Objects to export
        output_dir: Output directory
        export_settings: Additional export settings

    Returns:
        Export results dict
    """
    if not BLENDER_AVAILABLE:
        return {'error': 'Blender not available'}

    if export_settings is None:
        export_settings = {}

    results = {
        'exported_files': [],
        'errors': [],
    }

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Prepare objects - rename collision for Unreal convention
    collision_mapping = {}
    for obj in objects:
        if obj.get('is_collision_proxy'):
            source_name = obj.get('collision_source', obj.name.replace('_collision', ''))
            # Unreal uses UCX_ prefix for collision
            obj.name = f"UCX_{source_name}"
            collision_mapping[source_name] = obj

    # Select all objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)

    # Export FBX with Unreal settings
    fbx_path = output_path / "charlotte_unreal.fbx"

    try:
        bpy.ops.export_scene.fbx(
            filepath=str(fbx_path),
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Y',  # Unreal forward
            axis_up='Z',        # Unreal up
            object_types={'MESH', 'CURVE'},
            use_mesh_modifiers=True,
            mesh_smooth_type='FACE',
            use_tspace=True,
            embed_textures=True,
            path_mode='COPY',
        )
        results['exported_files'].append(str(fbx_path))
    except Exception as e:
        results['errors'].append(f"FBX export failed: {e}")

    # Export LOD data as separate files
    lod_objects = [obj for obj in objects if obj.get('lod_level') is not None]
    if lod_objects:
        for lod_level in [0, 1, 2, 3]:
            lod_for_level = [obj for obj in lod_objects if obj.get('lod_level') == lod_level]
            if lod_for_level:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in lod_for_level:
                    obj.select_set(True)

                lod_path = output_path / f"charlotte_LOD{lod_level}.fbx"
                try:
                    bpy.ops.export_scene.fbx(
                        filepath=str(lod_path),
                        use_selection=True,
                        axis_forward='-Y',
                        axis_up='Z',
                        use_mesh_modifiers=True,
                    )
                    results['exported_files'].append(str(lod_path))
                except Exception as e:
                    results['errors'].append(f"LOD{lod_level} export failed: {e}")

    return results


def export_gltf(
    objects: List[bpy.types.Object],
    output_path: str,
    export_settings: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Export scene as GLTF/GLB.

    Good for:
    - Web viewers
    - Cross-platform
    - Small file size

    Args:
        objects: Objects to export
        output_path: Output file path (.glb or .gltf)
        export_settings: Additional export settings

    Returns:
        Export results dict
    """
    if not BLENDER_AVAILABLE:
        return {'error': 'Blender not available'}

    results = {
        'exported_files': [],
        'errors': [],
    }

    # Select objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)

    # Determine format
    if output_path.endswith('.glb'):
        export_format = 'GLB'
    else:
        export_format = 'GLTF_SEPARATE'

    try:
        bpy.ops.export_scene.gltf(
            filepath=output_path,
            export_format=export_format,
            use_selection=True,
            export_cameras=False,
            export_lights=False,
            export_extras=True,  # Custom properties
            export_yup=True,
            export_apply=True,
        )
        results['exported_files'].append(output_path)
    except Exception as e:
        results['errors'].append(f"GLTF export failed: {e}")

    return results


# =============================================================================
# SPAWN POINT GENERATION
# =============================================================================

def generate_vehicle_spawn_points(
    npc_paths: List[bpy.types.Object],
    spacing: float = 100.0
) -> List[Dict[str, Any]]:
    """
    Generate vehicle spawn points along NPC paths.

    Args:
        npc_paths: List of NPC path curves
        spacing: Distance between spawn points

    Returns:
        List of spawn point data
    """
    spawn_points = []

    for path in npc_paths:
        if path.type != 'CURVE' or not path.data.splines:
            continue

        spline = path.data.splines[0]
        points = [path.matrix_world @ Vector(p.co[:3]) for p in spline.points]

        if len(points) < 2:
            continue

        # Calculate total length
        total_length = sum(
            (points[i+1] - points[i]).length
            for i in range(len(points) - 1)
        )

        # Generate spawn points
        num_spawns = int(total_length / spacing)
        path_name = path.name

        for i in range(num_spawns):
            target_dist = i * spacing
            current_dist = 0

            for j in range(len(points) - 1):
                segment_length = (points[j+1] - points[j]).length

                if current_dist + segment_length >= target_dist:
                    t = (target_dist - current_dist) / segment_length if segment_length > 0 else 0
                    position = points[j] + (points[j+1] - points[j]) * t
                    direction = (points[j+1] - points[j]).normalized()
                    rotation = math.atan2(direction.y, direction.x)

                    spawn_points.append({
                        'name': f"Spawn_{path_name}_{i}",
                        'position': [position.x, position.y, position.z],
                        'rotation': rotation,
                        'path': path_name,
                        'direction': path.get('direction', 'forward'),
                    })
                    break

                current_dist += segment_length

    return spawn_points


def create_spawn_point_objects(
    spawn_points: List[Dict[str, Any]],
    collection_name: str = "Spawn_Points"
) -> int:
    """
    Create spawn point marker objects in Blender.

    Args:
        spawn_points: List of spawn point data
        collection_name: Collection for spawn points

    Returns:
        Number of objects created
    """
    if not BLENDER_AVAILABLE:
        return 0

    # Create collection
    if collection_name not in bpy.data.collections:
        coll = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(coll)
    else:
        coll = bpy.data.collections[collection_name]

    created = 0

    for spawn in spawn_points:
        # Create empty as marker
        obj = bpy.data.objects.new(spawn['name'], None)
        obj.empty_display_type = 'ARROWS'
        obj.empty_display_size = 2.0

        pos = spawn['position']
        obj.location = (pos[0], pos[1], pos[2])
        obj.rotation_euler[2] = spawn['rotation']

        # Store metadata
        obj["spawn_type"] = "vehicle"
        obj["spawn_path"] = spawn['path']
        obj["spawn_direction"] = spawn['direction']

        bpy.context.collection.objects.link(obj)
        coll.objects.link(obj)
        created += 1

    return created


# =============================================================================
# MAIN
# =============================================================================

def setup_game_integration(
    export_target: ExportTarget = ExportTarget.UNITY,
    output_dir: str = "exports"
) -> Dict[str, Any]:
    """
    Complete game integration setup.

    Args:
        export_target: Target engine
        output_dir: Export directory

    Returns:
        Complete results dict
    """
    print("\n=== Game Integration Setup ===")

    results = {
        'collision': {},
        'lod': {},
        'npc_paths': {},
        'export': {},
        'spawn_points': {},
    }

    # Get scene objects
    road_objects = [
        obj for obj in bpy.context.scene.objects
        if obj.get('road_class') or 'road' in obj.name.lower()
    ]

    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('road_class')
    ]

    all_export_objects = [
        obj for obj in bpy.context.scene.objects
        if obj.type in ('MESH', 'CURVE') and not obj.get('is_collision_proxy')
    ]

    # 1. Setup collision
    print("\n[1/5] Setting up collision...")
    results['collision'] = setup_road_collision(road_objects)
    print(f"  Setup: {results['collision'].get('setup', 0)}")
    print(f"  Proxies: {results['collision'].get('proxies_created', 0)}")

    # 2. Setup LOD
    print("\n[2/5] Setting up LOD...")
    results['lod'] = setup_scene_lod(max_objects=50)
    print(f"  Processed: {results['lod'].get('processed', 0)}")
    print(f"  LOD objects: {results['lod'].get('lod_created', 0)}")

    # 3. Generate NPC paths
    print("\n[3/5] Generating NPC paths...")
    results['npc_paths'] = generate_all_npc_paths(road_curves)
    print(f"  Roads: {results['npc_paths'].get('roads_processed', 0)}")
    print(f"  Paths: {results['npc_paths'].get('paths_created', 0)}")
    print(f"  Total length: {results['npc_paths'].get('total_length', 0):.1f}m")

    # 4. Generate spawn points
    print("\n[4/5] Generating spawn points...")
    npc_path_objs = [
        obj for obj in bpy.context.scene.objects
        if obj.get('path_type') == 'npc_lane'
    ]
    spawn_points = generate_vehicle_spawn_points(npc_path_objs, spacing=100.0)
    spawn_created = create_spawn_point_objects(spawn_points[:100])  # Limit
    results['spawn_points']['created'] = spawn_created
    print(f"  Spawn points: {spawn_created}")

    # 5. Export
    print(f"\n[5/5] Exporting for {export_target.value}...")
    output_path = Path(__file__).parent.parent / output_dir / export_target.value
    output_path.mkdir(parents=True, exist_ok=True)

    if export_target == ExportTarget.UNITY:
        results['export'] = export_for_unity(all_export_objects, str(output_path))
    elif export_target == ExportTarget.UNREAL:
        results['export'] = export_for_unreal(all_export_objects, str(output_path))
    elif export_target == ExportTarget.GLTF:
        results['export'] = export_gltf(
            all_export_objects,
            str(output_path / "charlotte.glb")
        )

    print(f"  Files: {len(results['export'].get('exported_files', []))}")
    if results['export'].get('errors'):
        print(f"  Errors: {results['export']['errors']}")

    # Export NPC paths JSON
    npc_json_path = output_path / "npc_paths.json"
    export_npc_paths_json(npc_path_objs, str(npc_json_path))
    print(f"  NPC paths: {npc_json_path}")

    return results


if __name__ == '__main__':
    setup_game_integration()
