"""
Render 5 knobs with a simple setup to verify geometry nodes.
"""
import bpy
import pathlib
import sys
import math

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from projects.neve_knobs.scripts.neve_knob_gn import build_artifact

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Create collection
col = bpy.data.collections.new("Knobs")
bpy.context.scene.collection.children.link(col)

# Build 5 knobs with colors that are easy to distinguish
knob_configs = [
    ("Blue", [0.1, 0.3, 0.9], 0),
    ("Green", [0.1, 0.8, 0.2], 0),
    ("Yellow", [0.9, 0.8, 0.1], 0),
    ("Orange", [0.9, 0.4, 0.1], 0),
    ("Red", [0.9, 0.1, 0.1], 1),  # Separate skirt style
]

positions = [(-2, 0, 0), (-1, 0, 0), (0, 0, 0), (1, 0, 0), (2, 0, 0)]

for i, ((name, color, skirt_style), pos) in enumerate(zip(knob_configs, positions)):
    task = {
        "parameters": {
            "cap_height": 0.020,
            "cap_diameter": 0.018,
            "skirt_height": 0.008,
            "skirt_diameter": 0.020,
            "skirt_style": skirt_style,
            "ridge_count": 0,
            "pointer_length": 0.012,
            "pointer_width": 0.08,
            "segments": 64,
            "base_color": color,
            "pointer_color": [1.0, 1.0, 1.0],
            "roughness": 0.3,
        }
    }

    result = build_artifact(task, col)
    knob = result["root_objects"][0]
    knob.scale = (20, 20, 20)
    knob.location = pos
    knob.name = name
    print(f"Built {name} at {pos}")

# Apply transforms
for obj in col.objects:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(scale=True, location=True)
    print(f"Applied transform to {obj.name}")

# Save the blend file for manual inspection
blend_path = pathlib.Path(__file__).parent.parent / "build" / "debug_knobs.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
print(f"Saved blend file to {blend_path}")

# Simple orthographic camera from above
cam_data = bpy.data.cameras.new("TopCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 8  # Wide view for 5 knobs spread 4 meters
cam_obj = bpy.data.objects.new("TopCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (0, -5, 3)
cam_obj.rotation_euler = (math.radians(60), 0, 0)
bpy.context.scene.camera = cam_obj

# Simple sun light
bpy.ops.object.light_add(type="SUN", location=(5, 5, 10))
sun = bpy.context.active_object
sun.data.energy = 3

# Simple gray world
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.2, 0.2, 0.2, 1.0)

# Render settings - EEVEE for speed
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 400
scene.render.film_transparent = False

# Render
output = pathlib.Path(__file__).parent.parent / "build" / "test_v4_simple.png"
scene.render.filepath = str(output)
print(f"[RENDER] Rendering to {output}")
bpy.ops.render.render(write_still=True)
print(f"[RENDER] Done!")
