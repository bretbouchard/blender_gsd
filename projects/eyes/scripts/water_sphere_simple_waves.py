"""
Simple Visible Waves - No falloff killing the effect

Creates waves that are actually VISIBLE with:
- No aggressive falloff
- Higher amplitude
- Clear ripple pattern
"""

import bpy


def create_simple_waves_sphere():
    """Create sphere with simple, visible waves."""

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
    sphere.name = "SimpleWavesSphere"

    # Add Geometry Nodes modifier
    mod = sphere.modifiers.new(name="GeometryNodes", type='NODES')

    # Create node group
    node_group = bpy.data.node_groups.new("SimpleWaves", 'GeometryNodeTree')

    # Add input sockets
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Num Waves", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Amplitude", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Origin Z", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Speed", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Time", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Set defaults
    for item in node_group.interface.items_tree:
        if item.name == "Num Waves":
            item.default_value = 10.0
        elif item.name == "Amplitude":
            item.default_value = 0.5
        elif item.name == "Origin Z":
            item.default_value = 0.6
        elif item.name == "Speed":
            item.default_value = 1.0
        elif item.name == "Time":
            item.default_value = 0.0

    mod.node_group = node_group

    nodes = node_group.nodes
    links = node_group.links

    # === INPUT/OUTPUT ===
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1200, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1000, 0)

    # === GET POSITION AND NORMAL ===
    pos_node = nodes.new('GeometryNodeInputPosition')
    pos_node.location = (-1000, 200)

    normal_node = nodes.new('GeometryNodeInputNormal')
    normal_node.location = (-1000, -100)

    # === SEPARATE XYZ ===
    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.location = (-800, 200)
    links.new(pos_node.outputs['Position'], sep_xyz.inputs['Vector'])

    # === MASK: Only apply waves BELOW origin Z ===
    below_mask = nodes.new('ShaderNodeMath')
    below_mask.operation = 'LESS_THAN'
    below_mask.label = "Below Origin?"
    below_mask.location = (-600, 0)
    links.new(sep_xyz.outputs['Z'], below_mask.inputs[0])
    links.new(input_node.outputs['Origin Z'], below_mask.inputs[1])

    # === CALCULATE DISTANCE FROM ORIGIN POINT ===
    # Distance = sqrt(x² + y² + (z - origin_z)²)

    # Z - Origin
    z_minus = nodes.new('ShaderNodeMath')
    z_minus.operation = 'SUBTRACT'
    z_minus.location = (-800, 0)
    links.new(sep_xyz.outputs['Z'], z_minus.inputs[0])
    links.new(input_node.outputs['Origin Z'], z_minus.inputs[1])

    # Build distance calculation
    # Use Vector Math for length
    vec_sub = nodes.new('ShaderNodeVectorMath')
    vec_sub.operation = 'SUBTRACT'
    vec_sub.label = "Pos - Origin"
    vec_sub.location = (-600, 200)
    # Create vector (0, 0, origin_z)
    vec_sub.inputs[1].default_value = (0, 0, 0.6)  # Will be overridden
    links.new(pos_node.outputs['Position'], vec_sub.inputs[0])

    # Actually we need to set the origin point dynamically
    # Let's do it differently - just use the Z distance as the main driver

    # Simple approach: distance along sphere from origin
    # Use (z - origin) as primary distance measure
    abs_z_dist = nodes.new('ShaderNodeMath')
    abs_z_dist.operation = 'ABSOLUTE'
    abs_z_dist.label = "Distance from Origin"
    abs_z_dist.location = (-400, 0)
    links.new(z_minus.outputs[0], abs_z_dist.inputs[0])

    # === CREATE WAVE PATTERN ===
    # Wave = sin(distance * num_waves + time * speed)

    # Distance × Num Waves
    mult_freq = nodes.new('ShaderNodeMath')
    mult_freq.operation = 'MULTIPLY'
    mult_freq.label = "Dist × Waves"
    mult_freq.location = (-200, 0)
    links.new(abs_z_dist.outputs[0], mult_freq.inputs[0])
    links.new(input_node.outputs['Num Waves'], mult_freq.inputs[1])

    # Time × Speed
    time_speed = nodes.new('ShaderNodeMath')
    time_speed.operation = 'MULTIPLY'
    time_speed.label = "Time × Speed"
    time_speed.location = (-200, -200)
    links.new(input_node.outputs['Time'], time_speed.inputs[0])
    links.new(input_node.outputs['Speed'], time_speed.inputs[1])

    # Add them
    add_time = nodes.new('ShaderNodeMath')
    add_time.operation = 'ADD'
    add_time.label = "+ Time"
    add_time.location = (0, -100)
    links.new(mult_freq.outputs[0], add_time.inputs[0])
    links.new(time_speed.outputs[0], add_time.inputs[1])

    # Sine wave
    sin_wave = nodes.new('ShaderNodeMath')
    sin_wave.operation = 'SINE'
    sin_wave.label = "Sine"
    sin_wave.location = (200, -100)
    links.new(add_time.outputs[0], sin_wave.inputs[0])

    # === APPLY AMPLITUDE ===
    mult_amp = nodes.new('ShaderNodeMath')
    mult_amp.operation = 'MULTIPLY'
    mult_amp.label = "× Amplitude"
    mult_amp.location = (400, -100)
    links.new(sin_wave.outputs[0], mult_amp.inputs[0])
    links.new(input_node.outputs['Amplitude'], mult_amp.inputs[1])

    # === APPLY MASK (only below origin) ===
    apply_mask = nodes.new('ShaderNodeMath')
    apply_mask.operation = 'MULTIPLY'
    apply_mask.label = "Mask"
    apply_mask.location = (600, -100)
    links.new(mult_amp.outputs[0], apply_mask.inputs[0])
    links.new(below_mask.outputs[0], apply_mask.inputs[1])

    # === CREATE DISPLACEMENT ===
    disp_vec = nodes.new('ShaderNodeVectorMath')
    disp_vec.operation = 'MULTIPLY'
    disp_vec.label = "Displacement"
    disp_vec.location = (600, 100)
    links.new(normal_node.outputs['Normal'], disp_vec.inputs[0])
    links.new(apply_mask.outputs[0], disp_vec.inputs[1])

    # === SET POSITION ===
    set_pos = nodes.new('GeometryNodeSetPosition')
    set_pos.location = (800, 100)
    links.new(input_node.outputs['Geometry'], set_pos.inputs['Geometry'])
    links.new(disp_vec.outputs['Vector'], set_pos.inputs['Offset'])

    # === OUTPUT ===
    links.new(set_pos.outputs['Geometry'], output_node.inputs['Geometry'])

    # === SET VALUES ===
    mod['Socket_1'] = 10.0  # Num Waves
    mod['Socket_2'] = 0.5   # Amplitude
    mod['Socket_3'] = 0.6   # Origin Z
    mod['Socket_4'] = 1.0   # Speed
    mod['Socket_5'] = 0.0   # Time

    # === CREATE ANIMATION ===
    scene = bpy.context.scene
    scene.frame_set(1)
    mod['Socket_5'] = 0.0
    mod.keyframe_insert(data_path='["Socket_5"]', frame=1)

    scene.frame_set(250)
    mod['Socket_5'] = 30.0
    mod.keyframe_insert(data_path='["Socket_5"]', frame=250)

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
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/simple_waves_sphere.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "="*70)
    print("SIMPLE WAVES Sphere Created!")
    print("="*70)
    print("\nKey differences:")
    print("  • NO falloff - waves don't fade with distance")
    print("  • Higher default amplitude (0.5)")
    print("  • Simpler math - easier to see what's happening")
    print()
    print("Settings:")
    print("  • Num Waves: 10")
    print("  • Amplitude: 0.5")
    print("  • Origin Z: 0.6")
    print(f"\nSaved to: {output_path}")
    print("="*70 + "\n")

    return sphere


if __name__ == "__main__":
    create_simple_waves_sphere()
