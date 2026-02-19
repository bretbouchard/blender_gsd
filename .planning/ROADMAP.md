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

---

## Milestone: v0.5 - Cinematic Rendering System
**Target**: TBD
**Design**: `.planning/design/CINEMATIC_SYSTEM_DESIGN.md`
**Requirements**: `.planning/REQUIREMENTS_CINEMATIC.md`

### Phase 6.0: Foundation (REQ-CINE-01)
**Goal:** Establish foundational module structure, configuration directories, and state persistence framework for the cinematic rendering system.
**Plans:** 3 plans
**Completed:** 2026-02-18

Plans:
- [x] 06-01-PLAN.md - Create lib/cinematic/ Python package with types, enums, and state persistence
- [x] 06-02-PLAN.md - Create configuration directory structure with 21 YAML preset files
- [x] 06-03-PLAN.md - Create state persistence directory structure with frame index

### Phase 6.1: Camera System (REQ-CINE-CAM, REQ-CINE-PLUMB)
**Goal:** Implement comprehensive camera system with lenses, sensor presets, camera rigs, and plumb bob targeting system.
**Plans:** 5 plans
**Completed:** 2026-02-18

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

Plans:
- [x] 06.3-01-PLAN.md - Extend BackdropConfig with additional properties; add backdrop preset loaders (infinite curves, gradients, environments)
- [x] 06.3-02-PLAN.md - Create backdrops.py with create_infinite_curve, create_gradient_material, setup_shadow_catcher, create_backdrop
- [x] 06.3-03-PLAN.md - Update __init__.py with all backdrop exports and version bump to 0.1.3

### Phase 6.4: Color Pipeline (REQ-CINE-LUT)
- [ ] color.py - LUT management, color management
- [ ] LUT preset library (technical, film, creative)
- [ ] Exposure lock system

### Phase 6.5: Animation System (REQ-CINE-ANIM, REQ-CINE-PATH)
- [ ] animation.py - camera moves, unified timeline
- [ ] motion_path.py - procedural path generation
- [ ] Animation presets (orbit, dolly, crane, push-in)
- [ ] Turntable system
- [ ] Audio sync support

### Phase 6.6: Render System (REQ-CINE-RENDER)
- [ ] Extended render.py for cinematic profiles
- [ ] Render pass system (beauty, cryptomatte, depth, etc.)
- [ ] Quality tier presets (viewport, draft, preview, production, archive)
- [ ] Batch rendering with dependencies
- [ ] Metadata embedding in EXR

### Phase 6.7: Support Systems
- [ ] shuffler.py - shot variation generator
- [ ] frame_store.py - state capture/comparison
- [ ] depth_layers.py - fore/mid/background
- [ ] composition.py - guides and overlays
- [ ] lens_fx.py - post-process effects (bloom, flare, vignette)

### Phase 6.8: Shot Assembly (REQ-CINE-SHOT, REQ-CINE-TEMPLATE)
- [ ] shot.py - complete shot assembly
- [ ] template.py - inheritance system
- [ ] Shot preset library (product, control surface specific)
- [ ] Resume/edit system

### Phase 6.9: Camera Matching (REQ-CINE-MATCH, REQ-CINE-AUDIO)
- [ ] Camera matching from reference images
- [ ] Tracking data import (Nuke, After Effects)
- [ ] Audio track support with beat markers

### Phase 6.10: Integration & Testing
- [ ] Integration with control surface system
- [ ] End-to-end shot rendering tests
- [ ] Performance optimization
- [ ] Documentation

---

## Milestone: v0.6 - Motion Tracking System
**Target**: TBD
**Requirements**: `.planning/REQUIREMENTS_TRACKING.md`

### Phase 7.0: Tracking Foundation (REQ-TRACK-01)
**Priority**: P1 | **Est. Effort**: 2-3 days

**Goal**: Establish motion tracking module structure, configuration directories, and state persistence.

**Deliverables**:
```
lib/cinematic/tracking/
├── __init__.py
├── types.py              # Tracking data types
├── footage.py            # Footage analysis and import
├── point_tracker.py      # Point/feature tracking
├── camera_solver.py      # Camera solve integration
├── object_tracker.py     # Object tracking
├── import_export.py      # External format support
└── calibration.py        # Lens/camera calibration

configs/cinematic/tracking/
├── camera_profiles.yaml
├── tracking_presets.yaml
├── solver_settings.yaml
└── import_formats.yaml
```

**Tasks**:
- [ ] Create `lib/cinematic/tracking/` module structure
- [ ] Implement tracking data types (Track, Solve, Session)
- [ ] Create configuration directory structure
- [ ] Implement state persistence framework
- [ ] Create tracking session management

