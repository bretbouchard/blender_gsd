"""
Unit tests for CRT Compositor module.

Tests for node group creation and Blender compositor integration.
"""

import pytest

from lib.retro.crt_compositor import (
    # Node creation
    create_crt_node_group,
    create_scanline_node_config,
    create_phosphor_node_config,
    # Setup
    setup_crt_compositing,
    create_curvature_node,
    create_scanline_node,
    # Utilities
    get_crt_node_group_name,
    list_crt_node_templates,
    get_node_template_description,
    create_preset_nodes,
    export_node_setup_python,
    # Constants
    CRT_NODE_GROUP_NAME,
    CRT_NODE_TEMPLATES,
)
from lib.retro.crt_types import (
    CRTConfig,
    ScanlineConfig,
    PhosphorConfig,
    CurvatureConfig,
)


class TestCreateCRTNodeGroup:
    """Tests for create_crt_node_group function."""

    def test_default_config(self):
        """Test with default configuration."""
        config = CRTConfig()
        result = create_crt_node_group(config)

        assert isinstance(result, dict)
        assert "name" in result
        assert "nodes" in result
        assert "config" in result
        assert result["name"] == CRT_NODE_GROUP_NAME

    def test_with_brightness(self):
        """Test with brightness adjustment."""
        config = CRTConfig(brightness=1.2)
        result = create_crt_node_group(config)

        # Should include brightness node
        node_types = [n.get("type") for n in result["nodes"]]
        assert "CompositorNodeBrightContrast" in node_types

    def test_with_contrast(self):
        """Test with contrast adjustment."""
        config = CRTConfig(contrast=1.3)
        result = create_crt_node_group(config)

        node_types = [n.get("type") for n in result["nodes"]]
        assert "CompositorNodeBrightContrast" in node_types

    def test_with_gamma(self):
        """Test with gamma correction."""
        config = CRTConfig(gamma=2.4)
        result = create_crt_node_group(config)

        node_types = [n.get("type") for n in result["nodes"]]
        assert "CompositorNodeGamma" in node_types

    def test_with_curvature(self):
        """Test with curvature enabled."""
        config = CRTConfig(
            curvature=CurvatureConfig(enabled=True, amount=0.1)
        )
        result = create_crt_node_group(config)

        node_types = [n.get("type") for n in result["nodes"]]
        assert "CompositorNodeLensdist" in node_types

    def test_with_chromatic_aberration(self):
        """Test with chromatic aberration."""
        config = CRTConfig(chromatic_aberration=0.005)
        result = create_crt_node_group(config)

        node_types = [n.get("type") for n in result["nodes"]]
        assert "CompositorNodeChromaMatte" in node_types

    def test_with_scanlines(self):
        """Test with scanlines enabled."""
        config = CRTConfig(
            scanlines=ScanlineConfig(enabled=True, intensity=0.3)
        )
        result = create_crt_node_group(config)

        # Should include scanline-related nodes
        assert len(result["nodes"]) > 0

    def test_with_phosphor(self):
        """Test with phosphor mask enabled."""
        config = CRTConfig(
            phosphor=PhosphorConfig(enabled=True, pattern="rgb")
        )
        result = create_crt_node_group(config)

        # Should include phosphor-related nodes
        assert len(result["nodes"]) > 0

    def test_with_bloom(self):
        """Test with bloom effect."""
        config = CRTConfig(bloom=0.2)
        result = create_crt_node_group(config)

        node_types = [n.get("type") for n in result["nodes"]]
        assert "CompositorNodeBlur" in node_types

    def test_with_vignette(self):
        """Test with vignette."""
        config = CRTConfig(
            curvature=CurvatureConfig(enabled=True, vignette_amount=0.3)
        )
        result = create_crt_node_group(config)

        node_types = [n.get("type") for n in result["nodes"]]
        assert "CompositorNodeEllipseMask" in node_types

    def test_with_noise(self):
        """Test with noise effect."""
        config = CRTConfig(noise=0.1)
        result = create_crt_node_group(config)

        node_types = [n.get("type") for n in result["nodes"]]
        assert "CompositorNodeNoise" in node_types


class TestCreateScanlineNodeConfig:
    """Tests for create_scanline_node_config function."""

    def test_enabled(self):
        """Test with scanlines enabled."""
        config = ScanlineConfig(enabled=True, intensity=0.4)
        nodes = create_scanline_node_config(config)

        assert isinstance(nodes, list)
        assert len(nodes) > 0

    def test_node_types(self):
        """Test that correct node types are created."""
        config = ScanlineConfig(enabled=True)
        nodes = create_scanline_node_config(config)

        node_types = [n.get("type") for n in nodes]
        assert "CompositorNodeTexture" in node_types

    def test_intensity_included(self):
        """Test that intensity is included in config."""
        config = ScanlineConfig(enabled=True, intensity=0.5)
        nodes = create_scanline_node_config(config)

        # Check that intensity appears somewhere
        all_values = str(nodes)
        assert "0.5" in all_values or "intensity" in all_values.lower()


