"""Test if the inputs are being used correctly."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test object
bpy.ops.mesh.primitive_cube_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node tree with explicit interface inputs
nt = bpy.data.node_groups.new("InputTest", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

# Add our height inputs
b_bot = nt.interface.new_socket("B_Bot_Height", in_out="INPUT", socket_type="NodeSocketFloat")
b_bot.default_value = 2.0
b_mid = nt.interface.new_socket("B_Mid_Height", in_out="INPUT", socket_type="NodeSocketFloat")
b_mid.default_value = 6.0

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Unit conversion: B_Mid_Height * MM
MM = 0.001
math1 = nt.nodes.new("ShaderNodeMath")
math1.operation = "MULTIPLY"
nt.links.new(gi.outputs["B_Mid_Height"], math1.inputs[0])
math1.inputs[1].default_value = MM

# Half: result * 0.5
math2 = nt.nodes.new("ShaderNodeMath")
math2.operation = "MULTIPLY"
nt.links.new(math1.outputs[0], math2.inputs[0])
math2.inputs[1].default_value = 0.5

# Add: B_Bot_Height (in mm) + result (in m) - this is WRONG!
# B_Bot_Height is in mm, result is in m
# Let's also convert B_Bot_Height
math_bot = nt.nodes.new("ShaderNodeMath")
math_bot.operation = "MULTIPLY"
nt.links.new(gi.outputs["B_Bot_Height"], math_bot.inputs[0])
math_bot.inputs[1].default_value = MM

# Now add: B_BotH_M + B_Mid_Half
math3 = nt.nodes.new("ShaderNodeMath")
math3.operation = "ADD"
nt.links.new(math_bot.outputs[0], math3.inputs[0])
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

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

z_center = sum(v.co.z for v in mesh.vertices) / len(mesh.vertices) * 1000
print(f"Z center = {z_center:.3f}mm")
print(f"Expected: 5.0mm (2mm + 3mm)")
print(f"Difference: {z_center - 5.0:.3f}mm")

# Let's also check the node values
print("\nNode values:")
print(f"math1 (B_Mid_Height * MM): inputs = {math1.inputs[0].default_value if not math1.inputs[0].links else 'linked'}, {math1.inputs[1].default_value}")
print(f"math2 (result * 0.5): inputs = linked, {math2.inputs[1].default_value}")
print(f"math_bot (B_Bot_Height * MM): inputs = linked, {math_bot.inputs[1].default_value}")
print(f"math3 (B_BotH_M + B_Mid_Half): both inputs linked")

eval_obj.to_mesh_clear()
