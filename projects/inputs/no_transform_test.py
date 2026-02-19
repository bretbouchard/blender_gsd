"""Test cone primitive bounds without any transform."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test object
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node tree
nt = bpy.data.node_groups.new("ConeOnlyTest", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Create cone with NO transform
cone = nt.nodes.new("GeometryNodeMeshCone")
cone.inputs["Vertices"].default_value = 32
cone.inputs["Radius Top"].default_value = 0.005
cone.inputs["Radius Bottom"].default_value = 0.008
cone.inputs["Depth"].default_value = 0.006  # 6mm

# Output directly
nt.links.new(cone.outputs["Mesh"], go.inputs["Geometry"])

# Apply
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = nt

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

z_vals = [v.co.z for v in mesh.vertices]
z_min = min(z_vals)
z_max = max(z_vals)
z_center = (z_min + z_max) / 2

print("Cone with NO transform:")
print(f"  Depth input: 0.006m (6mm)")
print(f"  Z bounds: {z_min*1000:.1f}mm to {z_max*1000:.1f}mm")
print(f"  Z center: {z_center*1000:.1f}mm")
print(f"  Expected center: 0mm (cone is centered at origin)")
print("")

eval_obj.to_mesh_clear()

# Now with transform to Z=0 (identity)
nt2 = bpy.data.node_groups.new("ConeZeroTransform", "GeometryNodeTree")
nt2.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt2.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi2 = nt2.nodes.new("NodeGroupInput")
go2 = nt2.nodes.new("NodeGroupOutput")

cone2 = nt2.nodes.new("GeometryNodeMeshCone")
cone2.inputs["Vertices"].default_value = 32
cone2.inputs["Radius Top"].default_value = 0.005
cone2.inputs["Radius Bottom"].default_value = 0.008
cone2.inputs["Depth"].default_value = 0.006

# Transform with Z=0
combine2 = nt2.nodes.new("ShaderNodeCombineXYZ")
combine2.inputs["Z"].default_value = 0.0

xform2 = nt2.nodes.new("GeometryNodeTransform")
nt2.links.new(cone2.outputs["Mesh"], xform2.inputs["Geometry"])
nt2.links.new(combine2.outputs[0], xform2.inputs["Translation"])

nt2.links.new(xform2.outputs["Geometry"], go2.inputs["Geometry"])

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj2 = bpy.context.active_object
mod2 = obj2.modifiers.new(name="Test", type='NODES')
mod2.node_group = nt2

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj2 = obj2.evaluated_get(depsgraph)
mesh2 = eval_obj2.to_mesh()

z_vals2 = [v.co.z for v in mesh2.vertices]
z_min2 = min(z_vals2)
z_max2 = max(z_vals2)
z_center2 = (z_min2 + z_max2) / 2

print("Cone with transform Z=0:")
print(f"  Z bounds: {z_min2*1000:.1f}mm to {z_max2*1000:.1f}mm")
print(f"  Z center: {z_center2*1000:.1f}mm")
print(f"  Expected: -3mm to 3mm, center 0mm")
print("")

eval_obj2.to_mesh_clear()

# Now with Z=0.005 (5mm)
nt3 = bpy.data.node_groups.new("Cone5mmTransform", "GeometryNodeTree")
nt3.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt3.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi3 = nt3.nodes.new("NodeGroupInput")
go3 = nt3.nodes.new("NodeGroupOutput")

cone3 = nt3.nodes.new("GeometryNodeMeshCone")
cone3.inputs["Vertices"].default_value = 32
cone3.inputs["Radius Top"].default_value = 0.005
cone3.inputs["Radius Bottom"].default_value = 0.008
cone3.inputs["Depth"].default_value = 0.006

combine3 = nt3.nodes.new("ShaderNodeCombineXYZ")
combine3.inputs["Z"].default_value = 0.005  # 5mm

xform3 = nt3.nodes.new("GeometryNodeTransform")
nt3.links.new(cone3.outputs["Mesh"], xform3.inputs["Geometry"])
nt3.links.new(combine3.outputs[0], xform3.inputs["Translation"])

nt3.links.new(xform3.outputs["Geometry"], go3.inputs["Geometry"])

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj3 = bpy.context.active_object
mod3 = obj3.modifiers.new(name="Test", type='NODES')
mod3.node_group = nt3

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj3 = obj3.evaluated_get(depsgraph)
mesh3 = eval_obj3.to_mesh()

z_vals3 = [v.co.z for v in mesh3.vertices]
z_min3 = min(z_vals3)
z_max3 = max(z_vals3)
z_center3 = (z_min3 + z_max3) / 2

print("Cone with transform Z=5mm:")
print(f"  Z bounds: {z_min3*1000:.1f}mm to {z_max3*1000:.1f}mm")
print(f"  Z center: {z_center3*1000:.1f}mm")
print(f"  Expected: 2mm to 8mm, center 5mm")
print("")

eval_obj3.to_mesh_clear()

print("DIAGNOSIS:")
print("If Z=0 gives center=3mm (not 0mm), then the cone is created with a +3mm offset.")
print("If Z=5mm gives center=8mm (not 5mm), then there's a +3mm offset being added.")
