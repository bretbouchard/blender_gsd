# Project Template

This directory contains the scaffold for new Blender GSD projects.

## Usage

To create a new project:

```bash
# Copy this template to your new project location
cp -r /path/to/blender_gsd/templates/project /path/to/new-project

cd /path/to/new-project

# Initialize git
git init

# Add blender_gsd as a submodule (recommended)
git submodule add https://github.com/YOUR_USERNAME/blender_gsd.git lib/blender_gsd

# Or install via pip (if published)
# pip install blender-gsd
```

## Template Structure

```
project/
├── tasks/              # Task definitions (YAML)
├── scripts/            # Artifact scripts (Python)
├── build/              # Generated outputs (gitignored)
├── .planning/          # GSD planning documents
│   ├── PROJECT.md
│   ├── REQUIREMENTS.md
│   └── ROADMAP.md
├── Makefile            # Common commands
└── README.md           # Project documentation
```

## Quick Start

1. Create a task file in `tasks/`
2. Create an artifact script in `scripts/`
3. Run: `make run TASK=tasks/my_artifact.yaml`
