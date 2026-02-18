"""
Final render script - All 5 Neve knobs with proper colors.
Uses Cycles with proper color management.
"""

import bpy
import pathlib
import math

# Clear scene completely
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Purge orphaned data
for block_type in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for block in list(block_type):
        if block.users == 0:
            block_type.remove(block)

BUILD_DIR = pathlib.Path(__file__).parent.parent / "build"

# Verify GLB files exist and check their materials
print("[RENDER] Checking GLB files...")
glb_files = [
    "neve_knob_style1_blue.glb",
    "neve_knob_style2_silver.glb",
    "neve_knob_style3_silver.glb",
    "neve_knob_style4_silver.glb",
    "neve_knob_style5_red.glb",
]
for f in glb_files:
    p = BUILD_DIR / f
    print(f"  {f}: {'EXISTS' if p.exists() else 'MISSING'}")

# Load all 5 knobs with wider spacing
positions = [(-1.6, 0, 0), (-0.8, 0, 0), (0, 0, 0), (0.8, 0, 0), (1.6, 0, 0)]
print("[RENDER] Loading knobs...")

loaded_knobs = []
for filename, pos in zip(glb_files, positions):
    glb_path = BUILD_DIR / filename
    if glb_path.exists():
        bpy.ops.import_scene.gltf(filepath=str(glb_path))
        knob = bpy.context.selected_objects[0]
        knob.scale = (20, 20, 20)
        bpy.ops.object.transform_apply(scale=True)
        knob.location = pos

        # Debug: print material info
        for mat in knob.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        color = node.inputs['Base Color'].default_value
                        metallic = node.inputs['Metallic'].default_value
                        print(f"  {filename}: color=({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f}), metallic={metallic:.2f}")

        loaded_knobs.append(knob)
        print(f"  Loaded: {filename}")

# Studio lighting
print("[RENDER] Setting up lighting...")

# Key light
bpy.ops.object.light_add(type="SUN", location=(3, -3, 8))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 2.5
key.data.color = (1.0, 0.98, 0.95)

# Fill light
bpy.ops.object.light_add(type="AREA", location=(-4, -2, 6))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 800
fill.data.size = 4
fill.data.color = (0.95, 0.97, 1.0)

# Rim light
bpy.ops.object.light_add(type="AREA", location=(0, 3, 4))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 600
rim.data.size = 3
rim.data.color = (1.0, 1.0, 1.0)

# Camera - wide angle to see all 5 knobs
print("[RENDER] Setting up camera...")
bpy.ops.object.camera_add(location=(0, -2.5, 1.0))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(68), 0, 0)
cam.data.lens = 28  # Wide angle
cam.data.sensor_fit = "HORIZONTAL"
bpy.context.scene.camera = cam

# Render settings - Cycles
print("[RENDER] Setting up render...")
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 400
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "16"

# Color management - AgX for better color rendition
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.sequencer_colorspace_settings.name = "sRGB"

# World/background
world = bpy.data.worlds.get("World")
if not world:
    world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.08, 0.08, 0.08, 1.0)  # Dark gray
    bg.inputs["Strength"].default_value = 1.0

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -0.125))
ground = bpy.context.active_object
ground_mat = bpy.data.materials.new("GroundMat")
ground_mat.use_nodes = True
nt = ground_mat.node_tree
nt.nodes.clear()
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
bsdf.inputs["Roughness"].default_value = 0.9
output = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
ground.data.materials.append(ground_mat)

# Final check - count objects
print(f"[RENDER] Scene objects: {len([o for o in bpy.data.objects if o.type == 'MESH'])} meshes")

# Render
output = BUILD_DIR / "neve_knobs_final.png"
scene.render.filepath = str(output)
print(f"[RENDER] Rendering to {output}...")
bpy.ops.render.render(write_still=True)

print(f"[RENDER] Done!")
print(f"[RENDER] Output: {output}")
