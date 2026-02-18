"""
Render test with explicit depsgraph update.
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

# Build 5 knobs
knob_configs = [
    ("Blue", [0.1, 0.3, 0.9]),
    ("Green", [0.1, 0.8, 0.2]),
    ("Yellow", [0.9, 0.8, 0.1]),
    ("Orange", [0.9, 0.4, 0.1]),
    ("Red", [0.9, 0.1, 0.1]),
]

positions = [(-2, 0, 0), (-1, 0, 0), (0, 0, 0), (1, 0, 0), (2, 0, 0)]

for i, ((name, color), pos) in enumerate(zip(knob_configs, positions)):
    task = {
        "parameters": {
            "cap_height": 0.020,
            "cap_diameter": 0.018,
            "skirt_height": 0.008,
            "skirt_diameter": 0.020,
            "skirt_style": 0,
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

# CRITICAL: Update the view layer to evaluate geometry nodes
bpy.context.view_layer.update()

# Check evaluated objects
print("\n=== EVALUATED GEOMETRY ===")
depsgraph = bpy.context.evaluated_depsgraph_get()
for obj in col.objects:
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    print(f"{obj.name}: {len(mesh.vertices)} vertices, bounds: {mesh.vertices[0].co if mesh.vertices else 'empty'}...")
    eval_obj.to_mesh_clear()

# Apply geometry nodes to mesh (convert to real mesh)
for obj in col.objects:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    # Apply the geometry nodes modifier
    bpy.ops.object.modifier_apply(modifier="KnobGeometry")
    print(f"Applied geometry nodes to {obj.name}")

# Check real mesh dimensions now
print("\n=== REAL MESH DIMENSIONS ===")
for obj in col.objects:
    if obj.type == 'MESH':
        print(f"{obj.name}: dimensions = {obj.dimensions}")

# Camera
cam_data = bpy.data.cameras.new("TopCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 8
cam_obj = bpy.data.objects.new("TopCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (0, -5, 3)
cam_obj.rotation_euler = (math.radians(60), 0, 0)
bpy.context.scene.camera = cam_obj

# Light
bpy.ops.object.light_add(type="SUN", location=(5, 5, 10))
bpy.context.active_object.data.energy = 3

# World
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.2, 0.2, 0.2, 1.0)

# Render
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 400

output = pathlib.Path(__file__).parent.parent / "build" / "test_v5_real_mesh.png"
scene.render.filepath = str(output)
print(f"\n[RENDER] Rendering to {output}")
bpy.ops.render.render(write_still=True)
print("[RENDER] Done!")
