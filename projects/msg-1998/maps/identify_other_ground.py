"""
MSG-1998 Other Ground - Identify and Apply Heights

These are unlabeled OpenStreetMap areas. We need to identify what they are
based on their dimensions and apply appropriate heights.

Strategy:
1. Flat ground items (0m) - Leave as is (parks, plazas, sidewalks)
2. Small items (3-4m wide, 20m height) - Likely street furniture/utility, reduce to actual height
3. Buildings - Apply reasonable heights based on size/category
"""

import bpy
from mathutils import Vector

def get_other_ground_collection():
    if "other_ground" in bpy.data.collections:
        return bpy.data.collections["other_ground"]
    return None

def get_world_center(obj):
    """Get the world-space center of an object."""
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    center = Vector((
        (max(v.x for v in bbox) + min(v.x for v in bbox)) / 2,
        (max(v.y for v in bbox) + min(v.y for v in bbox)) / 2,
        (max(v.z for v in bbox) + min(v.z for v in bbox)) / 2
    ))
    return center

def get_dimensions(obj):
    """Get object dimensions in world space."""
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    height = max(v.z for v in bbox) - min(v.z for v in bbox)
    width = max(v.x for v in bbox) - min(v.x for v in bbox)
    depth = max(v.y for v in bbox) - min(v.y for v in bbox)
    return height, width, depth

def apply_height(obj, target_height):
    """Scale object to target height."""
    current_height, width, depth = get_dimensions(obj)
    if current_height <= 0:
        return False

    scale_factor = target_height / current_height
    obj.scale.z *= scale_factor

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return True

def analyze_and_identify():
    """Analyze items and create identification report."""

    coll = get_other_ground_collection()
    if not coll:
        print("ERROR: other_ground collection not found!")
        return

    items = [obj for obj in coll.objects if obj.type == 'MESH']

    print("\n" + "=" * 80)
    print("MSG-1998 Other Ground - Identification Report")
    print("=" * 80)
    print(f"\nTotal items: {len(items)}")

    # Categorize
    flat_ground = []      # 0m - parks, plazas
    small_structures = [] # Small footprint, likely street furniture
    narrow_tall = []      # Narrow but tall - may be incorrect
    buildings = []        # Actual buildings

    for obj in items:
        height, width, depth = get_dimensions(obj)
        min_dim = min(width, depth)
        max_dim = max(width, depth)
        area = width * depth

        item = {
            'name': obj.name,
            'height': height,
            'width': width,
            'depth': depth,
            'area': area,
            'min_dim': min_dim,
            'max_dim': max_dim,
            'obj': obj
        }

        if height < 0.5:
            flat_ground.append(item)
        elif min_dim < 5 and height > 15:
            # Narrow but tall - likely incorrect or special structure
            narrow_tall.append(item)
        elif min_dim < 5 and height <= 15:
            # Small structure
            small_structures.append(item)
        else:
            buildings.append(item)

    print(f"\nCategories:")
    print(f"  Flat ground (0m height): {len(flat_ground)}")
    print(f"  Small structures (<5m wide, <=15m tall): {len(small_structures)}")
    print(f"  Narrow/tall (may be incorrect): {len(narrow_tall)}")
    print(f"  Buildings: {len(buildings)}")

    # Show narrow/tall items that may need correction
    if narrow_tall:
        print("\n" + "-" * 80)
        print("NARROW/TALL ITEMS (may need height correction)")
        print("-" * 80)
        for item in sorted(narrow_tall, key=lambda x: -x['height']):
            print(f"  {item['name']:<20} H:{item['height']:>6.1f}m  W:{item['width']:>5.1f}m  D:{item['depth']:>5.1f}m")
            print(f"    -> Likely street pole, antenna, or incorrect data")

    # Show buildings grouped by height
    print("\n" + "-" * 80)
    print("BUILDINGS BY HEIGHT CATEGORY")
    print("-" * 80)

    # Group buildings by height
    height_groups = {
        'tiny': (0, 15),
        'low': (15, 30),
        'mid': (30, 60),
        'high': (60, 100),
        'tall': (100, 200),
        'super': (200, 1000)
    }

    for group_name, (min_h, max_h) in height_groups.items():
        group_items = [i for i in buildings if min_h <= i['height'] < max_h]
        if group_items:
            print(f"\n{group_name.upper()} ({min_h}-{max_h}m) - {len(group_items)} items:")
            for item in sorted(group_items, key=lambda x: -x['height'])[:10]:
                print(f"  {item['name']:<20} H:{item['height']:>6.1f}m  Area:{item['area']:>8.0f}m²")
            if len(group_items) > 10:
                print(f"  ... and {len(group_items) - 10} more")

    return {
        'flat_ground': flat_ground,
        'small_structures': small_structures,
        'narrow_tall': narrow_tall,
        'buildings': buildings
    }


def apply_smart_heights():
    """Apply intelligent heights based on item category."""

    print("\n" + "=" * 80)
    print("Applying Smart Heights to Other Ground")
    print("=" * 80)

    coll = get_other_ground_collection()
    if not coll:
        print("ERROR: other_ground collection not found!")
        return

    items = [obj for obj in coll.objects if obj.type == 'MESH']

    fixed = 0
    skipped = 0

    for obj in items:
        height, width, depth = get_dimensions(obj)
        min_dim = min(width, depth)
        area = width * depth

        # Determine appropriate height
        target_height = None
        reason = ""

        # Flat ground - leave as is
        if height < 0.5:
            skipped += 1
            continue

        # Very small footprint with 20m height - likely street furniture
        if min_dim < 5 and abs(height - 20.0) < 0.1:
            if min_dim < 4:
                target_height = 4.0  # Street light/utility pole base
                reason = "small utility"
            else:
                target_height = 6.0  # Small structure
                reason = "small structure"

        # Narrow tall items - cap at reasonable height
        elif min_dim < 5 and height > 30:
            target_height = min(height, 15.0)  # Cap at 15m for narrow items
            reason = "narrow item cap"

        # Buildings with 20m default - estimate based on area
        elif abs(height - 20.0) < 0.1 and min_dim >= 5:
            # Estimate floors based on footprint area
            if area > 20000:  # Large footprint
                target_height = 80.0  # ~20 floors
                reason = "large building estimate"
            elif area > 10000:  # Medium-large
                target_height = 60.0  # ~15 floors
                reason = "medium-large building"
            elif area > 5000:  # Medium
                target_height = 45.0  # ~12 floors
                reason = "medium building"
            elif area > 2000:  # Small-medium
                target_height = 30.0  # ~8 floors
                reason = "small-medium building"
            else:  # Small
                target_height = 20.0  # ~5 floors - keep default
                reason = "small building"

        if target_height and target_height != height:
            print(f"  {obj.name}: {height:.1f}m -> {target_height:.1f}m ({reason})")
            if apply_height(obj, target_height):
                fixed += 1
            else:
                skipped += 1
        else:
            skipped += 1

    print(f"\nFixed: {fixed}")
    print(f"Skipped: {skipped}")

    print("\n" + "=" * 80)
    print("Height Application Complete!")
    print("=" * 80)


if __name__ == "__main__":
    analyze_and_identify()
    # Uncomment to apply heights:
    # apply_smart_heights()
