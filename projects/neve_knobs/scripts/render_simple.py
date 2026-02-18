"""
Render 5 knobs - exact approach from working cube test.
"""
import bpy
import math

# Clear
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Knob colors: blue, silver, silver, silver, red - closer together
knobs = [
    ("Blue", (0.2, 0.4, 0.8), (-2, 0, 0)),
    ("Silver1", (0.75, 0.75, 0.78), (-1, 0, 0)),
    ("Silver2", (0.75, 0.75, 0.78), (0, 0, 0)),
    ("Silver3", (0.75, 0.75, 0.78), (1, 0, 0)),
    ("Red", (0.85, 0.15, 0.1), (2, 0, 0)),
]

for name, color, pos in knobs:
    # Smaller cubes so all 5 fit
    bpy.ops.mesh.primitive_cube_add(size=0.8, location=pos)
    knob = bpy.context.active_object
    knob.name = f"Knob_{name}"

    # EXACT same material setup as working test
    mat = bpy.data.materials.new(f"Mat_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 5.0
    knob.data.materials.append(mat)

# Camera - orthographic to see everything
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 12  # Wider view
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (0, -10, 5)
cam_obj.rotation_euler = (math.radians(60), 0, 0)
bpy.context.scene.camera = cam_obj

# Light - same as working test
light_data = bpy.data.lights.new("Light", type='SUN')
light_data.energy = 5
light_obj = bpy.data.objects.new("Light", light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (5, 5, 10)

# World - same as working test
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1)
bg.inputs["Strength"].default_value = 1.0
bpy.context.scene.world = world

# Render
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1200
scene.render.resolution_y = 400
scene.render.filepath = '/Users/bretbouchard/apps/blender_gsd/projects/neve_knobs/build/neve_knobs_render.png'
scene.render.image_settings.file_format = 'PNG'

bpy.ops.render.render(write_still=True)
print("Rendered!")
