"""
Unit tests for Quetzalcoatl Animation Prep System (Phase 20.10)

Tests for rig generation and weight painting data.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.animation import (
    BoneType,
    RigType,
    BoneDefinition,
    BoneGroup,
    WeightPaintData,
    IKConstraint,
    RigConfig,
    RigResult,
    RigGenerator,
    generate_rig,
    get_rig_preset,
    create_config_from_preset,
    RIG_PRESETS,
)


class TestBoneType:
    """Tests for BoneType enum."""

    def test_type_values(self):
        """Test bone type enum values."""
        assert BoneType.SPINE.value == 0
        assert BoneType.NECK.value == 1
        assert BoneType.HEAD.value == 2
        assert BoneType.TAIL.value == 3
        assert BoneType.LEG.value == 4
        assert BoneType.WING.value == 5


class TestRigType:
    """Tests for RigType enum."""

    def test_type_values(self):
        """Test rig type enum values."""
        assert RigType.SIMPLE.value == 0
        assert RigType.STANDARD.value == 1
        assert RigType.FULL.value == 2
        assert RigType.GAME_READY.value == 3


class TestBoneDefinition:
    """Tests for BoneDefinition dataclass."""

    def test_bone_creation(self):
        """Test creating a bone definition."""
        bone = BoneDefinition(
            name="spine_00",
            bone_type=BoneType.SPINE,
            head_position=np.array([0.0, 0.0, 0.0]),
            tail_position=np.array([0.0, 1.0, 0.0]),
        )

        assert bone.name == "spine_00"
        assert bone.bone_type == BoneType.SPINE

    def test_bone_length(self):
        """Test bone length calculation."""
        bone = BoneDefinition(
            name="test",
            bone_type=BoneType.SPINE,
            head_position=np.array([0.0, 0.0, 0.0]),
            tail_position=np.array([0.0, 2.0, 0.0]),
        )

        assert np.isclose(bone.length, 2.0)

    def test_bone_direction(self):
        """Test bone direction calculation."""
        bone = BoneDefinition(
            name="test",
            bone_type=BoneType.SPINE,
            head_position=np.array([0.0, 0.0, 0.0]),
            tail_position=np.array([0.0, 3.0, 4.0]),
        )

        direction = bone.direction
        assert np.isclose(np.linalg.norm(direction), 1.0)

    def test_bone_parent(self):
        """Test bone parent reference."""
        bone = BoneDefinition(
            name="spine_01",
            bone_type=BoneType.SPINE,
            head_position=np.array([0.0, 1.0, 0.0]),
            tail_position=np.array([0.0, 2.0, 0.0]),
            parent="spine_00",
        )

        assert bone.parent == "spine_00"


class TestBoneGroup:
    """Tests for BoneGroup dataclass."""

    def test_group_creation(self):
        """Test creating a bone group."""
        group = BoneGroup(
            name="spine",
            bone_type=BoneType.SPINE,
            bone_names=["spine_00", "spine_01", "spine_02"],
        )

        assert group.name == "spine"
        assert len(group.bone_names) == 3


class TestWeightPaintData:
    """Tests for WeightPaintData dataclass."""

    def test_weight_creation(self):
        """Test creating weight data."""
        weight = WeightPaintData(
            bone_name="spine_00",
            vertex_indices=np.array([0, 1, 2, 3]),
            weights=np.array([0.8, 0.6, 0.4, 0.2]),
        )

        assert weight.bone_name == "spine_00"
        assert weight.vertex_count == 4

    def test_empty_weights(self):
        """Test weight data with no vertices."""
        weight = WeightPaintData(
            bone_name="test",
            vertex_indices=np.array([]),
            weights=np.array([]),
        )

        assert weight.vertex_count == 0


class TestIKConstraint:
    """Tests for IKConstraint dataclass."""

    def test_ik_creation(self):
        """Test creating IK constraint."""
        ik = IKConstraint(
            bone_name="lower_leg_L0",
            target="foot_L0",
            chain_length=2,
        )

        assert ik.bone_name == "lower_leg_L0"
        assert ik.chain_length == 2

    def test_ik_with_pole(self):
        """Test IK with pole target."""
        ik = IKConstraint(
            bone_name="lower_leg_L0",
            target="foot_L0",
            chain_length=2,
            pole_target="pole_L0",
            pole_angle=1.57,
        )

        assert ik.pole_target == "pole_L0"


class TestRigConfig:
    """Tests for RigConfig dataclass."""

    def test_default_values(self):
        """Test default config values."""
        config = RigConfig()

        assert config.rig_type == RigType.STANDARD
        assert config.spine_bone_count == 12
        assert config.leg_pairs == 2

    def test_custom_values(self):
        """Test custom config values."""
        config = RigConfig(
            rig_type=RigType.FULL,
            spine_bone_count=16,
            leg_pairs=4,
            wing_pairs=2,
        )

        assert config.rig_type == RigType.FULL
        assert config.spine_bone_count == 16


class TestRigResult:
    """Tests for RigResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample rig result."""
        config = RigConfig()
        gen = RigGenerator(config)
        return gen.generate()

    def test_bone_count(self, sample_result):
        """Test that bones are generated."""
        assert sample_result.bone_count > 0

    def test_bone_groups_exist(self, sample_result):
        """Test that bone groups exist."""
        assert len(sample_result.bone_groups) > 0

    def test_root_bone(self, sample_result):
        """Test that root bone is set."""
        assert sample_result.root_bone is not None

    def test_deform_bones_exist(self, sample_result):
        """Test that deform bones exist."""
        assert len(sample_result.deform_bones) > 0


class TestRigGenerator:
    """Tests for RigGenerator."""

    def test_generate_basic(self):
        """Test basic rig generation."""
        config = RigConfig()
        gen = RigGenerator(config)
        result = gen.generate()

        assert isinstance(result, RigResult)
        assert result.bone_count > 0

    def test_generate_simple_rig(self):
        """Test simple rig generation."""
        config = RigConfig(rig_type=RigType.SIMPLE, leg_pairs=0)
        gen = RigGenerator(config)
        result = gen.generate()

        # Simple rig should have fewer bones
        assert result.bone_count > 0
        # Should only have spine, maybe neck/head/tail
        bone_types = {b.bone_type for b in result.bones}
        assert BoneType.SPINE in bone_types

    def test_generate_full_rig(self):
        """Test full rig generation."""
        config = RigConfig(
            rig_type=RigType.FULL,
            leg_pairs=2,
            wing_pairs=1,
        )
        gen = RigGenerator(config)
        result = gen.generate()

        # Full rig should have more bones
        bone_types = {b.bone_type for b in result.bones}
        assert BoneType.SPINE in bone_types
        assert BoneType.LEG in bone_types
        assert BoneType.WING in bone_types

    def test_spine_bone_count(self):
        """Test spine bone count configuration."""
        config = RigConfig(spine_bone_count=20)
        gen = RigGenerator(config)
        result = gen.generate()

        spine_bones = [b for b in result.bones if b.bone_type == BoneType.SPINE]
        assert len(spine_bones) == 20

    def test_tail_bone_count(self):
        """Test tail bone count configuration."""
        config = RigConfig(tail_bone_count=10)
        gen = RigGenerator(config)
        result = gen.generate()

        tail_bones = [b for b in result.bones if b.bone_type == BoneType.TAIL]
        assert len(tail_bones) == 10

    def test_leg_pairs(self):
        """Test leg pair generation."""
        config = RigConfig(leg_pairs=3)
        gen = RigGenerator(config)
        result = gen.generate()

        leg_bones = [b for b in result.bones if b.bone_type == BoneType.LEG]
        # 3 pairs * 2 sides * 3 bones (upper, lower, foot) = 18 minimum
        assert len(leg_bones) >= 18

    def test_wing_generation(self):
        """Test wing generation."""
        config = RigConfig(rig_type=RigType.FULL, wing_pairs=1)
        gen = RigGenerator(config)
        result = gen.generate()

        wing_bones = [b for b in result.bones if b.bone_type == BoneType.WING]
        assert len(wing_bones) > 0

    def test_custom_spine_curve(self):
        """Test with custom spine curve."""
        config = RigConfig()
        gen = RigGenerator(config)

        # Create wavy spine
        t = np.linspace(0, 1, 20)
        spine = np.column_stack([
            np.sin(t * np.pi * 3) * 0.5,
            t * 10.0,
            np.zeros(20),
        ])

        result = gen.generate(spine_curve=spine)

        assert result.bone_count > 0
        # First spine bone should be at spine start
        spine_bones = [b for b in result.bones if b.bone_type == BoneType.SPINE]
        if spine_bones:
            assert np.allclose(spine_bones[0].head_position, spine[0], atol=0.1)

    def test_weight_generation(self):
        """Test weight generation with vertices."""
        config = RigConfig()
        gen = RigGenerator(config)

        # Create some body vertices
        vertices = np.array([
            [0.0, 0.0, 0.0],
            [0.0, 2.0, 0.0],
            [0.0, 4.0, 0.0],
            [0.0, 6.0, 0.0],
            [0.0, 8.0, 0.0],
            [0.0, 10.0, 0.0],
        ])

        result = gen.generate(body_vertices=vertices)

        assert len(result.weights) > 0

    def test_ik_generation(self):
        """Test IK constraint generation."""
        config = RigConfig(generate_ik=True, leg_pairs=2)
        gen = RigGenerator(config)
        result = gen.generate()

        # Should have IK constraints for legs
        assert len(result.ik_constraints) > 0

    def test_no_ik_generation(self):
        """Test without IK constraint generation."""
        config = RigConfig(generate_ik=False, leg_pairs=2)
        gen = RigGenerator(config)
        result = gen.generate()

        assert len(result.ik_constraints) == 0

    def test_bone_hierarchy(self):
        """Test bone parent-child hierarchy."""
        config = RigConfig(spine_bone_count=5)
        gen = RigGenerator(config)
        result = gen.generate()

        spine_bones = [b for b in result.bones if b.bone_type == BoneType.SPINE]

        # Check hierarchy
        for i, bone in enumerate(spine_bones):
            if i > 0:
                assert bone.parent == spine_bones[i - 1].name

    def test_bone_groups_created(self):
        """Test that bone groups are created."""
        config = RigConfig()
        gen = RigGenerator(config)
        result = gen.generate()

        group_names = {g.name for g in result.bone_groups}
        assert "spine" in group_names


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_rig_defaults(self):
        """Test generate_rig with defaults."""
        result = generate_rig()

        assert isinstance(result, RigResult)
        assert result.bone_count > 0

    def test_generate_rig_custom(self):
        """Test generate_rig with custom parameters."""
        result = generate_rig(rig_type=RigType.FULL)

        assert isinstance(result, RigResult)

    def test_generate_rig_with_vertices(self):
        """Test generate_rig with body vertices."""
        vertices = np.random.rand(100, 3) * 5
        result = generate_rig(body_vertices=vertices)

        assert result.bone_count > 0


class TestRigPresets:
    """Tests for rig presets."""

    def test_get_rig_preset_exists(self):
        """Test getting existing preset."""
        preset = get_rig_preset("simple")

        assert "rig_type" in preset
        assert "spine_bone_count" in preset

    def test_get_rig_preset_not_exists(self):
        """Test getting non-existent preset returns default."""
        preset = get_rig_preset("nonexistent")

        # Should return standard as default
        assert preset["rig_type"] == RigType.STANDARD

    def test_create_config_from_preset(self):
        """Test creating config from preset."""
        config = create_config_from_preset("simple")

        assert isinstance(config, RigConfig)
        assert config.rig_type == RigType.SIMPLE

    def test_all_presets_valid(self):
        """Test that all presets have required fields."""
        required_fields = ["rig_type"]

        for name, preset in RIG_PRESETS.items():
            for field in required_fields:
                assert field in preset, f"Preset {name} missing {field}"

    def test_simple_preset(self):
        """Test simple preset values."""
        preset = get_rig_preset("simple")

        assert preset["rig_type"] == RigType.SIMPLE
        assert preset["leg_pairs"] == 0

    def test_standard_preset(self):
        """Test standard preset values."""
        preset = get_rig_preset("standard")

        assert preset["rig_type"] == RigType.STANDARD
        assert preset["leg_pairs"] == 2

    def test_winged_preset(self):
        """Test winged preset values."""
        preset = get_rig_preset("winged")

        assert preset["rig_type"] == RigType.FULL
        assert preset["wing_pairs"] == 1

    def test_game_ready_preset(self):
        """Test game_ready preset values."""
        preset = get_rig_preset("game_ready")

        assert preset["rig_type"] == RigType.GAME_READY


class TestIntegration:
    """Integration tests for animation system."""

    def test_full_rig_pipeline(self):
        """Test full rig generation pipeline."""
        # Create spine
        t = np.linspace(0, 1, 30)
        spine = np.column_stack([
            np.sin(t * np.pi * 2) * 0.3,
            t * 12.0,
            np.cos(t * np.pi * 2) * 0.2,
        ])

        # Create body vertices
        n_verts = 200
        body_t = np.random.rand(n_verts)
        body_angle = np.random.rand(n_verts) * 2 * np.pi
        body_radius = 0.5 + np.random.rand(n_verts) * 0.2

        vertices = np.column_stack([
            np.cos(body_angle) * body_radius,
            body_t * 12.0,
            np.sin(body_angle) * body_radius,
        ])

        config = RigConfig(
            rig_type=RigType.FULL,
            spine_bone_count=10,
            neck_bone_count=3,
            tail_bone_count=6,
            leg_pairs=2,
            wing_pairs=1,
            generate_ik=True,
        )

        gen = RigGenerator(config)
        result = gen.generate(
            spine_curve=spine,
            body_vertices=vertices,
        )

        # Verify output
        assert result.bone_count > 0
        assert len(result.bone_groups) > 0
        assert len(result.weights) > 0
        assert len(result.ik_constraints) > 0

    def test_different_rig_types(self):
        """Test different rig types produce different results."""
        results = {}

        for rig_type in [RigType.SIMPLE, RigType.STANDARD, RigType.FULL]:
            config = RigConfig(rig_type=rig_type)
            gen = RigGenerator(config)
            results[rig_type] = gen.generate()

        # Full should have more bones than simple
        assert results[RigType.FULL].bone_count > results[RigType.SIMPLE].bone_count

    def test_preset_integration(self):
        """Test using presets with rig system."""
        for preset_name in RIG_PRESETS.keys():
            config = create_config_from_preset(preset_name)
            gen = RigGenerator(config)
            result = gen.generate()

            assert result.bone_count > 0
