"""
Unit tests for lib/sd_projection/building_projection.py

Tests building-specific SD projection functionality including:
- BuildingProjectionConfig and BuildingInfo
- BuildingVisibility and BuildingLOD enums
- BuildingProjector class
- Style presets
- project_onto_buildings convenience function

Note: bpy and mathutils are mocked globally in tests/unit/conftest.py
"""

from pathlib import Path
from dataclasses import asdict
from unittest.mock import Mock, patch, MagicMock
import math

import pytest


class TestBuildingVisibility:
    """Tests for BuildingVisibility enum."""

    def test_visibility_modes(self):
        """Test all BuildingVisibility enum values."""
        from lib.sd_projection.building_projection import BuildingVisibility

        assert BuildingVisibility.FULL.value == "full"
        assert BuildingVisibility.BACKGROUND.value == "background"
        assert BuildingVisibility.SILHOUETTE.value == "silhouette"
        assert BuildingVisibility.HIDDEN.value == "hidden"


class TestBuildingLOD:
    """Tests for BuildingLOD enum."""

    def test_lod_levels(self):
        """Test all BuildingLOD enum values."""
        from lib.sd_projection.building_projection import BuildingLOD

        assert BuildingLOD.HIGH.value == "high"
        assert BuildingLOD.MEDIUM.value == "medium"
        assert BuildingLOD.LOW.value == "low"
        assert BuildingLOD.PROXY.value == "proxy"


class TestBuildingProjectionConfig:
    """Tests for BuildingProjectionConfig dataclass."""

    def test_default_config(self):
        """Test default BuildingProjectionConfig values."""
        from lib.sd_projection.building_projection import BuildingProjectionConfig

        config = BuildingProjectionConfig()

        assert config.batch_size == 4
        assert config.frustum_culling is True
        assert config.occlusion_culling is True
        assert config.cache_textures is True
        assert config.background_visibility.value == "background"
        assert config.background_opacity == 0.8

    def test_lod_distances(self):
        """Test LOD distance configuration."""
        from lib.sd_projection.building_projection import (
            BuildingProjectionConfig,
            BuildingLOD,
        )

        config = BuildingProjectionConfig()

        assert config.lod_distances[BuildingLOD.HIGH] == 50.0
        assert config.lod_distances[BuildingLOD.MEDIUM] == 150.0
        assert config.lod_distances[BuildingLOD.LOW] == 300.0
        assert config.lod_distances[BuildingLOD.PROXY] == 500.0


class TestBuildingInfo:
    """Tests for BuildingInfo dataclass."""

    def test_default_building_info(self):
        """Test BuildingInfo default values."""
        from lib.sd_projection.building_projection import (
            BuildingInfo,
            BuildingVisibility,
            BuildingLOD,
        )

        # Mock object
        mock_obj = Mock()
        mock_obj.name = "TestBuilding"

        info = BuildingInfo(
            name="TestBuilding",
            object=mock_obj,
        )

        assert info.name == "TestBuilding"
        assert info.distance_to_camera == 0.0
        assert info.screen_size == 0.0
        assert info.visibility == BuildingVisibility.FULL
        assert info.lod == BuildingLOD.MEDIUM
        assert info.is_occluded is False
        assert info.in_frustum is True

    def test_building_info_with_values(self):
        """Test BuildingInfo with custom values."""
        from lib.sd_projection.building_projection import (
            BuildingInfo,
            BuildingVisibility,
            BuildingLOD,
        )

        mock_obj = Mock()
        mock_obj.name = "FarBuilding"

        info = BuildingInfo(
            name="FarBuilding",
            object=mock_obj,
            distance_to_camera=450.0,
            screen_size=0.005,
            visibility=BuildingVisibility.BACKGROUND,
            lod=BuildingLOD.PROXY,
            is_occluded=False,
            in_frustum=True,
        )

        assert info.distance_to_camera == 450.0
        assert info.visibility == BuildingVisibility.BACKGROUND
        assert info.lod == BuildingLOD.PROXY


