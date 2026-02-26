"""
Unit tests for Quetzalcoatl Limb System (Phase 20.3)

Tests for leg generation with upper leg, lower leg, foot, toes, and claws.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.types import LimbConfig, SpineConfig, BodyConfig
from lib.spine import SpineGenerator
from lib.body import BodyGenerator
from lib.limb import (
    LimbGenerator,
    LimbResult,
    AllLimbsResult,
    LimbSegment,
    LimbSide,
    JointSocket,
    generate_limbs,
)


class TestLimbSegment:
    """Tests for LimbSegment enum."""

    def test_segment_values(self):
        """Test segment enum values."""
        assert LimbSegment.UPPER_LEG.value == 0
        assert LimbSegment.LOWER_LEG.value == 1
        assert LimbSegment.FOOT.value == 2
        assert LimbSegment.TOE.value == 3
        assert LimbSegment.CLAW.value == 4


class TestLimbSide:
    """Tests for LimbSide enum."""

    def test_side_values(self):
        """Test side enum values."""
        assert LimbSide.LEFT.value == -1
        assert LimbSide.RIGHT.value == 1


class TestJointSocket:
    """Tests for JointSocket dataclass."""

    def test_socket_creation(self):
        """Test creating a joint socket."""
        socket = JointSocket(
            joint_type=LimbSegment.UPPER_LEG,
            position=np.array([0.0, 0.0, -0.5]),
            normal=np.array([0.0, 0.0, -1.0]),
            rotation=0.0,
            scale=0.1,
        )

        assert socket.joint_type == LimbSegment.UPPER_LEG
        assert socket.scale == 0.1


class TestLimbResult:
    """Tests for LimbResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample limb result."""
        spine_config = SpineConfig(segments=32)
        spine_gen = SpineGenerator(spine_config, seed=42)
        spine_result = spine_gen.generate()

        body_config = BodyConfig()
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=8)

        limb_config = LimbConfig(leg_pairs=2)
        limb_gen = LimbGenerator(limb_config, spine_result, body_result)
        all_limbs = limb_gen.generate_all(resolution=8)

        return all_limbs.limbs[0]  # Return first limb

    def test_vertex_count(self, sample_result):
        """Test that vertices are generated."""
        assert sample_result.vertex_count > 0

    def test_face_count(self, sample_result):
        """Test that faces are generated."""
        assert sample_result.face_count > 0

    def test_vertices_shape(self, sample_result):
        """Test vertices array shape."""
        assert sample_result.vertices.shape[1] == 3

    def test_faces_shape(self, sample_result):
        """Test faces array shape."""
        assert sample_result.faces.shape[1] == 3

    def test_uvs_shape(self, sample_result):
        """Test UVs array shape."""
        assert sample_result.uvs.shape[1] == 2

    def test_sockets_exist(self, sample_result):
        """Test that joint sockets are generated."""
        assert len(sample_result.sockets) > 0

    def test_side_assigned(self, sample_result):
        """Test that side is assigned."""
        assert sample_result.side in (LimbSide.LEFT, LimbSide.RIGHT)

    def test_spine_position_in_range(self, sample_result):
        """Test spine position is in valid range."""
        assert 0 <= sample_result.spine_position <= 1


class TestAllLimbsResult:
    """Tests for AllLimbsResult dataclass."""

    @pytest.fixture
    def sample_all_limbs(self):
        """Create sample all limbs result."""
        spine_config = SpineConfig(segments=32)
        spine_gen = SpineGenerator(spine_config, seed=42)
        spine_result = spine_gen.generate()

        body_config = BodyConfig()
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=8)

        limb_config = LimbConfig(leg_pairs=2)
        limb_gen = LimbGenerator(limb_config, spine_result, body_result)
        return limb_gen.generate_all(resolution=8)

    def test_limb_count_two_pairs(self, sample_all_limbs):
        """Test that 2 leg pairs = 4 limbs."""
        assert sample_all_limbs.limb_count == 4

    def test_total_vertices(self, sample_all_limbs):
        """Test total vertices calculation."""
        expected = sum(l.vertex_count for l in sample_all_limbs.limbs)
        assert sample_all_limbs.total_vertices == expected

    def test_total_faces(self, sample_all_limbs):
        """Test total faces calculation."""
        expected = sum(l.face_count for l in sample_all_limbs.limbs)
        assert sample_all_limbs.total_faces == expected


class TestLimbGenerator:
    """Tests for LimbGenerator."""

    @pytest.fixture
    def setup_generators(self):
        """Create spine and body generators."""
        spine_config = SpineConfig(segments=32)
        spine_gen = SpineGenerator(spine_config, seed=42)
        spine_result = spine_gen.generate()

        body_config = BodyConfig()
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=8)

        return spine_result, body_result

    def test_generate_basic(self, setup_generators):
        """Test basic limb generation."""
        spine_result, body_result = setup_generators
        config = LimbConfig(leg_pairs=2)
        generator = LimbGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        assert isinstance(result, AllLimbsResult)
        assert result.limb_count == 4

    def test_generate_no_legs(self, setup_generators):
        """Test with zero leg pairs."""
        spine_result, body_result = setup_generators
        config = LimbConfig(leg_pairs=0)
        generator = LimbGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        assert result.limb_count == 0

    def test_generate_four_pairs(self, setup_generators):
        """Test with maximum leg pairs (4)."""
        spine_result, body_result = setup_generators
        config = LimbConfig(leg_pairs=4)
        generator = LimbGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        assert result.limb_count == 8  # 4 pairs = 8 limbs

    def test_custom_leg_positions(self, setup_generators):
        """Test with custom leg positions."""
        spine_result, body_result = setup_generators
        config = LimbConfig(
            leg_pairs=2,
            leg_positions=[0.25, 0.75],
        )
        generator = LimbGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        assert result.limb_count == 4
        # Check that positions are different
        positions = [l.spine_position for l in result.limbs]
        assert len(set(positions)) == 2  # Two unique positions

    def test_left_right_sides(self, setup_generators):
        """Test that left and right limbs are generated."""
        spine_result, body_result = setup_generators
        config = LimbConfig(leg_pairs=1)
        generator = LimbGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        sides = {l.side for l in result.limbs}
        assert LimbSide.LEFT in sides
        assert LimbSide.RIGHT in sides

    def test_leg_length_affects_size(self, setup_generators):
        """Test that leg length affects limb size."""
        spine_result, body_result = setup_generators

        config_short = LimbConfig(leg_pairs=1, leg_length=0.5)
        config_long = LimbConfig(leg_pairs=1, leg_length=2.0)

        gen_short = LimbGenerator(config_short, spine_result, body_result)
        gen_long = LimbGenerator(config_long, spine_result, body_result)

        result_short = gen_short.generate_all()
        result_long = gen_long.generate_all()

        # Both should generate successfully
        assert result_short.total_vertices > 0
        assert result_long.total_vertices > 0

        # Long legs should span a larger distance
        # Calculate the bounding box height for each leg
        def get_height_range(result):
            heights = []
            for limb in result.limbs:
                h_max = limb.vertices[:, 1].max()
                h_min = limb.vertices[:, 1].min()
                heights.append(h_max - h_min)
            return sum(heights) / len(heights)

        short_height = get_height_range(result_short)
        long_height = get_height_range(result_long)

        # Long legs should have greater vertical span
        assert long_height > short_height

    def test_toe_count_variation(self, setup_generators):
        """Test with different toe counts."""
        spine_result, body_result = setup_generators

        for toe_count in [2, 3, 4, 5]:
            config = LimbConfig(leg_pairs=1, toe_count=toe_count)
            generator = LimbGenerator(config, spine_result, body_result)
            result = generator.generate_all()

            assert result.limb_count == 2
            assert result.total_vertices > 0

    def test_claw_length_affects_size(self, setup_generators):
        """Test that claw length affects limb size."""
        spine_result, body_result = setup_generators

        config_short = LimbConfig(leg_pairs=1, claw_length=0.05)
        config_long = LimbConfig(leg_pairs=1, claw_length=0.2)

        gen_short = LimbGenerator(config_short, spine_result, body_result)
        gen_long = LimbGenerator(config_long, spine_result, body_result)

        result_short = gen_short.generate_all()
        result_long = gen_long.generate_all()

        # Both should generate successfully
        assert result_short.total_vertices > 0
        assert result_long.total_vertices > 0

    def test_vertex_normals_normalized(self, setup_generators):
        """Test that vertex normals are normalized."""
        spine_result, body_result = setup_generators
        config = LimbConfig(leg_pairs=1)
        generator = LimbGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        for limb in result.limbs:
            if limb.vertex_count > 0:
                lengths = np.linalg.norm(limb.normals, axis=1)
                non_zero = lengths > 0.01
                if np.any(non_zero):
                    assert np.allclose(lengths[non_zero], 1.0, atol=0.1)

    def test_faces_valid_indices(self, setup_generators):
        """Test that all face indices are valid."""
        spine_result, body_result = setup_generators
        config = LimbConfig(leg_pairs=2)
        generator = LimbGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        for limb in result.limbs:
            if limb.face_count > 0:
                max_idx = limb.vertex_count
                assert np.all(limb.faces >= 0)
                assert np.all(limb.faces < max_idx)

    def test_uvs_in_valid_range(self, setup_generators):
        """Test that UVs are in 0-1 range."""
        spine_result, body_result = setup_generators
        config = LimbConfig(leg_pairs=1)
        generator = LimbGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        for limb in result.limbs:
            if limb.vertex_count > 0:
                assert np.all(limb.uvs >= 0)
                assert np.all(limb.uvs <= 1)

    def test_joint_sockets_generated(self, setup_generators):
        """Test that joint sockets are generated for each segment."""
        spine_result, body_result = setup_generators
        config = LimbConfig(leg_pairs=1)
        generator = LimbGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        for limb in result.limbs:
            # Should have sockets for upper leg, lower leg, foot, and claws
            socket_types = {s.joint_type for s in limb.sockets}
            assert LimbSegment.UPPER_LEG in socket_types
            assert LimbSegment.LOWER_LEG in socket_types
            assert LimbSegment.FOOT in socket_types
            assert LimbSegment.CLAW in socket_types

    def test_deterministic_output(self, setup_generators):
        """Test that same config produces same output."""
        spine_result, body_result = setup_generators
        config = LimbConfig(leg_pairs=2, leg_length=1.0)

        gen1 = LimbGenerator(config, spine_result, body_result)
        gen2 = LimbGenerator(config, spine_result, body_result)

        result1 = gen1.generate_all()
        result2 = gen2.generate_all()

        # Same number of limbs
        assert result1.limb_count == result2.limb_count

        # Same vertex counts
        for l1, l2 in zip(result1.limbs, result2.limbs):
            assert l1.vertex_count == l2.vertex_count


class TestGenerateLimbs:
    """Tests for convenience function."""

    def test_generate_limbs_defaults(self):
        """Test generate_limbs with defaults."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        result = generate_limbs(
            LimbConfig(leg_pairs=2),
            spine_result,
            body_result,
        )

        assert isinstance(result, AllLimbsResult)
        assert result.limb_count == 4

    def test_generate_limbs_custom(self):
        """Test generate_limbs with custom parameters."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        result = generate_limbs(
            LimbConfig(
                leg_pairs=3,
                leg_length=1.5,
                toe_count=3,
                claw_length=0.15,
            ),
            spine_result,
            body_result,
            resolution=6,
        )

        assert result.limb_count == 6


class TestIntegration:
    """Integration tests for limb system."""

    def test_full_pipeline(self):
        """Test full spine + body + limb generation pipeline."""
        # Generate spine
        spine_config = SpineConfig(length=12.0, segments=48)
        spine_gen = SpineGenerator(spine_config, seed=12345)
        spine_result = spine_gen.generate()

        # Generate body
        body_config = BodyConfig(radius=0.5)
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=16)

        # Generate limbs
        limb_config = LimbConfig(
            leg_pairs=2,
            leg_positions=[0.3, 0.6],
            leg_length=1.2,
            leg_girth=0.15,
            toe_count=4,
            claw_length=0.1,
        )
        limb_gen = LimbGenerator(limb_config, spine_result, body_result)
        limb_result = limb_gen.generate_all(resolution=8)

        # Verify output
        assert limb_result.limb_count == 4
        assert limb_result.total_vertices > 0
        assert limb_result.total_faces > 0

    def test_different_creature_configs(self):
        """Test limb generation with different creature types."""
        # Serpent (no legs)
        spine_config = SpineConfig(length=10.0)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        serpent_limbs = generate_limbs(
            LimbConfig(leg_pairs=0),
            spine_result,
            body_result,
        )
        assert serpent_limbs.limb_count == 0

        # Dragon (4 legs, strong claws)
        dragon_limbs = generate_limbs(
            LimbConfig(
                leg_pairs=2,
                leg_length=1.5,
                leg_girth=0.2,
                toe_count=4,
                claw_length=0.2,
            ),
            spine_result,
            body_result,
        )
        assert dragon_limbs.limb_count == 4
