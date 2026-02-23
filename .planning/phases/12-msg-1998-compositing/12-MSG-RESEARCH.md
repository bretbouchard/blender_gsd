# RESEARCH: MSG 1998 SD Compositing Pipeline

**Phase:** 12.MSG (MSG 1998 Compositing)
**Created:** 2026-02-22
**Status:** Planning
**Input:** Phase 9.MSG (Location renders) + FDX GSD (SD configs)
**Output:** Final composited shots for editorial

---

## Overview

This phase handles the **Stable Diffusion compositing pipeline** for MSG 1998, combining:
- 3D renders from Blender (Phase 9.MSG)
- SD style transfer with ControlNet
- Depth/normal guided generation
- Layer-based compositing

**Core Principle:** Film-first approach. SD enhances, doesn't replace.

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FDX GSD                                │
│                                                             │
│  SD Configuration per shot:                                │
│  • Seeds (deterministic regeneration)                      │
│  • Prompts (1998 film aesthetic)                           │
│  • ControlNet specs (depth, normal)                        │
│  • Layer separation (BG, MG, FG)                           │
│                                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ gsd handoff sd --scene SCN-XXX
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 9.MSG (Location Building)                │
│                                                             │
│  3D Renders with passes:                                   │
│  • Beauty, Depth, Normal                                   │
│  • Object ID, Shadow, AO                                   │
│  • Cryptomatte for isolation                               │
│                                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ blender-gsd export-compositing
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 12.MSG (SD COMPOSITING)                  │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 3D Renders  │  │ SD Config   │  │   Output    │        │
│  │ (ControlNet │  │ (from FDX)  │  │ (Composite) │        │
│  │   inputs)   │  │             │  │             │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │               │
│         └────────────────┼────────────────┘               │
│                          ▼                                 │
│              ┌─────────────────────┐                      │
│              │   STABLE DIFFUSION   │                      │
│              │   + CONTROLNET       │                      │
│              └─────────────────────┘                      │
│                          │                                 │
│                          ▼                                 │
│              ┌─────────────────────┐                      │
│              │  BLENDER COMPOSITOR │                      │
│              │  (Final composite)  │                      │
│              └─────────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ControlNet Pipeline

### Input Maps from Blender

| Map | Purpose | ControlNet Model |
|-----|---------|------------------|
| **Depth (Z)** | Structure preservation | control_v11f1p_sd15_depth |
| **Normal** | Surface orientation | control_v11p_sd15_normalbae |
| **Canny Edge** | Edge detection | control_v11p_sd15_canny |
| **Object ID** | Segmentation masks | (used for layer isolation) |

### ControlNet Configuration

```json
{
  "controlnet": {
    "depth": {
      "model": "control_v11f1p_sd15_depth",
      "weight": 1.0,
      "guidance_start": 0.0,
      "guidance_end": 1.0
    },
    "normal": {
      "model": "control_v11p_sd15_normalbae",
      "weight": 0.8,
      "guidance_start": 0.0,
      "guidance_end": 0.8
    }
  }
}
```

---

## 1998 Film Aesthetic

### Base Style Prompts

**Positive (Shared across all shots):**
```
1998 film stock, Kodak Vision 500T 5279,
35mm anamorphic lens, 2.39:1 aspect ratio,
film grain, organic texture, practical lighting,
period accurate 1998 New York City,
Matthew Libatique cinematography style,
handheld camera, documentary feel,
no digital artifacts, no modern elements
```

**⚠️ CRITICAL: Film Stock Accuracy**
- **CORRECT:** Kodak Vision 500T 5279 (1996-2002 era)
- **WRONG:** Kodak Vision3 500T 5219 (introduced 2007 - NOT period accurate)
- See FDX GSD 08-TECH-GAPS.md for full film stock specifications

**Negative (Shared across all shots):**
```
digital, clean, sharp, 4K, modern,
2020s, smartphones, LED screens,
CGI look, video game aesthetic,
over-processed, HDR, flat lighting,
anamorphic lens blur on edges,
modern cars, contemporary fashion
```

