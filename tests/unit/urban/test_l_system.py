"""
Tests for L-System Road Generator

Tests L-system string rewriting and road network generation.
"""

import pytest
from lib.urban.l_system import (
    LSystemRule,
    LSystemConfig,
    LSystemRoads,
    TurtleState,
    ROAD_RULE_SETS,
    SYMBOL_MEANINGS,
    generate_road_network,
)


class TestLSystemRule:
    """Tests for LSystemRule dataclass."""

    def test_create_default(self):
        """Test creating LSystemRule with defaults."""
        rule = LSystemRule()
        assert rule.predecessor == ""
        assert rule.successor == ""
        assert rule.probability == 1.0
        assert rule.condition is None

    def test_create_with_values(self):
        """Test creating LSystemRule with values."""
        rule = LSystemRule(
            predecessor="R",
            successor="R+R",
            probability=0.5,
        )
        assert rule.predecessor == "R"
        assert rule.successor == "R+R"
        assert rule.probability == 0.5

    def test_matches_exact(self):
        """Test rule matching - exact match."""
        rule = LSystemRule(predecessor="R", successor="RR")
        assert rule.matches("R", "R", 0) is True

    def test_matches_different_symbol(self):
        """Test rule matching - different symbol."""
        rule = LSystemRule(predecessor="R", successor="RR")
        assert rule.matches("H", "H", 0) is False


class TestLSystemConfig:
    """Tests for LSystemConfig dataclass."""

    def test_create_default(self):
        """Test creating LSystemConfig with defaults."""
        config = LSystemConfig()
        assert config.angle == 90.0
        assert config.segment_length == 20.0
        assert config.road_width == 10.0
        assert config.variation == 0.1
        assert config.max_iterations == 5

    def test_create_with_values(self):
        """Test creating LSystemConfig with values."""
        config = LSystemConfig(
            angle=60.0,
            segment_length=15.0,
            variation=0.2,
            branching_probability=0.5,
        )
        assert config.angle == 60.0
        assert config.segment_length == 15.0
        assert config.variation == 0.2
        assert config.branching_probability == 0.5


class TestTurtleState:
    """Tests for TurtleState class."""

    def test_create_default(self):
        """Test creating TurtleState with defaults."""
        state = TurtleState()
        assert state.x == 0.0
        assert state.y == 0.0
        assert state.angle == 0.0

    def test_create_with_values(self):
        """Test creating TurtleState with values."""
        state = TurtleState(x=100.0, y=50.0, angle=45.0)
        assert state.x == 100.0
        assert state.y == 50.0
        assert state.angle == 45.0

    def test_copy(self):
        """Test copying TurtleState."""
        state = TurtleState(x=10.0, y=20.0, angle=30.0)
        copy = state.copy()
        assert copy.x == 10.0
        assert copy.y == 20.0
        assert copy.angle == 30.0
        # Modify original, copy should be unchanged
        state.x = 100.0
        assert copy.x == 10.0

    def test_move(self):
        """Test moving turtle forward."""
        state = TurtleState(x=0.0, y=0.0, angle=0.0)
        new_pos = state.move(10.0)
        assert new_pos == (10.0, 0.0)
        assert state.x == 10.0
        assert state.y == 0.0

    def test_move_at_angle(self):
        """Test moving turtle at angle."""
        import math
        state = TurtleState(x=0.0, y=0.0, angle=90.0)
        new_pos = state.move(10.0)
        assert new_pos[0] == pytest.approx(0.0, abs=0.001)
        assert new_pos[1] == pytest.approx(10.0, abs=0.001)

    def test_turn(self):
        """Test turning turtle."""
        state = TurtleState(angle=0.0)
        state.turn(90.0)
        assert state.angle == 90.0
        state.turn(-45.0)
        assert state.angle == 45.0


class TestRoadRuleSets:
    """Tests for predefined road rule sets."""

    def test_rule_sets_exist(self):
        """Test that ROAD_RULE_SETS is populated."""
        assert isinstance(ROAD_RULE_SETS, dict)
        assert len(ROAD_RULE_SETS) > 0

    def test_grid_rules(self):
        """Test grid rule set."""
        rules = ROAD_RULE_SETS.get("grid")
        assert rules is not None
        assert len(rules) > 0

    def test_organic_rules(self):
        """Test organic rule set."""
        rules = ROAD_RULE_SETS.get("organic")
        assert rules is not None
        assert len(rules) > 0

    def test_suburban_rules(self):
        """Test suburban rule set."""
        rules = ROAD_RULE_SETS.get("suburban")
        assert rules is not None
        assert len(rules) > 0

    def test_highway_rules(self):
        """Test highway rule set."""
        rules = ROAD_RULE_SETS.get("highway")
        assert rules is not None
        assert len(rules) > 0


