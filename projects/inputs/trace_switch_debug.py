"""Test Switch node with various boolean sources."""
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
print("SWITCH BOOLEAN SOURCE TEST")
print("=" * 60)

# METHOD 1: Direct link from Group Input
print("\n--- Method 1: Direct link from Group Input ---")
switch1 = nk.n("GeometryNodeSwitch", "Switch1", 200, 0)
switch1.input_type = 'MATERIAL'
nk.link(gi.outputs["Debug_Mode"], switch1.inputs["Switch"])
switch1.inputs["False"].default_value = false_mat
switch1.inputs["True"].default_value = true_mat

# Check what's connected
print(f"Switch input 'Switch': {switch1.inputs['Switch'].links[0].from_socket.name if switch1.inputs['Switch'].links else 'not linked'}")
print(f"Switch input 'Switch' type: {switch1.inputs['Switch'].type}")
print(f"Debug_Mode output type: {gi.outputs['Debug_Mode'].type}")

# Test
set_mat1 = nk.n("GeometryNodeSetMaterial", "SetMat1", 350, 0)
nk.link(cone.outputs["Mesh"], set_mat1.inputs["Geometry"])
nk.link(switch1.outputs[0], set_mat1.inputs["Material"])
nk.link(set_mat1.outputs["Geometry"], go.inputs["Geometry"])

# Test with True
test_obj = bpy.data.objects.new("Test", bpy.data.meshes.new("Mesh"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Debug_Mode"] = True

print(f"\nModifier Debug_Mode value: {mod['Debug_Mode']}")

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"Result: {[m.name if m else 'None' for m in mesh.materials]}")
eval_obj.to_mesh_clear()

# Let's try a workaround: use Boolean Math to ensure the value is being evaluated
print("\n--- Method 2: Boolean Math pass-through ---")

# Create a Boolean Math node (AND with True to pass through)
bool_math = nk.n("FunctionNodeBooleanMath", "BoolPass", 150, 50)
bool_math.operation = 'AND'
nk.link(gi.outputs["Debug_Mode"], bool_math.inputs[0])
bool_math.inputs[1].default_value = True  # AND with True

# Use this as the switch input
switch2 = nk.n("GeometryNodeSwitch", "Switch2", 200, -200)
switch2.input_type = 'MATERIAL'
nk.link(bool_math.outputs[0], switch2.inputs["Switch"])
switch2.inputs["False"].default_value = false_mat
switch2.inputs["True"].default_value = true_mat

print(f"Switch input from: {switch2.inputs['Switch'].links[0].from_node.name if switch2.inputs['Switch'].links else 'not linked'}")

# Update test object
bpy.data.objects.remove(test_obj)
test_obj = bpy.data.objects.new("Test2", bpy.data.meshes.new("Mesh2"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Debug_Mode"] = True

print(f"\nModifier Debug_Mode value: {mod['Debug_Mode']}")

# Re-evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"Result (switch connected to BoolMath): N/A - different output path")

eval_obj.to_mesh_clear()
bpy.data.objects.remove(test_obj)
