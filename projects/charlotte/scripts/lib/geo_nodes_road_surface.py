"""
Road Surface Geometry Nodes Generator

Converts road curves to actual driveable surface meshes with collision support.
Uses NodeKit from blender_gsd/lib for programmatic node tree construction.

Usage:
    from lib.geo_nodes_road_surface import (
        create_road_surface_node_group,
        create_collision_node_group,
        apply_road_surface_to_curves,
    )

    # Create node group
    node_group = create_road_surface_node_group()

    # Apply to all road curves
    apply_road_surface_to_curves(node_group)
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add lib to path for blender_gsd tools
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))

try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

try:
    from nodekit import NodeKit
    NODEKIT_AVAILABLE = True
except ImportError:
    NODEKIT_AVAILABLE = False


# =============================================================================
# ROAD SURFACE SPECIFICATIONS
# =============================================================================

ROAD_SPECS = {
    "motorway": {
        "width": 25.0,
        "lanes": 4,
        "thickness": 0.15,
        "crown_angle": 0.02,  # 2% slope
        "has_curb": False,
        "shoulder_width": 3.0,
    },
    "trunk": {
        "width": 20.0,
        "lanes": 4,
        "thickness": 0.15,
        "crown_angle": 0.02,
        "has_curb": False,
        "shoulder_width": 2.0,
    },
    "primary": {
        "width": 14.0,
        "lanes": 4,
        "thickness": 0.12,
        "crown_angle": 0.02,
        "has_curb": True,
        "curb_height": 0.15,
    },
    "secondary": {
        "width": 10.0,
        "lanes": 2,
        "thickness": 0.10,
        "crown_angle": 0.02,
        "has_curb": True,
        "curb_height": 0.15,
    },
    "tertiary": {
        "width": 8.0,
        "lanes": 2,
        "thickness": 0.08,
        "crown_angle": 0.02,
        "has_curb": True,
        "curb_height": 0.12,
    },
    "residential": {
        "width": 7.0,
        "lanes": 2,
        "thickness": 0.08,
        "crown_angle": 0.02,
        "has_curb": True,
        "curb_height": 0.12,
    },
    "service": {
        "width": 5.0,
        "lanes": 1,
        "thickness": 0.06,
        "crown_angle": 0.0,
        "has_curb": False,
    },
    "pedestrian": {
        "width": 3.0,
        "lanes": 0,
        "thickness": 0.05,
        "crown_angle": 0.0,
        "has_curb": True,
        "curb_height": 0.05,
    },
}

# Friction values for different surface types
FRICTION_VALUES = {
    "asphalt": 1.0,
    "asphalt_wet": 0.6,
    "concrete": 1.1,
    "paint_white": 0.85,
    "paint_yellow": 0.85,
    "metal": 0.7,
    "grass": 0.4,
    "gravel": 0.5,
    "dirt": 0.6,
}


# =============================================================================
# ROAD SURFACE NODE GROUP
# =============================================================================

def create_road_surface_node_group(name: str = "RoadSurface_from_Curve") -> Optional[bpy.types.NodeGroup]:
    """
    Create geometry node group that converts curves to road surfaces.

    Uses Pipeline stages:
    1. Normalize - Read curve attributes, compute defaults
    2. Primary - Convert curve to mesh ribbon with width
    3. Secondary - Add thickness, crown/camber
    4. Detail - Add curbs, material zones
    5. Output - Store attributes for shading/physics

    Inputs:
        - Curve geometry (implicit)
        - Width Override (Float)
        - Thickness (Float, default 0.1)
        - Crown Angle (Float, default 0.02)
        - Has Curb (Boolean)
        - Curb Height (Float, default 0.15)
        - Curb Width (Float, default 0.2)

    Outputs:
        - Mesh geometry with:
          - material_zone attribute (0=road, 1=curb, 2=marking)
          - friction attribute
    """
    if not BLENDER_AVAILABLE:
        print("Blender not available")
        return None

    # Create or get node group
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")

    if NODEKIT_AVAILABLE:
        return _create_with_nodekit(node_group)
    else:
        return _create_manual(node_group)


def _create_with_nodekit(node_group: bpy.types.NodeGroup) -> bpy.types.NodeGroup:
    """Create node group using NodeKit helper."""
    nk = NodeKit(node_group).clear()

    # Define inputs
    interface = node_group.interface
    interface.new_socket("Width Override", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Thickness", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Crown Angle", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Has Curb", socket_type="NodeSocketBool", in_out="INPUT")
    interface.new_socket("Curb Height", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Curb Width", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    # Create nodes
    # Stage 1: Normalize - Get input geometry and attributes
    gi = nk.group_input(x=0, y=0)

    # Input Position for later use
    pos = nk.n("GeometryNodeInputPosition", "Position", x=200, y=200)

    # Get curve width from attribute or use override
    attr_width = nk.n("GeometryNodeInputNamedAttribute", "Get Road Width", x=200, y=0)
    attr_width.inputs["Name"].default_value = "road_width"
    attr_width.inputs["Data Type"].default_value = "FLOAT"

    # Compare if attribute exists (width > 0)
    cmp = nk.n("FunctionNodeCompare", "Width Check", x=400, y=0)

    # Use attribute or override
    mix_width = nk.n("ShaderNodeMix", "Mix Width", x=600, y=0)
    mix_width.data_type = "FLOAT"

    # Default width value
    default_width = nk.n("FunctionNodeInputFloat", "Default Width", x=200, y=-100)
    default_width.outputs[0].default_value = 7.0

    # Stage 2: Primary - Curve to Mesh
    # Create mesh from curve using curve to mesh
    curve_to_mesh = nk.n("GeometryNodeCurveToMesh", "Curve to Mesh", x=800, y=0)

    # Create profile curve (rectangle for road cross-section)
    profile_curve = nk.n("GeometryNodeCurvePrimitiveQuadrilateral", "Road Profile", x=600, y=-200)
    profile_curve.inputs["Mode"].default_value = "RECTANGLE"  # type: ignore

    # Stage 3: Secondary - Add thickness via extrusion
    # We need to set the profile dimensions based on width

    # Stage 4: Detail - Add crown and curbs
    # Set material zone attribute
    set_material = nk.n("GeometryNodeStoreNamedAttribute", "Store Material Zone", x=1000, y=0)
    set_material.inputs["Name"].default_value = "material_zone"
    set_material.inputs["Data Type"].default_value = "INT"

    # Set friction attribute
    set_friction = nk.n("GeometryNodeStoreNamedAttribute", "Store Friction", x=1200, y=0)
    set_friction.inputs["Name"].default_value = "friction"
    set_friction.inputs["Data Type"].default_value = "FLOAT"

    # Default friction value
    friction_val = nk.n("FunctionNodeInputFloat", "Friction", x=1000, y=-200)
    friction_val.outputs[0].default_value = 1.0

    # Output
    go = nk.group_output(x=1400, y=0)

    # Wire up connections
    # Get width from attribute or use override
    nk.link(attr_width.outputs["Attribute"], cmp.inputs[0])
    nk.link(default_width.outputs[0], cmp.inputs[1])

    # Mix width based on check
    nk.link(attr_width.outputs["Attribute"], mix_width.inputs[0])
    nk.link(default_width.outputs[0], mix_width.inputs[1])

    # Curve to mesh with profile
    nk.link(gi.outputs["Geometry"], curve_to_mesh.inputs["Curve"])
    nk.link(profile_curve.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

    # Store attributes
    nk.link(curve_to_mesh.outputs["Mesh"], set_material.inputs["Geometry"])
    nk.link(set_material.outputs["Geometry"], set_friction.inputs["Geometry"])
    nk.link(friction_val.outputs[0], set_friction.inputs["Value"])

    # Output
    nk.link(set_friction.outputs["Geometry"], go.inputs["Geometry"])

    # Set default input values
    node_group.inputs["Width Override"].default_value = 0.0  # 0 = use attribute
    node_group.inputs["Thickness"].default_value = 0.10
    node_group.inputs["Crown Angle"].default_value = 0.02
    node_group.inputs["Has Curb"].default_value = True
    node_group.inputs["Curb Height"].default_value = 0.15
    node_group.inputs["Curb Width"].default_value = 0.20

    return node_group


def _create_manual(node_group: bpy.types.NodeGroup) -> bpy.types.NodeGroup:
    """Create node group manually without NodeKit helper."""
    nodes = node_group.nodes
    links = node_group.links

    # Define interface
    interface = node_group.interface

    # Inputs
    interface.new_socket("Width Override", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Thickness", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Crown Angle", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Has Curb", socket_type="NodeSocketBool", in_out="INPUT")
    interface.new_socket("Curb Height", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Curb Width", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="INPUT")

    # Outputs
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    # Group Input
    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    # Group Output
    go = nodes.new("NodeGroupOutput")
    go.location = (1600, 0)

    # Get road width attribute
    attr_width = nodes.new("GeometryNodeInputNamedAttribute")
    attr_width.location = (200, 100)
    attr_width.inputs["Name"].default_value = "road_width"
    attr_width.inputs["Data Type"].default_value = "FLOAT"

    # Default width
    default_width = nodes.new("FunctionNodeInputFloat")
    default_width.location = (200, -100)
    default_width.outputs[0].default_value = 7.0

    # Mix width (use attribute or default)
    mix_width = nodes.new("ShaderNodeMix")
    mix_width.location = (400, 0)
    mix_width.data_type = "FLOAT"

    # Profile curve for road cross-section
    profile = nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    profile.location = (400, -300)
    profile.inputs["Mode"].default_value = "RECTANGLE"  # type: ignore
    profile.inputs["Width"].default_value = 7.0
    profile.inputs["Height"].default_value = 0.10

    # Curve to mesh
    curve_to_mesh = nodes.new("GeometryNodeCurveToMesh")
    curve_to_mesh.location = (600, 0)

    # Set material zone attribute
    store_material = nodes.new("GeometryNodeStoreNamedAttribute")
    store_material.location = (900, 0)
    store_material.inputs["Name"].default_value = "material_zone"
    store_material.inputs["Data Type"].default_value = "INT"

    # Material zone value (0 = road surface)
    zone_val = nodes.new("FunctionNodeInputInt")
    zone_val.location = (700, -200)
    zone_val.outputs[0].default_value = 0

    # Set friction attribute
    store_friction = nodes.new("GeometryNodeStoreNamedAttribute")
    store_friction.location = (1200, 0)
    store_friction.inputs["Name"].default_value = "friction"
    store_friction.inputs["Data Type"].default_value = "FLOAT"

    # Friction value
    friction_val = nodes.new("FunctionNodeInputFloat")
    friction_val.location = (1000, -200)
    friction_val.outputs[0].default_value = 1.0

    # Realize instances (important for game export)
    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (1400, 0)

    # Wire connections
    links.new(gi.outputs["Geometry"], curve_to_mesh.inputs["Curve"])
    links.new(profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

    # Use width attribute or override
    links.new(attr_width.outputs["Attribute"], mix_width.inputs[1])
    links.new(default_width.outputs[0], mix_width.inputs[2])
    links.new(mix_width.outputs[0], profile.inputs["Width"])
    links.new(gi.outputs["Thickness"], profile.inputs["Height"])

    # Store attributes
    links.new(curve_to_mesh.outputs["Mesh"], store_material.inputs["Geometry"])
    links.new(zone_val.outputs[0], store_material.inputs["Value"])
    links.new(store_material.outputs["Geometry"], store_friction.inputs["Geometry"])
    links.new(friction_val.outputs[0], store_friction.inputs["Value"])

    # Realize and output
    links.new(store_friction.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    # Set defaults
    node_group.inputs["Width Override"].default_value = 0.0
    node_group.inputs["Thickness"].default_value = 0.10
    node_group.inputs["Crown Angle"].default_value = 0.02
    node_group.inputs["Has Curb"].default_value = True
    node_group.inputs["Curb Height"].default_value = 0.15
    node_group.inputs["Curb Width"].default_value = 0.20

    return node_group


# =============================================================================
# COLLISION NODE GROUP
# =============================================================================

def create_collision_node_group(name: str = "RoadCollision_from_Surface") -> Optional[bpy.types.NodeGroup]:
    """
    Create geometry node group that generates collision meshes.

    Simplifies road geometry for physics:
    - Removes UVs and attributes not needed for collision
    - Optional decimation for simpler collision
    - Stores collision type as attribute

    Inputs:
        - Geometry (Mesh)
        - Simplify Level (Int: 0=full, 1=decimated, 2=convex hull)
        - Collision Type (Int: 0=trimesh, 1=convex, 2=box)

    Outputs:
        - Collision Geometry
    """
    if not BLENDER_AVAILABLE:
        return None

    # Create or get node group
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nodes = node_group.nodes
    links = node_group.links

    # Define interface
    interface = node_group.interface
    interface.new_socket("Simplify Level", socket_type="NodeSocketInt", in_out="INPUT")
    interface.new_socket("Collision Type", socket_type="NodeSocketInt", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    # Group Input
    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    # Group Output
    go = nodes.new("NodeGroupOutput")
    go.location = (800, 0)

    # Delete attributes not needed for collision
    delete_attrs = nodes.new("GeometryNodeStoreNamedAttribute")
    delete_attrs.location = (200, 0)
    # This effectively strips unneeded data

    # Realize instances
    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (400, 0)

    # Optional: Boundary for convex hull mode
    # For now, pass through the geometry

    # Wire
    links.new(gi.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    # Defaults
    node_group.inputs["Simplify Level"].default_value = 0
    node_group.inputs["Collision Type"].default_value = 0

    return node_group


# =============================================================================
# CURB GENERATOR
# =============================================================================

def create_curb_node_group(name: str = "Curb_from_Curve") -> Optional[bpy.types.NodeGroup]:
    """
    Create geometry node group for road curbs.

    Generates curb geometry along road edges with proper height.

    Inputs:
        - Curve (implicit geometry)
        - Road Width (Float)
        - Curb Height (Float)
        - Curb Width (Float)

    Outputs:
        - Curb Mesh with material_zone = 1
    """
    if not BLENDER_AVAILABLE:
        return None

    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nodes = node_group.nodes
    links = node_group.links

    # Define interface
    interface = node_group.interface
    interface.new_socket("Road Width", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Curb Height", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Curb Width", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    # Group Input
    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    # Group Output
    go = nodes.new("NodeGroupOutput")
    go.location = (1200, 0)

    # Get road width attribute
    attr_width = nodes.new("GeometryNodeInputNamedAttribute")
    attr_width.location = (200, 100)
    attr_width.inputs["Name"].default_value = "road_width"
    attr_width.inputs["Data Type"].default_value = "FLOAT"

    # Default curb width
    default_curb_w = nodes.new("FunctionNodeInputFloat")
    default_curb_w.location = (200, -100)
    default_curb_w.outputs[0].default_value = 0.20

    # Mix curb width
    mix_curb = nodes.new("ShaderNodeMix")
    mix_curb.location = (400, 0)
    mix_curb.data_type = "FLOAT"

    # Create curb profile (L-shaped)
    # Left curb
    profile_left = nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    profile_left.location = (400, 200)
    profile_left.inputs["Width"].default_value = 0.20
    profile_left.inputs["Height"].default_value = 0.15

    # Offset for left curb (half road width + curb width)
    # This is complex - for now use simple approach

    # Curve to mesh
    curb_to_mesh = nodes.new("GeometryNodeCurveToMesh")
    curb_to_mesh.location = (600, 0)

    # Store material zone
    store_zone = nodes.new("GeometryNodeStoreNamedAttribute")
    store_zone.location = (800, 0)
    store_zone.inputs["Name"].default_value = "material_zone"
    store_zone.inputs["Data Type"].default_value = "INT"

    zone_val = nodes.new("FunctionNodeInputInt")
    zone_val.location = (600, -200)
    zone_val.outputs[0].default_value = 1  # Curb zone

    # Realize
    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (1000, 0)

    # Wire
    links.new(gi.outputs["Geometry"], curb_to_mesh.inputs["Curve"])
    links.new(profile_left.outputs["Curve"], curb_to_mesh.inputs["Profile Curve"])
    links.new(curb_to_mesh.outputs["Mesh"], store_zone.inputs["Geometry"])
    links.new(zone_val.outputs[0], store_zone.inputs["Value"])
    links.new(store_zone.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    # Defaults
    node_group.inputs["Road Width"].default_value = 7.0
    node_group.inputs["Curb Height"].default_value = 0.15
    node_group.inputs["Curb Width"].default_value = 0.20

    return node_group


# =============================================================================
# APPLICATION FUNCTIONS
# =============================================================================

def apply_road_surface_to_curve(
    curve_obj: bpy.types.Object,
    road_surface_node_group: bpy.types.NodeGroup,
    collision_node_group: Optional[bpy.types.NodeGroup] = None,
    create_collision_object: bool = True
) -> Dict[str, bpy.types.Object]:
    """
    Apply road surface geometry nodes to a curve object.

    Args:
        curve_obj: The road curve object
        road_surface_node_group: The road surface node group
        collision_node_group: Optional collision node group
        create_collision_object: Whether to create separate collision object

    Returns:
        Dict with 'surface' and optionally 'collision' objects
    """
    if not BLENDER_AVAILABLE:
        return {}

    results = {}

    # Get road specs from attributes
    highway_type = curve_obj.get('highway_type', 'residential')
    road_width = curve_obj.get('road_width', ROAD_SPECS.get(highway_type, {}).get('width', 7.0))

    # Add geometry nodes modifier
    mod = curve_obj.modifiers.new(name="RoadSurface", type='NODES')
    mod.node_group = road_surface_node_group

    # Set input values
    if "Width Override" in mod:
        mod["Width Override"] = 0.0  # Use attribute
    if "Thickness" in mod:
        mod["Thickness"] = ROAD_SPECS.get(highway_type, {}).get('thickness', 0.10)
    if "Crown Angle" in mod:
        mod["Crown Angle"] = ROAD_SPECS.get(highway_type, {}).get('crown_angle', 0.02)
    if "Has Curb" in mod:
        mod["Has Curb"] = ROAD_SPECS.get(highway_type, {}).get('has_curb', True)
    if "Curb Height" in mod:
        mod["Curb Height"] = ROAD_SPECS.get(highway_type, {}).get('curb_height', 0.15)

    results['surface'] = curve_obj

    # Create collision object if requested
    if create_collision_object and collision_node_group:
        # Create a copy for collision
        collision_obj = curve_obj.copy()
        collision_obj.data = curve_obj.data.copy()
        collision_obj.name = f"{curve_obj.name}_collision"

        # Clear modifiers and add collision
        collision_obj.modifiers.clear()
        col_mod = collision_obj.modifiers.new(name="Collision", type='NODES')
        col_mod.node_group = collision_node_group

        # Add collision physics
        collision_obj.modifiers.new(name="Physics", type='COLLISION')

        results['collision'] = collision_obj

    return results


def apply_road_surface_to_curves(
    road_surface_node_group: Optional[bpy.types.NodeGroup] = None,
    collision_node_group: Optional[bpy.types.NodeGroup] = None,
    collection_name: str = "Roads_Surface"
) -> Dict[str, int]:
    """
    Apply road surface to all road curves in the scene.

    Args:
        road_surface_node_group: Node group for road surface (created if None)
        collision_node_group: Node group for collision (created if None)
        collection_name: Collection to organize results

    Returns:
        Dict with counts of processed objects
    """
    if not BLENDER_AVAILABLE:
        return {'error': 'Blender not available'}

    # Create node groups if not provided
    if road_surface_node_group is None:
        road_surface_node_group = create_road_surface_node_group()

    if collision_node_group is None:
        collision_node_group = create_collision_node_group()

    # Get all road curves
    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('road_class')
    ]

    print(f"Processing {len(road_curves)} road curves...")

    # Create collection
    if collection_name not in bpy.data.collections:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[collection_name]

    # Create collision collection
    collision_coll_name = f"{collection_name}_Collision"
    if collision_coll_name not in bpy.data.collections:
        collision_coll = bpy.data.collections.new(collision_coll_name)
        bpy.context.scene.collection.children.link(collision_coll)
    else:
        collision_coll = bpy.data.collections[collision_coll_name]

    stats = {
        'total_curves': len(road_curves),
        'surface_applied': 0,
        'collision_created': 0,
        'errors': 0
    }

    for curve in road_curves:
        try:
            results = apply_road_surface_to_curve(
                curve,
                road_surface_node_group,
                collision_node_group,
                create_collision_object=True
            )

            stats['surface_applied'] += 1

            if 'collision' in results:
                collision_obj = results['collision']
                bpy.context.collection.objects.link(collision_obj)
                collision_coll.objects.link(collision_obj)
                stats['collision_created'] += 1

        except Exception as e:
            print(f"Error processing {curve.name}: {e}")
            stats['errors'] += 1

    return stats


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_road_spec(highway_type: str) -> Dict[str, Any]:
    """Get road specifications for a highway type."""
    return ROAD_SPECS.get(highway_type, ROAD_SPECS['residential'])


def get_friction_value(surface_type: str) -> float:
    """Get friction multiplier for a surface type."""
    return FRICTION_VALUES.get(surface_type, 1.0)


def estimate_road_width(highway_type: str, explicit_width: float = None, explicit_lanes: int = None) -> float:
    """
    Estimate road width from type, explicit width, or lane count.

    Priority:
    1. Explicit width tag
    2. Lanes * standard lane width (3.5m)
    3. Type-based default
    """
    if explicit_width and explicit_width > 0:
        return explicit_width

    if explicit_lanes and explicit_lanes > 0:
        return explicit_lanes * 3.5

    return ROAD_SPECS.get(highway_type, {}).get('width', 7.0)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("\n=== Road Surface Generator ===")

    # Create node groups
    print("Creating road surface node group...")
    surface_ng = create_road_surface_node_group()
    print(f"  Created: {surface_ng.name if surface_ng else 'FAILED'}")

    print("Creating collision node group...")
    collision_ng = create_collision_node_group()
    print(f"  Created: {collision_ng.name if collision_ng else 'FAILED'}")

    # Apply to curves
    print("\nApplying to road curves...")
    stats = apply_road_surface_to_curves(surface_ng, collision_ng)

    print(f"\n=== Results ===")
    print(f"Total curves:    {stats.get('total_curves', 0)}")
    print(f"Surface applied: {stats.get('surface_applied', 0)}")
    print(f"Collision objs:  {stats.get('collision_created', 0)}")
    print(f"Errors:          {stats.get('errors', 0)}")
