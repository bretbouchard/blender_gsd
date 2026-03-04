"""Quick render script for single power value."""
import bpy
import sys

# Parse power value from command line
power_val = float(sys.argv[-1]) if len(sys.argv) > 1 else 0.8

# Update power
mat = bpy.data.materials.get("PerSphereRadial")
if mat and mat.use_nodes:
    for node in mat.node_tree.nodes:
        if node.type == 'MATH' and node.operation == 'POWER':
            node.inputs[1].default_value = power_val

# Render
bpy.ops.render.render(write_still=True)
output_path = f"/Users/bretbouchard/apps/blender_gsd/projects/eyes/void_orb_power{int(power_val*100):03d}.png"
bpy.data.images['Render Result'].save_render(filepath=output_path)
print(f"Saved: {output_path}")
