# Blender GSD Framework

**Deterministic, GSD-powered procedural artifact generation for Blender.**

## Philosophy

> Blender never stores intent. Blender only executes intent.
>
> Intent lives in GSD. Logic lives in scripts. Structure lives in nodes.
> Files are disposable.

## Quick Start

```bash
# Run the example task
make run

# Or with a specific task
make run TASK=tasks/example_artifact.yaml

# Inspect interactively
make inspect
```

## Core Concepts

### Artifacts
Any thing Blender produces - panels, knobs, enclosures, materials, scenes.

### Systems
Reusable procedural logic blocks that generate artifacts.

### Stages
Every artifact is built through deterministic stages:
1. **Normalize** - Parameter canonicalization
2. **Primary** - Base geometry/material
3. **Secondary** - Modifications, cutouts
4. **Detail** - Surface effects (masked)
5. **OutputPrep** - Attributes, cleanup

### Masks
First-class infrastructure for controlling where effects apply.

## Directory Structure

```
blender_gsd/
├── lib/              # Core library (pipeline, nodekit, masks)
├── scripts/          # Task runner and artifact scripts
├── profiles/         # Export and render profiles
├── tasks/            # Task definitions
├── templates/        # Project templates
├── .planning/        # GSD planning documents
└── .claude/          # Claude configuration (agents, commands)
```

## Task Format

```yaml
task_id: my_artifact_v1
category: geometry
intent: >
  Description of what the artifact should be.

parameters:
  size: [0.25, 0.25, 0.08]
  detail_amount: 0.35

outputs:
  mesh:
    profile: stl_clean
    file: build/my_artifact.stl

debug:
  enabled: true
  show_mask: mask_height
```

## Blender Ricks

Specialist agents for the Council of Ricks:

| Agent | Specialty |
|-------|-----------|
| geometry-rick | Geometry Nodes systems |
| shader-rick | Material/shader pipelines |
| compositor-rick | Compositor graphs |
| export-rick | Export pipeline optimization |
| render-rick | Render pipeline configuration |
| asset-rick | Asset library management |
| pipeline-rick | GSD pipeline orchestration |

## Asset Library

Located at `/Volumes/Storage/3d`:
- 3,090 blend files
- 29 KitBash3D packs
- VFX assets, animation resources
- 3D printing models

## Requirements

- Blender 4.x
- Python 3.10+
- PyYAML (for task files)

## License

MIT
