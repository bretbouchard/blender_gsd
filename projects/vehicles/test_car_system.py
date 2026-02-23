"""
Test Script: Procedural Car Fleet with Style Control

Demonstrates the full procedural car system:
- Creating cars with different styles
- Setting colors
- Generating fleets
- Making them launch-control compatible

Run in Blender:
    blender --background --python test_car_system.py

Or in Blender's Script Editor:
    exec(open("test_car_system.py").read())
"""
import bpy
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "lib"))

from animation.vehicle.procedural_car import (
    ProceduralCarFactory,
    create_car,
    create_fleet,
    STYLE_PRESETS,
    COLOR_PRESETS
)


def test_single_car():
    """Test creating a single styled car."""
    print("\n" + "=" * 60)
    print("TEST 1: Creating Single Car")
    print("=" * 60)

    factory = ProceduralCarFactory()

    # Create a red sports car
    car = factory.create_car(
        name="SportsCar_Red",
        style="sports",
        color="red",
        seed=42,
        position=(0, 0, 0)
    )

    print(f"Created: {car.name}")
    print(f"Style: sports")
    print(f"Color: red")

    # Check modifier
    for mod in car.modifiers:
        if mod.type == 'NODES':
            print(f"Geometry Nodes: {mod.node_group.name if mod.node_group else 'None'}")
            # Print input values
            if mod.node_group:
                print("Inputs set:")
                ng = mod.node_group
                for item in ng.interface.items_tree:
                    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                        try:
                            val = mod[item.name]
                            print(f"  {item.name}: {val}")
                        except:
                            pass

    return car


def test_multiple_styles():
    """Test creating cars with different styles."""
    print("\n" + "=" * 60)
    print("TEST 2: Multiple Style Variations")
    print("=" * 60)

    factory = ProceduralCarFactory()
    styles = ["economy", "sedan", "sports", "suv", "pickup", "muscle", "hatchback"]

    cars = []
    for i, style in enumerate(styles):
        car = factory.create_car(
            name=f"Car_{style}",
            style=style,
            color=list(COLOR_PRESETS.keys())[i % len(COLOR_PRESETS)],
            seed=i * 1000,
            position=(i * 6, 0, 0)
        )
        cars.append(car)
        print(f"  Created: {style} car in {list(COLOR_PRESETS.keys())[i % len(COLOR_PRESETS)]}")

    return cars


def test_color_variations():
    """Test creating cars with different colors."""
    print("\n" + "=" * 60)
    print("TEST 3: Color Variations (same style)")
    print("=" * 60)

    factory = ProceduralCarFactory()
    colors = list(COLOR_PRESETS.keys())

    cars = []
    for i, color in enumerate(colors):
        car = factory.create_car(
            name=f"Sedan_{color}",
            style="sedan",
            color=color,
            seed=100,
            position=(0, i * 4, 0)
        )
        cars.append(car)
        print(f"  Created: sedan in {color}")

    return cars


def test_fleet_generation():
    """Test generating a fleet of varied cars."""
    print("\n" + "=" * 60)
    print("TEST 4: Fleet Generation")
    print("=" * 60)

    fleet = create_fleet(
        count=10,
        styles=["sedan", "sports", "suv"],
        colors=["red", "blue", "silver", "black"],
        spacing=5.0,
        seed=12345
    )

    print(f"Created fleet of {len(fleet)} cars")
    for car in fleet:
        print(f"  {car.name}")

    return fleet


def test_launch_compatibility():
    """Test that cars are launch-control compatible."""
    print("\n" + "=" * 60)
    print("TEST 5: Launch Control Compatibility")
    print("=" * 60)

    factory = ProceduralCarFactory()
    car = factory.create_car(
        name="LaunchTestCar",
        style="sports",
        color="red",
        position=(0, 0, 0)
    )

    # Check launch compatibility properties
    print(f"Launch compatible: {car.get('launch_compatible', False)}")
    print(f"Wheel radius: {car.get('wheel_radius', 'not set')}")
    print(f"Wheelbase: {car.get('wheelbase', 'not set')}")
    print(f"Track width: {car.get('track_width', 'not set')}")

    # Check wheel pivots exist
    wheel_pivots = [obj for obj in car.children if "wheel" in obj.name.lower()]
    print(f"Wheel pivots: {len(wheel_pivots)}")
    for pivot in wheel_pivots:
        print(f"  {pivot.name} at {pivot.location}")

    return car


def main():
    """Run all tests."""
    print("=" * 60)
    print("PROCEDURAL CAR SYSTEM - TEST SUITE")
    print("=" * 60)

    # Clear scene first
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Run tests
    test_single_car()
    test_multiple_styles()
    test_color_variations()
    test_fleet_generation()
    test_launch_compatibility()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)

    # Summary
    car_count = len([o for o in bpy.data.objects if o.type == 'MESH' and 'Car' in o.name or 'car' in o.name.lower()])
    print(f"Total cars in scene: {car_count}")

    # Save test file
    output_path = "//car_test_output.blend"
    bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath(output_path))
    print(f"\nSaved test file: {output_path}")


if __name__ == "__main__":
    main()
