"""
Render individual Neve knob styles - each knob gets its own render.

Outputs:
- build/renders/knob_style1_blue.png
- build/renders/knob_style2_silver.png
- build/renders/knob_style3_silver_deep.png
- build/renders/knob_style4_silver_shallow.png
- build/renders/knob_style5_red.png
- build/renders/all_knobs_combined.png
"""
import bpy
import pathlib
import sys
import math

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from projects.neve_knobs.scripts.neve_knob_gn import build_artifact

# Output directory
BUILD_DIR = pathlib.Path(__file__).parent.parent / "build" / "renders"
BUILD_DIR.mkdir(parents=True, exist_ok=True)


def clear_scene():
    """Clear all objects and orphaned data."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.node_groups:
        if block.users == 0:
            bpy.data.node_groups.remove(block)


def setup_lighting():
    """Setup studio lighting."""
    # Key light
    bpy.ops.object.light_add(type="AREA", location=(2, -2, 4))
    key = bpy.context.active_object
    key.data.energy = 800
    key.data.size = 2
    key.name = "KeyLight"

    # Fill light
    bpy.ops.object.light_add(type="AREA", location=(-2, -1, 3))
    fill = bpy.context.active_object
    fill.data.energy = 300
    fill.data.size = 1.5
    fill.name = "FillLight"

    # Rim light
    bpy.ops.object.light_add(type="SPOT", location=(0, 2, 2))
    rim = bpy.context.active_object
    rim.data.energy = 200
    rim.rotation_euler = (math.radians(45), 0, math.radians(180))
    rim.name = "RimLight"


def setup_camera():
    """Setup camera for individual knob."""
    bpy.ops.object.camera_add(location=(0, -0.18, 0.1))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(70), 0, 0)
    cam.data.lens = 50
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 0.18
    cam.data.dof.aperture_fstop = 2.8
    bpy.context.scene.camera = cam
    return cam


def setup_world():
    """Setup world background."""
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.08, 0.08, 0.08, 1.0)
        bg.inputs["Strength"].default_value = 0.5


def setup_ground():
    """Add ground plane."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.01))
    ground = bpy.context.active_object
    gmat = bpy.data.materials.new("Ground")
    gmat.use_nodes = True
    gbsdf = gmat.node_tree.nodes["Principled BSDF"]
    gbsdf.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1.0)
    gbsdf.inputs["Roughness"].default_value = 0.95
    ground.data.materials.append(gmat)
    return ground


# 5 knob configurations with detailed parameters
KNOB_CONFIGS = [
    {
        "name": "style1_blue",
        "display_name": "Blue Cap",
        "description": "Glossy blue cap, smooth surface, integrated skirt",
        "params": {
            "cap_height": 0.020,
            "cap_diameter": 0.018,
            "skirt_height": 0.008,
            "skirt_diameter": 0.020,
            "skirt_style": 0,
            "ridge_count": 0,
            "ridge_depth": 0.0,
            "pointer_length": 0.012,
            "pointer_width": 0.08,
            "segments": 64,
            "base_color": [0.2, 0.35, 0.75],
            "pointer_color": [1.0, 1.0, 1.0],
            "metallic": 0.0,
            "roughness": 0.3,
            "clearcoat": 0.6,
        }
    },
    {
        "name": "style2_silver",
        "display_name": "Silver Knurled",
        "description": "Brushed metal with fine knurling, integrated skirt",
        "params": {
            "cap_height": 0.020,
            "cap_diameter": 0.018,
            "skirt_height": 0.008,
            "skirt_diameter": 0.020,
            "skirt_style": 0,
            "ridge_count": 24,
            "ridge_depth": 0.0008,
            "knurl_z_start": 0.0,
            "knurl_z_end": 1.0,
            "knurl_profile": 0.5,
            "pointer_length": 0.012,
            "pointer_width": 0.08,
            "segments": 64,
            "base_color": [0.75, 0.75, 0.78],
            "pointer_color": [1.0, 0.95, 0.9],
            "metallic": 0.85,
            "roughness": 0.25,
        }
    },
    {
        "name": "style3_silver_deep",
        "display_name": "Deep Knurl",
        "description": "Silver with aggressive knurling, deep profile",
        "params": {
            "cap_height": 0.022,
            "cap_diameter": 0.018,
            "skirt_height": 0.010,
            "skirt_diameter": 0.022,
            "skirt_style": 0,
            "ridge_count": 32,
            "ridge_depth": 0.0012,
            "knurl_z_start": 0.0,
            "knurl_z_end": 1.0,
            "knurl_profile": 0.7,
            "pointer_length": 0.014,
            "pointer_width": 0.06,
            "segments": 64,
            "base_color": [0.7, 0.7, 0.73],
            "pointer_color": [0.9, 0.9, 0.95],
            "metallic": 0.9,
            "roughness": 0.2,
        }
    },
    {
        "name": "style4_silver_shallow",
        "display_name": "Shallow Knurl",
        "description": "Subtle knurling, wider grip area",
        "params": {
            "cap_height": 0.018,
            "cap_diameter": 0.020,
            "skirt_height": 0.006,
            "skirt_diameter": 0.024,
            "skirt_style": 0,
            "ridge_count": 18,
            "ridge_depth": 0.0005,
            "knurl_z_start": 0.2,
            "knurl_z_end": 0.8,
            "knurl_fade": 0.1,
            "knurl_profile": 0.3,
            "pointer_length": 0.012,
            "pointer_width": 0.1,
            "segments": 64,
            "base_color": [0.8, 0.8, 0.82],
            "pointer_color": [1.0, 1.0, 1.0],
            "metallic": 0.8,
            "roughness": 0.35,
        }
    },
    {
        "name": "style5_red",
        "display_name": "Red Collet",
        "description": "Red cap with separate rotating skirt (collet style)",
        "params": {
            "cap_height": 0.020,
            "cap_diameter": 0.018,
            "skirt_height": 0.008,
            "skirt_diameter": 0.020,
            "skirt_style": 1,  # Separate
            "ridge_count": 0,
            "ridge_depth": 0.0,
            "pointer_length": 0.012,
            "pointer_width": 0.08,
            "segments": 64,
            "base_color": [0.85, 0.15, 0.1],
            "pointer_color": [1.0, 1.0, 1.0],
            "metallic": 0.0,
            "roughness": 0.25,
            "clearcoat": 0.8,
        }
    },
]


