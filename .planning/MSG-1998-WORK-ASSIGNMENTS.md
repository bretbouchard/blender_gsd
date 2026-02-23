# MSG 1998 - Blender GSD Work Assignments

**Created:** 2026-02-22
**Source:** FDX GSD Phase 8 Planning + Council of Ricks Review
**Status:** READY FOR EXECUTION
**Updated:** 2026-02-22 — All Critical Issues Resolved

---

## Executive Summary

This document consolidates all work assignments from FDX GSD planning for the Blender team. It includes:

1. **20 Locations to Build** (from FDX 08-LOCATIONS.md)
2. **4 VFX Pipelines to Develop** (from FDX 08-TECH-GAPS.md)
3. **10 Execution Plans** (from FDX 08-PLAN.md)
4. **Council of Ricks Findings** (ALL CRITICAL ISSUES RESOLVED ✅)

---

## Council of Ricks - Critical Issues Status

### ✅ ALL CRITICAL ISSUES RESOLVED

| # | Issue | Status | Resolution |
|---|-------|--------|------------|
| 1 | Vision3 500T reference WRONG | ✅ RESOLVED | Kodak 5279/5289 documented in 12-MSG-RESEARCH.md |
| 2 | Meshroom CUDA dependency | ✅ RESOLVED | Colmap + cloud fallback documented in 08-TECH-GAPS.md |
| 3 | Render pass specs incomplete | ✅ RESOLVED | Full specs: format, bit depth, color space added |
| 4 | fSpy import workflow undocumented | ✅ RESOLVED | 7-stage camera calibration workflow documented |

**See FDX GSD `08-TECH-GAPS.md` for complete documentation.**

---

## Phase 9.MSG: Location Building Assignments

### Location Prioritization (from Council Review)

**Tier 1 (MVP) - 5 Locations:**
| LOC-ID | Name | Method | Hours | Priority |
|--------|------|--------|-------|----------|
| LOC-02 | MSG Exterior | Meshroom + fSpy | 12 | P0 |
| LOC-03 | MSG Interior/Lobby | fSpy + reference | 10 | P0 |
| LOC-04 | MSG Seating Bowl | Reference + modeling | 16 | P0 |
| LOC-05 | MSG Exit Stairwell | Procedural | 6 | P0 |
| LOC-06 | 31st Street | Meshroom + fSpy | 10 | P0 |

**Tier 2 (v1.0) - 8 Locations:**
| LOC-ID | Name | Method | Hours | Priority |
|--------|------|--------|-------|----------|
| LOC-01 | Highway into NYC | HDRI + CG | 8 | P1 |
| LOC-07 | 8th Avenue | Meshroom + fSpy | 12 | P1 |
| LOC-08 | Phish Bus Interior | Reference + modeling | 8 | P1 |
| LOC-09 | Subway Platform | fSpy + reference | 10 | P1 |
| LOC-10 | Subway Car Interior | Reference + modeling | 8 | P1 |
| LOC-11 | Restaurant Interior | fSpy + reference | 10 | P1 |
| LOC-12 | Parking Garage | Meshroom + fSpy | 8 | P1 |
| LOC-13 | Hospital Exterior | Meshroom + fSpy | 6 | P1 |

**Tier 3 (v2.0) - 7 Locations:**
| LOC-ID | Name | Method | Hours | Priority |
|--------|------|--------|-------|----------|
| LOC-14 | Hospital Interior | Reference + modeling | 12 | P2 |
| LOC-15 | Hospital Room | Reference + modeling | 8 | P2 |
| LOC-16 | Parents' Car Interior | Reference + modeling | 6 | P2 |
| LOC-17 | Highway Night | fSpy + reference | 6 | P2 |
| LOC-18 | Childhood Home | Reference + modeling | 8 | P2 |
| LOC-19 | Friend's Living Room | Reference + modeling | 6 | P2 |
| LOC-20 | Car Home | Reference + modeling | 4 | P2 |

**Total Hours:** 168 hours across all 20 locations

---

## VFX Pipeline Assignments

### VFX Categories (from FDX 08-TECH-GAPS.md)

