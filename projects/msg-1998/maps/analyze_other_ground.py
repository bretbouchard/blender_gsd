"""
MSG-1998 Other Ground Collection Analysis

Analyzes all items in the "Other Ground" collection to identify what they are
and determine appropriate heights.
"""

import bpy
from mathutils import Vector

def get_other_ground_collection():
    """Get the other_ground collection."""
    if "other_ground" in bpy.data.collections:
        return bpy.data.collections["other_ground"]
    # Fallback - look for similar names
    for c in bpy.data.collections:
        if 'ground' in c.name.lower() or 'other' in c.name.lower():
            print(f"Found matching collection: '{c.name}'")
            return c
    return None

def analyze_other_ground():
    """Analyze all items in Other Ground collection."""

    print("\n" + "=" * 80)
    print("MSG-1998 Other Ground Collection Analysis")
    print("=" * 80)

    coll = get_other_ground_collection()
    if not coll:
        print("ERROR: Other Ground collection not found!")
        print("\nAvailable collections:")
        for c in bpy.data.collections:
            print(f"  - {c.name}")
        return

    items = list(coll.objects)
    print(f"\nFound {len(items)} objects in Other Ground collection")

    # Categorize by current height
    by_height = {}
    for obj in items:
        if obj.type == 'MESH':
            bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            height = max(v.z for v in bbox) - min(v.z for v in bbox)
            width = max(v.x for v in bbox) - min(v.x for v in bbox)
            depth = max(v.y for v in bbox) - min(v.y for v in bbox)

            height_key = round(height, 1)
            if height_key not in by_height:
                by_height[height_key] = []
            by_height[height_key].append({
                'name': obj.name,
                'height': height,
                'width': width,
                'depth': depth,
                'obj': obj
            })

    print("\n" + "-" * 80)
    print("Items grouped by current height:")
    print("-" * 80)

    for height in sorted(by_height.keys()):
        items_at_height = by_height[height]
        print(f"\nHeight: {height}m ({len(items_at_height)} items)")
        for item in sorted(items_at_height, key=lambda x: x['name']):
            print(f"  {item['name'][:60]:<60} W:{item['width']:>6.1f}m D:{item['depth']:>6.1f}m")

    # List all items with details
    print("\n" + "-" * 80)
    print("Complete item list with dimensions:")
    print("-" * 80)
    print(f"{'Name':<55} {'Height':>8} {'Width':>8} {'Depth':>8}")
    print("-" * 80)

    for obj in sorted(items, key=lambda x: x.name):
        if obj.type == 'MESH':
            bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            height = max(v.z for v in bbox) - min(v.z for v in bbox)
            width = max(v.x for v in bbox) - min(v.x for v in bbox)
            depth = max(v.y for v in bbox) - min(v.y for v in bbox)
            print(f"{obj.name[:55]:<55} {height:>8.1f}m {width:>8.1f}m {depth:>8.1f}m")
        else:
            print(f"{obj.name[:55]:<55} [Type: {obj.type}]")

    print("\n" + "=" * 80)
    print("Analysis complete. Review items above to determine what each is.")
    print("=" * 80)

    return by_height


if __name__ == "__main__":
    analyze_other_ground()
