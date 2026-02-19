# Blender GSD Ability Matrix

**Purpose**: Track all features/capabilities built into the system to prevent reinvention and enable discovery.

**Last Updated**: 2026-02-19

---

## How to Use This Document

1. **Before implementing** - Check if capability already exists
2. **After implementing** - Add new capability to appropriate section
3. **When planning** - Reference capabilities by ID (e.g., `CAP-CAM-01`)

---

## Capability Categories

| Prefix | Category |
|--------|----------|
| CAP-CAM | Camera System |
| CAP-LIGHT | Lighting System |
| CAP-ENV | Environment/Backdrop |
| CAP-RENDER | Rendering |
| CAP-ANIM | Animation |
| CAP-TRACK | Tracking/Motion |
| CAP-COMP | Compositing |
| CAP-IO | Import/Export |
| CAP-GEN | Geometry Generation |
| CAP-MAT | Materials/Shader |
| CAP-CTRL | Control Surfaces |
| CAP-SCENE | Scene Management |
| CAP-PROJ | Projection/Anamorphic |
| CAP-RETRO | Retro Graphics |

---

## Camera System (CAP-CAM)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-CAM-01 | Camera creation from config | `lib/cinematic/camera.py` | ✅ Complete |
| CAP-CAM-02 | Lens presets (14mm-200mm) | `configs/cinematic/cameras/lens_presets.yaml` | ✅ Complete |
| CAP-CAM-03 | Sensor presets (Full frame, APS-C, etc.) | `configs/cinematic/cameras/sensor_presets.yaml` | ✅ Complete |
| CAP-CAM-04 | Camera rigs (tripod, dolly, crane, steadicam, drone) | `lib/cinematic/rigs.py` | ✅ Complete |
| CAP-CAM-05 | Plumb bob targeting system | `lib/cinematic/plumb_bob.py` | ✅ Complete |
| CAP-CAM-06 | Multi-camera layouts | `lib/cinematic/rigs.py` | ✅ Complete |
| CAP-CAM-07 | Depth of field configuration | `lib/cinematic/camera.py` | ✅ Complete |
| CAP-CAM-08 | Lens imperfections (vignette, CA, flare) | `lib/cinematic/lenses.py` | ✅ Complete |
| CAP-CAM-09 | Shot presets (32 presets across 5 categories) | `configs/cinematic/cameras/shot_presets/` | ✅ Complete |
| CAP-CAM-10 | Composition rules engine | `lib/cinematic/types.py` (CompositionConfig) | ✅ Complete |

---

## Lighting System (CAP-LIGHT)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-LIGHT-01 | Area/Spot/Point/Sun lights | `lib/cinematic/lighting.py` | ✅ Complete |
| CAP-LIGHT-02 | Light rig presets | `configs/cinematic/lighting/light_rig_presets.yaml` | ✅ Complete |
| CAP-LIGHT-03 | Gel system (CTB, CTO, diffusion) | `lib/cinematic/gel.py` | ✅ Complete |
| CAP-LIGHT-04 | HDRI environment lighting | `lib/cinematic/hdri.py` | ✅ Complete |
| CAP-LIGHT-05 | Light linking | `lib/cinematic/lighting.py` | ✅ Complete |
| CAP-LIGHT-06 | Color temperature (Kelvin) | `lib/cinematic/gel.py` | ✅ Complete |
| CAP-LIGHT-07 | Studio lighting presets | `configs/cinematic/lighting/` | ✅ Complete |

---

## Environment/Backdrop (CAP-ENV)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-ENV-01 | Infinite curve backdrop | `lib/cinematic/backdrops.py` | ✅ Complete |
| CAP-ENV-02 | Gradient backgrounds | `lib/cinematic/backdrops.py` | ✅ Complete |
| CAP-ENV-03 | Shadow catcher surfaces | `lib/cinematic/backdrops.py` | ✅ Complete |
| CAP-ENV-04 | HDRI backdrops | `lib/cinematic/backdrops.py` | ✅ Complete |
| CAP-ENV-05 | Mesh environment loading | `lib/cinematic/backdrops.py` | ✅ Complete |

---

## Rendering (CAP-RENDER)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-RENDER-01 | Quality tier presets (viewport, draft, preview, production, archive) | `lib/cinematic/render.py` | ✅ Complete |
| CAP-RENDER-02 | Render pass configuration (Z, normal, cryptomatte) | `lib/cinematic/render.py` | ✅ Complete |
| CAP-RENDER-03 | EXR multilayer output | `lib/cinematic/render.py` | ✅ Complete |
| CAP-RENDER-04 | Hardware-aware denoising | `lib/cinematic/render.py` | ✅ Complete |
| CAP-RENDER-05 | Batch rendering | `lib/cinematic/render.py` | ✅ Complete |
| CAP-RENDER-06 | Color pipeline (AgX, LUT, exposure lock) | `lib/cinematic/color.py` | ✅ Complete |

