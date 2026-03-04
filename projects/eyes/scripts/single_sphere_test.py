"""
Single Sphere Test - Top 1/4 White, Bottom 3/4 Black

Simple test: One sphere with hard cutoff shader.
"""

import bpy
import math


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


def create_cutoff_material():
    """
    Two-Zone Material System with Pearl and Velvet materials

    ZONE A (bottom 75%): Pearl - iridescent white using Fresnel color shift
    ZONE B (top 25%): Velvet black - deep black with purple rim via Fresnel

    Uses Generated Z coordinate for zone mask.
    Uses Fresnel for iridescence/rim effects (compatible with older Blender).
    """
    mat = bpy.data.materials.new(name="TwoZoneMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    x = 0

    # === ZONE MASK with WAVY TRANSITION ===
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (x, 0)
    x += 200

    separate = nodes.new('ShaderNodeSeparateXYZ')
    separate.location = (x, 0)
    x += 200

    # Wave noise texture - creates the wavy pattern
    wave_noise = nodes.new('ShaderNodeTexNoise')
    wave_noise.inputs['Scale'].default_value = 3.0  # Wave frequency
    wave_noise.inputs['Detail'].default_value = 1.0  # Some detail for organic waves
    wave_noise.inputs['Distortion'].default_value = 0.5
    wave_noise.location = (x, 200)
    x += 200

    # Scale the wave amount (how much it deviates from linear)
    wave_amount = nodes.new('ShaderNodeMath')
    wave_amount.operation = 'MULTIPLY'
    wave_amount.inputs[1].default_value = 0.15  # Wave amplitude (0.15 = subtle waves)
    wave_amount.location = (x, 200)
    x += 200

    # Add wave offset to Z coordinate
    add_wave = nodes.new('ShaderNodeMath')
    add_wave.operation = 'ADD'
    add_wave.location = (x, 0)
    x += 200

    # SOFT ZONE TRANSITION - now with WAVY distortion
    # Distorted Z goes from ~0 to ~1 with waves
    zone_ramp = nodes.new('ShaderNodeValToRGB')
    zone_ramp.color_ramp.interpolation = 'EASE'
    zone_ramp.color_ramp.elements[0].position = 0.72  # Narrower: 0.72 to 0.78
    zone_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)  # Pearl zone (Fac=0)
    zone_ramp.color_ramp.elements[1].position = 0.78  # Was 0.65/0.85
    zone_ramp.color_ramp.elements[1].color = (1, 1, 1, 1)  # Velvet zone (Fac=1)
    zone_ramp.location = (x, 0)
    x_zone = x
    x += 200

    # === SHARED: Geometry + Fresnel ===
    geometry = nodes.new('ShaderNodeNewGeometry')
    geometry.location = (x_zone - 200, -400)

    fresnel = nodes.new('ShaderNodeFresnel')
    fresnel.inputs['IOR'].default_value = 1.5
    fresnel.location = (x_zone, -400)

    # === ZONE A: PEARL (bottom) with SPARKLE ===
    # Noise texture for sparkle/iridescence - MASSIVE + BRIGHT
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 1.0  # Maximum size
    noise.inputs['Detail'].default_value = 0.0  # No detail = massive spots
    noise.inputs['Distortion'].default_value = 0.0
    noise.location = (x_zone + 100, 450)

    # Sparkle color ramp - MASSIVE + BRIGHT sparkle spots
    sparkle_ramp = nodes.new('ShaderNodeValToRGB')
    sparkle_ramp.color_ramp.interpolation = 'CONSTANT'
    sparkle_ramp.color_ramp.elements[0].position = 0.35  # Very low = maximum sparkles
    sparkle_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)  # No sparkle
    sparkle_ramp.color_ramp.elements[1].position = 0.50  # Wide band
    sparkle_ramp.color_ramp.elements[1].color = (1, 1, 1, 1)  # Sparkle
    sparkle_ramp.location = (x_zone + 300, 450)

    # Iridescence via color ramp on Fresnel (center = white, edge = purple)
    pearl_ramp = nodes.new('ShaderNodeValToRGB')
    pearl_ramp.color_ramp.interpolation = 'EASE'
    pearl_ramp.color_ramp.elements[0].position = 0.0
    pearl_ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)  # Center = white
    pearl_ramp.color_ramp.elements[1].position = 1.0
    pearl_ramp.color_ramp.elements[1].color = (0.7, 0.4, 0.9, 1.0)  # Edge = purple
    pearl_ramp.location = (x_zone + 200, 300)

    # Mix base color with sparkle
    sparkle_mult = nodes.new('ShaderNodeMixRGB')
    sparkle_mult.inputs['Fac'].default_value = 0.8  # Very strong sparkle intensity
    sparkle_mult.inputs['Color2'].default_value = (3.0, 3.0, 3.5, 1.0)  # Very bright sparkle
    sparkle_mult.location = (x_zone + 500, 350)

    pearl_base = nodes.new('ShaderNodeBsdfPrincipled')
    pearl_base.inputs['Roughness'].default_value = 0.05  # Very glossy
    pearl_base.inputs['IOR'].default_value = 2.0
    pearl_base.location = (x_zone + 700, 250)

    # Emission glow - stronger
    pearl_glow = nodes.new('ShaderNodeEmission')
    pearl_glow.inputs['Strength'].default_value = 2.0  # Stronger
    pearl_glow.location = (x_zone + 700, 100)

    pearl_mix = nodes.new('ShaderNodeMixShader')
    pearl_mix.inputs['Fac'].default_value = 0.35
    pearl_mix.location = (x_zone + 950, 200)

    # === ZONE B: VELVET BLACK (top 25%) ===
    # Rim light effect via inverted Fresnel
    velvet_ramp = nodes.new('ShaderNodeValToRGB')
    velvet_ramp.color_ramp.interpolation = 'EASE'
    velvet_ramp.color_ramp.elements[0].position = 0.0
    velvet_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)  # Center = black
    velvet_ramp.color_ramp.elements[1].position = 0.7
    velvet_ramp.color_ramp.elements[1].color = (0.4, 0.2, 0.6, 1.0)  # Edge = purple
    velvet_ramp.location = (x_zone + 200, -100)

    velvet = nodes.new('ShaderNodeBsdfPrincipled')
    velvet.inputs['Roughness'].default_value = 0.95  # Soft/velvety
    velvet.location = (x_zone + 400, -150)

    # === MIX ZONES ===
    mix_shader = nodes.new('ShaderNodeMixShader')
    mix_shader.location = (x_zone + 900, 0)

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (x_zone + 1100, 0)

    # === LINKS ===
    # Zone mask - Z with WAVY distortion
    links.new(tex_coord.outputs['Generated'], separate.inputs['Vector'])
    links.new(tex_coord.outputs['Generated'], wave_noise.inputs['Vector'])
    links.new(wave_noise.outputs['Fac'], wave_amount.inputs[0])
    links.new(separate.outputs['Z'], add_wave.inputs[0])
    links.new(wave_amount.outputs['Value'], add_wave.inputs[1])
    links.new(add_wave.outputs['Value'], zone_ramp.inputs['Fac'])

    # Fresnel
    links.new(geometry.outputs['Normal'], fresnel.inputs['Normal'])

    # Sparkle: Generated -> Noise -> Ramp -> Mix
    links.new(tex_coord.outputs['Generated'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], sparkle_ramp.inputs['Fac'])
    links.new(sparkle_ramp.outputs['Color'], sparkle_mult.inputs['Fac'])

    # Pearl: Fresnel -> Color Ramp -> Mix with sparkle -> Base Color
    links.new(fresnel.outputs['Fac'], pearl_ramp.inputs['Fac'])
    links.new(pearl_ramp.outputs['Color'], sparkle_mult.inputs['Color1'])  # Base iridescent color
    links.new(sparkle_mult.outputs['Color'], pearl_base.inputs['Base Color'])
    links.new(sparkle_mult.outputs['Color'], pearl_glow.inputs['Color'])
    links.new(pearl_base.outputs['BSDF'], pearl_mix.inputs[1])
    links.new(pearl_glow.outputs['Emission'], pearl_mix.inputs[2])

    # Velvet: Fresnel -> Color Ramp -> Base Color (rim effect)
    links.new(fresnel.outputs['Fac'], velvet_ramp.inputs['Fac'])
    links.new(velvet_ramp.outputs['Color'], velvet.inputs['Base Color'])

    # Mix zones
    links.new(zone_ramp.outputs['Color'], mix_shader.inputs['Fac'])
    links.new(velvet.outputs['BSDF'], mix_shader.inputs[1])  # Top = velvet
    links.new(pearl_mix.outputs['Shader'], mix_shader.inputs[2])  # Bottom = pearl

    links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])

    return mat


