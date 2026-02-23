# Council of Ricks Review Report
## Scene Generation Master Plan v1.0

**Date:** 2026-02-21
**Review Mode:** All Hands on Deck (9 Specialists)
**Decision:** **CONDITIONAL APPROVE** with Required Changes

---

## Executive Summary

The Scene Generation Master Plan demonstrates strong architectural thinking and comprehensive coverage of the scene generation domain. However, several critical gaps were identified that must be addressed before implementation can proceed.

### Overall Assessment

| Metric | Score |
|--------|-------|
| Architecture | 8/10 |
| Feasibility | 6/10 (downgraded due to GN algorithm issues) |
| Completeness | 7/10 |
| Test Coverage | 3/10 (missing entirely) |
| UX Design | 6/10 |

**VERDICT: CONDITIONAL APPROVE**
- Must address 3 REJECT findings before implementation
- 5 CONDITIONAL items should be addressed during implementation

---

## Specialist Reviews

### geometry-rick: REJECT

**Finding:** BSP floor plan generation and L-system road networks are **NOT feasible in pure Geometry Nodes**.

**Technical Analysis:**
- BSP requires recursive subdivision with arbitrary depth
- L-systems require string rewriting with context sensitivity
- GN has no loops, no string manipulation, no recursive node evaluation
- Attempting these in pure GN would create exponentially large node graphs

**Required Changes:**
1. Move BSP algorithm to Python pre-processing (`lib/interiors/bsp_solver.py`)
2. Move L-system to Python pre-processing (`lib/urban/l_system.py`)
3. GN used only for final geometry generation from pre-computed data
4. Define JSON interchange format between Python and GN

**Revised Architecture:**
```
Python Pre-Processing        Geometry Nodes
┌─────────────────┐         ┌─────────────────┐
│ BSP Solver      │ ─JSON─► │ Wall Builder    │
│ (Floor Plan)    │         │ (From Polygons) │
└─────────────────┘         └─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│ L-System Roads  │ ─JSON─► │ Road Geometry   │
│ (Network Gen)   │         │ (From Curves)   │
└─────────────────┘         └─────────────────┘
```

---

### shader-rick: CONDITIONAL PASS

**Finding:** Material system needs expansion for scene diversity.

**Issues:**
- No mention of PBR material library
- Missing material variation system (weathering, damage)
- No material assignment strategy for procedural scenes

**Required Changes:**
1. Add REQ-PH-08: Material Library System
2. Integrate with existing `lib/materials/sanctus/` (v3.3.2)
3. Define material variation nodes for procedural weathering
4. Create material assignment rules by asset category

---

### render-rick: CONDITIONAL PASS

**Finding:** Render pipeline solid but needs hardware specifications.

**Issues:**
- Performance targets lack hardware specifications
- No render farm / distributed rendering consideration
- Missing render time budgets per scene complexity

**Required Changes:**
1. Define reference hardware:
   - Minimum: M1 MacBook Pro, 16GB
   - Recommended: M2 Ultra, 64GB
   - Production: Multi-GPU render farm
2. Add render time budgets:
   - Preview: <30s per frame
   - Standard: <5min per frame
   - Production: <30min per frame
3. Define scene complexity limits per tier

---

### compositor-rick: REJECT

**Finding:** Missing Cryptomatte integration and multi-pass compositing strategy.

**Issues:**
- No Cryptomatte pass specification for object isolation
- No multi-pass workflow (beauty, diffuse, specular, shadow, AO)
- No EXR multi-layer output strategy
- Missing post-processing pipeline

**Required Changes:**
1. Add REQ-CP-01: Cryptomatte Pass System
   - Object ID by asset category
   - Material ID for selective adjustments
   - Asset-level isolation for review workflow
2. Add REQ-CP-02: Multi-Pass Render Pipeline
   - Beauty pass
   - Diffuse + Specular
   - Shadow catch pass
   - AO pass
   - Volume pass
3. Add REQ-CP-03: EXR Output Strategy
   - 16-bit half-float for preview
   - 32-bit float for production
   - Layer naming convention
4. Add REQ-CP-04: Post-Processing Chain
   - Color grading LUTs
   - Film grain
   - Lens distortion
   - Chromatic aberration

---

### pipeline-rick: CONDITIONAL PASS

**Finding:** Pipeline architecture solid, needs checkpoint strategy.

