"""
Bubble-Out Water Sphere

Sphere is flat/smooth ABOVE the wave origin.
Waves only appear BELOW the origin, rippling outward like bubbles.
"""

import bpy


def create_bubble_water_sphere():
    """Create water sphere with bubble-out effect - flat above origin."""

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
    sphere.name = "BubbleWaterSphere"

    # Add Geometry Nodes modifier
    mod = sphere.modifiers.new(name="GeometryNodes", type='NODES')

    # Create node group
    node_group = bpy.data.node_groups.new("BubbleRipple", 'GeometryNodeTree')

    # Add input sockets
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Wave Frequency", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Amplitude", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Origin Z", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Spread", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Animation Speed", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Time", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Set defaults
    for item in node_group.interface.items_tree:
        if item.name == "Wave Frequency":
            item.default_value = 5.0
        elif item.name == "Wave Amplitude":
            item.default_value = 0.15
        elif item.name == "Wave Origin Z":
            item.default_value = 0.2
        elif item.name == "Wave Spread":
            item.default_value = 0.6
        elif item.name == "Animation Speed":
            item.default_value = 2.0
        elif item.name == "Time":
            item.default_value = 0.0

    mod.node_group = node_group

    nodes = node_group.nodes
    links = node_group.links

    # === INPUT/OUTPUT ===
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1600, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1800, 0)

    # === GET POSITION AND NORMAL ===
    pos_node = nodes.new('GeometryNodeInputPosition')
    pos_node.location = (-1400, 400)

    normal_node = nodes.new('GeometryNodeInputNormal')
    normal_node.location = (-1400, 100)

    # === SEPARATE XYZ ===
    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.location = (-1200, 400)
    links.new(pos_node.outputs['Position'], sep_xyz.inputs['Vector'])

    # === CHECK IF BELOW ORIGIN (where waves happen) ===
    # If Z < Origin_Z, waves occur. If Z >= Origin_Z, no waves (flat).

    # Z - Origin
    z_minus_origin = nodes.new('ShaderNodeMath')
    z_minus_origin.operation = 'SUBTRACT'
    z_minus_origin.label = "Z - Origin"
    z_minus_origin.location = (-1200, 200)
    links.new(sep_xyz.outputs['Z'], z_minus_origin.inputs[0])
    links.new(input_node.outputs['Wave Origin Z'], z_minus_origin.inputs[1])

    # Is below origin? (Z - Origin < 0 means below)
    # Use Less Than to create mask
    below_origin = nodes.new('ShaderNodeMath')
    below_origin.operation = 'LESS_THAN'
    below_origin.label = "Below Origin?"
    below_origin.location = (-1000, 200)
    links.new(z_minus_origin.outputs[0], below_origin.inputs[0])
    below_origin.inputs[1].default_value = 0.0  # Compare to 0

    # === CALCULATE DISTANCE FROM ORIGIN POINT ===
    # Distance = sqrt(x² + y² + (z - origin_z)²)

    x_val = sep_xyz.outputs['X']
    y_val = sep_xyz.outputs['Y']

    # Square components
    x_sq = nodes.new('ShaderNodeMath')
    x_sq.operation = 'MULTIPLY'
    x_sq.label = "X²"
    x_sq.location = (-1000, 550)
    links.new(x_val, x_sq.inputs[0])
    links.new(x_val, x_sq.inputs[1])

    y_sq = nodes.new('ShaderNodeMath')
    y_sq.operation = 'MULTIPLY'
    y_sq.label = "Y²"
    y_sq.location = (-1000, 400)
    links.new(y_val, y_sq.inputs[0])
    links.new(y_val, y_sq.inputs[1])

    z_minus_sq = nodes.new('ShaderNodeMath')
    z_minus_sq.operation = 'MULTIPLY'
    z_minus_sq.label = "(Z-O)²"
    z_minus_sq.location = (-1000, 50)
    links.new(z_minus_origin.outputs[0], z_minus_sq.inputs[0])
    links.new(z_minus_origin.outputs[0], z_minus_sq.inputs[1])

    # Sum
    add_xy = nodes.new('ShaderNodeMath')
    add_xy.operation = 'ADD'
    add_xy.label = "X² + Y²"
    add_xy.location = (-800, 450)
    links.new(x_sq.outputs[0], add_xy.inputs[0])
    links.new(y_sq.outputs[0], add_xy.inputs[1])

    add_all = nodes.new('ShaderNodeMath')
    add_all.operation = 'ADD'
    add_all.label = "Total"
    add_all.location = (-600, 350)
    links.new(add_xy.outputs[0], add_all.inputs[0])
    links.new(z_minus_sq.outputs[0], add_all.inputs[1])

    # Distance
    distance = nodes.new('ShaderNodeMath')
    distance.operation = 'SQRT'
    distance.label = "Distance"
    distance.location = (-400, 350)
    links.new(add_all.outputs[0], distance.inputs[0])

    # === CREATE WAVE ===
    mult_freq = nodes.new('ShaderNodeMath')
    mult_freq.operation = 'MULTIPLY'
    mult_freq.label = "Dist × Freq"
    mult_freq.location = (-200, 350)
    links.new(distance.outputs[0], mult_freq.inputs[0])
    links.new(input_node.outputs['Wave Frequency'], mult_freq.inputs[1])

    time_speed = nodes.new('ShaderNodeMath')
    time_speed.operation = 'MULTIPLY'
    time_speed.label = "Time × Speed"
    time_speed.location = (-400, 0)
    links.new(input_node.outputs['Time'], time_speed.inputs[0])
    links.new(input_node.outputs['Animation Speed'], time_speed.inputs[1])

    add_time = nodes.new('ShaderNodeMath')
    add_time.operation = 'ADD'
    add_time.label = "+ Time"
    add_time.location = (0, 200)
    links.new(mult_freq.outputs[0], add_time.inputs[0])
    links.new(time_speed.outputs[0], add_time.inputs[1])

    sin_wave = nodes.new('ShaderNodeMath')
    sin_wave.operation = 'SINE'
    sin_wave.label = "Sine"
    sin_wave.location = (200, 200)
    links.new(add_time.outputs[0], sin_wave.inputs[0])

    # === FALLOFF ===
    dist_div_spread = nodes.new('ShaderNodeMath')
    dist_div_spread.operation = 'DIVIDE'
    dist_div_spread.label = "Dist / Spread"
    dist_div_spread.location = (-200, 0)
    links.new(distance.outputs[0], dist_div_spread.inputs[0])
    links.new(input_node.outputs['Wave Spread'], dist_div_spread.inputs[1])

    add_one = nodes.new('ShaderNodeMath')
    add_one.operation = 'ADD'
    add_one.label = "+ 1"
    add_one.location = (0, 0)
    add_one.inputs[1].default_value = 1.0
    links.new(dist_div_spread.outputs[0], add_one.inputs[0])

    falloff = nodes.new('ShaderNodeMath')
    falloff.operation = 'DIVIDE'
    falloff.label = "Falloff"
    falloff.location = (200, 0)
    falloff.inputs[0].default_value = 1.0
    links.new(add_one.outputs[0], falloff.inputs[1])

    # === COMBINE WAVE × FALLOFF ===
    wave_falloff = nodes.new('ShaderNodeMath')
    wave_falloff.operation = 'MULTIPLY'
    wave_falloff.label = "Wave × Falloff"
    wave_falloff.location = (400, 100)
    links.new(sin_wave.outputs[0], wave_falloff.inputs[0])
    links.new(falloff.outputs[0], wave_falloff.inputs[1])

    # === APPLY AMPLITUDE ===
    wave_amp = nodes.new('ShaderNodeMath')
    wave_amp.operation = 'MULTIPLY'
    wave_amp.label = "× Amplitude"
    wave_amp.location = (600, 100)
    links.new(wave_falloff.outputs[0], wave_amp.inputs[0])
    links.new(input_node.outputs['Wave Amplitude'], wave_amp.inputs[1])

    # === MASK BY "BELOW ORIGIN" ===
    # Only apply waves where below_origin = 1 (true)
    wave_masked = nodes.new('ShaderNodeMath')
    wave_masked.operation = 'MULTIPLY'
    wave_masked.label = "Mask to Below"
    wave_masked.location = (800, 100)
    links.new(wave_amp.outputs[0], wave_masked.inputs[0])
    links.new(below_origin.outputs[0], wave_masked.inputs[1])

    # === CREATE DISPLACEMENT ===
    disp_vec = nodes.new('ShaderNodeVectorMath')
    disp_vec.operation = 'MULTIPLY'
    disp_vec.label = "Displacement"
    disp_vec.location = (1000, 100)
    links.new(normal_node.outputs['Normal'], disp_vec.inputs[0])
    links.new(wave_masked.outputs[0], disp_vec.inputs[1])

    # === SET POSITION ===
    set_pos = nodes.new('GeometryNodeSetPosition')
    set_pos.location = (1200, 200)
    links.new(input_node.outputs['Geometry'], set_pos.inputs['Geometry'])
    links.new(disp_vec.outputs['Vector'], set_pos.inputs['Offset'])

    # === OUTPUT ===
    links.new(set_pos.outputs['Geometry'], output_node.inputs['Geometry'])

    # === SET VALUES ===
    mod['Socket_1'] = 5.0   # Wave Frequency
    mod['Socket_2'] = 0.15  # Wave Amplitude
    mod['Socket_3'] = 0.2   # Wave Origin Z
    mod['Socket_4'] = 0.6   # Wave Spread
    mod['Socket_5'] = 2.0   # Animation Speed
    mod['Socket_6'] = 0.0   # Time

    # === ANIMATION ===
    scene = bpy.context.scene
    scene.frame_set(1)
    mod['Socket_6'] = 0.0
    mod.keyframe_insert(data_path='["Socket_6"]', frame=1)

    scene.frame_set(250)
    mod['Socket_6'] = 25.0
    mod.keyframe_insert(data_path='["Socket_6"]', frame=250)

    scene.frame_start = 1
    scene.frame_end = 250

    # Camera
    bpy.ops.object.camera_add(location=(0, -8, 2))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.2, 0, 0)
    scene.camera = camera

    # Light
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 2.0

    # Material
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
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/bubble_water_sphere.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "="*70)
    print("BUBBLE Water Sphere Created!")
    print("="*70)
    print("\n🎯 Key Feature:")
    print("  • Sphere is FLAT above the wave origin")
    print("  • Waves only bubble out BELOW the origin")
    print("  • Like bubbles emerging from a specific point")
    print()
    print("📊 Wave Origin Z positions:")
    print("  • 0.2 = Current (lower-mid bubble)")
    print("  • 0.0 = Equator (half flat, half waves)")
    print("  • 0.5 = Upper (most of sphere flat)")
    print("  • -0.3 = Lower (waves from bottom)")
    print()
    print(f"Saved to: {output_path}")
    print("\nPress SPACE to see bubbles emerge!")
    print("="*70 + "\n")

    return sphere


if __name__ == "__main__":
    create_bubble_water_sphere()
