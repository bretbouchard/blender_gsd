"""Trace the actual node group to understand material assignment."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

# Create node group
ng = create_input_node_group("Trace_Test")

print("=" * 60)
print("NODE GROUP STRUCTURE TRACE")
print("=" * 60)

# Find all Set Material nodes
set_mat_nodes = [n for n in ng.nodes if n.type == 'SET_MATERIAL']
print(f"\nSet Material nodes: {len(set_mat_nodes)}")
for node in set_mat_nodes:
    print(f"\n  {node.name}:")
    # Check geometry input
    geo_inp = node.inputs["Geometry"]
    if geo_inp.links:
        src = geo_inp.links[0].from_node
        print(f"    Geometry input <- {src.name} ({src.type})")
    else:
        print(f"    Geometry input: NOT CONNECTED")

    # Check material input
    mat_inp = node.inputs["Material"]
    if mat_inp.links:
        src = mat_inp.links[0].from_node
        print(f"    Material input <- {src.name} ({src.type})")
    else:
        print(f"    Material input: NOT CONNECTED (default={mat_inp.default_value})")

# Find all Switch nodes (material type)
switch_nodes = [n for n in ng.nodes if n.type == 'SWITCH']
print(f"\n\nSwitch nodes: {len(switch_nodes)}")
for node in switch_nodes:
    print(f"\n  {node.name}:")
    print(f"    Input type: {node.input_type}")
    for inp in node.inputs:
        if inp.links:
            src = inp.links[0].from_node
            if hasattr(inp.links[0].from_socket, 'name'):
                src_socket = inp.links[0].from_socket.name
            else:
                src_socket = "?"
            print(f"    Input '{inp.name}' <- {src.name}.{src_socket}")
        else:
            if hasattr(inp, 'default_value'):
                print(f"    Input '{inp.name}': default = {inp.default_value}")
            else:
                print(f"    Input '{inp.name}': no connection")

# Find JoinGeometry node
join_nodes = [n for n in ng.nodes if n.type == 'JOIN_GEOMETRY']
print(f"\n\nJoin Geometry nodes: {len(join_nodes)}")
for node in join_nodes:
    print(f"\n  {node.name}:")
    for i, inp in enumerate(node.inputs):
        if inp.links:
            src = inp.links[0].from_node
            print(f"    Input {i} <- {src.name}")
        else:
            print(f"    Input {i}: NOT CONNECTED")

# Check for transform nodes and their positions
xform_nodes = [n for n in ng.nodes if n.type == 'TRANSFORM']
print(f"\n\nTransform nodes: {len(xform_nodes)}")
for node in xform_nodes:
    print(f"\n  {node.name}:")
    trans_inp = node.inputs["Translation"]
    if trans_inp.links:
        src = trans_inp.links[0].from_node
        print(f"    Translation <- {src.name}")
    else:
        print(f"    Translation: NOT CONNECTED")

# Check the actual math nodes for Z position calculations
math_nodes = [n for n in ng.nodes if n.type == 'MATH']
print(f"\n\nMath nodes: {len(math_nodes)}")
z_related = [n for n in math_nodes if any(x in n.name for x in ['Bot', 'Mid', 'Top', 'Z', 'Half', 'Total', 'A_'])]
print(f"Position-related math nodes: {len(z_related)}")
for node in z_related:
    print(f"  {node.name}: op={node.operation}")
