"""
Placement Orchestrator

Coordinates placement of all selected assets in scene.
Handles spatial reasoning, collision avoidance, and composition.

Implements REQ-SO-04: Placement Orchestrator.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import math

from .types import (
    AssetSelection,
    SceneOutline,
    SceneDimensions,
)


class PlacementZone(Enum):
    """Placement zone within scene."""
    CENTER = "center"
    CORNER = "corner"
    WALL = "wall"
    FLOOR = "floor"
    CEILING = "ceiling"
    FOREGROUND = "foreground"
    BACKGROUND = "background"
    LEFT = "left"
    RIGHT = "right"
    CUSTOM = "custom"


@dataclass
class PlacementRule:
    """
    Rule for asset placement.

    Attributes:
        category: Asset category this rule applies to
        preferred_zones: Preferred placement zones
        avoid_zones: Zones to avoid
        min_distance_from_wall: Minimum distance from walls
        min_distance_from_other: Minimum distance from other assets
        alignment: Preferred alignment (center, wall, grid)
        random_offset: Maximum random offset to apply
    """
    category: str = ""
    preferred_zones: List[str] = field(default_factory=list)
    avoid_zones: List[str] = field(default_factory=list)
    min_distance_from_wall: float = 0.5
    min_distance_from_other: float = 1.0
    alignment: str = "center"
    random_offset: float = 0.3


@dataclass
class PlacedAsset:
    """
    Asset with computed placement.

    Attributes:
        selection: Source asset selection
        position: Final position (x, y, z)
        rotation: Final rotation (x, y, z) in degrees
        zone: Placement zone used
        conflicts: IDs of conflicting assets
        rule_applied: Rule that was applied
    """
    selection: Optional[AssetSelection] = None
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    zone: str = "center"
    conflicts: List[str] = field(default_factory=list)
    rule_applied: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selection": self.selection.to_dict() if self.selection else None,
            "position": list(self.position),
            "rotation": list(self.rotation),
            "zone": self.zone,
            "conflicts": self.conflicts,
            "rule_applied": self.rule_applied,
        }


@dataclass
class PlacementResult:
    """
    Result of placement orchestration.

    Attributes:
        placed_assets: All placed assets
        unplaced: Assets that couldn't be placed
        conflicts: Detected conflicts
        warnings: Placement warnings
        scene_bounds: Scene boundary used
    """
    placed_assets: List[PlacedAsset] = field(default_factory=list)
    unplaced: List[AssetSelection] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    scene_bounds: Optional[Tuple[float, float, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "placed_assets": [a.to_dict() for a in self.placed_assets],
            "unplaced": [s.to_dict() for s in self.unplaced],
            "conflicts": self.conflicts,
            "warnings": self.warnings,
            "scene_bounds": list(self.scene_bounds) if self.scene_bounds else None,
        }


# =============================================================================
# DEFAULT PLACEMENT RULES
# =============================================================================

DEFAULT_PLACEMENT_RULES: Dict[str, PlacementRule] = {
    "furniture": PlacementRule(
        category="furniture",
        preferred_zones=["center", "wall", "corner"],
        avoid_zones=["foreground", "background"],
        min_distance_from_wall=0.5,
        min_distance_from_other=0.8,
        alignment="wall",
    ),
    "lighting": PlacementRule(
        category="lighting",
        preferred_zones=["ceiling", "wall", "center"],
        avoid_zones=["floor"],
        min_distance_from_wall=0.3,
        min_distance_from_other=1.0,
        alignment="grid",
    ),
    "prop": PlacementRule(
        category="prop",
        preferred_zones=["foreground", "center"],
        avoid_zones=[],
        min_distance_from_wall=0.3,
        min_distance_from_other=0.3,
        alignment="random",
        random_offset=0.5,
    ),
    "character": PlacementRule(
        category="character",
        preferred_zones=["center", "foreground"],
        avoid_zones=["corner", "background"],
        min_distance_from_wall=1.0,
        min_distance_from_other=1.5,
        alignment="center",
    ),
    "vehicle": PlacementRule(
        category="vehicle",
        preferred_zones=["floor", "center"],
        avoid_zones=["corner"],
        min_distance_from_wall=2.0,
        min_distance_from_other=3.0,
        alignment="grid",
    ),
    "backdrop": PlacementRule(
        category="backdrop",
        preferred_zones=["background"],
        avoid_zones=["foreground", "center"],
        min_distance_from_wall=0.0,
        alignment="wall",
    ),
}


class PlacementOrchestrator:
    """
    Orchestrates placement of assets in scene.

    Applies placement rules, resolves conflicts, and ensures
    balanced composition.

    Usage:
        orchestrator = PlacementOrchestrator()
        result = orchestrator.place_all(selections, outline)
    """

    def __init__(
        self,
        rules: Optional[Dict[str, PlacementRule]] = None,
        seed: Optional[int] = None,
    ):
        """
        Initialize placement orchestrator.

        Args:
            rules: Custom placement rules
            seed: Random seed for reproducibility
        """
        self.rules = rules or DEFAULT_PLACEMENT_RULES
        self.seed = seed
        self._placed_positions: List[Tuple[float, float, float]] = []

        if seed is not None:
            import random
            random.seed(seed)

    def place_all(
        self,
        selections: List[AssetSelection],
        outline: SceneOutline,
    ) -> PlacementResult:
        """
        Place all selected assets in scene.

        Args:
            selections: Asset selections to place
            outline: Scene outline with dimensions

        Returns:
            PlacementResult with all placements
        """
        result = PlacementResult()

        # Get scene bounds
        if outline.dimensions:
            bounds = (
                outline.dimensions.width,
                outline.dimensions.depth,
                outline.dimensions.height,
            )
        else:
            bounds = (20.0, 20.0, 4.0)
        result.scene_bounds = bounds

        # Sort selections by priority (required first)
        sorted_selections = sorted(
            selections,
            key=lambda s: s.priority_score,
            reverse=True,
        )

        # Place each asset
        for selection in sorted_selections:
            placed = self._place_asset(selection, bounds, result)

            if placed:
                result.placed_assets.append(placed)
                self._placed_positions.append(placed.position)
            else:
                result.unplaced.append(selection)

        return result

    def _place_asset(
        self,
        selection: AssetSelection,
        bounds: Tuple[float, float, float],
        result: PlacementResult,
    ) -> Optional[PlacedAsset]:
        """Place single asset."""
        # Determine category from requirement (mock for now)
        category = self._infer_category(selection)

        # Get placement rule
        rule = self.rules.get(category, PlacementRule(category=category))

        # Find valid position
        position = self._find_position(rule, bounds, result)

        if position is None:
            return None

        # Calculate rotation
        rotation = self._calculate_rotation(rule, position, bounds)

        # Determine zone
        zone = self._determine_zone(position, bounds)

        return PlacedAsset(
            selection=selection,
            position=position,
            rotation=rotation,
            zone=zone,
            rule_applied=rule.category,
        )

    def _infer_category(self, selection: AssetSelection) -> str:
        """Infer asset category from selection."""
        # In real implementation, this would come from asset vault
        if "furniture" in selection.asset_id.lower():
            return "furniture"
        elif "light" in selection.asset_id.lower():
            return "lighting"
        elif "prop" in selection.asset_id.lower():
            return "prop"
        return "prop"

    def _find_position(
        self,
        rule: PlacementRule,
        bounds: Tuple[float, float, float],
        result: PlacementResult,
    ) -> Optional[Tuple[float, float, float]]:
        """Find valid position for asset."""
        width, depth, height = bounds
        max_attempts = 50

        for _ in range(max_attempts):
            # Generate candidate position
            import random

            # Choose zone
            if rule.preferred_zones:
                zone = random.choice(rule.preferred_zones)
            else:
                zone = "center"

            # Generate position based on zone
            x, y, z = self._zone_to_position(zone, bounds, rule)

            # Add random offset
            if rule.random_offset > 0:
                x += random.uniform(-rule.random_offset, rule.random_offset)
                y += random.uniform(-rule.random_offset, rule.random_offset)

            # Check bounds
            x = max(rule.min_distance_from_wall,
                    min(width - rule.min_distance_from_wall, x))
            y = max(rule.min_distance_from_wall,
                    min(depth - rule.min_distance_from_wall, y))

            # Check distance from other assets
            if self._check_clearance(x, y, z, rule.min_distance_from_other):
                return (x, y, z)

        result.warnings.append(
            f"Could not find valid position for category: {rule.category}"
        )
        return None

    def _zone_to_position(
        self,
        zone: str,
        bounds: Tuple[float, float, float],
        rule: PlacementRule,
    ) -> Tuple[float, float, float]:
        """Convert zone name to position."""
        width, depth, height = bounds
        margin = rule.min_distance_from_wall

        zone_positions = {
            "center": (width / 2, depth / 2, 0),
            "corner": (margin, margin, 0),
            "wall": (width / 2, margin, 0),
            "floor": (width / 2, depth / 2, 0),
            "ceiling": (width / 2, depth / 2, height - 0.3),
            "foreground": (width / 2, depth - margin, 0),
            "background": (width / 2, margin, 0),
            "left": (margin, depth / 2, 0),
            "right": (width - margin, depth / 2, 0),
        }

        return zone_positions.get(zone, (width / 2, depth / 2, 0))

    def _check_clearance(
        self,
        x: float,
        y: float,
        z: float,
        min_distance: float,
    ) -> bool:
        """Check if position has sufficient clearance."""
        for px, py, pz in self._placed_positions:
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            if dist < min_distance:
                return False
        return True

    def _calculate_rotation(
        self,
        rule: PlacementRule,
        position: Tuple[float, float, float],
        bounds: Tuple[float, float, float],
    ) -> Tuple[float, float, float]:
        """Calculate rotation for asset."""
        import random

        if rule.alignment == "wall":
            # Face away from nearest wall
            x, y, z = position
            width, depth, height = bounds

            # Find nearest wall
            dist_to_walls = [
                x,              # Left wall
                width - x,      # Right wall
                y,              # Back wall
                depth - y,      # Front wall
            ]
            nearest = dist_to_walls.index(min(dist_to_walls))

            rotations = [90, 270, 0, 180]  # Y rotations for each wall
            return (0, rotations[nearest], 0)

        elif rule.alignment == "center":
            # Face center of room
            return (0, 0, 0)

        elif rule.alignment == "random":
            return (0, random.uniform(0, 360), 0)

        return (0, 0, 0)

    def _determine_zone(
        self,
        position: Tuple[float, float, float],
        bounds: Tuple[float, float, float],
    ) -> str:
        """Determine zone name from position."""
        x, y, z = position
        width, depth, height = bounds

        # Check if on ceiling
        if z > height * 0.8:
            return "ceiling"

        # Check horizontal position
        x_norm = x / width
        y_norm = y / depth

        if x_norm < 0.25:
            return "left"
        elif x_norm > 0.75:
            return "right"
        elif y_norm < 0.25:
            return "background"
        elif y_norm > 0.75:
            return "foreground"
        else:
            return "center"


def place_assets(
    selections: List[AssetSelection],
    outline: SceneOutline,
    seed: Optional[int] = None,
) -> PlacementResult:
    """
    Convenience function to place assets.

    Args:
        selections: Asset selections to place
        outline: Scene outline
        seed: Random seed

    Returns:
        PlacementResult
    """
    orchestrator = PlacementOrchestrator(seed=seed)
    return orchestrator.place_all(selections, outline)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "PlacementZone",
    "PlacementRule",
    "PlacedAsset",
    "PlacementResult",
    "DEFAULT_PLACEMENT_RULES",
    "PlacementOrchestrator",
    "place_assets",
]
