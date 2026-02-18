# Blender GSD Framework

## Project Context

**Purpose**: A deterministic, GSD-powered framework for procedural artifact generation in Blender.

**Philosophy**:
- Blender never stores intent. Blender only executes intent.
- Intent lives in GSD. Logic lives in scripts. Structure lives in nodes.
- Files are disposable. Regeneration is always possible.

## Core Concepts

### Universal Vocabulary
| Term | Meaning |
|------|---------|
| Artifact | Any thing Blender produces |
| System | A reusable procedural logic block |
| Stage | A deterministic transformation step |
| Graph | A node-based execution structure |
| Parameters | Externalized control inputs |
| Outputs | Files or previews |

### Stage Pipeline
Every artifact is built as stages:
- **Stage 0** — Normalize: Convert params to canonical ranges
- **Stage 1** — Primary: Base shape, gross dimensions
- **Stage 2** — Secondary: Recesses, cutouts, boolean effects
- **Stage 3** — Detail: Surface effects (always masked)
- **Stage 4** — OutputPrep: Store attributes, finalize geometry

### Key Rules
1. **One Task → One Script → One Artifact**
2. **Graphs are generated, not drawn**
3. **Masking is a first-class concept**
4. **Debug hooks everywhere**

## Asset Library

Location: `/Volumes/Storage/3d`

Contents:
- 3,090 `.blend` files
- 29 KitBash3D packs
- VFX assets, animation resources
- 3D printing models
- ControlNet pose references

## Blender Ricks (Specialist Agents)

| Agent | Specialty |
|-------|-----------|
| geometry-rick | Geometry Nodes systems |
| shader-rick | Material/shader pipelines |
| compositor-rick | Compositor graphs |
| export-rick | Export pipeline optimization |
| render-rick | Render pipeline configuration |
| asset-rick | Asset library management |
| pipeline-rick | GSD pipeline orchestration |

## Technology Stack

- **Python 3.x** - Script layer
- **Blender 4.x** - Execution layer
- **Geometry Nodes** - Procedural geometry
- **Shader Nodes** - Material systems
- **Compositor** - Post-processing

## Integration Points

- **GSD Workflow**: Task files drive execution
- **Beads**: Track progress across projects
- **Confucius**: Pattern memory and learning
- **Council of Ricks**: Quality review with Blender Ricks

## Project Status

**Phase**: Foundation
**Started**: 2026-02-17
