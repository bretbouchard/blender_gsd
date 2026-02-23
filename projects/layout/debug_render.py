"""
Debug render to understand why the image is black.
"""

import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.layout.standards import ElementSize, KNOB_SIZES
from lib.layout.panel import PanelLayout, ElementSpec, ElementType
from lib.layout.renderer import LayoutRenderer
from math import radians
from mathutils import Vector


def clear_scene():
    """Clear all objects, meshes, materials, and node groups."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for ng in bpy.data.node_groups:
        bpy.data.node_groups.remove(ng)


def debug_render():
    """Debug the render setup."""
    print("\n" + "="*60)
    print("Debug Render Setup")
    print("="*60)

    clear_scene()

    # Create a simple layout with one knob
    layout = PanelLayout("Debug", width=50, height=50)
    spec = ElementSpec(
        name="test_knob",
        element_type=ElementType.KNOB,
        x=25, y=25,
        size=ElementSize.LG,
    )
    layout.add_element(spec)

    # Render the layout
    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    print(f"\nCreated {len(objects)} objects:")
    for obj in objects:
        print(f"  {obj.name}: location=({obj.location.x:.4f}, {obj.location.y:.4f}, {obj.location.z:.4f})")

    # Find knob object and check its evaluated geometry
    knob_obj = None
    for obj in objects:
        if "Knob" in obj.name:
            knob_obj = obj
            break

    if knob_obj:
        # Evaluate geometry
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = knob_obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()

        # Get bounds in world space
        min_x = min(v.co.x for v in mesh.vertices)
        max_x = max(v.co.x for v in mesh.vertices)
        min_y = min(v.co.y for v in mesh.vertices)
        max_y = max(v.co.y for v in mesh.vertices)
        min_z = min(v.co.z for v in mesh.vertices)
        max_z = max(v.co.z for v in mesh.vertices)

        print(f"\nKnob geometry bounds (local):")
        print(f"  X: {min_x*1000:.1f} to {max_x*1000:.1f} mm (width: {(max_x-min_x)*1000:.1f}mm)")
        print(f"  Y: {min_y*1000:.1f} to {max_y*1000:.1f} mm")
        print(f"  Z: {min_z*1000:.1f} to {max_z*1000:.1f} mm (height: {(max_z-min_z)*1000:.1f}mm)")
        print(f"  Vertices: {len(mesh.vertices)}")

        eval_obj.to_mesh_clear()

    # Calculate overall scene bounds
    all_min_x = min(obj.location.x for obj in objects)
    all_max_x = max(obj.location.x for obj in objects)
    all_min_z = min(obj.location.z for obj in objects)
    all_max_z = max(obj.location.z for obj in objects)

    print(f"\nObject locations bounds:")
    print(f"  X: {all_min_x:.4f} to {all_max_x:.4f} ({(all_max_x-all_min_x)*1000:.1f}mm)")
    print(f"  Z: {all_min_z:.4f} to {all_max_z:.4f} ({(all_max_z-all_min_z)*1000:.1f}mm)")

    # Calculate subject center and size
    subject_center = ((all_min_x + all_max_x) / 2, 0, (all_min_z + all_max_z) / 2)
    actual_width = all_max_x - all_min_x
    actual_height = all_max_z - all_min_z

    print(f"\nSubject center: ({subject_center[0]:.4f}, {subject_center[1]:.4f}, {subject_center[2]:.4f})")
    print(f"Subject size: {actual_width*1000:.1f}mm x {actual_height*1000:.1f}mm")

    # Setup render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.cycles.samples = 64  # Lower for debug
    scene.cycles.use_denoising = True

    # World background
    if scene.world:
        bpy.data.worlds.remove(scene.world)
    world = bpy.data.worlds.new("Debug_World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.1, 0.1, 0.1, 1)  # Brighter for debug
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world

    # Add camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Position camera - use a fixed distance that makes sense for small objects
    # The knob is about 28mm wide, so we need to be close
    x, y, z = subject_center
    cam_distance = max(actual_width, actual_height) * 3  # 3x the subject size

    # Camera at negative Y (in front) and slightly above
    cam_obj.location = (x, y - cam_distance, z + cam_distance * 0.3)

    print(f"\nCamera position: ({cam_obj.location.x:.4f}, {cam_obj.location.y:.4f}, {cam_obj.location.z:.4f})")
    print(f"Camera distance: {cam_distance*1000:.1f}mm")

    # Point camera at subject
    direction = Vector((x, y, z)) - Vector(cam_obj.location)
    print(f"Direction to subject: ({direction.x:.4f}, {direction.y:.4f}, {direction.z:.4f})")
    print(f"Direction length: {direction.length:.4f}m ({direction.length*1000:.1f}mm)")

    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    # Add a simple light - KEY LIGHT
    light_data = bpy.data.lights.new("KeyLight", type='AREA')
    light_data.energy = 5000  # Very bright for debug
    light_data.color = (1.0, 1.0, 1.0)
    light_data.size = 0.5

    light_obj = bpy.data.objects.new("KeyLight", light_data)
    light_obj.location = (x + 0.3, y - 0.3, z + 0.5)
    light_obj.rotation_euler = (radians(45), 0, radians(45))
    scene.collection.objects.link(light_obj)

    print(f"\nLight position: ({light_obj.location.x:.4f}, {light_obj.location.y:.4f}, {light_obj.location.z:.4f})")

    # Add a FILL LIGHT
    fill_data = bpy.data.lights.new("FillLight", type='AREA')
    fill_data.energy = 2000
    fill_data.color = (1.0, 1.0, 1.0)
    fill_data.size = 0.5

    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.location = (x - 0.3, y - 0.2, z + 0.3)
    fill_obj.rotation_euler = (radians(60), 0, radians(-30))
    scene.collection.objects.link(fill_obj)

    # Render
    output_dir = ROOT / "projects" / "output" / "layout_previews"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "debug_render.png"

    bpy.context.scene.render.filepath = str(output_path)
    print(f"\nRendering to: {output_path}")
    bpy.ops.render.render(write_still=True)

    print(f"Render complete!")

    # Also save blend file for inspection
    blend_path = output_dir / "debug_render.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"Blend file saved: {blend_path}")

    return output_path


if __name__ == "__main__":
    debug_render()
