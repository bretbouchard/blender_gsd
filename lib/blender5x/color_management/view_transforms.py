"""
View Transform Utilities for Blender 5.0+.

Provides tools for managing and customizing view transforms,
including custom LUT support, filmic curve adjustments, and
display-specific configurations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    import bpy
    from bpy.types import Scene


class ViewTransformCategory(Enum):
    """Categories of view transforms."""

    SDR = "sdr"
    """Standard Dynamic Range transforms."""

    HDR = "hdr"
    """High Dynamic Range transforms."""

    LOG = "log"
    """Logarithmic encoding transforms."""

    RAW = "raw"
    """Raw/linear transforms (no transform)."""

    DEBUG = "debug"
    """Debug visualization transforms."""


@dataclass
class ViewTransformInfo:
    """Information about a view transform."""

    name: str
    """Display name of the transform."""

    identifier: str
    """Internal identifier."""

    category: ViewTransformCategory
    """Transform category."""

    description: str = ""
    """Human-readable description."""

    intended_display: str = "sRGB"
    """Intended display device."""

    peak_brightness: int = 100
    """Target peak brightness in nits."""


# Built-in view transform registry
BUILTIN_TRANSFORMS = {
    # SDR Transforms
    "Standard": ViewTransformInfo(
        name="Standard",
        identifier="Standard",
        category=ViewTransformCategory.SDR,
        description="Filmic sRGB view transform for standard displays",
        intended_display="sRGB",
        peak_brightness=100,
    ),
    "Filmic": ViewTransformInfo(
        name="Filmic",
        identifier="Filmic",
        category=ViewTransformCategory.SDR,
        description="High contrast film-like look",
        intended_display="sRGB",
        peak_brightness=100,
    ),
    "Filmic Log": ViewTransformInfo(
        name="Filmic Log",
        identifier="Filmic Log",
        category=ViewTransformCategory.LOG,
        description="Logarithmic filmic encoding",
        intended_display="sRGB",
        peak_brightness=100,
    ),
    # ACES 1.3 Transforms
    "ACES 1.0 SDR-video": ViewTransformInfo(
        name="ACES 1.0 SDR-video",
        identifier="ACES 1.0 SDR-video",
        category=ViewTransformCategory.SDR,
        description="ACES 1.0 SDR output transform",
        intended_display="sRGB",
        peak_brightness=100,
    ),
    # ACES 2.0 Transforms (Blender 5.0+)
    "ACES 2.0 Rec.709": ViewTransformInfo(
        name="ACES 2.0 Rec.709",
        identifier="ACES 2.0 Rec.709",
        category=ViewTransformCategory.SDR,
        description="ACES 2.0 output for Rec.709/sRGB displays",
        intended_display="sRGB",
        peak_brightness=100,
    ),
    "ACES 2.0 P3-D65": ViewTransformInfo(
        name="ACES 2.0 P3-D65",
        identifier="ACES 2.0 P3-D65",
        category=ViewTransformCategory.SDR,
        description="ACES 2.0 output for Display P3",
        intended_display="Display P3",
        peak_brightness=100,
    ),
    "ACES 2.0 Rec.2020 (ST 2084)": ViewTransformInfo(
        name="ACES 2.0 Rec.2020 (ST 2084)",
        identifier="ACES 2.0 Rec.2020 (ST 2084)",
        category=ViewTransformCategory.HDR,
        description="ACES 2.0 HDR output with PQ transfer",
        intended_display="Rec.2020",
        peak_brightness=10000,
    ),
    "ACES 2.0 Rec.2020 (HLG)": ViewTransformInfo(
        name="ACES 2.0 Rec.2020 (HLG)",
        identifier="ACES 2.0 Rec.2020 (HLG)",
        category=ViewTransformCategory.HDR,
        description="ACES 2.0 HDR output with HLG transfer",
        intended_display="Rec.2020",
        peak_brightness=1000,
    ),
    # Debug Transforms
    "False Color": ViewTransformInfo(
        name="False Color",
        identifier="False Color",
        category=ViewTransformCategory.DEBUG,
        description="Exposure visualization with color mapping",
        intended_display="sRGB",
        peak_brightness=100,
    ),
    "Raw": ViewTransformInfo(
        name="Raw",
        identifier="Raw",
        category=ViewTransformCategory.RAW,
        description="No view transform applied",
        intended_display="Any",
        peak_brightness=0,
    ),
}


class ViewTransforms:
    """
    View transform management utilities.

    Provides tools for querying, comparing, and applying view transforms.

    Example:
        >>> ViewTransforms.list_by_category(ViewTransformCategory.HDR)
        >>> ViewTransforms.compare_transforms(["Filmic", "ACES 2.0 Rec.709"])
    """

    @staticmethod
    def list_by_category(category: ViewTransformCategory) -> list[ViewTransformInfo]:
        """
        List all view transforms in a category.

        Args:
            category: Category to filter by.

        Returns:
            List of ViewTransformInfo for matching transforms.
        """
        return [
            info
            for info in BUILTIN_TRANSFORMS.values()
            if info.category == category
        ]

    @staticmethod
    def get_transform(name: str) -> ViewTransformInfo | None:
        """
        Get information about a specific transform.

        Args:
            name: Transform name.

        Returns:
            ViewTransformInfo if found, None otherwise.
        """
        return BUILTIN_TRANSFORMS.get(name)

    @staticmethod
    def apply_transform(
        scene: Scene,
        transform_name: str,
        display_device: str = "sRGB",
    ) -> None:
        """
        Apply a view transform to a scene.

        Args:
            scene: Scene to configure.
            transform_name: Name of the view transform.
            display_device: Display device name.

        Raises:
            ValueError: If transform is not available.

        Example:
            >>> ViewTransforms.apply_transform(scene, "ACES 2.0 Rec.709")
        """
        # Set display device
        scene.display_settings.display_device = display_device

        # Validate transform
        if transform_name not in BUILTIN_TRANSFORMS:
            # Check if available in Blender
            import bpy

            view_items = bpy.types.Scene.bl_rna.properties[
                "view_settings"
            ].nested.properties["view_transform"].enum_items

            available = [item.identifier for item in view_items]

            if transform_name not in available:
                raise ValueError(
                    f"Transform '{transform_name}' not available. "
                    f"Available: {available}"
                )

        # Apply transform
        scene.view_settings.view_transform = transform_name

    @staticmethod
    def compare_transforms(
        transform_names: list[str],
    ) -> list[dict]:
        """
        Compare multiple view transforms.

        Args:
            transform_names: List of transform names to compare.

        Returns:
            List of comparison dictionaries with characteristics.

        Example:
            >>> comparison = ViewTransforms.compare_transforms(
            ...     ["Filmic", "ACES 2.0 Rec.709", "Standard"]
            ... )
        """
        results = []

        for name in transform_names:
            info = BUILTIN_TRANSFORMS.get(name)

            if info is None:
                continue

            results.append(
                {
                    "name": info.name,
                    "category": info.category.value,
                    "intended_display": info.intended_display,
                    "peak_brightness": info.peak_brightness,
                    "description": info.description,
                }
            )

        return results

    @staticmethod
    def get_recommended_transform(
        target_display: str = "sRGB",
        is_hdr: bool = False,
        use_aces: bool = True,
    ) -> str:
        """
        Get recommended view transform for a target setup.

        Args:
            target_display: Target display device.
            is_hdr: Whether targeting HDR output.
            use_aces: Prefer ACES workflow if available.

        Returns:
            Recommended transform name.

        Example:
            >>> transform = ViewTransforms.get_recommended_transform(
            ...     target_display="Display P3",
            ...     is_hdr=False,
            ...     use_aces=True,
            ... )
        """
        if is_hdr:
            if use_aces:
                return "ACES 2.0 Rec.2020 (ST 2084)"
            else:
                return "Filmic Log"  # For manual HDR grade

        # SDR recommendations
        if use_aces:
            if target_display == "Display P3":
                return "ACES 2.0 P3-D65"
            else:
                return "ACES 2.0 Rec.709"
        else:
            return "Filmic"


class FilmicControls:
    """
    Filmic view transform controls for Blender 5.0+.

    Provides fine-grained control over the Filmic view transform,
    including contrast, shadows, highlights, and shoulder adjustments.

    Example:
        >>> FilmicControls.set_high_contrast(scene)
        >>> FilmicControls.configure_for_vfx(scene)
    """

    # Filmic preset configurations
    PRESETS = {
        "default": {
            "contrast": 0.0,
            "shoulder": 0.0,
            "toe": 0.0,
            "exposure": 0.0,
            "gamma": 1.0,
        },
        "high_contrast": {
            "contrast": 0.25,
            "shoulder": 0.2,
            "toe": 0.1,
            "exposure": 0.0,
            "gamma": 1.0,
        },
        "low_contrast": {
            "contrast": -0.2,
            "shoulder": -0.1,
            "toe": -0.05,
            "exposure": 0.0,
            "gamma": 1.1,
        },
        "vfx": {
            "contrast": 0.1,
            "shoulder": 0.3,
            "toe": 0.15,
            "exposure": 0.0,
            "gamma": 1.0,
        },
        "photorealistic": {
            "contrast": 0.15,
            "shoulder": 0.25,
            "toe": 0.1,
            "exposure": 0.0,
            "gamma": 1.0,
        },
        "stylized": {
            "contrast": 0.35,
            "shoulder": 0.4,
            "toe": 0.2,
            "exposure": 0.0,
            "gamma": 0.95,
        },
    }

    @staticmethod
    def apply_preset(scene: Scene, preset: str) -> None:
        """
        Apply a Filmic preset to a scene.

        Args:
            scene: Scene to configure.
            preset: Preset name. Options: 'default', 'high_contrast',
                'low_contrast', 'vfx', 'photorealistic', 'stylized'.

        Raises:
            ValueError: If preset is not valid.

        Example:
            >>> FilmicControls.apply_preset(scene, "high_contrast")
        """
        if preset not in FilmicControls.PRESETS:
            raise ValueError(
                f"Invalid preset: {preset}. "
                f"Options: {list(FilmicControls.PRESETS.keys())}"
            )

        settings = FilmicControls.PRESETS[preset]

        # Apply view transform
        scene.view_settings.view_transform = "Filmic"

        # Apply settings
        scene.view_settings.exposure = settings["exposure"]
        scene.view_settings.gamma = settings["gamma"]

        # Apply contrast if available (Blender 5.0+)
        if hasattr(scene.view_settings, "contrast"):
            scene.view_settings.contrast = settings["contrast"]

        # Apply shoulder and toe if available
        if hasattr(scene.view_settings, "shoulder"):
            scene.view_settings.shoulder = settings["shoulder"]

        if hasattr(scene.view_settings, "toe"):
            scene.view_settings.toe = settings["toe"]

    @staticmethod
    def set_high_contrast(scene: Scene) -> None:
        """Apply high contrast Filmic preset."""
        FilmicControls.apply_preset(scene, "high_contrast")

    @staticmethod
    def configure_for_vfx(scene: Scene) -> None:
        """Configure Filmic for VFX/CGI integration work."""
        FilmicControls.apply_preset(scene, "vfx")

    @staticmethod
    def configure_for_photorealism(scene: Scene) -> None:
        """Configure Filmic for photorealistic rendering."""
        FilmicControls.apply_preset(scene, "photorealistic")

    @staticmethod
    def set_custom_curve(
        scene: Scene,
        contrast: float = 0.0,
        shoulder: float = 0.0,
        toe: float = 0.0,
        exposure: float = 0.0,
        gamma: float = 1.0,
    ) -> None:
        """
        Set custom Filmic curve parameters.

        Args:
            scene: Scene to configure.
            contrast: Contrast adjustment (-1 to 1).
            shoulder: Highlight shoulder adjustment.
            toe: Shadow toe adjustment.
            exposure: Exposure compensation in stops.
            gamma: Gamma correction value.
        """
        scene.view_settings.view_transform = "Filmic"
        scene.view_settings.exposure = exposure
        scene.view_settings.gamma = gamma

        if hasattr(scene.view_settings, "contrast"):
            scene.view_settings.contrast = contrast

        if hasattr(scene.view_settings, "shoulder"):
            scene.view_settings.shoulder = shoulder

        if hasattr(scene.view_settings, "toe"):
            scene.view_settings.toe = toe


# Convenience exports
__all__ = [
    "ViewTransforms",
    "ViewTransformInfo",
    "ViewTransformCategory",
    "FilmicControls",
    "BUILTIN_TRANSFORMS",
]
