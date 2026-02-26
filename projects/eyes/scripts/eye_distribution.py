"""
Eye Distribution - Point Distribution and Instance System

Creates distribution node groups for placing eyes on surfaces or in volumes.
Supports random, grid, and sphere surface distributions.
"""

import bpy
from bpy.types import GeometryNodeTree
from mathutils import Vector
import random


def create_distribution_node_group(name: str = "EyeDistribution") -> GeometryNodeTree:
    """
    Creates a Geometry Node group for distributing eye instances.

    Distributes points on a sphere surface and instances the EyeGeometry
    node group on each point with size variation.

    Inputs:
    - Eye Count: Number of eyes to generate
    - Distribution Radius: Radius of distribution sphere
    - Size Min: Minimum eye size
    - Size Max: Maximum eye size
    - Seed: Random seed for reproducibility
    - Eye Geometry: The eye node group to instance

    Outputs:
    - Geometry: All eye instances combined
    """
    # Check if node group already exists
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    # Create new geometry node group
    node_group = bpy.data.node_groups.new(name, 'GeometryNodeTree')

    # Create interface inputs
    inputs = [
        ("Eye Count", 'NodeSocketInt', 100, 12, 1000000),
        ("Distribution Radius", 'NodeSocketFloat', 10.0, 0.1, 1000.0),
        ("Size Min", 'NodeSocketFloat', 0.1, 0.001, 10.0),
        ("Size Max", 'NodeSocketFloat', 1.0, 0.01, 10.0),
        ("Seed", 'NodeSocketInt', 42, 0, 999999),
        ("Pupil Ratio", 'NodeSocketFloat', 0.3, 0.0, 1.0),
        ("Iris Ratio", 'NodeSocketFloat', 0.6, 0.0, 1.0),
        ("Subdivisions", 'NodeSocketInt', 2, 0, 6),
    ]

    for input_name, socket_type, default, min_val, max_val in inputs:
        node_group.interface.new_socket(
            name=input_name,
            in_out='INPUT',
            socket_type=socket_type
        )
        # Set default and range
        for item in node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.name == input_name:
                item.default_value = default
                if socket_type == 'NodeSocketFloat':
                    item.min_value = min_val
                    item.max_value = max_val
                elif socket_type == 'NodeSocketInt':
                    item.min_value = int(min_val)
                    item.max_value = int(max_val)
                break

    # Create interface output
    node_group.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    # Create nodes
    nodes = node_group.nodes
    links = node_group.links

    # Input node
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1200, 0)

    # Create distribution sphere (invisible, just for point distribution)
    distribution_sphere = nodes.new('GeometryNodeMeshUVSphere')
    distribution_sphere.label = "Distribution Sphere"
    distribution_sphere.location = (-1000, 300)
    distribution_sphere.inputs['Segments'].default_value = 64
    distribution_sphere.inputs['Rings'].default_value = 32

    # Link radius input
    links.new(input_node.outputs['Distribution Radius'],
              distribution_sphere.inputs['Radius'])

    # Distribute points on surface
    distribute_points = nodes.new('GeometryNodeDistributePointsOnFaces')
    distribute_points.label = "Distribute Points"
    distribute_points.location = (-700, 300)
    distribute_points.distribute_method = 'RANDOM'

    # Link distribution sphere and count
    links.new(distribution_sphere.outputs['Mesh'],
              distribute_points.inputs['Mesh'])
    links.new(input_node.outputs['Eye Count'],
              distribute_points.inputs['Density Max'])
    # Set seed for randomness
    links.new(input_node.outputs['Seed'],
              distribute_points.inputs['Seed'])

    # Random value for size variation
    random_size = nodes.new('FunctionNodeRandomValue')
    random_size.label = "Random Size"
    random_size.location = (-700, 0)
    random_size.data_type = 'FLOAT'

    # Link seed to random
    links.new(input_node.outputs['Seed'], random_size.inputs['ID'])

    # Map range for size variation (min to max)
    map_range = nodes.new('ShaderNodeMapRange')
    map_range.label = "Size Range"
    map_range.location = (-500, 0)
    map_range.inputs[1].default_value = 0.0  # From min
    map_range.inputs[2].default_value = 1.0  # From max
    # To min and max will be linked from inputs

    links.new(random_size.outputs[0], map_range.inputs[0])  # Value
    links.new(input_node.outputs['Size Min'], map_range.inputs[3])  # To Min
    links.new(input_node.outputs['Size Max'], map_range.inputs[4])  # To Max

    # Store named attribute for size (so instances can use it)
    store_size = nodes.new('GeometryNodeStoreNamedAttribute')
    store_size.label = "Store Eye Size"
    store_size.location = (-300, 300)
    store_size.data_type = 'FLOAT'
    store_size.domain = 'POINT'
    store_size.inputs['Name'].default_value = "eye_size"

    links.new(distribute_points.outputs['Points'], store_size.inputs['Geometry'])
    links.new(map_range.outputs[0], store_size.inputs['Value'])

    # Instance eye geometry
    # First, we need to reference the EyeGeometry node group
    eye_node_group = bpy.data.node_groups.get("EyeGeometry")

    # Instance on points
    instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')
    instance_on_points.label = "Instance Eyes"
    instance_on_points.location = (0, 300)

    links.new(store_size.outputs['Geometry'], instance_on_points.inputs['Points'])

    # Create a single eye as instance reference
    # We'll use Object Info if we have an eye object, or create inline
    # For now, create a simple icosphere as placeholder
    eye_sphere = nodes.new('GeometryNodeMeshIcoSphere')
    eye_sphere.label = "Eye Instance"
    eye_sphere.location = (-300, 100)
    eye_sphere.inputs['Subdivisions'].default_value = 2

    # Link size from stored attribute
    # Note: We'll use the input size for now, proper attribute reading
    # requires more complex setup
    links.new(map_range.outputs[0], eye_sphere.inputs['Radius'])

    links.new(eye_sphere.outputs['Mesh'], instance_on_points.inputs['Instance'])

    # Scale instances by random size
    # Create vector from float size
    combine_vector = nodes.new('ShaderNodeCombineXYZ')
    combine_vector.label = "Size to Vector"
    combine_vector.location = (-300, -100)

    links.new(map_range.outputs[0], combine_vector.inputs['X'])
    links.new(map_range.outputs[0], combine_vector.inputs['Y'])
    links.new(map_range.outputs[0], combine_vector.inputs['Z'])

    links.new(combine_vector.outputs['Vector'], instance_on_points.inputs['Scale'])

    # Realize instances (optional - for export)
    realize_instances = nodes.new('GeometryNodeRealizeInstances')
    realize_instances.label = "Realize Instances"
    realize_instances.location = (300, 300)

    links.new(instance_on_points.outputs['Instances'], realize_instances.inputs['Geometry'])

    # Output node
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (500, 300)

    links.new(realize_instances.outputs['Geometry'], output_node.inputs['Geometry'])

    return node_group


