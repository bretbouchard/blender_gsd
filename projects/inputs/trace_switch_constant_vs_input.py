"""Final test: Compare constant vs input boolean for Switch."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

print("=" * 60)
print("CONSTANT VS INPUT BOOLEAN FOR SWITCH")
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
# TEST 1: Constant True from InputBool node
# =========================================================================
print("\n--- Test 1: Constant True from FunctionNodeInputBool ---")

if "Test1" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["Test1"])

tree1 = bpy.data.node_groups.new("Test1", "GeometryNodeTree")
nk1 = NodeKit(tree1)

tree1.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi1 = nk1.group_input(0, 0)
go1 = nk1.group_output(600, 0)

cone1 = nk1.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Constant True
const_true = nk1.n("FunctionNodeInputBool", "ConstTrue", 100, 0)
const_true.boolean = True

# Switch
switch1 = nk1.n("GeometryNodeSwitch", "Switch", 300, 0)
switch1.input_type = 'MATERIAL'
nk1.link(const_true.outputs[0], switch1.inputs["Switch"])
switch1.inputs["False"].default_value = mat_a
switch1.inputs["True"].default_value = mat_b

# Set material
set_mat1 = nk1.n("GeometryNodeSetMaterial", "SetMat", 450, 0)
nk1.link(cone1.outputs["Mesh"], set_mat1.inputs["Geometry"])
nk1.link(switch1.outputs[0], set_mat1.inputs["Material"])
nk1.link(set_mat1.outputs["Geometry"], go1.inputs["Geometry"])

# Test
test_obj1 = bpy.data.objects.new("Test1", bpy.data.meshes.new("Mesh1"))
bpy.context.collection.objects.link(test_obj1)
mod1 = test_obj1.modifiers.new(name="Test", type='NODES')
mod1.node_group = tree1

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj1 = test_obj1.evaluated_get(depsgraph)
mesh1 = eval_obj1.to_mesh()
result1 = [m.name if m else 'None' for m in mesh1.materials]
print(f"Constant True: {result1} (expected Mat_B)")
eval_obj1.to_mesh_clear()
bpy.data.objects.remove(test_obj1)

# =========================================================================
# TEST 2: Boolean from Group Input
# =========================================================================
print("\n--- Test 2: Boolean from Group Input (True) ---")

if "Test2" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["Test2"])

tree2 = bpy.data.node_groups.new("Test2", "GeometryNodeTree")
nk2 = NodeKit(tree2)

tree2.interface.new_socket("My_Bool", in_out="INPUT", socket_type="NodeSocketBool")
tree2.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi2 = nk2.group_input(0, 0)
go2 = nk2.group_output(600, 0)

cone2 = nk2.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Switch
switch2 = nk2.n("GeometryNodeSwitch", "Switch", 300, 0)
switch2.input_type = 'MATERIAL'
nk2.link(gi2.outputs["My_Bool"], switch2.inputs["Switch"])
switch2.inputs["False"].default_value = mat_a
switch2.inputs["True"].default_value = mat_b

# Set material
set_mat2 = nk2.n("GeometryNodeSetMaterial", "SetMat", 450, 0)
nk2.link(cone2.outputs["Mesh"], set_mat2.inputs["Geometry"])
nk2.link(switch2.outputs[0], set_mat2.inputs["Material"])
nk2.link(set_mat2.outputs["Geometry"], go2.inputs["Geometry"])

# Test with My_Bool = True
test_obj2 = bpy.data.objects.new("Test2", bpy.data.meshes.new("Mesh2"))
bpy.context.collection.objects.link(test_obj2)
mod2 = test_obj2.modifiers.new(name="Test", type='NODES')
mod2.node_group = tree2
mod2["My_Bool"] = True

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj2 = test_obj2.evaluated_get(depsgraph)
mesh2 = eval_obj2.to_mesh()
result2 = [m.name if m else 'None' for m in mesh2.materials]
print(f"Group Input True: {result2} (expected Mat_B)")
eval_obj2.to_mesh_clear()

# Change to False
mod2["My_Bool"] = False
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj2 = test_obj2.evaluated_get(depsgraph)
mesh2 = eval_obj2.to_mesh()
result2_false = [m.name if m else 'None' for m in mesh2.materials]
print(f"Group Input False: {result2_false} (expected Mat_A)")
eval_obj2.to_mesh_clear()
bpy.data.objects.remove(test_obj2)

# =========================================================================
# TEST 3: Try using a float comparison
# =========================================================================
print("\n--- Test 3: Float comparison (My_Float > 0.5) ---")

if "Test3" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["Test3"])

tree3 = bpy.data.node_groups.new("Test3", "GeometryNodeTree")
nk3 = NodeKit(tree3)

tree3.interface.new_socket("My_Float", in_out="INPUT", socket_type="NodeSocketFloat")
tree3.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi3 = nk3.group_input(0, 0)
go3 = nk3.group_output(600, 0)

cone3 = nk3.n("GeometryNodeMeshCone", "Cone", 100, 0)

# Compare: My_Float > 0.5
compare = nk3.n("ShaderNodeMath", "Compare", 200, 0)
compare.operation = 'GREATER_THAN'
nk3.link(gi3.outputs["My_Float"], compare.inputs[0])
compare.inputs[1].default_value = 0.5

# Switch
switch3 = nk3.n("GeometryNodeSwitch", "Switch", 300, 0)
switch3.input_type = 'MATERIAL'
nk3.link(compare.outputs[0], switch3.inputs["Switch"])
switch3.inputs["False"].default_value = mat_a
switch3.inputs["True"].default_value = mat_b

# Set material
set_mat3 = nk3.n("GeometryNodeSetMaterial", "SetMat", 450, 0)
nk3.link(cone3.outputs["Mesh"], set_mat3.inputs["Geometry"])
nk3.link(switch3.outputs[0], set_mat3.inputs["Material"])
nk3.link(set_mat3.outputs["Geometry"], go3.inputs["Geometry"])

# Test with My_Float = 1.0 (should be > 0.5, so True, so Mat_B)
test_obj3 = bpy.data.objects.new("Test3", bpy.data.meshes.new("Mesh3"))
bpy.context.collection.objects.link(test_obj3)
mod3 = test_obj3.modifiers.new(name="Test", type='NODES')
mod3.node_group = tree3
mod3["My_Float"] = 1.0

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj3 = test_obj3.evaluated_get(depsgraph)
mesh3 = eval_obj3.to_mesh()
result3 = [m.name if m else 'None' for m in mesh3.materials]
print(f"Float 1.0 > 0.5: {result3} (expected Mat_B)")
eval_obj3.to_mesh_clear()

# Test with My_Float = 0.0 (should be < 0.5, so False, so Mat_A)
mod3["My_Float"] = 0.0
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj3 = test_obj3.evaluated_get(depsgraph)
mesh3 = eval_obj3.to_mesh()
result3_false = [m.name if m else 'None' for m in mesh3.materials]
print(f"Float 0.0 > 0.5: {result3_false} (expected Mat_A)")
eval_obj3.to_mesh_clear()
bpy.data.objects.remove(test_obj3)

print("\n" + "=" * 60)
print("SUMMARY:")
print("Constant True works? " + ("YES" if "Mat_B" in result1 else "NO"))
print("Group Input works? " + ("YES" if "Mat_B" in result2 else "NO"))
print("Float comparison works? " + ("YES" if "Mat_B" in result3 else "NO"))
print("=" * 60)
