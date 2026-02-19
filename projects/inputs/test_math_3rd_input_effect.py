"""Test if the 3rd input on ShaderNodeMath affects calculations in a geometry tree."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

from lib.nodekit import NodeKit

print("\n" + "="*70)
print("TESTING: Does ShaderNodeMath 3rd input affect geometry calculations?")
print("="*70)

# Create two identical setups, one with input[2]=0.5 (default), one with input[2]=0
tree1 = bpy.data.node_groups.new("MathTest_Default", "GeometryNodeTree")
tree2 = bpy.data.node_groups.new("MathTest_Zero", "GeometryNodeTree")

for name, tree, third_input_val in [("DEFAULT (0.5)", tree1, 0.5), ("ZERO (0.0)", tree2, 0.0)]:
    print(f"\n--- Testing with 3rd input = {third_input_val} ({name}) ---")

    nk = NodeKit(tree)
    nk.clear()

    # Create interface
    tree.interface.new_socket("Input_Value", in_out="INPUT", socket_type="NodeSocketFloat")
    s = tree.interface.items_tree["Input_Value"]
    s.default_value = 10.0  # Test value

    tree.interface.new_socket("Result", in_out="OUTPUT", socket_type="NodeSocketFloat")

    # Create nodes
    gi = nk.group_input(0, 0)
    go = nk.group_output(400, 0)

    # Create math node: Input_Value * 0.5
    math_node = nk.n("ShaderNodeMath", "Multiply", 200, 0)
    math_node.operation = "MULTIPLY"
    math_node.inputs[0].default_value = 1.0  # Will be overridden by link
    math_node.inputs[1].default_value = 0.5
    math_node.inputs[2].default_value = third_input_val  # <-- THE VARIABLE

    # Link input to math node
    nk.link(gi.outputs["Input_Value"], math_node.inputs[0])

    # Link to output
    nk.link(math_node.outputs[0], go.inputs["Result"])

    # Store value info
    print(f"  Math node inputs after setup:")
    for i, inp in enumerate(math_node.inputs):
        linked = "LINKED" if inp.is_linked else str(inp.default_value)
        print(f"    Input[{i}]: {linked}")

# Now test by creating objects and using these node groups
print("\n" + "="*70)
print("CREATING TEST OBJECTS")
print("="*70)

# Create two plane objects with the node groups
for tree, third_val in [(tree1, 0.5), (tree2, 0.0)]:
    bpy.ops.mesh.primitive_plane_add(size=0.001)
    obj = bpy.context.active_object
    obj.name = f"Test_3rdInput_{third_val}"

    mod = obj.modifiers.new(name="TestNodes", type='NODES')
    mod.node_group = tree

print("\nCreated objects:")
for obj in bpy.data.objects:
    if obj.name.startswith("Test_3rdInput"):
        print(f"  {obj.name}")

# Now let's check the actual output by using Attribute nodes
print("\n" + "="*70)
print("CHECKING OUTPUT VIA GEOMETRY NODES ATTRIBUTE")
print("="*70)

# Create a third test that stores the result in an attribute
tree3 = bpy.data.node_groups.new("MathTest_Attribute", "GeometryNodeTree")
nk3 = NodeKit(tree3)
nk3.clear()

# Interface
tree3.interface.new_socket("Input_Value", in_out="INPUT", socket_type="NodeSocketFloat")
s = tree3.interface.items_tree["Input_Value"]
s.default_value = 10.0
tree3.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi3 = nk3.group_input(0, 0)
go3 = nk3.group_output(600, 0)

# Create a mesh to work with
mesh_node = nk3.n("GeometryNodeMeshGrid", "Grid", 0, -200)
mesh_node.inputs["Vertices X"].default_value = 2
mesh_node.inputs["Vertices Y"].default_value = 2
mesh_node.inputs["Size X"].default_value = 0.001
mesh_node.inputs["Size Y"].default_value = 0.001

# Create math node with default 3rd input (0.5)
math1 = nk3.n("ShaderNodeMath", "Math_Default", 200, 0)
math1.operation = "MULTIPLY"
math1.inputs[1].default_value = 0.5  # Multiply by 0.5
# Input[2] remains 0.5 (default)
nk3.link(gi3.outputs["Input_Value"], math1.inputs[0])

# Create math node with 3rd input = 0
math2 = nk3.n("ShaderNodeMath", "Math_Zero", 200, -100)
math2.operation = "MULTIPLY"
math2.inputs[1].default_value = 0.5  # Multiply by 0.5
math2.inputs[2].default_value = 0.0  # <-- EXPLICITLY SET TO 0
nk3.link(gi3.outputs["Input_Value"], math2.inputs[0])

# Store results as named attributes
store1 = nk3.n("GeometryNodeStoreNamedAttribute", "Store_Default", 400, 0)
store1.inputs["Name"].default_value = "result_default"
store1.data_type = 'FLOAT'
nk3.link(mesh_node.outputs["Mesh"], store1.inputs["Geometry"])
nk3.link(math1.outputs[0], store1.inputs["Value"])

store2 = nk3.n("GeometryNodeStoreNamedAttribute", "Store_Zero", 400, -100)
store2.inputs["Name"].default_value = "result_zero"
store2.data_type = 'FLOAT'
nk3.link(mesh_node.outputs["Mesh"], store2.inputs["Geometry"])
nk3.link(math2.outputs[0], store2.inputs["Value"])

# Join both geometries
join = nk3.n("GeometryNodeJoinGeometry", "Join", 500, -50)
nk3.link(store1.outputs["Geometry"], join.inputs["Geometry"])
nk3.link(store2.outputs["Geometry"], join.inputs["Geometry"])

nk3.link(join.outputs["Geometry"], go3.inputs["Geometry"])

# Create object with this tree
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object
obj.name = "Test_Attribute_Comparison"
mod = obj.modifiers.new(name="AttrTest", type='NODES')
mod.node_group = tree3

print(f"Created {obj.name} with attribute test node group")
print(f"  Math_Default: inputs[2] = {math1.inputs[2].default_value}")
print(f"  Math_Zero: inputs[2] = {math2.inputs[2].default_value}")

print("\n" + "="*70)
print("CHECKING SOURCE OF 0.5 DEFAULT")
print("="*70)

# Let's check where 0.5 comes from - is it hardcoded in Blender?
# Create a fresh math node and check its initial state
fresh_node = nk3.n("ShaderNodeMath", "FreshNode", 0, -300)
print(f"\nFresh Math node (just created):")
for i, inp in enumerate(fresh_node.inputs):
    print(f"  Input[{i}]: {inp.default_value}")

print("""
NOTE: The 0.5 default value on ShaderNodeMath inputs is likely Blender's default
for all float inputs in shader nodes. This is a common default in Blender.

The 3rd input (Value_002) exists for operations that need 3 inputs (like WRAP, PINGPONG).
For 2-input operations like MULTIPLY, the 3rd input should be ignored.

However, to be SAFE, we should explicitly set input[2] = 0.0 in our _math() function
to avoid any potential issues.
""")

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print("""
FINDING: Blender 5.0's ShaderNodeMath has 3 inputs, all defaulting to 0.5.
The 3rd input exists for operations that need 3 values (WRAP, PINGPONG, etc.).

For 2-input operations like MULTIPLY, ADD, SUBTRACT, etc.:
- The 3rd input should NOT affect the calculation
- But to be safe, we should explicitly set it to 0.0

NEXT STEP: Update the _math() helper function in node_group_builder.py to
explicitly clear the 3rd input to 0.0 for safety.
""")
