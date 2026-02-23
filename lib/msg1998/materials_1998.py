"""
MSG 1998 - Period-Accurate Materials

Material library for 1998 NYC period accuracy.
"""

from typing import Any, Dict, Optional, Tuple

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


# Period-accurate materials for 1998 NYC
MATERIALS_1998: Dict[str, Dict[str, Any]] = {
    # ==========================================================================
    # Building Materials
    # ==========================================================================

    "concrete_1998": {
        "base_color": (0.5, 0.5, 0.5),
        "roughness": 0.85,
        "metallic": 0.0,
        "wear_level": "moderate",
        "description": "Standard NYC concrete with moderate weathering"
    },

    "concrete_dirty": {
        "base_color": (0.4, 0.38, 0.35),
        "roughness": 0.9,
        "metallic": 0.0,
        "wear_level": "heavy",
        "description": "Dirty concrete for older buildings"
    },

    "brick_nyc": {
        "base_color": (0.6, 0.35, 0.25),
        "roughness": 0.9,
        "metallic": 0.0,
        "mortar_visible": True,
        "description": "Standard NYC red brick"
    },

    "brick_brownstone": {
        "base_color": (0.45, 0.3, 0.2),
        "roughness": 0.85,
        "metallic": 0.0,
        "description": "Brownstone facade material"
    },

    "glass_window": {
        "base_color": (0.15, 0.2, 0.25),
        "roughness": 0.05,
        "metallic": 0.0,
        "transmission": 0.9,
        "ior": 1.45,
        "description": "Standard window glass"
    },

    "glass_reflective": {
        "base_color": (0.1, 0.15, 0.2),
        "roughness": 0.02,
        "metallic": 0.3,
        "description": "Reflective office building glass"
    },

    "metal_steel": {
        "base_color": (0.35, 0.35, 0.38),
        "roughness": 0.4,
        "metallic": 0.9,
        "description": "Brushed steel"
    },

    "metal_rusted": {
        "base_color": (0.35, 0.2, 0.1),
        "roughness": 0.8,
        "metallic": 0.6,
        "description": "Rusted metal (fire escapes, etc.)"
    },

    # ==========================================================================
    # Signage (Pre-LED Era)
    # ==========================================================================

    "illuminated_sign_fluorescent": {
        "base_color": (1.0, 1.0, 0.95),
        "emission_color": (1.0, 0.95, 0.8),
        "emission_strength": 2.0,
        "emission_type": "fluorescent",
        "color_temperature": 4500,
        "description": "Fluorescent backlit signage (pre-LED)"
    },

    "neon_sign": {
        "base_color": (1.0, 0.2, 0.3),
        "emission_color": (1.0, 0.3, 0.4),
        "emission_strength": 5.0,
        "emission_type": "neon",
        "glow_radius": 0.02,
        "description": "Neon tube signage"
    },

    "neon_sign_blue": {
        "base_color": (0.2, 0.3, 1.0),
        "emission_color": (0.3, 0.5, 1.0),
        "emission_strength": 5.0,
        "emission_type": "neon",
        "description": "Blue neon signage"
    },

    "neon_sign_green": {
        "base_color": (0.2, 1.0, 0.3),
        "emission_color": (0.3, 1.0, 0.5),
        "emission_strength": 4.0,
        "emission_type": "neon",
        "description": "Green neon signage"
    },

    "printed_signage": {
        "base_color": (0.9, 0.9, 0.85),
        "roughness": 0.7,
        "description": "Printed poster/billboard"
    },

    # ==========================================================================
    # Street Elements
    # ==========================================================================

    "asphalt": {
        "base_color": (0.15, 0.15, 0.15),
        "roughness": 0.95,
        "description": "Street asphalt"
    },

    "asphalt_wet": {
        "base_color": (0.1, 0.1, 0.12),
        "roughness": 0.3,
        "specular": 0.8,
        "description": "Wet asphalt (after rain)"
    },

    "sidewalk_concrete": {
        "base_color": (0.55, 0.52, 0.48),
        "roughness": 0.9,
        "description": "Sidewalk concrete with dirty joints"
    },

    "pay_phone_metal": {
        "base_color": (0.4, 0.4, 0.4),
        "roughness": 0.5,
        "metallic": 0.8,
        "description": "Pay phone enclosure metal"
    },

    "newspaper_box": {
        "base_color": (0.7, 0.2, 0.1),  # Often red or green
        "roughness": 0.6,
        "metallic": 0.3,
        "description": "Newspaper vending box"
    },

    # ==========================================================================
    # Interior Elements
    # ==========================================================================

    "fluorescent_ceiling": {
        "base_color": (1.0, 1.0, 0.95),
        "emission_color": (1.0, 0.98, 0.9),
        "emission_strength": 3.0,
        "description": "Fluorescent ceiling panel"
    },

    "subway_tile": {
        "base_color": (0.9, 0.92, 0.88),
        "roughness": 0.3,
        "description": "White subway tile"
    },

    "subway_tile_dirty": {
        "base_color": (0.7, 0.68, 0.6),
        "roughness": 0.5,
        "description": "Dirty/graffiti-adjacent subway tile"
    },

    "linoleum_floor": {
        "base_color": (0.4, 0.35, 0.3),
        "roughness": 0.4,
        "description": "Commercial linoleum flooring"
    },

    "acoustic_ceiling_tile": {
        "base_color": (0.95, 0.95, 0.92),
        "roughness": 0.95,
        "description": "Drop ceiling acoustic tile"
    },

    # ==========================================================================
    # Vehicle Materials
    # ==========================================================================

    "car_paint_yellow_taxi": {
        "base_color": (0.95, 0.8, 0.1),
        "roughness": 0.3,
        "metallic": 0.2,
        "clearcoat": 0.8,
        "description": "NYC taxi yellow"
    },

    "car_paint_black": {
        "base_color": (0.02, 0.02, 0.02),
        "roughness": 0.2,
        "metallic": 0.3,
        "clearcoat": 1.0,
        "description": "Black car paint (limo, detective)"
    },

    "car_chrome": {
        "base_color": (0.8, 0.8, 0.85),
        "roughness": 0.1,
        "metallic": 1.0,
        "description": "Chrome trim"
    },
}


