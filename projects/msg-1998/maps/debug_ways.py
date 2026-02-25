"""
Debug script - Print all object names in 'ways' collection
Run this to see what we're working with
"""

import bpy

print("\n" + "="*60)
print("DEBUG: Objects in 'ways' collection")
print("="*60)

if "ways" in bpy.data.collections:
    ways = bpy.data.collections["ways"]
    objects = list(ways.objects)
    print(f"\nTotal objects: {len(objects)}")
    print("\nObject names:")
    for i, obj in enumerate(objects[:50]):  # First 50
        print(f"  {i+1}. {obj.name} | z={obj.location.z:.2f}")

    if len(objects) > 50:
        print(f"  ... and {len(objects) - 50} more")

else:
    print("'ways' collection not found!")
    print("\nAvailable collections:")
    for coll in bpy.data.collections:
        print(f"  - {coll.name} ({len(coll.objects)} objects)")

print("\n")
