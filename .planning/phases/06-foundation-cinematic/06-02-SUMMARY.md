---
phase: 06-foundation-cinematic
plan: 02
subsystem: cinematic-config
completed: 2026-02-18
duration: 8 minutes
tags:
  - yaml
  - configuration
  - presets
  - cinematic
  - camera
  - lighting
  - color
  - animation
  - render
requires:
  - 06-01 (cinematic module foundation)
provides:
  - Complete cinematic configuration directory structure
  - 21 YAML preset files for cinematic system
  - Base shot template inheritance system
affects:
  - 06-03+ (all subsequent cinematic phases will use these presets)
tech_stack:
  added: []
  patterns:
    - yaml-configuration
    - preset-system
    - template-inheritance
key_files:
  created:
    - configs/cinematic/cameras/lens_presets.yaml
    - configs/cinematic/cameras/sensor_presets.yaml
    - configs/cinematic/cameras/rig_presets.yaml
    - configs/cinematic/cameras/imperfection_presets.yaml
    - configs/cinematic/lighting/rig_presets.yaml
    - configs/cinematic/lighting/gel_presets.yaml
    - configs/cinematic/lighting/hdri_presets.yaml
    - configs/cinematic/backdrops/infinite_curves.yaml
    - configs/cinematic/backdrops/gradients.yaml
    - configs/cinematic/backdrops/environments.yaml
    - configs/cinematic/color/technical_luts.yaml
    - configs/cinematic/color/film_luts.yaml
    - configs/cinematic/color/creative_luts.yaml
    - configs/cinematic/color/color_management_presets.yaml
    - configs/cinematic/animation/camera_moves.yaml
    - configs/cinematic/animation/easing_curves.yaml
    - configs/cinematic/render/quality_profiles.yaml
    - configs/cinematic/render/pass_presets.yaml
    - configs/cinematic/shots/base/base_product.yaml
    - configs/cinematic/shots/base/base_hero.yaml
    - configs/cinematic/shots/base/base_turntable.yaml
  modified: []
---

# Phase 06 Plan 02: Cinematic Configuration Directory Structure

## Summary

Created the complete configuration directory structure for the cinematic rendering system. This establishes all preset files that will be loaded by cinematic modules in subsequent phases.

**One-liner:** 21 YAML preset files across 7 subdirectories defining cameras, lighting, backdrops, color, animation, render, and shot templates.

## Tasks Completed

| Task | Description | Commit | Status |
|------|-------------|--------|--------|
| 1 | Camera configuration presets | e08f548 | DONE |
| 2 | Lighting configuration presets | 5308ccc | DONE |
| 3 | Backdrop configuration presets | efea83a | DONE |
| 4 | Color configuration presets | f41965a | DONE |
| 5 | Animation configuration presets | 8930e9b | DONE |
| 6 | Render configuration presets | 4c007e3 | DONE |
| 7 | Base shot template files | 18a4339 | DONE |

## Configuration Structure

```
configs/cinematic/
├── cameras/
│   ├── lens_presets.yaml          # 8 lens configurations
│   ├── sensor_presets.yaml        # 6 sensor formats
│   ├── rig_presets.yaml           # 7 camera rig types
│   └── imperfection_presets.yaml  # 4 lens character profiles
├── lighting/
│   ├── rig_presets.yaml           # 8 lighting rigs
│   ├── gel_presets.yaml           # 17 gels (CTO/CTB, diffusion, creative)
│   └── hdri_presets.yaml          # 9 HDRI environments
├── backdrops/
│   ├── infinite_curves.yaml       # 7 cyclorama presets
│   ├── gradients.yaml             # 10 procedural gradients
│   └── environments.yaml          # 11 environment presets
├── color/
│   ├── technical_luts.yaml        # 7 technical LUTs
│   ├── film_luts.yaml             # 7 film stock emulations
│   ├── creative_luts.yaml         # 14 creative grades
│   └── color_management_presets.yaml  # 8 view transforms
├── animation/
│   ├── camera_moves.yaml          # 16 camera move types
│   └── easing_curves.yaml         # 18 easing functions
├── render/
│   ├── quality_profiles.yaml      # 5 render tiers
│   └── pass_presets.yaml          # 7 pass groups
└── shots/
    └── base/
        ├── base_product.yaml      # Abstract product template
        ├── base_hero.yaml         # Abstract hero template
        └── base_turntable.yaml    # Abstract turntable template
```

## Key Configuration Details

### Camera Presets
- **Lenses:** 14mm ultra-wide to 135mm telephoto, plus 90mm macro and vintage Helios 44-2
- **Sensors:** Full frame, APS-C, MFT, Super 35, RED Monstro, ARRI Alexa LF
- **Rigs:** Tripod, dolly, crane, steadicam, drone configurations
- **Imperfections:** Cooke S4, ARRI Master Prime, vintage Helios character profiles

### Lighting Presets
- **Rigs:** Three-point soft/hard, product hero/dramatic, studio high/low key, console overhead, mixer angle
- **Gels:** CTO/CTB (full/half/quarter), diffusion grades, creative colors
- **HDRI:** Studio bright/soft, overcast day, golden hour, night city, product HDRIs

### Color Management
- **Technical LUTs:** Rec709, sRGB, DCI-P3, ACEScg, linear-to-log
- **Film LUTs:** Kodak 2383/5219, Fuji 3510/400, Portra 400, Cineon
- **Creative LUTs:** Teal/orange, bleach bypass, product clean/vibrant/luxury, mood looks
- **View Transforms:** AgX (default/product/dramatic), ACEScg, Filmic, Raw

### Render Profiles
- **Tiers:** Viewport capture, EEVEE draft, Cycles preview, Cycles production, Cycles archive
- **CRITICAL:** Uses `BLENDER_EEVEE_NEXT` (not deprecated `BLENDER_EEVEE`)
- **Passes:** Beauty, data (depth, normal, vector), material, cryptomatte, full production

### Shot Templates
- All base templates marked `abstract: true` to prevent direct rendering
- Designed for template inheritance pattern (extends mechanism)

## Decisions Made

1. **EEVEE Next Engine:** Used `BLENDER_EEVEE_NEXT` identifier for Blender 5.x compatibility (deprecated `BLENDER_EEVEE`)

2. **Template Inheritance:** Base shot templates use `abstract: true` flag to enforce they cannot be rendered directly - must be extended

3. **Resolution Scaling:** Draft tier uses 50% scale for speed, production/archive use 100%

4. **Adaptive Sampling:** Enabled for all Cycles tiers with tier-appropriate thresholds

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None required for this plan (configuration file creation only).

## Next Phase Readiness

**Ready for:** 06-03 Camera System Implementation

**Dependencies Met:**
- Configuration directory structure complete
- All preset files in place for camera module to load
- Shot template inheritance pattern established

**Blockers:** None

## Verification

- [x] 21 YAML files created
- [x] 7 subdirectories exist
- [x] All base templates have `abstract: true`
- [x] All YAML files syntactically valid
- [x] lens_presets has 8 lenses
- [x] sensor_presets has 6 sensors
- [x] rig_presets has 8+ lighting rigs
- [x] quality_profiles has all 5 tiers
- [x] color_management_presets has agx_default
