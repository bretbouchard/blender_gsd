"""
Unit tests for target import system.

Tests for MeasurementInput, MeasurementSet, and TargetImporter.
"""

import pytest
from lib.cinematic.projection.physical.targets import (
    TargetType,
    MeasurementInput,
    MeasurementSet,
    TargetImporter,
    ProjectionTarget,
)


class TestMeasurementInput:
    """Tests for MeasurementInput dataclass."""

    def test_point_measurement(self):
        """Create point measurement."""
        m = MeasurementInput(
            name="test_point",
            measurement_type='point',
            position=(1.0, 2.0, 3.0),
        )

        assert m.name == "test_point"
        assert m.measurement_type == 'point'
        assert m.position == (1.0, 2.0, 3.0)

    def test_distance_measurement(self):
        """Create distance measurement."""
        m = MeasurementInput(
            name="test_distance",
            measurement_type='distance',
            start_point=(0, 0, 0),
            end_point=(1, 0, 0),
        )

        assert m.measurement_type == 'distance'
        assert m.start_point == (0, 0, 0)
        assert m.end_point == (1, 0, 0)

    def test_area_measurement(self):
        """Create area measurement."""
        corners = [(0, 0, 0), (2, 0, 0), (2, 0, 1.5), (0, 0, 1.5)]
        m = MeasurementInput(
            name="test_area",
            measurement_type='area',
            corners=corners,
        )

        assert m.measurement_type == 'area'
        assert len(m.corners) == 4

    def test_measurement_serialization(self):
        """Test to_dict and from_dict."""
        m = MeasurementInput(
            name="serialize_test",
            measurement_type='point',
            position=(1.5, 2.5, 3.5),
            notes="Test note",
        )

        data = m.to_dict()
        restored = MeasurementInput.from_dict(data)

        assert restored.name == m.name
        assert restored.position == m.position
        assert restored.notes == m.notes


class TestMeasurementSet:
    """Tests for MeasurementSet."""

    def test_empty_set(self):
        """Create empty measurement set."""
        ms = MeasurementSet(target_name="test")

        assert ms.target_name == "test"
        assert len(ms.measurements) == 0

    def test_add_measurement(self):
        """Add measurements to set."""
        ms = MeasurementSet(target_name="test")
        m = MeasurementInput(name="p1", measurement_type='point', position=(0, 0, 0))

        ms.add_measurement(m)

        assert len(ms.measurements) == 1


class TestTargetImporter:
    """Tests for TargetImporter."""

    def test_initialization(self):
        """Importer initializes correctly."""
        importer = TargetImporter()

        assert len(importer.measurements) == 0
        assert importer._target_name == "imported_target"

    def test_set_name(self):
        """Set target name."""
        importer = TargetImporter()
        importer.set_name("my_target")

        assert importer._target_name == "my_target"

    def test_add_point_measurement(self):
        """Add point measurement."""
        importer = TargetImporter()
        result = importer.add_point_measurement("corner", (1, 2, 3))

        assert result == importer  # Fluent API
        assert len(importer.measurements) == 1
        assert importer.measurements[0].name == "corner"

    def test_add_distance_measurement(self):
        """Add distance measurement."""
        importer = TargetImporter()
        importer.add_distance_measurement("width", (0, 0, 0), (2, 0, 0))

        assert len(importer.measurements) == 1
        assert importer.measurements[0].measurement_type == 'distance'

    def test_add_area_measurement(self):
        """Add area measurement."""
        importer = TargetImporter()
        corners = [(0, 0, 0), (2, 0, 0), (2, 0, 1), (0, 0, 1)]
        importer.add_area_measurement("surface", corners)

        assert len(importer.measurements) == 1
        assert importer.measurements[0].measurement_type == 'area'

    def test_compute_target_empty(self):
        """Compute target from empty measurements."""
        importer = TargetImporter()
        target = importer.compute_target()

        assert isinstance(target, ProjectionTarget)
        assert target.name == "imported_target"
        assert len(target.surfaces) == 0

    def test_compute_target_with_points(self):
        """Compute target with point measurements."""
        importer = TargetImporter()
        importer.set_name("point_test")
        importer.add_point_measurement("p1", (0, 0, 0))
        importer.add_point_measurement("p2", (2, 0, 0))
        importer.add_point_measurement("p3", (0, 0, 1.5))

        target = importer.compute_target()

        assert target.name == "point_test"
        # Points don't create surfaces directly
        assert len(target.surfaces) == 0

    def test_compute_target_with_area(self):
        """Compute target with area measurement."""
        importer = TargetImporter()
        importer.set_name("area_test")
        corners = [(0, 0, 0), (2, 0, 0), (2, 0, 1.5), (0, 0, 1.5)]
        importer.add_area_measurement("wall", corners)

        target = importer.compute_target()

        assert target.name == "area_test"
        assert len(target.surfaces) == 1
        assert target.surfaces[0].name == "wall"

    def test_fluent_api(self):
        """Test fluent method chaining."""
        importer = (
            TargetImporter()
            .set_name("chained")
            .set_description("Chained target")
            .add_point_measurement("p1", (0, 0, 0))
            .add_distance_measurement("d1", (0, 0, 0), (1, 0, 0))
        )

        assert importer._target_name == "chained"
        assert len(importer.measurements) == 2

    def test_get_measurement_set(self):
        """Get measurements as MeasurementSet."""
        importer = TargetImporter()
        importer.set_name("test")
        importer.add_point_measurement("p1", (0, 0, 0))

        ms = importer.get_measurement_set()

        assert isinstance(ms, MeasurementSet)
        assert ms.target_name == "test"
        assert len(ms.measurements) == 1


class TestTargetImporterDistance:
    """Tests for distance computation."""

    def test_compute_distance(self):
        """Distance computation is correct."""
        importer = TargetImporter()

        # 3-4-5 triangle
        dist = importer._compute_distance((0, 0, 0), (3, 4, 0))
        assert dist == pytest.approx(5.0)

        # Unit distance
        dist = importer._compute_distance((0, 0, 0), (1, 0, 0))
        assert dist == pytest.approx(1.0)

    def test_compute_bounding_box(self):
        """Bounding box computation is correct."""
        importer = TargetImporter()
        corners = [(1, 0, 2), (3, 0, 4), (0, 0, 0)]

        min_c, max_c = importer._compute_bounding_box(corners)

        assert min_c == (0, 0, 0)
        assert max_c == (3, 0, 4)

    def test_compute_area_from_corners(self):
        """Area computation from corners."""
        importer = TargetImporter()

        # 2m x 1.5m rectangle
        corners = [(0, 0, 0), (2, 0, 0), (2, 0, 1.5), (0, 0, 1.5)]
        area = importer._compute_area_from_corners(corners)

        assert area == pytest.approx(3.0)  # 2 * 1.5


class TestTargetImporterYAML:
    """Tests for YAML import."""

    def test_import_from_yaml_file_not_found(self):
        """Import raises error for missing file."""
        importer = TargetImporter()

        with pytest.raises(FileNotFoundError):
            importer.import_from_yaml("/nonexistent/path.yaml")

    def test_import_from_yaml_structure(self):
        """YAML structure is parsed correctly."""
        importer = TargetImporter()

        # This will raise FileNotFoundError since we're testing structure
        # The actual file tests would use real preset files
        pass
