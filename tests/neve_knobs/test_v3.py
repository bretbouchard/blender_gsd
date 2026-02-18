"""
Test v3 geometry nodes knob with real ridges.
Renders side-by-side: smooth vs ridged.
"""

import bpy
import pathlib
import sys
import math

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from projects.neve_knobs.scripts.neve_knob_v3 import build_artifact

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Create collection
col = bpy.data.collections.new("Knobs")
bpy.context.scene.collection.children.link(col)

# Build TWO knobs side by side
# Left: Smooth (no ridges)
# Right: Ridged (24 ridges)

positions = [(-0.025, 0, 0), (0.025, 0, 0)]
configs = [
    {"ridge_count": 0, "base_color": [0.2, 0.35, 0.75], "pointer_width": 0.08},  # Blue smooth
    {"ridge_count": 24, "ridge_depth": 0.001, "base_color": [0.75, 0.75, 0.78], "metallic": 0.85, "pointer_width": 0.05},  # Silver ridged
]

for pos, cfg in zip(positions, configs):
    task = {
        "parameters": {
            "cap_height": 0.018,
            "cap_diameter": 0.016,
            "skirt_height": 0.008,
            "skirt_diameter": 0.018,
            "skirt_style": 0,
            "pointer_length": 0.012,
            "segments": 64,
            "roughness": 0.35,
            "clearcoat": 0.0,
            "pointer_color": [1.0, 1.0, 1.0],
            **cfg
        }
    }

    result = build_artifact(task, col)
    knob = result["root_objects"][0]
    knob.scale = (20, 20, 20)
    knob.location = pos

# Apply transforms
for obj in col.objects:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(scale=True, location=True)

# Lighting
bpy.ops.object.light_add(type="SUN", location=(3, -3, 8))
bpy.context.active_object.data.energy = 2.5

bpy.ops.object.light_add(type="AREA", location=(-4, -2, 6))
bpy.context.active_object.data.energy = 800
bpy.context.active_object.data.size = 4

bpy.ops.object.light_add(type="AREA", location=(0, 3, 4))
bpy.context.active_object.data.energy = 600
bpy.context.active_object.data.size = 3

# Camera
bpy.ops.object.camera_add(location=(0, -0.9, 0.6))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(60), 0, 0)
cam.data.lens = 45
bpy.context.scene.camera = cam

# Render
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1200
scene.render.resolution_y = 600
scene.render.film_transparent = True
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"

# World
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.08, 0.08, 0.08, 1.0)

# Render
output = pathlib.Path(__file__).parent.parent / "build" / "v3_ridges_preview.png"
scene.render.filepath = str(output)
print(f"[RENDER] Rendering to {output}")
bpy.ops.render.render(write_still=True)
print(f"[RENDER] Done!")
