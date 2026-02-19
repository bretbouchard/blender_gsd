"""Trace the position calculation nodes in the actual builder output."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

# Create node group
ng = create_input_node_group("Trace_Math")

print("=" * 60)
print("POSITION CALCULATION NODE TRACE")
print("=" * 60)

# Find all math nodes
math_nodes = {n.name: n for n in ng.nodes if n.type == 'MATH'}

# Find the relevant ones
relevant = ['B_BotH_M', 'B_Bot_Half', 'B_Bot+Mid', 'B_Total', 'B+A_Bot', 'B+A_Mid', 'A_Top_Half', 'A_Top_Z']

for name in relevant:
    if name in math_nodes:
        node = math_nodes[name]
        print(f"\n{name}:")
        print(f"  Operation: {node.operation}")
        for i, inp in enumerate(node.inputs):
            if inp.links:
                link = inp.links[0]
                print(f"  Input[{i}] <- {link.from_node.name} (output: {link.from_socket.name})")
            else:
                print(f"  Input[{i}] = {inp.default_value}")
    else:
        print(f"\n{name}: NOT FOUND")

# Check the CombineXYZ nodes
print("\n" + "=" * 60)
print("COMBINE XYZ NODES (Position)")
print("=" * 60)

combine_nodes = {n.name: n for n in ng.nodes if n.type == 'COMBXYZ'}
pos_nodes = ['B_Bot_Pos', 'B_Mid_Pos', 'B_Top_Pos', 'A_Bot_Pos', 'A_Mid_Pos', 'A_Top_Pos']

for name in pos_nodes:
    if name in combine_nodes:
        node = combine_nodes[name]
        print(f"\n{name}:")
        z_inp = node.inputs["Z"]
        if z_inp.links:
            link = z_inp.links[0]
            print(f"  Z <- {link.from_node.name}")
        else:
            print(f"  Z = {z_inp.default_value}")
