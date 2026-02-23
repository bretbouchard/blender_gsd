"""
Render script for Universal Input System knobs.

Creates multiple renders showing different configurations:
1. Default knob with rounded caps
2. Knob with knurling enabled
3. Different cap styles

Supports debug mode to visualize individual sections with distinct colors.
"""

import bpy
import math
import sys
import pathlib

# Add project root to path
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group
from lib.inputs.debug_materials import create_all_debug_materials, DEBUG_PRESETS


def setup_scene():
    """Set up the scene with lighting and camera."""
    # Delete existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create a plane for ground
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, -0.01))
    plane = bpy.context.active_object
    plane.name = "Ground"

    # Add ground material
    mat = bpy.data.materials.new("Ground_Material")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.15, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.9
    plane.data.materials.append(mat)

    # Camera setup
    bpy.ops.object.camera_add(location=(0.08, -0.12, 0.08))
    camera = bpy.context.active_object
    camera.name = "Main_Camera"

    # Point camera at origin
    direction = -camera.location.normalized()
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()

    bpy.context.scene.camera = camera

    # Lighting - Three-point setup
    # Key light
    bpy.ops.object.light_add(type='SUN', location=(0.5, -0.5, 1))
    key_light = bpy.context.active_object
    key_light.name = "Key_Light"
    key_light.data.energy = 3.0
    key_light.data.angle = math.radians(15)
    key_light.rotation_euler = (math.radians(45), math.radians(30), 0)

    # Fill light
    bpy.ops.object.light_add(type='SUN', location=(-0.3, -0.3, 0.5))
    fill_light = bpy.context.active_object
    fill_light.name = "Fill_Light"
    fill_light.data.energy = 1.0
    fill_light.rotation_euler = (math.radians(60), math.radians(-30), 0)

    # Back light
    bpy.ops.object.light_add(type='SUN', location=(0, 0.3, 0.3))
    back_light = bpy.context.active_object
    back_light.name = "Back_Light"
    back_light.data.energy = 1.5
    back_light.rotation_euler = (math.radians(120), 0, 0)

    # Top fill light - illuminates rounded cap tops from angle views
    # Without this, UV sphere caps appear dark when viewed from side angles
    # because the curved surface catches less light from the key/fill lights
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 1))
    top_light = bpy.context.active_object
    top_light.name = "Top_Fill_Light"
    top_light.data.energy = 1.2  # Moderate intensity for natural look
    top_light.rotation_euler = (math.radians(0), 0, 0)  # Pointing straight down

    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.film_transparent = True

    return camera


def create_knob_with_settings(
    name: str,
    settings: dict,
    debug_mode: bool = False,
    debug_preset: str = "rainbow"
) -> bpy.types.Object:
    """
    Create a knob object with specific settings.

    Args:
        name: Object name
        settings: Dictionary of knob parameters
        debug_mode: If True, enable debug materials to show sections
        debug_preset: Debug color preset ("rainbow", "grayscale", "complementary", "heat_map")

    Returns:
        The created knob object
    """
    # Create the node group
    node_group = create_input_node_group(f"Input_{name}")

    # Create a mesh object
    bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name

    # Add geometry nodes modifier
    mod = obj.modifiers.new(name="Knob", type='NODES')
    mod.node_group = node_group

    # Build a mapping from socket name to identifier
    socket_map = {}
    for item in node_group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            socket_map[item.name] = item.identifier

    # In debug mode, apply tapered diameters so all 6 sections are visible
    # When sections have the same radius, they form a continuous cylinder
    # and material boundaries become invisible
    if debug_mode:
        settings = settings.copy()  # Don't modify original
        # Taper from top to bottom for visible sections
        # Chain: Top → A_Mid_Top → A_Bot_Top → AB_Junction → B_Mid_Bot → Bot
        settings["Top_Diameter"] = 8.0        # Smallest (A_Top cap top)
        settings["A_Mid_Top_Diameter"] = 10.0  # A_Mid top
        settings["A_Bot_Top_Diameter"] = 12.0  # A_Bot top
        settings["AB_Junction_Diameter"] = 14.0  # Zone transition
        settings["B_Mid_Bot_Diameter"] = 16.0  # B_Mid bottom
        settings["Bot_Diameter"] = 18.0        # Largest (B_Bot cap bottom)
        print(f"    Debug diameters: Top={settings['Top_Diameter']:.1f} → Bot={settings['Bot_Diameter']:.1f}")

    # Apply settings using identifier-based access
    for key, value in settings.items():
        if key in socket_map:
            identifier = socket_map[key]
            # Use the identifier to set the value
            try:
                if isinstance(value, (list, tuple)) and len(value) == 3:
                    mod[identifier] = (*value, 1.0)  # Add alpha for color
                else:
                    mod[identifier] = value
            except Exception as e:
                print(f"    Warning: Could not set {key}={value}: {e}")

    # Handle debug mode
    if debug_mode:
        # Create debug materials
        debug_mats = create_all_debug_materials(preset=debug_preset)

        # Set debug mode to True
        if "Debug_Mode" in socket_map:
            mod[socket_map["Debug_Mode"]] = True

        # Assign debug materials to each section (6 sections)
        section_map = {
            "Debug_A_Top_Material": "A_Top",
            "Debug_A_Mid_Material": "A_Mid",
            "Debug_A_Bot_Material": "A_Bot",
            "Debug_B_Top_Material": "B_Top",
            "Debug_B_Mid_Material": "B_Mid",
            "Debug_B_Bot_Material": "B_Bot",
        }

        for socket_name, section_name in section_map.items():
            if socket_name in socket_map and section_name in debug_mats:
                mod[socket_map[socket_name]] = debug_mats[section_name]

    return obj


