"""Verify the position fix with detailed material tracking."""
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

print("=" * 60)
print("MODIFIER INPUT VALUES")
print("=" * 60)

# Check what the modifier actually received
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        if "Debug" in item.name or "B_" in item.name or "A_" in item.name:
            try:
                val = mod[item.name]
                print(f"  {item.name}: {val}")
            except KeyError:
                print(f"  {item.name}: NOT SET")

# Check object's material slots
print("\n" + "=" * 60)
print("OBJECT MATERIAL SLOTS")
print("=" * 60)
print(f"Material slots: {len(obj.material_slots)}")
for i, slot in enumerate(obj.material_slots):
    print(f"  Slot {i}: {slot.material.name if slot.material else 'None'}")

# Evaluate
print("\n" + "=" * 60)
print("EVALUATING GEOMETRY")
print("=" * 60)

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print(f"Total vertices: {len(mesh.vertices)}")
print(f"Total polygons: {len(mesh.polygons)}")

# Get materials from mesh
print(f"\nMesh materials: {len(mesh.materials)}")
for i, mat in enumerate(mesh.materials):
    print(f"  Mat {i}: {mat.name if mat else 'None'}")

# Get polygon material indices
mat_indices = set()
for poly in mesh.polygons:
    mat_indices.add(poly.material_index)

print(f"\nMaterial indices used: {sorted(mat_indices)}")

# Count polygons by material index
mat_counts = {}
for poly in mesh.polygons:
    idx = poly.material_index
    if idx not in mat_counts:
        mat_counts[idx] = 0
    mat_counts[idx] += 1

print("\nPolygon counts by material index:")
for idx in sorted(mat_counts.keys()):
    mat_name = mesh.materials[idx].name if idx < len(mesh.materials) and mesh.materials[idx] else "None"
    print(f"  Mat {idx} ({mat_name}): {mat_counts[idx]} polys")

eval_obj.to_mesh_clear()