---

### Phase 7.1: Core Tracking (REQ-TRACK-POINT, REQ-TRACK-SOLVE)
**Priority**: P0 | **Est. Effort**: 9-11 days

**Goal**: Implement point tracking and camera solving.

**Tasks**:

1. **Point Tracking** (REQ-TRACK-POINT):
   - [ ] Feature detection (FAST, Harris, SIFT)
   - [ ] KLT optical flow tracking
   - [ ] Track management (add, delete, filter)
   - [ ] Track visualization
   - [ ] Manual track placement tools
   - [ ] Tracking presets (high_quality, balanced, fast, architectural)

2. **Camera Solver** (REQ-TRACK-SOLVE):
   - [ ] Blender libmv integration
   - [ ] Auto keyframe selection
   - [ ] Focal length refinement
   - [ ] Distortion refinement
   - [ ] Solve quality reporting
   - [ ] Blender camera creation from solve

**Acceptance Criteria**:
- [ ] Auto-detect 50+ trackable features
- [ ] Solve produces camera with <1px reprojection error
- [ ] Camera animation keyframes created in Blender

---

### Phase 7.2: Footage & Camera Profiles (REQ-TRACK-FOOTAGE, REQ-TRACK-CAMPROF)
**Priority**: P1 | **Est. Effort**: 5-7 days

**Goal**: Implement footage analysis and device-specific camera profiles.

**Tasks**:

1. **Footage Analysis** (REQ-TRACK-FOOTAGE):
   - [ ] Video format import (MOV, MP4, MXF, AVI, image sequences)
   - [ ] Metadata extraction (resolution, frame rate, codec)
   - [ ] Content analysis (motion blur, noise, contrast)
   - [ ] Rolling shutter detection
   - [ ] Rolling shutter compensation

2. **Camera Profiles** (REQ-TRACK-CAMPROF):
   - [ ] iPhone 14/14 Pro/15/15 Pro profiles
   - [ ] Cinema camera profiles (RED, ARRI, Blackmagic)
   - [ ] DSLR/Mirrorless profiles (Sony, Canon, Nikon)
   - [ ] Lens distortion models (Brown-Conrady, simple radial)
   - [ ] Focal length estimation from vanishing points
   - [ ] ST-Map generation for compositing

**Acceptance Criteria**:
- [ ] iPhone metadata extraction works
- [ ] 10+ device profiles available
- [ ] Rolling shutter compensation reduces skew

---

### Phase 7.3: External Import/Export (REQ-TRACK-IMPORT)
**Priority**: P1 | **Est. Effort**: 3-4 days

**Goal**: Import tracking data from professional match-move software.

**Tasks**:
- [ ] FBX camera import with coordinate conversion
- [ ] Alembic (.abc) import
- [ ] BVH motion capture import
- [ ] Nuke .chan import
- [ ] Collada (.dae) import
- [ ] 3DEqualizer export integration
- [ ] SynthEyes export integration

**Acceptance Criteria**:
- [ ] FBX import creates animated camera
- [ ] BVH import creates armature
- [ ] Coordinate system conversion works (Y-up to Z-up)

---

### Phase 7.4: Compositing & Shot Integration (REQ-TRACK-COMPOSITE, REQ-TRACK-SHOT)
**Priority**: P1 | **Est. Effort**: 5-7 days

**Goal**: Integrate tracking with compositing and shot assembly.

**Tasks**:

1. **Compositing Integration** (REQ-TRACK-COMPOSITE):
   - [ ] 2D stabilization from point tracks
   - [ ] Lens distortion ST-Map generation
   - [ ] Shadow catcher workflow
   - [ ] Background plate compositing
   - [ ] Compositor node creation from tracking data

2. **Shot Assembly Integration** (REQ-TRACK-SHOT):
   - [ ] Shot YAML references footage for tracking
   - [ ] Tracking runs as part of shot assembly
   - [ ] Solved camera integrates with cinematic camera system
   - [ ] Composite mode renders over footage
   - [ ] Resume tracking session support

**Acceptance Criteria**:
- [ ] Single YAML produces tracked composite shot
- [ ] Compositor nodes created automatically
- [ ] Resume works after interruption

---

### Phase 7.5: Advanced Features (REQ-TRACK-OBJECT, REQ-TRACK-SCAN, REQ-TRACK-MOCAP, REQ-TRACK-BATCH)
**Priority**: P2 | **Est. Effort**: 12-16 days

**Goal**: Implement object tracking, scan import, mocap, and batch processing.

**Tasks**:

1. **Object Tracking** (REQ-TRACK-OBJECT):
   - [ ] Planar tracking (corner pin)
   - [ ] Rigid body tracking
   - [ ] Knob/fader rotation extraction from footage

