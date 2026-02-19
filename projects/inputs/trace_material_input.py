"""Debug material input socket behavior."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

# Create test node tree
if "MatInputTest" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["MatInputTest"])

tree = bpy.data.node_groups.new("MatInputTest", "GeometryNodeTree")
nk = NodeKit(tree)

# Create interface with material input
mat_socket = tree.interface.new_socket("Mat_Input", in_out="INPUT", socket_type="NodeSocketMaterial")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

# Check the socket
print("=" * 60)
print("MATERIAL INPUT SOCKET DEBUG")
print("=" * 60)
print(f"\nSocket created: {mat_socket.name}")
print(f"Socket type: {mat_socket.socket_type}")
print(f"Socket default_value: {mat_socket.default_value}")

gi = nk.group_input(0, 0)
go = nk.group_output(400, 0)

# Create cone
cone = nk.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Create SetMaterial node
set_mat = nk.n("GeometryNodeSetMaterial", "SetMat", 250, 0)
nk.link(cone.outputs["Mesh"], set_mat.inputs["Geometry"])
nk.link(gi.outputs["Mat_Input"], set_mat.inputs["Material"])
nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

# Create a test material
test_mat = bpy.data.materials.new("Test_Material")
test_mat.use_nodes = True

# Check the link
print(f"\nSetMaterial inputs:")
for inp in set_mat.inputs:
    if inp.links:
        print(f"  {inp.name}: linked to {inp.links[0].from_socket.name}")
    elif hasattr(inp, 'default_value') and inp.default_value:
        print(f"  {inp.name}: {inp.default_value}")
    else:
        print(f"  {inp.name}: not linked, no default")

# Create test object
test_obj = bpy.data.objects.new("Test", bpy.data.meshes.new("Mesh"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree

print(f"\nBefore setting material:")
print(f"  Modifier['Mat_Input'] = {mod['Mat_Input'] if 'Mat_Input' in mod else 'NOT SET'}")

# Set the material
mod["Mat_Input"] = test_mat

print(f"After setting material:")
print(f"  Modifier['Mat_Input'] = {mod['Mat_Input'].name if mod['Mat_Input'] else 'None'}")

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print(f"\nResult:")
print(f"  Mesh materials: {[m.name if m else 'None' for m in mesh.materials]}")
print(f"  Polygon count: {len(mesh.polygons)}")

# Check if maybe the material is stored somewhere else
print(f"\n  Checking modifier IDProperties:")
for key in mod.keys():
    print(f"    {key}: {mod[key]}")

eval_obj.to_mesh_clear()
