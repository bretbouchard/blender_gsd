# Project State

## Current Position

**Phase:** Council Review Complete
**Status:** CONDITIONAL APPROVE - 5 specialists reviewed, 15 issues identified (1 critical, 5 high)
**Last activity:** 2026-02-22 - Council of Ricks comprehensive review

**Progress:** [██████████] 100% (Core Infrastructure Complete)

**Version:** 0.2.0

---

## Council Review Results (2026-02-22)

**Verdict**: ⚠️ CONDITIONAL APPROVE

### Specialist Summary:

| Specialist | Status | Key Findings |
|------------|--------|--------------|
| geometry-rick | ✅ APPROVE | Geometry nodes solid, LOD system complete |
| render-rick | ⚠️ CONDITIONAL | Camera good, render profiles missing |
| compositor-rick | ❌ REJECT (Expected) | Phase 12.1 planned, not yet executed |
| pipeline-rick | ⚠️ CONDITIONAL | Core sound, documentation gaps |
| asset-rick | ✅ APPROVE | Asset management well-structured |

### Required Actions:

**P0 (Blocking):**
1. Create render profiles system (`lib/render/profiles.py`)
2. Add Cycles X and EEVEE Next configurations

**P1 (Important):**
1. Add exports to `lib/orchestrator/__init__.py`
2. Add light linking for Blender 5.x
3. Add HDRI lighting system
4. Add `framestamp` to `CameraTarget`

**P2 (Future - Phase 12.1):**
1. Execute compositing phase
2. Create color management system
3. Implement multi-pass EXR rendering

---

**Note:** Phase 14.2 adds MasterProductionConfig schema with template expansion, comprehensive validation, and CLI tools for one-shot movie generation.
**Phase 13.4:** CRT display effects (scanlines, phosphor, curvature, bloom, aberration) with 18 presets.
**Phase 13.3:** Isometric/side-scroller cameras, sprite sheet generation (4 formats), tile system with autotile.
**Phase 13.2:** Dither Engine with 15+ modes (Bayer, error diffusion, patterns), 50+ presets.
**Phase 13.1:** Pixel Converter with 8 style modes, 3 quantization algorithms, 20+ console presets.
**Phase 13.0:** Rigging Foundation with 5 rig presets, bone utilities, weight painting.
**Phase 12.1:** Compositor with blend modes, color correction, cryptomatte.
**Phase 12.0:** 1-Sheet Generator with HTML/PDF export.

## Phase 13.7 Planning Summary

### 13.7-animation-layers (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 13.7-01 | Animation Layers | Complete | 13.7-01-SUMMARY.md |

**Delivered:**
- layer_system.py - Core layer management (create, delete, opacity, mute, solo, keyframes)
- layer_blend.py - Layer blending with 4 modes (BASE, OVERRIDE, ADDITIVE, MIX)
- layer_mask.py - Bone masking with patterns, sides, presets
- layer_presets.yaml - 8 layer preset configurations
- 56 layer unit tests

## Phase 14.2 Planning Summary

### 14.2-master-config (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 14.2-01 | Master Production Config | Complete | 14.2-01-SUMMARY.md |

**Delivered:**
- config_schema.py - MasterProductionConfig, CharacterDef, LocationDef, ShotDef, OutputDef, RetroOutputConfig
- template_expansion.py - 16 shot templates, 8 style presets, expand_shot_templates
- config_validation.py - validate_master_config, check_file_references, validate_for_execution_strict
- cli.py - 4 new commands (show, check, list-templates, suggest)
- 3 example productions (the_discovery, product_demo, retro_game)
- 48 unit tests

## Phase 14.1 Planning Summary

### 14.1-production-orchestrator (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 14.1-01 | Production Orchestrator | Complete | 14.1-01-SUMMARY.md |

**Delivered:**
- production_types.py - ProductionConfig, CharacterConfig, LocationConfig, ShotConfig, 6 enums
- production_loader.py - YAML loading, templates, time estimation
- production_validator.py - Validation with helpful error messages
- execution_engine.py - 8-phase execution orchestrator with checkpointing
- parallel_executor.py - Dependency analysis, parallel execution
- cli.py - Click-based CLI (run, validate, info, estimate, list, create)
- 3 templates (short_film, commercial, game_assets)
- 1 example configuration
- 44 unit tests

## Phase 13.4 Planning Summary

### 13.4-crt-effects (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 13.4-01 | CRT Display Effects | Complete | 13.4-01-SUMMARY.md |

**Delivered:**
- crt_types.py - CRTConfig, ScanlineConfig, PhosphorConfig, CurvatureConfig, 3 enums, 12 presets
- scanlines.py - Scanline patterns (alternate, every-line, random), overlays, GPU shaders
- phosphor.py - Phosphor masks (RGB stripe, aperture grille, slot mask, shadow mask)
- curvature.py - Barrel distortion, vignette, corner rounding, bilinear sampling
- crt_effects.py - Bloom, aberration, flicker, interlace, jitter, noise, ghosting, color adjustments
- crt_compositor.py - Blender compositor node integration
- crt_preset_loader.py - YAML preset loading with caching
- crt_presets.yaml - 18 presets (arcade, TV, professional, LCD, special)
- 254 unit tests

## Phase 13.3 Planning Summary

### 13.3-isometric-side-scroller (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 13.3-01 | Isometric & Side-Scroller | Complete | 13.3-01-SUMMARY.md |

**Delivered:**
- isometric_types.py - IsometricConfig, SideScrollerConfig, SpriteSheetConfig, TileConfig, 4 enums
- isometric.py - Isometric camera, projection math, depth sorting, grid, rendering
- side_scroller.py - Side-scroller camera, parallax layers, animation, depth assignment
- sprites.py - Sprite sheet generation, trimming, metadata, 4 format exporters
- tiles.py - Tile sets, tile maps, autotile, collision maps, transforms
- view_preset_loader.py - YAML preset loader with caching
- view_presets.yaml - 35 presets (9 isometric, 8 side-scroller, 10 sprite, 8 tile)
- 234 unit tests

## Phase 13.1 Planning Summary

### 13.1-pixel-converter (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 13.1-01 | Pixel Converter | Complete | 13.1-01-SUMMARY.md |

**Delivered:**
- pixel_types.py - PixelStyle, PixelationConfig, PixelationResult, ColorPalette, 6 enums
- pixelator.py - Main pixelation engine with 8 mode functions
- quantizer.py - Median cut, K-means, Octree quantization algorithms
- preset_loader.py - YAML profile loading with 20+ presets
- pixel_compositor.py - Blender compositor integration
- pixel_profiles.yaml - Console presets, palettes, resolutions
- 6 built-in palettes (Game Boy, NES, PICO-8, CGA, EGA, Mac Plus)
- 150 unit tests

## Phase 10.1 Planning Summary

