"""Trace exactly what B_Mid_Half and B_Mid_Z nodes contain."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Import the builder
from lib.inputs.node_group_builder import InputNodeGroupBuilder

# Create the builder and manually trace the node creation
builder = InputNodeGroupBuilder()
ng = builder.build("Manual_Trace")

print("="*60)
print("MANUAL BUILDER TRACE")
print("="*60)

node_map = {n.name: n for n in ng.nodes}

# Check B_Mid_Half node
print("\n--- B_Mid_Half Node ---")
if "B_Mid_Half" in node_map:
    node = node_map["B_Mid_Half"]
    print(f"Name: {node.name}")
    print(f"Operation: {node.operation}")
    print(f"Type: {node.type}")
    print(f"Inputs ({len(node.inputs)}):")
    for i, inp in enumerate(node.inputs):
        has_link = "YES" if inp.links else "NO"
        link_src = ""
        if inp.links:
            link = inp.links[0]
            link_src = f" <- {link.from_node.name}.{link.from_socket.name}"
        print(f"  [{i}] {inp.name}: linked={has_link}{link_src} default={inp.default_value}")

    print(f"Output:")
    out = node.outputs[0]
    print(f"  {out.name}: links={len(out.links)}")
    for link in out.links:
        print(f"    -> {link.to_node.name}.{link.to_socket.name}")

# Check B_Mid_Z node
print("\n--- B_Mid_Z Node ---")
if "B_Mid_Z" in node_map:
    node = node_map["B_Mid_Z"]
    print(f"Name: {node.name}")
    print(f"Operation: {node.operation}")
    print(f"Inputs ({len(node.inputs)}):")
    for i, inp in enumerate(node.inputs):
        has_link = "YES" if inp.links else "NO"
        link_src = ""
        if inp.links:
            link = inp.links[0]
            link_src = f" <- {link.from_node.name}.{link.from_socket.name}"
        print(f"  [{i}] {inp.name}: linked={has_link}{link_src} default={inp.default_value}")

# Now let's manually trace what the calculation should produce
print("\n" + "="*60)
print("CALCULATION TRACE")
print("="*60)

# From interface defaults:
b_bot_height_mm = 2.0
b_mid_height_mm = 6.0

MM = 0.001

# B_BotH_M = B_Bot_Height * MM
b_bot_h_m = b_bot_height_mm * MM  # 0.002

# B_MidH_M = B_Mid_Height * MM
b_mid_h_m = b_mid_height_mm * MM  # 0.006

# B_Mid_Half = B_MidH_M * 0.5
b_mid_half = b_mid_h_m * 0.5  # 0.003

# B_Mid_Z = B_BotH_M + B_Mid_Half
b_mid_z = b_bot_h_m + b_mid_half  # 0.002 + 0.003 = 0.005

print(f"B_Bot_Height = {b_bot_height_mm}mm")
print(f"B_Mid_Height = {b_mid_height_mm}mm")
print(f"B_BotH_M = {b_bot_height_mm} * {MM} = {b_bot_h_m}m")
print(f"B_MidH_M = {b_mid_height_mm} * {MM} = {b_mid_h_m}m")
print(f"B_Mid_Half = {b_mid_h_m} * 0.5 = {b_mid_half}m = {b_mid_half*1000}mm")
print(f"B_Mid_Z = {b_bot_h_m} + {b_mid_half} = {b_mid_z}m = {b_mid_z*1000}mm")

print(f"\nExpected B_Mid_Z center: {b_mid_z*1000}mm")
print(f"Actual B_Mid center: 8.0mm (from previous tests)")
print(f"Difference: {8.0 - b_mid_z*1000}mm = exactly B_Mid_Height/2 = {b_mid_height_mm/2}mm")

print("""
CONCLUSION:
The B_Mid_Z calculation is producing 8mm instead of 5mm.
The difference is exactly 3mm = B_Mid_Height * 0.5 = 6mm * 0.5

This suggests that B_Mid_Z is actually computing:
  B_BotH_M + B_MidH_M = 0.002 + 0.006 = 0.008m = 8mm

Instead of:
  B_BotH_M + B_Mid_Half = 0.002 + 0.003 = 0.005m = 5mm

This means B_Mid_Z's input[1] is receiving B_MidH_M instead of B_Mid_Half!
""")
