"""
API Stability Regression Tests

Verifies that public APIs remain stable across changes.
If these tests fail, it indicates a breaking change that
should be documented and versioned appropriately.
"""

import pytest

from lib.oracle import Oracle


@pytest.mark.regression
class TestCinematicAPIStability:
    """Verify cinematic module API stability."""

    def test_types_module_exports(self):
        """Types module should export expected symbols."""
        from lib.cinematic import types

        # Core types
        assert hasattr(types, "CameraConfig")
        assert hasattr(types, "LightConfig")
        assert hasattr(types, "RenderSettings")
        assert hasattr(types, "ColorConfig")
        assert hasattr(types, "TurntableConfig")

    def test_camera_module_exports(self):
        """Camera module should export expected symbols."""
        from lib.cinematic import camera

        # Check for camera module functions
        assert hasattr(camera, "create_camera") or hasattr(camera, "CameraRig")

    def test_lighting_module_exports(self):
        """Lighting module should export expected symbols."""
        from lib.cinematic import lighting

        # Check for lighting module
        assert hasattr(lighting, "create_light") or hasattr(lighting, "LightRig")

    def test_color_module_exports(self):
        """Color module should export expected symbols."""
        from lib.cinematic import color

        assert hasattr(color, "ColorConfig")
        assert hasattr(color, "LUTConfig")


@pytest.mark.regression
class TestGeometryAPIStability:
    """Verify geometry module API stability."""

    def test_types_module_exports(self):
        """Types module should export expected symbols."""
        from lib.charlotte_digital_twin.geometry import types

        assert hasattr(types, "GeometryConfig")
        assert hasattr(types, "SceneOrigin")
        assert hasattr(types, "WorldCoordinate")
        assert hasattr(types, "GeoCoordinate")
        assert hasattr(types, "RoadSegment")
        assert hasattr(types, "BuildingFootprint")
        assert hasattr(types, "SceneBounds")

    def test_coordinates_module_exports(self):
        """Coordinates module should export expected symbols."""
        from lib.charlotte_digital_twin.geometry import coordinates

        assert hasattr(coordinates, "CoordinateTransformer")
        assert hasattr(coordinates, "CHARLOTTE_ORIGINS")


@pytest.mark.regression
@pytest.mark.requires_blender
class TestSDProjectionAPIStability:
    """Verify SD projection module API stability.

    Note: These tests require bpy (Blender) as the sd_projection modules
    import bpy at module level.
    """

    def test_sd_projection_exports(self):
        """SD projection module should export expected symbols."""
        pytest.skip("Requires Blender (bpy module)")

    def test_style_blender_exports(self):
        """Style blender module should export expected symbols."""
        pytest.skip("Requires Blender (bpy module)")

    def test_building_projection_exports(self):
        """Building projection module should export expected symbols."""
        pytest.skip("Requires Blender (bpy module)")


@pytest.mark.regression
class TestTrackingAPIStability:
    """Verify tracking module API stability."""

    def test_tracking_types_exports(self):
        """Tracking types module should export expected symbols."""
        from lib.cinematic.tracking import types

        assert hasattr(types, "TrackingSession")
        assert hasattr(types, "TrackData")
        assert hasattr(types, "SolveData")


@pytest.mark.regression
class TestFollowCameraAPIStability:
    """Verify follow camera module API stability."""

    def test_follow_cam_types_exports(self):
        """Follow camera types module should export expected symbols."""
        from lib.cinematic.follow_cam import types

        assert hasattr(types, "FollowCameraConfig")
        assert hasattr(types, "FollowMode")
        assert hasattr(types, "ObstacleInfo")


@pytest.mark.regression
class TestOracleAPIStability:
    """Verify oracle module API stability."""

    def test_oracle_exports(self):
        """Oracle module should export expected symbols."""
        import lib.oracle as oracle

        assert hasattr(oracle, "Oracle")
        assert hasattr(oracle, "compare_numbers")
        assert hasattr(oracle, "compare_vectors")
        assert hasattr(oracle, "exit_code_zero")
        assert hasattr(oracle, "file_exists")


@pytest.mark.regression
@pytest.mark.requires_blender
class TestConvenienceFunctions:
    """Verify convenience functions remain available.

    Note: SD projection convenience functions require bpy.
    """

    def test_project_onto_buildings_function(self):
        """project_onto_buildings convenience function should exist."""
        pytest.skip("Requires Blender (bpy module)")

    def test_sd_projection_package_exports(self):
        """SD projection package should export main functions."""
        pytest.skip("Requires Blender (bpy module)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "regression"])
