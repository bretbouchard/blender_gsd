"""
Smooth Water Sphere - Calm Ball with Gentle Wind

Creates a smooth water sphere with gentle, rolling waves like
a calm ball of water with a steady wind. Uses sine waves instead
of noise for smoother, more predictable motion.
"""

import bpy
from bpy.types import GeometryNodeTree
from mathutils import Vector
import math


def create_smooth_water_sphere_node_group(name: str = "SmoothWaterSphere") -> GeometryNodeTree:
    """
    Creates a Geometry Node group for a smooth water sphere.
    Uses sine waves for gentle, rolling displacement instead of noise.
    """
    # Remove old version if exists
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    # Create new geometry node group
    node_group = bpy.data.node_groups.new(name, 'GeometryNodeTree')

    # Create interface inputs
    inputs = [
        ("Size", 'NodeSocketFloat', 1.0, 0.01, 10.0),
        ("Wave Scale", 'NodeSocketFloat', 1.0, 0.1, 10.0),
        ("Wave Height", 'NodeSocketFloat', 0.05, 0.0, 0.5),
        ("Wind Speed", 'NodeSocketFloat', 0.5, 0.0, 5.0),
        ("Time", 'NodeSocketFloat', 0.0, 0.0, 100000.0),
        ("Segments", 'NodeSocketInt', 64, 8, 256),
        ("Rings", 'NodeSocketInt', 48, 6, 128),
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
    input_node.location = (-1800, 0)

    # === CREATE BASE SPHERE ===
    sphere = nodes.new('GeometryNodeMeshUVSphere')
    sphere.label = "Water Sphere Base"
    sphere.location = (-1400, 300)
    links.new(input_node.outputs['Segments'], sphere.inputs['Segments'])
    links.new(input_node.outputs['Rings'], sphere.inputs['Rings'])
    links.new(input_node.outputs['Size'], sphere.inputs['Radius'])

    # === SUBDIVIDE SURFACE for smooth displacement ===
    subdiv = nodes.new('GeometryNodeSubdivisionSurface')
    subdiv.label = "Subdivide for Smoothness"
    subdiv.location = (-1100, 300)
    subdiv.inputs['Level'].default_value = 4  # Higher subdivision for smoother waves
    links.new(sphere.outputs['Mesh'], subdiv.inputs['Mesh'])

    # === INPUTS FOR DISPLACEMENT ===
    position = nodes.new('GeometryNodeInputPosition')
    position.location = (-1400, 0)

    normal = nodes.new('GeometryNodeInputNormal')
    normal.location = (-1400, -200)

    # === SEPARATE POSITION for spherical coordinates ===
    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.label = "Separate Position"
    sep_xyz.location = (-1100, 0)
    links.new(position.outputs['Position'], sep_xyz.inputs['Vector'])

    # === CALCULATE SPHERICAL COORDINATES ===
    # Distance from center (radius)
    length = nodes.new('ShaderNodeVectorMath')
    length.operation = 'LENGTH'
    length.label = "Radius"
    length.location = (-1100, -200)
    links.new(position.outputs['Position'], length.inputs[0])

    # === WIND DIRECTION DISPLACEMENT ===
    # Offset X position by time to create wind movement
    time_offset = nodes.new('ShaderNodeMath')
    time_offset.operation = 'MULTIPLY'
    time_offset.label = "Time * Wind Speed"
    time_offset.location = (-1100, 150)
    links.new(input_node.outputs['Time'], time_offset.inputs[0])
    links.new(input_node.outputs['Wind Speed'], time_offset.inputs[1])

    # Add time offset to X position
    add_wind = nodes.new('ShaderNodeMath')
    add_wind.operation = 'ADD'
    add_wind.label = "Add Wind to X"
    add_wind.location = (-900, 100)
    links.new(sep_xyz.outputs['X'], add_wind.inputs[0])
    links.new(time_offset.outputs[0], add_wind.inputs[1])

    # === PRIMARY WAVE - Large rolling waves ===
    # Scale position by wave scale
    scale_primary = nodes.new('ShaderNodeMath')
    scale_primary.operation = 'MULTIPLY'
    scale_primary.label = "Scale Primary Wave"
    scale_primary.location = (-700, 100)
    links.new(add_wind.outputs[0], scale_primary.inputs[0])
    links.new(input_node.outputs['Wave Scale'], scale_primary.inputs[1])

    # Also scale Y for 2D wave pattern
    scale_primary_y = nodes.new('ShaderNodeMath')
    scale_primary_y.operation = 'MULTIPLY'
    scale_primary_y.label = "Scale Y Primary"
    scale_primary_y.location = (-700, -50)
    links.new(sep_xyz.outputs['Y'], scale_primary_y.inputs[0])
    links.new(input_node.outputs['Wave Scale'], scale_primary_y.inputs[1])

    # Sine wave for smooth rolling motion
    sin_primary_x = nodes.new('ShaderNodeMath')
    sin_primary_x.operation = 'SINE'
    sin_primary_x.label = "Sin(Primary X)"
    sin_primary_x.location = (-500, 100)
    links.new(scale_primary.outputs[0], sin_primary_x.inputs[0])

    sin_primary_y = nodes.new('ShaderNodeMath')
    sin_primary_y.operation = 'SINE'
    sin_primary_y.label = "Sin(Primary Y)"
    sin_primary_y.location = (-500, -50)
    links.new(scale_primary_y.outputs[0], sin_primary_y.inputs[0])

    # Combine X and Y waves
    add_primary = nodes.new('ShaderNodeMath')
    add_primary.operation = 'ADD'
    add_primary.label = "Combine Primary Waves"
    add_primary.location = (-300, 25)
    links.new(sin_primary_x.outputs[0], add_primary.inputs[0])
    links.new(sin_primary_y.outputs[0], add_primary.inputs[1])

    # === SECONDARY WAVE - Smaller detail waves ===
    # Use different scale for variety
    scale_secondary_mult = nodes.new('ShaderNodeMath')
    scale_secondary_mult.operation = 'MULTIPLY'
    scale_secondary_mult.label = "Secondary Scale Mult"
    scale_secondary_mult.location = (-700, -300)
    scale_secondary_mult.inputs[1].default_value = 3.0
    links.new(input_node.outputs['Wave Scale'], scale_secondary_mult.inputs[0])

    scale_secondary_x = nodes.new('ShaderNodeMath')
    scale_secondary_x.operation = 'MULTIPLY'
    scale_secondary_x.label = "Scale Secondary X"
    scale_secondary_x.location = (-500, -300)
    links.new(add_wind.outputs[0], scale_secondary_x.inputs[0])
    links.new(scale_secondary_mult.outputs[0], scale_secondary_x.inputs[1])

    scale_secondary_y = nodes.new('ShaderNodeMath')
    scale_secondary_y.operation = 'MULTIPLY'
    scale_secondary_y.label = "Scale Secondary Y"
    scale_secondary_y.location = (-500, -400)
    links.new(sep_xyz.outputs['Y'], scale_secondary_y.inputs[0])
    links.new(scale_secondary_mult.outputs[0], scale_secondary_y.inputs[1])

    # Sine wave for secondary detail
    sin_secondary_x = nodes.new('ShaderNodeMath')
    sin_secondary_x.operation = 'SINE'
    sin_secondary_x.label = "Sin(Secondary X)"
    sin_secondary_x.location = (-300, -300)
    links.new(scale_secondary_x.outputs[0], sin_secondary_x.inputs[0])

    sin_secondary_y = nodes.new('ShaderNodeMath')
    sin_secondary_y.operation = 'SINE'
    sin_secondary_y.label = "Sin(Secondary Y)"
    sin_secondary_y.location = (-300, -400)
    links.new(scale_secondary_y.outputs[0], sin_secondary_y.inputs[1])

    # Combine secondary waves
    add_secondary = nodes.new('ShaderNodeMath')
    add_secondary.operation = 'ADD'
    add_secondary.label = "Combine Secondary Waves"
    add_secondary.location = (-100, -350)
    links.new(sin_secondary_x.outputs[0], add_secondary.inputs[0])
    links.new(sin_secondary_y.outputs[0], add_secondary.inputs[1])

    # Reduce secondary wave influence
    mult_secondary_weight = nodes.new('ShaderNodeMath')
    mult_secondary_weight.operation = 'MULTIPLY'
    mult_secondary_weight.label = "Secondary Weight"
    mult_secondary_weight.location = (100, -350)
    mult_secondary_weight.inputs[1].default_value = 0.3  # Subtle detail
    links.new(add_secondary.outputs[0], mult_secondary_weight.inputs[0])

    # === COMBINE ALL WAVES ===
    add_all_waves = nodes.new('ShaderNodeMath')
    add_all_waves.operation = 'ADD'
    add_all_waves.label = "Combine All Waves"
    add_all_waves.location = (300, -100)
    links.new(add_primary.outputs[0], add_all_waves.inputs[0])
    links.new(mult_secondary_weight.outputs[0], add_all_waves.inputs[1])

    # === APPLY WAVE HEIGHT ===
    mult_height = nodes.new('ShaderNodeMath')
    mult_height.operation = 'MULTIPLY'
    mult_height.label = "Apply Wave Height"
    mult_height.location = (500, -100)
    links.new(add_all_waves.outputs[0], mult_height.inputs[0])
    links.new(input_node.outputs['Wave Height'], mult_height.inputs[1])

    # === DISPLACEMENT ALONG NORMAL ===
    displacement = nodes.new('ShaderNodeVectorMath')
    displacement.operation = 'MULTIPLY'
    displacement.label = "Displacement Vector"
    displacement.location = (700, -100)
    links.new(normal.outputs['Normal'], displacement.inputs[0])
    links.new(mult_height.outputs[0], displacement.inputs[1])

    # === ADD DISPLACEMENT TO POSITION ===
    add_position = nodes.new('ShaderNodeVectorMath')
    add_position.operation = 'ADD'
    add_position.label = "New Position"
    add_position.location = (700, 150)
    links.new(position.outputs['Position'], add_position.inputs[0])
    links.new(displacement.outputs['Vector'], add_position.inputs[1])

    # === SET POSITION ON GEOMETRY ===
    set_position = nodes.new('GeometryNodeSetPosition')
    set_position.label = "Apply Smooth Waves"
    set_position.location = (900, 300)
    links.new(subdiv.outputs['Mesh'], set_position.inputs['Geometry'])
    links.new(add_position.outputs['Vector'], set_position.inputs['Position'])

    # === OUTPUT ===
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1100, 300)
    links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

    return node_group


