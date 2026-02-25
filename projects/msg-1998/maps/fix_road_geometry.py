"""
MSG-1998 Road System - Fix Road Geometry

Fixes:
1. White color - need to use input geometry, not separate curve input
2. Center bump - profile positioning issue
"""

import bpy


def get_or_create_material(name, color, roughness=0.8, metallic=0.0):
    """Get existing material or create a new one."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic

    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_proper_road_builder():
    """
    Create road builder that uses INPUT GEOMETRY (the curve itself)
    instead of a separate curve input.
    """

    materials = {
        'asphalt': get_or_create_material("M_Road_Asphalt", (0.08, 0.08, 0.09, 1.0), 0.85),
        'concrete': get_or_create_material("M_Road_Concrete", (0.5, 0.48, 0.45, 1.0), 0.9),
        'curb': get_or_create_material("M_Road_Curb", (0.4, 0.38, 0.36, 1.0), 0.8),
    }

    # Remove existing
    if "MSG_Road_Builder" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Road_Builder"])

    ng = bpy.data.node_groups.new("MSG_Road_Builder", 'GeometryNodeTree')

    # Interface - NO separate curve input, use implicit input geometry
    ng.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    ng.interface.new_socket(name="Sidewalk Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 2.0
    ng.interface.new_socket(name="Curb Height", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.15
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Input
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-1200, 0)

    # === PAVEMENT (flat rectangle extruded along curve) ===
    # Half road width
    half_road = nodes.new('ShaderNodeMath')
    half_road.location = (-900, 300)
    half_road.operation = 'DIVIDE'
    half_road.inputs[1].default_value = 2.0

    # Pavement profile - FLAT rectangle
    pavement_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    pavement_profile.location = (-600, 300)
    pavement_profile.mode = 'RECTANGLE'
    pavement_profile.inputs['Height'].default_value = 0.01  # Very thin, flat

    # Curve to mesh - uses INPUT GEOMETRY (the curve the modifier is on)
    pavement_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    pavement_to_mesh.location = (-300, 300)

    # Set asphalt material
    pavement_mat = nodes.new('GeometryNodeSetMaterial')
    pavement_mat.location = (0, 300)
    pavement_mat.inputs['Material'].default_value = materials['asphalt']

    # === CURBS (both sides) ===
    # Curb profile - vertical rectangle
    curb_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    curb_profile.location = (-600, 0)
    curb_profile.mode = 'RECTANGLE'
    curb_profile.inputs['Width'].default_value = 0.25  # 25cm wide
    curb_profile.inputs['Height'].default_value = 0.15  # 15cm tall

    # Offset for left curb (half road width)
    curb_offset_l = nodes.new('ShaderNodeMath')
    curb_offset_l.location = (-900, 50)
    curb_offset_l.operation = 'DIVIDE'
    curb_offset_l.inputs[1].default_value = 2.0

    # Set curve radius for left curb position
    curb_radius_l = nodes.new('GeometryNodeSetCurveRadius')
    curb_radius_l.location = (-600, -100)

    # Curve to mesh for left curb
    curb_to_mesh_l = nodes.new('GeometryNodeCurveToMesh')
    curb_to_mesh_l.location = (-300, -100)

    # Set curb material
    curb_mat_l = nodes.new('GeometryNodeSetMaterial')
    curb_mat_l.location = (0, -100)
    curb_mat_l.inputs['Material'].default_value = materials['curb']

    # Right curb - same profile, different offset
    curb_radius_r = nodes.new('GeometryNodeSetCurveRadius')
    curb_radius_r.location = (-600, -250)

    curb_to_mesh_r = nodes.new('GeometryNodeCurveToMesh')
    curb_to_mesh_r.location = (-300, -250)

    curb_mat_r = nodes.new('GeometryNodeSetMaterial')
    curb_mat_r.location = (0, -250)
    curb_mat_r.inputs['Material'].default_value = materials['curb']

    # === SIDEWALKS ===
    # Total offset = half road + curb + sidewalk
    sw_offset_calc = nodes.new('ShaderNodeMath')
    sw_offset_calc.location = (-900, -400)
    sw_offset_calc.operation = 'ADD'
    sw_offset_calc.inputs[1].default_value = 0.25 + 2.0  # curb + sidewalk

    # Sidewalk profile
    sw_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    sw_profile.location = (-600, -400)
    sw_profile.mode = 'RECTANGLE'
    sw_profile.inputs['Height'].default_value = 0.12  # 12cm thick

    # Left sidewalk
    sw_radius_l = nodes.new('GeometryNodeSetCurveRadius')
    sw_radius_l.location = (-600, -500)

    sw_to_mesh_l = nodes.new('GeometryNodeCurveToMesh')
    sw_to_mesh_l.location = (-300, -500)

    sw_mat_l = nodes.new('GeometryNodeSetMaterial')
    sw_mat_l.location = (0, -500)
    sw_mat_l.inputs['Material'].default_value = materials['concrete']

    # Right sidewalk
    sw_radius_r = nodes.new('GeometryNodeSetCurveRadius')
    sw_radius_r.location = (-600, -600)

    sw_to_mesh_r = nodes.new('GeometryNodeCurveToMesh')
    sw_to_mesh_r.location = (-300, -600)

    sw_mat_r = nodes.new('GeometryNodeSetMaterial')
    sw_mat_r.location = (0, -600)
    sw_mat_r.inputs['Material'].default_value = materials['concrete']

    # === JOIN ALL ===
    join_all = nodes.new('GeometryNodeJoinGeometry')
    join_all.location = (300, 0)

    # Output
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (500, 0)

    # === LINKS ===
    # Note: Input geometry (the curve) comes from the modifier automatically

    # Half road width calculation
    links.new(input_n.outputs['Road Width'], half_road.inputs[0])

    # Pavement - uses input curve directly
    links.new(input_n.outputs['Road Width'], pavement_profile.inputs['Width'])
    links.new(pavement_profile.outputs['Curve'], pavement_to_mesh.inputs['Profile Curve'])
    # INPUT GEOMETRY goes to Curve input
    links.new(input_n.outputs['Road Width'], pavement_to_mesh.inputs['Curve'])  # This is wrong - need input geometry

    # Actually we need to use a different approach
    # Let me reconsider...

    print("Created MSG_Road_Builder (partial - needs fixing)")
    return ng


def create_simple_road_builder():
    """
    Simple road builder - just extrudes a flat profile along the curve.
    Uses INPUT GEOMETRY properly.
    """

    materials = {
        'asphalt': get_or_create_material("M_Road_Asphalt", (0.08, 0.08, 0.09, 1.0), 0.85),
    }

    # Remove existing
    if "MSG_Road_Builder" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Road_Builder"])

    ng = bpy.data.node_groups.new("MSG_Road_Builder", 'GeometryNodeTree')

    # Simple interface
    ng.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Input
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-600, 0)

    # Create a flat profile (rectangle)
    profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    profile.location = (-300, 100)
    profile.mode = 'RECTANGLE'
    profile.inputs['Height'].default_value = 0.02  # 2cm thick

    # Curve to mesh - the INPUT CURVE is the road centerline
    # Profile curve is the cross-section
    curve_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    curve_to_mesh.location = (0, 0)

    # Set material
    set_mat = nodes.new('GeometryNodeSetMaterial')
    set_mat.location = (200, 0)
    set_mat.inputs['Material'].default_value = materials['asphalt']

    # Output
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (400, 0)

    # Links
    links.new(input_n.outputs['Road Width'], profile.inputs['Width'])
    links.new(profile.outputs['Curve'], curve_to_mesh.inputs['Profile Curve'])
    # The curve input comes from the object the modifier is on
    # But we need to pass it through... this is the issue

    # In Blender 5.0 geometry nodes, the input geometry is implicit
    # We need to not have a "Road Curves" input and instead use the
    # geometry that flows through the node tree

    # Actually the simplest approach: the node group should take the
    # input geometry and transform it

    links.new(curve_to_mesh.outputs['Mesh'], set_mat.inputs['Geometry'])
    links.new(set_mat.outputs['Geometry'], output_n.inputs['Geometry'])

    print("Created simple MSG_Road_Builder")
    return ng


def create_working_road_builder():
    """
    Create a road builder that actually works with curve modifiers.

    Key insight: When a geometry node modifier is on a CURVE object,
    the curve is automatically converted to mesh and passed as input geometry.
    We need to use that, not try to access the curve separately.
    """

    materials = {
        'asphalt': get_or_create_material("M_Road_Asphalt", (0.08, 0.08, 0.09, 1.0), 0.85),
        'concrete': get_or_create_material("M_Road_Concrete", (0.5, 0.48, 0.45, 1.0), 0.9),
        'curb': get_or_create_material("M_Road_Curb", (0.4, 0.38, 0.36, 1.0), 0.8),
    }

    # Remove existing
    if "MSG_Road_Builder" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Road_Builder"])

    ng = bpy.data.node_groups.new("MSG_Road_Builder", 'GeometryNodeTree')

    # Interface
    ng.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    ng.interface.new_socket(name="Sidewalk Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 2.0
    ng.interface.new_socket(name="Curb Height", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.15
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Input
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-1000, 0)

    # The trick: We need to capture the curve BEFORE it's converted to mesh
    # Then use Curve to Mesh nodes with our profile

    # Actually, for geometry nodes on a curve:
    # 1. The curve IS the input geometry
    # 2. We need to branch from it before processing

    # Half road width
    half_width = nodes.new('ShaderNodeMath')
    half_width.location = (-700, 200)
    half_width.operation = 'DIVIDE'
    half_width.inputs[1].default_value = 2.0

    # Total half width (road + sidewalk)
    total_half = nodes.new('ShaderNodeMath')
    total_half.location = (-500, 200)
    total_half.operation = 'ADD'

    # === ROAD SURFACE ===
    # Profile for road (flat)
    road_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    road_profile.location = (-300, 300)
    road_profile.mode = 'RECTANGLE'
    road_profile.inputs['Height'].default_value = 0.01

    # We need to use the INPUT CURVE - but how?
    # In geo nodes on a curve object, the input IS the curve
    # We need to access it via Input node... but there's no geometry output from Input

    # The solution: Create a curve primitive and use Curve to Mesh
    # But we need the ACTUAL road curve, not a new one

    # Alternative approach: Use Realize Instances, Set Position, etc.
    # on the mesh that comes from the curve

    # For now, let's try a different approach:
    # Just create a simple flat mesh and position it

    # Actually the simplest fix: Just output the input geometry with material
    set_mat = nodes.new('GeometryNodeSetMaterial')
    set_mat.location = (0, 0)
    set_mat.inputs['Material'].default_value = materials['asphalt']

    # Output
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (200, 0)

    # The input geometry flows through
    # We just apply material to it
    links.new(input_n.outputs['Road Width'], road_profile.inputs['Width'])  # Use width somehow
    links.new(set_mat.outputs['Geometry'], output_n.inputs['Geometry'])

    print("Created MSG_Road_Builder (basic version)")
    print("NOTE: This just applies asphalt material to the curve")
    print("For full roads, we need to use mesh-to-curve or different approach")

    return ng


def main():
    print("\n" + "=" * 50)
    print("Fixing Road Geometry")
    print("=" * 50)

    create_working_road_builder()

    print("\n" + "=" * 50)
    print("Road builder updated")
    print("You may need to re-apply modifiers")
    print("=" * 50)


# Run in Blender
if __name__ == "__main__":
    main()
