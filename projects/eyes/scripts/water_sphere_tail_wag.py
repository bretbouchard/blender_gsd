"""
Water Sphere with Tail Wag Effect

Creates waves that emanate from a specific origin point.
At 0.2 origin, looks like a tail wagging at the bottom.
"""

import bpy
from mathutils import Vector
import math


def create_tail_wag_water_sphere():
    """Create water sphere with tail wag wave effect."""

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
    sphere.name = "TailWagWaterSphere"

    # Add Geometry Nodes modifier
    mod = sphere.modifiers.new(name="GeometryNodes", type='NODES')

    # Create node group
    node_group = bpy.data.node_groups.new("TailWagRipple", 'GeometryNodeTree')

    # Add input sockets
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Wave Frequency", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Amplitude", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Origin Z", in_out='INPUT', socket_type='NodeSocketFloat')  # -1 to 1
    node_group.interface.new_socket(name="Wave Spread", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Animation Speed", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Time", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Set defaults
    for item in node_group.interface.items_tree:
        if item.name == "Wave Frequency":
            item.default_value = 4.0
            item.min_value = 0.1
            item.max_value = 20.0
        elif item.name == "Wave Amplitude":
            item.default_value = 0.12
            item.min_value = 0.0
            item.max_value = 0.5
        elif item.name == "Wave Origin Z":
            item.default_value = 0.2  # Tail wag position
            item.min_value = -1.0
            item.max_value = 1.0
        elif item.name == "Wave Spread":
            item.default_value = 0.8
            item.min_value = 0.1
            item.max_value = 5.0
        elif item.name == "Animation Speed":
            item.default_value = 2.0
            item.min_value = 0.0
            item.max_value = 10.0
        elif item.name == "Time":
            item.default_value = 0.0

    mod.node_group = node_group

    nodes = node_group.nodes
    links = node_group.links

    # === INPUT/OUTPUT ===
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1400, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1600, 0)

    # === GET POSITION AND NORMAL ===
    pos_node = nodes.new('GeometryNodeInputPosition')
    pos_node.location = (-1200, 400)

    normal_node = nodes.new('GeometryNodeInputNormal')
    normal_node.location = (-1200, 100)

    # === SEPARATE XYZ ===
    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.location = (-1000, 400)
    links.new(pos_node.outputs['Position'], sep_xyz.inputs['Vector'])

    # === CALCULATE DISTANCE FROM ORIGIN POINT ===
    # Origin is at (0, 0, origin_z) on the sphere
    # Distance = sqrt(x² + y² + (z - origin_z)²)

    # Get X, Y, Z
    x_val = sep_xyz.outputs['X']
    y_val = sep_xyz.outputs['Y']
    z_val = sep_xyz.outputs['Z']

    # (z - origin_z)
    sub_origin = nodes.new('ShaderNodeMath')
    sub_origin.operation = 'SUBTRACT'
    sub_origin.label = "Z - Origin"
    sub_origin.location = (-1000, 200)
    links.new(z_val, sub_origin.inputs[0])
    links.new(input_node.outputs['Wave Origin Z'], sub_origin.inputs[1])

    # Square each component
    x_sq = nodes.new('ShaderNodeMath')
    x_sq.operation = 'MULTIPLY'
    x_sq.label = "X²"
    x_sq.location = (-800, 500)
    links.new(x_val, x_sq.inputs[0])
    links.new(x_val, x_sq.inputs[1])

    y_sq = nodes.new('ShaderNodeMath')
    y_sq.operation = 'MULTIPLY'
    y_sq.label = "Y²"
    y_sq.location = (-800, 350)
    links.new(y_val, y_sq.inputs[0])
    links.new(y_val, y_sq.inputs[1])

    z_minus_sq = nodes.new('ShaderNodeMath')
    z_minus_sq.operation = 'MULTIPLY'
    z_minus_sq.label = "(Z-O)²"
    z_minus_sq.location = (-800, 200)
    links.new(sub_origin.outputs[0], z_minus_sq.inputs[0])
    links.new(sub_origin.outputs[0], z_minus_sq.inputs[1])

    # Sum: x² + y²
    add_xy = nodes.new('ShaderNodeMath')
    add_xy.operation = 'ADD'
    add_xy.label = "X² + Y²"
    add_xy.location = (-600, 400)
    links.new(x_sq.outputs[0], add_xy.inputs[0])
    links.new(y_sq.outputs[0], add_xy.inputs[1])

    # Sum: (x² + y²) + (z-o)²
    add_all = nodes.new('ShaderNodeMath')
    add_all.operation = 'ADD'
    add_all.label = "Total"
    add_all.location = (-400, 350)
    links.new(add_xy.outputs[0], add_all.inputs[0])
    links.new(z_minus_sq.outputs[0], add_all.inputs[1])

    # Distance = sqrt(total)
    distance = nodes.new('ShaderNodeMath')
    distance.operation = 'SQRT'
    distance.label = "Distance"
    distance.location = (-200, 350)
    links.new(add_all.outputs[0], distance.inputs[0])

    # === CREATE WAVE ===
    # Wave = sin(distance * frequency + time * speed)

    # Distance × Frequency
    mult_freq = nodes.new('ShaderNodeMath')
    mult_freq.operation = 'MULTIPLY'
    mult_freq.label = "Dist × Freq"
    mult_freq.location = (0, 350)
    links.new(distance.outputs[0], mult_freq.inputs[0])
    links.new(input_node.outputs['Wave Frequency'], mult_freq.inputs[1])

    # Time × Speed
    time_speed = nodes.new('ShaderNodeMath')
    time_speed.operation = 'MULTIPLY'
    time_speed.label = "Time × Speed"
    time_speed.location = (-200, 0)
    links.new(input_node.outputs['Time'], time_speed.inputs[0])
    links.new(input_node.outputs['Animation Speed'], time_speed.inputs[1])

    # Add time
    add_time = nodes.new('ShaderNodeMath')
    add_time.operation = 'ADD'
    add_time.label = "+ Time"
    add_time.location = (200, 200)
    links.new(mult_freq.outputs[0], add_time.inputs[0])
    links.new(time_speed.outputs[0], add_time.inputs[1])

    # Sine wave
    sin_wave = nodes.new('ShaderNodeMath')
    sin_wave.operation = 'SINE'
    sin_wave.label = "Sine"
    sin_wave.location = (400, 200)
    links.new(add_time.outputs[0], sin_wave.inputs[0])

    # === FALLOFF FROM ORIGIN ===
    # Waves fade with distance: amplitude / (1 + distance/spread)

    dist_div_spread = nodes.new('ShaderNodeMath')
    dist_div_spread.operation = 'DIVIDE'
    dist_div_spread.label = "Dist / Spread"
    dist_div_spread.location = (0, 0)
    links.new(distance.outputs[0], dist_div_spread.inputs[0])
    links.new(input_node.outputs['Wave Spread'], dist_div_spread.inputs[1])

    add_one = nodes.new('ShaderNodeMath')
    add_one.operation = 'ADD'
    add_one.label = "+ 1"
    add_one.location = (200, 0)
    add_one.inputs[1].default_value = 1.0
    links.new(dist_div_spread.outputs[0], add_one.inputs[0])

    falloff = nodes.new('ShaderNodeMath')
    falloff.operation = 'DIVIDE'
    falloff.label = "1 / Falloff"
    falloff.location = (400, 0)
    falloff.inputs[0].default_value = 1.0
    links.new(add_one.outputs[0], falloff.inputs[1])

    # === APPLY FALLOFF TO WAVE ===
    wave_with_falloff = nodes.new('ShaderNodeMath')
    wave_with_falloff.operation = 'MULTIPLY'
    wave_with_falloff.label = "Wave × Falloff"
    wave_with_falloff.location = (600, 100)
    links.new(sin_wave.outputs[0], wave_with_falloff.inputs[0])
    links.new(falloff.outputs[0], wave_with_falloff.inputs[1])

    # === APPLY AMPLITUDE ===
    final_wave = nodes.new('ShaderNodeMath')
    final_wave.operation = 'MULTIPLY'
    final_wave.label = "× Amplitude"
    final_wave.location = (800, 100)
    links.new(wave_with_falloff.outputs[0], final_wave.inputs[0])
    links.new(input_node.outputs['Wave Amplitude'], final_wave.inputs[1])

    # === CREATE DISPLACEMENT ===
    disp_vec = nodes.new('ShaderNodeVectorMath')
    disp_vec.operation = 'MULTIPLY'
    disp_vec.label = "Displacement"
    disp_vec.location = (1000, 100)
    links.new(normal_node.outputs['Normal'], disp_vec.inputs[0])
    links.new(final_wave.outputs[0], disp_vec.inputs[1])

    # === SET POSITION ===
    set_pos = nodes.new('GeometryNodeSetPosition')
    set_pos.location = (1200, 200)
    links.new(input_node.outputs['Geometry'], set_pos.inputs['Geometry'])
    links.new(disp_vec.outputs['Vector'], set_pos.inputs['Offset'])

    # === OUTPUT ===
    links.new(set_pos.outputs['Geometry'], output_node.inputs['Geometry'])

    # === SET DEFAULT VALUES ===
    mod['Socket_1'] = 4.0   # Wave Frequency
    mod['Socket_2'] = 0.12  # Wave Amplitude
    mod['Socket_3'] = 0.2   # Wave Origin Z (tail wag position!)
    mod['Socket_4'] = 0.8   # Wave Spread
    mod['Socket_5'] = 2.0   # Animation Speed
    mod['Socket_6'] = 0.0   # Time

    # === CREATE ANIMATION ===
    scene = bpy.context.scene
    scene.frame_set(1)
    mod['Socket_6'] = 0.0
    mod.keyframe_insert(data_path='["Socket_6"]', frame=1)

    scene.frame_set(250)
    mod['Socket_6'] = 25.0
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

    output_mat = nodes_mat.new('ShaderNodeOutputMaterial')
    output_mat.location = (300, 0)
    links_mat.new(bsdf.outputs['BSDF'], output_mat.inputs['Surface'])

    sphere.data.materials.append(mat)

    # Save
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/tail_wag_water_sphere.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "="*70)
    print("TAIL WAG Water Sphere Created!")
    print("="*70)
    print("\n🎯 Wave Origin Z Controls:")
    print("  • 1.0  = North Pole (top)")
    print("  • 0.5  = Upper hemisphere")
    print("  • 0.2  = Lower-mid (TAIL WAG!)")
    print("  • 0.0  = Equator")
    print("  • -0.5 = Lower hemisphere")
    print("  • -1.0 = South Pole (bottom)")
    print()
    print("At 0.2, waves ripple outward like a tail wagging!")
    print()
    print("📊 Current Settings:")
    print("  • Frequency: 4.0 (nice ripples)")
    print("  • Amplitude: 0.12 (visible waves)")
    print("  • Origin Z: 0.2 (tail position)")
    print("  • Spread: 0.8 (focused near origin)")
    print("  • Speed: 2.0 (lively wag)")
    print()
    print(f"Vertices: {len(sphere.data.vertices)}")
    print(f"Saved to: {output_path}")
    print("\nPress SPACE to see the tail wag!")
    print("="*70 + "\n")

    return sphere


if __name__ == "__main__":
    create_tail_wag_water_sphere()
