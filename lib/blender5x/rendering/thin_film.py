"""
Thin Film Iridescence for Blender 5.0+.

Blender 5.0 introduced thin film iridescence in the Principled BSDF shader,
enabling realistic soap bubbles, oil slicks, oxidized metals, and other
interference-based optical effects.

Example:
    >>> from lib.blender5x.rendering import ThinFilmIridescence
    >>> ThinFilmIridescence.create_soap_bubble()
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Material, Node


class ThinFilmPreset(Enum):
    """Presets for common thin film effects."""

    SOAP_BUBBLE = "soap_bubble"
    """Soap bubble with rainbow colors."""

    OIL_SLICK = "oil_slick"
    """Oil on water effect."""

    OXIDIZED_COPPER = "oxidized_copper"
    """Oxidized/tarnished copper."""

    OXIDIZED_BRONZE = "oxidized_bronze"
    """Oxidized/tarnished bronze."""

    PEARL = "pearl"
    """Pearlescent effect."""

    BEETLE_SHELL = "beetle_shell"
    """Beetle wing iridescence."""

    CD_RAINBOW = "cd_rainbow"
    """CD/DVD rainbow reflection."""

    TISSUE_FOIL = "tissue_foil"
    """Tissue foil / gift wrap."""

    ANODIZED_TITANIUM = "anodized_titanium"
    """Anodized titanium colors."""


@dataclass
class ThinFilmSettings:
    """Settings for thin film iridescence."""

    thickness: float = 300.0
    """Film thickness in nanometers."""

    ior: float = 1.5
    """Index of refraction of the film."""

    roughness: float = 0.0
    """Surface roughness."""

    base_color: tuple[float, float, float] = (1.0, 1.0, 1.0)
    """Base color of the material."""

    metallic: float = 0.0
    """Metallic value of the base material."""

    thickness_variation: float = 0.0
    """Random variation in thickness."""

    comment: str = ""
    """Description of the effect."""


# Preset configurations for thin film effects
THIN_FILM_PRESETS: dict[ThinFilmPreset, ThinFilmSettings] = {
    ThinFilmPreset.SOAP_BUBBLE: ThinFilmSettings(
        thickness=400.0,
        ior=1.33,
        roughness=0.0,
        base_color=(1.0, 1.0, 1.0),
        metallic=0.0,
        thickness_variation=200.0,
        comment="Soap bubble with rainbow interference colors",
    ),
    ThinFilmPreset.OIL_SLICK: ThinFilmSettings(
        thickness=600.0,
        ior=1.44,
        roughness=0.05,
        base_color=(0.1, 0.1, 0.1),
        metallic=0.0,
        thickness_variation=300.0,
        comment="Oil on water with colorful interference",
    ),
    ThinFilmPreset.OXIDIZED_COPPER: ThinFilmSettings(
        thickness=350.0,
        ior=2.5,
        roughness=0.2,
        base_color=(0.8, 0.5, 0.2),
        metallic=0.9,
        thickness_variation=50.0,
        comment="Oxidized copper with tarnish colors",
    ),
    ThinFilmPreset.OXIDIZED_BRONZE: ThinFilmSettings(
        thickness=400.0,
        ior=2.3,
        roughness=0.25,
        base_color=(0.7, 0.5, 0.2),
        metallic=0.85,
        thickness_variation=100.0,
        comment="Oxidized bronze patina",
    ),
    ThinFilmPreset.PEARL: ThinFilmSettings(
        thickness=500.0,
        ior=1.53,
        roughness=0.1,
        base_color=(0.95, 0.93, 0.9),
        metallic=0.0,
        thickness_variation=150.0,
        comment="Pearlescent shimmer",
    ),
    ThinFilmPreset.BEETLE_SHELL: ThinFilmSettings(
        thickness=300.0,
        ior=1.56,
        roughness=0.1,
        base_color=(0.1, 0.2, 0.1),
        metallic=0.5,
        thickness_variation=50.0,
        comment="Beetle wing iridescence",
    ),
    ThinFilmPreset.CD_RAINBOW: ThinFilmSettings(
        thickness=1200.0,
        ior=1.5,
        roughness=0.1,
        base_color=(0.9, 0.9, 0.9),
        metallic=0.95,
        thickness_variation=200.0,
        comment="CD/DVD rainbow reflection",
    ),
    ThinFilmPreset.TISSUE_FOIL: ThinFilmSettings(
        thickness=200.0,
        ior=1.4,
        roughness=0.3,
        base_color=(0.95, 0.95, 0.95),
        metallic=0.8,
        thickness_variation=100.0,
        comment="Tissue foil / gift wrap iridescence",
    ),
    ThinFilmPreset.ANODIZED_TITANIUM: ThinFilmSettings(
        thickness=250.0,
        ior=2.2,
        roughness=0.15,
        base_color=(0.7, 0.7, 0.7),
        metallic=0.95,
        thickness_variation=25.0,
        comment="Anodized titanium colors",
    ),
}


class ThinFilmIridescence:
    """
    Thin film iridescence utilities for Blender 5.0+.

    Provides tools for creating and configuring iridescent materials
    using the thin film feature in the Principled BSDF shader.

    Example:
        >>> mat = ThinFilmIridescence.create_soap_bubble()
        >>> ThinFilmIridescence.create_oil_slick()
    """

    @staticmethod
    def create_soap_bubble(name: str = "SoapBubble") -> str:
        """
        Create a soap bubble material with rainbow iridescence.

        Args:
            name: Material name.

        Returns:
            Name of the created material.

        Example:
            >>> mat = ThinFilmIridescence.create_soap_bubble()
        """
        import bpy

        settings = THIN_FILM_PRESETS[ThinFilmPreset.SOAP_BUBBLE]
        return ThinFilmIridescence.create_material(name, settings)

    @staticmethod
    def create_oil_slick(name: str = "OilSlick") -> str:
        """
        Create an oil slick material for oil-on-water effects.

        Args:
            name: Material name.

        Returns:
            Name of the created material.

        Example:
            >>> mat = ThinFilmIridescence.create_oil_slick()
        """
        import bpy

        settings = THIN_FILM_PRESETS[ThinFilmPreset.OIL_SLICK]
        return ThinFilmIridescence.create_material(name, settings)

    @staticmethod
    def create_oxidized_metal(
        base_color: tuple[float, float, float] = (0.8, 0.5, 0.2),
        name: str = "OxidizedMetal",
    ) -> str:
        """
        Create an oxidized/tarnished metal material.

        Args:
            base_color: RGB base color for the metal.
            name: Material name.

        Returns:
            Name of the created material.

        Example:
            >>> mat = ThinFilmIridescence.create_oxidized_metal(
            ...     base_color=(0.72, 0.45, 0.2)  # Copper
            ... )
        """
        import bpy

        settings = ThinFilmSettings(
            thickness=380.0,
            ior=2.4,
            roughness=0.2,
            base_color=base_color,
            metallic=0.9,
            thickness_variation=80.0,
        )
        return ThinFilmIridescence.create_material(name, settings)

    @staticmethod
    def configure_principled(
        material: Material | str,
        thickness: float = 300.0,
        ior: float = 1.5,
        roughness: float = 0.0,
        thickness_variation: float = 0.0,
    ) -> None:
        """
        Configure thin film on an existing Principled BSDF material.

        Args:
            material: Material to configure.
            thickness: Film thickness in nanometers.
            ior: Index of refraction of the film.
            roughness: Surface roughness.
            thickness_variation: Random variation in thickness.

        Example:
            >>> ThinFilmIridescence.configure_principled(
            ...     "MyMaterial",
            ...     thickness=500.0,
            ...     ior=1.44,
            ... )
        """
        import bpy

        # Get material
        if isinstance(material, str):
            mat = bpy.data.materials.get(material)
            if mat is None:
                raise ValueError(f"Material not found: {material}")
        else:
            mat = material

        # Find or create Principled BSDF
        if mat.use_nodes:
            principled = None
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    principled = node
                    break

            if principled is None:
                principled = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")

            # Configure thin film (Blender 5.0+)
            if hasattr(principled, "thin_film_thickness"):
                principled.thin_film_thickness = thickness
                principled.thin_film_ior = ior
                principled.roughness = roughness

                if hasattr(principled, "thin_film_thickness_variation"):
                    principled.thin_film_thickness_variation = thickness_variation

    @staticmethod
    def configure_metallic(
        material: Material | str,
        thickness: float = 400.0,
    ) -> None:
        """
        Configure thin film on a metallic material for oxidized look.

        Args:
            material: Material to configure.
            thickness: Film thickness in nanometers.

        Example:
            >>> ThinFilmIridescence.configure_metallic("Copper", thickness=350)
        """
        import bpy

        # Get material
        if isinstance(material, str):
            mat = bpy.data.materials.get(material)
            if mat is None:
                raise ValueError(f"Material not found: {material}")
        else:
            mat = material

        # Configure with metallic defaults
        ThinFilmIridescence.configure_principled(
            mat,
            thickness=thickness,
            ior=2.5,  # Higher IOR for metal oxide
            roughness=0.2,
            thickness_variation=50.0,
        )

    @staticmethod
    def rainbow_coating(
        base_material: Material | str,
        thickness_range: tuple[float, float] = (200.0, 600.0),
        name: str = "RainbowCoating",
    ) -> str:
        """
        Create a rainbow coating overlay material.

        Args:
            base_material: Base material to coat.
            thickness_range: Min and max thickness for rainbow effect.
            name: Material name.

        Returns:
            Name of the created material.

        Example:
            >>> mat = ThinFilmIridescence.rainbow_coating(
            ...     base_material="BaseMetal",
            ...     thickness_range=(200, 800),
            ... )
        """
        import bpy
        import math

        # Get base material
        if isinstance(base_material, str):
            base_mat = bpy.data.materials.get(base_material)
        else:
            base_mat = base_material

        # Create new material
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        # Clear default nodes
        tree = mat.node_tree
        for node in tree.nodes:
            tree.nodes.remove(node)

        # Create nodes
        output = tree.nodes.new("ShaderNodeOutputMaterial")
        mix_shader = tree.nodes.new("ShaderNodeMixShader")

        # Base material shader
        if base_mat and base_mat.use_nodes:
            # Copy base shader output
            base_output = base_mat.node_tree.nodes.get("Material Output")
            if base_output:
                base_surface = base_output.inputs["Surface"].links[0].from_socket
                # We'll just create a new principled for simplicity
                base_principled = tree.nodes.new("ShaderNodeBsdfPrincipled")
                base_principled.distribution = "MULTI_GGX"
        else:
            base_principled = tree.nodes.new("ShaderNodeBsdfPrincipled")

        # Coating shader with thin film
        coating = tree.nodes.new("ShaderNodeBsdfPrincipled")
        coating.distribution = "MULTI_GGX"

        # Configure thin film with varying thickness
        if hasattr(coating, "thin_film_thickness"):
            # Use average thickness
            avg_thickness = (thickness_range[0] + thickness_range[1]) / 2
            coating.thin_film_thickness = avg_thickness
            coating.thin_film_ior = 1.5
            coating.roughness = 0.0

            # Add variation via node
            if hasattr(coating, "thin_film_thickness_variation"):
                variation = (thickness_range[1] - thickness_range[0]) / 2
                coating.thin_film_thickness_variation = variation

        # Position nodes
        base_principled.location = (-400, 100)
        coating.location = (-400, -100)
        mix_shader.location = (0, 0)
        output.location = (300, 0)

        # Link nodes
        tree.links.new(base_principled.outputs["BSDF"], mix_shader.inputs[1])
        tree.links.new(coating.outputs["BSDF"], mix_shader.inputs[2])
        tree.links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])

        # Set mix factor (50% coating)
        mix_shader.inputs["Fac"].default_value = 0.3

        return mat.name

    @staticmethod
    def create_material(
        name: str,
        settings: ThinFilmSettings,
    ) -> str:
        """
        Create a thin film material with specified settings.

        Args:
            name: Material name.
            settings: ThinFilmSettings configuration.

        Returns:
            Name of the created material.

        Example:
            >>> settings = ThinFilmSettings(
            ...     thickness=400.0,
            ...     ior=1.33,
            ...     base_color=(1.0, 1.0, 1.0),
            ... )
            >>> mat = ThinFilmIridescence.create_material("Bubble", settings)
        """
        import bpy

        # Create material
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        # Get Principled BSDF
        tree = mat.node_tree
        principled = None

        for node in tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                principled = node
                break

        if principled is None:
            principled = tree.nodes.new("ShaderNodeBsdfPrincipled")

        # Configure base properties
        principled.inputs["Base Color"].default_value = (
            settings.base_color[0],
            settings.base_color[1],
            settings.base_color[2],
            1.0,
        )
        principled.inputs["Metallic"].default_value = settings.metallic
        principled.inputs["Roughness"].default_value = settings.roughness

        # Configure thin film (Blender 5.0+)
        if hasattr(principled, "thin_film_thickness"):
            principled.thin_film_thickness = settings.thickness
            principled.thin_film_ior = settings.ior

            if hasattr(principled, "thin_film_thickness_variation"):
                principled.thin_film_thickness_variation = settings.thickness_variation

        # Link to output
        output = tree.nodes.get("Material Output")
        if output is None:
            output = tree.nodes.new("ShaderNodeOutputMaterial")

        # Ensure connection
        if not output.inputs["Surface"].links:
            tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        return mat.name

    @staticmethod
    def apply_preset(
        material: Material | str,
        preset: ThinFilmPreset,
    ) -> None:
        """
        Apply a preset to an existing material.

        Args:
            material: Material to modify.
            preset: Preset to apply.

        Example:
            >>> ThinFilmIridescence.apply_preset(
            ...     "MyMaterial",
            ...     ThinFilmPreset.PEARL,
            ... )
        """
        import bpy

        settings = THIN_FILM_PRESETS.get(preset)
        if settings is None:
            raise ValueError(f"Unknown preset: {preset}")

        # Get material
        if isinstance(material, str):
            mat = bpy.data.materials.get(material)
            if mat is None:
                raise ValueError(f"Material not found: {material}")
        else:
            mat = material

        # Apply settings
        ThinFilmIridescence.configure_principled(
            mat,
            thickness=settings.thickness,
            ior=settings.ior,
            roughness=settings.roughness,
            thickness_variation=settings.thickness_variation,
        )

    @staticmethod
    def get_presets() -> list[ThinFilmPreset]:
        """
        Get list of available thin film presets.

        Returns:
            List of available presets.
        """
        return list(ThinFilmPreset)


# Convenience exports
__all__ = [
    "ThinFilmIridescence",
    "ThinFilmPreset",
    "ThinFilmSettings",
    "THIN_FILM_PRESETS",
]
