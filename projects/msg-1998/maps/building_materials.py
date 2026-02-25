"""
MSG-1998 Building Materials System

Creates and applies realistic building materials based on NYC Midtown architecture styles:
- Pre-War Masonry (1900-1940): Brownstone, brick, limestone
- Post-War Modern (1940-1970): Glass curtain wall, concrete
- Late Modern (1970-1990): Tinted glass, granite cladding
- Contemporary (1990s): Clear glass, metal panels
- MSG Arena (1968): Distinctive white cylindrical structure

Building categories based on actual NYC architecture:
"""

import bpy
import random
from mathutils import Color

# =============================================================================
# MATERIAL DEFINITIONS
# =============================================================================

# Building style categories with material assignments
BUILDING_STYLES = {
    # Pre-War Masonry (1900-1940)
    "prewar_brownstone": {
        "description": "Brown sandstone townhouses and low-rises",
        "base_color": (0.45, 0.32, 0.25),  # Warm brown
        "roughness": 0.9,
        "metallic": 0.0,
        "bump_strength": 0.03,
        "noise_scale": 20.0,
    },
    "prewar_brick_red": {
        "description": "Red brick facades",
        "base_color": (0.55, 0.25, 0.20),  # Red brick
        "roughness": 0.85,
        "metallic": 0.0,
        "bump_strength": 0.02,
        "noise_scale": 30.0,
    },
    "prewar_brick_brown": {
        "description": "Brown brick facades",
        "base_color": (0.40, 0.28, 0.22),  # Brown brick
        "roughness": 0.85,
        "metallic": 0.0,
        "bump_strength": 0.02,
        "noise_scale": 30.0,
    },
    "prewar_limestone": {
        "description": "Limestone cladding",
        "base_color": (0.85, 0.82, 0.75),  # Off-white limestone
        "roughness": 0.7,
        "metallic": 0.0,
        "bump_strength": 0.015,
        "noise_scale": 15.0,
    },

    # Post-War Modern (1940-1970)
    "postwar_concrete": {
        "description": "Exposed concrete facades",
        "base_color": (0.65, 0.65, 0.62),  # Gray concrete
        "roughness": 0.8,
        "metallic": 0.0,
        "bump_strength": 0.025,
        "noise_scale": 40.0,
    },
    "postwar_glass_green": {
        "description": "Early glass curtain walls (green tint)",
        "base_color": (0.30, 0.45, 0.40),  # Green tint
        "roughness": 0.05,
        "metallic": 0.3,
        "bump_strength": 0.0,
        "noise_scale": 0.0,
    },

    # Late Modern (1970-1990)
    "latemodern_glass_bronze": {
        "description": "Bronze/tinted glass (Seagram Building style)",
        "base_color": (0.35, 0.28, 0.20),  # Bronze/amber tint
        "roughness": 0.03,
        "metallic": 0.4,
        "bump_strength": 0.0,
        "noise_scale": 0.0,
    },
    "latemodern_granite": {
        "description": "Granite cladding",
        "base_color": (0.45, 0.42, 0.40),  # Dark granite
        "roughness": 0.4,
        "metallic": 0.1,
        "bump_strength": 0.01,
        "noise_scale": 80.0,
    },
    "latemodern_metal_panel": {
        "description": "Metal panel facades",
        "base_color": (0.55, 0.55, 0.58),  # Silver metal
        "roughness": 0.3,
        "metallic": 0.7,
        "bump_strength": 0.0,
        "noise_scale": 0.0,
    },

    # Contemporary (1990s)
    "contemporary_glass_clear": {
        "description": "Clear glass curtain walls",
        "base_color": (0.50, 0.60, 0.65),  # Slight blue tint
        "roughness": 0.02,
        "metallic": 0.2,
        "bump_strength": 0.0,
        "noise_scale": 0.0,
    },
    "contemporary_glass_blue": {
        "description": "Blue tinted glass",
        "base_color": (0.35, 0.50, 0.65),  # Blue tint
        "roughness": 0.02,
        "metallic": 0.2,
        "bump_strength": 0.0,
        "noise_scale": 0.0,
    },

    # Special Buildings
    "msg_arena": {
        "description": "Madison Square Garden - white cylindrical",
        "base_color": (0.92, 0.92, 0.90),  # Off-white
        "roughness": 0.6,
        "metallic": 0.0,
        "bump_strength": 0.01,
        "noise_scale": 10.0,
    },
    "empire_state": {
        "description": "Empire State Building - Art Deco limestone",
        "base_color": (0.78, 0.75, 0.70),  # Warm gray limestone
        "roughness": 0.5,
        "metallic": 0.0,
        "bump_strength": 0.02,
        "noise_scale": 25.0,
    },
    "penn_station": {
        "description": "Penn Station area buildings",
        "base_color": (0.55, 0.53, 0.50),  # Medium gray
        "roughness": 0.6,
        "metallic": 0.0,
        "bump_strength": 0.02,
        "noise_scale": 35.0,
    },

    # Generic fallbacks
    "generic_office_gray": {
        "description": "Generic office building - gray",
        "base_color": (0.55, 0.55, 0.55),
        "roughness": 0.6,
        "metallic": 0.0,
        "bump_strength": 0.02,
        "noise_scale": 40.0,
    },
    "generic_residential": {
        "description": "Generic residential - brick tones",
        "base_color": (0.55, 0.42, 0.35),
        "roughness": 0.8,
        "metallic": 0.0,
        "bump_strength": 0.025,
        "noise_scale": 30.0,
    },
}

