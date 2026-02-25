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
- [x] README with quickstart
- [x] Architecture documentation
- [x] Claude prompt pack
- [x] CI/CD setup

---

## Milestone: v0.2 - First Artifacts
**Target**: TBD

### Phase 5: Real Artifacts - COMPLETE
**Completed:** 2026-02-24

- [x] Panel artifact (full implementation)
  - PanelBuilder with PanelConfig, PanelStyle, MountingPattern
  - create_panel_node_group with dimensions, corner radius, style
  - create_panel_with_cutouts_node_group for boolean cutouts
  - MountingHoleConfig and CutoutConfig for precise control
- [x] Knob artifact
  - Already implemented in node_group_builder.py
  - create_knob_node_group with full parameter exposure
  - ZoneBuilder for zone-based geometry
  - KnurlConfig with V/U/Flat profiles
- [x] Enclosure artifact
  - EnclosureBuilder with EnclosureConfig, EnclosureType
  - create_enclosure_node_group with rack ears, rubber feet
  - RACK_UNIT_HEIGHT, RACK_WIDTH constants
  - create_rack_unit convenience function
- [x] Material system integration
  - Integrated with layout/renderer.py LayoutRenderer
  - Sanctus material loading support
  - Neve-style color palette for fallback

### Phase 6: Asset Integration - COMPLETE
**Completed:** 2026-02-24

- [x] Runtime asset search
  - AssetLibrary class with multi-path search
  - AssetMetadata for rich asset information
  - Fuzzy search by name, category, type, source
  - Asset caching to disk for fast subsequent scans
- [x] KitBash pack indexing
  - KitBashIndexer for KitBash3D pack structure
  - KitBashPack dataclass with pack metadata
  - Category detection from pack names
  - Pack caching system
- [x] Asset extraction from .blend files
  - AssetExtractor for linking/appending assets
  - append_collection, append_object, link_material
  - list_contents for blend file inspection
  - Support for both link (read-only) and append (editable) modes

---

## Milestone: v0.3 - Production Ready
**Target**: TBD

### Phase 7: Quality Assurance
- [x] Unit tests for all lib modules (4704 passing)
- [x] Integration tests for pipelines (27 tests)
- [x] CI pipeline (GitHub Actions)
- [x] Regression test suite (API stability tests)
- [ ] Integration tests requiring Blender (requires bpy)

### Phase 8: Ergonomics
- [x] Project template system
  - 6 templates: default, control-surface, cinematic, production, charlotte, minimal
  - Template registry with metadata and feature lists
- [x] `blender-gsd init` command
  - Creates project structure from templates
  - Supports --template, --no-git, --no-beads, --no-planning options
  - Auto-generates README, Makefile, .gitignore
- [x] VS Code integration
  - settings.json with Python, YAML, Makefile settings
  - extensions.json with recommended extensions
  - launch.json for debugging
- [x] Debug dashboard
  - Web-based real-time monitoring
  - Task execution tracking
  - Render job progress
  - System metrics (CPU, memory, disk)
  - Log viewer with error highlighting

---

## Milestone: v1.0 - Stable Release
**Target**: TBD

### Phase 9: Polish
- [x] Complete documentation
  - Updated README with CLI section
  - Updated test counts (4,610+ unit tests)
  - Updated codebase statistics
- [x] Example gallery
  - Basic examples: hello_nodekit, mask_basics, pipeline_stages
  - Control surfaces: neve_knob, ssl_fader, moog_button, style_morph
  - Cinematic: product_turntable, three_point_lighting, orbit_animation, shot_from_yaml
  - Charlotte: downtown_scene, road_network, building_extrusion
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

### Phase 5.10: Debug Material System (REQ-CTRL-DEBUG) - COMPLETE
**Goal:** Create a node-centric debug material workflow for per-section visualization with easy toggle between debug and production materials.
**Completed:** 2026-02-24

**Tasks:**
- [x] Create debug material utilities (create_debug_material, create_debug_palette)
- [x] Create Debug_Material_Switcher node group
- [x] Integrate debug materials into InputNodeGroupBuilder
- [x] Add exposed "Debug Mode" toggle input
- [x] Update render script for debug views

**Deliverables:**
- `lib/inputs/debug_materials.py` - Debug material creation utilities ✓
- `lib/inputs/node_groups/debug_switcher.py` - Material switcher node group ✓
- `lib/inputs/debug_render.py` - Debug render utilities ✓
- Per-section colors: A_Top (Red), A_Mid (Orange), A_Bot (Yellow), B_Top (Green), B_Mid (Blue), B_Bot (Purple) ✓
- Preset palettes: rainbow, grayscale, complementary, heat_map ✓

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

## Milestone: v0.6 - Motion Tracking System - COMPLETE
**Target**: 2026-02-19
**Requirements**: `.planning/REQUIREMENTS_TRACKING.md`
**Beads Epic**: `blender_gsd-41`
**Version**: 0.4.0
**Modules**: 8 | **Exports**: 70+ | **Lines**: ~5,100

### Phase 7.0: Tracking Foundation (REQ-TRACK-01)
**Priority**: P1 | **Est. Effort**: 2-3 days
**Beads**: `blender_gsd-42`
**Plans:** 5 plans
**Completed:** 2026-02-19

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
- [x] 07.0-01-PLAN.md - Create tracking types (TrackData, SolveData, FootageMetadata, TrackingSession, SolveReport)
- [x] 07.0-02-PLAN.md - Create config YAML files (tracking_presets, solver_settings, import_formats)
- [x] 07.0-03-PLAN.md - Create footage.py with ffprobe metadata extraction
- [x] 07.0-04-PLAN.md - Create import_export.py with coordinate conversion and Nuke .chan import
- [x] 07.0-05-PLAN.md - Update package exports and version bump to 0.3.1

---

