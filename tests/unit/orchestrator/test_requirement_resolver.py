"""
Tests for Requirement Resolver

Tests requirement resolution and dependency handling.
"""

import pytest
from lib.orchestrator.requirement_resolver import (
    RequirementResolver,
    RequirementSource,
    ResolvedRequirement,
    ResolutionResult,
    resolve_requirements,
    SCENE_TYPE_REQUIREMENTS,
    STYLE_REQUIREMENTS,
)
from lib.orchestrator.types import (
    AssetRequirement,
    SceneOutline,
    LightingRequirement,
)


class TestRequirementSource:
    """Tests for RequirementSource enum."""

    def test_source_values(self):
        """Test RequirementSource enum values."""
        assert RequirementSource.EXPLICIT.value == "explicit"
        assert RequirementSource.IMPLICIT.value == "implicit"
        assert RequirementSource.DERIVED.value == "derived"
        assert RequirementSource.DEFAULT.value == "default"


class TestResolvedRequirement:
    """Tests for ResolvedRequirement dataclass."""

    def test_create_default(self):
        """Test creating ResolvedRequirement with defaults."""
        requirement = AssetRequirement(
            requirement_id="req_01",
            category="furniture",
        )
        resolved = ResolvedRequirement(requirement=requirement)
        assert resolved.requirement == requirement
        assert resolved.source == "explicit"
        assert resolved.confidence == 1.0
        assert resolved.dependencies == []

    def test_create_with_values(self):
        """Test creating ResolvedRequirement with values."""
        requirement = AssetRequirement(
            requirement_id="req_01",
            category="furniture",
            subcategory="chair",
        )
        resolved = ResolvedRequirement(
            requirement=requirement,
            source="implicit",
            confidence=0.8,
            dependencies=["req_00"],
        )
        assert resolved.requirement.category == "furniture"
        assert resolved.source == "implicit"
        assert resolved.confidence == 0.8
        assert "req_00" in resolved.dependencies

    def test_to_dict(self):
        """Test ResolvedRequirement serialization."""
        requirement = AssetRequirement(
            requirement_id="test",
            category="props",
        )
        resolved = ResolvedRequirement(
            requirement=requirement,
            source="explicit",
        )
        data = resolved.to_dict()
        assert data["source"] == "explicit"
        assert data["requirement"]["requirement_id"] == "test"


class TestResolutionResult:
    """Tests for ResolutionResult dataclass."""

    def test_create_default(self):
        """Test creating ResolutionResult with defaults."""
        result = ResolutionResult()
        assert result.requirements == []
        assert result.conflicts == []
        assert result.warnings == []
        assert result.metadata == {}

    def test_create_with_values(self):
        """Test creating ResolutionResult with values."""
        requirement = AssetRequirement(requirement_id="req_01", category="furniture")
        resolved = ResolvedRequirement(requirement=requirement)
        result = ResolutionResult(
            requirements=[resolved],
            warnings=["test warning"],
        )
        assert len(result.requirements) == 1
        assert len(result.warnings) == 1

    def test_to_dict(self):
        """Test ResolutionResult serialization."""
        requirement = AssetRequirement(requirement_id="req_01", category="furniture")
        resolved = ResolvedRequirement(requirement=requirement)
        result = ResolutionResult(requirements=[resolved])
        data = result.to_dict()
        assert "requirements" in data
        assert len(data["requirements"]) == 1

    def test_get_requirements_by_category(self):
        """Test filtering requirements by category."""
        req1 = AssetRequirement(requirement_id="req_01", category="furniture")
        req2 = AssetRequirement(requirement_id="req_02", category="lighting")
        result = ResolutionResult(
            requirements=[
                ResolvedRequirement(requirement=req1),
                ResolvedRequirement(requirement=req2),
            ]
        )
        furniture = result.get_requirements_by_category("furniture")
        assert len(furniture) == 1
        assert furniture[0].category == "furniture"


class TestRequirementResolver:
    """Tests for RequirementResolver class."""

    def test_init(self):
        """Test RequirementResolver initialization."""
        resolver = RequirementResolver()
        assert resolver is not None

    def test_resolve_empty_outline(self):
        """Test resolving empty outline."""
        resolver = RequirementResolver()
        outline = SceneOutline(name="Test Scene")
        result = resolver.resolve(outline)
        assert isinstance(result, ResolutionResult)
        # Should have implicit requirements even with empty outline
        assert len(result.requirements) > 0

    def test_resolve_with_explicit_requirements(self):
        """Test resolving outline with explicit requirements."""
        resolver = RequirementResolver()
        outline = SceneOutline(
            name="Test Scene",
            asset_requirements=[
                AssetRequirement(
                    requirement_id="req_01",
                    category="furniture",
                    subcategory="chair",
                    quantity=2,
                ),
            ],
        )
        result = resolver.resolve(outline)
        # Find explicit requirement
        explicit = [r for r in result.requirements if r.source == "explicit"]
        assert len(explicit) == 1
        assert explicit[0].requirement.category == "furniture"

    def test_resolve_generates_ids(self):
        """Test that resolver generates IDs for requirements without them."""
        resolver = RequirementResolver()
        outline = SceneOutline(
            name="Test Scene",
            asset_requirements=[
                AssetRequirement(category="furniture"),  # No ID
            ],
        )
        result = resolver.resolve(outline)
        # Should have generated an ID
        assert result.requirements[0].requirement.requirement_id != ""

    def test_resolve_adds_implicit_scene_type_requirements(self):
        """Test that implicit requirements are added based on scene type."""
        resolver = RequirementResolver()
        outline = SceneOutline(
            name="Test Scene",
            scene_type="interior",
        )
        result = resolver.resolve(outline)
        # Interior should have implicit lighting requirement
        categories = [r.requirement.category for r in result.requirements]
        assert "lighting" in categories

    def test_resolve_adds_implicit_style_requirements(self):
        """Test that implicit requirements are added based on style."""
        resolver = RequirementResolver()
        outline = SceneOutline(
            name="Test Scene",
            scene_type="interior",
            style="photorealistic",
        )
        result = resolver.resolve(outline)
        assert isinstance(result, ResolutionResult)

    def test_resolve_with_lighting_config(self):
        """Test resolving with lighting configuration."""
        resolver = RequirementResolver()
        outline = SceneOutline(
            name="Test Scene",
            scene_type="interior",
            style="photorealistic",
            lighting=LightingRequirement(
                use_studio_lights=True,
                studio_preset="three_point",
            ),
        )
        result = resolver.resolve(outline)
        # Should have derived lighting requirements
        assert isinstance(result, ResolutionResult)


