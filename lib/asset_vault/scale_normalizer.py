"""
Asset Vault Scale Normalizer

Normalize asset scales to consistent units using reference-based detection.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .types import AssetInfo


# Reference scales (multiplier to convert to meters)
REFERENCE_SCALES: Dict[str, float] = {
    "1_unit = 1_meter": 1.0,
    "1_unit = 1_centimeter": 0.01,
    "1_unit = 1_inch": 0.0254,
    "1_unit = 1_foot": 0.3048,
    "1_unit = 1_yard": 0.9144,
    "z_up_meters": 1.0,
    "y_up_meters": 1.0,
}

# Known object heights in meters for scale detection heuristics
REFERENCE_HEIGHTS: Dict[str, Tuple[float, float]] = {
    # object_type: (min_height, max_height)
    "human_figure": (1.6, 2.0),
    "door": (2.0, 2.4),
    "car": (1.4, 1.8),
    "chair_seat": (0.4, 0.5),
    "table": (0.7, 0.9),
    "building_floor": (2.8, 3.5),
}


@dataclass
class ScaleInfo:
    """Information about detected scale."""
    detected_scale: float  # Multiplier to convert to meters
    confidence: float  # 0.0 to 1.0
    method: str  # "metadata", "heuristic", "reference", "default"
    reference_object: Optional[str] = None  # e.g., "human_figure_1.8m"
    details: str = ""


class ScaleNormalizer:
    """
    Detect and normalize asset scales.

    Uses multiple methods to determine scale:
    1. Metadata (if stored in asset)
    2. Reference object comparison
    3. Heuristic detection
    """

    def __init__(self, reference_scale: float = 1.0):
        """
        Initialize the normalizer.

        Args:
            reference_scale: Default scale to use when detection fails
        """
        self.reference_scale = reference_scale

    def detect_scale(self, asset: AssetInfo) -> ScaleInfo:
        """
        Detect the scale of an asset.

        Args:
            asset: Asset to analyze

        Returns:
            ScaleInfo with detection results
        """
        # Method 1: Check metadata scale
        if asset.scale_reference:
            if asset.scale_reference in REFERENCE_SCALES:
                return ScaleInfo(
                    detected_scale=REFERENCE_SCALES[asset.scale_reference],
                    confidence=1.0,
                    method="metadata",
                    reference_object=asset.scale_reference,
                    details=f"Scale from metadata: {asset.scale_reference}",
                )

        # Method 2: Heuristic detection from dimensions
        if asset.dimensions:
            height = asset.dimensions[1]  # Y is usually up
            heuristic_result = self._detect_scale_from_height(height, asset.category)
            if heuristic_result:
                return heuristic_result

        # Method 3: Category-based default
        if asset.category:
            category_scales: Dict[str, float] = {
                # Default 1 unit = 1 meter for most categories
            }
            default = category_scales.get(asset.category.value, self.reference_scale)
            return ScaleInfo(
                detected_scale=default,
                confidence=0.3,
                method="default",
                details=f"Default scale for category: {asset.category.value}",
            )

        # Fallback
        return ScaleInfo(
            detected_scale=self.reference_scale,
            confidence=0.1,
            method="default",
            details="No scale detection possible, using reference scale",
        )

    def _detect_scale_from_height(
        self,
        height: float,
        category: Optional[Any],
    ) -> Optional[ScaleInfo]:
        """
        Detect scale by comparing height to known objects.

        Args:
            height: Measured height in current units
            category: Asset category for context

        Returns:
            ScaleInfo if detected, None otherwise
        """
        # Check against reference heights
        for ref_name, (min_h, max_h) in REFERENCE_HEIGHTS.items():
            # If the height is within expected range, scale is 1:1
            if min_h <= height <= max_h:
                return ScaleInfo(
                    detected_scale=1.0,
                    confidence=0.7,
                    method="heuristic",
                    reference_object=ref_name,
                    details=f"Height {height:.2f} matches {ref_name} ({min_h}-{max_h})",
                )

            # If height is 10x too small, might be in decimeters
            if min_h <= height * 10 <= max_h:
                return ScaleInfo(
                    detected_scale=0.1,
                    confidence=0.6,
                    method="heuristic",
                    reference_object=ref_name,
                    details=f"Height suggests decimeters (x10 = {height*10:.2f})",
                )

            # If height is 100x too small, might be in centimeters
            if min_h <= height * 100 <= max_h:
                return ScaleInfo(
                    detected_scale=0.01,
                    confidence=0.6,
                    method="heuristic",
                    reference_object=ref_name,
                    details=f"Height suggests centimeters (x100 = {height*100:.2f})",
                )

            # If height is 39x too small, might be in inches
            if min_h <= height * 39.37 <= max_h:
                return ScaleInfo(
                    detected_scale=0.0254,
                    confidence=0.5,
                    method="heuristic",
                    reference_object=ref_name,
                    details="Height suggests inches",
                )

        return None

    def normalize_scale(
        self,
        asset: AssetInfo,
        target_scale: float = 1.0,
    ) -> Tuple[float, ScaleInfo]:
        """
        Calculate scale multiplier to normalize asset.

        Args:
            asset: Asset to normalize
            target_scale: Target scale (default: 1 meter per unit)

        Returns:
            Tuple of (multiplier, scale_info)
        """
        info = self.detect_scale(asset)

        # Calculate multiplier
        # If detected_scale is 0.01 (cm), we need to multiply by 100
        multiplier = target_scale / info.detected_scale if info.detected_scale != 0 else 1.0

        return multiplier, info

    def set_reference_object(
        self,
        asset: AssetInfo,
        known_height: float,
        object_name: Optional[str] = None,
    ) -> float:
        """
        Calibrate scale using a known reference object.

        Args:
            asset: Asset to calibrate
            known_height: Actual height of reference object in meters
            object_name: Name of reference object (for logging)

        Returns:
            Scale factor to apply
        """
        if not asset.dimensions:
            raise ValueError("Asset has no dimensions")

        measured_height = asset.dimensions[1]  # Y is usually up
        scale_factor = known_height / measured_height if measured_height != 0 else 1.0

        # Store reference in metadata
        asset.scale_reference = f"calibrated:{object_name or 'unknown'}:{known_height}m"

        return scale_factor

    def apply_scale_to_asset(self, asset: AssetInfo, scale: float) -> bool:
        """
        Apply scale to asset dimensions.

        Note: This only updates the AssetInfo, not the actual file.

        Args:
            asset: Asset to scale
            scale: Scale multiplier

        Returns:
            True if successful
        """
        if asset.dimensions:
            asset.dimensions = tuple(d * scale for d in asset.dimensions)
            return True
        return False


def apply_scale_to_blend(path, scale: float) -> bool:
    """
    Apply scale transform to all objects in a .blend file.

    Requires bpy (Blender Python API).

    Args:
        path: Path to .blend file
        scale: Scale multiplier

    Returns:
        True if successful, False if bpy unavailable
    """
    try:
        import bpy

        # This would be implemented for Blender operations
        # For now, return False to indicate bpy integration needed
        return False

    except ImportError:
        return False
