"""
MSG-1998 Road System - Geometry Nodes Version

Creates Blender Geometry Nodes node groups for road generation.
This is the non-destructive, interactive approach.

Node Group Hierarchy:
1. MSG_Road_Curve_Processor - Convert mesh roads to curves with classification
2. MSG_Road_Builder - Main road geometry (pavement, curb, sidewalk)
3. MSG_Intersection_Builder - Auto-detect and build intersections
4. MSG_Marking_Generator - Lane markings and crosswalks
5. MSG_Furniture_Distributor - Distribute manholes, etc.
"""

import bpy
from bpy.types import NodeTree, Node
import math


def create_node_group(name: str, inputs: dict, outputs: dict) -> NodeTree:
    """
    Create a geometry node group with specified inputs/outputs.

    Args:
        name: Node group name
        inputs: Dict of {name: (type, default_value)}
        outputs: Dict of {name: type}

    Returns:
        Created node group
    """
    # Create or get existing
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    node_group = bpy.data.node_groups.new(name, 'GeometryNodeTree')

    # Create interface
    for input_name, (input_type, default) in inputs.items():
        socket = node_group.interface.new_socket(
            name=input_name,
            in_out='INPUT',
            socket_type=input_type,
        )
        if hasattr(socket, 'default_value') and default is not None:
            socket.default_value = default

    for output_name, output_type in outputs.items():
        node_group.interface.new_socket(
            name=output_name,
            in_out='OUTPUT',
            socket_type=output_type,
        )

    return node_group


def create_road_curve_processor() -> NodeTree:
    """
    Create node group that processes road mesh objects into curves.

    Inputs:
        - Road Mesh: Collection of road meshes
        - Default Width: Width for roads without width attribute
        - Resolution: Curve resolution

    Outputs:
        - Road Curves: Curves with width and class attributes
    """
    ng = create_node_group(
        "MSG_Road_Curve_Processor",
        inputs={
            "Road Mesh": ('NodeSocketGeometry', None),
            "Default Width": ('NodeSocketFloat', 10.0),
            "Resolution": ('NodeSocketInt', 12),
        },
        outputs={
            "Road Curves": 'NodeSocketGeometry',
        }
    )

    # Add nodes
    nodes = ng.nodes

    # Input node
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    # Mesh to Curve conversion
    mesh_to_curve = nodes.new('GeometryNodeMeshToCurve')
    mesh_to_curve.location = (-400, 0)

    # Store named attribute for width
    store_width = nodes.new('GeometryNodeStoreNamedAttribute')
    store_width.location = (-200, 0)
    store_width.data_type = 'FLOAT'
    store_width.domain = 'SPLINE'
    store_width.inputs['Name'].default_value = "road_width"

    # Resample curves
    resample = nodes.new('GeometryNodeResampleCurve')
    resample.location = (0, 0)
    resample.mode = 'COUNT'

    # Output node
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (400, 0)

    # Link nodes
    ng.links.new(input_node.outputs['Road Mesh'], mesh_to_curve.inputs['Mesh'])
    ng.links.new(mesh_to_curve.outputs['Curve'], store_width.inputs['Geometry'])
    ng.links.new(input_node.outputs['Default Width'], store_width.inputs['Value'])
    ng.links.new(store_width.outputs['Geometry'], resample.inputs['Curve'])
    ng.links.new(input_node.outputs['Resolution'], resample.inputs['Count'])
    ng.links.new(resample.outputs['Curve'], output_node.inputs['Road Curves'])

    return ng


