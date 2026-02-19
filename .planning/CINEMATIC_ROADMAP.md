# Cinematic System Implementation Roadmap

**Version**: 1.0
**Status**: Planning
**Created**: 2026-02-18
**Related**: REQUIREMENTS_CINEMATIC.md, CINEMATIC_SYSTEM_DESIGN.md

---

## Executive Summary

This roadmap defines the phased implementation plan for all 23 cinematic system requirements. The plan follows a dependency-ordered approach, ensuring each phase builds on completed foundations.

**Total Requirements**: 23
- **P0 (Critical)**: 5 requirements - Foundation systems
- **P1 (High)**: 6 requirements - Core features
- **P2 (Medium)**: 6 requirements - Enhancement features
- **P3 (Low)**: 4 requirements - Future expansion

**Estimated Duration**: 10 phases over ~6-8 weeks

---

## Dependency Graph

```
Phase 6.0: Foundation (P0)
    │
    ├── Phase 6.1: Camera System (P0) ──────────────┐
    │                                               │
    ├── Phase 6.2: Lighting System (P0) ────────────┤
    │                                               │
    └── Phase 6.3: Render System (P0) ──────────────┤
                                                    │
    ┌───────────────────────────────────────────────┘
    │
    ▼
Phase 6.4: Shot Assembly (P0) ◄─────────────────────┐
    │                                               │
    ├── Phase 6.5: Plumb Bob (P1)                   │
    │                                               │
    ├── Phase 6.6: Backdrop System (P1)             │
    │                                               │
    ├── Phase 6.7: Color Pipeline (P1)              │
    │                                               │
    └── Phase 6.8: Animation System (P1)            │
                                                    │
    ┌───────────────────────────────────────────────┘
    │
    ▼
Phase 6.9: Template System (P1)
    │
    ├── Phase 6.10: Motion Path (P2)
    │
    ├── Phase 6.11: Lens Imperfections (P2)
    │
    ├── Phase 6.12: Isometric Views (P2)
    │
    └── Phase 6.13: Support Systems (P2)
        │   ├── Shuffler
        │   ├── Frame Store
        │   └── Depth Layers
        │
        ▼
Phase 6.14: Asset Catalog Generator (P1)
    │
    └── Phase 6.15: Future Enhancements (P3)
        ├── Composition Guides
        ├── Render Farm
        ├── Camera Matching
        └── Audio Sync
```

---

## Phase Definitions

### Phase 6.0: Foundation (REQ-CINE-01)

**Priority**: P0 | **Est. Effort**: 2-3 days

**Goal**: Establish the foundational module structure, configuration directories, and state persistence framework.

**Deliverables**:
```
lib/
├── cinematic/
│   ├── __init__.py              # Module exports
│   ├── types.py                 # Type definitions
│   ├── constants.py             # Constants and enums
│   └── state_manager.py         # State persistence

configs/
├── cinematic/
│   ├── cameras/
│   ├── lighting/
│   ├── backdrops/
│   ├── color/
│   ├── animation/
│   ├── render/
│   └── shots/
│       ├── base/
│       ├── product/
│       └── control_surface/

.gsd-state/
└── cinematic/
    ├── camera/
    ├── lighting/
    ├── frames/
    └── sessions/
```

**Tasks**:
1. Create `lib/cinematic/` directory structure
2. Implement `__init__.py` with module exports
3. Create `types.py` with data classes:
   - `ShotState`
   - `CameraConfig`
   - `LightConfig`
   - `BackdropConfig`
   - `RenderConfig`
4. Create `constants.py` with:
   - `ENGINES` dict (BLENDER_EEVEE_NEXT, CYCLES, etc.)
   - `PASS_MAPPING` for render passes
   - `COMPOSITOR_PIPELINE` ordering
5. Implement `state_manager.py`:
   - `StateManager` class
   - `FrameStore` class
   - YAML serialization
6. Create configuration directory structure
7. Create state persistence directory structure

**Acceptance Criteria**:
- [ ] Module structure created
- [ ] Configuration directories exist
- [ ] State persistence framework works
- [ ] Can save/load YAML state files

---

### Phase 6.1: Camera System (REQ-CINE-CAM)

**Priority**: P0 | **Est. Effort**: 4-5 days
**Dependencies**: Phase 6.0

**Goal**: Implement comprehensive camera system with lenses, sensor presets, rigs, and multi-camera support.

