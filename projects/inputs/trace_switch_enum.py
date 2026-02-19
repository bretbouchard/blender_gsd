"""Debug the Switch node more thoroughly."""
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

print("=" * 60)
print("SWITCH NODE ANALYSIS")
print("=" * 60)

# Check all inputs BEFORE connecting
print("\nSwitch inputs BEFORE connections:")
for i, inp in enumerate(switch.inputs):
    print(f"  {i}: {inp.name}, type={inp.type}, bl_idname={inp.bl_idname}")

# Connect debug mode to switch
nk.link(gi.outputs["Debug_Mode"], switch.inputs["Switch"])

# Set production material as False (default)
switch.inputs["False"].default_value = prod_mat

# Connect debug material as True
nk.link(gi.outputs["Debug_Mat"], switch.inputs["True"])

# Check all inputs AFTER connecting
print("\nSwitch inputs AFTER connections:")
for i, inp in enumerate(switch.inputs):
    has_link = "YES" if inp.links else "NO"
    if inp.links:
        src = inp.links[0].from_socket
        print(f"  {i}: {inp.name}, type={inp.type}, linked={has_link}, src={src.name}")
    elif hasattr(inp, 'default_value'):
        val = inp.default_value
        if hasattr(val, 'name'):
            print(f"  {i}: {inp.name}, type={inp.type}, linked={has_link}, val={val.name}")
        else:
            print(f"  {i}: {inp.name}, type={inp.type}, linked={has_link}, val={val}")
    else:
        print(f"  {i}: {inp.name}, type={inp.type}, linked={has_link}")

# Check outputs
print("\nSwitch outputs:")
for i, out in enumerate(switch.outputs):
    print(f"  {i}: {out.name}, type={out.type}")

# Check if there's a different way to use the switch
print("\nSwitch node attributes:")
for attr in dir(switch):
    if not attr.startswith('_') and attr not in ['rna_type', 'bl_rna', 'type', 'name', 'label', 'location', 'parent', 'select', 'hide', 'mute']:
        val = getattr(switch, attr, None)
        if val is not None and not callable(val):
            print(f"  {attr}: {val}")

# Set material
set_mat = nk.n("GeometryNodeSetMaterial", "SetMat", 280, 0)
nk.link(cone.outputs["Mesh"], set_mat.inputs["Geometry"])
nk.link(switch.outputs[0], set_mat.inputs["Material"])

# Output
nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

# Test with Debug_Mode = True (should get Debug_Mat_Test)
print("\n--- Test with Debug_Mode = True ---")
test_obj = bpy.data.objects.new("Test", bpy.data.meshes.new("Mesh"))
bpy.context.collection.objects.link(test_obj)
mod = test_obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree
mod["Debug_Mode"] = True
mod["Debug_Mat"] = debug_mat

# Verify modifier settings
print(f"Modifier Debug_Mode: {mod['Debug_Mode']}")
print(f"Modifier Debug_Mat: {mod['Debug_Mat'].name}")

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = test_obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
print(f"\nMesh materials: {[m.name if m else 'None' for m in mesh.materials]}")

# Check if maybe the issue is with how materials are indexed
print(f"Number of polygons: {len(mesh.polygons)}")
if mesh.polygons:
    print(f"First polygon material_index: {mesh.polygons[0].material_index}")

eval_obj.to_mesh_clear()
