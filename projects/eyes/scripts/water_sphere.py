"""
Water Sphere with Wind-Driven Ripples - V3

Creates a single water sphere with procedural ripples that flow away
from the wind direction. Optimized for instancing thousands of spheres.

V3: Using Noise Texture for proper visible displacement
"""

import bpy
from bpy.types import GeometryNodeTree
from mathutils import Vector
import math


def create_water_sphere_node_group(name: str = "WaterSphere") -> GeometryNodeTree:
    """
    Creates a Geometry Node group for a water sphere with wind-driven ripples.
    Uses noise texture for visible, organic wave patterns.
    """
    # Remove old version if exists
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    # Create new geometry node group
    node_group = bpy.data.node_groups.new(name, 'GeometryNodeTree')

    # Create interface inputs
    inputs = [
        ("Size", 'NodeSocketFloat', 1.0, 0.01, 10.0),
        ("Ripple Scale", 'NodeSocketFloat', 2.0, 0.1, 20.0),
        ("Ripple Intensity", 'NodeSocketFloat', 0.2, 0.0, 1.0),
        ("Wind Angle", 'NodeSocketFloat', 0.0, -math.pi, math.pi),
        ("Wind Strength", 'NodeSocketFloat', 1.0, 0.0, 5.0),
        ("Time", 'NodeSocketFloat', 0.0, 0.0, 100000.0),
        ("Segments", 'NodeSocketInt', 48, 8, 128),
        ("Rings", 'NodeSocketInt', 32, 6, 64),
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
    sphere.location = (-1200, 200)
    links.new(input_node.outputs['Segments'], sphere.inputs['Segments'])
    links.new(input_node.outputs['Rings'], sphere.inputs['Rings'])
    links.new(input_node.outputs['Size'], sphere.inputs['Radius'])

    # === SUBDIVIDE SURFACE for smooth displacement ===
    subdiv = nodes.new('GeometryNodeSubdivisionSurface')
    subdiv.label = "Subdivide for Smoothness"
    subdiv.location = (-900, 200)
    subdiv.inputs['Level'].default_value = 3
    links.new(sphere.outputs['Mesh'], subdiv.inputs['Mesh'])

    # === INPUTS FOR DISPLACEMENT ===
    position = nodes.new('GeometryNodeInputPosition')
    position.location = (-1200, -100)

    normal = nodes.new('GeometryNodeInputNormal')
    normal.location = (-1200, -300)

    # === CREATE WIND-OFFSET POSITION ===
    # Offset position by time to animate the noise
    wind_offset = nodes.new('ShaderNodeVectorMath')
    wind_offset.operation = 'ADD'
    wind_offset.label = "Add Time Offset"
    wind_offset.location = (-900, -100)

    # Create time vector (Time * wind_strength in X direction)
    time_vec = nodes.new('ShaderNodeCombineXYZ')
    time_vec.label = "Time Vector"
    time_vec.location = (-1100, -200)
    links.new(input_node.outputs['Time'], time_vec.inputs['X'])
    # Scale time by wind strength
    wind_mult = nodes.new('ShaderNodeMath')
    wind_mult.operation = 'MULTIPLY'
    wind_mult.label = "Wind Speed"
    wind_mult.location = (-1300, -200)
    links.new(input_node.outputs['Wind Strength'], wind_mult.inputs[0])
    wind_mult.inputs[1].default_value = 0.5  # Reasonable animation speed
    links.new(wind_mult.outputs[0], time_vec.inputs['X'])

    links.new(position.outputs['Position'], wind_offset.inputs[0])
    links.new(time_vec.outputs['Vector'], wind_offset.inputs[1])

    # === SCALE POSITION BY RIPPLE SCALE ===
    # Divide position by scale so larger scale = larger waves
    scale_vec = nodes.new('ShaderNodeVectorMath')
    scale_vec.operation = 'SCALE'
    scale_vec.label = "Scale for Noise"
    scale_vec.location = (-700, -100)
    links.new(wind_offset.outputs['Vector'], scale_vec.inputs[0])
    # Invert ripple scale (1/scale) so higher value = more detail
    invert_scale = nodes.new('ShaderNodeMath')
    invert_scale.operation = 'DIVIDE'
    invert_scale.label = "Invert Scale"
    invert_scale.location = (-900, -250)
    invert_scale.inputs[0].default_value = 1.0
    links.new(input_node.outputs['Ripple Scale'], invert_scale.inputs[1])
    links.new(invert_scale.outputs[0], scale_vec.inputs['Scale'])

    # === NOISE TEXTURE for organic wave pattern ===
    noise1 = nodes.new('ShaderNodeTexNoise')
    noise1.label = "Primary Waves"
    noise1.location = (-500, -100)
    noise1.inputs['Scale'].default_value = 4.0
    noise1.inputs['Detail'].default_value = 8.0
    noise1.inputs['Roughness'].default_value = 0.5
    links.new(scale_vec.outputs['Vector'], noise1.inputs['Vector'])

    # Second noise layer for complexity
    noise2 = nodes.new('ShaderNodeTexNoise')
    noise2.label = "Secondary Detail"
    noise2.location = (-500, -350)
    noise2.inputs['Scale'].default_value = 12.0
    noise2.inputs['Detail'].default_value = 4.0
    noise2.inputs['Roughness'].default_value = 0.7
    # Use same scaled position but with different scale
    scale_vec2 = nodes.new('ShaderNodeVectorMath')
    scale_vec2.operation = 'SCALE'
    scale_vec2.label = "Scale for Detail"
    scale_vec2.location = (-700, -350)
    links.new(wind_offset.outputs['Vector'], scale_vec2.inputs[0])
    invert_scale2 = nodes.new('ShaderNodeMath')
    invert_scale2.operation = 'DIVIDE'
    invert_scale2.label = "Invert Scale 2"
    invert_scale2.location = (-900, -450)
    invert_scale2.inputs[0].default_value = 2.0  # Smaller = more detail
    links.new(input_node.outputs['Ripple Scale'], invert_scale2.inputs[1])
    links.new(invert_scale2.outputs[0], scale_vec2.inputs['Scale'])
    links.new(scale_vec2.outputs['Vector'], noise2.inputs['Vector'])

    # === COMBINE NOISE LAYERS ===
    # Weight primary more than secondary
    mult_primary = nodes.new('ShaderNodeMath')
    mult_primary.operation = 'MULTIPLY'
    mult_primary.label = "Primary Weight"
    mult_primary.location = (-300, -100)
    mult_primary.inputs[1].default_value = 0.7
    links.new(noise1.outputs['Fac'], mult_primary.inputs[0])

    mult_secondary = nodes.new('ShaderNodeMath')
    mult_secondary.operation = 'MULTIPLY'
    mult_secondary.label = "Secondary Weight"
    mult_secondary.location = (-300, -350)
    mult_secondary.inputs[1].default_value = 0.3
    links.new(noise2.outputs['Fac'], mult_secondary.inputs[0])

    add_noise = nodes.new('ShaderNodeMath')
    add_noise.operation = 'ADD'
    add_noise.label = "Combine Noise"
    add_noise.location = (-100, -225)
    links.new(mult_primary.outputs[0], add_noise.inputs[0])
    links.new(mult_secondary.outputs[0], add_noise.inputs[1])

    # === REMAP FROM [0,1] TO [-1,1] for inward/outward displacement ===
    # (value - 0.5) * 2 = value * 2 - 1
    remap_mult = nodes.new('ShaderNodeMath')
    remap_mult.operation = 'MULTIPLY'
    remap_mult.label = "Remap * 2"
    remap_mult.location = (100, -225)
    remap_mult.inputs[1].default_value = 2.0
    links.new(add_noise.outputs[0], remap_mult.inputs[0])

    remap_sub = nodes.new('ShaderNodeMath')
    remap_sub.operation = 'SUBTRACT'
    remap_sub.label = "Remap - 1"
    remap_sub.location = (300, -225)
    remap_sub.inputs[1].default_value = 1.0
    links.new(remap_mult.outputs[0], remap_sub.inputs[0])

    # === APPLY INTENSITY ===
    mult_intensity = nodes.new('ShaderNodeMath')
    mult_intensity.operation = 'MULTIPLY'
    mult_intensity.label = "Apply Intensity"
    mult_intensity.location = (500, -225)
    links.new(remap_sub.outputs[0], mult_intensity.inputs[0])
    links.new(input_node.outputs['Ripple Intensity'], mult_intensity.inputs[1])

    # === DISPLACEMENT ALONG NORMAL ===
    displacement = nodes.new('ShaderNodeVectorMath')
    displacement.operation = 'MULTIPLY'
    displacement.label = "Displacement Vector"
    displacement.location = (700, -225)
    links.new(normal.outputs['Normal'], displacement.inputs[0])
    links.new(mult_intensity.outputs[0], displacement.inputs[1])

    # === ADD DISPLACEMENT TO POSITION ===
    add_position = nodes.new('ShaderNodeVectorMath')
    add_position.operation = 'ADD'
    add_position.label = "New Position"
    add_position.location = (700, 50)
    links.new(position.outputs['Position'], add_position.inputs[0])
    links.new(displacement.outputs['Vector'], add_position.inputs[1])

    # === SET POSITION ON GEOMETRY ===
    set_position = nodes.new('GeometryNodeSetPosition')
    set_position.label = "Apply Ripples"
    set_position.location = (900, 200)
    links.new(subdiv.outputs['Mesh'], set_position.inputs['Geometry'])
    links.new(add_position.outputs['Vector'], set_position.inputs['Position'])

    # === OUTPUT ===
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1100, 200)
    links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

    return node_group


