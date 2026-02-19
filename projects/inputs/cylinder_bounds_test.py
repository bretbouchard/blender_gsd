"""Test cylinder primitive bounds."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

nt = bpy.data.node_groups.new("CylinderTest", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Test cylinder
cyl = nt.nodes.new("GeometryNodeMeshCylinder")
cyl.inputs["Vertices"].default_value = 32
cyl.inputs["Radius"].default_value = 0.005
cyl.inputs["Depth"].default_value = 0.002  # 2mm

nt.links.new(cyl.outputs["Mesh"], go.inputs["Geometry"])

mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = nt

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

z_vals = [v.co.z for v in mesh.vertices]
print(f"Cylinder with depth=2mm:")
print(f"  Z bounds: {min(z_vals)*1000:.1f}mm to {max(z_vals)*1000:.1f}mm")
print(f"  Z center: {(min(z_vals)+max(z_vals))/2*1000:.1f}mm")
print(f"  Expected: -1mm to 1mm (centered) OR 0mm to 2mm (base at origin)")

eval_obj.to_mesh_clear()

# Also test UV sphere
bpy.data.node_groups.remove(nt)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

nt = bpy.data.node_groups.new("SphereTest", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

sphere = nt.nodes.new("GeometryNodeMeshUVSphere")
sphere.inputs["Segments"].default_value = 32
sphere.inputs["Rings"].default_value = 16
sphere.inputs["Radius"].default_value = 0.003  # 3mm radius

nt.links.new(sphere.outputs["Mesh"], go.inputs["Geometry"])

mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = nt

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

z_vals = [v.co.z for v in mesh.vertices]
print(f"\nUV Sphere with radius=3mm:")
print(f"  Z bounds: {min(z_vals)*1000:.1f}mm to {max(z_vals)*1000:.1f}mm")
print(f"  Z center: {(min(z_vals)+max(z_vals))/2*1000:.1f}mm")
print(f"  Expected: -3mm to 3mm (centered at origin)")
