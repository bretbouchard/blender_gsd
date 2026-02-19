"""Verify the position fix for all 6 sections."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create debug materials (rainbow palette)
def create_debug_material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.5

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat

# Create 6 debug materials with distinct colors
debug_mats = {
    "B_Bot": create_debug_material("Debug_B_Bot", (1.0, 0.0, 0.0)),    # Red
    "B_Mid": create_debug_material("Debug_B_Mid", (1.0, 0.5, 0.0)),    # Orange
    "B_Top": create_debug_material("Debug_B_Top", (1.0, 1.0, 0.0)),    # Yellow
    "A_Bot": create_debug_material("Debug_A_Bot", (0.0, 1.0, 0.0)),    # Green
    "A_Mid": create_debug_material("Debug_A_Mid", (0.0, 0.5, 1.0)),    # Light Blue
    "A_Top": create_debug_material("Debug_A_Top", (0.5, 0.0, 1.0)),    # Purple
}

# Create test object
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node group
ng = create_input_node_group("Verify_Fix")

# Apply modifier
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = ng

# Enable debug mode and set debug materials
mod["Debug_Mode"] = True
for section, mat in debug_mats.items():
    mod[f"Debug_{section}_Material"] = mat

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
# B_Bot (cylinder): base=0, center=0+1=1mm, depth=2mm → Z: 0 to 2
# B_Mid (cone): base=2, depth=6mm → Z: 2 to 8
# B_Top (cone): base=2+6=8, depth=4mm → Z: 8 to 12
# A_Bot (cone): base=2+6+4=12, depth=3mm → Z: 12 to 15
# A_Mid (cone): base=2+6+4+3=15, depth=6mm → Z: 15 to 21
# A_Top (cylinder): base=2+6+4+3+6=21, center=21+1.5=22.5mm, depth=3mm → Z: 21 to 24

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

# Get material indices and their polygons
material_polygons = {}
for i, poly in enumerate(mesh.polygons):
    mat_idx = poly.material_index
    if mat_idx not in material_polygons:
        material_polygons[mat_idx] = []
    material_polygons[mat_idx].append(i)

print(f"\nMaterials used: {sorted(material_polygons.keys())}")

# For each material, get Z bounds
print("\n" + "=" * 60)
print("ACTUAL Z BOUNDS BY MATERIAL")
print("=" * 60)

# Material indices: 0=B_Bot, 1=B_Mid, 2=B_Top, 3=A_Bot, 4=A_Mid, 5=A_Top
section_names = ['B_Bot', 'B_Mid', 'B_Top', 'A_Bot', 'A_Mid', 'A_Top']
expected_bounds = [
    (0, b_bot_h),
    (b_bot_h, b_bot_h + b_mid_h),
    (b_bot_h + b_mid_h, b_bot_h + b_mid_h + b_top_h),
    (b_bot_h + b_mid_h + b_top_h, b_bot_h + b_mid_h + b_top_h + a_bot_h),
    (b_bot_h + b_mid_h + b_top_h + a_bot_h, b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h),
    (b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h, b_bot_h + b_mid_h + b_top_h + a_bot_h + a_mid_h + a_top_h),
]

all_ok = True
for mat_idx in sorted(material_polygons.keys()):
    poly_indices = material_polygons[mat_idx]

    # Get all vertices for these polygons
    vertex_indices = set()
    for pi in poly_indices:
        poly = mesh.polygons[pi]
        vertex_indices.update(poly.vertices)

    # Get Z bounds
    z_vals = [mesh.vertices[vi].co.z * 1000 for vi in vertex_indices]  # Convert to mm
    z_min = min(z_vals)
    z_max = max(z_vals)

    section_name = section_names[mat_idx] if mat_idx < len(section_names) else f"Mat_{mat_idx}"
    exp_min, exp_max = expected_bounds[mat_idx]

    # Check if bounds are correct (with small tolerance)
    tol = 0.1
    min_ok = abs(z_min - exp_min) < tol
    max_ok = abs(z_max - exp_max) < tol
    status = "✓" if (min_ok and max_ok) else "✗"
    if not (min_ok and max_ok):
        all_ok = False

    print(f"\n{section_name} (mat {mat_idx}): {len(poly_indices)} polys")
    print(f"  Z bounds: {z_min:.2f}mm to {z_max:.2f}mm")
    print(f"  Expected: {exp_min:.2f}mm to {exp_max:.2f}mm")
    print(f"  Status: {status}")

print("\n" + "=" * 60)
if all_ok:
    print("✓ ALL SECTIONS HAVE CORRECT POSITIONS!")
else:
    print("✗ SOME SECTIONS HAVE INCORRECT POSITIONS")
print("=" * 60)

eval_obj.to_mesh_clear()
