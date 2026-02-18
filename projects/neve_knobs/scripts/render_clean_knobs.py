"""
Render 5 Neve knobs using basic cylinder primitives - no GN complexity.
"""
import bpy
import pathlib
import sys
import math

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from projects.neve_knobs.scripts.neve_knob_gn import build_artifact

# Clear scene completely
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Also clear orphaned data
for block in bpy.data.meshes:
    if block.users == 0:
        bpy.data.meshes.remove(block)
for block in bpy.data.materials:
    if block.users == 0:
        bpy.data.materials.remove(block)

# Create fresh collection
col = bpy.data.collections.new("Knobs")
bpy.context.scene.collection.children.link(col)

# 5 knob configurations
configs = [
    {"name": "Blue", "base_color": [0.2, 0.35, 0.75], "ridge_count": 0, "metallic": 0.0},
    {"name": "Silver1", "base_color": [0.75, 0.75, 0.78], "ridge_count": 24, "metallic": 0.85},
    {"name": "Silver2", "base_color": [0.75, 0.75, 0.78], "ridge_count": 32, "metallic": 0.85},
    {"name": "Silver3", "base_color": [0.75, 0.75, 0.78], "ridge_count": 18, "metallic": 0.85},
    {"name": "Red", "base_color": [0.85, 0.15, 0.1], "ridge_count": 0, "skirt_style": 1, "metallic": 0.0},
]

# Wider spacing - 1.5m between centers
positions = [(-3, 0, 0), (-1.5, 0, 0), (0, 0, 0), (1.5, 0, 0), (3, 0, 0)]

for cfg, pos in zip(configs, positions):
    task = {
        "parameters": {
            "cap_height": 0.020,
            "cap_diameter": 0.018,
            "skirt_height": 0.008,
            "skirt_diameter": 0.020,
            "skirt_style": cfg.get("skirt_style", 0),
            "ridge_count": cfg["ridge_count"],
            "ridge_depth": 0.0008,
            "pointer_length": 0.012,
            "pointer_width": 0.08,
            "segments": 64,
            "base_color": cfg["base_color"],
            "pointer_color": [1.0, 1.0, 1.0],
            "metallic": cfg["metallic"],
            "roughness": 0.3,
        }
    }

    result = build_artifact(task, col)
    knob = result["root_objects"][0]
    knob.scale = (20, 20, 20)
    knob.location = pos
    knob.name = cfg["name"]
    print(f"Built {cfg['name']} at {pos}")

# Apply geometry nodes
bpy.context.view_layer.update()
for obj in col.objects:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier="KnobGeometry")
    print(f"Applied GN to {obj.name}")

# Verify mesh
print("\n=== Mesh verification ===")
for obj in col.objects:
    print(f"{obj.name}: {len(obj.data.vertices)} verts, dims={obj.dimensions}")

# Camera - wider view
bpy.ops.object.camera_add(location=(0, -6, 3))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(55), 0, 0)
cam.data.lens = 35
bpy.context.scene.camera = cam

# Lighting
bpy.ops.object.light_add(type="SUN", location=(5, -5, 10))
bpy.context.active_object.data.energy = 3

bpy.ops.object.light_add(type="AREA", location=(-3, -3, 5))
bpy.context.active_object.data.energy = 500
bpy.context.active_object.data.size = 3

# World
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.12, 0.12, 0.12, 1.0)

# Ground
bpy.ops.mesh.primitive_plane_add(size=15, location=(0, 0, -0.25))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("Ground")
gmat.use_nodes = True
gbsdf = gmat.node_tree.nodes["Principled BSDF"]
gbsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
gbsdf.inputs["Roughness"].default_value = 0.9
ground.data.materials.append(gmat)

# Render
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 64
scene.render.resolution_x = 2000
scene.render.resolution_y = 500

output = pathlib.Path(__file__).parent.parent / "build" / "neve_knobs_clean.png"
scene.render.filepath = str(output)
print(f"\n[RENDER] Rendering to {output}")
bpy.ops.render.render(write_still=True)
print("[RENDER] Done!")
