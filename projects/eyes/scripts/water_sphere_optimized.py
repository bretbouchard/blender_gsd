"""
Optimized Smooth Water Sphere - Better Performance

Optimized for smooth playback (target 24+ FPS) while maintaining
calm, rolling wave appearance.
"""

import bpy
from bpy.types import GeometryNodeTree
from mathutils import Vector
import math


def create_optimized_water_sphere_node_group(name: str = "OptimizedWaterSphere") -> GeometryNodeTree:
    """
    Creates an optimized Geometry Node group for smooth water sphere.
    Uses simpler math and lower subdivision for better performance.
    """
    # Remove old version if exists
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    # Create new geometry node group
    node_group = bpy.data.node_groups.new(name, 'GeometryNodeTree')

    # Create interface inputs - optimized defaults
    inputs = [
        ("Size", 'NodeSocketFloat', 1.0, 0.01, 10.0),
        ("Wave Scale", 'NodeSocketFloat', 1.5, 0.1, 10.0),
        ("Wave Height", 'NodeSocketFloat', 0.05, 0.0, 0.5),
        ("Wind Speed", 'NodeSocketFloat', 0.3, 0.0, 5.0),
        ("Time", 'NodeSocketFloat', 0.0, 0.0, 100000.0),
        ("Segments", 'NodeSocketInt', 32, 8, 128),
        ("Rings", 'NodeSocketInt', 24, 6, 64),
    ]

    for input_name, socket_type, default, min_val, max_val in inputs:
        node_group.interface.new_socket(
            name=input_name,
            in_out='INPUT',
            socket_type=socket_type
        )
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
    input_node.location = (-1600, 0)

    # === CREATE BASE SPHERE ===
    sphere = nodes.new('GeometryNodeMeshUVSphere')
    sphere.label = "Water Sphere Base"
    sphere.location = (-1200, 300)
    links.new(input_node.outputs['Segments'], sphere.inputs['Segments'])
    links.new(input_node.outputs['Rings'], sphere.inputs['Rings'])
    links.new(input_node.outputs['Size'], sphere.inputs['Radius'])

    # === SUBDIVIDE SURFACE - Optimized level ===
    subdiv = nodes.new('GeometryNodeSubdivisionSurface')
    subdiv.label = "Subdivide (Optimized)"
    subdiv.location = (-900, 300)
    subdiv.inputs['Level'].default_value = 2  # Reduced from 4 to 2 for performance
    links.new(sphere.outputs['Mesh'], subdiv.inputs['Mesh'])

    # === INPUTS FOR DISPLACEMENT ===
    position = nodes.new('GeometryNodeInputPosition')
    position.location = (-1200, 0)

    normal = nodes.new('GeometryNodeInputNormal')
    normal.location = (-1200, -200)

    # === SEPARATE POSITION ===
    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.label = "Separate Position"
    sep_xyz.location = (-900, 0)
    links.new(position.outputs['Position'], sep_xyz.inputs['Vector'])

    # === WIND ANIMATION ===
    # Simplified: just offset X by time * wind_speed
    time_offset = nodes.new('ShaderNodeMath')
    time_offset.operation = 'MULTIPLY'
    time_offset.label = "Time * Wind"
    time_offset.location = (-900, -100)
    links.new(input_node.outputs['Time'], time_offset.inputs[0])
    links.new(input_node.outputs['Wind Speed'], time_offset.inputs[1])

    add_wind = nodes.new('ShaderNodeMath')
    add_wind.operation = 'ADD'
    add_wind.label = "Add Wind"
    add_wind.location = (-700, -50)
    links.new(sep_xyz.outputs['X'], add_wind.inputs[0])
    links.new(time_offset.outputs[0], add_wind.inputs[1])

    # === SINGLE SINE WAVE - Simplified for performance ===
    # Scale position
    scale_wave = nodes.new('ShaderNodeMath')
    scale_wave.operation = 'MULTIPLY'
    scale_wave.label = "Scale Wave"
    scale_wave.location = (-500, -50)
    links.new(add_wind.outputs[0], scale_wave.inputs[0])
    links.new(input_node.outputs['Wave Scale'], scale_wave.inputs[1])

    # Sine wave
    sin_wave = nodes.new('ShaderNodeMath')
    sin_wave.operation = 'SINE'
    sin_wave.label = "Sin Wave"
    sin_wave.location = (-300, -50)
    links.new(scale_wave.outputs[0], sin_wave.inputs[0])

    # Add Y component for 2D waves
    scale_y = nodes.new('ShaderNodeMath')
    scale_y.operation = 'MULTIPLY'
    scale_y.label = "Scale Y"
    scale_y.location = (-500, -200)
    links.new(sep_xyz.outputs['Y'], scale_y.inputs[0])
    links.new(input_node.outputs['Wave Scale'], scale_y.inputs[1])

    sin_y = nodes.new('ShaderNodeMath')
    sin_y.operation = 'SINE'
    sin_y.label = "Sin Y"
    sin_y.location = (-300, -200)
    links.new(scale_y.outputs[0], sin_y.inputs[1])

    # Combine X and Y waves
    combine_waves = nodes.new('ShaderNodeMath')
    combine_waves.operation = 'ADD'
    combine_waves.label = "Combine Waves"
    combine_waves.location = (-100, -125)
    links.new(sin_wave.outputs[0], combine_waves.inputs[0])
    links.new(sin_y.outputs[0], combine_waves.inputs[1])

    # === APPLY WAVE HEIGHT ===
    mult_height = nodes.new('ShaderNodeMath')
    mult_height.operation = 'MULTIPLY'
    mult_height.label = "Wave Height"
    mult_height.location = (100, -125)
    links.new(combine_waves.outputs[0], mult_height.inputs[0])
    links.new(input_node.outputs['Wave Height'], mult_height.inputs[1])

    # === DISPLACEMENT ALONG NORMAL ===
    displacement = nodes.new('ShaderNodeVectorMath')
    displacement.operation = 'MULTIPLY'
    displacement.label = "Displacement"
    displacement.location = (300, -125)
    links.new(normal.outputs['Normal'], displacement.inputs[0])
    links.new(mult_height.outputs[0], displacement.inputs[1])

    # === ADD DISPLACEMENT TO POSITION ===
    add_position = nodes.new('ShaderNodeVectorMath')
    add_position.operation = 'ADD'
    add_position.label = "New Position"
    add_position.location = (300, 125)
    links.new(position.outputs['Position'], add_position.inputs[0])
    links.new(displacement.outputs['Vector'], add_position.inputs[1])

    # === SET POSITION ON GEOMETRY ===
    set_position = nodes.new('GeometryNodeSetPosition')
    set_position.label = "Apply Waves"
    set_position.location = (500, 300)
    links.new(subdiv.outputs['Mesh'], set_position.inputs['Geometry'])
    links.new(add_position.outputs['Vector'], set_position.inputs['Position'])

    # === OUTPUT ===
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (700, 300)
    links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

    return node_group


