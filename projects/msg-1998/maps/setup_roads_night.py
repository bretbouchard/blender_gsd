"""
MSG 1998 - Road & Night Scene Setup
Run this in Blender to set up materials, textures, and lighting

This configures:
- Asphalt material for roads
- Street lamps with point lights
- Night ambiance
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

    # Clear default nodes
    nodes.clear()

    # Create nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)

    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)

    # Asphalt color (dark grey, slightly warm for 1998 feel)
    principled.inputs['Base Color'].default_value = (0.08, 0.08, 0.09, 1.0)

    # Rough surface
    principled.inputs['Roughness'].default_value = 0.85

    # Slight specular for wet look (night)
    principled.inputs['Specular IOR Level'].default_value = 0.3

    # Connect
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    # Add some noise for texture variation
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-300, 0)
    noise.inputs['Scale'].default_value = 50.0
    noise.inputs['Detail'].default_value = 10.0

    bump = nodes.new('ShaderNodeBump')
    bump.location = (-150, -100)
    bump.inputs['Strength'].default_value = 0.02

    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])

    return mat

def create_sidewalk_material():
    """Create concrete sidewalk material"""

    mat = bpy.data.materials.new(name="NYC_Sidewalk_1998")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)

    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)

    # Concrete grey
    principled.inputs['Base Color'].default_value = (0.25, 0.25, 0.26, 1.0)
    principled.inputs['Roughness'].default_value = 0.9

    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    return mat

# =============================================================================
# 2. APPLY MATERIALS TO ROADS
# =============================================================================

def apply_materials_to_roads():
    """Apply asphalt material to all road objects"""

    roads_coll = bpy.data.collections.get("Streets_Roads")
    if not roads_coll:
        print("Streets_Roads collection not found")
        return

    asphalt = create_asphalt_material()

    for obj in roads_coll.objects:
        if obj.type == 'MESH':
            # Assign material
            if len(obj.data.materials) == 0:
                obj.data.materials.append(asphalt)
            else:
                obj.data.materials[0] = asphalt

    print(f"Applied asphalt material to {len(roads_coll.objects)} road objects")

# =============================================================================
# 3. STREET LIGHTS
# =============================================================================

def create_street_light(location, rotation=0):
    """Create a street lamp pole with light"""

    # Create pole
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=6, location=location)
    pole = bpy.context.active_object
    pole.name = "StreetLight_Pole"
    pole.location.z += 3

    # Create lamp arm
    arm_loc = (location[0], location[1], location[2] + 6)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=arm_loc)
    arm = bpy.context.active_object
    arm.name = "StreetLight_Arm"
    arm.rotation_euler = (math.radians(90), 0, rotation)

    # Create light
    light_loc = (location[0] + 0.7 * math.cos(rotation),
                 location[1] + 0.7 * math.sin(rotation),
                 location[2] + 5.8)

    bpy.ops.object.light_add(type='POINT', location=light_loc)
    light = bpy.context.active_object
    light.name = "StreetLight_Point"
    light.data.energy = 500  # Brightness
    light.data.color = (1.0, 0.9, 0.7)  # Warm sodium vapor color
    light.data.shadow_soft_size = 0.5
    light.data.cutoff_distance = 20

    # Group into collection
    lights_coll = bpy.data.collections.get("StreetLights")
    if not lights_coll:
        lights_coll = bpy.data.collections.new("StreetLights")
        bpy.context.scene.collection.children.link(lights_coll)

    for obj in [pole, arm, light]:
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        lights_coll.objects.link(obj)

    return pole, arm, light

def add_street_lights_along_roads():
    """Add street lights along major roads"""

    # Get road bounds to place lights
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

    # Place lights in a grid pattern (every ~20 meters)
    spacing = 20
    lights_created = 0

    x = min_x + spacing
    while x < max_x:
        y = min_y + spacing
        while y < max_y:
            # Alternate sides of street
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
    """Set up overall night scene lighting"""

    # Delete existing sun if present
    if "Moon_Ambient" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["Moon_Ambient"])

    # Create dim ambient (moon/city glow)
    bpy.ops.object.light_add(type='SUN', location=(100, 100, 200))
    ambient = bpy.context.active_object
    ambient.name = "Night_Ambient"
    ambient.data.energy = 0.05  # Very dim
    ambient.data.color = (0.5, 0.6, 0.8)  # Cool blue
    ambient.rotation_euler = (math.radians(45), math.radians(30), 0)

    # City glow from below (light pollution) - use POINT instead of removed HEMI
    bpy.ops.object.light_add(type='POINT', location=(0, 0, 100))
    glow = bpy.context.active_object
    glow.name = "City_Glow"
    glow.data.energy = 50
    glow.data.color = (1.0, 0.8, 0.5)  # Warm city light
    glow.data.shadow_soft_size = 10  # Soft, diffuse light

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
    """Set up night sky world"""

    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("Night_Sky")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    nodes.clear()

    # Background node
    bg = nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.02, 0.02, 0.05, 1.0)  # Dark blue night
    bg.inputs['Strength'].default_value = 0.3

    # Output
    output = nodes.new('ShaderNodeOutputWorld')

    links.new(bg.outputs['Background'], output.inputs['Surface'])

    print("World set to night sky")

# =============================================================================
# RUN EVERYTHING
# =============================================================================

print("\n" + "="*50)
print("MSG 1998 - Setting up roads & night scene")
print("="*50 + "\n")

# Create materials
asphalt_mat = create_asphalt_material()
sidewalk_mat = create_sidewalk_material()
print("Materials created")

# Apply to roads
apply_materials_to_roads()

# Setup lighting
setup_night_lighting()
setup_world()

# Add street lights (optional - comment out if too many)
add_street_lights_along_roads()

print("\n" + "="*50)
print("SETUP COMPLETE")
print("="*50)
print("\nWhat was created:")
print("  - NYC_Asphalt_1998 material (dark, rough)")
print("  - NYC_Sidewalk_1998 material")
print("  - Night ambient lighting")
print("  - City glow")
print("  - Street lights along roads")
print("  - Dark night sky world")
print("\nCollections:")
print("  - StreetLights: lamp poles + point lights")
print("  - Lights: ambient lighting")
