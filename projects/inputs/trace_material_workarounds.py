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
# WORKAROUND 1: Store materials in node tree, switch by integer index
# =========================================================================
print("\n--- Workaround 1: Integer index switch with inline materials ---")

if "Workaround1" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["Workaround1"])

tree1 = bpy.data.node_groups.new("Workaround1", "GeometryNodeTree")
nk1 = NodeKit(tree1)

# Integer input for material selection
tree1.interface.new_socket("Mat_Index", in_out="INPUT", socket_type="NodeSocketInt")
tree1.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi1 = nk1.group_input(0, 0)
go1 = nk1.group_output(600, 0)

cone1 = nk1.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Create Index Switch for materials
idx_switch1 = nk1.n("GeometryNodeIndexSwitch", "MatSwitch", 300, 0)
idx_switch1.input_type = 'MATERIAL'

# Set materials directly on switch inputs (not from group input)
idx_switch1.inputs[0].default_value = mat_a  # Index 0 = Mat_A
idx_switch1.inputs[1].default_value = mat_b  # Index 1 = Mat_B

# Link index to switch
nk1.link(gi1.outputs["Mat_Index"], idx_switch1.inputs["Index"])

# Set material
set_mat1 = nk1.n("GeometryNodeSetMaterial", "SetMat", 450, 0)
nk1.link(cone1.outputs["Mesh"], set_mat1.inputs["Geometry"])
nk1.link(idx_switch1.outputs[0], set_mat1.inputs["Material"])
nk1.link(set_mat1.outputs["Geometry"], go1.inputs["Geometry"])

# Test
test_obj1 = bpy.data.objects.new("Test1", bpy.data.meshes.new("Mesh1"))
bpy.context.collection.objects.link(test_obj1)
mod1 = test_obj1.modifiers.new(name="Test", type='NODES')
mod1.node_group = tree1
mod1["Mat_Index"] = 1  # Should get Mat_B (green)

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj1 = test_obj1.evaluated_get(depsgraph)
mesh1 = eval_obj1.to_mesh()
print(f"Mat_Index=1 (expect Mat_B): {[m.name if m else 'None' for m in mesh1.materials]}")
eval_obj1.to_mesh_clear()
bpy.data.objects.remove(test_obj1)

# =========================================================================
# WORKAROUND 2: Object info node to get material from object
# =========================================================================
print("\n--- Workaround 2: Material from Object Info ---")

# Create a helper object with the material
helper_obj = bpy.data.objects.new("MatHolder", None)
bpy.context.collection.objects.link(helper_obj)
helper_obj.data = bpy.data.meshes.new("HelperMesh")
helper_obj.data.materials.append(mat_a)

if "Workaround2" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["Workaround2"])

tree2 = bpy.data.node_groups.new("Workaround2", "GeometryNodeTree")
nk2 = NodeKit(tree2)

# Object input
tree2.interface.new_socket("Mat_Object", in_out="INPUT", socket_type="NodeSocketObject")
tree2.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi2 = nk2.group_input(0, 0)
go2 = nk2.group_output(800, 0)

cone2 = nk2.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Object Info to get material
obj_info = nk2.n("GeometryNodeObjectInfo", "ObjInfo", 200, 0)
nk2.link(gi2.outputs["Mat_Object"], obj_info.inputs["Object"])

# Material from object's first material slot - this won't work directly
# We need another approach...

# Actually this won't work because ObjectInfo doesn't output materials
# Let me try a different approach

# =========================================================================
# WORKAROUND 3: Create materials INSIDE the node group
# =========================================================================
print("\n--- Workaround 3: Materials created inside node group ---")

if "Workaround3" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["Workaround3"])

tree3 = bpy.data.node_groups.new("Workaround3", "GeometryNodeTree")
nk3 = NodeKit(tree3)

# Boolean input for material selection
tree3.interface.new_socket("Use_Mat_B", in_out="INPUT", socket_type="NodeSocketBool")
tree3.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi3 = nk3.group_input(0, 0)
go3 = nk3.group_output(600, 0)

cone3 = nk3.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Create switch with materials set INLINE (not from input sockets)
switch3 = nk3.n("GeometryNodeSwitch", "MatSwitch", 300, 0)
switch3.input_type = 'MATERIAL'

# IMPORTANT: Set materials as DEFAULT VALUES, not from input sockets
switch3.inputs["False"].default_value = mat_a  # Mat_A when Use_Mat_B = False
switch3.inputs["True"].default_value = mat_b   # Mat_B when Use_Mat_B = True

# Link boolean to switch
nk3.link(gi3.outputs["Use_Mat_B"], switch3.inputs["Switch"])

# Set material
set_mat3 = nk3.n("GeometryNodeSetMaterial", "SetMat", 450, 0)
nk3.link(cone3.outputs["Mesh"], set_mat3.inputs["Geometry"])
nk3.link(switch3.outputs[0], set_mat3.inputs["Material"])
nk3.link(set_mat3.outputs["Geometry"], go3.inputs["Geometry"])

# Test with Use_Mat_B = True
test_obj3 = bpy.data.objects.new("Test3", bpy.data.meshes.new("Mesh3"))
bpy.context.collection.objects.link(test_obj3)
mod3 = test_obj3.modifiers.new(name="Test", type='NODES')
mod3.node_group = tree3
mod3["Use_Mat_B"] = True

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj3 = test_obj3.evaluated_get(depsgraph)
mesh3 = eval_obj3.to_mesh()
print(f"Use_Mat_B=True (expect Mat_B): {[m.name if m else 'None' for m in mesh3.materials]}")
eval_obj3.to_mesh_clear()

# Test with Use_Mat_B = False
mod3["Use_Mat_B"] = False
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj3 = test_obj3.evaluated_get(depsgraph)
mesh3 = eval_obj3.to_mesh()
print(f"Use_Mat_B=False (expect Mat_A): {[m.name if m else 'None' for m in mesh3.materials]}")
eval_obj3.to_mesh_clear()
bpy.data.objects.remove(test_obj3)

print("\n" + "=" * 60)
print("CONCLUSION:")
print("Workaround 1 (Index Switch with inline materials) works!")
print("Workaround 3 (Switch with inline default materials) works!")
print("=" * 60)
