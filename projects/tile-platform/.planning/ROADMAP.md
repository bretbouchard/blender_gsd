# Roadmap: Mechanical Tile Platform

## Overview

A procedurally-generated platform system that builds itself through mechanical arms placing and removing tiles. The system evolves from basic tile placement through physics-simulated articulated arms, unlimited procedural generation, automated following, and dual export pipelines—all with sleek brutalist mecha precision.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Platform Foundation** - Basic tile placement and retraction system
- [ ] **Phase 2: Tile System** - Tile shapes and magneto-mechanical connections
- [ ] **Phase 3: Arm Physics** - Physics simulation for natural arm movement
- [ ] **Phase 4: Arm Constraints** - Constrained arm movement ensuring target reach
- [ ] **Phase 5: Arm Folding** - Multi-joint folding mechanism for compact storage
- [ ] **Phase 6: Unlimited Scale** - Procedural generation at unlimited extent
- [ ] **Phase 7: Automated Following** - Platform follows paths/characters/objects
- [ ] **Phase 8: Export Pipeline** - Dual export for game engines and Blender renders
- [ ] **Phase 9: Visual Polish** - Sleek brutalist mecha precision aesthetics

## Phase Details

### Phase 1: Platform Foundation
**Goal**: Users can place and remove tiles at specified positions to extend and retract the platform
**Depends on**: Nothing (first phase)
**Requirements**: PLATFORM-01, PLATFORM-02
**Success Criteria** (what must be TRUE):
  1. User can trigger tile placement at a specific coordinate and a tile appears there
  2. User can trigger tile removal and the tile disappears from the platform
  3. Platform maintains a grid of placed tiles that can be queried
  4. System tracks which tiles are currently placed and which are available

Plans:
- [ ] 01-01-PLAN.md - Create foundation module structure with Platform, Tile, and Grid classes
- [ ] 01-02-PLAN.md - Implement tile geometry generation and platform tile management methods

### Phase 2: Tile System
**Goal**: Users have visually rich tile connections with configurable shapes
**Depends on**: Phase 1
**Requirements**: TILE-01, TILE-02
**Success Criteria** (what must be TRUE):
  1. When a tile is placed adjacent to another, visible magneto-mechanical connection feedback appears
  2. User can select from square, octagonal, or hexagonal tile shapes before placement
  3. Tiles of different shapes cannot connect to each other (validation feedback)
  4. Connection animation plays when tiles attach (visual engagement)

Plans:
- [ ] 02-01-PLAN.md - Create tile placement and retraction logic for path following
- [ ] 02-02-PLAN.md - Implement magneto-mechanical tile connection system with visual feedback

### Phase 3: Arm Physics
**Goal**: Users see natural, physics-driven arm movement when placing tiles
**Depends on**: Phase 1, Phase 2
**Requirements**: ARM-01
**Success Criteria** (what must be TRUE):
  1. Arms move with natural physics simulation (momentum, overshoot, settling)
  2. Arm motion looks organic rather than mechanically precise
  3. Physics simulation is deterministic (same input produces same motion)
  4. Arms respond to physics forces (gravity, collisions with platform)

Plans:
- [ ] 03-01-PLAN.md - Create arm physics system with multi-joint arms and constraints
- [ ] 03-02-PLAN.md - Create complete arm assembly and multi-arm controller

### Phase 4: Arm Constraints
**Goal**: Arms always reach their target positions despite physics simulation
**Depends on**: Phase 3
**Requirements**: ARM-02
**Success Criteria** (what must be TRUE):
  1. When a target position is set, the arm reaches it within tolerance
  2. Arms don't overshoot or miss targets due to physics randomness
  3. Constraint strength is configurable (softer for natural look, harder for precision)
  4. Arms reach targets at predictable times for animation synchronization

Plans:
- [ ] 04-01-PLAN.md - Implement arm constraint system that guarantees target reach
- [ ] 04-02-PLAN.md - Create integrated constraint solver that works with physics

