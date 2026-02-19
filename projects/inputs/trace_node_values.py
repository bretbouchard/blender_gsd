"""Trace the exact values flowing through position calculation nodes."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

ng = create_input_node_group("Value_Trace")

print("="*60)
print("POSITION NODE VALUE TRACE")
print("="*60)

# Find all math nodes involved in position calculations
pos_nodes = {}
for node in ng.nodes:
    if node.type == 'MATH' and ('_Z' in node.name or 'Half' in node.name or 'Total' in node.name or 'H_M' in node.name):
        pos_nodes[node.name] = node

print("\n--- Position-related Math Nodes ---")
for name in sorted(pos_nodes.keys()):
    node = pos_nodes[name]
    # Get input values (either connected or default)
    inp0 = node.inputs[0]
    inp1 = node.inputs[1]
    val0 = f"connected to {inp0.links[0].from_node.name}" if inp0.links else str(inp0.default_value)
    val1 = f"connected to {inp1.links[0].from_node.name}" if inp1.links else str(inp1.default_value)
    print(f"{name}: {node.operation}({val0}, {val1})")

# Now let's look at the actual CombineXYZ nodes and what they're receiving
print("\n--- CombineXYZ (Position) Nodes ---")
for node in ng.nodes:
    if node.type == 'COMBXYZ' and 'Pos' in node.name:
        print(f"\n{node.name}:")
        z_input = node.inputs["Z"]
        if z_input.links:
            src_node = z_input.links[0].from_node
            src_socket = z_input.links[0].from_socket
            print(f"  Z input from: {src_node.name}.{src_socket.name}")
            # If it's a math node, show the operation
            if src_node.type == 'MATH':
                print(f"    Operation: {src_node.operation}")
                for i, inp in enumerate(src_node.inputs):
                    if inp.links:
                        print(f"    Input {i}: {inp.links[0].from_node.name}")
                    else:
                        print(f"    Input {i}: default={inp.default_value}")
        else:
            print(f"  Z input: default {z_input.default_value}")

# Check if there are any issues with the height conversion nodes
print("\n--- Height Conversion Nodes (mm -> m) ---")
for node in ng.nodes:
    if node.type == 'MATH' and 'H_M' in node.name:
        print(f"\n{node.name}:")
        print(f"  Operation: {node.operation}")
        for i, inp in enumerate(node.inputs):
            if inp.links:
                print(f"  Input {i}: {inp.links[0].from_node.name}")
            else:
                print(f"  Input {i}: default={inp.default_value}")
