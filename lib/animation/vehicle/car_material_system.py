"""
Car Materials System - KitBash Integration

Connects procedural cars to KitBash CarMaterials plugins for
high-quality car paint, metal, and glass materials.

Supports:
- CarMaterials_Glossy (shiny car paint)
- CarMaterials_Matt (matte finishes)
- CarMaterials_Metallic (metal flake paints)

Usage:
    from lib.animation.vehicle.car_material_system import (
        CarMaterialSystem, PaintType
    )

    # Create material system
    mat_system = CarMaterialSystem(
        kitbash_path="/Volumes/Storage/3d/kitbash/converted_assets"
    )

    # Apply glossy paint to car
    mat_system.apply_paint(
        car_object=my_car,
        paint_type=PaintType.GLOSSY,
        color="shiny_blue"
    )

    # Or apply by material preset
    mat_system.apply_preset(car_object, "racing_red")
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum
import json


class PaintType(Enum):
    """Type of car paint finish."""
    GLOSSY = "glossy"
    MATT = "matt"
    METALLIC = "metallic"


@dataclass
class PaintColor:
    """Paint color definition."""
    name: str
    display_name: str
    paint_type: PaintType
    blend_file: str
    material_name: str
    rgb: Tuple[float, float, float] = (0.5, 0.5, 0.5)


# Color definitions for each paint type
GLOSSY_COLORS = {
    "shiny_black": ("Shiny Black", (0.02, 0.02, 0.02)),
    "shiny_blue": ("Shiny Blue", (0.1, 0.2, 0.7)),
    "shiny_brown": ("Shiny Brown", (0.4, 0.25, 0.15)),
    "shiny_burgundy_dark": ("Shiny Burgundy Dark", (0.3, 0.05, 0.1)),
    "shiny_champagne": ("Shiny Champagne", (0.9, 0.85, 0.7)),
    "shiny_dark_blue": ("Shiny Dark Blue", (0.05, 0.1, 0.3)),
    "shiny_dark_green": ("Shiny Dark Green", (0.05, 0.2, 0.1)),
    "shiny_dark_grey": ("Shiny Dark Grey", (0.15, 0.15, 0.15)),
    "shiny_dark_red": ("Shiny Dark Red", (0.4, 0.05, 0.05)),
    "shiny_fuschia": ("Shiny Fuschia", (0.8, 0.2, 0.6)),
    "shiny_green": ("Shiny Green", (0.2, 0.6, 0.2)),
    "shiny_green_light": ("Shiny Green Light", (0.4, 0.8, 0.4)),
}

MATT_COLORS = {
    "matt_black": ("Matt Black", (0.05, 0.05, 0.05)),
    "matt_blue": ("Matt Blue", (0.15, 0.25, 0.5)),
    "matt_brown": ("Matt Brown", (0.35, 0.25, 0.15)),
    "matt_dark_grey": ("Matt Dark Grey", (0.2, 0.2, 0.2)),
    "matt_green": ("Matt Green", (0.2, 0.4, 0.2)),
    "matt_grey": ("Matt Grey", (0.4, 0.4, 0.4)),
    "matt_orange": ("Matt Orange", (0.8, 0.4, 0.1)),
    "matt_purple": ("Matt Purple", (0.4, 0.2, 0.5)),
    "matt_red": ("Matt Red", (0.6, 0.1, 0.1)),
    "matt_white": ("Matt White", (0.9, 0.9, 0.9)),
    "matt_yellow": ("Matt Yellow", (0.8, 0.75, 0.2)),
}

METALLIC_COLORS = {
    "metallic_black": ("Metallic Black", (0.03, 0.03, 0.03)),
    "metallic_blue": ("Metallic Blue", (0.1, 0.15, 0.4)),
    "metallic_brown": ("Metallic Brown", (0.3, 0.2, 0.12)),
    "metallic_gold": ("Metallic Gold", (0.8, 0.65, 0.2)),
    "metallic_green": ("Metallic Green", (0.1, 0.35, 0.15)),
    "metallic_grey": ("Metallic Grey", (0.35, 0.35, 0.38)),
    "metallic_purple": ("Metallic Purple", (0.3, 0.15, 0.4)),
    "metallic_red": ("Metallic Red", (0.5, 0.08, 0.1)),
    "metallic_silver": ("Metallic Silver", (0.7, 0.7, 0.72)),
    "metallic_turquoise": ("Metallic Turquoise", (0.15, 0.5, 0.5)),
}

# Preset combinations
PAINT_PRESETS = {
    "racing_red": ("glossy", "shiny_dark_red"),
    "racing_blue": ("glossy", "shiny_blue"),
    "muscle_black": ("glossy", "shiny_black"),
    "luxury_champagne": ("glossy", "shiny_champagne"),
    "tactical_matt_green": ("matt", "matt_green"),
    "stealth_black": ("matt", "matt_black"),
    "premium_gold": ("metallic", "metallic_gold"),
    "premium_silver": ("metallic", "metallic_silver"),
    "sport_blue": ("metallic", "metallic_blue"),
    "vintage_brown": ("matt", "matt_brown"),
}


class CarMaterialSystem:
    """
    Manages car paint materials from KitBash plugins.

    Loads materials from converted KitBash assets and applies them
    to procedural or imported car models.
    """

    def __init__(
        self,
        kitbash_path: Optional[str] = None,
    ):
        """
        Initialize car material system.

        Args:
            kitbash_path: Path to KitBash converted assets
        """
        self.kitbash_path = Path(kitbash_path) if kitbash_path else None

        # Default paths
        if self.kitbash_path is None:
            self.kitbash_path = Path("/Volumes/Storage/3d/kitbash/converted_assets")

        self.plugins_path = self.kitbash_path / "plugins"

        # Material library (loaded on demand)
        self._material_cache: Dict[str, Any] = {}
        self._loaded_libraries: set = set()

        # Blender check
        self._blender_available = False
        self._bpy = None
        try:
            import bpy
            self._bpy = bpy
            self._blender_available = True
        except ImportError:
            pass

    def list_available_colors(self, paint_type: PaintType) -> List[str]:
        """
        List available colors for a paint type.

        Args:
            paint_type: Type of paint (GLOSSY, MATT, METALLIC)

        Returns:
            List of color names
        """
        if paint_type == PaintType.GLOSSY:
            return list(GLOSSY_COLORS.keys())
        elif paint_type == PaintType.MATT:
            return list(MATT_COLORS.keys())
        elif paint_type == PaintType.METALLIC:
            return list(METALLIC_COLORS.keys())
        return []

    def list_presets(self) -> List[str]:
        """List available paint presets."""
        return list(PAINT_PRESETS.keys())

    def get_color_rgb(self, color_name: str) -> Tuple[float, float, float]:
        """
        Get RGB values for a color name.

        Args:
            color_name: Name of the color

        Returns:
            RGB tuple
        """
        # Check all color dictionaries
        for colors in [GLOSSY_COLORS, MATT_COLORS, METALLIC_COLORS]:
            if color_name in colors:
                return colors[color_name][1]
        return (0.5, 0.5, 0.5)

    def apply_paint(
        self,
        car_object: Any,
        paint_type: PaintType,
        color: str,
        slot: int = 0,
    ) -> bool:
        """
        Apply KitBash paint material to car object.

        Args:
            car_object: Blender car object
            paint_type: Type of paint
            color: Color name
            slot: Material slot index

        Returns:
            True if successful
        """
        if not self._blender_available:
            return False

        # Get the blend file path
        blend_file = self._get_blend_file(paint_type, color)
        if blend_file is None:
            # Fallback: create simple material
            return self._create_fallback_material(car_object, paint_type, color, slot)

        # Try to load material from blend file
        material = self._load_material_from_blend(blend_file, color)
        if material is None:
            return self._create_fallback_material(car_object, paint_type, color, slot)

        # Apply to object
        return self._apply_material_to_object(car_object, material, slot)

    def apply_preset(
        self,
        car_object: Any,
        preset_name: str,
    ) -> bool:
        """
        Apply a named paint preset to car.

        Args:
            car_object: Blender car object
            preset_name: Preset name (e.g., "racing_red")

        Returns:
            True if successful
        """
        if preset_name not in PAINT_PRESETS:
            return False

        paint_type_str, color = PAINT_PRESETS[preset_name]
        paint_type = PaintType(paint_type_str)

        return self.apply_paint(car_object, paint_type, color)

    def apply_paint_to_parts(
        self,
        car_parts: Dict[str, Any],
        paint_type: PaintType,
        color: str,
    ) -> Dict[str, bool]:
        """
        Apply paint to specific car parts.

        Args:
            car_parts: Dictionary of part_name -> object
            paint_type: Type of paint
            color: Color name

        Returns:
            Dictionary of part_name -> success
        """
        results = {}

        # Parts that get body paint
        body_parts = ["body", "hood", "trunk", "doors", "fender_fl", "fender_fr",
                      "fender_rl", "fender_rr", "roof", "quarter_panel"]

        for part_name, part_obj in car_parts.items():
            if part_name.lower() in body_parts:
                results[part_name] = self.apply_paint(part_obj, paint_type, color)
            else:
                results[part_name] = True  # Skip non-body parts

        return results

    def apply_glass_material(
        self,
        glass_object: Any,
        tint: float = 0.3,
    ) -> bool:
        """
        Apply glass material to windows.

        Args:
            glass_object: Window/windshield object
            tint: Tint level (0=clear, 1=blackout)

        Returns:
            True if successful
        """
        if not self._blender_available:
            return False

        mat_name = f"car_glass_tint_{int(tint * 100)}"

        # Check cache
        if mat_name in self._material_cache:
            return self._apply_material_to_object(glass_object, self._material_cache[mat_name])

        # Create glass material
        mat = self._bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Glass BSDF
        glass = nodes.new("ShaderNodeBsdfGlass")
        glass.inputs["Color"].default_value = (0.1, 0.15, 0.2, 1.0 - tint)
        glass.inputs["Roughness"].default_value = 0.02
        glass.inputs["IOR"].default_value = 1.45

        # Mix with transparency for tint
        mix = nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = tint

        transparent = nodes.new("ShaderNodeBsdfTransparent")
        transparent.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1.0)

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        # Links
        links.new(transparent.outputs["BSDF"], mix.inputs[1])
        links.new(glass.outputs["BSDF"], mix.inputs[2])
        links.new(mix.outputs["Shader"], output.inputs["Surface"])

        self._material_cache[mat_name] = mat
        return self._apply_material_to_object(glass_object, mat)

    def apply_chrome_material(
        self,
        chrome_object: Any,
    ) -> bool:
        """Apply chrome material to trim/grille."""
        if not self._blender_available:
            return False

        mat_name = "car_chrome"

        if mat_name in self._material_cache:
            return self._apply_material_to_object(chrome_object, self._material_cache[mat_name])

        mat = self._bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.92, 1.0)
            bsdf.inputs["Metallic"].default_value = 1.0
            bsdf.inputs["Roughness"].default_value = 0.1

        self._material_cache[mat_name] = mat
        return self._apply_material_to_object(chrome_object, mat)

    def apply_rubber_material(
        self,
        tire_object: Any,
    ) -> bool:
        """Apply rubber material to tires."""
        if not self._blender_available:
            return False

        mat_name = "car_rubber"

        if mat_name in self._material_cache:
            return self._apply_material_to_object(tire_object, self._material_cache[mat_name])

        mat = self._bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.9

        self._material_cache[mat_name] = mat
        return self._apply_material_to_object(tire_object, mat)

    def create_material_set(
        self,
        car_object: Any,
        preset: str,
        include_parts: bool = False,
    ) -> Dict[str, bool]:
        """
        Apply complete material set to car.

        Includes body paint, glass, chrome, and rubber.

        Args:
            car_object: Main car object
            preset: Paint preset name
            include_parts: Apply to children (glass, chrome, etc.)

        Returns:
            Dictionary of material applications
        """
        results = {"body": self.apply_preset(car_object, preset)}

        if include_parts and self._blender_available:
            # Find child objects by naming convention
            for child in car_object.children_recursive:
                child_name = child.name.lower()

                if "glass" in child_name or "window" in child_name or "windshield" in child_name:
                    results[f"glass_{child.name}"] = self.apply_glass_material(child)
                elif "chrome" in child_name or "grille" in child_name or "trim" in child_name:
                    results[f"chrome_{child.name}"] = self.apply_chrome_material(child)
                elif "tire" in child_name or "wheel" in child_name:
                    results[f"rubber_{child.name}"] = self.apply_rubber_material(child)

        return results

    # === PRIVATE METHODS ===

    def _get_blend_file(self, paint_type: PaintType, color: str) -> Optional[Path]:
        """Get path to blend file for color."""
        type_folder = {
            PaintType.GLOSSY: "CarMaterials_Glossy",
            PaintType.MATT: "CarMaterials_Matt",
            PaintType.METALLIC: "CarMaterials_Metallic",
        }

        folder = type_folder.get(paint_type)
        if folder is None:
            return None

        blend_file = self.plugins_path / folder / f"{color}_assets.blend"
        if blend_file.exists():
            return blend_file

        return None

    def _load_material_from_blend(self, blend_file: Path, color: str) -> Optional[Any]:
        """Load material from blend file."""
        if not self._blender_available:
            return None

        cache_key = f"{blend_file.stem}_{color}"
        if cache_key in self._material_cache:
            return self._material_cache[cache_key]

        try:
            # Append material from blend
            with self._bpy.data.libraries.load(str(blend_file)) as (data_from, data_to):
                # Find material matching color name
                material_name = f"material_{color}"
                for mat_name in data_from.materials:
                    if color in mat_name.lower():
                        data_to.materials = [mat_name]
                        break

            if data_to.materials and data_to.materials[0]:
                self._material_cache[cache_key] = data_to.materials[0]
                return data_to.materials[0]

        except Exception:
            pass

        return None

    def _create_fallback_material(
        self,
        car_object: Any,
        paint_type: PaintType,
        color: str,
        slot: int,
    ) -> bool:
        """Create simple material when KitBash not available."""
        if not self._blender_available:
            return False

        mat_name = f"car_paint_{color}"

        if mat_name in self._material_cache:
            return self._apply_material_to_object(car_object, self._material_cache[mat_name], slot)

        # Get RGB for color
        rgb = self.get_color_rgb(color)

        mat = self._bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)

            if paint_type == PaintType.GLOSSY:
                bsdf.inputs["Roughness"].default_value = 0.2
                bsdf.inputs["Metallic"].default_value = 0.8
                bsdf.inputs["Clearcoat"].default_value = 1.0
            elif paint_type == PaintType.MATT:
                bsdf.inputs["Roughness"].default_value = 0.95
                bsdf.inputs["Metallic"].default_value = 0.0
            elif paint_type == PaintType.METALLIC:
                bsdf.inputs["Roughness"].default_value = 0.3
                bsdf.inputs["Metallic"].default_value = 1.0

        self._material_cache[mat_name] = mat
        return self._apply_material_to_object(car_object, mat, slot)

    def _apply_material_to_object(
        self,
        obj: Any,
        material: Any,
        slot: int = 0,
    ) -> bool:
        """Apply material to object slot."""
        if not self._blender_available or obj is None or material is None:
            return False

        # Ensure enough material slots
        while len(obj.data.materials) <= slot:
            obj.data.materials.append(None)

        obj.data.materials[slot] = material
        return True


# === CONVENIENCE FUNCTIONS ===

def apply_car_paint(
    car_object: Any,
    paint_preset: str = "racing_red",
) -> bool:
    """Quick function to apply paint preset to car."""
    system = CarMaterialSystem()
    return system.apply_preset(car_object, paint_preset)


def get_color_options() -> Dict[str, List[str]]:
    """Get all available color options organized by type."""
    return {
        "glossy": list(GLOSSY_COLORS.keys()),
        "matt": list(MATT_COLORS.keys()),
        "metallic": list(METALLIC_COLORS.keys()),
        "presets": list(PAINT_PRESETS.keys()),
    }


__all__ = [
    "CarMaterialSystem",
    "PaintType",
    "PaintColor",
    "GLOSSY_COLORS",
    "MATT_COLORS",
    "METALLIC_COLORS",
    "PAINT_PRESETS",
    "apply_car_paint",
    "get_color_options",
]
