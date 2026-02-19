"""
Render all 5 Neve knobs in a combined view.
Uses existing render files to create a composite.
"""
import bpy
import pathlib
import sys
import math

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from projects.neve_knobs.scripts.neve_knob_gn import build_artifact

BUILD_DIR = pathlib.Path(__file__).parent.parent / "build" / "renders"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.node_groups:
        if block.users == 0:
            bpy.data.node_groups.remove(block)


# Knob configurations
KNOB_CONFIGS = [
    {"name": "style1_blue", "params": {
        "cap_height": 0.020, "cap_diameter": 0.018, "skirt_height": 0.008, "skirt_diameter": 0.020,
        "skirt_style": 0, "ridge_count": 0, "ridge_depth": 0.0, "pointer_length": 0.012,
        "pointer_width": 0.08, "segments": 64, "base_color": [0.2, 0.35, 0.75],
        "pointer_color": [1.0, 1.0, 1.0], "metallic": 0.0, "roughness": 0.3, "clearcoat": 0.6,
    }},
    {"name": "style2_silver", "params": {
        "cap_height": 0.020, "cap_diameter": 0.018, "skirt_height": 0.008, "skirt_diameter": 0.020,
        "skirt_style": 0, "ridge_count": 64, "ridge_depth": 0.0015, "knurl_profile": 0.5,
        "pointer_length": 0.012, "pointer_width": 0.08, "segments": 64,
        "base_color": [0.75, 0.75, 0.78], "pointer_color": [1.0, 0.95, 0.9],
        "metallic": 0.85, "roughness": 0.25,
    }},
    {"name": "style3_silver_deep", "params": {
        "cap_height": 0.022, "cap_diameter": 0.018, "skirt_height": 0.010, "skirt_diameter": 0.022,
        "skirt_style": 0, "ridge_count": 32, "ridge_depth": 0.0012, "pointer_length": 0.014,
        "pointer_width": 0.06, "segments": 64, "base_color": [0.7, 0.7, 0.73],
        "pointer_color": [0.9, 0.9, 0.95], "metallic": 0.9, "roughness": 0.2,
    }},
    {"name": "style4_silver_shallow", "params": {
        "cap_height": 0.018, "cap_diameter": 0.020, "skirt_height": 0.006, "skirt_diameter": 0.024,
        "skirt_style": 0, "ridge_count": 18, "ridge_depth": 0.0005, "knurl_z_start": 0.2,
        "knurl_z_end": 0.8, "knurl_fade": 0.1, "pointer_length": 0.012, "pointer_width": 0.1,
        "segments": 64, "base_color": [0.8, 0.8, 0.82], "pointer_color": [1.0, 1.0, 1.0],
        "metallic": 0.8, "roughness": 0.35,
    }},
    {"name": "style5_red", "params": {
        "cap_height": 0.020, "cap_diameter": 0.018, "skirt_height": 0.008, "skirt_diameter": 0.020,
        "skirt_style": 1, "ridge_count": 0, "ridge_depth": 0.0, "pointer_length": 0.012,
        "pointer_width": 0.08, "segments": 64, "base_color": [0.85, 0.15, 0.1],
        "pointer_color": [1.0, 1.0, 1.0], "metallic": 0.0, "roughness": 0.25, "clearcoat": 0.8,
    }},
]


clear_scene()

col = bpy.data.collections.new("AllKnobs")
bpy.context.scene.collection.children.link(col)

# Build all knobs
spacing = 0.7
start_x = -spacing * 2

for i, config in enumerate(KNOB_CONFIGS):
    task = {"parameters": config["params"]}
    result = build_artifact(task, col)
    knob = result["root_objects"][0]
    knob.scale = (25, 25, 25)
    knob.location = (start_x + i * spacing, 0, 0)
    knob.name = config["name"]

    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = knob
    knob.select_set(True)
    bpy.ops.object.modifier_apply(modifier="KnobGeometry")
    print(f"Added: {config['name']}")

# World
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.08, 0.08, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 0.5

# Ground
bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, -0.01))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("Ground")
gmat.use_nodes = True
gbsdf = gmat.node_tree.nodes["Principled BSDF"]
gbsdf.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1.0)
gbsdf.inputs["Roughness"].default_value = 0.95
ground.data.materials.append(gmat)

# Camera - positioned to see all 5 knobs from a good angle
# Knobs are scaled 25x (~50cm tall), spaced 0.7m apart, total width ~3.5m
bpy.ops.object.camera_add(location=(0, -3.5, 1.8))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(50), 0, 0)  # Higher angle to see knob tops
cam.data.lens = 35  # Wider lens to fit all knobs
bpy.context.scene.camera = cam

# Lighting
bpy.ops.object.light_add(type="AREA", location=(3, -3, 5))
bpy.context.active_object.data.energy = 1500
bpy.context.active_object.data.size = 4

bpy.ops.object.light_add(type="AREA", location=(-3, -2, 4))
bpy.context.active_object.data.energy = 600
bpy.context.active_object.data.size = 3

# Render
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 64  # Faster for combined
scene.cycles.use_denoising = True
scene.render.resolution_x = 2400
scene.render.resolution_y = 600

output = BUILD_DIR / "all_knobs_combined.png"
scene.render.filepath = str(output)
print(f"\n[RENDER] Rendering combined view to {output}")
bpy.ops.render.render(write_still=True)
print(f"[OK] Saved: {output}")
