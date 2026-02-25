"""
MSG-1998 Road System - Rename Curves

Cleans up curve names by removing "Name:" prefix and "_curve" suffix.
Example: "Name:10th Avenue_curve.002" → "10th Avenue"
"""

import bpy
import re


def rename_road_curves():
    """Clean up road curve names."""

    print("\n" + "=" * 50)
    print("Renaming Road Curves")
    print("=" * 50)

    # Collections to process
    collections_to_check = ["Road_Objects", "Streets_Roads"]

    renamed = 0

    for coll_name in collections_to_check:
        if coll_name not in bpy.data.collections:
            continue

        coll = bpy.data.collections[coll_name]

        for obj in list(coll.objects):
            if obj.type != 'CURVE':
                continue

            old_name = obj.name

            # Remove "Name:" prefix
            new_name = old_name
            if new_name.startswith("Name:"):
                new_name = new_name[5:]  # Remove "Name:"

            # Remove "_curve" suffix (and any trailing .###)
            # First handle the .### version suffix
            version_suffix = ""
            match = re.search(r'\.\d+$', new_name)
            if match:
                version_suffix = match.group()
                new_name = new_name[:-len(version_suffix)]

            # Now remove _curve suffix
            if new_name.endswith("_curve"):
                new_name = new_name[:-6]

            # Add back version suffix if there was one
            new_name = new_name + version_suffix

            # Clean up any double spaces or leading/trailing spaces
            new_name = ' '.join(new_name.split())

            if new_name != old_name:
                obj.name = new_name
                print(f"  {old_name} → {new_name}")
                renamed += 1

    print(f"\nRenamed {renamed} curves")

    print("\n" + "=" * 50)
    print("Rename complete!")
    print("=" * 50)

    return renamed


# Run in Blender
if __name__ == "__main__":
    rename_road_curves()
