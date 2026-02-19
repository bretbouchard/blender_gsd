# Blender GSD Framework Roadmap

## Milestone: v0.1 - Foundation
**Target**: 2026-02

### Phase 1: Core Infrastructure
- [x] Git repo initialized
- [x] Directory structure created
- [x] Core library modules (pipeline, nodekit, masks, scene_ops)
- [x] Debug material system
- [x] Export utilities
- [x] Task file format
- [x] Task runner script

### Phase 2: Example Implementation
- [x] Example artifact task
- [x] Example artifact script
- [x] Export profiles defined
- [x] Render profiles defined
- [x] Asset library configuration

### Phase 3: Agent System
- [x] geometry-rick
- [x] shader-rick
- [x] compositor-rick
- [x] export-rick
- [x] render-rick
- [x] asset-rick
- [x] pipeline-rick

### Phase 4: Documentation
- [ ] README with quickstart
- [ ] Architecture documentation
- [ ] Claude prompt pack
- [ ] CI/CD setup

---

## Milestone: v0.2 - First Artifacts
**Target**: TBD

### Phase 5: Real Artifacts
- [ ] Panel artifact (full implementation)
- [ ] Knob artifact
- [ ] Enclosure artifact
- [ ] Material system integration

### Phase 6: Asset Integration
- [ ] Runtime asset search
- [ ] KitBash pack indexing
- [ ] Asset extraction from .blend files

---

## Milestone: v0.3 - Production Ready
**Target**: TBD

### Phase 7: Quality Assurance
- [ ] Unit tests for all lib modules
- [ ] Integration tests for pipelines
- [ ] CI pipeline with Blender
- [ ] Regression test suite

### Phase 8: Ergonomics
- [ ] Project template system
- [ ] `blender-gsd init` command
- [ ] VS Code integration
- [ ] Debug dashboard

---

## Milestone: v1.0 - Stable Release
**Target**: TBD

### Phase 9: Polish
- [ ] Complete documentation
- [ ] Example gallery
- [ ] Performance optimization
- [ ] Version migration tools

### Phase 10: Community
- [ ] Public release
- [ ] Contribution guidelines
- [ ] Issue templates
- [ ] Release process documented

---

---

## Milestone: v0.4 - Control Surface Design System
**Target**: TBD

### Phase 5: Core Control System (REQ-CTRL-01, REQ-CTRL-02)
- [x] Parameter hierarchy implementation
- [x] 9 parameter group loaders
- [x] YAML preset system
- [x] Color system with semantic tokens
- [x] Material system with PBR
- [x] Basic geometry generation for knobs

### Phase 5.1: Knob Geometry Profiles (REQ-CTRL-04)
- [x] Chicken head profile
- [x] Cylindrical profile
- [x] Domed profile
- [x] Flattop profile
- [x] Soft-touch profile
- [x] Pointer profile
- [x] Instrument profile
- [x] Collet profile
- [x] Apex profile
- [x] Custom profile loader

### Phase 5.2: Knob Surface Features (REQ-CTRL-04)
- [x] Knurling system (straight, diamond, helical patterns)
- [x] Ribbing system (horizontal rings)
- [x] Groove system (single, multi, spiral)
- [x] Indicator geometry (line, dot, pointer)
- [x] Collet and cap systems
- [x] Backlit indicator support

### Phase 5.3: Fader System (REQ-CTRL-04)
- [x] Channel fader geometry
- [x] Short fader geometry
- [x] Mini fader geometry
- [x] Fader knob styles
- [x] Track/scale generation
- [x] LED meter integration

### Phase 5.4: Button System (REQ-CTRL-04)
- [x] Momentary button geometry
- [x] Latching button geometry
- [x] Illuminated button system
- [x] Cap switch system
- [x] Toggle switch geometry

### Phase 5.5: LED/Indicator System (REQ-CTRL-04)
- [x] Single LED geometry
- [x] LED bar geometry
- [x] VU meter geometry
- [x] 7-segment placeholder
- [x] Emissive material integration

### Phase 5.6: Style Presets - Consoles (REQ-CTRL-03)
- [x] Neve 1073 preset
- [x] Neve 88RS preset
- [x] SSL 4000 E preset
- [x] SSL 9000 J preset
- [x] API 2500 preset

### Phase 5.7: Style Presets - Synths (REQ-CTRL-03)
- [x] Moog Minimoog preset
- [x] Roland TR-808 preset
- [x] Roland TR-909 preset
- [x] Sequential Prophet-5 preset
- [x] Korg MS-20 preset

### Phase 5.8: Style Presets - Pedals (REQ-CTRL-03)
- [x] Boss Compact preset
- [x] MXR Classic preset
- [x] Electro-Harmonix Big Muff preset
- [x] Ibanez Tube Screamer preset
- [x] Strymon preset

### Phase 5.9: Morphing Engine (REQ-CTRL-05)
- [x] Geometry morphing
- [x] Material morphing
- [x] Color morphing (LAB interpolation)
- [x] Animation system for transitions
- [x] Staggered animation support
- [x] Real-time morph preview

### Phase 5.10: Debug Material System (REQ-CTRL-DEBUG)
**Goal:** Create a node-centric debug material workflow for per-section visualization with easy toggle between debug and production materials.

**Tasks:**
- [ ] Create debug material utilities (create_debug_material, create_debug_palette)
- [ ] Create Debug_Material_Switcher node group
- [ ] Integrate debug materials into InputNodeGroupBuilder
- [ ] Add exposed "Debug Mode" toggle input
- [ ] Update render script for debug views

**Deliverables:**
- `lib/inputs/debug_materials.py` - Debug material creation utilities
- `lib/inputs/node_groups/debug_switcher.py` - Material switcher node group
- Per-section colors: A_Top (Red), A_Mid (Green), B_Mid (Blue), B_Bot (Yellow)
- Preset palettes: rainbow, grayscale, complementary, heat_map

