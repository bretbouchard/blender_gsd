# RESEARCH: MSG 1998 Location Building

**Phase:** 9.MSG (MSG 1998 Locations)
**Created:** 2026-02-22
**Status:** Planning
**Source:** FDX GSD Production Package (Phase 8)
**Target:** 20 NYC locations, 1998 period accuracy

---

## Overview

This phase builds **real-world NYC locations** for the MSG 1998 film, consuming production packages from FDX GSD and producing Blender-ready assets.

**Input:** FDX GSD → `handoff/blender/{SCENE_ID}/`
**Output:** `assets/locations/{LOC_ID}/` → `.blend` files with render layers

---

## Integration with FDX GSD

```
┌────────────────────────────────────────────────────────────┐
│                      FDX GSD                               │
│                                                            │
│  Location Breakdown (20 locations)                        │
│  Real addresses, coordinates, period notes                │
│  Reference photos, fSpy files                             │
│                                                            │
└────────────────────┬───────────────────────────────────────┘
                     │
                     │ gsd handoff blender --scene SCN-XXX
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                   BLENDER GSD                              │
│                                                            │
│  Phase 9.MSG: Location Building                           │
│  • Consume FDX handoff packages                           │
│  • Build 3D from fSpy + references                        │
│  • Generate render layers for SD compositing              │
│  • Export to Phase 12.MSG (compositing)                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Location Building Pipeline

### Stage 1: Receive FDX Handoff

**Input:** `handoff/blender/{SCENE_ID}/locations/{LOC_ID}/`

```
{LOC_ID}/
├── asset.json              # Location metadata from FDX
├── references/             # Reference photos
│   ├── ref_001.jpg
│   └── ref_002.jpg
├── fspy/
│   └── {LOC_ID}.fspy       # Camera matching file
└── period_notes.md         # 1998 period requirements
```

### Stage 2: Camera Matching (fSpy → Blender)

**Process:**
1. Open fSpy file in standalone fSpy app
2. Verify vanishing points are accurate
3. Export to `.fspy` format
4. Import via fSpy-Blender addon
5. Camera is now matched to reference photo

**Tools:**
- fSpy (FREE): https://fspy.io
- fSpy-Blender: https://github.com/stuffmatic/fSpy-Blender

### Stage 3: Model Building

**Universal Stage Order (from PROJECT.md):**
- **Stage 0** — Normalize: Scale to real-world units (meters)
- **Stage 1** — Primary: Base building geometry (walls, roof)
- **Stage 2** — Secondary: Windows, doors, architectural details
- **Stage 3** — Detail: Surface textures, wear, period signage
- **Stage 4** — OutputPrep: Store attributes, generate render layers

**Modeling Approach by Location Type:**

| Type | Approach | Tools |
|------|----------|-------|
| Exterior facade | fSpy + extrusion | Photo projection |
| Interior (accessible) | Meshroom photogrammetry | Multi-photo scan |
| Interior (inaccessible) | Reference modeling | Procedural + refs |
| Street/city block | fSpy + kit parts | Street kit, period props |
| Generic (hospital) | Reference composite | Stock assets + mods |

### Stage 4: Texturing

**Period-Accurate Materials:**
- 1998 signage (no LED screens)
- Period-appropriate wear on surfaces
- Correct architectural materials for era
- Pre-smartphone street furniture

**Projection vs. Procedural:**
- **Photo projection**: For hero buildings, accurate facades
- **Procedural**: For generic surfaces, variations

### Stage 5: Render Layer Setup

**Required Passes for SD Compositing:**
```python
render_passes = [
    "beauty",           # Final color
    "depth",            # Z-depth for ControlNet
    "normal",           # Surface normals for ControlNet
    "object_id",        # Object isolation masks
    "diffuse",          # Diffuse color only
    "shadow",           # Shadow pass
    "ao",               # Ambient occlusion
    "cryptomatte",      # Per-object mattes
]
```

---

## Location Specifications

### LOC-002: MSG Exterior (Hero Location)

**Priority:** P0 | **Complexity:** High

**Reference:**
- Address: 4 Pennsylvania Plaza, NYC
- Coordinates: 40.7505° N, 73.9934° W
- Period: 1998 (post-1991 renovation, pre-2011 transformation)

**Build Plan:**
1. fSpy from 4 cardinal directions
2. Primary: Cylindrical base geometry
3. Secondary: Entrance structures, windows
4. Detail: Period signage, surrounding buildings
5. OutputPrep: Separate BG/MG/FG layers

**Challenges:**
- Large scale building
- Multiple angles needed
- Period accuracy (remove 2011+ additions)

**Output:**
```
assets/locations/LOC-002/
├── LOC-002.blend           # Main model
├── LOC-002_exterior_A.fspy # North view
├── LOC-002_exterior_B.fspy # East view
├── references/
│   └── (20+ reference photos)
├── textures/
│   ├── concrete_diffuse.png
│   ├── signage_1998.png
│   └── ...
└── render_layers/
    ├── depth/
    ├── normal/
    └── ...
