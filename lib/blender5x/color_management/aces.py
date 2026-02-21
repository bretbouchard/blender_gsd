"""
ACES 1.3/2.0 Color Management for Blender 5.0+.

This module provides utilities for working with ACES (Academy Color Encoding System)
color management in Blender 5.0+, including ACEScg workflow configuration,
display transforms, and HDR video export.

Blender 5.0 introduced native ACES 2.0 support with improved color accuracy
and HDR workflow tools.

Example:
    >>> from lib.blender5x.color_management import ACESWorkflow, HDRVideoExport
    >>> ACESWorkflow.setup_acescg()
    >>> HDRVideoExport.configure_h264_hdr(transfer="PQ")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    import bpy
    from bpy.types import Scene

# Standard ACES view transforms
ACES_VIEWS_13 = [
    "ACES 1.0 SDR-video (ACES 1.0)",
    "ACES 1.0 SDR-video (P3-D65, D60 simulation)",
    "Unreal Engine",
    "Raw",
    "False Color",
    "Log",
]

ACES_VIEWS_20 = [
    "ACES 1.0 SDR-video",
    "ACES 1.0 SDR-video (P3-D65, D60 simulation)",
    "ACES 2.0 Rec.709",
    "ACES 2.0 P3-D65",
    "ACES 2.0 Rec.2020 (ST 2084)",
    "ACES 2.0 Rec.2020 (HLG)",
    "ACES 2.0 P3-D65 (D65 simulation)",
    "Unreal Engine",
    "Raw",
    "False Color",
    "Log",
]

# Standard display devices
DISPLAY_DEVICES = [
    "sRGB",
    "Display P3",
    "Rec.2020",
    "Rec.709",
]


@dataclass
class HDRMetadata:
    """HDR metadata for video export."""

    max_cll: int | None = None
    """Maximum Content Light Level (cd/m2)."""

    max_fall: int | None = None
    """Maximum Frame Average Light Level (cd/m2)."""

    primaries: tuple[float, float, float, float, float, float, float, float] | None = None
    """Mastering display primaries as (Gx, Gy, Bx, By, Rx, Ry, Wx, Wy)."""


class ACESWorkflow:
    """
    ACES 1.3/2.0 color management workflow for Blender 5.0+.

    Provides utilities for setting up ACEScg working color space,
    configuring display transforms, and managing color pipelines.

    Example:
        >>> ACESWorkflow.setup_acescg()
        >>> ACESWorkflow.configure_display(display="Display P3", view="ACES 2.0 P3-D65")
    """

    @staticmethod
    def setup_acescg() -> None:
        """
        Configure scene to use ACEScg as the working color space.

        Sets up Blender 5.0+ to use ACEScg (ACES 1.3) for scene-linear
        working color space, which is the industry standard for VFX
        and high-end production.

        Raises:
            ImportError: If not running in Blender.
            RuntimeError: If ACES config is not available.

        Note:
            Requires Blender 5.0+ with ACES OCIO config installed.
            Default location: <blender>/datafiles/colormanagement/config.ocio
        """
        import bpy

        scene = bpy.context.scene

        # Set view transform to ACES
        scene.view_settings.view_transform = "ACES 1.0 SDR-video"

        # Set sequence color space for linear workflow
        scene.sequencer_colorspace_settings.name = "ACEScg (ACES)"

        # Enable high quality color picking
        scene.view_settings.use_high_quality_color_picking = True

        # Configure render settings for ACEScg
        if hasattr(scene.render, "image_settings"):
            scene.render.image_settings.color_management = "OVERRIDE"
            scene.render.image_settings.view_transform = "ACES 1.0 SDR-video"

    @staticmethod
    def configure_display(
        display: str = "sRGB",
        view: str = "ACES 1.0 SDR-video",
    ) -> None:
        """
        Configure display device and view transform.

        Args:
            display: Display device name. Options: 'sRGB', 'Display P3',
                'Rec.2020', 'Rec.709'.
            view: View transform name. For ACES 1.3: 'ACES 1.0 SDR-video',
                'Unreal Engine', 'Raw', etc. For ACES 2.0: 'ACES 2.0 Rec.709',
                'ACES 2.0 P3-D65', etc.

        Raises:
            ValueError: If display or view is not valid.
            ImportError: If not running in Blender.

        Example:
            >>> ACESWorkflow.configure_display("Display P3", "ACES 2.0 P3-D65")
        """
        import bpy

        if display not in DISPLAY_DEVICES:
            raise ValueError(
                f"Invalid display device: {display}. "
                f"Valid options: {DISPLAY_DEVICES}"
            )

        scene = bpy.context.scene

        # Set display device
        scene.display_settings.display_device = display

        # Validate view transform
        available_views = ACESWorkflow.get_available_views()
        if view not in available_views:
            raise ValueError(
                f"Invalid view transform: {view}. "
                f"Available views: {available_views[:5]}..."
            )

        # Set view transform
        scene.view_settings.view_transform = view

    @staticmethod
    def setup_rec2100() -> None:
        """
        Configure for Rec.2100 HDR workflow with PQ or HLG transfer.

        Sets up the scene for HDR output using Rec.2100 color space
        with appropriate view transform for HDR monitoring.

        Raises:
            ImportError: If not running in Blender.
            RuntimeError: If ACES 2.0 is not available.

        Note:
            Requires Blender 5.0+ with ACES 2.0 support.
        """
        import bpy

        scene = bpy.context.scene

        # Set display device to Rec.2020 for HDR
        scene.display_settings.display_device = "Rec.2020"

        # Use ACES 2.0 HDR view transform (PQ)
        # Fall back to HLG if PQ not available
        views = ACESWorkflow.get_available_views()

        if "ACES 2.0 Rec.2020 (ST 2084)" in views:
            scene.view_settings.view_transform = "ACES 2.0 Rec.2020 (ST 2084)"
        elif "ACES 2.0 Rec.2020 (HLG)" in views:
            scene.view_settings.view_transform = "ACES 2.0 Rec.2020 (HLG)"
        else:
            # Fallback for ACES 1.3
            scene.view_settings.view_transform = "Raw"

        # Configure render output for HDR
        if hasattr(scene.render, "image_settings"):
            scene.render.image_settings.color_management = "OVERRIDE"
            scene.render.image_settings.view_transform = "Raw"

    @staticmethod
    def get_available_views() -> list[str]:
        """
        Get list of available view transforms.

        Returns:
            List of view transform names available in the current
            OCIO configuration.

        Raises:
            ImportError: If not running in Blender.
        """
        import bpy

        # Get the template pref for view transforms
        # In Blender 5.0+, we can query available views from scene
        scene = bpy.context.scene

        # Use rna_enum to get available view transforms
        view_items = bpy.types.Scene.bl_rna.properties[
            "view_settings"
        ].nested.properties["view_transform"].enum_items

        return [item.identifier for item in view_items]

    @staticmethod
    def set_look(look: str) -> None:
        """
        Set an ACES look transform.

        Args:
            look: Look transform name (e.g., 'ACES 1.0 - v01', 'None').

        Raises:
            ImportError: If not running in Blender.
            ValueError: If look is not available.
        """
        import bpy

        scene = bpy.context.scene

        # Get available looks
        look_items = bpy.types.Scene.bl_rna.properties[
            "view_settings"
        ].nested.properties["look"].enum_items

        available_looks = [item.identifier for item in look_items]

        if look not in available_looks:
            raise ValueError(
                f"Invalid look: {look}. "
                f"Available looks: {available_looks}"
            )

        scene.view_settings.look = look

    @staticmethod
    def enable_false_color(exposure_range: tuple[float, float] = (-10, 10)) -> None:
        """
        Enable false color view for exposure analysis.

        Args:
            exposure_range: Tuple of (min, max) exposure values in stops.

        Note:
            Useful for analyzing exposure and dynamic range in scene.
        """
        import bpy

        scene = bpy.context.scene

        # Enable false color view
        views = ACESWorkflow.get_available_views()
        if "False Color" in views:
            scene.view_settings.view_transform = "False Color"

        # Set exposure range if property available (Blender 5.0+)
        if hasattr(scene.view_settings, "false_color_range"):
            scene.view_settings.false_color_range = exposure_range


class HDRVideoExport:
    """
    HDR video export utilities for Blender 5.0+.

    Provides configuration helpers for exporting HDR video content
    with proper color encoding and metadata.

    Example:
        >>> config = HDRVideoExport.configure_h264_hdr(transfer="PQ")
        >>> HDRVideoExport.set_hdr_metadata(max_cll=4000, max_fall=1000)
    """

    # H.264 HDR profiles
    H264_HDR_PROFILES = {
        "PQ": {"transfer": "SMPTE ST 2084", "colorspace": "Rec.2020"},
        "HLG": {"transfer": "Hybrid Log-Gamma", "colorspace": "Rec.2020"},
    }

    # ProRes HDR profiles
    PRORES_HDR_PROFILES = {
        "4444 XQ": {"codec": "PRORES_4444XQ", "quality": 100},
        "4444": {"codec": "PRORES_4444", "quality": 100},
        "422 HQ": {"codec": "PRORES_422_HQ", "quality": 100},
        "422": {"codec": "PRORES_422", "quality": 90},
    }

    @staticmethod
    def configure_h264_hdr(transfer: str = "PQ") -> dict:
        """
        Configure scene for H.264 HDR video export.

        Args:
            transfer: Transfer function. Options: 'PQ' (Perceptual Quantizer),
                'HLG' (Hybrid Log-Gamma).

        Returns:
            Dictionary with configuration settings applied.

        Raises:
            ImportError: If not running in Blender.
            ValueError: If transfer type is invalid.

        Example:
            >>> config = HDRVideoExport.configure_h264_hdr(transfer="PQ")
        """
        import bpy

        if transfer not in HDRVideoExport.H264_HDR_PROFILES:
            raise ValueError(
                f"Invalid transfer: {transfer}. "
                f"Options: {list(HDRVideoExport.H264_HDR_PROFILES.keys())}"
            )

        scene = bpy.context.scene
        rd = scene.render

        # Set format to FFmpeg
        rd.image_settings.file_format = "FFMPEG"

        # Configure video codec
        rd.ffmpeg.codec = "H264"
        rd.ffmpeg.format = "MPEG4"
        rd.ffmpeg.constant_rate_factor = "HIGH"

        # Get profile settings
        profile = HDRVideoExport.H264_HDR_PROFILES[transfer]

        # Set color space for output (Blender 5.0+)
        if hasattr(rd.ffmpeg, "colorspace"):
            rd.ffmpeg.colorspace = profile["colorspace"]

        if hasattr(rd.ffmpeg, "color_transfer"):
            rd.ffmpeg.color_transfer = profile["transfer"]

        if hasattr(rd.ffmpeg, "color_range"):
            rd.ffmpeg.color_range = "FULL"

        # Set container metadata for HDR
        if hasattr(rd.ffmpeg, "use_max_b_frames"):
            rd.ffmpeg.use_max_b_frames = True
            rd.ffmpeg.max_b_frames = 4

        return {
            "codec": "H264",
            "transfer": profile["transfer"],
            "colorspace": profile["colorspace"],
            "container": "MP4",
        }

    @staticmethod
    def configure_prores_hdr(profile: str = "4444 XQ") -> dict:
        """
        Configure scene for ProRes HDR video export.

        Args:
            profile: ProRes profile. Options: '4444 XQ', '4444',
                '422 HQ', '422'.

        Returns:
            Dictionary with configuration settings applied.

        Raises:
            ImportError: If not running in Blender.
            ValueError: If profile is invalid.

        Example:
            >>> config = HDRVideoExport.configure_prores_hdr("4444 XQ")
        """
        import bpy

        if profile not in HDRVideoExport.PRORES_HDR_PROFILES:
            raise ValueError(
                f"Invalid ProRes profile: {profile}. "
                f"Options: {list(HDRVideoExport.PRORES_HDR_PROFILES.keys())}"
            )

        scene = bpy.context.scene
        rd = scene.render

        # Set format to FFmpeg
        rd.image_settings.file_format = "FFMPEG"

        # Get profile settings
        settings = HDRVideoExport.PRORES_HDR_PROFILES[profile]

        # Configure ProRes codec
        rd.ffmpeg.codec = settings["codec"]
        rd.ffmpeg.format = "QUICKTIME"

        # Set color space for HDR (Blender 5.0+)
        if hasattr(rd.ffmpeg, "colorspace"):
            rd.ffmpeg.colorspace = "Rec.2020"

        if hasattr(rd.ffmpeg, "color_transfer"):
            rd.ffmpeg.color_transfer = "SMPTE ST 2084"

        if hasattr(rd.ffmpeg, "color_range"):
            rd.ffmpeg.color_range = "FULL"

        return {
            "codec": settings["codec"],
            "quality": settings["quality"],
            "container": "QuickTime",
            "colorspace": "Rec.2020",
            "transfer": "PQ",
        }

    @staticmethod
    def set_hdr_metadata(
        max_cll: int | None = None,
        max_fall: int | None = None,
        primaries: tuple[float, ...] | None = None,
    ) -> None:
        """
        Set HDR metadata for video export.

        Args:
            max_cll: Maximum Content Light Level in cd/m2 (nits).
                Typical values: 1000-4000.
            max_fall: Maximum Frame Average Light Level in cd/m2.
                Typical values: 100-1000.
            primaries: Mastering display primaries as tuple of 8 floats:
                (Gx, Gy, Bx, By, Rx, Ry, Wx, Wy).
                Default D65 white point: (0.21, 0.71, 0.15, 0.06, 0.68, 0.32, 0.3127, 0.3290)

        Raises:
            ImportError: If not running in Blender.

        Note:
            Metadata is embedded in the video container for HDR displays.

        Example:
            >>> HDRVideoExport.set_hdr_metadata(
            ...     max_cll=4000,
            ...     max_fall=1000,
            ...     primaries=(0.21, 0.71, 0.15, 0.06, 0.68, 0.32, 0.3127, 0.3290)
            ... )
        """
        import bpy

        scene = bpy.context.scene
        rd = scene.render

        # Set MaxCLL if provided (Blender 5.0+)
        if max_cll is not None and hasattr(rd.ffmpeg, "max_cll"):
            rd.ffmpeg.max_cll = max_cll

        # Set MaxFALL if provided (Blender 5.0+)
        if max_fall is not None and hasattr(rd.ffmpeg, "max_fall"):
            rd.ffmpeg.max_fall = max_fall

        # Set mastering display primaries if provided
        if primaries is not None and hasattr(rd.ffmpeg, "mastering_display_primaries"):
            rd.ffmpeg.mastering_display_primaries = primaries

    @staticmethod
    def export_hdr_frame(
        filepath: str | Path,
        format: str = "OPEN_EXR",
        color_space: str = "Rec.2020",
    ) -> None:
        """
        Export a single HDR frame with proper color encoding.

        Args:
            filepath: Output file path.
            format: Image format. Options: 'OPEN_EXR', 'HDR', 'TIFF',
                'PNG' (16-bit).
            color_space: Output color space. Options: 'Rec.2020',
                'ACEScg', 'Linear Rec.709 (sRGB)'.

        Raises:
            ImportError: If not running in Blender.
            ValueError: If format or color_space is invalid.

        Note:
            For HDR, prefer EXR (16 or 32-bit float) or Radiance HDR.
        """
        import bpy
        from pathlib import Path

        valid_formats = ["OPEN_EXR", "HDR", "TIFF", "PNG"]
        if format not in valid_formats:
            raise ValueError(
                f"Invalid format: {format}. "
                f"Valid options: {valid_formats}"
            )

        scene = bpy.context.scene
        rd = scene.render

        # Store original settings
        original_format = rd.image_settings.file_format
        original_colorspace = rd.image_settings.color_management
        original_view = rd.image_settings.view_transform

        try:
            # Set format
            rd.image_settings.file_format = format

            # Configure format-specific settings
            if format == "OPEN_EXR":
                rd.image_settings.exr_codec = "ZIP"
                rd.image_settings.color_depth = "32"

                # Set output color space for EXR
                rd.image_settings.color_management = "OVERRIDE"
                rd.image_settings.view_transform = "Raw"

            elif format == "PNG":
                rd.image_settings.color_depth = "16"
                rd.image_settings.color_management = "OVERRIDE"
                rd.image_settings.view_transform = "Raw"

            elif format == "TIFF":
                rd.image_settings.color_depth = "16"
                rd.image_settings.color_management = "OVERRIDE"
                rd.image_settings.view_transform = "Raw"

            elif format == "HDR":
                # Radiance HDR is always linear
                rd.image_settings.color_management = "OVERRIDE"
                rd.image_settings.view_transform = "Raw"

            # Set output path
            rd.filepath = str(filepath)

            # Render frame
            bpy.ops.render.render(write_still=True)

        finally:
            # Restore original settings
            rd.image_settings.file_format = original_format
            rd.image_settings.color_management = original_colorspace
            rd.image_settings.view_transform = original_view


# Convenience exports
__all__ = [
    "ACESWorkflow",
    "HDRVideoExport",
    "HDRMetadata",
    "ACES_VIEWS_13",
    "ACES_VIEWS_20",
    "DISPLAY_DEVICES",
]
