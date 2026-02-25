"""
Blender GSD CLI

Command-line interface for Blender GSD framework.
Provides project initialization, template management, and development tools.

Usage:
    blender-gsd init my-project
    blender-gsd init my-project --template control-surface
    blender-gsd templates list
    blender-gsd validate project.yaml
"""

from .main import main, cli, BlenderGSDCLI
from .init_cmd import InitCommand, create_project
from .templates_cmd import TemplatesCommand
from .validate_cmd import ValidateCommand

__all__ = [
    "main",
    "cli",
    "BlenderGSDCLI",
    "InitCommand",
    "create_project",
    "TemplatesCommand",
    "ValidateCommand",
]

__version__ = "0.1.0"
