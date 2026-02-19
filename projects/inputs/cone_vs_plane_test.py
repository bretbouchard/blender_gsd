"""Minimal test comparing cone vs plane with same transform."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test plane
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node tree
if "MinimalTest" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["MinimalTest"])

tree = bpy.data.node_groups.new("MinimalTest", "GeometryNodeTree")
nk = NodeKit(tree)

# Create interface
tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
b_bot_h = tree.interface.new_socket("B_Bot_Height", in_out="INPUT", socket_type="NodeSocketFloat")
b_bot_h.default_value = 2.0
b_mid_h = tree.interface.new_socket("B_Mid_Height", in_out="INPUT", socket_type="NodeSocketFloat")
b_mid_h.default_value = 6.0

gi = nk.group_input(0, 0)
go = nk.group_output(2400, 0)

MM = 0.001
created_nodes = []

def _math(op, a, b, x, y, name):
    node = nk.n("ShaderNodeMath", name, x, y)
    ops = {"*": "MULTIPLY", "/": "DIVIDE", "+": "ADD", "-": "SUBTRACT"}
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

# Position calculations
b_bot_h_m = _math("*", gi.outputs["B_Bot_Height"], MM, 350, 300, "B_BotH_M")
b_mid_h_m = _math("*", gi.outputs["B_Mid_Height"], MM, 350, 330, "B_MidH_M")

b_mid_half = _math("*", b_mid_h_m, 0.5, 500, 420, "B_Mid_Half")
b_mid_z = _math("+", b_bot_h_m, b_mid_half, 650, 420, "B_Mid_Z")

# Create a cone
cone = nk.n("GeometryNodeMeshCone", "B_Mid_Cone", 300, -460)
cone.inputs["Vertices"].default_value = 32
cone.inputs["Radius Top"].default_value = 0.005
cone.inputs["Radius Bottom"].default_value = 0.008
nk.link(b_mid_h_m, cone.inputs["Depth"])

# Create position combine
combine = nk.n("ShaderNodeCombineXYZ", "B_Mid_Pos", 800, 400)
nk.link(b_mid_z, combine.inputs["Z"])

# Transform
xform = nk.n("GeometryNodeTransform", "B_Mid_Xform", 900, 400)
nk.link(cone.outputs["Mesh"], xform.inputs["Geometry"])
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
print("CONE ONLY TEST")
print("="*60)

# Check node state
node_map = {n.name: n for n in tree.nodes}

print("\n--- B_Mid_Half ---")
n = node_map["B_Mid_Half"]
print(f"Operation: {n.operation}")
for i, inp in enumerate(n.inputs):
    if inp.links:
        print(f"  Input[{i}] <- {inp.links[0].from_node.name}")
    else:
        print(f"  Input[{i}] = {inp.default_value}")

print("\n--- B_Mid_Z ---")
n = node_map["B_Mid_Z"]
print(f"Operation: {n.operation}")
for i, inp in enumerate(n.inputs):
    if inp.links:
        print(f"  Input[{i}] <- {inp.links[0].from_node.name}")
    else:
        print(f"  Input[{i}] = {inp.default_value}")

# Check what values B_BotH_M and B_MidH_M produce
print("\n--- Source values ---")
print(f"B_Bot_Height interface default: {b_bot_h.default_value}")
print(f"B_Mid_Height interface default: {b_mid_h.default_value}")
print(f"B_BotH_M should be: {b_bot_h.default_value * MM}m = {b_bot_h.default_value}mm")
print(f"B_MidH_M should be: {b_mid_h.default_value * MM}m = {b_mid_h.default_value}mm")
print(f"B_Mid_Half should be: {b_mid_h.default_value * MM * 0.5}m = {b_mid_h.default_value * 0.5}mm")
print(f"B_Mid_Z should be: {(b_bot_h.default_value + b_mid_h.default_value * 0.5) * MM}m = {b_bot_h.default_value + b_mid_h.default_value * 0.5}mm")

if len(mesh.vertices) > 0:
    z_vals = [v.co.z * 1000 for v in mesh.vertices]
    min_z = min(z_vals)
    max_z = max(z_vals)
    center = (min_z + max_z) / 2
    print(f"\nCone Z bounds: {min_z:.1f}mm to {max_z:.1f}mm")
    print(f"Cone Z center: {center:.1f}mm")
    print(f"Expected center: 5.0mm")
    print(f"Actual center: {center:.1f}mm")
    print(f"Difference: {center - 5.0:.1f}mm")

    # The depth should be 6mm
    print(f"Cone depth: {max_z - min_z:.1f}mm (expected 6mm)")

    # If center is 8mm with depth 6mm, then the translation is 8mm
    # If center is 5mm with depth 6mm, then the translation is 5mm
    print(f"\nThis means the Z translation being applied is: {center:.1f}mm")
    print(f"Which equals: B_Bot_Height ({b_bot_h.default_value}mm) + B_Mid_Height ({b_mid_h.default_value}mm) = {b_bot_h.default_value + b_mid_h.default_value}mm")
    print(f"NOT: B_Bot_Height ({b_bot_h.default_value}mm) + B_Mid_Height/2 ({b_mid_h.default_value/2}mm) = {b_bot_h.default_value + b_mid_h.default_value/2}mm")
else:
    print("\nNo vertices!")

eval_obj.to_mesh_clear()
