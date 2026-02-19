"""Check exact Z positions of vertices by material."""
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
ng = create_input_node_group("Z_Pos_Test")

# Create a test object
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Z_Test_Knob"

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

# Force evaluation
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("="*60)
print("VERTEX Z POSITIONS BY MATERIAL INDEX")
print("="*60)

# Material name mapping
mat_names = ["None"]
for i, slot in enumerate(eval_obj.material_slots):
    if slot.material:
        mat_names.append(slot.material.name)
    else:
        mat_names.append(f"Slot_{i}")

# Group vertices by material index and find Z range
mat_z_ranges = {}
for poly in mesh.polygons:
    mat_idx = poly.material_index
    if mat_idx not in mat_z_ranges:
        mat_z_ranges[mat_idx] = {'min_z': float('inf'), 'max_z': float('-inf'), 'count': 0}

    for vert_idx in poly.vertices:
        v = mesh.vertices[vert_idx]
        mat_z_ranges[mat_idx]['min_z'] = min(mat_z_ranges[mat_idx]['min_z'], v.co.z)
        mat_z_ranges[mat_idx]['max_z'] = max(mat_z_ranges[mat_idx]['max_z'], v.co.z)
        mat_z_ranges[mat_idx]['count'] += 1

print("\nExpected positions (in mm):")
print("  B_Bot: 1mm (2*0.5)")
print("  B_Mid: 5mm (2 + 6*0.5)")
print("  B_Top: 9mm (2+6 + 2*0.5)")
print("  A_Bot: 11mm (2+6+2 + 2*0.5)")
print("  A_Mid: 15mm (2+6+2+2 + 6*0.5)")
print("  A_Top: 20mm (2+6+2+2+6 + 3*0.5)")

print("\nActual Z positions (in mm):")
for mat_idx in sorted(mat_z_ranges.keys()):
    info = mat_z_ranges[mat_idx]
    mat_name = mat_names[mat_idx] if mat_idx < len(mat_names) else f"Index_{mat_idx}"
    min_mm = info['min_z'] * 1000
    max_mm = info['max_z'] * 1000
    center_mm = (min_mm + max_mm) / 2
    print(f"  {mat_name}: Z={min_mm:.1f} to {max_mm:.1f}mm (center={center_mm:.1f}mm) [{info['count']} vertices]")

eval_obj.to_mesh_clear()