### 10.1-wardrobe-system (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 10.1-01 | Wardrobe System | Complete | 10.1-01-SUMMARY.md |

**Delivered:**
- wardrobe_types.py - CostumePiece, Costume, CostumeChange, CostumeAssignment, WardrobeRegistry, 6 enums
- costume_manager.py - CostumeManager with CRUD, assignments, change detection, queries
- continuity_validator.py - validate_continuity, condition progression, report generation
- costume_bible.py - generate_costume_bible, shopping list, HTML/PDF/YAML export
- yaml_storage.py - load/save wardrobe YAML, directory loading
- schema.yaml, examples/, templates/ - YAML configurations
- 113 unit tests

## Phase 9.1 Planning Summary

### 9.1-set-builder (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 9.1-01 | Set Builder | Complete | 9.1-01-SUMMARY.md |

**Delivered:**
- set_types.py - WallConfig, DoorConfig, WindowConfig, RoomConfig, PropConfig, SetConfig, 8 enums
- room_builder.py - create_room, create_floor, create_ceiling, create_wall, add_wall_opening, create_molding
- openings.py - 8 door styles, 4+ window styles, frames, handles, curtains, blinds
- props.py - 40+ built-in props, prop library loading, dressing styles, auto-population
- set_presets.yaml - 12 style presets (modern, victorian, scifi, cyberpunk, etc.)
- furniture.yaml, decor.yaml, electronics.yaml - Prop definitions
- set_materials.yaml - Material definitions for wood, metal, fabric, glass, ceramic
- 66 unit tests

## Phase 8.2 Planning Summary

### 8.2-shot-list-generator (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 8.2-01 | Shot List Generator | Complete | 8.2-01-SUMMARY.md |

**Delivered:**
- shot_gen_types.py - ShotSuggestion, CoverageEstimate, SceneShotList, ShotList, StoryboardPrompt
- scene_analyzer.py - Scene analysis with dialogue/action/mixed detection
- shot_rules.py - Coverage rules engine with shot size and camera angle suggestions
- storyboard_prompts.py - AI image prompt generation with style presets
- shot_list_export.py - CSV, YAML, JSON, HTML, PDF export
- 39 unit tests

## Phase 8.1 Planning Summary

### 8.1-script-parser (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 8.1-01 | Script Parser | Complete | 8.1-01-SUMMARY.md |

**Delivered:**
- script_types.py - Script, Scene, Character, Location, ActionBlock, DialogueLine, Transition, Beat, BeatSheet, ScriptAnalysis
- fountain_parser.py - Fountain format parsing with title page, scenes, dialogue, transitions
- fdx_parser.py - Final Draft XML parsing
- beat_generator.py - Save the Cat, Three-Act, Story Circle, Hero's Journey, Sequel Method structures
- script_analysis.py - Comprehensive analysis with recommendations, character network, location schedule
- beat_structures.yaml - Configuration for 5 beat structure templates
- 58 unit tests

## Phase 7.1 Planning Summary

### 7.1-object-tracking (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 7.1-01 | Object Tracking | Complete | 7.1-01-SUMMARY.md |

**Delivered:**
- tracking_types.py - TrackingMarker, TrackingData, TrackingConfig, FollowFocusRig, TrackingExportResult
- tracking_solver.py - Position solving, velocity/acceleration, interpolation, prediction, smoothing
- follow_focus.py - Distance calculation, rig creation, focus animation
- tracking_export.py - JSON, After Effects (JSX), Nuke (.chan), Blender empties export
- 38 unit tests

## Phase 6.4 Planning Summary

### 6.4-lighting-system (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 6.4-01 | Lighting System | Complete | 6.4-01-SUMMARY.md |

**Delivered:**
- light_rigs.py - Three-point soft/hard, product hero, studio high-key/low-key, positioning utilities
- light_linking.py - Blender 4.0+ light linking with include/exclude modes
- test_lighting.py - 32 tests for light creation and management
- test_gel.py - 26 tests for gel/color filter system
- test_hdri.py - 28 tests for HDRI environment lighting
- test_light_rigs.py - 34 tests for lighting rig presets
- test_light_linking.py - 23 tests for light linking functionality
- 143 unit tests total

## Phase 6.3 Planning Summary

### 6.2-motion-tracking (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 6.2-01 | Motion Tracking System | Complete | 6.2-01-SUMMARY.md |

**Delivered:**
- tracking_types.py - TrackingMarker, TrackingData, TrackingConfig, FollowFocusRig
- tracking_solver.py - Position solving, velocity/acceleration calculation, prediction, smoothing
- follow_focus.py - Focus distance calculation, rig creation, animation
- tracking_export.py - JSON, After Effects, Nuke, Blender export
- object_tracking_presets.yaml - 8 tracking presets
- 38 unit tests

## Phase 6.3 Planning Summary

### 6.3-follow-camera (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 6.3-01 | Follow Camera System | Complete | 6.3-01-SUMMARY.md |

**Delivered:**
- follow_types.py - FollowConfig, FollowState, FollowRig, DeadZoneResult, FollowResult
- follow_modes.py - 5 follow modes (tight, loose, anticipatory, elastic, orbit)
- follow_deadzone.py - Screen position, dead zone detection, dynamic dead zones
- follow_controller.py - Rig creation, updates, baking, preview
- follow_presets.yaml - 12 preset configurations
- 37 unit tests

## Phase 7.5 Planning Summary

### 07.5-advanced-features (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 07.5-01 | Batch Processing | Complete | 07.5-01-SUMMARY.md |
| 07.5-02 | Object Tracker | Complete | 07.5-02-SUMMARY.md |
| 07.5-03 | Scan Import | Complete | 07.5-03-SUMMARY.md |
| 07.5-04 | Mocap Import | Complete | 07.5-04-SUMMARY.md |
| 07.5-05 | Package Exports + Version Bump | Complete | 07.5-05-SUMMARY.md |

**Wave Structure:**
1. Wave 1: batch.py (highest value, lowest complexity)
2. Wave 2: object_tracker.py (planar tracking, knob rotation)
3. Wave 3: scan_import.py (LiDAR with floor/scale detection)
4. Wave 4: mocap.py (retargeting to MorphEngine)
5. Wave 5: Package exports, version bump to 0.4.0

**Key Integrations:**
- KnobTracker.rotation_to_morph() → MorphEngine
- MocapRetargeter.retarget_to_morph() → MorphEngine
- ScanImporter → backdrop system
- BatchProcessor → shot assembly

## Phase 8.0 Planning Summary

### 08.0-foundation (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 08.0-01 | Follow Camera Foundation | Complete | 08.0-01-SUMMARY.md |

**Follow Camera Module Structure:**
- 10 Python modules in lib/cinematic/follow_cam/
- 8 follow modes: side_scroller, over_shoulder, chase, chase_side, orbit_follow, lead, aerial, free_roam
- 18 presets in follow_modes.yaml
- State directories for solves and previews

