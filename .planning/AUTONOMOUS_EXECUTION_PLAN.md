# Autonomous Execution Plan — Blender GSD Framework

**Created**: 2026-02-18
**Mode**: P0 Autonomous Execution
**Agent**: gsd-executor

---

## Executive Summary

This plan enables an agent to autonomously execute all assigned work from start to finish. The agent:
1. Resolves all blockers first
2. Proceeds through tasks in dependency order
3. Uses screenshots for progress verification
4. Commits atomic changes at each checkpoint
5. Never requires manual intervention

---

## Current State

### Completed Phases
- Phase 1: Core Infrastructure ✅
- Phase 2: Example Implementation ✅
- Phase 3: Agent System ✅

### Active Beads (Ready Work)
| ID | Title | Priority | Dependencies |
|----|-------|----------|--------------|
| blender_gsd-1 | Control Surface Design System (Meta) | P0 | None |
| blender_gsd-2 | REQ-CTRL-01: Universal Control System Core | P0 | None |
| blender_gsd-3 | REQ-CTRL-02: Hierarchical Parameter System | P0 | None |
| blender_gsd-7 | REQ-CTRL-01 (duplicate) | P0 | None |
| blender_gsd-8 | REQ-CTRL-02 (duplicate) | P0 | None |
| blender_gsd-19 | META-BLENDER-GSD (Framework) | P0 | None |

### Untracked Files Needing Commit
**Scripts:**
- `projects/neve_knobs/scripts/neve_knob_geo.py`
- `projects/neve_knobs/scripts/neve_knob_gn.py`
- `projects/neve_knobs/scripts/render_all_gn.py`
- `projects/neve_knobs/scripts/render_clean_knobs.py`
- `projects/neve_knobs/scripts/render_geo_debug.py`
- `projects/neve_knobs/scripts/render_geo_knob.py`
- `projects/neve_knobs/scripts/render_simple.py`
- `projects/neve_knobs/scripts/test_*.py` (all test scripts)
- `projects/neve_knobs/scripts/debug_*.py` (all debug scripts)

**Documentation:**
- `.planning/CONTROL_SURFACE_WORKFLOW.md`
- `.planning/FINDINGS.md`
- `.planning/research/CONTROL_SURFACE_DESIGN_RESEARCH.md`
- `.planning/research/PARAMETER_ARCHITECTURE.md`
- `projects/neve_knobs/docs/KNURLING_SYSTEM_SPEC.md`

**Task Files:**
- `projects/neve_knobs/tasks/knob_style*_gn.yaml` (5 files)

---

## Execution Path

### Phase A: Cleanup & Foundation (BLOCKER RESOLUTION)

#### A1. Clean Up Duplicate Beads
**Beads to close:** blender_gsd-7, blender_gsd-8 (duplicates of -2, -3)
```bash
bd close blender_gsd-7 --comment "Duplicate of blender_gsd-2"
bd close blender_gsd-8 --comment "Duplicate of blender_gsd-3"
```

#### A2. Commit All Working Code
**Files to commit:**
```bash
# Add all working scripts
git add projects/neve_knobs/scripts/*.py

# Add documentation
git add .planning/CONTROL_SURFACE_WORKFLOW.md
git add .planning/FINDINGS.md
git add .planning/research/
git add projects/neve_knobs/docs/

# Add task files
git add projects/neve_knobs/tasks/knob_style*_gn.yaml

# Commit
git commit -m "Add Neve knobs project with working Geometry Nodes implementation

- 5 procedural knob styles using pure Geometry Nodes
- Real mesh displacement for knurling (not shader bump)
- Configurable knurl zone, profile, and fade parameters
- Render scripts for preview and production
- Complete control surface research documentation
- Knurling system specification

🤖 Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

**Verification:** `git status` should show clean working tree

#### A3. Update .gitignore
Add build artifacts to ignore:
```gitignore
# Build outputs
*.blend
*.glb
*.gltf
*.stl
*.fbx
*.obj