**Deliverables**:
```
lib/cinematic/
├── camera.py                    # Camera transforms, rigs
└── lenses.py                    # Lens presets, DoF, imperfections

configs/cinematic/cameras/
├── lens_presets.yaml            # 10+ lens presets
├── sensor_presets.yaml          # 5+ sensor presets
├── rig_presets.yaml             # 5+ rig types
└── imperfection_presets.yaml    # Cooke, ARRI, vintage
```

**Tasks**:

1. **camera.py**:
   - `create_camera(name, config)` - Camera object creation
   - `set_transform(camera, position, rotation)` - Transform control
   - `set_position_mode(camera, mode, **params)` - angle_distance, explicit
   - `mount_rig(camera, rig_type, target)` - Rig mounting
   - `configure_multi_camera(layout, cameras)` - Multi-cam setup
   - `calculate_composite_positions(layout, count)` - Layout calculation

2. **lenses.py**:
   - `apply_lens_preset(camera, preset)` - Focal length, distortion
   - `configure_dof(camera, f_stop, focus_distance)` - DoF setup
   - `set_bokeh(camera, shape, blades, rotation)` - Bokeh control
   - `apply_imperfection_preset(camera, preset)` - Cooke, ARRI, etc.

3. **Configuration Files**:
   - `lens_presets.yaml`: 14mm, 24mm, 35mm, 50mm, 85mm, 135mm, 90mm macro, Helios vintage
   - `sensor_presets.yaml`: Full Frame, APS-C, M4/3, Cinema 4K, 8K
   - `rig_presets.yaml`: tripod, tripod_orbit, dolly, dolly_curved, crane, steadicam, drone
   - `imperfection_presets.yaml`: cooke_s4, arri_master_prime, vintage_helios, clean

**Acceptance Criteria**:
- [ ] Camera transform system works
- [ ] 10+ lens presets available
- [ ] 5+ sensor presets available
- [ ] 5+ camera rig types implemented
- [ ] Multi-camera composite rendering works
- [ ] Lens imperfection presets apply correctly

---

### Phase 6.2: Lighting System (REQ-CINE-LIGHT)

**Priority**: P0 | **Est. Effort**: 4-5 days
**Dependencies**: Phase 6.0

**Goal**: Implement modular lighting system with rigs, HDRI, gels, and light linking.

**Deliverables**:
```
lib/cinematic/
└── lighting.py                  # Light rigs, individual lights, HDRI

configs/cinematic/lighting/
├── rig_presets.yaml             # 8+ lighting rigs
├── gel_presets.yaml             # CTB, CTO, diffusion, creative
└── hdri_presets.yaml            # Studio and environment HDRIs

assets/hdri/
└── (bundled HDRI files)
```

**Tasks**:

1. **lighting.py**:
   - `create_light(type, name, config)` - Light creation
   - `apply_light_preset(light, preset)` - Preset application
   - `create_rig(rig_name, subject_position)` - Rig creation
   - `apply_gel(light, gel_type, intensity)` - Gel application
   - `load_hdri(preset, exposure, rotation)` - HDRI loading
   - `configure_light_linking(light, collection)` - Light linking
   - `find_hdri_path(preset_name)` - Multi-path search

2. **Light Rig Presets**:
   - three_point_soft
   - three_point_hard
   - product_hero
   - product_dramatic
   - studio_high_key
   - studio_low_key
   - console_overhead
   - mixer_angle

3. **HDRI System**:
   - Search paths: project → GSD bundled → external library
   - Auto-download from Polyhaven (optional)
   - Exposure and rotation control

**Acceptance Criteria**:
- [ ] All 5 light types supported
- [ ] 8+ lighting rig presets available
- [ ] Gel system with CTB/CTO/diffusion
- [ ] HDRI system with search paths
- [ ] Individual light override system works
- [ ] Light linking configured for selective illumination

---

### Phase 6.3: Render System (REQ-CINE-RENDER)

**Priority**: P0 | **Est. Effort**: 3-4 days
**Dependencies**: Phase 6.0

**Goal**: Implement render profiles, quality tiers, passes, and batch rendering.

**Deliverables**:
```
lib/cinematic/
└── render.py                    # Render profiles, passes, batch

configs/cinematic/render/
├── quality_profiles.yaml        # 5 quality tiers
└── pass_presets.yaml            # Pass configurations
```

**Tasks**:

