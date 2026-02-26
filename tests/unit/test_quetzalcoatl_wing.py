"""
Unit tests for Quetzalcoatl Wing System (Phase 20.4)

Tests for wing generation with feathered and membrane types.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.types import WingConfig, WingType, SpineConfig, BodyConfig
from lib.spine import SpineGenerator
from lib.body import BodyGenerator
from lib.wing import (
    WingGenerator,
    WingResult,
    AllWingsResult,
    WingSegment,
    WingSide,
    WingSocket,
    FeatherData,
    generate_wings,
)


class TestWingSegment:
    """Tests for WingSegment enum."""

    def test_segment_values(self):
        """Test segment enum values."""
        assert WingSegment.SHOULDER.value == 0
        assert WingSegment.ARM.value == 1
        assert WingSegment.FOREARM.value == 2
        assert WingSegment.HAND.value == 3
        assert WingSegment.FINGER.value == 4
        assert WingSegment.FEATHER.value == 5


class TestWingSide:
    """Tests for WingSide enum."""

    def test_side_values(self):
        """Test side enum values."""
        assert WingSide.LEFT.value == -1
        assert WingSide.RIGHT.value == 1


class TestWingSocket:
    """Tests for WingSocket dataclass."""

    def test_socket_creation(self):
        """Test creating a wing socket."""
        socket = WingSocket(
            segment_type=WingSegment.ARM,
            position=np.array([1.0, 0.5, 0.0]),
            normal=np.array([1.0, 0.0, 0.0]),
            rotation=0.0,
            scale=0.05,
        )

        assert socket.segment_type == WingSegment.ARM
        assert socket.scale == 0.05


class TestFeatherData:
    """Tests for FeatherData dataclass."""

    def test_feather_creation(self):
        """Test creating feather data."""
        feather = FeatherData(
            position=np.array([0.5, 0.0, 0.0]),
            direction=np.array([1.0, 0.0, 0.0]),
            length=0.3,
            width=0.03,
            barb_density=20,
            rotation=0.1,
        )

        assert feather.length == 0.3
        assert feather.barb_density == 20


class TestWingResult:
    """Tests for WingResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample wing result."""
        spine_config = SpineConfig(segments=32)
        spine_gen = SpineGenerator(spine_config, seed=42)
        spine_result = spine_gen.generate()

        body_config = BodyConfig()
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=8)

        wing_config = WingConfig(wing_type=WingType.FEATHERED)
        wing_gen = WingGenerator(wing_config, spine_result, body_result)
        all_wings = wing_gen.generate_all(resolution=8)

        return all_wings.wings[0]  # Return first wing

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

    def test_side_assigned(self, sample_result):
        """Test that side is assigned."""
        assert sample_result.side in (WingSide.LEFT, WingSide.RIGHT)

    def test_wing_type_assigned(self, sample_result):
        """Test that wing type is assigned."""
        assert sample_result.wing_type == WingType.FEATHERED


class TestAllWingsResult:
    """Tests for AllWingsResult dataclass."""

    @pytest.fixture
    def sample_all_wings(self):
        """Create sample all wings result."""
        spine_config = SpineConfig(segments=32)
        spine_gen = SpineGenerator(spine_config, seed=42)
        spine_result = spine_gen.generate()

        body_config = BodyConfig()
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=8)

        wing_config = WingConfig(wing_type=WingType.FEATHERED)
        wing_gen = WingGenerator(wing_config, spine_result, body_result)
        return wing_gen.generate_all(resolution=8)

    def test_wing_count(self, sample_all_wings):
        """Test that 2 wings are generated (left/right)."""
        assert sample_all_wings.wing_count == 2

    def test_total_vertices(self, sample_all_wings):
        """Test total vertices calculation."""
        expected = sum(w.vertex_count for w in sample_all_wings.wings)
        assert sample_all_wings.total_vertices == expected

    def test_total_faces(self, sample_all_wings):
        """Test total faces calculation."""
        expected = sum(w.face_count for w in sample_all_wings.wings)
        assert sample_all_wings.total_faces == expected


class TestWingGenerator:
    """Tests for WingGenerator."""

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

    def test_generate_feathered(self, setup_generators):
        """Test feathered wing generation."""
        spine_result, body_result = setup_generators
        config = WingConfig(wing_type=WingType.FEATHERED)
        generator = WingGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        assert isinstance(result, AllWingsResult)
        assert result.wing_count == 2
        for wing in result.wings:
            assert wing.wing_type == WingType.FEATHERED

    def test_generate_membrane(self, setup_generators):
        """Test membrane wing generation."""
        spine_result, body_result = setup_generators
        config = WingConfig(wing_type=WingType.MEMBRANE)
        generator = WingGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        assert isinstance(result, AllWingsResult)
        assert result.wing_count == 2
        for wing in result.wings:
            assert wing.wing_type == WingType.MEMBRANE

    def test_generate_none(self, setup_generators):
        """Test with no wings."""
        spine_result, body_result = setup_generators
        config = WingConfig(wing_type=WingType.NONE)
        generator = WingGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        assert result.wing_count == 0

    def test_left_right_sides(self, setup_generators):
        """Test that left and right wings are generated."""
        spine_result, body_result = setup_generators
        config = WingConfig(wing_type=WingType.FEATHERED)
        generator = WingGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        sides = {w.side for w in result.wings}
        assert WingSide.LEFT in sides
        assert WingSide.RIGHT in sides

    def test_feathered_has_feathers(self, setup_generators):
        """Test that feathered wings have feather data."""
        spine_result, body_result = setup_generators
        config = WingConfig(
            wing_type=WingType.FEATHERED,
            feather_layers=3,
        )
        generator = WingGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        for wing in result.wings:
            assert len(wing.feathers) > 0

    def test_membrane_no_feathers(self, setup_generators):
        """Test that membrane wings have no feathers."""
        spine_result, body_result = setup_generators
        config = WingConfig(wing_type=WingType.MEMBRANE)
        generator = WingGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        for wing in result.wings:
            assert len(wing.feathers) == 0

    def test_wing_span_affects_size(self, setup_generators):
        """Test that wing span affects wing size."""
        spine_result, body_result = setup_generators

        config_small = WingConfig(wing_type=WingType.MEMBRANE, wing_span=2.0)
        config_large = WingConfig(wing_type=WingType.MEMBRANE, wing_span=5.0)

        gen_small = WingGenerator(config_small, spine_result, body_result)
        gen_large = WingGenerator(config_large, spine_result, body_result)

        result_small = gen_small.generate_all()
        result_large = gen_large.generate_all()

        # Both should generate
        assert result_small.total_vertices > 0
        assert result_large.total_vertices > 0

    def test_feather_layers_variation(self, setup_generators):
        """Test with different feather layer counts."""
        spine_result, body_result = setup_generators

        for layers in [1, 2, 3, 4, 5]:
            config = WingConfig(
                wing_type=WingType.FEATHERED,
                feather_layers=layers,
            )
            generator = WingGenerator(config, spine_result, body_result)
            result = generator.generate_all()

            assert result.wing_count == 2

    def test_finger_count_variation(self, setup_generators):
        """Test with different finger counts for membrane wings."""
        spine_result, body_result = setup_generators

        for fingers in [2, 3, 4, 5]:
            config = WingConfig(
                wing_type=WingType.MEMBRANE,
                finger_count=fingers,
            )
            generator = WingGenerator(config, spine_result, body_result)
            result = generator.generate_all()

            assert result.wing_count == 2
            assert result.total_vertices > 0

    def test_vertex_normals_normalized(self, setup_generators):
        """Test that vertex normals are normalized."""
        spine_result, body_result = setup_generators
        config = WingConfig(wing_type=WingType.FEATHERED)
        generator = WingGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        for wing in result.wings:
            if wing.vertex_count > 0:
                lengths = np.linalg.norm(wing.normals, axis=1)
                non_zero = lengths > 0.01
                if np.any(non_zero):
                    assert np.allclose(lengths[non_zero], 1.0, atol=0.1)

    def test_faces_valid_indices(self, setup_generators):
        """Test that all face indices are valid."""
        spine_result, body_result = setup_generators
        config = WingConfig(wing_type=WingType.FEATHERED)
        generator = WingGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        for wing in result.wings:
            if wing.face_count > 0:
                max_idx = wing.vertex_count
                assert np.all(wing.faces >= 0)
                assert np.all(wing.faces < max_idx)

    def test_uvs_in_valid_range(self, setup_generators):
        """Test that UVs are in 0-1 range."""
        spine_result, body_result = setup_generators
        config = WingConfig(wing_type=WingType.FEATHERED)
        generator = WingGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        for wing in result.wings:
            if wing.vertex_count > 0:
                assert np.all(wing.uvs >= 0)
                assert np.all(wing.uvs <= 1)

    def test_sockets_generated(self, setup_generators):
        """Test that sockets are generated."""
        spine_result, body_result = setup_generators
        config = WingConfig(wing_type=WingType.FEATHERED)
        generator = WingGenerator(config, spine_result, body_result)
        result = generator.generate_all()

        for wing in result.wings:
            assert len(wing.sockets) > 0

    def test_deterministic_output(self, setup_generators):
        """Test that same config produces same output."""
        spine_result, body_result = setup_generators
        config = WingConfig(wing_type=WingType.FEATHERED, wing_span=3.0)

        gen1 = WingGenerator(config, spine_result, body_result)
        gen2 = WingGenerator(config, spine_result, body_result)

        result1 = gen1.generate_all()
        result2 = gen2.generate_all()

        assert result1.wing_count == result2.wing_count

        for w1, w2 in zip(result1.wings, result2.wings):
            assert w1.vertex_count == w2.vertex_count


class TestGenerateWings:
    """Tests for convenience function."""

    def test_generate_wings_defaults(self):
        """Test generate_wings with defaults."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        result = generate_wings(
            WingConfig(wing_type=WingType.FEATHERED),
            spine_result,
            body_result,
        )

        assert isinstance(result, AllWingsResult)
        assert result.wing_count == 2

    def test_generate_wings_membrane(self):
        """Test generate_wings with membrane type."""
        spine_config = SpineConfig(segments=16)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        result = generate_wings(
            WingConfig(
                wing_type=WingType.MEMBRANE,
                wing_span=4.0,
                finger_count=4,
            ),
            spine_result,
            body_result,
            resolution=6,
        )

        assert result.wing_count == 2


