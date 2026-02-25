"""
Charlotte Digital Twin - Crosswalk Generator

Geometry nodes system for generating crosswalks at intersections.
Crosswalks are placed where roads meet and stored as point data
on intersection markers.
"""

import bpy
from mathutils import Vector
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import math


def create_crosswalk_node_group():
    """
    Create node group for generating a single crosswalk.

    Crosswalk geometry:
    - Zebra stripes (white rectangles perpendicular to road)
    - Width matches road width
    - Standard 3m length
    """
    if "Crosswalk" in bpy.data.node_groups:
        return bpy.data.node_groups["Crosswalk"]

    node_group = bpy.data.node_groups.new("Crosswalk", 'GeometryNodeTree')

    # Inputs
    node_group.interface.new_socket(
        name="Width",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 6.0  # Width of road

    node_group.interface.new_socket(
        name="Length",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 3.0  # Crosswalk depth

    node_group.interface.new_socket(
        name="Stripe Width",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 0.4  # Width of each stripe

    node_group.interface.new_socket(
        name="Stripe Gap",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 0.6  # Gap between stripes

    node_group.interface.new_socket(
        name="Material",
        in_out='INPUT',
        socket_type='NodeSocketMaterial'
    )

    # Output
    node_group.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    nodes = node_group.nodes
    links = node_group.links

    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-600, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (600, 0)

    # Calculate number of stripes needed
    # Total width / (stripe_width + gap)
    stripe_count_div = nodes.new('ShaderNodeMath')
    stripe_count_div.location = (-400, 200)
    stripe_count_div.operation = 'DIVIDE'

    stripe_count_add = nodes.new('ShaderNodeMath')
    stripe_count_add.location = (-600, 100)
    stripe_count_add.operation = 'ADD'

    # Create grid of stripes
    # Use Mesh Grid with instances
    grid = nodes.new('GeometryNodeMeshGrid')
    grid.location = (-200, 0)

    # For crosswalk, we create a grid and then use selection
    # to create the stripe pattern
    # Simplified: create one stripe mesh and instance it

    # Single stripe mesh
    stripe = nodes.new('GeometryNodeMeshGrid')
    stripe.location = (-200, -200)
    stripe.inputs['Size X'].default_value = 0.4   # Stripe width
    stripe.inputs['Size Y'].default_value = 3.0   # Crosswalk length
    stripe.inputs['Vertices X'].default_value = 2
    stripe.inputs['Vertices Y'].default_value = 2

    # Grid of points for instancing
    points_grid = nodes.new('GeometryNodeMeshGrid')
    points_grid.location = (-200, 200)
    points_grid.inputs['Vertices X'].default_value = 10
    points_grid.inputs['Vertices Y'].default_value = 2
    points_grid.inputs['Size X'].default_value = 10.0
    points_grid.inputs['Size Y'].default_value = 0.1

    # Instance stripes on points
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    instance.location = (0, 0)

    # Realize instances
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (200, 0)

    links.new(input_node.outputs['Stripe Width'], stripe_count_add.inputs[0])
    links.new(input_node.outputs['Stripe Gap'], stripe_count_add.inputs[1])
    links.new(input_node.outputs['Width'], stripe_count_div.inputs[0])
    links.new(stripe_count_add.outputs[0], stripe_count_div.inputs[1])

    links.new(points_grid.outputs['Mesh'], instance.inputs['Points'])
    links.new(stripe.outputs['Mesh'], instance.inputs['Instance'])
    links.new(instance.outputs['Instances'], realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], output_node.inputs['Geometry'])

    return node_group


def create_crosswalk_distributor():
    """
    Create node group for distributing crosswalks at road endpoints.

    This is applied to road curves and generates crosswalks where
    roads meet (detected by proximity of endpoints).
    """
    if "Crosswalk_Distributor" in bpy.data.node_groups:
        return bpy.data.node_groups["Crosswalk_Distributor"]

    node_group = bpy.data.node_groups.new("Crosswalk_Distributor", 'GeometryNodeTree')

    # Inputs
    node_group.interface.new_socket(
        name="Road Curve",
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )
    node_group.interface.new_socket(
        name="Road Width",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 10.0

    node_group.interface.new_socket(
        name="Crosswalk Offset",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 2.0  # Distance from intersection center

    node_group.interface.new_socket(
        name="Crosswalk Length",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    ).default_value = 3.0

    node_group.interface.new_socket(
        name="Crosswalk Material",
        in_out='INPUT',
        socket_type='NodeSocketMaterial'
    )

    # Outputs
    node_group.interface.new_socket(
        name="Crosswalks",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )
    node_group.interface.new_socket(
        name="Endpoints",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    nodes = node_group.nodes
    links = node_group.links

    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (600, 0)

    # Get curve endpoints
    # Use Endpoint Selection node
    endpoint_selection = nodes.new('GeometryNodeCurveEndpointSelection')
    endpoint_selection.location = (-600, 200)
    endpoint_selection.inputs['Start Size'].default_value = 1
    endpoint_selection.inputs['End Size'].default_value = 1

    # Sample endpoints as points
    # We need to separate endpoints
    separate = nodes.new('GeometryNodeSeparateGeometry')
    separate.location = (-400, 200)

    # Instance crosswalks at endpoints
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    instance.location = (-200, 200)

    # Create crosswalk mesh (simplified stripe pattern)
    crosswalk_mesh = nodes.new('GeometryNodeMeshGrid')
    crosswalk_mesh.location = (-400, -100)
    crosswalk_mesh.inputs['Size X'].default_value = 6.0  # Will be overridden
    crosswalk_mesh.inputs['Size Y'].default_value = 3.0
    crosswalk_mesh.inputs['Vertices X'].default_value = 15  # Creates stripe effect
    crosswalk_mesh.inputs['Vertices Y'].default_value = 2

    # Align euler to curve
    align_rotation = nodes.new('GeometryNodeAlignRotationToVector')
    align_rotation.location = (-400, 400)
    align_rotation.inputs['Factor'].default_value = 1.0

    # Get curve tangent at endpoints for rotation
    curve_tangent = nodes.new('GeometryNodeInputTangent')
    curve_tangent.location = (-600, 400)

    links.new(input_node.outputs['Road Curve'], separate.inputs['Geometry'])
    links.new(endpoint_selection.outputs['Selection'], separate.inputs['Selection'])

    links.new(separate.outputs['Selection'], instance.inputs['Points'])
    links.new(crosswalk_mesh.outputs['Mesh'], instance.inputs['Instance'])
    links.new(curve_tangent.outputs['Tangent'], align_rotation.inputs['Vector'])

    # Realize instances
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (0, 200)

    # Set position (offset from endpoint along tangent)
    set_position = nodes.new('GeometryNodeSetPosition')
    set_position.location = (200, 200)

    # Offset calculation: tangent * offset_distance
    scale = nodes.new('ShaderNodeVectorMath')
    scale.location = (0, 400)
    scale.operation = 'SCALE'

    links.new(instance.outputs['Instances'], realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], set_position.inputs['Geometry'])

    # Create offset vector
    tangent_offset = nodes.new('ShaderNodeVectorMath')
    tangent_offset.location = (-200, 400)
    tangent_offset.operation = 'MULTIPLY'

    links.new(curve_tangent.outputs['Tangent'], tangent_offset.inputs[0])
    links.new(input_node.outputs['Crosswalk Offset'], tangent_offset.inputs[1].default_value)

    links.new(set_position.outputs['Geometry'], output_node.inputs['Crosswalks'])
    links.new(separate.outputs['Selection'], output_node.inputs['Endpoints'])

    return node_group


def create_zebra_crosswalk_asset():
    """
    Create a zebra crosswalk mesh asset.

    Returns the mesh object or creates it if it doesn't exist.
    """
    # Check if already exists
    if "Crosswalk_Zebra" in bpy.data.objects:
        return bpy.data.objects["Crosswalk_Zebra"]

    # Create mesh
    mesh = bpy.data.meshes.new("Crosswalk_Zebra")

    # Create zebra stripe pattern
    # Standard: 40cm stripes, 60cm gaps, 3m deep
    stripe_width = 0.4
    gap_width = 0.6
    crosswalk_length = 3.0
    num_stripes = 8

    vertices = []
    faces = []

    current_x = 0

    for i in range(num_stripes):
        # Stripe corners
        x1 = current_x
        x2 = current_x + stripe_width
        y1 = -crosswalk_length / 2
        y2 = crosswalk_length / 2

        # Four corners of stripe
        v_base = len(vertices)
        vertices.extend([
            (x1, y1, 0.01),  # Bottom left
            (x2, y1, 0.01),  # Bottom right
            (x2, y2, 0.01),  # Top right
            (x1, y2, 0.01),  # Top left
        ])

        # Two triangles for the quad
        faces.append((v_base, v_base + 1, v_base + 2, v_base + 3))

        # Move to next stripe position
        current_x += stripe_width + gap_width

    # Create mesh from data
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    # Create object
    obj = bpy.data.objects.new("Crosswalk_Zebra", mesh)

    # Set origin to center
    total_width = current_x - gap_width  # Last gap doesn't count
    obj.location = (-total_width / 2, 0, 0)

    return obj


def create_crosswalk_collection():
    """
    Create a collection containing crosswalk assets.
    """
    # Check if exists
    if "Crosswalk_Assets" in bpy.data.collections:
        return bpy.data.collections["Crosswalk_Assets"]

    # Create collection
    coll = bpy.data.collections.new("Crosswalk_Assets")
    bpy.context.scene.collection.children.link(coll)

    # Create zebra crosswalk asset
    zebra = create_zebra_crosswalk_asset()
    coll.objects.link(zebra)

    # Hide from render (it's an asset)
    zebra.hide_render = True

    return coll


def detect_crosswalk_positions(road_curves: List[bpy.types.Object]) -> List[Dict]:
    """
    Detect positions where crosswalks should be placed.

    Crosswalks are placed:
    - At intersections (where road endpoints meet)
    - Based on road class (higher class roads get crosswalks)
    - At specified offset from intersection center

    Args:
        road_curves: List of road curve objects

    Returns:
        List of crosswalk positions with:
        - position: (x, y, z)
        - rotation: radians
        - width: road width
        - road_names: list of road names at intersection
    """
    from .intersection_detector import IntersectionDetector

    # Extract road data for detection
    road_segments = []
    for curve in road_curves:
        if curve.type != 'CURVE':
            continue

        # Get curve points
        curve_data = curve.data
        if not curve_data.splines:
            continue

        spline = curve_data.splines[0]
        vertices = []
        for point in spline.points:
            # World coordinates
            world_co = curve.matrix_world @ Vector(point.co[:3])
            vertices.append((world_co.x, world_co.y, world_co.z))

        if len(vertices) < 2:
            continue

        road_segments.append({
            'osm_id': curve.get('osm_id', 0),
            'name': curve.get('road_name', ''),
            'road_class': curve.get('road_class', 'local'),
            'width': curve.get('road_width', 10.0),
            'vertices': vertices,
        })

    # Detect intersections
    detector = IntersectionDetector(
        proximity_threshold=3.0,  # Slightly larger for crosswalk detection
        elevation_threshold=3.0
    )
    clusters = detector.detect(road_segments)

    # Generate crosswalk positions
    crosswalks = []

    for cluster in detector.get_at_grade():
        # Skip if not at an intersection with multiple roads
        if cluster.road_count < 2:
            continue

        # Check if any road is major enough for crosswalks
        has_major_road = any(
            ep.road_class in ('arterial', 'collector')
            for ep in cluster.endpoints
        )

        if not has_major_road:
            continue

        # Generate crosswalk for each road endpoint
        cx, cy, cz = cluster.center

        for endpoint in cluster.endpoints:
            # Direction from center to endpoint
            dx = endpoint.position[0] - cx
            dy = endpoint.position[1] - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 0.1:
                continue

            # Normalize
            dx /= dist
            dy /= dist

            # Crosswalk position (offset from center)
            offset = endpoint.width / 2 + 2.5  # Half road width + crosswalk
            px = cx + dx * offset
            py = cy + dy * offset

            # Rotation (perpendicular to road direction)
            rotation = math.atan2(dy, dx) + math.pi / 2

            crosswalks.append({
                'position': (px, py, cz + 0.02),  # Slightly above road
                'rotation': rotation,
                'width': endpoint.width,
                'road_name': endpoint.road_name,
                'intersection_id': cluster.cluster_id,
            })

    return crosswalks


def create_crosswalk_objects(crosswalk_positions: List[Dict]) -> List[bpy.types.Object]:
    """
    Create crosswalk objects at specified positions.

    Args:
        crosswalk_positions: List of position dicts from detect_crosswalk_positions

    Returns:
        List of created crosswalk objects
    """
    # Ensure asset exists
    create_crosswalk_collection()

    # Get the zebra mesh
    zebra_mesh = bpy.data.meshes.get("Crosswalk_Zebra")
    if not zebra_mesh:
        zebra_obj = create_zebra_crosswalk_asset()
        zebra_mesh = zebra_obj.data

    crosswalk_objects = []

    for i, cw in enumerate(crosswalk_positions):
        # Create new object with shared mesh
        obj = bpy.data.objects.new(f"Crosswalk_{i:04d}", zebra_mesh.copy())

        # Set position
        obj.location = cw['position']

        # Set rotation (around Z axis)
        obj.rotation_euler = (0, 0, cw['rotation'])

        # Scale based on road width
        # Base zebra is ~7m wide, scale to match road width
        base_width = 7.0
        scale = cw['width'] / base_width
        obj.scale = (scale, 1.0, 1.0)

        # Store metadata
        obj['road_name'] = cw.get('road_name', '')
        obj['intersection_id'] = cw.get('intersection_id', '')
        obj['crosswalk_width'] = cw['width']

        # Link to scene
        bpy.context.scene.collection.objects.link(obj)
        crosswalk_objects.append(obj)

    return crosswalk_objects


def generate_all_crosswalks():
    """
    Main function to generate crosswalks for all roads in the scene.
    """
    print("\n=== Generating Crosswalks ===")

    # Get all road curves
    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('road_class')
    ]

    print(f"Found {len(road_curves)} road curves")

    # Detect crosswalk positions
    print("Detecting crosswalk positions...")
    positions = detect_crosswalk_positions(road_curves)
    print(f"  Found {len(positions)} crosswalk positions")

    # Create crosswalk collection
    crosswalk_coll = bpy.data.collections.get("Crosswalks")
    if not crosswalk_coll:
        crosswalk_coll = bpy.data.collections.new("Crosswalks")
        bpy.context.scene.collection.children.link(crosswalk_coll)

    # Create crosswalk objects
    print("Creating crosswalk objects...")
    objects = create_crosswalk_objects(positions)

    # Move to collection
    for obj in objects:
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        crosswalk_coll.objects.link(obj)

    print(f"Created {len(objects)} crosswalks")

    return objects


if __name__ == '__main__':
    generate_all_crosswalks()
