"""
Quick test script for the Geometry Nodes knob.
Run with: blender --background --python test_geo_knob.py
"""

import bpy
import pathlib
import sys

# Add project to path
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

# Import our knob builder
from projects.neve_knobs.scripts.neve_knob_geo import build_artifact

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Create test collection
test_col = bpy.data.collections.new("TestKnobs")
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
        "metallic": 0.0,
        "roughness": 0.3,
        "clearcoat": 0.6,
    },
    "debug": {"enabled": False}
}

# Build the knob
result = build_artifact(task, test_col)

# Save test blend
output = pathlib.Path(__file__).parent.parent / "build" / "test_geo_knob.blend"
output.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(output))

print(f"[TEST] Saved to: {output}")
print(f"[TEST] Objects created: {result['root_objects']}")