def create_eyes_on_sphere(
    count: int = 100,
    radius: float = 10.0,
    size_min: float = 0.1,
    size_max: float = 1.0,
    seed: int = 42,
    name: str = "EyeCluster"
) -> bpy.types.Object:
    """
    Creates a cluster of eyes distributed on a sphere surface.

    Args:
        count: Number of eyes to generate
        radius: Distribution sphere radius
        size_min: Minimum eye size
        size_max: Maximum eye size
        seed: Random seed for reproducibility
        name: Object name

    Returns:
        The created eye cluster object
    """
    # Ensure node group exists
    node_group = create_distribution_node_group()

    # Create a new mesh object
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Add geometry nodes modifier
    modifier = obj.modifiers.new(name="GeometryNodes", type='NODES')
    modifier.node_group = node_group

    # Set input values (socket indices may vary)
    # We need to find the correct socket indices
    input_indices = {}
    for i, item in enumerate(node_group.interface.items_tree):
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            input_indices[item.name] = i

    # Set values using identifier
    if 'Eye Count' in input_indices:
        modifier[input_indices['Eye Count']] = count
    if 'Distribution Radius' in input_indices:
        modifier[input_indices['Distribution Radius']] = radius
    if 'Size Min' in input_indices:
        modifier[input_indices['Size Min']] = size_min
    if 'Size Max' in input_indices:
        modifier[input_indices['Size Max']] = size_max
    if 'Seed' in input_indices:
        modifier[input_indices['Seed']] = seed

    return obj


def create_poison_disk_distribution(
    count: int,
    radius: float,
    min_distance: float
) -> list:
    """
    Creates a Poisson disk distribution of points on a sphere.

    This gives more uniform spacing than random distribution.

    Args:
        count: Target number of points
        radius: Sphere radius
        min_distance: Minimum distance between points

    Returns:
        List of Vector positions
    """
    points = []
    attempts = 0
    max_attempts = count * 30

    while len(points) < count and attempts < max_attempts:
        # Generate random point on sphere
        theta = random.random() * 2 * 3.14159
        phi = random.random() * 3.14159

        x = radius * math.sin(phi) * math.cos(theta)
        y = radius * math.sin(phi) * math.sin(theta)
        z = radius * math.cos(phi)

        candidate = Vector((x, y, z))

        # Check minimum distance
        valid = True
        for existing in points:
            if (candidate - existing).length < min_distance:
                valid = False
                break

        if valid:
            points.append(candidate)

        attempts += 1

    return points


if __name__ == "__main__":
    # Test: Create eye cluster
    cluster = create_eyes_on_sphere(
        count=50,
        radius=5.0,
        size_min=0.2,
        size_max=0.8,
        seed=42,
        name="TestCluster"
    )
    print(f"Created eye cluster: {cluster.name}")
