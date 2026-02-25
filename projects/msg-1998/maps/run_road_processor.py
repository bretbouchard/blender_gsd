"""
MSG-1998 Road System - Blender Console Runner

Paste this entire script into Blender's Python Console to run the road processor.
Or use: exec(open("path/to/this/file.py").read())
"""

import sys
import os

# Setup path
script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "/Users/bretbouchard/apps/blender_gsd/projects/msg-1998/maps"
road_system_dir = os.path.join(script_dir, "road_system")
if road_system_dir not in sys.path:
    sys.path.insert(0, road_system_dir)

# Now import and run
from processor import MSGRoadProcessor

def run():
    """Run the road processor."""
    print("\n" + "=" * 60)
    print("MSG-1998 Road System Processor")
    print("=" * 60 + "\n")

    # Check for source collection
    source_collection = "Streets_Roads"
    if source_collection not in bpy.data.collections:
        print(f"ERROR: Collection '{source_collection}' not found!")
        print("Available collections:")
        for coll in bpy.data.collections:
            print(f"  - {coll.name}")
        return None

    source = bpy.data.collections[source_collection]
    print(f"Source collection: {source_collection}")
    print(f"Road objects found: {len(source.objects)}")

    # Show first few road names
    print("\nSample road names:")
    for i, obj in enumerate(list(source.objects)[:10]):
        print(f"  {i+1}. {obj.name}")

    # Define hero roads for MSG area
    hero_roads = {
        "8th Avenue",
        "7th Avenue",
        "33rd Street",
        "34th Street",
        "31st Street",
        "Penn Station",
        "West 31st",
        "West 33rd",
        "West 34th",
    }

    # Create processor
    print("\nInitializing processor...")
    processor = MSGRoadProcessor(
        hero_roads=hero_roads,
        lod_mode="hero",
        seed=42,
    )

    # Process roads
    print("Processing roads...")
    try:
        result = processor.process_from_blender(source_collection)
    except Exception as e:
        print(f"ERROR during processing: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Print statistics
    print("\n" + "-" * 40)
    print("Processing Results:")
    print("-" * 40)
    print(f"  Road segments: {result.statistics['total_segments']}")
    print(f"  Intersections: {result.statistics['total_intersections']}")
    print(f"  Street furniture: {result.statistics['total_furniture']}")
    print(f"  Hero roads: {result.statistics['hero_roads']}")
    print(f"  Total length: {result.statistics['total_length_m']:.1f}m")
    print("\nBy road class:")
    for cls, count in result.statistics['by_class'].items():
        print(f"  {cls}: {count}")

    # Create target collection for processed geometry
    target_collection = "Roads_Processed"
    if target_collection in bpy.data.collections:
        # Clear existing collection
        coll = bpy.data.collections[target_collection]
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        coll = bpy.data.collections.new(target_collection)
        bpy.context.scene.collection.children.link(coll)

    print(f"\nCreating geometry in '{target_collection}'...")

    # Create Blender objects
    try:
        created = processor.create_blender_objects(result, target_collection)
        print(f"  Pavements: {len(created['pavements'])}")
        print(f"  Curbs: {len(created['curbs'])}")
        print(f"  Sidewalks: {len(created['sidewalks'])}")
        print(f"  Markings: {len(created['markings'])}")
        print(f"  Intersections: {len(created['intersections'])}")
    except Exception as e:
        print(f"ERROR creating objects: {e}")
        import traceback
        traceback.print_exc()
        return None

    print("\n" + "=" * 60)
    print("DONE! Check the 'Roads_Processed' collection")
    print("=" * 60 + "\n")

    return result

# Run it
result = run()
