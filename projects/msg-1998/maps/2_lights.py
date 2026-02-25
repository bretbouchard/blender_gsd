"""
MSG 1998 - Step 2: Night Lights Only
Run this in Blender - sets up ambient lighting
"""

import bpy
import math

def setup_night_lighting():
    # Create Lights collection
    lights_coll = bpy.data.collections.get("Lights")
    if not lights_coll:
        lights_coll = bpy.data.collections.new("Lights")
        bpy.context.scene.collection.children.link(lights_coll)

    # Create dim ambient (moon)
    bpy.ops.object.light_add(type='SUN', location=(100, 100, 200))
    ambient = bpy.context.active_object
    ambient.name = "Night_Ambient"
    ambient.data.energy = 0.05
    ambient.data.color = (0.5, 0.6, 0.8)  # Cool blue
    ambient.rotation_euler = (math.radians(45), math.radians(30), 0)

    # Move to Lights collection
    for coll in ambient.users_collection:
        coll.objects.unlink(ambient)
    lights_coll.objects.link(ambient)

    print("Created Night_Ambient (moon light)")

def setup_world():
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("Night_Sky")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    bg = nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.02, 0.02, 0.05, 1.0)  # Dark blue
    bg.inputs['Strength'].default_value = 0.3

    output = nodes.new('ShaderNodeOutputWorld')
    links.new(bg.outputs['Background'], output.inputs['Surface'])

    print("Set world to Night_Sky")

# Run
setup_night_lighting()
setup_world()
print("\nDone! Ambient lighting configured.")
