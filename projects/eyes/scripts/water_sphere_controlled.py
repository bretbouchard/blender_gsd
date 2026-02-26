"""
Controlled Water Sphere with Wave Parameters

Controls:
- Wave Frequency: How many waves (higher = more ripples)
- Wave Amplitude: How deep/tall waves are
- Wave Origin: Where waves start (0=equator, 1=north pole, -1=south pole)
- Wave Spread: How wide the wave pattern is
"""

import bpy
from mathutils import Vector
import math


def create_controlled_water_sphere():
    """Create water sphere with full wave controls."""

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create UV Sphere
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=64,
        ring_count=48,
        radius=2.0,
        location=(0, 0, 0)
    )
    sphere = bpy.context.active_object
    sphere.name = "ControlledWaterSphere"

    # Add Geometry Nodes modifier
    mod = sphere.modifiers.new(name="GeometryNodes", type='NODES')

    # Create node group
    node_group = bpy.data.node_groups.new("ControlledWaterRipple", 'GeometryNodeTree')

    # Add input sockets with clear names
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')

    # Wave controls
    node_group.interface.new_socket(name="Wave Frequency", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Amplitude", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Origin", in_out='INPUT', socket_type='NodeSocketFloat')  # 0 to 1
    node_group.interface.new_socket(name="Wave Spread", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Animation Speed", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Time", in_out='INPUT', socket_type='NodeSocketFloat')

    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Set defaults
    for item in node_group.interface.items_tree:
        if item.name == "Wave Frequency":
            item.default_value = 3.0
            item.min_value = 0.1
            item.max_value = 20.0
        elif item.name == "Wave Amplitude":
            item.default_value = 0.1
            item.min_value = 0.0
            item.max_value = 0.5
        elif item.name == "Wave Origin":
            item.default_value = 1.0  # Start at north pole
            item.min_value = -1.0
            item.max_value = 1.0
        elif item.name == "Wave Spread":
            item.default_value = 1.0
            item.min_value = 0.1
            item.max_value = 5.0
        elif item.name == "Animation Speed":
            item.default_value = 1.0
            item.min_value = 0.0
            item.max_value = 5.0
        elif item.name == "Time":
            item.default_value = 0.0

    mod.node_group = node_group

    nodes = node_group.nodes
    links = node_group.links

    # === INPUT/OUTPUT ===
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1200, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1400, 0)

    # === GET POSITION AND NORMAL ===
    pos_node = nodes.new('GeometryNodeInputPosition')
    pos_node.location = (-1000, 300)

    normal_node = nodes.new('GeometryNodeInputNormal')
    normal_node.location = (-1000, 0)

    # === SEPARATE XYZ ===
    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.location = (-800, 300)
    links.new(pos_node.outputs['Position'], sep_xyz.inputs['Vector'])

    # === CALCULATE DISTANCE FROM WAVE ORIGIN ===
    # Wave origin is on Z axis (0, 0, origin_z)
    # We calculate distance from this point

    # Get Z position
    z_pos = nodes.new('ShaderNodeSeparateXYZ')
    z_pos.label = "Get Z"
    z_pos.location = (-800, 150)
    links.new(pos_node.outputs['Position'], z_pos.inputs['Vector'])

    # Calculate distance from origin point on sphere
    # Distance = sqrt(x² + y² + (z - origin_z)²)
    # But we want distance ALONG sphere surface from origin latitude

    # Use angle from origin: theta = arccos(z/r) where r = sphere radius
    # Origin latitude = arccos(origin_value)

    # For simplicity: use Z coordinate relative to origin
    # Subtract origin (1.0 = top, -1.0 = bottom)
    sub_origin = nodes.new('ShaderNodeMath')
    sub_origin.operation = 'SUBTRACT'
    sub_origin.label = "Z - Origin"
    sub_origin.location = (-600, 150)
    links.new(z_pos.outputs['Z'], sub_origin.inputs[0])
    links.new(input_node.outputs['Wave Origin'], sub_origin.inputs[1])

    # Absolute distance from origin
    abs_dist = nodes.new('ShaderNodeMath')
    abs_dist.operation = 'ABSOLUTE'
    abs_dist.label = "Distance from Origin"
    abs_dist.location = (-400, 150)
    links.new(sub_origin.outputs[0], abs_dist.inputs[0])

    # === CREATE RADIAL WAVE PATTERN ===
    # Wave = sin(distance * frequency + time * speed)
    # This creates waves emanating from origin

    # Scale distance by frequency
    mult_freq = nodes.new('ShaderNodeMath')
    mult_freq.operation = 'MULTIPLY'
    mult_freq.label = "Distance × Frequency"
    mult_freq.location = (-200, 150)
    links.new(abs_dist.outputs[0], mult_freq.inputs[0])
    links.new(input_node.outputs['Wave Frequency'], mult_freq.inputs[1])

    # Add time for animation
    mult_speed = nodes.new('ShaderNodeMath')
    mult_speed.operation = 'MULTIPLY'
    mult_speed.label = "Time × Speed"
    mult_speed.location = (-400, -100)
    links.new(input_node.outputs['Time'], mult_speed.inputs[0])
    links.new(input_node.outputs['Animation Speed'], mult_speed.inputs[1])

    add_time = nodes.new('ShaderNodeMath')
    add_time.operation = 'ADD'
    add_time.label = "Add Animation"
    add_time.location = (-200, 0)
    links.new(mult_freq.outputs[0], add_time.inputs[0])
    links.new(mult_speed.outputs[0], add_time.inputs[1])

    # Sine wave
    sin_wave = nodes.new('ShaderNodeMath')
    sin_wave.operation = 'SINE'
    sin_wave.label = "Sine Wave"
    sin_wave.location = (0, 0)
    links.new(add_time.outputs[0], sin_wave.inputs[0])

    # === APPLY WAVE SPREAD ===
    # Spread affects how the wave amplitude falls off with distance
    # Higher spread = waves extend further from origin

    # Calculate falloff: 1 / (1 + distance/spread)
    div_spread = nodes.new('ShaderNodeMath')
    div_spread.operation = 'DIVIDE'
    div_spread.label = "Dist / Spread"
    div_spread.location = (-200, -200)
    links.new(abs_dist.outputs[0], div_spread.inputs[0])
    links.new(input_node.outputs['Wave Spread'], div_spread.inputs[1])

    add_one = nodes.new('ShaderNodeMath')
    add_one.operation = 'ADD'
    add_one.label = "+ 1"
    add_one.location = (0, -200)
    add_one.inputs[1].default_value = 1.0
    links.new(div_spread.outputs[0], add_one.inputs[0])

    invert_falloff = nodes.new('ShaderNodeMath')
    invert_falloff.operation = 'DIVIDE'
    invert_falloff.label = "1 / Falloff"
    invert_falloff.location = (200, -200)
    invert_falloff.inputs[0].default_value = 1.0
    links.new(add_one.outputs[0], invert_falloff.inputs[1])

    # === COMBINE WAVE AND FALLOFF ===
    mult_falloff = nodes.new('ShaderNodeMath')
    mult_falloff.operation = 'MULTIPLY'
    mult_falloff.label = "Wave × Falloff"
    mult_falloff.location = (200, 0)
    links.new(sin_wave.outputs[0], mult_falloff.inputs[0])
    links.new(invert_falloff.outputs[0], mult_falloff.inputs[1])

    # === APPLY AMPLITUDE ===
    mult_amp = nodes.new('ShaderNodeMath')
    mult_amp.operation = 'MULTIPLY'
    mult_amp.label = "Apply Amplitude"
    mult_amp.location = (400, 0)
    links.new(mult_falloff.outputs[0], mult_amp.inputs[0])
    links.new(input_node.outputs['Wave Amplitude'], mult_amp.inputs[1])

    # === CREATE DISPLACEMENT VECTOR ===
    # Displace along normal
    disp_vec = nodes.new('ShaderNodeVectorMath')
    disp_vec.operation = 'MULTIPLY'
    disp_vec.label = "Displacement Vector"
    disp_vec.location = (600, 0)
    links.new(normal_node.outputs['Normal'], disp_vec.inputs[0])
    links.new(mult_amp.outputs[0], disp_vec.inputs[1])

    # === SET POSITION ===
    set_pos = nodes.new('GeometryNodeSetPosition')
    set_pos.location = (800, 200)
    links.new(input_node.outputs['Geometry'], set_pos.inputs['Geometry'])
    links.new(disp_vec.outputs['Vector'], set_pos.inputs['Offset'])

    # === OUTPUT ===
    links.new(set_pos.outputs['Geometry'], output_node.inputs['Geometry'])

    # === SET MODIFIER VALUES ===
    mod['Socket_1'] = 3.0   # Wave Frequency
    mod['Socket_2'] = 0.1   # Wave Amplitude
    mod['Socket_3'] = 1.0   # Wave Origin (north pole)
    mod['Socket_4'] = 1.0   # Wave Spread
    mod['Socket_5'] = 1.0   # Animation Speed
    mod['Socket_6'] = 0.0   # Time

    # === CREATE ANIMATION ===
    scene = bpy.context.scene
    scene.frame_set(1)
    mod['Socket_6'] = 0.0
    mod.keyframe_insert(data_path='["Socket_6"]', frame=1)

    scene.frame_set(250)
    mod['Socket_6'] = 20.0
    mod.keyframe_insert(data_path='["Socket_6"]', frame=250)

    # Setup scene
    scene.frame_start = 1
    scene.frame_end = 250

    # Add camera
    bpy.ops.object.camera_add(location=(0, -8, 2))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.2, 0, 0)
    scene.camera = camera

    # Add light
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 2.0

    # Create material
    mat = bpy.data.materials.new(name="Water")
    mat.use_nodes = True
    nodes_mat = mat.node_tree.nodes
    links_mat = mat.node_tree.links
    nodes_mat.clear()

    bsdf = nodes_mat.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.1, 0.3, 0.5, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.1
    bsdf.inputs['Metallic'].default_value = 0.0

    output_mat = nodes_mat.new('ShaderNodeOutputMaterial')
    output_mat.location = (300, 0)
    links_mat.new(bsdf.outputs['BSDF'], output_mat.inputs['Surface'])

    sphere.data.materials.append(mat)

    # Save
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/controlled_water_sphere.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "="*70)
    print("CONTROLLED Water Sphere Created!")
    print("="*70)
    print("\n📊 Wave Controls:")
    print("  • Wave Frequency (Socket_1): 3.0")
    print("    - Higher = more ripples")
    print("    - Lower = fewer, wider waves")
    print()
    print("  • Wave Amplitude (Socket_2): 0.1")
    print("    - How deep/tall the waves are")
    print("    - 0.05 = gentle, 0.2 = pronounced")
    print()
    print("  • Wave Origin (Socket_3): 1.0")
    print("    - WHERE waves start from")
    print("    - 1.0 = North Pole (top)")
    print("    - 0.5 = Mid-latitude")
    print("    - 0.0 = Equator")
    print("    - -1.0 = South Pole (bottom)")
    print()
    print("  • Wave Spread (Socket_4): 1.0")
    print("    - How far waves extend from origin")
    print("    - Higher = waves reach further")
    print()
    print("  • Animation Speed (Socket_5): 1.0")
    print("    - How fast waves move")
    print()
    print("  • Time (Socket_6): ANIMATED 0→20")
    print()
    print(f"Vertices: {len(sphere.data.vertices)}")
    print(f"Saved to: {output_path}")
    print("\nPress SPACE to play animation!")
    print("="*70 + "\n")

    return sphere


if __name__ == "__main__":
    create_controlled_water_sphere()
