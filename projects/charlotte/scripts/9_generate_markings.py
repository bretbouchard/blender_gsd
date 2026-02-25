"""
Charlotte Digital Twin - Complete Road Markings Generation

Generates all road markings:
- Center lines (yellow double solid)
- Lane dividers (white dashed)
- Edge lines (white solid)
- Crosswalks (zebra stripes)
- Stop lines (white solid)
- Street lights
- Manholes
"""

import bpy
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.road_markings_geo_nodes import (
    generate_all_road_markings,
    create_road_marking_assets,
    generate_stop_lines_at_intersections,
)
from lib.crosswalk_generator import generate_all_crosswalks


def main():
    """Generate all road markings for Charlotte."""
    print("\n" + "=" * 60)
    print("Charlotte Road Markings Generation")
    print("=" * 60)

    # 1. Create marking assets
    print("\n[1/5] Creating marking mesh assets...")
    create_road_marking_assets()

    # 2. Generate lane markings (center, edge, dividers, manholes, street lights)
    print("\n[2/5] Generating lane markings, manholes, and street lights...")
    marking_count = generate_all_road_markings()

    # 3. Generate crosswalks at intersections
    print("\n[3/5] Generating crosswalks...")
    crosswalks = generate_all_crosswalks()

    # 4. Generate stop lines (requires intersection data)
    print("\n[4/5] Generating stop lines...")
    stop_lines = generate_stop_lines_for_scene()

    # 5. Organize collections
    print("\n[5/5] Organizing collections...")
    organize_collections()

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Markings generated: {marking_count}")
    print(f"  Crosswalks: {len(crosswalks)}")
    print(f"  Stop lines: {len(stop_lines)}")
    print("=" * 60)

    # Save
    output_path = 'output/charlotte_with_markings.blend'
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"\nSaved to {output_path}")


def generate_stop_lines_for_scene():
    """Generate stop lines based on intersection detection."""
    # Get crosswalk positions as intersection indicators
    crosswalks = [
        obj for obj in bpy.context.scene.objects
        if obj.get('marking_type') == 'crosswalk'
    ]

    intersections = []
    for cw in crosswalks:
        pos = cw.location
        width = cw.get('road_width', 10.0)
        # Approximate direction from crosswalk rotation
        import math
        rot = cw.rotation_euler[2]
        direction = (math.sin(rot), math.cos(rot), 0)

        intersections.append({
            'position': bpy.mathutils.Vector(pos),
            'road_width': width,
            'direction': bpy.mathutils.Vector(direction),
        })

    # Generate stop lines
    stop_lines = generate_stop_lines_at_intersections(intersections)

    # Add to scene
    stop_coll = bpy.data.collections.get('Stop_Lines')
    for sl in stop_lines:
        bpy.context.scene.collection.objects.link(sl)
        if stop_coll:
            for c in sl.users_collection:
                c.objects.unlink(sl)
            stop_coll.objects.link(sl)

    return stop_lines


def organize_collections():
    """Organize all marking objects into proper collections."""

    # Ensure all sub-collections exist
    markings_coll = bpy.data.collections.get("Road_Markings")
    if not markings_coll:
        markings_coll = bpy.data.collections.new("Road_Markings")
        bpy.context.scene.collection.children.link(markings_coll)

    subcollections = [
        'Center_Lines',
        'Edge_Lines',
        'Lane_Dividers',
        'Crosswalks',
        'Stop_Lines',
        'Street_Lights',
        'Manholes',
    ]

    for name in subcollections:
        if name not in bpy.data.collections:
            coll = bpy.data.collections.new(name)
            markings_coll.children.link(coll)

    # Move objects to correct collections based on marking_type
    for obj in bpy.context.scene.objects:
        marking_type = obj.get('marking_type', '')
        if not marking_type:
            continue

        target_name = {
            'center_line': 'Center_Lines',
            'edge_line': 'Edge_Lines',
            'lane_divider': 'Lane_Dividers',
            'crosswalk': 'Crosswalks',
            'stop_line': 'Stop_Lines',
            'street_light': 'Street_Lights',
            'manhole': 'Manholes',
        }.get(marking_type)

        if target_name:
            target = bpy.data.collections.get(target_name)
            if target:
                for coll in list(obj.users_collection):
                    if coll != target:
                        coll.objects.unlink(obj)
                if obj not in target.objects.values():
                    target.objects.link(obj)


if __name__ == '__main__':
    main()