| VFX Type | Scenes | Tools | Hours | Status |
|----------|--------|-------|-------|--------|
| Body Horror (flesh melting) | LOC-13 (Stoop) | Blender fluid sim + shader | 16 | Research Complete |
| Negative Man Effect | LOC-11 (Parking Lot) | DaVinci Invert OFX | 8 | Research Complete |
| Permtrails/Echo | LOC-05, LOC-07 | AE Echo, Blender plugin | 10 | Research Complete |
| Light Trails (glowsticks) | LOC-03, LOC-04 | Light Trails Generator | 12 | Research Complete |

### VFX by Scene Intensity

| Scene | VFX | Intensity | Notes |
|-------|-----|-----------|-------|
| SC-04/05 MSG Concert | Light trails | Heavy | Glowstick war |
| SC-06 Stairwell Run | Permtrails | Medium | Motion trails |
| SC-07 Street Panic | Permtrails, Negative Man | Heavy | Sensory overload |
| SC-08/09 Busboy Chase | Body horror | Extreme | Flesh falling off hands |
| SC-10/12 Subway | Permtrails | Medium | Running sequences |
| SC-11 "Albany" Lot | Negative Man | Heavy | Pure black void man |
| SC-13/14 Hospital | Negative Man | Subtle | Residual effect |

---

## Phase 12.MSG: SD Compositing Assignments

### Render Pass Requirements (✅ COMPLETE SPECS)

**All render pass specifications now documented with bit depth, format, and color space:**

| Pass | Format | Bit Depth | Color Space | Purpose |
|------|--------|-----------|-------------|---------|
| **Beauty** | OpenEXR | 32-bit float | ACEScg | Final color composite |
| **Depth (Z)** | OpenEXR | 32-bit float | Linear | ControlNet Depth, DOF |
| **Normal** | OpenEXR | 16-bit float | Linear | ControlNet Normal |
| **Diffuse** | OpenEXR | 16-bit float | ACEScg | Color grading isolation |
| **Specular** | OpenEXR | 16-bit float | ACEScg | Highlight control |
| **Cryptomatte** | OpenEXR MultiLayer | 32-bit float | Raw | Object/Material isolation |

**Blender Python Setup:**
```python
# See 08-TECH-GAPS.md for complete script
bpy.context.scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
bpy.context.scene.render.image_settings.color_depth = '32'
bpy.context.scene.view_settings.view_transform = 'ACEScg'
```

**ControlNet Compatibility:**
| Model | Required Pass | Pre-processing |
|-------|---------------|----------------|
| Depth (v11f1p) | Depth.Z | Normalize 0-1, invert |
| Normal (v11p) | Normal | Already correct format |
| Canny (v11p) | Combined | Edge detection |

### Layer System (BG/MG/FG)

Each location must be rendered with layer separation:

```
Collection Structure:
├── BG (Background) → View Layer 1
│   └── Sky, distant buildings, environment
├── MG (Midground) → View Layer 2
│   └── Main subject, hero elements
├── FG (Foreground) → View Layer 3
│   └── Close elements, atmospheric FX
└── FX (Effects) → View Layer 4
    └── Particles, light effects
```

---

## Execution Plan from FDX

### PLAN-4: 3D Location Building (Blender Team)

**Dependencies:** PLAN-2 (reference collection), PLAN-3 (photo capture)

**Blender Standards:**
- Collections: BG / MG / FG / FX
- Render Layers per collection
- Z-depth pass enabled
- Normal pass enabled
- Naming: `LOC-{NN}_{description}_{element}`

**Verification:**
- [ ] All 20 locations modeled
- [ ] Render layers properly separated
- [ ] Depth/Normal passes export correctly
- [ ] fSpy camera matches reference photos

### PLAN-5: VFX Development (VFX Team)

**Deliverables:**
| ID | VFX Type | Deliverable | Hours |
|----|----------|-------------|-------|
| 5.1 | Body Horror - Flesh Melting | Blender fluid sim + shader | 16 |
| 5.2 | Body Horror - Skin Peeling | Procedural displacement | 12 |
| 5.3 | Negative Man - Full Effect | DaVinci node tree | 8 |
| 5.4 | Negative Man - Partial | Subtle version | 4 |
| 5.5 | Permtrails - Echo Effect | AE preset | 6 |
| 5.6 | Permtrails - Heavy | Intense version | 4 |
| 5.7 | Light Trails - Glowsticks | Blender + composite | 8 |
| 5.8 | Light Trails - Crowd War | Massive glowstick scene | 12 |

