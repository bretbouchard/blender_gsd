"""Trace the actual input values being used."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

ng = create_input_node_group("Input_Trace")

print("="*60)
print("INPUT VALUE ANALYSIS")
print("="*60)

# Check interface defaults
print("\nInterface defaults:")
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        if hasattr(item, 'default_value'):
            print(f"  {item.name}: {item.default_value}")

# Now look at what the math nodes are actually receiving
node_map = {n.name: n for n in ng.nodes}

# Check B_BotH_M (unit conversion node)
print("\n--- B_BotH_M (mm to m conversion) ---")
if "B_BotH_M" in node_map:
    node = node_map["B_BotH_M"]
    print(f"Operation: {node.operation}")
    for i, inp in enumerate(node.inputs):
        if inp.links:
            link = inp.links[0]
            print(f"  Input {i}: connected to {link.from_node.name}.{link.from_socket.name}")
            # Check if it's from Group Input
            if link.from_node.type == 'GROUP_INPUT':
                # Find the interface item
                for item in ng.interface.items_tree:
                    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                        # Try to match by socket name/identifier
                        if link.from_socket.name == item.name or link.from_socket.identifier == item.identifier:
                            print(f"    -> Interface default: {item.default_value}")
        else:
            print(f"  Input {i}: default = {inp.default_value}")

# Check B_MidH_M (unit conversion node)
print("\n--- B_MidH_M (mm to m conversion) ---")
if "B_MidH_M" in node_map:
    node = node_map["B_MidH_M"]
    print(f"Operation: {node.operation}")
    for i, inp in enumerate(node.inputs):
        if inp.links:
            link = inp.links[0]
            print(f"  Input {i}: connected to {link.from_node.name}.{link.from_socket.name}")
        else:
            print(f"  Input {i}: default = {inp.default_value}")

# Let's manually calculate what the values should be
print("\n" + "="*60)
print("MANUAL CALCULATION CHECK")
print("="*60)

# Get the default values from interface
b_bot_height_mm = 2.0  # default
b_mid_height_mm = 6.0  # default

MM = 0.001

b_bot_h_m = b_bot_height_mm * MM  # 0.002
b_mid_h_m = b_mid_height_mm * MM  # 0.006

b_bot_z = b_bot_h_m * 0.5  # 0.001 (1mm)
b_mid_half = b_mid_h_m * 0.5  # 0.003 (3mm)
b_mid_z = b_bot_h_m + b_mid_half  # 0.002 + 0.003 = 0.005 (5mm)

print(f"\nB_Bot_Height: {b_bot_height_mm}mm = {b_bot_h_m}m")
print(f"B_Mid_Height: {b_mid_height_mm}mm = {b_mid_h_m}m")
print(f"B_Bot_Z = B_Bot_H * 0.5 = {b_bot_h_m} * 0.5 = {b_bot_z}m = {b_bot_z*1000}mm")
print(f"B_Mid_Half = B_Mid_H * 0.5 = {b_mid_h_m} * 0.5 = {b_mid_half}m = {b_mid_half*1000}mm")
print(f"B_Mid_Z = B_Bot_H + B_Mid_Half = {b_bot_h_m} + {b_mid_half} = {b_mid_z}m = {b_mid_z*1000}mm")
