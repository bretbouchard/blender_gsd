"""
Test script for Universal Input System

Creates test knobs using the new zone-based system.
"""

import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.inputs import build_input, list_presets, get_preset, InputConfig


def clear_scene():
    """Clear all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def test_input_system():
    """Test the universal input system."""

    clear_scene()

    # Create a collection for test inputs
    collection = bpy.data.collections.new("TestInputs")
    bpy.context.scene.collection.children.link(collection)

    # List available presets
    print("Available presets:", list_presets())

    # === TEST 1: Build from preset ===
    print("\n=== Building Neve 1073 preset ===")
    try:
        obj1 = build_input(
            preset="knob_neve_1073",
            collection=collection,
            object_name="Neve1073"
        )
        obj1.location = (-0.05, 0, 0)
        print(f"Created: {obj1.name}")
    except Exception as e:
        print(f"Error: {e}")

    # === TEST 2: Build with overrides ===
    print("\n=== Building MXR preset with overrides ===")
    try:
        obj2 = build_input(
            preset="knob_mxr_style",
            collection=collection,
            overrides={
                "material.base_color": [1.0, 0.3, 0.3],  # Red
            },
            object_name="MXR_Red"
        )
        obj2.location = (0, 0, 0)
        print(f"Created: {obj2.name}")
    except Exception as e:
        print(f"Error: {e}")

    # === TEST 3: Build SSL preset ===
    print("\n=== Building SSL 4000 preset ===")
    try:
        obj3 = build_input(
            preset="knob_ssl_4000",
            collection=collection,
            object_name="SSL4000"
        )
        obj3.location = (0.05, 0, 0)
        print(f"Created: {obj3.name}")
    except Exception as e:
        print(f"Error: {e}")

    # === TEST 4: Build minimal test ===
    print("\n=== Building Minimal preset ===")
    try:
        obj4 = build_input(
            preset="knob_minimal",
            collection=collection,
            object_name="Minimal"
        )
        obj4.location = (0.10, 0, 0)
        print(f"Created: {obj4.name}")
    except Exception as e:
        print(f"Error: {e}")

    # Add a light
    light_data = bpy.data.lights.new("TestLight", "POINT")
    light_data.energy = 1000
    light = bpy.data.objects.new("TestLight", light_data)
    collection.objects.link(light)
    light.location = (0.05, -0.1, 0.15)

    # Save the file
    output_path = pathlib.Path(__file__).parent.parent / "output" / "test_input_system.blend"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"\nSaved to: {output_path}")

    return True


if __name__ == "__main__":
    test_input_system()
