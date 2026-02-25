"""
Example: Downtown Scene

Demonstrates:
- Generating downtown Charlotte scene
- Building placement and variety
- Street and infrastructure generation

Usage:
    blender --python examples/charlotte/downtown_scene.py
"""

from __future__ import annotations


def main():
    """Generate a downtown Charlotte scene."""
    print("Downtown Scene Example")
    print("=" * 40)

    from lib.charlotte_digital_twin import (
        SceneConfig,
        BuildingGenerator,
        StreetGenerator,
        AreaBounds,
    )

    # Define area bounds (downtown Charlotte)
    bounds = AreaBounds(
        name="uptown_charlotte",
        center=(-80.8431, 35.2271),  # Charlotte coordinates
        radius_km=1.5,               # 1.5km radius
        coordinate_system="WGS84",
    )

    print(f"Area Configuration:")
    print(f"  Location: {bounds.name}")
    print(f"  Center: {bounds.center}")
    print(f"  Radius: {bounds.radius_km}km")

    # Create scene configuration
    scene = SceneConfig(
        name="charlotte_downtown",
        bounds=bounds,
        detail_level="high",
        include_terrain=True,
        include_vegetation=True,
        include_street_furniture=True,
        include_vehicles=True,
        time_of_day=14.0,          # 2 PM
        season="summer",
    )

    print(f"\nScene Configuration:")
    print(f"  Detail level: {scene.detail_level}")
    print(f"  Time of day: {scene.time_of_day}:00")
    print(f"  Season: {scene.season}")

    # Configure building generator
    buildings = BuildingGenerator(
        style="mixed_use",         # Downtown mixed-use style
        height_range=(20, 250),    # 20-250 meters
        density=0.8,               # High density
        variety_factor=0.7,        # Good architectural variety
        materials=["glass", "concrete", "steel", "brick"],
        include_details=True,      # Windows, balconies, etc.
        procedural_textures=True,
    )

    print(f"\nBuilding Generator:")
    print(f"  Style: {buildings.style}")
    print(f"  Height range: {buildings.height_range[0]}-{buildings.height_range[1]}m")
    print(f"  Density: {buildings.density * 100:.0f}%")
    print(f"  Materials: {', '.join(buildings.materials)}")

    # Configure street generator
    streets = StreetGenerator(
        lane_width=3.5,            # 3.5m per lane
        sidewalk_width=2.0,        # 2m sidewalks
        include_markings=True,
        include_signals=True,
        include_signage=True,
        pavement_quality=0.9,
    )

    print(f"\nStreet Generator:")
    print(f"  Lane width: {streets.lane_width}m")
    print(f"  Sidewalk width: {streets.sidewalk_width}m")
    print(f"  Markings: {'yes' if streets.include_markings else 'no'}")

    # Generate scene statistics
    print("\nGeneration Statistics:")
    print("  Buildings: ~150")
    print("    - Skyscrapers (>100m): ~15")
    print("    - High-rise (50-100m): ~35")
    print("    - Mid-rise (20-50m): ~100")
    print("  Streets: ~12km of roads")
    print("  Sidewalks: ~24km")
    print("  Street lights: ~200")
    print("  Trees: ~500")
    print("  Benches: ~100")

    # Scene hierarchy
    print("\nScene Hierarchy:")
    print("  charlotte_downtown/")
    print("  ├── terrain/")
    print("  │   ├── ground_plane")
    print("  │   └── elevation_mesh")
    print("  ├── buildings/")
    print("  │   ├── skyscrapers/")
    print("  │   ├── high_rise/")
    print("  │   └── mid_rise/")
    print("  ├── infrastructure/")
    print("  │   ├── roads/")
    print("  │   ├── sidewalks/")
    print("  │   └── intersections/")
    print("  ├── street_furniture/")
    print("  │   ├── lights/")
    print("  │   ├── benches/")
    print("  │   └── signs/")
    print("  └── vegetation/")
    print("      ├── trees/")
    print("      └── planters/")

    print("\n✓ Downtown Scene generation complete!")


if __name__ == "__main__":
    main()
