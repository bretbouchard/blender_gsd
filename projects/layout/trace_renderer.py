"""
Trace through LayoutRenderer to find the bug.
"""

import bpy
import sys
import pathlib
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.layout.panel import PanelLayout, ElementSpec, ElementType
from lib.layout.standards import ElementSize, KNOB_SIZES
from lib.layout.renderer import LayoutRenderer
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


def trace_renderer():
    print("\n" + "="*60)
    print("Trace LayoutRenderer")
    print("="*60)

    clear_scene()

    # Create layout
    layout = PanelLayout("Trace", width=50, height=50)
    spec = ElementSpec(
        name="test",
        element_type=ElementType.KNOB,
        x=25, y=25,
        size=ElementSize.LG,
    )
    layout.add_element(spec)

    # Get size params manually (same as renderer does)
    size = KNOB_SIZES[ElementSize.LG]

    # Create node group directly FIRST (simulating renderer behavior)
    print("\n1. Creating node group 'Knob_lg' directly...")
    ng = create_knob_node_group("Knob_lg")
    print(f"   Created: {ng.name}")

    # Check default values
    print("\n2. Node group default values:")
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET' and 'Diameter' in item.name:
            print(f"   {item.name}: {item.default_value}")

    # Now create object and add modifier manually
    print("\n3. Creating object and adding modifier...")
    bpy.ops.mesh.primitive_cube_add(size=0.001)
    obj = bpy.context.active_object
    obj.name = "Trace_Knob"
    obj.location = (0.025, 0, -0.025)

    mod = obj.modifiers.new(name="Knob_lg", type='NODES')
    mod.node_group = ng
    print(f"   Modifier: {mod.name}, NodeGroup: {ng.name}")

    # Set parameters manually (exactly as renderer does)
    print("\n4. Setting parameters (as renderer does)...")
    params = {
        "Top_Diameter": size.diameter,
        "A_Mid_Top_Diameter": size.diameter,
        "A_Bot_Top_Diameter": size.diameter,
        "AB_Junction_Diameter": size.diameter,
        "B_Mid_Bot_Diameter": size.diameter,
        "Bot_Diameter": size.diameter,
    }

    for param_name, param_value in params.items():
        for item in ng.interface.items_tree:
            if item.item_type == 'SOCKET' and item.name == param_name:
                print(f"   Setting {param_name} = {param_value} via identifier {item.identifier}")
                mod[item.identifier] = param_value
                break

    # Verify settings
    print("\n5. Verifying modifier values:")
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET' and 'Diameter' in item.name:
            val = mod[item.identifier]
            print(f"   {item.name}: {val}")

    # Evaluate geometry
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    all_x = [v.co.x for v in mesh.vertices]
    min_x, max_x = min(all_x), max(all_x)

    print(f"\n6. Evaluated geometry:")
    print(f"   Width: {(max_x - min_x)*1000:.1f}mm (expected: 28mm)")

    eval_obj.to_mesh_clear()

    # Now test using LayoutRenderer
    print("\n" + "="*60)
    print("Now testing via LayoutRenderer")
    print("="*60)

    clear_scene()

    layout2 = PanelLayout("Trace2", width=50, height=50)
    spec2 = ElementSpec(
        name="test2",
        element_type=ElementType.KNOB,
        x=25, y=25,
        size=ElementSize.LG,
    )
    layout2.add_element(spec2)

    renderer = LayoutRenderer(layout2)
    objects = renderer.render()

    # Find knob
    knob = None
    for obj in objects:
        if "Knob" in obj.name:
            knob = obj
            break

    if knob:
        print(f"\nKnob object: {knob.name}")
        print(f"Location: ({knob.location.x:.4f}, {knob.location.y:.4f}, {knob.location.z:.4f})")

        for mod in knob.modifiers:
            if mod.type == 'NODES':
                print(f"\nModifier: {mod.name}")
                print(f"Node Group: {mod.node_group.name}")

                ng = mod.node_group
                print("\nModifier parameter values:")
                for item in ng.interface.items_tree:
                    if item.item_type == 'SOCKET' and 'Diameter' in item.name:
                        try:
                            val = mod[item.identifier]
                            print(f"  {item.name}: {val}")
                        except Exception as e:
                            print(f"  {item.name}: ERROR - {e}")

        # Evaluate
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = knob.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()

        all_x = [v.co.x for v in mesh.vertices]
        min_x, max_x = min(all_x), max(all_x)

        print(f"\nEvaluated geometry width: {(max_x - min_x)*1000:.1f}mm (expected: 28mm)")

        eval_obj.to_mesh_clear()


if __name__ == "__main__":
    trace_renderer()
