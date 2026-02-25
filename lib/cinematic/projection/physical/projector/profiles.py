"""Projector hardware profile types for physical projection mapping.

This module provides dataclasses for representing physical projector
hardware specifications, including optical characteristics, lens shift,
and keystone correction capabilities.

Key Formula (Geometry Rick verified):
    focal_length = sensor_width * throw_ratio

NOT: focal_length = (throw_ratio * sensor_width) / 2

Part of Milestone v0.15 - Physical Projector Mapping System
"""

from dataclasses import dataclass, field
from typing import Tuple, Optional
from enum import Enum


class ProjectorType(Enum):
    """Projector technology type."""
    DLP = "dlp"
    LCD = "lcd"
    LCOS = "lcos"
    LASER = "laser"


class AspectRatio(Enum):
    """Common projector aspect ratios.

    The value tuple stores (width, height) ratio components.
    Use the ratio property to get the float value.
    """
    RATIO_16_9 = (16, 9)
    RATIO_4_3 = (4, 3)
    RATIO_16_10 = (16, 10)
    RATIO_17_9 = (17, 9)
    RATIO_21_9 = (21, 9)

    @property
    def ratio(self) -> float:
        """Get the aspect ratio as a float (width / height)."""
        return self._value_[0] / self._value_[1]


@dataclass
class LensShift:
    """Lens shift capabilities.

    Lens shift allows the projected image to be moved without
    physically moving the projector, which is critical for
    proper projection alignment.

    Attributes:
        vertical: Current vertical shift as fraction (e.g., 0.15 = 15% up)
        horizontal: Current horizontal shift as fraction (e.g., 0.05 = 5% right)
        vertical_range: Min and max vertical shift available
        horizontal_range: Min and max horizontal shift available
    """
    vertical: float = 0.0    # Fraction (e.g., 0.15 = 15% up)
    horizontal: float = 0.0  # Fraction (e.g., 0.05 = 5% right)
    vertical_range: Tuple[float, float] = (0.0, 0.0)   # (min, max) shift
    horizontal_range: Tuple[float, float] = (0.0, 0.0)  # (min, max) shift


@dataclass
class KeystoneCorrection:
    """Keystone correction capabilities.

    Keystone correction compensates for the trapezoidal distortion
    that occurs when a projector is not perpendicular to the screen.

    Attributes:
        horizontal: Horizontal keystone correction in degrees
        vertical: Vertical keystone correction in degrees
        automatic: Whether auto-keystone feature is available
        corner_correction: Whether 4-corner correction is supported
    """
    horizontal: float = 0.0  # Degrees
    vertical: float = 0.0    # Degrees
    automatic: bool = False   # Has auto-keystone feature
    corner_correction: bool = False  # 4-corner correction support


@dataclass
class ProjectorProfile:
    """Physical projector hardware specifications.

    This dataclass stores all the optical and output characteristics
    of a physical projector for use in Blender projection mapping.

    Key Formula (Geometry Rick verified):
        focal_length = sensor_width * throw_ratio

    NOT: focal_length = (throw_ratio * sensor_width) / 2

    Attributes:
        name: Unique identifier (e.g., "Epson_Home_Cinema_2150")
        manufacturer: Manufacturer name (e.g., "Epson")
        model: Display model name (e.g., "Home Cinema 2150")
        projector_type: Technology type (DLP, LCD, LCOS, LASER)
        native_resolution: Output resolution as (width, height)
        aspect_ratio: Native aspect ratio
        max_refresh_rate: Maximum refresh rate in Hz
        throw_ratio: Distance / width ratio (horizontal)
        throw_ratio_range: Min and max throw ratio for zoom lenses
        has_zoom: Whether the lens has optical zoom
        lens_shift: Lens shift capabilities
        keystone: Keystone correction capabilities
        brightness_lumens: Light output in ANSI lumens
        contrast_ratio: Contrast ratio (e.g., 70000:1 stored as 70000)
        color_gamut: Color space (Rec.709, DCI-P3, Rec.2020)
        sensor_width: Sensor/display width in mm for Blender camera
        sensor_height: Sensor/display height in mm for Blender camera
        calibration_date: ISO date string of last calibration
        calibration_notes: Free-form calibration notes
    """
    # Identity
    name: str                           # "Epson_Home_Cinema_2150"
    manufacturer: str                   # "Epson"
    model: str = ""                     # "Home Cinema 2150"
    projector_type: ProjectorType = ProjectorType.DLP

    # Output specifications
    native_resolution: Tuple[int, int] = (1920, 1080)
    aspect_ratio: AspectRatio = AspectRatio.RATIO_16_9
    max_refresh_rate: int = 60  # Hz

    # Optical characteristics
    throw_ratio: float = 1.32              # distance / width (horizontal)
    throw_ratio_range: Tuple[float, float] = (1.32, 1.32)  # (min, max) for zoom lenses
    has_zoom: bool = False                 # True if throw_ratio_range differs

    # Lens shift (Geometry Rick: critical for proper projection alignment)
    lens_shift: LensShift = field(default_factory=LensShift)

    # Keystone correction
    keystone: KeystoneCorrection = field(default_factory=KeystoneCorrection)

    # Brightness and contrast
    brightness_lumens: int = 2500
    contrast_ratio: int = 70000
    color_gamut: str = "Rec.709"  # Rec.709, DCI-P3, Rec.2020

    # Sensor specifications (for Blender camera conversion)
    sensor_width: float = 36.0   # mm (full frame equivalent)
    sensor_height: float = 20.25  # mm (16:9 aspect)

    # Calibration metadata
    calibration_date: Optional[str] = None
    calibration_notes: str = ""

    def __post_init__(self):
        """Validate and auto-set derived values."""
        # Auto-detect zoom capability
        if self.throw_ratio_range[0] != self.throw_ratio_range[1]:
            self.has_zoom = True

    def get_blender_focal_length(self, aspect: str = 'horizontal') -> float:
        """Convert throw ratio to Blender focal length.

        CORRECTED FORMULA (Geometry Rick):
            focal_length = sensor_width * throw_ratio

        The original formula had an incorrect division by 2.

        Args:
            aspect: 'horizontal', 'vertical', or 'diagonal'

        Returns:
            Focal length in mm for Blender camera
        """
        from .calibration import throw_ratio_to_focal_length
        return throw_ratio_to_focal_length(
            self.throw_ratio,
            self.sensor_width,
            self.sensor_height,
            aspect
        )

    def get_blender_shift_x(self) -> float:
        """Get Blender camera shift X from lens shift.

        Blender shift is normalized (-0.5 to 0.5).
        Lens shift is fraction (0.15 = 15%).

        Returns:
            Horizontal shift value for Blender camera
        """
        return self.lens_shift.horizontal

    def get_blender_shift_y(self) -> float:
        """Get Blender camera shift Y from lens shift.

        Blender shift is normalized (-0.5 to 0.5).
        Lens shift is fraction (0.15 = 15%).

        Returns:
            Vertical shift value for Blender camera
        """
        return self.lens_shift.vertical

    def get_throw_distance(self, image_width: float) -> float:
        """Calculate throw distance for desired image width.

        Args:
            image_width: Desired image width in meters

        Returns:
            Required throw distance in meters
        """
        from .calibration import calculate_throw_distance
        return calculate_throw_distance(self.throw_ratio, image_width)

    def get_image_width(self, throw_distance: float) -> float:
        """Calculate image width at given throw distance.

        Args:
            throw_distance: Distance from projector to surface in meters

        Returns:
            Image width in meters
        """
        from .calibration import calculate_image_width
        return calculate_image_width(self.throw_ratio, throw_distance)
