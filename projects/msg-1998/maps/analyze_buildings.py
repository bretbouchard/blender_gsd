"""
MSG-1998 Building Analysis

Analyzes all buildings in the scene:
1. Lists all building objects
2. Shows current dimensions
3. Extracts building names
4. Prepares for height correction
"""

import bpy
from mathutils import Vector


def get_all_buildings():
    """Get all building objects from the scene."""
    buildings = []

    # Common building collection names
    building_coll_names = ["Buildings", "Building", "buildings", "MSG_Buildings", "City_Buildings"]

    # Also check for any collection with "building" in name
    for coll in bpy.data.collections:
        if "building" in coll.name.lower():
            building_coll_names.append(coll.name)

    # Get objects from building collections
    for coll_name in set(building_coll_names):  # Remove duplicates
        if coll_name in bpy.data.collections:
            coll = bpy.data.collections[coll_name]
            for obj in coll.all_objects:
                if obj.type == 'MESH':
                    buildings.append(obj)

    # Also search for objects with "building" or common building names in name
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            name_lower = obj.name.lower()
            if any(keyword in name_lower for keyword in ['building', 'tower', 'plaza', 'hotel', 'office', 'empire', 'chrysler', 'penn', 'msg', 'garden', 'one ', 'two ', 'west']):
                if obj not in buildings:
                    buildings.append(obj)

    return buildings


def get_object_dimensions(obj):
    """Get the dimensions of an object in world space."""
    # Get bounding box in world space
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    # Calculate dimensions
    min_x = min(v.x for v in bbox)
    max_x = max(v.x for v in bbox)
    min_y = min(v.y for v in bbox)
    max_y = max(v.y for v in bbox)
    min_z = min(v.z for v in bbox)
    max_z = max(v.z for v in bbox)

    width = max_x - min_x
    depth = max_y - min_y
    height = max_z - min_z

    return {
        'width': width,
        'depth': depth,
        'height': height,
        'min_z': min_z,
        'max_z': max_z,
        'center_z': (min_z + max_z) / 2
    }


def analyze_buildings():
    """Analyze all buildings and print report."""

    print("\n" + "=" * 70)
    print("MSG-1998 Building Analysis")
    print("=" * 70)

    buildings = get_all_buildings()
    print(f"\nFound {len(buildings)} building objects\n")

    if not buildings:
        print("No buildings found!")
        print("\nSearching all collections...")
        for coll in bpy.data.collections:
            print(f"  Collection: {coll.name} ({len(coll.objects)} objects)")
            for obj in list(coll.objects)[:5]:
                print(f"    - {obj.name} ({obj.type})")
        return []

    # Sort by name
    buildings.sort(key=lambda x: x.name)

    print("-" * 70)
    print(f"{'Building Name':<45} {'Width':>8} {'Depth':>8} {'Height':>8}")
    print("-" * 70)

    building_data = []

    for obj in buildings:
        dims = get_object_dimensions(obj)
        name = obj.name[:44]  # Truncate long names

        print(f"{name:<45} {dims['width']:>8.1f} {dims['depth']:>8.1f} {dims['height']:>8.1f}")

        building_data.append({
            'object': obj,
            'name': obj.name,
            'dimensions': dims,
            'collection': obj.users_collection[0].name if obj.users_collection else 'None'
        })

    print("-" * 70)
    print(f"Total buildings: {len(buildings)}")

    # Summary statistics
    heights = [d['dimensions']['height'] for d in building_data]
    print(f"\nHeight statistics:")
    print(f"  Min: {min(heights):.1f}m")
    print(f"  Max: {max(heights):.1f}m")
    print(f"  Avg: {sum(heights)/len(heights):.1f}m")

    # List collections
    collections = set(d['collection'] for d in building_data)
    print(f"\nCollections with buildings: {', '.join(sorted(collections))}")

    print("=" * 70)

    return building_data


def export_building_list(building_data, filepath="/Users/bretbouchard/apps/blender_gsd/projects/msg-1998/maps/building_list.txt"):
    """Export building list to file for reference."""

    with open(filepath, 'w') as f:
        f.write("MSG-1998 Building List\n")
        f.write("=" * 70 + "\n\n")

        for b in building_data:
            f.write(f"Name: {b['name']}\n")
            f.write(f"  Current Height: {b['dimensions']['height']:.1f}m\n")
            f.write(f"  Width: {b['dimensions']['width']:.1f}m\n")
            f.write(f"  Depth: {b['dimensions']['depth']:.1f}m\n")
            f.write(f"  Collection: {b['collection']}\n")
            f.write("\n")

    print(f"\nExported building list to: {filepath}")


# Run in Blender
if __name__ == "__main__":
    building_data = analyze_buildings()
    if building_data:
        export_building_list(building_data)
