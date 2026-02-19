"""Test if Blender 5.0 Math node's 3rd input adds to result."""
import bpy
import math

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test object
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Test_Obj"

# Create geometry node tree
nt = bpy.data.node_groups.new("Math3Test", "GeometryNodeTree")
nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
nt.interface.new_socket("Value", in_out="OUTPUT", socket_type="NodeSocketFloat")

gi = nt.nodes.new("NodeGroupInput")
go = nt.nodes.new("NodeGroupOutput")

# Test 1: Simple multiply
math_mult = nt.nodes.new("ShaderNodeMath")
math_mult.name = "TestMult"
math_mult.operation = "MULTIPLY"
math_mult.location = (200, 0)
math_mult.inputs[0].default_value = 6.0
math_mult.inputs[1].default_value = 0.5

# Test 2: Simple add
math_add = nt.nodes.new("ShaderNodeMath")
math_add.name = "TestAdd"
math_add.operation = "ADD"
math_add.location = (200, -200)
math_add.inputs[0].default_value = 2.0
math_add.inputs[1].default_value = 3.0

# Test 3: Chained - multiply then add
math_chain_1 = nt.nodes.new("ShaderNodeMath")
math_chain_1.name = "Chain1_Mult"
math_chain_1.operation = "MULTIPLY"
math_chain_1.location = (200, -400)
math_chain_1.inputs[0].default_value = 6.0
math_chain_1.inputs[1].default_value = 0.5

math_chain_2 = nt.nodes.new("ShaderNodeMath")
math_chain_2.name = "Chain2_Add"
math_chain_2.operation = "ADD"
math_chain_2.location = (400, -400)
nt.links.new(math_chain_1.outputs[0], math_chain_2.inputs[0])
math_chain_2.inputs[1].default_value = 2.0

# Connect to output
nt.links.new(math_chain_2.outputs[0], go.inputs["Value"])

# Apply to object
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = nt

# Evaluate and get the actual value
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)

# The output should be accessible via the modifier
# Let's check the evaluated value
print("="*60)
print("MATH NODE 3-INPUT TEST")
print("="*60)

print("\n--- Node Input Summary ---")
print(f"TestMult: {math_mult.inputs[0].default_value} * {math_mult.inputs[1].default_value}")
print(f"  Expected: 6.0 * 0.5 = 3.0")
print(f"  Input[2] = {math_mult.inputs[2].default_value}")

print(f"\nTestAdd: {math_add.inputs[0].default_value} + {math_add.inputs[1].default_value}")
print(f"  Expected: 2.0 + 3.0 = 5.0")
print(f"  Input[2] = {math_add.inputs[2].default_value}")

print(f"\nChain1_Mult: {math_chain_1.inputs[0].default_value} * {math_chain_1.inputs[1].default_value}")
print(f"  Expected: 6.0 * 0.5 = 3.0")
print(f"Chain2_Add: (result) + {math_chain_2.inputs[1].default_value}")
print(f"  Expected: 3.0 + 2.0 = 5.0")
print(f"  Input[2] = {math_chain_2.inputs[2].default_value}")

# Now try changing input[2] and see if it affects the output
print("\n--- Testing input[2] effect ---")

# Set input[2] to different values and check if result changes
for val in [0.0, 1.0, 5.0, 10.0]:
    math_chain_2.inputs[2].default_value = val
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    # Can't easily read output value, but we can check the node state
    print(f"  Chain2_Add input[2]={val}")

# Let me try a different approach - check if there's a 'use_clamp' or similar property
print(f"\n--- Math Node Properties ---")
for prop in ['use_clamp', 'operation', 'data_type']:
    if hasattr(math_mult, prop):
        print(f"  {prop}: {getattr(math_mult, prop)}")

# Check if input[2] has a special name or property
print(f"\n--- Input[2] Details ---")
inp2 = math_mult.inputs[2]
print(f"  Name: {inp2.name}")
print(f"  Type: {inp2.type}")
print(f"  Identifier: {inp2.identifier}")
print(f"  Default: {inp2.default_value}")
