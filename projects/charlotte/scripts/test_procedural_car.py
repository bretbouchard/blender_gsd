"""Test script to render procedural car in isolation."""
import bpy
from mathutils import Euler
from pathlib import Path

# Clear scene
bpy.ops.object.select_all(action='DESELECT')
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)

# Load the procedural car
car_blend = Path("/Users/bretbouchard/apps/blender_gsd/assets/vehicles/procedural_car_wired.blend")
print(f"Loading from: {car_blend}")

with bpy.data.libraries.load(str(car_blend)) as (data_from, data_to):
    data_to.objects = [name for name in data_from.objects if name != "Plane"]

print(f"Loaded {len([o for o in data_to.objects if o])} objects")

# Create parent empty
car_root = bpy.data.objects.new("Car_Test", None)
car_root.empty_display_type = "PLAIN_AXES"
bpy.context.collection.objects.link(car_root)

# Link all objects
for obj in data_to.objects:
    if obj:
        bpy.context.collection.objects.link(obj)
        obj.parent = car_root
        obj.hide_viewport = True
        obj.hide_render = True

# Show specific parts
show_parts = ["front base 5", "central base 1", "back base 5", "wheel 1"]
for part_name in show_parts:
    if part_name in bpy.data.objects:
        obj = bpy.data.objects[part_name]
        obj.hide_viewport = False
        obj.hide_render = False
        print(f"Showing: {part_name}")

# Position car
car_root.location = (0, 0, 0)

# Create camera - angled view
cam_data = bpy.data.cameras.new("TestCam")
cam_obj = bpy.data.objects.new("TestCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (6, -6, 5)  # Off to side and above
cam_obj.rotation_euler = Euler((1.2, 0, 0.8), "XYZ")
bpy.context.scene.camera = cam_obj

# Add sun
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun_obj)
sun_obj.location = (5, 5, 10)
sun_obj.rotation_euler = Euler((0.5, 0.2, 0.5), "XYZ")
sun_data.energy = 3.0

# Render
bpy.context.scene.render.engine = "BLENDER_EEVEE"
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720

output_path = "/Users/bretbouchard/apps/blender_gsd/projects/charlotte/renders/procedural_car_test.png"
bpy.context.scene.render.filepath = output_path
print(f"Rendering to: {output_path}")
bpy.ops.render.render(write_still=True)
print("Done!")
