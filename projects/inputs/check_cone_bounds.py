"""Check the actual cone geometry bounds."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

ng = create_input_node_group("Cone_Bounds_Test")

# Create test object
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Cone_Test"

mod = obj.modifiers.new(name="Knob", type='NODES')
mod.node_group = ng

# Build socket map
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

# Apply test settings - all with 2mm heights for simplicity
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
    "B_Bot_Style": 0,  # Flat cylinder
}

for key, value in test_settings.items():
    if key in socket_map:
        mod[socket_map[key]] = value

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("="*60)
print("CONE GEOMETRY BOUNDS ANALYSIS")
print("="*60)

print(f"\nTotal vertices: {len(mesh.vertices)}")
print(f"Total polygons: {len(mesh.polygons)}")

# Get overall Z bounds
z_vals = [v.co.z for v in mesh.vertices]
print(f"\nOverall Z bounds: {min(z_vals)*1000:.2f}mm to {max(z_vals)*1000:.2f}mm")

# Get material names
mat_names = {}
for i, slot in enumerate(eval_obj.material_slots):
    if slot.material:
        mat_names[i] = slot.material.name

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

# The key insight: where does each section actually start and end?
print("\n" + "="*60)
print("ANALYSIS")
print("="*60)

print("""
Expected geometry:
  B_Bot (cylinder, h=2mm): Z=0 to Z=2, center=1mm
  B_Mid (cone, h=6mm): Z=2 to Z=8, center=5mm
  B_Top (cone, h=2mm): Z=8 to Z=10, center=9mm

For B_Mid to have center at 5mm with depth=6mm:
  - Cone created at origin (Z=-3 to Z=3)
  - Translated to center=5mm -> Z=2 to Z=8 (correct!)

For B_Mid to have center at 8mm with depth=6mm:
  - Cone created at origin (Z=-3 to Z=3)
  - Translated to center=8mm -> Z=5 to Z=11 (wrong!)

The issue is the translation value. Let's verify what translation is being applied.
""")

eval_obj.to_mesh_clear()

# Now let's directly check the transform node's translation input
print("="*60)
print("TRANSFORM NODE ANALYSIS")
print("="*60)

node_map = {n.name: n for n in ng.nodes}

# Find B_Mid_Xform
if "B_Mid_Xform" in node_map:
    xform = node_map["B_Mid_Xform"]
    trans_socket = xform.inputs["Translation"]
    print(f"\nB_Mid_Xform Translation input:")
    if trans_socket.links:
        link = trans_socket.links[0]
        combine = link.from_node
        print(f"  Connected to: {combine.name}")

        # Check Z input of combine
        z_socket = combine.inputs["Z"]
        if z_socket.links:
            z_link = z_socket.links[0]
            z_node = z_link.from_node
            print(f"  Z input <- {z_node.name}")

            # Trace back to find the actual computation
            print(f"    Operation: {z_node.operation}")
            for i, inp in enumerate(z_node.inputs):
                if inp.links:
                    sub = inp.links[0]
                    print(f"    Input[{i}] <- {sub.from_node.name}")
                else:
                    print(f"    Input[{i}] = {inp.default_value}")
