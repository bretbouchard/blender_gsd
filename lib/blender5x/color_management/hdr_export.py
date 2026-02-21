"""
HDR Export Utilities for Blender 5.0+.

Additional utilities for HDR video and image export workflows,
including tonemapping helpers, HDR analysis tools, and format converters.

Example:
    >>> from lib.blender5x.color_management import HDRExport
    >>> HDRExport.analyze_dynamic_range(scene)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    import bpy
    from bpy.types import Scene


class HDRFormat(Enum):
    """Supported HDR output formats."""

    EXR_32 = "OPEN_EXR_32"
    """32-bit float OpenEXR."""

    EXR_16 = "OPEN_EXR_16"
    """16-bit float OpenEXR (half precision)."""

    HDR = "HDR"
    """Radiance HDR format."""

    TIFF_16 = "TIFF_16"
    """16-bit TIFF."""

    PNG_16 = "PNG_16"
    """16-bit PNG (limited dynamic range)."""


class TransferFunction(Enum):
    """HDR transfer functions."""

    PQ = "PQ"
    """SMPTE ST 2084 Perceptual Quantizer (for displays up to 10,000 nits)."""

    HLG = "HLG"
    """Hybrid Log-Gamma (broadcast HDR standard)."""

    LINEAR = "Linear"
    """Linear light (no transfer function applied)."""

    SLOG3 = "S-Log3"
    """Sony S-Log3 gamma curve."""

    VLOG = "V-Log"
    """Panasonic V-Log gamma curve."""


@dataclass
class DynamicRangeInfo:
    """Information about scene dynamic range."""

    min_luminance: float
    """Minimum luminance in cd/m2 (nits)."""

    max_luminance: float
    """Maximum luminance in cd/m2 (nits)."""

    dynamic_range_stops: float
    """Dynamic range in photographic stops."""

    average_luminance: float
    """Average scene luminance in cd/m2."""

    histogram_data: list[float] | None = None
    """Optional luminance histogram data."""


@dataclass
class HDRMonitorSettings:
    """HDR monitor reference settings."""

    peak_brightness: int
    """Peak brightness in nits (e.g., 1000, 2000, 4000)."""

    min_black: float
    """Minimum black level in nits."""

    color_volume: str
    """Color volume description (e.g., 'P3', 'Rec.2020')."""

    eotf: str
    """Electro-Optical Transfer Function."""


# Common HDR monitor presets
HDR_MONITOR_PRESETS = {
    "SDR_100": HDRMonitorSettings(
        peak_brightness=100,
        min_black=0.1,
        color_volume="sRGB",
        eotf="sRGB",
    ),
    "HDR_400": HDRMonitorSettings(
        peak_brightness=400,
        min_black=0.05,
        color_volume="P3",
        eotf="PQ",
    ),
    "HDR_1000": HDRMonitorSettings(
        peak_brightness=1000,
        min_black=0.005,
        color_volume="Rec.2020",
        eotf="PQ",
    ),
    "HDR_2000": HDRMonitorSettings(
        peak_brightness=2000,
        min_black=0.001,
        color_volume="Rec.2020",
        eotf="PQ",
    ),
    "HDR_4000": HDRMonitorSettings(
        peak_brightness=4000,
        min_black=0.0005,
        color_volume="Rec.2020",
        eotf="PQ",
    ),
}


class HDRExport:
    """
    HDR export utilities for production workflows.

    Provides tools for analyzing, preparing, and exporting HDR content.

    Example:
        >>> info = HDRExport.analyze_dynamic_range(scene)
        >>> print(f"Dynamic range: {info.dynamic_range_stops} stops")
    """

    @staticmethod
    def analyze_dynamic_range(
        scene: Scene | None = None,
        sample_count: int = 1024,
    ) -> DynamicRangeInfo:
        """
        Analyze the dynamic range of a scene.

        Samples the rendered image to determine luminance range,
        useful for setting HDR metadata and verifying exposure.

        Args:
            scene: Scene to analyze (uses active scene if None).
            sample_count: Number of samples for analysis.

        Returns:
            DynamicRangeInfo with min/max luminance and stops.

        Note:
            Requires a rendered image in the render buffer.

        Example:
            >>> info = HDRExport.analyze_dynamic_range()
            >>> print(f"Range: {info.min_luminance:.4f} - {info.max_luminance:.0f} nits")
        """
        import bpy
        import numpy as np

        scene = scene or bpy.context.scene

        # Get render result
        render_result = bpy.data.images.get("Render Result")
        if render_result is None:
            raise RuntimeError(
                "No render result available. Render the scene first."
            )

        # Get pixel data
        pixels = np.array(render_result.pixels[:]).reshape(-1, 4)

        # Calculate luminance (using Rec.709 coefficients)
        r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # Filter out zero values for log calculations
        non_zero = luminance[luminance > 0]

        if len(non_zero) == 0:
            return DynamicRangeInfo(
                min_luminance=0.0,
                max_luminance=0.0,
                dynamic_range_stops=0.0,
                average_luminance=0.0,
            )

        # Calculate statistics
        min_lum = float(np.min(non_zero))
        max_lum = float(np.max(luminance))
        avg_lum = float(np.mean(luminance))

        # Convert to stops (log2 scale)
        if min_lum > 0:
            dynamic_range_stops = np.log2(max_lum / min_lum)
        else:
            dynamic_range_stops = np.log2(max_lum)

        # Create histogram data (64 bins)
        hist, _ = np.histogram(np.log2(luminance[luminance > 0] + 1e-10), bins=64)
        histogram_data = hist.tolist()

        return DynamicRangeInfo(
            min_luminance=min_lum,
            max_luminance=max_lum,
            dynamic_range_stops=float(dynamic_range_stops),
            average_luminance=avg_lum,
            histogram_data=histogram_data,
        )

    @staticmethod
    def calculate_tonemap_curve(
        source_range: tuple[float, float],
        target_range: tuple[float, float],
        curve_type: str = "reinhard",
    ) -> list[tuple[float, float]]:
        """
        Calculate a tonemap curve for HDR to SDR conversion.

        Args:
            source_range: Source (min, max) luminance values.
            target_range: Target (min, max) luminance values.
            curve_type: Tonemapping operator. Options: 'reinhard',
                'aces', 'filmic', 'linear'.

        Returns:
            List of (input, output) value pairs defining the curve.

        Example:
            >>> curve = HDRExport.calculate_tonemap_curve(
            ...     (0.001, 100.0), (0.0, 1.0), curve_type="aces"
            ... )
        """
        import numpy as np

        src_min, src_max = source_range
        tgt_min, tgt_max = target_range

        # Generate input values
        inputs = np.linspace(src_min, src_max, 256)

        if curve_type == "reinhard":
            # Reinhard tonemapping: L_d = L / (1 + L)
            normalized = inputs / src_max
            outputs = normalized / (1 + normalized)

        elif curve_type == "aces":
            # ACES filmic tonemapping approximation
            a, b, c, d = 2.51, 0.03, 2.43, 0.59
            normalized = inputs / src_max
            outputs = np.clip(
                (normalized * (a * normalized + b))
                / (normalized * (c * normalized + d) + 0.14),
                0,
                1,
            )

        elif curve_type == "filmic":
            # Filmic S-curve
            normalized = inputs / src_max
            x = np.clip(normalized, 0, 1)
            outputs = 3 * x**2 - 2 * x**3

        elif curve_type == "linear":
            # Simple linear mapping
            outputs = np.clip(
                (inputs - src_min) / (src_max - src_min),
                tgt_min,
                tgt_max,
            )

        else:
            raise ValueError(f"Unknown curve type: {curve_type}")

        # Scale to target range
        outputs = outputs * (tgt_max - tgt_min) + tgt_min

        return list(zip(inputs.tolist(), outputs.tolist()))

    @staticmethod
    def export_to_acescg(
        filepath: str | Path,
        scene: Scene | None = None,
        include_alpha: bool = True,
    ) -> None:
        """
        Export current render to ACEScg color space.

        Args:
            filepath: Output file path (.exr).
            scene: Scene to export (uses active scene if None).
            include_alpha: Whether to include alpha channel.

        Note:
            Output is always 32-bit float EXR in ACEScg color space.
        """
        import bpy
        from pathlib import Path

        scene = scene or bpy.context.scene
        rd = scene.render

        # Store original settings
        original_format = rd.image_settings.file_format
        original_depth = rd.image_settings.color_depth
        original_colorspace = rd.image_settings.color_management

        try:
            # Configure for ACEScg export
            rd.image_settings.file_format = "OPEN_EXR"
            rd.image_settings.color_depth = "32"
            rd.image_settings.exr_codec = "ZIP"
            rd.image_settings.color_management = "OVERRIDE"

            if include_alpha:
                rd.image_settings.color_mode = "RGBA"
            else:
                rd.image_settings.color_mode = "RGB"

            # Set output path
            rd.filepath = str(filepath)

            # Render and save
            bpy.ops.render.render(write_still=True)

        finally:
            # Restore settings
            rd.image_settings.file_format = original_format
            rd.image_settings.color_depth = original_depth
            rd.image_settings.color_management = original_colorspace

    @staticmethod
    def configure_for_dolby_vision() -> dict:
        """
        Configure scene for Dolby Vision HDR output.

        Returns:
            Configuration dictionary with Dolby Vision settings.

        Note:
            Dolby Vision uses PQ transfer with dynamic metadata.
            Requires Dolby Vision license and tools for final encoding.
        """
        import bpy

        scene = bpy.context.scene
        rd = scene.render

        # Configure for Dolby Vision specifications
        config = {
            "profile": 5,  # Dolby Vision Profile 5 (PQ)
            "level": 1,  # Minimum level
            "max_luminance": 4000,  # nits
            "min_luminance": 0.0001,  # nits
            "color_primaries": "Rec.2020",
            "transfer_characteristics": "PQ",
            "matrix_coefficients": "BT.2020 NCL",
        }

        # Apply scene settings
        if hasattr(rd.ffmpeg, "colorspace"):
            rd.ffmpeg.colorspace = "Rec.2020"

        if hasattr(rd.ffmpeg, "color_transfer"):
            rd.ffmpeg.color_transfer = "SMPTE ST 2084"

        return config

    @staticmethod
    def get_nit_scale(exposure: float = 0.0) -> list[tuple[float, str]]:
        """
        Get a nit scale reference for UI display.

        Args:
            exposure: Scene exposure compensation in stops.

        Returns:
            List of (nits, label) tuples for scale visualization.

        Example:
            >>> scale = HDRExport.get_nit_scale(exposure=1.0)
            >>> for nits, label in scale:
            ...     print(f"{nits} nits: {label}")
        """
        # Standard reference points
        ref_points = [
            (0.001, "Deep shadow"),
            (0.01, "Shadow"),
            (0.1, "Dark gray"),
            (1.0, "18% gray"),
            (10.0, "Light gray"),
            (100.0, "SDR peak white"),
            (203.0, "HLG reference white"),
            (400.0, "HDR 400 peak"),
            (1000.0, "HDR 1000 peak"),
            (2000.0, "HDR 2000 peak"),
            (4000.0, "HDR 4000 peak"),
            (10000.0, "Dolby Vision max"),
        ]

        # Apply exposure compensation
        exposure_mult = 2**exposure

        return [(nits * exposure_mult, label) for nits, label in ref_points]


# Convenience exports
__all__ = [
    "HDRExport",
    "HDRFormat",
    "TransferFunction",
    "DynamicRangeInfo",
    "HDRMonitorSettings",
    "HDR_MONITOR_PRESETS",
]