### Phase 7.1: Core Tracking (REQ-TRACK-POINT, REQ-TRACK-SOLVE)
**Priority**: P0 | **Est. Effort**: 9-11 days
**Beads**: `blender_gsd-43`, `blender_gsd-44`
**Plans:** 4 plans
**Completed:** 2026-02-20

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
- [x] 07.1-01-PLAN.md - Create context.py with tracking_context manager; create presets.py with tracking preset loader; update tracking_presets.yaml
- [x] 07.1-02-PLAN.md - Create point_tracker.py with feature detection, KLT tracking, track management; create quality.py with track analysis
- [x] 07.1-03-PLAN.md - Create camera_solver.py with libmv integration, camera creation; update solver_settings.yaml
- [x] 07.1-04-PLAN.md - Update package exports and version bump to 0.3.2

**Acceptance Criteria**:
- [x] Auto-detect 50+ trackable features
- [x] Solve produces camera with <1px reprojection error
- [x] Camera animation keyframes created in Blender

---

### Phase 7.2: Footage & Camera Profiles (REQ-TRACK-FOOTAGE, REQ-TRACK-CAMPROF)
**Priority**: P1 | **Est. Effort**: 5-7 days
**Beads**: `blender_gsd-45`, `blender_gsd-46`
**Plans:** 4 plans
**Completed:** 2026-02-20

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
- [x] 07.2-01-PLAN.md - Extend footage.py with FFprobeMetadataExtractor, iPhone metadata, content analysis
- [x] 07.2-02-PLAN.md - Create rolling_shutter.py with detection and compensation
- [x] 07.2-03-PLAN.md - Create distortion.py (ST-Map), vanishing_points.py (focal length estimation)
- [x] 07.2-04-PLAN.md - Update camera_profiles.yaml with rolling shutter, package exports, version bump to 0.3.3

**Acceptance Criteria**:
- [x] FFprobeMetadataExtractor extracts iPhone QuickTime metadata
- [x] 30+ device profiles available with rolling shutter data
- [x] Rolling shutter compensation reduces skew
- [x] ST-Map generation produces UV coordinate maps
- [x] Vanishing point detection estimates focal length

---

### Phase 7.3: External Import/Export (REQ-TRACK-IMPORT)
**Priority**: P1 | **Est. Effort**: 3-4 days
**Beads**: `blender_gsd-47`
**Plans:** 3 plans
**Completed:** 2026-02-20

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
- [x] 07.3-01-PLAN.md - Add ColladaParser for .dae import via Blender native importer
- [x] 07.3-02-PLAN.md - Add C3DParser, TDEExportHelper, SynthEyesExportHelper, FBX export
- [x] 07.3-03-PLAN.md - Update package exports, version bump to 1.1.0

**Acceptance Criteria**:
- [x] Collada .dae import creates animated camera
- [x] C3D marker data imports correctly
- [x] 3DEqualizer/SynthEyes export scripts generate valid Python
- [x] FBX export creates valid camera file
- [x] Coordinate system conversion works (Y-up to Z-up)

---

### Phase 7.4: Compositing & Shot Integration (REQ-TRACK-COMPOSITE, REQ-TRACK-SHOT)
**Priority**: P1 | **Est. Effort**: 5-7 days
**Beads**: `blender_gsd-48`, `blender_gsd-49`
**Plans:** 5 plans
**Completed:** 2026-02-20

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
- [x] 07.4-01-PLAN.md - Create compositor.py with stabilization nodes, corner pin, alpha over, shadow composite
- [x] 07.4-02-PLAN.md - Create session.py with TrackingSessionManager, checkpoint, resume support
- [x] 07.4-03-PLAN.md - Create shot_integration.py with TrackingShotConfig, assemble_shot_with_tracking
- [x] 07.4-04-PLAN.md - Extend shot.py with shadow catcher workflow, add composite_presets.yaml
- [x] 07.4-05-PLAN.md - Update package exports, version bump to 0.3.5

**Acceptance Criteria**:
- [x] Single YAML produces tracked composite shot
- [x] Compositor nodes created automatically from tracking data
- [x] Resume works after interruption
- [x] Solved camera integrates with cinematic camera system
- [x] Shadow catcher workflow functional

---

### Phase 7.5: Advanced Features (REQ-TRACK-OBJECT, REQ-TRACK-SCAN, REQ-TRACK-MOCAP, REQ-TRACK-BATCH)
**Priority**: P2 | **Est. Effort**: 12-16 days
**Plans:** 5 plans
**Completed:** 2026-02-19

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
- [x] 07.5-01-PLAN.md - Create batch.py with BatchProcessor, checkpoint resume, report generation
- [x] 07.5-02-PLAN.md - Create object_tracker.py with PlanarTracker, KnobTracker, RigidBodyTracker
- [x] 07.5-03-PLAN.md - Create scan_import.py with PLY/OBJ parsers, FloorDetector, ScaleDetector
- [x] 07.5-04-PLAN.md - Create mocap.py with MocapImporter, HandAnimation extraction, MocapRetargeter
- [x] 07.5-05-PLAN.md - Update package exports, version bump to 0.4.0 (MILESTONE v0.6 COMPLETE)

**Key Integrations**:
- KnobTracker.rotation_to_morph() -> MorphEngine
- MocapRetargeter.retarget_to_morph() -> MorphEngine
- ScanImporter -> backdrop system
- BatchProcessor -> shot assembly

**Acceptance Criteria**:
- [x] Planar tracking produces corner pin
- [x] LiDAR scan imports at correct scale
- [x] Mocap drives control surface animation
- [x] Batch processes multiple shots in parallel

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

## Milestone: v0.7 - Intelligent Follow Camera System - COMPLETE
**Target**: 2026-02-19
**Requirements**: `.planning/REQUIREMENTS_FOLLOW_CAMERA.md`
**Beads Epic**: `blender_gsd-50`
**Version**: 0.5.0
**Modules**: 11 | **Exports**: 72+ | **Lines**: ~8,000