# Building name to style mapping
BUILDING_STYLE_MAP = {
    # Major Landmarks
    "Empire State Building": "empire_state",
    "Madison Square Garden": "msg_arena",
    "Pennsylvania Station": "penn_station",
    "Pennsylvania Plaza": "penn_station",
    "James A. Farley Building": "prewar_limestone",
    "James A. Farley Post Office": "prewar_limestone",

    # Penn Plaza Office Buildings
    "PENN 1": "latemodern_granite",
    "PENN 2": "latemodern_granite",
    "PENN 11": "latemodern_granite",
    "Manhattan West": "contemporary_glass_blue",
    "One Manhattan West": "contemporary_glass_blue",
    "Two Manhattan West": "contemporary_glass_blue",
    "Four Manhattan West": "contemporary_glass_blue",
    "Five Manhattan West": "postwar_glass_green",

    # Hotels - Historic
    "New Yorker by Lotte Hotels": "prewar_brick_brown",
    "Martinique New York": "prewar_brick_red",
    "Hotel Stanford": "prewar_brick_brown",
    "The Gregorian Hotel": "prewar_brownstone",

    # Hotels - Modern
    "Hilton Garden Inn": "latemodern_metal_panel",
    "Stewart Hotel": "postwar_concrete",
    "Hyatt Place": "contemporary_glass_clear",
    "Hotel Indigo": "contemporary_glass_blue",
    "Renaissance": "latemodern_granite",
    "Hampton Inn": "latemodern_metal_panel",
    "Embassy Suites by Hilton": "contemporary_glass_clear",
    "Crowne Plaza HY36": "contemporary_glass_blue",
    "DoubleTree": "latemodern_granite",
    "Virgin Hotel": "contemporary_glass_clear",
    "Pendry Manhattan West": "contemporary_glass_blue",

    # Office Buildings
    "Five Bryant Park": "latemodern_granite",
    "Herald Towers": "prewar_brick_red",
    "Herald Square Building": "prewar_brick_brown",
    "Lefcourt Manhattan Building": "prewar_limestone",
    "Nelson Tower": "prewar_limestone",
    "Manhattan Center": "prewar_brick_brown",
    "Master Printers Building": "prewar_brick_red",
    "Millinery Building": "prewar_brick_brown",
    "Tower 111": "latemodern_granite",
    "Tower 31": "latemodern_granite",
    "Solari": "contemporary_glass_blue",
    "World Apparel Center": "latemodern_metal_panel",

    # Retail
    "Macy's": "prewar_brownstone",
    "Manhattan Mall": "postwar_concrete",

    # Residential
    "Penn South": "postwar_concrete",
    "Penn South Building 8": "postwar_concrete",
    "Penn South Building 9": "postwar_concrete",
    "Penn South Housing": "postwar_concrete",
    "Chelsea Houses": "postwar_concrete",
    "John Lovejoy Elliott Houses": "postwar_concrete",
    "London Terrace": "prewar_brick_red",
    "The NOMA": "contemporary_glass_clear",
    "Abington House": "contemporary_glass_blue",

    # Churches
    "Church of The Holy Innocents": "prewar_brownstone",
    "Church of St. John the Baptist": "prewar_brownstone",
    "Church of the Holy Apostles": "prewar_brick_red",
    "Church of Saint Francis of Assisi": "prewar_brownstone",
    "St. Michael's Church": "prewar_brownstone",
    "St. Columba Catholic Church": "prewar_brick_red",
    "West Side Jewish Center": "prewar_brownstone",

    # Educational
    "Fashion Institute of Technology": "postwar_concrete",
    "David Dubinsky Student Center": "postwar_concrete",
    "Kaufman Hall": "postwar_concrete",
    "Marvin Feldman Center": "postwar_concrete",
    "Fred P. Pomerantz Art": "postwar_concrete",
    "Shirley Goodman Resource Center": "postwar_concrete",
    "Alumni Hall": "postwar_concrete",
    "Coed Hall": "postwar_concrete",
    "Nagler Hall": "postwar_concrete",
    "Public School 33": "prewar_brick_red",
    "Saint Francis of Assisi School": "prewar_brownstone",
    "St. Columba School": "prewar_brick_red",
}


