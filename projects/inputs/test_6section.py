"""Test render with exaggerated 6-section heights for visibility."""
import bpy
import math
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
ng = create_input_node_group("Test_6Section")

# Create a mesh object
bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Test_Knob"

# Add geometry nodes modifier
mod = obj.modifiers.new(name="Knob", type='NODES')
mod.node_group = ng

# Build socket map
socket_map = {}
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        socket_map[item.name] = item.identifier

# Set exaggerated heights (all 5mm each for visibility)
# Use DIFFERENT widths to make each section visually distinct
settings = {
    "Height_mm": 35.0,  # Total height (not used in new design)
    "Width_mm": 14.0,
    "Segments": 32,

    # Zone A (top) - TAPERED (smaller at top)
    "A_Height": 15.0,
    "A_Width_Top": 10.0,  # Smaller at top (5mm radius)
    "A_Width_Bot": 14.0,  # Larger at bottom (7mm radius)
    "A_Top_Height": 5.0,
    "A_Top_Style": 0,  # Flat (cylinder)
    "A_Mid_Height": 5.0,
    "A_Bot_Height": 5.0,
    "A_Knurl": False,

    # Zone B (bottom) - TAPERED (larger at bottom)
    "B_Height": 15.0,
    "B_Width_Top": 14.0,  # Same as A bottom (7mm)
    "B_Width_Bot": 18.0,  # Larger at bottom (9mm radius)
    "B_Top_Height": 5.0,
    "B_Mid_Height": 5.0,
    "B_Knurl": False,
    "B_Bot_Height": 5.0,
    "B_Bot_Style": 0,  # Flat

    "Color": (0.5, 0.5, 0.5),
    "Metallic": 0.0,
    "Roughness": 0.3,
}

# Apply settings
for key, value in settings.items():
    if key in socket_map:
        identifier = socket_map[key]
        try:
            mod[identifier] = value
        except Exception as e:
            print(f"Warning: Could not set {key}={value}: {e}")

# Enable debug mode
debug_mats = create_all_debug_materials(preset="rainbow")

if "Debug_Mode" in socket_map:
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
        print(f"Assigned {section_name} material")

# Camera
bpy.ops.object.camera_add(location=(0, -0.2, 0.1))
cam = bpy.context.active_object
bpy.context.scene.camera = cam
direction = -cam.location.normalized()
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()

# Lighting
bpy.ops.object.light_add(type='SUN', location=(1, -1, 2))
light = bpy.context.active_object
light.data.energy = 3.0

# Render settings
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.film_transparent = True

# Render
output_path = str(ROOT / "projects" / "output" / "knob_renders" / "test_6section.png")
scene.render.filepath = output_path
bpy.ops.render.render(write_still=True)

print(f"\nRendered to: {output_path}")
print("\nExpected colors from bottom to top:")
print("  B_Bot = Purple")
print("  B_Mid = Blue")
print("  B_Top = Green")
print("  A_Bot = Yellow")
print("  A_Mid = Orange")
print("  A_Top = Red")
