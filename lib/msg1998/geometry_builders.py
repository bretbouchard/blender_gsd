"""
MSG 1998 - Geometry Builders

Building geometry creation following Universal Stage Order.
"""

from typing import List, Optional, Tuple

try:
    import bpy
    import bmesh
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from .types import BuildingSpec, WindowSpec


def create_building_base(
    spec: BuildingSpec,
    name: str = "Building",
    context=None
):
    """
    Create primary building geometry (Stage 1: Primary).

    Args:
        spec: Building specification
        name: Object name
        context: Blender context (uses bpy.context if None)

    Returns:
        Blender mesh object (building base)
    """
    if not BLENDER_AVAILABLE:
        return None

    if context is None:
        context = bpy.context

    # Create mesh
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    context.collection.objects.link(obj)

    # Create bmesh for geometry
    bm = bmesh.new()

    w, d, h = spec.width_m / 2, spec.depth_m / 2, spec.height_m

    # Create base box vertices
    verts = [
        bm.verts.new((-w, -d, 0)),
        bm.verts.new((w, -d, 0)),
        bm.verts.new((w, d, 0)),
        bm.verts.new((-w, d, 0)),
        bm.verts.new((-w, -d, h)),
        bm.verts.new((w, -d, h)),
        bm.verts.new((w, d, h)),
        bm.verts.new((-w, d, h)),
    ]

    # Ensure lookup table for indexed access
    bm.verts.ensure_lookup_table()

    # Create faces
    # Bottom
    bm.faces.new([verts[0], verts[1], verts[2], verts[3]])
    # Top
    bm.faces.new([verts[4], verts[7], verts[6], verts[5]])
    # Front
    bm.faces.new([verts[0], verts[4], verts[5], verts[1]])
    # Back
    bm.faces.new([verts[2], verts[6], verts[7], verts[3]])
    # Left
    bm.faces.new([verts[0], verts[3], verts[7], verts[4]])
    # Right
    bm.faces.new([verts[1], verts[5], verts[6], verts[2]])

    # Update mesh
    bm.to_mesh(mesh)
    bm.free()

    # Add floor subdivision markers
    if spec.floors > 1:
        _add_floor_edges(obj, spec)

    return obj


def _add_floor_edges(obj, spec: BuildingSpec) -> None:
    """Add edge loops at floor boundaries."""
    if not BLENDER_AVAILABLE:
        return

    floor_height = spec.height_m / spec.floors

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    for i in range(1, spec.floors):
        height = i * floor_height
        bpy.ops.mesh.knife_project(cut_through=True)
        # The knife_project is complex; simplified approach:
        # Just add loop cuts
        bpy.ops.mesh.loopcut_slide(
            MESH_OT_loopcut={
                "number_cuts": 1,
                "smoothness": 0,
                "falloff": 'INVERSE_SQUARE'
            }
        )

    bpy.ops.object.mode_set(mode='OBJECT')


def add_windows(
    building,
    window_spec: Optional[WindowSpec] = None,
    positions: Optional[List[Tuple[float, float, float]]] = None,
    face_index: int = 4  # Front face by default
) -> List:
    """
    Add window geometry to building (Stage 2: Secondary).

    Args:
        building: Building mesh object
        window_spec: Window specification
        positions: List of (x, y, z) positions for windows
        face_index: Index of face to add windows to

    Returns:
        List of window objects
    """
    if not BLENDER_AVAILABLE:
        return []

    if window_spec is None:
        window_spec = WindowSpec()

    windows = []

    if positions is None:
        # Generate default window positions based on building size
        bbox = building.bound_box
        width = max(v[0] for v in bbox) - min(v[0] for v in bbox)
        height = max(v[2] for v in bbox) - min(v[2] for v in bbox)

        # Create grid of windows
        cols = int(width / (window_spec.width_m * 2))
        rows = int(height / (window_spec.height_m * 2))

        positions = []
        for row in range(1, rows):
            for col in range(1, cols):
                x = -width/2 + col * (width / cols)
                z = row * (height / rows)
                positions.append((x, 0.01, z))

    for i, pos in enumerate(positions):
        window = _create_single_window(
            window_spec,
            name=f"Window_{i:03d}",
            location=pos
        )
        if window:
            windows.append(window)

    return windows


