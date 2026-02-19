"""Deep inspection of socket connections."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

ng = create_input_node_group("Socket_Deep")

node_map = {n.name: n for n in ng.nodes}

print("="*60)
print("SOCKET IDENTITY CHECK")
print("="*60)

# Get B_Mid_Half node and its output socket
b_mid_half_node = node_map["B_Mid_Half"]
b_mid_half_output = b_mid_half_node.outputs[0]

print(f"\nB_Mid_Half node: {b_mid_half_node.name}")
print(f"  Output socket: {b_mid_half_output.name}")
print(f"  Output identifier: {b_mid_half_output.identifier}")
print(f"  Output type: {b_mid_half_output.type}")

# Get B_Mid_Z node and check what's connected to Input[1]
b_mid_z_node = node_map["B_Mid_Z"]
b_mid_z_input1 = b_mid_z_node.inputs[1]

print(f"\nB_Mid_Z node: {b_mid_z_node.name}")
print(f"  Input[1] socket: {b_mid_z_input1.name}")
print(f"  Input[1] identifier: {b_mid_z_input1.identifier}")
print(f"  Input[1] type: {b_mid_z_input1.type}")

# Check the link
if b_mid_z_input1.links:
    link = b_mid_z_input1.links[0]
    print(f"\nLink details:")
    print(f"  From node: {link.from_node.name}")
    print(f"  From socket: {link.from_socket.name} (id: {link.from_socket.identifier})")
    print(f"  To node: {link.to_node.name}")
    print(f"  To socket: {link.to_socket.name} (id: {link.to_socket.identifier})")

    # Verify it's the SAME socket object
    print(f"\nSocket identity check:")
    print(f"  from_socket is b_mid_half_output: {link.from_socket is b_mid_half_output}")
    print(f"  from_socket == b_mid_half_output: {link.from_socket == b_mid_half_output}")

# Now check if there's maybe another node with a similar name
print("\n" + "="*60)
print("ALL NODES WITH 'Mid' IN NAME")
print("="*60)

for node in ng.nodes:
    if "Mid" in node.name:
        print(f"\n{node.name}:")
        print(f"  Type: {node.type}")
        if hasattr(node, 'operation'):
            print(f"  Operation: {node.operation}")
        print(f"  Location: ({node.location.x}, {node.location.y})")

        # Show outputs
        for out in node.outputs:
            if out.links:
                for link in out.links:
                    print(f"  Output '{out.name}' -> {link.to_node.name}.{link.to_socket.name}")

        # Show inputs
        for i, inp in enumerate(node.inputs):
            if inp.links:
                link = inp.links[0]
                print(f"  Input[{i}] '{inp.name}' <- {link.from_node.name}.{link.from_socket.name}")
            else:
                val = inp.default_value if hasattr(inp, 'default_value') else 'N/A'
                print(f"  Input[{i}] '{inp.name}' = {val}")
