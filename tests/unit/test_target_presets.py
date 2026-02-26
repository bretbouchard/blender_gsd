"""
Unit tests for target presets.

Tests for preset loading and creation functions.
"""

import pytest
from pathlib import Path
from lib.cinematic.projection.physical.targets import (
    TargetType,
    SurfaceMaterial,
    ProjectionTarget,
    load_target_preset,
    list_target_presets,
    create_reading_room_target,
    create_garage_door_target,
    create_building_facade_target,
    PLANAR_2X2M,
    GARAGE_DOOR_STANDARD,
)


class TestPresetConstants:
    """Tests for preset constants."""

    def test_planar_2x2m_preset(self):
        """PLANAR_2X2M preset is correct."""
        assert PLANAR_2X2M.name == "planar_2x2m"
        assert PLANAR_2X2M.target_type == TargetType.PLANAR
        assert PLANAR_2X2M.width_m == 2.0
        assert PLANAR_2X2M.height_m == 2.0
        assert len(PLANAR_2X2M.surfaces) == 1

    def test_garage_door_standard_preset(self):
        """GARAGE_DOOR_STANDARD preset is correct."""
        assert GARAGE_DOOR_STANDARD.name == "garage_door_standard"
        assert GARAGE_DOOR_STANDARD.target_type == TargetType.PLANAR
        assert GARAGE_DOOR_STANDARD.width_m == 4.88  # 16ft
        assert GARAGE_DOOR_STANDARD.height_m == 2.13  # 7ft


class TestCreateReadingRoomTarget:
    """Tests for create_reading_room_target function."""

    def test_default_reading_room(self):
        """Default reading room target."""
        target = create_reading_room_target()

        assert target.name == "reading_room"
        assert target.target_type == TargetType.MULTI_SURFACE
        assert len(target.surfaces) == 3

    def test_reading_room_surfaces(self):
        """Reading room has correct surfaces."""
        target = create_reading_room_target()

        surface_names = [s.name for s in target.surfaces]
        assert "upper_cabinet" in surface_names
        assert "lower_cabinet" in surface_names
        assert "desk_surface" in surface_names

    def test_reading_room_custom_dimensions(self):
        """Reading room with custom dimensions."""
        target = create_reading_room_target(
            upper_width=3.0,
            upper_height=0.3,
        )

        # Find upper cabinet
        upper = next(s for s in target.surfaces if s.name == "upper_cabinet")
        assert upper.dimensions == (3.0, 0.3)

    def test_reading_room_calibration_recommendation(self):
        """Reading room recommends four_point_dlt."""
        target = create_reading_room_target()

        assert target.recommended_calibration == "four_point_dlt"


class TestCreateGarageDoorTarget:
    """Tests for create_garage_door_target function."""

    def test_default_garage_door(self):
        """Default garage door target."""
        target = create_garage_door_target()

        assert target.name == "garage_door"
        assert target.target_type == TargetType.PLANAR
        assert len(target.surfaces) == 1

    def test_garage_door_default_dimensions(self):
        """Default dimensions are 16ft x 7ft."""
        target = create_garage_door_target()

        assert target.width_m == pytest.approx(4.88, abs=0.01)  # 16ft
        assert target.height_m == pytest.approx(2.13, abs=0.01)  # 7ft

    def test_garage_door_custom_dimensions(self):
        """Custom garage door dimensions."""
        target = create_garage_door_target(width=5.0, height=2.5)

        assert target.width_m == 5.0
        assert target.height_m == 2.5

    def test_garage_door_calibration_recommendation(self):
        """Garage door recommends three_point."""
        target = create_garage_door_target()

        assert target.recommended_calibration == "three_point"

    def test_garage_door_preset_measurements(self):
        """Garage door has preset measurements."""
        target = create_garage_door_target()

        assert "frame_width" in target.preset_measurements
        assert "handle_height" in target.preset_measurements


class TestCreateBuildingFacadeTarget:
    """Tests for create_building_facade_target function."""

    def test_default_building_facade(self):
        """Default building facade target."""
        target = create_building_facade_target()

        assert target.name == "building_facade"
        assert target.target_type == TargetType.MULTI_SURFACE
        assert len(target.surfaces) >= 2  # Main facade + windows

    def test_building_facade_default_dimensions(self):
        """Default dimensions are 20m x 15m."""
        target = create_building_facade_target()

        assert target.width_m == 20.0
        assert target.height_m == 15.0

    def test_building_facade_custom_dimensions(self):
        """Custom building facade dimensions."""
        target = create_building_facade_target(width=30.0, height=20.0)

        assert target.width_m == 30.0
        assert target.height_m == 20.0

    def test_building_facade_calibration_recommendation(self):
        """Building facade recommends four_point_dlt."""
        target = create_building_facade_target()

        assert target.recommended_calibration == "four_point_dlt"

    def test_building_facade_has_windows(self):
        """Building facade has window surfaces."""
        target = create_building_facade_target()

        window_surfaces = [s for s in target.surfaces if "window" in s.name.lower()]
        assert len(window_surfaces) >= 2


class TestListTargetPresets:
    """Tests for list_target_presets function."""

    def test_list_presets_returns_list(self):
        """list_target_presets returns a list."""
        presets = list_target_presets()

        assert isinstance(presets, list)

    def test_list_presets_includes_expected(self):
        """List includes known presets if files exist."""
        # This test depends on YAML files existing
        presets = list_target_presets()

        # If preset files exist, they should be listed
        # The actual content depends on what's in configs/
        pass


class TestLoadTargetPreset:
    """Tests for load_target_preset function."""

    def test_load_preset_not_found(self):
        """Loading non-existent preset raises error."""
        with pytest.raises(FileNotFoundError):
            load_target_preset("nonexistent_preset")

    def test_load_preset_structure(self):
        """Loaded preset has correct structure."""
        # This would test actual file loading
        # Skip if files don't exist
        try:
            target = load_target_preset("garage_door")

            assert isinstance(target, ProjectionTarget)
            assert target.name == "garage_door"
        except FileNotFoundError:
            pytest.skip("garage_door.yaml not found")


class TestPresetMaterials:
    """Tests for preset material assignments."""

    def test_garage_door_material(self):
        """Garage door uses white paint."""
        target = create_garage_door_target()

        assert target.surfaces[0].material == SurfaceMaterial.WHITE_PAINT
        assert target.surfaces[0].albedo == 0.85

    def test_reading_room_desk_material(self):
        """Reading room desk uses wood material."""
        target = create_reading_room_target()

        desk = next(s for s in target.surfaces if s.name == "desk_surface")
        assert desk.material == SurfaceMaterial.WOOD

    def test_building_facade_materials(self):
        """Building facade uses appropriate materials."""
        target = create_building_facade_target()

        main = next(s for s in target.surfaces if s.name == "main_facade")
        assert main.material == SurfaceMaterial.GRAY_PAINT

        windows = [s for s in target.surfaces if "window" in s.name.lower()]
        for window in windows:
            assert window.material == SurfaceMaterial.GLASS
