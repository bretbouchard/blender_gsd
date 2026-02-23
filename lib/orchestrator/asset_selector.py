"""
Asset Selector

Selects best matching assets from vault for requirements.
Scores and ranks candidates based on multiple criteria.

Implements REQ-SO-03: Asset Selection Engine.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import math

from .types import AssetRequirement, AssetSelection
from .requirement_resolver import ResolvedRequirement


class SelectionStrategy(Enum):
    """Asset selection strategy."""
    BEST_MATCH = "best_match"       # Highest score wins
    DIVERSE = "diverse"              # Maximize variety
    SIMILAR = "similar"              # Minimize variation
    RANDOM = "random"                # Random from top N
    WEIGHTED = "weighted"            # Weighted random from top N


@dataclass
class AssetCandidate:
    """
    Candidate asset for selection.

    Attributes:
        asset_id: Asset identifier
        asset_path: Path to asset file
        category: Asset category
        subcategory: Asset subcategory
        tags: Asset tags
        style: Asset style classification
        dimensions: Asset dimensions (width, height, depth)
        quality_score: Base quality score
        metadata: Additional metadata
        score: Computed selection score
    """
    asset_id: str = ""
    asset_path: str = ""
    category: str = ""
    subcategory: str = ""
    tags: List[str] = field(default_factory=list)
    style: str = ""
    dimensions: Optional[tuple] = None
    quality_score: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "asset_id": self.asset_id,
            "asset_path": self.asset_path,
            "category": self.category,
            "subcategory": self.subcategory,
            "tags": self.tags,
            "style": self.style,
            "dimensions": list(self.dimensions) if self.dimensions else None,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
            "score": self.score,
        }


@dataclass
class SelectionResult:
    """
    Result of asset selection.

    Attributes:
        selection: Selected asset (None if none found)
        candidates: All considered candidates
        requirement: Source requirement
        warnings: Selection warnings
    """
    selection: Optional[AssetSelection] = None
    candidates: List[AssetCandidate] = field(default_factory=list)
    requirement: Optional[AssetRequirement] = None
    warnings: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if selection succeeded."""
        return self.selection is not None


@dataclass
class ScoringWeights:
    """
    Weights for scoring criteria.

    Attributes:
        category_match: Weight for exact category match
        subcategory_match: Weight for subcategory match
        style_match: Weight for style match
        tag_overlap: Weight for tag overlap
        size_fit: Weight for size fit
        quality: Weight for quality score
        diversity: Weight for diversity bonus
    """
    category_match: float = 1.0
    subcategory_match: float = 0.5
    style_match: float = 0.3
    tag_overlap: float = 0.2
    size_fit: float = 0.15
    quality: float = 0.1
    diversity: float = 0.1