1. **render.py**:
   - `set_render_engine(engine)` - BLENDER_EEVEE_NEXT, CYCLES
   - `apply_quality_profile(profile_name)` - Quality tier
   - `configure_render_passes(passes)` - Pass configuration
   - `set_output_format(format, path)` - PNG, EXR, JPEG
   - `configure_denoiser()` - Hardware-aware selection
   - `render_frame()` - Single frame render
   - `render_animation()` - Animation render
   - `create_render_queue(tasks)` - Batch queue
   - `embed_metadata(render, metadata)` - EXR metadata

2. **Quality Profiles**:
   - viewport_capture (Workbench, 512px, instant)
   - eevee_draft (EEVEE Next, 1024px effective, 16 samples)
   - cycles_preview (Cycles, 2048px, 64 samples)
   - cycles_production (Cycles, 4096px, 256 samples)
   - cycles_archive (Cycles, 4096px, 1024+ samples)

3. **Render Passes**:
   - beauty, combined
   - diffuse_direct, diffuse_indirect, diffuse_color
   - glossy_direct, glossy_indirect, glossy_color
   - transmission_*, emission
   - cryptomatte_object, cryptomatte_material
   - depth, normal, vector

**Acceptance Criteria**:
- [ ] 5 quality tier presets available
- [ ] All 3 output formats supported
- [ ] All render passes available
- [ ] Batch rendering with dependencies works
- [ ] Metadata embedding functions

---

### Phase 6.4: Shot Assembly (REQ-CINE-SHOT)

**Priority**: P0 | **Est. Effort**: 3-4 days
**Dependencies**: Phases 6.1, 6.2, 6.3

**Goal**: Implement complete shot assembly combining all cinematic elements.

**Deliverables**:
```
lib/cinematic/
└── shot.py                      # Shot assembly, resume/edit

configs/cinematic/shots/
├── examples/
│   ├── hero_knob.yaml
│   ├── product_hero.yaml
│   └── console_overview.yaml
└── ...
```

**Tasks**:

1. **shot.py**:
   - `assemble_shot(shot_config)` - Complete shot setup
   - `load_shot(yaml_path)` - Load from YAML
   - `execute_shot(shot_config)` - Execute and render
   - `resume_shot(state_path)` - Resume from saved state
   - `edit_shot(shot_name, edits)` - Partial parameter override
   - `save_shot_state(shot_name)` - Save current state

2. **Shot Configuration Schema**:
```yaml
shot:
  name: hero_knob_01
  subject:
    type: artifact
    artifact: my_knob
    position: [0, 0, 0]
  plumb_bob:
    mode: auto
    offset: [0, 0, 0.015]
  camera: {...}
  lighting: {...}
  backdrop: {...}
  color: {...}
  render: {...}
  animation: {...}  # optional
```

**Acceptance Criteria**:
- [ ] Single YAML produces complete render
- [ ] Resume from saved state works
- [ ] Edit workflow applies partial changes

---

### Phase 6.5: Plumb Bob System (REQ-CINE-PLUMB)

**Priority**: P1 | **Est. Effort**: 1-2 days
**Dependencies**: Phase 6.1

**Goal**: Implement target system for camera orbit, focus, and dolly operations.

**Deliverables**:
```
lib/cinematic/
└── plumb_bob.py                 # Focus/orbit target system
```

**Tasks**:

1. **plumb_bob.py**:
   - `calculate_plumb_bob(subject, config)` - Position calculation
   - `calculate_focus_distance(camera_pos, plumb_bob)` - Focus distance
   - `set_plumb_bob_mode(mode, **params)` - auto, manual, object
   - `visualize_plumb_bob(position)` - Debug visualization

2. **Positioning Modes**:
   - auto: Center of bounding box + offset → world space
   - manual: Explicit world coordinates
   - object: Use another object's location + offset

**Acceptance Criteria**:
- [ ] Plumb bob position calculated correctly from bounding box
- [ ] Manual override works with offset specification
- [ ] Camera orbit uses plumb bob as pivot point
- [ ] Focus distance derived from camera-to-plumb-bob distance
- [ ] Dolly moves target plumb bob

---

### Phase 6.6: Backdrop System (REQ-CINE-ENV)

**Priority**: P1 | **Est. Effort**: 3-4 days
**Dependencies**: Phase 6.2

**Goal**: Implement procedural backdrop and environment system.

