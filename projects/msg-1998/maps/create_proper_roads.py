"""
MSG-1998 Road System - Proper Road Geometry

Creates a road builder that:
1. Uses the curve the modifier is on as the road centerline
2. Creates flat road surface (no bump)
3. Applies asphalt material

Key: Geometry nodes on curves receive the curve as input geometry.
We use Curve to Mesh with a flat profile.
"""

import bpy


def get_or_create_material(name, color, roughness=0.8):
    """Get or create material."""
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

    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_road_builder_v2():
    """
    Create road builder that works with curves.

    The curve object has the modifier. The curve IS the input.
    We need to use 'Object Info' to get the curve, then convert to mesh.
    """

    asphalt = get_or_create_material("M_Road_Asphalt", (0.08, 0.08, 0.09, 1.0), 0.85)
    concrete = get_or_create_material("M_Road_Concrete", (0.5, 0.48, 0.45, 1.0), 0.9)
    curb = get_or_create_material("M_Road_Curb", (0.4, 0.38, 0.36, 1.0), 0.8)

    # Remove existing
    if "MSG_Road_Builder" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Road_Builder"])

    ng = bpy.data.node_groups.new("MSG_Road_Builder", 'GeometryNodeTree')

    # Interface - only parameters, no geometry input
    ng.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    ng.interface.new_socket(name="Sidewalk Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 2.0
    ng.interface.new_socket(name="Curb Height", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.15
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Input node (for parameters)
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-800, 0)

    # === The key: Use a Curve to Mesh with the INPUT CURVE ===
    # In Blender geo nodes, when applied to a curve, the curve becomes
    # the input geometry. We access it via the Input node... but it doesn't
    # output geometry directly.

    # Actually, the way geo nodes work:
    # - The modifier takes the object's geometry as input
    # - For a curve, it's curve data
    # - We need to connect that to Curve to Mesh

    # But there's no explicit "input geometry" socket!
    # The geometry flows implicitly through the node tree.

    # Let me try a different approach: Use Mesh to Curve in reverse

    # Actually, I think the issue is simpler:
    # We just need to make sure the input geometry (the curve)
    # goes into Curve to Mesh's Curve input

    # In Blender 5.0, we need to use the "Input" node differently

    # === SIMPLEST APPROACH ===
    # Just use the curve with a flat profile

    # Half road width
    half_width = nodes.new('ShaderNodeMath')
    half_width.location = (-500, 200)
    half_width.operation = 'DIVIDE'
    half_width.inputs[1].default_value = 2.0

    # Road profile - FLAT
    road_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    road_profile.location = (-300, 200)
    road_profile.mode = 'RECTANGLE'
    road_profile.inputs['Height'].default_value = 0.01  # Very flat

    # Sidewalk profile
    sw_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    sw_profile.location = (-300, 0)
    sw_profile.mode = 'RECTANGLE'
    sw_profile.inputs['Height'].default_value = 0.10

    # The issue: We need to connect the INPUT CURVE to Curve to Mesh
    # But there's no geometry output from NodeGroupInput for the curve

    # Solution: Create the road as a MESH primitive, not from curve

    # Actually, let's check if there's a way to get the curve...

    # In Blender 5.0 geometry nodes, curves ARE passed as input geometry
    # We just need to accept it as a geometry input and use it

    # Let me add a geometry input socket and see if it auto-connects
    # Actually no - we already tried that and it didn't work

    # The real solution: The node tree starts with the input geometry
    # We need to use nodes that work with that geometry

    # For a curve input:
    # 1. It comes in as Curve geometry
    # 2. We can use Set Curve Radius, Curve to Mesh, etc.

    # Let me try: Just output the curve with material
    # The curve itself should render

    set_mat = nodes.new('GeometryNodeSetMaterial')
    set_mat.location = (0, 0)
    set_mat.inputs['Material'].default_value = asphalt

    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (200, 0)

    # Connect: input geometry -> set material -> output
    # But how do we get input geometry?
    # There should be an implicit connection...

    # AH! The issue is that in Blender 5.0, we need to explicitly
    # define a geometry input socket that auto-connects to the modifier's object

    # Let me check the interface again...

    print("Created MSG_Road_Builder v2")
    return ng


def create_road_builder_working():
    """
    Create a road builder that ACTUALLY WORKS.

    After research: In Blender geometry nodes, when you add a modifier
    to a curve, the curve geometry flows into the node tree.
    You access it by NOT having a separate geometry input.

    The node tree should start with nodes that accept the implicit input.
    """

    asphalt = get_or_create_material("M_Road_Asphalt", (0.08, 0.08, 0.09, 1.0), 0.85)
    concrete = get_or_create_material("M_Road_Concrete", (0.5, 0.48, 0.45, 1.0), 0.9)
    curb_mat = get_or_create_material("M_Road_Curb", (0.4, 0.38, 0.36, 1.0), 0.8)

    # Remove existing
    if "MSG_Road_Builder" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Road_Builder"])

    ng = bpy.data.node_groups.new("MSG_Road_Builder", 'GeometryNodeTree')

    # Interface - parameters only
    ng.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    ng.interface.new_socket(name="Sidewalk Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 2.0
    ng.interface.new_socket(name="Curb Height", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.15
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Input
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-600, 0)

    # Half width calculation
    half = nodes.new('ShaderNodeMath')
    half.location = (-400, 200)
    half.operation = 'DIVIDE'
    half.inputs[1].default_value = 2.0

    # Road + sidewalk
    total = nodes.new('ShaderNodeMath')
    total.location = (-400, 400)
    total.operation = 'ADD'

    half_total = nodes.new('ShaderNodeMath')
    half_total.location = (-200, 400)
    half_total.operation = 'DIVIDE'
    half_total.inputs[1].default_value = 2.0

    # Profile for road - FLAT
    road_prof = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    road_prof.location = (0, 300)
    road_prof.mode = 'RECTANGLE'
    road_prof.inputs['Height'].default_value = 0.01

    # Profile for curb - VERTICAL
    curb_prof = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    curb_prof.location = (0, 100)
    curb_prof.mode = 'RECTANGLE'
    curb_prof.inputs['Width'].default_value = 0.3
    curb_prof.inputs['Height'].default_value = 0.15

    # Profile for sidewalk - FLAT
    sw_prof = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    sw_prof.location = (0, -100)
    sw_prof.mode = 'RECTANGLE'
    sw_prof.inputs['Height'].default_value = 0.12

    # Curve to mesh for road
    # HERE IS THE KEY: We need to get the curve into this node
    # In Blender 5.0, the input curve should be available somehow

    c2m_road = nodes.new('GeometryNodeCurveToMesh')
    c2m_road.location = (200, 300)

    mat_road = nodes.new('GeometryNodeSetMaterial')
    mat_road.location = (400, 300)
    mat_road.inputs['Material'].default_value = asphalt

    # Curb left
    c2m_curb_l = nodes.new('GeometryNodeCurveToMesh')
    c2m_curb_l.location = (200, 100)

    mat_curb_l = nodes.new('GeometryNodeSetMaterial')
    mat_curb_l.location = (400, 100)
    mat_curb_l.inputs['Material'].default_value = curb_mat

    # Curb right
    c2m_curb_r = nodes.new('GeometryNodeCurveToMesh')
    c2m_curb_r.location = (200, -50)

    mat_curb_r = nodes.new('GeometryNodeSetMaterial')
    mat_curb_r.location = (400, -50)
    mat_curb_r.inputs['Material'].default_value = curb_mat

    # Sidewalk left
    c2m_sw_l = nodes.new('GeometryNodeCurveToMesh')
    c2m_sw_l.location = (200, -200)

    mat_sw_l = nodes.new('GeometryNodeSetMaterial')
    mat_sw_l.location = (400, -200)
    mat_sw_l.inputs['Material'].default_value = concrete

    # Sidewalk right
    c2m_sw_r = nodes.new('GeometryNodeCurveToMesh')
    c2m_sw_r.location = (200, -350)

    mat_sw_r = nodes.new('GeometryNodeSetMaterial')
    mat_sw_r.location = (400, -350)
    mat_sw_r.inputs['Material'].default_value = concrete

    # Join
    join = nodes.new('GeometryNodeJoinGeometry')
    join.location = (600, 0)

    # Output
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (800, 0)

    # LINKS
    links.new(input_n.outputs['Road Width'], half.inputs[0])
    links.new(input_n.outputs['Road Width'], total.inputs[0])
    links.new(input_n.outputs['Sidewalk Width'], total.inputs[1])
    links.new(total.outputs[0], half_total.inputs[0])

    links.new(input_n.outputs['Road Width'], road_prof.inputs['Width'])
    links.new(input_n.outputs['Sidewalk Width'], sw_prof.inputs['Width'])

    # Profiles to curve-to-mesh
    links.new(road_prof.outputs['Curve'], c2m_road.inputs['Profile Curve'])
    links.new(curb_prof.outputs['Curve'], c2m_curb_l.inputs['Profile Curve'])
    links.new(curb_prof.outputs['Curve'], c2m_curb_r.inputs['Profile Curve'])
    links.new(sw_prof.outputs['Curve'], c2m_sw_l.inputs['Profile Curve'])
    links.new(sw_prof.outputs['Curve'], c2m_sw_r.inputs['Profile Curve'])

    # Materials
    links.new(c2m_road.outputs['Mesh'], mat_road.inputs['Geometry'])
    links.new(c2m_curb_l.outputs['Mesh'], mat_curb_l.inputs['Geometry'])
    links.new(c2m_curb_r.outputs['Mesh'], mat_curb_r.inputs['Geometry'])
    links.new(c2m_sw_l.outputs['Mesh'], mat_sw_l.inputs['Geometry'])
    links.new(c2m_sw_r.outputs['Mesh'], mat_sw_r.inputs['Geometry'])

    # Join
    links.new(mat_road.outputs['Geometry'], join.inputs['Geometry'])
    links.new(mat_curb_l.outputs['Geometry'], join.inputs['Geometry'])
    links.new(mat_curb_r.outputs['Geometry'], join.inputs['Geometry'])
    links.new(mat_sw_l.outputs['Geometry'], join.inputs['Geometry'])
    links.new(mat_sw_r.outputs['Geometry'], join.inputs['Geometry'])

    links.new(join.outputs['Geometry'], output_n.inputs['Geometry'])

    # THE MISSING PIECE: We never connected the input curve!
    # We need to connect it to all the Curve to Mesh nodes

    # But where does the input curve come from?
    # In Blender 5.0, it should come from... somewhere

    # Let me check if we need a specific input socket

    print("\nCreated MSG_Road_Builder")
    print("NOTE: Missing curve input connection!")
    print("The curve needs to be connected to all Curve to Mesh nodes")

    return ng


def main():
    print("\n" + "=" * 50)
    print("Creating Road Builder")
    print("=" * 50)

    create_road_builder_working()

    print("\n" + "=" * 50)
    print("IMPORTANT: This won't work yet!")
    print("Geometry nodes on curves need special handling")
    print("=" * 50)


# Run in Blender
if __name__ == "__main__":
    main()
