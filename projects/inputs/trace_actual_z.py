"""Trace actual Z positions in evaluated geometry."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test object
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node group
ng = create_input_node_group("Trace_Z")

# Apply modifier
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = ng

# Get defaults
defaults = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        defaults[item.name] = item.default_value

# Build socket map and set flat caps
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

mod[socket_map["B_Bot_Style"]] = 0  # Flat
mod[socket_map["A_Top_Style"]] = 0  # Flat
mod[socket_map["A_Knurl"]] = False
mod[socket_map["B_Knurl"]] = False

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("=" * 60)
print("ACTUAL Z POSITIONS IN GEOMETRY")
print("=" * 60)

# Get defaults
b_bot_h = defaults['B_Bot_Height']
b_mid_h = defaults['B_Mid_Height']
b_top_h = defaults['B_Top_Height']
a_bot_h = defaults['A_Bot_Height']
a_mid_h = defaults['A_Mid_Height']
a_top_h = defaults['A_Top_Height']

print(f"\nHeight settings (mm):")
print(f"  B_Bot: {b_bot_h}")
print(f"  B_Mid: {b_mid_h}")
print(f"  B_Top: {b_top_h}")
print(f"  A_Bot: {a_bot_h}")
print(f"  A_Mid: {a_mid_h}")
print(f"  A_Top: {a_top_h}")

print(f"\nExpected translations (mm):")
print(f"  B_Bot (cyl, centered): Z = B_Bot_H/2 = {b_bot_h/2}")
print(f"  B_Mid (cone, base at 0): Z = B_Bot_H = {b_bot_h}")
print(f"  B_Top (cone, base at 0): Z = B_Bot_H + B_Mid_H = {b_bot_h + b_mid_h}")
print(f"  A_Bot (cone, base at 0): Z = B_Bot_H + B_Mid_H + B_Top_H = {b_bot_h + b_mid_h + b_top_h}")
print(f"  A_Mid (cone, base at 0): Z = ... + A_Bot_H = {b_bot_h + b_mid_h + b_top_h + a_bot_h}")
print(f"  A_Top (cyl, centered): Z = ... + A_Mid_H + A_Top_H/2 = {b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h + a_top_h/2}")

# Get Z values
z_vals = [v.co.z * 1000 for v in mesh.vertices]

# Find unique Z values
z_unique = sorted(set(round(z, 4) for z in z_vals))

print(f"\nActual Z positions found (unique values):")
for z in z_unique:
    count = sum(1 for vz in z_vals if abs(vz - z) < 0.01)
    print(f"  Z = {z:.2f}mm: {count} vertices")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("=" * 60)

# Check B_Bot (should have vertices at Z=0 and Z=2)
b_bot_expected = [0, b_bot_h]
b_bot_actual = [z for z in z_unique if z <= b_bot_h + 0.1]
print(f"\nB_Bot (should be at Z=0 and Z={b_bot_h}):")
print(f"  Actual: {[f'{z:.2f}' for z in b_bot_actual]}")

# Calculate the offset
if b_bot_actual:
    min_z = min(b_bot_actual)
    expected_min = 0
    offset = min_z - expected_min
    print(f"  Offset from expected: {offset:.2f}mm")

eval_obj.to_mesh_clear()
