"""
Debug script to inspect the Switch node input structure in Blender 5.0
"""

import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit

# Create a test node tree
if "Test_Switch" in bpy.data.node_groups:
    bpy.data.node_groups.remove(bpy.data.node_groups["Test_Switch"])

tree = bpy.data.node_groups.new("Test_Switch", "GeometryNodeTree")
nk = NodeKit(tree)

# Create a Switch node
switch = nk.n("GeometryNodeSwitch", "Test_Switch", 0, 0)
switch.input_type = 'GEOMETRY'

print("=" * 50)
print("Switch Node Input Structure")
print("=" * 50)
print(f"Node type: {switch.bl_idname}")
print(f"Input type: {switch.input_type}")
print(f"\nInputs ({len(switch.inputs)}):")
for i, inp in enumerate(switch.inputs):
    print(f"  [{i}] {inp.name} ({inp.bl_idname})")

print(f"\nOutputs ({len(switch.outputs)}):")
for i, out in enumerate(switch.outputs):
    print(f"  [{i}] {out.name} ({out.bl_idname})")

# Also check the SetMeshNormal node
print("\n" + "=" * 50)
print("SetMeshNormal Node Input Structure")
print("=" * 50)
normals = nk.n("GeometryNodeSetMeshNormal", "Test_Normals", 200, 0)
print(f"Node type: {normals.bl_idname}")
print(f"\nInputs ({len(normals.inputs)}):")
for i, inp in enumerate(normals.inputs):
    print(f"  [{i}] {inp.name} ({inp.bl_idname})")
    if hasattr(inp, 'default_value'):
        print(f"      Default: {inp.default_value}")

print(f"\nOutputs ({len(normals.outputs)}):")
for i, out in enumerate(normals.outputs):
    print(f"  [{i}] {out.name} ({out.bl_idname})")

print("\n" + "=" * 50)
