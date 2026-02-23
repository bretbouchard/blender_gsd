"""
Shared pytest fixtures for Blender GSD unit tests.

These fixtures provide mock objects and test utilities that work
without Blender (bpy) installed.
"""

import sys
from unittest.mock import MagicMock

# Mock Blender modules BEFORE any other imports
# This must be done at module level to work for all test files
mock_bpy = MagicMock()


class CallableProperty:
    """Descriptor that allows a property to be called like a method.

    This is needed because this project has some code using .length (property)
    and some code using .length() (method). The real mathutils.Vector uses
    .length as a property.
    """
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # Return a callable that returns the value
        # This allows both vec.length and vec.length() to work
        value = self.getter(obj)

        class CallableValue(float):
            """A float that can be called."""
            def __new__(cls, val):
                return float.__new__(cls, val)

            def __call__(self):
                return float(self)

        return CallableValue(value)


mock_bpy = MagicMock()
mock_bpy.ops = MagicMock()
mock_bpy.data = MagicMock()
mock_bpy.context = MagicMock()
mock_bpy.app = MagicMock()
mock_bpy.app.version = (4, 0, 0)
mock_bpy.data.cameras = MagicMock()
mock_bpy.data.objects = MagicMock()
mock_bpy.data.images = MagicMock()
mock_bpy.data.materials = MagicMock()
mock_bpy.data.meshes = MagicMock()
mock_bpy.context.scene = MagicMock()
mock_bpy.context.collection = MagicMock()

sys.modules['bpy'] = mock_bpy
sys.modules['bmesh'] = MagicMock()

# Mock mathutils
class MockVector:
    """Mock Vector class that mimics mathutils.Vector for testing outside Blender."""
    def __init__(self, values):
        if isinstance(values, MockVector):
            self.values = list(values.values)
        else:
            self.values = list(values)

    def __getitem__(self, index):
        return self.values[index]

    def __setitem__(self, index, value):
        self.values[index] = value

    def __len__(self):
        return len(self.values)

    @property
    def x(self):
        return self.values[0] if len(self.values) > 0 else 0.0

    @x.setter
    def x(self, value):
        if len(self.values) > 0:
            self.values[0] = value

    @property
    def y(self):
        return self.values[1] if len(self.values) > 1 else 0.0

    @y.setter
    def y(self, value):
        if len(self.values) > 1:
            self.values[1] = value

    @property
    def z(self):
        return self.values[2] if len(self.values) > 2 else 0.0

    @z.setter
    def z(self, value):
        if len(self.values) > 2:
            self.values[2] = value

    def normalized(self):
        length = sum(v * v for v in self.values) ** 0.5
        if length == 0:
            return MockVector(self.values)
        return MockVector([v / length for v in self.values])

    def normalize(self):
        """In-place normalization. Returns self for chaining."""
        length = sum(v * v for v in self.values) ** 0.5
        if length > 0:
            self.values = [v / length for v in self.values]
        return self

    def __add__(self, other):
        if isinstance(other, MockVector):
            return MockVector([a + b for a, b in zip(self.values, other.values)])
        return MockVector([a + other for a in self.values])

    def __sub__(self, other):
        if isinstance(other, MockVector):
            return MockVector([a - b for a, b in zip(self.values, other.values)])
        return MockVector([a - other for a in self.values])

    def __mul__(self, other):
        if isinstance(other, MockVector):
            return MockVector([a * b for a, b in zip(self.values, other.values)])
        return MockVector([a * other for a in self.values])

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, MockVector):
            return MockVector([a / b for a, b in zip(self.values, other.values)])
        return MockVector([a / other for a in self.values])

    def __neg__(self):
        return MockVector([-a for a in self.values])

    @CallableProperty
    def length(self):
        """Return the length of the vector.

        Note: Uses CallableProperty descriptor to support both:
        - vec.length (property access - correct mathutils API)
        - vec.length() (method call - legacy code in this project)
        """
        return sum(v * v for v in self.values) ** 0.5

    def magnitude(self):
        """Alias for length."""
        return self.length

    def to_tuple(self):
        return tuple(self.values)

    def to_4x4(self):
        return self

    def lerp(self, other, factor):
        """Linear interpolation between this vector and another."""
        if isinstance(other, MockVector):
            return MockVector([a + (b - a) * factor for a, b in zip(self.values, other.values)])
        return MockVector([a + (other - a) * factor for a in self.values])

    def cross(self, other):
        """Cross product with another vector."""
        if not isinstance(other, MockVector):
            raise TypeError("cross product requires MockVector")
        a = self.values
        b = other.values
        return MockVector([
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        ])

    def dot(self, other):
        """Dot product with another vector."""
        if isinstance(other, MockVector):
            return sum(a * b for a, b in zip(self.values, other.values))
        return sum(a * other for a in self.values)

    def copy(self):
        """Return a copy of this vector."""
        return MockVector(self.values)

    @property
    def _values(self):
        """Alias for values to match fallback Vector class in source code."""
        return self.values

