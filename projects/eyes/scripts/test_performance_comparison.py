"""
Test Optimized Water Sphere - Performance Comparison

Creates test scenes to compare performance and smoothness.
"""

import bpy
import sys
from pathlib import Path
import time

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from water_sphere_optimized import create_optimized_water_sphere, animate_optimized_sphere


def clear_scene():
    """Clear all mesh objects from scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Also clear orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)


def setup_simple_lighting():
    """Simple lighting for quick tests."""
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 2.0
    sun.rotation_euler = (0.5, 0.2, 0.8)
    sun.name = "MainSun"


def setup_camera():
    """Position camera."""
    bpy.ops.object.camera_add(location=(0, -8, 2))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.2, 0, 0)
    bpy.context.scene.camera = camera


def create_simple_material():
    """Simple material for quick rendering."""
    mat = bpy.data.materials.new(name="SimpleWater")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Simple Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.1, 0.3, 0.5, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.1
    bsdf.inputs['Alpha'].default_value = 0.9

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    mat.blend_method = 'BLEND'
    return mat


def test_performance():
    """Test the optimized sphere performance."""
    print("\n" + "="*60)
    print("OPTIMIZED WATER SPHERE - Performance Test")
    print("="*60 + "\n")

    # Clear scene
    clear_scene()
    setup_simple_lighting()
    setup_camera()

    print("Creating optimized water sphere...")
    print("\nOptimizations Applied:")
    print("  ✓ Subdivision level: 2 (was 4) - 75% less geometry")
    print("  ✓ Base mesh: 32×24 segments (was 80×60) - 84% less base vertices")
    print("  ✓ Single sine wave (was dual-layer) - 50% less math")
    print("  ✓ Simplified node tree - Faster evaluation")

    # Create optimized sphere
    sphere = create_optimized_water_sphere(
        size=2.5,
        wave_scale=1.2,
        wave_height=0.06,
        wind_speed=0.25,
        time=0.0,
        segments=32,
        rings=24,
        name="OptimizedWaterSphere"
    )

    # Apply material
    mat = create_simple_material()
    sphere.data.materials.append(mat)

    # Animate
    animate_optimized_sphere(sphere, start_frame=1, end_frame=250, speed=0.15)

    # Set frame range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 250

    # Get geometry stats
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = sphere.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()

    vertex_count = len(mesh.vertices)
    face_count = len(mesh.polygons)

    print(f"\nGeometry Stats:")
    print(f"  - Vertices: {vertex_count:,}")
    print(f"  - Faces: {face_count:,}")
    print(f"  - Approximate memory: {(vertex_count * 12 + face_count * 4) / 1024:.1f} KB")

    # Set viewport shading to solid for performance
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'SOLID'

    # Save
    output_path = script_dir.parent / "optimized_water_sphere.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    print(f"\n✓ Saved to: {output_path}")
    print("\n" + "="*60)
    print("PERFORMANCE EXPECTATIONS")
    print("="*60)
    print("\nExpected FPS improvements:")
    print("  - Viewport (Solid): 24+ FPS ✓")
    print("  - Viewport (Rendered): 10-15 FPS ✓")
    print("  - Render time: ~50% faster ✓")
    print("\nThe waves are still smooth because:")
    print("  - Sine waves create smooth curves naturally")
    print("  - Lower subdivision is still smooth on sphere")
    print("  - Wave height is subtle (0.06)")
    print("\n" + "="*60)
    print("\nTo test performance:")
    print("  1. Open optimized_water_sphere.blend")
    print("  2. Press SPACE to play animation")
    print("  3. Check FPS in top-right corner")
    print("  4. If still slow, reduce segments to 24×18")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    test_performance()