```

### LOC-008: Subway Platform

**Priority:** P1 | **Complexity:** Medium

**Reference:**
- Station: N/Q/R/W 34th St-Herald Sq
- Period: 1998 (pre-modernization)

**Build Plan:**
1. fSpy for entrance geometry
2. Meshroom for platform (if access possible)
3. MTA standard tile kit
4. Period advertisements as textures
5. Procedural crowd positions

**Challenges:**
- MTA photography restrictions
- Access for photogrammetry
- Period-accurate advertising

### LOC-009: Subway Car Interior

**Priority:** P1 | **Complexity:** Medium

**Reference:**
- Car type: MTA R142/R160 (1998 rolling stock)
- Period: 1998

**Build Plan:**
1. Reference-based modeling (no fSpy needed)
2. Modular seat/wall sections
3. Window view projection system
4. Procedural wear/grime

**Output:**
- Interior model
- Window mask plates for compositing
- Animated door/seats if needed

---

## 1998 Period Accuracy Checklist

### Architecture
- [ ] No LED screens/billboards (use printed/illuminated signs)
- [ ] Period-appropriate storefronts
- [ ] Pre-2011 MSG configuration
- [ ] 1998 subway car types

### Street Furniture
- [ ] Period pay phones (not smartphone stations)
- [ ] Newspaper boxes (not digital displays)
- [ ] Period traffic signals
- [ ] Correct municipal signage

### Vehicles
- [ ] No cars post-1998
- [ ] Period taxi design
- [ ] MTA bus styling
- [ ] Emergency vehicle styling

### General Atmosphere
- [ ] Fashion references (crowd)
- [ ] Advertising style
- [ ] General wear level

---

## Handoff to Phase 12.MSG (Compositing)

**Output Structure:**
```
handoff/compositing/{SCENE_ID}/
├── location_renders/
│   ├── LOC-XXX_beauty.exr
│   ├── LOC-XXX_depth.exr
│   ├── LOC-XXX_normal.exr
│   ├── LOC-XXX_object_id.exr
│   └── ...
├── masks/
│   ├── LOC-XXX_bg_mask.png
│   ├── LOC-XXX_mg_mask.png
│   └── LOC-XXX_fg_mask.png
└── metadata.json
```

**metadata.json:**
```json
{
  "location_id": "LOC-002",
  "scene_id": "SCN-002",
  "render_settings": {
    "resolution": [4096, 1716],
    "frame_rate": 24,
    "color_space": "ACEScg"
  },
  "camera": {
    "focal_length_mm": 35,
    "fov_degrees": 54.4
  },
  "layers": {
    "background": "Buildings and sky",
    "midground": "MSG and immediate surroundings",
    "foreground": "Street level, pedestrians"
  }
}
```

---

## CLI Commands (Planned)

```bash
# Receive handoff from FDX
blender-gsd receive-handoff --from-fdx --scene SCN-002

# Build location from fSpy
blender-gsd build-location LOC-002 --from-fspy assets/locations/LOC-002/

# Render location passes
blender-gsd render-location LOC-002 --passes all --output handoff/compositing/

# Validate period accuracy
blender-gsd validate-period LOC-002 --year 1998

# Export for compositing
blender-gsd export-compositing LOC-002 --scene SCN-002
```

---

## Dependencies

### Required Addons
- fSpy-Blender (FREE)
- Perspective Plotter (optional, paid)
- Auto-Building (optional, for procedural details)

### External Tools
- fSpy standalone (camera matching)
- Meshroom (photogrammetry, if accessible)

### From FDX GSD
- Location handoff packages
- Reference photos
- Period notes

---

## Next Steps

1. [ ] Create Phase 9.MSG-01 PLAN (fSpy import workflow)
2. [ ] Create Phase 9.MSG-02 PLAN (modeling pipeline)
3. [ ] Create Phase 9.MSG-03 PLAN (render layer setup)
4. [ ] Coordinate with FDX on first handoff package
5. [ ] Begin photo capture for MSG area
