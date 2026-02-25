"""
MSG 1998 - Separate Buildings (Batch Mode)
Run multiple times to separate buildings in batches of 50
"""

import bpy

# Get the Areas object
areas = None
for obj in bpy.context.scene.objects:
    if 'Areas' in obj.name:
        areas = obj
        break

if not areas:
    print("ERROR: Areas object not found")
else:
    # Create Buildings collection
    buildings_coll = bpy.data.collections.get("Buildings")
    if not buildings_coll:
        buildings_coll = bpy.data.collections.new("Buildings")
        bpy.context.scene.collection.children.link(buildings_coll)

    # Get building groups (not Tags)
    building_groups = [vg.name for vg in areas.vertex_groups if not vg.name.startswith("Tag:")]

    # BATCH SIZE - change this if needed
    BATCH_SIZE = 50
    START_INDEX = 0  # Change this for subsequent runs: 50, 100, 150, etc.

    # Check if we've already separated some (look in Buildings collection)
    already_done = len(buildings_coll.objects)
    start_index = max(START_INDEX, already_done)

    end_index = min(start_index + BATCH_SIZE, len(building_groups))

    print(f"Total buildings: {len(building_groups)}")
    print(f"Already separated: {already_done}")
    print(f"Processing batch: {start_index} to {end_index}")

    separated = []

    for i in range(start_index, end_index):
        group_name = building_groups[i]

        # Select Areas object
        bpy.context.view_layer.objects.active = areas
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        areas.select_set(True)

        # Edit mode, select group
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')

        vg_idx = areas.vertex_groups.find(group_name)
        if vg_idx >= 0:
            areas.vertex_groups.active_index = vg_idx
            bpy.ops.object.vertex_group_select()

            bpy.ops.object.mode_set(mode='OBJECT')
            verts_selected = [v for v in areas.data.vertices if v.select]

            if len(verts_selected) > 0:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.mode_set(mode='OBJECT')

                new_obj = None
                for obj in bpy.context.selected_objects:
                    if obj != areas:
                        new_obj = obj
                        break

                if new_obj:
                    clean_name = group_name.replace("Name:", "").strip()
                    if not clean_name:
                        clean_name = f"Building_{i:04d}"

                    new_obj.name = clean_name
                    new_obj.vertex_groups.clear()

                    for coll in new_obj.users_collection:
                        coll.objects.unlink(new_obj)
                    buildings_coll.objects.link(new_obj)

                    separated.append(clean_name)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

    print(f"\nBatch complete! Separated {len(separated)} buildings")
    print(f"Total in Buildings collection: {len(buildings_coll.objects)}")
    print(f"Remaining: {len(building_groups) - len(buildings_coll.objects)}")

    if len(building_groups) - len(buildings_coll.objects) > 0:
        print("\nRun again to continue separating...")