---

## Milestone: v0.5 - Cinematic Rendering System - COMPLETE
**Target**: 2026-02-19
**Design**: `.planning/design/CINEMATIC_SYSTEM_DESIGN.md`
**Requirements**: `.planning/REQUIREMENTS_CINEMATIC.md`
**Version**: 0.3.0
**Modules**: 30 | **Exports**: 315+ | **Lines**: ~24,000

### Phase 6.0: Foundation (REQ-CINE-01)
**Goal:** Establish foundational module structure, configuration directories, and state persistence framework for the cinematic rendering system.
**Plans:** 3 plans
**Completed:** 2026-02-18

**Dependencies:**
- Depends on: None (foundation phase)
- Enables: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
- Critical Path: Yes
- Test Coverage: 80%

Plans:
- [x] 06-01-PLAN.md - Create lib/cinematic/ Python package with types, enums, and state persistence
- [x] 06-02-PLAN.md - Create configuration directory structure with 21 YAML preset files
- [x] 06-03-PLAN.md - Create state persistence directory structure with frame index

### Phase 6.1: Camera System (REQ-CINE-CAM, REQ-CINE-PLUMB)
**Goal:** Implement comprehensive camera system with lenses, sensor presets, camera rigs, and plumb bob targeting system.
**Plans:** 5 plans
**Completed:** 2026-02-18

**Dependencies:**
- Depends on: 6.0
- Enables: 6.2, 6.4, 6.5, 7.1
- Critical Path: Yes
- Test Coverage: 80%
- Oracle Validators: compare_numbers, compare_vectors, file_exists

Plans:
- [x] 06.1-01-PLAN.md - Extend types.py with PlumbBobConfig, RigConfig, ImperfectionConfig, MultiCameraLayout dataclasses; create preset_loader.py
- [x] 06.1-02-PLAN.md - Create camera.py with camera creation, DoF configuration, and preset application
- [x] 06.1-03-PLAN.md - Create plumb_bob.py with targeting system (auto/manual/object modes)
- [x] 06.1-04-PLAN.md - Create lenses.py with compositor-based imperfections (vignette, chromatic aberration, flare)
- [x] 06.1-05-PLAN.md - Create rigs.py with camera rig constraints (tripod, dolly, crane, steadicam, drone) and multi-camera layouts

### Phase 6.2: Lighting System (REQ-CINE-LIGHT)
**Goal:** Implement comprehensive lighting system with area/spot/point/sun lights, HDRI environment, gel system, light linking, and 8+ preset rigs.
**Plans:** 5 plans
**Completed:** 2026-02-18

**Dependencies:**
- Depends on: 6.0, 6.1
- Enables: 8.3 (Style Director)
- Critical Path: No
- Test Coverage: 80%
- Oracle Validators: compare_numbers, compare_vectors

Plans:
- [x] 06.2-01-PLAN.md - Extend LightConfig with type-specific properties; add GelConfig, HDRIConfig, LightRigConfig dataclasses; add lighting preset loaders
- [x] 06.2-02-PLAN.md - Create lighting.py with create_light, create_area_light, create_spot_light, setup_light_linking, apply_lighting_rig
- [x] 06.2-03-PLAN.md - Create gel.py with apply_gel, create_gel_from_preset, kelvin_to_rgb, combine_gels
- [x] 06.2-04-PLAN.md - Create hdri.py with setup_hdri, load_hdri_preset, find_hdri_path, clear_hdri
- [x] 06.2-05-PLAN.md - Update __init__.py with all lighting exports and version bump to 0.1.2

### Phase 6.3: Backdrop System (REQ-CINE-ENV)
**Goal:** Implement backdrop system for product rendering with infinite curves, gradient backgrounds, shadow catchers, and HDRI backdrops.
**Plans:** 3 plans
**Completed:** 2026-02-18

**Dependencies:**
- Depends on: 6.0
- Enables: 9.1 (Set Builder)
- Critical Path: No
- Parallel Safe With: 6.1, 6.5
- Test Coverage: 80%

Plans:
- [x] 06.3-01-PLAN.md - Extend BackdropConfig with additional properties; add backdrop preset loaders (infinite curves, gradients, environments)
- [x] 06.3-02-PLAN.md - Create backdrops.py with create_infinite_curve, create_gradient_material, setup_shadow_catcher, create_backdrop
- [x] 06.3-03-PLAN.md - Update __init__.py with all backdrop exports and version bump to 0.1.3

### Phase 6.4: Color Pipeline (REQ-CINE-LUT)
**Goal:** Implement color management system with view transforms, LUT validation, compositor-based LUT application, and exposure lock system.
**Plans:** 3 plans
**Completed:** 2026-02-19

**Dependencies:**
- Depends on: 6.0, 6.1
- Enables: 12.1 (Compositor)
- Critical Path: No
- Parallel Safe With: 6.2
- Test Coverage: 80%

Plans:
- [x] 06.4-01-PLAN.md - Add ColorConfig, LUTConfig, ExposureLockConfig dataclasses; add ViewTransform, WorkingColorSpace enums; add color preset loaders
- [x] 06.4-02-PLAN.md - Create color.py with set_view_transform, apply_color_preset, validate_lut_file, apply_lut (with intensity blending), calculate_auto_exposure
- [x] 06.4-03-PLAN.md - Update __init__.py with all color exports (27 new exports)

### Phase 6.5: Animation System (REQ-CINE-ANIM, REQ-CINE-PATH)
**Goal:** Implement camera animation system with orbit, dolly, crane, pan, tilt, rack focus, and turntable rotation, plus procedural motion paths.
**Plans:** 3 plans
**Completed:** 2026-02-19

