"""Test cylinder positioning via Geometry Nodes in Blender 5.0."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a geometry node tree that creates a cylinder and translates it
tree = bpy.data.node_groups.new("CylinderTest", "GeometryNodeTree")
nk = NodeKit(tree)
nk.clear()

# Add output socket
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

# Create nodes
go = nk.group_output(600, 0)

# Create cylinder
cyl = nk.n("GeometryNodeMeshCylinder", "Cylinder", 0, 0)
cyl.inputs["Radius"].default_value = 0.007  # 7mm
cyl.inputs["Depth"].default_value = 0.002   # 2mm
cyl.inputs["Vertices"].default_value = 64

# Create transform node
xform = nk.n("GeometryNodeTransform", "Transform", 300, 0)
xform.inputs["Translation"].default_value = (0, 0, 0.001)  # 1mm up

# Link
nk.link(cyl.outputs["Mesh"], xform.inputs["Geometry"])
nk.link(xform.outputs["Geometry"], go.inputs["Geometry"])

# Create object with this node group
bpy.ops.mesh.primitive_plane_add(size=0.001)
obj = bpy.context.active_object
obj.name = "Cylinder_Test"

mod = obj.modifiers.new(name="GN", type='NODES')
mod.node_group = tree

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("=" * 60)
print("GEOMETRY NODES CYLINDER TEST")
print("=" * 60)
print("\nCylinder via GN:")
print("  Radius: 7mm")
print("  Depth: 2mm")
print("  Translation: +1mm in Z")

z_vals = [v.co.z * 1000 for v in mesh.vertices]
z_min = min(z_vals)
z_max = max(z_vals)
z_unique = sorted(set(round(z, 4) for z in z_vals))

print(f"\nTotal vertices: {len(mesh.vertices)}")
print(f"Z bounds: {z_min:.4f}mm to {z_max:.4f}mm")
print(f"\nUnique Z heights:")
for z in z_unique:
    count = sum(1 for vz in z_vals if abs(vz - z) < 0.0001)
    print(f"  Z = {z:.4f}mm: {count} vertices")

print("\n" + "=" * 60)
print("EXPECTED: After +1mm translation, Z should be 0mm to +2mm")
if abs(z_min - 0) < 0.01 and abs(z_max - 2) < 0.01:
    print("RESULT: ✓ CORRECT")
else:
    print(f"RESULT: ✗ WRONG - got {z_min:.2f}mm to {z_max:.2f}mm")
print("=" * 60)

eval_obj.to_mesh_clear()