def create_road_builder() -> NodeTree:
    """
    Create node group that builds road geometry from curves.

    Inputs:
        - Road Curves: Curves with road_width attribute
        - Sidewalk Width: Width of sidewalks on each side
        - Curb Height: Height of curbs
        - Cross Fall: Road surface slope for drainage

    Outputs:
        - Pavement: Road surface mesh
        - Curbs: Curb geometry
        - Sidewalks: Sidewalk geometry
        - Combined: All geometry joined
    """
    ng = create_node_group(
        "MSG_Road_Builder",
        inputs={
            "Road Curves": ('NodeSocketGeometry', None),
            "Sidewalk Width": ('NodeSocketFloat', 2.0),
            "Curb Height": ('NodeSocketFloat', 0.15),
            "Cross Fall": ('NodeSocketFloat', 0.02),
        },
        outputs={
            "Pavement": 'NodeSocketGeometry',
            "Curbs": 'NodeSocketGeometry',
            "Sidewalks": 'NodeSocketGeometry',
            "Combined": 'NodeSocketGeometry',
        }
    )

    nodes = ng.nodes

    # Input
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1200, 0)

    # === PAVEMENT ===
    # Get road width from attribute
    get_width = nodes.new('GeometryNodeInputNamedAttribute')
    get_width.location = (-800, 200)
    get_width.data_type = 'FLOAT'
    get_width.inputs['Name'].default_value = "road_width"

    # Calculate half width
    half_width_math = nodes.new('ShaderNodeMath')
    half_width_math.location = (-600, 200)
    half_width_math.operation = 'DIVIDE'

    # Curve to mesh (pavement)
    pavement_curve = nodes.new('GeometryNodeCurveToMesh')
    pavement_curve.location = (-200, 300)

    # Create profile curve for road surface
    road_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    road_profile.location = (-600, 400)
    road_profile.mode = 'RECTANGLE'

    # Set material for pavement
    pavement_material = nodes.new('GeometryNodeSetMaterial')
    pavement_material.location = (0, 300)

    # === CURBS ===
    # Offset curves for curb position
    curb_offset = nodes.new('GeometryNodeSetCurveRadius')
    curb_offset.location = (-400, 0)

    # Curb profile (extruded rectangle)
    curb_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    curb_profile.location = (-200, -100)
    curb_profile.mode = 'RECTANGLE'
    curb_profile.inputs['Width'].default_value = 0.15
    curb_profile.inputs['Height'].default_value = 0.15

    curb_curve_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    curb_curve_to_mesh.location = (0, -100)

    # Transform curb up
    curb_transform = nodes.new('GeometryNodeTransform')
    curb_transform.location = (200, -100)

    # === SIDEWALKS ===
    # Offset for sidewalk position
    sidewalk_offset = nodes.new('GeometryNodeSetCurveRadius')
    sidewalk_offset.location = (-400, -300)

    sidewalk_profile = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    sidewalk_profile.location = (-200, -300)
    sidewalk_profile.mode = 'RECTANGLE'
    sidewalk_profile.inputs['Height'].default_value = 1.5

    sidewalk_curve_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    sidewalk_curve_to_mesh.location = (0, -300)

    sidewalk_transform = nodes.new('GeometryNodeTransform')
    sidewalk_transform.location = (200, -300)

    # === COMBINE ===
    join_all = nodes.new('GeometryNodeJoinGeometry')
    join_all.location = (600, 0)

    # Output
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (900, 0)

    # Link pavement
    ng.links.new(input_node.outputs['Road Curves'], get_width.inputs[0])
    ng.links.new(get_width.outputs['Attribute'], half_width_math.inputs[0])
    ng.links.new(half_width_math.outputs[0], road_profile.inputs['Width'])
    ng.links.new(input_node.outputs['Road Curves'], pavement_curve.inputs['Curve'])
    ng.links.new(road_profile.outputs['Curve'], pavement_curve.inputs['Profile Curve'])
    ng.links.new(pavement_curve.outputs['Mesh'], pavement_material.inputs['Geometry'])
    ng.links.new(pavement_material.outputs['Geometry'], join_all.inputs['Geometry'])

    # Link curbs
    ng.links.new(input_node.outputs['Road Curves'], curb_offset.inputs['Curve'])
    ng.links.new(curb_offset.outputs['Curve'], curb_curve_to_mesh.inputs['Curve'])
    ng.links.new(curb_profile.outputs['Curve'], curb_curve_to_mesh.inputs['Profile Curve'])
    ng.links.new(curb_curve_to_mesh.outputs['Mesh'], curb_transform.inputs['Geometry'])
    ng.links.new(curb_transform.outputs['Geometry'], join_all.inputs['Geometry'])

    # Link sidewalks
    ng.links.new(input_node.outputs['Road Curves'], sidewalk_offset.inputs['Curve'])
    ng.links.new(sidewalk_offset.outputs['Curve'], sidewalk_curve_to_mesh.inputs['Curve'])
    ng.links.new(sidewalk_profile.outputs['Curve'], sidewalk_curve_to_mesh.inputs['Profile Curve'])
    ng.links.new(sidewalk_curve_to_mesh.outputs['Mesh'], sidewalk_transform.inputs['Geometry'])
    ng.links.new(sidewalk_transform.outputs['Geometry'], join_all.inputs['Geometry'])

    # Link outputs
    ng.links.new(pavement_material.outputs['Geometry'], output_node.inputs['Pavement'])
    ng.links.new(curb_transform.outputs['Geometry'], output_node.inputs['Curbs'])
    ng.links.new(sidewalk_transform.outputs['Geometry'], output_node.inputs['Sidewalks'])
    ng.links.new(join_all.outputs['Geometry'], output_node.inputs['Combined'])

    return ng


