# Mechanical Tile Platform

## What This Is

A procedurally-generated platform system that extends and retracts through mechanical arms placing and removing tiles. The platform automatically follows paths, characters, or objects, with physics-simulated multi-joint arms that fold under the platform when not in use. Tiles attach via high-tech magneto-mechanical side mounting.

**Core Value:** A sleek brutalist mechanical platform that builds itself — high-end mecha precision engineering that grows and shrinks to follow a target.

---

## The Problem

Creating dynamic, self-assembling platforms for animation and games requires:
- Complex armature animation synchronized with tile placement
- Physics simulation that looks natural but always hits targets
- Procedural generation at unlimited scale
- Dual export paths (render + real-time)

Existing solutions require manual keyframing or don't provide the mechanical realism of articulated arms placing individual tiles.

---

## The Solution

A Blender-based system with:
1. **Node-controlled tile placement** — Geometry/Animation nodes define where tiles appear/disappear
2. **Physics-simulated arms** — Rigid body simulation with constraints ensuring target reach
3. **Multi-joint folding mechanism** — Arms articulate and tuck under platform when idle
4. **Magneto-mechanical tile connection** — Visual feedback when tiles attach
5. **Automated following** — Platform grows/retracts to follow paths, characters, or objects
6. **Configurable tile shapes** — Square, octagonal, hexagonal support
7. **Unlimited procedural generation** — No hard cap on platform extent
8. **Dual export pipeline** — Blender renders + FBX/glTF for game engines

---

## For Whom

- **3D Artists** creating dynamic platform animations
- **Game Developers** needing self-assembling level geometry
- **Motion Designers** wanting mechanical precision aesthetics
- **Bret** exploring procedural mechanical systems in Blender

---

## Constraints

- Must work within Blender 4.x
- Must leverage parent project (blender_gsd) pipeline where applicable
- Physics must be deterministic for animation renders
- Game export must be performant (reasonable bone counts, optimized meshes)

---

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Position-based tile release | Arms reach exact coordinates before releasing — precise, controllable | — Pending |
| Multi-joint folding arms | Robot-arm style articulation for compact storage under platform | — Pending |
| Hybrid physics (natural + constrained) | Natural motion with overshoot, but guaranteed target reach | — Pending |
| Magneto-mechanical tile connection | High-tech aesthetic with visible/mechanical engagement | — Pending |
| Sleek brutalist visual style | Industrial function elevated to luxury — precision mecha | — Pending |
| Configurable tile shapes | System flexibility for different use cases | — Pending |
| Unlimited procedural generation | No artificial constraints on platform size | — Pending |
| Automated following | Platform responds to paths/characters/objects | — Pending |
| Dual export (render + game) | Maximum utility from single system | — Pending |
| Full system scope | Complete platform with all features | — Pending |

---

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Platform can extend by placing tiles at specified positions
- [ ] Platform can retract by removing tiles and storing arms underneath
- [ ] Arms use physics simulation for natural movement
- [ ] Arms are constrained to always reach their target positions
- [ ] Arms fold into compact storage under the platform when idle
- [ ] Tiles connect via magneto-mechanical side mounting (visual feedback)
- [ ] System supports multiple tile shapes (square, octagonal, hexagonal)
- [ ] Platform can grow unlimited in any direction
- [ ] Platform automatically follows paths/characters/objects
- [ ] System exports to FBX/glTF for game engines
- [ ] System renders high-quality animation in Blender
- [ ] Visual style is sleek brutalist with high-end mecha precision

### Out of Scope

- Real-time game engine integration (export only, not runtime)
- Physical/hardware implementation
- Non-flat platform topologies (bridges, stairs, ramps)
- Multi-level stacking

---

## Success Metrics

- Platform extends and retracts smoothly with natural arm motion
- Arms always reach target positions despite physics simulation
- Tile placement/removal is visually satisfying (magneto-mechanical feedback)
- System handles 100+ tiles without performance issues
- Exported FBX/glTF imports correctly in Unity/Unreal
- Rendered animation looks production-quality

---

## Risks

- **Physics determinism** — Randomized physics may not replay identically
- **Performance at scale** — Unlimited tiles could overwhelm system
- **Export complexity** — Bone counts for arms could bloat game files
- **Constraint tuning** — Finding balance between natural motion and guaranteed target reach

---

*Last updated: 2026-03-04 after initialization*
