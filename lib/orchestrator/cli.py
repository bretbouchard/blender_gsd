"""
CLI Interface

Command-line interface for scene generation.
Supports all UX tiers via command-line arguments.

Implements REQ-SO-10: CLI Interface.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class OutputFormat(Enum):
    """Output format options."""
    JSON = "json"
    YAML = "yaml"
    BLEND = "blend"
    PREVIEW = "preview"


class Verbosity(Enum):
    """Verbosity levels."""
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


@dataclass
class CLIConfig:
    """
    CLI configuration.

    Attributes:
        verbosity: Output verbosity level
        output_format: Output format
        output_path: Output file path
        dry_run: Show what would be done without executing
        checkpoint_dir: Directory for checkpoints
        resume: Resume from checkpoint
    """
    verbosity: int = 1
    output_format: str = "json"
    output_path: Optional[str] = None
    dry_run: bool = False
    checkpoint_dir: str = ".checkpoints"
    resume: Optional[str] = None


def create_parser() -> argparse.ArgumentParser:
    """
    Create main argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="scene-gen",
        description="Scene Generation System for Blender",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from template
  scene-gen template portrait_studio --output scene.blend

  # Interactive wizard
  scene-gen wizard

  # Generate from YAML
  scene-gen yaml scene.yaml --output scene.blend

  # Quick scene
  scene-gen quick --type interior --style photorealistic

  # List templates
  scene-gen templates list

  # Validate outline
  scene-gen validate scene.yaml
        """,
    )

    # Global options
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times)",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress output",
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml", "blend", "preview"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    parser.add_argument(
        "--checkpoint-dir",
        default=".checkpoints",
        help="Directory for checkpoints",
    )
    parser.add_argument(
        "--resume",
        help="Resume from checkpoint ID",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Template command
    template_parser = subparsers.add_parser(
        "template",
        help="Generate from template",
    )
    template_parser.add_argument(
        "template_id",
        help="Template identifier",
    )
    template_parser.add_argument(
        "--list",
        action="store_true",
        dest="list_templates",
        help="List available templates",
    )
    template_parser.add_argument(
        "--category",
        help="Filter templates by category",
    )
    template_parser.add_argument(
        "--set",
        nargs=2,
        action="append",
        metavar=("KEY", "VALUE"),
        help="Override template parameter",
    )

    # Wizard command
    wizard_parser = subparsers.add_parser(
        "wizard",
        help="Interactive wizard mode",
    )
    wizard_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run wizard with all defaults",
    )
    wizard_parser.add_argument(
        "--answers",
        help="JSON file with pre-filled answers",
    )

    # YAML command
    yaml_parser = subparsers.add_parser(
        "yaml",
        help="Generate from YAML file",
    )
    yaml_parser.add_argument(
        "yaml_path",
        help="Path to YAML file",
    )
    yaml_parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate, don't generate",
    )

    # Quick command
    quick_parser = subparsers.add_parser(
        "quick",
        help="Quick scene generation",
    )
    quick_parser.add_argument(
        "--type",
        dest="scene_type",
        choices=["interior", "exterior", "urban", "product", "portrait", "environment"],
        default="interior",
        help="Scene type",
    )
    quick_parser.add_argument(
        "--style",
        default="photorealistic",
        help="Visual style",
    )
    quick_parser.add_argument(
        "--width",
        type=float,
        default=20.0,
        help="Scene width",
    )
    quick_parser.add_argument(
        "--height",
        type=float,
        default=4.0,
        help="Scene height",
    )
    quick_parser.add_argument(
        "--depth",
        type=float,
        default=20.0,
        help="Scene depth",
    )

    # Templates command
    templates_parser = subparsers.add_parser(
        "templates",
        help="Template management",
    )
    templates_parser.add_argument(
        "action",
        choices=["list", "info", "preview"],
        help="Action to perform",
    )
    templates_parser.add_argument(
        "template_id",
        nargs="?",
        help="Template identifier (for info/preview)",
    )
    templates_parser.add_argument(
        "--category",
        help="Filter by category",
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate scene outline",
    )
    validate_parser.add_argument(
        "path",
        help="Path to YAML/JSON file",
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )

    # Styles command
    styles_parser = subparsers.add_parser(
        "styles",
        help="Style management",
    )
    styles_parser.add_argument(
        "action",
        choices=["list", "info"],
        help="Action to perform",
    )
    styles_parser.add_argument(
        "style_id",
        nargs="?",
        help="Style identifier",
    )

    # Checkpoint command
    checkpoint_parser = subparsers.add_parser(
        "checkpoint",
        help="Checkpoint management",
    )
    checkpoint_parser.add_argument(
        "action",
        choices=["list", "resume", "delete", "clean"],
        help="Action to perform",
    )
    checkpoint_parser.add_argument(
        "checkpoint_id",
        nargs="?",
        help="Checkpoint identifier",
    )

    return parser


class CLI:
    """
    CLI application.

    Usage:
        cli = CLI()
        exit_code = cli.run(sys.argv[1:])
    """

    def __init__(self):
        """Initialize CLI."""
        self.parser = create_parser()
        self.config = CLIConfig()
        self._verbosity = Verbosity.NORMAL

    def run(self, args: List[str]) -> int:
        """
        Run CLI with arguments.

        Args:
            args: Command-line arguments

        Returns:
            Exit code
        """
        parsed = self.parser.parse_args(args)

        # Configure verbosity
        if parsed.quiet:
            self._verbosity = Verbosity.QUIET
        elif parsed.verbose:
            self._verbosity = Verbosity(min(parsed.verbose + 1, 3))

        # Update config
        self.config = CLIConfig(
            verbosity=self._verbosity.value,
            output_format=getattr(parsed, "format", "json"),
            output_path=getattr(parsed, "output", None),
            dry_run=getattr(parsed, "dry_run", False),
            checkpoint_dir=getattr(parsed, "checkpoint_dir", ".checkpoints"),
            resume=getattr(parsed, "resume", None),
        )

        # Route to command handler
        command = parsed.command
        if not command:
            self.parser.print_help()
            return 0

        try:
            if command == "template":
                return self._handle_template(parsed)
            elif command == "wizard":
                return self._handle_wizard(parsed)
            elif command == "yaml":
                return self._handle_yaml(parsed)
            elif command == "quick":
                return self._handle_quick(parsed)
            elif command == "templates":
                return self._handle_templates(parsed)
            elif command == "validate":
                return self._handle_validate(parsed)
            elif command == "styles":
                return self._handle_styles(parsed)
            elif command == "checkpoint":
                return self._handle_checkpoint(parsed)
            else:
                self._error(f"Unknown command: {command}")
                return 1

        except KeyboardInterrupt:
            self._print("\nInterrupted")
            return 130
        except Exception as e:
            self._error(str(e))
            if self._verbosity == Verbosity.DEBUG:
                import traceback
                traceback.print_exc()
            return 1

    def _handle_template(self, args) -> int:
        """Handle template command."""
        from .ux_tiers import TemplateHandler, create_scene_from_template

        handler = TemplateHandler()

        # List templates
        if getattr(args, "list_templates", False):
            templates = handler.list_templates(
                category=getattr(args, "category", None)
            )
            self._print("Available Templates:")
            self._print("-" * 60)
            for t in templates:
                self._print(f"  {t.template_id:20s} {t.name}")
                self._print(f"  {'':20s} {t.description[:50]}...")
            return 0

        # Generate from template
        template_id = args.template_id

        # Parse overrides
        overrides = {}
        if args.set:
            for key, value in args.set:
                # Try to parse as JSON for complex values
                try:
                    overrides[key] = json.loads(value)
                except json.JSONDecodeError:
                    overrides[key] = value

        if self.config.dry_run:
            self._print(f"Would generate scene from template: {template_id}")
            if overrides:
                self._print(f"With overrides: {json.dumps(overrides, indent=2)}")
            return 0

        outline = handler.create_outline(template_id, **overrides)
        return self._output_outline(outline)

    def _handle_wizard(self, args) -> int:
        """Handle wizard command."""
        from .ux_tiers import WizardHandler

        handler = WizardHandler()
        state = handler.start()

        # Non-interactive mode with defaults
        if getattr(args, "non_interactive", False):
            # Use all defaults
            while state.current_step != "review":
                question = handler.get_current_question(state)
                if question:
                    state = handler.process_answer(
                        state,
                        question.question_id,
                        question.default,
                    )
        else:
            # Interactive mode
            self._print("Scene Generation Wizard")
            self._print("=" * 40)

            while state.current_step != "review":
                question = handler.get_current_question(state)
                if not question:
                    break

                # Display question
                self._print(f"\n{question.prompt}")
                if question.options:
                    for i, opt in enumerate(question.options, 1):
                        self._print(f"  {i}. {opt}")
                    default_idx = question.options.index(question.default) + 1 if question.default in question.options else 1
                    self._print(f"  [default: {default_idx}]")
                else:
                    self._print(f"  [default: {question.default}]")

                if question.help_text:
                    self._print(f"  ({question.help_text})")

                # Get input
                try:
                    user_input = input("> ").strip()
                except EOFError:
                    return 1

                # Use default if empty
                if not user_input:
                    answer = question.default
                elif question.options:
                    # Convert numeric input to option
                    try:
                        idx = int(user_input) - 1
                        if 0 <= idx < len(question.options):
                            answer = question.options[idx]
                        else:
                            self._error("Invalid option")
                            continue
                    except ValueError:
                        answer = user_input
                else:
                    answer = user_input

                state = handler.process_answer(state, question.question_id, answer)

                if state.errors:
                    for error in state.errors:
                        self._error(error)

        # Create outline
        outline = handler.create_outline(state)
        self._print("\nGenerating scene...")
        return self._output_outline(outline)

    def _handle_yaml(self, args) -> int:
        """Handle yaml command."""
        from .ux_tiers import YAMLHandler

        handler = YAMLHandler()

        if getattr(args, "validate_only", False):
            result = handler.validate_yaml(args.yaml_path)
            if result["valid"]:
                self._print(f"Valid: {args.yaml_path}")
                if result["warnings"]:
                    self._print("Warnings:")
                    for w in result["warnings"]:
                        self._print(f"  - {w}")
                return 0
            else:
                self._error(f"Invalid: {args.yaml_path}")
                for e in result["errors"]:
                    self._error(f"  {e}")
                return 1

        outline = handler.create_outline(yaml_path=args.yaml_path)
        return self._output_outline(outline)

    def _handle_quick(self, args) -> int:
        """Handle quick command."""
        from .ux_tiers import APIHandler

        handler = APIHandler()

        outline = handler.create_outline(
            scene_type=args.scene_type,
            style=args.style,
            dimensions={
                "width": args.width,
                "height": args.height,
                "depth": args.depth,
            },
        )

        return self._output_outline(outline)

    def _handle_templates(self, args) -> int:
        """Handle templates command."""
        from .ux_tiers import TemplateHandler

        handler = TemplateHandler()

        if args.action == "list":
            templates = handler.list_templates(
                category=getattr(args, "category", None)
            )
            self._print("Available Templates:")
            self._print("-" * 60)
            for t in templates:
                self._print(f"  {t.template_id:20s} {t.name}")

        elif args.action == "info":
            if not args.template_id:
                self._error("Template ID required")
                return 1
            info = handler.get_template_preview(args.template_id)
            if "error" in info:
                self._error(info["error"])
                return 1
            self._print(f"Template: {info['name']}")
            self._print(f"ID: {info['template_id']}")
            self._print(f"Category: {info['category']}")
            self._print(f"Scene Type: {info['scene_type']}")
            self._print(f"Description: {info['description']}")
            self._print(f"Tags: {', '.join(info['tags'])}")

        elif args.action == "preview":
            self._error("Preview not implemented")
            return 1

        return 0

    def _handle_validate(self, args) -> int:
        """Handle validate command."""
        from .ux_tiers import YAMLHandler

        handler = YAMLHandler()
        result = handler.validate_yaml(args.path)

        if result["valid"]:
            self._print(f"✓ Valid: {args.path}")
            if result["warnings"]:
                if getattr(args, "strict", False):
                    self._error("Warnings treated as errors (--strict)")
                    for w in result["warnings"]:
                        self._error(f"  {w}")
                    return 1
                else:
                    self._print("Warnings:")
                    for w in result["warnings"]:
                        self._print(f"  ⚠ {w}")
            return 0
        else:
            self._error(f"✗ Invalid: {args.path}")
            for e in result["errors"]:
                self._error(f"  {e}")
            return 1

    def _handle_styles(self, args) -> int:
        """Handle styles command."""
        from .style_manager import StyleManager

        manager = StyleManager()

        if args.action == "list":
            styles = manager.list_styles()
            self._print("Available Styles:")
            self._print("-" * 40)
            for style_id in styles:
                profile = manager.get_profile(style_id)
                if profile:
                    self._print(f"  {style_id:20s} {profile.name}")

        elif args.action == "info":
            if not args.style_id:
                self._error("Style ID required")
                return 1
            profile = manager.get_profile(args.style_id)
            if not profile:
                self._error(f"Style not found: {args.style_id}")
                return 1
            self._print(f"Style: {profile.name}")
            self._print(f"ID: {profile.style_id}")
            self._print(f"Category: {profile.category}")
            self._print(f"Material Style: {profile.material_style}")
            self._print(f"Lighting Style: {profile.lighting_style}")
            self._print(f"Color Palette: {', '.join(profile.color_palette)}")
            self._print(f"Texture Intensity: {profile.texture_intensity}")
            self._print(f"Geometry Detail: {profile.geometry_detail}")
            self._print(f"Post-Processing: {', '.join(profile.post_processing) or 'None'}")
            self._print(f"Compatible With: {', '.join(profile.compatible_styles) or 'None'}")

        return 0

    def _handle_checkpoint(self, args) -> int:
        """Handle checkpoint command."""
        from .checkpoint import CheckpointManager

        manager = CheckpointManager(self.config.checkpoint_dir)

        if args.action == "list":
            checkpoints = manager.list_checkpoints()
            if not checkpoints:
                self._print("No checkpoints found")
                return 0
            self._print("Checkpoints:")
            self._print("-" * 60)
            for cp in checkpoints:
                self._print(f"  {cp['checkpoint_id']:20s} {cp['stage']:15s} {cp['timestamp']}")

        elif args.action == "resume":
            if not args.checkpoint_id:
                self._error("Checkpoint ID required")
                return 1
            # Resume handled by generation system
            self._print(f"Resume checkpoint: {args.checkpoint_id}")

        elif args.action == "delete":
            if not args.checkpoint_id:
                self._error("Checkpoint ID required")
                return 1
            manager.delete_checkpoint(args.checkpoint_id)
            self._print(f"Deleted checkpoint: {args.checkpoint_id}")

        elif args.action == "clean":
            count = manager.clean_old_checkpoints()
            self._print(f"Cleaned {count} old checkpoints")

        return 0

    def _output_outline(self, outline) -> int:
        """Output scene outline."""
        if self.config.dry_run:
            self._print("Would output outline:")
            self._print(json.dumps(outline.to_dict(), indent=2))
            return 0

        output = outline.to_json() if self.config.output_format == "json" else str(outline.to_dict())

        if self.config.output_path:
            Path(self.config.output_path).write_text(output)
            self._print(f"Written to: {self.config.output_path}")
        else:
            self._print(output)

        return 0

    def _print(self, message: str) -> None:
        """Print message if not quiet."""
        if self._verbosity != Verbosity.QUIET:
            print(message)

    def _error(self, message: str) -> None:
        """Print error message."""
        print(f"Error: {message}", file=sys.stderr)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code
    """
    cli = CLI()
    return cli.run(args if args is not None else sys.argv[1:])


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "OutputFormat",
    "Verbosity",
    "CLIConfig",
    "CLI",
    "create_parser",
    "main",
]
