"""
Charlotte Digital Twin - Simple Rooftop Units via Python

Creates actual rooftop unit meshes on building tops.
This is a Python-based approach that works reliably without complex Geo Nodes.

The script:
1. Finds all buildings above a height threshold
2. Creates random HVAC units on their rooftops
3. Groups them by building for easy management
"""

import bpy
import bmesh
import random
import math
from pathlib import Path
from typing import List, Dict
from mathutils import Vector


def create_hvac_unit_mesh(width: float, depth: float, height: float) -> bpy.types.Mesh:
    """Create a simple HVAC box unit mesh."""
    mesh = bpy.data.meshes.new("HVAC_Unit_Mesh")

    bm = bmesh.new()

    # Create box
    bmesh.ops.create_cube(bm, size=1.0)

    # Scale to dimensions
    for v in bm.verts:
        v.co.x *= width / 2
        v.co.y *= depth / 2
        v.co.z *= height / 2

    bm.to_mesh(mesh)
    bm.free()

    return mesh


def create_cooling_tower_mesh(diameter: float, height: float) -> bpy.types.Mesh:
    """Create a cylindrical cooling tower mesh."""
    mesh = bpy.data.meshes.new("Cooling_Tower_Mesh")

    bm = bmesh.new()

    # Create cylinder (8 segments is enough for low-poly)
    bmesh.ops.create_cone(
        bm,
        segments=8,
        radius1=diameter / 2,
        radius2=diameter / 2,
        depth=height,
    )

    bm.to_mesh(mesh)
    bm.free()

    return mesh


def get_building_bbox(obj: bpy.types.Object) -> Dict:
    """Get world-space bounding box of a building."""
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    return {
        'min_x': min(v.x for v in bbox),
        'max_x': max(v.x for v in bbox),
        'min_y': min(v.y for v in bbox),
        'max_y': max(v.y for v in bbox),
        'min_z': min(v.z for v in bbox),
        'max_z': max(v.z for v in bbox),
        'center_x': sum(v.x for v in bbox) / 8,
        'center_y': sum(v.y for v in bbox) / 8,
        'width': max(v.x for v in bbox) - min(v.x for v in bbox),
        'depth': max(v.y for v in bbox) - min(v.y for v in bbox),
        'height': max(v.z for v in bbox) - min(v.z for v in bbox),
    }


