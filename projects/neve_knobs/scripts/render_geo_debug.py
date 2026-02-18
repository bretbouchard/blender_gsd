"""
Debug script - inspect what was built in the geometry nodes tree.
"""

import bpy
import pathlib
import sys

# Load the test blend
blend_path = pathlib.Path(__file__).parent.parent / "build" / "test_geo_knob.blend"
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

# Find the knob object
knob = bpy.data.objects.get("NeveKnob")
if not knob:
    print("ERROR: Knob not found")
    sys.exit(1)

print(f"\n=== KNOB OBJECT ===")
print(f"Name: {knob.name}")
print(f"Modifiers: {len(knob.modifiers)}")

for mod in knob.modifiers:
    print(f"\n  Modifier: {mod.name} ({mod.type})")
    if mod.type == 'NODES':
        tree = mod.node_group
        print(f"    Node Group: {tree.name}")
        print(f"    Nodes: {len(tree.nodes)}")
        print(f"    Inputs:")
        for item in tree.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                print(f"      - {item.name}: {item.default_value}")

        print(f"\n    Modifier Values:")
        for key in dir(mod):
            if not key.startswith('_') and key[0].isupper():
                try:
                    val = mod[key]
                    print(f"      {key}: {val}")
                except:
                    pass

# Check materials
print(f"\n=== MATERIALS ===")
for i, mat in enumerate(knob.data.materials):
    print(f"\nMaterial {i}: {mat.name}")
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                color = node.inputs['Base Color'].default_value
                print(f"  Base Color: ({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f}, {color[3]:.2f})")
                metallic = node.inputs['Metallic'].default_value
                roughness = node.inputs['Roughness'].default_value
                print(f"  Metallic: {metallic}")
                print(f"  Roughness: {roughness}")
