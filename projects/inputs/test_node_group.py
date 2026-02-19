"""
Test script for Input Node Group

Creates an object with the Input_ZoneBased node group
and saves it so you can see all exposed parameters in the modifier.
"""

import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group


def clear_scene():
    """Clear all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def test_node_group():
    """Test the input node group with exposed parameters."""

    clear_scene()

    # Create the node group
    print("Creating Input_ZoneBased node group...")
    node_group = create_input_node_group("Input_ZoneBased")
    print(f"Created node group with {len(list(node_group.interface.items_tree))} interface items")

    # List all inputs
    print("\n=== EXPOSED INPUTS ===")
    for item in node_group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            # Different socket types have different attributes
            min_val = getattr(item, 'min_value', 'N/A')
            max_val = getattr(item, 'max_value', 'N/A')
            print(f"  - {item.name}: default={item.default_value}, min={min_val}, max={max_val}")

    # Show frame hierarchy
    print("\n=== FRAME ORGANIZATION ===")
    frames = [n for n in node_group.nodes if n.type == 'FRAME']
    for frame in sorted(frames, key=lambda f: f.label or ""):
        children = [n for n in node_group.nodes if n.parent == frame]
        child_count = len(children)
        # Check for nested frames
        nested = [n for n in children if n.type == 'FRAME']
        print(f"  └── {frame.label} ({child_count} nodes, {len(nested)} nested frames)")
        for nested_frame in nested:
            nested_children = [n for n in node_group.nodes if n.parent == nested_frame]
            print(f"      └── {nested_frame.label} ({len(nested_children)} nodes)")

    # Create an empty mesh object
    mesh = bpy.data.meshes.new("Knob_Mesh")
    obj = bpy.data.objects.new("Test_Knob", mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Add Geometry Nodes modifier with our node group
    mod = obj.modifiers.new("GeometryNodes", "NODES")
    mod.node_group = node_group

    print("\n=== MODIFIER INPUTS ===")
    # The inputs are now accessible via the modifier
    # In Blender 5.x, we can set them like this:
    for i, item in enumerate(node_group.interface.items_tree):
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            # Get the socket identifier for the modifier
            identifier = item.identifier
            print(f"  [{i}] {item.name} (identifier: {identifier})")

    # Save the file
    output_path = pathlib.Path(__file__).parent.parent / "output" / "test_node_group.blend"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"\nSaved to: {output_path}")
    print("\n=== NEXT STEPS ===")
    print("1. Open the blend file in Blender")
    print("2. Select the 'Test_Knob' object")
    print("3. Go to the Modifiers tab")
    print("4. You will see ALL the exposed inputs you can adjust:")
    print("   - Height, Width, Segments")
    print("   - Zone A: Height, Widths, Top/Mid/Bot heights and styles")
    print("   - Zone A: Knurling (enable, count, depth, width, profile)")
    print("   - Zone B: Same parameters")
    print("   - Material: Color, Metallic, Roughness")

    return True


if __name__ == "__main__":
    test_node_group()