def render_view(output_path: str, azimuth: float = 45, elevation: float = 30):
    """Render from a specific view angle."""
    camera = bpy.data.objects["Main_Camera"]

    # Calculate camera position from azimuth and elevation
    distance = 0.16
    azimuth_rad = math.radians(azimuth)
    elev_rad = math.radians(elevation)

    x = distance * math.cos(elev_rad) * math.sin(azimuth_rad)
    y = distance * math.cos(elev_rad) * math.cos(azimuth_rad)
    z = distance * math.sin(elev_rad)

    camera.location = (x, -y, z)

    # Point at origin
    direction = (-x, y, -z)
    direction = bpy.mathutils.Vector(direction).normalized()
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()

    # Render
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


def main(debug_mode: bool = False, debug_preset: str = "rainbow"):
    """
    Main render function.

    Args:
        debug_mode: If True, render with debug materials showing sections
        debug_preset: Debug color preset ("rainbow", "grayscale", "complementary", "heat_map")
    """
    import mathutils
    bpy.mathutils = mathutils

    output_dir = ROOT / "projects" / "output" / "knob_renders"
    output_dir.mkdir(parents=True, exist_ok=True)

    mode_suffix = "_debug" if debug_mode else ""

    print("=" * 60)
    print("Universal Input System - Knob Renders (Base Shape Only)")
    if debug_mode:
        print(f"DEBUG MODE: {debug_preset} preset")
    print("=" * 60)

    # Setup scene
    setup_scene()

    # Define render configurations - Testing boolean-based knurling
    configs = [
        # Test 1: No knurling, rounded caps - baseline
        {
            "name": "no_knurl_rounded",
            "description": "Baseline: Rounded caps, no knurling",
            "settings": {
                "Segments": 64,
                "Top_Diameter": 14.0,
                "A_Mid_Top_Diameter": 14.0,
                "A_Bot_Top_Diameter": 14.0,
                "AB_Junction_Diameter": 14.0,
                "B_Mid_Bot_Diameter": 14.0,
                "Bot_Diameter": 14.0,
                "A_Top_Height": 3.0,
                "A_Mid_Height": 6.0,
                "A_Bot_Height": 2.0,
                "B_Top_Height": 2.0,
                "B_Mid_Height": 6.0,
                "B_Bot_Height": 2.0,
                "A_Top_Style": 2,  # Rounded
                "B_Bot_Style": 2,  # Rounded
                # NO knurling
                "A_Mid_Knurl": False,
                "A_Bot_Knurl": False,
                "B_Top_Knurl": False,
                "B_Mid_Knurl": False,
                "Color": (0.5, 0.5, 0.52),
                "Metallic": 0.0,
                "Roughness": 0.5,
            }
        },
        # Test 2: 20 grooves, 0.5 depth
        {
            "name": "knurl_20_depth05",
            "description": "20 grooves, 0.5mm depth",
            "settings": {
                "Segments": 64,
                "Top_Diameter": 14.0,
                "A_Mid_Top_Diameter": 14.0,
                "A_Bot_Top_Diameter": 14.0,
                "AB_Junction_Diameter": 14.0,
                "B_Mid_Bot_Diameter": 14.0,
                "Bot_Diameter": 14.0,
                "A_Top_Height": 3.0,
                "A_Mid_Height": 6.0,
                "A_Bot_Height": 2.0,
                "B_Top_Height": 2.0,
                "B_Mid_Height": 6.0,
                "B_Bot_Height": 2.0,
                "A_Top_Style": 2,
                "B_Bot_Style": 2,
                "A_Mid_Knurl": False,
                "A_Bot_Knurl": False,
                "B_Top_Knurl": False,
                "B_Mid_Knurl": True,
                "B_Mid_Knurl_Count": 20,
                "B_Mid_Knurl_Depth": 0.5,
                "Color": (0.5, 0.5, 0.52),
                "Metallic": 0.0,
                "Roughness": 0.5,
            }
        },
        # Test 3: 40 grooves, 0.3 depth
        {
            "name": "knurl_40_depth03",
            "description": "40 grooves, 0.3mm depth",
            "settings": {
                "Segments": 64,
                "Top_Diameter": 14.0,
                "A_Mid_Top_Diameter": 14.0,
                "A_Bot_Top_Diameter": 14.0,
                "AB_Junction_Diameter": 14.0,
                "B_Mid_Bot_Diameter": 14.0,
                "Bot_Diameter": 14.0,
                "A_Top_Height": 3.0,
                "A_Mid_Height": 6.0,
                "A_Bot_Height": 2.0,
                "B_Top_Height": 2.0,
                "B_Mid_Height": 6.0,
                "B_Bot_Height": 2.0,
                "A_Top_Style": 2,
                "B_Bot_Style": 2,
                "A_Mid_Knurl": False,
                "A_Bot_Knurl": False,
                "B_Top_Knurl": False,
                "B_Mid_Knurl": True,
                "B_Mid_Knurl_Count": 40,
                "B_Mid_Knurl_Depth": 0.3,
                "Color": (0.5, 0.5, 0.52),
                "Metallic": 0.0,
                "Roughness": 0.5,
            }
        },
        # Test 4: 60 grooves, 0.2 depth
        {
            "name": "knurl_60_depth02",
            "description": "60 grooves, 0.2mm depth",
            "settings": {
                "Segments": 64,
                "Top_Diameter": 14.0,
                "A_Mid_Top_Diameter": 14.0,
                "A_Bot_Top_Diameter": 14.0,
                "AB_Junction_Diameter": 14.0,
                "B_Mid_Bot_Diameter": 14.0,
                "Bot_Diameter": 14.0,
                "A_Top_Height": 3.0,
                "A_Mid_Height": 6.0,
                "A_Bot_Height": 2.0,
                "B_Top_Height": 2.0,
                "B_Mid_Height": 6.0,
                "B_Bot_Height": 2.0,
                "A_Top_Style": 2,
                "B_Bot_Style": 2,
                "A_Mid_Knurl": False,
                "A_Bot_Knurl": False,
                "B_Top_Knurl": False,
                "B_Mid_Knurl": True,
                "B_Mid_Knurl_Count": 60,
                "B_Mid_Knurl_Depth": 0.2,
                "Color": (0.5, 0.5, 0.52),
                "Metallic": 0.0,
                "Roughness": 0.5,
            }
        },
    ]

    # Render each configuration
    for i, config in enumerate(configs):
        print(f"\n[{i+1}/{len(configs)}] Rendering: {config['name']}")
        print(f"    {config['description']}")

        # Delete previous knob
        for obj in bpy.data.objects:
            if obj.name.startswith(("default", "knurled", "flat", "beveled")):
                bpy.data.objects.remove(obj, do_unlink=True)

        # Create new knob with debug mode
        knob = create_knob_with_settings(
            config['name'],
            config['settings'],
            debug_mode=debug_mode,
            debug_preset=debug_preset
        )

        # Render multiple angles
        views = [
            ("front", 0, 25),
            ("side", 90, 25),
            ("top", 0, 70),
            ("angle", 45, 30),
        ]

        for view_name, azimuth, elevation in views:
            output_path = str(output_dir / f"{config['name']}{mode_suffix}_{view_name}.png")
            print(f"    Rendering {view_name} view...")
            render_view(output_path, azimuth, elevation)

    print("\n" + "=" * 60)
    print(f"Renders saved to: {output_dir}")
    print("=" * 60)

    # Also save the blend file
    blend_name = f"knob_renders{mode_suffix}.blend"
    blend_path = str(output_dir / blend_name)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Blend file saved to: {blend_path}")


def render_debug(preset: str = "rainbow"):
    """Convenience function to render with debug mode enabled."""
    main(debug_mode=True, debug_preset=preset)


if __name__ == "__main__":
    # Handle Blender's argument passing (arguments after '--')
    import sys

    # Find where our args start (after '--' if present)
    try:
        arg_start = sys.argv.index('--') + 1
        our_args = sys.argv[arg_start:]
    except ValueError:
        our_args = []

    # Parse our arguments
    debug_mode = "--debug" in our_args
    preset = "rainbow"

    if "--preset" in our_args:
        idx = our_args.index("--preset")
        if idx + 1 < len(our_args):
            preset = our_args[idx + 1]

    main(debug_mode=debug_mode, debug_preset=preset)
