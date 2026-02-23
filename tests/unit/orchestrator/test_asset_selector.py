"""
Tests for Asset Selector

Tests asset selection and matching functionality.
"""

import pytest
from unittest.mock import MagicMock
from lib.orchestrator.asset_selector import (
    AssetSelector,
    AssetCandidate,
    SelectionStrategy,
    SelectionResult,
    ScoringWeights,
    select_assets,
    get_mock_candidates,
)
from lib.orchestrator.types import AssetRequirement
from lib.orchestrator.requirement_resolver import ResolvedRequirement


class TestAssetCandidate:
    """Tests for AssetCandidate dataclass."""

    def test_create_default(self):
        """Test creating AssetCandidate with defaults."""
        candidate = AssetCandidate()
        assert candidate.asset_id == ""
        assert candidate.score == 0.0
        assert candidate.tags == []

    def test_create_with_values(self):
        """Test creating AssetCandidate with values."""
        candidate = AssetCandidate(
            asset_id="chair_01",
            asset_path="/assets/furniture/chair_01.blend",
            score=0.95,
            tags=["style", "category"],
        )
        assert candidate.asset_id == "chair_01"
        assert candidate.score == 0.95
        assert "style" in candidate.tags

    def test_to_dict(self):
        """Test AssetCandidate serialization."""
        candidate = AssetCandidate(asset_id="test", score=0.8)
        result = candidate.to_dict()
        assert result["asset_id"] == "test"
        assert result["score"] == 0.8


class TestSelectionStrategy:
    """Tests for SelectionStrategy enum."""

    def test_strategy_values(self):
        """Test SelectionStrategy enum values."""
        assert SelectionStrategy.BEST_MATCH.value == "best_match"
        assert SelectionStrategy.DIVERSE.value == "diverse"
        assert SelectionStrategy.SIMILAR.value == "similar"
        assert SelectionStrategy.RANDOM.value == "random"
        assert SelectionStrategy.WEIGHTED.value == "weighted"


class TestSelectionResult:
    """Tests for SelectionResult dataclass."""

    def test_create_default(self):
        """Test creating SelectionResult with defaults."""
        result = SelectionResult()
        assert result.selection is None
        assert result.candidates == []
        assert result.warnings == []
        assert result.success is False

    def test_success_property(self):
        """Test success property."""
        result = SelectionResult()
        assert result.success is False
        # When selection is set, success is True (tested via actual selection)


class TestScoringWeights:
    """Tests for ScoringWeights dataclass."""

    def test_create_default(self):
        """Test creating ScoringWeights with defaults."""
        weights = ScoringWeights()
        assert weights.category_match == 1.0
        assert weights.subcategory_match == 0.5
        assert weights.style_match == 0.3

    def test_create_with_values(self):
        """Test creating ScoringWeights with custom values."""
        weights = ScoringWeights(
            category_match=2.0,
            style_match=0.5,
        )
        assert weights.category_match == 2.0
        assert weights.style_match == 0.5


class TestAssetSelector:
    """Tests for AssetSelector class."""

    def test_init(self):
        """Test AssetSelector initialization."""
        selector = AssetSelector()
        assert selector is not None
        assert selector.strategy == SelectionStrategy.BEST_MATCH

    def test_init_with_strategy(self):
        """Test AssetSelector with custom strategy."""
        selector = AssetSelector(strategy=SelectionStrategy.DIVERSE)
        assert selector.strategy == SelectionStrategy.DIVERSE

    def test_register_candidates(self):
        """Test registering candidates."""
        selector = AssetSelector()
        candidates = get_mock_candidates()
        selector.register_candidates(candidates)
        # Should not raise

    def test_add_candidate(self):
        """Test adding single candidate."""
        selector = AssetSelector()
        candidate = AssetCandidate(asset_id="test", category="furniture")
        selector.add_candidate(candidate)
        # Should not raise

    def test_select_single_asset(self):
        """Test selecting a single asset."""
        selector = AssetSelector()
        selector.register_candidates(get_mock_candidates())
        requirement = AssetRequirement(
            requirement_id="req_01",
            category="furniture",
            subcategory="sofa",
        )
        result = selector.select(requirement)
        assert isinstance(result, SelectionResult)
        assert result.requirement == requirement

    def test_select_no_candidates(self):
        """Test selection with no matching candidates."""
        selector = AssetSelector()
        requirement = AssetRequirement(
            requirement_id="req_01",
            category="nonexistent_category",
        )
        result = selector.select(requirement)
        assert result.success is False
        assert len(result.warnings) > 0

    def test_select_best_match_strategy(self):
        """Test BEST_MATCH strategy selects highest score."""
        selector = AssetSelector(strategy=SelectionStrategy.BEST_MATCH)
        selector.register_candidates(get_mock_candidates())
        requirement = AssetRequirement(
            requirement_id="req_01",
            category="furniture",
        )
        result = selector.select(requirement)
        # Should succeed with furniture candidates
        assert result.success is True
        # Best match should have highest score
        if result.candidates:
            assert result.candidates[0].score >= result.candidates[-1].score

    def test_select_with_style_constraints(self):
        """Test selection with style constraints."""
        selector = AssetSelector()
        selector.register_candidates(get_mock_candidates())
        requirement = AssetRequirement(
            requirement_id="req_01",
            category="furniture",
            style_constraints=["modern"],
        )
        result = selector.select(requirement)
        assert isinstance(result, SelectionResult)


class TestSelectAssetsFunction:
    """Tests for select_assets convenience function."""

    def test_select_assets_basic(self):
        """Test basic asset selection."""
        requirement = AssetRequirement(
            requirement_id="req_01",
            category="furniture",
        )
        resolved = ResolvedRequirement(requirement=requirement)
        candidates = get_mock_candidates()
        results = select_assets([resolved], candidates)
        assert isinstance(results, list)


class TestAssetSelectorEdgeCases:
    """Edge case tests for AssetSelector."""

    def test_empty_candidates(self):
        """Test selection with empty candidates."""
        selector = AssetSelector()
        selector.register_candidates([])
        requirement = AssetRequirement(
            requirement_id="req_01",
            category="furniture",
        )
        result = selector.select(requirement)
        assert result.success is False

    def test_multiple_selections(self):
        """Test multiple selections track diversity."""
        selector = AssetSelector(strategy=SelectionStrategy.DIVERSE)
        selector.register_candidates(get_mock_candidates())

        requirement1 = AssetRequirement(
            requirement_id="req_01",
            category="furniture",
        )
        result1 = selector.select(requirement1)

        requirement2 = AssetRequirement(
            requirement_id="req_02",
            category="furniture",
        )
        result2 = selector.select(requirement2)

        # Both should succeed
        assert result1.success is True
        assert result2.success is True

    def test_subcategory_filtering(self):
        """Test that subcategory filtering works."""
        selector = AssetSelector()
        selector.register_candidates(get_mock_candidates())

        # Request specific subcategory
        requirement = AssetRequirement(
            requirement_id="req_01",
            category="furniture",
            subcategory="chair",
        )
        result = selector.select(requirement)
        # Should find office chair
        assert result.success is True
