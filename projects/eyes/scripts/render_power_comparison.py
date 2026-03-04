"""
Render power comparison: 0.8, 0.9, 0.95
"""

import bpy
import sys

def update_power(value):
    """Update the power node value in PerSphereRadial material."""
    mat = bpy.data.materials.get("PerSphereRadial")
    if mat and mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == 'MATH' and node.operation == 'POWER':
                node.inputs[1].default_value = value
                print(f"Set power to {value}")
                return True
    print("ERROR: Power node not found!")
    return False

def render_scene(output_path):
    """Render and save."""
    bpy.ops.render.render(write_still=True)
    bpy.data.images['Render Result'].save_render(filepath=output_path)
    print(f"Saved: {output_path}")

# Get the blend file path from command line args
blend_path = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/void_orb.blend"
output_dir = "/Users/bretbouchard/apps/blender_gsd/projects/eyes/"

# Power values to test
power_values = [0.8, 0.9, 0.95]

for power_val in power_values:
    print(f"\n{'='*50}")
    print(f"Rendering Power {power_val}")
    print('='*50)

    if update_power(power_val):
        output_path = f"{output_dir}void_orb_power{int(power_val*100):03d}.png"
        render_scene(output_path)

print("\nDone!")
