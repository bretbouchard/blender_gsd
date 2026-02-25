"""
MSG 1998 - Road & Night Scene Setup (Fixed for Blender 5.0)
Run this in Blender
"""

import bpy
import math
import random

# =============================================================================
# 1. ROAD MATERIALS
# =============================================================================

def create_asphalt_material():
    """Create 1998 NYC asphalt material"""
    mat = bpy.data.materials.new(name="NYC_Asphalt_1998")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)

    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.08, 0.08, 0.09, 1.0)
    principled.inputs['Roughness'].default_value = 0.85

    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-300, 0)
    noise.inputs['Scale'].default_value = 50.0

    bump = nodes.new('ShaderNodeBump')
    bump.location = (-150, -100)
    bump.inputs['Strength'].default_value = 0.02

    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])

    return mat

# =============================================================================
# 2. APPLY MATERIALS TO ROADS
# =============================================================================

def apply_materials_to_roads():
    roads_coll = bpy.data.collections.get("Streets_Roads")
    if not roads_coll:
        print("Streets_Roads collection not found")
        return

    asphalt = create_asphalt_material()

    for obj in roads_coll.objects:
        if obj.type == 'MESH':
            if len(obj.data.materials) == 0:
                obj.data.materials.append(asphalt)
            else:
                obj.data.materials[0] = asphalt

    print(f"Applied asphalt material to {len(roads_coll.objects)} road objects")

# =============================================================================
# 3. STREET LIGHTS
# =============================================================================

def create_street_light(location, rotation=0):
    # Create pole
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=6, location=location)
    pole = bpy.context.active_object
    pole.name = "StreetLight_Pole"
    pole.location.z += 3

    # Create light
    light_loc = (location[0], location[1], location[2] + 5.8)

    bpy.ops.object.light_add(type='POINT', location=light_loc)
    light = bpy.context.active_object
    light.name = "StreetLight_Point"
    light.data.energy = 500
    light.data.color = (1.0, 0.9, 0.7)
    light.data.shadow_soft_size = 0.5

    # Group into collection
    lights_coll = bpy.data.collections.get("StreetLights")
    if not lights_coll:
        lights_coll = bpy.data.collections.new("StreetLights")
        bpy.context.scene.collection.children.link(lights_coll)

    for obj in [pole, light]:
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        lights_coll.objects.link(obj)

    return pole, light

def add_street_lights():
    roads_coll = bpy.data.collections.get("Streets_Roads")
    if not roads_coll:
        return

    # Find scene bounds
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    for obj in roads_coll.objects:
        for corner in obj.bound_box:
            min_x = min(min_x, corner[0])
            max_x = max(max_x, corner[0])
            min_y = min(min_y, corner[1])
            max_y = max(max_y, corner[1])

    print(f"Scene bounds: X({min_x:.1f} to {max_x:.1f}), Y({min_y:.1f} to {max_y:.1f})")

    spacing = 30
    lights_created = 0

    x = min_x + spacing
    while x < max_x:
        y = min_y + spacing
        while y < max_y:
            offset = (spacing/2) if (int(x/spacing) % 2 == 0) else -(spacing/2)
            create_street_light((x, y + offset, 0), rotation=random.uniform(0, 2*math.pi))
            lights_created += 1
            y += spacing
        x += spacing

    print(f"Created {lights_created} street lights")

# =============================================================================
# 4. NIGHT AMBIANCE
# =============================================================================

def setup_night_lighting():
    # Create dim ambient (moon)
    bpy.ops.object.light_add(type='SUN', location=(100, 100, 200))
    ambient = bpy.context.active_object
    ambient.name = "Night_Ambient"
    ambient.data.energy = 0.05
    ambient.data.color = (0.5, 0.6, 0.8)
    ambient.rotation_euler = (math.radians(45), math.radians(30), 0)

    # City glow - use POINT (HEMI removed in Blender 5)
    bpy.ops.object.light_add(type='POINT', location=(0, 0, 100))
    glow = bpy.context.active_object
    glow.name = "City_Glow"
    glow.data.energy = 100
    glow.data.color = (1.0, 0.8, 0.5)
    glow.data.shadow_soft_size = 20

    # Move to Lights collection
    lights_coll = bpy.data.collections.get("Lights")
    if not lights_coll:
        lights_coll = bpy.data.collections.new("Lights")
        bpy.context.scene.collection.children.link(lights_coll)

    for obj in [ambient, glow]:
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        lights_coll.objects.link(obj)

    print("Night lighting configured")

# =============================================================================
# 5. WORLD SETTINGS
# =============================================================================

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
    bg.inputs['Color'].default_value = (0.02, 0.02, 0.05, 1.0)
    bg.inputs['Strength'].default_value = 0.3

    output = nodes.new('ShaderNodeOutputWorld')
    links.new(bg.outputs['Background'], output.inputs['Surface'])

    print("World set to night sky")

# =============================================================================
# RUN
# =============================================================================

print("\n" + "="*50)
print("MSG 1998 - Setting up roads & night scene")
print("="*50 + "\n")

apply_materials_to_roads()
setup_night_lighting()
setup_world()
add_street_lights()

print("\n" + "="*50)
print("SETUP COMPLETE")
print("="*50)