def create_period_material(
    material_id: str,
    name: Optional[str] = None
):
    """
    Create period-accurate material from library.

    Args:
        material_id: Key from MATERIALS_1998
        name: Optional custom name

    Returns:
        Blender material or None if not available
    """
    if not BLENDER_AVAILABLE:
        return None

    if material_id not in MATERIALS_1998:
        print(f"Unknown material: {material_id}")
        return None

    mat_data = MATERIALS_1998[material_id]
    mat_name = name or f"MSG1998_{material_id}"

    # Check if material already exists
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    # Create new material
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Create Principled BSDF
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')

    # Set basic properties
    if "base_color" in mat_data:
        principled.inputs['Base Color'].default_value = (*mat_data["base_color"], 1.0)

    if "roughness" in mat_data:
        principled.inputs['Roughness'].default_value = mat_data["roughness"]

    if "metallic" in mat_data:
        principled.inputs['Metallic'].default_value = mat_data["metallic"]

    # Emission for signs
    if "emission_color" in mat_data:
        principled.inputs['Emission Color'].default_value = (*mat_data["emission_color"], 1.0)
        principled.inputs['Emission Strength'].default_value = mat_data.get("emission_strength", 1.0)

    # Transmission for glass
    if "transmission" in mat_data:
        principled.inputs['Transmission Weight'].default_value = mat_data["transmission"]

    if "ior" in mat_data:
        principled.inputs['IOR'].default_value = mat_data["ior"]

    # Clearcoat for car paint
    if "clearcoat" in mat_data:
        principled.inputs['Coat Weight'].default_value = mat_data["clearcoat"]

    # Connect nodes
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    # Position nodes
    output.location = (400, 0)
    principled.location = (0, 0)

    # Store metadata
    mat["msg1998_material_id"] = material_id
    mat["msg1998_description"] = mat_data.get("description", "")

    return mat


def get_all_material_ids() -> list:
    """Get list of all available material IDs."""
    return list(MATERIALS_1998.keys())


def get_material_info(material_id: str) -> Optional[Dict[str, Any]]:
    """Get material data without creating instance."""
    return MATERIALS_1998.get(material_id)


def create_signage_material(
    text: str,
    color: Tuple[float, float, float] = (1.0, 0.3, 0.3),
    is_neon: bool = False
):
    """
    Create custom signage material.

    Args:
        text: Sign text (for naming)
        color: Sign color (RGB)
        is_neon: Whether to use neon style emission

    Returns:
        Blender material
    """
    if not BLENDER_AVAILABLE:
        return None

    name = f"MSG1998_Sign_{text[:20]}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')

    if is_neon:
        principled.inputs['Base Color'].default_value = (*color, 1.0)
        principled.inputs['Emission Color'].default_value = (*color, 1.0)
        principled.inputs['Emission Strength'].default_value = 5.0
    else:
        principled.inputs['Base Color'].default_value = (*color, 1.0)
        principled.inputs['Emission Color'].default_value = (*color, 1.0)
        principled.inputs['Emission Strength'].default_value = 2.0

    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    output.location = (400, 0)
    principled.location = (0, 0)

    return mat
