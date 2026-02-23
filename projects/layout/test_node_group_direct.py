"""
Test node group directly without LayoutRenderer.
This isolates whether the issue is in the renderer or the node group.
"""

import bpy
import sys
import pathlib
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.layout.standards import ElementSize, KNOB_SIZES
from lib.inputs import create_knob_node_group


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for ng in bpy.data.node_groups:
        bpy.data.node_groups.remove(ng)


def test_direct():
    print("\n" + "="*60)
    print("Test Node Group Directly (No LayoutRenderer)")
    print("="*60)

    clear_scene()

    # Get LG size
    size = KNOB_SIZES[ElementSize.LG]
    print(f"\nLG Knob: diameter={size.diameter}mm, height={size.height}mm")

    # Create node group
    ng = create_knob_node_group("Direct_Knob")
    print(f"\nCreated node group: {ng.name}")

    # Print default values
    print("\nDefault interface values:")
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET' and 'Diameter' in item.name:
            print(f"  {item.name}: {item.default_value}")

    # Create object
    bpy.ops.mesh.primitive_cube_add(size=0.001)
    obj = bpy.context.active_object
    obj.name = "Direct_Test_Knob"
    obj.location = (0, 0, 0)

    # Add modifier
    mod = obj.modifiers.new(name="Knob_Mod", type='NODES')
    mod.node_group = ng

    # Set ALL diameter params
    print("\nSetting parameters:")
    params_set = {}
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET':
            if item.name == "Top_Diameter":
                mod[item.identifier] = size.diameter
                params_set[item.name] = size.diameter
            elif item.name == "A_Mid_Top_Diameter":
                mod[item.identifier] = size.diameter
                params_set[item.name] = size.diameter
            elif item.name == "A_Bot_Top_Diameter":
                mod[item.identifier] = size.diameter
                params_set[item.name] = size.diameter
            elif item.name == "AB_Junction_Diameter":
                mod[item.identifier] = size.diameter
                params_set[item.name] = size.diameter
            elif item.name == "B_Mid_Bot_Diameter":
                mod[item.identifier] = size.diameter
                params_set[item.name] = size.diameter
            elif item.name == "Bot_Diameter":
                mod[item.identifier] = size.diameter
                params_set[item.name] = size.diameter

    for name, val in params_set.items():
        print(f"  {name}: {val}")

    # Verify what was set
    print("\nVerifying modifier values:")
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET' and 'Diameter' in item.name:
            val = mod[item.identifier]
            print(f"  {item.name}: {val}")

    # Evaluate geometry
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    # Get bounds from vertices
    all_x = [v.co.x for v in mesh.vertices]
    all_y = [v.co.y for v in mesh.vertices]
    all_z = [v.co.z for v in mesh.vertices]

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    min_z, max_z = min(all_z), max(all_z)

    print(f"\nEvaluated geometry bounds (LOCAL space):")
    print(f"  X: {min_x*1000:.1f} to {max_x*1000:.1f} mm (width: {(max_x-min_x)*1000:.1f}mm)")
    print(f"  Y: {min_y*1000:.1f} to {max_y*1000:.1f} mm (depth: {(max_y-min_y)*1000:.1f}mm)")
    print(f"  Z: {min_z*1000:.1f} to {max_z*1000:.1f} mm (height: {(max_z-min_z)*1000:.1f}mm)")
    print(f"  Vertices: {len(mesh.vertices)}")

    # Print some vertex positions
    print("\nFirst 10 vertex positions (local):")
    for i, v in enumerate(mesh.vertices[:10]):
        print(f"  v{i}: ({v.co.x*1000:.2f}, {v.co.y*1000:.2f}, {v.co.z*1000:.2f}) mm")

    eval_obj.to_mesh_clear()


if __name__ == "__main__":
    test_direct()
