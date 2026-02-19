"""Exact replica of the node_group_builder position calculation."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a test cube
bpy.ops.mesh.primitive_cube_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node tree EXACTLY like the builder does
if "ExactTest" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["ExactTest"])

tree = bpy.data.node_groups.new("ExactTest", "GeometryNodeTree")
nk = NodeKit(tree)

# Create interface (like _create_interface)
tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

b_bot_h = tree.interface.new_socket("B_Bot_Height", in_out="INPUT", socket_type="NodeSocketFloat")
b_bot_h.default_value = 2.0
b_bot_h.min_value = 0
b_bot_h.max_value = 10

b_mid_h = tree.interface.new_socket("B_Mid_Height", in_out="INPUT", socket_type="NodeSocketFloat")
b_mid_h.default_value = 6.0
b_mid_h.min_value = 0
b_mid_h.max_value = 30

# Create nodes (like _build_geometry)
gi = nk.group_input(0, 0)
go = nk.group_output(2400, 0)

MM = 0.001
created_nodes = []

# Helper function like _math
def _math(op, a, b, x, y, name):
    ops = {"*": "MULTIPLY", "/": "DIVIDE", "+": "ADD", "-": "SUBTRACT"}
    node = nk.n("ShaderNodeMath", name, x, y)
    node.operation = ops.get(op, op)

    if isinstance(a, bpy.types.NodeSocket):
        nk.link(a, node.inputs[0])
    elif isinstance(a, bpy.types.Node):
        nk.link(a.outputs[0], node.inputs[0])
    else:
        node.inputs[0].default_value = a

    if isinstance(b, bpy.types.NodeSocket):
        nk.link(b, node.inputs[1])
    elif isinstance(b, bpy.types.Node):
        nk.link(b.outputs[0], node.inputs[1])
    else:
        node.inputs[1].default_value = b

    created_nodes.append(node)
    return node.outputs[0]

# Replicate the exact position calculation from node_group_builder
# B_BotH_M = B_Bot_Height * MM
b_bot_h_m = _math("*", gi.outputs["B_Bot_Height"], MM, 350, 300, "B_BotH_M")

# B_MidH_M = B_Mid_Height * MM
b_mid_h_m = _math("*", gi.outputs["B_Mid_Height"], MM, 350, 330, "B_MidH_M")

# B_Bot_Z = B_BotH_M * 0.5
b_bot_z = _math("*", b_bot_h_m, 0.5, 500, 450, "B_Bot_Z")

# B_Mid_Half = B_MidH_M * 0.5
b_mid_half = _math("*", b_mid_h_m, 0.5, 500, 420, "B_Mid_Half")

# B_Mid_Z = B_BotH_M + B_Mid_Half
b_mid_z = _math("+", b_bot_h_m, b_mid_half, 650, 420, "B_Mid_Z")

# Create transform with B_Mid_Z
combine = nk.n("ShaderNodeCombineXYZ", "Pos", 800, 400)
nk.link(b_mid_z, combine.inputs["Z"])

xform = nk.n("GeometryNodeTransform", "Xform", 900, 400)
nk.link(gi.outputs["Geometry"], xform.inputs["Geometry"])
nk.link(combine.outputs["Vector"], xform.inputs["Translation"])

nk.link(xform.outputs["Geometry"], go.inputs["Geometry"])

# Apply modifier
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("="*60)
print("EXACT REPLICA TEST")
print("="*60)

print("\n--- Node State ---")
node_map = {n.name: n for n in tree.nodes}

print("\nB_BotH_M:")
node = node_map["B_BotH_M"]
print(f"  Operation: {node.operation}")
for i, inp in enumerate(node.inputs):
    has_link = "YES" if inp.links else "NO"
    link_src = ""
    if inp.links:
        link = inp.links[0]
        link_src = f" <- {link.from_node.name}"
    print(f"  Input[{i}]: linked={has_link}{link_src} default={inp.default_value}")

print("\nB_MidH_M:")
node = node_map["B_MidH_M"]
print(f"  Operation: {node.operation}")
for i, inp in enumerate(node.inputs):
    has_link = "YES" if inp.links else "NO"
    link_src = ""
    if inp.links:
        link = inp.links[0]
        link_src = f" <- {link.from_node.name}"
    print(f"  Input[{i}]: linked={has_link}{link_src} default={inp.default_value}")

print("\nB_Mid_Half:")
node = node_map["B_Mid_Half"]
print(f"  Operation: {node.operation}")
for i, inp in enumerate(node.inputs):
    has_link = "YES" if inp.links else "NO"
    link_src = ""
    if inp.links:
        link = inp.links[0]
        link_src = f" <- {link.from_node.name}"
    print(f"  Input[{i}]: linked={has_link}{link_src} default={inp.default_value}")

print("\nB_Mid_Z:")
node = node_map["B_Mid_Z"]
print(f"  Operation: {node.operation}")
for i, inp in enumerate(node.inputs):
    has_link = "YES" if inp.links else "NO"
    link_src = ""
    if inp.links:
        link = inp.links[0]
        link_src = f" <- {link.from_node.name}"
    print(f"  Input[{i}]: linked={has_link}{link_src} default={inp.default_value}")

print(f"\nNumber of vertices: {len(mesh.vertices)}")

if len(mesh.vertices) > 0:
    z_vals = [v.co.z * 1000 for v in mesh.vertices]
    center_z = sum(z_vals) / len(z_vals)
    print(f"\nCube Z center: {center_z:.3f}mm")
    print(f"Expected: 5.0mm (B_Bot=2mm + B_Mid_Half=3mm)")
    print(f"Difference: {center_z - 5.0:.3f}mm")

eval_obj.to_mesh_clear()
