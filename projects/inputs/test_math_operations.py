"""Test what the 3rd input on ShaderNodeMath does for different operations."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a node group for testing
tree = bpy.data.node_groups.new("MathOpTest", "GeometryNodeTree")

from lib.nodekit import NodeKit
nk = NodeKit(tree)
nk.clear()

print("\n" + "="*70)
print("TESTING ShaderNodeMath 3RD INPUT FOR DIFFERENT OPERATIONS")
print("="*70)

# Operations to test
operations = [
    "MULTIPLY",
    "ADD",
    "SUBTRACT",
    "DIVIDE",
    "SINE",
    "COSINE",
    "ARCTAN2",
    "POWER",
    "LOGARITHM",
    "MINIMUM",
    "MAXIMUM",
    "LESS_THAN",
    "GREATER_THAN",
]

# Check each operation
for op in operations:
    node = nk.n("ShaderNodeMath", f"Test_{op}", 0, 0)
    try:
        node.operation = op
        input_count = len(node.inputs)
        input_info = []
        for i, inp in enumerate(node.inputs):
            dv = inp.default_value
            input_info.append(f"[{i}]={dv:.2f}")
        print(f"  {op:15s}: {input_count} inputs | {', '.join(input_info)}")
    except Exception as e:
        print(f"  {op:15s}: ERROR - {e}")

print("\n" + "="*70)
print("TESTING MULTIPLY WITH DIFFERENT 3RD INPUT VALUES")
print("="*70)

# Create a test node
mult_node = nk.n("ShaderNodeMath", "MultTest", 0, 0)
mult_node.operation = "MULTIPLY"

# Test: 5 * 2 with different 3rd input values
test_cases = [
    ("5 * 2, input[2]=0.0", 5.0, 2.0, 0.0),
    ("5 * 2, input[2]=0.5", 5.0, 2.0, 0.5),
    ("5 * 2, input[2]=1.0", 5.0, 2.0, 1.0),
    ("5 * 2, input[2]=2.0", 5.0, 2.0, 2.0),
]

print("\nManually testing MULTIPLY operation (can't evaluate directly in Python):")
for desc, a, b, c in test_cases:
    mult_node.inputs[0].default_value = a
    mult_node.inputs[1].default_value = b
    mult_node.inputs[2].default_value = c
    print(f"  {desc}")
    print(f"    Input[0]={mult_node.inputs[0].default_value}")
    print(f"    Input[1]={mult_node.inputs[1].default_value}")
    print(f"    Input[2]={mult_node.inputs[2].default_value}")
    print(f"    Output[0].default_value={mult_node.outputs[0].default_value}")

print("\n" + "="*70)
print("CHECKING BLENDER DOCS/FOR ONLINE INFO")
print("="*70)

# Check if the 3rd input has any special name or tooltip
print("\nChecking input properties for MULTIPLY node:")
for i, inp in enumerate(mult_node.inputs):
    print(f"  Input [{i}]:")
    print(f"    name: {inp.name}")
    print(f"    identifier: {inp.identifier}")
    print(f"    type: {type(inp).__name__}")
    # Check for any special attributes
    attrs = [attr for attr in dir(inp) if not attr.startswith('_')]
    interesting = [a for a in attrs if not callable(getattr(inp, a, None))]
    print(f"    attributes: {interesting[:10]}...")  # First 10

print("\n" + "="*70)
print("CHECKING IF 3RD INPUT IS RELATED TO CLAMPING")
print("="*70)

# Check use_clamp and see if it affects inputs
mult_node.use_clamp = True
print(f"\nAfter setting use_clamp=True:")
for i, inp in enumerate(mult_node.inputs):
    print(f"  Input [{i}]: {inp.default_value}")

mult_node.use_clamp = False
print(f"\nAfter setting use_clamp=False:")
for i, inp in enumerate(mult_node.inputs):
    print(f"  Input [{i}]: {inp.default_value}")

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print("""
The 3rd input on ShaderNodeMath in Blender 5.0 has a default value of 0.5.
This may be:
1. A new feature (e.g., for operations like LERP/MIX that use 3 values)
2. A bug/oversight in Blender 5.0
3. Related to some internal operation

For MULTIPLY with 2 inputs, the 3rd input should NOT affect the calculation
if it's not connected. But we should explicitly set it to 0 to be safe.

RECOMMENDATION: Update the _math() function to explicitly set input[2] = 0.0
to ensure predictable behavior.
""")