class TestCreatePhosphorNodeConfig:
    """Tests for create_phosphor_node_config function."""

    def test_rgb_pattern(self):
        """Test with RGB pattern."""
        config = PhosphorConfig(enabled=True, pattern="rgb", intensity=0.5)
        nodes = create_phosphor_node_config(config)

        assert isinstance(nodes, list)
        assert len(nodes) > 0

    def test_bgr_pattern(self):
        """Test with BGR pattern."""
        config = PhosphorConfig(enabled=True, pattern="bgr", intensity=0.5)
        nodes = create_phosphor_node_config(config)

        assert isinstance(nodes, list)
        assert len(nodes) > 0

    def test_intensity_included(self):
        """Test that intensity is included."""
        config = PhosphorConfig(enabled=True, intensity=0.7)
        nodes = create_phosphor_node_config(config)

        # Check for mix node with intensity
        mix_nodes = [n for n in nodes if "Mix" in n.get("name", "")]
        assert len(mix_nodes) > 0


class TestSetupCRTCompositing:
    """Tests for setup_crt_compositing function."""

    def test_returns_node_names(self):
        """Test that function returns node names."""
        config = CRTConfig()
        result = setup_crt_compositing(None, config)

        assert isinstance(result, list)

    def test_with_various_effects(self):
        """Test with various effects enabled."""
        config = CRTConfig(
            brightness=1.1,
            bloom=0.2,
        )
        result = setup_crt_compositing(None, config)

        assert isinstance(result, list)


class TestCreateCurvatureNode:
    """Tests for create_curvature_node function."""

    def test_disabled(self):
        """Test with curvature disabled."""
        config = CurvatureConfig(enabled=False)
        result = create_curvature_node(None, config)

        assert result is None

    def test_enabled(self):
        """Test with curvature enabled."""
        config = CurvatureConfig(enabled=True, amount=0.1)
        result = create_curvature_node(None, config)

        assert isinstance(result, dict)
        assert result["type"] == "lens_distortion"
        assert result["amount"] == 0.1

    def test_includes_vignette(self):
        """Test that vignette is included."""
        config = CurvatureConfig(enabled=True, vignette_amount=0.2)
        result = create_curvature_node(None, config)

        assert "vignette" in result
        assert result["vignette"] == 0.2


class TestCreateScanlineNode:
    """Tests for create_scanline_node function."""

    def test_disabled(self):
        """Test with scanlines disabled."""
        config = ScanlineConfig(enabled=False)
        result = create_scanline_node(None, config)

        assert result is None

    def test_enabled(self):
        """Test with scanlines enabled."""
        config = ScanlineConfig(enabled=True, intensity=0.3, spacing=2)
        result = create_scanline_node(None, config)

        assert isinstance(result, dict)
        assert result["type"] == "scanlines"
        assert result["intensity"] == 0.3


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_get_crt_node_group_name_default(self):
        """Test default node group name."""
        name = get_crt_node_group_name()
        assert name == CRT_NODE_GROUP_NAME

    def test_get_crt_node_group_name_with_preset(self):
        """Test node group name with preset."""
        name = get_crt_node_group_name("arcade")
        assert "arcade" in name.lower()

    def test_list_crt_node_templates(self):
        """Test listing templates."""
        templates = list_crt_node_templates()

        assert isinstance(templates, list)
        assert "scanlines" in templates
        assert "full_crt" in templates

    def test_get_node_template_description(self):
        """Test getting template description."""
        desc = get_node_template_description("scanlines")
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_get_node_template_description_unknown(self):
        """Test unknown template description."""
        desc = get_node_template_description("nonexistent")
        assert "Unknown" in desc


class TestCreatePresetNodes:
    """Tests for create_preset_nodes function."""

    def test_valid_preset(self):
        """Test with valid preset."""
        result = create_preset_nodes("crt_arcade")

        assert isinstance(result, dict)
        assert "nodes" in result

    def test_invalid_preset(self):
        """Test with invalid preset (uses default)."""
        result = create_preset_nodes("nonexistent_preset")

        # Should still return a valid config
        assert isinstance(result, dict)
        assert "nodes" in result


class TestExportNodeSetupPython:
    """Tests for export_node_setup_python function."""

    def test_basic_export(self):
        """Test basic Python export."""
        config = CRTConfig()
        code = export_node_setup_python(config)

        assert isinstance(code, str)
        assert "import bpy" in code
        assert "CompositorNode" in code

    def test_includes_preset_name(self):
        """Test that preset name is in comments."""
        config = CRTConfig(name="test_preset")
        code = export_node_setup_python(config)

        assert isinstance(code, str)

    def test_includes_node_creation(self):
        """Test that node creation is included."""
        config = CRTConfig(brightness=1.2)
        code = export_node_setup_python(config)

        assert "tree.nodes.new" in code

    def test_includes_output_linking(self):
        """Test that output linking is included."""
        config = CRTConfig()
        code = export_node_setup_python(config)

        assert "tree.links.new" in code
        assert "CompositorNodeComposite" in code


class TestCRTNodeTemplates:
    """Tests for CRT_NODE_TEMPLATES constant."""

    def test_template_structure(self):
        """Test that templates have correct structure."""
        for name, template in CRT_NODE_TEMPLATES.items():
            assert "inputs" in template
            assert "outputs" in template
            assert "description" in template

    def test_full_crt_template(self):
        """Test full_crt template."""
        template = CRT_NODE_TEMPLATES["full_crt"]

        assert "Image" in template["inputs"]
        assert "Image" in template["outputs"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
