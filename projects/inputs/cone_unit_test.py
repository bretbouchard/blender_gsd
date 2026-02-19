"""Cone test with unit conversion - exactly like the working test."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test object
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node tree with explicit interface inputs
nt = bpy.data.node_groups.new("ConeUnitTest", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

# Add our height inputs
b_bot = nt.interface.new_socket("B_Bot_Height", in_out="INPUT", socket_type="NodeSocketFloat")
b_bot.default_value = 2.0
b_mid = nt.interface.new_socket("B_Mid_Height", in_out="INPUT", socket_type="NodeSocketFloat")
b_mid.default_value = 6.0

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

MM = 0.001

# Unit conversion: B_Bot_Height * MM
math_bot = nt.nodes.new("ShaderNodeMath")
math_bot.operation = "MULTIPLY"
nt.links.new(gi.outputs["B_Bot_Height"], math_bot.inputs[0])
math_bot.inputs[1].default_value = MM
math_bot.name = "B_BotH_M"

# Unit conversion: B_Mid_Height * MM
math1 = nt.nodes.new("ShaderNodeMath")
math1.operation = "MULTIPLY"
nt.links.new(gi.outputs["B_Mid_Height"], math1.inputs[0])
math1.inputs[1].default_value = MM
math1.name = "B_MidH_M"

# Half: B_MidH_M * 0.5
math2 = nt.nodes.new("ShaderNodeMath")
math2.operation = "MULTIPLY"
nt.links.new(math1.outputs[0], math2.inputs[0])
math2.inputs[1].default_value = 0.5
math2.name = "B_Mid_Half"

# Add: B_Mid_Half + B_BotH_M (swapped order)
math3 = nt.nodes.new("ShaderNodeMath")
math3.operation = "ADD"
nt.links.new(math2.outputs[0], math3.inputs[0])  # B_Mid_Half first
nt.links.new(math_bot.outputs[0], math3.inputs[1])  # B_BotH_M second
math3.name = "B_Mid_Z"

# Create cone
cone = nt.nodes.new("GeometryNodeMeshCone")
cone.name = "B_Mid_Cone"
cone.inputs["Vertices"].default_value = 32
cone.inputs["Radius Top"].default_value = 0.005
cone.inputs["Radius Bottom"].default_value = 0.008
nt.links.new(math1.outputs[0], cone.inputs["Depth"])  # Use B_MidH_M for depth

# Combine for transform
combine = nt.nodes.new("ShaderNodeCombineXYZ")
combine.name = "B_Mid_Pos"
nt.links.new(math3.outputs[0], combine.inputs["Z"])

xform = nt.nodes.new("GeometryNodeTransform")
xform.name = "B_Mid_Xform"
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

print(f"Cone Z bounds: {z_min:.1f}mm to {z_max:.1f}mm")
print(f"Cone Z center: {z_center:.1f}mm")
print(f"Expected: 5.0mm")
print(f"Difference: {z_center - 5.0:.1f}mm")

# Check the node connections
print("\n--- B_Mid_Z node ---")
n = nt.nodes["B_Mid_Z"]
for i, inp in enumerate(n.inputs):
    if inp.links:
        print(f"Input[{i}] <- {inp.links[0].from_node.name}")
    else:
        print(f"Input[{i}] = {inp.default_value}")

eval_obj.to_mesh_clear()
