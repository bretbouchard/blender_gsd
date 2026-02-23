"""Verify the position fix for all 6 sections using Z bounds analysis."""
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
ng = create_input_node_group("Verify_Fix")

# Apply modifier
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = ng

# Build socket map for setting values
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

# Set FLAT caps for accurate position verification
# (Rounded spheres extend beyond the expected height)
mod[socket_map["B_Bot_Style"]] = 0  # Flat cylinder
mod[socket_map["A_Top_Style"]] = 0  # Flat cylinder
mod[socket_map["A_Knurl"]] = False  # Disable knurling
mod[socket_map["B_Knurl"]] = False  # Disable knurling

# Get default values from interface
defaults = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        defaults[item.name] = item.default_value

print("=" * 60)
print("SECTION POSITION VERIFICATION")
print("=" * 60)
print("\nDefault heights:")
print(f"  B_Bot_Height: {defaults['B_Bot_Height']}mm")
print(f"  B_Mid_Height: {defaults['B_Mid_Height']}mm")
print(f"  B_Top_Height: {defaults['B_Top_Height']}mm")
print(f"  A_Bot_Height: {defaults['A_Bot_Height']}mm")
print(f"  A_Mid_Height: {defaults['A_Mid_Height']}mm")
print(f"  A_Top_Height: {defaults['A_Top_Height']}mm")

# Expected Z positions (in mm):
# B_Bot (cylinder, centered): base=0, center=0+1=1mm, depth=2mm → Z: 0 to 2
# B_Mid (cone, base at Z=0): base=2, depth=6mm → Z: 2 to 8
# B_Top (cone, base at Z=0): base=2+6=8, depth=2mm → Z: 8 to 10
# A_Bot (cone, base at Z=0): base=2+6+2=10, depth=2mm → Z: 10 to 12
# A_Mid (cone, base at Z=0): base=2+6+2+2=12, depth=6mm → Z: 12 to 18
# A_Top (cylinder, centered): base=2+6+2+2+6=18, center=18+1.5=19.5mm, depth=3mm → Z: 18 to 21

b_bot_h = defaults['B_Bot_Height']
b_mid_h = defaults['B_Mid_Height']
b_top_h = defaults['B_Top_Height']
a_bot_h = defaults['A_Bot_Height']
a_mid_h = defaults['A_Mid_Height']
a_top_h = defaults['A_Top_Height']

print("\nExpected Z bounds (mm):")
print(f"  B_Bot (cyl): 0 to {b_bot_h}")
print(f"  B_Mid (cone): {b_bot_h} to {b_bot_h + b_mid_h}")
print(f"  B_Top (cone): {b_bot_h + b_mid_h} to {b_bot_h + b_mid_h + b_top_h}")
print(f"  A_Bot (cone): {b_bot_h + b_mid_h + b_top_h} to {b_bot_h + b_mid_h + b_top_h + a_bot_h}")
print(f"  A_Mid (cone): {b_bot_h + b_mid_h + b_top_h + a_bot_h} to {b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h}")
print(f"  A_Top (cyl): {b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h} to {b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h + a_top_h}")

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print(f"\nTotal vertices: {len(mesh.vertices)}")

if len(mesh.vertices) == 0:
    print("ERROR: No vertices in mesh!")
else:
    # Get all Z values
    z_vals = [v.co.z * 1000 for v in mesh.vertices]  # Convert to mm
    z_min = min(z_vals)
    z_max = max(z_vals)

    print(f"\nOverall Z bounds: {z_min:.2f}mm to {z_max:.2f}mm")

    # Calculate expected total height
    total_expected = b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h + a_top_h
    print(f"Expected total height: {total_expected}mm")

    # Check if overall bounds are correct
    tol = 0.1
    min_ok = abs(z_min - 0) < tol
    max_ok = abs(z_max - total_expected) < tol

    print(f"\nOverall bounds check:")
    print(f"  Z_min: {z_min:.2f}mm (expected 0mm) - {'✓' if min_ok else '✗'}")
    print(f"  Z_max: {z_max:.2f}mm (expected {total_expected}mm) - {'✓' if max_ok else '✗'}")

    # Now let's sample Z values at different heights to check section positions
    # We'll look for "breaks" in the geometry at section boundaries
    print("\n" + "=" * 60)
    print("SECTION BOUNDARY ANALYSIS")
    print("=" * 60)

    # Section boundaries (in mm)
    boundaries = [
        0,  # Start
        b_bot_h,
        b_bot_h + b_mid_h,
        b_bot_h + b_mid_h + b_top_h,
        b_bot_h + b_mid_h + b_top_h + a_bot_h,
        b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h,
        b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h + a_top_h
    ]
    section_names = ['B_Bot', 'B_Mid', 'B_Top', 'A_Bot', 'A_Mid', 'A_Top']

    # Count vertices in each section
    for i in range(len(section_names)):
        lower = boundaries[i]
        upper = boundaries[i + 1]
        count = sum(1 for z in z_vals if lower - 0.1 <= z <= upper + 0.1)
        print(f"  {section_names[i]}: {count} vertices in range [{lower:.1f}, {upper:.1f}]mm")

print("\n" + "=" * 60)
if min_ok and max_ok:
    print("✓ POSITION FIX VERIFIED - Overall bounds are correct!")
else:
    print("✗ POSITION FIX INCOMPLETE - Bounds are off")
print("=" * 60)

eval_obj.to_mesh_clear()
