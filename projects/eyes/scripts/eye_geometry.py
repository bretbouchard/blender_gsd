"""
Eye Geometry - Nested Sphere Generation

Creates procedural eye geometry with nested spheres:
- Outer sphere (cornea)
- Middle sphere (iris)
- Inner sphere (pupil)
"""

import bpy
from bpy.types import GeometryNodeTree
from mathutils import Vector


def create_eye_node_group(name: str = "EyeGeometry") -> GeometryNodeTree:
    """
    Creates a Geometry Node group for a single eye with nested spheres.

    The eye consists of three concentric spheres:
    - Cornea (outer, transparent)
    - Iris (middle, colored)
    - Pupil (inner, dark)

    Inputs:
    - Size: Overall eye scale
    - Pupil Ratio: Pupil size relative to eye (0.0-1.0)
    - Iris Ratio: Iris size relative to eye (0.0-1.0)
    - Subdivisions: Sphere detail level

    Outputs:
    - Geometry: Combined nested spheres
    """
    # Check if node group already exists
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    # Create new geometry node group
    node_group = bpy.data.node_groups.new(name, 'GeometryNodeTree')

    # Create interface inputs
    node_group.interface.new_socket(
        name="Size",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    node_group.interface.new_socket(
        name="Pupil Ratio",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    node_group.interface.new_socket(
        name="Iris Ratio",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    node_group.interface.new_socket(
        name="Subdivisions",
        in_out='INPUT',
        socket_type='NodeSocketInt'
    )

    # Create interface outputs
    node_group.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    # Set default values
    for item in node_group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Size":
                item.default_value = 1.0
                item.min_value = 0.001
                item.max_value = 100.0
            elif item.name == "Pupil Ratio":
                item.default_value = 0.3
                item.min_value = 0.0
                item.max_value = 1.0
            elif item.name == "Iris Ratio":
                item.default_value = 0.6
                item.min_value = 0.0
                item.max_value = 1.0
            elif item.name == "Subdivisions":
                item.default_value = 2
                item.min_value = 0
                item.max_value = 6

    # Create nodes
    nodes = node_group.nodes

    # Input node
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    # Create UV Sphere for Cornea (outer)
    cornea_sphere = nodes.new('GeometryNodeMeshUVSphere')
    cornea_sphere.label = "Cornea (Outer)"
    cornea_sphere.location = (-400, 200)
    cornea_sphere.inputs['Segments'].default_value = 16
    cornea_sphere.inputs['Rings'].default_value = 8

    # Create UV Sphere for Iris (middle)
    iris_sphere = nodes.new('GeometryNodeMeshUVSphere')
    iris_sphere.label = "Iris (Middle)"
    iris_sphere.location = (-400, 0)
    iris_sphere.inputs['Segments'].default_value = 16
    iris_sphere.inputs['Rings'].default_value = 8

    # Create UV Sphere for Pupil (inner)
    pupil_sphere = nodes.new('GeometryNodeMeshUVSphere')
    pupil_sphere.label = "Pupil (Inner)"
    pupil_sphere.location = (-400, -200)
    pupil_sphere.inputs['Segments'].default_value = 16
    pupil_sphere.inputs['Rings'].default_value = 8

    # Subdivision surface nodes for smoothness
    cornea_subdiv = nodes.new('GeometryNodeSubdivisionSurface')
    cornea_subdiv.label = "Cornea Smooth"
    cornea_subdiv.location = (-100, 200)

    iris_subdiv = nodes.new('GeometryNodeSubdivisionSurface')
    iris_subdiv.label = "Iris Smooth"
    iris_subdiv.location = (-100, 0)

    pupil_subdiv = nodes.new('GeometryNodeSubdivisionSurface')
    pupil_subdiv.label = "Pupil Smooth"
    pupil_subdiv.location = (-100, -200)

    # Math nodes for size calculations
    multiply_size = nodes.new('ShaderNodeMath')
    multiply_size.operation = 'MULTIPLY'
    multiply_size.label = "Scale by Size"
    multiply_size.location = (-600, 200)

    multiply_iris = nodes.new('ShaderNodeMath')
    multiply_iris.operation = 'MULTIPLY'
    multiply_iris.label = "Iris Scale"
    multiply_iris.location = (-600, 100)

    multiply_pupil = nodes.new('ShaderNodeMath')
    multiply_pupil.operation = 'MULTIPLY'
    multiply_pupil.label = "Pupil Scale"
    multiply_pupil.location = (-600, 0)

    # Combine geometry
    join_geometry = nodes.new('GeometryNodeJoinGeometry')
    join_geometry.location = (200, 0)

    # Output node
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (400, 0)

    # Link nodes
    links = node_group.links

    # Size -> Cornea radius
    links.new(input_node.outputs['Size'], cornea_sphere.inputs['Radius'])

    # Size * Iris Ratio -> Iris radius
    links.new(input_node.outputs['Size'], multiply_iris.inputs[0])
    links.new(input_node.outputs['Iris Ratio'], multiply_iris.inputs[1])
    links.new(multiply_iris.outputs[0], iris_sphere.inputs['Radius'])

    # Size * Pupil Ratio -> Pupil radius
    links.new(input_node.outputs['Size'], multiply_pupil.inputs[0])
    links.new(input_node.outputs['Pupil Ratio'], multiply_pupil.inputs[1])
    links.new(multiply_pupil.outputs[0], pupil_sphere.inputs['Radius'])

    # Subdivisions to all subdivision nodes
    links.new(input_node.outputs['Subdivisions'], cornea_subdiv.inputs['Level'])
    links.new(input_node.outputs['Subdivisions'], iris_subdiv.inputs['Level'])
    links.new(input_node.outputs['Subdivisions'], pupil_subdiv.inputs['Level'])

    # Spheres to subdivision
    links.new(cornea_sphere.outputs['Mesh'], cornea_subdiv.inputs['Mesh'])
    links.new(iris_sphere.outputs['Mesh'], iris_subdiv.inputs['Mesh'])
    links.new(pupil_sphere.outputs['Mesh'], pupil_subdiv.inputs['Mesh'])

    # Subdivision to join
    links.new(cornea_subdiv.outputs['Mesh'], join_geometry.inputs['Geometry'])
    links.new(iris_subdiv.outputs['Mesh'], join_geometry.inputs['Geometry'])
    links.new(pupil_subdiv.outputs['Mesh'], join_geometry.inputs['Geometry'])

    # Join to output
    links.new(join_geometry.outputs['Geometry'], output_node.inputs['Geometry'])

    return node_group


def create_single_eye(
    size: float = 1.0,
    pupil_ratio: float = 0.3,
    iris_ratio: float = 0.6,
    subdivisions: int = 2,
    location: Vector = None,
    name: str = "Eye"
) -> bpy.types.Object:
    """
    Creates a single eye object with nested spheres.

    Args:
        size: Overall eye size
        pupil_ratio: Pupil size relative to eye
        iris_ratio: Iris size relative to eye
        subdivisions: Mesh detail level
        location: World position
        name: Object name

    Returns:
        The created eye object
    """
    if location is None:
        location = Vector((0, 0, 0))

    # Ensure node group exists
    node_group = create_eye_node_group()

    # Create a new mesh object
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Add geometry nodes modifier
    modifier = obj.modifiers.new(name="GeometryNodes", type='NODES')
    modifier.node_group = node_group

    # Set input values
    modifier['Socket_0'] = size      # Size
    modifier['Socket_1'] = pupil_ratio  # Pupil Ratio
    modifier['Socket_2'] = iris_ratio   # Iris Ratio
    modifier['Socket_3'] = subdivisions  # Subdivisions

    # Set location
    obj.location = location

    return obj


if __name__ == "__main__":
    # Test: Create a single eye
    eye = create_single_eye(
        size=2.0,
        pupil_ratio=0.3,
        iris_ratio=0.6,
        subdivisions=2,
        name="TestEye"
    )
    print(f"Created eye: {eye.name}")
