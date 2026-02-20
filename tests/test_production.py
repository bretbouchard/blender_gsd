"""
Tests for Production Orchestrator

Unit tests for production types, loader, validator, and execution engine.

Run with: pytest tests/test_production.py -v
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.production.production_types import (
    ProductionMeta,
    CharacterConfig,
    LocationConfig,
    ShotConfig,
    StyleConfig,
    RetroConfig,
    OutputFormat,
    RenderSettings,
    ProductionConfig,
    ValidationIssue,
    ValidationResult,
    ExecutionState,
    ProductionResult,
    ParallelConfig,
    ExecutionPhase,
    ExecutionStatus,
    ValidationSeverity,
    EXECUTION_PHASES,
    get_output_format_preset,
    OUTPUT_FORMAT_PRESETS,
)

from lib.production.production_loader import (
    load_production,
    load_production_from_dir,
    resolve_production,
    expand_shots,
    save_production,
    create_production_from_template,
    list_productions,
    get_production_info,
    estimate_production_time,
)

from lib.production.production_validator import (
    validate_production,
    validate_characters,
    validate_locations,
    validate_shots,
    validate_dependencies,
    validate_timeline,
    validate_outputs,
    validate_for_execution,
)

from lib.production.execution_engine import (
    ExecutionEngine,
    execute_production,
)

from lib.production.parallel_executor import (
    analyze_dependencies,
    create_execution_graph,
    get_parallel_estimate,
    optimize_worker_count,
    ParallelExecutor,
    BatchProcessor,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


@pytest.fixture
def sample_production_config():
    """Create a sample production config."""
    return ProductionConfig(
        meta=ProductionMeta(
            title="Test Production",
            author="Test Author",
            description="A test production",
        ),
        style=StyleConfig(
            preset="cinematic",
            mood="dramatic",
        ),
        characters={
            "hero": CharacterConfig(
                name="Hero",
                model="assets/hero.blend",
                wardrobe_assignments={"scenes_1_5": "hero_casual"},
            ),
        },
        locations={
            "warehouse": LocationConfig(
                name="Warehouse",
                preset="industrial",
                hdri="warehouse_4k",
            ),
        },
        shots=[
            ShotConfig(name="shot_001", template="hero_cu", scene=1, character="hero"),
            ShotConfig(name="shot_002", template="establishing_wide", scene=1, location="warehouse"),
            ShotConfig(name="shot_003", template="hero_cu", scene=2, character="hero"),
        ],
        render_settings=RenderSettings(
            engine="CYCLES",
            samples=128,
        ),
        outputs=[
            OutputFormat(
                name="Master",
                format="streaming_1080p",
                resolution=(1920, 1080),
            ),
        ],
    )


@pytest.fixture
def sample_yaml_content():
    """Sample YAML content for testing."""
    return """
production:
  meta:
    title: "My Test Film"
    version: "1.0.0"
    author: "Test Author"
    description: "A test production"

  style:
    preset: cinematic
    mood: dramatic

  characters:
    hero:
      name: Hero
      model: assets/hero.blend
      wardrobe_assignments:
        scenes_1_5: hero_casual

  locations:
    warehouse:
      name: Warehouse
      preset: industrial

  shots:
    - name: shot_001
      template: hero_cu
      scene: 1
      character: hero
    - name: shot_002
      template: establishing_wide
      scene: 1
      location: warehouse

  render_settings:
    engine: CYCLES
    samples: 128

  outputs:
    - name: Master
      format: streaming_1080p
      resolution: [1920, 1080]
