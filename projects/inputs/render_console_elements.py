"""
Console UI Elements - Test Render

Creates renders of all UI element types:
1. Knobs (various styles)
2. Buttons (flat, domed, illuminated)
3. Faders (channel, short)
4. LEDs (single, bar)

Following the same methodology as the Neve knob renders.
"""

import bpy
import math
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group
from lib.inputs.button_builder import create_button_node_group
from lib.inputs.fader_builder import create_fader_node_group
from lib.inputs.led_builder import create_led_node_group


def setup_scene():
    """Set up scene with professional lighting."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Camera
    bpy.ops.object.camera_add(location=(0.15, -0.20, 0.12))
    camera = bpy.context.active_object
    direction = -camera.location.normalized()
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    bpy.context.scene.camera = camera

    # Key light
    bpy.ops.object.light_add(type='SUN', location=(0.5, -0.5, 1))
    light = bpy.context.active_object
    light.data.energy = 2.5
    light.rotation_euler = (math.radians(50), math.radians(25), 0)

    # Fill light
    bpy.ops.object.light_add(type='SUN', location=(-0.3, -0.4, 0.6))
    light = bpy.context.active_object
    light.data.energy = 1.2
    light.rotation_euler = (math.radians(55), math.radians(-25), 0)

    # Top fill
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 1))
    light = bpy.context.active_object
    light.data.energy = 1.0

    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 800
    scene.render.film_transparent = True


def create_element(node_group_func, name: str, settings: dict, position: tuple):
    """Create an element with specific settings at a position."""
    node_group = node_group_func(f"Element_{name}")

    bpy.ops.mesh.primitive_plane_add(size=0.001, location=position)
    obj = bpy.context.active_object
    obj.name = name

    mod = obj.modifiers.new(name="Element", type='NODES')
    mod.node_group = node_group

    # Build socket map
    socket_map = {}
    for item in node_group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            socket_map[item.name] = item.identifier

    # Apply settings
    for key, value in settings.items():
        if key in socket_map:
            try:
                if isinstance(value, (list, tuple)) and len(value) == 3:
                    mod[socket_map[key]] = (*value, 1.0)
                else:
                    mod[socket_map[key]] = value
            except Exception as e:
                pass

    return obj


def render(output_path: str):
    """Render."""
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


def main():
    import mathutils
    bpy.mathutils = mathutils

    output_dir = ROOT / "projects" / "output" / "console_elements"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Console UI Elements - Test Render")
    print("=" * 60)

    setup_scene()

    # =========================================================================
    # KNOBS (using existing knob builder)
    # =========================================================================
    print("\n[1/4] Creating Knobs...")

    knob_settings = {
        "Segments": 64,
        "Top_Diameter": 12.0,
        "A_Mid_Top_Diameter": 14.0,
        "A_Bot_Top_Diameter": 14.0,
        "AB_Junction_Diameter": 14.0,
        "B_Mid_Bot_Diameter": 14.0,
        "Bot_Diameter": 16.0,
        "A_Top_Height": 3.0,
        "A_Mid_Height": 6.0,
        "A_Bot_Height": 2.0,
        "B_Top_Height": 2.0,
        "B_Mid_Height": 6.0,
        "B_Bot_Height": 3.0,
        "A_Top_Style": 2,  # Rounded
        "B_Bot_Style": 3,  # Tapered+Skirt
        "B_Mid_Knurl": True,
        "B_Mid_Knurl_Count": 40,
        "B_Mid_Knurl_Depth": 0.35,
        "Color": (0.45, 0.45, 0.47),
        "Metallic": 0.0,
        "Roughness": 0.4,
    }

    create_element(create_input_node_group, "Knob_Neve", knob_settings, (-0.04, 0, 0))
    print("    Created Neve-style knob")

    # =========================================================================
    # BUTTONS
    # =========================================================================
    print("\n[2/4] Creating Buttons...")

    button_domed = {
        "Diameter": 12.0,
        "Height": 5.0,
        "Travel": 2.0,
        "Segments": 32,
        "Style": 1,  # Domed
        "Dome_Radius": 0.6,
        "Bezel_Enabled": True,
        "Bezel_Width": 1.5,
        "Body_Color": (0.15, 0.15, 0.15),
        "Roughness": 0.4,
    }

    create_element(create_button_node_group, "Button_Domed", button_domed, (0.0, 0, 0))
    print("    Created domed button")

    button_illuminated = {
        "Diameter": 10.0,
        "Height": 4.0,
        "Travel": 1.5,
        "Segments": 32,
        "Style": 3,  # Illuminated
        "LED_Enabled": True,
        "LED_Style": 0,  # Ring
        "LED_Size": 3.0,
        "LED_Color_On": (0.0, 1.0, 0.0),
        "LED_State": True,
        "LED_Intensity": 3.0,
        "Body_Color": (0.1, 0.1, 0.1),
    }

    create_element(create_button_node_group, "Button_LED", button_illuminated, (0.04, 0, 0))
    print("    Created illuminated button")

    # =========================================================================
    # FADERS
    # =========================================================================
    print("\n[3/4] Creating Faders...")

    fader_settings = {
        "Type": 0,  # Channel fader
        "Track_Width": 6.0,
        "Track_Depth": 3.0,
        "Knob_Style": 0,  # Square (SSL style)
        "Knob_Width": 12.0,
        "Knob_Height": 18.0,
        "Knob_Depth": 8.0,
        "Value": 0.7,  # 70% position
        "Travel_Length": 100.0,
        "Track_Color": (0.3, 0.3, 0.3),
        "Knob_Color": (0.1, 0.1, 0.1),
    }

    create_element(create_fader_node_group, "Fader_Channel", fader_settings, (0.10, 0, 0))
    print("    Created channel fader")

    # =========================================================================
    # LEDs
    # =========================================================================
    print("\n[4/4] Creating LEDs...")

    led_single = {
        "Type": 0,  # Single
        "Size": 5.0,
        "Height": 2.0,
        "Shape": 0,  # Round
        "Bezel_Enabled": True,
        "Bezel_Width": 1.0,
        "Color_On": (0.0, 1.0, 0.0),
        "State": True,
        "Glow_Enabled": True,
        "Glow_Intensity": 3.0,
    }

    create_element(create_led_node_group, "LED_Single", led_single, (-0.04, 0.06, 0))
    print("    Created single LED")

    led_bar = {
        "Type": 1,  # Bar
        "Segments": 15,
        "Segment_Width": 3.0,
        "Segment_Height": 20.0,
        "Segment_Spacing": 1.0,
        "Direction": 0,  # Vertical
        "Bezel_Enabled": True,
        "Color_On": (0.0, 0.8, 0.0),
        "Color_Warning": (1.0, 1.0, 0.0),
        "Color_Danger": (1.0, 0.0, 0.0),
        "Value": 0.75,
        "Warning_Threshold": 0.7,
        "Danger_Threshold": 0.9,
        "Glow_Enabled": True,
    }

    create_element(create_led_node_group, "LED_Bar", led_bar, (0.0, 0.06, 0))
    print("    Created LED bar")

    # =========================================================================
    # RENDER
    # =========================================================================
    print("\nRendering...")
    render(str(output_dir / "console_elements_test.png"))
    print(f"Saved: console_elements_test.png")

    # Save blend file
    blend_path = str(output_dir / "console_elements.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Blend file: {blend_path}")

    print("\n" + "=" * 60)
    print(f"Output: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
