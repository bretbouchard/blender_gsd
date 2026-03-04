# _MANIFEST.md — Context Scoping for Claude

> This file tells Claude which documents are source of truth, which to load on demand, and which to skip entirely.

---

## Tier 1 — Source of Truth (Always Read)

These files are loaded for every task in this project:

```
PROJECT.md          # Project context, goals, constraints
REQUIREMENTS.md     # Scoped requirements (REQ-ID format)
ROADMAP.md          # Phase structure with requirement mapping
STATE.md            # Living memory and current position
```

---

## Tier 2 — Domain Context (Load on Demand)

Load these when working in specific areas:

### Current Phase
```
phases/{current}/PLAN.md      # Active execution plan
phases/{current}/SUMMARY.md   # Progress summary
```

### Patterns & Solutions
```
patterns/*.md                 # Reusable solutions and fixes
```

### Domain-Specific Requirements
```
REQUIREMENTS_TENTACLE.md         # Tentacle system requirements
REQUIREMENTS_ANAMORPHIC.md       # Anamorphic projection requirements
REQUIREMENTS_ANIMATION.md        # Animation system requirements
REQUIREMENTS_CINEMATIC.md        # Cinematic rendering requirements
REQUIREMENTS_FOLLOW_CAMERA.md    # Follow camera requirements
REQUIREMENTS_PRODUCTION_TRACKING.md  # Production tracking requirements
REQUIREMENTS_RETRO_GRAPHICS.md   # Retro graphics requirements
REQUIREMENTS_SHOT_PRESETS.md     # Shot presets requirements
REQUIREMENTS_TRACKING.md         # Tracking system requirements
```

### Specialized Plans
```
CINEMATIC_ROADMAP.md          # Cinematic production roadmap
TUTORIAL_MASTER_PLAN.md       # Tutorial system master plan
SCENE_GENERATION_MASTER_PLAN.md  # Scene generation architecture
FULL_PRODUCTION_SYSTEM.md     # Complete production pipeline
```

---

## Tier 3 — Archive (Skip Unless Asked)

Do not load unless explicitly requested:

```
phases/{completed}/           # Finished phases
research/                     # Research documents
tracking/                     # Tracking data
AUTONOMOUS_EXECUTION_*.md     # Execution logs
FINDINGS.md                   # Historical findings
06.6-render-system/           # Old render system phase
```

---

## Usage Instructions for Claude

When starting any task in this project:

1. **First:** Read `_MANIFEST.md` (this file)
2. **Always:** Load Tier 1 files for context
3. **Then:** Based on the task, load relevant Tier 2 files
4. **Never:** Load Tier 3 files unless explicitly asked

## Project-Specific Notes

This is a **Blender Python API project** for procedural generation and cinematic rendering. Key domains:

- **Geometry Nodes** — Procedural mesh generation
- **Camera Systems** — Follow cameras, shot presets, anamorphic projection
- **Rendering** — Eevee/Cycles integration, render automation
- **Animation** — Rigging, motion graphics, simulation nodes
- **Hair/Fur** — Grooming systems, particle workflows

When working in these domains, load the corresponding REQUIREMENTS_*.md files from Tier 2.