"""


# =============================================================================
# Production Types Tests
# =============================================================================

class TestProductionMeta:
    """Tests for ProductionMeta."""

    def test_create(self):
        """Test creating ProductionMeta."""
        meta = ProductionMeta(
            title="Test",
            author="Author",
        )
        assert meta.title == "Test"
        assert meta.author == "Author"
        assert meta.production_id != ""

    def test_to_dict(self):
        """Test serialization."""
        meta = ProductionMeta(title="Test")
        data = meta.to_dict()
        assert data["title"] == "Test"
        assert "production_id" in data

    def test_from_dict(self):
        """Test deserialization."""
        data = {"title": "Test", "author": "Author"}
        meta = ProductionMeta.from_dict(data)
        assert meta.title == "Test"
        assert meta.author == "Author"

    def test_touch(self):
        """Test touch updates timestamp."""
        meta = ProductionMeta(title="Test")
        old_modified = meta.modified
        meta.touch()
        assert meta.modified != old_modified


class TestCharacterConfig:
    """Tests for CharacterConfig."""

    def test_create(self):
        """Test creating CharacterConfig."""
        char = CharacterConfig(
            name="Hero",
            model="hero.blend",
        )
        assert char.name == "Hero"
        assert char.model == "hero.blend"

    def test_get_costume_for_scene(self):
        """Test costume lookup by scene."""
        char = CharacterConfig(
            name="Hero",
            wardrobe_assignments={
                "scenes_1_5": "casual",
                "scenes_6_10": "formal",
                "11-15": "action",
            },
        )
        assert char.get_costume_for_scene(3) == "casual"
        assert char.get_costume_for_scene(7) == "formal"
        assert char.get_costume_for_scene(12) == "action"
        assert char.get_costume_for_scene(100) is None


class TestShotConfig:
    """Tests for ShotConfig."""

    def test_create(self):
        """Test creating ShotConfig."""
        shot = ShotConfig(
            name="shot_001",
            template="hero_cu",
            scene=1,
            character="hero",
        )
        assert shot.name == "shot_001"
        assert shot.scene == 1

    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        shot = ShotConfig(
            name="shot_001",
            template="hero_cu",
            scene=1,
            frame_range=(1, 120),
        )
        data = shot.to_dict()
        restored = ShotConfig.from_dict(data)
        assert restored.name == shot.name
        assert restored.frame_range == shot.frame_range


class TestOutputFormat:
    """Tests for OutputFormat."""

    def test_create(self):
        """Test creating OutputFormat."""
        output = OutputFormat(
            name="Master",
            format="streaming_1080p",
            resolution=(1920, 1080),
        )
        assert output.name == "Master"
        assert output.resolution == (1920, 1080)

    def test_with_retro_config(self):
        """Test output with retro config."""
        output = OutputFormat(
            name="16-bit",
            format="16bit_game",
            retro_config=RetroConfig(
                enabled=True,
                palette="snes",
            ),
        )
        data = output.to_dict()
        assert data["retro_config"]["enabled"] is True
        assert data["retro_config"]["palette"] == "snes"


class TestProductionConfig:
    """Tests for ProductionConfig."""

    def test_create(self, sample_production_config):
        """Test creating ProductionConfig."""
        assert sample_production_config.meta.title == "Test Production"
        assert len(sample_production_config.characters) == 1
        assert len(sample_production_config.shots) == 3

    def test_get_shot_count(self, sample_production_config):
        """Test shot count with variations."""
        count = sample_production_config.get_shot_count()
        assert count == 3  # 3 shots, no variations

        # Add variations
        sample_production_config.shots[0].variations = 2
        count = sample_production_config.get_shot_count()
        assert count == 5  # 3 shots + 2 variations

    def test_get_scenes(self, sample_production_config):
        """Test getting scene numbers."""
        scenes = sample_production_config.get_scenes()
        assert scenes == [1, 2]


class TestValidationTypes:
    """Tests for validation types."""

    def test_validation_issue(self):
        """Test ValidationIssue."""
        issue = ValidationIssue(
            path="characters.hero.model",
            severity="error",
            message="File not found",
        )
        assert issue.is_error()
        assert not issue.is_warning()

    def test_validation_result(self):
        """Test ValidationResult."""
        result = ValidationResult(valid=True)
        assert result.valid

        result.add_error("test.path", "Test error")
        assert not result.valid
        assert len(result.errors) == 1

        result.add_warning("test.path", "Test warning")
        assert len(result.warnings) == 1


class TestExecutionState:
    """Tests for ExecutionState."""

    def test_create(self):
        """Test creating ExecutionState."""
        state = ExecutionState(
            production_id="test-123",
            current_phase=ExecutionPhase.VALIDATE.value,
        )
        assert state.production_id == "test-123"
        assert state.status == ExecutionStatus.PENDING.value

    def test_advance_phase(self):
        """Test phase advancement."""
        state = ExecutionState()
        assert state.current_phase == ExecutionPhase.VALIDATE.value

        state.advance_phase()
        assert state.current_phase == ExecutionPhase.PREPARE.value

    def test_complete_shot(self):
        """Test shot completion tracking."""
        state = ExecutionState()
        state.fail_shot(0)  # First fail it
        assert 0 in state.failed_shots

        state.complete_shot(0)  # Then complete it
        assert 0 in state.completed_shots
        assert 0 not in state.failed_shots


class TestOutputPresets:
    """Tests for output format presets."""

    def test_get_preset(self):
        """Test getting output preset."""
        preset = get_output_format_preset("cinema_4k")
        assert preset is not None
        assert preset.resolution == (4096, 2160)

    def test_get_invalid_preset(self):
        """Test getting invalid preset."""
        preset = get_output_format_preset("invalid_format")
        assert preset is None

    def test_builtin_presets(self):
        """Test built-in presets exist."""
        assert "streaming_1080p" in OUTPUT_FORMAT_PRESETS
        assert "16bit_game" in OUTPUT_FORMAT_PRESETS


# =============================================================================
# Production Loader Tests
# =============================================================================

class TestProductionLoader:
    """Tests for production loader."""

    def test_load_production(self, temp_dir, sample_yaml_content):
        """Test loading production from YAML."""
        yaml_path = os.path.join(temp_dir, "production.yaml")
        with open(yaml_path, "w") as f:
            f.write(sample_yaml_content)

        config = load_production(yaml_path)
        assert config.meta.title == "My Test Film"
        assert len(config.characters) == 1
        assert len(config.locations) == 1
        assert len(config.shots) == 2

    def test_load_production_from_dir(self, temp_dir):
        """Test loading production from directory."""
        # Create main production file
        main_yaml = os.path.join(temp_dir, "production.yaml")
        with open(main_yaml, "w") as f:
            f.write("""
