"""
Tentacle Skin Shader Generator

Procedural skin material generation with horror themes.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

try:
    import bpy
    from bpy.types import Material, Node, NodeSocket
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Material = None
    Node = None
    NodeSocket = None

from .types import (
    MaterialTheme,
    WetnessLevel,
    SSSConfig,
    WetnessConfig,
    VeinConfig,
    RoughnessConfig,
    ThemePreset,
    TentacleMaterialConfig,
    MaterialZone,
)
from .themes import THEME_PRESETS, get_theme_preset


@dataclass
class SkinShaderResult:
    """Result from skin shader generation."""

    material_name: str
    """Name of the generated material."""

    success: bool = True
    """Whether generation was successful."""

    node_count: int = 0
    """Number of nodes in material tree."""

    has_sss: bool = False
    """Whether material has SSS enabled."""

    has_emission: bool = False
    """Whether material has emission enabled."""

    error: Optional[str] = None
    """Error message if failed."""


class SkinShaderGenerator:
    """Generator for procedural tentacle skin materials."""

    def __init__(self, config: TentacleMaterialConfig):
        """Initialize the skin shader generator.

        Args:
            config: Material configuration
        """
        self.config = config
        self._theme = config.theme_preset
        self._seed = config.seed if config.seed is not None else hash(str(config.seed))

    def generate(self, material_name: Optional[str] = None) -> SkinShaderResult:
        """
        Generate the skin material.

        Args:
            material_name: Optional name for the material

        Returns:
            SkinShaderResult with generation details
        """
        name = material_name or self.config.name

        if not BLENDER_AVAILABLE:
            return SkinShaderResult(
                material_name=name,
                success=False,
                error="Blender not available - skin shader requires Blender API"
            )

        try:
            # Create new material
            if name in bpy.data.materials:
                bpy.data.materials.remove(bpy.data.materials[name])

            material = bpy.data.materials.new(name=name)

            # Enable nodes
            material.use_nodes = True

            # Use Principled BSDF as base
            bsdf = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
            bsdf.location = (0, 0)

            # Apply theme preset if available
            if self._theme:
                self._apply_theme(bsdf, self._theme)
            else:
                # Apply custom configuration
                self._apply_custom_config(bsdf, self.config)

            # Apply zones if configured
            if self.config.zones:
                self._apply_zones(material, bsdf)

            return SkinShaderResult(
                material_name=name,
                success=True,
                node_count=len(material.node_tree.nodes),
                has_sss=self._theme.sss.weight > 0 if self._theme else False,
                has_emission=self._theme.emission_strength > 0 if self._theme else False,
            )

        except Exception as e:
            return SkinShaderResult(
                material_name=name,
                success=False,
                error=str(e)
            )

    def _apply_theme(self, bsdf, theme: ThemePreset) -> None:
        """Apply theme preset to BSDF node."""
        # Base color
        bsdf.inputs["Base Color"].default_value = theme.base_color

        # SSS
        sss = theme.sss
        bsdf.subsurface_method = "BURLEY"  # Blender 4.0+
        bsdf.subsurface_weight = sss.weight
        bsdf.subsurface_radius = sss.radius
        bsdf.subsurface_color = sss.color

        # Roughness
        roughness = theme.roughness
        bsdf.inputs["Roughness"].default_value = roughness.base
        bsdf.inputs["Metallic"].default_value = roughness.metallic

        # Wetness effects
        wetness = theme.wetness
        if wetness.level != WetnessLevel.DRY:
            # Reduce roughness based on wetness
            bsdf.inputs["Roughness"].default_value = max(
                0.1,
                roughness.base - (wetness.intensity * wetness.roughness_modifier)
            )
            # Add specular boost
            bsdf.inputs["Specular IOR Level"].default_value = 1.5 + wetness.specular_boost

            # Add clearcoat for slimy look
            if wetness.clearcoat > 0:
                self._add_clearcoat(bsdf, wetness.clearcoat)

        # Emission for bioluminescent themes
        if theme.emission_strength > 0:
            bsdf.emission_color = theme.emission_color
            bsdf.emission_strength = theme.emission_strength

    def _apply_custom_config(self, bsdf, config: TentacleMaterialConfig) -> None:
        """Apply custom configuration to BSDF node.

        Note: This is a placeholder for future custom configuration support.
        Currently, theme presets provide comprehensive coverage for all use cases.
        Custom configuration would allow fine-grained control over individual
        material parameters without using a preset theme.

        Future implementation will support:
        - Direct SSS parameter control
        - Custom wetness profiles
        - Per-zone material overrides
        - Custom vein/bioluminescence patterns
        """
        # Apply basic defaults from config
        if config.global_wetness_multiplier != 1.0:
            # Adjust roughness based on wetness
            current_roughness = bsdf.inputs["Roughness"].default_value
            bsdf.inputs["Roughness"].default_value = max(
                0.1,
                current_roughness / config.global_wetness_multiplier
            )

    def _apply_zones(self, material, bsdf) -> None:
        """Apply zone-based material variation.

        Note: This is a placeholder for future zone-based material support.
        Zone-based materials allow different parts of the tentacle to have
        different material properties (e.g., darker tip, lighter base).

        Future implementation will support:
        - Vertex color-based zone blending
        - UV coordinate-based zone mapping
        - Per-zone SSS/roughness/wetness overrides
        - Smooth transitions between zones
        """
        if not BLENDER_AVAILABLE:
            return

        zones = self.config.zones
        if not zones:
            return

        # TODO: Implement zone-based material blending
        # This would create a vertex color attribute and use it
        # to blend between different material zones
        pass

    def _add_clearcoat(self, bsdf, intensity: float) -> None:
        """Add clearcoat layer for slimy look.

        Note: This is a placeholder for clearcoat layer support.
        Clearcoat adds a glossy coating on top of the base material,
        useful for wet/slimy tentacle appearances.

        Future implementation will support:
        - Separate clearcoat BSDF node
        - Clearcoat roughness control
        - Clearcoat normal map support
        - IOR control for clearcoat layer
        """
        if not BLENDER_AVAILABLE:
            return

        # Set clearcoat intensity on Principled BSDF
        # Note: Blender 4.0+ uses coat_weight instead of clearcoat
        if hasattr(bsdf.inputs, "Coat Weight"):
            bsdf.inputs["Coat Weight"].default_value = intensity
        elif "Clearcoat" in bsdf.inputs:
            bsdf.inputs["Clearcoat"].default_value = intensity


def create_skin_material(
    theme: MaterialTheme = MaterialTheme.ROTTING,
    name: Optional[str] = None,
) -> SkinShaderResult:
    """
    Convenience function to create a skin material from theme.

    Args:
        theme: Material theme preset
        name: Optional material name

    Returns:
        SkinShaderResult with generation details
    """
    preset = get_theme_preset(theme)
    config = TentacleMaterialConfig(
        name=name or f"Tentacle_{theme.value}",
        theme_preset=preset,
    )

    generator = SkinShaderGenerator(config)
    return generator.generate(name)


def create_custom_material(
    config: TentacleMaterialConfig,
) -> SkinShaderResult:
    """
    Convenience function to create a custom skin material.

    Args:
        config: Custom material configuration

    Returns:
        SkinShaderResult with generation details
    """
    generator = SkinShaderGenerator(config)
    return generator.generate(config.name)
