"""
Test render with sharp-edged cylinders (no smooth shading on flat faces).
"""
import bpy
import pathlib
import sys
import math

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Create collection
col = bpy.data.collections.new("Knobs")
bpy.context.scene.collection.children.link(col)

# Simple test: Create 5 basic cylinders WITHOUT any modifiers
knob_configs = [
    ("Blue", (0.2, 0.4, 0.8)),
    ("Green", (0.2, 0.7, 0.3)),
    ("Yellow", (0.9, 0.8, 0.1)),
    ("Orange", (0.9, 0.5, 0.1)),
    ("Red", (0.9, 0.2, 0.2)),
]

positions = [(-2, 0, 0), (-1, 0, 0), (0, 0, 0), (1, 0, 0), (2, 0, 0)]

for (name, color), pos in zip(knob_configs, positions):
    # Cap cylinder (top part)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.009,  # 9mm radius = 18mm diameter
        depth=0.020,   # 20mm height
        location=(pos[0], pos[1], 0.008 + 0.010),  # On top of skirt
        vertices=64
    )
    cap = bpy.context.active_object
    cap.name = f"{name}_cap"

    # Skirt cylinder (bottom part)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.010,  # 10mm radius = 20mm diameter (wider)
        depth=0.008,   # 8mm height
        location=(pos[0], pos[1], 0.004),  # Bottom
        vertices=64
    )
    skirt = bpy.context.active_object
    skirt.name = f"{name}_skirt"

    # Join them
    bpy.context.view_layer.objects.active = cap
    cap.select_set(True)
    skirt.select_set(True)
    bpy.ops.object.join()
    knob = bpy.context.active_object
    knob.name = name

    # Scale up for visibility
    knob.scale = (20, 20, 20)
    bpy.ops.object.transform_apply(scale=True)

    # Material
    mat = bpy.data.materials.new(f"Mat_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.3
    if name == "Blue" or name == "Red":
        bsdf.inputs["Coat Weight"].default_value = 0.5
    else:
        bsdf.inputs["Metallic"].default_value = 0.8
        bsdf.inputs["Roughness"].default_value = 0.35
    knob.data.materials.append(mat)

# Camera
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = 'PERSP'
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (0, -4, 2)
cam_obj.rotation_euler = (math.radians(60), 0, 0)
bpy.context.scene.camera = cam_obj

# Light
bpy.ops.object.light_add(type="SUN", location=(5, -5, 10))
bpy.context.active_object.data.energy = 3

# World
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.15, 0.15, 0.15, 1.0)

# Render
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 400

output = pathlib.Path(__file__).parent.parent / "build" / "test_sharp_knobs.png"
scene.render.filepath = str(output)
print(f"[RENDER] Rendering to {output}")
bpy.ops.render.render(write_still=True)
print("[RENDER] Done!")
