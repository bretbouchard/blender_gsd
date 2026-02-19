"""Diagnose why overall bounds don't match section boundaries."""
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
ng = create_input_node_group("Diagnose_Bounds")

# Apply modifier
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = ng

# Build socket map
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

# Set FLAT caps (style=0) to eliminate sphere/cap uncertainty
mod[socket_map["B_Bot_Style"]] = 0  # Flat cylinder
mod[socket_map["A_Top_Style"]] = 0  # Flat cylinder

# Disable knurling for cleaner mesh
mod[socket_map["A_Knurl"]] = False
mod[socket_map["B_Knurl"]] = False

print("=" * 60)
print("DIAGNOSTIC: Overall vs Section Bounds")
print("=" * 60)
print("\nUsing FLAT caps (style=0) to eliminate sphere extension")

# Get defaults
defaults = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        defaults[item.name] = item.default_value

b_bot_h = defaults['B_Bot_Height']
b_mid_h = defaults['B_Mid_Height']
b_top_h = defaults['B_Top_Height']
a_bot_h = defaults['A_Bot_Height']
a_mid_h = defaults['A_Mid_Height']
a_top_h = defaults['A_Top_Height']

total_expected = b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h + a_top_h
print(f"\nExpected total height: {total_expected}mm")

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print(f"\nTotal vertices: {len(mesh.vertices)}")

if len(mesh.vertices) > 0:
    # Get all Z values
    z_vals = [v.co.z * 1000 for v in mesh.vertices]  # Convert to mm
    z_min = min(z_vals)
    z_max = max(z_vals)

    print(f"\nActual Z bounds: {z_min:.4f}mm to {z_max:.4f}mm")
    print(f"Z_min delta: {z_min - 0:.4f}mm")
    print(f"Z_max delta: {z_max - total_expected:.4f}mm")

    # Group vertices by Z height (rounded to 0.1mm)
    z_groups = {}
    for z in z_vals:
        z_rounded = round(z, 1)
        if z_rounded not in z_groups:
            z_groups[z_rounded] = 0
        z_groups[z_rounded] += 1

    print("\nZ height distribution (showing vertices at each height):")
    for z in sorted(z_groups.keys()):
        count = z_groups[z]
        bar = "#" * (count // 10)
        print(f"  Z={z:6.1f}mm: {count:4d} vertices {bar}")

    # Check if there are vertices below 0 or above expected
    below_zero = sum(1 for z in z_vals if z < -0.01)
    above_max = sum(1 for z in z_vals if z > total_expected + 0.01)
    print(f"\nVertices below Z=0: {below_zero}")
    print(f"Vertices above Z={total_expected}: {above_max}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)

eval_obj.to_mesh_clear()
