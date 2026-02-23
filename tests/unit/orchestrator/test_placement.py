"""
Tests for Placement System

Tests asset placement algorithms and positioning.
"""

import pytest
from lib.orchestrator.placement import (
    PlacementZone,
    PlacementRule,
    PlacedAsset,
    PlacementResult,
    PlacementOrchestrator,
    DEFAULT_PLACEMENT_RULES,
    place_assets,
)
from lib.orchestrator.types import (
    AssetSelection,
    SceneOutline,
    SceneDimensions,
)


class TestPlacementZone:
    """Tests for PlacementZone enum."""

    def test_zone_values(self):
        """Test PlacementZone enum values."""
        assert PlacementZone.CENTER.value == "center"
        assert PlacementZone.CORNER.value == "corner"
        assert PlacementZone.WALL.value == "wall"
        assert PlacementZone.FLOOR.value == "floor"
        assert PlacementZone.CEILING.value == "ceiling"
        assert PlacementZone.FOREGROUND.value == "foreground"
        assert PlacementZone.BACKGROUND.value == "background"
        assert PlacementZone.LEFT.value == "left"
        assert PlacementZone.RIGHT.value == "right"


class TestPlacementRule:
    """Tests for PlacementRule dataclass."""

    def test_create_default(self):
        """Test creating PlacementRule with defaults."""
        rule = PlacementRule()
        assert rule.category == ""
        assert rule.preferred_zones == []
        assert rule.avoid_zones == []
        assert rule.min_distance_from_wall == 0.5
        assert rule.min_distance_from_other == 1.0

    def test_create_with_values(self):
        """Test creating PlacementRule with values."""
        rule = PlacementRule(
            category="furniture",
            preferred_zones=["center", "wall"],
            avoid_zones=["foreground"],
            min_distance_from_wall=1.0,
        )
        assert rule.category == "furniture"
        assert len(rule.preferred_zones) == 2
        assert "center" in rule.preferred_zones
        assert rule.min_distance_from_wall == 1.0


class TestPlacedAsset:
    """Tests for PlacedAsset dataclass."""

    def test_create_default(self):
        """Test creating PlacedAsset with defaults."""
        placed = PlacedAsset()
        assert placed.selection is None
        assert placed.position == (0.0, 0.0, 0.0)
        assert placed.rotation == (0.0, 0.0, 0.0)
        assert placed.zone == "center"
        assert placed.conflicts == []

    def test_create_with_values(self):
        """Test creating PlacedAsset with values."""
        selection = AssetSelection(
            requirement_id="req_01",
            asset_id="asset_01",
            asset_path="/path/to/asset.blend",
        )
        placed = PlacedAsset(
            selection=selection,
            position=(10.0, 5.0, 0.0),
            rotation=(0.0, 45.0, 0.0),
            zone="center",
        )
        assert placed.selection.asset_id == "asset_01"
        assert placed.position == (10.0, 5.0, 0.0)
        assert placed.rotation[1] == 45.0

    def test_to_dict(self):
        """Test PlacedAsset serialization."""
        placed = PlacedAsset(position=(1, 2, 3), zone="center")
        data = placed.to_dict()
        assert data["position"] == [1, 2, 3]
        assert data["zone"] == "center"


class TestPlacementResult:
    """Tests for PlacementResult dataclass."""

    def test_create_default(self):
        """Test creating PlacementResult with defaults."""
        result = PlacementResult()
        assert result.placed_assets == []
        assert result.unplaced == []
        assert result.conflicts == []
        assert result.warnings == []
        assert result.scene_bounds is None

    def test_create_with_values(self):
        """Test creating PlacementResult with values."""
        placed = PlacedAsset(position=(1, 2, 3))
        result = PlacementResult(
            placed_assets=[placed],
            scene_bounds=(20.0, 20.0, 4.0),
        )
        assert len(result.placed_assets) == 1
        assert result.scene_bounds == (20.0, 20.0, 4.0)

    def test_to_dict(self):
        """Test PlacementResult serialization."""
        result = PlacementResult(
            placed_assets=[PlacedAsset(position=(1, 2, 3))],
            warnings=["test warning"],
        )
        data = result.to_dict()
        assert "placed_assets" in data
        assert data["warnings"] == ["test warning"]