### Scene-Specific Modifiers

| Scene Type | Prompt Addition |
|------------|-----------------|
| MSG exterior | "Madison Square Garden exterior, daytime, establishing shot" |
| MSG interior | "arena concourse, fluorescent lighting, crowd" |
| Subway | "underground, tile walls, fluorescent, 1998 graffiti state" |
| Night exterior | "neon signs, wet pavement, streetlights, urban night" |
| Hospital | "fluorescent hospital lighting, sterile, clinical" |
| Apartment | "warm interior, cozy, golden hour through window" |

---

## Layer-Based Compositing

### Three-Layer System

```
┌─────────────────────────────────────────────────┐
│  FOREGROUND (Layer 3)                           │
│  • Characters (if composited separately)        │
│  • Close-up props                               │
│  • Atmospheric effects (rain, particles)        │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│  MIDGROUND (Layer 2)                            │
│  • Main subject/setting                         │
│  • Hero location elements                       │
│  • Interactive objects                          │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│  BACKGROUND (Layer 1)                           │
│  • Sky, distant buildings                       │
│  • Environment extensions                       │
│  • Atmospheric perspective                      │
└─────────────────────────────────────────────────┘
```

### Why Three Layers?

1. **Flexibility** - Each layer can be styled independently
2. **Consistency** - Foreground characters can share a seed
3. **Efficiency** - Background can be static across shots
4. **Control** - Adjust depth-of-field per layer

### Layer Seed Strategy

```json
{
  "shot_id": "SHOT-002-001",
  "layers": {
    "background": {
      "seed": 1234567890,
      "enabled": true,
      "prompt_suffix": "New York City skyline, MSG building, blue sky"
    },
    "midground": {
      "seed": 1234567891,
      "enabled": true,
      "prompt_suffix": "MSG building detail, street level activity"
    },
    "foreground": {
      "seed": 1234567892,
      "enabled": true,
      "prompt_suffix": "pedestrians in 1998 fashion, period cars"
    }
  }
}
```

---

## Compositing Workflow

### Step 1: Receive Inputs

```
From Phase 9.MSG:
- LOC-XXX_beauty.exr
- LOC-XXX_depth.exr
- LOC-XXX_normal.exr
- LOC-XXX_object_id.exr
- masks/LOC-XXX_bg_mask.png
- masks/LOC-XXX_mg_mask.png
- masks/LOC-XXX_fg_mask.png

From FDX GSD:
- sd_configs/SDCFG-XXX-XXX.json
```

### Step 2: SD Generation per Layer

```bash
# Generate background layer
sd-generate \
  --depth depth.exr \
  --mask masks/bg_mask.png \
  --config sd_configs/SDCFG-002-001.json \
  --layer background \
  --output layers/bg_sd.png

# Generate midground layer
sd-generate \
  --depth depth.exr \
  --normal normal.exr \
  --mask masks/mg_mask.png \
  --config sd_configs/SDCFG-002-001.json \
  --layer midground \
  --output layers/mg_sd.png

# Generate foreground layer
sd-generate \
  --depth depth.exr \
  --mask masks/fg_mask.png \
  --config sd_configs/SDCFG-002-001.json \
  --layer foreground \
  --output layers/fg_sd.png
```

### Step 3: Blender Composite

```python
# In Blender compositor
def composite_shot(shot_id):
    # Load layers
    bg_sd = load_image(f"layers/{shot_id}_bg_sd.png")
    mg_sd = load_image(f"layers/{shot_id}_mg_sd.png")
    fg_sd = load_image(f"layers/{shot_id}_fg_sd.png")

    # Load depth for DOF
    depth = load_render_pass("depth")

    # Combine with depth-based blending
    composite = alpha_over(bg_sd, mg_sd)
    composite = alpha_over(composite, fg_sd)

    # Apply film grain (1998 aesthetic)
    composite = apply_film_grain(composite, intensity=0.15)

    # Apply subtle lens distortion
    composite = apply_lens_distortion(composite, amount=0.02)

    # Color grade to match 1998 film stock
    composite = apply_color_grade(composite, lut="kodak_vision3_500t")

    return composite
```