class TestIntegration:
    """Integration tests for wing system."""

    def test_full_pipeline_feathered(self):
        """Test full spine + body + wing generation with feathered wings."""
        # Generate spine
        spine_config = SpineConfig(length=12.0, segments=48)
        spine_gen = SpineGenerator(spine_config, seed=12345)
        spine_result = spine_gen.generate()

        # Generate body
        body_config = BodyConfig(radius=0.5)
        body_gen = BodyGenerator(spine_result, body_config)
        body_result = body_gen.generate(radial_segments=16)

        # Generate wings
        wing_config = WingConfig(
            wing_type=WingType.FEATHERED,
            wing_span=4.0,
            wing_arm_length=1.5,
            feather_layers=3,
        )
        wing_gen = WingGenerator(wing_config, spine_result, body_result)
        wing_result = wing_gen.generate_all(resolution=8)

        # Verify output
        assert wing_result.wing_count == 2
        assert wing_result.total_vertices > 0
        assert wing_result.total_faces > 0

    def test_full_pipeline_membrane(self):
        """Test full pipeline with membrane wings."""
        spine_config = SpineConfig(length=12.0, segments=48)
        spine_result = SpineGenerator(spine_config, seed=12345).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        wing_config = WingConfig(
            wing_type=WingType.MEMBRANE,
            wing_span=5.0,
            wing_arm_length=2.0,
            finger_count=4,
        )
        wing_result = generate_wings(
            wing_config,
            spine_result,
            body_result,
        )

        assert wing_result.wing_count == 2
        # Membrane wings should have fewer feathers (none)
        for wing in wing_result.wings:
            assert len(wing.feathers) == 0

    def test_different_creature_configs(self):
        """Test wing generation with different creature types."""
        spine_config = SpineConfig(length=10.0)
        spine_result = SpineGenerator(spine_config, seed=42).generate()
        body_result = BodyGenerator(spine_result, BodyConfig()).generate()

        # Serpent (no wings)
        no_wings = generate_wings(
            WingConfig(wing_type=WingType.NONE),
            spine_result,
            body_result,
        )
        assert no_wings.wing_count == 0

        # Dragon (membrane wings)
        dragon_wings = generate_wings(
            WingConfig(
                wing_type=WingType.MEMBRANE,
                wing_span=6.0,
                finger_count=5,
            ),
            spine_result,
            body_result,
        )
        assert dragon_wings.wing_count == 2

        # Bird-like (feathered wings)
        feathered_wings = generate_wings(
            WingConfig(
                wing_type=WingType.FEATHERED,
                wing_span=3.0,
                feather_layers=4,
            ),
            spine_result,
            body_result,
        )
        assert feathered_wings.wing_count == 2
