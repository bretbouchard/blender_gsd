"""
Improved Subsurface Scattering for Blender 5.0+.

Blender 5.0 introduced improved subsurface scattering with better
energy conservation, new scattering profiles, and enhanced control
over SSS quality and performance.

Example:
    >>> from lib.blender5x.rendering import SubsurfaceScattering
    >>> SubsurfaceScattering.configure_skin(material)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Material


class SSSProfile(Enum):
    """Subsurface scattering profiles."""

    BURLEY = "burley"
    """Disney Burley normalized diffusion."""

    RANDOM_WALK = "random_walk"
    """Random walk (volume) method."""

    RANDOM_WALK_SKIN = "random_walk_skin"
    """Random walk optimized for skin."""

    CHRISTENSEN_BURLEY = "christensen_burley"
    """Christensen-Burley approximation."""


class SSSPreset(Enum):
    """Presets for common SSS materials."""

    SKIN_CAUCASIAN = "skin_caucasian"
    """Caucasian skin tones."""

    SKIN_ASIAN = "skin_asian"
    """Asian skin tones."""

    SKIN_AFRICAN = "skin_african"
    """African skin tones."""

    MARBLE = "marble"
    """White marble stone."""

    JADE = "jade"
    """Jade green stone."""

    WAX = "wax"
    """Translucent wax."""

    MILK = "milk"
    """White milk."""

    POTATO = "potato"
    """Raw potato flesh."""

    CHICKEN_MEAT = "chicken_meat"
    """Raw chicken meat."""

    BREAD = "bread"
    """White bread."""

    KETCHUP = "ketchup"
    """Tomato ketchup."""

    CREAM = "cream"
    """Whipped cream."""


@dataclass
class SSSSettings:
    """Settings for subsurface scattering."""

    weight: float = 1.0
    """SSS weight (0-1)."""

    radius: tuple[float, float, float] = (1.0, 0.2, 0.1)
    """RGB scattering radius (in mm)."""

    anisotropy: float = 0.0
    """Scattering anisotropy (-1 to 1)."""

    scale: float = 1.0
    """Global scale factor."""

    profile: SSSProfile = SSSProfile.BURLEY
    """Scattering profile/method."""

    subsurface_color: tuple[float, float, float] | None = None
    """Subsurface color override."""

    comment: str = ""
    """Description."""


# SSS preset configurations
SSS_PRESETS: dict[SSSPreset, SSSSettings] = {
    SSSPreset.SKIN_CAUCASIAN: SSSSettings(
        weight=1.0,
        radius=(1.0, 0.5, 0.25),
        anisotropy=0.0,
        scale=1.0,
        profile=SSSProfile.RANDOM_WALK_SKIN,
        subsurface_color=(0.9, 0.7, 0.5),
        comment="Caucasian skin with warm undertones",
    ),
    SSSPreset.SKIN_ASIAN: SSSSettings(
        weight=1.0,
        radius=(0.8, 0.4, 0.2),
        anisotropy=0.0,
        scale=1.0,
        profile=SSSProfile.RANDOM_WALK_SKIN,
        subsurface_color=(0.95, 0.8, 0.65),
        comment="Asian skin with yellow undertones",
    ),
    SSSPreset.SKIN_AFRICAN: SSSSettings(
        weight=0.8,
        radius=(0.6, 0.3, 0.15),
        anisotropy=0.0,
        scale=1.0,
        profile=SSSProfile.RANDOM_WALK_SKIN,
        subsurface_color=(0.6, 0.4, 0.3),
        comment="African skin with deep tones",
    ),
    SSSPreset.MARBLE: SSSSettings(
        weight=0.5,
        radius=(1.5, 1.0, 0.5),
        anisotropy=0.2,
        scale=0.5,
        profile=SSSProfile.RANDOM_WALK,
        subsurface_color=(0.95, 0.95, 0.98),
        comment="White marble with subtle translucency",
    ),
    SSSPreset.JADE: SSSSettings(
        weight=0.7,
        radius=(1.0, 0.8, 0.5),
        anisotropy=0.1,
        scale=0.5,
        profile=SSSProfile.RANDOM_WALK,
        subsurface_color=(0.2, 0.6, 0.3),
        comment="Jade green stone",
    ),
    SSSPreset.WAX: SSSSettings(
        weight=0.8,
        radius=(1.0, 0.5, 0.3),
        anisotropy=0.0,
        scale=0.3,
        profile=SSSProfile.RANDOM_WALK,
        subsurface_color=(0.9, 0.85, 0.8),
        comment="Translucent candle wax",
    ),
    SSSPreset.MILK: SSSSettings(
        weight=1.0,
        radius=(0.5, 0.8, 1.0),
        anisotropy=0.7,
        scale=0.5,
        profile=SSSProfile.RANDOM_WALK,
        subsurface_color=(0.98, 0.98, 0.98),
        comment="White milk with forward scattering",
    ),
    SSSPreset.POTATO: SSSSettings(
        weight=0.6,
        radius=(0.4, 0.3, 0.2),
        anisotropy=0.0,
        scale=0.5,
        profile=SSSProfile.BURLEY,
        subsurface_color=(0.9, 0.85, 0.5),
        comment="Raw potato flesh",
    ),
    SSSPreset.CHICKEN_MEAT: SSSSettings(
        weight=0.7,
        radius=(0.3, 0.2, 0.15),
        anisotropy=0.0,
        scale=0.3,
        profile=SSSProfile.BURLEY,
        subsurface_color=(0.95, 0.75, 0.7),
        comment="Raw chicken meat",
    ),
    SSSPreset.BREAD: SSSSettings(
        weight=0.4,
        radius=(1.5, 1.2, 0.8),
        anisotropy=0.1,
        scale=0.2,
        profile=SSSProfile.BURLEY,
        subsurface_color=(0.9, 0.85, 0.7),
        comment="White bread crumb",
    ),
    SSSPreset.KETCHUP: SSSSettings(
        weight=0.9,
        radius=(0.1, 0.3, 0.4),
        anisotropy=0.0,
        scale=0.3,
        profile=SSSProfile.RANDOM_WALK,
        subsurface_color=(0.8, 0.1, 0.05),
        comment="Tomato ketchup",
    ),
    SSSPreset.CREAM: SSSSettings(
        weight=0.6,
        radius=(0.8, 0.9, 1.0),
        anisotropy=0.3,
        scale=0.4,
        profile=SSSProfile.RANDOM_WALK,
        subsurface_color=(0.98, 0.96, 0.92),
        comment="Whipped cream",
    ),
}


class SubsurfaceScattering:
    """
    Improved subsurface scattering utilities for Blender 5.0+.

    Provides tools for configuring and optimizing SSS materials
    with the improved algorithms introduced in Blender 5.0.

    Example:
        >>> SubsurfaceScattering.configure_skin(material, "caucasian")
        >>> SubsurfaceScattering.configure_marble(material)
    """

    @staticmethod
    def configure(
        material: Material | str,
        settings: SSSSettings,
    ) -> None:
        """
        Configure SSS on a material with specified settings.

        Args:
            material: Material to configure.
            settings: SSSSettings configuration.

        Example:
            >>> settings = SSSSettings(
            ...     weight=0.8,
            ...     radius=(1.0, 0.5, 0.25),
            ...     profile=SSSProfile.RANDOM_WALK,
            ... )
            >>> SubsurfaceScattering.configure(mat, settings)
        """
        import bpy

        # Get material
        if isinstance(material, str):
            mat = bpy.data.materials.get(material)
            if mat is None:
                raise ValueError(f"Material not found: {material}")
        else:
            mat = material

        if not mat.use_nodes:
            mat.use_nodes = True

        # Find Principled BSDF
        tree = mat.node_tree
        principled = None

        for node in tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                principled = node
                break

        if principled is None:
            principled = tree.nodes.new("ShaderNodeBsdfPrincipled")

        # Configure SSS weight
        if "Subsurface Weight" in principled.inputs:
            principled.inputs["Subsurface Weight"].default_value = settings.weight
        elif "Subsurface" in principled.inputs:
            principled.inputs["Subsurface"].default_value = settings.weight

        # Configure SSS radius
        if "Subsurface Radius" in principled.inputs:
            principled.inputs["Subsurface Radius"].default_value = settings.radius

        # Configure SSS scale
        if "Subsurface Scale" in principled.inputs:
            principled.inputs["Subsurface Scale"].default_value = settings.scale

        # Configure anisotropy (Blender 5.0+)
        if hasattr(principled, "subsurface_anisotropy"):
            principled.subsurface_anisotropy = settings.anisotropy
        elif "Subsurface Anisotropy" in principled.inputs:
            principled.inputs["Subsurface Anisotropy"].default_value = (
                settings.anisotropy
            )

        # Configure subsurface color if provided
        if settings.subsurface_color and "Subsurface Color" in principled.inputs:
            principled.inputs["Subsurface Color"].default_value = (
                settings.subsurface_color[0],
                settings.subsurface_color[1],
                settings.subsurface_color[2],
                1.0,
            )

        # Set profile (Blender 5.0+)
        if hasattr(principled, "subsurface_method"):
            principled.subsurface_method = settings.profile.value.upper()

    @staticmethod
    def configure_skin(
        material: Material | str,
        skin_type: str = "caucasian",
    ) -> None:
        """
        Configure material for realistic skin rendering.

        Args:
            material: Material to configure.
            skin_type: Skin type preset. Options: 'caucasian', 'asian', 'african'.

        Example:
            >>> SubsurfaceScattering.configure_skin("SkinMat", "asian")
        """
        preset_map = {
            "caucasian": SSSPreset.SKIN_CAUCASIAN,
            "asian": SSSPreset.SKIN_ASIAN,
            "african": SSSPreset.SKIN_AFRICAN,
        }

        if skin_type not in preset_map:
            raise ValueError(
                f"Unknown skin type: {skin_type}. "
                f"Options: {list(preset_map.keys())}"
            )

        preset = preset_map[skin_type]
        settings = SSS_PRESETS[preset]

        SubsurfaceScattering.configure(material, settings)

    @staticmethod
    def configure_marble(material: Material | str) -> None:
        """
        Configure material for realistic marble rendering.

        Args:
            material: Material to configure.

        Example:
            >>> SubsurfaceScattering.configure_marble("MarbleMat")
        """
        settings = SSS_PRESETS[SSSPreset.MARBLE]
        SubsurfaceScattering.configure(material, settings)

    @staticmethod
    def configure_wax(material: Material | str) -> None:
        """
        Configure material for realistic wax rendering.

        Args:
            material: Material to configure.

        Example:
            >>> SubsurfaceScattering.configure_wax("WaxMat")
        """
        settings = SSS_PRESETS[SSSPreset.WAX]
        SubsurfaceScattering.configure(material, settings)

    @staticmethod
    def apply_preset(
        material: Material | str,
        preset: SSSPreset,
    ) -> None:
        """
        Apply an SSS preset to a material.

        Args:
            material: Material to configure.
            preset: SSS preset to apply.

        Example:
            >>> SubsurfaceScattering.apply_preset(mat, SSSPreset.MILK)
        """
        if preset not in SSS_PRESETS:
            raise ValueError(f"Unknown preset: {preset}")

        settings = SSS_PRESETS[preset]
        SubsurfaceScattering.configure(material, settings)

    @staticmethod
    def get_presets() -> list[SSSPreset]:
        """
        Get list of available SSS presets.

        Returns:
            List of available presets.
        """
        return list(SSSPreset)

    @staticmethod
    def set_profile(
        material: Material | str,
        profile: SSSProfile,
    ) -> None:
        """
        Set the SSS profile/method for a material.

        Args:
            material: Material to configure.
            profile: SSS profile to use.

        Example:
            >>> SubsurfaceScattering.set_profile(mat, SSSProfile.RANDOM_WALK_SKIN)
        """
        import bpy

        # Get material
        if isinstance(material, str):
            mat = bpy.data.materials.get(material)
            if mat is None:
                raise ValueError(f"Material not found: {material}")
        else:
            mat = material

        if not mat.use_nodes:
            mat.use_nodes = True

        # Find Principled BSDF
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if hasattr(node, "subsurface_method"):
                    node.subsurface_method = profile.value.upper()
                break

    @staticmethod
    def optimize_for_performance(material: Material | str) -> None:
        """
        Optimize SSS settings for faster rendering.

        Args:
            material: Material to optimize.

        Note:
            Uses faster Burley profile instead of Random Walk.
        """
        import bpy

        # Get material
        if isinstance(material, str):
            mat = bpy.data.materials.get(material)
            if mat is None:
                raise ValueError(f"Material not found: {material}")
        else:
            mat = material

        if not mat.use_nodes:
            mat.use_nodes = True

        # Find Principled BSDF
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                # Use faster Burley profile
                if hasattr(node, "subsurface_method"):
                    node.subsurface_method = "BURLEY"

                # Reduce samples for faster preview
                # Note: Sample count is a render setting, not material
                break


# Convenience exports
__all__ = [
    "SubsurfaceScattering",
    "SSSProfile",
    "SSSPreset",
    "SSSSettings",
    "SSS_PRESETS",
]
