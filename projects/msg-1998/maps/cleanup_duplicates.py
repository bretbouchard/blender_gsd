"""
MSG-1998 Road System - Cleanup Duplicate Curves

Removes old duplicate curves (with .001, .002 suffixes) from the
Streets_Roads and Road_Objects collections.
"""

import bpy


def cleanup_duplicate_curves():
    """Remove duplicate curves, keeping only the newest ones."""

    print("\n" + "=" * 50)
    print("Cleaning Up Duplicate Curves")
    print("=" * 50)

    # Collections to check
    collections_to_check = ["Streets_Roads", "Road_Objects"]

    # First, collect all objects to remove (store names, not references)
    to_remove = []
    kept = []

    for coll_name in collections_to_check:
        if coll_name not in bpy.data.collections:
            continue

        coll = bpy.data.collections[coll_name]

        # Group objects by base name
        base_names = {}
        for obj in list(coll.objects):
            if obj.type != 'CURVE':
                continue

            # Extract base name (remove .001, .002, etc.)
            name = obj.name
            if '.' in name and name.split('.')[-1].isdigit():
                base = '.'.join(name.split('.')[:-1])
            else:
                base = name

            if base not in base_names:
                base_names[base] = []
            base_names[base].append(name)  # Store name, not object

        # For each group, keep the newest (highest suffix or no suffix)
        for base, names in base_names.items():
            if len(names) <= 1:
                kept.append(names[0])
                continue

            # Sort by name (higher suffix = newer)
            names.sort(reverse=True)

            # Keep the first (newest), mark the rest for removal
            kept.append(names[0])
            to_remove.extend(names[1:])
            for old_name in names[1:]:
                print(f"  Marking for removal: {old_name}")

    # Now remove all marked objects by name
    removed = []
    for name in to_remove:
        if name in bpy.data.objects:
            obj = bpy.data.objects[name]
            # Unlink from all collections first
            for c in list(obj.users_collection):
                c.objects.unlink(obj)
            # Delete the object
            bpy.data.objects.remove(obj, do_unlink=True)
            removed.append(name)
            print(f"  Removed: {name}")
        else:
            print(f"  Already gone: {name}")

    print(f"\nKept {len(kept)} curves")
    print(f"Removed {len(removed)} duplicates")

    print("\n" + "=" * 50)
    print("Cleanup complete!")
    print("=" * 50)

    return removed


# Run in Blender
if __name__ == "__main__":
    cleanup_duplicate_curves()
