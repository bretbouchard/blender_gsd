"""
MSG 1998 - Separate Buildings
Separates the Areas object into individual building objects
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
    print(f"Found Areas object with {len(areas.vertex_groups)} vertex groups")

    # Create Buildings collection
    buildings_coll = bpy.data.collections.get("Buildings")
    if not buildings_coll:
        buildings_coll = bpy.data.collections.new("Buildings")
        bpy.context.scene.collection.children.link(buildings_coll)

    # Get building vertex groups (exclude Tag: groups)
    building_groups = [vg.name for vg in areas.vertex_groups if not vg.name.startswith("Tag:")]

    print(f"Separating {len(building_groups)} buildings...")

    separated = []

    for i, group_name in enumerate(building_groups):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(building_groups)}")

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

            # Check if anything selected
            bpy.ops.object.mode_set(mode='OBJECT')
            verts_selected = [v for v in areas.data.vertices if v.select]

            if len(verts_selected) > 0:
                # Separate
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.mode_set(mode='OBJECT')

                # Get new object
                new_obj = None
                for obj in bpy.context.selected_objects:
                    if obj != areas:
                        new_obj = obj
                        break

                if new_obj:
                    # Clean name
                    clean_name = group_name.replace("Name:", "").strip()
                    if not clean_name:
                        clean_name = f"Building_{i:04d}"

                    new_obj.name = clean_name

                    # Clear vertex groups from new object
                    new_obj.vertex_groups.clear()

                    # Move to Buildings collection
                    for coll in new_obj.users_collection:
                        coll.objects.unlink(new_obj)
                    buildings_coll.objects.link(new_obj)

                    separated.append(clean_name)

        # Deselect for next iteration
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

    print(f"\n{'='*50}")
    print(f"DONE! Separated {len(separated)} buildings")
    print(f"Objects in Buildings collection: {len(buildings_coll.objects)}")

    # Show first 20 names
    print(f"\nFirst 20 buildings:")
    for name in separated[:20]:
        print(f"  - {name}")
