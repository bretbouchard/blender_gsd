# Quetzalcoatl — Procedural Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUETZALCOATL GENERATOR                       │
├─────────────────────────────────────────────────────────────────┤
│  INPUT: Parameters (YAML/UI)                                    │
│  OUTPUT: Fully rigged, textured creature                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 0: NORMALIZE                                             │
│  - Validate parameters                                          │
│  - Convert to canonical ranges                                  │
│  - Resolve mutual exclusivities (leg positions, wing types)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: PRIMARY (Body Structure)                              │
│  - Spine curve generation (length, taper, wave)                 │
│  - Body cross-sections (elliptical, tapering)                   │
│  - Head placement (snout shape, jaw)                            │
│  - Limb sockets (0-4 leg pairs)                                 │
│  - Wing sockets (none/feathered/membrane)                       │
│  - Tail ending (tuft/pointed/rattle)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: SECONDARY (Features)                                  │
│  - Eye sockets and eyes                                         │
│  - Nostrils                                                     │
│  - Ear openings / hearing structures                            │
│  - Mouth interior (tongue, teeth sockets)                       │
│  - Crest/horn bases                                             │
│  - Whisker roots                                                │
│  - Limb geometry (legs with joints)                             │
│  - Wing geometry (if selected)                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: DETAIL (Surface)                                      │
│  - LAYER 1: Base scales (lizard-like, primary coverage)         │
│  - LAYER 2: Scale-feathers (intermediate, transition areas)     │
│  - LAYER 3: Full feathers (crest, tail tip, accent areas)       │
│  - Teeth instancing                                             │
│  - Whisker curves                                               │
│  - Claw/talon detail                                            │
│  - Color attribute painting (groups, gradients)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 4: OUTPUT PREP                                           │
│  - Store named attributes for shaders                           │
│  - UV mapping (multi-channel for scales/feathers)               │
│  - Vertex color groups                                          │
│  - Animation-ready rigging (if requested)                       │
│  - Export variants (game-ready, film-quality)                   │
└─────────────────────────────────────────────────────────────────┘
```

## Geometry Node Groups

### 1. `qc_spine` — Body Foundation
**Inputs:**
- `length`: Total body length (1m - 100m+)
- `segments`: Resolution of spine curve
- `taper_head`: Head taper ratio
- `taper_tail`: Tail taper ratio
- `wave_amplitude`: Base wave amplitude
- `wave_frequency`: Wave cycles along body

**Outputs:**
- Spine curve with tangent/normal attributes
- Body profile points for cross-sections

### 2. `qc_body` — Volume Generation
**Inputs:**
- Spine curve from `qc_spine`
- `body_radius`: Maximum body thickness
- `body_profile`: Cross-section shape (circular, elliptical, dorsal-flat)
- `compression`: Lateral/vertical compression ratio

**Outputs:**
- Body mesh with UV coordinates
- Named attributes: `spine_position`, `body_region` (head/body/tail)

### 3. `qc_head` — Cranial Structure
**Inputs:**
- Body mesh end
- `snout_length`: Muzzle extension
- `snout_profile`: Taper curve
- `jaw_depth`: Lower jaw offset
- `crest_type`: None/ridge/frill/horns
- `crest_size`: Scale of head ornamentation

**Outputs:**
- Head mesh with feature sockets
- Named attributes: `head_region` (snout/cheek/crest/jaw)

### 4. `qc_limbs` — Leg System
**Inputs:**
- Body mesh
- `leg_count`: 0/2/4 legs (pairs)
- `leg_positions`: Where along spine (normalized 0-1)
- `leg_length`: Limb proportion
- `leg_girth`: Thickness
- `toe_count`: 3/4/5 toes
- `claw_length`: Talon extension

**Outputs:**
- Limb geometry with joints
- Named attributes for rigging

### 5. `qc_wings` — Wing System
**Inputs:**
- Body mesh
- `wing_type`: None/feathered/membrane
- `wing_span`: Total wingspan
- `wing_arm_length`: Leading edge bone
- `finger_count`: Membrane supports (3-5)
- `feather_layers`: For feathered wings

**Outputs:**
- Wing geometry
- Named attributes: `wing_region`, `feather_row`

### 6. `qc_scales` — Layer 1: Base Scales
**Inputs:**
- Body mesh
- `scale_size`: Primary scale dimension
- `scale_shape`: Round/oval/hexagonal/diamond
- `scale_overlap`: How much scales layer
- `scale_density`: Instances per area
- `scale_variation`: Random size variance

**Outputs:**
- Scale instances with rotation variation
- Named attributes: `scale_id`, `scale_size`, `scale_color_group`

### 7. `qc_scale_feathers` — Layer 2: Transitional
**Inputs:**
- Body mesh with scale positions
- `feather_scale_ratio`: Size relative to scales
- `coverage_mask`: Where transition occurs
- `blend_sharpness`: Hard or gradual transition

**Outputs:**
- Hybrid scale-feather instances
- Named attributes for shader blending

### 8. `qc_feathers` — Layer 3: Full Feathers
**Inputs:**
- Body mesh
- Coverage regions (crest, tail, spine ridge)
- `feather_length`: Primary feather size
- `feather_width`: Rachis (shaft) width
- `barb_density`: How many barbs per side
- `iridescence_strength`: Color shift intensity
- `layer_count`: Stacked feather layers (1-5)

**Outputs:**
- Feather instances with barb geometry
- Named attributes: `feather_row`, `feather_id`, `iridescence_factor`

### 9. `qc_teeth` — Dentition
**Inputs:**
- Jaw mesh
- `tooth_count`: Number of teeth
- `tooth_type`: Uniform/mixed (incisors/canines/molars)
- `tooth_curve`: Curvature for fangs
- `tooth_size_variation`: Random variance

**Outputs:**
- Tooth instances positioned along jaw

### 10. `qc_whiskers` — Sensory Hairs
**Inputs:**
- Snout mesh
- `whisker_count`: Number per side
- `whisker_length`: Maximum length
- `whisker_taper`: Tip thinning
- `whisker_curve`: Natural curvature

**Outputs:**
- Whisker curves with thickness attribute

### 11. `qc_tail` — Tail Ending
**Inputs:**
- Tail end mesh
- `tail_type`: Pointed/feather_tuft/rattle/fan
- `tail_ornament_size`: Scale of ending feature
- `tail_feather_count`: For tuft type

**Outputs:**
- Tail ending geometry

### 12. `qc_colors` — Color System
**Inputs:**
- Full creature mesh
- `base_color`: Primary body color
- `accent_color`: Secondary highlights
- `iridescent_colors`: Shift palette (3-5 colors)
- `color_pattern`: Solid/gradient/spotted/striped
- `color_group_count`: Number of distinct color zones

**Outputs:**
- Vertex color layers
- Named attributes: `color_group`, `iridescent_blend`, `pattern_mask`

---

## Shader System

### `qc_iridescent_shader`

```
┌─────────────────────────────────────────────┐
│           IRIDESCENT FEATHER SHADER         │
├─────────────────────────────────────────────┤
│  Inputs:                                    │
│  - Base Color                               │
│  - Iridescent Palette (gradient)            │
│  - Iridescence Strength (0-1)               │
│  - Translucency Weight (0-1)                │
│  - Roughness                                │
│                                             │
│  Technique:                                 │
│  - Fresnel-based color shift                │
│  - Thin-film interference simulation        │
│  - SSS for translucent glow                 │
│  - Anisotropic for scale direction          │
└─────────────────────────────────────────────┘
```

**Key Nodes:**
- Layer Weight (Fresnel) → Color Ramp → Iridescent palette
- Subsurface Scattering with scale radius
- Anisotropic BSDF for directional highlights
- Mix shader between opaque and translucent

### `qc_scale_shader`

**Key Nodes:**
- UV-based scale pattern
- Height-based color variation
- Ambient occlusion in scale crevices
- Clearcoat for wet/reflective look

### `qc_translucent_ghost`

**For invisible/ethereal variant:**
- High SSS weight (0.8+)
- Low alpha (0.3-0.6)
- Refraction with IOR variation
- Volume absorption for depth

---

## Animation System

### Wave Propagation
```
spine_position (0-1) → sin(wave_phase + spine_position * wave_frequency)
```

**Parameters:**
- `wave_speed`: Cycles per second
- `wave_amplitude`: Maximum displacement
- `wave_decay`: Reduction toward head
- `secondary_wave`: Counter-propagating wave for complexity

### Secondary Motion
- **Feather sway**: Responds to body velocity + wind
- **Whisker lag**: Delayed response to head movement
- **Scale ripple**: Wave of scale rotation along body

---

## Parameter Categories

### Body Parameters
| Name | Type | Range | Default |
|------|------|-------|---------|
| `body_length` | Float | 1-100 | 10 |
| `body_radius` | Float | 0.1-5 | 0.5 |
| `body_taper` | Float | 0-1 | 0.3 |
| `spine_wave_amp` | Float | 0-2 | 0.5 |
| `spine_wave_freq` | Int | 1-10 | 3 |

### Limb Parameters
| Name | Type | Range | Default |
|------|------|-------|---------|
| `leg_pairs` | Int | 0-4 | 2 |
| `leg_positions` | Float[4] | 0-1 | [0.3, 0.6] |
| `leg_length` | Float | 0.1-3 | 1.0 |
| `wing_type` | Enum | 0-2 | 0 (none) |
| `wing_span` | Float | 0-10 | 3.0 |

### Detail Parameters
| Name | Type | Range | Default |
|------|------|-------|---------|
| `scale_size` | Float | 0.01-0.5 | 0.05 |
| `scale_density` | Float | 0.5-2 | 1.0 |
| `feather_layers` | Int | 1-5 | 3 |
| `iridescence` | Float | 0-1 | 0.5 |
| `translucency` | Float | 0-1 | 0.3 |

### Color Parameters
| Name | Type | Default |
|------|------|---------|
| `base_color` | Color | (0.1, 0.3, 0.2) |
| `accent_color` | Color | (0.8, 0.6, 0.2) |
| `iridescent_1` | Color | (0.0, 0.8, 0.6) |
| `iridescent_2` | Color | (0.8, 0.2, 0.8) |
| `iridescent_3` | Color | (0.2, 0.4, 0.9) |

---

## File Structure

```
projects/quetzalcoatl/
├── REQUIREMENTS.md           # This document
├── ARCHITECTURE.md           # System design
├── assets/
│   ├── references/           # Reference images
│   └── textures/             # Custom textures
├── configs/
│   ├── base_creature.yaml    # Default parameters
│   ├── presets/              # Named creature variants
│   │   ├── serpent.yaml
│   │   ├── dragon.yaml
│   │   ├── wyvern.yaml
│   │   └── ghost.yaml
│   └── animation/
│       ├── idle.yaml
│       ├── flight.yaml
│       └── slither.yaml
├── inputs/
│   └── reference_curves.blend
├── lib/
│   ├── __init__.py
│   ├── spine.py              # Spine curve generation
│   ├── body.py               # Body mesh generation
│   ├── head.py               # Head/face generation
│   ├── limbs.py              # Leg/wing generation
│   ├── scales.py             # Scale instancing
│   ├── feathers.py           # Feather generation
│   ├── teeth.py              # Dentition
│   ├── whiskers.py           # Whisker curves
│   ├── colors.py             # Color attribute system
│   └── shaders.py            # Material generation
├── node_groups/
│   ├── qc_spine.blend
│   ├── qc_body.blend
│   ├── qc_head.blend
│   ├── qc_limbs.blend
│   ├── qc_wings.blend
│   ├── qc_scales.blend
│   ├── qc_scale_feathers.blend
│   ├── qc_feathers.blend
│   ├── qc_teeth.blend
│   ├── qc_whiskers.blend
│   ├── qc_tail.blend
│   └── qc_colors.blend
├── shaders/
│   ├── qc_iridescent.blend
│   ├── qc_scale.blend
│   └── qc_translucent.blend
├── output/
│   └── (generated .blend files)
└── scripts/
    ├── generate_creature.py  # Main generation script
    ├── apply_preset.py       # Load preset config
    └── export_variants.py    # Export for different uses
```