**Deliverables**:
```
lib/cinematic/
└── backdrops.py                 # Infinite curves, gradients, HDRI

configs/cinematic/backdrops/
├── infinite_curves.yaml         # White, gray, dark, gradients
├── gradients.yaml               # Linear, radial, angular
└── environments.yaml            # Pre-built scenes
```

**Tasks**:

1. **backdrops.py**:
   - `create_backdrop(type, config)` - Backdrop creation
   - `create_infinite_curve(config)` - Procedural curve mesh
   - `create_gradient_backdrop(config)` - Gradient background
   - `apply_shadow_catcher(mesh, enabled)` - Shadow catcher setup
   - `configure_hdri_backdrop(preset)` - HDRI environment

2. **Infinite Curve Algorithm**:
   - Calculate floor extent from subject bounding box
   - Generate quadratic bezier curve from floor to wall
   - Create mesh with proper UVs
   - Apply gradient material
   - Configure shadow catcher if enabled

**Acceptance Criteria**:
- [ ] Infinite curve generation works with bounding box
- [ ] 5+ backdrop presets available
- [ ] Shadow catcher mode functions with proper alpha
- [ ] HDRI backdrop integration works

---

### Phase 6.7: Color Pipeline (REQ-CINE-LUT)

**Priority**: P1 | **Est. Effort**: 3-4 days
**Dependencies**: Phase 6.3

**Goal**: Implement complete color management with LUTs and exposure control.

**Deliverables**:
```
lib/cinematic/
└── color.py                     # LUTs, color management, exposure lock

configs/cinematic/color/
├── technical_luts.yaml          # Rec.709, sRGB, ACES (65³)
├── film_luts.yaml               # Kodak, Fuji, Cineon (33³)
├── creative_luts.yaml           # Cinematic looks
└── color_management_presets.yaml # AgX, ACES, Filmic

assets/luts/
└── (bundled LUT files)
```

**Tasks**:

1. **color.py**:
   - `apply_color_management(scene, preset)` - Color space setup
   - `load_lut(file_path)` - LUT loading
   - `apply_lut(node_tree, lut_config, stage)` - LUT application
   - `configure_exposure_lock(scene, config)` - Exposure lock
   - `apply_color_overrides(scene, overrides)` - Per-shot adjustments

2. **LUT Categories**:
   - Technical (65³): rec709_to_srgb, linear_to_log, acescg_to_rec709
   - Film (33³): kodak_2383, fuji_3510, cineon
   - Creative: cinematic_tealorange, product_clean

3. **Application Points**:
   - Technical LUTs: Stage 8 (early, before creative grading)
   - Creative LUTs: Stage 9 (late, after color correction)

**Acceptance Criteria**:
- [ ] Color management system implemented
- [ ] Color management presets available
- [ ] 5+ technical LUTs available (65³ precision)
- [ ] 5+ film emulation LUTs available (33³ precision)
- [ ] Exposure lock maintains consistent brightness
- [ ] LUT intensity blend control works

---

### Phase 6.8: Animation System (REQ-CINE-ANIM)

**Priority**: P1 | **Est. Effort**: 3-4 days
**Dependencies**: Phases 6.1, 6.5

**Goal**: Implement unified animation system for camera and object movement.

**Deliverables**:
```
lib/cinematic/
└── animation.py                 # Camera moves, turntable, timeline

configs/cinematic/animation/
├── camera_moves.yaml            # Orbit, dolly, crane, push-in
└── easing_curves.yaml           # Easing function definitions
```

**Tasks**:

1. **animation.py**:
   - `create_camera_move(move_type, config)` - Camera move setup
   - `create_turntable(subject, config)` - Turntable animation
   - `apply_easing(keyframes, easing_type)` - Easing curves
   - `create_animation_track(name, keyframes)` - Track creation
   - `sync_audio(animation, audio_file)` - Audio sync
   - `set_beat_markers(audio, beats)` - Beat marker placement

2. **Camera Moves**:
   - orbit_90, orbit_180, orbit_360
   - dolly_in, dolly_out
   - push_in (combined dolly + focal length)
   - crane_up, crane_down
   - rack_focus
   - reveal (sequence)

3. **Easing Functions**:
   - linear
   - ease_in (quadratic acceleration)
   - ease_out (quadratic deceleration)
   - ease_in_out (combined)

**Acceptance Criteria**:
- [ ] 8+ camera move presets available
- [ ] Track-based timeline implemented
- [ ] Easing curves work correctly
- [ ] Turntable rotation functions
- [ ] Camera and object animations can be synchronized