def add_rooftop_units_to_building(
    obj: bpy.types.Object,
    num_units: int = None,
    seed: int = None,
    min_clearance: float = 2.0
) -> List[bpy.types.Object]:
    """
    Add rooftop HVAC units to a building.

    Args:
        obj: Building object
        num_units: Number of units (None for auto based on roof size)
        seed: Random seed for reproducibility
        min_clearance: Minimum space between units

    Returns:
        List of created unit objects
    """
    if seed is not None:
        random.seed(seed)

    # Get building bounds
    bbox = get_building_bbox(obj)
    rooftop_z = bbox['max_z']
    roof_width = bbox['width']
    roof_depth = bbox['depth']

    # Auto-calculate number of units based on roof area
    if num_units is None:
        roof_area = roof_width * roof_depth
        # One unit per ~100 sq meters, max 6
        num_units = min(6, max(1, int(roof_area / 100)))

    created_units = []

    # Calculate available space
    usable_width = roof_width - min_clearance * 2
    usable_depth = roof_depth - min_clearance * 2

    if usable_width < 1 or usable_depth < 1:
        return []  # Roof too small

    # Generate unit positions using grid-based placement
    for i in range(num_units):
        # Random unit type (80% box, 20% cylinder)
        if random.random() < 0.8:
            # Box HVAC unit
            unit_width = random.uniform(1.5, 3.0)
            unit_depth = random.uniform(1.5, 2.5)
            unit_height = random.uniform(1.0, 2.0)

            mesh = create_hvac_unit_mesh(unit_width, unit_depth, unit_height)
            unit_name = f"HVAC_{obj.name}_{i}"
        else:
            # Cooling tower
            diameter = random.uniform(2.0, 3.0)
            unit_height = random.uniform(3.0, 5.0)

            mesh = create_cooling_tower_mesh(diameter, unit_height)
            unit_width = diameter
            unit_depth = diameter
            unit_name = f"CoolingTower_{obj.name}_{i}"

        # Create object
        unit_obj = bpy.data.objects.new(unit_name, mesh)

        # Position on rooftop
        # Use grid-based placement to avoid overlaps
        grid_cols = max(1, int(math.sqrt(num_units)))
        grid_rows = max(1, (num_units + grid_cols - 1) // grid_cols)

        col = i % grid_cols
        row = i // grid_cols

        cell_width = usable_width / grid_cols
        cell_depth = usable_depth / grid_rows

        x = bbox['min_x'] + min_clearance + cell_width * (col + 0.5)
        y = bbox['min_y'] + min_clearance + cell_depth * (row + 0.5)

        # Add some randomness within cell
        x += random.uniform(-cell_width * 0.2, cell_width * 0.2)
        y += random.uniform(-cell_depth * 0.2, cell_depth * 0.2)

        unit_obj.location = (x, y, rooftop_z + unit_height / 2)

        # Random rotation
        unit_obj.rotation_euler.z = random.uniform(0, math.pi * 2)

        # Add to scene
        bpy.context.scene.collection.objects.link(unit_obj)

        # Add metadata
        unit_obj['is_rooftop_unit'] = True
        unit_obj['parent_building'] = obj.name
        unit_obj['unit_type'] = 'hvac_box' if 'HVAC' in unit_name else 'cooling_tower'

        created_units.append(unit_obj)

    return created_units


def add_rooftop_units_to_all_buildings(
    min_height: float = 30.0,
    seed: int = 42
):
    """
    Add rooftop units to all qualifying buildings.

    Args:
        min_height: Minimum building height in meters
        seed: Random seed for reproducibility
    """
    print("\n" + "=" * 60)
    print("ADDING ROOFTOP UNITS TO BUILDINGS")
    print("=" * 60)

    random.seed(seed)

    # Find all building objects
    buildings = []
    for obj in bpy.context.scene.objects:
        if obj.get('building_type') or obj.get('osm_id'):
            height = obj.get('height', 0)
            if height >= min_height:
                buildings.append(obj)

    print(f"\nFound {len(buildings)} buildings taller than {min_height}m")

    # Create collection for rooftop units
    units_coll = bpy.data.collections.get("Rooftop_Units")
    if not units_coll:
        units_coll = bpy.data.collections.new("Rooftop_Units")
        bpy.context.scene.collection.children.link(units_coll)

    total_units = 0

    for i, building in enumerate(buildings):
        # Use building name hash as seed for reproducibility per building
        building_seed = hash(building.name) % 10000 + seed

        units = add_rooftop_units_to_building(
            building,
            seed=building_seed,
        )

        # Move units to collection
        for unit in units:
            for c in unit.users_collection:
                c.objects.unlink(unit)
            units_coll.objects.link(unit)

            # Parent to building (optional, helps with organization)
            unit.parent = building

        total_units += len(units)

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(buildings)} buildings...")

    print(f"\n✓ Created {total_units} rooftop units on {len(buildings)} buildings")

    return total_units


def clear_rooftop_units():
    """Remove all rooftop units from the scene."""
    print("\nClearing existing rooftop units...")

    count = 0
    for obj in bpy.data.objects:
        if obj.get('is_rooftop_unit'):
            bpy.data.objects.remove(obj, do_unlink=True)
            count += 1

    # Remove collection if empty
    coll = bpy.data.collections.get("Rooftop_Units")
    if coll and len(coll.objects) == 0:
        bpy.data.collections.remove(coll)

    print(f"Removed {count} rooftop units")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Add rooftop units to buildings')
    parser.add_argument('--min-height', type=float, default=30.0,
                        help='Minimum building height (default: 30m)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    parser.add_argument('--clear', action='store_true',
                        help='Clear existing units first')

    args = parser.parse_args()

    if args.clear:
        clear_rooftop_units()

    add_rooftop_units_to_all_buildings(
        min_height=args.min_height,
        seed=args.seed,
    )

    print("\nDone!")


if __name__ == '__main__':
    main()