### Phase 8.0: Follow Camera Foundation (REQ-FOLLOW-01)
**Priority**: P1 | **Est. Effort**: 2-3 days
**Beads**: `blender_gsd-51`
**Plans:** 1 plan
**Completed:** 2026-02-19

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

Plans:
- [x] 08.0-01-PLAN.md - Create follow camera module structure, types, and configuration

---

### Phase 8.1: Follow Camera Modes (REQ-FOLLOW-MODE)
**Priority**: P0 | **Est. Effort**: 5-7 days
**Beads**: `blender_gsd-52`, `blender_gsd-53`, `blender_gsd-54`, `blender_gsd-55`, `blender_gsd-56`
**Plans:** 3 plans
**Completed:** 2026-02-19

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

**Wave Structure**:
- **Wave 1**: Type definitions and YAML presets
- **Wave 2**: All 8 mode implementations
- **Wave 3**: Transitions and unit tests

Plans:
- [x] 08.1-01-PLAN.md - Define Follow Camera Type System and YAML presets
- [x] 08.1-02-PLAN.md - Implement all 8 follow camera mode calculations
- [x] 08.1-03-PLAN.md - Implement mode transitions and unit tests

**Acceptance Criteria**:
- [x] All 8 modes produce correct camera positioning
- [x] Mode transitions smooth without jumps
- [x] Presets available for common use cases

---

### Phase 8.2: Obstacle Avoidance (REQ-FOLLOW-AVOID, REQ-FOLLOW-PREDICT)
**Priority**: P0 | **Est. Effort**: 8-11 days
**Beads**: `blender_gsd-57`, `blender_gsd-58`, `blender_gsd-59`
**Unblocked by**: `blender_gsd-34` (Raycasting)
**Plans:** 3 plans
**Completed:** 2026-02-19

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
- [x] 08.2-01-PLAN.md - Create avoidance_presets.yaml and prediction_settings.yaml configuration files
- [x] 08.2-02-PLAN.md - Add OperatorBehavior dataclass, OscillationPreventer class, and integrate with collision.py
- [x] 08.2-03-PLAN.md - Create test_follow_cam_operator.py unit tests, update package exports

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
- [x] Raycast collision detection works
- [x] Camera pushes forward when wall behind
- [x] Camera orbits around obstacles
- [x] Prediction anticipates obstacles before contact
- [x] No oscillation or jitter in avoidance
- [x] Subject never fully occluded
- [x] Camera has human-like reaction delay
- [x] Camera prefers specific angle ranges
- [x] Camera has subtle breathing movement

---

### Phase 8.3: Pre-Solve System (REQ-FOLLOW-SOLVE, REQ-FOLLOW-ENV)
**Priority**: P0 | **Est. Effort**: 7-9 days
**Beads**: `blender_gsd-60`, `blender_gsd-61`
**Completed:** 2026-02-19

**Goal**: Pre-compute complex camera moves for deterministic one-shot renders.

**Tasks**:

1. **Pre-Solve Workflow** (REQ-FOLLOW-SOLVE):
   - [x] Scene analysis stage (subject path, obstacles)
   - [x] Ideal path computation
   - [x] Avoidance adjustment
   - [x] Path smoothing
   - [x] Keyframe baking

2. **One-Shot Configuration** (REQ-FOLLOW-SOLVE):
   - [x] Mode changes at specific times
   - [x] Framing changes at specific times
   - [x] Transition types (cut, blend, orbit, dolly)
   - [x] Preview video generation

3. **Environment Awareness** (REQ-FOLLOW-ENV):
   - [x] Scene geometry analysis
   - [x] Clearance map generation
   - [x] Navigation mesh for camera
   - [x] Volume constraints (allowed, forbidden, preferred)
   - [x] Path planning with A* algorithm

**Acceptance Criteria**:
- [x] Pre-solve produces deterministic camera path
- [x] Baked camera renders identically every time
- [x] One-shot handles multiple mode transitions
- [x] Clearance map prevents camera from entering tight spaces

---

### Phase 8.4: Integration & Polish (REQ-FOLLOW-INTEGRATE, REQ-FOLLOW-FRAME, REQ-FOLLOW-DEBUG)
**Priority**: P1 | **Est. Effort**: 7-10 days
**Beads**: `blender_gsd-62`, `blender_gsd-63`
**Completed:** 2026-02-19

**Goal**: Integrate with cinematic system, add intelligent framing, and debug tools.

**Tasks**:

1. **Cinematic Integration** (REQ-FOLLOW-INTEGRATE):
   - [x] Follow camera in shot YAML (`camera.type: follow`)
   - [x] Pre-solve integration with render pipeline
   - [x] Animation system blending modes
   - [x] Batch rendering with pre-solved cameras

2. **Intelligent Framing** (REQ-FOLLOW-FRAME):
   - [x] Rule of thirds positioning
   - [x] Headroom and look room
   - [x] Dead zone (center area for subtle movements)
   - [x] Dynamic framing (speed-based, action-aware)
   - [x] Multi-subject framing

3. **Debug & Visualization** (REQ-FOLLOW-DEBUG):
   - [x] Camera frustum visualization
   - [x] Target and prediction visualization
   - [x] Obstacle detection rays
   - [x] Path visualization (ideal vs actual)
   - [x] HUD display (mode, distance, obstacles)
   - [x] Frame-by-frame analysis output

**Acceptance Criteria**:
- [x] Single YAML produces complete follow camera shot
- [x] Framing maintains composition rules
- [x] Debug overlays render in viewport
- [x] Frame analysis available for troubleshooting

---

### Follow Camera Summary

| Phase | Requirements | Priority | Est. Days | Beads | Plans |
|-------|-------------|----------|-----------|-------|-------|
| 8.0 | FOLLOW-01 | P1 | 2-3 | blender_gsd-51 | 1 |
| 8.1 | FOLLOW-MODE | P0 | 5-7 | blender_gsd-52..56 | 3 |
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