### PLAN-6: SD Pipeline Development (SD Team)

**Deliverables:**
| ID | Task | Deliverable | Hours |
|----|------|-------------|-------|
| 6.1 | ComfyUI workflow template | .json workflow file | 4 |
| 6.2 | Depth ControlNet integration | Verified pipeline | 3 |
| 6.3 | Normal ControlNet integration | Verified pipeline | 3 |
| 6.4 | Seed management script | Python + JSON system | 4 |
| 6.5 | 1998 style prompt library | Prompt templates | 4 |

### PLAN-8: Test Shot Production

**Test Shot Criteria:**
- Location: LOC-11 Restaurant
- Scene: SC-08 Busboy Chase
- VFX: Body horror (flesh falling off hands)
- Duration: 5 seconds (150 frames)

**Tasks:**
| ID | Task | Deliverable | Hours |
|----|------|-------------|-------|
| 8.2 | Build Blender scene | LOC-11 restaurant + character | 8 |
| 8.3 | Render layers | EXR MultiLayer output | 4 |
| 8.4 | Generate depth/normal maps | ControlNet inputs | 2 |
| 8.5 | SD generation | Style transfer | 4 |
| 8.6 | VFX application | Body horror effect | 4 |
| 8.7 | Compositing | DaVinci Fusion | 4 |
| 8.8 | Color grading | 1998 film look | 2 |

---

## 1998 Film Aesthetic Specifications

### Film Stock (CORRECTED)

**PRIMARY:** Kodak Vision 500T 5279 (1996-2002 era)
**NOT:** Kodak Vision3 500T 5219 (introduced 2007 - WRONG)

### Color Grading Parameters

```python
FILM_STOCK_5279_SPEC = {
    "grain": {
        "intensity": "0.8-1.2%",
        "pattern": "35mm organic",
        "tool": "FilmConvert Pro 35mm, 15-20% blend"
    },
    "halation": {
        "threshold": "85-90% luminance",
        "intensity": "Moderate",
        "blend": "30-40%"
    },
    "color": {
        "shadow_response": "Warm bias",
        "highlight_handling": "Softer roll-off",
        "skin_tones": "Slightly golden"
    }
}

# Scene-specific color
HOSPITAL_LOOK = {
    "color_temp": 5000,  # Kelvin
    "tint": "+5 green (fluorescent)",
    "saturation": 0.80,
    "description": "Sterile, clinical, slightly sickly"
}

ACID_TRIP_STAGES = {
    "onset": {"saturation": "1.0 → 1.3"},
    "peak": {"saturation": "1.5 → 2.0", "hue_rotation": "+15 to +30"},
    "void": {"saturation": 0.3, "contrast": -0.3},
    "recovery": {"saturation": "0.8 → 1.0", "warmth": "4500K → 3200K"}
}
```

---

## Period Accuracy Checklist (from Research Rick)

### Must Address Before Production

| Category | Item | Status |
|----------|------|--------|
| Drug form | Specify blotter paper (not liquid) | ⚠️ Needed in script |
| Hospital | Research 1998 ER procedures | ⚠️ Research needed |
| Signage | Compile NYC 1998 billboard reference | ⚠️ Research needed |

### 1998 Period Rules

- **NO** LED screens/billboards (use printed/illuminated signs)
- **NO** smartphones, modern electronics
- **NO** cars post-1998
- **YES** pay phones, newspaper boxes
- **YES** period traffic signals
- **YES** 1998 fashion (JNCO jeans, platform shoes, etc.)

---

## Pipeline Technical Requirements

### ✅ AMD Fallback (RESOLVED)

Meshroom requires NVIDIA CUDA. Full fallback options now documented:

```yaml
Primary: Meshroom (CUDA, fastest)
Fallback Options:
  1. Colmap (FREE, CPU/GPU, open-source)
     colmap automatic_reconstructor --workspace_path ./workspace --image_path ./photos
  2. Polycam Web (cloud, freemium)
  3. Luma AI (cloud, high quality)
  4. RunPod + Meshroom (cloud GPU rental ~$0.50/hr)

GPU Recommendation:
  - NVIDIA RTX/GTX → Use Meshroom (fastest)
  - AMD Radeon → Use Colmap CPU mode or Cloud
```

