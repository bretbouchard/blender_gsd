"""Test if the issue is with material assignment, not Switch."""
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
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nk.group_input(0, 0)
go = nk.group_output(400, 0)

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
print("TEST DIRECT MATERIAL ASSIGNMENT (NO SWITCH)")
print("=" * 60)

# Method 1: Set material directly without Switch
set_mat = nk.n("GeometryNodeSetMaterial", "SetMat", 250, 0)
nk.link(cone.outputs["Mesh"], set_mat.inputs["Geometry"])
set_mat.inputs["Material"].default_value = true_mat  # Set TRUE_MAT directly
nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

print("Config: Set material directly to TRUE_MAT (no switch)")

test_obj = bpy.data.objects.new("Test", bpy.data.meshes.new("Mesh"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"\nDirect assignment to TRUE_MAT:")
print(f"  Actual: {[m.name if m else 'None' for m in mesh.materials]}")
print(f"  Polygons: {len(mesh.polygons)}")
if mesh.polygons:
    print(f"  First poly material_index: {mesh.polygons[0].material_index}")
eval_obj.to_mesh_clear()
bpy.data.objects.remove(test_obj)

# Method 2: Using a material INPUT socket
print("\n" + "=" * 60)
print("TEST MATERIAL INPUT SOCKET")
print("=" * 60)

tree2 = bpy.data.node_groups.new("SwitchTest2", "GeometryNodeTree")
nk2 = NodeKit(tree2)

tree2.interface.new_socket("Material_Input", in_out="INPUT", socket_type="NodeSocketMaterial")
tree2.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi2 = nk2.group_input(0, 0)
go2 = nk2.group_output(400, 0)

cone2 = nk2.n("GeometryNodeMeshCone", "Cone", 100, 0)
set_mat2 = nk2.n("GeometryNodeSetMaterial", "SetMat", 250, 0)
nk2.link(cone2.outputs["Mesh"], set_mat2.inputs["Geometry"])
nk2.link(gi2.outputs["Material_Input"], set_mat2.inputs["Material"])
nk2.link(set_mat2.outputs["Geometry"], go2.inputs["Geometry"])

print("Config: Material from input socket")

test_obj2 = bpy.data.objects.new("Test2", bpy.data.meshes.new("Mesh2"))
bpy.context.collection.objects.link(test_obj2)
mod2 = test_obj2.modifiers.new(name="Test", type='NODES')
mod2.node_group = tree2
mod2["Material_Input"] = true_mat  # Set TRUE_MAT via modifier

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj2 = test_obj2.evaluated_get(depsgraph)
mesh2 = eval_obj2.to_mesh()
print(f"\nMaterial from input socket (TRUE_MAT):")
print(f"  Actual: {[m.name if m else 'None' for m in mesh2.materials]}")
eval_obj2.to_mesh_clear()
