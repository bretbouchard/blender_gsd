"""
Separate the Ways object into individual road objects by vertex group
Run this in Blender
"""

import bpy

# Get the Ways object
obj = bpy.data.objects.get("Ways")

if not obj:
    print("ERROR: 'Ways' object not found")
else:
    # Get the collection to put new objects in
    roads_coll = bpy.data.collections.get("Streets_Roads")
    if not roads_coll:
        roads_coll = bpy.data.collections.new("Streets_Roads")
        bpy.context.scene.collection.children.link(roads_coll)

    # Get vertex groups that are road names (not Tags)
    road_groups = [vg.name for vg in obj.vertex_groups if not vg.name.startswith("Tag:")]

    print(f"Found {len(road_groups)} roads to separate")

    # Select the Ways object
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    # For each road, select its vertices and separate
    separated_count = 0

    for i, group_name in enumerate(road_groups):
        print(f"Processing {i+1}/{len(road_groups)}: {group_name}")

        # Switch to edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')

        # Select vertices in this vertex group
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.object.vertex_groups.active_index = obj.vertex_groups.find(group_name)
        bpy.ops.object.vertex_group_select()

        # Check if anything is selected
        bpy.ops.object.mode_set(mode='OBJECT')
        me = obj.data
        selected = [v for v in me.vertices if v.select]

        if len(selected) > 0:
            # Switch back to edit and separate
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.separate(type='SELECTED')

            # The new object becomes active
            new_obj = bpy.context.view_layer.objects.active
            if new_obj and new_obj != obj:
                new_obj.name = f"Road_{group_name}"

                # Move to Roads collection
                for coll in new_obj.users_collection:
                    coll.objects.unlink(new_obj)
                roads_coll.objects.link(new_obj)

                separated_count += 1

        # Deselect for next iteration
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

    print(f"\nDone! Separated {separated_count} road objects")
    print(f"Objects in Streets_Roads: {len(roads_coll.objects)}")
