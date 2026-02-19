"""Test Switch with Float input instead of Boolean."""
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

# Create interface - USE FLOAT instead of BOOL
tree.interface.new_socket("Debug_Mode_Float", in_out="INPUT", socket_type="NodeSocketFloat")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nk.group_input(0, 0)
go = nk.group_output(500, 0)

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
print("SWITCH WITH FLOAT INPUT")
print("=" * 60)

# Create Switch node - connect float directly
switch = nk.n("GeometryNodeSwitch", "Switch", 200, 0)
switch.input_type = 'MATERIAL'
nk.link(gi.outputs["Debug_Mode_Float"], switch.inputs["Switch"])
switch.inputs["False"].default_value = false_mat
switch.inputs["True"].default_value = true_mat

print(f"Switch input type: {switch.inputs['Switch'].type}")
print(f"Source output type: {gi.outputs['Debug_Mode_Float'].type}")

# Set material
set_mat = nk.n("GeometryNodeSetMaterial", "SetMat", 350, 0)
nk.link(cone.outputs["Mesh"], set_mat.inputs["Geometry"])
nk.link(switch.outputs[0], set_mat.inputs["Material"])
nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

# Test with Debug_Mode_Float = 1.0 (True)
test_obj = bpy.data.objects.new("Test", bpy.data.meshes.new("Mesh"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Debug_Mode_Float"] = 1.0

print(f"\nModifier Debug_Mode_Float = 1.0")
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"Expected: MAT_TRUE")
print(f"Actual: {[m.name if m else 'None' for m in mesh.materials]}")
eval_obj.to_mesh_clear()
bpy.data.objects.remove(test_obj)

# Test with Debug_Mode_Float = 0.0 (False)
test_obj = bpy.data.objects.new("Test2", bpy.data.meshes.new("Mesh2"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Debug_Mode_Float"] = 0.0

print(f"\nModifier Debug_Mode_Float = 0.0")
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"Expected: MAT_FALSE")
print(f"Actual: {[m.name if m else 'None' for m in mesh.materials]}")
eval_obj.to_mesh_clear()