## Milestone: v0.8 - Anamorphic / Forced Perspective System - COMPLETE
**Target**: 2026-02-19
**Requirements**: `.planning/REQUIREMENTS_ANAMORPHIC.md`
**Beads Epic**: `blender_gsd-40`
**Version**: 0.6.0
**Modules**: 10 | **Exports**: 73+ | **Lines**: ~6,500

### Phase 9.0: Projection Foundation (REQ-ANAM-01)
**Priority**: P1 | **Est. Effort**: 3-4 days
**Beads**: `blender_gsd-34`
**Completed:** 2026-02-19

**Dependencies:**
- Depends on: 6.1 (Camera System)
- Enables: 9.1, 9.2, 9.3
- Critical Path: Yes
- Test Coverage: 80%

**Goal**: Implement camera frustum raycasting to cast rays from camera through image pixels onto scene geometry.

**Tasks**:
- [x] Create `lib/cinematic/projection/` module structure
- [x] Implement frustum ray generation from camera FOV
- [x] Implement ray-geometry intersection using Blender's BVH
- [x] Return hit positions, normals, and UV coordinates
- [x] Handle multiple surfaces in frustum

**Deliverables**:
```
lib/cinematic/projection/
├── __init__.py
├── types.py              # ProjectionResult, RayHit, FrustumConfig
├── raycast.py            # Frustum raycasting implementation
└── utils.py              # Ray-surface utilities
```

**Acceptance Criteria**:
- [x] Cast rays from camera through image pixel grid
- [x] Find intersections with scene geometry
- [x] Return hit positions with <1cm accuracy
- [x] Performance: 1000 rays in <100ms

---

### Phase 9.1: Surface Detection (REQ-ANAM-02)
**Priority**: P1 | **Est. Effort**: 2-3 days
**Beads**: `blender_gsd-35`
**Completed:** 2026-02-19

**Dependencies:**
- Depends on: 9.0 (Raycasting)
- Enables: 9.2
- Critical Path: No
- Test Coverage: 80%

**Goal**: Automatically detect and select surfaces for projection within camera frustum.

