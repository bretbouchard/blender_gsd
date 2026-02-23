"""
Verify that renderer parameters are being set correctly.
"""

import bpy
import sys
import pathlib
from math import radians
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.layout.panel import PanelLayout, ElementSpec, ElementType
from lib.layout.standards import ElementSize, KNOB_SIZES
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


def verify_renderer():
    print("\n" + "="*60)
    print("Verify Renderer Parameters")
    print("="*60)

    clear_scene()

    # Create layout with LG knob
    layout = PanelLayout("Verify", width=50, height=50)
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

    # Find knob
    knob = None
    for obj in objects:
        if "Knob" in obj.name:
            knob = obj
            break

    if not knob:
        print("ERROR: No knob found!")
        return

    print(f"\nKnob: {knob.name}")
    print(f"Modifiers: {[m.name for m in knob.modifiers]}")

    # Check modifier parameters
    for mod in knob.modifiers:
        if mod.type == 'NODES':
            print(f"\nModifier: {mod.name}")
            print(f"Node Group: {mod.node_group.name if mod.node_group else 'None'}")

            if mod.node_group:
                ng = mod.node_group
                print("\nNode Group Interface:")
                for item in ng.interface.items_tree:
                    if item.item_type == 'SOCKET' and 'Diameter' in item.name:
                        print(f"  {item.name}: default={item.default_value}")

                print("\nModifier Parameter Values:")
                for item in ng.interface.items_tree:
                    if item.item_type == 'SOCKET' and 'Diameter' in item.name:
                        try:
                            val = mod[item.identifier]
                            print(f"  {item.name}: {val}")
                        except Exception as e:
                            print(f"  {item.name}: ERROR - {e}")

    # Now evaluate geometry
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_knob = knob.evaluated_get(depsgraph)
    mesh = eval_knob.to_mesh()

    min_x = min(v.co.x for v in mesh.vertices)
    max_x = max(v.co.x for v in mesh.vertices)
    min_z = min(v.co.z for v in mesh.vertices)
    max_z = max(v.co.z for v in mesh.vertices)

    print(f"\nEvaluated Geometry (local):")
    print(f"  Width: {(max_x - min_x)*1000:.1f}mm (expected: 28mm)")
    print(f"  Height: {(max_z - min_z)*1000:.1f}mm")
    print(f"  Vertices: {len(mesh.vertices)}")

    eval_knob.to_mesh_clear()

    # Also test by directly creating a knob with explicit parameters
    print("\n" + "-"*60)
    print("DIRECT TEST: Create knob with explicit params")
    print("-"*60)

    from lib.inputs import create_knob_node_group

    # Create fresh node group
    ng = create_knob_node_group("Direct_Test_Knob")

    # Create object
    bpy.ops.mesh.primitive_cube_add(size=0.001)
    obj = bpy.context.active_object
    obj.name = "Direct_Test"

    # Add modifier
    mod = obj.modifiers.new(name="Direct_Mod", type='NODES')
    mod.node_group = ng

    # Set ALL diameter params explicitly
    size = KNOB_SIZES[ElementSize.LG]
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET' and item.name == "Top_Diameter":
            mod[item.identifier] = size.diameter
        if item.item_type == 'SOCKET' and item.name == "A_Mid_Top_Diameter":
            mod[item.identifier] = size.diameter
        if item.item_type == 'SOCKET' and item.name == "A_Bot_Top_Diameter":
            mod[item.identifier] = size.diameter
        if item.item_type == 'SOCKET' and item.name == "AB_Junction_Diameter":
            mod[item.identifier] = size.diameter
        if item.item_type == 'SOCKET' and item.name == "B_Mid_Bot_Diameter":
            mod[item.identifier] = size.diameter
        if item.item_type == 'SOCKET' and item.name == "Bot_Diameter":
            mod[item.identifier] = size.diameter

    # Check what was set
    print(f"\nDirect test - modifier values:")
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET' and 'Diameter' in item.name:
            val = mod[item.identifier]
            print(f"  {item.name}: {val}")

    # Evaluate
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    min_x = min(v.co.x for v in mesh.vertices)
    max_x = max(v.co.x for v in mesh.vertices)

    print(f"\nDirect test geometry:")
    print(f"  Width: {(max_x - min_x)*1000:.1f}mm (expected: 28mm)")

    eval_obj.to_mesh_clear()


if __name__ == "__main__":
    verify_renderer()
