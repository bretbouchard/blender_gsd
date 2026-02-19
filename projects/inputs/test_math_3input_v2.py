"""Test Math node 3rd input - using separate objects."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

def create_test_object(name, third_input_value):
    """Create an object with a math test."""
    tree = bpy.data.node_groups.new(f"MathTest_{name}", "GeometryNodeTree")
    nk = NodeKit(tree)
    nk.clear()

    tree.interface.new_socket("Result", in_out="OUTPUT", socket_type="NodeSocketFloat")

    go = nk.group_output(400, 0)

    # Math node
    math_node = nk.n("ShaderNodeMath", "Math", 200, 0)
    math_node.operation = "MULTIPLY"
    math_node.inputs[0].default_value = 2.0
    math_node.inputs[1].default_value = 0.5
    math_node.inputs[2].default_value = third_input_value

    nk.link(math_node.outputs[0], go.inputs["Result"])

    return tree

# Create two separate node groups with different 3rd input values
tree_default = create_test_object("Default", 0.5)
tree_zero = create_test_object("Zero", 0.0)

print("=" * 60)
print("MATH NODE 3RD INPUT TEST (SEPARATE NODES)")
print("=" * 60)

# Check the math nodes directly
for tree_name, third_val in [("Default", 0.5), ("Zero", 0.0)]:
    tree = bpy.data.node_groups[f"MathTest_{tree_name}"]
    for node in tree.nodes:
        if node.type == 'MATH':
            print(f"\nNode: {node.name}")
            print(f"  Operation: {node.operation}")
            print(f"  Input[0]: {node.inputs[0].default_value}")
            print(f"  Input[1]: {node.inputs[1].default_value}")
            print(f"  Input[2]: {node.inputs[2].default_value}")
            print(f"  Output[0] default: {node.outputs[0].default_value}")

print("\n" + "=" * 60)
print("TESTING WITH STORED ATTRIBUTE")
print("=" * 60)

# Create a more reliable test - store the math result as a vertex attribute
tree = bpy.data.node_groups.new("AttributeTest", "GeometryNodeTree")
nk = NodeKit(tree)
nk.clear()

tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

go = nk.group_output(600, 0)

# Create a single point
point = nk.n("GeometryNodeMeshGrid", "Grid", 0, 0)
point.inputs["Vertices X"].default_value = 2
point.inputs["Vertices Y"].default_value = 2
point.inputs["Size X"].default_value = 0.001
point.inputs["Size Y"].default_value = 0.001

# Math 1: 2.0 * 0.5 with input[2] = 0.5 (should give 1.0 if 2-input, or 0.5 if 3-input)
math1 = nk.n("ShaderNodeMath", "Math_3rd_0.5", 200, 50)
math1.operation = "MULTIPLY"
math1.inputs[0].default_value = 2.0
math1.inputs[1].default_value = 0.5
# input[2] stays at default 0.5

# Math 2: 2.0 * 0.5 with input[2] = 0.0
math2 = nk.n("ShaderNodeMath", "Math_3rd_0.0", 200, 0)
math2.operation = "MULTIPLY"
math2.inputs[0].default_value = 2.0
math2.inputs[1].default_value = 0.5
math2.inputs[2].default_value = 0.0

# Store math1 result as Y position (offset)
offset_y = nk.n("ShaderNodeCombineXYZ", "OffsetY", 300, 50)
offset_y.inputs["X"].default_value = 0.5
nk.link(math1.outputs[0], offset_y.inputs["Y"])
offset_y.inputs["Z"].default_value = 0

# Store math2 result as Z position (offset)
offset_z = nk.n("ShaderNodeCombineXYZ", "OffsetZ", 300, 0)
offset_z.inputs["X"].default_value = 0
offset_z.inputs["Y"].default_value = 0
nk.link(math2.outputs[0], offset_z.inputs["Z"])

# Transform to apply offsets
xform = nk.n("GeometryNodeTransform", "Transform", 400, 0)
# Actually, we can't easily separate these. Let me use SetPosition instead.

# Better approach: Store results in separate named attributes
store1 = nk.n("GeometryNodeStoreNamedAttribute", "Store_Result1", 400, 50)
store1.inputs["Name"].default_value = "result_3rd_0.5"
store1.data_type = 'FLOAT'
nk.link(point.outputs["Mesh"], store1.inputs["Geometry"])
nk.link(math1.outputs[0], store1.inputs["Value"])

store2 = nk.n("GeometryNodeStoreNamedAttribute", "Store_Result2", 500, 0)
store2.inputs["Name"].default_value = "result_3rd_0.0"
store2.data_type = 'FLOAT'
nk.link(store1.outputs["Geometry"], store2.inputs["Geometry"])
nk.link(math2.outputs[0], store2.inputs["Value"])

nk.link(store2.outputs["Geometry"], go.inputs["Geometry"])

# Create object with this tree
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object
obj.name = "Math_Attribute_Test"

mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("\nAttribute values (all vertices should have same value):")
for attr in mesh.attributes:
    if attr.name.startswith("result_"):
        vals = [val.value for val in attr.data]
        unique_vals = set(vals)
        print(f"\n  {attr.name}:")
        print(f"    All values: {vals[:8]}...")  # First 8
        print(f"    Unique values: {unique_vals}")
        if len(unique_vals) == 1:
            print(f"    Result: {list(unique_vals)[0]}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("  With input[2]=0.5: expecting 1.0 (if 2-input) or 0.5 (if 3-input)")
print("  With input[2]=0.0: expecting 1.0 (if 2-input) or 0.0 (if 3-input)")
print("=" * 60)

eval_obj.to_mesh_clear()
