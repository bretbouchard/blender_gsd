"""
Debug - check what was actually rendered.
"""

import bpy
import pathlib

# Load the blend file to inspect
blend_path = pathlib.Path(__file__).parent.parent / "build" / "test_geo_knob.blend"

# Create a fresh scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Build 5 knobs with wider spacing
import sys
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from projects.neve_knobs.scripts.neve_knob_gn import build_artifact

col = bpy.data.collections.new("TestKnobs")
bpy.context.scene.collection.children.link(col)

# Just build 2 knobs for debugging
positions = [(-0.05, 0, 0), (0.05, 0, 0)]
configs = [
    {"base_color": [0.2, 0.35, 0.75], "ridge_count": 0},
    {"base_color": [0.85, 0.15, 0.1], "skirt_style": 1, "ridge_count": 0},
]

for pos, cfg in zip(positions, configs):
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
    print(f"Created knob at {pos}: {knob.name}")

# List all objects
print("\n=== OBJECTS IN SCENE ===")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        print(f"  {obj.name}: location={obj.location}, scale={obj.scale}")
