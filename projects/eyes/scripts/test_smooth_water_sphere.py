"""
Test Smooth Water Sphere - Calm Water Visualization

Creates a test scene with a smooth water sphere to visualize
the gentle, rolling wave effect.
"""

import bpy
import sys
from pathlib import Path

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from water_sphere_smooth import create_smooth_water_sphere, animate_smooth_water_sphere


def clear_scene():
    """Clear all mesh objects from scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Also clear orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)


def setup_lighting():
    """Add soft lighting for water material visibility."""
    # Main key light - soft and diffused
    bpy.ops.object.light_add(type='AREA', location=(5, -5, 8))
    key = bpy.context.active_object
    key.data.energy = 200.0
    key.data.size = 8.0
    key.rotation_euler = (0.8, 0.2, 0.5)
    key.name = "KeyLight"

    # Fill light - softer, from opposite side
    bpy.ops.object.light_add(type='AREA', location=(-5, 5, 6))
    fill = bpy.context.active_object
    fill.data.energy = 100.0
    fill.data.size = 6.0
    fill.rotation_euler = (0.6, -0.3, -0.5)
    fill.name = "FillLight"

    # Rim light - subtle highlight from behind
    bpy.ops.object.light_add(type='AREA', location=(0, -8, 3))
    rim = bpy.context.active_object
    rim.data.energy = 80.0
    rim.data.size = 4.0
    rim.rotation_euler = (1.2, 0, 3.14)
    rim.name = "RimLight"


def setup_camera():
    """Position camera to view the sphere."""
    bpy.ops.object.camera_add(location=(0, -10, 2))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.35, 0, 0)
    bpy.context.scene.camera = camera


def create_smooth_water_material():
    """Create a smooth water material for the sphere."""
    mat = bpy.data.materials.new(name="SmoothWaterMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Create Principled BSDF for water
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Smooth water settings
    bsdf.inputs['Base Color'].default_value = (0.05, 0.2, 0.4, 1.0)  # Deep blue
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.02  # Very smooth surface
    bsdf.inputs['IOR'].default_value = 1.33  # Water IOR
    bsdf.inputs['Alpha'].default_value = 0.85  # Slight transparency

    # Mix with glass shader for realistic water look
    glass = nodes.new('ShaderNodeBsdfGlass')
    glass.location = (0, -200)
    glass.inputs['Color'].default_value = (0.05, 0.2, 0.4, 1.0)
    glass.inputs['Roughness'].default_value = 0.01  # Very smooth
    glass.inputs['IOR'].default_value = 1.33

    mix = nodes.new('ShaderNodeMixShader')
    mix.location = (300, -100)
    mix.inputs['Fac'].default_value = 0.4  # Mix between glass and principled

    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (500, -100)

    # Link nodes
    links.new(bsdf.outputs['BSDF'], mix.inputs[1])
    links.new(glass.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])

    # Set blend mode for transparency
    mat.blend_method = 'BLEND'

    return mat


def main():
    """Main test function."""
    print("\n" + "="*60)
    print("Creating Smooth Water Sphere Test Scene")
    print("="*60 + "\n")

    # Clear scene
    clear_scene()

    # Setup scene
    setup_lighting()
    setup_camera()

    # Create smooth water sphere
    print("Creating smooth water sphere with gentle rolling waves...")
    sphere = create_smooth_water_sphere(
        size=2.5,
        wave_scale=1.2,        # Gentle, wide waves
        wave_height=0.06,      # Subtle displacement
        wind_speed=0.25,       # Slow, steady wind
        time=0.0,
        segments=80,           # High resolution for smoothness
        rings=60,
        name="SmoothWaterSphere"
    )

    # Apply water material
    water_mat = create_smooth_water_material()
    sphere.data.materials.append(water_mat)

    # Animate
    print("Animating gentle waves...")
    animate_smooth_water_sphere(sphere, start_frame=1, end_frame=250, speed=0.15)

    # Set frame range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 250

    # Set render settings for smooth preview
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128

    # Set viewport to rendered for visibility
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'

    # Save the blend file
    output_path = script_dir.parent / "smooth_water_sphere_test.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"Saved to: {output_path}")

    print("\n" + "="*60)
    print("Smooth Water Sphere Created Successfully!")
    print("="*60)
    print("\nSphere Properties:")
    print(f"  - Name: {sphere.name}")
    print(f"  - Size: 2.5")
    print(f"  - Wave Scale: 1.2 (gentle, wide rolling waves)")
    print(f"  - Wave Height: 0.06 (subtle displacement)")
    print(f"  - Wind Speed: 0.25 (slow, steady wind)")
    print(f"  - Segments/Rings: 80/60 (very smooth surface)")
    print("\nKey Differences from Noise-Based Version:")
    print("  - Uses SINE WAVES instead of noise for smooth motion")
    print("  - Two layers: primary (rolling) + secondary (detail)")
    print("  - Much higher subdivision (level 4) for smoothness")
    print("  - Gentle parameters for calm water effect")
    print("\nAnimation:")
    print(f"  - Frames: 1-250")
    print(f"  - Speed: 0.15 (slow, peaceful motion)")
    print("\nControls:")
    print("  - Press SPACE to play animation")
    print("  - Adjust 'Wave Scale' to change wave frequency")
    print("  - Adjust 'Wave Height' for wave amplitude")
    print("  - Adjust 'Wind Speed' for animation speed")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
