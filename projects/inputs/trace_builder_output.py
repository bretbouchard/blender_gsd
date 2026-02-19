"""Check for node name collisions in the actual builder output."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

ng = create_input_node_group("Collision_Test")

print("="*60)
print("NODE NAME COLLISION CHECK")
print("="*60)

# Count nodes by name
name_count = {}
for node in ng.nodes:
    name = node.name
    if name not in name_count:
        name_count[name] = []
    name_count[name].append(node)

# Find duplicates
print("\nDuplicate node names:")
for name, nodes in sorted(name_count.items()):
    if len(nodes) > 1:
        print(f"  {name}: {len(nodes)} nodes!")
        for n in nodes:
            print(f"    - type={n.type}, loc=({n.location.x}, {n.location.y})")

# Check specific nodes
print("\n--- Position-related Math Nodes ---")
for node in ng.nodes:
    if node.type == 'MATH' and any(x in node.name for x in ['Bot', 'Mid', 'Top', 'Z', 'Half', 'Total']):
        print(f"\n{node.name}:")
        print(f"  Location: ({node.location.x}, {node.location.y})")
        print(f"  Operation: {node.operation}")
        for i, inp in enumerate(node.inputs):
            if inp.links:
                link = inp.links[0]
                print(f"  Input[{i}] <- {link.from_node.name}")
            else:
                print(f"  Input[{i}] = {inp.default_value}")

# Also check if there are any unexpected node connections
print("\n" + "="*60)
print("B_Mid_Half OUTPUT CONNECTIONS")
print("="*60)

node_map = {n.name: n for n in ng.nodes}
if "B_Mid_Half" in node_map:
    node = node_map["B_Mid_Half"]
    out = node.outputs[0]
    print(f"\nNode: {node.name} at ({node.location.x}, {node.location.y})")
    print(f"Output connections ({len(out.links)}):")
    for link in out.links:
        print(f"  -> {link.to_node.name} (input {link.to_socket.name})")
