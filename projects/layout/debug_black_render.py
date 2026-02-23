"""
Debug why renders are still black despite correct geometry.
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


def debug_render():
    print("\n" + "="*60)
    print("Debug Black Render")
    print("="*60)

    clear_scene()

    # Create simple layout with ONE knob only
    layout = PanelLayout("Debug", width=50, height=50)
    spec = ElementSpec(
        name="test",
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
        print(f"  {obj.name}")

    # Get actual geometry bounds
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for obj in objects:
        eval_obj = obj.evaluated_get(depsgraph)
        bbox = eval_obj.bound_box

        # World space bounds
        world_bbox = [obj.matrix_world @ Vector(corner) for corner in bbox]
        min_x = min(v.x for v in world_bbox)
        max_x = max(v.x for v in world_bbox)
        min_y = min(v.y for v in world_bbox)
        max_y = max(v.y for v in world_bbox)
        min_z = min(v.z for v in world_bbox)
        max_z = max(v.z for v in world_bbox)

        print(f"\n{obj.name} world bounds:")
        print(f"  X: {min_x*1000:.1f} to {max_x*1000:.1f} mm")
        print(f"  Y: {min_y*1000:.1f} to {max_y*1000:.1f} mm")
        print(f"  Z: {min_z*1000:.1f} to {max_z*1000:.1f} mm")

    # Calculate subject bounds
    all_min_x = []
    all_max_x = []
    all_min_y = []
    all_max_y = []
    all_min_z = []
    all_max_z = []

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

    min_x = min(all_min_x)
    max_x = max(all_max_x)
    min_y = min(all_min_y)
    max_y = max(all_max_y)
    min_z = min(all_min_z)
    max_z = max(all_max_z)

    center = ((min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2)
    width = max_x - min_x
    height = max_z - min_z

    print(f"\nOverall bounds:")
    print(f"  Center: ({center[0]*1000:.1f}, {center[1]*1000:.1f}, {center[2]*1000:.1f}) mm")
    print(f"  Size: {width*1000:.1f}mm x {height*1000:.1f}mm")

    # Setup render - use EEVEE for faster debugging
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'  # EEVEE in Blender 5.0
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    # Bright world background
    if scene.world:
        bpy.data.worlds.remove(scene.world)
    world = bpy.data.worlds.new("Debug_World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1)  # Bright gray
    bg.inputs["Strength"].default_value = 5.0  # Very bright
    scene.world = world

    # Camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    x, y, z = center
    cam_distance = max(width, height) * 3
    if cam_distance < 0.1:
        cam_distance = 0.1

    cam_obj.location = (x, y - cam_distance, z + cam_distance * 0.3)

    direction = Vector(center) - Vector(cam_obj.location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    print(f"\nCamera:")
    print(f"  Location: ({cam_obj.location.x*1000:.1f}, {cam_obj.location.y*1000:.1f}, {cam_obj.location.z*1000:.1f}) mm")
    print(f"  Distance: {cam_distance*1000:.1f}mm")

    # Simple point light
    light_data = bpy.data.lights.new("Light", type='POINT')
    light_data.energy = 10000  # Very bright
    light_data.color = (1, 1, 1)
    light_obj = bpy.data.objects.new("Light", light_data)
    light_obj.location = (x, y - cam_distance * 0.5, z + 0.2)
    scene.collection.objects.link(light_obj)

    print(f"  Light at: ({light_obj.location.x*1000:.1f}, {light_obj.location.y*1000:.1f}, {light_obj.location.z*1000:.1f}) mm")

    # Render
    output_dir = ROOT / "projects" / "output" / "layout_previews"
    output_path = output_dir / "debug_eevee.png"

    bpy.context.scene.render.filepath = str(output_path)
    print(f"\nRendering to: {output_path}")
    bpy.ops.render.render(write_still=True)

    print(f"Done!")

    # Save blend
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "debug_eevee.blend"))


if __name__ == "__main__":
    debug_render()
