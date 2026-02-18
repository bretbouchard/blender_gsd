"""
Test v2 geometry nodes knob.
"""

import bpy
import pathlib
import sys
import math

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from projects.neve_knobs.scripts.neve_knob_v2 import build_artifact

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Create collection
col = bpy.data.collections.new("Knobs")
bpy.context.scene.collection.children.link(col)

# Build knob
task = {
    "parameters": {
        "cap_height": 0.020,
        "cap_diameter": 0.018,
        "skirt_height": 0.008,
        "skirt_diameter": 0.020,
        "ridge_count": 24,
        "ridge_depth": 0.001,
        "pointer_length": 0.012,
        "pointer_width": 0.08,
        "segments": 64,
        "base_color": [0.2, 0.35, 0.75],
        "pointer_color": [1.0, 1.0, 1.0],
        "metallic": 0.0,
        "roughness": 0.3,
        "clearcoat": 0.6,
    }
}

result = build_artifact(task, col)
knob = result["root_objects"][0]

# Scale for visibility
knob.scale = (20, 20, 20)
bpy.context.view_layer.objects.active = knob
bpy.ops.object.transform_apply(scale=True)

# Lighting
bpy.ops.object.light_add(type="SUN", location=(3, -3, 8))
bpy.context.active_object.data.energy = 2.5

bpy.ops.object.light_add(type="AREA", location=(-4, -2, 6))
bpy.context.active_object.data.energy = 800
bpy.context.active_object.data.size = 4

# Camera
bpy.ops.object.camera_add(location=(0, -0.8, 0.5))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(65), 0, 0)
cam.data.lens = 50
bpy.context.scene.camera = cam

# Render
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.film_transparent = True
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"

# World
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.1, 0.1, 0.1, 1.0)

# Render
output = pathlib.Path(__file__).parent.parent / "build" / "v2_preview.png"
scene.render.filepath = str(output)
print(f"[RENDER] Rendering to {output}")
bpy.ops.render.render(write_still=True)
print(f"[RENDER] Done!")