**Issues:**
- No checkpoint/resume strategy for long generations
- No partial regeneration capability
- Missing cache invalidation rules

**Required Changes:**
1. Add checkpoint files at each stage
2. Define cache keys for asset loading
3. Add resume capability for interrupted generation

---

### rick-prime: CONDITIONAL APPROVE

**Finding:** UX needs progressive disclosure for different user levels.

**Issues:**
- Full YAML configuration is overwhelming for beginners
- No template library for common scenes
- Missing wizard interface for guided setup

**Required Changes:**
1. Add UX Tiers:
   - **Tier 1 (Template)**: Pre-built scene templates, one-click generation
   - **Tier 2 (Wizard)**: Guided Q&A for customization
   - **Tier 3 (YAML)**: Full configuration file access
   - **Tier 4 (Python API)**: Programmatic control
2. Create scene template library:
   - "Portrait Studio" - Single subject, lighting presets
   - "Product Shot" - Turntable, backdrop options
   - "Interior Scene" - Room with furniture
   - "Street Scene" - Road with vehicles/pedestrians
   - "Full Environment" - Complex multi-zone scene

---

### performance-rick: CONDITIONAL APPROVE

**Finding:** Performance targets need hardware baselines and optimization strategy.

**Issues:**
- "10,000+ instances" is meaningless without LOD specs
- No memory budget for asset loading
- Missing culling strategy for off-screen geometry

**Required Changes:**
1. Define LOD tiers:
   - LOD0: Full detail (<100 instances, <10m distance)
   - LOD1: Reduced polys (100-1000 instances, 10-50m)
   - LOD2: Billboard/impostor (1000+ instances, >50m)
2. Add memory budget:
   - Texture pool: 4GB max
   - Geometry pool: 2GB max
   - Instance buffer: 1GB max
3. Add culling rules:
   - Frustum culling
   - Occlusion culling
   - Distance-based LOD switching

---

### automation-rick: PARTIAL PASS

**Finding:** Missing CLI and headless specifications.

**Issues:**
- No command-line interface defined
- No headless Blender execution strategy
- Missing batch processing support

**Required Changes:**
1. Add CLI specification:
   ```bash
   blender-gsd scene-generate --template "Portrait Studio" --preset "rembrandt" --output scene.blend
   blender-gsd asset-index --path /Volumes/Storage/3d/ --update
   blender-gsd validate --scene scene.blend --check scale,materials,lighting
   ```
2. Add headless execution:
   - `--background` flag for all operations
   - JSON output for machine parsing
   - Exit codes for CI integration

---

### security-rick: CONDITIONAL APPROVE

**Finding:** Asset paths and file operations need security hardening.

**Issues:**
- Direct file path exposure in configs
- No path traversal protection
- Missing input validation on YAML configs

**Required Changes:**
1. Add path sanitization:
   - Resolve symlinks
   - Block `..` traversal
   - Whitelist allowed directories
2. Add YAML validation:
   - Schema validation
   - Type checking
   - Size limits
3. Add audit logging for file operations

---

### dufus-rick: REJECT

**Finding:** No testing strategy documented.

**Issues:**
- No unit test specifications
- No integration test plan
- No visual regression testing
- No performance benchmarks
- Missing Oracle integration for validation

**Required Changes:**
1. Add Testing Strategy section with:
   - Unit tests: 80%+ coverage target
   - Integration tests: End-to-end scene generation
   - Visual regression: Screenshot comparison
   - Performance benchmarks: <100ms search, <5min scene generation
2. Test files structure:
   ```
   tests/
   ├── unit/
   │   ├── test_asset_vault.py
   │   ├── test_bsp_solver.py
   │   ├── test_l_system.py
   │   └── test_scale_normalizer.py
   ├── integration/
   │   ├── test_scene_generation.py
   │   └── test_photoshoot_presets.py
   └── visual/
       └── test_render_comparison.py
   ```
3. Add Oracle assertions:
   ```python
   from lib.oracle import Oracle

   def test_bsp_generates_valid_floor_plan():
       solver = BSPSolver(seed=42)
       plan = solver.generate(width=10, height=8, room_count=5)
       Oracle.assert_equal(len(plan.rooms), 5)
       Oracle.assert_true(plan.is_connected())
   ```

---

## Required Changes Summary

### Critical (Must Fix Before Implementation)

