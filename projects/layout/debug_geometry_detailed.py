"""
Debug geometry visibility - check what objects look like.
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


def debug_geometry():
    print("\n" + "="*60)
    print("Debug Geometry Visibility")
    print("="*60)

    clear_scene()

    # Create layout with ONE knob
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

    # Get fresh depsgraph
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for obj in objects:
        print(f"\n{'='*50}")
        print(f"Object: {obj.name}")
        print(f"  Location: ({obj.location.x*1000:.1f}, {obj.location.y*1000:.1f}, {obj.location.z*1000:.1f}) mm")
        print(f"  Scale: ({obj.scale.x:.4f}, {obj.scale.y:.4f}, {obj.scale.z:.4f})")

        # Evaluate and get bounds
        eval_obj = obj.evaluated_get(depsgraph)
        bbox = eval_obj.bound_box
        world_bbox = [obj.matrix_world @ Vector(corner) for corner in bbox]

        min_x = min(v.x for v in world_bbox)
        max_x = max(v.x for v in world_bbox)
        min_y = min(v.y for v in world_bbox)
        max_y = max(v.y for v in world_bbox)
        min_z = min(v.z for v in world_bbox)
        max_z = max(v.z for v in world_bbox)

        width = max_x - min_x
        depth = max_y - min_y
        height = max_z - min_z

        print(f"  World bounds:")
        print(f"    X: {min_x*1000:.1f} to {max_x*1000:.1f} mm (width: {width*1000:.1f}mm)")
        print(f"    Y: {min_y*1000:.1f} to {max_y*1000:.1f} mm (depth: {depth*1000:.1f}mm)")
        print(f"    Z: {min_z*1000:.1f} to {max_z*1000:.1f} mm (height: {height*1000:.1f}mm)")

        # Get mesh info
        mesh = eval_obj.to_mesh()
        print(f"  Vertices: {len(mesh.vertices)}")
        print(f"  Faces: {len(mesh.polygons)}")
        eval_obj.to_mesh_clear()

        # Check modifiers
        for mod in obj.modifiers:
            print(f"  Modifier: {mod.name} ({mod.type})")


if __name__ == "__main__":
    debug_geometry()
