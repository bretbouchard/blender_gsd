"""
MSG 1998 - Organize Streets & Ways
Run this in Blender to separate roads from subways
"""

import bpy

# Create collection structure
collections_to_create = [
    "Streets_Roads",
    "Streets_Sidewalks",
    "Subway_Entrances",
    "Subway_Tracks",
    "Subway_Platforms",
    "_Unsorted",
]

for coll_name in collections_to_create:
    if coll_name not in bpy.data.collections:
        coll = bpy.data.collections.new(coll_name)
        bpy.context.scene.collection.children.link(coll)

print("Collections created")

# Classification function
def classify_object(obj):
    name_lower = obj.name.lower()

    # Subway keywords
    subway_keywords = ['subway', 'metro', 'mta', 'train', 'platform', 'track',
                       'station', 'underground', 'entrance', 'stair', 'tunnel']

    # Road keywords
    road_keywords = ['road', 'street', 'ave', 'avenue', 'drive',
                     'lane', 'highway', 'boulevard', 'blvd', 'way']

    # Check for subway
    for keyword in subway_keywords:
        if keyword in name_lower:
            if 'entrance' in name_lower or 'stair' in name_lower:
                return "Subway_Entrances"
            elif 'track' in name_lower or 'rail' in name_lower:
                return "Subway_Tracks"
            elif 'platform' in name_lower:
                return "Subway_Platforms"
            else:
                return "Subway_Tracks"

    # Check for road
    for keyword in road_keywords:
        if keyword in name_lower:
            return "Streets_Roads"

    # Check Z position (below ground = subway)
    if hasattr(obj, 'location') and obj.location.z < -1:
        return "Subway_Tracks"

    return "_Unsorted"

def move_to_collection(obj, target_name):
    if target_name not in bpy.data.collections:
        return
    target = bpy.data.collections[target_name]
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    target.objects.link(obj)

# Process 'ways' collection
if "ways" in bpy.data.collections:
    ways_objects = list(bpy.data.collections["ways"].objects)
    print(f"Processing {len(ways_objects)} objects from 'ways'")

    counts = {"Streets_Roads": 0, "Streets_Sidewalks": 0,
              "Subway_Entrances": 0, "Subway_Tracks": 0,
              "Subway_Platforms": 0, "_Unsorted": 0}

    for obj in ways_objects:
        target = classify_object(obj)
        move_to_collection(obj, target)
        counts[target] += 1

    print("Results:")
    for name, count in counts.items():
        print(f"  {name}: {count}")
else:
    print("ways collection not found")

print("Done - check _Unsorted for missed items")