| ID | Issue | Owner | Phase |
|----|-------|-------|-------|
| CR-01 | BSP to Python pre-processing | geometry-rick | Phase 3 |
| CR-02 | L-system to Python pre-processing | geometry-rick | Phase 4 |
| CR-03 | Add Testing Strategy section | dufus-rick | All phases |
| CR-04 | Add Cryptomatte/multi-pass compositing | compositor-rick | Phase 8 |

### High Priority (Fix During Implementation)

| ID | Issue | Owner | Phase |
|----|-------|-------|-------|
| HP-01 | Add UX tiers (Template/Wizard/YAML/API) | rick-prime | Phase 5 |
| HP-02 | Define hardware specifications | performance-rick | All phases |
| HP-03 | Add CLI/headless specification | automation-rick | Phase 5 |
| HP-04 | Add material library system | shader-rick | Phase 2 |

### Medium Priority (Address When Possible)

| ID | Issue | Owner | Phase |
|----|-------|-------|-------|
| MP-01 | Security hardening | security-rick | Phase 1 |
| MP-02 | Checkpoint/resume strategy | pipeline-rick | Phase 5 |
| MP-03 | LOD and culling strategy | performance-rick | Phase 6 |

---

## Revised Phase Structure

After incorporating Council feedback, phases are restructured:

### Phase 1: Asset Vault System (5-7 days) + [MP-01 Security]
- Add security hardening for file operations
- Add audit logging

### Phase 2: Studio & Photoshoot System (4-5 days) + [HP-04 Materials]
- Add material library integration
- Add Sanctus integration

### Phase 3: Interior Layout System (7-10 days) + [CR-01 BSP]
- **NEW:** `lib/interiors/bsp_solver.py` (Python pre-processing)
- BSP generates JSON floor plans
- GN consumes JSON for wall geometry

### Phase 4: Road & Urban Infrastructure (6-8 days) + [CR-02 L-System]
- **NEW:** `lib/urban/l_system.py` (Python pre-processing)
- L-system generates JSON road networks
- GN consumes JSON for road geometry

### Phase 5: Scene Orchestrator (8-10 days) + [HP-01 UX, HP-03 CLI]
- Add UX tiers (Template → Wizard → YAML → API)
- Add CLI specification
- Add checkpoint/resume [MP-02]

### Phase 6: Geometry Nodes Extensions (5-7 days) + [MP-03 LOD]
- Add LOD system
- Add culling strategy

### Phase 7: Character & Verticals (5-6 days)
- No changes

### Phase 8: Quality & Review System (4-5 days) + [CR-04 Compositing]
- **NEW:** Cryptomatte pass system
- **NEW:** Multi-pass render pipeline
- **NEW:** Post-processing chain

### NEW: Phase 9: Testing Infrastructure (3-4 days)
- [CR-03] Add comprehensive testing
- Unit tests (80%+ coverage)
- Integration tests
- Visual regression tests
- Performance benchmarks

---

## Next Actions

1. **Update Master Plan** with all required changes
2. **Create detailed PLAN.md for Phase 1** with security hardening
3. **Create Python architecture** for BSP and L-system pre-processing
4. **Define JSON interchange format** between Python and GN
5. **Begin Phase 1 implementation** after plan approval

---

## Appendix: JSON Interchange Formats

### BSP Floor Plan Output
```json
{
  "version": "1.0",
  "dimensions": {"width": 10.0, "height": 8.0},
  "rooms": [
    {
      "id": "room_0",
      "type": "living_room",
      "polygon": [[0,0], [5,0], [5,4], [0,4]],
      "doors": [{"wall": 1, "position": 0.5, "width": 0.9}],
      "windows": [{"wall": 0, "position": 0.3, "width": 1.2}]
    }
  ],
  "connections": [
    {"from": "room_0", "to": "room_1", "via": "door_0"}
  ]
}
```

### L-System Road Network Output
```json
{
  "version": "1.0",
  "nodes": [
    {"id": "node_0", "position": [0, 0], "type": "intersection_4way"},
    {"id": "node_1", "position": [50, 0], "type": "intersection_3way"}
  ],
  "edges": [
    {
      "id": "edge_0",
      "from": "node_0",
      "to": "node_1",
      "curve": [[0,0], [25,0], [50,0]],
      "lanes": 2,
      "width": 7.0,
      "markings": ["center_line", "edge_lines"]
    }
  ]
}
```

---

*Report compiled by Council of Ricks Orchestrator*
*All Hands on Deck Mode - 9 Specialists Consulted*
