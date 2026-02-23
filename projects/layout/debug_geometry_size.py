"""
Debug script to understand why geometry is tiny despite correct parameters.
"""

import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.layout.standards import ElementSize, KNOB_SIZES
from lib.inputs import create_knob_node_group


def clear_scene():
    """Clear all objects and node groups."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for ng in bpy.data.node_groups:
        bpy.data.node_groups.remove(ng)


def test_direct_parameter_setting():
    """Test setting parameters directly on a fresh node group."""
    print("\n" + "="*60)
    print("TEST 1: Direct Parameter Setting")
    print("="*60)

    # Create node group fresh
    ng = create_knob_node_group("Test_Knob_Direct")

    # Print all interface items with name and identifier
    print("\nNode Group Interface Items:")
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET':
            print(f"  {item.name:30} | identifier: {item.identifier:15} | default: {getattr(item, 'default_value', 'N/A')}")

    # Create object
    bpy.ops.mesh.primitive_cube_add(size=0.001)
    obj = bpy.context.active_object
    obj.name = "Test_Knob_Direct"

    # Add modifier
    mod = obj.modifiers.new(name="Knob_Mod", type='NODES')
    mod.node_group = ng

    # Set a single parameter to see how it works
    print("\n\nSetting Top_Diameter to 28.0:")
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET' and item.name == "Top_Diameter":
            print(f"  Found: name={item.name}, identifier={item.identifier}")
            print(f"  Setting mod[{item.identifier}] = 28.0")
            mod[item.identifier] = 28.0
            break

    # Verify what was set
    print(f"\n  Verification: mod[{item.identifier}] = {mod[item.identifier]}")

    # Get geometry bounds after evaluation
    import bpy_extras.mesh_utils
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    # Get bounding box
    min_x = min(v.co.x for v in mesh.vertices)
    max_x = max(v.co.x for v in mesh.vertices)
    min_z = min(v.co.z for v in mesh.vertices)
    max_z = max(v.co.z for v in mesh.vertices)

    width_mm = (max_x - min_x) * 1000
    height_mm = (max_z - min_z) * 1000

    print(f"\n  Geometry bounds:")
    print(f"    Width: {width_mm:.1f}mm (expected: 28mm)")
    print(f"    Height: {height_mm:.1f}mm")

    eval_obj.to_mesh_clear()
    return width_mm


def test_all_parameters():
    """Test setting all diameter parameters."""
    print("\n" + "="*60)
    print("TEST 2: All Diameter Parameters")
    print("="*60)

    # Get LG knob size
    size = KNOB_SIZES[ElementSize.LG]
    print(f"\nLG Knob Size: diameter={size.diameter}mm, height={size.height}mm")

    # Create node group fresh
    ng = create_knob_node_group("Test_Knob_All")

    # Create object
    bpy.ops.mesh.primitive_cube_add(size=0.001)
    obj = bpy.context.active_object
    obj.name = "Test_Knob_All"

    # Add modifier
    mod = obj.modifiers.new(name="Knob_Mod", type='NODES')
    mod.node_group = ng

    # Set all parameters
    params = {
        "Top_Diameter": size.diameter,
        "A_Mid_Top_Diameter": size.diameter,
        "A_Bot_Top_Diameter": size.diameter,
        "AB_Junction_Diameter": size.diameter,
        "B_Mid_Bot_Diameter": size.diameter,
        "Bot_Diameter": size.diameter,
        "A_Top_Height": size.height * 0.15,
        "A_Mid_Height": size.height * 0.25,
        "A_Bot_Height": size.height * 0.1,
        "B_Top_Height": size.height * 0.1,
        "B_Mid_Height": size.height * 0.25,
        "B_Bot_Height": size.height * 0.15,
    }

    print("\nSetting parameters:")
    for param_name, param_value in params.items():
        for item in ng.interface.items_tree:
            if item.item_type == 'SOCKET' and item.name == param_name:
                mod[item.identifier] = param_value
                print(f"  {param_name}: {param_value} -> mod[{item.identifier}]")
                break

    # Verify settings
    print("\nVerifying modifier settings:")
    for item in ng.interface.items_tree:
        if item.item_type == 'SOCKET' and item.name in params:
            try:
                val = mod[item.identifier]
                print(f"  {item.name}: {val}")
            except:
                print(f"  {item.name}: ERROR reading")

    # Get geometry bounds
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    min_x = min(v.co.x for v in mesh.vertices)
    max_x = max(v.co.x for v in mesh.vertices)
    min_z = min(v.co.z for v in mesh.vertices)
    max_z = max(v.co.z for v in mesh.vertices)

    width_mm = (max_x - min_x) * 1000
    height_mm = (max_z - min_z) * 1000

    print(f"\n  Geometry bounds:")
    print(f"    Width: {width_mm:.1f}mm (expected: ~28mm)")
    print(f"    Height: {height_mm:.1f}mm (expected: ~22mm)")

    eval_obj.to_mesh_clear()
    return width_mm


def test_with_renderer():
    """Test using the actual LayoutRenderer."""
    print("\n" + "="*60)
    print("TEST 3: Using LayoutRenderer")
    print("="*60)

    from lib.layout.panel import PanelLayout, ElementSpec, ElementType
    from lib.layout.renderer import LayoutRenderer

    # Create simple layout with one knob
    layout = PanelLayout("Test", width=100, height=100)
    spec = ElementSpec(
        name="test",
        element_type=ElementType.KNOB,
        x=50, y=50,
        size=ElementSize.LG,
    )
    layout.add_element(spec)

    # Render
    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    # Find the knob object
    knob_obj = None
    for obj in objects:
        if "Knob" in obj.name:
            knob_obj = obj
            break

    if knob_obj:
        print(f"\nKnob object: {knob_obj.name}")
        print(f"Modifiers: {[m.name for m in knob_obj.modifiers]}")

        for mod in knob_obj.modifiers:
            if mod.type == 'NODES':
                print(f"\n  Modifier: {mod.name}")
                print(f"  Node Group: {mod.node_group.name}")

                # Print all parameter values
                ng = mod.node_group
                print("\n  Parameter values:")
                for item in ng.interface.items_tree:
                    if item.item_type == 'SOCKET':
                        try:
                            val = mod[item.identifier]
                            print(f"    {item.name}: {val}")
                        except:
                            pass

        # Get geometry bounds
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = knob_obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()

        min_x = min(v.co.x for v in mesh.vertices)
        max_x = max(v.co.x for v in mesh.vertices)
        min_z = min(v.co.z for v in mesh.vertices)
        max_z = max(v.co.z for v in mesh.vertices)

        width_mm = (max_x - min_x) * 1000
        height_mm = (max_z - min_z) * 1000

        print(f"\n  Geometry bounds:")
        print(f"    Width: {width_mm:.1f}mm (expected: ~28mm)")
        print(f"    Height: {height_mm:.1f}mm (expected: ~22mm)")

        eval_obj.to_mesh_clear()
        return width_mm

    return 0


def main():
    print("="*60)
    print("Geometry Size Debug")
    print("="*60)

    # Test 1: Direct setting
    clear_scene()
    width1 = test_direct_parameter_setting()

    # Test 2: All parameters
    clear_scene()
    width2 = test_all_parameters()

    # Test 3: Renderer
    clear_scene()
    width3 = test_with_renderer()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Test 1 (Direct):    {width1:.1f}mm")
    print(f"Test 2 (All Params): {width2:.1f}mm")
    print(f"Test 3 (Renderer):  {width3:.1f}mm")
    print(f"Expected:           28.0mm")


if __name__ == "__main__":
    main()
