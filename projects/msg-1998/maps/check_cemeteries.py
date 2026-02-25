"""
MSG-1998 Cemetery Check Script

Checks for any cemetery-related objects in the scene.
Historical accuracy: Manhattan has NO cemeteries in the MSG/Midtown area.
"""

import bpy

def find_cemetery_objects():
    """Find any objects that might be cemeteries."""
    keywords = ['cemetery', 'cemetary', 'grave', 'burial', 'tomb', 'memorial park', 'columbarium']

    found = []
    for obj in bpy.data.objects:
        name_lower = obj.name.lower()
        for kw in keywords:
            if kw in name_lower:
                found.append(obj)
                break

    # Also check collections
    cemetery_collections = []
    for coll in bpy.data.collections:
        coll_lower = coll.name.lower()
        for kw in keywords:
            if kw in coll_lower:
                cemetery_collections.append(coll)
                break

    print("\n" + "=" * 70)
    print("MSG-1998 Cemetery Check")
    print("=" * 70)

    if found:
        print(f"\nFound {len(found)} potential cemetery objects:")
        for obj in found:
            print(f"  - {obj.name}")
            # Show location
            if obj.users_collection:
                print(f"    Collection: {obj.users_collection[0].name}")
    else:
        print("\nNo cemetery objects found in scene.")

    if cemetery_collections:
        print(f"\nFound {len(cemetery_collections)} cemetery collections:")
        for coll in cemetery_collections:
            print(f"  - {coll.name} ({len(coll.objects)} objects)")
    else:
        print("No cemetery collections found.")

    if not found and not cemetery_collections:
        print("\n✓ Scene is historically accurate - no cemeteries in Manhattan!")

    print("=" * 70)

    return found, cemetery_collections


def remove_cemetery_objects(found_objects, found_collections):
    """Remove or rename cemetery objects for accuracy."""

    print("\n" + "=" * 70)
    print("Removing/Renaming Cemetery Objects")
    print("=" * 70)

    # Rename objects to parks
    for obj in found_objects:
        old_name = obj.name
        new_name = obj.name
        for kw in ['cemetery', 'Cemetery', 'CEMETERY']:
            new_name = new_name.replace(kw, 'Park')
        for kw in ['grave', 'Grave', 'GRAVE']:
            new_name = new_name.replace(kw, 'Green')
        obj.name = new_name
        print(f"  Renamed: {old_name} -> {new_name}")

    # Rename collections
    for coll in found_collections:
        old_name = coll.name
        new_name = coll.name
        for kw in ['cemetery', 'Cemetery', 'CEMETERY']:
            new_name = new_name.replace(kw, 'Parks')
        coll.name = new_name
        print(f"  Renamed collection: {old_name} -> {new_name}")

    print("=" * 70)


# Run the check
if __name__ == "__main__":
    found_objects, found_collections = find_cemetery_objects()

    # Uncomment to automatically rename:
    # if found_objects or found_collections:
    #     remove_cemetery_objects(found_objects, found_collections)
