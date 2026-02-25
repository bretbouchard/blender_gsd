"""
MSG-1998 Other Ground Categorization

Categorizes items in other_ground collection by likely type based on dimensions.
Then identifies buildings vs parks vs other features.
"""

import bpy
from mathutils import Vector

def get_other_ground_collection():
    """Get the other_ground collection."""
    if "other_ground" in bpy.data.collections:
        return bpy.data.collections["other_ground"]
    return None

def categorize_by_dimensions():
    """Categorize items by their dimensions to identify likely types."""

    print("\n" + "=" * 80)
    print("MSG-1998 Other Ground Categorization by Dimensions")
    print("=" * 80)

    coll = get_other_ground_collection()
    if not coll:
        print("ERROR: other_ground collection not found!")
        return

    items = [obj for obj in coll.objects if obj.type == 'MESH']

    # Categories
    flat_ground = []      # Height ~0m - parks, plazas, parking lots
    low_rise = []         # Height 1-10m - small structures, single story
    mid_rise = []         # Height 10-50m - typical buildings
    high_rise = []        # Height 50-100m - tall buildings
    skyscrapers = []      # Height 100m+ - very tall buildings
    unknown_20m = []      # Height exactly 20m - default/unknown

    for obj in items:
        bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        height = max(v.z for v in bbox) - min(v.z for v in bbox)
        width = max(v.x for v in bbox) - min(v.x for v in bbox)
        depth = max(v.y for v in bbox) - min(v.y for v in bbox)
        area = width * depth

        item = {
            'name': obj.name,
            'height': height,
            'width': width,
            'depth': depth,
            'area': area,
            'obj': obj
        }

        if height < 0.5:
            flat_ground.append(item)
        elif height < 10:
            low_rise.append(item)
        elif height < 50:
            mid_rise.append(item)
        elif height < 100:
            high_rise.append(item)
        elif height >= 100:
            skyscrapers.append(item)

        if abs(height - 20.0) < 0.1:
            unknown_20m.append(item)

    # Print categorization
    print(f"\nTotal items: {len(items)}")

    print("\n" + "-" * 80)
    print(f"FLAT GROUND (height < 0.5m) - {len(flat_ground)} items")
    print("Likely: Parks, plazas, parking lots, sidewalks")
    print("-" * 80)
    for item in sorted(flat_ground, key=lambda x: -x['area'])[:30]:
        print(f"  {item['name']:<20} H:{item['height']:>6.1f}m  Area:{item['area']:>8.0f}m²")
    if len(flat_ground) > 30:
        print(f"  ... and {len(flat_ground) - 30} more")

    print("\n" + "-" * 80)
    print(f"LOW-RISE (height 0.5-10m) - {len(low_rise)} items")
    print("Likely: Small structures, single-story buildings, kiosks")
    print("-" * 80)
    for item in sorted(low_rise, key=lambda x: -x['area']):
        print(f"  {item['name']:<20} H:{item['height']:>6.1f}m  W:{item['width']:>6.1f}m  D:{item['depth']:>6.1f}m")

    print("\n" + "-" * 80)
    print(f"MID-RISE (height 10-50m) - {len(mid_rise)} items")
    print("Likely: Typical buildings, 3-15 stories")
    print("-" * 80)
    for item in sorted(mid_rise, key=lambda x: -x['height']):
        print(f"  {item['name']:<20} H:{item['height']:>6.1f}m  W:{item['width']:>6.1f}m  D:{item['depth']:>6.1f}m")

    print("\n" + "-" * 80)
    print(f"HIGH-RISE (height 50-100m) - {len(high_rise)} items")
    print("Likely: Tall buildings, 15-30 stories")
    print("-" * 80)
    for item in sorted(high_rise, key=lambda x: -x['height']):
        print(f"  {item['name']:<20} H:{item['height']:>6.1f}m  W:{item['width']:>6.1f}m  D:{item['depth']:>6.1f}m")

    print("\n" + "-" * 80)
    print(f"SKYSCRAPERS (height 100m+) - {len(skyscrapers)} items")
    print("Likely: Major towers, 30+ stories")
    print("-" * 80)
    for item in sorted(skyscrapers, key=lambda x: -x['height']):
        print(f"  {item['name']:<20} H:{item['height']:>6.1f}m  W:{item['width']:>6.1f}m  D:{item['depth']:>6.1f}m")

    print("\n" + "-" * 80)
    print(f"DEFAULT HEIGHT (exactly 20m) - {len(unknown_20m)} items")
    print("These have default height and may need correction")
    print("-" * 80)
    for item in sorted(unknown_20m, key=lambda x: -x['area']):
        print(f"  {item['name']:<20} W:{item['width']:>6.1f}m  D:{item['depth']:>6.1f}m  Area:{item['area']:>8.0f}m²")

    # Get locations for tall buildings to help identify them
    print("\n" + "-" * 80)
    print("TALL BUILDING LOCATIONS (for identification)")
    print("-" * 80)
    tall_items = high_rise + skyscrapers
    for item in sorted(tall_items, key=lambda x: -x['height']):
        obj = item['obj']
        loc = obj.location
        print(f"  {item['name']:<20} H:{item['height']:>6.1f}m  Location: ({loc.x:.0f}, {loc.y:.0f})")

    return {
        'flat_ground': flat_ground,
        'low_rise': low_rise,
        'mid_rise': mid_rise,
        'high_rise': high_rise,
        'skyscrapers': skyscrapers,
        'unknown_20m': unknown_20m
    }


if __name__ == "__main__":
    categorize_by_dimensions()
