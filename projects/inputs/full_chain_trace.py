"""Full chain trace to find where the calculation goes wrong."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group
from lib.inputs.debug_materials import create_all_debug_materials

ng = create_input_node_group("Full_Trace")

# Create test object
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Trace_Knob"

mod = obj.modifiers.new(name="Knob", type='NODES')
mod.node_group = ng

# Build socket map
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

# Apply known test values
test_settings = {
    "Segments": 32,
    "B_Bot_Height": 2.0,  # -> 0.002m
    "B_Mid_Height": 6.0,  # -> 0.006m
    "B_Top_Height": 2.0,  # -> 0.002m
    "A_Bot_Height": 2.0,
    "A_Mid_Height": 6.0,
    "A_Top_Height": 3.0,
    # Widths
    "A_Width_Top": 8.4,
    "A_Width_Bot": 11.9,
    "B_Width_Top": 11.9,
    "B_Width_Bot": 16.1,
    "B_Bot_Style": 0,
}

for key, value in test_settings.items():
    if key in socket_map:
        mod[socket_map[key]] = value

# Enable debug mode
debug_mats = create_all_debug_materials(preset="rainbow")
mod[socket_map["Debug_Mode"]] = True

section_map = {
    "Debug_A_Top_Material": "A_Top",
    "Debug_A_Mid_Material": "A_Mid",
    "Debug_A_Bot_Material": "A_Bot",
    "Debug_B_Top_Material": "B_Top",
    "Debug_B_Mid_Material": "B_Mid",
    "Debug_B_Bot_Material": "B_Bot",
}

for socket_name, section_name in section_map.items():
    if socket_name in socket_map and section_name in debug_mats:
        mod[socket_map[socket_name]] = debug_mats[section_name]

# Now let's trace through the ACTUAL evaluation
# We need to find the transform nodes and see what their translation values are
print("="*60)
print("TRANSFORM NODE ANALYSIS")
print("="*60)

# Evaluate the depsgraph
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)

# Find the transform nodes in the node group
node_map = {n.name: n for n in ng.nodes}

# Check B_Bot transform
print("\n--- B_Bot_Xform ---")
if "B_Bot_Xform" in node_map:
    xform = node_map["B_Bot_Xform"]
    trans_socket = xform.inputs["Translation"]
    if trans_socket.links:
        link = trans_socket.links[0]
        print(f"Translation connected to: {link.from_node.name}.{link.from_socket.name}")

        # Check the CombineXYZ node
        combine = link.from_node
        print(f"Combine node: {combine.name}")

        # Check Z input
        z_socket = combine.inputs["Z"]
        if z_socket.links:
            z_link = z_socket.links[0]
            print(f"  Z input <- {z_link.from_node.name}.{z_link.from_socket.name}")

            # Check what that node is connected to
            z_node = z_link.from_node
            if z_node.type == 'MATH':
                print(f"    Operation: {z_node.operation}")
                for i, inp in enumerate(z_node.inputs):
                    if inp.links:
                        sub_link = inp.links[0]
                        print(f"    Input[{i}] <- {sub_link.from_node.name}.{sub_link.from_socket.name}")
                    else:
                        print(f"    Input[{i}] = {inp.default_value}")
        else:
            print(f"  Z input = {z_socket.default_value}")

# Check B_Mid transform
print("\n--- B_Mid_Xform ---")
if "B_Mid_Xform" in node_map:
    xform = node_map["B_Mid_Xform"]
    trans_socket = xform.inputs["Translation"]
    if trans_socket.links:
        link = trans_socket.links[0]
        print(f"Translation connected to: {link.from_node.name}.{link.from_socket.name}")

        combine = link.from_node
        print(f"Combine node: {combine.name}")

        z_socket = combine.inputs["Z"]
        if z_socket.links:
            z_link = z_socket.links[0]
            print(f"  Z input <- {z_link.from_node.name}.{z_link.from_socket.name}")

            z_node = z_link.from_node
            if z_node.type == 'MATH':
                print(f"    Operation: {z_node.operation}")
                for i, inp in enumerate(z_node.inputs):
                    if inp.links:
                        sub_link = inp.links[0]
                        print(f"    Input[{i}] <- {sub_link.from_node.name}.{sub_link.from_socket.name}")
                    else:
                        print(f"    Input[{i}] = {inp.default_value}")

# Now let's check what the ACTUAL values are in the evaluated mesh
print("\n" + "="*60)
print("EVALUATED MESH VERTEX POSITIONS")
print("="*60)

mesh = eval_obj.to_mesh()

# Find a single vertex from each section to see its actual Z
# Group by material
mat_verts = {}
for poly in mesh.polygons:
    mat_idx = poly.material_index
    if mat_idx not in mat_verts:
        mat_verts[mat_idx] = set()
    for vi in poly.vertices:
        mat_verts[mat_idx].add(vi)

# Get material names
mat_names = {}
for i, slot in enumerate(eval_obj.material_slots):
    if slot.material:
        mat_names[i] = slot.material.name

# Print sample vertices
print("\nSample vertex Z positions:")
for mat_idx in sorted(mat_verts.keys()):
    mat_name = mat_names.get(mat_idx, f"Mat_{mat_idx}")
    verts = list(mat_verts[mat_idx])[:3]  # First 3 vertices
    for vi in verts:
        v = mesh.vertices[vi]
        print(f"  {mat_name} vertex {vi}: Z = {v.co.z * 1000:.2f}mm")

eval_obj.to_mesh_clear()

# Expected B_Mid cone: depth=6mm, centered at origin -> Z = -3mm to +3mm
# Translated by B_Mid_Z = 5mm -> actual Z = 2mm to 8mm
# But if translated by B_Mid_Z = 8mm -> actual Z = 5mm to 11mm
print("\n" + "="*60)
print("DIAGNOSIS")
print("="*60)
print("""
Expected B_Mid behavior:
  - Cone depth: 6mm (created at Z=-3 to Z=3)
  - B_Mid_Z should be: 5mm (B_Bot_H + B_Mid_H*0.5 = 2 + 3)
  - Final position: Z=2mm to Z=8mm (centered at 5mm)

If actual center is 8mm:
  - Cone depth: 6mm (at Z=-3 to Z=3)
  - Actual translation appears to be: 8mm
  - That would place it at Z=5mm to Z=11mm (centered at 8mm)

This suggests B_Mid_Z is being calculated as B_Bot_H + B_Mid_H = 2 + 6 = 8
instead of B_Bot_H + (B_Mid_H * 0.5) = 2 + 3 = 5
""")