**Key Files:**
- types.py (473 lines) - FollowMode enum, FollowCameraConfig, CameraState
- follow_modes.py - Mode implementations
- transitions.py - Mode transitions
- collision.py - Collision detection
- prediction.py - Motion prediction
- framing.py - Intelligent framing
- pre_solve.py - Pre-solve workflow
- navmesh.py - Navigation mesh
- debug.py - Debug visualization

## Phase Summary

### 07.0-tracking-foundation (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 07.0-01 | Tracking Foundation Types | Complete | 07.0-01-SUMMARY.md |
| 07.0-02 | Session Management | Complete | 07.0-02-SUMMARY.md |
| 07.0-03 | Footage Analysis | Complete | 07.0-03-SUMMARY.md |
| 07.0-04 | Import/Export | Complete | 07.0-04-SUMMARY.md |
| 07.0-05 | Package Exports | Complete | 07.0-05-SUMMARY.md |

### 06.10-integration-testing (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06.10-01 | Integration Testing Types | Complete | 06.10-01-SUMMARY.md |
| 06.10-02 | Testing + Benchmark Modules | Complete* | 06.10-03-SUMMARY.md (combined with 03) |
| 06.10-03 | Package Exports + Version Bump | Complete | 06.10-03-SUMMARY.md |

*Plan 06.10-02 was implemented inline with 06.10-03 as a blocking issue fix.

### 06-foundation-cinematic (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06-01 | Cinematic Foundation | Complete | 06-01-SUMMARY.md |
| 06-02 | Camera Presets | Complete | 06-02-SUMMARY.md |
| 06-03 | State Directory Structure | Complete | 06-03-SUMMARY.md |

### 06.1-camera-system (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06.1-01 | Types + Preset Loader | Complete | 06.1-01-SUMMARY.md |
| 06.1-02 | Camera Builder | Complete | 06.1-02-SUMMARY.md |
| 06.1-03 | Plumb Bob Targeting | Complete | 06.1-03-SUMMARY.md |
| 06.1-04 | Lens System | Complete | 06.1-04-SUMMARY.md |
| 06.1-05 | Camera Rigs + Multi-Camera | Complete | 06.1-05-SUMMARY.md |

### 06.2-lighting-system (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06.2-01 | Types + Preset Loaders | Complete | 06.2-01-SUMMARY.md |
| 06.2-02 | Core Lighting Module | Complete | 06.2-02-SUMMARY.md |
| 06.2-03 | Gel/Color Filter System | Complete | 06.2-03-SUMMARY.md |
| 06.2-04 | HDRI Environment Lighting | Complete | 06.2-04-SUMMARY.md |
| 06.2-05 | Package Exports + Version Bump | Complete | 06.2-05-SUMMARY.md |

### 06.3-backdrop-system (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06.3-01 | Types + Preset Loaders | Complete | 06.3-01-SUMMARY.md |
| 06.3-02 | Backdrop Module | Complete | 06.3-02-SUMMARY.md |
| 06.3-03 | Package Exports + Version Bump | Complete | 06.3-03-SUMMARY.md |

### 06.4-color-pipeline (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06.4-01 | Types + Preset Loaders | Complete | 06.4-01-SUMMARY.md |
| 06.4-02 | Color Management Module | Complete | 06.4-02-SUMMARY.md |
| 06.4-03 | Package Exports + Version Bump | Complete | 06.4-03-SUMMARY.md |

### 06.5-animation-system (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06.5-01 | Animation Types + Preset Loaders | Complete | 06.5-01-SUMMARY.md |
| 06.5-02 | Animation Module | Complete | 06.5-02-SUMMARY.md |
| 06.5-03 | Package Exports + Version Bump | Complete | 06.5-03-SUMMARY.md |

### 06.6-render-system (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06.6-01 | Render Types + Preset Loaders | Complete | 06.6-01-SUMMARY.md |
| 06.6-02 | Render Module | Complete* | 06.6-03-SUMMARY.md (combined with 03) |
| 06.6-03 | Package Exports + Version Bump | Complete | 06.6-03-SUMMARY.md |

*Plan 06.6-02 was implemented inline with 06.6-03 as a blocking issue fix.

### 06.7-support-systems (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06.7-01 | Types + Preset Loaders | Complete | 06.7-01-SUMMARY.md |
| 06.7-02 | Support Modules | Complete | 06.7-02-SUMMARY.md |
| 06.7-03 | Package Exports + Version Bump | Complete | 06.7-03-SUMMARY.md |

### 06.8-shot-assembly (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06.8-01 | Shot Template Types + Loaders | Complete | 06.8-01-SUMMARY.md |
| 06.8-02 | Shot Assembly Module | Complete* | 06.8-03-SUMMARY.md (combined with 03) |
| 06.8-03 | Shot Template Presets + Exports | Complete | 06.8-03-SUMMARY.md |

*Plan 06.8-02 was implemented inline with 06.8-03 as a blocking issue fix.

### 06.9-camera-matching (Complete)

| Plan | Name | Status | Summary |
|------|------|--------|---------|
| 06.9-01 | Camera Matching Types + Loaders | Complete | 06.9-01-SUMMARY.md |
| 06.9-02 | Camera Matching + Audio Sync Modules | Complete* | 06.9-03-SUMMARY.md (combined with 03) |
| 06.9-03 | Camera Profiles + Exports | Complete | 06.9-03-SUMMARY.md |

*Plan 06.9-02 was implemented inline with 06.9-03 as a blocking issue fix.

## Cinematic System Module Summary

