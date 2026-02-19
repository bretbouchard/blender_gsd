"""Trace the Join node links in the actual builder."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

# Create node group
ng = create_input_node_group("Trace_Join")

print("=" * 60)
print("DETAILED JOIN NODE ANALYSIS")
print("=" * 60)

# Find Join node
join_node = None
for node in ng.nodes:
    if node.type == 'JOIN_GEOMETRY':
        join_node = node
        break

if not join_node:
    print("ERROR: No Join node found!")
else:
    print(f"\nJoin node: {join_node.name}")
    print(f"  Number of inputs: {len(join_node.inputs)}")

    geo_input = join_node.inputs["Geometry"]
    print(f"  Geometry input:")
    print(f"    Is multi-input: {geo_input.is_multi_input}")
    print(f"    Number of links: {len(geo_input.links)}")

    print(f"\n  Links to Geometry input:")
    for i, link in enumerate(geo_input.links):
        print(f"    Link {i}: {link.from_node.name} -> {link.to_node.name}")

# Now let's check all the SetMaterial nodes and their output connections
print("\n" + "=" * 60)
print("SET MATERIAL NODE OUTPUT CONNECTIONS")
print("=" * 60)

for node in ng.nodes:
    if node.type == 'SET_MATERIAL':
        geo_out = node.outputs["Geometry"]
        print(f"\n{node.name}:")
        print(f"  Output connections: {len(geo_out.links)}")
        for link in geo_out.links:
            print(f"    -> {link.to_node.name} (input: {link.to_socket.name})")

# Check all links in the tree
print("\n" + "=" * 60)
print("ALL LINKS IN NODE TREE")
print("=" * 60)
print(f"Total links: {len(ng.links)}")

# Group links by destination node
links_by_dest = {}
for link in ng.links:
    dest_name = link.to_node.name
    if dest_name not in links_by_dest:
        links_by_dest[dest_name] = []
    links_by_dest[dest_name].append(link)

print("\nLinks to Join_All:")
if "Join_All" in links_by_dest:
    for link in links_by_dest["Join_All"]:
        print(f"  {link.from_node.name} -> Join_All")
else:
    print("  NONE!")