**Dependencies:**
- Depends on: 6.0, 6.1
- Enables: 11.1 (Timeline System)
- Critical Path: No
- Parallel Safe With: 6.3
- Test Coverage: 80%

Plans:
- [x] 06.5-01-PLAN.md - Add AnimationConfig, MotionPathConfig, TurntableConfig dataclasses; add animation preset loaders
- [x] 06.5-02-PLAN.md - Create animation.py with orbit/dolly/crane/turntable animations; create motion_path.py with Bezier path generation
- [x] 06.5-03-PLAN.md - Update __init__.py with all animation exports (~30 new exports)

### Phase 6.6: Render System (REQ-CINE-RENDER)
**Goal:** Implement render system with quality tier presets, render pass configuration, EXR output, hardware-aware denoising, and batch rendering.
**Plans:** 3 plans
**Completed:** 2026-02-18

**Dependencies:**
- Depends on: 6.0, 6.1
- Enables: 6.7, 12.1, 13.1
- Critical Path: Yes
- Test Coverage: 80%

Plans:
- [x] 06.6-01-PLAN.md - Add CinematicRenderSettings dataclass, render enums, and render preset loaders
- [x] 06.6-02-PLAN.md - Create render.py with quality tiers, pass configuration, EXR output, denoiser selection, and batch rendering
- [x] 06.6-03-PLAN.md - Update __init__.py with all render exports and version bump to 0.2.2

### Phase 6.7: Support Systems
**Goal:** Implement support utilities for shot variation, state capture/comparison, depth organization, composition guides, and lens effects.
**Plans:** 3 plans
**Completed:** 2026-02-19

**Dependencies:**
- Depends on: 6.0, 6.6
- Enables: None (utility phase)
- Critical Path: No
- Test Coverage: 80%

Plans:
- [x] 06.7-01-PLAN.md - Add ShuffleConfig, FrameState, DepthLayerConfig, CompositionGuide, LensFXConfig dataclasses; add preset loaders
- [x] 06.7-02-PLAN.md - Create shuffler.py, frame_store.py, depth_layers.py, composition.py, lens_fx.py modules with YAML presets
- [x] 06.7-03-PLAN.md - Update __init__.py with all support system exports and version bump to 0.2.3

### Phase 6.8: Shot Assembly (REQ-CINE-SHOT, REQ-CINE-TEMPLATE)
**Goal:** Implement complete shot assembly from YAML with template inheritance.
**Plans:** 3 plans
**Completed:** 2026-02-19

Plans:
- [x] 06.8-01-PLAN.md - Add ShotTemplateConfig, ShotAssemblyConfig dataclasses with template inheritance support
- [x] 06.8-02-PLAN.md - Create shot.py with assemble_shot, load_shot_yaml, save_shot_state, render_shot
- [x] 06.8-03-PLAN.md - Create templates.yaml with base templates, update __init__.py, version bump to 0.2.4

### Phase 6.9: Camera Matching (REQ-CINE-MATCH, REQ-CINE-AUDIO)
**Goal:** Implement camera matching from reference images and audio sync with beat markers.
**Plans:** 3 plans
**Completed:** 2026-02-19

Plans:
- [x] 06.9-01-PLAN.md - Add CameraMatchConfig, TrackingImportConfig, AudioSyncConfig, CameraProfile dataclasses
- [x] 06.9-02-PLAN.md - Create camera_match.py and audio_sync.py modules
- [x] 06.9-03-PLAN.md - Create camera_profiles.yaml with device profiles, update __init__.py, version bump to 0.2.5

### Phase 6.10: Integration & Testing
**Goal:** Complete integration with control surface system, testing utilities, and benchmarks.
**Plans:** 3 plans
**Completed:** 2026-02-19

Plans:
- [x] 06.10-01-PLAN.md - Add IntegrationConfig, TestConfig, PerformanceConfig, BenchmarkResult dataclasses
- [x] 06.10-02-PLAN.md - Create testing.py and benchmark.py modules
- [x] 06.10-03-PLAN.md - Update __init__.py with all exports, version bump to 0.3.0 (MILESTONE COMPLETE)

---

## Milestone: v0.6 - Motion Tracking System
**Target**: TBD
**Requirements**: `.planning/REQUIREMENTS_TRACKING.md`
**Beads Epic**: `blender_gsd-41`

### Phase 7.0: Tracking Foundation (REQ-TRACK-01)
**Priority**: P1 | **Est. Effort**: 2-3 days
**Beads**: `blender_gsd-42`
**Plans:** 5 plans

**Dependencies:**
- Depends on: 6.0, 6.1
- Enables: 7.1, 7.2, 7.3, 7.4, 7.5
- Critical Path: No
- Test Coverage: 80%

**Goal**: Establish motion tracking module structure, configuration directories, and state persistence.

**Deliverables**:
```
lib/cinematic/tracking/
├── __init__.py
├── types.py              # Tracking data types
├── footage.py            # Footage analysis and import
├── point_tracker.py      # Point/feature tracking (Phase 7.1)
├── camera_solver.py      # Camera solve integration (Phase 7.1)
├── object_tracker.py     # Object tracking (Phase 7.5)
├── import_export.py      # External format support
└── calibration.py        # Lens/camera calibration (Phase 7.2)

configs/cinematic/tracking/
├── camera_profiles.yaml  # Already exists from Phase 6.9
├── tracking_presets.yaml
├── solver_settings.yaml
└── import_formats.yaml
```

Plans:
- [ ] 07.0-01-PLAN.md - Create tracking types (TrackData, SolveData, FootageMetadata, TrackingSession, SolveReport)
- [ ] 07.0-02-PLAN.md - Create config YAML files (tracking_presets, solver_settings, import_formats)
- [ ] 07.0-03-PLAN.md - Create footage.py with ffprobe metadata extraction
- [ ] 07.0-04-PLAN.md - Create import_export.py with coordinate conversion and Nuke .chan import
- [ ] 07.0-05-PLAN.md - Update package exports and version bump to 0.3.1