**lib/cinematic/** (30 modules, ~24,000 lines):
- types.py (2220 lines) - Core dataclasses (CinematicRenderSettings, camera matching, audio sync, test configs)
- enums.py (163 lines) - Type-safe enumerations (RenderEngine, DenoiserType, CompositionGuideType)
- state_manager.py (458 lines) - State persistence
- preset_loader.py (1238 lines) - Preset loading utilities (render + support + shot template + camera profile loaders)
- camera.py (375 lines) - Camera creation and management
- camera_match.py (399 lines) - Camera matching from reference and tracking import
- audio_sync.py (300 lines) - Audio sync and beat marker support
- plumb_bob.py (348 lines) - Orbit/focus targeting
- lenses.py (320 lines) - Compositor imperfections
- rigs.py (641 lines) - Camera rigs and multi-camera composite
- lighting.py (806 lines) - Light creation and management
- gel.py (313 lines) - Gel/color filter system
- hdri.py (401 lines) - HDRI environment lighting
- backdrops.py (770 lines) - Backdrop creation and management
- color.py (793 lines) - Color management, LUT validation, exposure lock
- animation.py (1203 lines) - Camera animation functions, easing, turntable
- motion_path.py (692 lines) - Procedural motion path generation
- shot_builder.py (500 lines) - Shot preset system
- shot.py (338 lines) - Shot assembly from YAML
- render.py (830 lines) - Quality tiers, passes, EXR output, denoising
- shuffler.py (365 lines) - Shot variation generator
- frame_store.py (419 lines) - State capture and comparison
- depth_layers.py (438 lines) - Fore/mid/background organization
- composition.py (643 lines) - Composition guide overlays
- lens_fx.py (719 lines) - Post-process lens effects
- testing.py (284 lines) - End-to-end test utilities
- benchmark.py (308 lines) - Performance benchmarking utilities
- __init__.py (817 lines) - Package exports

**Total exports:** 400+
**Version:** 0.4.0

## Tracking System Module Summary

**lib/cinematic/tracking/** (7 modules, ~4,668 lines):
- types.py (1188 lines) - TrackData, SolveData, FootageMetadata, TrackingSession, BatchJob, BatchConfig, BatchResult, CornerPinData, PlanarTrack, RotationCurve, RigidBodySolve, FloorPlane, ScaleCalibration, ScanData, JointTransform, BoneChannel, MocapData, FingerData, HandFrame, HandAnimation
- footage.py (833 lines) - Footage import, ffprobe metadata extraction
- import_export.py (976 lines) - Nuke .chan import, coordinate conversion
- session_manager.py (130 lines) - Session persistence (save/load/resume)
- object_tracker.py (500 lines) - PlanarTracker, KnobTracker, RigidBodyTracker, FaderTracker, ObjectTracker
- scan_import.py (751 lines) - PLYParser, OBJParser, FloorDetector, ScaleDetector, ScanImporter
- mocap.py (694 lines) - MocapImporter, MocapRetargeter, ButtonPressDetector, PressEvent

**lib/cinematic/batch.py** (608 lines) - BatchProcessor, BatchCheckpoint, generate_batch_report, run_batch

**State directories:**
- .gsd-state/tracking/sessions/ - Active tracking sessions
- .gsd-state/tracking/solves/ - Completed camera solves
- .gsd-state/tracking/footage/ - Footage metadata cache

**Total exports:** 70+
**Version:** 0.4.0

## Follow Camera System Module Summary

**lib/cinematic/follow_cam/** (10 modules, ~14,000 lines):
- types.py (473 lines) - FollowMode, FollowCameraConfig, FollowTarget, CameraState, ObstacleInfo
- follow_modes.py (~600 lines) - calculate_ideal_position, smooth_position, smooth_angle
- transitions.py (~400 lines) - TransitionManager, create_orbit_transition, create_dolly_transition
- collision.py (~500 lines) - detect_obstacles, calculate_avoidance_position
- prediction.py (~400 lines) - MotionPredictor, predict_look_ahead
- framing.py (~300 lines) - calculate_framing_offset, apply_dead_zone
- pre_solve.py (~400 lines) - PreSolver, compute_pre_solve_path
- navmesh.py (~400 lines) - NavMesh, smooth_path, simplify_path
- debug.py (~400 lines) - DebugVisualizer, generate_hud_text
- __init__.py (~200 lines) - Package exports

**configs/cinematic/follow_cam/follow_modes.yaml** (18 presets)
- 8 follow mode presets (one per mode)
- Collision presets (relaxed, strict, minimal)
- Transition presets (instant, smooth, cinematic, orbit)

**State directories:**
- .gsd-state/follow_cam/solves/ - Pre-solved camera paths
- .gsd-state/follow_cam/previews/ - Preview videos

**Total exports:** 60+
**Version:** 0.4.0

## Character System Module Summary

**lib/character/** (5 modules, ~2,725 lines):
- wardrobe_types.py (455 lines) - CostumePiece, Costume, CostumeChange, CostumeAssignment, WardrobeRegistry, 6 enums
- costume_manager.py (516 lines) - CostumeManager with CRUD, assignments, change detection
- continuity_validator.py (600 lines) - validate_continuity, condition progression, report generation
- costume_bible.py (645 lines) - generate_costume_bible, shopping list, HTML/PDF/YAML export
- yaml_storage.py (287 lines) - load/save wardrobe YAML, directory loading
- __init__.py (222 lines) - Package exports (50+ exports)

**configs/production/wardrobe/**
- schema.yaml - Complete YAML schema documentation
- examples/hero_costumes.yaml - Hero character example (3 costumes, 9 scenes)
- examples/villain_costumes.yaml - Villain character example (3 costumes, 7 scenes)
- templates/character_template.yaml - Blank template with inline documentation

**Total exports:** 50+
**Version:** 0.1.0

## Production Orchestrator Module Summary

**lib/production/** (6 modules, ~2,900 lines):
- production_types.py (690 lines) - ProductionConfig, CharacterConfig, LocationConfig, ShotConfig, 6 enums
- production_loader.py (420 lines) - YAML loading, templates, time estimation
- production_validator.py (460 lines) - Validation with helpful error messages
- execution_engine.py (430 lines) - 8-phase execution orchestrator with checkpointing
- parallel_executor.py (340 lines) - Dependency analysis, parallel execution
- cli.py (430 lines) - Click-based CLI (run, validate, info, estimate, list, create)

**configs/production/**
- templates/short_film.yaml - Short film production template
- templates/commercial.yaml - Commercial/advertising template
- templates/game_assets.yaml - Game assets with retro conversion
- examples/example_production.yaml - Complete example

**Output Format Presets:**
- cinema_4k, cinema_2k, streaming_4k, streaming_1080p
- youtube_1080p, social_square
- 16bit_game, 8bit_game

**CLI Commands:**
- `run` - Execute production from YAML
- `validate` - Validate configuration
- `info` - Show production information
- `estimate` - Estimate execution time
- `list` - List productions in directory
- `create` - Create from template

**Total exports:** 70+
**Total tests:** 44
**Version:** 0.1.0

## Retro Pixel Art System Module Summary

**lib/retro/** (23 modules, ~13,000 lines):
- pixel_types.py (480 lines) - PixelStyle, PixelationConfig, PixelationResult, ColorPalette, 6 enums
- pixelator.py (680 lines) - Main pixelation engine with 8 mode functions, dithering
- quantizer.py (580 lines) - Median cut, K-means, Octree quantization algorithms
- preset_loader.py (320 lines) - YAML profile loading with 20+ presets
- pixel_compositor.py (400 lines) - Blender compositor integration
- dither_types.py (465 lines) - DitherConfig, DitherMatrix, DitherMode, DitherColorSpace
- dither_ordered.py (400 lines) - Bayer matrices, ordered dithering, halftone
- dither_error.py (530 lines) - Error diffusion (Floyd-Steinberg, Atkinson, Sierra, JJN)
- dither_patterns.py (440 lines) - Pattern-based dithering, stipple, woodcut
- dither.py (380 lines) - Main dither() function with unified interface
- isometric_types.py (820 lines) - IsometricConfig, SideScrollerConfig, SpriteSheetConfig, TileConfig, 4 enums
- isometric.py (525 lines) - Isometric camera, projection, depth sorting, grid
- side_scroller.py (470 lines) - Parallax layers, animation, depth assignment
- sprites.py (540 lines) - Sprite sheet generation, trimming, 4 format exporters
- tiles.py (580 lines) - Tile sets, maps, autotile, collision, transforms
- view_preset_loader.py (280 lines) - YAML preset loader with caching
- crt_types.py (480 lines) - CRTConfig, ScanlineConfig, PhosphorConfig, CurvatureConfig, 3 enums
- scanlines.py (420 lines) - Scanline patterns, overlays, GPU shaders
- phosphor.py (450 lines) - Phosphor masks (RGB stripe, aperture grille, slot mask, shadow mask)
- curvature.py (380 lines) - Barrel distortion, vignette, corner rounding
- crt_effects.py (650 lines) - Bloom, aberration, flicker, noise, ghosting, color adjustments
- crt_compositor.py (400 lines) - Blender compositor node integration
- crt_preset_loader.py (265 lines) - CRT YAML preset loading with caching
- __init__.py (1107 lines) - Package exports (350+ exports)

**configs/cinematic/retro/**
- pixel_profiles.yaml - 20+ console presets, 7 palettes, 14 resolutions
- dither_presets.yaml - 50+ dither presets
- view_presets.yaml - 35 view presets (9 isometric, 8 side-scroller, 10 sprite, 8 tile)
- crt_presets.yaml - 18 CRT display presets (arcade, TV, professional, LCD, special)

**Built-in Palettes:**
- Game Boy (4 colors) - Original green monochrome
- PICO-8 (16 colors) - Fantasy console
- NES (30 colors) - Simplified NES palette
- CGA (4 colors) - IBM CGA
- EGA (16 colors) - IBM EGA
- Mac Plus (2 colors) - Black and white

**Isometric Angles:**
- true_isometric, pixel, pixel_perfect, military, dimetric, blizzard, fallout

**Sprite Formats:**
- Phaser, Unity, Godot, Generic JSON

**Total exports:** 350+
**Total tests:** 685 (197 dither + 234 isometric + 254 CRT)
**Version:** 0.3.0

## Decisions

| Date | Phase | Decision | Rationale |
|------|-------|----------|-----------|
| 2026-02-18 | 06-03 | State in .gsd-state/ not config/ | Separate runtime state from static configuration |
| 2026-02-18 | 06-03 | YAML for frame_index.yaml | Human-readable, easy debugging |
| 2026-02-18 | 06.1-01 | PlumbBobConfig.focus_mode | Support both auto and manual focus distance |
| 2026-02-18 | 06.1-02 | APERTURE_MIN=0.95, MAX=22.0 | Real-world lens aperture range |
| 2026-02-18 | 06.1-04 | Compositor pipeline order | Geometric -> Luminance -> Color -> Film |
| 2026-02-18 | 06.1-05 | Version bump to 0.1.1 | Camera system complete |
| 2026-02-18 | 06.2-02 | Light linking for Blender 4.0+ | Selective illumination feature |
| 2026-02-18 | 06.2-03 | Tanner Helland algorithm | Kelvin to RGB conversion |
| 2026-02-18 | 06.2-04 | Multi-path HDRI search | assets/hdri, configs, ~/hdri_library |
| 2026-02-18 | 06.2-05 | Version bump to 0.1.2 | Lighting system complete |
| 2026-02-19 | 06.3-01 | BackdropConfig extended properties | Support infinite curves, gradients, HDRI, mesh |
| 2026-02-19 | 06.3-02 | bmesh over bpy.ops for geometry | Context-free mesh creation for batch processing |
| 2026-02-19 | 06.3-02 | CLIP shadow_method | Clean shadow edges (not HASHED) |
| 2026-02-19 | 06.3-02 | LINEAR ColorRamp interpolation | Avoid gradient banding artifacts |
| 2026-02-19 | 06.3-03 | Version bump to 0.1.3 | Backdrop system complete |
| 2026-02-19 | 06.4-01 | LUTConfig.intensity default = 0.8 | Per REQ-CINE-LUT requirements |
| 2026-02-19 | 06.4-01 | ExposureLockConfig.target_gray = 0.18 | 18% gray standard |
| 2026-02-19 | 06.4-02 | ColorBalance for LUT approximation | Blender lacks native .cube LUT loader in compositor |
| 2026-02-19 | 06.4-02 | MixRGB intensity blending | LUT output blends at config.intensity ratio (0.8 default) |
| 2026-02-19 | 06.4-02 | Optional scene_luminance parameter | Direct luminance requires render pass access |
| 2026-02-19 | 06.4-03 | Version left at 0.2.0 | Already bumped from prior shot_builder integration |
| 2026-02-19 | 06.5-01 | AnimationConfig.type as string enum | Flexible for future animation types without enum maintenance |
| 2026-02-19 | 06.5-01 | TurntableConfig.defaults loop=True | Product showcase typically requires continuous rotation |
| 2026-02-19 | 06.5-01 | Separate dataclasses for each animation type | Clean separation of concerns, easier to extend independently |
| 2026-02-19 | 06.5-01 | Match existing YAML structure | Consistent with camera_moves.yaml and easing_curves.yaml patterns |
| 2026-02-19 | 06.5-02 | LINEAR interpolation for turntable/orbit | Constant-speed motion for product showcase |
| 2026-02-19 | 06.5-02 | Direct keyframe_insert API | Avoid bpy.ops context dependencies |
| 2026-02-19 | 06.5-02 | Separate motion_path module | Isolate procedural path generation logic |
| 2026-02-18 | 06.6-01 | CinematicRenderSettings as separate class | Extends basic RenderSettings with pass configuration and quality tiers |
| 2026-02-18 | 06.6-01 | Default engine EEVEE_NEXT | Modern Blender 4.0+ default, faster iteration |
| 2026-02-18 | 06.6-01 | Default samples 64 | Balance between quality and speed for preview tier |
| 2026-02-18 | 06.6-03 | Created render.py inline | Plan dependency 06.6-02 was unmet; necessary for export task |
| 2026-02-18 | 06.6-03 | BLENDER_EEVEE_NEXT not BLENDER_EEVEE | Critical: EEVEE deprecated in Blender 4.2+ |
| 2026-02-18 | 06.6-03 | Version bump to 0.2.2 | Render system complete |
| 2026-02-19 | 06.7-01 | ShuffleConfig default ranges | Camera angle +/-15 deg, focal length 45-85mm for useful variations |
| 2026-02-19 | 06.7-01 | FrameState includes timestamp | Essential for version comparison and undo history |
| 2026-02-19 | 06.7-01 | DepthLayerConfig separate DOF per layer | Fine control over depth of field by scene depth |
| 2026-02-19 | 06.7-01 | LensFXConfig defaults to disabled | Effects should be explicitly enabled |
| 2026-02-19 | 06.7-03 | Version bump to 0.2.3 | Support systems exports complete |
| 2026-02-19 | 06.8-01 | extends field as string | Simple template name reference, resolved at load time |
| 2026-02-19 | 06.8-01 | abstract boolean field | Clean way to mark non-renderable base templates |
| 2026-02-19 | 06.8-01 | Deep merge for dicts in inheritance | Allows partial overrides (e.g., just change camera.focal_length) |
| 2026-02-19 | 06.8-03 | Created shot.py inline | Plan dependency 06.8-02 was unmet; necessary for export task |
| 2026-02-19 | 06.8-03 | Version bump to 0.2.4 | Shot assembly system complete |
| 2026-02-19 | 06.9-01 | CameraMatchConfig vanishing points as List[Tuple] | Flexible storage for 2D image coordinates |
| 2026-02-19 | 06.9-01 | TrackingImportConfig format as string | Easier YAML serialization and future extensibility |
| 2026-02-19 | 06.9-01 | AudioSyncConfig markers as Dict[str, int] | Maps marker names to frame numbers |
| 2026-02-19 | 06.9-01 | CameraProfile distortion_params as list | Supports various distortion models with different coefficient counts |
| 2026-02-19 | 06.9-02 | detect_bpm placeholder | Full implementation requires audio analysis library (librosa/aubio) |
| 2026-02-19 | 06.9-02 | detect_horizon_line placeholder | Full implementation requires image analysis (edge detection, vanishing point) |
| 2026-02-19 | 06.9-02 | Nuke .chan Y-up conversion | Converts Y-up coordinate system to Blender's Z-up default |
| 2026-02-19 | 06.9-02 | FOV to focal length conversion | Uses 36mm sensor width for simplified calculation |
| 2026-02-19 | 06.9-03 | Camera profiles organized by category | Easy discovery: smartphone, cinema, DSLR, action, drone |
| 2026-02-19 | 06.9-03 | Brown-Conrady for action cameras | Wide-angle lenses (GoPro, DJI Osmo) need 5-coefficient model |
| 2026-02-19 | 06.9-03 | Version bump to 0.2.5 | Camera matching system complete |
| 2026-02-19 | 06.10-01 | IntegrationConfig for control surface | Links cinematic with control surface design system |
| 2026-02-19 | 06.10-01 | TestConfig with validation checks | Define test scenarios with validation criteria |
| 2026-02-19 | 06.10-01 | PerformanceConfig with targets | Define performance benchmarks (render time, memory, GPU) |
| 2026-02-19 | 06.10-01 | BenchmarkResult for measurements | Store timing and resource usage data |
| 2026-02-19 | 06.10-03 | Created benchmark.py inline | Plan dependency 06.10-02 was unmet; necessary for export task |
| 2026-02-19 | 06.10-03 | Version bump to 0.3.0 | Milestone v0.5 Cinematic Rendering System complete |
| 2026-02-19 | 07.5-PLAN | Wave 1 = batch.py first | Highest value (parallel processing), lowest complexity |
| 2026-02-19 | 07.5-PLAN | Wave 5 = Version bump to 0.4.0 | Marks MILESTONE v0.6 (Motion Tracking System) complete |
| 2026-02-19 | 07.5-PLAN | rotation_to_morph() in KnobTracker | Direct integration with MorphEngine for control surfaces |
| 2026-02-19 | 07.5-PLAN | RANSAC for floor detection | Standard algorithm for robust plane fitting |
| 2026-02-19 | 07.5-PLAN | ProcessPoolExecutor for batch | Subprocess isolation prevents crashes from affecting other jobs |
| 2026-02-19 | 07.5-PLAN | P2 priority for Phase 7.5 | Can be implemented incrementally after core tracking |
| 2026-02-19 | 07.0-01 | Dict keys as strings in to_dict() | Integer frame numbers must be strings for JSON/YAML serialization |
| 2026-02-19 | 07.0-01 | Track markers normalized 0-1 | Resolution-independent tracking data for any footage size |
| 2026-02-19 | 07.0-01 | field(default_factory=dict) for markers | Prevents mutable default issues in dataclasses |
| 2026-02-19 | 07.0-04 | Y-up to Z-up via (x, z, -y) | 90 degree rotation around X-axis for Blender compatibility |
| 2026-02-19 | 07.0-04 | SolveData return type | New import functions return SolveData instead of legacy ImportedCamera |
| 2026-02-19 | 07.0-04 | Backward compatibility with ImportedCamera | Legacy class preserved with to_solve_data() method |
| 2026-02-19 | 07.0-05 | JSON fallback when PyYAML not available | Session persistence works without PyYAML dependency |
| 2026-02-19 | 07.0-05 | Version bump to 0.3.1 | Tracking foundation exports complete |
| 2026-02-19 | 07.5-01 | ProcessPoolExecutor for batch | Subprocess isolation prevents crashes from affecting other jobs |
| 2026-02-19 | 07.5-01 | JSON checkpoint format | Cross-platform compatibility, easy debugging |
| 2026-02-19 | 07.5-01 | Auto-detect workers (CPU-1) | Safe default that leaves headroom for system |
| 2026-02-19 | 07.5-01 | Per-job timeout support | Prevents hung jobs from blocking batch indefinitely |
| 2026-02-19 | 07.5-02 | rotation_to_morph() for MorphEngine | Direct integration with control surface morphing system |
| 2026-02-19 | 07.5-02 | Nuke CornerPin2D export format | Industry standard for compositing workflows |
| 2026-02-19 | 07.5-02 | Quaternion rotation in RigidBodySolve | Full 3D rotation without gimbal lock |
| 2026-02-19 | 07.5-02 | Unified ObjectTracker interface | Single entry point for all tracking types |
| 2026-02-19 | 07.5-03 | RANSAC floor detection with horizontal bias | Robust plane fitting with prefer_horizontal option |
| 2026-02-19 | 07.5-03 | PLY binary little/big endian support | Cross-platform binary format compatibility |
| 2026-02-19 | 07.5-03 | Scale calibration confidence scoring | Inverse proportional to deviation from 1.0 |
| 2026-02-19 | 07.5-04 | BVH hierarchy parsing with bone_stack | Tracks parent-child relationships during recursive parse |
| 2026-02-19 | 07.5-04 | Hysteresis for button press detection | Different press/release thresholds prevent flickering |
| 2026-02-19 | 07.5-04 | Rotation ranges per control type | Knob=360deg, Fader=90deg, Button=30deg depth |
| 2026-02-19 | 07.5-05 | Version bump to 0.4.0 | MILESTONE v0.6 Motion Tracking System complete |
| 2026-02-19 | 08.0-01 | State directories for follow_cam | Separate runtime state (solves/previews) from source files |
| 2026-02-19 | 08.0-01 | .gitkeep for empty directories | Track state directories in git without content |
| 2026-02-20 | 6.2-01 | Separate tracking_types.py from tracking/ | Phase 6.2 object tracking distinct from Phase 7.x camera solving |
| 2026-02-20 | 6.2-01 | Exponential + Gaussian smoothing | Two smoothing algorithms for different use cases |
| 2026-02-20 | 6.2-01 | Kinematic prediction equation | p_future = p_current + v*t + 0.5*a*t^2 for smooth following |
| 2026-02-20 | 6.2-01 | Multi-format export (JSON/AE/Nuke/Blender) | Integration with post-production pipelines |
| 2026-02-20 | 6.3-01 | Separate cinematic follow from follow_cam | Phase 6.3 cinematic modes distinct from Phase 8.x game modes |
| 2026-02-20 | 6.3-01 | Exponential decay smoothing | Natural camera movement feel |
| 2026-02-20 | 6.3-01 | Spring physics for elastic mode | Physically-based settling behavior with Hooke's law |
| 2026-02-20 | 6.3-01 | Dynamic dead zones | Adapts to target speed for stable framing |
| 2026-02-20 | 7.1-01 | Kinematic prediction formula | p_future = p_current + v*t + 0.5*a*t^2 for smooth following |
| 2026-02-20 | 7.1-01 | Multi-format export | JSON/AE/Nuke/Blender for post-production integration |
| 2026-02-20 | 7.1-01 | Central difference for velocity | More accurate than forward/backward for interior frames |
| 2026-02-20 | 8.1-01 | Standard library only for parsers | No external dependencies for Fountain/FDX parsing |
| 2026-02-20 | 8.1-01 | 1 page = 1 minute for runtime | Industry standard rule of thumb for screenplay timing |
| 2026-02-20 | 8.1-01 | 55 lines per page estimate | Standard screenplay format convention |
| 2026-02-20 | 8.1-01 | 5 beat structure templates | Save the Cat, Three-Act, Story Circle, Hero's Journey, Sequel Method |
| 2026-02-20 | 8.1-01 | Version bump to 0.5.0 | Script Parser module complete |
| 2026-02-20 | 8.2-01 | Dialogue threshold at 70% | Standard screenplay analysis convention |
| 2026-02-20 | 8.2-01 | 8 shot size types | Industry standard coverage options |
| 2026-02-20 | 8.2-01 | 6 camera angles | Common cinematographic vocabulary |
| 2026-02-20 | 8.2-01 | Priority: essential/recommended/optional | Flexible scheduling for productions |
| 2026-02-20 | 8.2-01 | Style presets for AI prompts | Easy switching between visualization styles |
| 2026-02-20 | 8.2-01 | Version bump to 0.6.0 | Shot List Generator module complete |
| 2026-02-20 | 9.1-01 | bmesh for geometry creation | Context-free mesh creation for batch processing |
| 2026-02-20 | 9.1-01 | 8 dressing styles with density/clutter | Range from minimal (0.3/0.1) to hoarder (1.0/1.0) |
| 2026-02-20 | 9.1-01 | 12 style presets | Modern, victorian, scifi, cyberpunk, scandinavian, etc. |
| 2026-02-20 | 9.1-01 | Prop library separation | Furniture, decor, electronics in separate YAML files |
| 2026-02-20 | 9.1-01 | 40+ built-in props | Common furniture, decor, electronics, bathroom items |
| 2026-02-20 | 10.1-01 | Condition progression rules in dict | Easy to validate, clear documentation |
| 2026-02-20 | 10.1-01 | Separate validator module | Clean separation of concerns |
| 2026-02-20 | 10.1-01 | HTML export with inline CSS | Self-contained single file |
| 2026-02-20 | 10.1-01 | Shopping list consolidates duplicates | Accurate quantities for purchasing |
| 2026-02-20 | 10.1-01 | Suggestion threshold at 10+ scenes | Balance between helpful and noisy |

## Concerns

None currently.

## Session Continuity

**Last session:** 2026-02-20
**Stopped at:** Completed Phase 14.2 Master Production Config
**Resume file:** None - Phase complete
**Next phase:** Review requirements for next steps

## Milestone Summary

### Milestone v0.7: Intelligent Follow Camera System (COMPLETE)

**Version:** 0.4.0
**Completed:** 2026-02-19

**Delivered Systems:**
- Follow Camera Foundation (08.0) - Types, modes, presets, state directories
- Follow Camera Modes (08.1) - 8 modes: side_scroller, over_shoulder, chase, chase_side, orbit_follow, lead, aerial, free_roam
- Obstacle Avoidance (08.2) - Collision detection, OscillationPreventer, OperatorBehavior
- Pre-Solve System (08.3) - One-shot config, mode/framing changes, NavMesh with A*
- Integration & Polish (08.4) - Dynamic framing, FrameAnalyzer, 356 unit tests

**Total:** 10 modules, 62+ exports, ~5,000 lines, 356 tests

### Milestone v0.9: Production Tracking System (Phase 11.0 COMPLETE)

**Status:** Phase 11.0 complete (Dashboard UI)
**Completed:** 2026-02-19

**Delivered Systems:**
- Production Tracking Dashboard (11.0) - TypeScript/Vite web application
  - Kanban board with status columns
  - Item cards with category, name, description
  - Filter by status and category
  - Search by name/id/description
  - Blocker panel
  - Item detail modal
  - Dark theme, responsive design
  - Read-only by design (AI handles writes)

**Tech Stack:** Vite, TypeScript, Vanilla JS, CSS, YAML
**Data:** 9 sample items, 2 blockers in .planning/tracking/

**Commands:**
```bash
cd tracking-ui && npm run dev   # Start dev server
```

### Milestone v0.9: Timeline/Editorial System (Phase 11.1 COMPLETE)

**Status:** Phase 11.1 complete (Editorial System)
**Completed:** 2026-02-19

**Delivered Systems:**
- Timeline System (11.1) - Editorial/video editing support
  - Timecode (SMPTE HH:MM:SS:FF) with arithmetic
  - Clip, Track, Timeline data structures
  - Marker and Transition support
  - TimelineManager for operations (add/remove/move/trim/split/ripple)
  - Transitions (cut, dissolve, wipe, fade)
  - EDL (CMX 3600) export/import
  - FCPXML (Final Cut Pro) export/import
  - OTIO (OpenTimelineIO) export/import
  - Assembly from shot lists
  - Runtime calculation and statistics
  - Blender VSE integration

**Modules:** 7 Python modules, 50+ exports, 47 tests
**Location:** lib/editorial/

### Milestone v0.9: 1-Sheet Generator (Phase 12.0 COMPLETE)

**Status:** Phase 12.0 complete
**Completed:** 2026-02-19

**Delivered Systems:**
- 1-Sheet Generator (12.0) - Asset presentation sheets
  - Template system with category-specific layouts
  - Base template with hero image, metadata, dependencies
  - Character, prop, shot templates
  - HTML export (download)
  - PDF export (via print)
  - PNG export (optional, requires html2canvas)
  - Preview modal with actions
  - Dark/light theme support
  - Print-optimized CSS

**Tech Stack:** TypeScript, Vite, CSS
**Modules:** 10 TypeScript files in tracking-ui/src/onesheet/
**Integration:** 1-sheet button (📄) on item cards

### Milestone v0.9: Compositor (Phase 12.1 COMPLETE)

**Status:** Phase 12.1 complete
**Completed:** 2026-02-19

**Delivered Systems:**
- Compositor (12.1) - Multi-layer compositing system
  - Layer-based compositing with CompLayer, CompositeConfig
  - 18 blend modes (normal, multiply, screen, overlay, add, etc.)
  - Full color correction with presets (cinematic_warm, vintage, etc.)
  - Cryptomatte manifest and matte extraction
  - Blender compositor node creation
  - Lift/Gamma/Gain, ASC CDL, curves, levels
  - HSV adjustment, white balance
  - Highlights/shadows control

**Modules:** 6 Python modules, 100+ exports, 43 tests
**Location:** lib/vfx/

### Milestone v0.8: Anamorphic / Forced Perspective System (ALREADY IMPLEMENTED)

**Version:** 0.6.0
**Status:** Complete with 51 tests passing

**Delivered Systems:**
- Projection Foundation (9.0) - FrustumConfig, RayHit, ProjectionResult, AnamorphicProjectionConfig
- Surface Detection (9.1) - SurfaceInfo, OcclusionResult, MultiSurfaceGroup
- UV Generation (9.2) - UVGenerationResult, UVSeamInfo, UVLayoutConfig
- Texture Baking (9.3) - BakeConfig, BakeResult, BakeMode, BakeFormat
- Camera Zones (9.4) - ZoneManager, CameraZone, ZoneState, VisibilityController

**Total:** 10 modules, 50+ exports, 51 tests

### Milestone v0.6: Motion Tracking System (COMPLETE)

**Version:** 0.4.0
**Completed:** 2026-02-19

**Delivered Systems:**
- Tracking Foundation (07.0) - TrackData, SolveData, FootageMetadata, TrackingSession
- Batch Processing (07.5-01) - BatchProcessor, checkpoint resume, parallel execution
- Object Tracking (07.5-02) - PlanarTracker, KnobTracker, RigidBodyTracker, FaderTracker
- Scan Import (07.5-03) - PLY/OBJ parsers, FloorDetector, ScaleDetector, ScanImporter
- Mocap Import (07.5-04) - MocapImporter, MocapRetargeter, ButtonPressDetector, HandAnimation

**Total:** 8 modules, 70+ exports, ~5,100 lines

### Milestone v0.5: Cinematic Rendering System (COMPLETE)

**Version:** 0.3.0
**Completed:** 2026-02-19

**Delivered Systems:**
- Camera System (6.1) - Camera creation, DOF, plumb bob, lenses, rigs
- Lighting System (6.2) - Light creation, gels, HDRI environment
- Backdrop System (6.3) - Infinite curves, gradients, shadow catchers
- Color Pipeline (6.4) - Color management, LUTs, exposure lock
- Animation System (6.5) - Camera moves, motion paths, turntable
- Render System (6.6) - Quality tiers, passes, EXR, denoising
- Support Systems (6.7) - Shuffler, frame store, depth layers, composition, lens FX
- Shot Assembly (6.8) - Shot templates, YAML assembly
- Camera Matching (6.9) - Reference matching, tracking import, audio sync, camera profiles
- Integration Testing (6.10) - Test utilities, benchmarks

**Total:** 30 modules, 315+ exports, ~24,000 lines

### Milestone v0.6 Phase 1: Tracking Foundation (COMPLETE)

**Version:** 0.3.1
**Completed:** 2026-02-19

**Delivered Systems:**
- Tracking Types (07.0-01) - TrackData, SolveData, FootageMetadata, TrackingSession, SolveReport
- Footage Analysis (07.0-03) - ffprobe metadata extraction, frame rate detection
- Import/Export (07.0-04) - Nuke .chan import, Y-up to Z-up coordinate conversion
- Session Persistence (07.0-05) - TrackingSessionManager for save/load/resume

**Total:** 4 modules, 15+ exports, ~2,300 lines
**Next:** Phase 07.5 (Advanced Features) - batch processing, object tracking, scan import, mocap
| 2026-02-20 | 13.3-01 | 2:1 pixel ratio as default | Most common for games (SimCity, Diablo, etc.) |
| 2026-02-20 | 13.3-01 | PIL for sprite sheet generation | Cross-platform, no Blender dependency |
| 2026-02-20 | 13.3-01 | 4 export formats | Cover major game engines (Phaser, Unity, Godot) |
| 2026-02-20 | 13.3-01 | 16-tile autotile template | Standard blob tile approach |
| 2026-02-20 | 13.3-01 | YAML presets for all configs | Human-readable, easy to extend |
| 2026-02-20 | 13.3-01 | Version bump to 0.2.0 | Isometric & Side-Scroller system complete |
| 2026-02-20 | 14.1-01 | 8 execution phases | Standard production workflow (validate → finalize) |
| 2026-02-20 | 14.1-01 | JSON checkpoint format | Cross-platform, easy debugging |
| 2026-02-20 | 14.1-01 | Click for CLI | Industry standard Python CLI framework |
| 2026-02-20 | 14.1-01 | Scene range formats (scenes_X_Y, X-Y) | Flexible scene assignment syntax |
| 2026-02-20 | 14.1-01 | 8 output format presets | Cover cinema, streaming, social, retro |
| 2026-02-20 | 14.1-01 | ThreadPoolExecutor default | Thread-safe for I/O-bound rendering tasks |
| 2026-02-20 | 14.1-01 | Dependency graph for parallel execution | Independent shots execute concurrently |
| 2026-02-20 | 14.1-01 | Version bump to 0.8.0 | Production Orchestrator complete |
| 2026-02-20 | 14.2-01 | Separate schema from types.py | Clean separation of concerns |
| 2026-02-20 | 14.2-01 | ShotDef separate from ShotConfig | Simplified YAML syntax, auto-expansion |
| 2026-02-20 | 14.2-01 | RetroOutputConfig as nested class | Clean retro configuration in outputs |
| 2026-02-20 | 14.2-01 | 16 shot templates | Cover standard cinematography |
| 2026-02-20 | 14.2-01 | 8 style presets | Cover common visual styles |
| 2026-02-20 | 14.2-01 | validate_for_execution_strict | Strict validation for execution readiness |

