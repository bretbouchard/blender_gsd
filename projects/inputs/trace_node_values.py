"""Dump the computed Z positions from the node group."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create node group
ng = create_input_node_group("Trace_Z_Values")

print("=" * 60)
print("TRACING Z POSITION CALCULATIONS")
print("=" * 60)

# Find all Math nodes related to position calculations
print("\nMath nodes in the node group:")
for node in ng.nodes:
    if node.type == 'MATH':
        # Check if it's in the POSITION CALC frame or has relevant name
        name = node.name.lower()
        if any(x in name for x in ['bot', 'mid', 'top', 'z', 'half', 'total']):
            print(f"\n  {node.name}:")
            print(f"    Operation: {node.operation}")
            for i, inp in enumerate(node.inputs):
                if inp.is_linked:
                    from_node = inp.links[0].from_node.name
                    from_socket = inp.links[0].from_socket.name
                    print(f"    Input[{i}]: LINKED from {from_node}.{from_socket}")
                else:
                    print(f"    Input[{i}]: {inp.default_value}")
            print(f"    Output[0] default: {node.outputs[0].default_value}")

# Also check CombineXYZ nodes for Z values
print("\n\nCombineXYZ nodes (for Z translations):")
for node in ng.nodes:
    if node.type == 'COMBXYZ':
        if 'Pos' in node.name or 'pos' in node.name:
            print(f"\n  {node.name}:")
            z_inp = node.inputs["Z"]
            if z_inp.is_linked:
                from_node = z_inp.links[0].from_node.name
                from_socket = z_inp.links[0].from_socket.name
                print(f"    Z input: LINKED from {from_node}.{from_socket}")
            else:
                print(f"    Z input: {z_inp.default_value}")

# Check Transform nodes to see what translation they're receiving
print("\n\nTransform nodes:")
for node in ng.nodes:
    if node.type == 'TRANSFORM':
        print(f"\n  {node.name}:")
        trans_inp = node.inputs["Translation"]
        if trans_inp.is_linked:
            from_node = trans_inp.links[0].from_node.name
            from_socket = trans_inp.links[0].from_socket.name
            print(f"    Translation: LINKED from {from_node}.{from_socket}")
        else:
            print(f"    Translation: {trans_inp.default_value}")

print("\n" + "=" * 60)
