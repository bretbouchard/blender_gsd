"""
MSG 1998 - Step 4: Multiple Street Lamps
Run this in Blender - adds street lamps along roads
"""

import bpy
import math

# Get scene bounds from roads
roads_coll = bpy.data.collections.get("Streets_Roads")

if not roads_coll:
    print("ERROR: Streets_Roads collection not found")
else:
    # Find bounds
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    for obj in roads_coll.objects:
        for corner in obj.bound_box:
            min_x = min(min_x, obj.location.x + corner[0])
            max_x = max(max_x, obj.location.x + corner[0])
            min_y = min(min_y, obj.location.y + corner[1])
            max_y = max(max_y, obj.location.y + corner[1])

    print(f"Scene bounds: X({min_x:.1f} to {max_x:.1f}), Y({min_y:.1f} to {max_y:.1f})")

    # Get or create StreetLamps collection
    lamps_coll = bpy.data.collections.get("StreetLamps")
    if not lamps_coll:
        lamps_coll = bpy.data.collections.new("StreetLamps")
        bpy.context.scene.collection.children.link(lamps_coll)

    # Place lamps every 40 meters
    spacing = 40
    lamps_created = 0

    x = min_x + spacing/2
    while x < max_x:
        y = min_y + spacing/2
        while y < max_y:
            # Alternate sides
            offset = 5 if (int((x + y) / spacing) % 2 == 0) else -5

            loc_x = x
            loc_y = y + offset
            loc_z = 0

            # Create pole
            bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=8, location=(loc_x, loc_y, loc_z))
            pole = bpy.context.active_object
            pole.name = f"Lamp_{lamps_created:03d}_Pole"
            pole.location.z += 4

            # Create lamp head
            bpy.ops.mesh.primitive_cube_add(size=0.5, location=(loc_x, loc_y, loc_z + 8))
            head = bpy.context.active_object
            head.name = f"Lamp_{lamps_created:03d}_Head"

            # Create point light
            bpy.ops.object.light_add(type='POINT', location=(loc_x, loc_y, loc_z + 7.5))
            light = bpy.context.active_object
            light.name = f"Lamp_{lamps_created:03d}_Light"
            light.data.energy = 500
            light.data.color = (1.0, 0.9, 0.7)
            light.data.shadow_soft_size = 0.5

            # Move to collection
            for obj in [pole, head, light]:
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                lamps_coll.objects.link(obj)

            lamps_created += 1
            y += spacing
        x += spacing

        # Progress update every row
        print(f"  Created {lamps_created} lamps so far...")

    print(f"\nDone! Created {lamps_created} street lamps")
    print(f"Check the 'StreetLamps' collection")