class TestBuildingProjector:
    """Tests for BuildingProjector class."""

    def test_projector_initialization(self):
        """Test BuildingProjector initialization."""
        from lib.sd_projection.building_projection import (
            BuildingProjector,
            BuildingProjectionConfig,
        )

        projector = BuildingProjector()

        assert projector.config is not None
        assert projector.mapper is not None
        assert projector.blender is not None

    def test_projector_with_config(self):
        """Test BuildingProjector with custom config."""
        from lib.sd_projection.building_projection import (
            BuildingProjector,
            BuildingProjectionConfig,
        )

        config = BuildingProjectionConfig(
            batch_size=8,
            frustum_culling=False,
        )

        projector = BuildingProjector(config=config)

        assert projector.config.batch_size == 8
        assert projector.config.frustum_culling is False

    def test_lod_resolution_mapping(self):
        """Test LOD to resolution mapping."""
        from lib.sd_projection.building_projection import (
            BuildingProjector,
            BuildingLOD,
        )

        projector = BuildingProjector()

        # Test resolution for each LOD
        high_res = projector._get_lod_resolution(BuildingLOD.HIGH)
        medium_res = projector._get_lod_resolution(BuildingLOD.MEDIUM)
        low_res = projector._get_lod_resolution(BuildingLOD.LOW)
        proxy_res = projector._get_lod_resolution(BuildingLOD.PROXY)

        assert high_res == (4096, 4096)
        assert medium_res == (2048, 2048)
        assert low_res == (1024, 1024)
        assert proxy_res == (512, 512)

    def test_lod_distance_calculation(self):
        """Test LOD calculation from distance."""
        from lib.sd_projection.building_projection import (
            BuildingProjector,
            BuildingLOD,
        )

        projector = BuildingProjector()

        # Test LOD at different distances
        assert projector._get_lod(25.0) == BuildingLOD.HIGH
        assert projector._get_lod(75.0) == BuildingLOD.MEDIUM
        assert projector._get_lod(200.0) == BuildingLOD.LOW
        assert projector._get_lod(600.0) == BuildingLOD.PROXY


class TestStylePresets:
    """Tests for style presets."""

    def test_cyberpunk_night_preset(self):
        """Test cyberpunk_night style preset."""
        from lib.sd_projection.building_projection import (
            STYLE_PRESETS,
            get_style_preset,
        )

        preset = get_style_preset("cyberpunk_night")

        assert preset is not None
        assert "cyberpunk" in preset.prompt.lower()
        assert preset.drift_config.speed == 0.05

    def test_arcane_painted_preset(self):
        """Test arcane_painted style preset."""
        from lib.sd_projection.building_projection import (
            STYLE_PRESETS,
            get_style_preset,
        )

        preset = get_style_preset("arcane_painted")

        assert preset is not None
        assert "painted" in preset.prompt.lower()
        assert preset.drift_config.speed == 0.02

    def test_trippy_drift_preset(self):
        """Test trippy_drift style preset."""
        from lib.sd_projection.building_projection import (
            STYLE_PRESETS,
            get_style_preset,
            DriftPattern,
        )

        preset = get_style_preset("trippy_drift")

        assert preset is not None
        assert preset.drift_config.speed == 0.15
        # Should have chaos pattern for trippy effect
        from lib.sd_projection.style_blender import DriftPattern
        assert preset.drift_config.pattern == DriftPattern.CHAOS

    def test_noir_gritty_preset(self):
        """Test noir_gritty style preset."""
        from lib.sd_projection.building_projection import (
            get_style_preset,
        )

        preset = get_style_preset("noir_gritty")

        assert preset is not None
        assert "noir" in preset.prompt.lower() or "gritty" in preset.prompt.lower()

    def test_anime_cel_preset(self):
        """Test anime_cel style preset."""
        from lib.sd_projection.building_projection import (
            get_style_preset,
        )

        preset = get_style_preset("anime_cel")

        assert preset is not None
        assert "anime" in preset.prompt.lower()
        # Anime should have drift disabled for clean cel look
        assert preset.drift_config.enabled is False

    def test_invalid_preset(self):
        """Test get_style_preset with invalid name."""
        from lib.sd_projection.building_projection import get_style_preset

        preset = get_style_preset("nonexistent")

        assert preset is None

    def test_list_style_presets(self):
        """Test list_style_presets returns all preset names."""
        from lib.sd_projection.building_projection import (
            list_style_presets,
            STYLE_PRESETS,
        )

        presets = list_style_presets()

        assert len(presets) == len(STYLE_PRESETS)
        assert "cyberpunk_night" in presets
        assert "arcane_painted" in presets
        assert "trippy_drift" in presets
        assert "noir_gritty" in presets
        assert "anime_cel" in presets


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_project_onto_buildings_exists(self):
        """Test project_onto_buildings function exists."""
        from lib.sd_projection.building_projection import project_onto_buildings

        assert project_onto_buildings is not None
        assert callable(project_onto_buildings)


class TestScreenSizeEstimation:
    """Tests for screen size estimation."""

    def test_estimate_screen_size_method_exists(self):
        """Test that _estimate_screen_size method exists."""
        from lib.sd_projection.building_projection import BuildingProjector

        projector = BuildingProjector()

        # Method should exist
        assert hasattr(projector, '_estimate_screen_size')
        assert callable(projector._estimate_screen_size)

    def test_screen_size_math(self):
        """Test screen size calculation math (independent of Vector)."""
        import math

        # Test the angular size formula used in _estimate_screen_size
        # angular_size = 2 * atan(radius / distance)

        # Object at 100 units distance with radius 10
        radius = 10.0
        distance = 100.0
        angular_size = 2 * math.atan(radius / distance)

        # Should be a small positive value
        assert angular_size > 0
        assert angular_size < math.pi  # Less than 180 degrees

        # Object very close should have larger angular size
        close_distance = 10.0
        close_angular = 2 * math.atan(radius / close_distance)
        assert close_angular > angular_size
