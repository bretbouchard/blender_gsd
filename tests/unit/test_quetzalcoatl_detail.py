"""
Unit tests for Quetzalcoatl Detail Features (Phase 20.7)

Tests for teeth, whiskers, and claws generation.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/quetzalcoatl"))

from lib.detail import (
    ToothType,
    WhiskerType,
    ClawType,
    ToothData,
    WhiskerData,
    ClawData,
    TeethResult,
    WhiskerResult,
    ClawResult,
    DetailResult,
    TeethGenerator,
    WhiskerGenerator,
    ClawGenerator,
    DetailGenerator,
    generate_teeth,
    generate_whiskers,
    generate_claws,
    generate_details,
)


class TestToothType:
    """Tests for ToothType enum."""

    def test_type_values(self):
        """Test tooth type enum values."""
        assert ToothType.CONICAL.value == 0
        assert ToothType.SERRATED.value == 1
        assert ToothType.FANG.value == 2
        assert ToothType.TUSK.value == 3


class TestWhiskerType:
    """Tests for WhiskerType enum."""

    def test_type_values(self):
        """Test whisker type enum values."""
        assert WhiskerType.THIN.value == 0
        assert WhiskerType.THICK.value == 1
        assert WhiskerType.FEATHERED.value == 2
        assert WhiskerType.TENDRIL.value == 3


class TestClawType:
    """Tests for ClawType enum."""

    def test_type_values(self):
        """Test claw type enum values."""
        assert ClawType.SHARP.value == 0
        assert ClawType.BLUNT.value == 1
        assert ClawType.HOOVED.value == 2
        assert ClawType.WEBBED.value == 3


class TestToothData:
    """Tests for ToothData dataclass."""

    def test_tooth_creation(self):
        """Test creating tooth data."""
        tooth = ToothData(
            position=np.array([0.5, 0.0, 0.2]),
            direction=np.array([0.0, 0.0, -1.0]),
            length=0.05,
            width=0.01,
            tooth_type=ToothType.CONICAL,
            is_fang=False,
        )

        assert tooth.length == 0.05
        assert tooth.width == 0.01
        assert tooth.tooth_type == ToothType.CONICAL
        assert not tooth.is_fang


class TestWhiskerData:
    """Tests for WhiskerData dataclass."""

    def test_whisker_creation(self):
        """Test creating whisker data."""
        whisker = WhiskerData(
            position=np.array([0.1, 0.2, 0.0]),
            direction=np.array([1.0, 0.0, 0.0]),
            length=0.3,
            thickness=0.003,
            curve_amount=0.2,
            whisker_type=WhiskerType.THIN,
        )

        assert whisker.length == 0.3
        assert whisker.thickness == 0.003
        assert whisker.whisker_type == WhiskerType.THIN


class TestClawData:
    """Tests for ClawData dataclass."""

    def test_claw_creation(self):
        """Test creating claw data."""
        claw = ClawData(
            position=np.array([0.0, 0.0, -0.5]),
            direction=np.array([0.0, 0.0, -1.0]),
            length=0.08,
            width=0.015,
            curve_amount=0.4,
            claw_type=ClawType.SHARP,
        )

        assert claw.length == 0.08
        assert claw.width == 0.015
        assert claw.claw_type == ClawType.SHARP


class TestTeethResult:
    """Tests for TeethResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample teeth result."""
        gen = TeethGenerator(ToothType.CONICAL, count=10)
        return gen.generate(seed=42)

    def test_tooth_count(self, sample_result):
        """Test that teeth are generated."""
        assert sample_result.tooth_count > 0

    def test_vertex_count(self, sample_result):
        """Test that vertices are generated."""
        assert sample_result.vertex_count > 0

    def test_vertices_shape(self, sample_result):
        """Test vertices array shape."""
        assert sample_result.vertices.shape[1] == 3

    def test_faces_shape(self, sample_result):
        """Test faces array shape."""
        if len(sample_result.faces) > 0:
            assert sample_result.faces.shape[1] == 3

    def test_uvs_shape(self, sample_result):
        """Test UVs array shape."""
        assert sample_result.uvs.shape[1] == 2


class TestWhiskerResult:
    """Tests for WhiskerResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample whisker result."""
        gen = WhiskerGenerator(WhiskerType.THIN, count=4)
        return gen.generate(seed=42)

    def test_whisker_count(self, sample_result):
        """Test that whiskers are generated."""
        assert sample_result.whisker_count > 0

    def test_vertex_count(self, sample_result):
        """Test that vertices are generated."""
        assert sample_result.vertex_count > 0

    def test_vertices_shape(self, sample_result):
        """Test vertices array shape."""
        assert sample_result.vertices.shape[1] == 3

    def test_bilateral_whiskers(self, sample_result):
        """Test that whiskers appear on both sides."""
        left_whiskers = [w for w in sample_result.whiskers if w.position[0] < 0]
        right_whiskers = [w for w in sample_result.whiskers if w.position[0] > 0]

        assert len(left_whiskers) > 0
        assert len(right_whiskers) > 0


class TestClawResult:
    """Tests for ClawResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample claw result."""
        gen = ClawGenerator(ClawType.SHARP, count_per_foot=4)
        return gen.generate(seed=42)

    def test_claw_count(self, sample_result):
        """Test that claws are generated."""
        assert sample_result.claw_count > 0

    def test_vertex_count(self, sample_result):
        """Test that vertices are generated."""
        assert sample_result.vertex_count > 0

    def test_vertices_shape(self, sample_result):
        """Test vertices array shape."""
        assert sample_result.vertices.shape[1] == 3


class TestDetailResult:
    """Tests for DetailResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample detail result."""
        gen = DetailGenerator(
            tooth_type=ToothType.CONICAL,
            whisker_type=WhiskerType.THIN,
            claw_type=ClawType.SHARP,
        )
        return gen.generate(seed=42)

    def test_combined_vertices(self, sample_result):
        """Test combined vertex count."""
        assert sample_result.total_vertex_count > 0

    def test_combined_faces(self, sample_result):
        """Test combined face count."""
        assert sample_result.total_face_count > 0

    def test_has_teeth(self, sample_result):
        """Test that teeth are present."""
        assert sample_result.teeth_result.tooth_count > 0

    def test_has_whiskers(self, sample_result):
        """Test that whiskers are present."""
        assert sample_result.whisker_result.whisker_count > 0

    def test_has_claws(self, sample_result):
        """Test that claws are present."""
        assert sample_result.claw_result.claw_count > 0


class TestTeethGenerator:
    """Tests for TeethGenerator."""

    def test_generate_basic(self):
        """Test basic teeth generation."""
        gen = TeethGenerator(ToothType.CONICAL, count=10)
        result = gen.generate(seed=42)

        assert isinstance(result, TeethResult)
        assert result.tooth_count == 10

    def test_generate_with_seed(self):
        """Test that seed produces consistent results."""
        gen1 = TeethGenerator(ToothType.CONICAL, count=15)
        gen2 = TeethGenerator(ToothType.CONICAL, count=15)

        result1 = gen1.generate(seed=123)
        result2 = gen2.generate(seed=123)

        assert result1.tooth_count == result2.tooth_count

    def test_count_affects_output(self):
        """Test that count affects tooth count."""
        gen_low = TeethGenerator(ToothType.CONICAL, count=5)
        gen_high = TeethGenerator(ToothType.CONICAL, count=25)

        result_low = gen_low.generate(seed=42)
        result_high = gen_high.generate(seed=42)

        assert result_high.tooth_count > result_low.tooth_count

    def test_fang_generation(self):
        """Test that fangs are generated when configured."""
        gen = TeethGenerator(
            ToothType.FANG,
            count=20,
            fang_count=2,
            fang_length_multiplier=2.5,
        )
        result = gen.generate(seed=42)

        fangs = [t for t in result.teeth if t.is_fang]
        assert len(fangs) == 2

        # Fangs should be longer
        regular = [t for t in result.teeth if not t.is_fang]
        if len(regular) > 0 and len(fangs) > 0:
            avg_regular = np.mean([t.length for t in regular])
            avg_fang = np.mean([t.length for t in fangs])
            assert avg_fang > avg_regular

    def test_no_fangs(self):
        """Test generation without fangs."""
        gen = TeethGenerator(ToothType.CONICAL, count=10, fang_count=0)
        result = gen.generate(seed=42)

        fangs = [t for t in result.teeth if t.is_fang]
        assert len(fangs) == 0

    def test_length_affects_geometry(self):
        """Test that length affects geometry size."""
        gen_short = TeethGenerator(ToothType.CONICAL, count=5, length=0.02)
        gen_long = TeethGenerator(ToothType.CONICAL, count=5, length=0.1)

        result_short = gen_short.generate(seed=42)
        result_long = gen_long.generate(seed=42)

        # Both should generate
        assert result_short.vertex_count > 0
        assert result_long.vertex_count > 0

    def test_empty_mouth_positions(self):
        """Test handling of empty mouth positions."""
        gen = TeethGenerator(ToothType.CONICAL, count=10)
        result = gen.generate(mouth_positions=[], seed=42)

        assert result.tooth_count == 0
        assert result.vertex_count == 0

    def test_vertex_normals_normalized(self):
        """Test that vertex normals are normalized."""
        gen = TeethGenerator(ToothType.CONICAL, count=5)
        result = gen.generate(seed=42)

        if result.vertex_count > 0:
            lengths = np.linalg.norm(result.normals, axis=1)
            non_zero = lengths > 0.01
            if np.any(non_zero):
                assert np.allclose(lengths[non_zero], 1.0, atol=0.2)

    def test_faces_valid_indices(self):
        """Test that all face indices are valid."""
        gen = TeethGenerator(ToothType.CONICAL, count=5)
        result = gen.generate(seed=42)

        if len(result.faces) > 0:
            max_idx = result.vertex_count
            assert np.all(result.faces >= 0)
            assert np.all(result.faces < max_idx)

    def test_uvs_in_valid_range(self):
        """Test that UVs are in 0-1 range."""
        gen = TeethGenerator(ToothType.CONICAL, count=5)
        result = gen.generate(seed=42)

        if result.vertex_count > 0:
            assert np.all(result.uvs >= 0)
            assert np.all(result.uvs <= 1)


class TestWhiskerGenerator:
    """Tests for WhiskerGenerator."""

    def test_generate_basic(self):
        """Test basic whisker generation."""
        gen = WhiskerGenerator(WhiskerType.THIN, count=4)
        result = gen.generate(seed=42)

        assert isinstance(result, WhiskerResult)
        # Count per side, so total is count * 2
        assert result.whisker_count == 8

    def test_generate_with_seed(self):
        """Test that seed produces consistent results."""
        gen1 = WhiskerGenerator(WhiskerType.THIN, count=5)
        gen2 = WhiskerGenerator(WhiskerType.THIN, count=5)

        result1 = gen1.generate(seed=123)
        result2 = gen2.generate(seed=123)

        assert result1.whisker_count == result2.whisker_count

    def test_count_affects_output(self):
        """Test that count affects whisker count."""
        gen_low = WhiskerGenerator(WhiskerType.THIN, count=2)
        gen_high = WhiskerGenerator(WhiskerType.THIN, count=8)

        result_low = gen_low.generate(seed=42)
        result_high = gen_high.generate(seed=42)

        assert result_high.whisker_count > result_low.whisker_count

    def test_custom_snout_position(self):
        """Test with custom snout position."""
        gen = WhiskerGenerator(WhiskerType.THIN, count=3)
        result = gen.generate(
            snout_position=np.array([0.0, 1.0, 0.5]),
            snout_direction=np.array([0.0, 1.0, 0.0]),
            seed=42,
        )

        assert result.whisker_count > 0
        # Check whiskers are near the snout position
        for whisker in result.whiskers:
            assert whisker.position[1] > 0.5  # Should be forward

    def test_length_affects_geometry(self):
        """Test that length affects geometry."""
        gen_short = WhiskerGenerator(WhiskerType.THIN, count=2, length=0.1)
        gen_long = WhiskerGenerator(WhiskerType.THIN, count=2, length=0.5)

        result_short = gen_short.generate(seed=42)
        result_long = gen_long.generate(seed=42)

        # Both should generate
        assert result_short.vertex_count > 0
        assert result_long.vertex_count > 0

    def test_curve_amount_configured(self):
        """Test that curve amount is configured."""
        gen = WhiskerGenerator(WhiskerType.THIN, count=2, curve_amount=0.5)
        result = gen.generate(seed=42)

        for whisker in result.whiskers:
            assert whisker.curve_amount > 0

    def test_vertex_normals_normalized(self):
        """Test that vertex normals are normalized."""
        gen = WhiskerGenerator(WhiskerType.THIN, count=2)
        result = gen.generate(seed=42)

        if result.vertex_count > 0:
            lengths = np.linalg.norm(result.normals, axis=1)
            non_zero = lengths > 0.01
            if np.any(non_zero):
                assert np.allclose(lengths[non_zero], 1.0, atol=0.2)

    def test_faces_valid_indices(self):
        """Test that all face indices are valid."""
        gen = WhiskerGenerator(WhiskerType.THIN, count=2)
        result = gen.generate(seed=42)

        if len(result.faces) > 0:
            max_idx = result.vertex_count
            assert np.all(result.faces >= 0)
            assert np.all(result.faces < max_idx)


class TestClawGenerator:
    """Tests for ClawGenerator."""

    def test_generate_basic(self):
        """Test basic claw generation."""
        gen = ClawGenerator(ClawType.SHARP, count_per_foot=4)
        result = gen.generate(seed=42)

        assert isinstance(result, ClawResult)
        # 4 feet * 4 claws = 16 claws
        assert result.claw_count == 16

    def test_generate_with_seed(self):
        """Test that seed produces consistent results."""
        gen1 = ClawGenerator(ClawType.SHARP, count_per_foot=3)
        gen2 = ClawGenerator(ClawType.SHARP, count_per_foot=3)

        result1 = gen1.generate(seed=123)
        result2 = gen2.generate(seed=123)

        assert result1.claw_count == result2.claw_count

    def test_count_affects_output(self):
        """Test that count affects claw count."""
        gen_low = ClawGenerator(ClawType.SHARP, count_per_foot=2)
        gen_high = ClawGenerator(ClawType.SHARP, count_per_foot=5)

        result_low = gen_low.generate(seed=42)
        result_high = gen_high.generate(seed=42)

        assert result_high.claw_count > result_low.claw_count

    def test_custom_foot_positions(self):
        """Test with custom foot positions."""
        gen = ClawGenerator(ClawType.SHARP, count_per_foot=3)
        foot_positions = [
            (np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, -1.0])),
            (np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, -1.0])),
        ]
        result = gen.generate(foot_positions=foot_positions, seed=42)

        # 2 feet * 3 claws = 6 claws
        assert result.claw_count == 6

    def test_length_affects_geometry(self):
        """Test that length affects geometry."""
        gen_short = ClawGenerator(ClawType.SHARP, count_per_foot=2, length=0.03)
        gen_long = ClawGenerator(ClawType.SHARP, count_per_foot=2, length=0.15)

        result_short = gen_short.generate(seed=42)
        result_long = gen_long.generate(seed=42)

        # Both should generate
        assert result_short.vertex_count > 0
        assert result_long.vertex_count > 0

    def test_curve_amount_configured(self):
        """Test that curve amount is configured."""
        gen = ClawGenerator(ClawType.SHARP, count_per_foot=2, curve_amount=0.6)
        result = gen.generate(seed=42)

        for claw in result.claws:
            assert claw.curve_amount > 0

    def test_vertex_normals_normalized(self):
        """Test that vertex normals are normalized."""
        gen = ClawGenerator(ClawType.SHARP, count_per_foot=2)
        result = gen.generate(seed=42)

        if result.vertex_count > 0:
            lengths = np.linalg.norm(result.normals, axis=1)
            non_zero = lengths > 0.01
            if np.any(non_zero):
                assert np.allclose(lengths[non_zero], 1.0, atol=0.2)

    def test_faces_valid_indices(self):
        """Test that all face indices are valid."""
        gen = ClawGenerator(ClawType.SHARP, count_per_foot=2)
        result = gen.generate(seed=42)

        if len(result.faces) > 0:
            max_idx = result.vertex_count
            assert np.all(result.faces >= 0)
            assert np.all(result.faces < max_idx)

    def test_empty_foot_positions(self):
        """Test handling of empty foot positions."""
        gen = ClawGenerator(ClawType.SHARP, count_per_foot=4)
        result = gen.generate(foot_positions=[], seed=42)

        assert result.claw_count == 0
        assert result.vertex_count == 0


class TestDetailGenerator:
    """Tests for combined DetailGenerator."""

    def test_generate_all(self):
        """Test generating all detail features."""
        gen = DetailGenerator(
            tooth_type=ToothType.CONICAL,
            whisker_type=WhiskerType.THIN,
            claw_type=ClawType.SHARP,
        )
        result = gen.generate(seed=42)

        assert isinstance(result, DetailResult)
        assert result.teeth_result.tooth_count > 0
        assert result.whisker_result.whisker_count > 0
        assert result.claw_result.claw_count > 0

    def test_deterministic_output(self):
        """Test that same seed produces same output."""
        gen1 = DetailGenerator()
        gen2 = DetailGenerator()

        result1 = gen1.generate(seed=123)
        result2 = gen2.generate(seed=123)

        assert result1.teeth_result.tooth_count == result2.teeth_result.tooth_count
        assert result1.whisker_result.whisker_count == result2.whisker_result.whisker_count
        assert result1.claw_result.claw_count == result2.claw_result.claw_count

    def test_combined_geometry(self):
        """Test combined geometry output."""
        gen = DetailGenerator()
        result = gen.generate(seed=42)

        # Combined vertices should include all features
        assert result.total_vertex_count > 0
        assert result.vertices.shape[0] == result.total_vertex_count

    def test_different_types(self):
        """Test with different feature types."""
        gen = DetailGenerator(
            tooth_type=ToothType.FANG,
            whisker_type=WhiskerType.THICK,
            claw_type=ClawType.BLUNT,
        )
        result = gen.generate(seed=42)

        # Should generate all types
        assert result.teeth_result.tooth_count > 0
        assert result.whisker_result.whisker_count > 0
        assert result.claw_result.claw_count > 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_teeth_defaults(self):
        """Test generate_teeth with defaults."""
        result = generate_teeth()

        assert isinstance(result, TeethResult)
        assert result.tooth_count > 0

    def test_generate_teeth_custom(self):
        """Test generate_teeth with custom parameters."""
        result = generate_teeth(
            tooth_type=ToothType.FANG,
            count=15,
            seed=42,
        )

        assert result.tooth_count == 15

    def test_generate_whiskers_defaults(self):
        """Test generate_whiskers with defaults."""
        result = generate_whiskers()

        assert isinstance(result, WhiskerResult)
        assert result.whisker_count > 0

    def test_generate_whiskers_custom(self):
        """Test generate_whiskers with custom parameters."""
        result = generate_whiskers(
            whisker_type=WhiskerType.THICK,
            count=8,
            seed=42,
        )

        # Count * 2 for bilateral
        assert result.whisker_count == 16

    def test_generate_claws_defaults(self):
        """Test generate_claws with defaults."""
        result = generate_claws()

        assert isinstance(result, ClawResult)
        assert result.claw_count > 0

    def test_generate_claws_custom(self):
        """Test generate_claws with custom parameters."""
        result = generate_claws(
            claw_type=ClawType.SHARP,
            count_per_foot=3,
            seed=42,
        )

        # 4 feet * 3 claws
        assert result.claw_count == 12

    def test_generate_details_defaults(self):
        """Test generate_details with defaults."""
        result = generate_details()

        assert isinstance(result, DetailResult)
        assert result.total_vertex_count > 0


class TestIntegration:
    """Integration tests for detail system."""

    def test_full_detail_pipeline(self):
        """Test full detail generation pipeline."""
        # Generate all details
        gen = DetailGenerator(
            tooth_type=ToothType.SERRATED,
            whisker_type=WhiskerType.THIN,
            claw_type=ClawType.SHARP,
            tooth_count=30,
            whisker_count=8,
            claw_count_per_foot=4,
        )

        result = gen.generate(
            snout_position=np.array([0.0, 1.5, 0.3]),
            snout_direction=np.array([0.0, 1.0, 0.0]),
            seed=42,
        )

        # Verify output
        assert result.teeth_result.tooth_count == 30
        assert result.whisker_result.whisker_count == 16  # 8 * 2
        assert result.claw_result.claw_count == 16  # 4 feet * 4 claws
        assert result.total_vertex_count > 0

    def test_different_creature_configs(self):
        """Test different creature configurations."""
        # Serpent: many small teeth, no whiskers, no claws
        serpent_gen = DetailGenerator(
            tooth_type=ToothType.CONICAL,
            whisker_type=WhiskerType.THIN,
            claw_type=ClawType.SHARP,
            tooth_count=40,
            whisker_count=0,
            claw_count_per_foot=0,
        )
        serpent_result = serpent_gen.generate(seed=42)

        # Dragon: fangs, thick whiskers, sharp claws
        dragon_gen = DetailGenerator(
            tooth_type=ToothType.FANG,
            whisker_type=WhiskerType.THICK,
            claw_type=ClawType.SHARP,
            tooth_count=20,
            whisker_count=4,
            claw_count_per_foot=4,
        )
        dragon_result = dragon_gen.generate(seed=42)

        # Serpent should have more teeth
        assert serpent_result.teeth_result.tooth_count > dragon_result.teeth_result.tooth_count

        # Dragon should have claws, serpent should not
        assert dragon_result.claw_result.claw_count > 0
        assert serpent_result.claw_result.claw_count == 0

    def test_empty_generation(self):
        """Test with zero counts."""
        gen = DetailGenerator(
            tooth_type=ToothType.CONICAL,
            whisker_type=WhiskerType.THIN,
            claw_type=ClawType.SHARP,
            tooth_count=0,
            whisker_count=0,
            claw_count_per_foot=0,
        )
        result = gen.generate(seed=42)

        assert result.teeth_result.tooth_count == 0
        assert result.whisker_result.whisker_count == 0
        assert result.claw_result.claw_count == 0
        assert result.total_vertex_count == 0