def create_building_material(style_name, style_data):
    """Create a building material based on style data."""
    mat_name = f"MSG_Building_{style_name}"
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output node
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)

    # Principled BSDF
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (200, 0)

    # Set base properties
    base_color = style_data.get("base_color", (0.5, 0.5, 0.5, 1.0))
    if len(base_color) == 3:
        base_color = (*base_color, 1.0)
    principled.inputs['Base Color'].default_value = base_color
    principled.inputs['Roughness'].default_value = style_data.get("roughness", 0.5)
    principled.inputs['Metallic'].default_value = style_data.get("metallic", 0.0)

    # Add slight random variation to color
    variation = nodes.new('ShaderNodeTexNoise')
    variation.location = (-400, 200)
    variation.inputs['Scale'].default_value = 5.0
    variation.inputs['Detail'].default_value = 2.0

    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (-200, 200)
    color_ramp.color_ramp.elements[0].color = (0.95, 0.95, 0.95, 1.0)
    color_ramp.color_ramp.elements[1].color = (1.05, 1.05, 1.05, 1.0)

    mix_color = nodes.new('ShaderNodeMixRGB')
    mix_color.location = (0, 0)
    mix_color.inputs[0].default_value = 0.15  # Subtle variation
    mix_color.inputs[1].default_value = base_color

    links.new(variation.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], mix_color.inputs[2])
    links.new(mix_color.outputs['Color'], principled.inputs['Base Color'])

    # Add bump if specified
    bump_strength = style_data.get("bump_strength", 0.0)
    if bump_strength > 0:
        noise = nodes.new('ShaderNodeTexNoise')
        noise.location = (-400, -200)
        noise.inputs['Scale'].default_value = style_data.get("noise_scale", 30.0)
        noise.inputs['Detail'].default_value = 4.0

        bump = nodes.new('ShaderNodeBump')
        bump.location = (-200, -200)
        bump.inputs['Strength'].default_value = bump_strength

        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], principled.inputs['Normal'])

    # Link to output
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    return mat


def get_style_for_building(building_name):
    """Determine the appropriate style for a building."""
    # Clean name
    clean_name = building_name.replace(".001", "").replace(".002", "").strip()

    # Direct match
    if clean_name in BUILDING_STYLE_MAP:
        return BUILDING_STYLE_MAP[clean_name]

    # Partial match
    for name, style in BUILDING_STYLE_MAP.items():
        if name.lower() in clean_name.lower():
            return style
        if clean_name.lower() in name.lower():
            return style

    # Infer from building type keywords
    name_lower = clean_name.lower()

    if "church" in name_lower or "st." in name_lower or "saint" in name_lower or "cathedral" in name_lower:
        return "prewar_brownstone"

    if "hotel" in name_lower or "inn" in name_lower or "suites" in name_lower:
        # Randomly assign hotel style based on era inference
        if "historic" in name_lower or "vintage" in name_lower:
            return "prewar_brick_brown"
        return random.choice(["latemodern_granite", "contemporary_glass_clear"])

    if "tower" in name_lower:
        return "latemodern_granite"

    if "plaza" in name_lower or "penn" in name_lower:
        return "penn_station"

    if "mall" in name_lower or "retail" in name_lower:
        return "postwar_concrete"

    if "house" in name_lower or "housing" in name_lower or "apartment" in name_lower:
        return "generic_residential"

    if "school" in name_lower or "college" in name_lower or "university" in name_lower or "hall" in name_lower:
        return "postwar_concrete"

    # Default
    return "generic_office_gray"


