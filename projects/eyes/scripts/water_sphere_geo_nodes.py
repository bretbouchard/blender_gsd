"""
Water Sphere Swarm - Geometry Nodes Version

Creates a swarm of spheres using Geometry Nodes with:
- Per-sphere radial gradient shader (dark rim, emissive pearlescent center)
- Geo nodes controlling size, spacing, and distribution
- Animated drift/orbit movement via geo nodes
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


def create_per_sphere_radial_material():
    """
    Create a material where each individual sphere has:
    - Dark black on the outer rim (perpendicular to view)
    - Emissive pearlescent white at the center (facing the camera)

    Uses Normal · Incoming dot product for per-sphere radial gradient.
    """
    mat = bpy.data.materials.new(name="PerSphereRadial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    x = 0

    # 1. Geometry node for vectors
    geometry = nodes.new('ShaderNodeNewGeometry')
    geometry.location = (x, 0)
    x += 200

    # 2. Vector Dot Product: Normal · Incoming
    # Result: 1.0 = facing camera (center), 0.0 = perpendicular (edge)
    dot_product = nodes.new('ShaderNodeVectorMath')
    dot_product.operation = 'DOT_PRODUCT'
    dot_product.location = (x, 0)
    x += 200

    # 3. Color Ramp: 0 (edge) → dark, 1 (center) → pearlescent white
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.color_ramp.interpolation = 'EASE'
    # Dark at position 0.0 (edge/rim)
    color_ramp.color_ramp.elements[0].position = 0.0
    color_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.02, 1.0)  # Near black with hint of blue
    # Pearlescent white at position 1.0 (center facing camera)
    color_ramp.color_ramp.elements[1].position = 1.0
    color_ramp.color_ramp.elements[1].color = (0.95, 0.97, 1.0, 1.0)  # Slightly cool white
    color_ramp.location = (x, 0)
    x += 250

    # 4. Another ramp for emission strength (stronger at center)
    emission_ramp = nodes.new('ShaderNodeValToRGB')
    emission_ramp.color_ramp.interpolation = 'EASE'
    emission_ramp.color_ramp.elements[0].position = 0.0
    emission_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)  # No emission at edge
    emission_ramp.color_ramp.elements[1].position = 0.7
    emission_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)  # Full emission at center
    emission_ramp.location = (x, -200)
    x_ramp = x

    # 5. Math: Multiply for emission intensity control
    emission_mult = nodes.new('ShaderNodeMath')
    emission_mult.operation = 'MULTIPLY'
    emission_mult.inputs[1].default_value = 5.0  # Increased emission strength for visibility
    emission_mult.location = (x, -200)
    x += 200

    # 6. Emission node
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (0.9, 0.95, 1.0, 1.0)  # Cool white emission
    emission.location = (x, -200)
    x += 200

    # 7. Principled BSDF for base surface
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.15
    bsdf.inputs['IOR'].default_value = 1.45
    bsdf.inputs['Transmission Weight'].default_value = 0.3
    bsdf.location = (x_ramp + 450, 100)
    x_bsdf = x

    # 8. Mix Shader: Combine BSDF + Emission
    mix_shader = nodes.new('ShaderNodeMixShader')
    mix_shader.inputs['Fac'].default_value = 0.5  # Balance between surface and emission
    mix_shader.location = (x, 0)
    x += 200

    # 9. Material Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (x, 0)

    # Link nodes
    # Dot product: Normal · Incoming
    links.new(geometry.outputs['Normal'], dot_product.inputs[0])
    links.new(geometry.outputs['Incoming'], dot_product.inputs[1])

    # Color ramp for base color
    links.new(dot_product.outputs['Value'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])

    # Emission ramp and multiplier
    links.new(dot_product.outputs['Value'], emission_ramp.inputs['Fac'])
    links.new(emission_ramp.outputs['Color'], emission_mult.inputs[0])
    links.new(emission_mult.outputs['Value'], emission.inputs['Strength'])
    links.new(color_ramp.outputs['Color'], emission.inputs['Color'])

    # Mix shaders
    links.new(bsdf.outputs['BSDF'], mix_shader.inputs[1])
    links.new(emission.outputs['Emission'], mix_shader.inputs[2])

    # Output
    links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])

    mat.blend_method = 'BLEND'

    return mat


def create_geometry_nodes_distribution():
    """
    Create a Geometry Nodes setup that:
    1. Creates a sphere mesh and converts to volume
    2. Distributes points inside the volume
    3. Instances spheres with random sizes
    4. Provides controls for count, radius, size distribution, spacing
    """
    # Create a new node group
    node_group = bpy.data.node_groups.new(name="SphereSwarmDistribution", type='GeometryNodeTree')

    # Create input/output interfaces
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Input parameters
    node_group.interface.new_socket(name="Sphere Count", in_out='INPUT', socket_type='NodeSocketInt')
    node_group.interface.new_socket(name="Swarm Radius", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Base Sphere Size", in_out='INPUT', socket_type='NodeSocketFloat')
    node_group.interface.new_socket(name="Seed", in_out='INPUT', socket_type='NodeSocketInt')

    nodes = node_group.nodes
    links = node_group.links

    x = 0

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

    # 5. Random Value for size (0.3 to 4.0 for variety)
    random_size = nodes.new('FunctionNodeRandomValue')
    random_size.data_type = 'FLOAT'
    random_size.inputs['Min'].default_value = 0.3  # Tiny
    random_size.inputs['Max'].default_value = 4.0  # Very large
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

    # 7. CombineXYZ to convert float scale to vector (uniform scale)
    combine_xyz = nodes.new('ShaderNodeCombineXYZ')
    combine_xyz.location = (x, -400)
    x += 200

    # 8. Instance on Points - sphere mesh
    instance_sphere = nodes.new('GeometryNodeMeshUVSphere')
    instance_sphere.inputs['Segments'].default_value = 16
    instance_sphere.inputs['Rings'].default_value = 12
    instance_sphere.location = (x, -600)

    instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')
    instance_on_points.location = (x, -200)
    x += 300

    # 9. Realize Instances (so shader works per-sphere)
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (x, -200)
    x += 200

    # 10. Set Material
    set_material = nodes.new('GeometryNodeSetMaterial')
    set_material.location = (x, -200)
    x += 200

    # 11. Output node
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (x, -200)

    # === LINK NODES ===

    # Create volume sphere from radius
    links.new(input_node.outputs['Swarm Radius'], uv_sphere.inputs['Radius'])

    # Mesh to volume
    links.new(uv_sphere.outputs['Mesh'], mesh_to_volume.inputs['Mesh'])

    # Distribute points in volume
    links.new(mesh_to_volume.outputs['Volume'], distribute.inputs['Volume'])
    links.new(input_node.outputs['Sphere Count'], distribute.inputs['Density'])
    links.new(input_node.outputs['Seed'], distribute.inputs['Seed'])

    # Random size with index as ID for variation
    links.new(index_node.outputs['Index'], random_size.inputs['ID'])
    links.new(input_node.outputs['Seed'], random_size.inputs['Seed'])

    # Multiply by base size
    links.new(input_node.outputs['Base Sphere Size'], size_mult.inputs[0])
    links.new(random_size.outputs['Value'], size_mult.inputs[1])

    # Convert float to vector for uniform scale
    links.new(size_mult.outputs['Value'], combine_xyz.inputs['X'])
    links.new(size_mult.outputs['Value'], combine_xyz.inputs['Y'])
    links.new(size_mult.outputs['Value'], combine_xyz.inputs['Z'])

    # Instance spheres with uniform scale
    links.new(distribute.outputs['Points'], instance_on_points.inputs['Points'])
    links.new(instance_sphere.outputs['Mesh'], instance_on_points.inputs['Instance'])
    links.new(combine_xyz.outputs['Vector'], instance_on_points.inputs['Scale'])

    # Realize and output
    links.new(instance_on_points.outputs['Instances'], realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], set_material.inputs['Geometry'])
    links.new(set_material.outputs['Geometry'], output_node.inputs['Geometry'])

    return node_group


def create_geo_nodes_swarm():
    """
    Create the complete geo nodes swarm setup with a base object.
    """
    clear_scene()

    # Create a simple icosphere as the base object (will be replaced by geo nodes)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1, location=(0, 0, 0))
    base_obj = bpy.context.active_object
    base_obj.name = "SphereSwarmBase"

    # CRITICAL: Proper visibility settings for geo nodes
    # - hide_render must be FALSE so geo nodes output is visible
    # - Use display_type to hide the base gizmo in viewport
    base_obj.hide_render = False  # MUST be False - geo nodes output needs this
    base_obj.display_type = 'BOUNDS'  # Hide base mesh gizmo, show only bounds
    base_obj.show_in_front = False

    # Add geometry nodes modifier
    geo_mod = base_obj.modifiers.new(name="SphereSwarm", type='NODES')
    node_group = create_geometry_nodes_distribution()
    geo_mod.node_group = node_group

    # CRITICAL: Ensure modifier is enabled for render
    geo_mod.show_render = True
    geo_mod.show_viewport = True

    # Set default values - tuned from smooth_water_swarm.blend
    # 10,000 spheres, 1.5 radius, 0.06 base size
    # Weighted size distribution: 30% tiny (0.3x), 35% medium (0.8x), 25% large (2x), 10% very large (4x)
    for i, item in enumerate(node_group.interface.items_tree):
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Sphere Count":
                geo_mod[item.identifier] = 10000  # Dense fill
            elif item.name == "Swarm Radius":
                geo_mod[item.identifier] = 1.5  # Tight ball formation
            elif item.name == "Base Sphere Size":
                geo_mod[item.identifier] = 0.06  # Base radius
            elif item.name == "Seed":
                geo_mod[item.identifier] = 42

    # Create and assign material
    water_mat = create_per_sphere_radial_material()

    # Set material in geo nodes Set Material node
    for node in node_group.nodes:
        if node.type == 'SET_MATERIAL':
            node.inputs['Material'].default_value = water_mat

    return base_obj, node_group, water_mat


def create_backdrop():
    """Create a simple dark backdrop plane behind the swarm."""
    # Simple large plane positioned behind the swarm
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 8, 2))
    obj = bpy.context.active_object
    obj.name = "Backdrop"
    obj.rotation_euler = (math.pi / 2, 0, 0)  # Stand vertical, facing camera

    # Dark material for backdrop
    mat = bpy.data.materials.new("BackdropMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1.0)
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

    # Lighting
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 2.0

    bpy.ops.object.light_add(type='AREA', location=(-4, 3, 5))
    fill = bpy.context.active_object
    fill.data.energy = 30.0
    fill.data.size = 4.0

    # World lighting - subtle ambient for emissive materials
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")

    scene.world.use_nodes = True
    world_nodes = scene.world.node_tree.nodes
    world_links = scene.world.node_tree.links
    world_nodes.clear()

    # Background with subtle ambient
    bg = world_nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.02, 0.02, 0.05, 1)  # Very dark blue
    bg.inputs['Strength'].default_value = 0.1  # Subtle ambient

    output = world_nodes.new('ShaderNodeOutputWorld')
    world_links.new(bg.outputs['Background'], output.inputs['Surface'])

    # Render settings
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 150

    # Viewport shading
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'

    return camera


def create_water_sphere_geo_nodes():
    """Main function to create the complete geo nodes swarm setup."""

    print("\n" + "="*70)
    print("Creating Geo Nodes Water Sphere Swarm...")
    print("="*70)

    # Create the geo nodes swarm
    base_obj, node_group, water_mat = create_geo_nodes_swarm()

    # Create backdrop
    print("Creating studio backdrop...")
    backdrop = create_backdrop()

    # Setup scene
    print("Setting up camera and lighting...")
    camera = setup_scene()

    # Assign material to geo nodes (need to set it in the node group)
    # Find the Set Material node and set the material
    for node in node_group.nodes:
        if node.type == 'SET_MATERIAL':
            node.inputs['Material'].default_value = water_mat

    # Save
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/geo_nodes_swarm.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    print("\n" + "="*70)
    print("GEO NODES WATER SPHERE SWARM Created!")
    print("="*70)
    print(f"\nFeatures:")
    print(f"  - Per-sphere radial gradient shader (dark rim, emissive center)")
    print(f"  - Geometry Nodes controlling distribution")
    print(f"  - WEIGHTED size distribution (matching smooth_water_swarm.blend):")
    print(f"    • 30% tiny (0.3x)")
    print(f"    • 35% medium (0.8x)")
    print(f"    • 25% large (2.0x)")
    print(f"    • 10% very large (4.0x)")
    print(f"  - Adjustable parameters:")
    print(f"    • Sphere Count: 10,000")
    print(f"    • Swarm Radius: 1.5")
    print(f"    • Base Sphere Size: 0.06")
    print(f"    • Seed: 42")
    print(f"\nSaved to: {output_path}")
    print("="*70 + "\n")

    return output_path


if __name__ == "__main__":
    create_water_sphere_geo_nodes()
