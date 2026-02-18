# Blender GSD Framework Requirements

## REQ-CORE-01: Deterministic Execution
**Priority**: P0
**Status**: In Progress

The framework MUST produce identical outputs given identical inputs.
- Same task file + same parameters = same artifact
- No hidden state, no manual modifications
- Full regeneration from source

### Acceptance Criteria
- [ ] Running same task twice produces byte-identical STL
- [ ] No .blend files contain manual modifications
- [ ] All parameters are externalized

---

## REQ-CORE-02: Stage-Based Pipeline
**Priority**: P0
**Status**: Implemented

All artifacts are built through a deterministic stage pipeline.
- Stage order is fixed and enforced
- Each stage is isolated and testable
- Debug breakpoints allow stage inspection

### Acceptance Criteria
- [x] Pipeline class enforces stage order
- [x] stop_after_stage debug control works
- [ ] Each stage has unit tests

---

## REQ-CORE-03: Mask Infrastructure
**Priority**: P0
**Status**: Implemented

Masking is a first-class concept for all systems.
- Every effect must be maskable
- Masks are stored as named attributes
- Debug materials visualize masks

### Acceptance Criteria
- [x] height_mask_geo function implemented
- [x] Debug material system created
- [ ] Curvature and attribute masks added

---

## REQ-CORE-04: Node Generation
**Priority**: P0
**Status**: Implemented

All node graphs are generated via Python.
- Manual node wiring is forbidden
- NodeKit helper provides clean API
- Graphs are version-controlled as code

### Acceptance Criteria
- [x] NodeKit class implemented
- [x] Works with Geometry, Shader, Compositor nodes
- [ ] Graph comparison/diff tools

---

## REQ-IO-01: Task File Format
**Priority**: P0
**Status**: Implemented

Tasks are defined in YAML/JSON with explicit schema.
- Parameters are scalar, vector, or enum only
- Outputs are explicitly declared
- Debug controls are opt-in

### Acceptance Criteria
- [x] YAML loading works
- [x] Validation function exists
- [ ] JSON schema for validation

---

## REQ-IO-02: Export Profiles
**Priority**: P1
**Status**: Implemented

Export configurations are reusable profiles.
- STL, GLTF, FBX, OBJ profiles defined
- Profiles are referenced by name in tasks
- Format-specific optimizations are documented

### Acceptance Criteria
- [x] export_profiles.yaml created
- [x] STL export works
- [ ] GLTF export tested
- [ ] FBX export tested

---

## REQ-ASSET-01: Asset Library Integration
**Priority**: P1
**Status**: Implemented

Framework is aware of external asset library.
- Asset paths are configurable
- KitBash packs are indexed
- Suggestion system recommends relevant assets

### Acceptance Criteria
- [x] asset_library.yaml configuration
- [x] Pack metadata documented
- [ ] Runtime asset search

---

## REQ-RICKS-01: Blender Ricks Agents
**Priority**: P1
**Status**: Implemented

Specialist agents for Blender-specific domains.
- 7 Blender Ricks defined
- Each has clear expertise area
- Compatible with Council of Ricks

### Acceptance Criteria
- [x] geometry-rick
- [x] shader-rick
- [x] compositor-rick
- [x] export-rick
- [x] render-rick
- [x] asset-rick
- [x] pipeline-rick

---

## REQ-PROJECT-01: Project Isolation
**Priority**: P1
**Status**: Planned

Each Blender project is self-contained.
- Projects are separate git repos
- Framework is shared via submodule or pip
- No cross-project contamination

### Acceptance Criteria
- [ ] Project template system
- [ ] Init command for new projects
- [ ] Isolated build directories
