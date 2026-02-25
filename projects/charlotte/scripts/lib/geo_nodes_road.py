"""
Charlotte Digital Twin - Geometry Nodes Road Builder

Creates and configures geometry nodes for building roads from curves.
"""

import bpy
from mathutils import Vector
import sys
from pathlib import Path


def create_road_builder_node_group():
    """
    Create the main Road_Builder geometry node group.

    This node group takes curve inputs and generates:
    - Road surface mesh
    - Lane markings
    - Street lights (optional)
    """

    # Check if already exists
    if "Road_Builder" in bpy.data.node_groups:
        return bpy.data.node_groups["Road_Builder"]

    # Create new node group
    node_group = bpy.data.node_groups.new("Road_Builder", 'GeometryNodeTree')

    # Create interface
    # Inputs
    node_group.interface.new_socket(
        name="Road Curve",
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )
    node_group.interface.new_socket(
        name="Width",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 10.0
    node_group.interface.new_socket(
        name="Lanes",
        in_out='INPUT',
        socket_type='NodeSocketInt'
    ).default_value = 2
    node_group.interface.new_socket(
        name="Road Class",
        in_out='INPUT',
        socket_type='NodeSocketInt'
    ).default_value = 3  # Local
    node_group.interface.new_socket(
        name="Has Markings",
        in_out='INPUT',
        socket_type='NodeSocketBool'
    ).default_value = True
    node_group.interface.new_socket(
        name="Has Sidewalk",
        in_out='INPUT',
        socket_type='NodeSocketBool'
    ).default_value = True
    node_group.interface.new_socket(
        name="Light Spacing",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 30.0
    node_group.interface.new_socket(
        name="Marking Material",
        in_out='INPUT',
        socket_type='NodeSocketMaterial'
    )
    node_group.interface.new_socket(
        name="Road Material",
        in_out='INPUT',
        socket_type='NodeSocketMaterial'
    )

    # Outputs
    node_group.interface.new_socket(
        name="Road Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )
    node_group.interface.new_socket(
        name="Markings",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )
    node_group.interface.new_socket(
        name="Street Lights",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    # Create nodes
    nodes = node_group.nodes
    links = node_group.links

    # Input node
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    # Output node
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (800, 0)

    # --- Road Surface Generation ---

    # Resample Curve (even spacing)
    resample = nodes.new('GeometryNodeResampleCurve')
    resample.location = (-600, 200)
    resample.mode = 'LENGTH'
    resample.inputs['Length'].default_value = 1.0  # 1m segments

    # Curve to Mesh
    curve_to_mesh = nodes.new('GeometryNodeCurveToMesh')
    curve_to_mesh.location = (-400, 200)

    # Create profile curve (rectangle for road cross-section)
    profile_curve = nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    profile_curve.location = (-600, -100)
    profile_curve.mode = 'RECTANGLE'

    # Join geometry for output
    join_geo = nodes.new('GeometryNodeJoinGeometry')
    join_geo.location = (600, 0)

    # Link nodes
    links.new(input_node.outputs['Road Curve'], resample.inputs['Curve'])
    links.new(resample.outputs['Curve'], curve_to_mesh.inputs['Curve'])
    links.new(profile_curve.outputs['Curve'], curve_to_mesh.inputs['Profile Curve'])
    links.new(curve_to_mesh.outputs['Mesh'], join_geo.inputs['Geometry'])
    links.new(join_geo.outputs['Geometry'], output_node.inputs['Road Geometry'])

    # Connect width to profile
    # We need to divide width by 2 for the rectangle
    divide = nodes.new('ShaderNodeMath')
    divide.location = (-800, -100)
    divide.operation = 'DIVIDE'
    divide.inputs[1].default_value = 2.0

    links.new(input_node.outputs['Width'], divide.inputs[0])
    links.new(divide.outputs[0], profile_curve.inputs['Width'])

    return node_group


def create_lane_markings_node_group():
    """
    Create node group for generating lane markings.
    """
    if "Lane_Markings" in bpy.data.node_groups:
        return bpy.data.node_groups["Lane_Markings"]

    node_group = bpy.data.node_groups.new("Lane_Markings", 'GeometryNodeTree')

    # Inputs
    node_group.interface.new_socket(
        name="Curve",
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )
    node_group.interface.new_socket(
        name="Road Width",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 10.0
    node_group.interface.new_socket(
        name="Lanes",
        in_out='INPUT',
        socket_type='NodeSocketInt'
    ).default_value = 2
    node_group.interface.new_socket(
        name="Has Center Line",
        in_out='INPUT',
        socket_type='NodeSocketBool'
    ).default_value = True
    node_group.interface.new_socket(
        name="Has Edge Lines",
        in_out='INPUT',
        socket_type='NodeSocketBool'
    ).default_value = True
    node_group.interface.new_socket(
        name="Dash Length",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 3.0
    node_group.interface.new_socket(
        name="Dash Gap",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 6.0

    # Output
    node_group.interface.new_socket(
        name="Markings",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    # Basic implementation: distribute cube instances along curve
    nodes = node_group.nodes
    links = node_group.links

    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-400, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (400, 0)

    # Resample curve for marking positions
    resample = nodes.new('GeometryNodeResampleCurve')
    resample.location = (-200, 0)
    resample.mode = 'LENGTH'
    resample.inputs['Length'].default_value = 3.0  # Dash every 3m

    # Instance on points
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    instance.location = (0, 0)

    # Create marking mesh (thin rectangle)
    cube = nodes.new('GeometryNodeMeshGrid')
    cube.location = (-200, -200)
    cube.inputs['Vertices X'].default_value = 2  # 2m long
    cube.inputs['Vertices Y'].default_value = 2
    cube.inputs['Size X'].default_value = 3.0
    cube.inputs['Size Y'].default_value = 0.15  # 15cm wide

    links.new(input_node.outputs['Curve'], resample.inputs['Curve'])
    links.new(resample.outputs['Curve'], instance.inputs['Points'])
    links.new(cube.outputs['Mesh'], instance.inputs['Instance'])
    links.new(instance.outputs['Instances'], output_node.inputs['Markings'])

    return node_group


def create_street_light_distributor():
    """
    Create node group for distributing street lights along roads.
    """
    if "Street_Light_Distributor" in bpy.data.node_groups:
        return bpy.data.node_groups["Street_Light_Distributor"]

    node_group = bpy.data.node_groups.new("Street_Light_Distributor", 'GeometryNodeTree')

    # Inputs
    node_group.interface.new_socket(
        name="Curve",
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )
    node_group.interface.new_socket(
        name="Spacing",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 30.0
    node_group.interface.new_socket(
        name="Offset",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 2.0
    node_group.interface.new_socket(
        name="Light Collection",
        in_out='INPUT',
        socket_type='NodeSocketCollection'
    )

    # Output
    node_group.interface.new_socket(
        name="Lights",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    nodes = node_group.nodes
    links = node_group.links

    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-400, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (400, 0)

    # Resample at spacing intervals
    resample = nodes.new('GeometryNodeResampleCurve')
    resample.location = (-200, 0)
    resample.mode = 'LENGTH'

    # Instance on points
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    instance.location = (0, 0)

    # Placeholder: use a simple cube as light
    # In production, would use collection instance
    cube = nodes.new('GeometryNodeMeshCube')
    cube.location = (-200, -200)
    cube.inputs['Size X'].default_value = 0.3
    cube.inputs['Size Y'].default_value = 0.3
    cube.inputs['Size Z'].default_value = 8.0  # 8m tall

    links.new(input_node.outputs['Curve'], resample.inputs['Curve'])
    links.new(input_node.outputs['Spacing'], resample.inputs['Length'])
    links.new(resample.outputs['Curve'], instance.inputs['Points'])
    links.new(cube.outputs['Mesh'], instance.inputs['Instance'])
    links.new(instance.outputs['Instances'], output_node.inputs['Lights'])

    return node_group


def apply_road_builder_to_curves():
    """
    Apply the Road_Builder geometry nodes modifier to all road curves.
    """
    # Get or create node group
    road_builder = create_road_builder_node_group()

    # Find all road curve objects
    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('road_class')
    ]

    print(f"Applying Road_Builder to {len(road_curves)} curves")

    for obj in road_curves:
        # Add geometry nodes modifier
        mod = obj.modifiers.new(name="Road_Builder", type='NODES')
        mod.node_group = road_builder

        # Set input values from object properties
        if 'gn_width' in obj:
            mod['Socket_2'] = obj['gn_width']  # Width
        if 'gn_lanes' in obj:
            mod['Socket_3'] = obj['gn_lanes']  # Lanes
        if 'gn_road_class' in obj:
            mod['Socket_4'] = obj['gn_road_class']  # Road Class
        if 'gn_has_markings' in obj:
            mod['Socket_5'] = obj['gn_has_markings']
        if 'gn_has_sidewalk' in obj:
            mod['Socket_6'] = obj['gn_has_sidewalk']

    print("Applied Road_Builder to all curves")


def create_crosswalk_geo_nodes():
    """
    Create node group for procedural crosswalk generation at road endpoints.
    """
    if "Crosswalk_Generator" in bpy.data.node_groups:
        return bpy.data.node_groups["Crosswalk_Generator"]

    node_group = bpy.data.node_groups.new("Crosswalk_Generator", 'GeometryNodeTree')

    # Inputs
    node_group.interface.new_socket(
        name="Curve",
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )
    node_group.interface.new_socket(
        name="Road Width",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 10.0
    node_group.interface.new_socket(
        name="Crosswalk Length",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 3.0
    node_group.interface.new_socket(
        name="Stripe Width",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 0.4
    node_group.interface.new_socket(
        name="Stripe Gap",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 0.6

    # Output
    node_group.interface.new_socket(
        name="Crosswalks",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    nodes = node_group.nodes
    links = node_group.links

    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-600, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (600, 0)

    # Select endpoints
    endpoint_sel = nodes.new('GeometryNodeCurveEndpointSelection')
    endpoint_sel.location = (-400, 200)
    endpoint_sel.inputs['Start Size'].default_value = 1
    endpoint_sel.inputs['End Size'].default_value = 1

    # Separate endpoints
    separate = nodes.new('GeometryNodeSeparateGeometry')
    separate.location = (-200, 200)

    # Create crosswalk stripe pattern
    # Grid of stripes
    stripe_count = 8
    grid = nodes.new('GeometryNodeMeshGrid')
    grid.location = (-200, -100)
    grid.inputs['Vertices X'].default_value = stripe_count * 2  # Stripes + gaps
    grid.inputs['Vertices Y'].default_value = 2
    grid.inputs['Size X'].default_value = 8.0  # Will scale with road width
    grid.inputs['Size Y'].default_value = 3.0  # Crosswalk length

    # Instance on endpoints
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    instance.location = (0, 100)

    # Align to curve tangent
    align = nodes.new('GeometryNodeAlignRotationToVector')
    align.location = (-200, 300)

    tangent = nodes.new('GeometryNodeInputTangent')
    tangent.location = (-400, 300)

    # Realize instances
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (200, 100)

    # Offset from endpoint
    set_pos = nodes.new('GeometryNodeSetPosition')
    set_pos.location = (400, 100)

    links.new(input_node.outputs['Curve'], separate.inputs['Geometry'])
    links.new(endpoint_sel.outputs['Selection'], separate.inputs['Selection'])
    links.new(separate.outputs['Selection'], instance.inputs['Points'])
    links.new(grid.outputs['Mesh'], instance.inputs['Instance'])
    links.new(tangent.outputs['Tangent'], align.inputs['Vector'])
    links.new(align.outputs['Rotation'], instance.inputs['Rotation'])
    links.new(instance.outputs['Instances'], realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], set_pos.inputs['Geometry'])
    links.new(set_pos.outputs['Geometry'], output_node.inputs['Crosswalks'])

    return node_group


def setup_road_geometry_nodes():
    """
    Main setup function - creates all node groups and applies to curves.
    """
    print("\n=== Setting up Road Geometry Nodes ===")

    # Create node groups
    print("Creating Road_Builder node group...")
    create_road_builder_node_group()

    print("Creating Lane_Markings node group...")
    create_lane_markings_node_group()

    print("Creating Street_Light_Distributor node group...")
    create_street_light_distributor()

    print("Creating Crosswalk_Generator node group...")
    create_crosswalk_geo_nodes()

    # Apply to curves
    apply_road_builder_to_curves()

    print("\nGeometry nodes setup complete!")


if __name__ == '__main__':
    setup_road_geometry_nodes()
