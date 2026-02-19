"""Deep diagnostic to trace geometry generation and material assignment."""
import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group
from lib.inputs.debug_materials import create_all_debug_materials

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create the node group
ng = create_input_node_group("Trace_Test")

# Print all geometry-generating nodes and their connections
print("\n" + "="*60)
print("GEOMETRY GENERATION CHAIN")
print("="*60)

# Find all mesh primitive nodes
print("\n--- MESH PRIMITIVE NODES (geometry sources) ---")
primitives = []
for node in ng.nodes:
    if 'Cone' in node.bl_idname or 'Cylinder' in node.bl_idname or 'Sphere' in node.bl_idname or 'Capsule' in node.bl_idname:
        primitives.append(node)
        print(f"{node.name}:")
        # Print inputs
        for inp in node.inputs:
            if inp.links:
                src = inp.links[0].from_node
                print(f"  {inp.name} <- {src.name}")
            else:
                if hasattr(inp, 'default_value'):
                    print(f"  {inp.name} = {inp.default_value}")

# Find all Transform nodes and trace back to their geometry sources
print("\n--- TRANSFORM NODES (positioning) ---")
transforms = []
for node in ng.nodes:
    if 'Xform' in node.name:
        transforms.append(node)
        print(f"\n{node.name}:")
        # Geometry input
        if node.inputs["Geometry"].links:
            geo_src = node.inputs["Geometry"].links[0].from_node
            print(f"  Geometry <- {geo_src.name}")
        # Translation input
        if node.inputs["Translation"].links:
            trans_src = node.inputs["Translation"].links[0].from_node
            print(f"  Translation <- {trans_src.name}")

# Find all SetMaterial nodes
print("\n--- SET MATERIAL NODES ---")
set_mats = []
for node in ng.nodes:
    if node.type == 'SET_MATERIAL':
        set_mats.append(node)
        print(f"\n{node.name}:")
        # Geometry input
        if node.inputs["Geometry"].links:
            geo_src = node.inputs["Geometry"].links[0].from_node
            print(f"  Geometry <- {geo_src.name}")
        # Material input
        if node.inputs["Material"].links:
            mat_src = node.inputs["Material"].links[0].from_node
            print(f"  Material <- {mat_src.name}")

# Find the Join node and trace all inputs
print("\n--- JOIN NODE INPUTS ---")
for node in ng.nodes:
    if node.type == 'JOIN_GEOMETRY':
        print(f"\n{node.name}:")
        for i, inp in enumerate(node.inputs):
            if inp.links:
                for link in inp.links:
                    print(f"  Input {i}: {link.from_node.name}")

# Create a test object and apply settings
print("\n" + "="*60)
print("TESTING WITH ACTUAL VALUES")
print("="*60)

bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Trace_Knob"

mod = obj.modifiers.new(name="Knob", type='NODES')
mod.node_group = ng

# Build socket map
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

# Apply test settings (matching render_knob.py debug mode)
settings = {
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
}

for key, value in settings.items():
    if key in socket_map:
        mod[socket_map[key]] = value
        print(f"Set {key} = {value}")

# Enable debug mode
debug_mats = create_all_debug_materials(preset="rainbow")
mod[socket_map["Debug_Mode"]] = True

section_map = {
    "Debug_A_Top_Material": "A_Top",
    "Debug_A_Mid_Material": "A_Mid",
    "Debug_A_Bot_Material": "A_Bot",
    "Debug_B_Top_Material": "B_Top",
    "Debug_B_Mid_Material": "B_Mid",
    "Debug_B_Bot_Material": "B_Bot",
}

for socket_name, section_name in section_map.items():
    if socket_name in socket_map and section_name in debug_mats:
        mod[socket_map[socket_name]] = debug_mats[section_name]
        print(f"Assigned {section_name} material to {socket_name}")

# Force evaluation and check geometry
print("\n" + "="*60)
print("EVALUATED GEOMETRY")
print("="*60)

# Get the evaluated object
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)

# Get the mesh
mesh = eval_obj.to_mesh()

# Count vertices by Z position (grouped into bands)
print(f"\nTotal vertices: {len(mesh.vertices)}")

# Group vertices by Z position
z_buckets = {}
for v in mesh.vertices:
    z_rounded = round(v.co.z * 1000, 0)  # Convert to mm and round
    bucket = int(z_rounded // 5) * 5  # 5mm buckets
    if bucket not in z_buckets:
        z_buckets[bucket] = 0
    z_buckets[bucket] += 1

print("\nVertices by Z position (5mm buckets):")
for bucket in sorted(z_buckets.keys()):
    print(f"  Z={bucket}-{bucket+5}mm: {z_buckets[bucket]} vertices")

# Check material slots
print(f"\nMaterial slots on evaluated mesh: {len(eval_obj.material_slots)}")
for i, slot in enumerate(eval_obj.material_slots):
    print(f"  Slot {i}: {slot.material.name if slot.material else 'None'}")

eval_obj.to_mesh_clear()
