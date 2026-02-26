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
    emission_mult.inputs[1].default_value = 2.0  # Emission strength multiplier
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
    1. Distributes points in a sphere volume
    2. Instances spheres with WEIGHTED size distribution matching original:
       - 30% tiny (0.3x)
       - 35% medium (0.8x)
       - 25% large (2.0x)
       - 10% very large (4.0x)
    3. Provides controls for count, radius, size distribution, spacing

    Uses math-based stepped selection for weighted sizes since geo nodes
    don't support shader nodes like ValToRGB.
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

    # 2. Distribute Points in Volume (sphere)
    uv_sphere = nodes.new('GeometryNodeMeshUVSphere')
    uv_sphere.inputs['Radius'].default_value = 1.0
    uv_sphere.inputs['Segments'].default_value = 2
    uv_sphere.inputs['Rings'].default_value = 2
    uv_sphere.location = (x, -400)
    x += 200

    # Distribute points inside
    distribute = nodes.new('GeometryNodeDistributePointsInVolume')
    distribute.location = (x, -200)
    x += 250

    # 3. Random Value for weighted size lookup (0-1)
    random_picker = nodes.new('FunctionNodeRandomValue')
    random_picker.data_type = 'FLOAT'
    random_picker.inputs['Min'].default_value = 0.0
    random_picker.inputs['Max'].default_value = 1.0
    random_picker.location = (x, -500)
    x_random = x
    x += 200

    # 4. Weighted size selection using stepped approach
    # Thresholds: 0.3 (30%), 0.65 (30+35%), 0.9 (30+35+25%)
    # Sizes: 0.3 (tiny), 0.8 (medium), 2.0 (large), 4.0 (very large)

    # Compare: random >= 0.9 (top 10%)
    compare_09 = nodes.new('FunctionNodeCompare')
    compare_09.operation = 'GREATER_EQUAL'
    compare_09.inputs[1].default_value = 0.9
    compare_09.location = (x, -700)

    # Compare: random >= 0.65 (top 35%)
    compare_065 = nodes.new('FunctionNodeCompare')
    compare_065.operation = 'GREATER_EQUAL'
    compare_065.inputs[1].default_value = 0.65
    compare_065.location = (x, -500)

    # Compare: random >= 0.3 (top 70%)
    compare_03 = nodes.new('FunctionNodeCompare')
    compare_03.operation = 'GREATER_EQUAL'
    compare_03.inputs[1].default_value = 0.3
    compare_03.location = (x, -300)

    x += 200

    # Boolean math to isolate each category
    # is_very_large = compare_09
    # is_large = compare_065 AND NOT compare_09
    # is_medium = compare_03 AND NOT compare_065
    # is_tiny = NOT compare_03

    not_09 = nodes.new('FunctionNodeBooleanMath')
    not_09.operation = 'NOT'
    not_09.location = (x, -700)

    not_065 = nodes.new('FunctionNodeBooleanMath')
    not_065.operation = 'NOT'
    not_065.location = (x, -500)

    and_large = nodes.new('FunctionNodeBooleanMath')
    and_large.operation = 'AND'
    and_large.location = (x + 200, -600)

    and_medium = nodes.new('FunctionNodeBooleanMath')
    and_medium.operation = 'AND'
    and_medium.location = (x + 200, -400)

    x += 400

    # Multiply each size by its selection boolean
    # Using math nodes with hardcoded size values
    mult_tiny = nodes.new('ShaderNodeMath')
    mult_tiny.operation = 'MULTIPLY'
    mult_tiny.inputs[1].default_value = 0.3  # tiny size
    mult_tiny.location = (x, -800)

    mult_medium = nodes.new('ShaderNodeMath')
    mult_medium.operation = 'MULTIPLY'
    mult_medium.inputs[1].default_value = 0.8  # medium size
    mult_medium.location = (x, -650)

    mult_large = nodes.new('ShaderNodeMath')
    mult_large.operation = 'MULTIPLY'
    mult_large.inputs[1].default_value = 2.0  # large size
    mult_large.location = (x, -500)

    mult_vlarge = nodes.new('ShaderNodeMath')
    mult_vlarge.operation = 'MULTIPLY'
    mult_vlarge.inputs[1].default_value = 4.0  # very large size
    mult_vlarge.location = (x, -350)

    x += 200

    # Add all together: tiny_contrib + medium_contrib + large_contrib + vlarge_contrib
    add_1 = nodes.new('ShaderNodeMath')
    add_1.operation = 'ADD'
    add_1.location = (x, -700)

    add_2 = nodes.new('ShaderNodeMath')
    add_2.operation = 'ADD'
    add_2.location = (x + 200, -550)

    add_3 = nodes.new('ShaderNodeMath')
    add_3.operation = 'ADD'
    add_3.location = (x + 400, -400)

    x += 600

    # Now multiply by base sphere size
    size_mult = nodes.new('ShaderNodeMath')
    size_mult.operation = 'MULTIPLY'
    size_mult.location = (x, -400)
    x += 200

    # CombineXYZ to convert float scale to vector (uniform scale)
    combine_xyz = nodes.new('ShaderNodeCombineXYZ')
    combine_xyz.location = (x, -400)
    x += 200

    # 5. Instance on Points - sphere mesh
    instance_sphere = nodes.new('GeometryNodeMeshUVSphere')
    instance_sphere.inputs['Segments'].default_value = 16
    instance_sphere.inputs['Rings'].default_value = 12
    instance_sphere.location = (x, -600)

    instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')
    instance_on_points.location = (x, -200)
    x += 300

    # 6. Realize Instances (so shader works per-sphere)
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (x, -200)
    x += 200

    # 7. Set Material
    set_material = nodes.new('GeometryNodeSetMaterial')
    set_material.location = (x, -200)
    x += 200

    # 8. Output node
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (x, -200)

    # === LINK NODES ===

    # Create volume sphere from radius
    links.new(input_node.outputs['Swarm Radius'], uv_sphere.inputs['Radius'])

    # Distribute points
    links.new(uv_sphere.outputs['Mesh'], distribute.inputs['Volume'])
    links.new(input_node.outputs['Sphere Count'], distribute.inputs['Density'])

    # Random picker with seed and index
    index_node = nodes.new('GeometryNodeInputIndex')
    index_node.location = (x_random - 200, -600)
    links.new(index_node.outputs['Index'], random_picker.inputs['ID'])
    links.new(input_node.outputs['Seed'], random_picker.inputs['Seed'])

    # Compare thresholds
    links.new(random_picker.outputs['Value'], compare_09.inputs[0])
    links.new(random_picker.outputs['Value'], compare_065.inputs[0])
    links.new(random_picker.outputs['Value'], compare_03.inputs[0])

    # Boolean isolation
    links.new(compare_09.outputs['Result'], not_09.inputs[0])
    links.new(compare_065.outputs['Result'], not_065.inputs[0])

    # is_large = compare_065 AND NOT compare_09
    links.new(compare_065.outputs['Result'], and_large.inputs[0])
    links.new(not_09.outputs['Boolean'], and_large.inputs[1])

    # is_medium = compare_03 AND NOT compare_065
    links.new(compare_03.outputs['Result'], and_medium.inputs[0])
    links.new(not_065.outputs['Boolean'], and_medium.inputs[1])

    # is_tiny = NOT compare_03 (already have not_065, need NOT of compare_03)
    not_03 = nodes.new('FunctionNodeBooleanMath')
    not_03.operation = 'NOT'
    not_03.location = (x_random + 400, -200)
    links.new(compare_03.outputs['Result'], not_03.inputs[0])

    # Multiply size by selection (bool converted to 0 or 1)
    # tiny: not_03 * 0.3
    links.new(not_03.outputs['Boolean'], mult_tiny.inputs[0])

    # medium: and_medium * 0.8
    links.new(and_medium.outputs['Boolean'], mult_medium.inputs[0])

    # large: and_large * 2.0
    links.new(and_large.outputs['Boolean'], mult_large.inputs[0])

    # very_large: compare_09 * 4.0
    links.new(compare_09.outputs['Result'], mult_vlarge.inputs[0])

    # Add contributions
    links.new(mult_tiny.outputs['Value'], add_1.inputs[0])
    links.new(mult_medium.outputs['Value'], add_1.inputs[1])
    links.new(mult_large.outputs['Value'], add_2.inputs[0])
    links.new(mult_vlarge.outputs['Value'], add_2.inputs[1])
    links.new(add_1.outputs['Value'], add_3.inputs[0])
    links.new(add_2.outputs['Value'], add_3.inputs[1])

    # Multiply by base size
    links.new(input_node.outputs['Base Sphere Size'], size_mult.inputs[0])
    links.new(add_3.outputs['Value'], size_mult.inputs[1])

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

    # Hide the base object gizmo in viewport only (geo nodes output still renders)
    base_obj.show_in_front = False  # Don't show in front
    # Don't hide_viewport as that hides geo nodes output too

    # Add geometry nodes modifier
    geo_mod = base_obj.modifiers.new(name="SphereSwarm", type='NODES')
    node_group = create_geometry_nodes_distribution()
    geo_mod.node_group = node_group

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
    # Camera
    bpy.ops.object.camera_add(location=(0, -10, 3))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.15, 0, 0)
    bpy.context.scene.camera = camera

    # Lighting
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 2.0

    bpy.ops.object.light_add(type='AREA', location=(-4, 3, 5))
    fill = bpy.context.active_object
    fill.data.energy = 30.0
    fill.data.size = 4.0

    # Render settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.fps = 24
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 150

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
