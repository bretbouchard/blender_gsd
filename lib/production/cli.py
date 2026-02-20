"""
Production CLI Interface

Command-line interface for production management.

Requirements:
- REQ-ORCH-01 through REQ-ORCH-06: Full CLI control
- REQ-CONFIG-01 through REQ-CONFIG-06: Master config support
- Progress display and error reporting

Part of Phase 14.1: Production Orchestrator
Part of Phase 14.2: Master Production Config

Usage:
    python -m lib.production.cli run production.yaml
    python -m lib.production.cli validate production.yaml
    python -m lib.production.cli info production.yaml
    python -m lib.production.cli estimate production.yaml
    python -m lib.production.cli list
    python -m lib.production.cli create my_film
    python -m lib.production.cli show production.yaml
    python -m lib.production.cli check production.yaml
"""

from __future__ import annotations
import os
import sys
import time
import json
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import click
    HAS_CLICK = True
except ImportError:
    HAS_CLICK = False

from lib.production.production_types import (
    ProductionConfig,
    ExecutionStatus,
    ParallelConfig,
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
    validate_for_execution,
)
from lib.production.execution_engine import (
    ExecutionEngine,
    execute_production,
    resume_production,
)
from lib.production.parallel_executor import (
    ParallelExecutor,
    get_parallel_estimate,
    optimize_worker_count,
)

# Master config imports (Phase 14.2)
from lib.production.config_schema import (
    MasterProductionConfig,
    create_master_config_from_preset,
)
from lib.production.template_expansion import (
    expand_shot_templates,
    get_production_summary,
    list_shot_templates,
    list_style_presets,
    suggest_shot_for_context,
)
from lib.production.config_validation import (
    validate_master_config,
    validate_for_execution_strict,
    check_file_references,
    check_shot_templates,
)


