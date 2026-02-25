"""
CLI Types

Data types and configurations for the Blender GSD CLI.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any


class ProjectTemplate(Enum):
    """Available project templates."""
    DEFAULT = "default"
    CONTROL_SURFACE = "control-surface"
    CINEMATIC = "cinematic"
    PRODUCTION = "production"
    CHARLOTTE = "charlotte"
    MINIMAL = "minimal"


class Verbosity(Enum):
    """Verbosity levels."""
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


@dataclass
class ProjectConfig:
    """
    Project configuration.

    Attributes:
        name: Project name
        template: Template to use
        output_path: Where to create the project
        description: Project description
        author: Project author
        blender_gsd_path: Path to blender_gsd library
        init_git: Whether to initialize git
        init_beads: Whether to initialize beads tracking
        init_planning: Whether to create .planning directory
    """
    name: str
    template: ProjectTemplate = ProjectTemplate.DEFAULT
    output_path: Optional[Path] = None
    description: str = ""
    author: str = ""
    blender_gsd_path: Optional[Path] = None
    init_git: bool = True
    init_beads: bool = True
    init_planning: bool = True


@dataclass
class TemplateInfo:
    """
    Information about a project template.

    Attributes:
        template_id: Template identifier
        name: Human-readable name
        description: Template description
        category: Template category
        features: List of features included
        files: Files created by template
        requires: Required dependencies
    """
    template_id: str
    name: str
    description: str
    category: str = "general"
    features: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)


@dataclass
class CLIConfig:
    """
    CLI configuration.

    Attributes:
        verbosity: Output verbosity
        color_output: Enable colored output
        dry_run: Show what would be done without executing
        config_file: Path to config file
    """
    verbosity: Verbosity = Verbosity.NORMAL
    color_output: bool = True
    dry_run: bool = False
    config_file: Optional[Path] = None


# Template registry
TEMPLATE_REGISTRY: Dict[str, TemplateInfo] = {
    "default": TemplateInfo(
        template_id="default",
        name="Default Project",
        description="Standard Blender GSD project with tasks, scripts, and planning",
        category="general",
        features=[
            "Task definitions (YAML)",
            "Artifact scripts (Python)",
            "GSD planning structure",
            "VS Code settings",
            "Makefile for common commands",
        ],
        files=[
            "tasks/",
            "scripts/",
            ".planning/PROJECT.md",
            ".planning/REQUIREMENTS.md",
            ".planning/ROADMAP.md",
            ".vscode/settings.json",
            "Makefile",
            "README.md",
        ],
    ),
    "control-surface": TemplateInfo(
        template_id="control-surface",
        name="Control Surface Design",
        description="Control surface design project with knob/fader/button components",
        category="audio",
        features=[
            "Control surface parameter loaders",
            "Style presets (Neve, SSL, API)",
            "Morph engine integration",
            "Debug material system",
            "Product shot rendering",
        ],
        files=[
            "tasks/",
            "scripts/",
            "configs/controls/",
            ".planning/",
            ".vscode/",
            "Makefile",
            "README.md",
        ],
        requires=["lib/inputs/", "lib/morph/"],
    ),
    "cinematic": TemplateInfo(
        template_id="cinematic",
        name="Cinematic Rendering",
        description="Cinematic rendering project with camera, lighting, and animation",
        category="cinematic",
        features=[
            "Camera system with presets",
            "Lighting rigs and HDRI",
            "Animation and motion paths",
            "Shot assembly from YAML",
            "Batch rendering",
        ],
        files=[
            "shots/",
            "configs/cinematic/",
            ".planning/",
            ".vscode/",
            "Makefile",
            "README.md",
        ],
        requires=["lib/cinematic/"],
    ),
    "production": TemplateInfo(
        template_id="production",
        name="Production Tracking",
        description="Full production with characters, locations, and shots",
        category="production",
        features=[
            "Character management",
            "Location management",
            "Shot scheduling",
            "1-sheet generation",
            "Progress tracking",
        ],
        files=[
            "configs/production/",
            ".planning/",
            ".vscode/",
            "Makefile",
            "README.md",
        ],
        requires=["lib/production/"],
    ),
    "charlotte": TemplateInfo(
        template_id="charlotte",
        name="Charlotte Digital Twin",
        description="Charlotte digital twin project with geometry pipeline",
        category="digital-twin",
        features=[
            "Coordinate transformation",
            "Road network geometry",
            "Building extrusion",
            "POI placement",
            "Scene assembly",
        ],
        files=[
            "data/",
            "maps/",
            ".planning/",
            ".vscode/",
            "Makefile",
            "README.md",
        ],
        requires=["lib/charlotte_digital_twin/"],
    ),
    "minimal": TemplateInfo(
        template_id="minimal",
        name="Minimal Project",
        description="Bare-bones project with just the essentials",
        category="general",
        features=[
            "Basic README",
            "Minimal Makefile",
        ],
        files=[
            "README.md",
            "Makefile",
        ],
    ),
}
