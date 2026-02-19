"""Test UV sphere position in Blender 5.0."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test object
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node tree
nt = bpy.data.node_groups.new("SphereTest", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Create UV sphere with radius=5mm
sphere = nt.nodes.new("GeometryNodeMeshUVSphere")
sphere.inputs["Segments"].default_value = 32
sphere.inputs["Rings"].default_value = 8
sphere.inputs["Radius"].default_value = 0.005  # 5mm

# Transform with Z=5mm
combine = nt.nodes.new("ShaderNodeCombineXYZ")
combine.inputs["Z"].default_value = 0.005  # 5mm

xform = nt.nodes.new("GeometryNodeTransform")
nt.links.new(sphere.outputs["Mesh"], xform.inputs["Geometry"])
nt.links.new(combine.outputs[0], xform.inputs["Translation"])

nt.links.new(xform.outputs["Geometry"], go.inputs["Geometry"])

# Apply
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = nt

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

z_vals = [v.co.z * 1000 for v in mesh.vertices]
z_min = min(z_vals)
z_max = max(z_vals)
z_center = (z_min + z_max) / 2

print("=" * 60)
print("UV SPHERE WITH Z=5mm TRANSLATION")
print("=" * 60)
print(f"Radius input: 5mm (0.005m)")
print(f"Z bounds: {z_min:.2f}mm to {z_max:.2f}mm")
print(f"Z center: {z_center:.2f}mm")
print("")
print("Expected if sphere is CENTERED:")
print("  Z bounds: 0mm to 10mm, center 5mm")
print("")

if abs(z_min) < 0.1 and abs(z_max - 10) < 0.1:
    print("  Sphere is CENTERED at origin")
else:
    print(f"  UNKNOWN: bounds are {z_min:.1f}mm to {z_max:.1f}mm")

eval_obj.to_mesh_clear()
