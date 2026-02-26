"""
FAST Water Sphere - No Subdivision Recalculation

Key insight: Subdivision Surface recalculation every frame is the bottleneck.
Solution: Create base mesh at high resolution ONCE, then only displace vertices.
This should give 60+ FPS easily.
"""

import bpy
from bpy.types import GeometryNodeTree
from mathutils import Vector
import math


def create_fast_water_sphere_node_group(name: str = "FastWaterSphere") -> GeometryNodeTree:
    """
    Creates a FAST Geometry Node group for water sphere.
    NO subdivision - uses high-res base mesh instead.
    Only calculates displacement each frame (very fast).
    """
    # Remove old version if exists
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    # Create new geometry node group
    node_group = bpy.data.node_groups.new(name, 'GeometryNodeTree')

    # Create interface inputs - MUST include Geometry input first!
    inputs = [
        ("Geometry", 'NodeSocketGeometry', None, None, None),
        ("Size", 'NodeSocketFloat', 1.0, 0.01, 10.0),
        ("Wave Scale", 'NodeSocketFloat', 1.5, 0.1, 10.0),
        ("Wave Height", 'NodeSocketFloat', 0.05, 0.0, 0.5),
        ("Wind Speed", 'NodeSocketFloat', 0.3, 0.0, 5.0),
        ("Time", 'NodeSocketFloat', 0.0, 0.0, 100000.0),
    ]

    for input_name, socket_type, default, min_val, max_val in inputs:
        node_group.interface.new_socket(
            name=input_name,
            in_out='INPUT',
            socket_type=socket_type
        )
        # Only set defaults for numeric inputs
        if default is not None:
            for item in node_group.interface.items_tree:
                if item.item_type == 'SOCKET' and item.name == input_name:
                    item.default_value = default
                    item.min_value = min_val
                    item.max_value = max_val

    # Create interface outputs
    node_group.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    nodes = node_group.nodes
    links = node_group.links

    # === INPUT NODE ===
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1200, 0)

    # === INPUTS FOR DISPLACEMENT ===
    position = nodes.new('GeometryNodeInputPosition')
    position.location = (-1200, 200)

    normal = nodes.new('GeometryNodeInputNormal')
    normal.location = (-1200, -100)

    # === SEPARATE POSITION ===
    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.label = "Get X,Y,Z"
    sep_xyz.location = (-900, 200)
    links.new(position.outputs['Position'], sep_xyz.inputs['Vector'])

    # === WIND ANIMATION ===
    time_offset = nodes.new('ShaderNodeMath')
    time_offset.operation = 'MULTIPLY'
    time_offset.label = "Time * Wind"
    time_offset.location = (-900, 0)
    links.new(input_node.outputs['Time'], time_offset.inputs[0])
    links.new(input_node.outputs['Wind Speed'], time_offset.inputs[1])

    add_wind = nodes.new('ShaderNodeMath')
    add_wind.operation = 'ADD'
    add_wind.label = "Offset X"
    add_wind.location = (-700, 50)
    links.new(sep_xyz.outputs['X'], add_wind.inputs[0])
    links.new(time_offset.outputs[0], add_wind.inputs[1])

    # === SIMPLE SINE WAVE ===
    scale_wave = nodes.new('ShaderNodeMath')
    scale_wave.operation = 'MULTIPLY'
    scale_wave.label = "Scale"
    scale_wave.location = (-500, 50)
    links.new(add_wind.outputs[0], scale_wave.inputs[0])
    links.new(input_node.outputs['Wave Scale'], scale_wave.inputs[1])

    sin_wave = nodes.new('ShaderNodeMath')
    sin_wave.operation = 'SINE'
    sin_wave.label = "Sin"
    sin_wave.location = (-300, 50)
    links.new(scale_wave.outputs[0], sin_wave.inputs[0])

    # Y wave for 2D pattern
    scale_y = nodes.new('ShaderNodeMath')
    scale_y.operation = 'MULTIPLY'
    scale_y.label = "Scale Y"
    scale_y.location = (-500, -100)
    links.new(sep_xyz.outputs['Y'], scale_y.inputs[0])
    links.new(input_node.outputs['Wave Scale'], scale_y.inputs[1])

    sin_y = nodes.new('ShaderNodeMath')
    sin_y.operation = 'SINE'
    sin_y.label = "Sin Y"
    sin_y.location = (-300, -100)
    links.new(scale_y.outputs[0], sin_y.inputs[0])

    # Combine
    combine = nodes.new('ShaderNodeMath')
    combine.operation = 'ADD'
    combine.label = "Combine"
    combine.location = (-100, -25)
    links.new(sin_wave.outputs[0], combine.inputs[0])
    links.new(sin_y.outputs[0], combine.inputs[1])

    # Apply height
    mult_height = nodes.new('ShaderNodeMath')
    mult_height.operation = 'MULTIPLY'
    mult_height.label = "Height"
    mult_height.location = (100, -25)
    links.new(combine.outputs[0], mult_height.inputs[0])
    links.new(input_node.outputs['Wave Height'], mult_height.inputs[1])

    # === DISPLACEMENT ===
    displacement = nodes.new('ShaderNodeVectorMath')
    displacement.operation = 'MULTIPLY'
    displacement.label = "Displace"
    displacement.location = (300, -25)
    links.new(normal.outputs['Normal'], displacement.inputs[0])
    links.new(mult_height.outputs[0], displacement.inputs[1])

    # === NEW POSITION ===
    add_position = nodes.new('ShaderNodeVectorMath')
    add_position.operation = 'ADD'
    add_position.label = "New Pos"
    add_position.location = (500, 100)
    links.new(position.outputs['Position'], add_position.inputs[0])
    links.new(displacement.outputs['Vector'], add_position.inputs[1])

    # === SET POSITION ===
    set_position = nodes.new('GeometryNodeSetPosition')
    set_position.label = "Apply"
    set_position.location = (700, 100)
    links.new(input_node.outputs['Geometry'], set_position.inputs['Geometry'])  # Connect input geometry!
    links.new(add_position.outputs['Vector'], set_position.inputs['Position'])

    # === OUTPUT ===
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (900, 100)
    links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

    return node_group


