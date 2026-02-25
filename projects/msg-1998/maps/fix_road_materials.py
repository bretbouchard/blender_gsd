"""
MSG-1998 Road System - Fix Materials and Cleanup

1. Fixes road materials by rebuilding geometry nodes with materials
2. Removes intersection marker spheres
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


def rebuild_road_builder_with_materials():
    """Rebuild MSG_Road_Builder with materials built-in."""

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
    ng.interface.new_socket(name="Road Curves", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    ng.interface.new_socket(name="Sidewalk Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 2.0
    ng.interface.new_socket(name="Curb Height", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.15
    ng.interface.new_socket(name="Combined", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Input
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-1400, 0)

    # Calculate half road width
    half_road = nodes.new('ShaderNodeMath')
    half_road.location = (-1100, 200)
    half_road.operation = 'DIVIDE'
    half_road.inputs[1].default_value = 2.0

    # Road + sidewalk offset
    road_plus_sw = nodes.new('ShaderNodeMath')
    road_plus_sw.location = (-1100, 400)
    road_plus_sw.operation = 'ADD'

    half_total = nodes.new('ShaderNodeMath')
    half_total.location = (-900, 400)
    half_total.operation = 'DIVIDE'
    half_total.inputs[1].default_value = 2.0

    # === PAVEMENT ===
    pavement_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    pavement_profile.location = (-600, 400)
    pavement_profile.mode = 'RECTANGLE'
    pavement_profile.inputs['Height'].default_value = 0.02

    pavement_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    pavement_to_mesh.location = (-300, 400)

    pavement_set_mat = nodes.new('GeometryNodeSetMaterial')
    pavement_set_mat.location = (-100, 400)
    pavement_set_mat.inputs['Material'].default_value = materials['asphalt']

    # === LEFT CURB ===
    curb_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    curb_profile.location = (-600, 100)
    curb_profile.mode = 'RECTANGLE'
    curb_profile.inputs['Width'].default_value = 0.30
    curb_profile.inputs['Height'].default_value = 0.15

    curb_radius_l = nodes.new('GeometryNodeSetCurveRadius')
    curb_radius_l.location = (-800, 50)

    curb_to_mesh_l = nodes.new('GeometryNodeCurveToMesh')
    curb_to_mesh_l.location = (-300, 50)

    curb_set_mat_l = nodes.new('GeometryNodeSetMaterial')
    curb_set_mat_l.location = (-100, 50)
    curb_set_mat_l.inputs['Material'].default_value = materials['curb']

    # === RIGHT CURB ===
    curb_radius_r = nodes.new('GeometryNodeSetCurveRadius')
    curb_radius_r.location = (-800, -50)

    curb_to_mesh_r = nodes.new('GeometryNodeCurveToMesh')
    curb_to_mesh_r.location = (-300, -50)

    curb_set_mat_r = nodes.new('GeometryNodeSetMaterial')
    curb_set_mat_r.location = (-100, -50)
    curb_set_mat_r.inputs['Material'].default_value = materials['curb']

    # === LEFT SIDEWALK ===
    sw_profile_l = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    sw_profile_l.location = (-600, -200)
    sw_profile_l.mode = 'RECTANGLE'
    sw_profile_l.inputs['Height'].default_value = 0.10

    sw_radius_l = nodes.new('GeometryNodeSetCurveRadius')
    sw_radius_l.location = (-800, -250)

    sw_to_mesh_l = nodes.new('GeometryNodeCurveToMesh')
    sw_to_mesh_l.location = (-300, -200)

    sw_set_mat_l = nodes.new('GeometryNodeSetMaterial')
    sw_set_mat_l.location = (-100, -200)
    sw_set_mat_l.inputs['Material'].default_value = materials['concrete']

    # === RIGHT SIDEWALK ===
    sw_radius_r = nodes.new('GeometryNodeSetCurveRadius')
    sw_radius_r.location = (-800, -350)

    sw_to_mesh_r = nodes.new('GeometryNodeCurveToMesh')
    sw_to_mesh_r.location = (-300, -350)

    sw_set_mat_r = nodes.new('GeometryNodeSetMaterial')
    sw_set_mat_r.location = (-100, -350)
    sw_set_mat_r.inputs['Material'].default_value = materials['concrete']

    # === JOIN ALL ===
    join_all = nodes.new('GeometryNodeJoinGeometry')
    join_all.location = (200, 0)

    # Output
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (400, 0)

    # === LINKS ===
    # Width calculations
    links.new(input_n.outputs['Road Width'], half_road.inputs[0])
    links.new(input_n.outputs['Road Width'], road_plus_sw.inputs[0])
    links.new(input_n.outputs['Sidewalk Width'], road_plus_sw.inputs[1])
    links.new(road_plus_sw.outputs[0], half_total.inputs[0])

    # Pavement
    links.new(input_n.outputs['Road Width'], pavement_profile.inputs['Width'])
    links.new(input_n.outputs['Road Curves'], pavement_to_mesh.inputs['Curve'])
    links.new(pavement_profile.outputs['Curve'], pavement_to_mesh.inputs['Profile Curve'])
    links.new(pavement_to_mesh.outputs['Mesh'], pavement_set_mat.inputs['Geometry'])
    links.new(pavement_set_mat.outputs['Geometry'], join_all.inputs['Geometry'])

    # Left curb
    links.new(input_n.outputs['Road Curves'], curb_radius_l.inputs['Curve'])
    links.new(half_road.outputs[0], curb_radius_l.inputs['Radius'])
    links.new(curb_radius_l.outputs['Curve'], curb_to_mesh_l.inputs['Curve'])
    links.new(curb_profile.outputs['Curve'], curb_to_mesh_l.inputs['Profile Curve'])
    links.new(curb_to_mesh_l.outputs['Mesh'], curb_set_mat_l.inputs['Geometry'])
    links.new(curb_set_mat_l.outputs['Geometry'], join_all.inputs['Geometry'])

    # Right curb
    links.new(input_n.outputs['Road Curves'], curb_radius_r.inputs['Curve'])
    links.new(half_road.outputs[0], curb_radius_r.inputs['Radius'])
    links.new(curb_radius_r.outputs['Curve'], curb_to_mesh_r.inputs['Curve'])
    links.new(curb_profile.outputs['Curve'], curb_to_mesh_r.inputs['Profile Curve'])
    links.new(curb_to_mesh_r.outputs['Mesh'], curb_set_mat_r.inputs['Geometry'])
    links.new(curb_set_mat_r.outputs['Geometry'], join_all.inputs['Geometry'])

    # Left sidewalk
    links.new(input_n.outputs['Road Curves'], sw_radius_l.inputs['Curve'])
    links.new(half_total.outputs[0], sw_radius_l.inputs['Radius'])
    links.new(input_n.outputs['Sidewalk Width'], sw_profile_l.inputs['Width'])
    links.new(sw_radius_l.outputs['Curve'], sw_to_mesh_l.inputs['Curve'])
    links.new(sw_profile_l.outputs['Curve'], sw_to_mesh_l.inputs['Profile Curve'])
    links.new(sw_to_mesh_l.outputs['Mesh'], sw_set_mat_l.inputs['Geometry'])
    links.new(sw_set_mat_l.outputs['Geometry'], join_all.inputs['Geometry'])

    # Right sidewalk
    links.new(input_n.outputs['Road Curves'], sw_radius_r.inputs['Curve'])
    links.new(half_total.outputs[0], sw_radius_r.inputs['Radius'])
    links.new(sw_radius_r.outputs['Curve'], sw_to_mesh_r.inputs['Curve'])
    links.new(sw_profile_l.outputs['Curve'], sw_to_mesh_r.inputs['Profile Curve'])
    links.new(sw_to_mesh_r.outputs['Mesh'], sw_set_mat_r.inputs['Geometry'])
    links.new(sw_set_mat_r.outputs['Geometry'], join_all.inputs['Geometry'])

    # Output
    links.new(join_all.outputs['Geometry'], output_n.inputs['Combined'])

    print("Rebuilt MSG_Road_Builder with materials")
    return ng


def rebuild_lane_markings_with_materials():
    """Rebuild MSG_Lane_Markings with materials built-in."""

    materials = {
        'marking': get_or_create_material("M_Road_LaneMarking", (0.95, 0.95, 0.95, 1.0), 0.5),
    }

    # Remove existing
    if "MSG_Lane_Markings" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Lane_Markings"])

    ng = bpy.data.node_groups.new("MSG_Lane_Markings", 'GeometryNodeTree')

    # Interface
    ng.interface.new_socket(name="Road Curves", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    ng.interface.new_socket(name="Center Line Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.15
    ng.interface.new_socket(name="Edge Line Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.10
    ng.interface.new_socket(name="Z Offset", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.02
    ng.interface.new_socket(name="Markings", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Input
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-800, 0)

    # Center line profile
    center_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    center_profile.location = (-400, 200)
    center_profile.mode = 'RECTANGLE'
    center_profile.inputs['Height'].default_value = 0.02

    center_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    center_to_mesh.location = (-100, 200)

    combine_z = nodes.new('ShaderNodeCombineXYZ')
    combine_z.location = (-400, 0)

    center_transform = nodes.new('GeometryNodeTransform')
    center_transform.location = (200, 200)

    center_set_mat = nodes.new('GeometryNodeSetMaterial')
    center_set_mat.location = (400, 200)
    center_set_mat.inputs['Material'].default_value = materials['marking']

    # Edge line profiles
    edge_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    edge_profile.location = (-600, -100)
    edge_profile.mode = 'RECTANGLE'
    edge_profile.inputs['Height'].default_value = 0.02

    half_width = nodes.new('ShaderNodeMath')
    half_width.location = (-600, -250)
    half_width.operation = 'DIVIDE'
    half_width.inputs[1].default_value = 2.0

    edge_offset = nodes.new('ShaderNodeMath')
    edge_offset.location = (-400, -250)
    edge_offset.operation = 'SUBTRACT'
    edge_offset.inputs[1].default_value = 0.5

    edge_radius_l = nodes.new('GeometryNodeSetCurveRadius')
    edge_radius_l.location = (-200, -100)

    edge_radius_r = nodes.new('GeometryNodeSetCurveRadius')
    edge_radius_r.location = (-200, -200)

    edge_to_mesh_l = nodes.new('GeometryNodeCurveToMesh')
    edge_to_mesh_l.location = (100, -100)

    edge_to_mesh_r = nodes.new('GeometryNodeCurveToMesh')
    edge_to_mesh_r.location = (100, -200)

    edge_set_mat_l = nodes.new('GeometryNodeSetMaterial')
    edge_set_mat_l.location = (300, -100)
    edge_set_mat_l.inputs['Material'].default_value = materials['marking']

    edge_set_mat_r = nodes.new('GeometryNodeSetMaterial')
    edge_set_mat_r.location = (300, -200)
    edge_set_mat_r.inputs['Material'].default_value = materials['marking']

    # Join
    join_all = nodes.new('GeometryNodeJoinGeometry')
    join_all.location = (500, 0)

    # Output
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (700, 0)

    # Links
    links.new(input_n.outputs['Center Line Width'], center_profile.inputs['Width'])
    links.new(input_n.outputs['Road Curves'], center_to_mesh.inputs['Curve'])
    links.new(center_profile.outputs['Curve'], center_to_mesh.inputs['Profile Curve'])
    links.new(input_n.outputs['Z Offset'], combine_z.inputs['Z'])
    links.new(combine_z.outputs['Vector'], center_transform.inputs['Translation'])
    links.new(center_to_mesh.outputs['Mesh'], center_transform.inputs['Geometry'])
    links.new(center_transform.outputs['Geometry'], center_set_mat.inputs['Geometry'])
    links.new(center_set_mat.outputs['Geometry'], join_all.inputs['Geometry'])

    links.new(input_n.outputs['Edge Line Width'], edge_profile.inputs['Width'])
    links.new(input_n.outputs['Road Width'], half_width.inputs[0])
    links.new(half_width.outputs[0], edge_offset.inputs[0])
    links.new(input_n.outputs['Road Curves'], edge_radius_l.inputs['Curve'])
    links.new(edge_offset.outputs[0], edge_radius_l.inputs['Radius'])
    links.new(input_n.outputs['Road Curves'], edge_radius_r.inputs['Curve'])
    links.new(edge_offset.outputs[0], edge_radius_r.inputs['Radius'])

    links.new(edge_radius_l.outputs['Curve'], edge_to_mesh_l.inputs['Curve'])
    links.new(edge_profile.outputs['Curve'], edge_to_mesh_l.inputs['Profile Curve'])
    links.new(edge_radius_r.outputs['Curve'], edge_to_mesh_r.inputs['Curve'])
    links.new(edge_profile.outputs['Curve'], edge_to_mesh_r.inputs['Profile Curve'])

    links.new(edge_to_mesh_l.outputs['Mesh'], edge_set_mat_l.inputs['Geometry'])
    links.new(edge_to_mesh_r.outputs['Mesh'], edge_set_mat_r.inputs['Geometry'])
    links.new(edge_set_mat_l.outputs['Geometry'], join_all.inputs['Geometry'])
    links.new(edge_set_mat_r.outputs['Geometry'], join_all.inputs['Geometry'])

    links.new(join_all.outputs['Geometry'], output_n.inputs['Markings'])

    print("Rebuilt MSG_Lane_Markings with materials")
    return ng


def remove_intersection_markers():
    """Remove the white sphere intersection markers."""
    if "Intersections" not in bpy.data.collections:
        print("Intersections collection not found")
        return 0

    coll = bpy.data.collections["Intersections"]
    count = 0

    # Remove all objects in the collection
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
        count += 1

    # Remove the collection too
    bpy.data.collections.remove(coll)

    print(f"Removed {count} intersection markers")
    return count


def fix_road_system():
    """Fix materials and cleanup."""

    print("\n" + "=" * 50)
    print("Fixing Road System")
    print("=" * 50)

    # Rebuild geometry nodes with materials
    rebuild_road_builder_with_materials()
    rebuild_lane_markings_with_materials()

    # Remove intersection markers
    remove_intersection_markers()

    print("\n" + "=" * 50)
    print("Road System Fixed!")
    print("Roads should now render with proper materials")
    print("=" * 50)


# Run in Blender
if __name__ == "__main__":
    fix_road_system()
