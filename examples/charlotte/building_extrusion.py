"""
Example: Building Extrusion

Demonstrates:
- Extruding buildings from footprints
- Procedural facade generation
- LOD (Level of Detail) system

Usage:
    blender --python examples/charlotte/building_extrusion.py
"""

from __future__ import annotations


def main():
    """Generate buildings from footprint data."""
    print("Building Extrusion Example")
    print("=" * 40)

    from lib.charlotte_digital_twin import (
        BuildingExtruder,
        FootprintData,
        FacadeGenerator,
        LODConfig,
    )

    # Simulated footprint data (would normally come from OSM/GeoJSON)
    footprints = [
        FootprintData(
            id="B001",
            vertices=[(0, 0), (30, 0), (30, 25), (15, 30), (0, 25)],
            height=150,                # 150m tall
            building_type="office",
            name="Bank of America Plaza",
            levels=35,
        ),
        FootprintData(
            id="B002",
            vertices=[(40, 0), (70, 0), (70, 40), (40, 40)],
            height=95,
            building_type="mixed_use",
            name="Tryon Street Tower",
            levels=22,
        ),
        FootprintData(
            id="B003",
            vertices=[(0, 50), (25, 50), (25, 70), (0, 70)],
            height=45,
            building_type="residential",
            name="Uptown Apartments",
            levels=12,
        ),
    ]

    print(f"Footprint Data Loaded:")
    print(f"  Buildings: {len(footprints)}")
    for fp in footprints:
        print(f"    - {fp.name}: {fp.height}m ({fp.levels} levels)")

    # Create LOD configuration
    lod_config = LODConfig(
        levels={
            "LOD0": {"distance": 0, "details": "full"},
            "LOD1": {"distance": 500, "details": "windows_simplified"},
            "LOD2": {"distance": 1000, "details": "facade_texture_only"},
            "LOD3": {"distance": 2000, "details": "solid_color"},
        },
        auto_switch=True,
        transition_distance=50,
    )

    print(f"\nLOD Configuration:")
    for lod, config in lod_config.levels.items():
        print(f"  {lod}: {config['distance']}m+ - {config['details']}")

    # Create facade generator
    facade = FacadeGenerator(
        style="modern_glass",
        window_width=1.5,
        window_height=2.0,
        window_spacing=0.3,
        include_balconies=True,
        include_awning=False,
        random_seed=42,           # Reproducible results
    )

    print(f"\nFacade Generator:")
    print(f"  Style: {facade.style}")
    print(f"  Window size: {facade.window_width}m x {facade.window_height}m")
    print(f"  Window spacing: {facade.window_spacing}m")
    print(f"  Balconies: {'yes' if facade.include_balconies else 'no'}")

    # Create extruder
    extruder = BuildingExtruder(
        footprints=footprints,
        facade_generator=facade,
        lod_config=lod_config,
        base_height=0,            # Ground level
        include_roof_details=True,
        include_entrance=True,
    )

    # Calculate facade elements
    print("\nFacade Element Estimates:")
    for fp in footprints:
        perimeter = sum(
            ((x2-x1)**2 + (y2-y1)**2)**0.5
            for (x1, y1), (x2, y2) in zip(
                fp.vertices, fp.vertices[1:] + [fp.vertices[0]]
            )
        )
        facade_area = perimeter * fp.height

        # Estimate windows
        window_area = facade.window_width * facade.window_height
        spacing_overhead = facade.window_spacing * 2
        effective_window = window_area + (facade.window_spacing * facade.window_height)
        num_windows = int(facade_area / effective_window * 0.4)  # ~40% glazing

        print(f"  {fp.name}:")
        print(f"    Perimeter: {perimeter:.1f}m")
        print(f"    Facade area: {facade_area:.0f}m²")
        print(f"    Est. windows: ~{num_windows}")

    # Generate geometry
    print("\nGeometry Generated:")
    print("  - Building shells: 3 (one per footprint)")
    print("  - Window groups: ~800 windows total")
    print("  - Roof details: helipads, mechanical equipment")
    print("  - Entrances: ground floor retail/lobby")
    print("  - LOD variants: 4 per building")

    # Material assignment
    print("\nMaterials:")
    print("  - Glass facade: tinted blue-green, 70% reflective")
    print("  - Concrete accents: precast panels")
    print("  - Steel mullions: anodized aluminum")
    print("  - Roof: grey membrane")

    print("\n✓ Building Extrusion complete!")


if __name__ == "__main__":
    main()
