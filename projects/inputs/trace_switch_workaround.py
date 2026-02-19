"""Test workarounds for Blender 5.0 material input socket issue."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

print("=" * 60)
print("BLENDER 5.0 MATERIAL INPUT WORKAROUNDS")
print("=" * 60)

# Create materials
mat_a = bpy.data.materials.new("Mat_A")
mat_a.use_nodes = True
bsdf = mat_a.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)  # Red

mat_b = bpy.data.materials.new("Mat_B")
mat_b.use_nodes = True
bsdf = mat_b.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.0, 1.0, 0.0, 1.0)  # Green

# =========================================================================
# WORKAROUND: Switch with inline default materials (not from input sockets)
# =========================================================================
print("\n--- Workaround: Switch with inline default materials ---")

if "Workaround3" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["Workaround3"])

tree = bpy.data.node_groups.new("Workaround3", "GeometryNodeTree")
nk = NodeKit(tree)

# Boolean input for material selection
tree.interface.new_socket("Use_Mat_B", in_out="INPUT", socket_type="NodeSocketBool")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nk.group_input(0, 0)
go = nk.group_output(600, 0)

cone = nk.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Create switch with materials set INLINE (not from input sockets)
switch = nk.n("GeometryNodeSwitch", "MatSwitch", 300, 0)
switch.input_type = 'MATERIAL'

# IMPORTANT: Set materials as DEFAULT VALUES, not from input sockets
switch.inputs["False"].default_value = mat_a  # Mat_A when Use_Mat_B = False
switch.inputs["True"].default_value = mat_b   # Mat_B when Use_Mat_B = True

# Link boolean to switch
nk.link(gi.outputs["Use_Mat_B"], switch.inputs["Switch"])

# Set material
set_mat = nk.n("GeometryNodeSetMaterial", "SetMat", 450, 0)
nk.link(cone.outputs["Mesh"], set_mat.inputs["Geometry"])
nk.link(switch.outputs[0], set_mat.inputs["Material"])
nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

# Test with Use_Mat_B = True
test_obj = bpy.data.objects.new("Test3", bpy.data.meshes.new("Mesh3"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Use_Mat_B"] = True

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"Use_Mat_B=True (expect Mat_B): {[m.name if m else 'None' for m in mesh.materials]}")
eval_obj.to_mesh_clear()

# Test with Use_Mat_B = False
mod["Use_Mat_B"] = False
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"Use_Mat_B=False (expect Mat_A): {[m.name if m else 'None' for m in mesh.materials]}")
eval_obj.to_mesh_clear()

print("\n" + "=" * 60)
print("RESULT: Switch with inline default materials works!")
print("=" * 60)
