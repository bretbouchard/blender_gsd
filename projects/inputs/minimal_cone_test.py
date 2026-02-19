"""Minimal test matching exact builder behavior."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create test plane (like builder does)
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object

# Create node tree
if "MinimalTest" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["MinimalTest"])

tree = bpy.data.node_groups.new("MinimalTest", "GeometryNodeTree")
nk = NodeKit(tree)

# Create interface exactly like builder
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
    """Exactly like builder's _math."""
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

# Replicate builder's position calculations EXACTLY
b_bot_h_m = _math("*", gi.outputs["B_Bot_Height"], MM, 350, 300, "B_BotH_M")
b_mid_h_m = _math("*", gi.outputs["B_Mid_Height"], MM, 350, 330, "B_MidH_M")

b_bot_z = _math("*", b_bot_h_m, 0.5, 500, 450, "B_Bot_Z")

b_mid_half = _math("*", b_mid_h_m, 0.5, 500, 420, "B_Mid_Half")
b_mid_z = _math("+", b_bot_h_m, b_mid_half, 650, 420, "B_Mid_Z")

# Create a cone like builder does
cone = nk.n("GeometryNodeMeshCone", "B_Mid_Cone", 300, -460)
cone.inputs["Vertices"].default_value = 32  # Fixed vertex count
cone.inputs["Radius Top"].default_value = 0.005
cone.inputs["Radius Bottom"].default_value = 0.008
nk.link(b_mid_h_m, cone.inputs["Depth"])

# ALSO create a cube for comparison
cube = nk.n("GeometryNodeMeshCube", "Test_Cube", 300, -560)
cube.inputs["Size"].default_value = 0.006  # 6mm cube

# Create position combines
combine_cone = nk.n("ShaderNodeCombineXYZ", "Cone_Pos", 800, 400)
nk.link(b_mid_z, combine_cone.inputs["Z"])

combine_cube = nk.n("ShaderNodeCombineXYZ", "Cube_Pos", 800, 500)
nk.link(b_mid_z, combine_cube.inputs["Z"])

# Transforms
xform_cone = nk.n("GeometryNodeTransform", "Cone_Xform", 900, 400)
nk.link(cone.outputs["Mesh"], xform_cone.inputs["Geometry"])
nk.link(combine_cone.outputs["Vector"], xform_cone.inputs["Translation"])

xform_cube = nk.n("GeometryNodeTransform", "Cube_Xform", 900, 500)
nk.link(cube.outputs["Mesh"], xform_cube.inputs["Geometry"])
nk.link(combine_cube.outputs["Vector"], xform_cube.inputs["Translation"])

# Join
join = nk.n("GeometryNodeJoinGeometry", "Join", 1000, 450)
nk.link(xform_cone.outputs["Geometry"], join.inputs["Geometry"])
nk.link(xform_cube.outputs["Geometry"], join.inputs["Geometry"])
nk.link(join.outputs["Geometry"], go.inputs["Geometry"])

# Apply modifier
mod = obj.modifiers.new(name="Test", type='NODES')
mod.node_group = tree

# Evaluate
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

print("="*60)
print("MINIMAL CONE TEST")
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

if len(mesh.vertices) > 0:
    # Cube has 8 vertices, cone has more
    # First 8 should be cone (created first in join)
    # Next 8 should be cube

    # Actually, we need to distinguish by position
    # Cube: X and Y are very small (0.001)
    # Cone: X and Y span larger range

    cone_verts = []
    cube_verts = []

    for v in mesh.vertices:
        # Cube has size 0.006 (6mm), cone has wider radius
        if abs(v.co.x) <= 0.004 and abs(v.co.y) <= 0.004:
            cube_verts.append(v.co.z * 1000)
        else:
            cone_verts.append(v.co.z * 1000)

    print(f"\nCone vertices: {len(cone_verts)}")
    if cone_verts:
        print(f"  Z range: {min(cone_verts):.1f}mm to {max(cone_verts):.1f}mm")
        print(f"  Z center: {(min(cone_verts) + max(cone_verts))/2:.1f}mm")

    print(f"\nCube vertices: {len(cube_verts)}")
    if cube_verts:
        print(f"  Z range: {min(cube_verts):.1f}mm to {max(cube_verts):.1f}mm")
        print(f"  Z center: {(min(cube_verts) + max(cube_verts))/2:.1f}mm")

    print(f"\nExpected center: 5.0mm (B_Bot=2 + B_Mid_Half=3)")
else:
    print("\nNo vertices!")

eval_obj.to_mesh_clear()
