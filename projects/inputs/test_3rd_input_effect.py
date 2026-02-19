"""Test if the third input of Blender 5.0 Math node affects ADD operation."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test object
bpy.ops.mesh.primitive_cube_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node tree
nt = bpy.data.node_groups.new("ThirdInputTest", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Chain: Multiply then Add
# Multiply: 6 * 0.001 = 0.006
math1 = nt.nodes.new("ShaderNodeMath")
math1.operation = "MULTIPLY"
math1.inputs[0].default_value = 6.0
math1.inputs[1].default_value = 0.001

# Multiply: result * 0.5 = 0.003
math2 = nt.nodes.new("ShaderNodeMath")
math2.operation = "MULTIPLY"
nt.links.new(math1.outputs[0], math2.inputs[0])
math2.inputs[1].default_value = 0.5

# Add: 2 + result = 2 + 3 = 5mm
# But let's try with different input[2] values
math3 = nt.nodes.new("ShaderNodeMath")
math3.operation = "ADD"
math3.inputs[0].default_value = 2.0
nt.links.new(math2.outputs[0], math3.inputs[1])

# Combine for transform
combine = nt.nodes.new("ShaderNodeCombineXYZ")
nt.links.new(math3.outputs[0], combine.inputs["Z"])

xform = nt.nodes.new("GeometryNodeTransform")
nt.links.new(gi.outputs[0], xform.inputs["Geometry"])
nt.links.new(combine.outputs[0], xform.inputs["Translation"])
nt.links.new(xform.outputs["Geometry"], go.inputs["Geometry"])

# Apply
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = nt

# Evaluate with input[2] = 0.5 (default)
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

z_center = sum(v.co.z for v in mesh.vertices) / len(mesh.vertices) * 1000
print(f"With input[2] = 0.5: Z center = {z_center:.3f}mm")
eval_obj.to_mesh_clear()

# Now set input[2] = 0.0 and re-evaluate
math3.inputs[2].default_value = 0.0
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

z_center = sum(v.co.z for v in mesh.vertices) / len(mesh.vertices) * 1000
print(f"With input[2] = 0.0: Z center = {z_center:.3f}mm")
eval_obj.to_mesh_clear()

# Now set input[2] = 3.0 (the difference we're seeing)
math3.inputs[2].default_value = 3.0
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

z_center = sum(v.co.z for v in mesh.vertices) / len(mesh.vertices) * 1000
print(f"With input[2] = 3.0: Z center = {z_center:.3f}mm")
eval_obj.to_mesh_clear()

print("\nConclusion:")
print("If input[2] affects the result, then Blender 5.0's Math node has a 3-operand mode!")
