"""Test how to add multiple inputs to Join node in Blender 5.0."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

# Create a test node tree
if "JoinTest" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["JoinTest"])

tree = bpy.data.node_groups.new("JoinTest", "GeometryNodeTree")
nk = NodeKit(tree)

# Create group input/output
tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gi = nk.group_input(0, 0)
go = nk.group_output(1000, 0)

# Create 6 primitive cones
cones = []
for i in range(6):
    cone = nk.n("GeometryNodeMeshCone", f"Cone_{i}", 100, i * 100)
    cones.append(cone)

# Create join node
join = nk.n("GeometryNodeJoinGeometry", "Join", 500, 0)

print("=" * 60)
print("JOIN NODE INPUTS - Blender 5.0")
print("=" * 60)

# Method 1: Check if we can add inputs via the node's socket collection
print("\nMethod 1: Check node.inputs type and methods")
print(f"  Type: {type(join.inputs)}")
print(f"  Dir: {[x for x in dir(join.inputs) if not x.startswith('_')]}")

# Method 2: Try to add inputs via new()
if hasattr(join.inputs, 'new'):
    print("\nMethod 2: Try inputs.new()")
    try:
        join.inputs.new('NodeSocketGeometry', 'Geometry')
        print("  SUCCESS!")
    except Exception as e:
        print(f"  FAILED: {e}")

# Method 3: Check if there's a multi_input_socket or similar
print("\nMethod 3: Check for multi-input capability")
for inp in join.inputs:
    print(f"  Input '{inp.name}':")
    print(f"    Type: {inp.type}")
    print(f"    Is Multi Input: {getattr(inp, 'is_multi_input', 'N/A')}")
    print(f"    Dir: {[x for x in dir(inp) if not x.startswith('_') and 'multi' in x.lower()]}")

# Method 4: Check Blender version specific API
print("\nMethod 4: Blender version")
import bpy
print(f"  Version: {bpy.app.version}")

# Method 5: Try linking multiple outputs to same input (multi-input)
print("\nMethod 5: Try multi-linking to single input")
join2 = nk.n("GeometryNodeJoinGeometry", "Join2", 500, -200)
# Try using tree.links.new directly with multiple links to same socket
for i, cone in enumerate(cones):
    try:
        # Use the tree.links.new() method directly
        link = tree.links.new(cone.outputs["Mesh"], join2.inputs["Geometry"])
        print(f"  Cone_{i}: link = {link is not None}")
    except Exception as e:
        print(f"  Cone_{i}: ERROR - {e}")

print(f"\nJoin2 inputs after multi-link:")
for i, inp in enumerate(join2.inputs):
    print(f"  Input {i} '{inp.name}': {len(inp.links)} links")
    for link in inp.links:
        print(f"    -> {link.from_node.name}")