def create_single_sphere():
    """Create a single UV sphere with cutoff material."""
    clear_scene()

    # Create sphere with more segments for smoothness
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=2.0,
        location=(0, 0, 0),
        segments=64,  # More segments for smoother sphere
        ring_count=32
    )
    sphere = bpy.context.active_object
    sphere.name = "TestSphere"

    # Add subdivision surface for extra smoothness
    subsurf = sphere.modifiers.new(name="Subdivision", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 3

    # Create and assign material
    mat = create_cutoff_material()
    sphere.data.materials.append(mat)

    return sphere, mat


def setup_scene():
    """Setup camera and lighting."""
    scene = bpy.context.scene

    # Camera - centered on sphere, looking straight at it
    # Sphere is at (0,0,0) with radius 2, so camera at Y=-8 looks at center
    bpy.ops.object.camera_add(location=(0, -8, 0))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.pi / 2, 0, 0)  # Looking straight at sphere center
    scene.camera = camera

    # Set render resolution
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100

    # Simple lighting
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 2.0

    # World
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    world_nodes = scene.world.node_tree.nodes
    world_links = scene.world.node_tree.links
    world_nodes.clear()

    bg = world_nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.05, 0.05, 0.05, 1)  # Dark grey
    bg.inputs['Strength'].default_value = 0.5

    output = world_nodes.new('ShaderNodeOutputWorld')
    world_links.new(bg.outputs['Background'], output.inputs['Surface'])

    # Render settings - Cycles with more samples for smooth materials
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128  # Higher samples for iridescence/sheen
    scene.cycles.use_denoising = True

    return camera


def main():
    print("\n" + "="*50)
    print("Single Sphere Test - Top 1/4 White, Bottom 3/4 Black")
    print("="*50)

    # Create sphere
    sphere, mat = create_single_sphere()
    print("Created single sphere with cutoff material...")

    # Setup scene
    camera = setup_scene()
    print("Setup camera and lighting...")

    # Save blend file
    output_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/single_sphere_test.blend"
    bpy.ops.wm.save_as_mainfile(filepath=output_path)

    # Render and save image
    render_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/single_sphere_render.png"
    bpy.ops.render.render(write_still=True)
    bpy.data.images['Render Result'].save_render(filepath=render_path)

    print(f"\nSaved blend to: {output_path}")
    print(f"Saved render to: {render_path}")
    print("="*50 + "\n")

    return output_path


if __name__ == "__main__":
    main()
