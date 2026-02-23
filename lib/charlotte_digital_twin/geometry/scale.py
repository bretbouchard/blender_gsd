"""
Scale Management for Charlotte Digital Twin

Handles scene scale, unit conversion, and size presets.

Usage:
    from lib.charlotte_digital_twin.geometry import ScaleManager, ScalePreset

    manager = ScaleManager()
    manager.set_scale(ScalePreset.REALISTIC)  # 1m = 1 BU

    # Convert sizes
    road_width_bu = manager.meters_to_blender(7.0)  # 7 meters to Blender units
    building_height_m = manager.blender_to_meters(50.0)  # 50 BU to meters
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class ScalePreset(Enum):
    """Scale presets for scene configuration."""
    REALISTIC = "realistic"      # 1 meter = 1 Blender unit
    HALF = "half"                # 1 meter = 0.5 Blender units
    DOUBLE = "double"            # 1 meter = 2 Blender units
    DECIMETER = "decimeter"      # 1 meter = 10 Blender units (1 BU = 10cm)
    CENTIMETER = "centimeter"    # 1 meter = 100 Blender units (1 BU = 1cm)
    KILOMETER = "kilometer"      # 1 kilometer = 1 Blender unit


@dataclass
class ScaleConfig:
    """Configuration for scene scale."""
    meters_per_blender_unit: float = 1.0
    name: str = "Realistic"
    description: str = "1 meter = 1 Blender unit"

    @classmethod
    def from_preset(cls, preset: ScalePreset) -> "ScaleConfig":
        """Create from preset."""
        configs = {
            ScalePreset.REALISTIC: cls(
                meters_per_blender_unit=1.0,
                name="Realistic",
                description="1 meter = 1 Blender unit"
            ),
            ScalePreset.HALF: cls(
                meters_per_blender_unit=2.0,
                name="Half Scale",
                description="1 meter = 0.5 Blender units"
            ),
            ScalePreset.DOUBLE: cls(
                meters_per_blender_unit=0.5,
                name="Double Scale",
                description="1 meter = 2 Blender units"
            ),
            ScalePreset.DECIMETER: cls(
                meters_per_blender_unit=0.1,
                name="Decimeter",
                description="1 meter = 10 Blender units (1 BU = 10cm)"
            ),
            ScalePreset.CENTIMETER: cls(
                meters_per_blender_unit=0.01,
                name="Centimeter",
                description="1 meter = 100 Blender units (1 BU = 1cm)"
            ),
            ScalePreset.KILOMETER: cls(
                meters_per_blender_unit=1000.0,
                name="Kilometer",
                description="1 kilometer = 1 Blender unit"
            ),
        }
        return configs[preset]


class ScaleManager:
    """
    Manages scene scale and unit conversions.

    The default scale is "realistic" where 1 meter = 1 Blender unit.
    This works well for most real-world scenes and matches Blender's
    default unit settings.
    """

    def __init__(self, preset: Optional[ScalePreset] = None):
        """
        Initialize scale manager.

        Args:
            preset: Scale preset (default: REALISTIC)
        """
        self._preset = preset or ScalePreset.REALISTIC
        self._config = ScaleConfig.from_preset(self._preset)

    @property
    def scale(self) -> float:
        """Get meters per Blender unit."""
        return self._config.meters_per_blender_unit

    @property
    def blender_units_per_meter(self) -> float:
        """Get Blender units per meter."""
        return 1.0 / self._config.meters_per_blender_unit

    def set_scale(self, preset: ScalePreset) -> None:
        """Set scale from preset."""
        self._preset = preset
        self._config = ScaleConfig.from_preset(preset)

    def meters_to_blender(self, meters: float) -> float:
        """
        Convert meters to Blender units.

        Args:
            meters: Distance in meters

        Returns:
            Distance in Blender units
        """
        return meters / self._config.meters_per_blender_unit

    def blender_to_meters(self, blender_units: float) -> float:
        """
        Convert Blender units to meters.

        Args:
            blender_units: Distance in Blender units

        Returns:
            Distance in meters
        """
        return blender_units * self._config.meters_per_blender_unit

    def kilometers_to_blender(self, km: float) -> float:
        """Convert kilometers to Blender units."""
        return self.meters_to_blender(km * 1000.0)

    def blender_to_kilometers(self, blender_units: float) -> float:
        """Convert Blender units to kilometers."""
        return self.blender_to_meters(blender_units) / 1000.0

    def feet_to_blender(self, feet: float) -> float:
        """Convert feet to Blender units."""
        return self.meters_to_blender(feet * 0.3048)

    def blender_to_feet(self, blender_units: float) -> float:
        """Convert Blender units to feet."""
        return self.blender_to_meters(blender_units) / 0.3048

    def scale_vector(
        self,
        x_m: float,
        y_m: float,
        z_m: float
    ) -> tuple:
        """
        Scale a 3D vector from meters to Blender units.

        Args:
            x_m, y_m, z_m: Coordinates in meters

        Returns:
            Tuple of (x, y, z) in Blender units
        """
        scale = 1.0 / self._config.meters_per_blender_unit
        return (x_m * scale, y_m * scale, z_m * scale)

    def get_blender_unit_settings(self) -> Dict[str, any]:
        """
        Get recommended Blender unit settings for current scale.

        Returns:
            Dictionary with unit settings
        """
        if self._preset == ScalePreset.REALISTIC:
            return {
                "system": "METRIC",
                "scale_length": 1.0,
                "length_unit": "METERS",
            }
        elif self._preset == ScalePreset.HALF:
            return {
                "system": "METRIC",
                "scale_length": 0.5,
                "length_unit": "METERS",
            }
        elif self._preset == ScalePreset.DOUBLE:
            return {
                "system": "METRIC",
                "scale_length": 2.0,
                "length_unit": "METERS",
            }
        elif self._preset == ScalePreset.DECIMETER:
            return {
                "system": "METRIC",
                "scale_length": 0.1,
                "length_unit": "CENTIMETERS",
            }
        elif self._preset == ScalePreset.CENTIMETER:
            return {
                "system": "METRIC",
                "scale_length": 0.01,
                "length_unit": "CENTIMETERS",
            }
        elif self._preset == ScalePreset.KILOMETER:
            return {
                "system": "METRIC",
                "scale_length": 1000.0,
                "length_unit": "KILOMETERS",
            }
        return {
            "system": "METRIC",
            "scale_length": 1.0,
            "length_unit": "METERS",
        }


# Common road widths in meters (for reference)
ROAD_WIDTHS_METERS = {
    "motorway_lane": 3.75,
    "highway_lane": 3.5,
    "urban_lane": 3.0,
    "residential_lane": 2.75,
    "shoulder": 1.5,
    "sidewalk": 1.5,
    "bike_lane": 1.2,
    "parking_lane": 2.5,
}

# Common building heights in meters
BUILDING_HEIGHTS_METERS = {
    "single_story": 3.5,
    "two_story": 7.0,
    "three_story": 10.5,
    "floor_height": 3.5,  # Average floor-to-floor
    "office_floor": 4.0,
    "residential_floor": 3.0,
}

# Charlotte landmark heights
CHARLOTTE_BUILDING_HEIGHTS = {
    "bank_of_america_corporate_center": 312.0,
    "duke_energy_center": 240.0,
    "wells_fargo_capital_center": 176.0,
    "truist_center": 150.0,
    "the_vue": 158.0,
    "one_wells_fargo_center": 150.0,
    "bank_of_america_stadium": 60.0,
    "spectrum_center": 40.0,
}


__all__ = [
    "ScalePreset",
    "ScaleConfig",
    "ScaleManager",
    "ROAD_WIDTHS_METERS",
    "BUILDING_HEIGHTS_METERS",
    "CHARLOTTE_BUILDING_HEIGHTS",
]