**See FDX 08-TECH-GAPS.md Section 1.2 for complete Colmap workflow.**

### ✅ fSpy Workflow (RESOLVED)

**7-Stage Camera Calibration Pipeline:**

| Stage | Task | Output |
|-------|------|--------|
| 1 | Photo Capture | 12MP+ with clear parallel lines |
| 2 | fSpy Calibration | Define 3 vanishing points + reference distance |
| 3 | Export | .fspy file + camera JSON |
| 4 | Blender Import | Camera object with matched position/rotation |
| 5 | Validation | Compare test geometry to photo (<5% tolerance) |
| 6 | Multi-Angle | Import additional views per location |
| 7 | Handoff | Camera export JSON for modelers |

**Tolerance Specifications:**
| Element | Acceptable | Impact if Exceeded |
|---------|------------|-------------------|
| Position | ±0.5m | Parallax errors |
| Rotation | ±2° | Horizon misalignment |
| Focal Length | ±3mm | Perspective distortion |
| Scale | ±5% | Object size mismatch |

**See FDX 08-TECH-GAPS.md Section 1.1 for complete 7-stage workflow.**

### Depth Map Encoding (HIGH)

Standardize depth encoding:

```yaml
depth_map_encoding:
  standard: "linear_normalized"
  range: { near: 0.0, far: 1.0 }
  formula: "depth_ndc = (z_world - near_clip) / (far_clip - near_clip)"
```

---

## Resource Requirements

### Team Assignments

| Role | Count | Phases |
|------|-------|--------|
| 3D Artist | 2 | PLAN-4, PLAN-8, PLAN-9 |
| VFX Artist | 1 | PLAN-5, PLAN-8, PLAN-9 |
| SD Operator | 1 | PLAN-6, PLAN-8, PLAN-9 |
| Compositor | 1 | PLAN-8, PLAN-9, PLAN-10 |

### Hardware Requirements

| Resource | Purpose | Qty |
|----------|---------|-----|
| Workstation (RTX 4090) | SD, Rendering | 2 |
| Workstation (RTX 3070) | Blender, Meshroom | 2 |
| NAS Storage | Asset storage | 10TB |
| Cloud GPU | Overflow/AMD fallback | As needed |

---

## Timeline

| Phase | Hours | Weeks (40hr) |
|-------|-------|--------------|
| PLAN-4: 3D Locations | 168 | 4.2 |
| PLAN-5: VFX Development | 80 | 2.0 |
| PLAN-6: SD Pipeline | 30 | 0.8 |
| PLAN-8: Test Shot | 31 | 0.8 |
| PLAN-9: Production | 180 | 4.5 |
| **TOTAL** | **489** | **12.2** |

---

## Handoff Protocol

### From FDX GSD

```bash
# FDX generates handoff
gsd handoff blender --scene SCN-002 --output handoff/
gsd handoff sd --scene SCN-002 --output handoff/
```

### Receive in Blender GSD

```bash
# Blender receives handoff
blender-gsd receive-handoff --from-fdx --scene SCN-002

# Build location
blender-gsd build-location LOC-002 --from-fspy

# Render passes
blender-gsd render-location LOC-002 --passes all

# Composite with SD
blender-gsd composite --shot SHOT-002-001 --with-sd

# Export for editorial
blender-gsd export-editorial --shot SHOT-002-001 --format prores
```

---

## Next Actions

### ✅ Completed (Council Critical Issues)

1. [x] Document fSpy → Blender workflow → See FDX 08-TECH-GAPS.md Section 1.1
2. [x] Add Colmap as AMD fallback → See FDX 08-TECH-GAPS.md Section 1.2
3. [x] Complete render pass export specs → See FDX 08-TECH-GAPS.md Section 2.3
4. [x] Fix film stock reference → Kodak 5279 documented in 12-MSG-RESEARCH.md

### Immediate (Before Production)

