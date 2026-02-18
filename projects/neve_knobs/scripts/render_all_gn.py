"""
Render all 5 Neve knob styles using Geometry Nodes.
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

# 5 knob configurations
configs = [
    {
        "name": "Style1_Blue",
        "cap_height": 0.020, "cap_diameter": 0.018,
        "skirt_height": 0.008, "skirt_diameter": 0.020,
        "skirt_style": 0, "ridge_count": 0, "ridge_depth": 0.0,
        "pointer_length": 0.012, "pointer_width": 0.08,
        "base_color": [0.2, 0.35, 0.75], "metallic": 0.0,
        "roughness": 0.3, "clearcoat": 0.6
    },
    {
        "name": "Style2_Silver",
        "cap_height": 0.018, "cap_diameter": 0.016,
        "skirt_height": 0.008, "skirt_diameter": 0.018,
        "skirt_style": 0, "ridge_count": 24, "ridge_depth": 0.0008,
        "pointer_length": 0.012, "pointer_width": 0.05,
        "base_color": [0.75, 0.75, 0.78], "metallic": 0.85,
        "roughness": 0.35, "clearcoat": 0.0
    },
    {
        "name": "Style3_SilverDeep",
        "cap_height": 0.018, "cap_diameter": 0.016,
        "skirt_height": 0.008, "skirt_diameter": 0.018,
        "skirt_style": 0, "ridge_count": 32, "ridge_depth": 0.0012,
        "pointer_length": 0.012, "pointer_width": 0.05,
        "base_color": [0.75, 0.75, 0.78], "metallic": 0.85,
        "roughness": 0.35, "clearcoat": 0.0
    },
    {
        "name": "Style4_SilverSmall",
        "cap_height": 0.015, "cap_diameter": 0.014,
        "skirt_height": 0.006, "skirt_diameter": 0.016,
        "skirt_style": 0, "ridge_count": 18, "ridge_depth": 0.0005,
        "pointer_length": 0.010, "pointer_width": 0.05,
        "base_color": [0.75, 0.75, 0.78], "metallic": 0.85,
        "roughness": 0.4, "clearcoat": 0.0
    },
    {
        "name": "Style5_Red",
        "cap_height": 0.025, "cap_diameter": 0.020,
        "skirt_height": 0.010, "skirt_diameter": 0.022,
        "skirt_style": 1, "ridge_count": 0, "ridge_depth": 0.0,  # SEPARATE style
        "pointer_length": 0.015, "pointer_width": 0.06,
        "base_color": [0.85, 0.15, 0.1], "metallic": 0.0,
        "roughness": 0.25, "clearcoat": 0.8
    },
]

# Positions for 5 knobs in a row - AFTER scaling by 20x
# Each knob is ~2cm diameter scaled to ~40cm
# Spacing of 1.0 meter between centers
positions = [(-2, 0, 0), (-1, 0, 0), (0, 0, 0), (1, 0, 0), (2, 0, 0)]

for cfg, pos in zip(configs, positions):
    task = {
        "parameters": {
            "segments": 64,
            "pointer_color": [1.0, 1.0, 1.0],
            **cfg
        }
    }

    result = build_artifact(task, col)
    knob = result["root_objects"][0]
    knob.scale = (20, 20, 20)
    knob.location = pos  # Position AFTER scale
    knob.name = cfg["name"]

# Update view layer to evaluate geometry nodes
bpy.context.view_layer.update()

# Apply geometry nodes modifiers to create real meshes
for obj in col.objects:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    # Apply the geometry nodes modifier to convert to real mesh
    bpy.ops.object.modifier_apply(modifier="KnobGeometry")

# Apply transforms
for obj in col.objects:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(scale=True, location=True)

# Studio lighting
bpy.ops.object.light_add(type="SUN", location=(3, -3, 8))
key = bpy.context.active_object
key.data.energy = 2.5
key.data.color = (1.0, 0.98, 0.95)

bpy.ops.object.light_add(type="AREA", location=(-4, -2, 6))
fill = bpy.context.active_object
fill.data.energy = 800
fill.data.size = 4
fill.data.color = (0.95, 0.97, 1.0)

bpy.ops.object.light_add(type="AREA", location=(0, 3, 4))
rim = bpy.context.active_object
rim.data.energy = 600
rim.data.size = 3

# Camera - positioned higher and farther for wider view (5 knobs spread 4m wide)
bpy.ops.object.camera_add(location=(0, -4, 2.5))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(55), 0, 0)
cam.data.lens = 35
bpy.context.scene.camera = cam

# Render settings
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 2000
scene.render.resolution_y = 500
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"

# World
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.08, 0.08, 0.08, 1.0)

# Ground plane - lower to match scaled knobs
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.3))
ground = bpy.context.active_object
ground_mat = bpy.data.materials.new("GroundMat")
ground_mat.use_nodes = True
nt = ground_mat.node_tree
nt.nodes.clear()
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
bsdf.inputs["Roughness"].default_value = 0.9
output = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
ground.data.materials.append(ground_mat)

# Render
output = pathlib.Path(__file__).parent.parent / "build" / "neve_knobs_gn_all.png"
scene.render.filepath = str(output)
print(f"[RENDER] Rendering 5 knobs to {output}")
bpy.ops.render.render(write_still=True)
print(f"[RENDER] Done!")
