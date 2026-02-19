"""Test Switch node with inverted logic."""
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
go = nk.group_output(400, 0)

# Create a simple cone
cone = nk.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Create two materials with CLEARLY different names
false_mat = bpy.data.materials.new("FALSE_MAT_WHEN_SWITCH_IS_FALSE")
false_mat.use_nodes = True
true_mat = bpy.data.materials.new("TRUE_MAT_WHEN_SWITCH_IS_TRUE")
true_mat.use_nodes = True
bsdf = true_mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)  # Red

# Create Switch node for material
switch = nk.n("GeometryNodeSwitch", "MatSwitch", 200, 0)
switch.input_type = 'MATERIAL'

# Connect debug mode to switch
nk.link(gi.outputs["Debug_Mode"], switch.inputs["Switch"])

# IMPORTANT: Let's try SWAPPING the inputs to see what happens!
# Put TRUE_MAT in the "False" slot
switch.inputs["False"].default_value = true_mat

# Put FALSE_MAT in the "True" slot
switch.inputs["True"].default_value = false_mat

# Set material
set_mat = nk.n("GeometryNodeSetMaterial", "SetMat", 280, 0)
nk.link(cone.outputs["Mesh"], set_mat.inputs["Geometry"])
nk.link(switch.outputs[0], set_mat.inputs["Material"])

# Output
nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

print("=" * 60)
print("SWITCH NODE SWAPPED TEST")
print("=" * 60)
print("Switch config:")
print("  'False' input = TRUE_MAT (red)")
print("  'True' input = FALSE_MAT (gray)")

# Test with Debug_Mode = False (should get TRUE_MAT since it's in 'False' slot)
print("\n--- Test 1: Debug_Mode = False ---")
test_obj1 = bpy.data.objects.new("Test1", bpy.data.meshes.new("Mesh1"))
bpy.context.collection.objects.link(test_obj1)
mod1 = test_obj1.modifiers.new(name="Test", type='NODES')
mod1.node_group = tree
mod1["Debug_Mode"] = False

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj1 = test_obj1.evaluated_get(depsgraph)
mesh1 = eval_obj1.to_mesh()
print(f"Expected: TRUE_MAT (since switch=False, we get 'False' input)")
print(f"Actual materials: {[m.name if m else 'None' for m in mesh1.materials]}")
eval_obj1.to_mesh_clear()
bpy.data.objects.remove(test_obj1)
bpy.data.meshes.remove(bpy.data.meshes["Mesh1"])

# Test with Debug_Mode = True (should get FALSE_MAT since it's in 'True' slot)
print("\n--- Test 2: Debug_Mode = True ---")
test_obj2 = bpy.data.objects.new("Test2", bpy.data.meshes.new("Mesh2"))
bpy.context.collection.objects.link(test_obj2)
mod2 = test_obj2.modifiers.new(name="Test", type='NODES')
mod2.node_group = tree
mod2["Debug_Mode"] = True

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj2 = test_obj2.evaluated_get(depsgraph)
mesh2 = eval_obj2.to_mesh()
print(f"Expected: FALSE_MAT (since switch=True, we get 'True' input)")
print(f"Actual materials: {[m.name if m else 'None' for m in mesh2.materials]}")
eval_obj2.to_mesh_clear()
bpy.data.objects.remove(test_obj2)
bpy.data.meshes.remove(bpy.data.meshes["Mesh2"])

# Now let's try WITHOUT setting any material and see what happens
print("\n--- Test 3: Default material slot ---")
switch2 = nk.n("GeometryNodeSwitch", "MatSwitch2", 200, -200)
switch2.input_type = 'MATERIAL'
nk.link(gi.outputs["Debug_Mode"], switch2.inputs["Switch"])

# Don't set any materials - just leave them as None
print(f"False input: {switch2.inputs['False'].default_value}")
print(f"True input: {switch2.inputs['True'].default_value}")

set_mat2 = nk.n("GeometryNodeSetMaterial", "SetMat2", 280, -200)
nk.link(cone.outputs["Mesh"], set_mat2.inputs["Geometry"])
nk.link(switch2.outputs[0], set_mat2.inputs["Material"])