---

### Phase 6.9: Template System (REQ-CINE-TEMPLATE)

**Priority**: P1 | **Est. Effort**: 2-3 days
**Dependencies**: Phase 6.4

**Goal**: Implement template inheritance for shot configurations.

**Deliverables**:
```
lib/cinematic/
└── template.py                  # Template inheritance, resolution

configs/cinematic/shots/
├── base/
│   ├── base_product.yaml        # Abstract product base
│   ├── base_hero.yaml           # Abstract hero base
│   └── base_turntable.yaml      # Abstract turntable base
└── ...
```

**Tasks**:

1. **template.py**:
   - `resolve_template(shot_config, trace=False)` - Inheritance resolution
   - `load_template(template_name)` - Template loading
   - `validate_template(config)` - Template validation
   - `deep_merge(base, override)` - Deep dictionary merge

2. **Template Features**:
   - Abstract base templates (cannot render directly)
   - Extends/override pattern
   - Multi-level inheritance
   - Resolution trace for debugging

**Acceptance Criteria**:
- [ ] Template inheritance works
- [ ] Overrides apply correctly
- [ ] Abstract templates cannot render directly

---

### Phase 6.10: Motion Path System (REQ-CINE-PATH)

**Priority**: P2 | **Est. Effort**: 2-3 days
**Dependencies**: Phases 6.5, 6.8

**Goal**: Implement procedural motion path generation.

**Deliverables**:
```
lib/cinematic/
└── motion_path.py               # Path generation, easing, look-at
```

**Tasks**:

1. **motion_path.py**:
   - `generate_path(type, config)` - Path generation
   - `generate_orbit_path(config)` - Procedural orbit
   - `generate_spline_path(points)` - Spline interpolation
   - `generate_bezier_path(control_points)` - Bezier curves
   - `apply_look_at(path, target)` - Look-at constraint
   - `generate_keyframes(path, duration, easing)` - Keyframe generation

2. **Path Types**:
   - linear
   - spline (cubic interpolation)
   - bezier (control points)

**Acceptance Criteria**:
- [ ] Path generation from control points works
- [ ] Spline and bezier interpolation implemented
- [ ] Look-at constraint maintains subject framing
- [ ] Easing functions produce smooth motion

---

### Phase 6.11: Lens Imperfections (REQ-CINE-GIMP)

**Priority**: P2 | **Est. Effort**: 3-4 days
**Dependencies**: Phase 6.3

**Goal**: Implement procedural lens imperfection system via compositor.

**Deliverables**:
```
lib/cinematic/
└── lens_fx.py                   # Compositor effects pipeline
```

**Tasks**:

1. **lens_fx.py**:
   - `build_compositor_tree(node_tree, config)` - Effect chain
   - `create_lens_distortion(node_tree, config)` - Barrel/pincushion
   - `create_chromatic_aberration(node_tree, config)` - RGB separation
   - `create_vignette(node_tree, config)` - Edge darkening
   - `create_bloom(node_tree, config)` - Bloom effect
   - `create_glare(node_tree, config)` - Lens flare
   - `create_film_grain(node_tree, config)` - Grain overlay

2. **Effect Pipeline Order** (CRITICAL):
```
1. lens_distortion
2. chromatic_aberration
3. vignette
4. exposure_adjust
5. bloom
6. glare
7. color_correction
8. technical_lut (EARLY)
9. creative_lut (LATE)
10. film_grain
```

**Acceptance Criteria**:
- [ ] All effects implemented as compositing nodes
- [ ] Effects applied in correct pipeline order
- [ ] LUTs applied at correct stage
- [ ] 4+ lens character presets available
- [ ] Effects configurable individually

---

### Phase 6.12: Isometric View System (REQ-CINE-ISO)

**Priority**: P2 | **Est. Effort**: 2-3 days
**Dependencies**: Phase 6.1

**Goal**: Implement orthographic camera system for technical documentation.

**Deliverables**:
```
lib/cinematic/
└── isometric.py                 # Orthographic views, flat lighting
```

**Tasks**:

1. **isometric.py**:
   - `create_orthographic_camera(config)` - ORTHO camera setup
   - `set_isometric_angle(preset)` - Angle preset application
   - `create_grid_overlay(type, spacing)` - Grid overlay
   - `create_flat_lighting(preset)` - Flat lighting setup
   - `configure_pixel_perfect(resolution, grid_units)` - Pixel alignment

