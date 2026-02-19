"""Final check: Z positions by material to verify stacking."""
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

ng = create_input_node_group("Final_Pos_Check")

bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Final_Check"

mod = obj.modifiers.new(name="Knob", type='NODES')
mod.node_group = ng

# Build socket map
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

# Apply test settings (matching render_knob.py debug mode)
test_settings = {
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

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("="*60)
print("FINAL Z POSITION CHECK")
print("="*60)

print("\nExpected Z positions (centers in mm):")
print("  B_Bot: 2*0.5 = 1mm")
print("  B_Mid: 2 + 6*0.5 = 5mm")
print("  B_Top: 2+6 + 2*0.5 = 9mm")
print("  A_Bot: 2+6+2 + 2*0.5 = 11mm")
print("  A_Mid: 2+6+2+2 + 6*0.5 = 15mm")
print("  A_Top: 2+6+2+2+6 + 3*0.5 = 20mm")

# Get material info
mat_info = {}
for i, slot in enumerate(eval_obj.material_slots):
    if slot.material:
        mat_info[i] = slot.material.name

# Calculate Z centers and ranges by material
print("\nActual Z positions (from geometry):")
for poly in mesh.polygons:
    mat_idx = poly.material_index
    if mat_idx not in mat_info:
        continue
    if mat_idx not in mat_info:
        mat_info[mat_idx] = {'z_vals': [], 'name': mat_info.get(mat_idx, f'Mat_{mat_idx}')}
    if not hasattr(mat_info[mat_idx], 'z_vals'):
        mat_info[mat_idx] = {'z_vals': [], 'name': mat_info[mat_idx] if isinstance(mat_info[mat_idx], str) else f'Mat_{mat_idx}'}
    for vi in poly.vertices:
        mat_info[mat_idx]['z_vals'].append(mesh.vertices[vi].co.z)

# Re-read with proper structure
mat_data = {}
for i, slot in enumerate(eval_obj.material_slots):
    if slot.material:
        mat_data[i] = {'name': slot.material.name, 'z_vals': []}

for poly in mesh.polygons:
    mat_idx = poly.material_index
    if mat_idx in mat_data:
        for vi in poly.vertices:
            mat_data[mat_idx]['z_vals'].append(mesh.vertices[vi].co.z)

for idx in sorted(mat_data.keys()):
    z_vals = mat_data[idx]['z_vals']
    if z_vals:
        avg_z = sum(z_vals) / len(z_vals) * 1000
        min_z = min(z_vals) * 1000
        max_z = max(z_vals) * 1000
        print(f"  {mat_data[idx]['name']}: center={avg_z:.1f}mm, span={min_z:.1f}-{max_z:.1f}mm")

eval_obj.to_mesh_clear()
