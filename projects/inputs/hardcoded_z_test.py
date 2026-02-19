"""Test with hardcoded Z value."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test object
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node tree
nt = bpy.data.node_groups.new("HardcodedTest", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Create cone with hardcoded depth
cone = nt.nodes.new("GeometryNodeMeshCone")
cone.inputs["Vertices"].default_value = 32
cone.inputs["Radius Top"].default_value = 0.005
cone.inputs["Radius Bottom"].default_value = 0.008
cone.inputs["Depth"].default_value = 0.006  # Hardcoded 6mm

# Combine with hardcoded Z = 0.005 (5mm)
combine = nt.nodes.new("ShaderNodeCombineXYZ")
combine.inputs["Z"].default_value = 0.005  # Hardcoded 5mm

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

print(f"Hardcoded Z = 5mm:")
print(f"  Cone Z bounds: {z_min:.1f}mm to {z_max:.1f}mm")
print(f"  Cone Z center: {z_center:.1f}mm")
print(f"  Expected: 5.0mm")
print(f"  Difference: {z_center - 5.0:.1f}mm")

eval_obj.to_mesh_clear()

# Now try with computed Z from simple math
nt2 = bpy.data.node_groups.new("ComputedTest", "GeometryNodeTree")
nt2.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt2.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi2 = nt2.nodes.new("NodeGroupInput")
go2 = nt2.nodes.new("NodeGroupOutput")

# Simple: 2 + 3 = 5
math_add = nt2.nodes.new("ShaderNodeMath")
math_add.operation = "ADD"
math_add.inputs[0].default_value = 2.0
math_add.inputs[1].default_value = 3.0

# Convert to meters
math_m = nt2.nodes.new("ShaderNodeMath")
math_m.operation = "MULTIPLY"
nt2.links.new(math_add.outputs[0], math_m.inputs[0])
math_m.inputs[1].default_value = 0.001

# Create cone
cone2 = nt2.nodes.new("GeometryNodeMeshCone")
cone2.inputs["Vertices"].default_value = 32
cone2.inputs["Radius Top"].default_value = 0.005
cone2.inputs["Radius Bottom"].default_value = 0.008
cone2.inputs["Depth"].default_value = 0.006

# Combine
combine2 = nt2.nodes.new("ShaderNodeCombineXYZ")
nt2.links.new(math_m.outputs[0], combine2.inputs["Z"])

xform2 = nt2.nodes.new("GeometryNodeTransform")
nt2.links.new(cone2.outputs["Mesh"], xform2.inputs["Geometry"])
nt2.links.new(combine2.outputs[0], xform2.inputs["Translation"])

nt2.links.new(xform2.outputs["Geometry"], go2.inputs["Geometry"])

# Apply
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj2 = bpy.context.active_object
mod2 = obj2.modifiers.new(name="Test", type='NODES')
mod2.node_group = nt2

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj2 = obj2.evaluated_get(depsgraph)
mesh2 = eval_obj2.to_mesh()

z_vals2 = [v.co.z * 1000 for v in mesh2.vertices]
z_min2 = min(z_vals2)
z_max2 = max(z_vals2)
z_center2 = (z_min2 + z_max2) / 2

print(f"\nComputed Z = 2 + 3 = 5mm (in mm, then * 0.001):")
print(f"  Cone Z bounds: {z_min2:.1f}mm to {z_max2:.1f}mm")
print(f"  Cone Z center: {z_center2:.1f}mm")
print(f"  Expected: 5.0mm")
print(f"  Difference: {z_center2 - 5.0:.1f}mm")

eval_obj2.to_mesh_clear()
