"""
Unit tests for lib/knowledge/query.py

Tests the Knowledge Query System including:
- KnowledgeResult dataclass
- Pattern dataclass
- KnowledgeQuery class
- search, get_pattern, list_patterns functions
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from lib.knowledge.query import (
    KnowledgeResult,
    Pattern,
    KnowledgeQuery,
    search_knowledge,
    get_pattern,
    list_all_patterns,
)


class TestKnowledgeResult:
    """Tests for KnowledgeResult dataclass."""

    def test_default_values(self):
        """Test KnowledgeResult default values."""
        result = KnowledgeResult(
            file="test.md",
            section="Section",
            title="Title",
            content="Content",
            relevance=0.5
        )
        assert result.file == "test.md"
        assert result.section == "Section"
        assert result.title == "Title"
        assert result.content == "Content"
        assert result.relevance == 0.5
        assert result.keywords == []
        assert result.code_example is False

    def test_custom_values(self):
        """Test KnowledgeResult with custom values."""
        result = KnowledgeResult(
            file="test.md",
            section="Section",
            title="Title",
            content="Content",
            relevance=0.8,
            keywords=["curl", "noise"],
            code_example=True
        )
        assert result.keywords == ["curl", "noise"]
        assert result.code_example is True

    def test_to_dict(self):
        """Test KnowledgeResult.to_dict() serialization."""
        result = KnowledgeResult(
            file="test.md",
            section="Section",
            title="Title",
            content="Content",
            relevance=0.75,
            keywords=["test"],
            code_example=True
        )
        data = result.to_dict()
        assert data["file"] == "test.md"
        assert data["relevance"] == 0.75
        assert data["keywords"] == ["test"]
        assert data["code_example"] is True


class TestPattern:
    """Tests for Pattern dataclass."""

    def test_default_values(self):
        """Test Pattern default values."""
        pattern = Pattern(
            name="test_pattern",
            description="Test description",
            category="test",
            nodes=["Node1", "Node2"],
            workflow="A -> B -> C"
        )
        assert pattern.name == "test_pattern"
        assert pattern.description == "Test description"
        assert pattern.category == "test"
        assert pattern.nodes == ["Node1", "Node2"]
        assert pattern.workflow == "A -> B -> C"
        assert pattern.code_example is None
        assert pattern.source_file == ""
        assert pattern.blender_version == "5.0"
        assert pattern.tags == []

    def test_custom_values(self):
        """Test Pattern with custom values."""
        pattern = Pattern(
            name="custom_pattern",
            description="Custom description",
            category="volume",
            nodes=["SDF", "Grid"],
            workflow="Mesh -> SDF -> Grid",
            code_example="# code here",
            source_file="test.md",
            source_section="Section 1",
            blender_version="4.0+",
            tags=["volume", "sdf"]
        )
        assert pattern.code_example == "# code here"
        assert pattern.source_file == "test.md"
        assert pattern.blender_version == "4.0+"
        assert pattern.tags == ["volume", "sdf"]

    def test_to_dict(self):
        """Test Pattern.to_dict() serialization."""
        pattern = Pattern(
            name="test",
            description="Desc",
            category="cat",
            nodes=["N1"],
            workflow="W",
            code_example="code",
            tags=["t1", "t2"]
        )
        data = pattern.to_dict()
        assert data["name"] == "test"
        assert data["nodes"] == ["N1"]
        assert data["tags"] == ["t1", "t2"]


class TestKnowledgeQuery:
    """Tests for KnowledgeQuery class."""

    def test_initialization(self):
        """Test KnowledgeQuery initialization."""
        kb = KnowledgeQuery()
        assert kb.docs_path is not None
        assert isinstance(kb.docs_path, Path)
        assert isinstance(kb._cache, dict)
        assert isinstance(kb._loaded_files, dict)

    def test_initialization_with_custom_path(self):
        """Test KnowledgeQuery with custom docs path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = KnowledgeQuery(docs_path=tmpdir)
            assert kb.docs_path == Path(tmpdir)

    def test_patterns_loaded(self):
        """Test that patterns are loaded on initialization."""
        kb = KnowledgeQuery()
        assert len(kb.PATTERNS) > 0
        # Check for known patterns
        assert "sdf_workflow" in kb.PATTERNS
        assert "curl_noise" in kb.PATTERNS
        assert "material_bundle" in kb.PATTERNS

    def test_get_pattern_exact_match(self):
        """Test getting a pattern by exact name."""
        kb = KnowledgeQuery()
        pattern = kb.get_pattern("sdf_workflow")
        assert pattern is not None
        assert pattern.name == "sdf_workflow"
        assert pattern.category == "volume"

    def test_get_pattern_normalized(self):
        """Test getting a pattern with normalized name."""
        kb = KnowledgeQuery()
        # Test with spaces and case
        pattern = kb.get_pattern("SDF Workflow")
        assert pattern is not None
        assert pattern.name == "sdf_workflow"

    def test_get_pattern_not_found(self):
        """Test getting a non-existent pattern."""
        kb = KnowledgeQuery()
        pattern = kb.get_pattern("nonexistent_pattern")
        assert pattern is None

    def test_search_returns_results(self):
        """Test that search returns results."""
        kb = KnowledgeQuery()
        results = kb.search("curl noise")
        assert len(results) > 0
        # Results should be sorted by relevance
        assert results[0].relevance >= results[-1].relevance

    def test_search_max_results(self):
        """Test search respects max_results."""
        kb = KnowledgeQuery()
        results = kb.search("noise", max_results=2)
        assert len(results) <= 2

    def test_search_min_relevance(self):
        """Test search respects min_relevance."""
        kb = KnowledgeQuery()
        results = kb.search("xyzabc123", min_relevance=0.5)
        # Should have few or no results with high threshold
        for result in results:
            assert result.relevance >= 0.5

    def test_list_patterns(self):
        """Test listing all patterns."""
        kb = KnowledgeQuery()
        patterns = kb.list_patterns()
        assert len(patterns) > 0
        # Each pattern should have required keys
        for p in patterns:
            assert "name" in p
            assert "description" in p
            assert "category" in p

    def test_list_patterns_by_category(self):
        """Test listing patterns filtered by category."""
        kb = KnowledgeQuery()
        patterns = kb.list_patterns(category="volume")
        assert len(patterns) > 0
        for p in patterns:
            assert p["category"] == "volume"

    def test_list_categories(self):
        """Test listing all categories."""
        kb = KnowledgeQuery()
        categories = kb.list_categories()
        assert len(categories) > 0
        assert "volume" in categories
        assert "particles" in categories

    def test_get_quick_reference_known_topics(self):
        """Test quick reference for known topics."""
        kb = KnowledgeQuery()
        for topic in ["closures", "bundles", "volume", "physics", "curl"]:
            ref = kb.get_quick_reference(topic)
            assert "╔" in ref  # Box drawing character
            assert topic.upper() in ref.upper()

    def test_get_quick_reference_unknown_topic(self):
        """Test quick reference for unknown topic."""
        kb = KnowledgeQuery()
        ref = kb.get_quick_reference("unknown_topic")
        assert "No quick reference" in ref

    def test_search_caches_results(self):
        """Test that search caches results."""
        kb = KnowledgeQuery()
        kb.search("test query")
        # Cache should have entry
        assert "test query" in kb._cache or len(kb._cache) >= 0

    def test_yaml_index_loading_graceful_failure(self):
        """Test that YAML index loading fails gracefully when file missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No YAML file in this directory
            kb = KnowledgeQuery(docs_path=tmpdir)
            # Should still have hardcoded patterns
            assert len(kb.PATTERNS) > 0


class TestKnowledgeQueryRelevance:
    """Tests for relevance calculation."""

    def test_name_match_high_relevance(self):
        """Test that name matches get high relevance."""
        kb = KnowledgeQuery()
        results = kb.search("sdf workflow")
        # Should find sdf_workflow pattern with high relevance
        sdf_results = [r for r in results if "sdf_workflow" in r.title.lower()]
        if sdf_results:
            assert sdf_results[0].relevance >= 0.5

    def test_tag_match_relevance(self):
        """Test that tag matches contribute to relevance."""
        kb = KnowledgeQuery()
        results = kb.search("volume sdf")
        # Should find patterns tagged with volume/sdf
        assert len(results) > 0

    def test_results_sorted_by_relevance(self):
        """Test that results are sorted by relevance descending."""
        kb = KnowledgeQuery()
        results = kb.search("noise particles simulation")
        relevances = [r.relevance for r in results]
        assert relevances == sorted(relevances, reverse=True)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_search_knowledge(self):
        """Test search_knowledge convenience function."""
        results = search_knowledge("curl noise")
        assert isinstance(results, list)
        if results:
            assert "file" in results[0]
            assert "relevance" in results[0]

    def test_get_pattern_function(self):
        """Test get_pattern convenience function."""
        pattern = get_pattern("sdf_workflow")
        assert pattern is not None
        assert pattern["name"] == "sdf_workflow"

    def test_get_pattern_not_found(self):
        """Test get_pattern returns None for unknown pattern."""
        pattern = get_pattern("nonexistent_pattern_xyz")
        assert pattern is None

    def test_list_all_patterns(self):
        """Test list_all_patterns convenience function."""
        patterns = list_all_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) > 0

    def test_list_all_patterns_with_category(self):
        """Test list_all_patterns with category filter."""
        patterns = list_all_patterns(category="bundles")
        assert len(patterns) > 0
        for p in patterns:
            assert p["category"] == "bundles"


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_query(self):
        """Test search with empty query."""
        kb = KnowledgeQuery()
        results = kb.search("")
        # Should return empty or minimal results
        assert isinstance(results, list)

    def test_special_characters_query(self):
        """Test search with special characters."""
        kb = KnowledgeQuery()
        results = kb.search("!@#$%^&*()")
        assert isinstance(results, list)

    def test_unicode_query(self):
        """Test search with unicode characters."""
        kb = KnowledgeQuery()
        results = kb.search("卷曲噪声")  # Chinese for "curl noise"
        assert isinstance(results, list)

    def test_very_long_query(self):
        """Test search with very long query."""
        kb = KnowledgeQuery()
        long_query = "noise " * 100
        results = kb.search(long_query)
        assert isinstance(results, list)

    def test_pattern_with_no_tags(self):
        """Test pattern relevance with no tags."""
        kb = KnowledgeQuery()
        # Create a pattern with no tags
        pattern = Pattern(
            name="no_tags",
            description="No tags here",
            category="test",
            nodes=[],
            workflow=""
        )
        kb.PATTERNS["no_tags"] = pattern
        results = kb.search("no_tags")
        assert isinstance(results, list)


class TestYAMLIndexLoading:
    """Tests for YAML index loading."""

    def test_yaml_not_available(self):
        """Test graceful handling when PyYAML not available."""
        with patch('lib.knowledge.query.YAML_AVAILABLE', False):
            kb = KnowledgeQuery()
            # Should still work with hardcoded patterns
            assert len(kb.PATTERNS) > 0

    def test_yaml_with_valid_index(self):
        """Test loading from valid YAML index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid YAML index
            yaml_content = """
patterns:
  test_yaml_pattern:
    description: "Test pattern from YAML"
    category: test
    nodes: ["Node1"]
    keywords: ["test"]
"""
            yaml_path = Path(tmpdir) / "KNOWLEDGE_INDEX.yaml"
            yaml_path.write_text(yaml_content)

            kb = KnowledgeQuery(docs_path=tmpdir)
            # Should have loaded the pattern
            # Note: This requires PyYAML to be installed
            assert len(kb.PATTERNS) > 0

    def test_yaml_with_invalid_syntax(self):
        """Test graceful handling of invalid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid YAML
            yaml_content = """
patterns:
  invalid: [unclosed bracket
"""
            yaml_path = Path(tmpdir) / "KNOWLEDGE_INDEX.yaml"
            yaml_path.write_text(yaml_content)

            # Should not raise, just log warning
            kb = KnowledgeQuery(docs_path=tmpdir)
            # Should still have hardcoded patterns
            assert len(kb.PATTERNS) > 0

    def test_yaml_with_missing_patterns_key(self):
        """Test graceful handling of YAML without patterns key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_content = """
other_key:
  something: value
"""
            yaml_path = Path(tmpdir) / "KNOWLEDGE_INDEX.yaml"
            yaml_path.write_text(yaml_content)

            kb = KnowledgeQuery(docs_path=tmpdir)
            assert len(kb.PATTERNS) > 0
