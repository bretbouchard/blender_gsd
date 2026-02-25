"""
Blender GSD CLI Main

Main entry point for the blender-gsd command-line interface.

Usage:
    blender-gsd init my-project
    blender-gsd init my-project --template cinematic
    blender-gsd templates list
    blender-gsd validate .
    blender-gsd --help
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Optional, List

from .types import CLIConfig, Verbosity, ProjectTemplate, TEMPLATE_REGISTRY
from .init_cmd import InitCommand, create_project
from .templates_cmd import TemplatesCommand
from .validate_cmd import ValidateCommand


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


def colorize(text: str, color: str, enabled: bool = True) -> str:
    """Apply ANSI color to text."""
    if not enabled:
        return text
    return f"{color}{text}{Colors.RESET}"


class BlenderGSDCLI:
    """
    Main CLI application for Blender GSD.

    Usage:
        cli = BlenderGSDCLI()
        exit_code = cli.run(sys.argv[1:])
    """

    def __init__(self):
        """Initialize CLI."""
        self.parser = self._create_parser()
        self.config = CLIConfig()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            prog="blender-gsd",
            description="Blender GSD Framework - Get Shit Done with Blender",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Create a new project
  blender-gsd init my-project

  # Create with a specific template
  blender-gsd init my-project --template cinematic

  # List available templates
  blender-gsd templates list

  # Validate a project
  blender-gsd validate .

  # Get template info
  blender-gsd templates info control-surface
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
            "--no-color",
            action="store_true",
            help="Disable colored output",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without executing",
        )
        parser.add_argument(
            "--version",
            action="version",
            version="%(prog)s 0.1.0",
        )

        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Init command
        self._add_init_parser(subparsers)

        # Templates command
        self._add_templates_parser(subparsers)

        # Validate command
        self._add_validate_parser(subparsers)

        # Dashboard command
        self._add_dashboard_parser(subparsers)

        return parser

    def _add_init_parser(self, subparsers) -> None:
        """Add init subcommand parser."""
        init_parser = subparsers.add_parser(
            "init",
            help="Create a new project",
            description="Initialize a new Blender GSD project from a template",
        )

        init_parser.add_argument(
            "name",
            help="Project name",
        )

        init_parser.add_argument(
            "-t", "--template",
            choices=list(TEMPLATE_REGISTRY.keys()),
            default="default",
            help="Project template to use (default: default)",
        )

        init_parser.add_argument(
            "-o", "--output",
            help="Output directory (default: current directory)",
        )

        init_parser.add_argument(
            "-d", "--description",
            default="",
            help="Project description",
        )

        init_parser.add_argument(
            "-a", "--author",
            default="",
            help="Project author",
        )

        init_parser.add_argument(
            "--no-git",
            action="store_true",
            help="Skip git initialization",
        )

        init_parser.add_argument(
            "--no-beads",
            action="store_true",
            help="Skip beads initialization",
        )

        init_parser.add_argument(
            "--no-planning",
            action="store_true",
            help="Skip .planning directory creation",
        )

    def _add_templates_parser(self, subparsers) -> None:
        """Add templates subcommand parser."""
        templates_parser = subparsers.add_parser(
            "templates",
            help="Manage project templates",
            description="List and get info about project templates",
        )

        templates_parser.add_argument(
            "action",
            choices=["list", "info"],
            help="Action to perform",
        )

        templates_parser.add_argument(
            "template_id",
            nargs="?",
            help="Template ID (for info action)",
        )

        templates_parser.add_argument(
            "-c", "--category",
            help="Filter by category (for list action)",
        )

    def _add_validate_parser(self, subparsers) -> None:
        """Add validate subcommand parser."""
        validate_parser = subparsers.add_parser(
            "validate",
            help="Validate project structure",
            description="Validate project structure and configuration",
        )

        validate_parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Path to validate (default: current directory)",
        )

        validate_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show info-level issues",
        )

    def _add_dashboard_parser(self, subparsers) -> None:
        """Add dashboard subcommand parser."""
        dashboard_parser = subparsers.add_parser(
            "dashboard",
            help="Start debug dashboard",
            description="Start the web-based debug dashboard for monitoring",
        )

        dashboard_parser.add_argument(
            "--port",
            type=int,
            default=5000,
            help="Port to serve dashboard on (default: 5000)",
        )

        dashboard_parser.add_argument(
            "--no-open",
            action="store_true",
            help="Don't open browser automatically",
        )

        dashboard_parser.add_argument(
            "project_path",
            nargs="?",
            default=".",
            help="Path to project (default: current directory)",
        )

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run CLI with arguments.

        Args:
            args: Command-line arguments (defaults to sys.argv[1:])

        Returns:
            Exit code
        """
        parsed = self.parser.parse_args(args)

        # Configure
        use_color = not parsed.no_color

        if parsed.quiet:
            self.config = CLIConfig(verbosity=Verbosity.QUIET, color_output=use_color)
        elif parsed.verbose:
            self.config = CLIConfig(
                verbosity=Verbosity(min(parsed.verbose + 1, 3)),
                color_output=use_color
            )
        else:
            self.config = CLIConfig(color_output=use_color)

        if parsed.dry_run:
            self.config.dry_run = True

        # Route to command handler
        command = parsed.command

        if not command:
            self.parser.print_help()
            return 0

        try:
            if command == "init":
                return self._handle_init(parsed)
            elif command == "templates":
                return self._handle_templates(parsed)
            elif command == "validate":
                return self._handle_validate(parsed)
            elif command == "dashboard":
                return self._handle_dashboard(parsed)
            else:
                self._error(f"Unknown command: {command}", use_color)
                return 1

        except KeyboardInterrupt:
            self._print("\nInterrupted", use_color)
            return 130
        except Exception as e:
            self._error(str(e), use_color)
            if self.config.verbosity == Verbosity.DEBUG:
                import traceback
                traceback.print_exc()
            return 1

    def _handle_init(self, args) -> int:
        """Handle init command."""
        use_color = self.config.color_output

        # Parse output path
        output_path = Path(args.output) if args.output else None

        self._print(
            f"Creating project: {colorize(args.name, Colors.BOLD, use_color)}",
            use_color
        )
        self._print(f"  Template: {args.template}", use_color)

        if self.config.dry_run:
            self._print("\nDry run - would create:", use_color)
            self._print(f"  Project: {args.name}", use_color)
            self._print(f"  Template: {args.template}", use_color)
            self._print(f"  Output: {output_path or 'current directory'}", use_color)
            self._print(f"  Git: {not args.no_git}", use_color)
            self._print(f"  Beads: {not args.no_beads}", use_color)
            self._print(f"  Planning: {not args.no_planning}", use_color)
            return 0

        try:
            path = create_project(
                name=args.name,
                template=args.template,
                output_path=str(output_path) if output_path else None,
                description=args.description,
                author=args.author,
                init_git=not args.no_git,
                init_beads=not args.no_beads,
                init_planning=not args.no_planning,
            )

            self._print(
                f"\n{colorize('Success!', Colors.GREEN, use_color)} Created project at: {path}",
                use_color
            )
            self._print("\nNext steps:", use_color)
            self._print(f"  cd {path.name}", use_color)
            self._print("  # Edit README.md and .planning/PROJECT.md", use_color)
            self._print("  make help  # Show available commands", use_color)

            return 0

        except ValueError as e:
            self._error(str(e), use_color)
            return 1

    def _handle_templates(self, args) -> int:
        """Handle templates command."""
        use_color = self.config.color_output
        cmd = TemplatesCommand(self.config)

        if args.action == "list":
            templates = cmd.list_templates(category=args.category)

            if not templates:
                self._print("No templates found", use_color)
                return 0

            # Group by category
            categories = cmd.get_template_categories()

            self._print(colorize("Available Templates:", Colors.BOLD, use_color))
            self._print("-" * 60, use_color)

            for category, template_ids in categories.items():
                if args.category and category != args.category:
                    continue

                self._print(f"\n{colorize(category.upper(), Colors.CYAN, use_color)}", use_color)

                for template_id in template_ids:
                    template = cmd.get_template(template_id)
                    if template:
                        self._print(f"  {colorize(template_id, Colors.BOLD, use_color):20s} {template.name}", use_color)
                        self._print(f"  {'':20s} {template.description[:50]}...", use_color)

            return 0

        elif args.action == "info":
            if not args.template_id:
                self._error("Template ID required for info action", use_color)
                return 1

            template = cmd.get_template(args.template_id)
            if not template:
                self._error(f"Template not found: {args.template_id}", use_color)
                return 1

            self._print(cmd.format_template_info(template), use_color)
            return 0

        return 0

    def _handle_validate(self, args) -> int:
        """Handle validate command."""
        use_color = self.config.color_output
        project_path = Path(args.path).resolve()

        self._print(
            f"Validating: {colorize(str(project_path), Colors.BOLD, use_color)}",
            use_color
        )
        self._print("", use_color)

        cmd = ValidateCommand(self.config)
        result = cmd.validate_project(project_path)

        # Print result
        self._print(cmd.format_result(result, verbose=args.verbose), use_color)

        if result.valid:
            self._print(
                colorize("Project is valid!", Colors.GREEN, use_color),
                use_color
            )
            return 0
        else:
            self._print(
                colorize("Project has validation errors", Colors.RED, use_color),
                use_color
            )
            return 1

    def _handle_dashboard(self, args) -> int:
        """Handle dashboard command."""
        use_color = self.config.color_output

        project_path = Path(args.project_path).resolve()

        self._print(
            f"Starting dashboard for: {colorize(str(project_path), Colors.BOLD, use_color)}",
            use_color
        )
        self._print(f"  Port: {args.port}", use_color)
        self._print(f"  Auto-open: {not args.no_open}", use_color)
        self._print("", use_color)

        try:
            from lib.debug_dashboard import DebugDashboard

            dashboard = DebugDashboard(
                project_path=project_path,
                port=args.port,
                auto_open=not args.no_open
            )
            dashboard.start()

        except ImportError:
            self._error("Dashboard requires additional dependencies", use_color)
            self._print("  Install with: pip install psutil", use_color)
            return 1
        except KeyboardInterrupt:
            self._print("\nDashboard stopped", use_color)
            return 0

        return 0

    def _print(self, message: str, use_color: bool = True) -> None:
        """Print message if not quiet."""
        if self.config.verbosity != Verbosity.QUIET:
            print(message)

    def _error(self, message: str, use_color: bool = True) -> None:
        """Print error message."""
        error_prefix = colorize("Error:", Colors.RED, use_color)
        print(f"{error_prefix} {message}", file=sys.stderr)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser (for backwards compatibility)."""
    cli = BlenderGSDCLI()
    return cli.parser


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code
    """
    cli = BlenderGSDCLI()
    return cli.run(args if args is not None else sys.argv[1:])


# Create a simple cli function for direct import
cli = BlenderGSDCLI()


if __name__ == "__main__":
    sys.exit(main())
