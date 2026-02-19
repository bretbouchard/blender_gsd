"""Check the actual cone geometry bounds with DEBUG MODE enabled."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group
from lib.inputs.debug_materials import create_all_debug_materials

ng = create_input_node_group("Debug_Bounds_Test")

# Create test object
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

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
    "B_Bot_Height": 2.0,
    "B_Mid_Height": 6.0,
    "B_Top_Height": 2.0,
    "A_Bot_Height": 2.0,
    "A_Mid_Height": 6.0,
    "A_Top_Height": 3.0,
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

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("="*60)
print("DEBUG MODE GEOMETRY BOUNDS")
print("="*60)

print(f"\nTotal vertices: {len(mesh.vertices)}")

# Get material names
mat_names = {}
for i, slot in enumerate(eval_obj.material_slots):
    if slot.material:
        mat_names[i] = slot.material.name

print(f"\nMaterial slots: {list(mat_names.values())}")

# Group by material
mat_info = {}
for poly in mesh.polygons:
    mat_idx = poly.material_index
    if mat_idx not in mat_info:
        mat_info[mat_idx] = {'min_z': float('inf'), 'max_z': float('-inf'), 'verts': set()}

    for vi in poly.vertices:
        v = mesh.vertices[vi]
        mat_info[mat_idx]['min_z'] = min(mat_info[mat_idx]['min_z'], v.co.z)
        mat_info[mat_idx]['max_z'] = max(mat_info[mat_idx]['max_z'], v.co.z)
        mat_info[mat_idx]['verts'].add(vi)

print("\nZ bounds by material:")
print("Expected: B_Bot=0-2, B_Mid=2-8, B_Top=8-10, A_Bot=10-12, A_Mid=12-18, A_Top=18-21")
print("")
for mat_idx in sorted(mat_info.keys()):
    info = mat_info[mat_idx]
    mat_name = mat_names.get(mat_idx, f"Mat_{mat_idx}")
    min_mm = info['min_z'] * 1000
    max_mm = info['max_z'] * 1000
    center_mm = (min_mm + max_mm) / 2
    print(f"  {mat_name}: {min_mm:.1f}mm to {max_mm:.1f}mm (center={center_mm:.1f}mm)")

# Focus on B_Mid
print("\n" + "="*60)
print("B_Mid ANALYSIS")
print("="*60)

if any("B_Mid" in mat_names.get(i, "") for i in mat_info):
    for mat_idx in mat_info:
        if "B_Mid" in mat_names.get(mat_idx, ""):
            info = mat_info[mat_idx]
            min_mm = info['min_z'] * 1000
            max_mm = info['max_z'] * 1000
            print(f"\nB_Mid actual bounds: {min_mm:.1f}mm to {max_mm:.1f}mm")
            print(f"B_Mid center: {(min_mm + max_mm)/2:.1f}mm")
            print(f"Depth: {max_mm - min_mm:.1f}mm (should be 6mm)")

            # The center tells us the translation Z value
            center = (min_mm + max_mm) / 2
            print(f"\nTranslation Z applied: {center:.1f}mm")
            print(f"Expected translation Z: 5.0mm (B_Bot_H + B_Mid_H/2 = 2 + 3)")
            print(f"Difference: {center - 5.0:.1f}mm")

eval_obj.to_mesh_clear()
