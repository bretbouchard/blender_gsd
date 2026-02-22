# MSG 1998 - Cross-Project Integration

**Created:** 2026-02-22
**Projects:** FDX GSD (Source of Truth) + Blender GSD (Execution)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FDX GSD                                      │
│                    (SOURCE OF TRUTH)                                │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │   SCRIPT    │  │   CANON     │  │      CONTINUITY             │ │
│  │  Scenes,    │  │ Characters, │  │  Wardrobe, Props, Timeline  │ │
│  │  Dialogue   │  │ Locations   │  │  Knowledge Validation       │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────────┘ │
│         │                │                      │                  │
│         │    ┌───────────┴──────────────────────┘                  │
│         │    │                                                          │
│         ▼    ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    SHOT LISTS                                 │   │
│  │  (Scene → Shots → Camera angles → Evidence links)            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                PRODUCTION PACKAGES (Phase 8)                  │   │
│  │                                                               │   │
│  │  • Location Assets (fSpy, references, addresses)             │   │
│  │  • Shot Packages (camera, VFX notes, render specs)           │   │
│  │  • SD Configurations (seeds, prompts, ControlNet)            │   │
│  │  • Handoff Manifests (for Blender team)                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│         │                                                            │
└─────────│────────────────────────────────────────────────────────────┘
          │
          │  gsd handoff blender --scene SCN-XXX
          │  gsd handoff sd --scene SCN-XXX
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BLENDER GSD                                    │
│                       (EXECUTION)                                   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │           PHASE 9.MSG: LOCATION BUILDING                      │   │
│  │                                                               │   │
│  │  • Receive FDX handoff packages                              │   │
│  │  • fSpy camera matching                                      │   │
│  │  • Build 3D models from references                           │   │
│  │  • Generate render layers (depth, normal, etc.)              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │           PHASE 12.MSG: SD COMPOSITING                        │   │
│  │                                                               │   │
│  │  • Receive SD configs from FDX                               │   │
│  │  • ControlNet-guided generation (depth, normal)              │   │
│  │  • Layer-based compositing (BG, MG, FG)                      │   │
│  │  • 1998 film aesthetic (grain, color, lens)                  │   │
│  │  • Final output for editorial                                │   │
│  └──────────────────────────────────────────────────────────────┘   │
│         │                                                            │
└─────────│────────────────────────────────────────────────────────────┘
          │
          │  blender-gsd export-editorial --scene SCN-XXX
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EDITORIAL                                      │
│                                                                     │
│  • Final ProRes files for editing                                  │
│  • EXR masters for color grading                                   │
│  • Shot metadata from FDX                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Project Responsibilities

### FDX GSD Owns

| Domain | Examples |
|--------|----------|
| **Script** | Scenes, dialogue, action descriptions |
| **Canon** | Characters, locations, aliases |
| **Continuity** | Wardrobe, props, timeline, knowledge |
| **Shot Planning** | Shot types, camera angles, evidence links |
| **Production Metadata** | SD seeds, prompts, render specs |
| **Handoff Generation** | Packages for Blender/SD teams |

### Blender GSD Owns

| Domain | Examples |
|--------|----------|
| **3D Execution** | Building models, texturing, lighting |
| **Camera Matching** | fSpy import, camera setup |
| **Rendering** | Render passes, quality profiles |
| **SD Integration** | ControlNet inputs, layer generation |
| **Compositing** | Layer blending, film effects |
| **Output** | Final renders for editorial |

---

## Handoff Protocol

### FDX → Blender (Location Handoff)

**Command:**
```bash
# In FDX GSD
cd ~/apps/fdx_gsd
gsd handoff blender --scene SCN-002 --output handoff/
```

**Output:**
```
handoff/blender/SCN-002/
├── manifest.json              # Package metadata
├── scene.json                 # Scene data
├── shots/
│   ├── SHOT-002-001.json     # Per-shot package
│   └── ...
├── locations/
│   ├── LOC-002/
│   │   ├── asset.json        # Location metadata
│   │   ├── references/       # Reference photos
│   │   └── fspy/             # fSpy files
│   └── ...
└── camera/
    └── camera_rig.json       # Camera specs
```

**Receiving in Blender GSD:**
```bash
# In Blender GSD
cd ~/apps/blender_gsd
blender-gsd receive-handoff --from-fdx --scene SCN-002
```

### FDX → SD Team (SD Config Handoff)

**Command:**
```bash
# In FDX GSD
gsd handoff sd --scene SCN-002 --output handoff/
```

