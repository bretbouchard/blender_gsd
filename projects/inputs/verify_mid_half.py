"""Verify what B_Mid_Half is actually computing."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

ng = create_input_node_group("Verify_Half")

# Create node map
node_map = {n.name: n for n in ng.nodes}

print("="*60)
print("B_Mid_Half VERIFICATION")
print("="*60)

# Check B_Mid_Half
if "B_Mid_Half" in node_map:
    node = node_map["B_Mid_Half"]
    print(f"\nNode: {node.name}")
    print(f"Location: ({node.location.x}, {node.location.y})")
    print(f"Operation: {node.operation}")

    # Check inputs
    for i, inp in enumerate(node.inputs):
        if inp.links:
            link = inp.links[0]
            from_node = link.from_node
            print(f"Input[{i}]: connected to {from_node.name}")

            # If connected to B_MidH_M, trace that
            if from_node.name == "B_MidH_M":
                print(f"  B_MidH_M inputs:")
                for j, sub_inp in enumerate(from_node.inputs):
                    if sub_inp.links:
                        sub_link = sub_inp.links[0]
                        print(f"    [{j}] <- {sub_link.from_node.name}")
                    else:
                        print(f"    [{j}] = {sub_inp.default_value}")
        else:
            print(f"Input[{i}]: default = {inp.default_value}")

# Now let's look at what the interface says about B_Mid_Height
print("\n" + "="*60)
print("INTERFACE DEFAULTS")
print("="*60)

for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        if "Mid_Height" in item.name or "Bot_Height" in item.name:
            print(f"  {item.name}: {item.default_value}")

# Manual calculation
print("\n" + "="*60)
print("MANUAL CALCULATION")
print("="*60)

# Get defaults
defaults = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        defaults[item.name] = item.default_value

MM = 0.001
b_bot_height = defaults.get("B_Bot_Height", 2.0)
b_mid_height = defaults.get("B_Mid_Height", 6.0)

b_bot_h_m = b_bot_height * MM  # 0.002
b_mid_h_m = b_mid_height * MM  # 0.006
b_mid_half = b_mid_h_m * 0.5  # 0.003
b_mid_z = b_bot_h_m + b_mid_half  # 0.005

print(f"B_Bot_Height = {b_bot_height}mm -> {b_bot_h_m}m")
print(f"B_Mid_Height = {b_mid_height}mm -> {b_mid_h_m}m")
print(f"B_Mid_Half = B_MidH_M * 0.5 = {b_mid_h_m} * 0.5 = {b_mid_half}m = {b_mid_half*1000}mm")
print(f"B_Mid_Z = B_BotH_M + B_Mid_Half = {b_bot_h_m} + {b_mid_half} = {b_mid_z}m = {b_mid_z*1000}mm")
print(f"\nExpected: {b_mid_z*1000}mm")
print(f"Actual: 8.0mm")
print(f"Bug: We're getting 8mm which equals {b_bot_height} + {b_mid_height} = {b_bot_height + b_mid_height}mm")
print(f"This suggests B_Mid_Z is using B_Mid_Height instead of B_Mid_Half!")

# Check if B_Mid_Half is actually being linked correctly
print("\n" + "="*60)
print("CHECKING B_Mid_Z INPUTS")
print("="*60)

if "B_Mid_Z" in node_map:
    node = node_map["B_Mid_Z"]
    print(f"\nNode: {node.name}")
    print(f"Operation: {node.operation}")

    for i, inp in enumerate(node.inputs):
        if inp.links:
            link = inp.links[0]
            from_node = link.from_node
            from_socket = link.from_socket
            print(f"Input[{i}]: {from_node.name}.{from_socket.name}")

            # If this is B_Mid_Half, verify it's the MULTIPLY node
            if "Half" in from_node.name:
                print(f"  -> CORRECT: connected to Half multiply node")
                print(f"  -> This node computes: B_MidH_M * 0.5")
            elif "B_MidH" in from_node.name and "Half" not in from_node.name:
                print(f"  -> BUG: connected directly to B_MidH_M (full height)!")
        else:
            print(f"Input[{i}]: default = {inp.default_value}")
