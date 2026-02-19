"""Trace the exact computed position values by evaluating the node tree."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group

ng = create_input_node_group("Pos_Value_Trace")

print("="*60)
print("NODE TREE POSITION VALUES")
print("="*60)

# Find the CombineXYZ position nodes and trace back their Z inputs
def find_source_value(socket, depth=0):
    """Recursively find the computed value of a socket."""
    indent = "  " * depth
    if not socket.links:
        if hasattr(socket, 'default_value'):
            return f"{indent}default: {socket.default_value}"
        return f"{indent}no connection"

    from_node = socket.links[0].from_node
    from_socket = socket.links[0].from_socket

    if from_node.type == 'MATH':
        op = from_node.operation
        # Get inputs
        in0 = from_node.inputs[0]
        in1 = from_node.inputs[1]

        val0 = find_source_value(in0, depth+1) if in0.links else f"{indent}  val: {in0.default_value}"
        val1 = find_source_value(in1, depth+1) if in1.links else f"{indent}  val: {in1.default_value}"

        return f"{indent}{from_node.name} ({op}):\n{val0}\n{val1}"
    elif from_node.type == 'GROUP_INPUT':
        # Get the default value from interface
        for item in ng.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                if item.name in from_socket.name or from_socket.name in item.name:
                    return f"{indent}Input '{item.name}': {item.default_value}"
        return f"{indent}Group Input: {from_socket.name}"
    else:
        return f"{indent}{from_node.type}: {from_socket.name}"

# Find all position CombineXYZ nodes
for node in ng.nodes:
    if node.type == 'COMBXYZ' and 'Pos' in node.name:
        print(f"\n{node.name}:")
        z_socket = node.inputs["Z"]
        print(find_source_value(z_socket))

# Now let's actually evaluate the node tree with specific input values
print("\n" + "="*60)
print("EVALUATED POSITION VALUES (with test heights)")
print("="*60)

# We can't directly evaluate, but we can create an object and check
from lib.inputs.debug_materials import create_all_debug_materials

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Pos_Eval"

mod = obj.modifiers.new(name="Knob", type='NODES')
mod.node_group = ng

# Build socket map
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

# Apply test settings
test_settings = {
    "Segments": 32,
    "A_Width_Top": 8.4,
    "A_Width_Bot": 11.9,
    "A_Top_Height": 3.0,
    "A_Mid_Height": 6.0,
    "A_Bot_Height": 2.0,
    "B_Width_Top": 11.9,
    "B_Width_Bot": 16.1,
    "B_Top_Height": 2.0,
    "B_Mid_Height": 6.0,
    "B_Bot_Height": 2.0,
    "B_Bot_Style": 0,
}

for key, value in test_settings.items():
    if key in socket_map:
        mod[socket_map[key]] = value

# Evaluate and print actual Z centers
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()

# Find center of each section by material
mat_centers = {}
for poly in mesh.polygons:
    mat_idx = poly.material_index
    if mat_idx not in mat_centers:
        mat_centers[mat_idx] = []
    for vi in poly.vertices:
        mat_centers[mat_idx].append(mesh.vertices[vi].co.z)

# Get material names
mat_names = {}
for i, slot in enumerate(eval_obj.material_slots):
    if slot.material:
        mat_names[i] = slot.material.name

print("\nActual Z centers (mm):")
print("  Expected: B_Bot=1, B_Mid=5, B_Top=9, A_Bot=11, A_Mid=15, A_Top=20")
print("")

for mat_idx in sorted(mat_centers.keys()):
    z_vals = mat_centers[mat_idx]
    avg_z = sum(z_vals) / len(z_vals) * 1000  # Convert to mm
    min_z = min(z_vals) * 1000
    max_z = max(z_vals) * 1000
    name = mat_names.get(mat_idx, f"Mat_{mat_idx}")
    print(f"  {name}: center={avg_z:.1f}mm (range: {min_z:.1f}-{max_z:.1f}mm)")

eval_obj.to_mesh_clear()
