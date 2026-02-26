"""
Render Water Sphere Preview

Renders a preview image of the water sphere test scene.
"""

import bpy
import sys
from pathlib import Path

def render_preview():
    """Render a preview image of the water sphere."""
    # Set render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 50  # Render at 50% for speed

    # Cycles settings for fast preview
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True

    # Set output path
    script_dir = Path(__file__).parent
    output_path = script_dir.parent / "water_sphere_preview.png"
    scene.render.filepath = str(output_path)

    # Render
    print(f"Rendering preview to: {output_path}")
    bpy.ops.render.render(write_still=True)
    print("Render complete!")

if __name__ == "__main__":
    # The blend file should already be loaded
    render_preview()
