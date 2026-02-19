"""Test what the 3rd input of Math node does in Blender 5.0."""
import bpy

# Create a test setup
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
obj = bpy.context.active_object

# Create a geometry node tree
nt = bpy.data.node_groups.new("Test_Math", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

# Add nodes
gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Create a math node
math1 = nt.nodes.new("ShaderNodeMath")
math1.operation = "MULTIPLY"
math1.inputs[0].default_value = 2.0
math1.inputs[1].default_value = 3.0
# Check if there's a 3rd input
print(f"Math node has {len(math1.inputs)} inputs")
for i, inp in enumerate(math1.inputs):
    print(f"  Input {i}: default = {inp.default_value}")

# Test calculation
result1 = math1.outputs[0].default_value
print(f"\nTest 1: 2.0 * 3.0 = {result1}")

# Change 3rd input if it exists
if len(math1.inputs) > 2:
    math1.inputs[2].default_value = 0.0
    result2 = math1.outputs[0].default_value
    print(f"Test 2: 2.0 * 3.0 (input[2]=0) = {result2}")

    math1.inputs[2].default_value = 1.0
    result3 = math1.outputs[0].default_value
    print(f"Test 3: 2.0 * 3.0 (input[2]=1) = {result3}")

    math1.inputs[2].default_value = 10.0
    result4 = math1.outputs[0].default_value
    print(f"Test 4: 2.0 * 3.0 (input[2]=10) = {result4}")

# Check for properties like 'use_clamp'
print(f"\nNode properties:")
for prop in dir(math1):
    if not prop.startswith('_') and not prop.startswith('bl_'):
        val = getattr(math1, prop, None)
        if 'clamp' in prop.lower() or 'use' in prop.lower():
            print(f"  {prop}: {val}")

# Check the actual node type
print(f"\nNode bl_idname: {math1.bl_idname}")
