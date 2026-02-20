"""
Unit tests for Light Linking Module

Tests for lib/cinematic/light_linking.py - Light linking for Blender 4.0+.
All tests run without Blender (mocked) for CI compatibility.
"""

import pytest
from unittest.mock import patch, MagicMock

from lib.cinematic.light_linking import (
    link_light_to_collection,
    unlink_light_from_collection,
    set_light_include_only,
    set_light_exclude,
    get_light_links,
    clear_light_links,
    get_objects_affected_by_light,
    copy_light_linking,
    is_light_linking_supported,
    BLENDER_40_MIN,
)


class TestIsLightLinkingSupported:
    """Tests for light linking support check."""

    def test_returns_boolean(self):
        """Test that function returns boolean."""
        result = is_light_linking_supported()
        assert isinstance(result, bool)


class TestLinkLightToCollection:
    """Tests for linking lights to collections."""

    def test_blender_unavailable(self):
        """Test returns False when Blender not available."""
        result = link_light_to_collection("key_light", "receivers")
        assert result is False

    def test_receiver_link_type(self):
        """Test receiver link type."""
        result = link_light_to_collection(
            "key_light",
            "receivers",
            link_type="receiver"
        )
        assert result is False  # Blender not available

    def test_blocker_link_type(self):
        """Test blocker link type."""
        result = link_light_to_collection(
            "key_light",
            "blockers",
            link_type="blocker"
        )
        assert result is False  # Blender not available


class TestUnlinkLightFromCollection:
    """Tests for unlinking lights from collections."""

    def test_blender_unavailable(self):
        """Test returns False when Blender not available."""
        result = unlink_light_from_collection("key_light", "receivers")
        assert result is False


class TestSetLightIncludeOnly:
    """Tests for include-only light linking."""

    def test_blender_unavailable(self):
        """Test returns False when Blender not available."""
        result = set_light_include_only("key_light", ["object1", "object2"])
        assert result is False

    def test_empty_object_list(self):
        """Test with empty object list."""
        result = set_light_include_only("key_light", [])
        assert result is False

    def test_multiple_objects(self):
        """Test with multiple objects."""
        result = set_light_include_only(
            "key_light",
            ["product", "base", "label"]
        )
        assert result is False


class TestSetLightExclude:
    """Tests for exclude light linking."""

    def test_blender_unavailable(self):
        """Test returns False when Blender not available."""
        result = set_light_exclude("rim_light", ["background"])
        assert result is False

    def test_multiple_exclusions(self):
        """Test with multiple excluded objects."""
        result = set_light_exclude(
            "rim_light",
            ["background", "floor", "wall"]
        )
        assert result is False


class TestGetLightLinks:
    """Tests for querying light linking configuration."""

    def test_blender_unavailable(self):
        """Test returns default dict when Blender not available."""
        result = get_light_links("test_light")

        assert result["has_linking"] is False
        assert result["receiver_collection"] is None
        assert result["blocker_collection"] is None
        assert result["receiver_objects"] == []
        assert result["blocker_objects"] == []
        assert result["supported"] is False

    def test_nonexistent_light(self):
        """Test with nonexistent light name."""
        result = get_light_links("nonexistent")

        assert result["has_linking"] is False
        assert result["supported"] is False


class TestClearLightLinks:
    """Tests for clearing light links."""

    def test_blender_unavailable(self):
        """Test returns False when Blender not available."""
        result = clear_light_links("test_light")
        assert result is False


class TestGetObjectsAffectedByLight:
    """Tests for getting objects affected by a light."""

    def test_blender_unavailable(self):
        """Test returns empty list when Blender not available."""
        result = get_objects_affected_by_light("test_light")
        assert result == []

    def test_no_linking(self):
        """Test returns empty when no linking configured."""
        # Since get_light_links returns has_linking=False
        result = get_objects_affected_by_light("test_light")
        assert result == []


class TestCopyLightLinking:
    """Tests for copying light linking configuration."""

    def test_blender_unavailable(self):
        """Test returns False when Blender not available."""
        result = copy_light_linking("source_light", "target_light")
        assert result is False


class TestLightLinkingIntegration:
    """Integration tests for light linking workflow."""

    def test_full_workflow(self):
        """Test complete linking workflow (all should fail gracefully)."""
        light_name = "test_light"

        # Set up include-only linking
        result1 = set_light_include_only(light_name, ["obj1", "obj2"])
        assert result1 is False

        # Query linking
        result2 = get_light_links(light_name)
        assert result2["has_linking"] is False

        # Clear linking
        result3 = clear_light_links(light_name)
        assert result3 is False


class TestConstants:
    """Tests for module constants."""

    def test_blender_version(self):
        """Test Blender version constant."""
        assert BLENDER_40_MIN == (4, 0, 0)


class TestLightLinkingScenarios:
    """Tests for common light linking scenarios."""

    def test_product_lighting_scenario(self):
        """Test product-only illumination scenario."""
        # Light should only affect product
        result = set_light_include_only(
            "key_light",
            ["product_body", "product_label"]
        )
        assert result is False  # Blender not available

    def test_rim_light_exclusion_scenario(self):
        """Test rim light excluding background."""
        # Rim should not illuminate background
        result = set_light_exclude(
            "rim_light",
            ["background_plane", "studio_backdrop"]
        )
        assert result is False

    def test_multi_light_setup(self):
        """Test multi-light linking setup."""
        lights = ["key_light", "fill_light", "rim_light"]

        for light in lights:
            result = set_light_include_only(light, ["subject"])
            assert result is False

    def test_copy_setup_between_lights(self):
        """Test copying linking setup between lights."""
        result = copy_light_linking("key_light", "key_light_copy")
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
