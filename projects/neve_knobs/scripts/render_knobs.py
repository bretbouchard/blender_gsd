"""
Render Knobs - Create preview renders for all Neve knob styles.

This script:
1. Loads all 5 knob GLB files
2. Arranges them in a row
3. Sets up studio lighting
4. Renders a composite image
"""

import bpy
import sys
import pathlib
from math import radians

# Paths
ROOT = pathlib.Path(__file__).resolve().parents[3]
PROJECT_ROOT = ROOT / "projects" / "neve_knobs"
BUILD_DIR = PROJECT_ROOT / "build"


def reset_scene():
    """Clean the scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Purge orphan data
    for datablock in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.lights,
        bpy.data.cameras,
    ):
        for item in list(datablock):
            if item.users == 0:
                datablock.remove(item)


def setup_render_settings():
    """Configure render settings for product visualization."""
    scene = bpy.context.scene

    # Use Cycles for quality
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True

    # Resolution
    scene.render.resolution_x = 2048
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100

    # Transparent background
    scene.render.film_transparent = True

    # Color management
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"


def create_camera():
    """Create camera positioned for product shot."""
    bpy.ops.object.camera_add(
        location=(0, -0.25, 0.12),
        rotation=(radians(75), 0, 0)
    )
    cam = bpy.context.active_object
    cam.name = "ProductCamera"

    # Set focal length for nice perspective
    cam.data.lens = 85
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 0.25
    cam.data.dof.aperture_fstop = 2.8

    bpy.context.scene.camera = cam
    return cam


def create_studio_lighting():
    """Create 3-point studio lighting setup."""
    lights = []

    # Key light (main illumination)
    bpy.ops.object.light_add(
        type="AREA",
        location=(0.3, -0.15, 0.3)
    )
    key = bpy.context.active_object
    key.name = "KeyLight"
    key.data.energy = 50
    key.data.size = 0.5
    key.data.color = (1.0, 0.98, 0.95)  # Slightly warm
    key.rotation_euler = (radians(45), radians(15), 0)
    lights.append(key)

    # Fill light (softer, from opposite side)
    bpy.ops.object.light_add(
        type="AREA",
        location=(-0.25, -0.1, 0.15)
    )
    fill = bpy.context.active_object
    fill.name = "FillLight"
    fill.data.energy = 15
    fill.data.size = 0.4
    fill.data.color = (0.95, 0.97, 1.0)  # Slightly cool
    lights.append(fill)

    # Rim/back light (edge definition)
    bpy.ops.object.light_add(
        type="AREA",
        location=(0, 0.2, 0.2)
    )
    rim = bpy.context.active_object
    rim.name = "RimLight"
    rim.data.energy = 25
    rim.data.size = 0.3
    rim.data.color = (1.0, 1.0, 1.0)
    lights.append(rim)

    return lights


def create_ground_plane():
    """Create a subtle ground plane for shadows."""
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"

    # Simple diffuse material (shadow catching is handled by transparent BG)
    mat = bpy.data.materials.new("Ground")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
    bsdf.inputs["Color"].default_value = (0.15, 0.15, 0.15, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.9

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    ground.data.materials.append(mat)
    return ground


def load_knob(glb_path: pathlib.Path, position: tuple) -> bpy.types.Object:
    """Load a knob GLB and position it."""
    # Import GLB
    bpy.ops.import_scene.gltf(filepath=str(glb_path))

    # Get the imported object(s)
    imported = bpy.context.selected_objects
    if not imported:
        return None

    # Group all imported objects under a parent empty if multiple
    if len(imported) == 1:
        obj = imported[0]
    else:
        # Create parent empty
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=position)
        parent = bpy.context.active_object
        parent.name = glb_path.stem

        for obj in imported:
            obj.parent = parent
        obj = parent

    # Position the knob
    obj.location = position

    return obj


def render_scene(output_path: pathlib.Path):
    """Render the scene to file."""
    bpy.context.scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)
    print(f"[RENDER] Saved: {output_path}")


def main():
    """Main render pipeline."""
    print("[RENDER] Setting up scene...")

    # Reset
    reset_scene()

    # Setup
    setup_render_settings()
    create_camera()
    create_studio_lighting()
    create_ground_plane()

    # Knob files and positions (arranged in a row)
    knobs = [
        ("neve_knob_style1_blue.glb", (-0.10, 0, 0)),
        ("neve_knob_style2_silver.glb", (-0.05, 0, 0)),
        ("neve_knob_style3_silver.glb", (0.0, 0, 0)),
        ("neve_knob_style4_silver.glb", (0.05, 0, 0)),
        ("neve_knob_style5_red.glb", (0.10, 0, 0)),
    ]

    print("[RENDER] Loading knobs...")
    for filename, position in knobs:
        glb_path = BUILD_DIR / filename
        if glb_path.exists():
            obj = load_knob(glb_path, position)
            if obj:
                # Scale up for better visibility
                obj.scale = (3.0, 3.0, 3.0)
                print(f"[RENDER] Loaded: {filename}")
        else:
            print(f"[RENDER] WARNING: Missing {glb_path}")

    # Render
    output_path = BUILD_DIR / "neve_knobs_all.png"
    print(f"[RENDER] Rendering to {output_path}...")
    render_scene(output_path)

    print("[RENDER] Done!")


if __name__ == "__main__":
    main()
