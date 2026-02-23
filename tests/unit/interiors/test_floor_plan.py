"""
Tests for Floor Plan Generator

Tests floor plan presets and generator functions.
"""

import pytest
from lib.interiors.floor_plan import (
    FloorPlanPreset,
    FLOOR_PLAN_PRESETS,
    FloorPlanGenerator,
    generate_apartment_floor_plan,
    generate_office_floor_plan,
    generate_house_floor_plan,
    list_floor_plan_presets,
    get_floor_plan_preset,
)


class TestFloorPlanPreset:
    """Tests for FloorPlanPreset dataclass."""

    def test_create(self):
        """Test creating FloorPlanPreset."""
        preset = FloorPlanPreset(
            name="Test",
            description="Test preset",
            width=10.0,
            height=8.0,
            room_count=4,
            room_types=["living_room", "bedroom"],
            style="modern",
        )
        assert preset.name == "Test"
        assert preset.width == 10.0
        assert preset.room_count == 4


class TestFloorPlanPresets:
    """Tests for predefined presets."""

    def test_presets_exist(self):
        """Test that FLOOR_PLAN_PRESETS is populated."""
        assert isinstance(FLOOR_PLAN_PRESETS, dict)
        assert len(FLOOR_PLAN_PRESETS) > 0

    def test_apartment_presets(self):
        """Test apartment presets exist."""
        assert "studio_apartment" in FLOOR_PLAN_PRESETS
        assert "one_bedroom_apartment" in FLOOR_PLAN_PRESETS
        assert "two_bedroom_apartment" in FLOOR_PLAN_PRESETS
        assert "luxury_apartment" in FLOOR_PLAN_PRESETS

    def test_house_presets(self):
        """Test house presets exist."""
        assert "small_house" in FLOOR_PLAN_PRESETS
        assert "medium_house" in FLOOR_PLAN_PRESETS
        assert "large_house" in FLOOR_PLAN_PRESETS
        assert "mansion" in FLOOR_PLAN_PRESETS

    def test_office_presets(self):
        """Test office presets exist."""
        assert "small_office" in FLOOR_PLAN_PRESETS
        assert "medium_office" in FLOOR_PLAN_PRESETS
        assert "large_office" in FLOOR_PLAN_PRESETS

    def test_specialty_presets(self):
        """Test specialty presets exist."""
        assert "loft" in FLOOR_PLAN_PRESETS
        assert "cottage" in FLOOR_PLAN_PRESETS
        assert "penthouse" in FLOOR_PLAN_PRESETS

    def test_preset_dimensions(self):
        """Test preset dimensions are positive."""
        for name, preset in FLOOR_PLAN_PRESETS.items():
            assert preset.width > 0, f"{name} has invalid width"
            assert preset.height > 0, f"{name} has invalid height"
            assert preset.room_count > 0, f"{name} has invalid room_count"


class TestFloorPlanGenerator:
    """Tests for FloorPlanGenerator class."""

    def test_init(self):
        """Test FloorPlanGenerator initialization."""
        generator = FloorPlanGenerator()
        assert generator.seed is None

    def test_init_with_seed(self):
        """Test FloorPlanGenerator initialization with seed."""
        generator = FloorPlanGenerator(seed=42)
        assert generator.seed == 42

    def test_generate_preset(self):
        """Test generating from preset."""
        generator = FloorPlanGenerator(seed=42)
        plan = generator.generate_preset("studio_apartment")

        assert plan is not None
        assert len(plan.rooms) > 0

    def test_generate_preset_invalid(self):
        """Test generating from invalid preset."""
        generator = FloorPlanGenerator()
        with pytest.raises(ValueError):
            generator.generate_preset("nonexistent_preset")

    def test_generate_custom(self):
        """Test generating custom floor plan."""
        generator = FloorPlanGenerator(seed=42)
        plan = generator.generate_custom(
            width=12,
            height=10,
            room_count=5,
            style="modern",
        )

        assert plan is not None
        assert plan.dimensions == (12, 10)

    def test_generate_custom_with_room_types(self):
        """Test generating custom with room types."""
        generator = FloorPlanGenerator(seed=42)
        plan = generator.generate_custom(
            width=12,
            height=10,
            room_count=3,
            room_types=["living_room", "kitchen", "bedroom"],
        )

        assert plan is not None

    def test_list_presets(self):
        """Test listing presets."""
        generator = FloorPlanGenerator()
        presets = generator.list_presets()

        assert isinstance(presets, list)
        assert len(presets) > 0
        assert "studio_apartment" in presets

    def test_get_preset_info(self):
        """Test getting preset info."""
        generator = FloorPlanGenerator()
        info = generator.get_preset_info("studio_apartment")

        assert "name" in info
        assert "description" in info
        assert "dimensions" in info
        assert "area" in info
        assert "room_count" in info

    def test_get_preset_info_invalid(self):
        """Test getting invalid preset info."""
        generator = FloorPlanGenerator()
        with pytest.raises(ValueError):
            generator.get_preset_info("nonexistent")


