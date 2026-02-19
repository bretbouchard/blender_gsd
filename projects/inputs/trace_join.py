"""Debug the Join node input issue."""
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

print("Join node inputs BEFORE linking:")
print(f"  Number of inputs: {len(join.inputs)}")
for i, inp in enumerate(join.inputs):
    print(f"    Input {i}: {inp.name}, type={inp.type}")

# Try to link all 6 cones
for i, cone in enumerate(cones):
    print(f"\nLinking Cone_{i} to Join...")
    nk.link(cone.outputs["Mesh"], join.inputs["Geometry"])
    print(f"  Number of inputs after link {i}: {len(join.inputs)}")

print("\n\nJoin node inputs AFTER all linking:")
print(f"  Number of inputs: {len(join.inputs)}")
for i, inp in enumerate(join.inputs):
    if inp.links:
        print(f"    Input {i} '{inp.name}': connected to {inp.links[0].from_node.name}")
    else:
        print(f"    Input {i} '{inp.name}': NOT connected")

# Link to output
nk.link(join.outputs["Geometry"], go.inputs["Geometry"])

print("\n\nThis shows if Join node auto-creates inputs or if we need to add them manually.")
