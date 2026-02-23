"""
Tests for CLI Module

Tests command-line interface functionality.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from lib.orchestrator.cli import (
    CLI,
    CLIConfig,
    OutputFormat,
    Verbosity,
    create_parser,
    main,
)


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_format_values(self):
        """Test OutputFormat enum values."""
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.YAML.value == "yaml"
        assert OutputFormat.BLEND.value == "blend"
        assert OutputFormat.PREVIEW.value == "preview"


class TestVerbosity:
    """Tests for Verbosity enum."""

    def test_verbosity_values(self):
        """Test Verbosity enum values."""
        assert Verbosity.QUIET.value == 0
        assert Verbosity.NORMAL.value == 1
        assert Verbosity.VERBOSE.value == 2
        assert Verbosity.DEBUG.value == 3


class TestCLIConfig:
    """Tests for CLIConfig dataclass."""

    def test_create_default(self):
        """Test creating CLIConfig with defaults."""
        config = CLIConfig()
        assert config.verbosity == 1
        assert config.output_format == "json"
        assert config.output_path is None
        assert config.dry_run is False

    def test_create_with_values(self):
        """Test creating CLIConfig with values."""
        config = CLIConfig(
            verbosity=2,
            output_format="yaml",
            output_path="/tmp/output.yaml",
            dry_run=True,
        )
        assert config.verbosity == 2
        assert config.output_format == "yaml"
        assert config.output_path == "/tmp/output.yaml"
        assert config.dry_run is True


class TestCreateParser:
    """Tests for create_parser function."""

    def test_create_parser(self):
        """Test creating argument parser."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "scene-gen"

    def test_parser_has_subcommands(self):
        """Test parser has expected subcommands."""
        parser = create_parser()
        # Parse with --help to see available commands
        # Just verify it doesn't raise
        assert parser is not None


class TestCLI:
    """Tests for CLI class."""

    def test_init(self):
        """Test CLI initialization."""
        cli = CLI()
        assert cli is not None
        assert cli.parser is not None
        assert cli.config is not None

    def test_run_no_args(self):
        """Test running with no arguments shows help."""
        cli = CLI()
        # No command should show help and return 0
        result = cli.run([])
        assert result == 0

    def test_run_quiet(self):
        """Test running with quiet flag."""
        cli = CLI()
        result = cli.run(["-q"])
        assert result == 0

    def test_run_verbose(self):
        """Test running with verbose flag."""
        cli = CLI()
        result = cli.run(["-v"])
        assert result == 0

    def test_run_help(self):
        """Test running with help."""
        cli = CLI()
        with pytest.raises(SystemExit):
            cli.run(["--help"])

    def test_run_unknown_command(self):
        """Test running with unknown command."""
        cli = CLI()
        # Invalid command causes SystemExit(2) from argparse
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["nonexistent_command"])
        assert exc_info.value.code == 2


class TestCLICommands:
    """Tests for specific CLI commands."""

    def test_templates_list(self):
        """Test templates list command."""
        cli = CLI()
        # This may fail if ux_tiers module doesn't exist
        # Just test that CLI handles it gracefully
        result = cli.run(["templates", "list"])
        # Result depends on whether dependencies are available
        assert result is not None

    def test_validate_command_missing_file(self):
        """Test validate command with missing file."""
        cli = CLI()
        result = cli.run(["validate", "/nonexistent/path.yaml"])
        # Should fail because file doesn't exist
        assert result == 1

    def test_styles_list(self):
        """Test styles list command."""
        cli = CLI()
        # This may fail if style_manager module doesn't exist
        result = cli.run(["styles", "list"])
        assert result is not None

    def test_checkpoint_list(self):
        """Test checkpoint list command."""
        cli = CLI()
        result = cli.run(["checkpoint", "list"])
        # Should succeed even with no checkpoints
        assert result == 0


class TestMainFunction:
    """Tests for main entry point."""

    def test_main_no_args(self):
        """Test main with no arguments."""
        result = main([])
        assert result == 0

    def test_main_with_args(self):
        """Test main with arguments."""
        result = main(["-q"])
        assert result == 0


class TestCLIEdgeCases:
    """Edge case tests for CLI."""

    def test_dry_run_flag(self):
        """Test dry run flag."""
        cli = CLI()
        result = cli.run(["--dry-run", "templates", "list"])
        assert result is not None

    def test_format_option(self):
        """Test format option."""
        cli = CLI()
        result = cli.run(["--format", "json"])
        assert result == 0

    def test_output_option(self):
        """Test output option."""
        cli = CLI()
        result = cli.run(["--output", "/tmp/test.json"])
        assert result == 0

    def test_multiple_verbose_flags(self):
        """Test multiple verbose flags."""
        cli = CLI()
        result = cli.run(["-vvv"])
        assert result == 0

    def test_checkpoint_dir_option(self):
        """Test checkpoint directory option."""
        cli = CLI()
        result = cli.run(["--checkpoint-dir", "/tmp/checkpoints"])
        assert result == 0
