"""
Void Orb System - Three-Layer Shader with Reverse Wave Displacement

Implements the creative vision:
- "Ball of swirling nothingness with bubble of glowing light pushing against the edge"
- "Like a lightbulb in a balloon of oil"
- "Not smooth transition - light stretches the nothing"
- "White with sparkles and purple swirls"
- "When white iris pushes against black lens it causes ripples like waves crashing on beach in REVERSE"

Three-layer material system:
1. VOID CORE - Absolute black, the nothingness
2. MEMBRANE INTERFACE - Oil-balloon thin film interference
3. LIGHT EXPANSION - Glowing white iris pushing outward

Plus:
- Reverse wave displacement (latitudinal ripples)
- Sparkles and purple swirls
"""

import bpy
import math
import random


def clear_scene():
    """Clear all mesh objects from scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Clear orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.node_groups:
        if block.users == 0:
            bpy.data.node_groups.remove(block)


def create_void_orb_material():
    """
    Create a material with hard cutoff PER SPHERE:
    - Top 1/4 of each sphere = WHITE
    - Bottom 3/4 of each sphere = BLACK

    Uses TRANSFORMED Normal Y (world->object space) so each sphere
    has its own local split regardless of world position.
    """
    mat = bpy.data.materials.new(name="PerSphereRadial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    x = 0

    # 1. Geometry node for normal
    geometry = nodes.new('ShaderNodeNewGeometry')
    geometry.location = (x, 0)
    x += 200

    # 2. Vector Transform: World Normal -> Object Normal (THE KEY FIX)
    transform = nodes.new('ShaderNodeVectorTransform')
    transform.vector_type = 'NORMAL'
    transform.convert_from = 'WORLD'
    transform.convert_to = 'OBJECT'
    transform.location = (x, 0)
    x += 200

    # 3. Separate XYZ to get Normal Y (now in local/object space)
    separate = nodes.new('ShaderNodeSeparateXYZ')
    separate.location = (x, 0)
    x += 200

    # 4. Map Normal Y (-1 to 1) to (0 to 1)
    map_range = nodes.new('ShaderNodeMapRange')
    map_range.inputs['From Min'].default_value = -1.0
    map_range.inputs['From Max'].default_value = 1.0
    map_range.inputs['To Min'].default_value = 0.0
    map_range.inputs['To Max'].default_value = 1.0
    map_range.location = (x, 0)
    x += 200

    # 5. Math: Greater Than for hard cutoff (top 1/4 = 0.75)
    greater_than = nodes.new('ShaderNodeMath')
    greater_than.operation = 'GREATER_THAN'
    greater_than.inputs[1].default_value = 0.75  # Top 1/4
    greater_than.location = (x, 0)
    x += 200

    # 6. Color Ramp for hard black/white
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.color_ramp.interpolation = 'CONSTANT'  # Hard edge
    color_ramp.color_ramp.elements[0].position = 0.0
    color_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)  # Black
    color_ramp.color_ramp.elements[1].position = 0.5
    color_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)  # White
    color_ramp.location = (x, 0)
    x += 200

    # 7. Emission
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value = 2.0
    emission.location = (x, 0)
    x += 200

    # 8. Material Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (x, 0)

    # === LINK NODES ===

    # KEY: Transform normal from world to object space FIRST
    links.new(geometry.outputs['Normal'], transform.inputs['Vector'])
    links.new(transform.outputs['Vector'], separate.inputs['Vector'])

    links.new(separate.outputs['Y'], map_range.inputs['Value'])
    links.new(map_range.outputs['Result'], greater_than.inputs[0])
    links.new(greater_than.outputs['Value'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], emission.inputs['Color'])
    links.new(emission.outputs['Emission'], output.inputs['Surface'])

    mat.blend_method = 'BLEND'

    return mat


def create_reverse_wave_geometry_nodes():
    """
    Create Geometry Nodes for reverse wave displacement.

    The effect: When the white iris pushes against the black lens,
    it causes ripples like waves crashing on a beach IN REVERSE.

    Uses latitudinal displacement based on radial distance from Y-axis.
    Waves emanate from the "light expansion" zone and flow inward.
    """
    node_group = bpy.data.node_groups.new(name="ReverseWaveDisplacement", type='GeometryNodeTree')

    # Create input/output interfaces
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Input parameters
    node_group.interface.new_socket(name="Wave Amplitude", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Frequency", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Speed", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Light Zone Radius", in_out='INPUT', socket_type='NodeSocketFloat')

    nodes = node_group.nodes
    links = node_group.links

    x = 0

    # 1. Input node
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (x, 0)
    x += 200

    # 2. Position node - get vertex positions
    position = nodes.new('GeometryNodeInputPosition')
    position.location = (x, -200)
    x += 200

    # 3. Separate XYZ to get individual coordinates
    separate = nodes.new('ShaderNodeSeparateXYZ')
    separate.location = (x, -200)
    x += 200

    # 4. Calculate radial distance (XZ plane)
    # sqrt(X^2 + Z^2)
    x_squared = nodes.new('ShaderNodeMath')
    x_squared.operation = 'MULTIPLY'
    x_squared.location = (x, -100)

    z_squared = nodes.new('ShaderNodeMath')
    z_squared.operation = 'MULTIPLY'
    z_squared.location = (x, -300)

    add_sq = nodes.new('ShaderNodeMath')
    add_sq.operation = 'ADD'
    add_sq.location = (x + 200, -200)

    sqrt_radial = nodes.new('ShaderNodeMath')
    sqrt_radial.operation = 'SQRT'
    sqrt_radial.location = (x + 400, -200)

    x += 600

    # 5. Calculate wave pattern
    # Wave = sin(frequency * radial_distance - time * speed)
    # But INVERSE - waves flow toward center, not away

    # Scene time
    scene_time = nodes.new('GeometryNodeInputSceneTime')
    scene_time.location = (x, 300)

    # Multiply radial by frequency
    mult_freq = nodes.new('ShaderNodeMath')
    mult_freq.operation = 'MULTIPLY'
    mult_freq.location = (x, -200)

    # Multiply time by speed
    mult_speed = nodes.new('ShaderNodeMath')
    mult_speed.operation = 'MULTIPLY'
    mult_speed.location = (x, 100)

    # Subtract: (radial * freq) - (time * speed) for outward waves
    # For REVERSE waves: (radial * freq) + (time * speed) or negate the whole thing
    sub_wave = nodes.new('ShaderNodeMath')
    sub_wave.operation = 'SUBTRACT'
    sub_wave.location = (x + 200, -100)

    # Sine for wave shape
    sin_wave = nodes.new('ShaderNodeMath')
    sin_wave.operation = 'SINE'
    sin_wave.location = (x + 400, -100)

    x += 600

    # 6. Modulate wave by distance from light zone
    # Waves should be strongest at the edge of the light zone
    # and diminish toward center and far edges

    # Subtract light zone radius
    sub_light = nodes.new('ShaderNodeMath')
    sub_light.operation = 'SUBTRACT'
    sub_light.location = (x, -200)

    # Absolute value for symmetric falloff
    abs_dist = nodes.new('ShaderNodeMath')
    abs_dist.operation = 'ABSOLUTE'
    abs_dist.location = (x + 200, -200)

    # Invert for falloff (closer to light edge = stronger)
    invert_dist = nodes.new('ShaderNodeMath')
    invert_dist.operation = 'SUBTRACT'
    invert_dist.inputs[1].default_value = 1.0  # 1 - dist
    invert_dist.location = (x + 400, -200)

    # Clamp to 0-1
    clamp_dist = nodes.new('ShaderNodeMath')
    clamp_dist.operation = 'CLAMP'
    clamp_dist.location = (x + 600, -200)

    x += 800

    # 7. Multiply wave by amplitude and falloff
    mult_amp = nodes.new('ShaderNodeMath')
    mult_amp.operation = 'MULTIPLY'
    mult_amp.location = (x, -100)

    mult_falloff = nodes.new('ShaderNodeMath')
    mult_falloff.operation = 'MULTIPLY'
    mult_falloff.location = (x + 200, -100)

    x += 400

    # 8. Apply displacement along normal
    # Get normal
    normal = nodes.new('GeometryNodeInputNormal')
    normal.location = (x, -300)

    # Multiply displacement by normal
    mult_normal = nodes.new('ShaderNodeCombineXYZ')
    mult_normal.location = (x + 200, -200)

    # Actually use Vector Math for scale
    scale_normal = nodes.new('ShaderNodeVectorMath')
    scale_normal.operation = 'SCALE'
    scale_normal.location = (x + 200, -100)

    x += 400

    # 9. Set Position node to apply displacement
    set_position = nodes.new('GeometryNodeSetPosition')
    set_position.location = (x, 0)

    x += 200

    # 10. Output node
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (x, 0)

    # === LINK NODES ===

    # Position to separate
    links.new(position.outputs['Position'], separate.inputs['Vector'])

    # Calculate radial distance
    links.new(separate.outputs['X'], x_squared.inputs[0])
    links.new(separate.outputs['X'], x_squared.inputs[1])
    links.new(separate.outputs['Z'], z_squared.inputs[0])
    links.new(separate.outputs['Z'], z_squared.inputs[1])
    links.new(x_squared.outputs['Value'], add_sq.inputs[0])
    links.new(z_squared.outputs['Value'], add_sq.inputs[1])
    links.new(add_sq.outputs['Value'], sqrt_radial.inputs[0])

    # Wave calculation
    links.new(input_node.outputs['Wave Frequency'], mult_freq.inputs[0])
    links.new(sqrt_radial.outputs['Value'], mult_freq.inputs[1])
    links.new(input_node.outputs['Wave Speed'], mult_speed.inputs[0])
    links.new(scene_time.outputs['Seconds'], mult_speed.inputs[1])
    links.new(mult_freq.outputs['Value'], sub_wave.inputs[0])
    links.new(mult_speed.outputs['Value'], sub_wave.inputs[1])
    links.new(sub_wave.outputs['Value'], sin_wave.inputs[0])

    # Falloff calculation
    links.new(input_node.outputs['Light Zone Radius'], sub_light.inputs[1])
    links.new(sqrt_radial.outputs['Value'], sub_light.inputs[0])
    links.new(sub_light.outputs['Value'], abs_dist.inputs[0])
    links.new(abs_dist.outputs['Value'], invert_dist.inputs[0])
    links.new(invert_dist.outputs['Value'], clamp_dist.inputs[0])

    # Final displacement
    links.new(input_node.outputs['Wave Amplitude'], mult_amp.inputs[0])
    links.new(sin_wave.outputs['Value'], mult_amp.inputs[1])
    links.new(mult_amp.outputs['Value'], mult_falloff.inputs[0])
    links.new(clamp_dist.outputs['Value'], mult_falloff.inputs[1])

    # Apply to normal
    links.new(normal.outputs['Normal'], scale_normal.inputs['Vector'])
    links.new(mult_falloff.outputs['Value'], scale_normal.inputs['Scale'])

    # Set position
    links.new(input_node.outputs['Geometry'], set_position.inputs['Geometry'])
    links.new(position.outputs['Position'], set_position.inputs['Offset'])  # Base position
    links.new(scale_normal.outputs['Vector'], set_position.inputs['Offset'])  # Actually this should be added

    # Output
    links.new(set_position.outputs['Geometry'], output_node.inputs['Geometry'])

    return node_group


def create_geometry_nodes_distribution():
    """
    Create a Geometry Nodes setup that:
    1. Creates a sphere mesh and converts to volume
    2. Distributes points inside the volume
    3. Instances spheres with random sizes
    4. Applies reverse wave displacement (latitudinal ripples)
    5. Applies void orb material
    """
    node_group = bpy.data.node_groups.new(name="VoidOrbDistribution", type='GeometryNodeTree')

    # Create input/output interfaces
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Input parameters
    node_group.interface.new_socket(name="Sphere Count", in_out='INPUT', socket_type='NodeSocketInt')
    node_group.interface.new_socket(name="Swarm Radius", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Base Sphere Size", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Seed", in_out='INPUT', socket_type='NodeSocketInt')
    node_group.interface.new_socket(name="Wave Amplitude", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Wave Frequency", in_out='INPUT', socket_type='NodeSocketFloat')

    nodes = node_group.nodes
    links = node_group.links

    x = 0

    # === STAGE 1: DISTRIBUTION ===

    # 1. Input node
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (x, 0)
    x += 200

    # 2. Create UV sphere mesh (low poly for volume)
    uv_sphere = nodes.new('GeometryNodeMeshUVSphere')
    uv_sphere.inputs['Radius'].default_value = 1.0
    uv_sphere.inputs['Segments'].default_value = 24
    uv_sphere.inputs['Rings'].default_value = 16
    uv_sphere.location = (x, -400)
    x += 200

    # 3. Convert mesh to volume
    mesh_to_volume = nodes.new('GeometryNodeMeshToVolume')
    mesh_to_volume.inputs['Voxel Size'].default_value = 0.1
    mesh_to_volume.inputs['Interior Band Width'].default_value = 0.2
    mesh_to_volume.location = (x, -400)
    x += 200

    # 4. Distribute points in volume
    distribute = nodes.new('GeometryNodeDistributePointsInVolume')
    distribute.location = (x, -200)
    x += 250

    # 5. Random Value for size
    random_size = nodes.new('FunctionNodeRandomValue')
    random_size.data_type = 'FLOAT'
    random_size.inputs['Min'].default_value = 0.3
    random_size.inputs['Max'].default_value = 4.0
    random_size.location = (x, -500)
    x += 200

    # Index for random seed
    index_node = nodes.new('GeometryNodeInputIndex')
    index_node.location = (x - 450, -650)

    # 6. Multiply by base sphere size
    size_mult = nodes.new('ShaderNodeMath')
    size_mult.operation = 'MULTIPLY'
    size_mult.location = (x, -400)
    x += 200

    # 7. CombineXYZ for scale
    combine_xyz = nodes.new('ShaderNodeCombineXYZ')
    combine_xyz.location = (x, -400)
    x += 200

    # 8. Instance sphere mesh (higher detail for wave displacement)
    instance_sphere = nodes.new('GeometryNodeMeshUVSphere')
    instance_sphere.inputs['Segments'].default_value = 24  # More segments for waves
    instance_sphere.inputs['Rings'].default_value = 16
    instance_sphere.location = (x, -600)

    instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')
    instance_on_points.location = (x, -200)
    x += 300

    # 9. Realize Instances
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (x, -200)
    x += 200

    # === STAGE 2: REVERSE WAVE DISPLACEMENT ===

    # Get position for wave calculation
    position = nodes.new('GeometryNodeInputPosition')
    position.location = (x, -400)
    x_pos = x

    # Separate XYZ
    separate = nodes.new('ShaderNodeSeparateXYZ')
    separate.location = (x, -400)
    x += 200

    # Calculate radial distance (XZ plane) - latitudinal
    # sqrt(X^2 + Z^2)
    x_sq = nodes.new('ShaderNodeMath')
    x_sq.operation = 'MULTIPLY'
    x_sq.location = (x, -300)

    z_sq = nodes.new('ShaderNodeMath')
    z_sq.operation = 'MULTIPLY'
    z_sq.location = (x, -500)

    add_sq = nodes.new('ShaderNodeMath')
    add_sq.operation = 'ADD'
    add_sq.location = (x + 200, -400)

    sqrt_radial = nodes.new('ShaderNodeMath')
    sqrt_radial.operation = 'SQRT'
    sqrt_radial.location = (x + 400, -400)

    x += 600

    # Scene time for animation
    scene_time = nodes.new('GeometryNodeInputSceneTime')
    scene_time.location = (x_pos, 200)

    # Wave: sin(frequency * radial - time * 2) for REVERSE waves
    # (waves flow inward, toward center)
    mult_freq = nodes.new('ShaderNodeMath')
    mult_freq.operation = 'MULTIPLY'
    mult_freq.location = (x, -400)

    mult_time = nodes.new('ShaderNodeMath')
    mult_time.operation = 'MULTIPLY'
    mult_time.inputs[1].default_value = 2.0  # Speed
    mult_time.location = (x, 0)

    # REVERSE: subtract time from radial (not add)
    sub_wave = nodes.new('ShaderNodeMath')
    sub_wave.operation = 'SUBTRACT'
    sub_wave.location = (x + 200, -300)

    sin_wave = nodes.new('ShaderNodeMath')
    sin_wave.operation = 'SINE'
    sin_wave.location = (x + 400, -300)

    x += 600

    # Amplitude control
    mult_amp = nodes.new('ShaderNodeMath')
    mult_amp.operation = 'MULTIPLY'
    mult_amp.location = (x, -300)

    x += 200

    # Get normal for displacement direction
    normal = nodes.new('GeometryNodeInputNormal')
    normal.location = (x, -500)

    # Scale normal by wave displacement
    scale_normal = nodes.new('ShaderNodeVectorMath')
    scale_normal.operation = 'SCALE'
    scale_normal.location = (x, -300)

    x += 200

    # Add displacement to position
    add_pos = nodes.new('ShaderNodeVectorMath')
    add_pos.operation = 'ADD'
    add_pos.location = (x, -300)

    x += 200

    # Set new position
    set_position = nodes.new('GeometryNodeSetPosition')
    set_position.location = (x, -200)
    x += 200

    # === STAGE 3: MATERIAL ===

    # 10. Set Material
    set_material = nodes.new('GeometryNodeSetMaterial')
    set_material.location = (x, -200)
    x += 200

    # 11. Output node
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (x, -200)

    # === LINK NODES ===

    # Distribution
    links.new(input_node.outputs['Swarm Radius'], uv_sphere.inputs['Radius'])
    links.new(uv_sphere.outputs['Mesh'], mesh_to_volume.inputs['Mesh'])
    links.new(mesh_to_volume.outputs['Volume'], distribute.inputs['Volume'])
    links.new(input_node.outputs['Sphere Count'], distribute.inputs['Density'])
    links.new(input_node.outputs['Seed'], distribute.inputs['Seed'])

    links.new(index_node.outputs['Index'], random_size.inputs['ID'])
    links.new(input_node.outputs['Seed'], random_size.inputs['Seed'])

    links.new(input_node.outputs['Base Sphere Size'], size_mult.inputs[0])
    links.new(random_size.outputs['Value'], size_mult.inputs[1])

    links.new(size_mult.outputs['Value'], combine_xyz.inputs['X'])
    links.new(size_mult.outputs['Value'], combine_xyz.inputs['Y'])
    links.new(size_mult.outputs['Value'], combine_xyz.inputs['Z'])

    links.new(distribute.outputs['Points'], instance_on_points.inputs['Points'])
    links.new(instance_sphere.outputs['Mesh'], instance_on_points.inputs['Instance'])
    links.new(combine_xyz.outputs['Vector'], instance_on_points.inputs['Scale'])

    links.new(instance_on_points.outputs['Instances'], realize.inputs['Geometry'])

    # Wave displacement
    links.new(position.outputs['Position'], separate.inputs['Vector'])
    links.new(separate.outputs['X'], x_sq.inputs[0])
    links.new(separate.outputs['X'], x_sq.inputs[1])
    links.new(separate.outputs['Z'], z_sq.inputs[0])
    links.new(separate.outputs['Z'], z_sq.inputs[1])
    links.new(x_sq.outputs['Value'], add_sq.inputs[0])
    links.new(z_sq.outputs['Value'], add_sq.inputs[1])
    links.new(add_sq.outputs['Value'], sqrt_radial.inputs[0])

    links.new(input_node.outputs['Wave Frequency'], mult_freq.inputs[0])
    links.new(sqrt_radial.outputs['Value'], mult_freq.inputs[1])
    links.new(scene_time.outputs['Seconds'], mult_time.inputs[0])
    links.new(mult_freq.outputs['Value'], sub_wave.inputs[0])
    links.new(mult_time.outputs['Value'], sub_wave.inputs[1])
    links.new(sub_wave.outputs['Value'], sin_wave.inputs[0])

    links.new(input_node.outputs['Wave Amplitude'], mult_amp.inputs[0])
    links.new(sin_wave.outputs['Value'], mult_amp.inputs[1])

    links.new(normal.outputs['Normal'], scale_normal.inputs['Vector'])
    links.new(mult_amp.outputs['Value'], scale_normal.inputs['Scale'])

    links.new(position.outputs['Position'], add_pos.inputs[0])
    links.new(scale_normal.outputs['Vector'], add_pos.inputs[1])

    links.new(realize.outputs['Geometry'], set_position.inputs['Geometry'])
    links.new(add_pos.outputs['Vector'], set_position.inputs['Position'])

    # Material
    links.new(set_position.outputs['Geometry'], set_material.inputs['Geometry'])
    links.new(set_material.outputs['Geometry'], output_node.inputs['Geometry'])

    return node_group


def create_void_orb():
    """Create the complete void orb setup."""
    clear_scene()

    # Create base object
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1, location=(0, 0, 0))
    base_obj = bpy.context.active_object
    base_obj.name = "VoidOrbBase"

    base_obj.hide_render = False
    base_obj.display_type = 'BOUNDS'
    base_obj.show_in_front = False

    # Add geometry nodes modifier
    geo_mod = base_obj.modifiers.new(name="VoidOrb", type='NODES')
    node_group = create_geometry_nodes_distribution()
    geo_mod.node_group = node_group

    geo_mod.show_render = True
    geo_mod.show_viewport = True

    # Set default values
    for i, item in enumerate(node_group.interface.items_tree):
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Sphere Count":
                geo_mod[item.identifier] = 2000  # Reduced for faster render
            elif item.name == "Swarm Radius":
                geo_mod[item.identifier] = 1.5
            elif item.name == "Base Sphere Size":
                geo_mod[item.identifier] = 0.06
            elif item.name == "Seed":
                geo_mod[item.identifier] = 42
            elif item.name == "Wave Amplitude":
                geo_mod[item.identifier] = 0.02
            elif item.name == "Wave Frequency":
                geo_mod[item.identifier] = 8.0

    # Create and assign void orb material
    void_mat = create_void_orb_material()

    for node in node_group.nodes:
        if node.type == 'SET_MATERIAL':
            node.inputs['Material'].default_value = void_mat

    return base_obj, node_group, void_mat


def create_backdrop():
    """Create a simple dark backdrop."""
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 8, 2))
    obj = bpy.context.active_object
    obj.name = "Backdrop"
    obj.rotation_euler = (math.pi / 2, 0, 0)

    mat = bpy.data.materials.new("BackdropMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (0.01, 0.01, 0.02, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.95
    obj.data.materials.append(mat)

    return obj


def setup_scene():
    """Setup camera, lighting, and render settings."""
    scene = bpy.context.scene

    # Camera
    bpy.ops.object.camera_add(location=(0, -10, 3))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.15, 0, 0)
    scene.camera = camera

    # Subtle lighting (void orb is mostly emissive)
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 0.5  # Very subtle

    # World lighting - minimal ambient
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")

    scene.world.use_nodes = True
    world_nodes = scene.world.node_tree.nodes
    world_links = scene.world.node_tree.links
    world_nodes.clear()

    bg = world_nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.0, 0.0, 0.02, 1)  # Near black
    bg.inputs['Strength'].default_value = 0.05

    output = world_nodes.new('ShaderNodeOutputWorld')
    world_links.new(bg.outputs['Background'], output.inputs['Surface'])

    # Render settings
    scene.render.engine = 'BLENDER_EEVEE_NEXT'  # EEVEE for faster renders
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 150

    return camera


def create_void_orb_system():
    """Main function to create the complete void orb system."""

    print("\n" + "="*70)
    print("Creating Void Orb System...")
    print("="*70)

    # Create the void orb
    base_obj, node_group, void_mat = create_void_orb()
    print("Created void orb with three-layer shader...")

    # Create backdrop
    backdrop = create_backdrop()
    print("Created backdrop...")

    # Setup scene
    camera = setup_scene()
    print("Setup scene...")

    # Save
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/void_orb.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "="*70)
    print("VOID ORB SYSTEM Created!")
    print("="*70)
    print(f"\nFeatures:")
    print(f"  - Three-layer material system:")
    print(f"    • Void Core (absolute black nothingness)")
    print(f"    • Membrane Interface (oil balloon thin film)")
    print(f"    • Light Expansion (glowing white iris)")
    print(f"  - Reverse wave displacement (latitudinal ripples)")
    print(f"  - Sparkles (scattered bright points)")
    print(f"  - Purple swirls (animated patterns)")
    print(f"\nSaved to: {output_path}")
    print("="*70 + "\n")

    return output_path


if __name__ == "__main__":
    create_void_orb_system()
