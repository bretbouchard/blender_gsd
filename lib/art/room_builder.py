"""
Room Builder Module

Procedural room construction with walls, floor, ceiling, and moldings.
Uses bmesh for context-free mesh creation suitable for batch processing.

Implements REQ-SET-01: Wall and room generation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
import math

from .set_types import (
    RoomConfig,
    WallConfig,
    WallOrientation,
)


@dataclass
class RoomMeshes:
    """Container for generated room meshes."""
    floor: Any = None
    ceiling: Any = None
    walls: Dict[str, Any] = field(default_factory=dict)
    baseboards: Dict[str, Any] = field(default_factory=dict)
    crown_moldings: Dict[str, Any] = field(default_factory=dict)


def create_room(config: RoomConfig, collection: Any = None) -> RoomMeshes:
    """
    Create complete room geometry from configuration.

    Args:
        config: Room configuration
        collection: Optional Blender collection to add meshes to

    Returns:
        RoomMeshes container with all generated meshes
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for room building")

    meshes = RoomMeshes()

    # Create floor
    meshes.floor = create_floor(config, collection)

    # Create ceiling
    meshes.ceiling = create_ceiling(config, collection)

    # Create walls with proper orientations
    wall_configs = [
        ("north", (0, -config.depth / 2, 0), 0),  # Front wall
        ("south", (0, config.depth / 2, 0), math.pi),  # Back wall
        ("east", (config.width / 2, 0, 0), math.pi / 2),  # Right wall
        ("west", (-config.width / 2, 0, 0), -math.pi / 2),  # Left wall
    ]

    for orientation, position, rotation in wall_configs:
        wall_config = config.walls.get(orientation, WallConfig())

        # Adjust wall width based on orientation
        if orientation in ("north", "south"):
            wall_config.width = config.width
        else:
            wall_config.width = config.depth

        wall_mesh = create_wall(
            wall_config,
            position,
            rotation,
            collection,
            name=f"{config.name}_wall_{orientation}"
        )
        meshes.walls[orientation] = wall_mesh

        # Create baseboard if enabled
        if config.has_baseboard and wall_config.baseboard_height > 0:
            baseboard = create_molding(
                "baseboard",
                wall_config.width,
                wall_config.baseboard_height,
                wall_config.thickness + 0.01,  # Slight offset from wall
                position,
                rotation,
                collection,
                name=f"{config.name}_baseboard_{orientation}"
            )
            meshes.baseboards[orientation] = baseboard

        # Create crown molding if enabled
        if config.has_crown_molding and wall_config.crown_molding:
            crown = create_molding(
                "crown",
                wall_config.width,
                wall_config.crown_molding_height,
                wall_config.thickness + 0.01,
                (position[0], position[1], config.height - wall_config.crown_molding_height),
                rotation,
                collection,
                name=f"{config.name}_crown_{orientation}"
            )
            meshes.crown_moldings[orientation] = crown

    return meshes


