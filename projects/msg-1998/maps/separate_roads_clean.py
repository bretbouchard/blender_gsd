"""
Separate roads into individual objects with correct names
First deletes existing separated roads, then creates fresh ones
Run this in Blender
"""

import bpy

# Delete existing separated road objects in Streets_Roads
roads_coll = bpy.data.collections.get("Streets_Roads")
if roads_coll:
    for obj in list(roads_coll.objects):
        if obj.name != "Ways":
            bpy.data.objects.remove(obj, do_unlink=True)
    print("Cleaned up old road objects")

# Get the original Ways object
obj = bpy.data.objects.get("Ways")

if not obj:
    print("ERROR: 'Ways' object not found")
else:
    # Make sure Streets_Roads collection exists
    if not roads_coll:
        roads_coll = bpy.data.collections.new("Streets_Roads")
        bpy.context.scene.collection.children.link(roads_coll)

    # Get road names (not Tags)
    road_names = [vg.name for vg in obj.vertex_groups if not vg.name.startswith("Tag:")]
    print(f"Found {len(road_names)} roads to separate")

    separated = []

    for i, road_name in enumerate(road_names):
        print(f"[{i+1}/{len(road_names)}] {road_name}")

        # Select the Ways object
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

        # Edit mode, deselect all
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')

        # Select vertices in this vertex group
        vg_idx = obj.vertex_groups.find(road_name)
        if vg_idx >= 0:
            obj.vertex_groups.active_index = vg_idx
            bpy.ops.object.vertex_group_select()

            # Check if anything selected
            bpy.ops.object.mode_set(mode='OBJECT')
            verts_selected = [v for v in obj.data.vertices if v.select]

            if len(verts_selected) > 0:
                # Separate
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.mode_set(mode='OBJECT')

                # Get the newly created object (last selected)
                new_obj = bpy.context.selected_objects[-1] if len(bpy.context.selected_objects) > 1 else None

                if new_obj and new_obj != obj:
                    # Remove all vertex groups from new object
                    new_obj.vertex_groups.clear()

                    # Rename object to street name
                    new_obj.name = road_name

                    # Move to Streets_Roads collection
                    for coll in new_obj.users_collection:
                        coll.objects.unlink(new_obj)
                    roads_coll.objects.link(new_obj)

                    separated.append(road_name)
                    print(f"  Created: {road_name}")

    # Move original Ways back to root or delete
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"\n{'='*50}")
    print(f"DONE! Separated {len(separated)} roads:")
    for name in separated:
        print(f"  - {name}")
    print(f"\nObjects in Streets_Roads: {len(roads_coll.objects)}")
