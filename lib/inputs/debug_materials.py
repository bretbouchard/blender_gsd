"""
Debug Material Utilities for Universal Input System

Provides distinct colors for each section (A_Top, A_Mid, A_Bot, B_Top, B_Mid, B_Bot)
to help visualize zone separation during development.

Usage:
    from lib.inputs.debug_materials import create_all_debug_materials

    # Create debug materials with default rainbow palette
    materials = create_all_debug_materials()

    # Use a different preset
    materials = create_all_debug_materials(preset="grayscale")

    # Access individual materials
    a_top_mat = materials["A_Top"]
"""

from __future__ import annotations
import bpy
from typing import Dict, Tuple, Optional


# Default rainbow color palette (6 sections)
DEBUG_COLORS: Dict[str, Tuple[float, float, float]] = {
    "A_Top": (1.0, 0.3, 0.3),    # Red
    "A_Mid": (1.0, 0.6, 0.2),    # Orange
    "A_Bot": (1.0, 1.0, 0.3),    # Yellow
    "B_Top": (0.3, 0.8, 0.3),    # Green
    "B_Mid": (0.3, 0.5, 1.0),    # Blue
    "B_Bot": (0.7, 0.3, 0.9),    # Purple
}


# Preset palettes for different visualization needs (6 sections each)
DEBUG_PRESETS: Dict[str, Dict[str, Tuple[float, float, float]]] = {
    "rainbow": {
        "A_Top": (1.0, 0.3, 0.3),    # Red
        "A_Mid": (1.0, 0.6, 0.2),    # Orange
        "A_Bot": (1.0, 1.0, 0.3),    # Yellow
        "B_Top": (0.3, 0.8, 0.3),    # Green
        "B_Mid": (0.3, 0.5, 1.0),    # Blue
        "B_Bot": (0.7, 0.3, 0.9),    # Purple
    },
    "grayscale": {
        "A_Top": (0.9, 0.9, 0.9),    # 90% gray
        "A_Mid": (0.7, 0.7, 0.7),    # 70% gray
        "A_Bot": (0.5, 0.5, 0.5),    # 50% gray
        "B_Top": (0.35, 0.35, 0.35),    # 35% gray
        "B_Mid": (0.2, 0.2, 0.2),    # 20% gray
        "B_Bot": (0.1, 0.1, 0.1),    # 10% gray
    },
    "complementary": {
        "A_Top": (1.0, 0.0, 0.5),    # Hot pink
        "A_Mid": (0.0, 1.0, 0.5),    # Spring green
        "A_Bot": (0.5, 0.0, 1.0),    # Purple
        "B_Top": (0.5, 1.0, 0.0),    # Chartreuse
        "B_Mid": (0.0, 0.5, 1.0),    # Azure
        "B_Bot": (1.0, 0.5, 0.0),    # Orange
    },
    "heat_map": {
        "A_Top": (1.0, 0.0, 0.0),    # Red (hottest)
        "A_Mid": (1.0, 0.5, 0.0),    # Orange
        "A_Bot": (1.0, 1.0, 0.0),    # Yellow
        "B_Top": (0.0, 1.0, 0.5),    # Cyan-green
        "B_Mid": (0.0, 0.5, 1.0),    # Light blue
        "B_Bot": (0.0, 0.0, 1.0),    # Blue (coldest)
    },
}


def create_debug_material(
    name: str,
    color: Tuple[float, float, float],
    metallic: float = 0.0,
    roughness: float = 0.5
) -> bpy.types.Material:
    """
    Create a simple Principled BSDF material with the given color.

    Uses direct API calls only - no bpy.ops.

    Args:
        name: Material name (will be prefixed with "Debug_")
        color: RGB color tuple (0-1 range)
        metallic: Metallic value (default 0.0)
        roughness: Roughness value (default 0.5)

    Returns:
        The created Material object
    """
    mat_name = f"Debug_{name}"

    # Remove existing material with same name
    if mat_name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[mat_name])

    # Create new material
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True

    # Get node tree and clear it
    nt = mat.node_tree
    nt.nodes.clear()

    # Create Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.label = f"Debug_{name}_BSDF"
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness

    # Create Material Output
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    output.label = "Output"

    # Link BSDF to Output
    nt.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Position nodes for readability
    bsdf.location = (-200, 0)
    output.location = (0, 0)

    return mat


def create_debug_palette(preset_name: str = "rainbow") -> Dict[str, Tuple[float, float, float]]:
    """
    Get a color palette by preset name.

    Args:
        preset_name: Name of the preset ("rainbow", "grayscale", "complementary", "heat_map")

    Returns:
        Dictionary mapping section names to RGB color tuples

    Raises:
        ValueError: If preset name is not found
    """
    if preset_name not in DEBUG_PRESETS:
        available = ", ".join(DEBUG_PRESETS.keys())
        raise ValueError(f"Preset '{preset_name}' not found. Available: {available}")

    return DEBUG_PRESETS[preset_name].copy()


def create_all_debug_materials(
    preset: str = "rainbow",
    metallic: float = 0.0,
    roughness: float = 0.5
) -> Dict[str, bpy.types.Material]:
    """
    Create debug materials for all sections using a preset palette.

    Args:
        preset: Preset name ("rainbow", "grayscale", "complementary", "heat_map")
        metallic: Metallic value for all materials
        roughness: Roughness value for all materials

    Returns:
        Dictionary mapping section names ("A_Top", "A_Mid", "A_Bot", "B_Top", "B_Mid", "B_Bot")
        to Material objects
    """
    colors = create_debug_palette(preset)
    materials = {}

    for section_name, color in colors.items():
        mat = create_debug_material(
            section_name,
            color,
            metallic=metallic,
            roughness=roughness
        )
        materials[section_name] = mat

    return materials


def get_debug_color(section: str, preset: str = "rainbow") -> Tuple[float, float, float]:
    """
    Get the debug color for a specific section from a preset.

    Args:
        section: Section name ("A_Top", "A_Mid", "A_Bot", "B_Top", "B_Mid", "B_Bot")
        preset: Preset name

    Returns:
        RGB color tuple

    Raises:
        ValueError: If section or preset not found
    """
    colors = create_debug_palette(preset)

    if section not in colors:
        available = ", ".join(colors.keys())
        raise ValueError(f"Section '{section}' not found. Available: {available}")

    return colors[section]


# Section names for iteration (6 sections)
SECTION_NAMES = ["A_Top", "A_Mid", "A_Bot", "B_Top", "B_Mid", "B_Bot"]