2. **LiDAR/Scan Import** (REQ-TRACK-SCAN):
   - [ ] Polycam OBJ/GLB import
   - [ ] RealityScan FBX import
   - [ ] Floor plane auto-detection
   - [ ] Scale detection
   - [ ] Scan as backdrop environment

3. **Motion Capture Import** (REQ-TRACK-MOCAP):
   - [ ] Move.ai FBX/BVH import
   - [ ] Rokoko Video import
   - [ ] Hand animation extraction for control surfaces
   - [ ] Retargeting to morphing engine

4. **Batch Processing** (REQ-TRACK-BATCH):
   - [ ] Multi-shot batch configuration
   - [ ] Parallel processing
   - [ ] Resume on failure
   - [ ] Batch report generation

**Acceptance Criteria**:
- [ ] Planar tracking produces corner pin
- [ ] LiDAR scan imports at correct scale
- [ ] Mocap drives control surface animation
- [ ] Batch processes multiple shots in parallel

---

### Motion Tracking Summary

| Phase | Requirements | Priority | Est. Days |
|-------|-------------|----------|-----------|
| 7.0 | TRACK-01 | P1 | 2-3 |
| 7.1 | TRACK-POINT, TRACK-SOLVE | P0 | 9-11 |
| 7.2 | TRACK-FOOTAGE, TRACK-CAMPROF | P1 | 5-7 |
| 7.3 | TRACK-IMPORT | P1 | 3-4 |
| 7.4 | TRACK-COMPOSITE, TRACK-SHOT | P1 | 5-7 |
| 7.5 | TRACK-OBJECT, TRACK-SCAN, TRACK-MOCAP, TRACK-BATCH | P2 | 12-16 |

**Total**: 36-48 days

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

### Phase 8.0: Follow Camera Foundation (REQ-FOLLOW-01)
**Priority**: P1 | **Est. Effort**: 2-3 days

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

**Goal**: Implement intelligent obstacle detection, avoidance, and prediction.

**Tasks**:

1. **Collision Detection** (REQ-FOLLOW-AVOID):
   - [ ] Raycast detection from camera to subject
   - [ ] Spherecast for wider detection radius
   - [ ] Frustum check for objects in view
   - [ ] Collision layer support
   - [ ] Ignore list (transparent, triggers, subject)

2. **Obstacle Response** (REQ-FOLLOW-AVOID):
   - [ ] Push forward (move camera closer to subject)
   - [ ] Orbit away (rotate around obstacle)
   - [ ] Raise up (move camera higher)
   - [ ] Zoom through (for transparent obstacles)
   - [ ] Camera backing response (wall behind camera)

3. **Camera Operator Behavior** (REQ-FOLLOW-AVOID):
   - [ ] Human-like reaction delay
   - [ ] Angle preferences
   - [ ] Smooth, intentional movements
   - [ ] Natural breathing (subtle movement)
   - [ ] Decision weighting (visibility, composition, smoothness)

4. **Motion Prediction** (REQ-FOLLOW-PREDICT):
   - [ ] Velocity-based trajectory prediction
   - [ ] Animation-based prediction (read keyframes ahead)
   - [ ] Look-ahead system (anticipate subject movement)
   - [ ] Speed anticipation (adjust for acceleration/deceleration)
   - [ ] Corner prediction (for vehicle following)

**Acceptance Criteria**:
- [ ] Camera never passes through walls
- [ ] Subject never fully occluded
- [ ] No oscillation or jitter in avoidance
- [ ] Prediction reduces camera lag by >50%

---

### Phase 8.3: Pre-Solve System (REQ-FOLLOW-SOLVE, REQ-FOLLOW-ENV)
**Priority**: P0 | **Est. Effort**: 7-9 days

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

| Phase | Requirements | Priority | Est. Days |
|-------|-------------|----------|-----------|
| 8.0 | FOLLOW-01 | P1 | 2-3 |
| 8.1 | FOLLOW-MODE | P0 | 5-7 |
| 8.2 | FOLLOW-AVOID, FOLLOW-PREDICT | P0 | 8-11 |
| 8.3 | FOLLOW-SOLVE, FOLLOW-ENV | P0 | 7-9 |
| 8.4 | FOLLOW-INTEGRATE, FOLLOW-FRAME, FOLLOW-DEBUG | P1 | 7-10 |

**Total**: 29-40 days

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

## Future Considerations

### Not Yet Scheduled
- Blender 5.x compatibility
- Alternative DCC support (Houdini, Maya)
- Cloud render integration
- Real-time collaboration
- Physical simulation (springs, dampers)
- Audio-reactive visualization