class AssetSelector:
    """
    Selects best assets for requirements.

    Scores candidates based on multiple criteria and selects
    the best match.

    Usage:
        selector = AssetSelector()
        selector.register_candidates(candidates)
        result = selector.select(requirement)
    """

    def __init__(
        self,
        strategy: SelectionStrategy = SelectionStrategy.BEST_MATCH,
        weights: Optional[ScoringWeights] = None,
    ):
        """
        Initialize asset selector.

        Args:
            strategy: Selection strategy
            weights: Custom scoring weights
        """
        self.strategy = strategy
        self.weights = weights or ScoringWeights()
        self._candidates: List[AssetCandidate] = []
        self._selected_ids: List[str] = []

    def register_candidates(self, candidates: List[AssetCandidate]) -> None:
        """
        Register candidates for selection.

        Args:
            candidates: List of asset candidates
        """
        self._candidates = candidates

    def add_candidate(self, candidate: AssetCandidate) -> None:
        """Add single candidate."""
        self._candidates.append(candidate)

    def select(
        self,
        requirement: AssetRequirement,
        scene_style: str = "photorealistic",
    ) -> SelectionResult:
        """
        Select best asset for requirement.

        Args:
            requirement: Asset requirement
            scene_style: Overall scene style

        Returns:
            SelectionResult with selected asset
        """
        result = SelectionResult(requirement=requirement)

        # Filter candidates by category
        candidates = [
            c for c in self._candidates
            if c.category == requirement.category
        ]

        if not candidates:
            result.warnings.append(
                f"No candidates found for category: {requirement.category}"
            )
            return result

        # Further filter by subcategory if specified
        if requirement.subcategory:
            subcategory_match = [
                c for c in candidates
                if c.subcategory == requirement.subcategory
            ]
            if subcategory_match:
                candidates = subcategory_match
            else:
                result.warnings.append(
                    f"No exact subcategory match for: {requirement.subcategory}"
                )

        # Score all candidates
        for candidate in candidates:
            candidate.score = self._compute_score(
                candidate, requirement, scene_style
            )

        # Sort by score
        candidates.sort(key=lambda c: c.score, reverse=True)
        result.candidates = candidates

        # Select based on strategy
        selected = self._apply_strategy(candidates, requirement)

        if selected:
            result.selection = AssetSelection(
                requirement_id=requirement.requirement_id,
                asset_id=selected.asset_id,
                asset_path=selected.asset_path,
                scale_factor=self._compute_scale_factor(selected, requirement),
                priority_score=selected.score,
                alternatives_considered=[c.asset_id for c in candidates[:5]],
            )
            self._selected_ids.append(selected.asset_id)
        else:
            result.warnings.append("No suitable asset found")

        return result

    def select_all(
        self,
        requirements: List[ResolvedRequirement],
        scene_style: str = "photorealistic",
    ) -> List[SelectionResult]:
        """
        Select assets for all requirements.

        Args:
            requirements: List of resolved requirements
            scene_style: Overall scene style

        Returns:
            List of SelectionResult
        """
        results = []

        for resolved in requirements:
            result = self.select(resolved.requirement, scene_style)
            results.append(result)

        return results

    def _compute_score(
        self,
        candidate: AssetCandidate,
        requirement: AssetRequirement,
        scene_style: str,
    ) -> float:
        """Compute selection score for candidate."""
        score = 0.0

        # Category match (already filtered, but weight it)
        if candidate.category == requirement.category:
            score += self.weights.category_match

        # Subcategory match
        if requirement.subcategory and candidate.subcategory == requirement.subcategory:
            score += self.weights.subcategory_match

        # Style match
        if candidate.style and candidate.style == scene_style:
            score += self.weights.style_match

        # Tag overlap
        if requirement.style_constraints and candidate.tags:
            overlap = len(set(requirement.style_constraints) & set(candidate.tags))
            max_overlap = max(len(requirement.style_constraints), 1)
            score += (overlap / max_overlap) * self.weights.tag_overlap

        # Size fit
        if requirement.size_constraints and candidate.dimensions:
            fit_score = self._compute_size_fit(
                candidate.dimensions,
                requirement.size_constraints,
            )
            score += fit_score * self.weights.size_fit

        # Quality score
        score += candidate.quality_score * self.weights.quality

        # Diversity bonus
        if candidate.asset_id not in self._selected_ids:
            score += self.weights.diversity

        return score

    def _compute_size_fit(
        self,
        dimensions: tuple,
        constraints: tuple,
    ) -> float:
        """Compute size fit score (0-1)."""
        if len(dimensions) < 3 or len(constraints) < 2:
            return 0.5

        # Use volume as proxy for size
        volume = dimensions[0] * dimensions[1] * dimensions[2]
        min_size, max_size = constraints

        # Estimate volume from size constraints
        min_vol = min_size ** 3
        max_vol = max_size ** 3

        if min_vol <= volume <= max_vol:
            return 1.0  # Perfect fit

        # Penalize based on distance from range
        if volume < min_vol:
            return max(0, 1 - (min_vol - volume) / min_vol)
        else:
            return max(0, 1 - (volume - max_vol) / max_vol)

    def _compute_scale_factor(
        self,
        candidate: AssetCandidate,
        requirement: AssetRequirement,
    ) -> float:
        """Compute scale factor to apply to asset."""
        if not requirement.size_constraints or not candidate.dimensions:
            return 1.0

        min_size, max_size = requirement.size_constraints
        target_size = (min_size + max_size) / 2

        # Use largest dimension
        asset_size = max(candidate.dimensions)

        if asset_size > 0:
            return target_size / asset_size
        return 1.0

    def _apply_strategy(
        self,
        candidates: List[AssetCandidate],
        requirement: AssetRequirement,
    ) -> Optional[AssetCandidate]:
        """Apply selection strategy to candidates."""
        if not candidates:
            return None

        if self.strategy == SelectionStrategy.BEST_MATCH:
            return candidates[0]

        elif self.strategy == SelectionStrategy.DIVERSE:
            # Prefer assets not yet selected
            for c in candidates:
                if c.asset_id not in self._selected_ids:
                    return c
            return candidates[0]

        elif self.strategy == SelectionStrategy.RANDOM:
            import random
            top_n = min(3, len(candidates))
            return random.choice(candidates[:top_n])

        elif self.strategy == SelectionStrategy.WEIGHTED:
            import random
            # Weighted random from top 5
            top_n = min(5, len(candidates))
            weights = [c.score for c in candidates[:top_n]]
            total = sum(weights)
            if total > 0:
                normalized = [w / total for w in weights]
                return random.choices(candidates[:top_n], weights=normalized)[0]
            return candidates[0]

        return candidates[0]