**Output:**
```
handoff/sd/SCN-002/
├── manifest.json
├── batch.json                 # All shot configs
├── shots/
│   ├── SHOT-002-001.json     # SD config + prompts
│   └── ...
├── prompts/
│   ├── positive_base.txt     # Shared positive prompt
│   ├── negative_base.txt     # Shared negative prompt
│   └── per_shot/             # Shot-specific additions
└── seeds.json                # Seed manifest
```

---

## Status Tracking

### Handoff Status Values

| Status | Owner | Meaning |
|--------|-------|---------|
| `pending` | FDX | Generated, not yet sent |
| `sent` | FDX | Delivered to team |
| `received` | Blender | Acknowledged receipt |
| `in_progress` | Blender | Work started |
| `review` | Blender | Ready for review |
| `complete` | Blender | Approved, integrated |
| `revision_needed` | FDX/Blender | Requires changes |
| `blocked` | Either | Waiting on dependency |

### Status Update Flow

```
FDX: pending → sent
Blender: received → in_progress → review → complete
                ↑                    │
                └────────────────────┘
                     revision_needed
```

---

## File Locations

### FDX GSD

```
~/apps/fdx_gsd/
├── .planning/
│   └── phases/08-msg-1998-production/
│       ├── 08-RESEARCH.md
│       ├── 08-REQUIREMENTS.md
│       ├── 08-LOCATIONS.md
│       └── 08-HANDOFF-SPEC.md
├── assets/                          # Git LFS
│   └── locations/
│       └── MSG/
│           ├── reference_photos/
│           └── fspy/
├── handoff/
│   ├── blender/
│   └── sd/
└── build/
    └── production/
        ├── shot_packages.json
        └── location_assets.json
```

### Blender GSD

```
~/apps/blender_gsd/
├── .planning/
│   └── phases/
│       ├── 09-msg-1998-locations/
│       │   └── 09-MSG-RESEARCH.md
│       └── 12-msg-1998-compositing/
│           └── 12-MSG-RESEARCH.md
├── assets/
│   └── locations/
│       └── LOC-XXX/
│           ├── LOC-XXX.blend
│           └── render_layers/
├── handoff/
│   ├── from_fdx/
│   └── to_editorial/
└── output/
    └── final/
```

---

## Workflow Example: SCN-002

### Step 1: FDX GSD (Planning)

```bash
# Create location asset
gsd location add "MSG Exterior" \
  --address "4 Pennsylvania Plaza, NYC" \
  --coordinates "40.7505,-73.9934"

# Link fSpy file
gsd location link-fspy LOC-002 --file assets/locations/MSG/exterior.fspy

# Create shot package with SD config
gsd shot package SHOT-002-001 \
  --camera-focal-length 35 \
  --sd-seed 1234567890 \
  --sd-prompt prompts/msg_exterior.txt

# Generate handoff
gsd handoff blender --scene SCN-002 --output handoff/
gsd handoff sd --scene SCN-002 --output handoff/
```

### Step 2: Blender GSD (Execution)

```bash
# Receive handoff
blender-gsd receive-handoff --from-fdx --scene SCN-002

# Build location from fSpy
blender-gsd build-location LOC-002 --from-fspy

# Render passes
blender-gsd render-location LOC-002 --passes all

# Run SD compositing
blender-gsd composite --shot SHOT-002-001 --with-sd

# Export for editorial
blender-gsd export-editorial --shot SHOT-002-001 --format prores
```

### Step 3: Update Status

```bash
# In FDX GSD
gsd handoff update SHOT-002-001 --status complete
```

---

## Communication Protocol

### When FDX Changes

1. **Update script/canon** → Regenerate affected shot packages
2. **Notify Blender** → `gsd handoff notify --scene SCN-XXX --change description`
3. **Blender pulls** → `blender-gsd pull-changes --scene SCN-XXX`

### When Blender Needs Changes

1. **Flag revision_needed** → `blender-gsd request-revision SHOT-XXX-XXX --reason "..."`
2. **FDX updates** → Modify source, regenerate handoff
3. **Blender re-executes** → Pull new package, re-render

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Handoff packages processed | 100% success |
| Seed reproducibility | 100% identical outputs |
| Period accuracy | 0 modern elements |
| Render quality | Matches 1998 film stock |
| Integration time | < 1 hour per shot |

---

## Next Steps

1. [ ] Complete FDX Phase 8 implementation
2. [ ] Test handoff workflow with sample scene
3. [ ] Validate Blender receives correct packages
4. [ ] Test SD seed reproducibility
5. [ ] Document first full shot workflow
