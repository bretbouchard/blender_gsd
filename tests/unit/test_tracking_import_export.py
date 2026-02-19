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
    COORDINATE_SYSTEMS,
)
from cinematic.tracking.types import (
    Solve,
    SolveStatus,
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

    def test_to_solve(self):
        """Test converting to Solve object."""
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

        solve = camera.to_solve()

        Oracle.assert_equal(solve.status, SolveStatus.SUCCESS)
        Oracle.assert_equal(len(solve.results), 3)

    def test_euler_to_quaternion(self):
        """Test Euler to quaternion conversion."""
        camera = ImportedCamera()

        # No rotation
        quat = camera._euler_to_quaternion((0, 0, 0))
        Oracle.assert_equal(round(quat[0], 3), 1.0)  # w = 1

        # 90 degree Y rotation
        quat = camera._euler_to_quaternion((0, 90, 0))
        # Quaternion magnitude should be ~1
        mag = math.sqrt(sum(q ** 2 for q in quat))
        Oracle.assert_less_than(abs(mag - 1.0), 0.001)


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

    def test_import_with_offset(self):
        """Test importing with frame offset."""
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

    def test_import_with_scale(self):
        """Test importing with scale factor."""
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

    def test_import_to_session(self):
        """Test importing directly to session."""
        importer = TrackingImporter()
        session = TrackingSession(name="import_test")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            import json
            data = {
                "camera": {
                    "name": "session_test",
                    "frames": [
                        {"frame": 1, "position": [0, 0, 5], "rotation": [0, 0, 0]},
                    ]
                }
            }
            f.write(json.dumps(data).encode())
            temp_path = f.name

        try:
            solve = importer.import_to_session(session, temp_path)

            Oracle.assert_not_none(solve)
            Oracle.assert_equal(len(session.solves), 1)
            Oracle.assert_equal(session.active_solve, solve.id)

        finally:
            os.unlink(temp_path)


class TestTrackingExporter:
    """Tests for TrackingExporter class."""

    def create_test_solve(self):
        """Create a test solve for export."""
        from cinematic.tracking.types import SolveResult

        solve = Solve(
            status=SolveStatus.SUCCESS,
            results=[
                SolveResult(frame=1, position=(0, 0, 5), rotation=(1, 0, 0, 0), focal_length=50),
                SolveResult(frame=2, position=(1, 0, 5), rotation=(0.98, 0, 0.17, 0), focal_length=50),
                SolveResult(frame=3, position=(2, 0, 5), rotation=(0.94, 0, 0.34, 0), focal_length=50),
            ],
        )
        return solve

    def test_export_nuke_chan(self):
        """Test exporting to Nuke .chan format."""
        exporter = TrackingExporter()
        solve = self.create_test_solve()

        with tempfile.NamedTemporaryFile(suffix=".chan", delete=False) as f:
            temp_path = f.name

        try:
            result = exporter.export_nuke_chan(solve, temp_path)
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
        solve = self.create_test_solve()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            result = exporter.export_json(solve, temp_path)
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

    def test_quaternion_to_euler(self):
        """Test quaternion to Euler conversion."""
        exporter = TrackingExporter()

        # Identity quaternion
        euler = exporter._quaternion_to_euler((1, 0, 0, 0))
        Oracle.assert_less_than(abs(euler[0]), 0.001)
        Oracle.assert_less_than(abs(euler[1]), 0.001)
        Oracle.assert_less_than(abs(euler[2]), 0.001)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_import_tracking_data(self):
        """Test convenience import function."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            import json
            data = {
                "camera": {
                    "name": "convenience_test",
                    "frames": [
                        {"frame": 1, "position": [0, 0, 5], "rotation": [0, 0, 0]},
                    ]
                }
            }
            f.write(json.dumps(data).encode())
            temp_path = f.name

        try:
            camera = import_tracking_data(temp_path)

            Oracle.assert_not_none(camera)
            Oracle.assert_equal(camera.source_format, "json")

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
