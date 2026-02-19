"""Test if Switch uses INVERTED logic or needs NOT."""
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
tree.interface.new_socket("Switch_Value", in_out="INPUT", socket_type="NodeSocketBool")
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
print("TEST INVERTED SWITCH LOGIC")
print("=" * 60)

# Method: Use NOT to invert the boolean before sending to Switch
not_node = nk.n("FunctionNodeBooleanMath", "NOT", 150, 0)
not_node.operation = 'NOT'
nk.link(gi.outputs["Switch_Value"], not_node.inputs[0])

# Create Switch node
switch = nk.n("GeometryNodeSwitch", "Switch", 300, 0)
switch.input_type = 'MATERIAL'
nk.link(not_node.outputs[0], switch.inputs["Switch"])

# INVERTED: Put TRUE material in "False" slot, FALSE in "True" slot
switch.inputs["False"].default_value = true_mat   # When NOT(True)=False, return this
switch.inputs["True"].default_value = false_mat  # When NOT(False)=True, return this

# Set material
set_mat = nk.n("GeometryNodeSetMaterial", "SetMat", 450, 0)
nk.link(cone.outputs["Mesh"], set_mat.inputs["Geometry"])
nk.link(switch.outputs[0], set_mat.inputs["Material"])
nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

print("Config: NOT(Switch_Value) -> Switch")
print("  False slot = TRUE_MAT")
print("  True slot = FALSE_MAT")

# Test with Switch_Value = True
# NOT(True) = False -> Switch gets False -> returns "False" input = TRUE_MAT
test_obj = bpy.data.objects.new("Test", bpy.data.meshes.new("Mesh"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Switch_Value"] = True

print(f"\nSwitch_Value = True:")
print(f"  NOT(True) = False")
print(f"  Switch(False) should return 'False' input = TRUE_MAT")
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"  Actual: {[m.name if m else 'None' for m in mesh.materials]}")
eval_obj.to_mesh_clear()
bpy.data.objects.remove(test_obj)

# Test with Switch_Value = False
# NOT(False) = True -> Switch gets True -> returns "True" input = FALSE_MAT
test_obj = bpy.data.objects.new("Test2", bpy.data.meshes.new("Mesh2"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Switch_Value"] = False

print(f"\nSwitch_Value = False:")
print(f"  NOT(False) = True")
print(f"  Switch(True) should return 'True' input = FALSE_MAT")
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"  Actual: {[m.name if m else 'None' for m in mesh.materials]}")
eval_obj.to_mesh_clear()
