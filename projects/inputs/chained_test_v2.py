"""Simple test of chained math operations - fixed."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a small test cube (1mm size)
bpy.ops.mesh.primitive_cube_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create geometry node tree
nt = bpy.data.node_groups.new("SimpleTest2", "GeometryNodeTree")

# Add Geometry input AND output
nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

# Add float inputs
b_bot_h = nt.interface.new_socket("B_Bot_Height", in_out="INPUT", socket_type="NodeSocketFloat")
b_bot_h.default_value = 2.0  # 2mm
b_mid_h = nt.interface.new_socket("B_Mid_Height", in_out="INPUT", socket_type="NodeSocketFloat")
b_mid_h.default_value = 6.0  # 6mm

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Unit conversion: B_Bot_Height * MM
MM = 0.001
math_b_bot_m = nt.nodes.new("ShaderNodeMath")
math_b_bot_m.operation = "MULTIPLY"
math_b_bot_m.location = (100, 0)
nt.links.new(gi.outputs["B_Bot_Height"], math_b_bot_m.inputs[0])
math_b_bot_m.inputs[1].default_value = MM

# Unit conversion: B_Mid_Height * MM
math_b_mid_m = nt.nodes.new("ShaderNodeMath")
math_b_mid_m.operation = "MULTIPLY"
math_b_mid_m.location = (100, -100)
nt.links.new(gi.outputs["B_Mid_Height"], math_b_mid_m.inputs[0])
math_b_mid_m.inputs[1].default_value = MM

# B_Mid_Half = B_MidH_M * 0.5
math_b_mid_half = nt.nodes.new("ShaderNodeMath")
math_b_mid_half.operation = "MULTIPLY"
math_b_mid_half.location = (200, -100)
nt.links.new(math_b_mid_m.outputs[0], math_b_mid_half.inputs[0])
math_b_mid_half.inputs[1].default_value = 0.5

# B_Mid_Z = B_BotH_M + B_Mid_Half
math_b_mid_z = nt.nodes.new("ShaderNodeMath")
math_b_mid_z.operation = "ADD"
math_b_mid_z.location = (300, -50)
nt.links.new(math_b_bot_m.outputs[0], math_b_mid_z.inputs[0])
nt.links.new(math_b_mid_half.outputs[0], math_b_mid_z.inputs[1])

# Combine XYZ for translation
combine = nt.nodes.new("ShaderNodeCombineXYZ")
combine.location = (400, 0)
nt.links.new(math_b_mid_z.outputs[0], combine.inputs["Z"])

# Transform
xform = nt.nodes.new("GeometryNodeTransform")
xform.location = (500, 0)
nt.links.new(gi.outputs["Geometry"], xform.inputs["Geometry"])  # Use named socket
nt.links.new(combine.outputs[0], xform.inputs["Translation"])
nt.links.new(xform.outputs["Geometry"], go.inputs["Geometry"])

# Apply modifier
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = nt

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("="*60)
print("CHAINED MATH TEST (simulating B_Mid_Z)")
print("="*60)

print("\nNode chain (expected: B_Mid_Z = 2mm + 3mm = 5mm):")
print(f"  B_Bot_Height = {b_bot_h.default_value}mm")
print(f"  B_Mid_Height = {b_mid_h.default_value}mm")
print(f"  B_BotH_M = {b_bot_h.default_value} * {MM} = {b_bot_h.default_value * MM}m")
print(f"  B_MidH_M = {b_mid_h.default_value} * {MM} = {b_mid_h.default_value * MM}m")
print(f"  B_Mid_Half = {b_mid_h.default_value * MM} * 0.5 = {b_mid_h.default_value * MM * 0.5}m = {b_mid_h.default_value * MM * 0.5 * 1000}mm")
print(f"  B_Mid_Z = {b_bot_h.default_value * MM} + {b_mid_h.default_value * MM * 0.5} = {b_bot_h.default_value * MM + b_mid_h.default_value * MM * 0.5}m = {(b_bot_h.default_value * MM + b_mid_h.default_value * MM * 0.5) * 1000}mm")

print(f"\nNumber of vertices: {len(mesh.vertices)}")

if len(mesh.vertices) > 0:
    print(f"\nCube vertices after translation:")
    z_vals = [v.co.z * 1000 for v in mesh.vertices]
    for i, z_mm in enumerate(z_vals[:8]):  # First 8 vertices
        print(f"  v{i}: Z = {z_mm:.3f}mm")

    center_z = sum(z_vals) / len(z_vals)
    print(f"\nActual Z center: {center_z:.3f}mm")
    print(f"Expected Z center: 5.0mm")
    print(f"Difference: {center_z - 5.0:.3f}mm")
else:
    print("ERROR: No vertices in evaluated mesh!")

eval_obj.to_mesh_clear()
