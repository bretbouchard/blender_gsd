# Blender GSD Framework - Findings & Current State

**Last Updated**: 2026-02-18
**Session**: Beads Tracking Setup

---

## Project Overview

**Blender GSD** is a deterministic, GSD-powered framework for procedural artifact generation in Blender 4.x/5.x.

**Core Philosophy:**
- Blender never stores intent. Blender only executes intent.
- Intent lives in GSD. Logic lives in scripts. Structure lives in nodes.
- Files are disposable. Regeneration is always possible.

---

## Current State Summary

### Completed Phases (v0.1 Foundation)

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | DONE | Core Infrastructure - lib modules, pipeline, nodekit, masks |
| Phase 2 | DONE | Example Implementation - artifact task/script, profiles |
| Phase 3 | DONE | Agent System - 7 Blender Ricks defined |
| Phase 4 | PENDING | Documentation - README, architecture, CI/CD |

### Active Work

1. **Neve Knobs Project** (`projects/neve_knobs/`)
   - 5 procedural knob styles generated
   - Geometry Nodes based generation
   - Render scripts created
   - Working preview renders

2. **Control Surface Research** (`.planning/research/`)
   - `CONTROL_SURFACE_DESIGN_RESEARCH.md` - 26KB of design research
   - `PARAMETER_ARCHITECTURE.md` - 21KB of parameter system design

3. **Knurling Specification** (`projects/neve_knobs/docs/`)
   - `KNURLING_SYSTEM_SPEC.md` - Detailed knurling implementation spec

---

## Beads Tracking Structure

### Meta-Level
```
META-BLENDER-GSD (blender_gsd-19)
└── Blender GSD Framework - root epic
```

### Milestones
```
EPIC-V0.1: Foundation (blender_gsd-20)
├── Phases 1-3: COMPLETE
└── Phase 4: Documentation - PENDING

EPIC-V0.4: Control Surface Design System (blender_gsd-21)
├── REQ-CTRL-01: Universal Control System
├── REQ-CTRL-02: Hierarchical Parameters
├── REQ-CTRL-03: Style Preset Library
├── REQ-CTRL-04: Control Element Types
└── REQ-CTRL-05: Morphing Engine
```

### Feature Beads (Core Requirements)
| ID | Title | Priority | Status |
|----|-------|----------|--------|
| blender_gsd-22 | REQ-CORE-01: Deterministic Execution | P0 | In Progress |
| blender_gsd-23 | REQ-CORE-02: Stage-Based Pipeline | P0 | Implemented |
| blender_gsd-24 | REQ-CORE-03: Mask Infrastructure | P0 | Implemented |
| blender_gsd-25 | REQ-CORE-04: Node Generation | P0 | Implemented |

### Feature Beads (Control Surface)
| ID | Title | Priority | Status |
|----|-------|----------|--------|
| blender_gsd-26 | REQ-CTRL-01: Universal Control System | P0 | Planned |
| blender_gsd-27 | REQ-CTRL-02: Hierarchical Parameters | P0 | Planned |
| blender_gsd-28 | REQ-CTRL-03: Style Preset Library | P1 | Planned |
| blender_gsd-29 | REQ-CTRL-04: Control Element Types | P0 | In Progress |
| blender_gsd-30 | REQ-CTRL-05: Morphing Engine | P1 | Planned |

### Active Task Beads
| ID | Title | Priority | Status |
|----|-------|----------|--------|
| blender_gsd-31 | TASK-NEVE-KNOBS: Neve Knob Rendering | P0 | Open |
| blender_gsd-32 | TASK-PHASE4-DOCS: Phase 4 Documentation | P1 | Open |
| blender_gsd-33 | TASK-KNURLING-SPEC: Knurling System Spec | P0 | Open |

---

## Key Technical Findings

### Geometry Nodes Workflow
- **Working**: Using Geometry Nodes for procedural knob generation
- **Approach**: Python generates/modifies node trees programmatically
- **Benefit**: Fully deterministic, version-controllable

### Rendering Pipeline
- **Engine**: Cycles for production, EEVEE for preview
- **Lighting**: Studio HDRI + key lights
- **Materials**: PBR-based with debug visualization modes

### Parameter System Architecture
```
Global Parameters
├── Color System (semantic tokens)
├── Material System (PBR properties)
├── Animation System (easing curves)
├── Lighting Presets
│
├── Category Parameters (Console, Synth, Pedal)
│   ├── Variant Parameters (Neve 1073, SSL 4000, etc.)
│   │   └── Instance Parameters (individual knob)
```

### Knob Profiles Identified (10+)
1. Chicken Head
2. Cylindrical
3. Domed
4. Flattop
5. Soft-touch
6. Pointer
7. Instrument
8. Collet
9. Apex
10. Custom (user-defined)

---

## Untracked Files (Need Decision)

From git status - these files need to be either:
- Committed to repo
- Added to .gitignore
- Reviewed and potentially removed

### New Scripts (candidate for commit)
- `projects/neve_knobs/scripts/neve_knob_geo.py`
- `projects/neve_knobs/scripts/neve_knob_gn.py`
- `projects/neve_knobs/scripts/render_*.py`
- `projects/neve_knobs/scripts/test_*.py`

### New Documentation (candidate for commit)
- `.planning/CONTROL_SURFACE_WORKFLOW.md`
- `.planning/research/` directory
- `projects/neve_knobs/docs/`

### Task Files (candidate for commit)
- `projects/neve_knobs/tasks/knob_style*_gn.yaml`

---

## Next Steps

1. **Immediate**
   - [ ] Complete Neve knob renders (TASK-NEVE-KNOBS)
   - [ ] Finalize knurling specification (TASK-KNURLING-SPEC)

2. **Short Term**
   - [ ] Phase 4 documentation (TASK-PHASE4-DOCS)
   - [ ] Commit working scripts to repo

3. **Medium Term**
   - [ ] Implement REQ-CTRL-01 (Universal Control System)
   - [ ] Build parameter hierarchy (REQ-CTRL-02)

---

## Asset Library Reference

**Location**: `/Volumes/Storage/3d`
- 3,090 `.blend` files
- 29 KitBash3D packs
- VFX assets, animation resources
- 3D printing models
- ControlNet pose references

---

## Blender Ricks (Specialist Agents)

| Agent | Specialty | Status |
|-------|-----------|--------|
| geometry-rick | Geometry Nodes systems | Defined |
| shader-rick | Material/shader pipelines | Defined |
| compositor-rick | Compositor graphs | Defined |
| export-rick | Export pipeline optimization | Defined |
| render-rick | Render pipeline configuration | Defined |
| asset-rick | Asset library management | Defined |
| pipeline-rick | GSD pipeline orchestration | Defined |

---

## Commands Reference

```bash
# View all beads
bd list

# View ready work
bd ready

# Show specific bead
bd show blender_gsd-31

# Update bead status
bd update blender_gsd-31 --status in_progress
```
