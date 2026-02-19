"""Trace the actual node connections in the node group."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

# Create the node group
ng = create_input_node_group("Connection_Trace")

print("="*60)
print("NODE CONNECTION ANALYSIS")
print("="*60)

# Find all Math nodes and their connections
math_nodes = [n for n in ng.nodes if n.type == 'MATH']

# Group by name for easier lookup
node_map = {n.name: n for n in ng.nodes}

# Find specific position calculation nodes
position_nodes = [
    "B_Bot_Z", "B_Mid_Half", "B_Mid_Z",
    "B_Bot+Mid", "B_Top_Half", "B_Top_Z",
    "B_Total", "A_Bot_Half", "A_Bot_Z",
    "B+A_Bot", "A_Mid_Half", "A_Mid_Z",
    "B+A_Mid", "A_Top_Half", "A_Top_Z"
]

print("\n--- Position Calculation Nodes ---")
for node_name in position_nodes:
    if node_name in node_map:
        node = node_map[node_name]
        print(f"\n{node_name} ({node.operation}):")

        # Input 0
        in0 = node.inputs[0]
        if in0.links:
            from_node = in0.links[0].from_node
            from_socket = in0.links[0].from_socket.name
            print(f"  Input[0] <- {from_node.name}.{from_socket}")
        else:
            print(f"  Input[0] = {in0.default_value}")

        # Input 1
        in1 = node.inputs[1]
        if in1.links:
            from_node = in1.links[0].from_node
            from_socket = in1.links[0].from_socket.name
            print(f"  Input[1] <- {from_node.name}.{from_socket}")
        else:
            print(f"  Input[1] = {in1.default_value}")
    else:
        print(f"\n{node_name}: NOT FOUND")

# Now let's look at what B_Mid_Z is actually connected to
print("\n" + "="*60)
print("DETAILED B_Mid_Z TRACE")
print("="*60)

if "B_Mid_Z" in node_map:
    b_mid_z_node = node_map["B_Mid_Z"]
    print(f"\nB_Mid_Z node: {b_mid_z_node.name}")
    print(f"  Operation: {b_mid_z_node.operation}")

    for i, inp in enumerate(b_mid_z_node.inputs):
        print(f"\n  Input {i}:")
        if inp.links:
            link = inp.links[0]
            from_node = link.from_node
            from_socket = link.from_socket
            print(f"    Connected to: {from_node.name}.{from_socket.name}")
            print(f"    Node type: {from_node.type}")
            print(f"    Node operation: {from_node.operation if hasattr(from_node, 'operation') else 'N/A'}")

            # If it's a math node, show its inputs
            if from_node.type == 'MATH':
                print(f"    This node's inputs:")
                for j, sub_inp in enumerate(from_node.inputs):
                    if sub_inp.links:
                        sub_link = sub_inp.links[0]
                        print(f"      [{j}] <- {sub_link.from_node.name}")
                    else:
                        print(f"      [{j}] = {sub_inp.default_value}")
        else:
            print(f"    Default value: {inp.default_value}")

# Also check what B_Mid_Half is
print("\n" + "="*60)
print("B_Mid_Half NODE CHECK")
print("="*60)

if "B_Mid_Half" in node_map:
    b_mid_half_node = node_map["B_Mid_Half"]
    print(f"\nB_Mid_Half node: {b_mid_half_node.name}")
    print(f"  Operation: {b_mid_half_node.operation}")

    for i, inp in enumerate(b_mid_half_node.inputs):
        if inp.links:
            link = inp.links[0]
            print(f"  Input {i} <- {link.from_node.name}.{link.from_socket.name}")
        else:
            print(f"  Input {i} = {inp.default_value}")

# Check if B_Mid_Half output is connected to anything
print("\n--- B_Mid_Half output connections ---")
if "B_Mid_Half" in node_map:
    b_mid_half_node = node_map["B_Mid_Half"]
    out_socket = b_mid_half_node.outputs[0]
    print(f"Output socket: {out_socket.name}")
    print(f"Connected to:")
    for link in out_socket.links:
        print(f"  -> {link.to_node.name}.{link.to_socket.name}")