---

### Phase 7.1: Core Tracking (REQ-TRACK-POINT, REQ-TRACK-SOLVE)
**Priority**: P0 | **Est. Effort**: 9-11 days
**Beads**: `blender_gsd-43`, `blender_gsd-44`
**Plans:** 4 plans

**Dependencies:**
- Depends on: 7.0
- Enables: 7.2, 7.4
- Critical Path: No
- Test Coverage: 80%

**Goal**: Implement point tracking and camera solving.

**Deliverables**:
```
lib/cinematic/tracking/
├── context.py            # Context manager for tracking operators
├── presets.py            # Tracking preset loader
├── point_tracker.py      # REQ-TRACK-POINT implementation
├── quality.py            # Track quality analysis and filtering
└── camera_solver.py      # REQ-TRACK-SOLVE implementation

configs/cinematic/tracking/
├── tracking_presets.yaml # Extended with detection parameters
└── solver_settings.yaml  # Solver configuration presets
```

Plans:
- [ ] 07.1-01-PLAN.md - Create context.py with tracking_context manager; create presets.py with tracking preset loader; update tracking_presets.yaml
- [ ] 07.1-02-PLAN.md - Create point_tracker.py with feature detection, KLT tracking, track management; create quality.py with track analysis
- [ ] 07.1-03-PLAN.md - Create camera_solver.py with libmv integration, camera creation; update solver_settings.yaml
- [ ] 07.1-04-PLAN.md - Update package exports and version bump to 0.3.2

**Acceptance Criteria**:
- [ ] Auto-detect 50+ trackable features
- [ ] Solve produces camera with <1px reprojection error
- [ ] Camera animation keyframes created in Blender

---

### Phase 7.2: Footage & Camera Profiles (REQ-TRACK-FOOTAGE, REQ-TRACK-CAMPROF)
**Priority**: P1 | **Est. Effort**: 5-7 days
**Beads**: `blender_gsd-45`, `blender_gsd-46`
**Plans:** 4 plans

**Dependencies:**
- Depends on: 7.0, 7.1
- Enables: 7.4
- Critical Path: No
- Test Coverage: 80%

**Goal**: Implement footage analysis and device-specific camera profiles.

**Deliverables**:
```
lib/cinematic/tracking/
├── footage.py            # Extended with FFprobeMetadataExtractor, content analysis
├── rolling_shutter.py    # NEW: Detection and compensation
├── distortion.py         # NEW: ST-Map generation
├── vanishing_points.py   # NEW: Focal length estimation
└── types.py              # Extended with FootageMetadata, RollingShutterConfig

configs/cinematic/tracking/
└── camera_profiles.yaml  # Extended with rolling_shutter read times
```

Plans:
- [ ] 07.2-01-PLAN.md - Extend footage.py with FFprobeMetadataExtractor, iPhone metadata, content analysis
- [ ] 07.2-02-PLAN.md - Create rolling_shutter.py with detection and compensation
- [ ] 07.2-03-PLAN.md - Create distortion.py (ST-Map), vanishing_points.py (focal length estimation)
- [ ] 07.2-04-PLAN.md - Update camera_profiles.yaml with rolling shutter, package exports, version bump to 0.3.3

**Acceptance Criteria**:
- [ ] FFprobeMetadataExtractor extracts iPhone QuickTime metadata
- [ ] 30+ device profiles available with rolling shutter data
- [ ] Rolling shutter compensation reduces skew
- [ ] ST-Map generation produces UV coordinate maps
- [ ] Vanishing point detection estimates focal length

---

### Phase 7.3: External Import/Export (REQ-TRACK-IMPORT)
**Priority**: P1 | **Est. Effort**: 3-4 days
**Beads**: `blender_gsd-47`
**Plans:** 3 plans

**Dependencies:**
- Depends on: 7.0, 7.1
- Enables: 7.4
- Critical Path: No
- Test Coverage: 80%

**Goal**: Import tracking data from professional match-move software.

**Deliverables**:
```
lib/cinematic/tracking/
├── import_export.py        # Extended with ColladaParser, C3DParser
│                           # TDEExportHelper, SynthEyesExportHelper
│                           # FBX export via TrackingExporter
```

Plans:
- [ ] 07.3-01-PLAN.md - Add ColladaParser for .dae import via Blender native importer
- [ ] 07.3-02-PLAN.md - Add C3DParser, TDEExportHelper, SynthEyesExportHelper, FBX export
- [ ] 07.3-03-PLAN.md - Update package exports, version bump to 1.1.0

**Acceptance Criteria**:
- [ ] Collada .dae import creates animated camera
- [ ] C3D marker data imports correctly
- [ ] 3DEqualizer/SynthEyes export scripts generate valid Python
- [ ] FBX export creates valid camera file
- [ ] Coordinate system conversion works (Y-up to Z-up)

---

### Phase 7.4: Compositing & Shot Integration (REQ-TRACK-COMPOSITE, REQ-TRACK-SHOT)
**Priority**: P1 | **Est. Effort**: 5-7 days
**Beads**: `blender_gsd-48`, `blender_gsd-49`
**Plans:** 5 plans

**Dependencies:**
- Depends on: 7.0, 7.1, 7.2
- Enables: Production tracking workflow
- Critical Path: No
- Test Coverage: 80%

**Goal**: Integrate tracking with compositing and shot assembly.

