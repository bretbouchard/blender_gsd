# Quetzalcoatl System — Phase Roadmap

## Project: Quetzalcoatl Feathered Serpent Generator

**Location**: `projects/quetzalcoatl/`
**Type**: Procedural Creature System
**Complexity**: High (multi-layer, parametric, animated)

---

## Phase Overview

| Phase | Name | Focus | Est. Complexity |
|-------|------|-------|-----------------|
| 20.0 | Foundation | Project setup, config system, spine prototype | Medium |
| 20.1 | Body System | Spine curve, body mesh, taper, regions | High |
| 20.2 | Head System | Snout, jaw, eyes, nostrils, crest options | High |
| 20.3 | Limb System | Legs (0-4 pairs), positioning, joints | High |
| 20.4 | Wing System | None/feathered/membrane variants | High |
| 20.5 | Scale Layer | Base scale instancing, variation, attributes | High |
| 20.6 | Feather Layer | Scale-feathers, full feathers, layering | Very High |
| 20.7 | Detail Features | Teeth, whiskers, claws, tail endings | Medium |
| 20.8 | Color System | Color groups, gradients, attribute painting | Medium |
| 20.9 | Shader System | Iridescence, translucency, SSS | High |
| 20.10 | Animation Prep | Wave propagation, secondary motion hooks | Medium |
| 20.11 | Presets & Export | Named presets, export variants | Low |

---

## Phase 20.0: Foundation

**Goal**: Establish project structure, configuration system, and prove spine curve generation.

### Tasks
1. Create project folder structure
2. Define YAML configuration schema
3. Implement base parameter loader
4. Create spine curve prototype (geo nodes)
5. Write spine.py module
6. Add unit tests for spine generation

### Deliverables
- `projects/quetzalcoatl/` full structure
- `configs/base_creature.yaml`
- `lib/spine.py`
- `node_groups/qc_spine.blend`
- Tests passing

---

## Phase 20.1: Body System

**Goal**: Generate procedural body mesh from spine curve.

### Key Features
- Elliptical cross-sections
- Head/body/tail region attributes
- Taper controls
- Body profile variations

### Deliverables
- `lib/body.py`
- `node_groups/qc_body.blend`
- Body mesh with proper UVs and attributes

---

## Phase 20.2: Head System

**Goal**: Parametric head with selectable features.

### Key Features
- Snout length/shape control
- Jaw with mouth interior
- Eye sockets with eye geometry
- Nostril placement
- Crest/horn variants (selectable)

### Deliverables
- `lib/head.py`
- `node_groups/qc_head.blend`
- Feature socket system

---

## Phase 20.3: Limb System

**Goal**: Parametric legs (0-4 pairs) with proper anatomy.

### Key Features
- Selectable leg count
- Position along spine
- Upper/lower leg, foot, toes
- Joint attributes for rigging
- Claw/talon geometry

### Deliverables
- `lib/limbs.py`
- `node_groups/qc_limbs.blend`
- Leg presets (squat, lanky, etc.)

---

## Phase 20.4: Wing System

**Goal**: Optional wings (none/feathered/membrane).

### Key Features
- Wing type selection
- Feathered: layered feathers, arm/finger structure
- Membrane: bat-like with finger supports
- Wing fold/extend poses

### Deliverables
- `lib/wings.py`
- `node_groups/qc_wings.blend`
- Wing type presets

---

## Phase 20.5: Scale Layer

**Goal**: Procedural base scale instancing.

### Key Features
- Multiple scale shapes (round, oval, hex, diamond)
- Size variation and noise
- Overlap control
- Direction/orientation following body flow
- Color group attributes

### Deliverables
- `lib/scales.py`
- `node_groups/qc_scales.blend`
- Scale density tests

---

## Phase 20.6: Feather Layer

**Goal**: Multi-layer feather system with iridescence prep.

### Key Features
- Scale-feather transition (hybrid)
- Full feathers with barb detail
- Multiple layer passes (1-5 layers)
- Feather direction/orientation
- Coverage masking (where feathers vs scales)

### Deliverables
- `lib/feathers.py`
- `node_groups/qc_feathers.blend`
- `node_groups/qc_scale_feathers.blend`
- Layer blending tests

---

## Phase 20.7: Detail Features

**Goal**: Fine details — teeth, whiskers, tail endings.

### Key Features
- Teeth: count, type, curvature
- Whiskers: count, length, curve, thickness
- Tail endings: pointed, tuft, rattle, fan
- Claws/talons on limbs

### Deliverables
- `lib/teeth.py`
- `lib/whiskers.py`
- `node_groups/qc_teeth.blend`
- `node_groups/qc_whiskers.blend`
- `node_groups/qc_tail.blend`

---

## Phase 20.8: Color System

**Goal**: Procedural color attributes for shader use.

### Key Features
- Color groups (body regions)
- Gradient patterns (solid, stripe, spot)
- Iridescence factor per region
- Accent color placement

### Deliverables
- `lib/colors.py`
- `node_groups/qc_colors.blend`
- Color attribute tests

---

## Phase 20.9: Shader System

**Goal**: Iridescent, translucent materials.

### Key Features
- Fresnel-based color shift
- Thin-film iridescence simulation
- SSS for translucency
- Anisotropic highlights for scales
- Ghost/invisible variant

### Deliverables
- `lib/shaders.py`
- `shaders/qc_iridescent.blend`
- `shaders/qc_scale.blend`
- `shaders/qc_translucent.blend`

---

## Phase 20.10: Animation Prep

**Goal**: Wave propagation and secondary motion.

### Key Features
- Spine wave animation (sinusoidal)
- Wave speed/amplitude/frequency control
- Feather sway response
- Whisker secondary motion
- Motion blur compatibility

### Deliverables
- Animation drivers/setup
- Wave parameter exposure
- Animation tests

---

## Phase 20.11: Presets & Export

**Goal**: Named presets and export variants.

### Key Features
- Preset configurations (serpent, dragon, wyvern, ghost)
- Export for game (low-poly)
- Export for film (high-detail)
- Documentation

### Deliverables
- `configs/presets/*.yaml`
- `scripts/export_variants.py`
- User documentation

---

## Dependencies

```
20.0 Foundation
    │
    ├──► 20.1 Body (needs spine)
    │       │
    │       ├──► 20.2 Head (needs body)
    │       │
    │       ├──► 20.3 Limbs (needs body)
    │       │
    │       └──► 20.4 Wings (needs body)
    │
    ├──► 20.5 Scales (needs body)
    │       │
    │       └──► 20.6 Feathers (needs scales)
    │
    ├──► 20.7 Details (needs head + limbs)
    │
    ├──► 20.8 Colors (needs all geometry)
    │
    └──► 20.9 Shaders (needs colors + attributes)
            │
            └──► 20.10 Animation (needs shaders)
                    │
                    └──► 20.11 Presets (needs everything)
```

---

## Success Criteria

- [ ] Can generate serpent (0 legs, no wings)
- [ ] Can generate dragon (4 legs, feathered wings)
- [ ] Can generate wyvern (2 legs, membrane wings)
- [ ] All parameters exposed and functional
- [ ] Iridescence visibly shifts with viewing angle
- [ ] Translucency option creates ethereal look
- [ ] Wave animation produces hypnotic motion
- [ ] Export produces usable assets
