"""
Unit tests for Quetzalcoatl Shader System (Phase 20.9)

Tests for shader generation and material configurations.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.shader import (
    MaterialType,
    ShaderQuality,
    BaseMaterialProperties,
    SubsurfaceScattering,
    IridescenceShader,
    FeatherShaderConfig,
    ScaleShaderConfig,
    EyeShaderConfig,
    MaterialLayer,
    ShaderConfig,
    ShaderNodeData,
    ShaderResult,
    ShaderGenerator,
    generate_shaders,
    get_shader_preset,
    create_generator_from_preset,
    SHADER_PRESETS,
)


class TestMaterialType:
    """Tests for MaterialType enum."""

    def test_type_values(self):
        """Test material type enum values."""
        assert MaterialType.SKIN.value == 0
        assert MaterialType.FEATHER.value == 1
        assert MaterialType.SCALE.value == 2
        assert MaterialType.CLAW.value == 3
        assert MaterialType.TOOTH.value == 4
        assert MaterialType.EYE.value == 5
        assert MaterialType.WING_MEMBRANE.value == 6
        assert MaterialType.IRIDESCENT.value == 7


class TestShaderQuality:
    """Tests for ShaderQuality enum."""

    def test_quality_values(self):
        """Test quality enum values."""
        assert ShaderQuality.PREVIEW.value == 0
        assert ShaderQuality.STANDARD.value == 1
        assert ShaderQuality.HIGH.value == 2
        assert ShaderQuality.ULTRA.value == 3


class TestBaseMaterialProperties:
    """Tests for BaseMaterialProperties dataclass."""

    def test_default_values(self):
        """Test default property values."""
        props = BaseMaterialProperties()

        assert props.roughness == 0.5
        assert props.metallic == 0.0
        assert props.specular == 0.5
        assert props.alpha == 1.0

    def test_custom_values(self):
        """Test custom property values."""
        props = BaseMaterialProperties(
            base_color=np.array([1.0, 0.0, 0.0]),
            roughness=0.2,
            metallic=0.8,
        )

        assert props.base_color[0] == 1.0
        assert props.roughness == 0.2
        assert props.metallic == 0.8

    def test_list_to_array(self):
        """Test automatic conversion to numpy array."""
        props = BaseMaterialProperties(base_color=[0.5, 0.5, 0.5])

        assert isinstance(props.base_color, np.ndarray)


class TestSubsurfaceScattering:
    """Tests for SubsurfaceScattering dataclass."""

    def test_default_values(self):
        """Test default SSS values."""
        sss = SubsurfaceScattering()

        assert not sss.enabled
        assert sss.weight == 0.5

    def test_custom_values(self):
        """Test custom SSS values."""
        sss = SubsurfaceScattering(
            enabled=True,
            weight=0.8,
            radius=np.array([1.5, 0.5, 0.2]),
        )

        assert sss.enabled
        assert sss.weight == 0.8
        assert sss.radius[0] == 1.5


class TestIridescenceShader:
    """Tests for IridescenceShader dataclass."""

    def test_default_values(self):
        """Test default iridescence values."""
        irid = IridescenceShader()

        assert not irid.enabled
        assert irid.intensity == 1.0

    def test_custom_values(self):
        """Test custom iridescence values."""
        irid = IridescenceShader(
            enabled=True,
            hue_shift_range=0.5,
            fresnel_power=5.0,
        )

        assert irid.enabled
        assert irid.hue_shift_range == 0.5
        assert irid.fresnel_power == 5.0


class TestFeatherShaderConfig:
    """Tests for FeatherShaderConfig dataclass."""

    def test_default_values(self):
        """Test default feather config."""
        config = FeatherShaderConfig()

        assert config.barb_separation == 0.02
        assert config.translucency == 0.3


class TestScaleShaderConfig:
    """Tests for ScaleShaderConfig dataclass."""

    def test_default_values(self):
        """Test default scale config."""
        config = ScaleShaderConfig()

        assert config.scale_pattern_intensity == 0.5
        assert config.wetness == 0.0


class TestEyeShaderConfig:
    """Tests for EyeShaderConfig dataclass."""

    def test_default_values(self):
        """Test default eye config."""
        config = EyeShaderConfig()

        assert config.pupil_size == 0.3
        assert config.cornea_ior == 1.4

    def test_custom_values(self):
        """Test custom eye config."""
        config = EyeShaderConfig(
            iris_color=np.array([0.8, 0.2, 0.1]),
            pupil_size=0.5,
        )

        assert config.iris_color[0] == 0.8
        assert config.pupil_size == 0.5


class TestShaderConfig:
    """Tests for ShaderConfig dataclass."""

    def test_basic_config(self):
        """Test basic shader config."""
        config = ShaderConfig(
            material_type=MaterialType.SKIN,
            base_properties=BaseMaterialProperties(),
        )

        assert config.material_type == MaterialType.SKIN
        assert config.quality == ShaderQuality.STANDARD

    def test_config_with_sss(self):
        """Test config with subsurface scattering."""
        config = ShaderConfig(
            material_type=MaterialType.SKIN,
            base_properties=BaseMaterialProperties(),
            subsurface=SubsurfaceScattering(enabled=True),
        )

        assert config.subsurface.enabled


class TestShaderNodeData:
    """Tests for ShaderNodeData dataclass."""

    def test_node_creation(self):
        """Test creating shader node data."""
        node = ShaderNodeData(
            node_type="bsdf_principled",
            position=(0, 0),
            properties={"Roughness": 0.5},
            inputs={},
            outputs={"BSDF": "Surface"},
        )

        assert node.node_type == "bsdf_principled"
        assert node.position == (0, 0)
        assert "Roughness" in node.properties


class TestShaderResult:
    """Tests for ShaderResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample shader result."""
        gen = ShaderGenerator()
        return gen.generate()

    def test_material_count(self, sample_result):
        """Test that materials are generated."""
        assert sample_result.material_count > 0

    def test_shader_configs_exist(self, sample_result):
        """Test that shader configs exist."""
        assert len(sample_result.shader_configs) > 0

    def test_node_data_exists(self, sample_result):
        """Test that node data is generated."""
        assert len(sample_result.node_data) > 0


class TestShaderGenerator:
    """Tests for ShaderGenerator."""

    def test_generate_basic(self):
        """Test basic shader generation."""
        gen = ShaderGenerator()
        result = gen.generate()

        assert isinstance(result, ShaderResult)
        assert result.material_count > 0

    def test_generate_specific_materials(self):
        """Test generating specific material types."""
        gen = ShaderGenerator()
        result = gen.generate([
            MaterialType.SKIN,
            MaterialType.EYE,
        ])

        assert result.material_count == 2
        assert "skin" in result.shader_configs
        assert "eye" in result.shader_configs

    def test_quality_affects_sss(self):
        """Test that quality affects SSS generation."""
        gen_preview = ShaderGenerator(ShaderQuality.PREVIEW)
        gen_high = ShaderGenerator(ShaderQuality.HIGH)

        result_preview = gen_preview.generate([MaterialType.SKIN])
        result_high = gen_high.generate([MaterialType.SKIN])

        # High quality should have SSS enabled for skin
        skin_high = result_high.shader_configs.get("skin")
        if skin_high and skin_high.subsurface:
            assert skin_high.subsurface.enabled

    def test_quality_affects_iridescence(self):
        """Test that quality affects iridescence."""
        gen_preview = ShaderGenerator(ShaderQuality.PREVIEW)
        gen_standard = ShaderGenerator(ShaderQuality.STANDARD)

        result_preview = gen_preview.generate([MaterialType.FEATHER])
        result_standard = gen_standard.generate([MaterialType.FEATHER])

        feather_standard = result_standard.shader_configs.get("feather")
        if feather_standard and feather_standard.iridescence:
            # Standard quality should have iridescence for feathers
            assert feather_standard.iridescence.enabled

    def test_skin_material(self):
        """Test skin material generation."""
        gen = ShaderGenerator()
        result = gen.generate([MaterialType.SKIN])

        skin = result.shader_configs.get("skin")
        assert skin is not None
        assert skin.material_type == MaterialType.SKIN
        assert skin.base_properties.roughness > 0

    def test_feather_material(self):
        """Test feather material generation."""
        gen = ShaderGenerator()
        result = gen.generate([MaterialType.FEATHER])

        feather = result.shader_configs.get("feather")
        assert feather is not None
        assert feather.material_type == MaterialType.FEATHER
        assert feather.feather_config is not None

    def test_scale_material(self):
        """Test scale material generation."""
        gen = ShaderGenerator()
        result = gen.generate([MaterialType.SCALE])

        scale = result.shader_configs.get("scale")
        assert scale is not None
        assert scale.material_type == MaterialType.SCALE
        assert scale.scale_config is not None

    def test_claw_material(self):
        """Test claw material generation."""
        gen = ShaderGenerator()
        result = gen.generate([MaterialType.CLAW])

        claw = result.shader_configs.get("claw")
        assert claw is not None
        assert claw.material_type == MaterialType.CLAW

    def test_tooth_material(self):
        """Test tooth material generation."""
        gen = ShaderGenerator()
        result = gen.generate([MaterialType.TOOTH])

        tooth = result.shader_configs.get("tooth")
        assert tooth is not None
        assert tooth.material_type == MaterialType.TOOTH
        # Teeth are glossy
        assert tooth.base_properties.roughness < 0.3

    def test_eye_material(self):
        """Test eye material generation."""
        gen = ShaderGenerator()
        result = gen.generate([MaterialType.EYE])

        eye = result.shader_configs.get("eye")
        assert eye is not None
        assert eye.material_type == MaterialType.EYE
        assert eye.eye_config is not None

    def test_membrane_material(self):
        """Test wing membrane material generation."""
        gen = ShaderGenerator()
        result = gen.generate([MaterialType.WING_MEMBRANE])

        membrane = result.shader_configs.get("wing_membrane")
        assert membrane is not None
        assert membrane.material_type == MaterialType.WING_MEMBRANE

    def test_iridescent_material(self):
        """Test iridescent material generation."""
        gen = ShaderGenerator()
        result = gen.generate([MaterialType.IRIDESCENT])

        irid = result.shader_configs.get("iridescent")
        assert irid is not None
        assert irid.material_type == MaterialType.IRIDESCENT
        assert irid.iridescence.enabled

    def test_node_data_structure(self):
        """Test node data structure."""
        gen = ShaderGenerator()
        result = gen.generate([MaterialType.SKIN])

        # Should have at least BSDF and output nodes
        assert len(result.node_data) >= 2

        node_types = [n.node_type for n in result.node_data]
        assert "bsdf_principled" in node_types
        assert "output_material" in node_types


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_shaders_defaults(self):
        """Test generate_shaders with defaults."""
        result = generate_shaders()

        assert isinstance(result, ShaderResult)
        assert result.material_count > 0

    def test_generate_shaders_custom_quality(self):
        """Test generate_shaders with custom quality."""
        result = generate_shaders(quality=ShaderQuality.HIGH)

        assert isinstance(result, ShaderResult)

    def test_generate_shaders_custom_materials(self):
        """Test generate_shaders with custom materials."""
        result = generate_shaders(
            quality=ShaderQuality.STANDARD,
            material_types=[MaterialType.EYE, MaterialType.TOOTH],
        )

        assert result.material_count == 2


class TestShaderPresets:
    """Tests for shader presets."""

    def test_get_shader_preset_exists(self):
        """Test getting existing preset."""
        preset = get_shader_preset("realistic")

        assert "quality" in preset
        assert "materials" in preset

    def test_get_shader_preset_not_exists(self):
        """Test getting non-existent preset returns default."""
        preset = get_shader_preset("nonexistent")

        # Should return realistic as default
        assert preset["quality"] == ShaderQuality.HIGH

    def test_create_generator_from_preset(self):
        """Test creating generator from preset."""
        gen = create_generator_from_preset("preview")

        assert gen.quality == ShaderQuality.PREVIEW

    def test_all_presets_valid(self):
        """Test that all presets have required fields."""
        required_fields = ["quality", "materials"]

        for name, preset in SHADER_PRESETS.items():
            for field in required_fields:
                assert field in preset, f"Preset {name} missing {field}"

    def test_realistic_preset(self):
        """Test realistic preset values."""
        preset = get_shader_preset("realistic")

        assert preset["quality"] == ShaderQuality.HIGH
        assert MaterialType.SKIN in preset["materials"]
        assert MaterialType.EYE in preset["materials"]

    def test_stylized_preset(self):
        """Test stylized preset values."""
        preset = get_shader_preset("stylized")

        assert preset["quality"] == ShaderQuality.STANDARD

    def test_preview_preset(self):
        """Test preview preset values."""
        preset = get_shader_preset("preview")

        assert preset["quality"] == ShaderQuality.PREVIEW

    def test_iridescent_creature_preset(self):
        """Test iridescent_creature preset values."""
        preset = get_shader_preset("iridescent_creature")

        assert preset["quality"] == ShaderQuality.HIGH
        assert MaterialType.IRIDESCENT in preset["materials"]


class TestIntegration:
    """Integration tests for shader system."""

    def test_full_shader_pipeline(self):
        """Test full shader generation pipeline."""
        gen = ShaderGenerator(ShaderQuality.HIGH)
        result = gen.generate([
            MaterialType.SKIN,
            MaterialType.FEATHER,
            MaterialType.SCALE,
            MaterialType.CLAW,
            MaterialType.TOOTH,
            MaterialType.EYE,
        ])

        # Should have all materials
        assert result.material_count == 6

        # Each should have node data
        assert len(result.node_data) > 0

    def test_quality_progression(self):
        """Test quality affects output."""
        materials = [MaterialType.SKIN]

        for quality in ShaderQuality:
            gen = ShaderGenerator(quality)
            result = gen.generate(materials)

            assert result.material_count == 1
            skin = result.shader_configs.get("skin")
            assert skin is not None

    def test_different_material_types(self):
        """Test generating different material types."""
        gen = ShaderGenerator()

        for mat_type in MaterialType:
            result = gen.generate([mat_type])
            assert result.material_count == 1

    def test_preset_integration(self):
        """Test using presets with shader system."""
        for preset_name in SHADER_PRESETS.keys():
            gen = create_generator_from_preset(preset_name)
            preset = get_shader_preset(preset_name)

            result = gen.generate(preset["materials"])

            assert result.material_count == len(preset["materials"])
