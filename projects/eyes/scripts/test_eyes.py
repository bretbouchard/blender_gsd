"""
Test script for eye generation - runs in Blender
"""
import bpy
import sys

# Add path
sys.path.insert(0, '/Users/bretbouchard/apps/blender_gsd/projects/eyes/scripts')

print("Testing Eye Geometry Generation...")

# Import and test
from eye_geometry import create_eye_node_group

# Create the node group
node_group = create_eye_node_group()
print(f"Created node group: {node_group.name}")

# List all node groups
print(f"Total node groups: {len(bpy.data.node_groups)}")
for ng in bpy.data.node_groups:
    print(f"  - {ng.name}")

# Create a test object
from eye_geometry import create_single_eye
from mathutils import Vector

eye = create_single_eye(
    size=2.0,
    pupil_ratio=0.3,
    iris_ratio=0.6,
    subdivisions=2,
    location=Vector((0, 0, 0)),
    name="TestEye"
)

print(f"Created test eye object: {eye.name}")
print(f"Object location: {eye.location}")
print(f"Modifiers: {[m.name for m in eye.modifiers]}")

# Save test file
bpy.ops.wm.save_as_mainfile(filepath="/Users/bretbouchard/apps/blender_gsd/projects/eyes/test_eye.blend")
print("Saved test file to test_eye.blend")