**Deliverables**:
```
lib/cinematic/tracking/
├── compositor.py          # NEW: Compositor node creation from tracking data
├── session.py             # NEW: Session persistence and resume capability
└── shot_integration.py    # NEW: Shot YAML extension for tracking

lib/cinematic/
└── shot.py                # Extended with shadow catcher, tracking hooks

configs/cinematic/tracking/
└── composite_presets.yaml # NEW: Composite mode presets
```

Plans:
- [ ] 07.4-01-PLAN.md - Create compositor.py with stabilization nodes, corner pin, alpha over, shadow composite
- [ ] 07.4-02-PLAN.md - Create session.py with TrackingSessionManager, checkpoint, resume support
- [ ] 07.4-03-PLAN.md - Create shot_integration.py with TrackingShotConfig, assemble_shot_with_tracking
- [ ] 07.4-04-PLAN.md - Extend shot.py with shadow catcher workflow, add composite_presets.yaml
- [ ] 07.4-05-PLAN.md - Update package exports, version bump to 0.3.5

**Acceptance Criteria**:
- [ ] Single YAML produces tracked composite shot
- [ ] Compositor nodes created automatically from tracking data
- [ ] Resume works after interruption
- [ ] Solved camera integrates with cinematic camera system
- [ ] Shadow catcher workflow functional

---

### Phase 7.5: Advanced Features (REQ-TRACK-OBJECT, REQ-TRACK-SCAN, REQ-TRACK-MOCAP, REQ-TRACK-BATCH)
**Priority**: P2 | **Est. Effort**: 12-16 days
**Plans:** 5 plans
**Planned:** 2026-02-19

**Dependencies:**
- Depends on: 7.0, 7.1, 7.2, 7.3
- Enables: Production tracking workflow (advanced)
- Critical Path: No
- Test Coverage: 80%

**Goal**: Implement object tracking, scan import, mocap, and batch processing.

**Deliverables**:
```
lib/cinematic/tracking/
├── object_tracker.py      # NEW: Planar, rigid body, knob/fader tracking
├── scan_import.py         # NEW: LiDAR/scan import with floor detection
├── mocap.py               # NEW: BVH/FBX import, hand extraction, retargeting

lib/cinematic/
└── batch.py               # NEW: Batch processing with resume
```

**Wave Structure**:
- **Wave 1**: batch.py (highest value, lowest complexity)
- **Wave 2**: object_tracker.py (planar tracking, knob rotation)
- **Wave 3**: scan_import.py (LiDAR with floor/scale detection)
- **Wave 4**: mocap.py (retargeting to MorphEngine)
- **Wave 5**: Package exports, version bump to 0.4.0

Plans:
- [ ] 07.5-01-PLAN.md - Create batch.py with BatchProcessor, checkpoint resume, report generation
- [ ] 07.5-02-PLAN.md - Create object_tracker.py with PlanarTracker, KnobTracker, RigidBodyTracker
- [ ] 07.5-03-PLAN.md - Create scan_import.py with PLY/OBJ parsers, FloorDetector, ScaleDetector
- [ ] 07.5-04-PLAN.md - Create mocap.py with MocapImporter, HandAnimation extraction, MocapRetargeter
- [ ] 07.5-05-PLAN.md - Update package exports, version bump to 0.4.0 (MILESTONE v0.6 COMPLETE)

**Key Integrations**:
- KnobTracker.rotation_to_morph() -> MorphEngine
- MocapRetargeter.retarget_to_morph() -> MorphEngine
- ScanImporter -> backdrop system
- BatchProcessor -> shot assembly

**Acceptance Criteria**:
- [ ] Planar tracking produces corner pin
- [ ] LiDAR scan imports at correct scale
- [ ] Mocap drives control surface animation
- [ ] Batch processes multiple shots in parallel

---

### Motion Tracking Summary

| Phase | Requirements | Priority | Est. Days | Plans | Beads |
|-------|-------------|----------|-----------|-------|-------|
| 7.0 | TRACK-01 | P1 | 2-3 | 5 | blender_gsd-42 |
| 7.1 | TRACK-POINT, TRACK-SOLVE | P0 | 9-11 | 4 | blender_gsd-43, blender_gsd-44 |
| 7.2 | TRACK-FOOTAGE, TRACK-CAMPROF | P1 | 5-7 | 4 | blender_gsd-45, blender_gsd-46 |
| 7.3 | TRACK-IMPORT | P1 | 3-4 | 3 | blender_gsd-47 |
| 7.4 | TRACK-COMPOSITE, TRACK-SHOT | P1 | 5-7 | 5 | blender_gsd-48, blender_gsd-49 |
| 7.5 | TRACK-OBJECT, TRACK-SCAN, TRACK-MOCAP, TRACK-BATCH | P2 | 12-16 | 5 | - |

**Total**: 36-48 days, 26 plans
**Epic**: `blender_gsd-41`
**Milestone Complete Version**: 0.4.0

**Supported External Tools**:
| Tool | Use Case | Export Format |
|------|----------|---------------|
| SynthEyes | Budget match move | FBX, Python |
| 3DEqualizer | Industry standard | FBX, Python |
| PFTrack | High-end tracking | FBX, Alembic |
| Nuke | Compositing + tracking | .chan, FBX |
| Move.ai | iPhone mocap | FBX, BVH |
| Polycam | iPhone LiDAR | OBJ, GLB, FBX |

---

## Milestone: v0.7 - Intelligent Follow Camera System
**Target**: TBD
**Requirements**: `.planning/REQUIREMENTS_FOLLOW_CAMERA.md`
**Beads Epic**: `blender_gsd-50`

### Phase 8.0: Follow Camera Foundation (REQ-FOLLOW-01)
**Priority**: P1 | **Est. Effort**: 2-3 days
**Beads**: `blender_gsd-51`

**Dependencies:**
- Depends on: 6.1, 6.5
- Enables: 8.1, 8.2, 8.3, 8.4
- Critical Path: No
- Test Coverage: 80%

