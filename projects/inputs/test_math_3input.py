"""Test what happens with ShaderNodeMath MULTIPLY and 3 inputs."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a geometry node tree that tests math operations
tree = bpy.data.node_groups.new("MathTest", "GeometryNodeTree")
nk = NodeKit(tree)
nk.clear()

# Add input/output sockets
tree.interface.new_socket("Input", in_out="INPUT", socket_type="NodeSocketFloat")
s = tree.interface.items_tree["Input"]
s.default_value = 2.0

tree.interface.new_socket("Result_Default", in_out="OUTPUT", socket_type="NodeSocketFloat")
tree.interface.new_socket("Result_Zero", in_out="OUTPUT", socket_type="NodeSocketFloat")

# Create nodes
gi = nk.group_input(0, 0)
go = nk.group_output(400, 0)

# Math node with default 3rd input (0.5)
math_default = nk.n("ShaderNodeMath", "Math_Default", 200, 0)
math_default.operation = "MULTIPLY"
nk.link(gi.outputs["Input"], math_default.inputs[0])
math_default.inputs[1].default_value = 0.5
# Input[2] remains at default 0.5

# Math node with 3rd input = 0.0
math_zero = nk.n("ShaderNodeMath", "Math_Zero", 200, -100)
math_zero.operation = "MULTIPLY"
nk.link(gi.outputs["Input"], math_zero.inputs[0])
math_zero.inputs[1].default_value = 0.5
math_zero.inputs[2].default_value = 0.0

# Link to output
nk.link(math_default.outputs[0], go.inputs["Result_Default"])
nk.link(math_zero.outputs[0], go.inputs["Result_Zero"])

# Now test by storing values in attributes
tree2 = bpy.data.node_groups.new("MathTest2", "GeometryNodeTree")
nk2 = NodeKit(tree2)
nk2.clear()

tree2.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

go2 = nk2.group_output(800, 0)

# Create a mesh
grid = nk2.n("GeometryNodeMeshGrid", "Grid", 0, 0)
grid.inputs["Vertices X"].default_value = 2
grid.inputs["Vertices Y"].default_value = 2
grid.inputs["Size X"].default_value = 0.001
grid.inputs["Size Y"].default_value = 0.001

# Test 1: 2.0 * 0.5 with input[2] = 0.5 (default)
test1 = nk2.n("ShaderNodeMath", "Test1", 200, 0)
test1.operation = "MULTIPLY"
test1.inputs[0].default_value = 2.0
test1.inputs[1].default_value = 0.5
# input[2] = 0.5 (default)
store1 = nk2.n("GeometryNodeStoreNamedAttribute", "Store1", 400, 0)
store1.inputs["Name"].default_value = "result_default"
store1.data_type = 'FLOAT'
nk2.link(grid.outputs["Mesh"], store1.inputs["Geometry"])
nk2.link(test1.outputs[0], store1.inputs["Value"])

# Test 2: 2.0 * 0.5 with input[2] = 0.0
test2 = nk2.n("ShaderNodeMath", "Test2", 200, -100)
test2.operation = "MULTIPLY"
test2.inputs[0].default_value = 2.0
test2.inputs[1].default_value = 0.5
test2.inputs[2].default_value = 0.0
store2 = nk2.n("GeometryNodeStoreNamedAttribute", "Store2", 400, -100)
store2.inputs["Name"].default_value = "result_zero"
store2.data_type = 'FLOAT'
nk2.link(grid.outputs["Mesh"], store2.inputs["Geometry"])
nk2.link(test2.outputs[0], store2.inputs["Value"])

# Join
join = nk2.n("GeometryNodeJoinGeometry", "Join", 600, -50)
nk2.link(store1.outputs["Geometry"], join.inputs["Geometry"])
nk2.link(store2.outputs["Geometry"], join.inputs["Geometry"])
nk2.link(join.outputs["Geometry"], go2.inputs["Geometry"])

# Create object with this node group
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object
obj.name = "Math_Test"

mod = obj.modifiers.new(name="MathTest", type='NODES')
mod.node_group = tree2

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("=" * 60)
print("MATH NODE 3RD INPUT TEST")
print("=" * 60)

# Get attribute values
for attr in mesh.attributes:
    print(f"\nAttribute: {attr.name}")
    if attr.name == "result_default":
        for i, val in enumerate(attr.data):
            print(f"  2.0 * 0.5 (input[2]=0.5): {val.value}")
    elif attr.name == "result_zero":
        for i, val in enumerate(attr.data):
            print(f"  2.0 * 0.5 (input[2]=0.0): {val.value}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("  If MULTIPLY uses all 3 inputs (a * b * c):")
print("    - With input[2]=0.5: 2.0 * 0.5 * 0.5 = 0.5")
print("    - With input[2]=0.0: 2.0 * 0.5 * 0.0 = 0.0")
print("  If MULTIPLY uses only 2 inputs (a * b):")
print("    - Both should give: 2.0 * 0.5 = 1.0")
print("=" * 60)

eval_obj.to_mesh_clear()