def create_fast_water_sphere(
    size: float = 1.0,
    wave_scale: float = 1.5,
    wave_height: float = 0.05,
    wind_speed: float = 0.3,
    time: float = 0.0,
    segments: int = 64,  # Higher because NO subdivision
    rings: int = 48,
    location: Vector = None,
    name: str = "FastWaterSphere"
) -> bpy.types.Object:
    """Creates a FAST water sphere - no subdivision recalculation."""
    if location is None:
        location = Vector((0, 0, 0))

    node_group = create_fast_water_sphere_node_group()

    # Create UV Sphere manually with high resolution
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        radius=size,
        location=location
    )
    obj = bpy.context.active_object
    obj.name = name

    # Add geometry nodes modifier
    modifier = obj.modifiers.new(name="GeometryNodes", type='NODES')
    modifier.node_group = node_group

    # Set parameters (no segments/rings - those are baked into mesh)
    modifier['Socket_0'] = size
    modifier['Socket_1'] = wave_scale
    modifier['Socket_2'] = wave_height
    modifier['Socket_3'] = wind_speed
    modifier['Socket_4'] = time

    return obj


def animate_fast_sphere(obj: bpy.types.Object, start_frame: int = 1, end_frame: int = 250, speed: float = 0.2):
    """Animates the fast water sphere."""
    if not obj.modifiers:
        return

    modifier = obj.modifiers[0]
    if modifier.type != 'NODES':
        return

    time_socket = 'Socket_4'

    bpy.context.scene.frame_set(start_frame)
    modifier[time_socket] = 0.0
    modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=start_frame)

    bpy.context.scene.frame_set(end_frame)
    modifier[time_socket] = (end_frame - start_frame) * speed / 24.0
    modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=end_frame)


if __name__ == "__main__":
    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    sphere = create_fast_water_sphere(
        size=2.0,
        wave_scale=1.5,
        wave_height=0.06,
        wind_speed=0.25,
        time=0.0,
        segments=64,  # High-res base mesh
        rings=48,
        name="FastWaterSphere"
    )
    animate_fast_sphere(sphere, start_frame=1, end_frame=250, speed=0.15)

    # Get vertex count
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = sphere.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()

    print(f"\n✓ Created FAST water sphere: {sphere.name}")
    print(f"\nPerformance Optimizations:")
    print("  ✓ NO Subdivision Surface node (main bottleneck removed)")
    print("  ✓ High-res base mesh created ONCE")
    print("  ✓ Only vertex displacement calculated per frame")
    print(f"  ✓ Vertices: {len(mesh.vertices):,}")
    print(f"  ✓ Expected FPS: 60+ FPS")
    print("\nThe base mesh is 'baked' - only simple math on vertices each frame!")
