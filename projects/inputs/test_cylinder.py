"""Test cylinder vertex distribution in Blender 5.0."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a cylinder with depth=2mm
cyl = bpy.data.meshes.new("Test_Cyl")
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.007,  # 7mm
    depth=0.002,   # 2mm
    vertices=64,
    location=(0, 0, 0)
)
obj = bpy.context.active_object

# Get mesh
mesh = obj.data

print("=" * 60)
print("CYLINDER VERTEX ANALYSIS")
print("=" * 60)
print(f"\nCylinder settings:")
print(f"  Radius: 7mm")
print(f"  Depth: 2mm")
print(f"  Location: (0, 0, 0)")
print(f"\nTotal vertices: {len(mesh.vertices)}")

# Get Z values
z_vals = [v.co.z * 1000 for v in mesh.vertices]
z_min = min(z_vals)
z_max = max(z_vals)
z_unique = sorted(set(round(z, 4) for z in z_vals))

print(f"\nZ bounds: {z_min:.4f}mm to {z_max:.4f}mm")
print(f"\nUnique Z heights:")
for z in z_unique:
    count = sum(1 for vz in z_vals if abs(vz - z) < 0.0001)
    print(f"  Z = {z:.4f}mm: {count} vertices")

print("\n" + "=" * 60)
print("EXPECTED: Cylinder is CENTERED, so Z should be -1mm to +1mm")
print("ACTUAL: See above")
print("=" * 60)

# Now translate by 1mm and check again
bpy.ops.transform.translate(value=(0, 0, 0.001))  # 1mm up

# Update mesh
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

z_vals = [v.co.z * 1000 for v in mesh.vertices]
z_min = min(z_vals)
z_max = max(z_vals)
z_unique = sorted(set(round(z, 4) for z in z_vals))

print("\n" + "=" * 60)
print("AFTER TRANSLATION BY +1mm:")
print("=" * 60)
print(f"Z bounds: {z_min:.4f}mm to {z_max:.4f}mm")
print(f"\nUnique Z heights:")
for z in z_unique:
    count = sum(1 for vz in z_vals if abs(vz - z) < 0.0001)
    print(f"  Z = {z:.4f}mm: {count} vertices")

print("\n" + "=" * 60)
print("EXPECTED: After +1mm translation, Z should be 0mm to +2mm")
print("=" * 60)
