"""
Rename road objects based on their vertex group (street name)
Run this in Blender
"""

import bpy

roads_coll = bpy.data.collections.get("Streets_Roads")

if not roads_coll:
    print("ERROR: Streets_Roads collection not found")
else:
    renamed = 0

    for obj in roads_coll.objects:
        # Check if object has vertex groups
        if len(obj.vertex_groups) > 0:
            # Get the first vertex group name (the street name)
            street_name = obj.vertex_groups[0].name

            # Skip if it's a Tag
            if not street_name.startswith("Tag:"):
                obj.name = street_name
                print(f"Renamed: {obj.name}")
                renamed += 1

    print(f"\nDone! Renamed {renamed} objects to street names")