**Goal**: Establish follow camera module structure, types, and configuration.

**Deliverables**:
```
lib/cinematic/follow_cam/
├── __init__.py
├── types.py                 # Follow camera data types
├── follow_modes.py          # Side-scroller, over-shoulder, chase
├── framing.py               # Intelligent composition
├── obstacle_avoidance.py    # Collision detection and avoidance
├── prediction.py            # Look-ahead and anticipation
├── solver.py                # Pre-solve system
└── constraints.py           # Camera constraint helpers

configs/cinematic/follow_cam/
├── follow_modes.yaml
├── framing_rules.yaml
├── avoidance_presets.yaml
└── prediction_settings.yaml
```

**Tasks**:
- [ ] Create `lib/cinematic/follow_cam/` module structure
- [ ] Implement FollowMode enum (8 modes)
- [ ] Define FollowTarget, ObstacleInfo, FollowCameraConfig types
- [ ] Create configuration directory structure
- [ ] Implement state persistence

---

### Phase 8.1: Follow Camera Modes (REQ-FOLLOW-MODE)
**Priority**: P0 | **Est. Effort**: 5-7 days
**Beads**: `blender_gsd-52`, `blender_gsd-53`, `blender_gsd-54`, `blender_gsd-55`, `blender_gsd-56`

**Dependencies:**
- Depends on: 8.0
- Enables: 8.2, 8.4
- Critical Path: No
- Test Coverage: 80%

**Goal**: Implement all 8 follow camera modes.

**Modes**:
1. **Side-Scroller** - Locked plane following (2.5D platformer view)
2. **Over-Shoulder** - Third-person behind subject
3. **Chase** - Following from behind with speed response
4. **Chase-Side** - Following from the side
5. **Orbit-Follow** - Orbiting while following movement
6. **Lead** - Camera leads subject, showing destination
7. **Aerial** - Top-down or high-angle following
8. **Free Roam** - Game-style free camera with collision

**Tasks**:
- [ ] Implement side-scroller mode with axis locking
- [ ] Implement over-shoulder mode with offset positioning
- [ ] Implement chase mode with speed-based distance
- [ ] Implement chase-side mode with side selection
- [ ] Implement orbit-follow mode with rotation
- [ ] Implement lead mode with look-ahead positioning
- [ ] Implement aerial mode with height/angle control
- [ ] Implement free roam mode with collision
- [ ] Implement mode transitions (cut, blend, orbit, dolly)
- [ ] Create presets for each mode

**Acceptance Criteria**:
- [ ] All 8 modes produce correct camera positioning
- [ ] Mode transitions smooth without jumps
- [ ] Presets available for common use cases

---

### Phase 8.2: Obstacle Avoidance (REQ-FOLLOW-AVOID, REQ-FOLLOW-PREDICT)
**Priority**: P0 | **Est. Effort**: 8-11 days
**Beads**: `blender_gsd-57`, `blender_gsd-58`, `blender_gsd-59`
**Unblocked by**: `blender_gsd-34` (Raycasting)
**Plans:** 3 plans

**Dependencies:**
- Depends on: 8.0, 8.1
- Enables: 8.3
- Critical Path: No
- Test Coverage: 80%

**Goal**: Implement intelligent obstacle detection, avoidance, and prediction.

**Wave Structure**:
- **Wave 1**: Configuration files (avoidance_presets.yaml, prediction_settings.yaml)
- **Wave 2**: Operator behavior implementation (human-like reactions, oscillation prevention)
- **Wave 3**: Unit tests and package exports

Plans:
- [ ] 08.2-01-PLAN.md - Create avoidance_presets.yaml and prediction_settings.yaml configuration files
- [ ] 08.2-02-PLAN.md - Add OperatorBehavior dataclass, OscillationPreventer class, and integrate with collision.py
- [ ] 08.2-03-PLAN.md - Create test_follow_cam_operator.py unit tests, update package exports

**Features**:

1. **Collision Detection** (REQ-FOLLOW-AVOID):
   - Raycast detection from camera to subject (3x3 grid)
   - Spherecast for wider detection radius
   - Frustum check for objects in view
   - Collision layer support
   - Ignore list (transparent, triggers, subject)

2. **Obstacle Response** (REQ-FOLLOW-AVOID):
   - Push forward (move camera closer to subject)
   - Orbit away (rotate around obstacle)
   - Raise up (move camera higher)
   - Zoom through (for transparent obstacles)
   - Camera backing response (wall behind camera)

3. **Camera Operator Behavior** (REQ-FOLLOW-AVOID):
   - Human-like reaction delay (0.1s default)
   - Angle preferences (horizontal: -45 to 45, vertical: 10 to 30)
   - Smooth, intentional movements
   - Natural breathing (subtle movement: 0.01m, 0.25Hz)
   - Decision weighting (visibility=1.0, composition=0.7, smoothness=0.5, distance=0.3)

4. **Motion Prediction** (REQ-FOLLOW-PREDICT):
   - Velocity-based trajectory prediction
   - Animation-based prediction (read keyframes ahead)
   - Look-ahead system (0.5s default, anticipate subject movement)
   - Speed anticipation (adjust for acceleration/deceleration)
   - Corner prediction (for vehicle following)

5. **Anti-Oscillation**:
   - Position history tracking
   - Direction change detection
   - Damping when oscillation detected
   - Minimum damping factor (never freeze camera)

**Deliverables**:
```
configs/cinematic/follow_cam/
├── avoidance_presets.yaml   # Collision, response, operator behavior presets
└── prediction_settings.yaml # Trajectory, look-ahead, corner prediction

lib/cinematic/follow_cam/
├── types.py               # Extended with OperatorBehavior dataclass
├── collision.py           # Extended with apply_operator_behavior, breathing, angle preference
└── prediction.py          # Extended with OscillationPreventer class

tests/unit/
└── test_follow_cam_operator.py  # Unit tests for operator behavior
```

