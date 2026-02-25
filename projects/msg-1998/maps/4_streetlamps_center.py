"""
MSG 1998 - Street Lamps (MSG area only)
Only places lamps in the immediate MSG area, not the whole 3km map
"""

import bpy
import math

# MSG is approximately at center of scene
# Only place lamps in a 400m x 400m area around center
CENTER_X = 250  # Approximate MSG center
CENTER_Y = -600
RADIUS = 200  # 200m radius = 400m x 400m area

# Get or create StreetLamps collection
lamps_coll = bpy.data.collections.get("StreetLamps")
if not lamps_coll:
    lamps_coll = bpy.data.collections.new("StreetLamps")
    bpy.context.scene.collection.children.link(lamps_coll)

# Place lamps every 30 meters within the radius
spacing = 30
lamps_created = 0

x = CENTER_X - RADIUS
while x <= CENTER_X + RADIUS:
    y = CENTER_Y - RADIUS
    while y <= CENTER_Y + RADIUS:
        # Check if within radius
        dist = math.sqrt((x - CENTER_X)**2 + (y - CENTER_Y)**2)
        if dist <= RADIUS:
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

print(f"\nDone! Created {lamps_created} street lamps in MSG area")
print(f"Area: {RADIUS*2}m x {RADIUS*2}m around ({CENTER_X}, {CENTER_Y})")
