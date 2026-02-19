"""Test the Switch node behavior with boolean input."""
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
tree.interface.new_socket("Debug_Mat", in_out="INPUT", socket_type="NodeSocketMaterial")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nk.group_input(0, 0)
go = nk.group_output(400, 0)

# Create a simple cone
cone = nk.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Create two materials
prod_mat = bpy.data.materials.new("Prod_Mat")
prod_mat.use_nodes = True
debug_mat = bpy.data.materials.new("Debug_Mat_Test")
debug_mat.use_nodes = True
bsdf = debug_mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)  # Red

# Create Switch node for material
switch = nk.n("GeometryNodeSwitch", "MatSwitch", 200, 0)
switch.input_type = 'MATERIAL'

# Connect debug mode to switch
nk.link(gi.outputs["Debug_Mode"], switch.inputs["Switch"])

# Set production material as False (default)
switch.inputs["False"].default_value = prod_mat

# Connect debug material as True
nk.link(gi.outputs["Debug_Mat"], switch.inputs["True"])

# Set material
set_mat = nk.n("GeometryNodeSetMaterial", "SetMat", 280, 0)
nk.link(cone.outputs["Mesh"], set_mat.inputs["Geometry"])
nk.link(switch.outputs[0], set_mat.inputs["Material"])

# Output
nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

print("=" * 60)
print("SWITCH NODE TEST")
print("=" * 60)

# Check switch node inputs
print("\nSwitch node inputs:")
for inp in switch.inputs:
    if inp.links:
        print(f"  {inp.name}: linked to {inp.links[0].from_socket.name}")
    elif hasattr(inp, 'default_value'):
        val = inp.default_value
        if hasattr(val, 'name'):
            print(f"  {inp.name}: {val.name}")
        else:
            print(f"  {inp.name}: {val}")
    else:
        print(f"  {inp.name}: no value")

# Test with Debug_Mode = False (should get Prod_Mat)
print("\n--- Test 1: Debug_Mode = False ---")
test_obj = bpy.data.objects.new("Test1", bpy.data.meshes.new("Mesh1"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Debug_Mode"] = False
mod["Debug_Mat"] = debug_mat

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"Mesh materials: {[m.name if m else 'None' for m in mesh.materials]}")
eval_obj.to_mesh_clear()
bpy.data.objects.remove(test_obj)
bpy.data.meshes.remove(bpy.data.meshes["Mesh1"])

# Test with Debug_Mode = True (should get Debug_Mat_Test)
print("\n--- Test 2: Debug_Mode = True ---")
test_obj2 = bpy.data.objects.new("Test2", bpy.data.meshes.new("Mesh2"))
bpy.context.collection.objects.link(test_obj2)
mod2 = test_obj2.modifiers.new(name="Test", type='NODES')
mod2.node_group = tree
mod2["Debug_Mode"] = True
mod2["Debug_Mat"] = debug_mat

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj2 = test_obj2.evaluated_get(depsgraph)
mesh2 = eval_obj2.to_mesh()
print(f"Mesh materials: {[m.name if m else 'None' for m in mesh2.materials]}")
eval_obj2.to_mesh_clear()
bpy.data.objects.remove(test_obj2)
bpy.data.meshes.remove(bpy.data.meshes["Mesh2"])
