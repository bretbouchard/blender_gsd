"""
Unit tests for Import/Export module.

Tests external format parsers for FBX, Alembic, BVH, Nuke .chan,
and JSON camera formats.
"""

import pytest
import sys
import tempfile
import os
import math
from pathlib import Path

# Add lib to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from cinematic.tracking.import_export import (
    ImportedCamera,
    FBXParser,
    AlembicParser,
    BVHParser,
    NukeChanParser,
    JSONCameraParser,
    TrackingImporter,
    TrackingExporter,
    get_supported_import_formats,
    import_tracking_data,
    import_nuke_chan,
    COORDINATE_SYSTEMS,
    convert_yup_to_zup_position,
    fov_to_focal_length,
)
from cinematic.tracking.types import (
    SolveData,
    TrackingSession,
)
from oracle import Oracle


class TestImportedCamera:
    """Tests for ImportedCamera dataclass."""

    def test_create_default(self):
        """Test creating imported camera with defaults."""
        camera = ImportedCamera()
        Oracle.assert_equal(camera.name, "imported_camera")
        Oracle.assert_equal(camera.frame_start, 1)
        Oracle.assert_equal(camera.frame_end, 1)
        Oracle.assert_equal(len(camera.positions), 0)

    def test_create_with_data(self):
        """Test creating with animation data."""
        camera = ImportedCamera(
            name="test_camera",
            frame_start=1,
            frame_end=10,
            positions={1: (0, 0, 5), 10: (10, 0, 5)},
            rotations_euler={1: (0, 0, 0), 10: (0, 45, 0)},
        )
        Oracle.assert_equal(camera.name, "test_camera")
        Oracle.assert_equal(len(camera.positions), 2)

    def test_to_solve_data(self):
        """Test converting to SolveData object."""
        camera = ImportedCamera(
            name="conversion_test",
            frame_start=1,
            frame_end=5,
            positions={
                1: (0, 0, 5),
                2: (1, 0, 5),
                3: (2, 0, 5),
            },
            rotations_euler={
                1: (0, 0, 0),
                2: (0, 15, 0),
                3: (0, 30, 0),
            },
            focal_lengths={1: 50.0, 2: 50.0, 3: 50.0},
        )

        solve_data = camera.to_solve_data()

        Oracle.assert_equal(solve_data.name, "conversion_test")
        Oracle.assert_equal(solve_data.frame_range, (1, 5))  # Uses camera frame_start/end
        Oracle.assert_equal(len(solve_data.camera_transforms), 3)

    def test_quaternion_to_euler(self):
        """Test quaternion to Euler conversion."""
        camera = ImportedCamera()

        # No rotation (identity quaternion)
        quat = (1, 0, 0, 0)
        euler = camera._quaternion_to_euler(quat)
        Oracle.assert_less_than(abs(euler[0]), 0.001)
        Oracle.assert_less_than(abs(euler[1]), 0.001)
        Oracle.assert_less_than(abs(euler[2]), 0.001)

        # 90 degree Y rotation
        # Quaternion for 90 degree rotation around Y: (cos(45), 0, sin(45), 0)
        import math
        quat = (math.cos(math.pi/4), 0, math.sin(math.pi/4), 0)
        euler = camera._quaternion_to_euler(quat)
        # Should be approximately 90 degrees around Y
        Oracle.assert_less_than(abs(euler[1] - 90), 1.0)


class TestFBXParser:
    """Tests for FBX parser."""

    def test_parse_fallback(self):
        """Test fallback parsing (without Blender)."""
        with tempfile.NamedTemporaryFile(suffix=".fbx", delete=False) as f:
            f.write(b"mock fbx data")
            temp_path = f.name

        try:
            camera = FBXParser.parse(temp_path)
            Oracle.assert_not_none(camera)
            Oracle.assert_equal(camera.source_format, "fbx")
            Oracle.assert_greater_than(len(camera.positions), 0)
        finally:
            os.unlink(temp_path)

    def test_generates_animation(self):
        """Test that fallback generates animation data."""
        with tempfile.NamedTemporaryFile(suffix=".fbx", delete=False) as f:
            f.write(b"mock")
            temp_path = f.name

        try:
            camera = FBXParser.parse(temp_path)

            # Should have animation frames
            Oracle.assert_greater_than(camera.frame_end, camera.frame_start)

            # Positions should change over time
            pos_start = camera.positions[camera.frame_start]
            pos_end = camera.positions[camera.frame_end]
            Oracle.assert_not_equal(pos_start, pos_end)
        finally:
            os.unlink(temp_path)