def create_all_materials():
    """Create all building materials."""
    materials = {}

    print("\n" + "=" * 70)
    print("Creating Building Materials")
    print("=" * 70)

    for style_name, style_data in BUILDING_STYLES.items():
        mat_name = f"MSG_Building_{style_name}"

        # Remove existing if present
        if mat_name in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[mat_name])

        mat = create_building_material(style_name, style_data)
        materials[style_name] = mat
        print(f"  Created: {mat_name}")

    print(f"\nTotal materials created: {len(materials)}")
    return materials


def apply_materials_to_buildings():
    """Apply appropriate materials to all buildings."""

    print("\n" + "=" * 70)
    print("Applying Materials to Buildings")
    print("=" * 70)

    # Get Buildings collection
    if "Buildings" not in bpy.data.collections:
        print("ERROR: Buildings collection not found!")
        return

    buildings_coll = bpy.data.collections["Buildings"]
    buildings = [obj for obj in buildings_coll.objects if obj.type == 'MESH']

    # Create materials if needed
    materials = {}
    for style_name, style_data in BUILDING_STYLES.items():
        mat_name = f"MSG_Building_{style_name}"
        if mat_name in bpy.data.materials:
            materials[style_name] = bpy.data.materials[mat_name]
        else:
            materials[style_name] = create_building_material(style_name, style_data)

    # Apply materials
    applied = {}
    for obj in buildings:
        style = get_style_for_building(obj.name)
        mat = materials[style]

        # Clear existing materials
        obj.data.materials.clear()
        obj.data.materials.append(mat)

        if style not in applied:
            applied[style] = []
        applied[style].append(obj.name)

    # Print summary
    print(f"\nApplied materials to {len(buildings)} buildings:")
    for style, buildings_list in sorted(applied.items()):
        print(f"\n  {style} ({len(buildings_list)} buildings):")
        for name in buildings_list[:5]:
            print(f"    - {name}")
        if len(buildings_list) > 5:
            print(f"    ... and {len(buildings_list) - 5} more")

    print("\n" + "=" * 70)
    print("Material Application Complete!")
    print("=" * 70)


def apply_materials_to_other_ground():
    """Apply appropriate materials to other_ground collection."""

    print("\n" + "=" * 70)
    print("Applying Materials to other_ground")
    print("=" * 70)

    if "other_ground" not in bpy.data.collections:
        print("ERROR: other_ground collection not found!")
        return

    other_coll = bpy.data.collections["other_ground"]
    items = [obj for obj in other_coll.objects if obj.type == 'MESH']

    # Create materials if needed
    materials = {}
    for style_name, style_data in BUILDING_STYLES.items():
        mat_name = f"MSG_Building_{style_name}"
        if mat_name in bpy.data.materials:
            materials[style_name] = bpy.data.materials[mat_name]
        else:
            materials[style_name] = create_building_material(style_name, style_data)

    # Also create a park/ground material
    park_mat_name = "MSG_Park_Ground"
    if park_mat_name not in bpy.data.materials:
        park_mat = bpy.data.materials.new(name=park_mat_name)
        park_mat.use_nodes = True
        nodes = park_mat.node_tree.nodes
        links = park_mat.node_tree.links
        nodes.clear()

        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (400, 0)

        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (0, 0)
        principled.inputs['Base Color'].default_value = (0.25, 0.40, 0.20, 1.0)  # Grass green
        principled.inputs['Roughness'].default_value = 0.95

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    else:
        park_mat = bpy.data.materials[park_mat_name]

    # Apply materials
    ground_count = 0
    building_count = 0

    for obj in items:
        # Get object height
        from mathutils import Vector
        bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        height = max(v.z for v in bbox) - min(v.z for v in bbox)

        if height < 1.0:
            # Flat ground - use park material
            obj.data.materials.clear()
            obj.data.materials.append(park_mat)
            ground_count += 1
        else:
            # Building-like structure
            style = get_style_for_building(obj.name)
            mat = materials[style]
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            building_count += 1

    print(f"\nApplied materials to {len(items)} items:")
    print(f"  Park/Ground materials: {ground_count}")
    print(f"  Building materials: {building_count}")

    print("\n" + "=" * 70)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function to create and apply all building materials."""

    print("\n" + "=" * 80)
    print("MSG-1998 Building Materials System")
    print("=" * 80)

    # Step 1: Create all materials
    materials = create_all_materials()

    # Step 2: Apply to Buildings collection
    apply_materials_to_buildings()

    # Step 3: Apply to other_ground collection
    apply_materials_to_other_ground()

    print("\n" + "=" * 80)
    print("Building Materials Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