---

## Animation (CAP-ANIM)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-ANIM-01 | Camera orbit animation | `lib/cinematic/animation.py` | ✅ Complete |
| CAP-ANIM-02 | Dolly/crane movements | `lib/cinematic/animation.py` | ✅ Complete |
| CAP-ANIM-03 | Turntable rotation | `lib/cinematic/animation.py` | ✅ Complete |
| CAP-ANIM-04 | Procedural motion paths (Bezier) | `lib/cinematic/motion_path.py` | ✅ Complete |
| CAP-ANIM-05 | Easing functions | `lib/cinematic/animation.py` | ✅ Complete |
| CAP-ANIM-06 | Rack focus | `lib/cinematic/animation.py` | ✅ Complete |
| CAP-ANIM-07 | Geometry morphing | `lib/morphing/` | ✅ Complete |
| CAP-ANIM-08 | Material morphing | `lib/morphing/` | ✅ Complete |
| CAP-ANIM-09 | Color morphing (LAB interpolation) | `lib/morphing/` | ✅ Complete |

---

## Tracking/Motion (CAP-TRACK)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-TRACK-01 | Point tracking | Planned - Phase 7.1 | 📋 Planned |
| CAP-TRACK-02 | Camera solving | Planned - Phase 7.1 | 📋 Planned |
| CAP-TRACK-03 | Object tracking | Planned - Phase 7.5 | 📋 Planned |
| CAP-TRACK-04 | LiDAR/scan import | Planned - Phase 7.5 | 📋 Planned |
| CAP-TRACK-05 | Motion capture import | Planned - Phase 7.5 | 📋 Planned |

---

## Compositing (CAP-COMP)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-COMP-01 | Compositor node setup | `lib/cinematic/lenses.py` | ✅ Complete |
| CAP-COMP-02 | Lens effects pipeline | `lib/cinematic/lenses.py` | ✅ Complete |
| CAP-COMP-03 | LUT application | `lib/cinematic/color.py` | ✅ Complete |
| CAP-COMP-04 | Multi-camera composite | `lib/cinematic/rigs.py` | ✅ Complete |

---

## Import/Export (CAP-IO)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-IO-01 | YAML preset loading | `lib/cinematic/preset_loader.py` | ✅ Complete |
| CAP-IO-02 | YAML state persistence | `lib/cinematic/state_manager.py` | ✅ Complete |
| CAP-IO-03 | FBX camera import | Planned - Phase 7.3 | 📋 Planned |
| CAP-IO-04 | Alembic import | Planned - Phase 7.3 | 📋 Planned |
| CAP-IO-05 | STL/GLTF/FBX/OBJ/USD export | `lib/exporters/` | ✅ Complete |

---

## Geometry Generation (CAP-GEN)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-GEN-01 | Knob profiles (9 types) | `lib/knobs/profiles/` | ✅ Complete |
| CAP-GEN-02 | Surface features (knurling, ribbing, grooves) | `lib/knobs/features/` | ✅ Complete |
| CAP-GEN-03 | Fader geometry | `lib/faders/` | ✅ Complete |
| CAP-GEN-04 | Button geometry | `lib/buttons/` | ✅ Complete |
| CAP-GEN-05 | LED/indicator geometry | `lib/leds/` | ✅ Complete |
| CAP-GEN-06 | Panel geometry | `lib/panels/` | ✅ Complete |
| CAP-GEN-07 | Geometry nodes pipeline | `lib/pipeline.py` | ✅ Complete |
| CAP-GEN-08 | Universal Stage Order (5-stage pipeline) | `lib/pipeline.py` | ✅ Complete |

---

## Materials/Shaders (CAP-MAT)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-MAT-01 | PBR material system | `lib/materials/` | ✅ Complete |
| CAP-MAT-02 | Debug material system | `lib/nodekit.py` | ✅ Complete |
| CAP-MAT-03 | Color system with semantic tokens | `lib/colors/` | ✅ Complete |
| CAP-MAT-04 | Style presets (Neve, SSL, API, Moog, etc.) | `configs/styles/` | ✅ Complete |
| CAP-MAT-05 | Emissive materials | `lib/materials/` | ✅ Complete |

---

