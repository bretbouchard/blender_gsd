"""
Unit tests for Quetzalcoatl Head System (Phase 20.2)

Tests for head generation with snout, jaw, eyes, and crest.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.types import HeadConfig, CrestType
from lib.head import (
    HeadGenerator,
    HeadResult,
    HeadFeature,
    FeatureSocket,
    generate_head,
)


class TestHeadFeature:
    """Tests for HeadFeature enum."""

    def test_feature_values(self):
        """Test feature enum values."""
        assert HeadFeature.SNOUT.value == 0
        assert HeadFeature.JAW.value == 1
        assert HeadFeature.LEFT_EYE.value == 2
        assert HeadFeature.RIGHT_EYE.value == 3


class TestFeatureSocket:
    """Tests for FeatureSocket dataclass."""

    def test_socket_creation(self):
        """Test creating a feature socket."""
        socket = FeatureSocket(
            feature_type=HeadFeature.LEFT_EYE,
            position=np.array([1.0, 0.0, 0.5]),
            normal=np.array([1.0, 0.0, 0.0]),
            scale=0.1,
            rotation=0.0,
        )

        assert socket.feature_type == HeadFeature.LEFT_EYE
        assert socket.scale == 0.1


class TestHeadResult:
    """Tests for HeadResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample head result."""
        config = HeadConfig()
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
            head_scale=1.0,
        )
        return generator.generate(resolution=8)

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
        """Test that feature sockets are generated."""
        assert len(sample_result.sockets) > 0


class TestHeadGenerator:
    """Tests for HeadGenerator."""

    def test_generate_basic(self):
        """Test basic head generation."""
        config = HeadConfig()
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        result = generator.generate()

        assert isinstance(result, HeadResult)
        assert result.vertex_count > 0

    def test_generate_with_snout(self):
        """Test head generation with snout."""
        config = HeadConfig(snout_length=1.0)
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        result = generator.generate()

        assert result.vertex_count > 0
        # Should have snout socket
        snout_sockets = [
            s for s in result.sockets if s.feature_type == HeadFeature.SNOUT
        ]
        assert len(snout_sockets) == 1

    def test_generate_with_jaw(self):
        """Test head generation with jaw."""
        config = HeadConfig(jaw_depth=0.5)
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        result = generator.generate()

        assert result.vertex_count > 0

    def test_generate_with_crest_ridge(self):
        """Test head generation with ridge crest."""
        config = HeadConfig(crest_type=CrestType.RIDGE, crest_size=0.5)
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        result = generator.generate()

        assert result.vertex_count > 0

    def test_generate_with_crest_horns(self):
        """Test head generation with horns."""
        config = HeadConfig(crest_type=CrestType.HORNS, crest_size=0.5)
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        result = generator.generate()

        # Should have horn sockets
        horn_sockets = [
            s for s in result.sockets
            if s.feature_type in (HeadFeature.LEFT_HORN, HeadFeature.RIGHT_HORN)
        ]
        assert len(horn_sockets) == 2

    def test_eye_sockets_generated(self):
        """Test that eye sockets are generated."""
        config = HeadConfig()
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        result = generator.generate()

        eye_sockets = [
            s for s in result.sockets
            if s.feature_type in (HeadFeature.LEFT_EYE, HeadFeature.RIGHT_EYE)
        ]
        assert len(eye_sockets) == 2

    def test_nostril_sockets_generated(self):
        """Test that nostril sockets are generated."""
        config = HeadConfig(snout_length=0.5)
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        result = generator.generate()

        nostril_sockets = [
            s for s in result.sockets
            if s.feature_type in (HeadFeature.LEFT_NOSTRIL, HeadFeature.RIGHT_NOSTRIL)
        ]
        assert len(nostril_sockets) == 2

    def test_scale_affects_size(self):
        """Test that scale affects head size."""
        config = HeadConfig()

        gen_small = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
            head_scale=0.5,
        )
        gen_large = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
            head_scale=2.0,
        )

        result_small = gen_small.generate()
        result_large = gen_large.generate()

        # Large head should have vertices further from center
        dist_small = np.linalg.norm(result_small.vertices, axis=1)
        dist_large = np.linalg.norm(result_large.vertices, axis=1)

        assert np.mean(dist_large) > np.mean(dist_small)

    def test_different_directions(self):
        """Test head generation with different orientations."""
        config = HeadConfig()

        # Facing different directions
        for direction in [(1, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 0, 0)]:
            generator = HeadGenerator(
                config=config,
                head_position=np.array([0.0, 0.0, 0.0]),
                head_direction=np.array(direction),
            )
            result = generator.generate()

            assert result.vertex_count > 0

    def test_vertex_normals_normalized(self):
        """Test that vertex normals are normalized."""
        config = HeadConfig()
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        result = generator.generate()

        if result.vertex_count > 0:
            # Get non-zero normals only
            lengths = np.linalg.norm(result.normals, axis=1)
            non_zero = lengths > 0.01
            if np.any(non_zero):
                assert np.allclose(lengths[non_zero], 1.0, atol=0.1)

    def test_faces_valid_indices(self):
        """Test that all face indices are valid."""
        config = HeadConfig()
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        result = generator.generate()

        if result.face_count > 0:
            max_idx = result.vertex_count
            assert np.all(result.faces >= 0)
            assert np.all(result.faces < max_idx)

    def test_uvs_in_valid_range(self):
        """Test that UVs are in 0-1 range."""
        config = HeadConfig()
        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        result = generator.generate()

        if result.vertex_count > 0:
            assert np.all(result.uvs >= 0)
            assert np.all(result.uvs <= 1)

    def test_deterministic_output(self):
        """Test that same config produces same output."""
        config = HeadConfig(snout_length=0.8, jaw_depth=0.3)

        gen1 = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )
        gen2 = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
        )

        result1 = gen1.generate()
        result2 = gen2.generate()

        assert np.allclose(result1.vertices, result2.vertices)


class TestGenerateHead:
    """Tests for convenience function."""

    def test_generate_head_defaults(self):
        """Test generate_head with defaults."""
        result = generate_head(HeadConfig())

        assert isinstance(result, HeadResult)
        assert result.vertex_count > 0

    def test_generate_head_custom(self):
        """Test generate_head with custom parameters."""
        result = generate_head(
            HeadConfig(snout_length=1.0, crest_type=CrestType.HORNS),
            position=(5.0, 0.0, 2.0),
            direction=(1.0, 0.0, 0.0),
            scale=1.5,
            resolution=12,
        )

        assert isinstance(result, HeadResult)
        assert result.vertex_count > 0


class TestIntegration:
    """Integration tests for head system."""

    def test_head_with_all_features(self):
        """Test head with all features enabled."""
        config = HeadConfig(
            snout_length=1.0,
            snout_profile=0.5,
            jaw_depth=0.4,
            crest_type=CrestType.HORNS,
            crest_size=0.6,
        )

        generator = HeadGenerator(
            config=config,
            head_position=np.array([0.0, 0.0, 0.0]),
            head_direction=np.array([0.0, 1.0, 0.0]),
            head_scale=1.0,
        )
        result = generator.generate(resolution=12)

        assert result.vertex_count > 0
        assert result.face_count > 0

        # Should have multiple socket types
        socket_types = {s.feature_type for s in result.sockets}
        assert HeadFeature.LEFT_EYE in socket_types
        assert HeadFeature.RIGHT_EYE in socket_types
        assert HeadFeature.LEFT_NOSTRIL in socket_types
        assert HeadFeature.RIGHT_NOSTRIL in socket_types

    def test_different_creature_heads(self):
        """Test heads for different creature types."""
        # Serpent head (long snout, no crest)
        serpent_config = HeadConfig(
            snout_length=1.2, jaw_depth=0.2, crest_type=CrestType.NONE
        )
        serpent_result = generate_head(serpent_config)

        # Dragon head (horns, strong jaw)
        dragon_config = HeadConfig(
            snout_length=0.8,
            jaw_depth=0.5,
            crest_type=CrestType.HORNS,
            crest_size=0.8,
        )
        dragon_result = generate_head(dragon_config)

        # Both should generate successfully
        assert serpent_result.vertex_count > 0
        assert dragon_result.vertex_count > 0
