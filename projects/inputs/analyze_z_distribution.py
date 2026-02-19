"""Analyze actual Z distribution in the generated mesh."""
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
ng = create_input_node_group("Analyze_Z")

# Apply modifier
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = ng

# Get default values
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

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

z_vals = sorted([v.co.z * 1000 for v in mesh.vertices])

print("=" * 60)
print("Z VALUE DISTRIBUTION ANALYSIS")
print("=" * 60)
print(f"\nTotal vertices: {len(z_vals)}")

# Show distribution
print(f"\nZ value distribution (every 50th vertex):")
for i in range(0, len(z_vals), 50):
    print(f"  Vertex {i}: Z = {z_vals[i]:.2f}mm")
print(f"  Last vertex: Z = {z_vals[-1]:.2f}mm")

# Find unique Z values and their counts
z_counts = {}
for z in z_vals:
    z_r = round(z, 2)
    if z_r not in z_counts:
        z_counts[z_r] = 0
    z_counts[z_r] += 1

print(f"\nUnique Z values (with counts > 10):")
for z in sorted(z_counts.keys()):
    if z_counts[z] > 10:
        print(f"  Z = {z:.2f}mm: {z_counts[z]} vertices")

# Expected boundaries
print("\n" + "=" * 60)
print("EXPECTED SECTION BOUNDARIES")
print("=" * 60)
print(f"  B_Bot (cyl, depth={b_bot_h}): 0 to {b_bot_h}mm")
print(f"  B_Mid (cone, depth={b_mid_h}): {b_bot_h} to {b_bot_h + b_mid_h}mm")
print(f"  B_Top (cone, depth={b_top_h}): {b_bot_h + b_mid_h} to {b_bot_h + b_mid_h + b_top_h}mm")
print(f"  A_Bot (cone, depth={a_bot_h}): {b_bot_h + b_mid_h + b_top_h} to {b_bot_h + b_mid_h + b_top_h + a_bot_h}mm")
print(f"  A_Mid (cone, depth={a_mid_h}): {b_bot_h + b_mid_h + b_top_h + a_bot_h} to {b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h}mm")
print(f"  A_Top (cyl, depth={a_top_h}): {b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h} to {b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h + a_top_h}mm")

# Find sections by looking at contiguous Z ranges
print("\n" + "=" * 60)
print("DETECTED Z RANGES (by gaps in Z values)")
print("=" * 60)

# Find significant gaps
z_unique = sorted(z_counts.keys())
gaps = []
for i in range(1, len(z_unique)):
    gap = z_unique[i] - z_unique[i-1]
    if gap > 0.1:  # Significant gap
        gaps.append((z_unique[i-1], z_unique[i], gap))

if gaps:
    print("Gaps found:")
    for low, high, gap in gaps:
        print(f"  Gap between {low:.2f}mm and {high:.2f}mm (size: {gap:.2f}mm)")
else:
    print("No significant gaps - all geometry is continuous")

eval_obj.to_mesh_clear()