## Control Surfaces (CAP-CTRL)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-CTRL-01 | Parameter hierarchy | `lib/params/` | ✅ Complete |
| CAP-CTRL-02 | YAML preset system | `lib/preset_loader.py` | ✅ Complete |
| CAP-CTRL-03 | Style presets | `configs/styles/` | ✅ Complete |
| CAP-CTRL-04 | Geometry profiles | `lib/knobs/profiles/` | ✅ Complete |
| CAP-CTRL-05 | Morphing engine | `lib/morphing/` | ✅ Complete |

---

## Scene Management (CAP-SCENE)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-SCENE-01 | Scene reset | `lib/scene_ops.py` | ✅ Complete |
| CAP-SCENE-02 | Collection management | `lib/scene_ops.py` | ✅ Complete |
| CAP-SCENE-03 | Frame state capture | `lib/cinematic/types.py` (FrameState) | ✅ Complete |
| CAP-SCENE-04 | Shot state persistence | `lib/cinematic/state_manager.py` | ✅ Complete |
| CAP-SCENE-05 | Shot variation/shuffling | `lib/cinematic/types.py` (ShuffleConfig) | ✅ Complete |

---

## Projection/Anamorphic (CAP-PROJ) 🆕

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-PROJ-01 | Anamorphic image projection | NOT STARTED | 🚫 Blocked |
| CAP-PROJ-02 | Camera frustum projection | NOT STARTED | 🚫 Blocked |
| CAP-PROJ-03 | Surface projection baking | NOT STARTED | 🚫 Blocked |
| CAP-PROJ-04 | Multi-viewpoint anamorphic | NOT STARTED | 🚫 Blocked |
| CAP-PROJ-05 | Visibility by camera position | NOT STARTED | 🚫 Blocked |
| CAP-PROJ-06 | Projection onto arbitrary geometry | NOT STARTED | 🚫 Blocked |

---

## Retro Graphics (CAP-RETRO)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-RETRO-01 | Pixel converter | Planned - Phase 13.1 | 📋 Planned |
| CAP-RETRO-02 | Dither engine (Bayer, Floyd-Steinberg, Atkinson) | Planned - Phase 13.2 | 📋 Planned |
| CAP-RETRO-03 | Isometric view | Planned - Phase 13.3 | 📋 Planned |
| CAP-RETRO-04 | Side-scroller mode | Planned - Phase 13.3 | 📋 Planned |
| CAP-RETRO-05 | CRT effects | Planned - Phase 13.4 | 📋 Planned |
| CAP-RETRO-06 | Color palettes (NES, SNES, Game Boy, etc.) | Planned - Phase 13.1 | 📋 Planned |

---

## Follow Camera (CAP-FOLLOW)

| ID | Capability | Module | Status |
|----|------------|--------|--------|
| CAP-FOLLOW-01 | Side-scroller camera | Planned - Phase 8.1 | 📋 Planned |
| CAP-FOLLOW-02 | Over-shoulder camera | Planned - Phase 8.1 | 📋 Planned |
| CAP-FOLLOW-03 | Chase camera | Planned - Phase 8.1 | 📋 Planned |
| CAP-FOLLOW-04 | Obstacle avoidance | Planned - Phase 8.2 | 📋 Planned |
| CAP-FOLLOW-05 | Pre-solve system | Planned - Phase 8.3 | 📋 Planned |

---

## Summary Statistics

| Category | Complete | Planned | Blocked |
|----------|----------|---------|---------|
| Camera | 10 | 0 | 0 |
| Lighting | 7 | 0 | 0 |
| Environment | 5 | 0 | 0 |
| Rendering | 6 | 0 | 0 |
| Animation | 9 | 0 | 0 |
| Tracking | 0 | 5 | 0 |
| Compositing | 4 | 0 | 0 |
| Import/Export | 2 | 3 | 0 |
| Geometry | 8 | 0 | 0 |
| Materials | 5 | 0 | 0 |
| Control Surfaces | 5 | 0 | 0 |
| Scene Management | 5 | 0 | 0 |
| **Projection** | **0** | **0** | **6** |
| Retro Graphics | 0 | 6 | 0 |
| Follow Camera | 0 | 5 | 0 |
| **TOTAL** | **66** | **19** | **6** |

---

## Adding New Capabilities

When adding a new capability:

1. **Check this document first** - Search for similar functionality
2. **Assign a unique ID** - Use prefix from category table
3. **Document the module** - Where is the implementation?
4. **Update status** - ✅ Complete, 📋 Planned, 🚫 Blocked, 🔄 In Progress

```markdown
| CAP-XXX-NN | Description | `lib/module.py` | ✅ Complete |
```

---

*This document is the single source of truth for what the system can do.*