2. **Isometric Presets**:
   - true_isometric: 35.264° elevation, 45° rotation
   - dimetric_2_1: 30° elevation, 45° rotation
   - plan_view: 90° elevation (top-down)
   - front_view: 0° elevation, 0° rotation
   - side_view: 0° elevation, 90° rotation

3. **Flat Lighting Presets**:
   - flat_overhead
   - flat_softbox
   - technical_documentation
   - product_catalog

**Acceptance Criteria**:
- [ ] Orthographic camera mode works with isometric presets
- [ ] 5+ isometric angle presets available
- [ ] Grid overlay system functional
- [ ] Flat lighting presets produce even illumination
- [ ] Renders show no perspective distortion

---

### Phase 6.13: Support Systems (P2)

**Priority**: P2 | **Est. Effort**: 4-5 days
**Dependencies**: Phase 6.4

**Goal**: Implement shuffler, frame store, and depth layer systems.

**Deliverables**:
```
lib/cinematic/
├── shuffler.py                  # Shot variation generator
├── frame_store.py               # State capture/comparison
└── depth_layers.py              # Fore/mid/background layers
```

**Tasks**:

1. **shuffler.py**:
   - `generate_variations(base_config, ranges)` - Variation generation
   - `random_sample(ranges, seed)` - Random sampling
   - `grid_sample(ranges)` - Grid sampling
   - `organize_output(variations, base_path)` - Directory organization

2. **frame_store.py**:
   - `save_frame(shot_name, state)` - State capture
   - `load_frame(shot_name, frame_num)` - State restore
   - `compare_frames(frame_a, frame_b)` - Side-by-side comparison
   - `diff_frames(frame_a, frame_b)` - Parameter diff
   - `cleanup_old_frames(max_versions)` - Auto-cleanup

3. **depth_layers.py**:
   - `assign_depth_layers(objects, config)` - Layer assignment
   - `create_parallax_animation(layers, camera_move)` - Parallax effect
   - `calculate_layer_response(layer, distance)` - Response ratios

**Acceptance Criteria**:
- [ ] Random and grid modes implemented
- [ ] Reproducible with seed
- [ ] Frame capture preserves complete state
- [ ] Thumbnail generation works
- [ ] Layer assignment works
- [ ] Parallax animation creates depth effect

---

### Phase 6.14: Asset Catalog Generator (REQ-CINE-CATALOG)

**Priority**: P1 | **Est. Effort**: 5-6 days
**Dependencies**: Phases 6.4, 6.12

**Goal**: Implement automated screenshot and 3D asset generation for catalogs.

**Deliverables**:
```
lib/cinematic/
├── catalog.py                   # Catalog generator orchestrator
├── catalog_unit.py              # Test unit builder
├── catalog_layouts.py           # Strip, grid, comparison layouts
└── catalog_export.py            # GLTF/GLB export

configs/cinematic/catalog/
├── test_unit.yaml               # Test unit definition
├── capture_presets.yaml         # Capture configurations
└── layout_presets.yaml          # Layout definitions
```

**Tasks**:

1. **catalog.py**:
   - `generate_catalog(config)` - Main orchestrator
   - `capture_variations(parameter, values)` - Single-param variations
   - `capture_matrix(parameters)` - Multi-param matrix
   - `generate_manifest()` - manifest.json creation

2. **catalog_unit.py**:
   - `build_test_unit(config)` - Test object creation
   - `arrange_artifacts(artifacts, layout)` - Artifact arrangement
   - `apply_variation(unit, parameter, value)` - Variation application

3. **catalog_layouts.py**:
   - `create_strip_layout(items, direction)` - Horizontal/vertical strip
   - `create_grid_layout(items, rows, cols)` - N×M grid
   - `create_comparison_layout(item_a, item_b)` - A/B comparison
   - `create_isolated_layout(item)` - Single item

4. **catalog_export.py**:
   - `export_gltf(object, path, config)` - GLTF export
   - `export_glb(object, path, config)` - GLB export
   - `apply_draco_compression(path, settings)` - Draco compression
   - `generate_viewer_html(manifest)` - HTML viewer generation

**Acceptance Criteria**:
- [ ] Single-parameter variation capture works
- [ ] Multi-parameter matrix generation works
- [ ] All layout modes implemented
- [ ] Shot planning/edit/re-capture workflow functional
- [ ] Output organized in configurable directory structure
- [ ] GLTF/GLB export for 3D viewers works
- [ ] Catalog manifest generated automatically