def create_intersection_detector() -> NodeTree:
    """
    Create node group that detects intersection points from overlapping curves.

    This uses proximity detection to find where road endpoints cluster.

    Inputs:
        - Road Curves: Processed road curves
        - Detection Radius: Distance to consider endpoints as same intersection

    Outputs:
        - Intersection Points: Points at intersection centers
        - Intersection Radii: Radius for each intersection based on road widths
    """
    ng = create_node_group(
        "MSG_Intersection_Detector",
        inputs={
            "Road Curves": ('NodeSocketGeometry', None),
            "Detection Radius": ('NodeSocketFloat', 3.0),
        },
        outputs={
            "Intersection Points": 'NodeSocketGeometry',
            "Intersection Radii": 'NodeSocketFloat',
        }
    )

    nodes = ng.nodes

    # Input
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    # Extract curve endpoints
    endpoints = nodes.new('GeometryNodeEndpoints')
    endpoints.location = (-400, 0)

    # Merge by distance to cluster endpoints
    merge_by_distance = nodes.new('GeometryNodeMergeByDistance')
    merge_by_distance.location = (-100, 0)

    # Output
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (300, 0)

    # Link
    ng.links.new(input_node.outputs['Road Curves'], endpoints.inputs['Geometry'])
    ng.links.new(endpoints.outputs['End Points'], merge_by_distance.inputs['Geometry'])
    ng.links.new(input_node.outputs['Detection Radius'], merge_by_distance.inputs['Distance'])
    ng.links.new(merge_by_distance.outputs['Geometry'], output_node.inputs['Intersection Points'])

    return ng


def create_marking_generator() -> NodeTree:
    """
    Create node group that generates lane markings along roads.

    Inputs:
        - Road Curves: Curves with road attributes
        - Lanes: Number of lanes
        - Dash Length: Length of dashed line segments
        - Gap Length: Gap between dashes

    Outputs:
        - Center Lines: Yellow center line geometry
        - Lane Dividers: White dashed lane dividers
        - Edge Lines: White solid edge lines
    """
    ng = create_node_group(
        "MSG_Marking_Generator",
        inputs={
            "Road Curves": ('NodeSocketGeometry', None),
            "Lanes": ('NodeSocketInt', 2),
            "Dash Length": ('NodeSocketFloat', 3.0),
            "Gap Length": ('NodeSocketFloat', 9.0),
            "Line Width": ('NodeSocketFloat', 0.1),
        },
        outputs={
            "Center Lines": 'NodeSocketGeometry',
            "Lane Dividers": 'NodeSocketGeometry',
            "Edge Lines": 'NodeSocketGeometry',
            "All Markings": 'NodeSocketGeometry',
        }
    )

    nodes = ng.nodes

    # Input
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    # === CENTER LINE (yellow, double) ===
    # Trim curve to create gaps (simplified - just create solid line for now)
    center_resample = nodes.new('GeometryNodeResampleCurve')
    center_resample.location = (-400, 300)
    center_resample.mode = 'LENGTH'

    # Offset for double line
    center_offset_left = nodes.new('GeometryNodeSetCurveRadius')
    center_offset_left.location = (-200, 400)
    center_offset_left.inputs['Radius'].default_value = 0.15

    center_offset_right = nodes.new('GeometryNodeSetCurveRadius')
    center_offset_right.location = (-200, 200)
    center_offset_right.inputs['Radius'].default_value = 0.15

    # Profile for line
    line_profile = nodes.new('GeometryNodeCurvePrimitiveCircle')
    line_profile.location = (0, 300)
    line_profile.inputs['Resolution'].default_value = 4  # Square profile

    center_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    center_to_mesh.location = (200, 300)

    # === EDGE LINES ===
    edge_offset = nodes.new('GeometryNodeSetCurveRadius')
    edge_offset.location = (-400, -200)

    edge_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    edge_to_mesh.location = (0, -200)

    # Combine all
    join_all = nodes.new('GeometryNodeJoinGeometry')
    join_all.location = (400, 0)

    # Output
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (700, 0)

    # Links
    ng.links.new(input_node.outputs['Road Curves'], center_resample.inputs['Curve'])
    ng.links.new(input_node.outputs['Road Curves'], center_offset_left.inputs['Curve'])
    ng.links.new(input_node.outputs['Road Curves'], center_offset_right.inputs['Curve'])

    ng.links.new(center_resample.outputs['Curve'], center_to_mesh.inputs['Curve'])
    ng.links.new(line_profile.outputs['Curve'], center_to_mesh.inputs['Profile Curve'])

    ng.links.new(center_to_mesh.outputs['Mesh'], join_all.inputs['Geometry'])
    ng.links.new(edge_to_mesh.outputs['Mesh'], join_all.inputs['Geometry'])

    ng.links.new(center_to_mesh.outputs['Mesh'], output_node.inputs['Center Lines'])
    ng.links.new(edge_to_mesh.outputs['Mesh'], output_node.inputs['Edge Lines'])
    ng.links.new(join_all.outputs['Geometry'], output_node.inputs['All Markings'])

    return ng