**Acceptance Criteria**:
- [ ] Raycast collision detection works
- [ ] Camera pushes forward when wall behind
- [ ] Camera orbits around obstacles
- [ ] Prediction anticipates obstacles before contact
- [ ] No oscillation or jitter in avoidance
- [ ] Subject never fully occluded
- [ ] Camera has human-like reaction delay
- [ ] Camera prefers specific angle ranges
- [ ] Camera has subtle breathing movement

---

### Phase 8.3: Pre-Solve System (REQ-FOLLOW-SOLVE, REQ-FOLLOW-ENV)
**Priority**: P0 | **Est. Effort**: 7-9 days
**Beads**: `blender_gsd-60`, `blender_gsd-61`

**Goal**: Pre-compute complex camera moves for deterministic one-shot renders.

**Tasks**:

1. **Pre-Solve Workflow** (REQ-FOLLOW-SOLVE):
   - [ ] Scene analysis stage (subject path, obstacles)
   - [ ] Ideal path computation
   - [ ] Avoidance adjustment
   - [ ] Path smoothing
   - [ ] Keyframe baking

2. **One-Shot Configuration** (REQ-FOLLOW-SOLVE):
   - [ ] Mode changes at specific times
   - [ ] Framing changes at specific times
   - [ ] Transition types (cut, blend, orbit, dolly)
   - [ ] Preview video generation

3. **Environment Awareness** (REQ-FOLLOW-ENV):
   - [ ] Scene geometry analysis
   - [ ] Clearance map generation
   - [ ] Navigation mesh for camera
   - [ ] Volume constraints (allowed, forbidden, preferred)
   - [ ] Path planning with A* algorithm

**Acceptance Criteria**:
- [ ] Pre-solve produces deterministic camera path
- [ ] Baked camera renders identically every time
- [ ] One-shot handles multiple mode transitions
- [ ] Clearance map prevents camera from entering tight spaces

---

### Phase 8.4: Integration & Polish (REQ-FOLLOW-INTEGRATE, REQ-FOLLOW-FRAME, REQ-FOLLOW-DEBUG)
**Priority**: P1 | **Est. Effort**: 7-10 days
**Beads**: `blender_gsd-62`, `blender_gsd-63`

**Goal**: Integrate with cinematic system, add intelligent framing, and debug tools.

**Tasks**:

1. **Cinematic Integration** (REQ-FOLLOW-INTEGRATE):
   - [ ] Follow camera in shot YAML (`camera.type: follow`)
   - [ ] Pre-solve integration with render pipeline
   - [ ] Animation system blending modes
   - [ ] Batch rendering with pre-solved cameras

2. **Intelligent Framing** (REQ-FOLLOW-FRAME):
   - [ ] Rule of thirds positioning
   - [ ] Headroom and look room
   - [ ] Dead zone (center area for subtle movements)
   - [ ] Dynamic framing (speed-based, action-aware)
   - [ ] Multi-subject framing

3. **Debug & Visualization** (REQ-FOLLOW-DEBUG):
   - [ ] Camera frustum visualization
   - [ ] Target and prediction visualization
   - [ ] Obstacle detection rays
   - [ ] Path visualization (ideal vs actual)
   - [ ] HUD display (mode, distance, obstacles)
   - [ ] Frame-by-frame analysis output

**Acceptance Criteria**:
- [ ] Single YAML produces complete follow camera shot
- [ ] Framing maintains composition rules
- [ ] Debug overlays render in viewport
- [ ] Frame analysis available for troubleshooting

---

### Follow Camera Summary

| Phase | Requirements | Priority | Est. Days | Beads | Plans |
|-------|-------------|----------|-----------|-------|-------|
| 8.0 | FOLLOW-01 | P1 | 2-3 | blender_gsd-51 | - |
| 8.1 | FOLLOW-MODE | P0 | 5-7 | blender_gsd-52..56 | - |
| 8.2 | FOLLOW-AVOID, FOLLOW-PREDICT | P0 | 8-11 | blender_gsd-57..59 | 3 |
| 8.3 | FOLLOW-SOLVE, FOLLOW-ENV | P0 | 7-9 | blender_gsd-60, blender_gsd-61 | - |
| 8.4 | FOLLOW-INTEGRATE, FOLLOW-FRAME, FOLLOW-DEBUG | P1 | 7-10 | blender_gsd-62, blender_gsd-63 | - |

**Total**: 29-40 days
**Epic**: `blender_gsd-50`
**Unblocked by**: `blender_gsd-34` (Raycasting -> Collision Detection)

**Follow Modes**:
| Mode | Use Case |
|------|----------|
| Side-Scroller | 2.5D platformer, locked plane |
| Over-Shoulder | Third-person character |
| Chase | Vehicle following from behind |
| Chase-Side | Vehicle following from side |
| Orbit-Follow | Dynamic orbiting around subject |
| Lead | Camera ahead of subject |
| Aerial | Top-down/drone view |
| Free Roam | Game-style free camera |

**Key Features**:
- **Obstacle avoidance** - Camera "operator" that prevents blocking
- **Prediction** - Anticipates subject movement
- **Pre-solve** - Deterministic one-shot renders
- **Intelligent framing** - Rule of thirds, headroom, dead zones

---

## Milestone: v0.8 - Anamorphic / Forced Perspective System
**Target**: TBD
**Requirements**: `.planning/REQUIREMENTS_ANAMORPHIC.md`
**Beads Epic**: `blender_gsd-40`

### Phase 9.0: Projection Foundation (REQ-ANAM-01)
**Priority**: P1 | **Est. Effort**: 3-4 days
**Beads**: `blender_gsd-34`

