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

---

## REQ-CTRL-01: Universal Control Surface System
**Priority**: P0
**Status**: Planned

A comprehensive system for generating ANY control surface aesthetic with complete flexibility.
- Supports knobs, faders, buttons, LEDs, encoders, displays
- Hierarchical parameter inheritance
- Style preset system for instant aesthetic changes
- Smooth morphing between any styles

### Acceptance Criteria
- [ ] Can generate 10+ knob profile types
- [ ] Can replicate Neve 1073 aesthetic
- [ ] Can replicate SSL 4000 aesthetic
- [ ] Can replicate Roland TR-808 aesthetic
- [ ] Morphing between any two styles works
- [ ] All parameters are runtime-adjustable

---

## REQ-CTRL-02: Hierarchical Parameter System
**Priority**: P0
**Status**: Planned

Parameters are organized in logical groups with inheritance.
- Global → Category → Variant → Instance hierarchy
- Color system with semantic tokens
- Material system with PBR properties
- Animation system with easing curves
- Lighting presets

### Acceptance Criteria
- [ ] 9 parameter groups defined and implemented
- [ ] Inheritance chain works correctly
- [ ] Override at any level works
- [ ] YAML preset loading works

---

## REQ-CTRL-03: Style Preset Library
**Priority**: P1
**Status**: Planned

Comprehensive library of iconic equipment presets.
- Consoles: Neve, SSL, API, Harrison
- Synths: Moog, Roland, Sequential, Korg
- Pedals: Boss, MXR, EHX, boutique
- Drum machines: 808, 909, MPC, Elektron
- Outboard: 1176, LA-2A, Pultec

### Acceptance Criteria
- [ ] 5+ console presets
- [ ] 5+ synth presets
- [ ] 5+ pedal presets
- [ ] 3+ drum machine presets
- [ ] 3+ outboard gear presets

---

## REQ-CTRL-04: Control Element Types
**Priority**: P0
**Status**: Planned

Complete coverage of all control element types.

### Rotary Controls
- [ ] 10+ knob profiles (chicken head, cylindrical, domed, etc.)
- [ ] Surface features (knurling, ribbing, grooves)
- [ ] Indicator types (line, dot, pointer, skirt)
- [ ] Collet and cap systems
- [ ] Backlit indicators

### Linear Controls
- [ ] Channel faders (100mm)
- [ ] Short faders (60mm)
- [ ] Mini faders (45mm)
- [ ] Motorized faders
- [ ] Touch-sensitive faders

### Buttons/Switches
- [ ] Momentary buttons
- [ ] Latching buttons
- [ ] Illuminated buttons
- [ ] Cap switch system
- [ ] Toggle switches
- [ ] Rotary push-switches

### Indicators
- [ ] Single LEDs
- [ ] LED bars
- [ ] VU meters
- [ ] 7-segment displays
- [ ] OLED/LCD placeholders

### Encoders
- [ ] Detented encoders
- [ ] Smooth encoders
- [ ] Push-encoders

---

## REQ-CTRL-05: Morphing Engine
**Priority**: P1
**Status**: Planned

Smooth transitions between any control styles.
- Geometry morphing (blend shapes)
- Material morphing (property interpolation)
- Color morphing (color space interpolation)
- Animation system for transitions
- Staggered animation support

### Acceptance Criteria
- [ ] Morph between any two presets
- [ ] Per-group morph factors
- [ ] Per-control morph factors
- [ ] Animation with easing curves
- [ ] Real-time preview
