"""
Measurement import system for projection targets.

Provides tools for importing real-world measurements and converting them
into ProjectionTarget configurations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import math

from .types import (
    ProjectionTarget,
    ProjectionSurface,
    TargetType,
    SurfaceMaterial,
)


@dataclass
class MeasurementInput:
    """
    Real-world measurement input for target creation.

    Supports point, distance, and area measurements.

    Attributes:
        name: Measurement identifier
        measurement_type: 'point', 'distance', or 'area'
        position: 3D position for point measurements
        start_point: Start position for distance measurements
        end_point: End position for distance measurements
        distance_m: Measured distance in meters
        corners: Corner points for area measurements
        area_m2: Measured area in square meters
        notes: Additional notes about the measurement
    """
    name: str
    measurement_type: str  # 'point', 'distance', 'area'

    # For points (3D position)
    position: Optional[Tuple[float, float, float]] = None

    # For distances
    start_point: Optional[Tuple[float, float, float]] = None
    end_point: Optional[Tuple[float, float, float]] = None
    distance_m: Optional[float] = None

    # For areas
    corners: Optional[List[Tuple[float, float, float]]] = None
    area_m2: Optional[float] = None

    # Metadata
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            'name': self.name,
            'type': self.measurement_type,
            'notes': self.notes,
        }

        if self.measurement_type == 'point':
            data['position'] = list(self.position) if self.position else None
        elif self.measurement_type == 'distance':
            data['start'] = list(self.start_point) if self.start_point else None
            data['end'] = list(self.end_point) if self.end_point else None
            data['distance_m'] = self.distance_m
        elif self.measurement_type == 'area':
            data['corners'] = [list(c) for c in self.corners] if self.corners else None
            data['area_m2'] = self.area_m2

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeasurementInput':
        """Create from dictionary."""
        m_type = data.get('type', 'point')

        return cls(
            name=data['name'],
            measurement_type=m_type,
            position=tuple(data['position']) if data.get('position') else None,
            start_point=tuple(data['start']) if data.get('start') else None,
            end_point=tuple(data['end']) if data.get('end') else None,
            distance_m=data.get('distance_m'),
            corners=[tuple(c) for c in data['corners']] if data.get('corners') else None,
            area_m2=data.get('area_m2'),
            notes=data.get('notes', ''),
        )


@dataclass
class MeasurementSet:
    """
    Collection of measurements defining a target.

    Attributes:
        target_name: Name for the resulting target
        measurements: List of measurement inputs
        computed_positions: Dict of computed point positions
        computed_dimensions: Dict of computed dimensions
    """
    target_name: str
    measurements: List[MeasurementInput] = field(default_factory=list)

    # Computed values
    computed_positions: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)
    computed_dimensions: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)

    def add_measurement(self, measurement: MeasurementInput) -> 'MeasurementSet':
        """Add a measurement to the set."""
        self.measurements.append(measurement)
        return self


class TargetImporter:
    """
    Import target geometry from real-world measurements.

    Provides fluent API for building targets from measurements.

    Example:
        >>> importer = TargetImporter()
        >>> importer.add_point_measurement("bottom_left", (0, 0, 0))
        >>> importer.add_point_measurement("bottom_right", (2, 0, 0))
        >>> importer.add_point_measurement("top_left", (0, 0, 1.5))
        >>> target = importer.compute_target()
    """

    def __init__(self):
        self.measurements: List[MeasurementInput] = []
        self._target_name: str = "imported_target"
        self._description: str = ""
        self._target_type: TargetType = TargetType.PLANAR

    def set_name(self, name: str) -> 'TargetImporter':
        """Set target name."""
        self._target_name = name
        return self

    def set_description(self, description: str) -> 'TargetImporter':
        """Set target description."""
        self._description = description
        return self

    def set_target_type(self, target_type: TargetType) -> 'TargetImporter':
        """Set target type."""
        self._target_type = target_type
        return self

    def add_point_measurement(
        self,
        name: str,
        position: Tuple[float, float, float],
        notes: str = ""
    ) -> 'TargetImporter':
        """Add a 3D point measurement."""
        self.measurements.append(MeasurementInput(
            name=name,
            measurement_type='point',
            position=position,
            notes=notes
        ))
        return self

    def add_distance_measurement(
        self,
        name: str,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        notes: str = ""
    ) -> 'TargetImporter':
        """Add a distance measurement."""
        self.measurements.append(MeasurementInput(
            name=name,
            measurement_type='distance',
            start_point=start,
            end_point=end,
            notes=notes
        ))
        return self

    def add_area_measurement(
        self,
        name: str,
        corners: List[Tuple[float, float, float]],
        notes: str = ""
    ) -> 'TargetImporter':
        """Add an area measurement from corner points."""
        self.measurements.append(MeasurementInput(
            name=name,
            measurement_type='area',
            corners=corners,
            notes=notes
        ))
        return self

    def _compute_distance(self, start: Tuple, end: Tuple) -> float:
        """Compute Euclidean distance between two points."""
        return math.sqrt(
            (end[0] - start[0])**2 +
            (end[1] - start[1])**2 +
            (end[2] - start[2])**2
        )

    def _compute_bounding_box(
        self,
        corners: List[Tuple[float, float, float]]
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Compute bounding box from corner points."""
        min_corner = (
            min(c[0] for c in corners),
            min(c[1] for c in corners),
            min(c[2] for c in corners)
        )
        max_corner = (
            max(c[0] for c in corners),
            max(c[1] for c in corners),
            max(c[2] for c in corners)
        )
        return min_corner, max_corner

    def _compute_area_from_corners(
        self,
        corners: List[Tuple[float, float, float]]
    ) -> float:
        """Compute approximate area from corner points (assuming planar quad)."""
        if len(corners) < 3:
            return 0.0

        # For a quad, compute width and height from bounding box
        min_c, max_c = self._compute_bounding_box(corners)
        width = max_c[0] - min_c[0]
        height = max_c[2] - min_c[2]  # Using Z as height

        return width * height

    def compute_target(self) -> ProjectionTarget:
        """
        Compute ProjectionTarget from measurements.

        Returns:
            ProjectionTarget configured from the measurements
        """
        # Process measurements
        points: Dict[str, Tuple[float, float, float]] = {}
        dimensions: Dict[str, float] = {}
        surfaces: List[ProjectionSurface] = []

        for m in self.measurements:
            if m.measurement_type == 'point':
                points[m.name] = m.position

            elif m.measurement_type == 'distance':
                if m.start_point and m.end_point:
                    dist = self._compute_distance(m.start_point, m.end_point)
                    dimensions[m.name] = dist

            elif m.measurement_type == 'area':
                if m.corners:
                    # Compute surface from area measurement
                    min_c, max_c = self._compute_bounding_box(m.corners)
                    center = (
                        (min_c[0] + max_c[0]) / 2,
                        (min_c[1] + max_c[1]) / 2,
                        (min_c[2] + max_c[2]) / 2
                    )
                    width = max_c[0] - min_c[0]
                    height = max_c[2] - min_c[2]
                    area = m.area_m2 or self._compute_area_from_corners(m.corners)

                    surface = ProjectionSurface(
                        name=m.name,
                        surface_type=TargetType.PLANAR,
                        position=center,
                        dimensions=(width, height),
                        area_m2=area,
                        calibration_points=m.corners[:3] if len(m.corners) >= 3 else [],
                    )
                    surfaces.append(surface)

        # Determine overall dimensions
        if surfaces:
            all_corners = []
            for s in surfaces:
                x, y, z = s.position
                w, h = s.dimensions
                all_corners.extend([
                    (x - w/2, y, z - h/2),
                    (x + w/2, y, z + h/2),
                ])

            if all_corners:
                min_c, max_c = self._compute_bounding_box(all_corners)
                total_width = max_c[0] - min_c[0]
                total_height = max_c[2] - min_c[2]
            else:
                total_width = 1.0
                total_height = 1.0
        else:
            total_width = 1.0
            total_height = 1.0

        # Determine recommended calibration
        if len(surfaces) > 1:
            recommended = "four_point_dlt"
        else:
            recommended = "three_point"

        return ProjectionTarget(
            name=self._target_name,
            description=self._description,
            target_type=self._target_type,
            surfaces=surfaces,
            width_m=total_width,
            height_m=total_height,
            recommended_calibration=recommended,
        )

    def import_from_yaml(self, yaml_path: str) -> ProjectionTarget:
        """
        Import target from YAML measurements file.

        Args:
            yaml_path: Path to YAML file containing measurements

        Returns:
            ProjectionTarget configured from YAML data
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML required for YAML import: pip install pyyaml")

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Set target metadata
        self._target_name = data.get('target_name', data.get('name', 'imported_target'))
        self._description = data.get('description', '')
        self._target_type = TargetType(data.get('target_type', 'planar'))

        # Clear existing measurements
        self.measurements = []

        # Process measurements section
        for measurement in data.get('measurements', []):
            m_type = measurement.get('type')

            if m_type == 'point':
                self.add_point_measurement(
                    name=measurement['name'],
                    position=tuple(measurement['position']),
                    notes=measurement.get('notes', '')
                )
            elif m_type == 'distance':
                self.add_distance_measurement(
                    name=measurement['name'],
                    start=tuple(measurement['start']),
                    end=tuple(measurement['end']),
                    notes=measurement.get('notes', '')
                )
            elif m_type == 'area':
                self.add_area_measurement(
                    name=measurement['name'],
                    corners=[tuple(c) for c in measurement['corners']],
                    notes=measurement.get('notes', '')
                )

        # If target has surfaces defined directly, process those
        if 'surfaces' in data and not data.get('measurements'):
            # This is a target config file, not a measurements file
            # Use ProjectionTarget.from_dict instead
            return ProjectionTarget.from_dict(data)

        return self.compute_target()

    def get_measurement_set(self) -> MeasurementSet:
        """Get current measurements as a MeasurementSet."""
        return MeasurementSet(
            target_name=self._target_name,
            measurements=self.measurements.copy(),
        )