# Render outputs
*.png
!docs/images/*.png

# OS files
.DS_Store
```

---

### Phase B: Neve Knobs Completion

#### B1. Generate Production Knob Renders
**Script:** `projects/neve_knobs/scripts/render_clean_knobs.py`
**Output:** `build/neve_knobs_production.png`
**Verification:** Screenshot of rendered output

#### B2. Export All 5 Knob Styles as GLB
**Task files:**
- `tasks/knob_style1_blue_gn.yaml`
- `tasks/knob_style2_silver_gn.yaml`
- `tasks/knob_style3_silver_deep_gn.yaml`
- `tasks/knob_style4_silver_shallow_gn.yaml`
- `tasks/knob_style5_red_gn.yaml`

**Output:** `build/neve_knob_style*_gn.glb` (5 files)
**Verification:** `ls -la build/*.glb | wc -l` should return 5

#### B3. Update Task Files for Consistency
Ensure all 5 GN task files have:
- Correct parameters matching neve_knob_gn.py capabilities
- Consistent output paths
- Production-ready settings

---

### Phase C: Phase 4 Documentation

#### C1. Create README.md
**Location:** `/README.md`
**Content:**
```markdown
# Blender GSD Framework

Deterministic, GSD-powered framework for procedural artifact generation in Blender 4.x/5.x.

## Philosophy

**Blender never stores intent. Blender only executes intent.**

- Intent lives in GSD
- Logic lives in scripts
- Structure lives in nodes
- Files are disposable. Regeneration is always possible.

## Quick Start

\`\`\`bash
# Run a task
blender --background --python scripts/run_task.py -- tasks/example_artifact.yaml

# Output appears in build/
\`\`\`

## Structure

- `lib/` - Core framework modules
- `scripts/` - Task runner and utilities
- `tasks/` - YAML task definitions
- `presets/` - Export and render profiles
- `projects/` - Individual artifact projects

## Projects

- `neve_knobs/` - Neve-style audio knob generator (5 styles)

## Documentation

- [Control Surface Workflow](.planning/CONTROL_SURFACE_WORKFLOW.md)
- [Parameter Architecture](.planning/research/PARAMETER_ARCHITECTURE.md)
```

#### C2. Create Architecture Documentation
**Location:** `/docs/ARCHITECTURE.md`
**Content:**
```markdown
# Architecture Overview

## Core Components

### 1. Pipeline (lib/pipeline.py)
Deterministic stage-based execution with debug breakpoints.

### 2. NodeKit (lib/nodekit.py)
Clean API for generating Blender node trees programmatically.

### 3. Masks (lib/masks.py)
Height-based and attribute-based masking for effects.

### 4. Scene Ops (lib/scene_ops.py)
Scene setup, lighting, and render configuration.

## Stage Order (Universal)

1. **Normalize** - Clean scene, set units
2. **Primary** - Core geometry
3. **Secondary** - Details and surface features
4. **Detail** - Fine details
5. **Output** - Export

## Determinism Guarantees

Same task + same parameters = identical output
```

#### C3. Create Claude Prompt Pack
**Location:** `/docs/CLAUDE_PROMPTS.md`
**Content:** Instructions for using Claude with this framework

---

### Phase D: Control Surface Core System (REQ-CTRL-01, REQ-CTRL-02)

#### D1. Create Parameter System Module
**Location:** `lib/control_system/parameters.py`
**Features:**
- YAML preset loading
- Inheritance chain (Global → Category → Variant → Instance)
- 9 parameter groups (GEOMETRY, MATERIAL, COLOR_SYSTEM, etc.)
- Runtime override support

#### D2. Create Color System Module
**Location:** `lib/control_system/colors.py`
**Features:**
- Semantic color tokens
- State colors (on, off, active, warning)
- Gradient support
- LAB color space interpolation

#### D3. Create Base Presets
**Location:** `presets/base.yaml`
**Content:**
```yaml
# Global defaults
global:
  units: meters
  scale: 0.001  # mm to meters

# Geometry defaults
geometry:
  base_diameter: 0.020
  height: 0.028
  segments: 64

# Material defaults
material:
  metallic: 0.0
  roughness: 0.3
  clearcoat: 0.0

# Color system defaults
color_system:
  primary: [0.5, 0.5, 0.5]
  secondary: [0.3, 0.3, 0.3]
  indicator: [1.0, 1.0, 1.0]
```

#### D4. Integrate with Neve Knobs
Update `neve_knob_gn.py` to use the new parameter system:
- Load preset from YAML
- Apply inheritance chain
- Generate geometry from resolved parameters

---

## Verification Checkpoints

### After Phase A
- [ ] `git status` shows clean tree
- [ ] `bd list` shows no duplicates
- [ ] All files committed with proper message

### After Phase B
- [ ] 5 GLB files exported
- [ ] Production render created
- [ ] Screenshot captured for verification

### After Phase C
- [ ] README.md exists with quickstart
- [ ] docs/ARCHITECTURE.md exists
- [ ] docs/CLAUDE_PROMPTS.md exists

### After Phase D
- [ ] lib/control_system/parameters.py exists
- [ ] lib/control_system/colors.py exists
- [ ] presets/base.yaml exists
- [ ] Neve knobs use new parameter system

---

## Screenshot Requirements

At each checkpoint, capture screenshot:
1. **Phase A:** `git status` output
2. **Phase B:** Rendered knob preview
3. **Phase C:** Documentation files in editor
4. **Phase D:** Generated knobs with parameter overlay

---

## Commit Strategy

Each phase gets its own atomic commit:

```
Phase A: "Clean up duplicate beads and commit working code"
Phase B: "Complete Neve knob production renders and exports"
Phase C: "Add Phase 4 documentation (README, architecture, prompts)"
Phase D: "Implement core control system parameter hierarchy"
```

---

## Error Recovery

If any step fails:
1. Log error to `.planning/autonomous-log.md`
2. Roll back to last checkpoint
3. Retry with adjusted approach
4. If 3 retries fail, pause and log blocker

---

## Execution Command

```bash
# Run autonomous execution
/gsd:execute-phase --autonomous --max-iterations 10
```

Or spawn executor directly with this plan as context.

---

## Success Criteria

- [ ] All duplicate beads closed
- [ ] All working code committed
- [ ] Phase 4 documentation complete
- [ ] Control system foundation implemented
- [ ] Neve knobs use new parameter system
- [ ] All verification screenshots captured
- [ ] Clean git history with atomic commits