class TestAlembicParser:
    """Tests for Alembic parser."""

    def test_parse_fallback(self):
        """Test fallback parsing."""
        with tempfile.NamedTemporaryFile(suffix=".abc", delete=False) as f:
            f.write(b"mock alembic")
            temp_path = f.name

        try:
            camera = AlembicParser.parse(temp_path)
            Oracle.assert_not_none(camera)
            Oracle.assert_equal(camera.source_format, "alembic")
        finally:
            os.unlink(temp_path)


class TestBVHParser:
    """Tests for BVH parser."""

    def create_test_bvh(self):
        """Create a test BVH file."""
        bvh_content = """
HIERARCHY
ROOT Hips
{
    OFFSET 0.00 0.00 0.00
    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
    JOINT Chest
    {
        OFFSET 0.00 10.00 0.00
        CHANNELS 3 Zrotation Xrotation Yrotation
        End Site
        {
            OFFSET 0.00 10.00 0.00
        }
    }
}
MOTION
Frames: 5
Frame Time: 0.04
0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00
1.00 0.50 0.00 5.00 2.00 0.00 0.00 0.00 0.00
2.00 1.00 0.00 10.00 4.00 0.00 0.00 0.00 0.00
3.00 1.50 0.00 15.00 6.00 0.00 0.00 0.00 0.00
4.00 2.00 0.00 20.00 8.00 0.00 0.00 0.00 0.00
"""
        return bvh_content

    def test_parse_bvh(self):
        """Test parsing BVH file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bvh", delete=False) as f:
            f.write(self.create_test_bvh())
            temp_path = f.name

        try:
            camera = BVHParser.parse(temp_path)

            Oracle.assert_not_none(camera)
            Oracle.assert_equal(camera.source_format, "bvh")
            Oracle.assert_equal(camera.frame_start, 1)
            Oracle.assert_equal(camera.frame_end, 5)

            # Should have position and rotation data
            Oracle.assert_greater_than(len(camera.positions), 0)
            Oracle.assert_greater_than(len(camera.rotations_euler), 0)

        finally:
            os.unlink(temp_path)


class TestNukeChanParser:
    """Tests for Nuke .chan parser."""

    def create_test_chan(self):
        """Create a test .chan file."""
        chan_content = """# Nuke camera export
1 0.0 0.0 5.0 0.0 0.0 0.0 50.0
2 0.5 0.0 5.2 0.0 5.0 0.0 50.0
3 1.0 0.0 5.4 0.0 10.0 0.0 50.0
4 1.5 0.0 5.6 0.0 15.0 0.0 50.0
5 2.0 0.0 5.8 0.0 20.0 0.0 50.0
"""
        return chan_content

    def test_parse_chan(self):
        """Test parsing .chan file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".chan", delete=False) as f:
            f.write(self.create_test_chan())
            temp_path = f.name

        try:
            camera = NukeChanParser.parse(temp_path)

            Oracle.assert_not_none(camera)
            Oracle.assert_equal(camera.source_format, "nuke_chan")
            Oracle.assert_equal(camera.frame_start, 1)
            Oracle.assert_equal(camera.frame_end, 5)

            # Check position conversion
            Oracle.assert_in(1, camera.positions)
            Oracle.assert_in(5, camera.positions)

            # Check focal length
            Oracle.assert_equal(camera.focal_lengths[1], 50.0)

        finally:
            os.unlink(temp_path)

    def test_coordinate_conversion(self):
        """Test coordinate system conversion."""
        parser = NukeChanParser()

        # Test Nuke to Blender
        pos = parser._convert_position(1.0, 2.0, 3.0, "nuke")
        Oracle.assert_equal(pos, (1.0, -3.0, 2.0))

        # Test Maya to Blender
        pos = parser._convert_position(1.0, 2.0, 3.0, "maya")
        Oracle.assert_equal(pos, (1.0, 3.0, 2.0))


