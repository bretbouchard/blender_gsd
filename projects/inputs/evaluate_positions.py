"""Evaluate the actual computed position values using the Blender node tree."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

ng = create_input_node_group("Eval_Positions")

print("="*60)
print("POSITION VALUE EVALUATION")
print("="*60)

# Test values (in mm)
test_values = {
    "B_Bot_Height": 2.0,
    "B_Mid_Height": 6.0,
    "B_Top_Height": 2.0,
    "A_Bot_Height": 2.0,
    "A_Mid_Height": 6.0,
    "A_Top_Height": 3.0,
}

# Calculate expected values manually
# B_Bot_Z = B_Bot_Height * 0.5 = 2.0 * 0.5 = 1.0mm
# B_Mid_Z = B_Bot_Height + (B_Mid_Height * 0.5) = 2.0 + 3.0 = 5.0mm
# B_Top_Z = B_Bot_Height + B_Mid_Height + (B_Top_Height * 0.5) = 2.0 + 6.0 + 1.0 = 9.0mm

print("\nExpected Z positions (in mm):")
print(f"  B_Bot_Z = B_Bot_H * 0.5 = {test_values['B_Bot_Height']} * 0.5 = {test_values['B_Bot_Height'] * 0.5}mm")
print(f"  B_Mid_Z = B_Bot_H + (B_Mid_H * 0.5) = {test_values['B_Bot_Height']} + ({test_values['B_Mid_Height']} * 0.5) = {test_values['B_Bot_Height']} + {test_values['B_Mid_Height'] * 0.5} = {test_values['B_Bot_Height'] + test_values['B_Mid_Height'] * 0.5}mm")
print(f"  B_Top_Z = B_Bot_H + B_Mid_H + (B_Top_H * 0.5) = {test_values['B_Bot_Height']} + {test_values['B_Mid_Height']} + ({test_values['B_Top_Height']} * 0.5) = {test_values['B_Bot_Height'] + test_values['B_Mid_Height'] + test_values['B_Top_Height'] * 0.5}mm")

# Now create an object and evaluate the actual mesh
from lib.inputs.debug_materials import create_all_debug_materials

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Eval_Knob"

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
    "A_Top_Height": test_values["A_Top_Height"],
    "A_Mid_Height": test_values["A_Mid_Height"],
    "A_Bot_Height": test_values["A_Bot_Height"],
    "B_Width_Top": 11.9,
    "B_Width_Bot": 16.1,
    "B_Top_Height": test_values["B_Top_Height"],
    "B_Mid_Height": test_values["B_Mid_Height"],
    "B_Bot_Height": test_values["B_Bot_Height"],
    "B_Bot_Style": 0,
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

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("\n" + "="*60)
print("ACTUAL MESH Z POSITIONS")
print("="*60)

# Get material names
mat_names = {}
for i, slot in enumerate(eval_obj.material_slots):
    if slot.material:
        mat_names[i] = slot.material.name

# Calculate Z centers per material
mat_z_info = {}
for poly in mesh.polygons:
    mat_idx = poly.material_index
    if mat_idx not in mat_z_info:
        mat_z_info[mat_idx] = {'min_z': float('inf'), 'max_z': float('-inf'), 'count': 0}

    for vi in poly.vertices:
        z = mesh.vertices[vi].co.z
        mat_z_info[mat_idx]['min_z'] = min(mat_z_info[mat_idx]['min_z'], z)
        mat_z_info[mat_idx]['max_z'] = max(mat_z_info[mat_idx]['max_z'], z)
        mat_z_info[mat_idx]['count'] += 1

print("\nActual Z positions (converted to mm):")
for mat_idx in sorted(mat_z_info.keys()):
    info = mat_z_info[mat_idx]
    mat_name = mat_names.get(mat_idx, f"Mat_{mat_idx}")
    center_mm = ((info['min_z'] + info['max_z']) / 2) * 1000
    min_mm = info['min_z'] * 1000
    max_mm = info['max_z'] * 1000
    print(f"  {mat_name}: center={center_mm:.2f}mm (range: {min_mm:.2f}-{max_mm:.2f}mm)")

# Compare with expected
print("\n" + "="*60)
print("COMPARISON (Expected vs Actual)")
print("="*60)

expected = {
    "Debug_B_Bot": 1.0,
    "Debug_B_Mid": 5.0,
    "Debug_B_Top": 9.0,
    "Debug_A_Bot": 11.0,
    "Debug_A_Mid": 15.0,
    "Debug_A_Top": 20.0,
}

for mat_name, expected_z in expected.items():
    # Find actual
    for mat_idx, info in mat_z_info.items():
        actual_name = mat_names.get(mat_idx, "")
        if mat_name in actual_name:
            actual_center = ((info['min_z'] + info['max_z']) / 2) * 1000
            diff = actual_center - expected_z
            status = "OK" if abs(diff) < 0.1 else f"OFF BY {diff:.1f}mm"
            print(f"  {mat_name}: expected={expected_z}mm, actual={actual_center:.2f}mm [{status}]")
            break

eval_obj.to_mesh_clear()
