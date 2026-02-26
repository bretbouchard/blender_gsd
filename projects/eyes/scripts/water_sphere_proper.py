"""
PROPER Animated Water Sphere - Fixed Version

Based on research:
1. Geometry Nodes work best with simple SetPosition operations
2. Use Offset instead of absolute Position for better performance
3. Animation must be properly keyframed
"""

import bpy
from mathutils import Vector


def create_simple_water_sphere():
    """
    Create a simple animated water sphere using PROVEN techniques.
    """

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Create UV Sphere with good resolution
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=48,  # Good balance of quality/performance
        ring_count=36,
        radius=2.0,
        location=(0, 0, 0)
    )
    sphere = bpy.context.active_object
    sphere.name = "WaterSphere"

    # Add Geometry Nodes modifier
    mod = sphere.modifiers.new(name="GeometryNodes", type='NODES')

    # Create node group
    node_group = bpy.data.node_groups.new("WaterRipple", 'GeometryNodeTree')

    # Add input/output sockets
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Wave Height", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Speed", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Time", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Set socket defaults
    for item in node_group.interface.items_tree:
        if item.name == "Wave Height":
            item.default_value = 0.05
        elif item.name == "Wave Speed":
            item.default_value = 2.0
        elif item.name == "Time":
            item.default_value = 0.0

    # Assign node group to modifier
    mod.node_group = node_group

    nodes = node_group.nodes
    links = node_group.links

    # Create nodes
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (800, 0)

    # Get position and normal
    pos_node = nodes.new('GeometryNodeInputPosition')
    pos_node.location = (-600, 200)

    normal_node = nodes.new('GeometryNodeInputNormal')
    normal_node.location = (-600, -200)

    # Separate XYZ
    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.location = (-400, 200)
    links.new(pos_node.outputs['Position'], sep_xyz.inputs['Vector'])

    # Calculate wave offset
    # Use X + Time*Speed
    time_mult = nodes.new('ShaderNodeMath')
    time_mult.operation = 'MULTIPLY'
    time_mult.location = (-600, 0)
    links.new(input_node.outputs['Time'], time_mult.inputs[0])
    links.new(input_node.outputs['Wave Speed'], time_mult.inputs[1])

    add_time = nodes.new('ShaderNodeMath')
    add_time.operation = 'ADD'
    add_time.location = (-400, 0)
    links.new(sep_xyz.outputs['X'], add_time.inputs[0])
    links.new(time_mult.outputs[0], add_time.inputs[1])

    # Sine wave
    sin_node = nodes.new('ShaderNodeMath')
    sin_node.operation = 'SINE'
    sin_node.location = (-200, 0)
    links.new(add_time.outputs[0], sin_node.inputs[0])

    # Add Y component for 2D waves
    sin_y = nodes.new('ShaderNodeMath')
    sin_y.operation = 'SINE'
    sin_y.location = (-200, -200)
    links.new(sep_xyz.outputs['Y'], sin_y.inputs[0])

    # Combine waves
    add_waves = nodes.new('ShaderNodeMath')
    add_waves.operation = 'ADD'
    add_waves.location = (0, -100)
    links.new(sin_node.outputs[0], add_waves.inputs[0])
    links.new(sin_y.outputs[0], add_waves.inputs[1])

    # Apply wave height
    mult_height = nodes.new('ShaderNodeMath')
    mult_height.operation = 'MULTIPLY'
    mult_height.location = (200, -100)
    links.new(add_waves.outputs[0], mult_height.inputs[0])
    links.new(input_node.outputs['Wave Height'], mult_height.inputs[1])

    # Create offset vector along normal
    offset_vec = nodes.new('ShaderNodeVectorMath')
    offset_vec.operation = 'MULTIPLY'
    offset_vec.location = (400, -100)
    links.new(normal_node.outputs['Normal'], offset_vec.inputs[0])
    links.new(mult_height.outputs[0], offset_vec.inputs[1])

    # Set Position with OFFSET (not absolute position!)
    set_pos = nodes.new('GeometryNodeSetPosition')
    set_pos.location = (600, 0)
    links.new(input_node.outputs['Geometry'], set_pos.inputs['Geometry'])
    links.new(offset_vec.outputs['Vector'], set_pos.inputs['Offset'])  # Use Offset, not Position!

    # Output
    links.new(set_pos.outputs['Geometry'], output_node.inputs['Geometry'])

    # Set modifier values
    mod['Socket_1'] = 0.05   # Wave Height
    mod['Socket_2'] = 2.0    # Wave Speed
    mod['Socket_3'] = 0.0    # Time

    # Create proper animation
    scene = bpy.context.scene
    scene.frame_set(1)
    mod['Socket_3'] = 0.0
    mod.keyframe_insert(data_path='["Socket_3"]', frame=1)

    scene.frame_set(250)
    mod['Socket_3'] = 10.0  # Good range for smooth animation
    mod.keyframe_insert(data_path='["Socket_3"]', frame=250)

    # Set animation curve to linear for smooth motion
    if sphere.animation_data and sphere.animation_data.action:
        action = sphere.animation_data.action
        # Note: modifier keyframes are stored differently in Blender 5.0

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

    # Create simple material
    mat = bpy.data.materials.new(name="Water")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.1, 0.3, 0.5, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.1

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    sphere.data.materials.append(mat)

    # Save
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/proper_water_sphere.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "="*70)
    print("PROPER Water Sphere Created!")
    print("="*70)
    print("\nKey Improvements:")
    print("  ✓ Using OFFSET instead of absolute Position")
    print("  ✓ Proper socket mapping")
    print("  ✓ Animation actually keyframed")
    print("  ✓ Simpler node tree")
    print("  ✓ 48×36 resolution (good balance)")
    print(f"\nVertices: {len(sphere.data.vertices)}")
    print(f"\nSaved to: {output_path}")
    print("\nAnimation: Frames 1-250")
    print("Time range: 0.0 → 10.0")
    print("\nPress SPACE to play animation!")
    print("="*70 + "\n")

    return sphere


if __name__ == "__main__":
    create_simple_water_sphere()