def select_assets(
    requirements: List[ResolvedRequirement],
    candidates: List[AssetCandidate],
    scene_style: str = "photorealistic",
    strategy: SelectionStrategy = SelectionStrategy.BEST_MATCH,
) -> List[SelectionResult]:
    """
    Convenience function to select assets for requirements.

    Args:
        requirements: List of resolved requirements
        candidates: Available asset candidates
        scene_style: Scene style
        strategy: Selection strategy

    Returns:
        List of SelectionResult
    """
    selector = AssetSelector(strategy=strategy)
    selector.register_candidates(candidates)
    return selector.select_all(requirements, scene_style)


# =============================================================================
# MOCK ASSET CATALOG (for testing without asset vault)
# =============================================================================

MOCK_ASSET_CATALOG: List[AssetCandidate] = [
    AssetCandidate(
        asset_id="sofa_modern_01",
        asset_path="/assets/furniture/sofa_modern_01.blend",
        category="furniture",
        subcategory="sofa",
        tags=["modern", "fabric", "3-seater"],
        style="photorealistic",
        dimensions=(2.0, 0.9, 0.8),
        quality_score=0.9,
    ),
    AssetCandidate(
        asset_id="sofa_classic_01",
        asset_path="/assets/furniture/sofa_classic_01.blend",
        category="furniture",
        subcategory="sofa",
        tags=["classic", "leather", "3-seater"],
        style="photorealistic",
        dimensions=(2.2, 1.0, 0.85),
        quality_score=0.85,
    ),
    AssetCandidate(
        asset_id="chair_office_01",
        asset_path="/assets/furniture/chair_office_01.blend",
        category="furniture",
        subcategory="chair",
        tags=["office", "modern", "swivel"],
        style="photorealistic",
        dimensions=(0.7, 0.7, 1.2),
        quality_score=0.8,
    ),
    AssetCandidate(
        asset_id="table_coffee_01",
        asset_path="/assets/furniture/table_coffee_01.blend",
        category="furniture",
        subcategory="coffee_table",
        tags=["wood", "modern", "rectangular"],
        style="photorealistic",
        dimensions=(1.2, 0.6, 0.45),
        quality_score=0.85,
    ),
    AssetCandidate(
        asset_id="light_ceiling_01",
        asset_path="/assets/lighting/ceiling_light_01.blend",
        category="lighting",
        subcategory="ceiling_light",
        tags=["modern", "led", "dimmable"],
        style="photorealistic",
        dimensions=(0.5, 0.5, 0.15),
        quality_score=0.75,
    ),
]


def get_mock_candidates() -> List[AssetCandidate]:
    """Get mock asset catalog for testing."""
    return MOCK_ASSET_CATALOG.copy()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "SelectionStrategy",
    "AssetCandidate",
    "SelectionResult",
    "ScoringWeights",
    "AssetSelector",
    "select_assets",
    "MOCK_ASSET_CATALOG",
    "get_mock_candidates",
]
