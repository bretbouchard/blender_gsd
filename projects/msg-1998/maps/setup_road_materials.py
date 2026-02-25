"""
MSG-1998 Road System - Materials

Creates materials for all road elements:
- Road pavement (asphalt)
- Sidewalks (concrete)
- Curbs (concrete edge)
- Lane markings (white paint)
- Crosswalks (white stripes)
- Manhole covers (metal)
- Fire hydrants (red)
- Street signs (green/yellow)

Run this after all road elements are created.
"""

import bpy


def create_asphalt_material():
    """Create dark asphalt material for road surface."""
    mat = bpy.data.materials.new("M_Road_Asphalt")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Dark gray color with slight roughness
    bsdf.inputs['Base Color'].default_value = (0.08, 0.08, 0.09, 1.0)  # Dark gray
    bsdf.inputs['Roughness'].default_value = 0.85
    bsdf.inputs['Specular IOR Level'].default_value = 0.1

    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_concrete_material():
    """Create concrete material for sidewalks."""
    mat = bpy.data.materials.new("M_Road_Concrete")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Light gray concrete
    bsdf.inputs['Base Color'].default_value = (0.5, 0.48, 0.45, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.9
    bsdf.inputs['Specular IOR Level'].default_value = 0.15

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_curb_material():
    """Create material for curbs (slightly different from sidewalk)."""
    mat = bpy.data.materials.new("M_Road_Curb")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Medium gray for curbs
    bsdf.inputs['Base Color'].default_value = (0.4, 0.38, 0.36, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.8
    bsdf.inputs['Specular IOR Level'].default_value = 0.2

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_lane_marking_material():
    """Create white material for lane markings."""
    mat = bpy.data.materials.new("M_Road_LaneMarking")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Bright white with slight emission for visibility
    bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.5
    bsdf.inputs['Specular IOR Level'].default_value = 0.3

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_crosswalk_material():
    """Create white material for crosswalk stripes."""
    mat = bpy.data.materials.new("M_Road_Crosswalk")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Bright white
    bsdf.inputs['Base Color'].default_value = (0.98, 0.98, 0.98, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.4
    bsdf.inputs['Specular IOR Level'].default_value = 0.4

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_manhole_material():
    """Create dark metal material for manhole covers."""
    mat = bpy.data.materials.new("M_Road_Manhole")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Dark metallic gray
    bsdf.inputs['Base Color'].default_value = (0.15, 0.15, 0.16, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.6
    bsdf.inputs['Metallic'].default_value = 0.7

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_hydrant_material():
    """Create red material for fire hydrants."""
    mat = bpy.data.materials.new("M_Road_Hydrant")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Fire engine red
    bsdf.inputs['Base Color'].default_value = (0.8, 0.1, 0.05, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.4
    bsdf.inputs['Metallic'].default_value = 0.3

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_sign_pole_material():
    """Create material for sign poles."""
    mat = bpy.data.materials.new("M_Road_SignPole")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Dark gray metal
    bsdf.inputs['Base Color'].default_value = (0.2, 0.2, 0.2, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.5
    bsdf.inputs['Metallic'].default_value = 0.8

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def create_traffic_signal_material():
    """Create material for traffic signal poles."""
    mat = bpy.data.materials.new("M_Road_TrafficSignal")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Dark greenish gray
    bsdf.inputs['Base Color'].default_value = (0.15, 0.18, 0.15, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.4
    bsdf.inputs['Metallic'].default_value = 0.6

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def get_or_create_material(name, create_func):
    """Get existing material or create new one."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    return create_func()


def apply_material_to_collection(coll_name, mat):
    """Apply material to all objects in a collection."""
    if coll_name not in bpy.data.collections:
        return 0

    count = 0
    coll = bpy.data.collections[coll_name]

    for obj in coll.objects:
        if len(obj.material_slots) == 0:
            obj.data.materials.append(mat)
        else:
            obj.material_slots[0].material = mat
        count += 1

    return count


def apply_materials_by_prefix(collection_name, prefix, mat):
    """Apply material to objects with specific name prefix."""
    if collection_name not in bpy.data.collections:
        return 0

    count = 0
    coll = bpy.data.collections[collection_name]

    for obj in coll.objects:
        if obj.name.startswith(prefix):
            if len(obj.material_slots) == 0:
                obj.data.materials.append(mat)
            else:
                obj.material_slots[0].material = mat
            count += 1

    return count


def create_all_road_materials():
    """Create all road materials."""

    print("\n" + "=" * 50)
    print("Creating Road Materials")
    print("=" * 50)

    materials = {
        'asphalt': get_or_create_material("M_Road_Asphalt", create_asphalt_material),
        'concrete': get_or_create_material("M_Road_Concrete", create_concrete_material),
        'curb': get_or_create_material("M_Road_Curb", create_curb_material),
        'lane_marking': get_or_create_material("M_Road_LaneMarking", create_lane_marking_material),
        'crosswalk': get_or_create_material("M_Road_Crosswalk", create_crosswalk_material),
        'manhole': get_or_create_material("M_Road_Manhole", create_manhole_material),
        'hydrant': get_or_create_material("M_Road_Hydrant", create_hydrant_material),
        'sign_pole': get_or_create_material("M_Road_SignPole", create_sign_pole_material),
        'traffic_signal': get_or_create_material("M_Road_TrafficSignal", create_traffic_signal_material),
    }

    print("Created materials:")
    for name, mat in materials.items():
        print(f"  ✓ {mat.name}")

    return materials


def apply_all_materials(materials):
    """Apply materials to all road elements."""

    print("\n" + "=" * 50)
    print("Applying Materials")
    print("=" * 50)

    # Crosswalks
    count = apply_material_to_collection("Crosswalks", materials['crosswalk'])
    print(f"  Crosswalks: {count} objects")

    # Street Furniture - by prefix
    if "Street_Furniture" in bpy.data.collections:
        coll = bpy.data.collections["Street_Furniture"]

        manhole_count = apply_materials_by_prefix("Street_Furniture", "Manhole_", materials['manhole'])
        hydrant_count = apply_materials_by_prefix("Street_Furniture", "Hydrant_", materials['hydrant'])
        sign_count = apply_materials_by_prefix("Street_Furniture", "StreetSign_", materials['sign_pole'])
        signal_count = apply_materials_by_prefix("Street_Furniture", "TrafficSignal_", materials['traffic_signal'])

        print(f"  Manholes: {manhole_count}")
        print(f"  Hydrants: {hydrant_count}")
        print(f"  Street Signs: {sign_count}")
        print(f"  Traffic Signals: {signal_count}")

    print("\n" + "=" * 50)
    print("Materials Applied!")
    print("=" * 50)


def setup_road_materials():
    """Main function to create and apply all road materials."""

    materials = create_all_road_materials()
    apply_all_materials(materials)

    return materials


# Run in Blender
if __name__ == "__main__":
    setup_road_materials()