### Phase 5: Arm Folding
**Goal**: Arms fold into compact storage under the platform when not placing tiles
**Depends on**: Phase 4
**Requirements**: ARM-03
**Success Criteria** (what must be TRUE):
  1. When idle, arms fold into a compact configuration beneath the platform
  2. Folding animation looks natural (multi-joint articulation)
  3. Folded arms don't interfere with platform tiles or each other
  4. Arms smoothly transition from folded to extended when needed

Plans:
- [ ] 05-01-PLAN.md - Create arm folding system for compact storage under platform
- [ ] 05-02-PLAN.md - Create folding controller that integrates with tile system

### Phase 6: Unlimited Scale
**Goal**: Platform can grow to unlimited size in any direction without performance collapse
**Depends on**: Phase 1, Phase 2
**Requirements**: SCALE-01
**Success Criteria** (what must be TRUE):
  1. User can place tiles at arbitrary distances from origin (no hard cap)
  2. System handles 100+ tiles without significant frame rate drop
  3. Memory usage scales linearly with tile count
  4. Far-distant tiles don't cause precision issues (floating point handling)

Plans:
- [ ] 06-01-PLAN.md - Create unlimited scale management system
- [ ] 06-02-PLAN.md - Create performance optimization for large-scale platforms

### Phase 7: Automated Following
**Goal**: Platform automatically grows and retracts to follow a target
**Depends on**: Phase 1, Phase 2, Phase 6
**Requirements**: FOLLOW-01
**Success Criteria** (what must be TRUE):
  1. User can assign a path, character, or object as the follow target
  2. Platform extends tiles ahead of the moving target (predictive placement)
  3. Platform retracts tiles behind the moving target (cleanup)
  4. Following behavior is smooth and doesn't cause visual stuttering

Plans:
- [ ] 07-01-PLAN.md - Create automated following system for target tracking
- [ ] 07-02-PLAN.md - Create predictive tile placement and removal

### Phase 8: Export Pipeline
**Goal**: Users can export the platform for game engines and render high-quality animations
**Depends on**: All previous phases
**Requirements**: EXPORT-01, EXPORT-02
**Success Criteria** (what must be TRUE):
  1. User can export platform to FBX format that imports correctly in Unity
  2. User can export platform to glTF format that imports correctly in Unreal
  3. Exported armatures have reasonable bone counts (optimized for game engines)
  4. User can render the platform animation in Blender at production quality

Plans:
- [ ] 08-01-PLAN.md - Create export pipeline for game engines (FBX/glTF)
- [ ] 08-02-PLAN.md - Create render pipeline for high-quality Blender animation

### Phase 9: Visual Polish
**Goal**: Platform has sleek brutalist mecha precision visual style
**Depends on**: All previous phases
**Requirements**: STYLE-01
**Success Criteria** (what must be TRUE):
  1. Arms have high-end mecha precision aesthetic (industrial luxury)
  2. Tiles have sleek brutalist design (bold geometric forms)
  3. Materials and lighting emphasize precision engineering quality
  4. Motion has satisfying weight and mechanical authenticity

Plans:
- [ ] 09-01-PLAN.md - Create visual polish system for sleek brutalist mecha aesthetic
- [ ] 09-02-PLAN.md - Create motion polish system for satisfying mechanical feedback

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Platform Foundation | 0/2 | Not started | - |
| 2. Tile System | 0/2 | Not started | - |
| 3. Arm Physics | 0/2 | Not started | - |
| 4. Arm Constraints | 0/2 | Not started | - |
| 5. Arm Folding | 0/2 | Not started | - |
| 6. Unlimited Scale | 0/2 | Not started | - |
| 7. Automated Following | 0/2 | Not started | - |
| 8. Export Pipeline | 0/2 | Not started | - |
| 9. Visual Polish | 0/2 | Not started | - |

---

*Last updated: 2026-03-04 after phase planning*