1. [ ] Research hospital ER 1998 procedures
2. [ ] Compile NYC 1998 signage reference
3. [ ] Gather Phish MSG 1998 concert reference (photos/video)

### Week 1-2 (Foundation)

1. [ ] Set up fSpy + Meshroom pipeline
2. [ ] Configure ComfyUI with ControlNet
3. [ ] Create Blender render layer templates
4. [ ] Begin Tier 1 location building

### ✅ Week 3-4 (VFX Development) — COMPLETED

1. [x] Build Negative Man node tree (DaVinci) → See FDX vfx/negative_man/
2. [x] Create permtrails Echo preset (AE) → See FDX vfx/permtrails/permtrails_ae_preset.jsx
3. [x] Test Light Trails Generator (Blender) → See FDX vfx/light_trails/
4. [x] Body horror effect prototypes → See FDX vfx/body_horror/flesh_melt_shader.py
5. [x] 1998 Film Grade PowerGrade → See FDX vfx/film_grade/msg1998_powergrade_config.py
6. [x] VFX Verification Checklist → See FDX vfx/verification/VFX_VERIFICATION_CHECKLIST.md

---

## VFX Development Assets (PLAN-5 Complete)

### Files Created in FDX GSD

| File | Purpose | Location |
|------|---------|----------|
| VFX_DEVELOPMENT_GUIDE.md | Complete VFX documentation | vfx/ |
| VFX_VERIFICATION_CHECKLIST.md | QA checklist for all effects | vfx/verification/ |
| msg1998_powergrade_config.py | DaVinci PowerGrade generator | vfx/film_grade/ |
| flesh_melt_shader.py | Blender shader setup | vfx/body_horror/ |
| permtrails_ae_preset.jsx | After Effects preset | vfx/permtrails/ |

### VFX Pipeline Status

| VFX Category | Documentation | Preset/Script | Status |
|--------------|---------------|---------------|--------|
| Body Horror (Flesh Melt) | ✅ Complete | ✅ Blender shader | Ready |
| Body Horror (Skin Peel) | ✅ Complete | ✅ Blender shader | Ready |
| Body Horror (Rewind) | ✅ Complete | ⏳ Blender time remap | Pending |
| Negative Man | ✅ Complete | ✅ DaVinci PowerGrade | Ready |
| Permtrails | ✅ Complete | ✅ AE preset + DaVinci | Ready |
| Light Trails | ✅ Complete | ✅ Blender shader | Ready |
| Crowd Glow | ✅ Complete | ✅ DaVinci PowerGrade | Ready |
| 1998 Film Grade | ✅ Complete | ✅ DaVinci PowerGrade | Ready |

---

**Document Status:** PLAN-5 & PLAN-6 Complete — VFX + SD Development Finished
**Dependencies:** FDX GSD Phase 8 (Source of Truth)
**Last Updated:** 2026-02-22
**Version:** 4.0 — VFX + SD Pipeline Complete

---

## SD Pipeline Assets (PLAN-6 Complete)

### Files Created in FDX GSD

| File | Purpose | Location |
|------|---------|----------|
| SD_PIPELINE_GUIDE.md | Complete SD specifications | sd_pipeline/ |
| seed_manager.py | Deterministic seed generation | sd_pipeline/scripts/ |
| batch_generate.py | Multi-shot batch processing | sd_pipeline/scripts/ |
| MSG1998_PROMPT_LIBRARY.json | Scene-specific prompts | sd_pipeline/prompts/ |
| SD_VERIFICATION_CHECKLIST.md | QA checklist | sd_pipeline/verification/ |

### SD Pipeline Status

| Component | Documentation | Script/Config | Status |
|-----------|---------------|---------------|--------|
| ComfyUI Workflow | ✅ Complete | ✅ JSON template | Ready |
| Depth ControlNet | ✅ Complete | ✅ Pre-processing | Ready |
| Normal ControlNet | ✅ Complete | ✅ Pre-processing | Ready |
| Seed Management | ✅ Complete | ✅ Python script | Ready |
| Prompt Library | ✅ Complete | ✅ JSON config | Ready |
| Batch Generation | ✅ Complete | ✅ Python script | Ready |
| 1998 Style | ✅ Complete | ✅ Prompts defined | Ready |
