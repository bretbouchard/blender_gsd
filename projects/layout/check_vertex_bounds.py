"""
Check actual vertex positions of evaluated geometry.
"""

import bpy
import sys
import pathlib
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


def check_vertices():
    print("\n" + "="*60)
    print("Check Vertex Positions")
    print("="*60)

    clear_scene()

    # Create layout
    layout = PanelLayout("Test", width=50, height=50)
    spec = ElementSpec(
        name="test",
        element_type=ElementType.KNOB,
        x=25, y=25,
        size=ElementSize.LG,
    )
    layout.add_element(spec)

    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    depsgraph = bpy.context.evaluated_depsgraph_get()

    for obj in objects:
        if "Knob" not in obj.name:
            continue

        print(f"\nObject: {obj.name}")
        print(f"Location: ({obj.location.x:.6f}, {obj.location.y:.6f}, {obj.location.z:.6f})")

        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()

        print(f"\nFirst 20 vertex positions (WORLD space):")
        for i, v in enumerate(mesh.vertices):
            if i >= 20:
                break
            # Convert to world space
            world_pos = obj.matrix_world @ v.co
            print(f"  v{i}: ({world_pos.x*1000:.2f}, {world_pos.y*1000:.2f}, {world_pos.z*1000:.2f}) mm")

        # Calculate actual bounds from vertices
        all_x = []
        all_y = []
        all_z = []
        for v in mesh.vertices:
            world_pos = obj.matrix_world @ v.co
            all_x.append(world_pos.x)
            all_y.append(world_pos.y)
            all_z.append(world_pos.z)

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        min_z, max_z = min(all_z), max(all_z)

        print(f"\nActual vertex bounds (world space):")
        print(f"  X: {min_x*1000:.1f} to {max_x*1000:.1f} mm (width: {(max_x-min_x)*1000:.1f}mm)")
        print(f"  Y: {min_y*1000:.1f} to {max_y*1000:.1f} mm (depth: {(max_y-min_y)*1000:.1f}mm)")
        print(f"  Z: {min_z*1000:.1f} to {max_z*1000:.1f} mm (height: {(max_z-min_z)*1000:.1f}mm)")

        # Compare with bound_box
        bbox = eval_obj.bound_box
        bbox_min_x = min((obj.matrix_world @ Vector(corner)).x for corner in bbox)
        bbox_max_x = max((obj.matrix_world @ Vector(corner)).x for corner in bbox)

        print(f"\nBounding box says X width: {(bbox_max_x - bbox_min_x)*1000:.1f}mm")
        print(f"Actual vertex X width:     {(max_x - min_x)*1000:.1f}mm")

        eval_obj.to_mesh_clear()


if __name__ == "__main__":
    check_vertices()