def create_optimized_water_sphere(
    size: float = 1.0,
    wave_scale: float = 1.5,
    wave_height: float = 0.05,
    wind_speed: float = 0.3,
    time: float = 0.0,
    segments: int = 32,
    rings: int = 24,
    location: Vector = None,
    name: str = "OptimizedWaterSphere"
) -> bpy.types.Object:
    """Creates an optimized smooth water sphere."""
    if location is None:
        location = Vector((0, 0, 0))

    node_group = create_optimized_water_sphere_node_group()

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    modifier = obj.modifiers.new(name="GeometryNodes", type='NODES')
    modifier.node_group = node_group

    modifier['Socket_0'] = size
    modifier['Socket_1'] = wave_scale
    modifier['Socket_2'] = wave_height
    modifier['Socket_3'] = wind_speed
    modifier['Socket_4'] = time
    modifier['Socket_5'] = segments
    modifier['Socket_6'] = rings

    obj.location = location
    return obj


def animate_optimized_sphere(obj: bpy.types.Object, start_frame: int = 1, end_frame: int = 250, speed: float = 0.2):
    """Animates the optimized water sphere."""
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

    sphere = create_optimized_water_sphere(
        size=2.0,
        wave_scale=1.5,
        wave_height=0.06,
        wind_speed=0.25,
        time=0.0,
        segments=32,
        rings=24,
        name="OptimizedWaterSphere"
    )
    animate_optimized_sphere(sphere, start_frame=1, end_frame=250, speed=0.15)
    print(f"Created optimized water sphere: {sphere.name}")
    print("\nOptimizations:")
    print("  - Subdivision level: 2 (was 4)")
    print("  - Base segments: 32 (was 80)")
    print("  - Base rings: 24 (was 60)")
    print("  - Single sine wave (was dual-layer)")
    print("  - Target: 24+ FPS playback")