def create_floor(config: RoomConfig, collection: Any = None) -> Any:
    """
    Create floor mesh.

    Args:
        config: Room configuration
        collection: Optional Blender collection

    Returns:
        Floor mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for floor creation")

    # Create mesh
    mesh = bpy.data.meshes.new(f"{config.name}_floor")
    obj = bpy.data.objects.new(f"{config.name}_floor", mesh)

    # Create floor geometry
    bm = bmesh.new()

    half_width = config.width / 2
    half_depth = config.depth / 2

    # Create vertices
    v1 = bm.verts.new((-half_width, -half_depth, 0))
    v2 = bm.verts.new((half_width, -half_depth, 0))
    v3 = bm.verts.new((half_width, half_depth, 0))
    v4 = bm.verts.new((-half_width, half_depth, 0))
    bm.verts.ensure_lookup_table()

    # Create face
    bm.faces.new([v1, v2, v3, v4])

    # Update mesh
    bm.to_mesh(mesh)
    bm.free()

    # Add to collection
    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    # Set material (placeholder - would be replaced with actual material system)
    # obj.material_slots[0].material = get_material(config.floor_material)

    return obj


def create_ceiling(config: RoomConfig, collection: Any = None) -> Any:
    """
    Create ceiling mesh.

    Args:
        config: Room configuration
        collection: Optional Blender collection

    Returns:
        Ceiling mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for ceiling creation")

    # Create mesh
    mesh = bpy.data.meshes.new(f"{config.name}_ceiling")
    obj = bpy.data.objects.new(f"{config.name}_ceiling", mesh)

    # Create ceiling geometry
    bm = bmesh.new()

    half_width = config.width / 2
    half_depth = config.depth / 2
    ceiling_z = config.height

    # Create vertices (flipped normal - facing down)
    v1 = bm.verts.new((-half_width, -half_depth, ceiling_z))
    v2 = bm.verts.new((-half_width, half_depth, ceiling_z))
    v3 = bm.verts.new((half_width, half_depth, ceiling_z))
    v4 = bm.verts.new((half_width, -half_depth, ceiling_z))
    bm.verts.ensure_lookup_table()

    # Create face (counter-clockwise for downward normal)
    bm.faces.new([v1, v2, v3, v4])

    # Update mesh
    bm.to_mesh(mesh)
    bm.free()

    # Add to collection
    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def create_wall(
    config: WallConfig,
    position: Tuple[float, float, float],
    rotation: float,
    collection: Any = None,
    name: str = "wall"
) -> Any:
    """
    Create wall mesh at specified position and rotation.

    Args:
        config: Wall configuration
        position: Wall center position (x, y, z)
        rotation: Wall rotation around Z axis in radians
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Wall mesh object
    """
    try:
        import bpy
        import bmesh
        from mathutils import Matrix
    except ImportError:
        raise ImportError("Blender required for wall creation")

    # Create mesh
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    # Create wall geometry
    bm = bmesh.new()

    half_width = config.width / 2
    half_height = config.height / 2
    half_thickness = config.thickness / 2

    # Create 8 vertices for the wall box
    # Front face
    v1 = bm.verts.new((-half_width, -half_thickness, 0))
    v2 = bm.verts.new((half_width, -half_thickness, 0))
    v3 = bm.verts.new((half_width, -half_thickness, config.height))
    v4 = bm.verts.new((-half_width, -half_thickness, config.height))

    # Back face
    v5 = bm.verts.new((-half_width, half_thickness, 0))
    v6 = bm.verts.new((half_width, half_thickness, 0))
    v7 = bm.verts.new((half_width, half_thickness, config.height))
    v8 = bm.verts.new((-half_width, half_thickness, config.height))

    bm.verts.ensure_lookup_table()

    # Create faces (6 sides of the box)
    # Front face (visible from inside room)
    bm.faces.new([v1, v2, v3, v4])
    # Back face
    bm.faces.new([v6, v5, v8, v7])
    # Left edge
    bm.faces.new([v5, v1, v4, v8])
    # Right edge
    bm.faces.new([v2, v6, v7, v3])
    # Top edge
    bm.faces.new([v4, v3, v7, v8])
    # Bottom edge
    bm.faces.new([v1, v5, v6, v2])

    # Update mesh
    bm.to_mesh(mesh)
    bm.free()

    # Position and rotate the wall
    obj.location = position
    obj.rotation_euler = (0, 0, rotation)

    # Add to collection
    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def add_wall_opening(
    wall: Any,
    opening_type: str,
    position: Tuple[float, float, float],
    size: Tuple[float, float, float],
    collection: Any = None
) -> Any:
    """
    Add door/window opening to wall by boolean subtraction.

    Args:
        wall: Wall mesh object
        opening_type: Type of opening ('door', 'window', 'arch')
        position: Opening position relative to wall center
        size: Opening size (width, depth, height)
        collection: Optional Blender collection

    Returns:
        Boolean modifier applied to wall
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for wall opening")

    # Create opening cutter mesh
    cutter_mesh = bpy.data.meshes.new(f"{wall.name}_cutter")
    cutter_obj = bpy.data.objects.new(f"{wall.name}_cutter", cutter_mesh)

    # Create box for opening
    bm = bmesh.new()

    half_w = size[0] / 2
    half_d = size[1] / 2
    half_h = size[2] / 2

    # Create vertices
    verts = []
    for x in [-half_w, half_w]:
        for y in [-half_d, half_d]:
            for z in [-half_h, half_h]:
                v = bm.verts.new((x, y, z))
                verts.append(v)

    bm.verts.ensure_lookup_table()

    # Create faces
    # Front
    bm.faces.new([verts[0], verts[1], verts[3], verts[2]])
    # Back
    bm.faces.new([verts[5], verts[4], verts[6], verts[7]])
    # Left
    bm.faces.new([verts[4], verts[0], verts[2], verts[6]])
    # Right
    bm.faces.new([verts[1], verts[5], verts[7], verts[3]])
    # Top
    bm.faces.new([verts[2], verts[3], verts[7], verts[6]])
    # Bottom
    bm.faces.new([verts[4], verts[5], verts[1], verts[0]])

    bm.to_mesh(cutter_mesh)
    bm.free()

    # Position cutter
    cutter_obj.location = position

    # Add to scene (hide from render)
    if collection:
        collection.objects.link(cutter_obj)
    else:
        bpy.context.collection.objects.link(cutter_obj)

    # Add boolean modifier to wall
    mod = wall.modifiers.new(name="Opening", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter_obj

    # Hide cutter object
    cutter_obj.hide_render = True
    cutter_obj.hide_viewport = True

    return mod


def create_molding(
    type: str,
    length: float,
    height: float,
    depth: float,
    position: Tuple[float, float, float],
    rotation: float,
    collection: Any = None,
    name: str = "molding"
) -> Any:
    """
    Create baseboard or crown molding.

    Args:
        type: Molding type ('baseboard', 'crown', 'chair_rail')
        length: Molding length in meters
        height: Molding height in meters
        depth: Molding depth/projection from wall
        position: Position in scene
        rotation: Rotation around Z axis
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Molding mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for molding creation")

    # Create mesh
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()

    half_length = length / 2

    if type == "baseboard":
        # Simple rectangular baseboard profile
        # Front face vertices
        v1 = bm.verts.new((-half_length, 0, 0))
        v2 = bm.verts.new((half_length, 0, 0))
        v3 = bm.verts.new((half_length, 0, height))
        v4 = bm.verts.new((-half_length, 0, height))
        # Back face vertices
        v5 = bm.verts.new((-half_length, -depth, 0))
        v6 = bm.verts.new((half_length, -depth, 0))
        v7 = bm.verts.new((half_length, -depth, height))
        v8 = bm.verts.new((-half_length, -depth, height))

    elif type == "crown":
        # Angled crown molding profile
        angle = math.radians(45)
        crown_depth = depth
        crown_height = height

        # Front profile (angled top)
        v1 = bm.verts.new((-half_length, 0, 0))
        v2 = bm.verts.new((half_length, 0, 0))
        v3 = bm.verts.new((half_length, -crown_depth, crown_height))
        v4 = bm.verts.new((-half_length, -crown_depth, crown_height))
        # Back profile
        v5 = bm.verts.new((-half_length, -crown_depth * 0.3, 0))
        v6 = bm.verts.new((half_length, -crown_depth * 0.3, 0))
        v7 = bm.verts.new((half_length, -crown_depth * 1.3, crown_height))
        v8 = bm.verts.new((-half_length, -crown_depth * 1.3, crown_height))

    elif type == "chair_rail":
        # Simple rectangular chair rail
        rail_height = height
        rail_depth = depth * 0.5  # Thinner than baseboard

        # Front face
        v1 = bm.verts.new((-half_length, 0, 0))
        v2 = bm.verts.new((half_length, 0, 0))
        v3 = bm.verts.new((half_length, 0, rail_height))
        v4 = bm.verts.new((-half_length, 0, rail_height))
        # Back face
        v5 = bm.verts.new((-half_length, -rail_depth, 0))
        v6 = bm.verts.new((half_length, -rail_depth, 0))
        v7 = bm.verts.new((half_length, -rail_depth, rail_height))
        v8 = bm.verts.new((-half_length, -rail_depth, rail_height))
    else:
        # Default to baseboard profile
        v1 = bm.verts.new((-half_length, 0, 0))
        v2 = bm.verts.new((half_length, 0, 0))
        v3 = bm.verts.new((half_length, 0, height))
        v4 = bm.verts.new((-half_length, 0, height))
        v5 = bm.verts.new((-half_length, -depth, 0))
        v6 = bm.verts.new((half_length, -depth, 0))
        v7 = bm.verts.new((half_length, -depth, height))
        v8 = bm.verts.new((-half_length, -depth, height))

    bm.verts.ensure_lookup_table()

    # Create faces
    bm.faces.new([v1, v2, v3, v4])  # Front
    bm.faces.new([v6, v5, v8, v7])  # Back
    bm.faces.new([v5, v1, v4, v8])  # Left
    bm.faces.new([v2, v6, v7, v3])  # Right
    bm.faces.new([v4, v3, v7, v8])  # Top
    bm.faces.new([v1, v5, v6, v2])  # Bottom

    bm.to_mesh(mesh)
    bm.free()

    # Position and rotate
    obj.location = position
    obj.rotation_euler = (0, 0, rotation)

    # Add to collection
    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def create_wainscoting(
    wall: Any,
    height: float,
    panel_width: float,
    rail_height: float,
    stile_width: float,
    collection: Any = None
) -> List[Any]:
    """
    Create wainscoting panels on a wall.

    Args:
        wall: Wall mesh object
        height: Wainscoting height
        panel_width: Width of each raised panel
        rail_height: Height of top/bottom rails
        stile_width: Width of side stiles
        collection: Optional Blender collection

    Returns:
        List of wainscoting panel objects
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("Blender required for wainscoting")

    # This would create raised panel wainscoting
    # For simplicity, returning empty list - full implementation
    # would create individual panel meshes
    return []


def get_wall_bounds(config: WallConfig, position: Tuple[float, float, float]) -> Dict[str, float]:
    """
    Calculate wall bounding box.

    Args:
        config: Wall configuration
        position: Wall center position

    Returns:
        Dictionary with min/max bounds
    """
    half_width = config.width / 2
    half_thickness = config.thickness / 2

    return {
        "min_x": position[0] - half_width,
        "max_x": position[0] + half_width,
        "min_y": position[1] - half_thickness,
        "max_y": position[1] + half_thickness,
        "min_z": position[2],
        "max_z": position[2] + config.height,
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RoomMeshes",
    "create_room",
    "create_floor",
    "create_ceiling",
    "create_wall",
    "add_wall_opening",
    "create_molding",
    "create_wainscoting",
    "get_wall_bounds",
]
