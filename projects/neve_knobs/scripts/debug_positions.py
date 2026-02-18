"""
Debug script to check knob positions after building.
"""
import bpy
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from projects.neve_knobs.scripts.neve_knob_gn import build_artifact

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Create collection
col = bpy.data.collections.new("Knobs")
bpy.context.scene.collection.children.link(col)

# Build just 2 knobs for debugging
configs = [
    {"name": "Blue", "base_color": [0.2, 0.35, 0.75], "ridge_count": 0},
    {"name": "Red", "base_color": [0.85, 0.15, 0.1], "skirt_style": 1, "ridge_count": 0},
]

positions = [(-1, 0, 0), (1, 0, 0)]

for cfg, pos in zip(configs, positions):
    task = {
        "parameters": {
            "cap_height": 0.020,
            "cap_diameter": 0.018,
            "skirt_height": 0.008,
            "skirt_diameter": 0.020,
            "pointer_length": 0.012,
            "pointer_width": 0.08,
            "segments": 64,
            **cfg
        }
    }

    result = build_artifact(task, col)
    knob = result["root_objects"][0]
    knob.scale = (20, 20, 20)
    knob.location = pos
    print(f"Created {cfg['name']}:")
    print(f"  location = {knob.location}")
    print(f"  scale = {knob.scale}")
    print(f"  dimensions = {knob.dimensions}")

# List all objects and their bounds
print("\n=== ALL OBJECTS ===")
for obj in bpy.data.objects:
    if obj.type in ['MESH', 'EMPTY']:
        print(f"{obj.name}:")
        print(f"  location = {obj.location}")
        print(f"  scale = {obj.scale}")
        print(f"  bounds = {obj.bound_box[0]} to {obj.bound_box[6]}")
