"""
MSG-1998 Road System Runner

Run this script in Blender to process roads from Streets_Roads collection.

Usage in Blender:
    1. Open msg_map.blend
    2. Open Text Editor
    3. Load this script
    4. Click "Run Script"

Or from command line:
    blender msg_map.blend --python process_roads.py
"""

import bpy
import sys
import os

# Add the road_system module to path
script_dir = os.path.dirname(os.path.abspath(__file__))
road_system_dir = os.path.join(script_dir, "road_system")
if road_system_dir not in sys.path:
    sys.path.insert(0, road_system_dir)

from processor import MSGRoadProcessor, process_msg_roads


def main():
    """Main entry point for road processing."""
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
        return

    source = bpy.data.collections[source_collection]
    print(f"Source collection: {source_collection}")
    print(f"Road objects found: {len(source.objects)}")

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
        seed=42,  # Reproducible results
    )

    # Process roads
    print("Processing roads...")
    result = processor.process_from_blender(source_collection)

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
    created = processor.create_blender_objects(result, target_collection)

    print(f"  Pavements: {len(created['pavements'])}")
    print(f"  Curbs: {len(created['curbs'])}")
    print(f"  Sidewalks: {len(created['sidewalks'])}")
    print(f"  Markings: {len(created['markings'])}")
    print(f"  Intersections: {len(created['intersections'])}")

    print("\n" + "=" * 60)
    print("DONE! Check the 'Roads_Processed' collection")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
