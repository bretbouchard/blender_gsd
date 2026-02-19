"""Investigate the ShaderNodeMath 3rd input in Blender 5.0."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a simple node group with just one math node
tree = bpy.data.node_groups.new("MathTest", "GeometryNodeTree")

# Add interface
tree.interface.new_socket("Value", in_out="INPUT", socket_type="NodeSocketFloat")
tree.interface.new_socket("Result", in_out="OUTPUT", socket_type="NodeSocketFloat")

# Create nodes
from lib.nodekit import NodeKit
nk = NodeKit(tree)
nk.clear()

gi = nk.group_input(0, 0)
go = nk.group_output(400, 0)

# Create a simple MULTIPLY math node
math_node = nk.n("ShaderNodeMath", "Test_Multiply", 200, 0)
math_node.operation = "MULTIPLY"

print("\n" + "="*60)
print("INVESTIGATING ShaderNodeMath INPUTS")
print("="*60)

# List all inputs on the math node
print(f"\nMath Node: {math_node.name}")
print(f"Operation: {math_node.operation}")
print(f"\nInputs ({len(math_node.inputs)} total):")

for i, inp in enumerate(math_node.inputs):
    print(f"  Input [{i}]: '{inp.name}'")
    print(f"    Type: {type(inp).__name__}")
    print(f"    Default value: {inp.default_value}")
    # Check if it's linked
    if inp.links:
        for link in inp.links:
            print(f"    Linked from: {link.from_node.name}.{link.from_socket.name}")
    else:
        print(f"    Not linked")

# Check if there's a use_clamp property
print(f"\nOther properties:")
print(f"  use_clamp: {getattr(math_node, 'use_clamp', 'N/A')}")

# Now let's check if setting values affects the 3rd input
print("\n" + "-"*60)
print("TESTING VALUE ASSIGNMENT")
print("-"*60)

# Set first two inputs
math_node.inputs[0].default_value = 10.0
math_node.inputs[1].default_value = 0.5

print("\nAfter setting Input[0]=10.0, Input[1]=0.5:")
for i, inp in enumerate(math_node.inputs):
    print(f"  Input [{i}] '{inp.name}': {inp.default_value}")

# Check if there's a way to clear the 3rd input
if len(math_node.inputs) > 2:
    print(f"\nTrying to set Input[2] to 0...")
    try:
        math_node.inputs[2].default_value = 0.0
        print(f"  Success! Input[2] = {math_node.inputs[2].default_value}")
    except Exception as e:
        print(f"  Error: {e}")

# Link group input to first two inputs
nk.link(gi.outputs["Value"], math_node.inputs[0])
nk.link(gi.outputs["Value"], math_node.inputs[1])
nk.link(math_node.outputs[0], go.inputs["Result"])

print("\n" + "-"*60)
print("AFTER LINKING")
print("-"*60)
for i, inp in enumerate(math_node.inputs):
    val = inp.default_value if not inp.is_linked else "(linked)"
    print(f"  Input [{i}] '{inp.name}': {val}")

# Check the output
print(f"\nOutput Value: {math_node.outputs[0].default_value}")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)
print("""
The 3rd input on ShaderNodeMath appears to be a Blender 5.0 addition.
Let's check what operations use it and if it affects our calculations.
""")
