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
- [x] **Phase 9: Visual Polish** - Sleek brutalist mecha precision aesthetics ✓ COMPLETE

---
## GN Migration Phases (Phase 10-14)

*Added after Council of Ricks review identified architectural misalignment with intended Geometry Nodes stack.*

- [ ] **Phase 10: GN Foundation Migration** - Migrate Platform/Tile to Geometry Nodes
- [ ] **Phase 11: GN Arm System Migration** - Migrate arm physics to SimulationBuilder
- [ ] **Phase 12: GN Scale & Following Migration** - Migrate procedural generation and tracking
- [ ] **Phase 13: GN Export & Polish Integration** - Complete GN pipeline integration
- [ ] **Phase 14: Hybrid Mode & Deprecation** - Runtime mode selection, documentation, deprecation

---

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
- [x] 09-01-PLAN.md - Create visual polish system for sleek brutalist mecha aesthetic ✓
- [x] 09-02-PLAN.md - Create motion polish system for satisfying mechanical feedback ✓

### Phase 10: GN Foundation Migration
**Goal**: Migrate platform and tile systems to proper Geometry Nodes architecture
**Depends on**: Phase 9
**Requirements**: GN-01
**Success Criteria** (what must be TRUE):
  1. Platform geometry is generated via Geometry Nodes, not Python
  2. NodeTreeBuilder is used for all node tree creation
  3. InstanceController handles tile distribution
  4. Named attributes store masks for shader access
  5. Parity testing validates Python vs GN outputs match

Plans:
- [ ] 10-01-PLAN.md - Create GN platform package with PlatformGN, TileGN, GNValidator

### Phase 11: GN Arm System Migration
**Goal**: Migrate arm physics to SimulationBuilder zones
**Depends on**: Phase 10
**Requirements**: GN-02
**Success Criteria** (what must be TRUE):
  1. Arm physics uses SimulationBuilder zones
  2. Multi-joint state is stored in simulation state variables
  3. Constraints are enforced via GN math nodes
  4. Target reach is guaranteed within tolerance

Plans:
- [ ] 11-01-PLAN.md - Create PhysicsGN and ArmGN using SimulationBuilder

### Phase 12: GN Scale & Following Migration
**Goal**: Migrate procedural generation and following to GN
**Depends on**: Phase 11
**Requirements**: GN-03
**Success Criteria** (what must be TRUE):
  1. Procedural generation uses GN simulation zones
  2. Path following is implemented in GN
  3. System handles unlimited scale efficiently

Plans:
- [ ] 12-01-PLAN.md - Create ScaleGN and FollowingGN for procedural systems

### Phase 13: GN Export & Polish Integration
**Goal**: Complete GN pipeline with export and validation
**Depends on**: Phase 12
**Requirements**: GN-04
**Success Criteria** (what must be TRUE):
  1. GN output integrates with export pipeline
  2. Materials use named attributes from GN
  3. Performance is optimized for real-time
  4. Python vs GN parity is validated

Plans:
- [ ] 13-01-PLAN.md - Create ExportGN, MaterialGN, final parity validation

### Phase 14: Hybrid Mode & Deprecation
**Goal**: Provide smooth transition path from Python to GN
**Depends on**: Phase 13
**Requirements**: GN-05
**Success Criteria** (what must be TRUE):
  1. Hybrid mode allows Python OR GN selection at runtime
  2. Migration guide documents the GN API
  3. Deprecation warnings guide users to GN
  4. Python reference is archived but accessible

Plans:
- [ ] 14-01-PLAN.md - Create hybrid dispatcher, compatibility layer, migration guide

## Progress

**Execution Order:**
Phases 1-9: ✓ COMPLETE (Pure Python implementation)
Phases 10-14: GN Migration (In Progress)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Platform Foundation | 2/2 | ✓ Complete | 2026-03-05 |
| 2. Tile System | 2/2 | ✓ Complete | 2026-03-05 |
| 3. Arm Physics | 2/2 | ✓ Complete | 2026-03-05 |
| 4. Arm Constraints | 2/2 | ✓ Complete | 2026-03-05 |
| 5. Arm Folding | 2/2 | ✓ Complete | 2026-03-05 |
| 6. Unlimited Scale | 2/2 | ✓ Complete | 2026-03-05 |
| 7. Automated Following | 2/2 | ✓ Complete | 2026-03-05 |
| 8. Export Pipeline | 2/2 | ✓ Complete | 2026-03-05 |
| 9. Visual Polish | 2/2 | ✓ Complete | 2026-03-05 |
| **10. GN Foundation** | 0/1 | Not started | - |
| **11. GN Arms** | 0/1 | Not started | - |
| **12. GN Scale/Follow** | 0/1 | Not started | - |
| **13. GN Export/Polish** | 0/1 | Not started | - |
| **14. Hybrid/Deprecation** | 0/1 | Not started | - |

**Baseline Tag:** `v1.0-python-stable`

---

*Last updated: 2026-03-05 after Council of Ricks review and migration planning*