def create_smooth_water_sphere(
    size: float = 1.0,
    wave_scale: float = 1.0,
    wave_height: float = 0.05,
    wind_speed: float = 0.5,
    time: float = 0.0,
    segments: int = 64,
    rings: int = 48,
    location: Vector = None,
    name: str = "SmoothWaterSphere"
) -> bpy.types.Object:
    """Creates a single smooth water sphere with gentle waves."""
    if location is None:
        location = Vector((0, 0, 0))

    node_group = create_smooth_water_sphere_node_group()

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


def animate_smooth_water_sphere(obj: bpy.types.Object, start_frame: int = 1, end_frame: int = 250, speed: float = 1.0):
    """Animates the time input of a smooth water sphere for gentle wave motion."""
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

    sphere = create_smooth_water_sphere(
        size=2.0,
        wave_scale=1.5,      # Moderate wave frequency
        wave_height=0.08,    # Gentle wave height
        wind_speed=0.3,      # Slow, steady wind
        time=0.0,
        segments=64,         # Higher resolution for smoothness
        rings=48,
        name="SmoothWaterSphere"
    )
    animate_smooth_water_sphere(sphere, start_frame=1, end_frame=250, speed=0.2)
    print(f"Created smooth water sphere: {sphere.name}")
    print("\nParameters:")
    print(f"  - Wave Scale: 1.5 (gentle rolling waves)")
    print(f"  - Wave Height: 0.08 (subtle displacement)")
    print(f"  - Wind Speed: 0.3 (slow, steady motion)")
    print(f"  - Segments/Rings: 64/48 (smooth surface)")
