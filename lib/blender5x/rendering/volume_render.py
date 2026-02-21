"""
Volume Rendering Algorithm for Blender 5.0+.

Blender 5.0 introduced a new volume rendering algorithm with improved
quality and performance, including better multi-scattering, absorption,
and emission handling.

Example:
    >>> from lib.blender5x.rendering import VolumeRendering
    >>> VolumeRendering.configure_high_quality(domain)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Material, Object


class VolumeSamplingMethod(Enum):
    """Volume sampling methods."""

    DISTANCE = "distance"
    """Distance-based sampling (equidistant)."""

    EQUIANGULAR = "equiangular"
    """Equiangular sampling (better for lights in volume)."""

    MULTIPLE_IMPORTANCE = "multiple_importance"
    """Multiple importance sampling (combines methods)."""

    RESERVOIR = "reservoir"
    """Reservoir-based resampling (new in Blender 5.0)."""


class VolumeInterpolation(Enum):
    """Volume interpolation methods."""

    LINEAR = "linear"
    """Linear interpolation."""

    CUBIC = "cubic"
    """Cubic (smooth) interpolation."""

    CLOSEST = "closest"
    """Nearest neighbor (blocky)."""


@dataclass
class VolumeRenderSettings:
    """Volume rendering quality settings."""

    step_size: float = 0.0
    """Step size for ray marching (0 = auto)."""

    max_steps: int = 1024
    """Maximum number of steps per ray."""

    sampling_method: VolumeSamplingMethod = VolumeSamplingMethod.MULTIPLE_IMPORTANCE
    """Sampling method to use."""

    interpolation: VolumeInterpolation = VolumeInterpolation.LINEAR
    """Volume grid interpolation."""

    use_clipping: bool = True
    """Clip volume at object bounds."""

    clipping_margin: float = 0.001
    """Extra margin for clipping."""

    homogeneous: bool = False
    """Assume homogeneous volume for optimization."""

    comment: str = ""
    """Description."""


# Quality presets
VOLUME_QUALITY_PRESETS = {
    "preview": VolumeRenderSettings(
        step_size=0.1,
        max_steps=256,
        sampling_method=VolumeSamplingMethod.DISTANCE,
        interpolation=VolumeInterpolation.LINEAR,
        use_clipping=True,
        comment="Fast preview quality",
    ),
    "standard": VolumeRenderSettings(
        step_size=0.0,  # Auto
        max_steps=1024,
        sampling_method=VolumeSamplingMethod.MULTIPLE_IMPORTANCE,
        interpolation=VolumeInterpolation.LINEAR,
        use_clipping=True,
        comment="Standard quality for most cases",
    ),
    "high": VolumeRenderSettings(
        step_size=0.0,
        max_steps=2048,
        sampling_method=VolumeSamplingMethod.MULTIPLE_IMPORTANCE,
        interpolation=VolumeInterpolation.CUBIC,
        use_clipping=True,
        comment="High quality for final renders",
    ),
    "ultra": VolumeRenderSettings(
        step_size=0.0,
        max_steps=4096,
        sampling_method=VolumeSamplingMethod.RESERVOIR,
        interpolation=VolumeInterpolation.CUBIC,
        use_clipping=True,
        comment="Ultra quality for hero shots",
    ),
}


class VolumeRendering:
    """
    Volume rendering configuration utilities for Blender 5.0+.

    Provides tools for configuring volume rendering quality,
    sampling methods, and performance optimization.

    Example:
        >>> VolumeRendering.configure_high_quality(domain)
        >>> VolumeRendering.optimize_for_gpu(domain)
    """

    @staticmethod
    def configure(
        volume: Object | str,
        settings: VolumeRenderSettings,
    ) -> None:
        """
        Configure volume rendering settings.

        Args:
            volume: Volume object or name.
            settings: VolumeRenderSettings configuration.

        Example:
            >>> settings = VolumeRenderSettings(
            ...     step_size=0.05,
            ...     max_steps=2048,
            ...     sampling_method=VolumeSamplingMethod.EQUIANGULAR,
            ... )
            >>> VolumeRendering.configure("SmokeVolume", settings)
        """
        import bpy

        # Get volume object
        if isinstance(volume, str):
            volume_obj = bpy.data.objects.get(volume)
            if volume_obj is None:
                raise ValueError(f"Volume object not found: {volume}")
        else:
            volume_obj = volume

        # Configure volume render settings
        # These are material-level settings in Cycles
        # Get or create volume material
        mat = volume_obj.data.materials[0] if volume_obj.data.materials else None

        if mat is None:
            mat = bpy.data.materials.new(f"{volume_obj.name}_VolMat")
            volume_obj.data.materials.append(mat)

        if not mat.use_nodes:
            mat.use_nodes = True

        # Find volume shader
        tree = mat.node_tree
        volume_shader = None

        for node in tree.nodes:
            if node.type in ("SHADER_VOLUME_ABSORPTION", "SHADER_VOLUME_SCATTER", "SHADER_VOLUME_PRINCIPLED"):
                volume_shader = node
                break

        if volume_shader is None:
            volume_shader = tree.nodes.new("ShaderNodeVolumePrincipled")

        # Configure step size
        if "Step Size" in volume_shader.inputs:
            volume_shader.inputs["Step Size"].default_value = settings.step_size

        # Configure max steps (Blender 5.0+)
        if hasattr(volume_shader, "max_steps"):
            volume_shader.max_steps = settings.max_steps

        # Configure sampling method (Blender 5.0+)
        if hasattr(volume_shader, "sampling_method"):
            volume_shader.sampling_method = settings.sampling_method.value.upper()

        # Configure interpolation (Blender 5.0+)
        if hasattr(volume_shader, "interpolation"):
            volume_shader.interpolation = settings.interpolation.value.upper()

        # Link to output if needed
        output = tree.nodes.get("Material Output")
        if output is None:
            output = tree.nodes.new("ShaderNodeOutputMaterial")

        if not output.inputs["Volume"].links:
            tree.links.new(volume_shader.outputs["Volume"], output.inputs["Volume"])

    @staticmethod
    def configure_preview(volume: Object | str) -> None:
        """
        Configure for fast preview rendering.

        Args:
            volume: Volume object or name.

        Example:
            >>> VolumeRendering.configure_preview("SmokeVolume")
        """
        settings = VOLUME_QUALITY_PRESETS["preview"]
        VolumeRendering.configure(volume, settings)

    @staticmethod
    def configure_high_quality(volume: Object | str) -> None:
        """
        Configure for high quality rendering.

        Args:
            volume: Volume object or name.

        Example:
            >>> VolumeRendering.configure_high_quality("SmokeVolume")
        """
        settings = VOLUME_QUALITY_PRESETS["high"]
        VolumeRendering.configure(volume, settings)

    @staticmethod
    def configure_ultra_quality(volume: Object | str) -> None:
        """
        Configure for maximum quality rendering.

        Args:
            volume: Volume object or name.

        Example:
            >>> VolumeRendering.configure_ultra_quality("SmokeVolume")
        """
        settings = VOLUME_QUALITY_PRESETS["ultra"]
        VolumeRendering.configure(volume, settings)

    @staticmethod
    def set_sampling_method(
        volume: Object | str,
        method: VolumeSamplingMethod,
    ) -> None:
        """
        Set the volume sampling method.

        Args:
            volume: Volume object or name.
            method: Sampling method to use.

        Example:
            >>> VolumeRendering.set_sampling_method(
            ...     "SmokeVolume",
            ...     VolumeSamplingMethod.EQUIANGULAR,
            ... )
        """
        import bpy

        # Get volume object
        if isinstance(volume, str):
            volume_obj = bpy.data.objects.get(volume)
        else:
            volume_obj = volume

        if volume_obj is None:
            return

        mat = volume_obj.data.materials[0] if volume_obj.data.materials else None
        if mat is None or not mat.use_nodes:
            return

        for node in mat.node_tree.nodes:
            if node.type in ("SHADER_VOLUME_PRINCIPLED",):
                if hasattr(node, "sampling_method"):
                    node.sampling_method = method.value.upper()

    @staticmethod
    def optimize_for_gpu(
        volume: Object | str,
        max_memory_mb: int = 2048,
    ) -> None:
        """
        Optimize volume settings for GPU rendering.

        Args:
            volume: Volume object or name.
            max_memory_mb: Maximum GPU memory in MB.

        Example:
            >>> VolumeRendering.optimize_for_gpu("SmokeVolume", max_memory_mb=4096)
        """
        import bpy

        # Get volume object
        if isinstance(volume, str):
            volume_obj = bpy.data.objects.get(volume)
        else:
            volume_obj = volume

        if volume_obj is None:
            return

        # Adjust step size based on memory budget
        if max_memory_mb >= 4096:
            step_size = 0.0  # Auto
            max_steps = 2048
        elif max_memory_mb >= 2048:
            step_size = 0.0
            max_steps = 1024
        else:
            step_size = 0.05
            max_steps = 512

        settings = VolumeRenderSettings(
            step_size=step_size,
            max_steps=max_steps,
            sampling_method=VolumeSamplingMethod.MULTIPLE_IMPORTANCE,
        )

        VolumeRendering.configure(volume_obj, settings)

    @staticmethod
    def create_principled_volume(
        name: str = "VolumeMaterial",
        density: float = 1.0,
        anisotropy: float = 0.0,
        color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> str:
        """
        Create a Principled Volume material.

        Args:
            name: Material name.
            density: Volume density.
            anisotropy: Scattering anisotropy (-1 to 1).
            color: Volume color.

        Returns:
            Name of the created material.

        Example:
            >>> mat = VolumeRendering.create_principled_volume(
            ...     "SmokeMat",
            ...     density=0.5,
            ...     anisotropy=0.2,
            ... )
        """
        import bpy

        # Create material
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        tree = mat.node_tree

        # Clear default nodes
        for node in tree.nodes:
            tree.nodes.remove(node)

        # Create Principled Volume
        volume = tree.nodes.new("ShaderNodeVolumePrincipled")
        volume.inputs["Density"].default_value = density
        volume.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)

        if "Anisotropy" in volume.inputs:
            volume.inputs["Anisotropy"].default_value = anisotropy

        # Create output
        output = tree.nodes.new("ShaderNodeOutputMaterial")

        # Position nodes
        volume.location = (0, 0)
        output.location = (300, 0)

        # Link
        tree.links.new(volume.outputs["Volume"], output.inputs["Volume"])

        return mat.name

    @staticmethod
    def create_emission_volume(
        name: str = "EmissionVolume",
        emission_strength: float = 1.0,
        emission_color: tuple[float, float, float] = (1.0, 0.5, 0.1),
        density: float = 0.5,
    ) -> str:
        """
        Create an emission volume material (fire, glow).

        Args:
            name: Material name.
            emission_strength: Emission strength.
            emission_color: Emission color.
            density: Volume density.

        Returns:
            Name of the created material.

        Example:
            >>> mat = VolumeRendering.create_emission_volume(
            ...     "FireMat",
            ...     emission_strength=5.0,
            ...     emission_color=(1.0, 0.3, 0.0),
            ... )
        """
        import bpy

        # Create material
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        tree = mat.node_tree

        # Clear default nodes
        for node in tree.nodes:
            tree.nodes.remove(node)

        # Create Principled Volume with emission
        volume = tree.nodes.new("ShaderNodeVolumePrincipled")
        volume.inputs["Density"].default_value = density
        volume.inputs["Emission Strength"].default_value = emission_strength
        volume.inputs["Emission Color"].default_value = (
            emission_color[0],
            emission_color[1],
            emission_color[2],
            1.0,
        )

        # Create output
        output = tree.nodes.new("ShaderNodeOutputMaterial")

        # Position nodes
        volume.location = (0, 0)
        output.location = (300, 0)

        # Link
        tree.links.new(volume.outputs["Volume"], output.inputs["Volume"])

        return mat.name

    @staticmethod
    def get_quality_presets() -> list[str]:
        """
        Get list of available quality presets.

        Returns:
            List of preset names.
        """
        return list(VOLUME_QUALITY_PRESETS.keys())

    @staticmethod
    def apply_preset(volume: Object | str, preset: str) -> None:
        """
        Apply a quality preset to a volume.

        Args:
            volume: Volume object or name.
            preset: Preset name ('preview', 'standard', 'high', 'ultra').

        Example:
            >>> VolumeRendering.apply_preset("SmokeVolume", "high")
        """
        if preset not in VOLUME_QUALITY_PRESETS:
            raise ValueError(
                f"Unknown preset: {preset}. "
                f"Options: {list(VOLUME_QUALITY_PRESETS.keys())}"
            )

        settings = VOLUME_QUALITY_PRESETS[preset]
        VolumeRendering.configure(volume, settings)


# Convenience exports
__all__ = [
    "VolumeRendering",
    "VolumeSamplingMethod",
    "VolumeInterpolation",
    "VolumeRenderSettings",
    "VOLUME_QUALITY_PRESETS",
]
