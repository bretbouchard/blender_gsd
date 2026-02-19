"""Create a direct test to see actual evaluated values."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a test cube
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
obj = bpy.context.active_object

# Create geometry node tree
nt = bpy.data.node_groups.new("DirectTest", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Create position node, separate Z, and pass through
pos = nt.nodes.new("GeometryNodeInputPosition")
pos.location = (0, 0)

# Transform node to move the cube
xform = nt.nodes.new("GeometryNodeTransform")
xform.location = (400, 0)

# Math node for Z translation
math_z = nt.nodes.new("ShaderNodeMath")
math_z.operation = "ADD"
math_z.location = (200, -100)
math_z.inputs[0].default_value = 0.0  # Start at 0
math_z.inputs[1].default_value = 0.005  # Add 5mm = 0.005m

# Combine XYZ for translation
combine = nt.nodes.new("ShaderNodeCombineXYZ")
combine.location = (200, 0)
nt.links.new(math_z.outputs[0], combine.inputs["Z"])

# Connect
nt.links.new(gi.outputs[0], xform.inputs["Geometry"])
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
print("DIRECT TRANSLATION TEST")
print("="*60)

# The cube should be translated by 5mm in Z
# Original cube is at Z=0 (size 1 means -0.5 to 0.5)
# After translation of +5mm, it should be at Z=4.5mm to 5.5mm

print(f"\nMath node inputs:")
print(f"  Input[0] = {math_z.inputs[0].default_value}")
print(f"  Input[1] = {math_z.inputs[1].default_value}")
print(f"  Input[2] = {math_z.inputs[2].default_value}")

print(f"\nCube vertices (original center at 0, size 1):")
for i, v in enumerate(obj.data.vertices[:4]):
    print(f"  Original v{i}: Z = {v.co.z * 1000:.1f}mm")

print(f"\nCube vertices after translation (expected +5mm in Z):")
for i, v in enumerate(mesh.vertices[:4]):
    print(f"  Evaluated v{i}: Z = {v.co.z * 1000:.1f}mm")

# Calculate the actual translation applied
original_z = obj.data.vertices[0].co.z
evaluated_z = mesh.vertices[0].co.z
translation_z = (evaluated_z - original_z) * 1000

print(f"\nActual Z translation applied: {translation_z:.1f}mm")
print(f"Expected Z translation: 5.0mm")
print(f"Difference: {translation_z - 5.0:.1f}mm")

eval_obj.to_mesh_clear()