### Step 4: Final Output

```
output/
├── SHOT-XXX-XXX_final.exr     # Master file (linear)
├── SHOT-XXX-XXX_final.png     # Preview
└── SHOT-XXX-XXX_final_prores.mov  # For editorial
```

---

## Period-Specific Post Processing

### 1998 Film Look

| Effect | Parameters | Purpose |
|--------|------------|---------|
| **Film Grain** | 0.10-0.20 intensity | Organic texture |
| **Lens Distortion** | 0.01-0.03 | Subtle barrel |
| **Chromatic Aberration** | 0.002-0.005 | Lens imperfection |
| **Vignette** | 0.3-0.5 | Focus attention |
| **Color Temperature** | Slightly warm | Film stock look |

### LUT Recommendations

- **Kodak Vision 500T 5279** - Primary look (1996-2002 era, NOT Vision3)
- **Print Film Emulation (Kodak 2383)** - For release print look
- **Bleach Bypass** - For specific scenes (optional)

**Period-Accurate 1998 Film Stocks:**
| Stock | Type | Notes |
|-------|------|-------|
| Kodak 5289/7289 | 500T | Pre-Vision3 tungsten |
| Kodak Vision 500T 5279 | 500T | Primary stock (1996-2002) |
| Fuji 8572 | 500T | Reala 500 alternative |

---

## Seed Management

### Deterministic Regeneration

**Rule:** Same seed + same prompt + same inputs = identical output

**Storage:** Seeds stored in FDX GSD, exported in handoff packages

**Verification:**
```bash
# Verify seed produces same output
sd-verify-seed \
  --seed 1234567890 \
  --config sd_configs/SDCFG-002-001.json \
  --reference outputs/SHOT-002-001_ref.png
```

### Seed Assignment Strategy

| Element | Seed Strategy |
|---------|---------------|
| Background sky | One seed per scene |
| Location architecture | One seed per location |
| Crowds | One seed per shot |
| Characters | Dedicated seed per character |
| Atmosphere | One seed per mood/time |

---

## CLI Commands (Planned)

```bash
# Receive SD config from FDX
blender-gsd receive-sd-config --from-fdx --scene SCN-002

# Generate SD layers
blender-gsd sd-generate --shot SHOT-002-001 --layers all

# Run full composite
blender-gsd composite --shot SHOT-002-001

# Batch process scene
blender-gsd batch-composite --scene SCN-002

# Verify output matches seed
blender-gsd verify-seed --shot SHOT-002-001

# Export for editorial
blender-gsd export-editorial --scene SCN-002 --format prores
```

---

## Quality Control

### Visual Review Checklist

- [ ] Period accuracy (no modern elements)
- [ ] Film grain visible but not excessive
- [ ] Color temperature matches 1998 film stock
- [ ] Layer edges invisible
- [ ] Depth consistency between layers
- [ ] No artifacts from SD generation

### Technical Validation

- [ ] Output resolution matches spec
- [ ] Frame rate correct (24fps)
- [ | Color space correct (ACES → Rec.709)
- [ ] Seed reproducibility verified

---

## Dependencies

### SD Models
- SDXL base 1.0
- ControlNet Depth
- ControlNet Normal
- (Optional) Custom 1998 film LoRA

### Blender Addons
- Compositor nodes (built-in)
- Cryptomatte (built-in)

### External Tools
- Stable Diffusion WebUI or ComfyUI
- ControlNet extension

---

## Next Steps

1. [ ] Create Phase 12.MSG-01 PLAN (ControlNet setup)
2. [ ] Create Phase 12.MSG-02 PLAN (layer compositing)
3. [ ] Create Phase 12.MSG-03 PLAN (final output pipeline)
4. [ ] Test with sample location render
5. [ ] Validate seed reproducibility
