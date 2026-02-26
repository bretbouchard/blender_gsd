"""
Test Water Sphere - Visualization Script

Creates a test scene with a single water sphere to visualize
the wind-driven ripple effect.
"""

import bpy
import sys
from pathlib import Path

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from water_sphere import create_single_water_sphere, animate_water_sphere


def clear_scene():
    """Clear all mesh objects from scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Also clear orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)


def setup_lighting():
    """Add lighting for water material visibility."""
    # Add a sun light
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    sun.rotation_euler = (0.5, 0.2, 0.8)
    sun.name = "MainSun"

    # Add fill light
    bpy.ops.object.light_add(type='AREA', location=(-5, 5, 5))
    fill = bpy.context.active_object
    fill.data.energy = 100.0
    fill.data.size = 5.0
    fill.name = "FillLight"


def setup_camera():
    """Position camera to view the sphere."""
    bpy.ops.object.camera_add(location=(0, -8, 2))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.2, 0, 0)
    bpy.context.scene.camera = camera


def create_water_material():
    """Create a basic water material for the sphere."""
    mat = bpy.data.materials.new(name="WaterMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Create Principled BSDF for water
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Water-like settings
    bsdf.inputs['Base Color'].default_value = (0.1, 0.3, 0.5, 1.0)  # Blue tint
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.05  # Very smooth
    bsdf.inputs['IOR'].default_value = 1.33  # Water IOR
    bsdf.inputs['Alpha'].default_value = 0.8  # Slight transparency

    # Mix with glass shader for better water look
    glass = nodes.new('ShaderNodeBsdfGlass')
    glass.location = (0, -200)
    glass.inputs['Color'].default_value = (0.1, 0.3, 0.5, 1.0)
    glass.inputs['Roughness'].default_value = 0.02
    glass.inputs['IOR'].default_value = 1.33

    mix = nodes.new('ShaderNodeMixShader')
    mix.location = (300, -100)
    mix.inputs['Fac'].default_value = 0.3  # Mix between glass and principled

    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (500, -100)

    # Link nodes
    links.new(bsdf.outputs['BSDF'], mix.inputs[1])
    links.new(glass.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])

    # Set blend mode for transparency
    mat.blend_method = 'BLEND'
    # shadow_method removed in Blender 5.0

    return mat


def main():
    """Main test function."""
    print("\n" + "="*60)
    print("Creating Water Sphere Test Scene")
    print("="*60 + "\n")

    # Clear scene
    clear_scene()

    # Setup scene
    setup_lighting()
    setup_camera()

    # Create water sphere
    print("Creating water sphere with wind-driven ripples...")
    sphere = create_single_water_sphere(
        size=2.0,
        ripple_scale=0.8,
        ripple_intensity=0.12,  # Visible ripples
        wind_angle=0.0,  # Wind from +X direction
        time=0.0,
        segments=24,  # Good quality for test
        rings=18,
        name="WaterSphere"
    )

    # Apply water material
    water_mat = create_water_material()
    sphere.data.materials.append(water_mat)

    # Animate
    print("Animating ripples...")
    animate_water_sphere(sphere, start_frame=1, end_frame=250, speed=0.3)

    # Set frame range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 250

    # Set viewport to rendered for visibility
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'

    # Save the blend file
    output_path = script_dir.parent / "water_sphere_test.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"Saved to: {output_path}")

    print("\n" + "="*60)
    print("Test Scene Created Successfully!")
    print("="*60)
    print("\nSphere Properties:")
    print(f"  - Name: {sphere.name}")
    print(f"  - Size: 2.0")
    print(f"  - Ripple Scale: 0.8")
    print(f"  - Ripple Intensity: 0.12")
    print(f"  - Wind Direction: +X (0 radians)")
    print("\nAnimation:")
    print(f"  - Frames: 1-250")
    print(f"  - Speed: 0.3")
    print("\nControls:")
    print("  - Press SPACE to play animation")
    print("  - Adjust 'Time' socket to see ripples")
    print("  - Change 'Wind Angle' to rotate wind direction")
    print("  - Adjust 'Ripple Intensity' for wave height")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