class TestSymbolMeanings:
    """Tests for symbol meanings."""

    def test_symbol_meanings_exist(self):
        """Test that SYMBOL_MEANINGS is populated."""
        assert isinstance(SYMBOL_MEANINGS, dict)
        assert len(SYMBOL_MEANINGS) > 0

    def test_road_symbol(self):
        """Test R symbol meaning."""
        assert SYMBOL_MEANINGS.get("R") == "road_forward"

    def test_turn_symbols(self):
        """Test turn symbol meanings."""
        assert SYMBOL_MEANINGS.get("+") == "turn_left"
        assert SYMBOL_MEANINGS.get("-") == "turn_right"

    def test_branch_symbols(self):
        """Test branch symbol meanings."""
        assert "[" in SYMBOL_MEANINGS
        assert "]" in SYMBOL_MEANINGS


class TestLSystemRoads:
    """Tests for LSystemRoads class."""

    def test_init(self):
        """Test LSystemRoads initialization."""
        generator = LSystemRoads()
        assert generator.config is not None

    def test_init_with_seed(self):
        """Test initialization with seed."""
        generator = LSystemRoads(seed=42)
        assert generator.seed == 42

    def test_init_with_config(self):
        """Test initialization with config."""
        config = LSystemConfig(angle=60.0)
        generator = LSystemRoads(config=config)
        assert generator.config.angle == 60.0

    def test_generate_simple(self):
        """Test simple road generation."""
        generator = LSystemRoads(seed=42)
        network = generator.generate(
            axiom="R",
            iterations=1,
            pattern="grid",
        )
        assert network is not None
        assert len(network.nodes) > 0

    def test_generate_grid_pattern(self):
        """Test grid pattern generation."""
        generator = LSystemRoads(seed=42)
        network = generator.generate(
            axiom="R+R+R+R",
            iterations=2,
            pattern="grid",
            dimensions=(200, 200),
        )
        assert network is not None
        assert network.dimensions == (200, 200)

    def test_generate_organic_pattern(self):
        """Test organic pattern generation."""
        generator = LSystemRoads(seed=42)
        network = generator.generate(
            axiom="R~R~R~R",
            iterations=2,
            pattern="organic",
        )
        assert network is not None

    def test_generate_reproducible(self):
        """Test that same seed produces same output."""
        gen1 = LSystemRoads(seed=12345)
        gen2 = LSystemRoads(seed=12345)

        net1 = gen1.generate("R", 2, "grid")
        net2 = gen2.generate("R", 2, "grid")

        # Same seed should produce same number of nodes/edges
        assert len(net1.nodes) == len(net2.nodes)

    def test_generate_with_start_position(self):
        """Test generation with custom start position."""
        generator = LSystemRoads(seed=42)
        network = generator.generate(
            axiom="R",
            iterations=1,
            start_position=(50.0, 50.0),
        )
        assert network is not None


class TestGenerateRoadNetworkFunction:
    """Tests for generate_road_network convenience function."""

    def test_generate_default(self):
        """Test generating with defaults."""
        network = generate_road_network()
        assert network is not None
        assert len(network.nodes) > 0

    def test_generate_grid(self):
        """Test generating grid network."""
        network = generate_road_network(
            pattern="grid",
            dimensions=(100, 100),
            iterations=2,
        )
        assert network is not None
        assert network.dimensions == (100, 100)

    def test_generate_organic(self):
        """Test generating organic network."""
        network = generate_road_network(pattern="organic")
        assert network is not None

    def test_generate_suburban(self):
        """Test generating suburban network."""
        network = generate_road_network(pattern="suburban")
        assert network is not None

    def test_generate_highway(self):
        """Test generating highway network."""
        network = generate_road_network(pattern="highway")
        assert network is not None

    def test_generate_downtown(self):
        """Test generating downtown network."""
        network = generate_road_network(pattern="downtown")
        assert network is not None

    def test_generate_with_seed(self):
        """Test generating with seed."""
        network = generate_road_network(seed=42)
        assert network is not None
        assert network.seed == 42


class TestLSystemEdgeCases:
    """Edge case tests for L-system generator."""

    def test_empty_axiom(self):
        """Test with empty axiom."""
        generator = LSystemRoads()
        network = generator.generate(axiom="", iterations=1)
        # Should still produce something (at least start node)
        assert network is not None

    def test_zero_iterations(self):
        """Test with zero iterations."""
        generator = LSystemRoads()
        network = generator.generate(axiom="R", iterations=0)
        assert network is not None

    def test_high_iterations(self):
        """Test with high iteration count."""
        generator = LSystemRoads(seed=42)
        network = generator.generate(
            axiom="R",
            iterations=4,
            dimensions=(500, 500),
        )
        # Should still work, though may be complex
        assert network is not None

    def test_very_small_dimensions(self):
        """Test with small dimensions."""
        generator = LSystemRoads(seed=42)
        network = generator.generate(
            axiom="R",
            iterations=1,
            dimensions=(10, 10),
        )
        assert network is not None

    def test_unknown_pattern(self):
        """Test with unknown pattern (should fall back to grid)."""
        network = generate_road_network(pattern="nonexistent_pattern")
        assert network is not None