**Dependencies:**
- Depends on: 6.1 (Camera System)
- Enables: 9.1, 9.2, 9.3
- Critical Path: Yes
- Test Coverage: 80%

**Goal**: Implement camera frustum raycasting to cast rays from camera through image pixels onto scene geometry.

**Tasks**:
- [ ] Create `lib/cinematic/projection/` module structure
- [ ] Implement frustum ray generation from camera FOV
- [ ] Implement ray-geometry intersection using Blender's BVH
- [ ] Return hit positions, normals, and UV coordinates
- [ ] Handle multiple surfaces in frustum

**Deliverables**:
```
lib/cinematic/projection/
├── __init__.py
├── types.py              # ProjectionResult, RayHit, FrustumConfig
├── raycast.py            # Frustum raycasting implementation
└── utils.py              # Ray-surface utilities
```

**Acceptance Criteria**:
- [ ] Cast rays from camera through image pixel grid
- [ ] Find intersections with scene geometry
- [ ] Return hit positions with <1cm accuracy
- [ ] Performance: 1000 rays in <100ms

---

### Phase 9.1: Surface Detection (REQ-ANAM-02)
**Priority**: P1 | **Est. Effort**: 2-3 days
**Beads**: `blender_gsd-35`

**Dependencies:**
- Depends on: 9.0 (Raycasting)
- Enables: 9.2
- Critical Path: No
- Test Coverage: 80%

**Goal**: Automatically detect and select surfaces for projection within camera frustum.

**Tasks**:
- [ ] Filter surfaces by type (floor, wall, ceiling, custom)
- [ ] Handle occlusion (don't project onto hidden surfaces)
- [ ] Support multi-surface projections (floor + wall = corner)
- [ ] Generate surface selection masks

**Acceptance Criteria**:
- [ ] Automatically finds floor surfaces in frustum
- [ ] Automatically finds wall surfaces in frustum
- [ ] Handles corners and complex geometry
- [ ] Occluded surfaces correctly excluded

---

### Phase 9.2: UV Generation & Texture Baking (REQ-ANAM-03)
**Priority**: P1 | **Est. Effort**: 3-4 days
**Beads**: `blender_gsd-36`, `blender_gsd-37`

**Dependencies:**
- Depends on: 9.0 (Raycasting), 9.1 (Surface Detection)
- Enables: 9.3
- Critical Path: No
- Test Coverage: 80%

**Goal**: Generate UV coordinates from projection and bake projected image onto geometry.

**Tasks**:
- [ ] Generate UV coordinates from projection rays
- [ ] Handle UV seams on complex geometry
- [ ] Bake to texture (diffuse, emission, decal modes)
- [ ] Support non-destructive workflow
- [ ] Export-friendly UV layout

**Acceptance Criteria**:
- [ ] UVs generated from projection rays
- [ ] No visible seams or distortion
- [ ] Non-destructive option preserves original materials
- [ ] Works with all export formats

---

### Phase 9.3: Camera Zones & Visibility (REQ-ANAM-04, REQ-ANAM-05)
**Priority**: P2 | **Est. Effort**: 3-4 days
**Beads**: `blender_gsd-38`, `blender_gsd-39`

**Dependencies:**
- Depends on: 9.2 (UV/Baking)
- Enables: Multi-viewpoint installations
- Critical Path: No
- Test Coverage: 80%

**Goal**: Define camera position zones ("sweet spots") and camera-triggered visibility.

**Tasks**:
- [ ] Define zone volumes (sphere, box, custom)
- [ ] Trigger visibility on camera enter/exit
- [ ] Smooth fade transitions at zone boundaries
- [ ] Works with animated cameras
- [ ] Multiple installations per scene

**Acceptance Criteria**:
- [ ] Projection visible only within defined zone
- [ ] Smooth fade in/out at zone boundaries
- [ ] Works with animated cameras
- [ ] Multiple anamorphic installations in one scene

---

### Phase 9.4: Advanced Features (REQ-ANAM-06, REQ-ANAM-07)
**Priority**: P2 | **Est. Effort**: 4-5 days

**Dependencies:**
- Depends on: 9.3
- Enables: Production-ready system
- Critical Path: No

**Goal**: Arbitrary geometry projection and real-time preview.

**Tasks**:
- [ ] Project onto curved surfaces
- [ ] Project onto 3D objects (furniture, characters)
- [ ] Handle UV seams on arbitrary geometry
- [ ] Viewport preview from projection camera
- [ ] Side-by-side comparison (sweet spot vs. other angles)

**Acceptance Criteria**:
- [ ] Works on curved walls
- [ ] Works on 3D objects
- [ ] Real-time preview in viewport

---

### Anamorphic System Summary

| Phase | Requirements | Priority | Est. Days | Beads |
|-------|-------------|----------|-----------|-------|
| 9.0 | ANAM-01 (Raycasting) | P1 | 3-4 | blender_gsd-34 |
| 9.1 | ANAM-02 (Surface Detection) | P1 | 2-3 | blender_gsd-35 |
| 9.2 | ANAM-03 (UV/Baking) | P1 | 3-4 | blender_gsd-36, blender_gsd-37 |
| 9.3 | ANAM-04, ANAM-05 (Zones/Visibility) | P2 | 3-4 | blender_gsd-38, blender_gsd-39 |
| 9.4 | ANAM-06, ANAM-07 (Advanced) | P2 | 4-5 | - |

**Total**: 15-20 days

**Capability IDs**: CAP-PROJ-01 through CAP-PROJ-06

---

## Future Considerations

### Not Yet Scheduled
- Blender 5.x compatibility
- Alternative DCC support (Houdini, Maya)
- Cloud render integration
- Real-time collaboration
- Physical simulation (springs, dampers)
- Audio-reactive visualization