def render_individual_knob(config: dict, output_path: pathlib.Path):
    """Render a single knob to file."""
    print(f"\n{'='*50}")
    print(f"Rendering: {config['display_name']}")
    print(f"Description: {config['description']}")
    print(f"Output: {output_path}")
    print(f"{'='*50}")

    # Clear scene
    clear_scene()

    # Setup scene
    col = bpy.data.collections.new("Knob")
    bpy.context.scene.collection.children.link(col)

    # Build knob
    task = {"parameters": config["params"]}
    result = build_artifact(task, col)
    knob = result["root_objects"][0]

    # Scale up for better visibility
    knob.scale = (25, 25, 25)
    knob.location = (0, 0, 0)
    knob.name = config["name"]

    # Apply geometry nodes modifier
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = knob
    knob.select_set(True)
    bpy.ops.object.modifier_apply(modifier="KnobGeometry")

    # Verify mesh
    print(f"Mesh: {len(knob.data.vertices)} vertices")

    # Setup scene elements
    setup_world()
    setup_ground()
    setup_lighting()
    setup_camera()

    # Render settings
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.film_transparent = False

    # Render
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)
    print(f"[OK] Saved: {output_path}")

    return knob


def render_combined():
    """Render all knobs in a single scene."""
    print(f"\n{'='*50}")
    print("Rendering: Combined view of all 5 knobs")
    print(f"{'='*50}")

    clear_scene()

    col = bpy.data.collections.new("AllKnobs")
    bpy.context.scene.collection.children.link(col)

    # Build all knobs
    spacing = 0.7  # meters between centers
    start_x = -spacing * 2

    for i, config in enumerate(KNOB_CONFIGS):
        task = {"parameters": config["params"]}
        result = build_artifact(task, col)
        knob = result["root_objects"][0]

        knob.scale = (25, 25, 25)
        knob.location = (start_x + i * spacing, 0, 0)
        knob.name = config["name"]

        # Apply modifier
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = knob
        knob.select_set(True)
        bpy.ops.object.modifier_apply(modifier="KnobGeometry")
        print(f"  Added: {config['name']}")

    # Setup scene
    setup_world()

    # Wider ground
    bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, -0.01))
    ground = bpy.context.active_object
    gmat = bpy.data.materials.new("Ground")
    gmat.use_nodes = True
    gbsdf = gmat.node_tree.nodes["Principled BSDF"]
    gbsdf.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1.0)
    gbsdf.inputs["Roughness"].default_value = 0.95
    ground.data.materials.append(gmat)

    # Wider camera view
    bpy.ops.object.camera_add(location=(0, -2.5, 1.2))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(65), 0, 0)
    cam.data.lens = 45
    bpy.context.scene.camera = cam

    # Lighting
    bpy.ops.object.light_add(type="AREA", location=(3, -3, 5))
    bpy.context.active_object.data.energy = 1500
    bpy.context.active_object.data.size = 4

    bpy.ops.object.light_add(type="AREA", location=(-3, -2, 4))
    bpy.context.active_object.data.energy = 600
    bpy.context.active_object.data.size = 3

    # Render settings - wider aspect
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 2400
    scene.render.resolution_y = 600

    output = BUILD_DIR / "all_knobs_combined.png"
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    print(f"[OK] Saved: {output}")


def main():
    print("\n" + "="*60)
    print("NEVE KNOBS - Individual Render Generator")
    print("="*60)

    # Render each knob individually
    for config in KNOB_CONFIGS:
        output_path = BUILD_DIR / f"knob_{config['name']}.png"
        render_individual_knob(config, output_path)

    # Render combined view
    render_combined()

    print("\n" + "="*60)
    print("RENDER COMPLETE")
    print("="*60)
    print(f"\nOutput directory: {BUILD_DIR}")
    print("\nFiles created:")
    for config in KNOB_CONFIGS:
        print(f"  - knob_{config['name']}.png")
    print("  - all_knobs_combined.png")


if __name__ == "__main__":
    main()
