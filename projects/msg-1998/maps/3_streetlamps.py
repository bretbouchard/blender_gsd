"""
MSG 1998 - Step 3: Street Lamps (single test)
Run this in Blender - creates ONE street lamp to test
"""

import bpy
import math

# Create at origin (0,0,0)
location = (0, 0, 0)

# Create pole
bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=8, location=location)
pole = bpy.context.active_object
pole.name = "StreetLamp_Pole"
pole.location.z += 4

# Create lamp head
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(location[0], location[1], location[2] + 8))
head = bpy.context.active_object
head.name = "StreetLamp_Head"

# Create point light
bpy.ops.object.light_add(type='POINT', location=(location[0], location[1], location[2] + 7.5))
light = bpy.context.active_object
light.name = "StreetLamp_Light"
light.data.energy = 500
light.data.color = (1.0, 0.9, 0.7)  # Warm sodium vapor
light.data.shadow_soft_size = 0.5

# Create StreetLamps collection
lamps_coll = bpy.data.collections.get("StreetLamps")
if not lamps_coll:
    lamps_coll = bpy.data.collections.new("StreetLamps")
    bpy.context.scene.collection.children.link(lamps_coll)

# Move all to collection
for obj in [pole, head, light]:
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    lamps_coll.objects.link(obj)

print("Created 1 test street lamp at origin")
print("Check the StreetLamps collection")
