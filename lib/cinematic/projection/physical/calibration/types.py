"""
Surface calibration types for physical projector mapping.

Provides data structures for calibration points, surface calibration,
and calibration pattern configuration.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import math


class CalibrationType(Enum):
    """Type of calibration alignment."""
    THREE_POINT = "three_point"        # Planar surfaces (3 points)
    FOUR_POINT_DLT = "four_point_dlt"  # Non-planar/multi-surface (4+ points)


class PatternType(Enum):
    """Type of calibration pattern."""
    CHECKERBOARD = "checkerboard"
    COLOR_BARS = "color_bars"
    GRID = "grid"
    CROSSHAIR = "crosshair"
    GRADIENT = "gradient"


@dataclass
class CalibrationPoint:
    """
    Single calibration point with real-world and projector coordinates.

    Attributes:
        world_position: 3D position in scene (meters)
        projector_uv: 2D position in projector space (0-1 range)
        label: Human-readable label (e.g., "Bottom Left")
    """
    world_position: Tuple[float, float, float]
    projector_uv: Tuple[float, float]
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'world_position': list(self.world_position),
            'projector_uv': list(self.projector_uv),
            'label': self.label,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalibrationPoint':
        """Create from dictionary."""
        return cls(
            world_position=tuple(data['world_position']),
            projector_uv=tuple(data['projector_uv']),
            label=data.get('label', ''),
        )


@dataclass
class SurfaceCalibration:
    """
    Calibration data for a projection surface.

    Stores calibration points, computed transform, and metadata.
    Supports both 3-point (planar) and 4-point DLT (non-planar) calibration.
    """
    name: str
    calibration_type: CalibrationType
    points: List[CalibrationPoint] = field(default_factory=list)

    # Computed transform (set after alignment)
    transform_matrix: Optional[List[List[float]]] = None  # 4x4 matrix as list of lists
    calibration_error: float = 0.0  # RMS error in meters
    is_calibrated: bool = False

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

    def add_point(
        self,
        world_position: Tuple[float, float, float],
        projector_uv: Tuple[float, float],
        label: str = ""
    ) -> 'CalibrationPoint':
        """Add a calibration point."""
        point = CalibrationPoint(world_position, projector_uv, label)
        self.points.append(point)
        self.last_modified = datetime.now()
        return point

    def clear_calibration(self):
        """Clear computed calibration data."""
        self.transform_matrix = None
        self.calibration_error = 0.0
        self.is_calibrated = False
        self.last_modified = datetime.now()

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate calibration data.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Check point count
        if self.calibration_type == CalibrationType.THREE_POINT:
            if len(self.points) != 3:
                errors.append(f"3-point calibration requires exactly 3 points, got {len(self.points)}")
        elif self.calibration_type == CalibrationType.FOUR_POINT_DLT:
            if len(self.points) < 4:
                errors.append(f"4-point DLT requires at least 4 points, got {len(self.points)}")

        # Check for duplicate points
        world_positions = [p.world_position for p in self.points]
        if len(set(world_positions)) != len(world_positions):
            errors.append("Duplicate world positions detected")

        projector_uvs = [p.projector_uv for p in self.points]
        if len(set(projector_uvs)) != len(projector_uvs):
            errors.append("Duplicate projector UV coordinates detected")

        # Check UV bounds
        for i, point in enumerate(self.points):
            u, v = point.projector_uv
            if not (0 <= u <= 1 and 0 <= v <= 1):
                errors.append(f"Point {i} projector UV ({u}, {v}) out of bounds [0, 1]")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'calibration_type': self.calibration_type.value,
            'points': [p.to_dict() for p in self.points],
            'transform_matrix': self.transform_matrix,
            'calibration_error': self.calibration_error,
            'is_calibrated': self.is_calibrated,
            'created_at': self.created_at.isoformat(),
            'last_modified': self.last_modified.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SurfaceCalibration':
        """Create from dictionary."""
        calibration = cls(
            name=data['name'],
            calibration_type=CalibrationType(data['calibration_type']),
            points=[CalibrationPoint.from_dict(p) for p in data.get('points', [])],
            transform_matrix=data.get('transform_matrix'),
            calibration_error=data.get('calibration_error', 0.0),
            is_calibrated=data.get('is_calibrated', False),
        )
        if 'created_at' in data:
            calibration.created_at = datetime.fromisoformat(data['created_at'])
        if 'last_modified' in data:
            calibration.last_modified = datetime.fromisoformat(data['last_modified'])
        return calibration


@dataclass
class CalibrationPattern:
    """
    Configuration for calibration pattern generation.

    Used to create test patterns for physical projector alignment.
    """
    name: str
    pattern_type: PatternType
    resolution: Tuple[int, int]  # (width, height)

    # Pattern-specific settings
    grid_size: int = 8            # For checkerboard: squares per row/column
    spacing: int = 100            # For grid: pixel spacing
    line_width: int = 2           # For grid/crosshair: line width in pixels
    color_depth: int = 8          # Bits per channel (8, 10, 12)

    # Color settings
    primary_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)    # White
    secondary_color: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Black

    # Color bars specific
    smpte_standard: bool = True   # SMPTE vs ARIB color bars

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'pattern_type': self.pattern_type.value,
            'resolution': list(self.resolution),
            'grid_size': self.grid_size,
            'spacing': self.spacing,
            'line_width': self.line_width,
            'color_depth': self.color_depth,
            'primary_color': list(self.primary_color),
            'secondary_color': list(self.secondary_color),
            'smpte_standard': self.smpte_standard,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalibrationPattern':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            pattern_type=PatternType(data['pattern_type']),
            resolution=tuple(data['resolution']),
            grid_size=data.get('grid_size', 8),
            spacing=data.get('spacing', 100),
            line_width=data.get('line_width', 2),
            color_depth=data.get('color_depth', 8),
            primary_color=tuple(data.get('primary_color', (1.0, 1.0, 1.0))),
            secondary_color=tuple(data.get('secondary_color', (0.0, 0.0, 0.0))),
            smpte_standard=data.get('smpte_standard', True),
        )


# Preset patterns
CHECKERBOARD_STANDARD = CalibrationPattern(
    name="checkerboard_standard",
    pattern_type=PatternType.CHECKERBOARD,
    resolution=(1920, 1080),
    grid_size=8,
)

CHECKERBOARD_FINE = CalibrationPattern(
    name="checkerboard_fine",
    pattern_type=PatternType.CHECKERBOARD,
    resolution=(1920, 1080),
    grid_size=16,
)

COLOR_BARS_SMpte = CalibrationPattern(
    name="color_bars_smpte",
    pattern_type=PatternType.COLOR_BARS,
    resolution=(1920, 1080),
    smpte_standard=True,
)

GRID_100PX = CalibrationPattern(
    name="grid_100px",
    pattern_type=PatternType.GRID,
    resolution=(1920, 1080),
    spacing=100,
    line_width=2,
)

GRADIENT_HORIZONTAL = CalibrationPattern(
    name="gradient_horizontal",
    pattern_type=PatternType.GRADIENT,
    resolution=(1920, 1080),
)
