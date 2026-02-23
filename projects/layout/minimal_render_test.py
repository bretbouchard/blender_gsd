"""
Minimal render test - render a single knob with simple setup.
"""

import bpy
import sys
import pathlib
from math import radians
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.layout.panel import PanelLayout, ElementSpec, ElementType
from lib.layout.standards import ElementSize
from lib.layout.renderer import LayoutRenderer


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for ng in bpy.data.node_groups:
        bpy.data.node_groups.remove(ng)
    if bpy.context.scene.world:
        bpy.data.worlds.remove(bpy.context.scene.world)


def minimal_render():
    print("\n" + "="*60)
    print("Minimal Render Test")
    print("="*60)

    clear_scene()

    # Create layout with ONE knob
    layout = PanelLayout("Test", width=50, height=50)
    spec = ElementSpec(
        name="knob",
        element_type=ElementType.KNOB,
        x=25, y=25,
        size=ElementSize.LG,
    )
    layout.add_element(spec)

    # Render
    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    print(f"\nCreated {len(objects)} objects")
    for obj in objects:
        print(f"  {obj.name}: location=({obj.location.x:.4f}, {obj.location.y:.4f}, {obj.location.z:.4f})")

    # Get FRESH depsgraph and calculate bounds
    depsgraph = bpy.context.evaluated_depsgraph_get()

    all_min_x, all_max_x = [], []
    all_min_y, all_max_y = [], []
    all_min_z, all_max_z = [], []

    for obj in objects:
        eval_obj = obj.evaluated_get(depsgraph)
        bbox = eval_obj.bound_box
        world_bbox = [obj.matrix_world @ Vector(corner) for corner in bbox]

        all_min_x.append(min(v.x for v in world_bbox))
        all_max_x.append(max(v.x for v in world_bbox))
        all_min_y.append(min(v.y for v in world_bbox))
        all_max_y.append(max(v.y for v in world_bbox))
        all_min_z.append(min(v.z for v in world_bbox))
        all_max_z.append(max(v.z for v in world_bbox))

    min_x, max_x = min(all_min_x), max(all_max_x)
    min_y, max_y = min(all_min_y), max(all_max_y)
    min_z, max_z = min(all_min_z), max(all_max_z)

    center = ((min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2)
    width = max_x - min_x
    height = max_z - min_z

    print(f"\nSubject bounds:")
    print(f"  X: {min_x*1000:.1f} to {max_x*1000:.1f} mm")
    print(f"  Y: {min_y*1000:.1f} to {max_y*1000:.1f} mm")
    print(f"  Z: {min_z*1000:.1f} to {max_z*1000:.1f} mm")
    print(f"  Center: ({center[0]*1000:.1f}, {center[1]*1000:.1f}, {center[2]*1000:.1f}) mm")
    print(f"  Size: {width*1000:.1f}mm x {height*1000:.1f}mm")

    # Setup scene for rendering
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True

    # Bright white world background
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.8, 0.8, 0.8, 1)  # Bright gray
    bg.inputs["Strength"].default_value = 2.0
    scene.world = world

    # Add camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Position camera
    x, y, z = center
    # Make sure we have a reasonable distance
    cam_distance = max(width, height) * 4
    if cam_distance < 0.15:
        cam_distance = 0.15  # Minimum 150mm for small objects

    # Camera from side-front angle to see the 3D form
    cam_obj.location = (x + cam_distance * 0.3, y - cam_distance * 0.8, z + cam_distance * 0.5)

    direction = Vector(center) - Vector(cam_obj.location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    print(f"\nCamera:")
    print(f"  Location: ({cam_obj.location.x*1000:.1f}, {cam_obj.location.y*1000:.1f}, {cam_obj.location.z*1000:.1f}) mm")
    print(f"  Distance: {cam_distance*1000:.1f}mm")
    print(f"  Direction: ({direction.x:.4f}, {direction.y:.4f}, {direction.z:.4f})")

    # Add multiple lights for better visibility
    # Key light
    key_data = bpy.data.lights.new("KeyLight", type='AREA')
    key_data.energy = 2000
    key_data.size = 0.3
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    key_obj.location = (x + 0.2, y - 0.15, z + 0.15)
    key_obj.rotation_euler = (radians(45), 0, radians(-30))
    scene.collection.objects.link(key_obj)

    # Fill light
    fill_data = bpy.data.lights.new("FillLight", type='AREA')
    fill_data.energy = 1000
    fill_data.size = 0.3
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.location = (x - 0.15, y - 0.1, z + 0.1)
    fill_obj.rotation_euler = (radians(60), 0, radians(30))
    scene.collection.objects.link(fill_obj)

    # Rim light from behind
    rim_data = bpy.data.lights.new("RimLight", type='AREA')
    rim_data.energy = 1500
    rim_data.size = 0.2
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    rim_obj.location = (x, y + 0.1, z + 0.1)
    rim_obj.rotation_euler = (radians(70), 0, radians(180))
    scene.collection.objects.link(rim_obj)

    print(f"Lights: Key, Fill, Rim added")

    # Render
    output_dir = ROOT / "projects" / "output" / "layout_previews"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "minimal_test.png"

    scene.render.filepath = str(output_path)
    print(f"\nRendering to: {output_path}")
    bpy.ops.render.render(write_still=True)

    print(f"\nDone! Saved to: {output_path}")

    # Save blend for inspection
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "minimal_test.blend"))


if __name__ == "__main__":
    minimal_render()