class TestJSONCameraParser:
    """Tests for JSON camera parser."""

    def create_test_json(self):
        """Create a test JSON file."""
        import json
        data = {
            "camera": {
                "name": "test_json_camera",
                "frames": [
                    {"frame": 1, "position": [0, 0, 5], "rotation": [0, 0, 0], "focal": 50},
                    {"frame": 2, "position": [1, 0, 5], "rotation": [0, 10, 0], "focal": 50},
                    {"frame": 3, "position": [2, 0, 5], "rotation": [0, 20, 0], "focal": 50},
                ]
            }
        }
        return json.dumps(data, indent=2)

    def test_parse_json(self):
        """Test parsing JSON camera file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(self.create_test_json())
            temp_path = f.name

        try:
            camera = JSONCameraParser.parse(temp_path)

            Oracle.assert_not_none(camera)
            Oracle.assert_equal(camera.name, "test_json_camera")
            Oracle.assert_equal(camera.frame_start, 1)
            Oracle.assert_equal(camera.frame_end, 3)

            # Check data
            Oracle.assert_equal(camera.positions[1], (0, 0, 5))
            Oracle.assert_equal(camera.rotations_euler[2], (0, 10, 0))
            Oracle.assert_equal(camera.focal_lengths[3], 50)

        finally:
            os.unlink(temp_path)


class TestTrackingImporter:
    """Tests for TrackingImporter class."""

    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = get_supported_import_formats()

        Oracle.assert_in(".fbx", formats)
        Oracle.assert_in(".abc", formats)
        Oracle.assert_in(".bvh", formats)
        Oracle.assert_in(".chan", formats)
        Oracle.assert_in(".json", formats)

    def test_import_unsupported_format(self):
        """Test importing unsupported format raises error."""
        importer = TrackingImporter()

        with pytest.raises(ValueError):
            importer.import_camera("test.xyz")

    def test_import_json_with_offset(self):
        """Test importing JSON with frame offset."""
        importer = TrackingImporter()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            import json
            data = {
                "camera": {
                    "name": "offset_test",
                    "frames": [
                        {"frame": 1, "position": [0, 0, 0], "rotation": [0, 0, 0]},
                        {"frame": 2, "position": [1, 0, 0], "rotation": [0, 0, 0]},
                    ]
                }
            }
            f.write(json.dumps(data).encode())
            temp_path = f.name

        try:
            camera = importer.import_camera(temp_path, frame_offset=100)

            # Frames should be shifted by 100
            Oracle.assert_equal(camera.frame_start, 101)
            Oracle.assert_equal(camera.frame_end, 102)
            Oracle.assert_in(101, camera.positions)

        finally:
            os.unlink(temp_path)

    def test_import_json_with_scale(self):
        """Test importing JSON with scale factor."""
        importer = TrackingImporter()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            import json
            data = {
                "camera": {
                    "name": "scale_test",
                    "frames": [
                        {"frame": 1, "position": [1, 1, 1], "rotation": [0, 0, 0]},
                    ]
                }
            }
            f.write(json.dumps(data).encode())
            temp_path = f.name

        try:
            camera = importer.import_camera(temp_path, scale_factor=2.0)

            # Position should be scaled
            Oracle.assert_equal(camera.positions[1], (2.0, 2.0, 2.0))

        finally:
            os.unlink(temp_path)

    def test_import_to_solve_data(self):
        """Test importing to SolveData."""
        importer = TrackingImporter()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            import json
            data = {
                "camera": {
                    "name": "solve_test",
                    "frames": [
                        {"frame": 1, "position": [0, 0, 5], "rotation": [0, 0, 0]},
                    ]
                }
            }
            f.write(json.dumps(data).encode())
            temp_path = f.name

        try:
            solve_data = importer.import_to_solve_data(temp_path)

            Oracle.assert_not_none(solve_data)
            assert isinstance(solve_data, SolveData)
            Oracle.assert_equal(len(solve_data.camera_transforms), 1)

        finally:
            os.unlink(temp_path)


class TestTrackingExporter:
    """Tests for TrackingExporter class."""

    def create_test_solve_data(self):
        """Create a test SolveData for export."""
        return SolveData(
            name="test_solve",
            frame_range=(1, 3),
            focal_length=50.0,
            camera_transforms={
                1: (0.0, 0.0, 5.0, 0.0, 0.0, 0.0),
                2: (1.0, 0.0, 5.0, 0.0, 10.0, 0.0),
                3: (2.0, 0.0, 5.0, 0.0, 20.0, 0.0),
            },
            coordinate_system="z_up",
        )

    def test_export_nuke_chan(self):
        """Test exporting to Nuke .chan format."""
        exporter = TrackingExporter()
        solve_data = self.create_test_solve_data()

        with tempfile.NamedTemporaryFile(suffix=".chan", delete=False) as f:
            temp_path = f.name

        try:
            result = exporter.export_nuke_chan(solve_data, temp_path)
            Oracle.assert_true(result)

            # Verify file was created with content
            with open(temp_path, "r") as f:
                content = f.read()
                Oracle.assert_in("# Nuke camera", content)
                Oracle.assert_in("1 0.0", content)  # Frame 1

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_export_json(self):
        """Test exporting to JSON format."""
        exporter = TrackingExporter()
        solve_data = self.create_test_solve_data()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            result = exporter.export_json(solve_data, temp_path)
            Oracle.assert_true(result)

            # Verify JSON structure
            import json
            with open(temp_path, "r") as f:
                data = json.load(f)
                Oracle.assert_in("camera", data)
                Oracle.assert_equal(len(data["camera"]["frames"]), 3)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_import_nuke_chan(self):
        """Test convenience import_nuke_chan function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".chan", delete=False) as f:
            f.write("# Test chan file\n")
            f.write("1 0.0 0.0 5.0 0.0 0.0 0.0 50.0\n")
            f.write("2 1.0 0.0 5.0 0.0 10.0 0.0 50.0\n")
            temp_path = f.name

        try:
            solve_data = import_nuke_chan(temp_path)

            Oracle.assert_not_none(solve_data)
            assert isinstance(solve_data, SolveData)
            Oracle.assert_equal(solve_data.coordinate_system, "z_up")

        finally:
            os.unlink(temp_path)

    def test_import_tracking_data_chan(self):
        """Test convenience import_tracking_data function with .chan."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".chan", delete=False) as f:
            f.write("# Test chan file\n")
            f.write("1 0.0 0.0 5.0 0.0 0.0 0.0\n")
            temp_path = f.name

        try:
            solve_data = import_tracking_data(temp_path)

            Oracle.assert_not_none(solve_data)
            assert isinstance(solve_data, SolveData)

        finally:
            os.unlink(temp_path)

    def test_coordinate_conversion(self):
        """Test coordinate conversion functions."""
        # Y-up to Z-up
        result = convert_yup_to_zup_position(1.0, 2.0, 3.0)
        Oracle.assert_equal(result, (1.0, 3.0, -2.0))

    def test_fov_to_focal_length(self):
        """Test FOV to focal length conversion."""
        # 45 degree FOV, 36mm sensor = ~43.5mm focal
        focal = fov_to_focal_length(45.0, 36.0)
        Oracle.assert_greater_than(focal, 40.0)
        Oracle.assert_less_than(focal, 45.0)


class TestCoordinateSystems:
    """Tests for coordinate system constants."""

    def test_coordinate_systems_exist(self):
        """Test that coordinate system definitions exist."""
        Oracle.assert_in("blender", COORDINATE_SYSTEMS)
        Oracle.assert_in("maya", COORDINATE_SYSTEMS)
        Oracle.assert_in("nuke", COORDINATE_SYSTEMS)

    def test_blender_coordinate_system(self):
        """Test Blender coordinate system definition."""
        blender = COORDINATE_SYSTEMS["blender"]
        Oracle.assert_equal(blender["up"], "Z")
        Oracle.assert_equal(blender["forward"], "-Y")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
