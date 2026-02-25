"""
MSG-1998 Road System - Geometry Nodes Setup

Creates a practical Geometry Nodes setup for road generation.
Run this in Blender to create the node groups.

This version uses a simpler, more direct approach.
"""

import bpy


def create_road_builder_node_group():
    """
    Create the main road builder node group.

    Takes road curves and generates:
    - Pavement (road surface)
    - Curbs (raised edges)
    - Sidewalks (pedestrian areas)
    """

    # Remove existing if present
    if "MSG_Road_Builder" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Road_Builder"])

    # Create new node group
    ng = bpy.data.node_groups.new("MSG_Road_Builder", 'GeometryNodeTree')

    # Create interface sockets
    # Inputs
    ng.interface.new_socket(name="Road Curves", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    ng.interface.new_socket(name="Sidewalk Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 2.0
    ng.interface.new_socket(name="Curb Height", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.15
    ng.interface.new_socket(name="Resolution", in_out='INPUT', socket_type='NodeSocketInt').default_value = 24

    # Outputs
    ng.interface.new_socket(name="Pavement", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Curbs", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Sidewalks", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Combined", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # === INPUT NODE ===
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-1200, 0)

    # === HALF WIDTH CALCULATION ===
    divide = nodes.new('ShaderNodeMath')
    divide.location = (-900, 200)
    divide.operation = 'DIVIDE'
    divide.inputs[1].default_value = 2.0

    # === ROAD WIDTH (total) ===
    # Add sidewalk widths to road width
    total_width = nodes.new('ShaderNodeMath')
    total_width.location = (-900, 400)
    total_width.operation = 'ADD'

    total_width2 = nodes.new('ShaderNodeMath')
    total_width2.location = (-700, 400)
    total_width2.operation = 'ADD'

    # === PAVEMENT SECTION ===
    # Create profile curve for road surface
    pavement_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    pavement_profile.location = (-500, 400)
    pavement_profile.mode = 'RECTANGLE'
    pavement_profile.inputs['Height'].default_value = 0.02  # Slight thickness

    # Curve to mesh for pavement
    pavement_curve_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    pavement_curve_to_mesh.location = (-200, 400)

    # Set Z position (on ground)
    pavement_transform = nodes.new('GeometryNodeTransform')
    pavement_transform.location = (100, 400)
    pavement_transform.inputs['Translation'].default_value = (0, 0, 0.01)

    # === CURB SECTION ===
    # Create curb profile
    curb_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    curb_profile.location = (-500, 100)
    curb_profile.mode = 'RECTANGLE'
    curb_profile.inputs['Width'].default_value = 0.30  # 30cm curb width
    curb_profile.inputs['Height'].default_value = 0.15  # 15cm curb height

    # Offset curve for left curb
    curb_radius_left = nodes.new('GeometryNodeSetCurveRadius')
    curb_radius_left.location = (-700, 50)
    curb_radius_left.inputs['Radius'].default_value = 0.001  # Thin for positioning

    # Curve to mesh for left curb
    curb_to_mesh_left = nodes.new('GeometryNodeCurveToMesh')
    curb_to_mesh_left.location = (-200, 50)

    # Transform left curb to side
    curb_transform_left = nodes.new('GeometryNodeTransform')
    curb_transform_left.location = (100, 50)

    # === SIDEWALK SECTION ===
    # Create sidewalk profile
    sidewalk_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    sidewalk_profile.location = (-500, -200)
    sidewalk_profile.mode = 'RECTANGLE'
    sidewalk_profile.inputs['Height'].default_value = 0.10  # 10cm thickness

    # Offset for sidewalk position
    sidewalk_radius = nodes.new('GeometryNodeSetCurveRadius')
    sidewalk_radius.location = (-700, -250)

    # Curve to mesh for sidewalk
    sidewalk_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    sidewalk_to_mesh.location = (-200, -200)

    # Transform sidewalk to side and up
    sidewalk_transform = nodes.new('GeometryNodeTransform')
    sidewalk_transform.location = (100, -200)

    # === JOIN GEOMETRY ===
    join_pavement = nodes.new('GeometryNodeJoinGeometry')
    join_pavement.location = (400, 400)

    join_curbs = nodes.new('GeometryNodeJoinGeometry')
    join_curbs.location = (400, 100)

    join_sidewalks = nodes.new('GeometryNodeJoinGeometry')
    join_sidewalks.location = (400, -200)

    join_all = nodes.new('GeometryNodeJoinGeometry')
    join_all.location = (600, 0)

    # === OUTPUT NODE ===
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (900, 0)

    # === LINKS ===
    # Input connections
    links.new(input_n.outputs['Road Curves'], pavement_curve_to_mesh.inputs['Curve'])
    links.new(input_n.outputs['Road Curves'], curb_radius_left.inputs['Curve'])
    links.new(input_n.outputs['Road Curves'], sidewalk_radius.inputs['Curve'])
    links.new(input_n.outputs['Road Width'], divide.inputs[0])

    # Width calculations
    links.new(input_n.outputs['Road Width'], total_width.inputs[0])
    links.new(input_n.outputs['Sidewalk Width'], total_width.inputs[1])
    links.new(total_width.outputs[0], total_width2.inputs[0])
    links.new(input_n.outputs['Sidewalk Width'], total_width2.inputs[1])

    # Pavement
    links.new(divide.outputs[0], pavement_profile.inputs['Width'])
    links.new(pavement_profile.outputs['Curve'], pavement_curve_to_mesh.inputs['Profile Curve'])
    links.new(pavement_curve_to_mesh.outputs['Mesh'], pavement_transform.inputs['Geometry'])
    links.new(pavement_transform.outputs['Geometry'], join_pavement.inputs['Geometry'])

    # Curbs
    links.new(curb_profile.outputs['Curve'], curb_to_mesh_left.inputs['Profile Curve'])
    links.new(curb_radius_left.outputs['Curve'], curb_to_mesh_left.inputs['Curve'])
    links.new(curb_to_mesh_left.outputs['Mesh'], curb_transform_left.inputs['Geometry'])
    links.new(curb_transform_left.outputs['Geometry'], join_curbs.inputs['Geometry'])

    # Sidewalks
    links.new(input_n.outputs['Sidewalk Width'], sidewalk_profile.inputs['Width'])
    links.new(sidewalk_profile.outputs['Curve'], sidewalk_to_mesh.inputs['Profile Curve'])
    links.new(sidewalk_radius.outputs['Curve'], sidewalk_to_mesh.inputs['Curve'])
    links.new(sidewalk_to_mesh.outputs['Mesh'], sidewalk_transform.inputs['Geometry'])
    links.new(sidewalk_transform.outputs['Geometry'], join_sidewalks.inputs['Geometry'])

    # Join all for combined output
    links.new(join_pavement.outputs['Geometry'], join_all.inputs['Geometry'])
    links.new(join_curbs.outputs['Geometry'], join_all.inputs['Geometry'])
    links.new(join_sidewalks.outputs['Geometry'], join_all.inputs['Geometry'])

    # Outputs
    links.new(join_pavement.outputs['Geometry'], output_n.inputs['Pavement'])
    links.new(join_curbs.outputs['Geometry'], output_n.inputs['Curbs'])
    links.new(join_sidewalks.outputs['Geometry'], output_n.inputs['Sidewalks'])
    links.new(join_all.outputs['Geometry'], output_n.inputs['Combined'])

    print(f"Created node group: {ng.name}")
    return ng


def create_lane_marking_node_group():
    """
    Create node group for lane markings.

    Generates dashed and solid lines along road centerline.
    """

    if "MSG_Lane_Markings" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Lane_Markings"])

    ng = bpy.data.node_groups.new("MSG_Lane_Markings", 'GeometryNodeTree')

    # Interface
    ng.interface.new_socket(name="Road Curves", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    ng.interface.new_socket(name="Center Line Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.10
    ng.interface.new_socket(name="Edge Line Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.15
    ng.interface.new_socket(name="Z Offset", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.02

    ng.interface.new_socket(name="Markings", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Input
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-800, 0)

    # Half width for positioning
    half_width = nodes.new('ShaderNodeMath')
    half_width.location = (-500, 200)
    half_width.operation = 'DIVIDE'
    half_width.inputs[1].default_value = 2.0

    # === CENTER LINE ===
    # Profile for center line
    center_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    center_profile.location = (-300, 300)
    center_profile.mode = 'RECTANGLE'
    center_profile.inputs['Height'].default_value = 0.01

    center_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    center_to_mesh.location = (0, 300)

    center_transform = nodes.new('GeometryNodeTransform')
    center_transform.location = (200, 300)

    # Combine vector for Z offset
    combine_z = nodes.new('ShaderNodeCombineXYZ')
    combine_z.location = (0, 400)

    # === EDGE LINES (left and right) ===
    edge_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    edge_profile.location = (-300, 0)
    edge_profile.mode = 'RECTANGLE'
    edge_profile.inputs['Height'].default_value = 0.01

    # Left edge
    edge_left_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    edge_left_to_mesh.location = (0, 100)

    edge_left_transform = nodes.new('GeometryNodeTransform')
    edge_left_transform.location = (200, 100)

    # Right edge
    edge_right_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    edge_right_to_mesh.location = (0, -100)

    edge_right_transform = nodes.new('GeometryNodeTransform')
    edge_right_transform.location = (200, -100)

    # Combine
    join_all = nodes.new('GeometryNodeJoinGeometry')
    join_all.location = (500, 0)

    # Output
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (800, 0)

    # Links
    links.new(input_n.outputs['Road Width'], half_width.inputs[0])
    links.new(input_n.outputs['Center Line Width'], center_profile.inputs['Width'])
    links.new(input_n.outputs['Road Curves'], center_to_mesh.inputs['Curve'])
    links.new(center_profile.outputs['Curve'], center_to_mesh.inputs['Profile Curve'])
    links.new(center_to_mesh.outputs['Mesh'], center_transform.inputs['Geometry'])
    links.new(input_n.outputs['Z Offset'], combine_z.inputs['Z'])
    links.new(combine_z.outputs['Vector'], center_transform.inputs['Translation'])

    # Edge lines
    links.new(input_n.outputs['Edge Line Width'], edge_profile.inputs['Width'])
    links.new(edge_profile.outputs['Curve'], edge_left_to_mesh.inputs['Profile Curve'])
    links.new(edge_profile.outputs['Curve'], edge_right_to_mesh.inputs['Profile Curve'])
    links.new(input_n.outputs['Road Curves'], edge_left_to_mesh.inputs['Curve'])
    links.new(input_n.outputs['Road Curves'], edge_right_to_mesh.inputs['Curve'])

    # Join and output
    links.new(center_transform.outputs['Geometry'], join_all.inputs['Geometry'])
    links.new(edge_left_transform.outputs['Geometry'], join_all.inputs['Geometry'])
    links.new(edge_right_transform.outputs['Geometry'], join_all.inputs['Geometry'])
    links.new(join_all.outputs['Geometry'], output_n.inputs['Markings'])

    print(f"Created node group: {ng.name}")
    return ng


def create_intersection_node_group():
    """
    Create node group for intersection geometry.

    Uses curve-to-points and proximity to detect intersections.
    """

    if "MSG_Intersections" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Intersections"])

    ng = bpy.data.node_groups.new("MSG_Intersections", 'GeometryNodeTree')

    # Interface
    ng.interface.new_socket(name="Road Curves", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Detection Radius", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 3.0
    ng.interface.new_socket(name="Intersection Radius", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 8.0

    ng.interface.new_socket(name="Intersection Surfaces", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Crosswalk Points", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Input
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-600, 0)

    # Convert curves to points using LENGTH mode
    # Blender 5.0 changed modes: use LENGTH with large value to get sparse points
    curve_to_points = nodes.new('GeometryNodeCurveToPoints')
    curve_to_points.location = (-300, 0)
    curve_to_points.mode = 'LENGTH'
    # Set a large length value to get endpoint-like behavior
    curve_to_points.inputs['Length'].default_value = 1000.0  # Large value = fewer points

    # Merge nearby points to find intersections
    merge = nodes.new('GeometryNodeMergeByDistance')
    merge.location = (0, 0)

    # Create intersection circles at merged points
    # Use instance on points
    circle = nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.location = (-100, 200)

    instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')
    instance_on_points.location = (200, 0)

    # Realize instances
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (400, 0)

    # Output
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (700, 0)

    # Links
    links.new(input_n.outputs['Road Curves'], curve_to_points.inputs['Curve'])
    links.new(curve_to_points.outputs['Points'], merge.inputs['Geometry'])
    links.new(input_n.outputs['Detection Radius'], merge.inputs['Distance'])
    links.new(merge.outputs['Geometry'], instance_on_points.inputs['Points'])
    links.new(circle.outputs['Curve'], instance_on_points.inputs['Instance'])
    links.new(input_n.outputs['Intersection Radius'], circle.inputs['Radius'])
    links.new(instance_on_points.outputs['Instances'], realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], output_n.inputs['Intersection Surfaces'])
    links.new(merge.outputs['Geometry'], output_n.inputs['Crosswalk Points'])

    print(f"Created node group: {ng.name}")
    return ng


def create_furniture_node_group():
    """
    Create node group for street furniture distribution.

    Distributes points for manholes, hydrants, etc.
    """

    if "MSG_Street_Furniture" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Street_Furniture"])

    ng = bpy.data.node_groups.new("MSG_Street_Furniture", 'GeometryNodeTree')

    # Interface
    ng.interface.new_socket(name="Road Curves", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Manhole Spacing", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 40.0
    ng.interface.new_socket(name="Hydrant Spacing", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 120.0

    ng.interface.new_socket(name="Manhole Points", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Hydrant Points", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # Input
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-400, 0)

    # Resample for manholes (using CurveToPoints in Blender 5.0)
    resample_manhole = nodes.new('GeometryNodeCurveToPoints')
    resample_manhole.location = (0, 100)
    resample_manhole.mode = 'LENGTH'

    # Resample for hydrants
    resample_hydrant = nodes.new('GeometryNodeCurveToPoints')
    resample_hydrant.location = (0, -100)
    resample_hydrant.mode = 'LENGTH'

    # Output
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (300, 0)

    # Links
    links.new(input_n.outputs['Road Curves'], resample_manhole.inputs['Curve'])
    links.new(input_n.outputs['Manhole Spacing'], resample_manhole.inputs['Length'])
    links.new(resample_manhole.outputs['Points'], output_n.inputs['Manhole Points'])

    links.new(input_n.outputs['Road Curves'], resample_hydrant.inputs['Curve'])
    links.new(input_n.outputs['Hydrant Spacing'], resample_hydrant.inputs['Length'])
    links.new(resample_hydrant.outputs['Points'], output_n.inputs['Hydrant Points'])

    print(f"Created node group: {ng.name}")
    return ng


def create_master_road_node_group():
    """
    Create the master node group that chains all sub-groups together.

    This is the main entry point for road generation.
    """

    if "MSG_Road_System_Master" in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups["MSG_Road_System_Master"])

    ng = bpy.data.node_groups.new("MSG_Road_System_Master", 'GeometryNodeTree')

    # Interface - All controllable parameters
    # Inputs
    ng.interface.new_socket(name="Road Curves", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    ng.interface.new_socket(name="Sidewalk Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 2.0
    ng.interface.new_socket(name="Curb Height", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.15
    ng.interface.new_socket(name="Enable Markings", in_out='INPUT', socket_type='NodeSocketBool').default_value = True
    ng.interface.new_socket(name="Enable Intersections", in_out='INPUT', socket_type='NodeSocketBool').default_value = True
    ng.interface.new_socket(name="Enable Furniture", in_out='INPUT', socket_type='NodeSocketBool').default_value = True

    # Outputs
    ng.interface.new_socket(name="Roads", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Markings", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Intersections", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Furniture Points", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    # === INPUT ===
    input_n = nodes.new('NodeGroupInput')
    input_n.location = (-800, 0)

    # === ROAD BUILDER SUBGROUP ===
    road_builder = nodes.new('GeometryNodeGroup')
    road_builder.location = (-400, 300)
    road_builder.node_tree = bpy.data.node_groups["MSG_Road_Builder"]

    # === LANE MARKINGS SUBGROUP ===
    lane_markings = nodes.new('GeometryNodeGroup')
    lane_markings.location = (-400, 0)
    lane_markings.node_tree = bpy.data.node_groups["MSG_Lane_Markings"]

    # === INTERSECTIONS SUBGROUP ===
    intersections = nodes.new('GeometryNodeGroup')
    intersections.location = (-400, -200)
    intersections.node_tree = bpy.data.node_groups["MSG_Intersections"]

    # === FURNITURE SUBGROUP ===
    furniture = nodes.new('GeometryNodeGroup')
    furniture.location = (-400, -400)
    furniture.node_tree = bpy.data.node_groups["MSG_Street_Furniture"]

    # === JOIN FOR COMBINED OUTPUT ===
    join_roads = nodes.new('GeometryNodeJoinGeometry')
    join_roads.location = (0, 300)

    join_markings = nodes.new('GeometryNodeJoinGeometry')
    join_markings.location = (0, 0)

    join_intersections = nodes.new('GeometryNodeJoinGeometry')
    join_intersections.location = (0, -200)

    join_furniture = nodes.new('GeometryNodeJoinGeometry')
    join_furniture.location = (0, -400)

    # === OUTPUT ===
    output_n = nodes.new('NodeGroupOutput')
    output_n.location = (400, 0)

    # === LINKS ===
    # Road Builder connections
    links.new(input_n.outputs['Road Curves'], road_builder.inputs['Road Curves'])
    links.new(input_n.outputs['Road Width'], road_builder.inputs['Road Width'])
    links.new(input_n.outputs['Sidewalk Width'], road_builder.inputs['Sidewalk Width'])
    links.new(input_n.outputs['Curb Height'], road_builder.inputs['Curb Height'])
    links.new(road_builder.outputs['Combined'], join_roads.inputs['Geometry'])

    # Lane Markings connections
    links.new(input_n.outputs['Road Curves'], lane_markings.inputs['Road Curves'])
    links.new(input_n.outputs['Road Width'], lane_markings.inputs['Road Width'])
    links.new(lane_markings.outputs['Markings'], join_markings.inputs['Geometry'])

    # Intersections connections
    links.new(input_n.outputs['Road Curves'], intersections.inputs['Road Curves'])
    links.new(intersections.outputs['Intersection Surfaces'], join_intersections.inputs['Geometry'])

    # Furniture connections
    links.new(input_n.outputs['Road Curves'], furniture.inputs['Road Curves'])
    links.new(furniture.outputs['Manhole Points'], join_furniture.inputs['Geometry'])
    links.new(furniture.outputs['Hydrant Points'], join_furniture.inputs['Geometry'])

    # Final outputs
    links.new(join_roads.outputs['Geometry'], output_n.inputs['Roads'])
    links.new(join_markings.outputs['Geometry'], output_n.inputs['Markings'])
    links.new(join_intersections.outputs['Geometry'], output_n.inputs['Intersections'])
    links.new(join_furniture.outputs['Geometry'], output_n.inputs['Furniture Points'])

    print(f"Created node group: {ng.name}")
    return ng


def setup_all_geo_nodes():
    """Create all MSG road system geometry node groups."""
    print("\n" + "=" * 50)
    print("Creating MSG Road System Geometry Nodes")
    print("=" * 50)

    groups = {
        "Road Builder": create_road_builder_node_group(),
        "Lane Markings": create_lane_marking_node_group(),
        "Intersections": create_intersection_node_group(),
        "Street Furniture": create_furniture_node_group(),
    }

    print("\nCreated node groups:")
    for name, group in groups.items():
        print(f"  ✓ {group.name}")

    # Create master node group last (depends on others)
    print("\nCreating master node group...")
    master = create_master_road_node_group()
    print(f"  ✓ {master.name}")

    print("\n" + "=" * 50)
    print("To use:")
    print("1. Add a Geometry Nodes modifier to an object")
    print("2. Select 'MSG_Road_System_Master' for full pipeline")
    print("3. Or use individual MSG_* groups for specific parts")
    print("4. Connect your road curves to the input")
    print("=" * 50 + "\n")

    groups["Master"] = master
    return groups


# Run in Blender
if __name__ == "__main__":
    setup_all_geo_nodes()