class MockMatrix:
    def __init__(self, rows=None):
        self.rows = rows or [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    def to_4x4(self):
        return MockMatrix([[*self.rows[0], 0], [*self.rows[1], 0], [*self.rows[2], 0], [0, 0, 0, 1]])

mock_mathutils = MagicMock()
mock_mathutils.Vector = MockVector
mock_mathutils.Matrix = MockMatrix
sys.modules['mathutils'] = mock_mathutils

import pytest
import tempfile
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime


# =============================================================================
# MSG 1998 Fixtures
# =============================================================================

@pytest.fixture
def mock_bpy():
    """Mock bpy module for testing without Blender."""
    mock = MagicMock()
    mock.ops = MagicMock()
    mock.data = MagicMock()
    mock.context = MagicMock()
    mock.app = MagicMock()
    mock.app.version = (4, 0, 0)

    # Mock data collections
    mock.data.cameras = MagicMock()
    mock.data.objects = MagicMock()
    mock.data.images = MagicMock()
    mock.data.materials = MagicMock()
    mock.data.meshes = MagicMock()

    # Mock context
    mock.context.scene = MagicMock()
    mock.context.collection = MagicMock()
    mock.context.collection.objects = MagicMock()
    mock.context.collection.objects.link = MagicMock()

    return mock


@pytest.fixture
def mock_mathutils():
    """Mock mathutils module for testing without Blender."""
    mock = MagicMock()

    # Mock Vector class
    class MockVector:
        def __init__(self, values):
            self.values = list(values)

        def __getitem__(self, index):
            return self.values[index]

        def __len__(self):
            return len(self.values)

        def normalized(self):
            length = sum(v * v for v in self.values) ** 0.5
            if length == 0:
                return MockVector(self.values)
            return MockVector([v / length for v in self.values])

        def __add__(self, other):
            if isinstance(other, MockVector):
                return MockVector([a + b for a, b in zip(self.values, other.values)])
            return MockVector([a + other for a in self.values])

        def __sub__(self, other):
            if isinstance(other, MockVector):
                return MockVector([a - b for a, b in zip(self.values, other.values)])
            return MockVector([a - other for a in self.values])

        def __mul__(self, other):
            if isinstance(other, MockVector):
                return MockVector([a * b for a, b in zip(self.values, other.values)])
            return MockVector([a * other for a in self.values])

        def length(self):
            """Return the length of the vector (method to match mathutils API)."""
            return sum(v * v for v in self.values) ** 0.5

        def to_tuple(self):
            return tuple(self.values)

    # Mock Matrix class
    class MockMatrix:
        def __init__(self, rows=None):
            self.rows = rows or [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

        def to_4x4(self):
            return MockMatrix([
                [*self.rows[0], 0],
                [*self.rows[1], 0],
                [*self.rows[2], 0],
                [0, 0, 0, 1]
            ])

    mock.Vector = MockVector
    mock.Matrix = MockMatrix

    return mock


@pytest.fixture
def sample_fspy_file(tmp_path):
    """Create a sample fSpy file for testing."""
    fspy_path = tmp_path / "test_location.fspy"

    # fSpy files are ZIP archives with JSON data
    fspy_data = {
        "version": "1.0.0",
        "camera": {
            "focalLength": 35.0,
            "sensorWidth": 36.0,
            "rotation": {
                "x": [1.0, 0.0, 0.0],
                "y": [0.0, 1.0, 0.0],
                "z": [0.0, 0.0, 1.0]
            }
        },
        "image": {
            "width": 1920,
            "height": 1080
        }
    }

    with zipfile.ZipFile(fspy_path, 'w') as zf:
        zf.writestr('data.json', json.dumps(fspy_data))

    return fspy_path


@pytest.fixture
def sample_fspy_file_with_image(tmp_path):
    """Create a sample fSpy file with embedded image."""
    fspy_path = tmp_path / "test_with_image.fspy"

    fspy_data = {
        "version": "1.0.0",
        "camera": {
            "focalLength": 50.0,
            "sensorWidth": 36.0
        }
    }

    # Create a minimal "image" file
    image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100  # Fake PNG header

    with zipfile.ZipFile(fspy_path, 'w') as zf:
        zf.writestr('data.json', json.dumps(fspy_data))
        zf.writestr('reference.jpg', image_data)

    return fspy_path


@pytest.fixture
def invalid_fspy_file(tmp_path):
    """Create an invalid (non-ZIP) file for testing error handling."""
    fspy_path = tmp_path / "invalid.fspy"
    fspy_path.write_text("not a valid fspy file")
    return fspy_path


@pytest.fixture
def sample_handoff_data():
    """Sample FDX handoff package data."""
    return {
        "scene_id": "SC001",
        "locations": [
            {
                "location_id": "LOC001",
                "name": "Test Building",
                "address": "123 Main St, NYC",
                "coordinates": [40.7128, -74.0060],
                "period_year": 1998,
                "period_notes": "Original 1998 appearance"
            }
        ],
        "manifest": {
            "created_at": "2024-01-15T10:00:00",
            "source": "fdx_gsd",
            "version": "1.0"
        }
    }


@pytest.fixture
def sample_controlnet_config_dict():
    """Sample ControlNet configuration dict."""
    return {
        "depth_model": "control_v11f1p_sd15_depth",
        "depth_weight": 1.0,
        "normal_model": "control_v11p_sd15_normalbae",
        "normal_weight": 0.8,
        "guidance_start": 0.0,
        "guidance_end": 1.0,
        "canny_model": "control_v11p_sd15_canny",
        "canny_weight": 0.5,
        "canny_enabled": False
    }


@pytest.fixture
def sample_film_look_params():
    """Sample 1998 film look parameters."""
    return {
        "grain_intensity": 0.15,
        "grain_size": 1.0,
        "lens_distortion": 0.02,
        "chromatic_aberration": 0.003,
        "vignette_strength": 0.4,
        "color_temperature": 5500,
        "cooke_flare_intensity": 0.1,
        "cooke_breathing": 0.02
    }


# =============================================================================
# Charlotte Digital Twin Fixtures
# =============================================================================

@pytest.fixture
def charlotte_downtown_origin():
    """Charlotte downtown scene origin."""
    from lib.charlotte_digital_twin.geometry.types import SceneOrigin
    return SceneOrigin(
        lat=35.2271,
        lon=-80.8431,
        name="Charlotte Downtown",
        elevation=230.0,
        utm_zone=17,
        utm_hemisphere="N"
    )


@pytest.fixture
def sample_geometry_config(charlotte_downtown_origin):
    """Sample geometry configuration."""
    from lib.charlotte_digital_twin.geometry.types import GeometryConfig, DetailLevel
    return GeometryConfig(
        origin=charlotte_downtown_origin,
        scale=1.0,
        detail_level=DetailLevel.STANDARD,
        flatten_to_plane=True,
        z_offset=0.0,
        default_road_width=7.0,
        road_height=0.1,
        default_building_height=10.0,
        max_building_height=500.0,
        min_building_height=3.0
    )


@pytest.fixture
def sample_world_coordinates():
    """Sample world coordinates for testing."""
    from lib.charlotte_digital_twin.geometry.types import WorldCoordinate
    return [
        WorldCoordinate(x=0.0, y=0.0, z=0.0),
        WorldCoordinate(x=100.0, y=0.0, z=0.0),
        WorldCoordinate(x=100.0, y=50.0, z=0.0),
        WorldCoordinate(x=0.0, y=50.0, z=0.0),
    ]


@pytest.fixture
def sample_geo_coordinates():
    """Sample geographic coordinates for Charlotte area."""
    return [
        (35.2271, -80.8431),  # Downtown
        (35.2280, -80.8420),  # Near downtown
        (35.2260, -80.8440),  # South of downtown
        (35.2275, -80.8450),  # West of downtown
    ]


@pytest.fixture
def sample_road_segment():
    """Sample road segment for testing."""
    from lib.charlotte_digital_twin.geometry.types import (
        RoadSegment, RoadType, WorldCoordinate
    )
    return RoadSegment(
        osm_id=12345,
        name="Test Highway",
        road_type=RoadType.MOTORWAY,
        coordinates=[
            WorldCoordinate(x=0.0, y=0.0, z=0.0),
            WorldCoordinate(x=100.0, y=0.0, z=0.0),
            WorldCoordinate(x=200.0, y=10.0, z=0.0),
        ],
        width=25.0,
        lanes=4,
        surface="asphalt",
        is_bridge=False,
        is_tunnel=False,
        is_oneway=False,
        tags={"maxspeed": "65 mph"}
    )


@pytest.fixture
def sample_building_footprint():
    """Sample building footprint for testing."""
    from lib.charlotte_digital_twin.geometry.types import (
        BuildingFootprint, BuildingType, WorldCoordinate
    )
    return BuildingFootprint(
        osm_id=67890,
        name="Test Building",
        building_type=BuildingType.OFFICE,
        coordinates=[
            WorldCoordinate(x=0.0, y=0.0, z=0.0),
            WorldCoordinate(x=20.0, y=0.0, z=0.0),
            WorldCoordinate(x=20.0, y=30.0, z=0.0),
            WorldCoordinate(x=0.0, y=30.0, z=0.0),
        ],
        height=50.0,
        levels=12,
        outline=[
            WorldCoordinate(x=0.0, y=0.0, z=0.0),
            WorldCoordinate(x=20.0, y=0.0, z=0.0),
            WorldCoordinate(x=20.0, y=30.0, z=0.0),
            WorldCoordinate(x=0.0, y=30.0, z=0.0),
        ],
        tags={"name": "Test Tower"}
    )


@pytest.fixture
def sample_scene_bounds():
    """Sample scene bounds for Charlotte downtown."""
    from lib.charlotte_digital_twin.geometry.types import SceneBounds
    return SceneBounds(
        min_lat=35.2171,
        max_lat=35.2371,
        min_lon=-80.8531,
        max_lon=-80.8331
    )


@pytest.fixture
def sample_marking_config():
    """Sample lane marking configuration."""
    from lib.charlotte_digital_twin.geometry.lane_markings import MarkingConfig
    return MarkingConfig(
        dash_length=3.0,
        dash_gap=9.0,
        line_width=0.15,
        edge_line_width=0.20,
        double_line_spacing=0.10,
        paint_thickness=0.003,
        paint_roughness=0.4,
        paint_metallic=0.0,
        wear_amount=0.0,
        edge_chipping=0.1,
        emission_strength=0.0
    )


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_depth_exr(tmp_path):
    """Create a mock depth EXR file."""
    exr_path = tmp_path / "depth_0001.exr"
    exr_path.write_bytes(b"mock exr data")
    return exr_path


@pytest.fixture
def mock_normal_exr(tmp_path):
    """Create a mock normal EXR file."""
    exr_path = tmp_path / "normal_0001.exr"
    exr_path.write_bytes(b"mock exr data")
    return exr_path