# ANSI color codes
class Colors:
    """ANSI terminal colors."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def colorize(text: str, color: str) -> str:
    """Apply ANSI color to text."""
    return f"{color}{text}{Colors.RESET}"


def print_header(title: str) -> None:
    """Print section header."""
    print()
    print(colorize(f"{'=' * 60}", Colors.BOLD))
    print(colorize(f"  {title}", Colors.BOLD))
    print(colorize(f"{'=' * 60}", Colors.BOLD))
    print()


def print_success(message: str) -> None:
    """Print success message."""
    print(colorize(f"  [OK] {message}", Colors.GREEN))


def print_error(message: str) -> None:
    """Print error message."""
    print(colorize(f"  [ERROR] {message}", Colors.RED))


def print_warning(message: str) -> None:
    """Print warning message."""
    print(colorize(f"  [WARNING] {message}", Colors.YELLOW))


def print_info(message: str) -> None:
    """Print info message."""
    print(colorize(f"  [INFO] {message}", Colors.CYAN))


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_progress(completed: int, total: int, percent: float) -> str:
    """Format progress bar."""
    bar_width = 30
    filled = int(bar_width * percent / 100)
    bar = '█' * filled + '░' * (bar_width - filled)
    return f"[{bar}] {completed}/{total} ({percent:.1f}%)"


if HAS_CLICK:
    @click.group()
    @click.version_option('0.1.0')
    def production():
        """Production management commands."""
        pass

    @production.command()
    @click.argument('yaml_path')
    @click.option('--validate-only', is_flag=True, help='Only validate, do not execute')
    @click.option('--dry-run', is_flag=True, help='Show what would be done')
    @click.option('--resume', is_flag=True, help='Resume from checkpoint')
    @click.option('--parallel', default=4, help='Number of parallel workers')
    @click.option('--checkpoint', default='', help='Checkpoint file path for resume')
    @click.option('--verbose', '-v', is_flag=True, help='Verbose output')
    def run(yaml_path: str, validate_only: bool, dry_run: bool, resume: bool,
            parallel: int, checkpoint: str, verbose: bool):
        """Execute production from YAML."""
        print_header(f"Production Execution: {yaml_path}")

        # Load production
        print_info("Loading production configuration...")
        try:
            config = load_production(yaml_path)
            config = resolve_production(config)
            config = expand_shots(config)
            print_success(f"Loaded: {config.meta.title}")
        except Exception as e:
            print_error(f"Failed to load production: {e}")
            sys.exit(1)

        # Show summary
        print()
        print(f"  Title: {config.meta.title}")
        print(f"  Characters: {len(config.characters)}")
        print(f"  Locations: {len(config.locations)}")
        print(f"  Shots: {len(config.shots)}")
        print(f"  Outputs: {len(config.outputs)}")
        print()

        # Validate
        print_info("Validating production...")
        result = validate_for_execution(config)

        if result.errors:
            print_error("Validation failed:")
            for error in result.errors:
                print(f"    - {error.path}: {error.message}")
            sys.exit(1)

        if result.warnings:
            print_warning("Validation warnings:")
            for warning in result.warnings:
                print(f"    - {warning.path}: {warning.message}")

        print_success("Validation passed")

        if validate_only:
            print_info("Validate-only mode, skipping execution")
            sys.exit(0)

        if dry_run:
            print_info("Dry-run mode, showing execution plan:")
            _show_execution_plan(config, parallel)
            sys.exit(0)

        # Execute
        print_header("Starting Execution")

        start_time = time.time()
        engine = ExecutionEngine(config)

        # Setup callbacks
        def on_progress(info):
            if verbose:
                progress_str = format_progress(
                    info['shots_completed'],
                    info['shots_total'],
                    info['progress_percent']
                )
                print(f"\r  {progress_str}", end='', flush=True)

        def on_phase_start(phase):
            print_info(f"Starting phase: {phase}")

        def on_shot_complete(idx, success):
            if verbose:
                status = "OK" if success else "FAILED"
                shot = config.shots[idx]
                print(f"\n  Shot {idx + 1}: {shot.name} [{status}]")

        engine.on_progress = on_progress
        engine.on_phase_start = on_phase_start
        engine.on_shot_complete = on_shot_complete

        # Resume from checkpoint if requested
        if resume and checkpoint:
            try:
                engine.load_checkpoint(checkpoint)
                print_info(f"Resumed from checkpoint: {checkpoint}")
            except Exception as e:
                print_warning(f"Could not load checkpoint: {e}")

        # Run execution
        exec_result = engine.execute()

        # Print results
        print()
        print_header("Execution Complete")

        duration = time.time() - start_time
        print(f"  Duration: {format_duration(duration)}")
        print(f"  Shots Completed: {exec_result.shots_completed}")
        print(f"  Shots Failed: {exec_result.shots_failed}")
        print(f"  Status: {exec_result.state.status if exec_result.state else 'unknown'}")

        if exec_result.errors:
            print_error("Errors:")
            for error in exec_result.errors:
                print(f"    - {error}")

        if exec_result.success:
            print_success("Production completed successfully!")
            sys.exit(0)
        else:
            print_error("Production failed")
            sys.exit(1)

    @production.command()
    @click.argument('yaml_path')
    @click.option('--strict', is_flag=True, help='Use strict validation')
    def validate(yaml_path: str, strict: bool):
        """Validate production configuration."""
        print_header(f"Validation: {yaml_path}")

        try:
            config = load_production(yaml_path)
            config = resolve_production(config)
        except Exception as e:
            print_error(f"Failed to load: {e}")
            sys.exit(1)

        if strict:
            result = validate_for_execution(config)
        else:
            result = validate_production(config)

        # Print results
        print(f"  Valid: {result.valid}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Warnings: {len(result.warnings)}")
        print(f"  Total Issues: {len(result.issues)}")
        print()

        if result.errors:
            print_error("Errors:")
            for error in result.errors:
                print(f"    [{error.path}] {error.message}")
                if error.suggestion:
                    print(f"      Suggestion: {error.suggestion}")
            print()

        if result.warnings:
            print_warning("Warnings:")
            for warning in result.warnings:
                print(f"    [{warning.path}] {warning.message}")
            print()

        if result.valid:
            print_success("Production is valid")
            sys.exit(0)
        else:
            print_error("Production has validation errors")
            sys.exit(1)

    @production.command()
    @click.argument('yaml_path')
    def info(yaml_path: str):
        """Show production information."""
        print_header(f"Production Info: {yaml_path}")

        try:
            info = get_production_info(yaml_path)
        except Exception as e:
            print_error(f"Failed to load: {e}")
            sys.exit(1)

        print(f"  Title: {info['title']}")
        print(f"  Version: {info['version']}")
        print(f"  Author: {info['author'] or 'Not specified'}")
        print(f"  Description: {info['description'] or 'None'}")
        print()
        print(f"  Characters: {info['character_count']}")
        print(f"  Locations: {info['location_count']}")
        print(f"  Shots: {info['shot_count']}")
        print(f"  Output Formats: {info['output_format_count']}")
        print(f"  Has Script: {'Yes' if info['has_script'] else 'No'}")
        print()

    @production.command()
    @click.argument('yaml_path')
    @click.option('--parallel', default=4, help='Number of parallel workers')
    def estimate(yaml_path: str, parallel: int):
        """Estimate execution time."""
        print_header(f"Time Estimate: {yaml_path}")

        try:
            config = load_production(yaml_path)
            config = resolve_production(config)
            config = expand_shots(config)
        except Exception as e:
            print_error(f"Failed to load: {e}")
            sys.exit(1)

        # Get time estimate
        estimate = estimate_production_time(config)

        print(f"  Total Time: {format_duration(estimate['total_seconds'])}")
        print(f"  Shots: {estimate['shot_count']}")
        print(f"  Characters: {estimate['character_count']}")
        print(f"  Locations: {estimate['location_count']}")
        print(f"  Outputs: {estimate['output_count']}")
        print()

        print("  Phase Estimates:")
        for phase, time_val in estimate['phase_times'].items():
            if time_val > 0:
                print(f"    - {phase}: {format_duration(time_val)}")
        print()

        # Parallel estimate
        if config.shots:
            parallel_est = get_parallel_estimate(config.shots, parallel)
            print(f"  Parallel Execution ({parallel} workers):")
            print(f"    - Speedup: {parallel_est['speedup_factor']:.1f}x")
            print(f"    - Parallel groups: {parallel_est['parallel_groups']}")
            print(f"    - Max parallelism: {parallel_est['max_parallelism']}")

            parallel_time = estimate['total_seconds'] / parallel_est['speedup_factor']
            print(f"    - Estimated time: {format_duration(parallel_time)}")
            print()

    @production.command('list')
    @click.option('--directory', default='.', help='Directory to search')
    def list_cmd(directory: str):
        """List all productions in directory."""
        print_header("Productions")

        productions = list_productions(directory)

        if not productions:
            print_info("No productions found")
            return

        print(f"  Found {len(productions)} production(s):")
        print()

        for prod in productions:
            print(f"  {colorize(prod['title'], Colors.BOLD)}")
            print(f"    Path: {prod['path']}")
            print(f"    Version: {prod['version']}")
            print(f"    Author: {prod['author'] or 'Not specified'}")
            print()

    @production.command()
    @click.argument('name')
    @click.option('--template', default='short_film',
                  type=click.Choice(['short_film', 'commercial', 'game_assets']),
                  help='Production template')
    @click.option('--output', default='', help='Output directory')
    def create(name: str, template: str, output: str):
        """Create new production from template."""
        print_header(f"Create Production: {name}")

        output_dir = output or name

        print_info(f"Creating {template} production in {output_dir}...")

        try:
            config = create_production_from_template(name, template, output_dir)
            print_success(f"Created production: {config.meta.title}")
            print()
            print(f"  Configuration: {output_dir}/production.yaml")
            print()
            print_info("Next steps:")
            print("  1. Edit production.yaml to add characters, locations, shots")
            print("  2. Run 'python -m lib.production.cli validate production.yaml'")
            print("  3. Run 'python -m lib.production.cli run production.yaml'")
        except Exception as e:
            print_error(f"Failed to create: {e}")
            sys.exit(1)

    @production.command()
    @click.argument('yaml_path')
    @click.option('--expand', is_flag=True, help='Show expanded configuration')
    @click.option('--verbose', '-v', is_flag=True, help='Verbose output')
    def show(yaml_path: str, expand: bool, verbose: bool):
        """Show production configuration.

        Displays the master production configuration with optional
        expansion of shot templates and resolution of references.
        """
        print_header(f"Production Configuration: {yaml_path}")

        try:
            config = MasterProductionConfig.from_yaml(yaml_path)
        except Exception as e:
            print_error(f"Failed to load: {e}")
            sys.exit(1)

        # Get summary
        summary = get_production_summary(config)

        # Print basic info
        print(colorize("  Metadata", Colors.BOLD))
        print(f"    Title: {summary['title']}")
        print(f"    Version: {summary['version']}")
        print(f"    Author: {config.meta.author or 'Not specified'}")
        print(f"    Description: {config.meta.description or 'None'}")
        print()

        # Source info
        print(colorize("  Source", Colors.BOLD))
        print(f"    Script: {config.source.script or 'None'}")
        print(f"    Style Preset: {summary['style_preset']}")
        print(f"    Reference Images: {len(config.source.reference_images)}")
        print()

        # Counts
        print(colorize("  Contents", Colors.BOLD))
        print(f"    Characters: {summary['character_count']}")
        print(f"    Locations: {summary['location_count']}")
        print(f"    Shots: {summary['shot_count']} (total: {summary['total_shot_count']})")
        print(f"    Scenes: {summary['scene_count']} ({', '.join(map(str, summary['scenes']))})")
        print()

        # Timing
        print(colorize("  Timing", Colors.BOLD))
        print(f"    Total Frames: {summary['total_frames']}")
        print(f"    Duration: {summary['total_minutes']:.1f} minutes")
        print()

        # Outputs
        print(colorize("  Outputs", Colors.BOLD))
        print(f"    Cinematic: {summary['cinematic_outputs']}")
        print(f"    Retro: {summary['retro_outputs']}")
        for output in config.outputs:
            retro_tag = " [retro]" if output.retro and output.retro.enabled else ""
            print(f"      - {output.name}: {output.resolution[0]}x{output.resolution[1]}{retro_tag}")
        print()

        # Render settings
        print(colorize("  Render Settings", Colors.BOLD))
        print(f"    Engine: {summary['render_engine']}")
        print(f"    Samples: {summary['render_samples']}")
        print()

        # Expanded shots
        if expand:
            print_header("Expanded Shots")

            expanded = expand_shot_templates(config)
            for shot in expanded:
                char_name = shot.character.name if shot.character else "-"
                loc_name = shot.location.name if shot.location else "-"
                costume = f" ({shot.costume})" if shot.costume else ""

                print(f"  {shot.name} (Scene {shot.scene})")
                print(f"    Template: {shot.template}")
                print(f"    Shot Size: {shot.shot_size}")
                print(f"    Camera: {shot.camera_angle}")
                print(f"    Character: {char_name}{costume}")
                print(f"    Location: {loc_name}")
                print(f"    Frames: {shot.frame_range[0]}-{shot.frame_range[1]} ({shot.duration} frames)")
                if shot.notes:
                    print(f"    Notes: {shot.notes}")
                print()

    @production.command()
    @click.argument('yaml_path')
    @click.option('--strict', is_flag=True, help='Strict validation for execution')
    @click.option('--check-files', is_flag=True, help='Check file references')
    @click.option('--verbose', '-v', is_flag=True, help='Verbose output')
    def check(yaml_path: str, strict: bool, check_files: bool, verbose: bool):
        """Validate production configuration.

        Performs comprehensive validation of the master production
        configuration, checking for errors, warnings, and missing files.
        """
        print_header(f"Validation: {yaml_path}")

        try:
            config = MasterProductionConfig.from_yaml(yaml_path)
        except Exception as e:
            print_error(f"Failed to load: {e}")
            sys.exit(1)

        # Run validation
        if strict:
            result = validate_for_execution_strict(config)
        else:
            result = validate_master_config(config)

        # Check file references if requested
        if check_files:
            file_issues = check_file_references(config)
            result.issues.extend(file_issues)
            for issue in file_issues:
                if issue.severity == "error":
                    result.valid = False

        # Print results
        print(f"  Valid: {colorize(str(result.valid), Colors.GREEN if result.valid else Colors.RED)}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Warnings: {len(result.warnings)}")
        print(f"  Total Issues: {len(result.issues)}")
        print()

        if result.errors:
            print_error("Errors:")
            for error in result.errors:
                print(f"    [{error.path}] {error.message}")
                if error.suggestion and verbose:
                    print(f"      Suggestion: {error.suggestion}")
            print()

        if result.warnings:
            print_warning("Warnings:")
            for warning in result.warnings:
                print(f"    [{warning.path}] {warning.message}")
                if warning.suggestion and verbose:
                    print(f"      Suggestion: {warning.suggestion}")
            print()

        if verbose and result.issues:
            info_issues = [i for i in result.issues if i.severity == "info"]
            if info_issues:
                print_info("Info:")
                for info in info_issues:
                    print(f"    [{info.path}] {info.message}")
                print()

        if result.valid:
            print_success("Production is valid")
            sys.exit(0)
        else:
            print_error("Production has validation errors")
            sys.exit(1)

    @production.command('list-templates')
    @click.option('--shots', is_flag=True, help='List shot templates')
    @click.option('--styles', is_flag=True, help='List style presets')
    def list_templates(shots: bool, styles: bool):
        """List available templates and presets.

        Shows shot templates and style presets that can be used
        in production configurations.
        """
        if not shots and not styles:
            # Default to showing both
            shots = True
            styles = True

        if shots:
            print_header("Shot Templates")
            templates = list_shot_templates()
            for name in sorted(templates):
                from lib.production.template_expansion import SHOT_TEMPLATES
                info = SHOT_TEMPLATES.get(name, {})
                desc = info.get("description", "")
                duration = info.get("duration", "?")
                print(f"  {name}")
                print(f"    Description: {desc}")
                print(f"    Default Duration: {duration} frames")
                print()

        if styles:
            print_header("Style Presets")
            presets = list_style_presets()
            for name in sorted(presets):
                from lib.production.template_expansion import STYLE_PRESETS
                info = STYLE_PRESETS.get(name, {})
                mood = info.get("mood", "?")
                grade = info.get("color_grade", "?")
                contrast = info.get("contrast", "?")
                print(f"  {name}")
                print(f"    Mood: {mood}")
                print(f"    Color Grade: {grade}")
                print(f"    Contrast: {contrast}")
                print()

    @production.command('suggest')
    @click.option('--character', is_flag=True, help='Include character')
    @click.option('--two-characters', is_flag=True, help='Include two characters')
    @click.option('--location', is_flag=True, help='Include location')
    @click.option('--action', is_flag=True, help='Action shot')
    def suggest(character: bool, two_characters: bool, location: bool, action: bool):
        """Suggest shot templates for context.

        Provides shot template suggestions based on the scene context.
        """
        print_header("Shot Template Suggestions")

        suggestions = suggest_shot_for_context(
            has_character=character or two_characters,
            has_two_characters=two_characters,
            has_location=location,
            is_action=action
        )

        if suggestions:
            print("  Suggested templates:")
            for name in suggestions:
                from lib.production.template_expansion import SHOT_TEMPLATES
                info = SHOT_TEMPLATES.get(name, {})
                desc = info.get("description", "No description")
                print(f"    {name}: {desc}")
        else:
            print_info("No specific suggestions for this context")

        print()

    def _show_execution_plan(config: ProductionConfig, parallel: int) -> None:
        """Show execution plan for dry-run."""
        print()
        print("  Execution Plan:")
        print()

        phases = ["validate", "prepare", "characters", "locations", "shots",
                  "post_process", "export", "finalize"]

        for i, phase in enumerate(phases):
            print(f"    {i + 1}. {phase.upper()}")

        print()

        # Show parallel estimates
        if config.shots:
            parallel_est = get_parallel_estimate(config.shots, parallel)
            print(f"  Parallel Execution:")
            print(f"    - Workers: {parallel}")
            print(f"    - Parallel groups: {parallel_est['parallel_groups']}")
            print(f"    - Speedup factor: {parallel_est['speedup_factor']:.1f}x")
            print()

        # Show outputs
        print("  Output Formats:")
        for output in config.outputs:
            retro = " (retro)" if output.retro_config and output.retro_config.enabled else ""
            print(f"    - {output.name}: {output.resolution[0]}x{output.resolution[1]}{retro}")
        print()


def main():
    """Main entry point."""
    if HAS_CLICK:
        production()
    else:
        print("Error: click library not installed.")
        print("Install with: pip install click")
        sys.exit(1)


if __name__ == '__main__':
    main()