**Tasks**:
- [x] Filter surfaces by type (floor, wall, ceiling, custom)
- [x] Handle occlusion (don't project onto hidden surfaces)
- [x] Support multi-surface projections (floor + wall = corner)
- [x] Generate surface selection masks

**Acceptance Criteria**:
- [x] Automatically finds floor surfaces in frustum
- [x] Automatically finds wall surfaces in frustum
- [x] Handles corners and complex geometry
- [x] Occluded surfaces correctly excluded

---

### Phase 9.2: UV Generation & Texture Baking (REQ-ANAM-03)
**Priority**: P1 | **Est. Effort**: 3-4 days
**Beads**: `blender_gsd-36`, `blender_gsd-37`
**Completed:** 2026-02-19

**Dependencies:**
- Depends on: 9.0 (Raycasting), 9.1 (Surface Detection)
- Enables: 9.3
- Critical Path: No
- Test Coverage: 80%

**Goal**: Generate UV coordinates from projection and bake projected image onto geometry.

**Tasks**:
- [x] Generate UV coordinates from projection rays
- [x] Handle UV seams on complex geometry
- [x] Bake to texture (diffuse, emission, decal modes)
- [x] Support non-destructive workflow
- [x] Export-friendly UV layout

**Acceptance Criteria**:
- [x] UVs generated from projection rays
- [x] No visible seams or distortion
- [x] Non-destructive option preserves original materials
- [x] Works with all export formats

---

### Phase 9.3: Camera Zones & Visibility (REQ-ANAM-04, REQ-ANAM-05)
**Priority**: P2 | **Est. Effort**: 3-4 days
**Beads**: `blender_gsd-38`, `blender_gsd-39`
**Completed:** 2026-02-19

**Dependencies:**
- Depends on: 9.2 (UV/Baking)
- Enables: Multi-viewpoint installations
- Critical Path: No
- Test Coverage: 80%

**Goal**: Define camera position zones ("sweet spots") and camera-triggered visibility.

**Tasks**:
- [x] Define zone volumes (sphere, box, custom)
- [x] Trigger visibility on camera enter/exit
- [x] Smooth fade transitions at zone boundaries
- [x] Works with animated cameras
- [x] Multiple installations per scene

**Acceptance Criteria**:
- [x] Projection visible only within defined zone
- [x] Smooth fade in/out at zone boundaries
- [x] Works with animated cameras
- [x] Multiple anamorphic installations in one scene

---

### Phase 9.4: Advanced Features (REQ-ANAM-06, REQ-ANAM-07)
**Priority**: P2 | **Est. Effort**: 4-5 days
**Completed:** 2026-02-19

**Dependencies:**
- Depends on: 9.3
- Enables: Production-ready system
- Critical Path: No

**Goal**: Arbitrary geometry projection and real-time preview.

**Tasks**:
- [x] Project onto curved surfaces
- [x] Project onto 3D objects (furniture, characters)
- [x] Handle UV seams on arbitrary geometry
- [x] Viewport preview from projection camera
- [x] Side-by-side comparison (sweet spot vs. other angles)

**Acceptance Criteria**:
- [x] Works on curved walls
- [x] Works on 3D objects
- [x] Real-time preview in viewport

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

## Milestone: v0.9 - Production Tracking System
**Target**: TBD
**Requirements**: `.planning/REQUIREMENTS_PRODUCTION_TRACKING.md`

### Phase 11.0: Production Tracking Dashboard (REQ-TRACK-01, REQ-TRACK-03)
**Priority**: P1 | **Est. Effort**: 2-3 days
**Plans:** 1 plan

**Goal**: Build a simple TypeScript UI to VIEW all production elements with status, blockers, and source traceability.

**Key Features**:
- Kanban board with status columns (complete/in_progress/planned/vague/blocked)
- Item cards with category, name, description, images
- Filter by status and category
- Search by name/id
- Blocker panel always visible
- Link to source spec for each item
- All data in YAML files (no database)
- **Read-only by design** - AI handles writes

**Write Model**: The UI is read-only. To add/edit items, talk to Claude:
> "Add a new character CHAR-003 named 'Villain' with status planned"
> "Mark WARD-015 as complete"
> "Add blocker to PROP-003: waiting on concept approval"

The AI edits the YAML files directly. No backend needed.

**Philosophy**: If we need fancy UI tools, we're doing it wrong. Keep it simple, uniform, fluid.

**Tech Stack**:
- TypeScript + Vite
- YAML files for data
- No framework, minimal CSS
- No backend server

Plans:
- [x] 11.0-PLAN.md - Read-only tracking UI with board, filters, blocker panel

---

### Production Tracking Summary

| Phase | Requirements | Priority | Est. Days |
|-------|-------------|----------|-----------|
| 11.0 | TRACK-01, TRACK-03 | P1 | 2-3 |

**Total**: 2-3 days

**Asset Categories**:
| Category | Examples |
|----------|----------|
| character | Hero, NPC, creature |
| wardrobe | Costume pieces, accessories |
| prop | Hand props, set dressing |
| set | Environments, locations |
| shot | Camera shots, sequences |
| asset | Control surfaces, products |
| audio | Music, SFX, dialogue |

---

## Milestone: v0.10 - Asset 1-Sheet System
**Target**: TBD
**Requirements**: `.planning/REQUIREMENTS_PRODUCTION_TRACKING.md` (REQ-ONESHEET-01, REQ-ONESHEET-02)

### Phase 12.0: 1-Sheet Generator (REQ-ONESHEET-01)
**Priority**: P1 | **Est. Effort**: 2-3 days
**Depends on**: Phase 11.0

**Goal**: Generate presentable 1-sheets from tracked assets with images and descriptions.

**1-Sheet Structure**:
```
+----------------------------------+
|  [Hero Image - Main Product Shot]|
|                                  |
|  ASSET NAME                      |
|  Category: Character | Status: ✓ |
|                                  |
|  Description:                    |
|  Brief description of asset...   |
|                                  |
|  [Thumb 1] [Thumb 2] [Thumb 3]   |
|                                  |
|  Dependencies:                   |
|  → WARD-001 (Hero Costume)       |
|                                  |
|  Source: specs/characters/hero   |
|  Created: 2026-02-19 by bret     |
+----------------------------------+
```

**Output Formats**: HTML, PDF, PNG

**Key Features**:
- Auto-generate from asset data
- Template system for different categories
- Hero image + thumbnails
- Status and metadata
- Dependency chain
- Source traceability

Plans:
- [x] 12.0-PLAN.md - 1-sheet templates, export (HTML/PDF/PNG), preview modal

---

### Phase 12.1: Product Shot Integration (REQ-ONESHEET-02)
**Priority**: P2 | **Est. Effort**: 3-4 days
**Depends on**: Phase 12.0

**Goal**: Integrate with render pipeline to generate product shots for 1-sheets.

**Shot Types**:
| Shot Type | Purpose |
|-----------|---------|
| hero | Main hero shot, dramatic |
| beauty | Clean product shot on backdrop |
| detail | Close-up of details |
| context | In-context/environment shot |
| turntable | 360° rotation (animated) |

**Key Features**:
- Define shot templates per category
- Batch generate product shots
- Auto-attach to asset record
- Trigger from tracking board

---

### 1-Sheet System Summary

| Phase | Requirements | Priority | Est. Days |
|-------|-------------|----------|-----------|
| 12.0 | ONESHEET-01 | P1 | 2-3 |
| 12.1 | ONESHEET-02 | P2 | 3-4 |

**Total**: 5-7 days

---

## Milestone: v0.11 - Character & Object Animation System
**Target**: TBD
**Requirements**: `.planning/REQUIREMENTS_ANIMATION.md`

### Phase 13.0: Rigging Foundation (REQ-ANIM-01)
**Priority**: P0 | **Est. Effort**: 5-7 days

**Goal**: Create and manage skeletal hierarchies for any animatable entity.

**Entity Types**:
| Entity | Bone Structure | Notes |
|--------|---------------|-------|
| Human | Biped rig (60-100 bones) | Standard skeleton |
| Face | Face rig (50-100 bones) | Shape keys + bones |
| Quadruped | Quad rig (40-80 bones) | Dogs, horses, etc |
| Vehicle | Wheel/suspension rig | Mechanical articulation |
| Robot | Custom rig | Mechanical or organic |
| Prop | Simple rig | Doors, levers, etc |

**Key Features**:
- Rig template system (human_biped, face_standard, vehicle_basic, etc)
- Auto-rig from mesh (bone placement from geometry)
- Bone hierarchy management
- Weight painting automation
- Rig import/export (BVH, FBX)

---

### Phase 13.1: IK/FK System (REQ-ANIM-02, REQ-ANIM-03)
**Priority**: P0 | **Est. Effort**: 4-5 days

**Goal**: Animate limbs with inverse/forward kinematics.

**IK Types**:
| Type | Use Case |
|------|----------|
| Two-bone IK | Arms, legs |
| Chain IK | Spines, tails |
| Spline IK | Spines, tentacles |
| Floor IK | Keep feet on ground |

**Key Features**:
- Two-bone IK solver (standard limb)
- Pole targets (elbow/knee direction)
- IK/FK blending (seamless switching)
- Joint rotation limits

---

### Phase 13.2: Pose Library (REQ-ANIM-04)
**Priority**: P1 | **Est. Effort**: 3-4 days

**Goal**: Save, organize, and blend reusable poses.

**Pose Types**:
| Type | Examples |
|------|----------|
| Rest | T-pose, A-pose, standing |
| Action | Walk, run, jump, sit |
| Expression | Happy, sad, angry, neutral |
| Hand | Fist, point, grip, open |

**Key Features**:
- Pose capture from current rig state
- Pose library with categories
- Pose blending (mix multiple poses)
- Pose mirroring

---

### Phase 13.3: Blocking System (REQ-ANIM-05)
**Priority**: P1 | **Est. Effort**: 3-4 days

**Goal**: Rough animation pass to establish timing and key poses.

**Workflow**:
```
Storyboards → Key Poses (Blocking) → Breakdowns → Splining → Polish
```

**Key Features**:
- Stepped interpolation mode
- Key pose markers on timeline
- Pose thumbnails on timeline
- Copy/paste poses between frames
- Onion skinning (show adjacent poses)

---

### Phase 13.4: Face Animation (REQ-ANIM-06)
**Priority**: P1 | **Est. Effort**: 4-5 days

**Goal**: Animate facial expressions and lip sync.

**Face Rig Components**:
| Component | Bones/Controls |
|-----------|---------------|
| Eyes | Eye L/R, eyelids, eyebrows |
| Mouth | Jaw, lips, corners |
| Brows | Inner/outer brows |
| Cheeks | Cheek raise/squint |

**Key Features**:
- Face rig template
- Shape key system for expressions
- Viseme library (lip sync shapes)
- Expression presets
- Audio-driven lip sync

---

### Phase 13.5: Crowd System (REQ-ANIM-07)
**Priority**: P2 | **Est. Effort**: 2-3 days

**Goal**: Integrate crowd simulation plugins into GSD workflow.

**Approach**: Use existing plugins rather than building from scratch.

**Plugin Options**:
| Plugin | Best For |
|--------|----------|
| BlenderCrowd | Pedestrians, general crowds |
| CrowdSim3D | Large scale simulations |
| Boids (built-in) | Flocks, herds, swarms |

**Key Features**:
- Plugin integration layer
- Behavior state configuration
- Export to GSD pipeline
- Crowd asset tracking

---

### Phase 13.6: Vehicle Animation (REQ-ANIM-08)
**Priority**: P2 | **Est. Effort**: 2-3 days

**Goal**: Integrate vehicle animation plugins into GSD workflow.

**Approach**: Use existing plugins rather than building from scratch.

**Plugin Options**:
| Plugin | Best For |
|--------|----------|
| Vehicle Rigger | Cars, trucks |
| MCamTools | Vehicle camera rigs |
| Blender Physics | Basic vehicle motion |

**Key Features**:
- Plugin integration layer
- Vehicle rig templates
- Export to GSD pipeline
- Vehicle asset tracking

---

### Phase 13.7: Animation Layers (REQ-ANIM-09)
**Priority**: P2 | **Est. Effort**: 4-5 days

**Goal**: Non-destructive animation editing with multiple layers.

**Layer Types**:
| Layer | Purpose |
|-------|---------|
| Base | Foundation motion |
| Detail | Secondary motion added |
| Override | Replace specific bones |
| Additive | Add motion on top |

**Key Features**:
- Create/delete layers
- Layer opacity/mixing
- Layer masking
- Solo/mute layers
- Non-destructive editing

---

### Animation System Summary

| Phase | Requirements | Priority | Est. Days |
|-------|-------------|----------|-----------|
| 13.0 | ANIM-01 (Rigging) | P0 | 5-7 |
| 13.1 | ANIM-02, ANIM-03 (IK/FK) | P0 | 4-5 |
| 13.2 | ANIM-04 (Pose Library) | P1 | 3-4 |
| 13.3 | ANIM-05 (Blocking) | P1 | 3-4 |
| 13.4 | ANIM-06 (Face) | P1 | 4-5 |
| 13.5 | ANIM-07 (Crowds - Plugin Integration) | P2 | 2-3 |
| 13.6 | ANIM-08 (Vehicles - Plugin Integration) | P2 | 2-3 |
| 13.7 | ANIM-09 (Layers) | P2 | 4-5 |

**Total P0**: 9-12 days
**Total P1**: 10-13 days
**Total P2**: 8-11 days
**Grand Total**: 27-36 days

**Plugin Strategy**: Crowds and vehicles use existing Blender plugins (BlenderCrowd, Vehicle Rigger, etc.) with GSD integration layer.

---

## Milestone: v0.12 - Charlotte Digital Twin Core Geometry Pipeline - COMPLETE
**Target**: 2026-02-22
**Requirements**: `.planning/REQUIREMENTS_CHARLOTTE_GEOMETRY.md`
**Version**: 0.1.0
**Modules**: 13 | **Exports**: 54+ | **Lines**: ~4,500

### Phase 15.0: Geometry Foundation & Coordinate System (REQ-GEO-01)
**Priority**: P0 | **Est. Effort**: 1 day
**Plans:** 1 plan
**Completed:** 2026-02-21

**Dependencies:**
- Depends on: Charlotte Digital Twin data acquisition (existing)
- Enables: 15.1, 15.2, 15.3, 15.4
- Critical Path: Yes

**Goal**: Establish geometry module structure with coordinate transformation from WGS84 to Blender.

**Tasks**:
- [x] Create `lib/charlotte_digital_twin/geometry/` module structure
- [x] Implement WGS84 to UTM Zone 17N conversion for Charlotte
- [x] Implement local scene origin and scale factor (meters to Blender units)
- [x] Create coordinate transformer utilities

**Deliverables**:
```
lib/charlotte_digital_twin/geometry/
├── __init__.py
├── types.py              # GeometryConfig, SceneOrigin, CoordinateTransformer
├── coordinates.py        # WGS84 → UTM → Local conversion
└── scale.py              # Scene scale and unit management
```

**Acceptance Criteria**:
- [x] Convert lat/lon to Blender world coordinates
- [x] Configurable scene origin (default: Charlotte center)
- [x] 1 meter = 1 Blender unit scale

---

### Phase 15.1: Road Network Geometry (REQ-GEO-02)
**Priority**: P0 | **Est. Effort**: 2 days
**Plans:** 1 plan
**Completed:** 2026-02-21

**Dependencies:**
- Depends on: 15.0
- Enables: 15.2, 15.5
- Critical Path: Yes

**Goal**: Convert OSM road data to Blender curve/mesh geometry with proper materials.

**Tasks**:
- [x] Create RoadNetworkProcessor to build connected road graph
- [x] Convert OSM ways to Blender curves (poly/bezier)
- [x] Generate road mesh with proper width per highway type
- [x] Apply ground texture materials from lib/materials/ground_textures/
- [x] UV unwrap roads along path

**Deliverables**:
```
lib/charlotte_digital_twin/geometry/
├── road_processor.py     # Road network graph building
├── road_geometry.py      # Curve → mesh conversion
├── road_materials.py     # OSM tags → material selection
└── road_uv.py            # UV unwrapping utilities
```

**Acceptance Criteria**:
- [x] Download Charlotte OSM data → visible road network in Blender
- [x] Roads connect at intersections
- [x] Different materials for different road types (highway, residential, etc.)

---

### Phase 15.2: Building Geometry (REQ-GEO-03)
**Priority**: P1 | **Est. Effort**: 1 day
**Plans:** 1 plan
**Completed:** 2026-02-21

**Dependencies:**
- Depends on: 15.0, 15.1
- Enables: 15.5
- Critical Path: No

**Goal**: Extrude OSM building footprints to 3D geometry.

**Tasks**:
- [x] Parse OSM building footprint coordinates
- [x] Extrude footprints to proper height (from tags or estimation)
- [x] Apply building materials based on type
- [x] Support multi-building generation

**Deliverables**:
```
lib/charlotte_digital_twin/geometry/
├── building_processor.py  # Building footprint processing
├── building_geometry.py   # Extrusion and mesh creation
└── building_materials.py  # Material assignment
```

**Acceptance Criteria**:
- [x] Building footprints extrude to correct heights
- [x] Buildings placed at correct locations
- [x] Materials vary by building type

---

### Phase 15.3: POI Geometry (REQ-GEO-04)
**Priority**: P2 | **Est. Effort**: 1 day
**Plans:** 1 plan
**Completed:** 2026-02-21

**Dependencies:**
- Depends on: 15.0
- Enables: 15.5
- Critical Path: No

**Goal**: Place POI markers and placeholder geometry.

**Tasks**:
- [x] Create POIGeometryGenerator
- [x] Place marker objects at POI locations
- [x] Scale markers by importance score
- [x] Support custom POI models

**Deliverables**:
```
lib/charlotte_digital_twin/geometry/
├── poi_geometry.py       # POI placement and scaling
└── poi_models.py         # POI model definitions
```

**Acceptance Criteria**:
- [x] POI markers visible at correct locations
- [x] Importance scaling works
- [x] Custom models load correctly

---

### Phase 15.4: Scene Assembly (REQ-GEO-05)
**Priority**: P0 | **Est. Effort**: 1 day
**Plans:** 1 plan
**Completed:** 2026-02-21

**Dependencies:**
- Depends on: 15.0, 15.1, 15.2
- Enables: User workflows
- Critical Path: Yes

**Goal**: High-level API to assemble complete Charlotte scenes.

**Tasks**:
- [x] Create CharlotteSceneBuilder class
- [x] Support area selection (bbox, named areas)
- [x] Support detail level configuration
- [x] Generate complete scene from single call

**Deliverables**:
```
lib/charlotte_digital_twin/geometry/
├── scene_builder.py      # CharlotteSceneBuilder class
└── scene_presets.yaml    # Scene templates (downtown, highway, etc.)
```

**Acceptance Criteria**:
- [x] Single call generates complete scene
- [x] Scene templates work
- [x] Bounding box filtering works

---

### Charlotte Geometry Summary

| Phase | Requirements | Priority | Est. Days | Plans |
|-------|-------------|----------|-----------|-------|
| 15.0 | GEO-01 (Coordinates) | P0 | 1 | 1 |
| 15.1 | GEO-02 (Roads) | P0 | 2 | 1 |
| 15.2 | GEO-03 (Buildings) | P1 | 1 | 1 |
| 15.3 | GEO-04 (POIs) | P2 | 1 | 1 |
| 15.4 | GEO-05 (Assembly) | P0 | 1 | 1 |

**Total**: 6 days, 5 plans

**Key Features**:
- **Coordinate transformation** - WGS84 to Blender world
- **Road network** - Connected curves with materials
- **Building extrusion** - 3D from 2D footprints
- **POI placement** - Markers scaled by importance
- **Scene assembly** - One-call scene generation

---

## Milestone: v0.13 - SD Projection Mapping System
**Target**: 2026-02-24
**Version**: 0.1.0
**Modules**: 3 | **Exports**: 40+ | **Lines**: ~1,800

### Phase 16.0: SD Projection Foundation
**Priority**: P0 | **Completed:** 2026-02-24

**Goal**: Create the Arcane-style painted texture projection system with Stable Diffusion ControlNet.

**Key Features**:
- Camera-based projection mapping onto 3D geometry
- ControlNet conditioning (depth, normal, canny)
- Multi-style blending with LoRA support
- Drifting/slipping texture animation ("trippy" effect)
- Background building LOD support

**Architecture**:
```
lib/sd_projection/
├── __init__.py              # Package exports
├── sd_projection.py         # Core SD projection with ControlNet
├── style_blender.py         # Multi-style blending and drift animation
└── building_projection.py   # Building-specific projection with LOD
```

**Style Presets**:
| Preset | Description |
|--------|-------------|
| cyberpunk_night | Neon-lit cyberpunk with rain |
| arcane_painted | Arcane-style hand-painted look |
| trippy_drift | Psychedelic with heavy drift |
| noir_gritty | Film noir with rain streaks |
| anime_cel | Clean cel-shaded anime style |

**Drift Effects**:
| Pattern | Description |
|---------|-------------|
| LINEAR | Constant direction drift |
| RADIAL | Drift outward from center |
| SPIRAL | Spiral drift pattern |
| CHAOS | Chaotic/noise-based drift |
| WAVE | Wave-like undulation |

**Tasks**:
- [x] Create sd_projection.py with SDProjectionMapper, PassGenerator, SDClient
- [x] Create style_blender.py with StyleBlender, DriftConfig, StyleAnimator
- [x] Create building_projection.py with BuildingProjector, LOD support
- [x] Add style presets (cyberpunk, arcane, trippy, noir, anime)
- [x] Integrate depth/normal/canny pass generation
- [x] Add UV drift animation system

**Usage**:
```python
from lib.sd_projection import project_onto_buildings

results = project_onto_buildings(
    camera=scene.camera,
    buildings=city_buildings,
    style="cyberpunk_night",
    prompt="neon lit cyberpunk city, rain",
    drift_speed=0.1,
)
```

**Requirements**:
- SD WebUI running at http://127.0.0.1:7860 (or ComfyUI)
- ControlNet models installed
- Style LoRAs for preset styles

---

## Milestone: v0.14 - Vehicle Stunt System - COMPLETE
**Target**: 2026-02-24
**Requirements**: `.planning/REQUIREMENTS_VEHICLE_STUNTS.md`
**Version**: 0.1.0
**Modules**: 8 | **Exports**: 70+ | **Lines**: ~4,500

### Phase 17.0: Stunt Foundation (REQ-STUNT-01)
**Priority**: P0 | **Completed:** 2026-02-24

**Goal**: Establish vehicle stunt system foundation with physics-aware ramp generation.

**Tasks**:
- [x] Create lib/vehicle_stunts/ module structure
- [x] Implement RampConfig, LoopConfig, TrajectoryPoint data types
- [x] Create physics constants and utilities

**Deliverables**:
- `lib/vehicle_stunts/__init__.py` - Package exports
- `lib/vehicle_stunts/types.py` - Core data structures

---

### Phase 17.1: Ramp & Jump Generation (REQ-STUNT-02)
**Priority**: P0 | **Completed:** 2026-02-24

**Goal**: Generate physics-accurate ramps, jumps, and launch surfaces.

**Tasks**:
- [x] Implement 12 ramp presets (beginner to pro)
- [x] Create ramp geometry generator
- [x] Implement trajectory calculation with drag
- [x] Add landing zone generation

**Deliverables**:
- `lib/vehicle_stunts/ramps.py` - Ramp creation and presets
- `lib/vehicle_stunts/jumps.py` - Trajectory calculations

---

### Phase 17.2: Building Interaction (REQ-STUNT-03)
**Priority**: P1 | **Completed:** 2026-02-24

**Goal**: Enable vehicles to interact with buildings for urban stunts.

**Tasks**:
- [x] Implement wall-ride detection and configuration
- [x] Create corner bank generation
- [x] Add rooftop landing zone detection

**Deliverables**:
- `lib/vehicle_stunts/building_interaction.py` - Wall rides, corner banks

---

### Phase 17.3: Loop & Curve Generation (REQ-STUNT-04)
**Priority**: P1 | **Completed:** 2026-02-24

**Goal**: Generate vertical loops and banked curves for vehicles.

**Tasks**:
- [x] Implement 4 loop types (circular, clothoid, egg, helix)
- [x] Create banked turn generator
- [x] Add half-pipe, wave, barrel roll elements

**Deliverables**:
- `lib/vehicle_stunts/loops.py` - Loop and curve generation

---

### Phase 17.4: Launch Control & Physics (REQ-STUNT-05)
**Priority**: P0 | **Completed:** 2026-02-24

**Goal**: Calculate and visualize launch parameters for successful stunts.

**Tasks**:
- [x] Implement launch velocity calculator
- [x] Create G-force calculations
- [x] Add speed requirement system
- [x] Implement launch angle optimizer

**Deliverables**:
- `lib/vehicle_stunts/physics.py` - Physics calculations
- `lib/vehicle_stunts/launch_control.py` - Launch optimization

---

### Phase 17.5: Stunt Course Assembly (REQ-STUNT-06)
**Priority**: P2 | **Completed:** 2026-02-24

**Goal**: Assemble complete stunt courses from individual elements.

**Tasks**:
- [x] Implement StuntCourseBuilder
- [x] Create course flow analyzer
- [x] Add course validation
- [x] Create 4 course presets (beginner, intermediate, pro, extreme)

**Deliverables**:
- `lib/vehicle_stunts/course.py` - Course builder and validation

---

### Vehicle Stunt System Summary

| Phase | Requirements | Priority | Status |
|-------|-------------|----------|--------|
| 17.0 | STUNT-01 (Foundation) | P0 | ✅ Complete |
| 17.1 | STUNT-02 (Ramps) | P0 | ✅ Complete |
| 17.2 | STUNT-03 (Buildings) | P1 | ✅ Complete |
| 17.3 | STUNT-04 (Loops) | P1 | ✅ Complete |
| 17.4 | STUNT-05 (Launch Control) | P0 | ✅ Complete |
| 17.5 | STUNT-06 (Course Assembly) | P2 | ✅ Complete |

**Total**: 8 modules, 70+ exports, ~4,500 lines

**Use Cases**:
- Urban stunt driving (parkour with cars)
- Rooftop racing
- Stunt film choreography
- Game level design
- Action sequence previsualization

---

## Future Considerations

### Not Yet Scheduled
- Blender 5.x compatibility
- Alternative DCC support (Houdini, Maya)
- Cloud render integration
- Real-time collaboration
- Physical simulation (springs, dampers)
- Audio-reactive visualization
- Real elevation data (OpenTopography API)
- Traffic flow visualization
- Weather effects
