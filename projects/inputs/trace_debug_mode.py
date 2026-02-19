"""Check if debug mode switch is actually working."""
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

ng = create_input_node_group("Debug_Switch_Test")

bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Debug_Test"

mod = obj.modifiers.new(name="Knob", type='NODES')
mod.node_group = ng

# Build socket map
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

# Apply test settings
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

# Enable debug mode AND assign materials
debug_mats = create_all_debug_materials(preset="rainbow")

# Enable debug mode FIRST
mod[socket_map["Debug_Mode"]] = True
print(f"Debug_Mode set to: {mod[socket_map['Debug_Mode']]}")

# Then assign materials
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
        print(f"Assigned {socket_name} = {debug_mats[section_name].name}")

# Evaluate and check materials
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("\n" + "="*60)
print("MATERIAL ANALYSIS")
print("="*60)

# Get material names
print("\nMaterial slots:")
for i, slot in enumerate(eval_obj.material_slots):
    print(f"  Slot {i}: {slot.material.name if slot.material else 'None'}")

# Count polygons by material
mat_counts = {}
for poly in mesh.polygons:
    mat_idx = poly.material_index
    mat_counts[mat_idx] = mat_counts.get(mat_idx, 0) + 1

print("\nPolygons by material index:")
for idx in sorted(mat_counts.keys()):
    slot_name = eval_obj.material_slots[idx].material.name if idx < len(eval_obj.material_slots) and eval_obj.material_slots[idx].material else f"Slot_{idx}"
    print(f"  Material {idx} ({slot_name}): {mat_counts[idx]} polygons")

eval_obj.to_mesh_clear()
