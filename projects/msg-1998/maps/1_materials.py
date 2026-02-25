"""
MSG 1998 - Step 1: Road Materials Only
Run this in Blender - just applies materials to roads
"""

import bpy

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

    # Add noise bump
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-300, 0)
    noise.inputs['Scale'].default_value = 50.0

    bump = nodes.new('ShaderNodeBump')
    bump.location = (-150, -100)
    bump.inputs['Strength'].default_value = 0.02

    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])

    return mat

# Get or create material
if "NYC_Asphalt_1998" in bpy.data.materials:
    asphalt = bpy.data.materials["NYC_Asphalt_1998"]
else:
    asphalt = create_asphalt_material()

# Apply to roads
roads_coll = bpy.data.collections.get("Streets_Roads")

if roads_coll:
    count = 0
    for obj in roads_coll.objects:
        if obj.type == 'MESH':
            if len(obj.data.materials) == 0:
                obj.data.materials.append(asphalt)
            else:
                obj.data.materials[0] = asphalt
            count += 1
    print(f"Applied asphalt to {count} road objects")
else:
    print("ERROR: Streets_Roads collection not found")
