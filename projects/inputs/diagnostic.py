"""Diagnostic script to check node group structure."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

# Create the node group
ng = create_input_node_group("Test_Diagnostic")

# Print input interface
print("\n=== INTERFACE INPUTS ===")
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        print(f"{item.name:30} | {item.socket_type}")

# Check Transform nodes and their input connections
print("\n=== TRANSFORM NODES AND THEIR GEOMETRY SOURCES ===")
for node in ng.nodes:
    if 'Xform' in node.name or 'Transform' in node.name:
        print(f"\n{node.name} (type={node.type}):")
        # Check all inputs
        for inp in node.inputs:
            if inp.links:
                link = inp.links[0]
                print(f"  {inp.name} from: {link.from_node.name}.{link.from_socket.name}")
            else:
                if hasattr(inp, 'default_value'):
                    print(f"  {inp.name}: default = {inp.default_value}")
                else:
                    print(f"  {inp.name}: NOT CONNECTED")

# Check CombineXYZ nodes for positions
print("\n=== COMBINEXYZ POSITION NODES ===")
for node in ng.nodes:
    if node.type == 'COMBXYZ' and 'Pos' in node.name:
        print(f"\n{node.name}:")
        # Check Z input
        if node.inputs["Z"].links:
            link = node.inputs["Z"].links[0]
            print(f"  Z from: {link.from_node.name}.{link.from_socket.name}")
        else:
            print(f"  Z: default = {node.inputs['Z'].default_value}")

# Check SetMaterial nodes
print("\n=== SET MATERIAL NODES ===")
for node in ng.nodes:
    if node.type == 'SET_MATERIAL':
        print(f"\n{node.name}:")
        # Check Geometry input
        if node.inputs["Geometry"].links:
            link = node.inputs["Geometry"].links[0]
            print(f"  Geometry from: {link.from_node.name}.{link.from_socket.name}")
        else:
            print(f"  Geometry: NOT CONNECTED!")

        # Check Material input
        if node.inputs["Material"].links:
            link = node.inputs["Material"].links[0]
            print(f"  Material from: {link.from_node.name}.{link.from_socket.name}")
        else:
            mat = node.inputs["Material"].default_value
            print(f"  Material: default = {mat.name if mat else 'None'}")
