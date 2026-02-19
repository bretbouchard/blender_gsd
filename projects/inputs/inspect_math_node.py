"""Inspect the Math node structure in Blender 5.0."""
import bpy

# Create a temporary node tree
nt = bpy.data.node_groups.new("Test", "GeometryNodeTree")

# Create a math node inside a shader node tree... wait, we need a shader tree
# Let's use a different approach - just look at the socket count

# Actually, let's look at the actual nodes created in our node group
import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

ng = create_input_node_group("Math_Inspect")

# Find a multiply math node
for node in ng.nodes:
    if node.type == 'MATH' and node.operation == 'MULTIPLY':
        print(f"\nNode: {node.name}")
        print(f"  Type: {node.type}")
        print(f"  Operation: {node.operation}")
        print(f"  Number of inputs: {len(node.inputs)}")
        for i, inp in enumerate(node.inputs):
            print(f"    Input {i}: '{inp.name}' - type: {inp.type}, default: {inp.default_value if hasattr(inp, 'default_value') else 'N/A'}")
        print(f"  Number of outputs: {len(node.outputs)}")
        for i, out in enumerate(node.outputs):
            print(f"    Output {i}: '{out.name}' - type: {out.type}")
        break

bpy.data.node_groups.remove(ng)