meta:
  title: Test
  author: Author
""")

        # Create characters file
        chars_yaml = os.path.join(temp_dir, "characters.yaml")
        with open(chars_yaml, "w") as f:
            f.write("""
characters:
  hero:
    name: Hero
""")

        # Create shots file
        shots_yaml = os.path.join(temp_dir, "shots.yaml")
        with open(shots_yaml, "w") as f:
            f.write("""
shots:
  - name: shot_001
    scene: 1
""")

        config = load_production_from_dir(temp_dir)
        assert config.meta.title == "Test"
        assert "hero" in config.characters
        assert len(config.shots) == 1

    def test_save_production(self, temp_dir, sample_production_config):
        """Test saving production to YAML."""
        yaml_path = os.path.join(temp_dir, "output.yaml")
        save_production(sample_production_config, yaml_path)

        assert os.path.exists(yaml_path)

        # Load and verify
        loaded = load_production(yaml_path)
        assert loaded.meta.title == "Test Production"

    def test_resolve_production(self, sample_production_config):
        """Test resolving production references."""
        resolved = resolve_production(sample_production_config)
        # Presets should be resolved
        assert resolved is not None

    def test_expand_shots(self, sample_production_config):
        """Test expanding shots."""
        expanded = expand_shots(sample_production_config)
        # All shots should have names
        for shot in expanded.shots:
            assert shot.name != ""

    def test_create_from_template(self, temp_dir):
        """Test creating from template."""
        config = create_production_from_template(
            "Test Film",
            template="short_film",
            output_dir=temp_dir
        )
        assert config.meta.title == "Test Film"
        assert os.path.exists(os.path.join(temp_dir, "production.yaml"))

    def test_estimate_production_time(self, sample_production_config):
        """Test time estimation."""
        estimate = estimate_production_time(sample_production_config)
        assert estimate["shot_count"] == 3
        assert estimate["character_count"] == 1
        assert estimate["location_count"] == 1
        assert estimate["total_seconds"] > 0


# =============================================================================
# Production Validator Tests
# =============================================================================

class TestProductionValidator:
    """Tests for production validator."""

    def test_validate_valid_production(self, temp_dir):
        """Test validating valid production."""
        # Create a valid production config without file dependencies
        config = ProductionConfig(
            meta=ProductionMeta(title="Test"),
            characters={
                "hero": CharacterConfig(
                    name="hero",  # Match key to avoid warning
                    model="",  # Empty model to skip file check
                ),
            },
            locations={
                "warehouse": LocationConfig(
                    name="warehouse",  # Match key to avoid warning
                    preset="industrial",  # Use preset, no file needed
                ),
            },
            shots=[
                ShotConfig(name="shot_001", scene=1, frame_range=(1, 120)),
                ShotConfig(name="shot_002", scene=2, frame_range=(121, 240)),
            ],
            outputs=[
                OutputFormat(
                    name="Master",
                    format="streaming_1080p",
                    resolution=(1920, 1080),
                ),
            ],
            base_path=temp_dir,
        )
        result = validate_production(config)
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_missing_shots(self):
        """Test validation with no shots."""
        config = ProductionConfig(
            meta=ProductionMeta(title="Test"),
        )
        result = validate_production(config)
        assert not result.valid
        assert any("No shots" in e.message for e in result.errors)

    def test_validate_missing_character_reference(self):
        """Test validation with missing character."""
        config = ProductionConfig(
            meta=ProductionMeta(title="Test"),
            shots=[
                ShotConfig(name="shot_1", character="missing_hero"),
            ],
        )
        result = validate_for_execution(config)
        assert not result.valid
        assert any("missing_hero" in e.message for e in result.errors)

    def test_validate_timeline_overlaps(self):
        """Test timeline validation."""
        config = ProductionConfig(
            meta=ProductionMeta(title="Test"),
            shots=[
                ShotConfig(name="shot_1", frame_range=(1, 100)),
                ShotConfig(name="shot_2", frame_range=(50, 150)),  # Overlaps
            ],
        )
        result = validate_timeline(config)
        assert any("overlap" in issue.message.lower() for issue in result)

    def test_validate_dependencies(self, temp_dir):
        """Test dependency validation."""
        # Create a non-existent path
        config = ProductionConfig(
            meta=ProductionMeta(title="Test"),
            script_path="non_existent_file.fountain",
            shots=[ShotConfig(name="shot_1")],
            base_path=temp_dir,
        )
        result = validate_dependencies(config)
        assert any("not found" in issue.message.lower() for issue in result)


# =============================================================================
# Execution Engine Tests
# =============================================================================

class TestExecutionEngine:
    """Tests for execution engine."""

    def test_create_engine(self, sample_production_config):
        """Test creating execution engine."""
        engine = ExecutionEngine(sample_production_config)
        assert engine.config == sample_production_config
        assert engine.state.status == ExecutionStatus.PENDING.value

    def test_get_progress(self, sample_production_config):
        """Test progress tracking."""
        engine = ExecutionEngine(sample_production_config)
        progress = engine.get_progress()

        assert progress["status"] == ExecutionStatus.PENDING.value
        assert progress["shots_total"] == 3
        assert progress["shots_completed"] == 0

    def test_execute_production(self, sample_production_config):
        """Test production execution."""
        result = execute_production(sample_production_config)

        assert result is not None
        assert isinstance(result, ProductionResult)
        assert result.state is not None

    def test_checkpoint_save_load(self, sample_production_config, temp_dir):
        """Test checkpoint save and load."""
        engine = ExecutionEngine(sample_production_config)
        engine.state.checkpoint_path = os.path.join(temp_dir, "checkpoint.json")

        # Save checkpoint
        engine.save_checkpoint()
        assert os.path.exists(engine.state.checkpoint_path)

        # Load checkpoint
        engine2 = ExecutionEngine(sample_production_config)
        engine2.load_checkpoint(engine.state.checkpoint_path)
        assert engine2.state.production_id == engine.state.production_id

    def test_estimate_remaining_time(self, sample_production_config):
        """Test time estimation."""
        engine = ExecutionEngine(sample_production_config)
        remaining = engine.estimate_remaining_time()
        assert remaining >= 0


# =============================================================================
# Parallel Executor Tests
# =============================================================================

class TestParallelExecutor:
    """Tests for parallel executor."""

    def test_analyze_dependencies(self):
        """Test dependency analysis."""
        shots = [
            ShotConfig(name="shot_1", scene=1, character="hero"),
            ShotConfig(name="shot_2", scene=1, character="villain"),
            ShotConfig(name="shot_3", scene=2, character="hero"),
        ]

        groups = analyze_dependencies(shots)
        assert len(groups) > 0

        # First two shots in same scene should be parallelizable
        assert len(groups[0]) == 2

    def test_create_execution_graph(self):
        """Test execution graph creation."""
        shots = [
            ShotConfig(name="shot_1", scene=1),
            ShotConfig(name="shot_2", scene=1),
            ShotConfig(name="shot_3", scene=2),
        ]

        graph = create_execution_graph(shots)
        assert graph.total_shots == 3
        assert len(graph.groups) > 0

    def test_get_parallel_estimate(self):
        """Test parallel estimation."""
        shots = [
            ShotConfig(name=f"shot_{i}", scene=i // 2)
            for i in range(10)
        ]

        estimate = get_parallel_estimate(shots, max_workers=4)
        assert estimate["total_shots"] == 10
        assert estimate["speedup_factor"] >= 1.0

    def test_optimize_worker_count(self):
        """Test worker optimization."""
        shots = [ShotConfig(name=f"shot_{i}", scene=1) for i in range(20)]
        optimal = optimize_worker_count(shots, max_available=8)
        assert 1 <= optimal <= 8

    def test_parallel_executor_create(self):
        """Test creating parallel executor."""
        config = ParallelConfig(max_workers=4)
        executor = ParallelExecutor(config)
        assert executor.config.max_workers == 4


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests."""

    def test_full_workflow(self, temp_dir, sample_yaml_content):
        """Test full production workflow."""
        # 1. Create production file
        yaml_path = os.path.join(temp_dir, "production.yaml")
        with open(yaml_path, "w") as f:
            f.write(sample_yaml_content)

        # 2. Load production
        config = load_production(yaml_path)
        assert config.meta.title == "My Test Film"

        # 3. Resolve references
        config = resolve_production(config)

        # 4. Expand shots
        config = expand_shots(config)

        # 5. Validate
        result = validate_for_execution(config)
        # May have warnings but should be valid for execution
        # (character model doesn't exist but that's a warning)

        # 6. Get estimate
        estimate = estimate_production_time(config)
        assert estimate["total_seconds"] > 0

        # 7. Execute (mock)
        engine = ExecutionEngine(config)
        progress = engine.get_progress()
        assert progress is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