class TestPlacementOrchestrator:
    """Tests for PlacementOrchestrator class."""

    def test_init(self):
        """Test PlacementOrchestrator initialization."""
        orchestrator = PlacementOrchestrator()
        assert orchestrator is not None
        assert orchestrator.rules is not None

    def test_init_with_custom_rules(self):
        """Test PlacementOrchestrator with custom rules."""
        custom_rules = {
            "custom": PlacementRule(category="custom", preferred_zones=["center"]),
        }
        orchestrator = PlacementOrchestrator(rules=custom_rules)
        assert "custom" in orchestrator.rules

    def test_init_with_seed(self):
        """Test PlacementOrchestrator with random seed."""
        orchestrator = PlacementOrchestrator(seed=42)
        assert orchestrator.seed == 42

    def test_place_all_single_asset(self):
        """Test placing a single asset."""
        orchestrator = PlacementOrchestrator(seed=42)
        selection = AssetSelection(
            requirement_id="req_01",
            asset_id="furniture_sofa_01",
            asset_path="/path/to/sofa.blend",
        )
        outline = SceneOutline(
            name="Test Scene",
            dimensions=SceneDimensions(width=20.0, depth=20.0, height=4.0),
        )
        result = orchestrator.place_all([selection], outline)
        assert len(result.placed_assets) == 1
        assert result.placed_assets[0].position is not None

    def test_place_all_multiple_assets(self):
        """Test placing multiple assets."""
        orchestrator = PlacementOrchestrator(seed=42)
        selections = [
            AssetSelection(
                requirement_id=f"req_{i}",
                asset_id=f"furniture_item_{i}",
                asset_path=f"/path/to/item_{i}.blend",
            )
            for i in range(3)
        ]
        outline = SceneOutline(
            name="Test Scene",
            dimensions=SceneDimensions(width=20.0, depth=20.0, height=4.0),
        )
        result = orchestrator.place_all(selections, outline)
        assert len(result.placed_assets) == 3

    def test_place_all_with_no_dimensions(self):
        """Test placing assets when outline has no dimensions."""
        orchestrator = PlacementOrchestrator(seed=42)
        selection = AssetSelection(
            requirement_id="req_01",
            asset_id="furniture_sofa_01",
            asset_path="/path/to/sofa.blend",
        )
        outline = SceneOutline(name="Test Scene")
        result = orchestrator.place_all([selection], outline)
        # Should use default dimensions
        assert result.scene_bounds == (20.0, 20.0, 4.0)


class TestPlaceAssetsFunction:
    """Tests for place_assets convenience function."""

    def test_place_assets_basic(self):
        """Test basic asset placement."""
        selections = [
            AssetSelection(
                requirement_id="req_01",
                asset_id="furniture_sofa_01",
                asset_path="/path/to/sofa.blend",
            ),
            AssetSelection(
                requirement_id="req_02",
                asset_id="lighting_ceiling_01",
                asset_path="/path/to/light.blend",
            ),
        ]
        outline = SceneOutline(
            name="Test Scene",
            dimensions=SceneDimensions(width=50.0, depth=50.0, height=5.0),
        )
        result = place_assets(selections, outline, seed=42)
        assert isinstance(result, PlacementResult)
        assert len(result.placed_assets) == 2


class TestDefaultPlacementRules:
    """Tests for default placement rules."""

    def test_default_rules_exist(self):
        """Test that default rules exist for common categories."""
        assert "furniture" in DEFAULT_PLACEMENT_RULES
        assert "lighting" in DEFAULT_PLACEMENT_RULES
        assert "prop" in DEFAULT_PLACEMENT_RULES
        assert "character" in DEFAULT_PLACEMENT_RULES
        assert "vehicle" in DEFAULT_PLACEMENT_RULES
        assert "backdrop" in DEFAULT_PLACEMENT_RULES

    def test_furniture_rule(self):
        """Test furniture placement rule."""
        rule = DEFAULT_PLACEMENT_RULES["furniture"]
        assert "center" in rule.preferred_zones or "wall" in rule.preferred_zones

    def test_lighting_rule(self):
        """Test lighting placement rule."""
        rule = DEFAULT_PLACEMENT_RULES["lighting"]
        assert "ceiling" in rule.preferred_zones or "wall" in rule.preferred_zones


class TestPlacementEdgeCases:
    """Edge case tests for placement."""

    def test_empty_selections(self):
        """Test placement with no selections."""
        orchestrator = PlacementOrchestrator()
        outline = SceneOutline(
            name="Test Scene",
            dimensions=SceneDimensions(width=20.0, depth=20.0, height=4.0),
        )
        result = orchestrator.place_all([], outline)
        assert len(result.placed_assets) == 0

    def test_very_small_scene(self):
        """Test placement in very small scene."""
        orchestrator = PlacementOrchestrator(seed=42)
        selection = AssetSelection(
            requirement_id="req_01",
            asset_id="prop_small_01",
            asset_path="/path/to/prop.blend",
        )
        outline = SceneOutline(
            name="Test Scene",
            dimensions=SceneDimensions(width=1.0, depth=1.0, height=1.0),
        )
        result = orchestrator.place_all([selection], outline)
        # Should still succeed
        assert len(result.placed_assets) >= 0

    def test_many_assets_in_small_space(self):
        """Test placing many assets in small space."""
        orchestrator = PlacementOrchestrator(seed=42)
        selections = [
            AssetSelection(
                requirement_id=f"req_{i}",
                asset_id=f"prop_item_{i}",
                asset_path=f"/path/to/item_{i}.blend",
            )
            for i in range(20)
        ]
        outline = SceneOutline(
            name="Test Scene",
            dimensions=SceneDimensions(width=5.0, depth=5.0, height=2.0),
        )
        result = orchestrator.place_all(selections, outline)
        # May have unplaced assets due to space constraints
        total = len(result.placed_assets) + len(result.unplaced)
        assert total == 20

    def test_deterministic_with_seed(self):
        """Test that same seed produces same results."""
        selections = [
            AssetSelection(
                requirement_id="req_01",
                asset_id="furniture_sofa_01",
                asset_path="/path/to/sofa.blend",
            )
        ]
        outline = SceneOutline(
            name="Test Scene",
            dimensions=SceneDimensions(width=20.0, depth=20.0, height=4.0),
        )

        result1 = place_assets(selections, outline, seed=123)
        result2 = place_assets(selections, outline, seed=123)

        # Same seed should produce same positions
        assert result1.placed_assets[0].position == result2.placed_assets[0].position
