"""
Requirement Resolver

Analyzes scene outlines and determines required assets.
Extracts implicit requirements from scene configuration.

Implements REQ-SO-02: Requirement Resolver.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
from enum import Enum

from .types import (
    SceneOutline,
    AssetRequirement,
    SceneType,
)


class RequirementSource(Enum):
    """Source of a requirement."""
    EXPLICIT = "explicit"      # Directly specified in outline
    IMPLICIT = "implicit"      # Inferred from scene type/style
    DERIVED = "derived"        # Computed from other requirements
    DEFAULT = "default"        # Default requirement for category


@dataclass
class ResolvedRequirement:
    """
    Resolved requirement with source tracking.

    Attributes:
        requirement: The asset requirement
        source: Where requirement came from
        confidence: Confidence level (0-1)
        dependencies: IDs of dependent requirements
    """
    requirement: AssetRequirement
    source: str = "explicit"
    confidence: float = 1.0
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requirement": self.requirement.to_dict(),
            "source": self.source,
            "confidence": self.confidence,
            "dependencies": self.dependencies,
        }


@dataclass
class ResolutionResult:
    """
    Result of requirement resolution.

    Attributes:
        requirements: All resolved requirements
        conflicts: Conflicting requirements found
        warnings: Resolution warnings
        metadata: Resolution metadata
    """
    requirements: List[ResolvedRequirement] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requirements": [r.to_dict() for r in self.requirements],
            "conflicts": self.conflicts,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }

    def get_requirements_by_category(self, category: str) -> List[AssetRequirement]:
        """Get all requirements for a category."""
        return [
            r.requirement
            for r in self.requirements
            if r.requirement.category == category
        ]


# =============================================================================
# IMPLICIT REQUIREMENT RULES
# =============================================================================

# Scene type → implicit requirements
SCENE_TYPE_REQUIREMENTS: Dict[str, List[Dict[str, Any]]] = {
    "interior": [
        {"category": "lighting", "subcategory": "ceiling_light", "quantity": 1, "source": "implicit"},
        {"category": "flooring", "subcategory": "default", "quantity": 1, "source": "implicit"},
        {"category": "walls", "subcategory": "interior", "quantity": 4, "source": "implicit"},
    ],
    "exterior": [
        {"category": "terrain", "subcategory": "ground", "quantity": 1, "source": "implicit"},
        {"category": "sky", "subcategory": "hdri", "quantity": 1, "source": "implicit"},
    ],
    "urban": [
        {"category": "road", "subcategory": "asphalt", "quantity": 1, "source": "implicit"},
        {"category": "sidewalk", "subcategory": "concrete", "quantity": 2, "source": "implicit"},
        {"category": "street_light", "subcategory": "standard", "quantity": 4, "source": "implicit"},
    ],
    "product": [
        {"category": "surface", "subcategory": "platform", "quantity": 1, "source": "implicit"},
        {"category": "backdrop", "subcategory": "seamless", "quantity": 1, "source": "implicit"},
    ],
    "portrait": [
        {"category": "backdrop", "subcategory": "studio", "quantity": 1, "source": "implicit"},
        {"category": "lighting", "subcategory": "studio", "quantity": 3, "source": "implicit"},
    ],
    "environment": [
        {"category": "terrain", "subcategory": "ground", "quantity": 1, "source": "implicit"},
        {"category": "sky", "subcategory": "hdri", "quantity": 1, "source": "implicit"},
        {"category": "atmosphere", "subcategory": "fog", "quantity": 1, "source": "implicit"},
    ],
}

# Style → implicit requirements
STYLE_REQUIREMENTS: Dict[str, List[Dict[str, Any]]] = {
    "photorealistic": [
        {"category": "post_processing", "subcategory": "color_grading", "source": "implicit"},
    ],
    "sci_fi": [
        {"category": "effects", "subcategory": "glow", "source": "implicit"},
        {"category": "effects", "subcategory": "hologram", "source": "implicit"},
    ],
    "retro": [
        {"category": "post_processing", "subcategory": "film_grain", "source": "implicit"},
        {"category": "post_processing", "subcategory": "vignette", "source": "implicit"},
    ],
}


class RequirementResolver:
    """
    Resolves all requirements from scene outline.

    Analyzes outline, adds implicit requirements, and resolves conflicts.

    Usage:
        resolver = RequirementResolver()
        result = resolver.resolve(outline)
        for req in result.requirements:
            print(f"{req.requirement.category}: {req.source}")
    """

    def __init__(self):
        """Initialize requirement resolver."""
        self._requirement_counter = 0

    def resolve(self, outline: SceneOutline) -> ResolutionResult:
        """
        Resolve all requirements from outline.

        Args:
            outline: Scene outline to resolve

        Returns:
            ResolutionResult with all requirements
        """
        result = ResolutionResult()
        seen_categories: Set[str] = set()

        # Add explicit requirements
        for req in outline.asset_requirements:
            if not req.requirement_id:
                req.requirement_id = self._generate_id()

            result.requirements.append(ResolvedRequirement(
                requirement=req,
                source="explicit",
                confidence=1.0,
            ))
            seen_categories.add(req.category)

        # Add implicit requirements from scene type
        self._add_scene_type_requirements(
            outline.scene_type,
            result,
            seen_categories,
        )

        # Add implicit requirements from style
        self._add_style_requirements(
            outline.style,
            result,
            seen_categories,
        )

        # Add derived requirements from lighting config
        if outline.lighting:
            self._add_lighting_requirements(outline.lighting, result, seen_categories)

        # Resolve conflicts
        self._resolve_conflicts(result)

        # Add metadata
        result.metadata = {
            "scene_type": outline.scene_type,
            "style": outline.style,
            "explicit_count": len(outline.asset_requirements),
            "total_count": len(result.requirements),
        }

        return result

    def _generate_id(self) -> str:
        """Generate unique requirement ID."""
        self._requirement_counter += 1
        return f"req_{self._requirement_counter:04d}"

    def _add_scene_type_requirements(
        self,
        scene_type: str,
        result: ResolutionResult,
        seen_categories: Set[str],
    ) -> None:
        """Add implicit requirements based on scene type."""
        implicit_reqs = SCENE_TYPE_REQUIREMENTS.get(scene_type, [])

        for req_data in implicit_reqs:
            category = req_data.get("category", "")

            # Skip if explicit requirement exists for category
            if category in seen_categories:
                continue

            requirement = AssetRequirement(
                requirement_id=self._generate_id(),
                category=category,
                subcategory=req_data.get("subcategory", ""),
                quantity=req_data.get("quantity", 1),
                priority="preferred",
                metadata={"implicit": True},
            )

            result.requirements.append(ResolvedRequirement(
                requirement=requirement,
                source="implicit",
                confidence=0.8,
            ))

    def _add_style_requirements(
        self,
        style: str,
        result: ResolutionResult,
        seen_categories: Set[str],
    ) -> None:
        """Add implicit requirements based on style."""
        implicit_reqs = STYLE_REQUIREMENTS.get(style, [])

        for req_data in implicit_reqs:
            category = req_data.get("category", "")

            # Skip if explicit requirement exists for category
            if category in seen_categories:
                continue

            requirement = AssetRequirement(
                requirement_id=self._generate_id(),
                category=category,
                subcategory=req_data.get("subcategory", ""),
                quantity=req_data.get("quantity", 1),
                priority="optional",
                metadata={"style_based": True},
            )

            result.requirements.append(ResolvedRequirement(
                requirement=requirement,
                source="implicit",
                confidence=0.6,
            ))

    def _add_lighting_requirements(
        self,
        lighting: Any,
        result: ResolutionResult,
        seen_categories: Set[str],
    ) -> None:
        """Add derived requirements from lighting configuration."""
        # Studio lights
        if lighting.use_studio_lights and "lighting" not in seen_categories:
            requirement = AssetRequirement(
                requirement_id=self._generate_id(),
                category="lighting",
                subcategory="studio",
                description=f"Studio lighting preset: {lighting.studio_preset}",
                quantity=3,  # Typical 3-point setup
                priority="required",
                metadata={
                    "preset": lighting.studio_preset,
                    "derived": True,
                },
            )

            result.requirements.append(ResolvedRequirement(
                requirement=requirement,
                source="derived",
                confidence=0.9,
            ))

        # Natural light
        if lighting.use_natural_light and "sun" not in seen_categories:
            requirement = AssetRequirement(
                requirement_id=self._generate_id(),
                category="lighting",
                subcategory="sun",
                description=f"Natural light: {lighting.time_of_day}",
                quantity=1,
                priority="required",
                metadata={
                    "time_of_day": lighting.time_of_day,
                    "weather": lighting.weather,
                    "derived": True,
                },
            )

            result.requirements.append(ResolvedRequirement(
                requirement=requirement,
                source="derived",
                confidence=0.9,
            ))

        # Atmospherics
        for atm in lighting.atmospherics:
            requirement = AssetRequirement(
                requirement_id=self._generate_id(),
                category="atmosphere",
                subcategory=atm,
                description=f"Atmospheric effect: {atm}",
                quantity=1,
                priority="optional",
                metadata={"atmospheric": True},
            )

            result.requirements.append(ResolvedRequirement(
                requirement=requirement,
                source="derived",
                confidence=0.7,
            ))

    def _resolve_conflicts(self, result: ResolutionResult) -> None:
        """Detect and resolve requirement conflicts."""
        # Group by category
        by_category: Dict[str, List[ResolvedRequirement]] = {}
        for req in result.requirements:
            cat = req.requirement.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(req)

        # Check for conflicts
        for category, reqs in by_category.items():
            if len(reqs) > 1:
                # Multiple requirements for same category
                priorities = [r.requirement.priority for r in reqs]
                if "required" in priorities and "optional" in priorities:
                    result.warnings.append(
                        f"Category '{category}' has both required and optional requirements"
                    )

                # Keep highest priority
                explicit_count = sum(1 for r in reqs if r.source == "explicit")
                if explicit_count > 1:
                    result.conflicts.append(
                        f"Multiple explicit requirements for '{category}'"
                    )


def resolve_requirements(outline: SceneOutline) -> ResolutionResult:
    """
    Convenience function to resolve requirements.

    Args:
        outline: Scene outline to resolve

    Returns:
        ResolutionResult with all requirements
    """
    resolver = RequirementResolver()
    return resolver.resolve(outline)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RequirementSource",
    "ResolvedRequirement",
    "ResolutionResult",
    "RequirementResolver",
    "resolve_requirements",
    "SCENE_TYPE_REQUIREMENTS",
    "STYLE_REQUIREMENTS",
]