def create_furniture_distributor() -> NodeTree:
    """
    Create node group that distributes street furniture along roads.

    Inputs:
        - Road Curves: Curves with road attributes
        - Spacing: Average spacing between items
        - Randomness: Position variation

    Outputs:
        - Manhole Points: Points for manhole placement
        - Hydrant Points: Points for fire hydrant placement
    """
    ng = create_node_group(
        "MSG_Furniture_Distributor",
        inputs={
            "Road Curves": ('NodeSocketGeometry', None),
            "Manhole Spacing": ('NodeSocketFloat', 40.0),
            "Hydrant Spacing": ('NodeSocketFloat', 120.0),
            "Randomness": ('NodeSocketFloat', 0.5),
        },
        outputs={
            "Manhole Points": 'NodeSocketGeometry',
            "Hydrant Points": 'NodeSocketGeometry',
        }
    )

    nodes = ng.nodes

    # Input
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-600, 0)

    # Resample curve to get even distribution points
    resample = nodes.new('GeometryNodeResampleCurve')
    resample.location = (-300, 0)
    resample.mode = 'LENGTH'

    # Distribute points
    distribute_points = nodes.new('GeometryNodeDistributePointsOnFaces')
    distribute_points.location = (0, 0)

    # Output
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (300, 0)

    # Links
    ng.links.new(input_node.outputs['Road Curves'], resample.inputs['Curve'])
    ng.links.new(input_node.outputs['Manhole Spacing'], resample.inputs['Length'])
    ng.links.new(resample.outputs['Curve'], output_node.inputs['Manhole Points'])

    return ng


def setup_all_node_groups():
    """Create all MSG road system node groups."""
    print("Creating MSG Road System Node Groups...")

    groups = {
        "Road Curve Processor": create_road_curve_processor(),
        "Road Builder": create_road_builder(),
        "Intersection Detector": create_intersection_detector(),
        "Marking Generator": create_marking_generator(),
        "Furniture Distributor": create_furniture_distributor(),
    }

    print(f"Created {len(groups)} node groups:")
    for name, group in groups.items():
        print(f"  - {group.name}")

    return groups


def create_master_modifier():
    """
    Create a master Geometry Nodes modifier setup on a new object.

    This chains all the node groups together.
    """
    # Ensure all node groups exist
    setup_all_node_groups()

    # Create a new object for the road system
    bpy.ops.mesh.primitive_plane_add(size=0.1)
    road_system = bpy.context.active_object
    road_system.name = "MSG_Road_System"

    # Add Geometry Nodes modifier
    modifier = road_system.modifiers.new(name="Road System", type='NODES')
    node_group = bpy.data.node_groups.new("MSG_Road_Master", 'GeometryNodeTree')

    # Set up the master node group
    modifier.node_group = node_group

    print(f"Created master road system object: {road_system.name}")
    print("Connect your 'Streets_Roads' collection to the input")

    return road_system


# Run setup when executed in Blender
if __name__ == "__main__":
    setup_all_node_groups()