---

### Phase 6.15: Future Enhancements (P3)

**Priority**: P3 | **Est. Effort**: Variable
**Dependencies**: Variable

**Goal**: Implement lower-priority enhancement features.

**Deliverables**:
```
lib/cinematic/
├── composition.py               # Viewport guides
├── render_farm.py               # Distributed rendering
├── camera_match.py              # Reference matching
└── audio_sync.py                # Audio timing
```

**Tasks**:

1. **composition.py** (REQ-CINE-COMPOSE):
   - Rule of thirds overlay
   - Golden ratio grid
   - Center cross
   - Safe areas
   - Custom guides

2. **render_farm.py** (REQ-CINE-FARM):
   - Chunk by shot/frame/tile
   - Manifest generation
   - Skip existing frames
   - Checksum verification

3. **camera_match.py** (REQ-CINE-MATCH):
   - Focal length estimation from reference
   - Horizon line matching
   - Tracking data import

4. **audio_sync.py** (REQ-CINE-AUDIO):
   - Audio file loading
   - Beat marker detection
   - Frame-based sync points

**Acceptance Criteria**:
- [ ] Standard guides available
- [ ] Custom guides supported
- [ ] Chunking produces independent work units
- [ ] Reference image matching works
- [ ] Audio loads and plays in timeline

---

## Implementation Schedule

| Phase | Requirements | Priority | Est. Days | Dependencies |
|-------|-------------|----------|-----------|--------------|
| 6.0 | CINE-01 | P0 | 2-3 | None |
| 6.1 | CINE-CAM | P0 | 4-5 | 6.0 |
| 6.2 | CINE-LIGHT | P0 | 4-5 | 6.0 |
| 6.3 | CINE-RENDER | P0 | 3-4 | 6.0 |
| 6.4 | CINE-SHOT | P0 | 3-4 | 6.1, 6.2, 6.3 |
| 6.5 | CINE-PLUMB | P1 | 1-2 | 6.1 |
| 6.6 | CINE-ENV | P1 | 3-4 | 6.2 |
| 6.7 | CINE-LUT | P1 | 3-4 | 6.3 |
| 6.8 | CINE-ANIM | P1 | 3-4 | 6.1, 6.5 |
| 6.9 | CINE-TEMPLATE | P1 | 2-3 | 6.4 |
| 6.10 | CINE-PATH | P2 | 2-3 | 6.5, 6.8 |
| 6.11 | CINE-GIMP | P2 | 3-4 | 6.3 |
| 6.12 | CINE-ISO | P2 | 2-3 | 6.1 |
| 6.13 | CINE-SHUFFLE, CINE-FRAME, CINE-DEPTH | P2 | 4-5 | 6.4 |
| 6.14 | CINE-CATALOG | P1 | 5-6 | 6.4, 6.12 |
| 6.15 | CINE-COMPOSE, CINE-FARM, CINE-MATCH, CINE-AUDIO | P3 | Variable | Variable |

**Total Estimated Effort**: 45-60 days

---

## Parallel Execution Opportunities

The following phases can be executed in parallel:

**Wave 1**: 6.1, 6.2, 6.3 (all depend only on 6.0)
**Wave 2**: 6.5, 6.6, 6.7 (after 6.4)
**Wave 3**: 6.10, 6.11, 6.12, 6.13 (after 6.9)

With parallel execution, total calendar time can be reduced to approximately **4-6 weeks**.

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Blender API changes | High | Pin to Blender 5.x, test against LTS |
| LUT file availability | Medium | Bundle essential LUTs, document sources |
| HDRI licensing | Medium | Use CC0 sources (Polyhaven) |
| Performance on large catalogs | Medium | Implement chunked rendering |
| Compositor node complexity | Medium | Thorough testing, clear docs |

---

## Success Metrics

1. **Functionality**: All 23 requirements implemented with acceptance criteria met
2. **Performance**: Draft render <10s, Production render <5min for single knob
3. **Usability**: Single YAML produces complete shot
4. **Reliability**: Resume works after crash
5. **Quality**: Production renders match control surface style presets

---

## Next Steps

1. **Review and approve** this roadmap
2. **Begin Phase 6.0**: Foundation
3. **Parallelize Waves 1-3** as dependencies allow
4. **Iterate** based on testing feedback

To start implementation:
```bash
/gsd:plan-phase 6.0
```
