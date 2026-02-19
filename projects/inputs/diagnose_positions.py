"""Diagnostic to trace position calculation values."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

# Create the node group
ng = create_input_node_group("Diag_Positions")

# Find the Group Input node
gi = None
for node in ng.nodes:
    if node.type == 'GROUP_INPUT':
        gi = node
        break

# Print the default values for height inputs
print("\n=== DEFAULT HEIGHT VALUES (from interface) ===")
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and 'Height' in item.name:
        print(f"{item.name}: {item.default_value}")

# Find all CombineXYZ nodes that create positions
print("\n=== COMBINEXYZ POSITION NODES ===")
for node in ng.nodes:
    if node.type == 'COMBXYZ' and 'Pos' in node.name:
        # Check what's connected to the Z input
        z_input = node.inputs["Z"]
        if z_input.links:
            link = z_input.links[0]
            from_node = link.from_node
            print(f"\n{node.name}:")
            print(f"  Z from: {from_node.name} (type={from_node.type})")
            if from_node.type == 'MATH':
                # Check what's connected to the math node
                for i, inp in enumerate(from_node.inputs):
                    if inp.links:
                        src = inp.links[0].from_node
                        print(f"    Math input {i}: {src.name}")
                    else:
                        print(f"    Math input {i}: default={inp.default_value}")
        else:
            print(f"\n{node.name}: Z = default {z_input.default_value}")

# Find Transform nodes and their translation inputs
print("\n=== TRANSFORM NODE TRANSLATIONS ===")
for node in ng.nodes:
    if 'Xform' in node.name:
        trans_input = node.inputs["Translation"]
        if trans_input.links:
            link = trans_input.links[0]
            print(f"{node.name}: Translation from {link.from_node.name}")
        else:
            print(f"{node.name}: Translation = default {trans_input.default_value}")
