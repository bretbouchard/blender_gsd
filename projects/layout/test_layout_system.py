"""
Test Layout System - Demonstrate the console layout system.

Creates:
1. Neve 1073 style channel strip
2. 8-channel console (row of strips)
3. 808-style drum machine layout
4. 1176-style compressor
"""

import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.layout import (
    # Standards
    ElementSize, KNOB_SIZES, BUTTON_SIZES, DEFAULT_GRID,
    ConsoleType, CONSOLE_CONFIGS,

    # Panel
    PanelLayout, ElementSpec, ElementType,
    ChannelStripBuilder, DrumMachineBuilder, CompressorBuilder,

    # Preset layouts
    create_neve_1073_channel, create_808_drum_machine, create_1176_compressor,

    # Renderer
    LayoutRenderer, BatchRenderer, render_layout, render_console_row,
)


def clear_scene():
    """Clear all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Also clear orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.node_groups:
        if block.users == 0:
            bpy.data.node_groups.remove(block)


def setup_scene():
    """Set up the scene for rendering."""
    # Camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Position camera to see the console
    cam_obj.location = (0.3, -0.5, 0.3)
    cam_obj.rotation_euler = (1.1, 0, 0.2)

    # Lighting
    light_data = bpy.data.lights.new("KeyLight", type='SUN')
    light_data.energy = 3.0
    light_obj = bpy.data.objects.new("KeyLight", light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.location = (0.5, -1, 1)
    light_obj.rotation_euler = (0.8, 0.2, 0.5)

    # Render settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.cycles.samples = 64


def test_single_channel_strip():
    """Test rendering a single Neve 1073 style channel strip."""
    print("\n[1/4] Creating single channel strip...")

    # Create layout using builder
    layout = create_neve_1073_channel()

    # Render
    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    print(f"    Created {len(objects)} objects")
    return layout


def test_8channel_console():
    """Test rendering an 8-channel console."""
    print("\n[2/4] Creating 8-channel console...")

    # Create base layout
    layout = create_neve_1073_channel()

    # Render 8 channels in a row
    batch = BatchRenderer("8_Channel_Console")
    batch.add_layout_row(layout, count=8)

    objects = batch.render()

    print(f"    Created {len(objects)} objects")
    return layout


def test_drum_machine():
    """Test rendering an 808-style drum machine."""
    print("\n[3/4] Creating drum machine layout...")

    layout = create_808_drum_machine()

    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    # Offset for visibility
    for obj in objects:
        obj.location.y += 0.5

    print(f"    Created {len(objects)} objects")
    return layout


def test_compressor():
    """Test rendering an 1176-style compressor."""
    print("\n[4/4] Creating compressor layout...")

    layout = create_1176_compressor()

    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    # Offset for visibility
    for obj in objects:
        obj.location.y += 1.0

    print(f"    Created {len(objects)} objects")
    return layout


def test_custom_layout():
    """Test creating a custom layout from scratch."""
    print("\n[BONUS] Creating custom layout...")

    # Create a custom layout
    layout = PanelLayout(
        name="Custom Console",
        width=200.0,
        height=100.0,
        console_type=ConsoleType.MIXING_CONSOLE,
        default_knob_size=ElementSize.MD,
        default_button_size=ElementSize.SM,
    )

    # Add a row of 4 knobs
    layout.add_knob_row(
        names=["Volume", "Pan", "Send_A", "Send_B"],
        y=20.0,
        labels=["Vol", "Pan", "A", "B"]
    )

    # Add a row of buttons
    layout.add_button_row(
        names=["Mute", "Solo", "Select", "Record"],
        y=50.0,
        styles=[0, 0, 0, 3]  # Style 3 = illuminated for Record
    )

    # Add a single fader
    layout.add_element(ElementSpec(
        element_type=ElementType.FADER,
        name="Main_Fader",
        x=100.0,
        y=80.0,
        size=ElementSize.LG,
        value=0.75
    ))

    renderer = LayoutRenderer(layout)
    objects = renderer.render()

    # Offset for visibility
    for obj in objects:
        obj.location.y += 1.5

    print(f"    Created {len(objects)} objects")
    return layout


def main():
    """Main test function."""
    print("=" * 60)
    print("Console Layout System - Test Render")
    print("=" * 60)

    # Clear and setup
    clear_scene()
    setup_scene()

    # Run tests
    test_single_channel_strip()
    test_8channel_console()
    test_drum_machine()
    test_compressor()
    test_custom_layout()

    # Save blend file
    output_dir = ROOT / "projects" / "output" / "layout_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "layout_test.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    print("\n" + "=" * 60)
    print(f"Output: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