def _create_single_window(spec: WindowSpec, name: str, location: Tuple[float, float, float]):
    """Create a single window mesh."""
    if not BLENDER_AVAILABLE:
        return None

    w, h = spec.width_m / 2, spec.height_m / 2
    d = spec.frame_depth_m

    # Create window frame
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()

    # Outer frame
    outer_verts = [
        bm.verts.new((-w - 0.05, -d, -h - 0.05)),
        bm.verts.new((w + 0.05, -d, -h - 0.05)),
        bm.verts.new((w + 0.05, -d, h + 0.05)),
        bm.verts.new((-w - 0.05, -d, h + 0.05)),
        bm.verts.new((-w - 0.05, d, -h - 0.05)),
        bm.verts.new((w + 0.05, d, -h - 0.05)),
        bm.verts.new((w + 0.05, d, h + 0.05)),
        bm.verts.new((-w - 0.05, d, h + 0.05)),
    ]

    # Inner frame (glass opening)
    inner_verts = [
        bm.verts.new((-w, -d * 0.5, -h)),
        bm.verts.new((w, -d * 0.5, -h)),
        bm.verts.new((w, -d * 0.5, h)),
        bm.verts.new((-w, -d * 0.5, h)),
        bm.verts.new((-w, d * 0.5, -h)),
        bm.verts.new((w, d * 0.5, -h)),
        bm.verts.new((w, d * 0.5, h)),
        bm.verts.new((-w, d * 0.5, h)),
    ]

    bm.verts.ensure_lookup_table()

    # Create frame faces (simplified - just front and back)
    # Front face (outer to inner)
    bm.faces.new([outer_verts[0], outer_verts[1], inner_verts[1], inner_verts[0]])
    bm.faces.new([outer_verts[1], outer_verts[2], inner_verts[2], inner_verts[1]])
    bm.faces.new([outer_verts[2], outer_verts[3], inner_verts[3], inner_verts[2]])
    bm.faces.new([outer_verts[3], outer_verts[0], inner_verts[0], inner_verts[3]])

    # Glass face
    bm.faces.new([inner_verts[0], inner_verts[1], inner_verts[2], inner_verts[3]])

    bm.to_mesh(mesh)
    bm.free()

    obj.location = location

    return obj


def add_doors(
    building,
    door_width: float = 1.0,
    door_height: float = 2.2,
    positions: Optional[List[Tuple[float, float, float]]] = None
) -> List:
    """
    Add door geometry to building (Stage 2: Secondary).

    Args:
        building: Building mesh object
        door_width: Door width in meters
        door_height: Door height in meters
        positions: List of (x, y, z) positions for doors

    Returns:
        List of door objects
    """
    if not BLENDER_AVAILABLE:
        return []

    doors = []

    if positions is None:
        # Default: single door at ground level center
        bbox = building.bound_box
        positions = [(0, 0.01, door_height / 2)]

    for i, pos in enumerate(positions):
        door = _create_single_door(
            width=door_width,
            height=door_height,
            name=f"Door_{i:03d}",
            location=pos
        )
        if door:
            doors.append(door)

    return doors


def _create_single_door(width: float, height: float, name: str, location: Tuple[float, float, float]):
    """Create a single door mesh."""
    if not BLENDER_AVAILABLE:
        return None

    w, h = width / 2, height

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()

    # Door panel (simple flat door)
    d = 0.05  # Door thickness

    verts = [
        bm.verts.new((-w, -d/2, 0)),
        bm.verts.new((w, -d/2, 0)),
        bm.verts.new((w, d/2, 0)),
        bm.verts.new((-w, d/2, 0)),
        bm.verts.new((-w, -d/2, h)),
        bm.verts.new((w, -d/2, h)),
        bm.verts.new((w, d/2, h)),
        bm.verts.new((-w, d/2, h)),
    ]

    bm.verts.ensure_lookup_table()

    # Create faces
    bm.faces.new([verts[0], verts[1], verts[2], verts[3]])  # Bottom
    bm.faces.new([verts[4], verts[7], verts[6], verts[5]])  # Top
    bm.faces.new([verts[0], verts[4], verts[5], verts[1]])  # Front
    bm.faces.new([verts[2], verts[6], verts[7], verts[3]])  # Back
    bm.faces.new([verts[0], verts[3], verts[7], verts[4]])  # Left
    bm.faces.new([verts[1], verts[5], verts[6], verts[2]])  # Right

    bm.to_mesh(mesh)
    bm.free()

    obj.location = location

    return obj


def add_architectural_details(
    building,
    detail_type: str = "cornice",
    height_offset: float = 0
) -> None:
    """
    Add secondary architectural details (Stage 2: Secondary).

    Args:
        building: Building mesh object
        detail_type: Type of detail ("cornice", "cornice_simple", "base_molding")
        height_offset: Height offset from building top
    """
    if not BLENDER_AVAILABLE:
        return

    bbox = building.bound_box
    building_height = max(v[2] for v in bbox)
    building_width = max(v[0] for v in bbox) - min(v[0] for v in bbox)
    building_depth = max(v[1] for v in bbox) - min(v[1] for v in bbox)

    if detail_type == "cornice":
        _add_cornice(building, building_width, building_depth, building_height, height_offset)
    elif detail_type == "base_molding":
        _add_base_molding(building, building_width, building_depth)


def _add_cornice(building, width: float, depth: float, height: float, offset: float) -> None:
    """Add cornice detail at top of building."""
    if not BLENDER_AVAILABLE:
        return

    # Create simple cornice as thin box on top
    cornice_height = 0.15
    cornice_depth = 0.1

    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, height + cornice_height/2 + offset)
    )
    cornice = bpy.context.active_object
    cornice.name = f"{building.name}_cornice"

    cornice.scale = (width/2 + cornice_depth, depth/2 + cornice_depth, cornice_height/2)


def _add_base_molding(building, width: float, depth: float) -> None:
    """Add base molding at bottom of building."""
    if not BLENDER_AVAILABLE:
        return

    molding_height = 0.3
    molding_depth = 0.05

    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, molding_height/2)
    )
    molding = bpy.context.active_object
    molding.name = f"{building.name}_base_molding"

    molding.scale = (width/2 + molding_depth, depth/2 + molding_depth, molding_height/2)