def create_single_water_sphere(
    size: float = 1.0,
    ripple_scale: float = 2.0,
    ripple_intensity: float = 0.2,
    wind_angle: float = 0.0,
    wind_strength: float = 1.0,
    time: float = 0.0,
    segments: int = 48,
    rings: int = 32,
    location: Vector = None,
    name: str = "WaterSphere"
) -> bpy.types.Object:
    """Creates a single water sphere with wind-driven ripples."""
    if location is None:
        location = Vector((0, 0, 0))

    node_group = create_water_sphere_node_group()

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    modifier = obj.modifiers.new(name="GeometryNodes", type='NODES')
    modifier.node_group = node_group

    modifier['Socket_0'] = size
    modifier['Socket_1'] = ripple_scale
    modifier['Socket_2'] = ripple_intensity
    modifier['Socket_3'] = wind_angle
    modifier['Socket_4'] = wind_strength
    modifier['Socket_5'] = time
    modifier['Socket_6'] = segments
    modifier['Socket_7'] = rings

    obj.location = location
    return obj


def animate_water_sphere(obj: bpy.types.Object, start_frame: int = 1, end_frame: int = 250, speed: float = 1.0):
    """Animates the time input of a water sphere for rippling effect."""
    if not obj.modifiers:
        return

    modifier = obj.modifiers[0]
    if modifier.type != 'NODES':
        return

    time_socket = 'Socket_5'

    bpy.context.scene.frame_set(start_frame)
    modifier[time_socket] = 0.0
    modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=start_frame)

    bpy.context.scene.frame_set(end_frame)
    modifier[time_socket] = (end_frame - start_frame) * speed / 24.0
    modifier.keyframe_insert(data_path=f'["{time_socket}"]', frame=end_frame)


if __name__ == "__main__":
    sphere = create_single_water_sphere(
        size=2.0,
        ripple_scale=2.0,
        ripple_intensity=0.2,
        wind_angle=0.0,
        time=0.0,
        segments=48,
        rings=32,
        name="TestWaterSphere"
    )
    animate_water_sphere(sphere, start_frame=1, end_frame=250, speed=0.5)
    print(f"Created water sphere: {sphere.name}")
