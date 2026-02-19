"""Test Switch with Math node to convert boolean."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

# Create test node tree
if "SwitchTest" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["SwitchTest"])

tree = bpy.data.node_groups.new("SwitchTest", "GeometryNodeTree")
nk = NodeKit(tree)

# Create interface
tree.interface.new_socket("Debug_Mode", in_out="INPUT", socket_type="NodeSocketBool")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nk.group_input(0, 0)
go = nk.group_output(600, 0)

# Create a simple cone
cone = nk.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Create two materials
false_mat = bpy.data.materials.new("MAT_FALSE")
false_mat.use_nodes = True
true_mat = bpy.data.materials.new("MAT_TRUE")
true_mat.use_nodes = True
bsdf = true_mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)  # Red

print("=" * 60)
print("SWITCH WITH MATH NODE (Boolean to Float)")
print("=" * 60)

# Use Math node to convert boolean to float: Debug_Mode * 1.0
math_mult = nk.n("ShaderNodeMath", "BoolToFloat", 150, 0)
math_mult.operation = 'MULTIPLY'
nk.link(gi.outputs["Debug_Mode"], math_mult.inputs[0])
math_mult.inputs[1].default_value = 1.0

# Create Switch node
switch = nk.n("GeometryNodeSwitch", "Switch", 300, 0)
switch.input_type = 'MATERIAL'
nk.link(math_mult.outputs[0], switch.inputs["Switch"])
switch.inputs["False"].default_value = false_mat
switch.inputs["True"].default_value = true_mat

print(f"Switch input from: {switch.inputs['Switch'].links[0].from_node.name}")

# Set material
set_mat = nk.n("GeometryNodeSetMaterial", "SetMat", 450, 0)
nk.link(cone.outputs["Mesh"], set_mat.inputs["Geometry"])
nk.link(switch.outputs[0], set_mat.inputs["Material"])
nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

# Test with Debug_Mode = True
test_obj = bpy.data.objects.new("Test", bpy.data.meshes.new("Mesh"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Debug_Mode"] = True

print(f"\nModifier Debug_Mode = True")
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"Expected: MAT_TRUE")
print(f"Actual: {[m.name if m else 'None' for m in mesh.materials]}")
eval_obj.to_mesh_clear()
bpy.data.objects.remove(test_obj)

# Test with Debug_Mode = False
test_obj = bpy.data.objects.new("Test2", bpy.data.meshes.new("Mesh2"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Debug_Mode"] = False

print(f"\nModifier Debug_Mode = False")
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"Expected: MAT_FALSE")
print(f"Actual: {[m.name if m else 'None' for m in mesh.materials]}")
eval_obj.to_mesh_clear()
