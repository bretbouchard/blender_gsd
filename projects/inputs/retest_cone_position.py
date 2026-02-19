"""Re-test cone position in Blender 5.0."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test object
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node tree
nt = bpy.data.node_groups.new("ConeTest", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Create cone with depth=6mm
cone = nt.nodes.new("GeometryNodeMeshCone")
cone.inputs["Vertices"].default_value = 32
cone.inputs["Radius Top"].default_value = 0.005
cone.inputs["Radius Bottom"].default_value = 0.008
cone.inputs["Depth"].default_value = 0.006  # 6mm

# Transform with Z=0 (no translation)
combine = nt.nodes.new("ShaderNodeCombineXYZ")
combine.inputs["Z"].default_value = 0.0

xform = nt.nodes.new("GeometryNodeTransform")
nt.links.new(cone.outputs["Mesh"], xform.inputs["Geometry"])
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
print("CONE WITH Z=0 (NO TRANSLATION)")
print("=" * 60)
print(f"Depth input: 6mm (0.006m)")
print(f"Z bounds: {z_min:.2f}mm to {z_max:.2f}mm")
print(f"Z center: {z_center:.2f}mm")
print("")
print("Expected if cone is CENTERED at origin:")
print("  Z bounds: -3mm to 3mm, center 0mm")
print("")
print("Expected if cone BASE is at origin:")
print("  Z bounds: 0mm to 6mm, center 3mm")
print("")
print("ACTUAL BEHAVIOR:")
if abs(z_min + 3) < 0.1 and abs(z_max - 3) < 0.1:
    print("  Cone is CENTERED at origin")
elif abs(z_min) < 0.1 and abs(z_max - 6) < 0.1:
    print("  Cone BASE is at origin")
else:
    print(f"  UNKNOWN: bounds are {z_min:.1f}mm to {z_max:.1f}mm")

eval_obj.to_mesh_clear()
