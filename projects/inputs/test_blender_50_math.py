"""Test Blender 5.0 Math node behavior with 3 inputs."""
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a simple test mesh
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
obj = bpy.context.active_object

# Create geometry node tree
nt = bpy.data.node_groups.new("Test_Math_3Input", "GeometryNodeTree")
nt.interface.new_socket("Result", in_out="OUTPUT", socket_type="NodeSocketFloat")

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Create a simple chain: multiply 2 * 3 = 6
math1 = nt.nodes.new("ShaderNodeMath")
math1.name = "Mult_2x3"
math1.operation = "MULTIPLY"
math1.location = (200, 0)
math1.inputs[0].default_value = 2.0
math1.inputs[1].default_value = 3.0

print(f"\n=== Initial Math Node State ===")
print(f"Inputs count: {len(math1.inputs)}")
for i, inp in enumerate(math1.inputs):
    print(f"  Input {i}: {inp.default_value}")
print(f"Output default_value: {math1.outputs[0].default_value}")

# Now let's see what happens with 3 inputs
# Let's create a second math node that adds 5 to the result
math2 = nt.nodes.new("ShaderNodeMath")
math2.name = "Add_5"
math2.operation = "ADD"
math2.location = (400, 0)
nt.links.new(math1.outputs[0], math2.inputs[0])
math2.inputs[1].default_value = 5.0

print(f"\n=== Second Math Node State ===")
print(f"Inputs count: {len(math2.inputs)}")
for i, inp in enumerate(math2.inputs):
    print(f"  Input {i}: {inp.default_value}")

# Connect output
nt.links.new(math2.outputs[0], go.inputs[0])

# Assign to object
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = nt

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)

print(f"\n=== Test Result ===")
print("Expected: 2 * 3 + 5 = 11")
print("The math nodes should chain correctly.")

# Now let's check what input[2] does
print(f"\n=== Testing Input[2] Effect ===")

# Create another test
math3 = nt.nodes.new("ShaderNodeMath")
math3.name = "Test_3rd_Input"
math3.operation = "ADD"
math3.location = (600, 0)
math3.inputs[0].default_value = 10.0
math3.inputs[1].default_value = 20.0
math3.inputs[2].default_value = 0.0

# Check if input[2] affects the output
print(f"ADD with 10 + 20 + input[2]=0")

# Try different values
for val in [0.0, 5.0, 30.0, 100.0]:
    math3.inputs[2].default_value = val
    # We can't easily read the evaluated value, but let's see if there's a pattern

# Let's check if there's documentation or a tooltip
print(f"\nMath node type: {math3.bl_idname}")
print(f"Math node description: {math3.bl_description if hasattr(math3, 'bl_description') else 'N/A'}")

# Check for any properties related to the 3rd input
for prop_name in dir(math3):
    if 'input' in prop_name.lower() and not prop_name.startswith('_'):
        try:
            val = getattr(math3, prop_name)
            if not callable(val):
                print(f"  {prop_name}: {val}")
        except:
            pass
