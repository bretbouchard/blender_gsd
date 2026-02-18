"""
Render preview for Geometry Nodes knob.
Shows the knob with proper lighting and camera setup.
"""

import bpy
import pathlib
import math
import sys

# Add project to path
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from projects.neve_knobs.scripts.neve_knob_geo import build_artifact

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Create test collection
test_col = bpy.data.collections.new("Knobs")
bpy.context.scene.collection.children.link(test_col)

# Test task - integrated style with ridges
task = {
    "parameters": {
        "cap_height": 0.020,
        "cap_diameter": 0.018,
        "skirt_height": 0.008,
        "skirt_diameter": 0.020,
        "skirt_style": 0,  # 0=integrated flat bottom
        "cap_shape": 0,    # 0=flat top
        "ridge_count": 24,
        "ridge_depth": 0.001,
        "pointer_width": 0.08,
        "pointer_length": 0.012,
        "segments": 64,
        "base_color": [0.2, 0.35, 0.75],
        "pointer_color": [1.0, 1.0, 1.0],
        "metallic": 0.0,
        "roughness": 0.3,
        "clearcoat": 0.6,
    },
    "debug": {"enabled": False}
}

# Build the knob
result = build_artifact(task, test_col)
knob = result["root_objects"][0]

# Scale up for visibility (20x)
knob.scale = (20, 20, 20)
bpy.context.view_layer.objects.active = knob
bpy.ops.object.transform_apply(scale=True)

# === STUDIO LIGHTING ===
# Key light
bpy.ops.object.light_add(type="SUN", location=(3, -3, 8))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 2.5
key.data.color = (1.0, 0.98, 0.95)

# Fill light
bpy.ops.object.light_add(type="AREA", location=(-4, -2, 6))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 800
fill.data.size = 4
fill.data.color = (0.95, 0.97, 1.0)

# Rim light
bpy.ops.object.light_add(type="AREA", location=(0, 3, 4))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 600
rim.data.size = 3
rim.data.color = (1.0, 1.0, 1.0)

# === CAMERA ===
bpy.ops.object.camera_add(location=(0, -0.8, 0.5))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(65), 0, 0)
cam.data.lens = 50
cam.data.sensor_fit = "HORIZONTAL"
bpy.context.scene.camera = cam

# === RENDER SETTINGS ===
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "16"

# Color management
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"

# World/background
world = bpy.data.worlds.get("World")
if not world:
    world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.08, 0.08, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# === RENDER ===
BUILD_DIR = pathlib.Path(__file__).parent.parent / "build"
BUILD_DIR.mkdir(parents=True, exist_ok=True)
output = BUILD_DIR / "geo_knob_preview.png"

scene.render.filepath = str(output)
print(f"[RENDER] Rendering to {output}...")
bpy.ops.render.render(write_still=True)

print(f"[RENDER] Done!")
print(f"[RENDER] Output: {output}")
