"""Trace complete data flow from primitive to final output."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group
from lib.inputs.debug_materials import create_all_debug_materials

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create the node group
ng = create_input_node_group("Flow_Trace")

# Create a test object
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Flow_Knob"

mod = obj.modifiers.new(name="Knob", type='NODES')
mod.node_group = ng

# Build socket map
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

# Apply test settings
settings = {
    "Segments": 32,
    "A_Width_Top": 8.4,
    "A_Width_Bot": 11.9,
    "A_Top_Height": 3.0,
    "A_Mid_Height": 6.0,
    "A_Bot_Height": 2.0,
    "B_Width_Top": 11.9,
    "B_Width_Bot": 16.1,
    "B_Top_Height": 2.0,
    "B_Mid_Height": 6.0,
    "B_Bot_Height": 2.0,
    "B_Bot_Style": 0,  # Flat cap
}

for key, value in settings.items():
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

# Evaluate and check mesh data
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("="*60)
print("MESH DATA ANALYSIS")
print("="*60)

print(f"\nTotal vertices: {len(mesh.vertices)}")
print(f"Total polygons: {len(mesh.polygons)}")

# Group polygons by material index
mat_polys = {}
for poly in mesh.polygons:
    mat_idx = poly.material_index
    if mat_idx not in mat_polys:
        mat_polys[mat_idx] = []
    mat_polys[mat_idx].append(poly)

# Get material names
mat_names = {}
for i, slot in enumerate(eval_obj.material_slots):
    if slot.material:
        mat_names[i] = slot.material.name
    else:
        mat_names[i] = f"Slot_{i}_None"

print("\nPolygons by material index:")
for mat_idx in sorted(mat_polys.keys()):
    polys = mat_polys[mat_idx]
    # Get Z range for this material
    min_z = float('inf')
    max_z = float('-inf')
    for poly in polys:
        for vi in poly.vertices:
            z = mesh.vertices[vi].co.z
            min_z = min(min_z, z)
            max_z = max(max_z, z)
    print(f"  Material {mat_idx} ({mat_names.get(mat_idx, 'Unknown')}):")
    print(f"    Polygons: {len(polys)}")
    print(f"    Z range: {min_z*1000:.1f}mm to {max_z*1000:.1f}mm")

# Check if any polygons have material_index 0
print("\n--- Material Index 0 Analysis ---")
if 0 in mat_polys:
    polys_0 = mat_polys[0]
    print(f"Polygons with material_index=0: {len(polys_0)}")

    # Get the vertices for these polys
    verts_0 = set()
    for poly in polys_0:
        verts_0.update(poly.vertices)

    min_z = min(mesh.vertices[vi].co.z for vi in verts_0)
    max_z = max(mesh.vertices[vi].co.z for vi in verts_0)
    print(f"Z range: {min_z*1000:.1f}mm to {max_z*1000:.1f}mm")

# Check material slot assignments
print("\n--- Material Slots ---")
for i, slot in enumerate(eval_obj.material_slots):
    print(f"Slot {i}: {slot.material.name if slot.material else 'None'}")

eval_obj.to_mesh_clear()
