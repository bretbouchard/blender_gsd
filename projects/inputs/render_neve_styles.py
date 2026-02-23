"""
Neve-Style Knob Renders

Creates renders matching the classic Neve console knob styles:
1. Large Knob - Fine Knurling (tall with fine grip)
2. Medium Knob - Coarse Knurling (shorter, wider grooves)
3. Small Knob - Fine Knurling (compact)
4. Push-Button Style - Recessed top ring
5. Large Smooth - No knurling, rounded
6. Medium Smooth with Indicator - No knurling
7. Small Push-Button - Compact push style
8. Tiny Smooth - Very small, no knurling
"""

import bpy
import math
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs.node_group_builder import create_input_node_group


def setup_scene():
    """Set up scene with professional lighting."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Ground plane
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, -0.01))
    plane = bpy.context.active_object
    plane.name = "Ground"
    mat = bpy.data.materials.new("Ground_Material")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.12, 0.12, 0.12, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95
    plane.data.materials.append(mat)

    # Camera
    bpy.ops.object.camera_add(location=(0.08, -0.14, 0.07))
    camera = bpy.context.active_object
    camera.name = "Main_Camera"
    direction = -camera.location.normalized()
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    bpy.context.scene.camera = camera

    # Three-point lighting
    # Key light
    bpy.ops.object.light_add(type='SUN', location=(0.5, -0.5, 1))
    key_light = bpy.context.active_object
    key_light.name = "Key_Light"
    key_light.data.energy = 2.5
    key_light.data.angle = math.radians(10)
    key_light.rotation_euler = (math.radians(50), math.radians(25), 0)

    # Fill light
    bpy.ops.object.light_add(type='SUN', location=(-0.3, -0.4, 0.6))
    fill_light = bpy.context.active_object
    fill_light.name = "Fill_Light"
    fill_light.data.energy = 1.2
    fill_light.rotation_euler = (math.radians(55), math.radians(-25), 0)

    # Back/rim light
    bpy.ops.object.light_add(type='SUN', location=(0.1, 0.4, 0.4))
    back_light = bpy.context.active_object
    back_light.name = "Back_Light"
    back_light.data.energy = 1.8
    back_light.rotation_euler = (math.radians(120), 0, 0)

    # Top fill for rounded caps
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 1))
    top_light = bpy.context.active_object
    top_light.name = "Top_Fill"
    top_light.data.energy = 1.0
    top_light.rotation_euler = (0, 0, 0)

    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 256
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.film_transparent = True


def create_knob(name: str, settings: dict) -> bpy.types.Object:
    """Create a knob with specific settings."""
    node_group = create_input_node_group(f"Input_{name}")

    bpy.ops.mesh.primitive_plane_add(size=0.001, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name

    mod = obj.modifiers.new(name="Knob", type='NODES')
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
                print(f"    Warning: Could not set {key}={value}: {e}")

    return obj


def render_view(output_path: str, azimuth: float = 45, elevation: float = 25):
    """Render from a specific view angle."""
    camera = bpy.data.objects["Main_Camera"]
    distance = 0.16
    azimuth_rad = math.radians(azimuth)
    elev_rad = math.radians(elevation)

    x = distance * math.cos(elev_rad) * math.sin(azimuth_rad)
    y = distance * math.cos(elev_rad) * math.cos(azimuth_rad)
    z = distance * math.sin(elev_rad)

    camera.location = (x, -y, z)
    direction = (-x, y, -z)
    direction = bpy.mathutils.Vector(direction).normalized()
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()

    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


# =============================================================================
# NEVE KNOB CONFIGURATIONS
# =============================================================================

# Base settings common to all Neve knobs
NEVE_BASE = {
    "Segments": 64,
    # All Neve knobs have uniform diameter (no taper)
    "Top_Diameter": 14.0,
    "A_Mid_Top_Diameter": 14.0,
    "A_Bot_Top_Diameter": 14.0,
    "AB_Junction_Diameter": 14.0,
    "B_Mid_Bot_Diameter": 14.0,
    "Bot_Diameter": 14.0,
    # Default knurling off
    "A_Mid_Knurl": False,
    "A_Bot_Knurl": False,
    "B_Top_Knurl": False,
    "B_Mid_Knurl": False,
    # Neve gray color
    "Color": (0.45, 0.45, 0.47),
    "Metallic": 0.0,
    "Roughness": 0.4,
}

# 1. Large Knob - Fine Knurling (tall with fine grip)
NEVE_LARGE_FINE_KNURL = {
    **NEVE_BASE,
    "Top_Diameter": 12.0,
    "A_Mid_Top_Diameter": 14.0,
    "A_Bot_Top_Diameter": 14.0,
    "AB_Junction_Diameter": 14.0,
    "B_Mid_Bot_Diameter": 14.0,
    "Bot_Diameter": 16.0,     # Wider bottom for taper
    "A_Top_Height": 4.0,      # Tall rounded top
    "A_Mid_Height": 4.0,
    "A_Bot_Height": 2.0,
    "B_Top_Height": 2.0,
    "B_Mid_Height": 8.0,      # Tall grip section
    "B_Bot_Height": 3.0,      # Tapered+skirt height
    "A_Top_Style": 2,         # Rounded
    "B_Bot_Style": 3,         # Tapered+Skirt (Neve style)
    "B_Mid_Knurl": True,
    "B_Mid_Knurl_Count": 60,  # Fine knurling (60 grooves)
    "B_Mid_Knurl_Depth": 0.3,
}

# 2. Medium Knob - Coarse Knurling (shorter, wider grooves)
NEVE_MEDIUM_COARSE_KNURL = {
    **NEVE_BASE,
    "Top_Diameter": 12.0,
    "A_Mid_Top_Diameter": 14.0,
    "A_Bot_Top_Diameter": 14.0,
    "AB_Junction_Diameter": 14.0,
    "B_Mid_Bot_Diameter": 14.0,
    "Bot_Diameter": 16.0,     # Wider bottom
    "A_Top_Height": 3.0,
    "A_Mid_Height": 3.0,
    "A_Bot_Height": 2.0,
    "B_Top_Height": 2.0,
    "B_Mid_Height": 6.0,
    "B_Bot_Height": 2.5,
    "A_Top_Style": 2,
    "B_Bot_Style": 3,         # Tapered+Skirt
    "B_Mid_Knurl": True,
    "B_Mid_Knurl_Count": 30,  # Coarse knurling (30 grooves)
    "B_Mid_Knurl_Depth": 0.5,
}

# 3. Small Knob - Fine Knurling (compact)
NEVE_SMALL_FINE_KNURL = {
    **NEVE_BASE,
    "Top_Diameter": 9.0,
    "A_Mid_Top_Diameter": 11.0,
    "A_Bot_Top_Diameter": 11.0,
    "AB_Junction_Diameter": 11.0,
    "B_Mid_Bot_Diameter": 11.0,
    "Bot_Diameter": 13.0,     # Wider bottom
    "A_Top_Height": 2.5,
    "A_Mid_Height": 2.0,
    "A_Bot_Height": 1.5,
    "B_Top_Height": 1.5,
    "B_Mid_Height": 5.0,
    "B_Bot_Height": 2.0,
    "A_Top_Style": 2,
    "B_Bot_Style": 3,         # Tapered+Skirt
    "B_Mid_Knurl": True,
    "B_Mid_Knurl_Count": 50,  # Fine knurling
    "B_Mid_Knurl_Depth": 0.25,
}

# 4. Push-Button Style - Flat top with ring (recessed appearance)
NEVE_PUSH_BUTTON = {
    **NEVE_BASE,
    "Top_Diameter": 10.0,     # Smaller top for recessed look
    "A_Mid_Top_Diameter": 14.0,
    "A_Bot_Top_Diameter": 14.0,
    "AB_Junction_Diameter": 14.0,
    "B_Mid_Bot_Diameter": 14.0,
    "Bot_Diameter": 16.0,     # Wider bottom
    "A_Top_Height": 2.0,      # Short flat top
    "A_Mid_Height": 3.0,
    "A_Bot_Height": 2.0,
    "B_Top_Height": 2.0,
    "B_Mid_Height": 6.0,
    "B_Bot_Height": 2.5,
    "A_Top_Style": 0,         # Flat top
    "B_Bot_Style": 3,         # Tapered+Skirt
    "B_Mid_Knurl": True,
    "B_Mid_Knurl_Count": 40,
    "B_Mid_Knurl_Depth": 0.35,
}

# 5. Large Smooth - No knurling, fully rounded
NEVE_LARGE_SMOOTH = {
    **NEVE_BASE,
    "Top_Diameter": 14.0,
    "A_Mid_Top_Diameter": 14.0,
    "A_Bot_Top_Diameter": 14.0,
    "AB_Junction_Diameter": 14.0,
    "B_Mid_Bot_Diameter": 14.0,
    "Bot_Diameter": 16.0,     # Wider bottom
    "A_Top_Height": 4.0,
    "A_Mid_Height": 4.0,
    "A_Bot_Height": 2.0,
    "B_Top_Height": 2.0,
    "B_Mid_Height": 8.0,
    "B_Bot_Height": 3.0,
    "A_Top_Style": 2,         # Rounded
    "B_Bot_Style": 3,         # Tapered+Skirt
    # No knurling
}

# 6. Medium Smooth with Indicator - No knurling
NEVE_MEDIUM_SMOOTH = {
    **NEVE_BASE,
    "Top_Diameter": 12.0,
    "A_Mid_Top_Diameter": 13.0,
    "A_Bot_Top_Diameter": 13.0,
    "AB_Junction_Diameter": 13.0,
    "B_Mid_Bot_Diameter": 13.0,
    "Bot_Diameter": 15.0,     # Wider bottom
    "A_Top_Height": 3.0,
    "A_Mid_Height": 3.0,
    "A_Bot_Height": 2.0,
    "B_Top_Height": 2.0,
    "B_Mid_Height": 6.0,
    "B_Bot_Height": 2.5,
    "A_Top_Style": 2,
    "B_Bot_Style": 3,         # Tapered+Skirt
    # No knurling
}

# 7. Small Push-Button - Compact push style
NEVE_SMALL_PUSH = {
    **NEVE_BASE,
    "Top_Diameter": 8.0,
    "A_Mid_Top_Diameter": 10.0,
    "A_Bot_Top_Diameter": 10.0,
    "AB_Junction_Diameter": 10.0,
    "B_Mid_Bot_Diameter": 10.0,
    "Bot_Diameter": 12.0,     # Wider bottom
    "A_Top_Height": 1.5,
    "A_Mid_Height": 2.0,
    "A_Bot_Height": 1.0,
    "B_Top_Height": 1.0,
    "B_Mid_Height": 4.0,
    "B_Bot_Height": 2.0,
    "A_Top_Style": 0,         # Flat
    "B_Bot_Style": 3,         # Tapered+Skirt
    "B_Mid_Knurl": True,
    "B_Mid_Knurl_Count": 35,
    "B_Mid_Knurl_Depth": 0.3,
}

# 8. Tiny Smooth - Very small, no knurling
NEVE_TINY_SMOOTH = {
    **NEVE_BASE,
    "Top_Diameter": 8.0,
    "A_Mid_Top_Diameter": 9.0,
    "A_Bot_Top_Diameter": 9.0,
    "AB_Junction_Diameter": 9.0,
    "B_Mid_Bot_Diameter": 9.0,
    "Bot_Diameter": 11.0,     # Wider bottom
    "A_Top_Height": 2.0,
    "A_Mid_Height": 2.0,
    "A_Bot_Height": 1.0,
    "B_Top_Height": 1.0,
    "B_Mid_Height": 3.0,
    "B_Bot_Height": 1.5,
    "A_Top_Style": 2,         # Rounded
    "B_Bot_Style": 3,         # Tapered+Skirt
    # No knurling
}


def main():
    import mathutils
    bpy.mathutils = mathutils

    output_dir = ROOT / "projects" / "output" / "neve_styles"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Neve-Style Knob Renders")
    print("=" * 60)

    setup_scene()

    # All Neve knob configurations
    configs = [
        ("neve_01_large_fine", "Large - Fine Knurling (60 grooves)", NEVE_LARGE_FINE_KNURL),
        ("neve_02_medium_coarse", "Medium - Coarse Knurling (30 grooves)", NEVE_MEDIUM_COARSE_KNURL),
        ("neve_03_small_fine", "Small - Fine Knurling (50 grooves)", NEVE_SMALL_FINE_KNURL),
        ("neve_04_push_button", "Push-Button Style", NEVE_PUSH_BUTTON),
        ("neve_05_large_smooth", "Large - Smooth (no knurling)", NEVE_LARGE_SMOOTH),
        ("neve_06_medium_smooth", "Medium - Smooth (no knurling)", NEVE_MEDIUM_SMOOTH),
        ("neve_07_small_push", "Small Push-Button", NEVE_SMALL_PUSH),
        ("neve_08_tiny_smooth", "Tiny - Smooth (no knurling)", NEVE_TINY_SMOOTH),
    ]

    for i, (name, description, settings) in enumerate(configs):
        print(f"\n[{i+1}/{len(configs)}] {name}")
        print(f"    {description}")

        # Delete previous knob
        for obj in list(bpy.data.objects):
            if obj.type == 'MESH' or obj.type == 'EMPTY':
                bpy.data.objects.remove(obj, do_unlink=True)

        # Create new knob
        create_knob(name, settings)

        # Render multiple views
        views = [
            ("front", 0, 20),
            ("angle", 45, 25),
            ("top", 0, 70),
        ]

        for view_name, azimuth, elevation in views:
            output_path = str(output_dir / f"{name}_{view_name}.png")
            render_view(output_path, azimuth, elevation)

        print(f"    Rendered {len(views)} views")

    print("\n" + "=" * 60)
    print(f"Renders saved to: {output_dir}")
    print("=" * 60)

    # Save blend file
    blend_path = str(output_dir / "neve_styles.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Blend file: {blend_path}")


if __name__ == "__main__":
    main()