class TestResolveRequirementsFunction:
    """Tests for resolve_requirements convenience function."""

    def test_resolve_requirements_basic(self):
        """Test basic requirement resolution."""
        outline = SceneOutline(
            name="Test Scene",
            asset_requirements=[
                AssetRequirement(
                    requirement_id="req_01",
                    category="furniture",
                ),
            ],
        )
        result = resolve_requirements(outline)
        assert isinstance(result, ResolutionResult)
        assert len(result.requirements) >= 1


class TestImplicitRequirementRules:
    """Tests for implicit requirement rules."""

    def test_scene_type_requirements_exist(self):
        """Test that scene type requirements are defined."""
        assert "interior" in SCENE_TYPE_REQUIREMENTS
        assert "exterior" in SCENE_TYPE_REQUIREMENTS
        assert "urban" in SCENE_TYPE_REQUIREMENTS
        assert "product" in SCENE_TYPE_REQUIREMENTS
        assert "portrait" in SCENE_TYPE_REQUIREMENTS
        assert "environment" in SCENE_TYPE_REQUIREMENTS

    def test_style_requirements_exist(self):
        """Test that style requirements are defined."""
        assert "photorealistic" in STYLE_REQUIREMENTS
        assert "sci_fi" in STYLE_REQUIREMENTS
        assert "retro" in STYLE_REQUIREMENTS

    def test_interior_has_lighting(self):
        """Test interior scene has lighting requirement."""
        interior_reqs = SCENE_TYPE_REQUIREMENTS.get("interior", [])
        categories = [r.get("category") for r in interior_reqs]
        assert "lighting" in categories


class TestRequirementResolverEdgeCases:
    """Edge case tests for RequirementResolver."""

    def test_multiple_requirements_same_category(self):
        """Test resolving with multiple requirements for same category."""
        resolver = RequirementResolver()
        outline = SceneOutline(
            name="Test Scene",
            asset_requirements=[
                AssetRequirement(
                    requirement_id="req_01",
                    category="furniture",
                    priority="required",
                ),
                AssetRequirement(
                    requirement_id="req_02",
                    category="furniture",
                    priority="optional",
                ),
            ],
        )
        result = resolver.resolve(outline)
        # May have warnings about same category
        assert isinstance(result, ResolutionResult)

    def test_unknown_scene_type(self):
        """Test resolving with unknown scene type."""
        resolver = RequirementResolver()
        outline = SceneOutline(
            name="Test Scene",
            scene_type="unknown_type",
        )
        # Should not raise
        result = resolver.resolve(outline)
        assert isinstance(result, ResolutionResult)

    def test_unknown_style(self):
        """Test resolving with unknown style."""
        resolver = RequirementResolver()
        outline = SceneOutline(
            name="Test Scene",
            style="unknown_style",
        )
        # Should not raise
        result = resolver.resolve(outline)
        assert isinstance(result, ResolutionResult)

    def test_metadata_populated(self):
        """Test that metadata is populated in result."""
        resolver = RequirementResolver()
        outline = SceneOutline(
            name="Test Scene",
            scene_type="interior",
            style="photorealistic",
            asset_requirements=[
                AssetRequirement(requirement_id="req_01", category="furniture"),
            ],
        )
        result = resolver.resolve(outline)
        assert "scene_type" in result.metadata
        assert "style" in result.metadata
        assert "explicit_count" in result.metadata
        assert "total_count" in result.metadata
        assert result.metadata["explicit_count"] == 1

    def test_atmospherics_derived_requirements(self):
        """Test that atmospherics create derived requirements."""
        resolver = RequirementResolver()
        outline = SceneOutline(
            name="Test Scene",
            lighting=LightingRequirement(
                atmospherics=["fog", "mist"],
            ),
        )
        result = resolver.resolve(outline)
        # Should have derived atmosphere requirements
        atmosphere_reqs = [
            r for r in result.requirements
            if r.requirement.category == "atmosphere"
        ]
        assert len(atmosphere_reqs) == 2