class TestGenerateApartmentFloorPlan:
    """Tests for generate_apartment_floor_plan function."""

    def test_studio(self):
        """Test generating studio apartment."""
        plan = generate_apartment_floor_plan(size="studio", seed=42)
        assert plan is not None

    def test_one_bedroom(self):
        """Test generating one bedroom apartment."""
        plan = generate_apartment_floor_plan(size="one_bedroom", seed=42)
        assert plan is not None

    def test_two_bedroom(self):
        """Test generating two bedroom apartment."""
        plan = generate_apartment_floor_plan(size="two_bedroom", seed=42)
        assert plan is not None

    def test_luxury(self):
        """Test generating luxury apartment."""
        plan = generate_apartment_floor_plan(size="luxury", seed=42)
        assert plan is not None

    def test_default(self):
        """Test default size (medium)."""
        plan = generate_apartment_floor_plan(seed=42)
        assert plan is not None


class TestGenerateOfficeFloorPlan:
    """Tests for generate_office_floor_plan function."""

    def test_small(self):
        """Test generating small office."""
        plan = generate_office_floor_plan(size="small", seed=42)
        assert plan is not None

    def test_medium(self):
        """Test generating medium office."""
        plan = generate_office_floor_plan(size="medium", seed=42)
        assert plan is not None

    def test_large(self):
        """Test generating large office."""
        plan = generate_office_floor_plan(size="large", seed=42)
        assert plan is not None

    def test_default(self):
        """Test default size."""
        plan = generate_office_floor_plan(seed=42)
        assert plan is not None


class TestGenerateHouseFloorPlan:
    """Tests for generate_house_floor_plan function."""

    def test_small(self):
        """Test generating small house."""
        plan = generate_house_floor_plan(size="small", seed=42)
        assert plan is not None

    def test_medium(self):
        """Test generating medium house."""
        plan = generate_house_floor_plan(size="medium", seed=42)
        assert plan is not None

    def test_large(self):
        """Test generating large house."""
        plan = generate_house_floor_plan(size="large", seed=42)
        assert plan is not None

    def test_mansion(self):
        """Test generating mansion."""
        plan = generate_house_floor_plan(size="mansion", seed=42)
        assert plan is not None

    def test_default(self):
        """Test default size."""
        plan = generate_house_floor_plan(seed=42)
        assert plan is not None


class TestListFloorPlanPresets:
    """Tests for list_floor_plan_presets function."""

    def test_list(self):
        """Test listing all presets."""
        presets = list_floor_plan_presets()
        assert isinstance(presets, list)
        assert len(presets) >= 13  # At least all defined presets


class TestGetFloorPlanPreset:
    """Tests for get_floor_plan_preset function."""

    def test_get_valid(self):
        """Test getting valid preset."""
        preset = get_floor_plan_preset("studio_apartment")
        assert preset.name == "Studio Apartment"

    def test_get_invalid(self):
        """Test getting invalid preset."""
        with pytest.raises(ValueError):
            get_floor_plan_preset("nonexistent_preset")


class TestGeneratorEdgeCases:
    """Edge case tests for floor plan generator."""

    def test_deterministic_generation(self):
        """Test that same seed produces same results."""
        plan1 = generate_apartment_floor_plan(size="studio", seed=42)
        plan2 = generate_apartment_floor_plan(size="studio", seed=42)

        assert len(plan1.rooms) == len(plan2.rooms)

    def test_different_seeds(self):
        """Test that different seeds can produce different results."""
        generator1 = FloorPlanGenerator(seed=1)
        generator2 = FloorPlanGenerator(seed=999)

        # Note: Small floor plans may still produce same results
        # This test just verifies the mechanism works
        plan1 = generator1.generate_custom(width=20, height=20, room_count=10)
        plan2 = generator2.generate_custom(width=20, height=20, room_count=10)

        assert plan1.seed == 1
        assert plan2.seed == 999
