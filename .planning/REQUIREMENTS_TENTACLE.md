# Tentacle System Requirements

**Version:** 1.0
**Status:** Draft
**Created:** 2026-02-25
**Research:** `.planning/phases/19.0-tentacle-system/RESEARCH.md`

---

## Overview

The Tentacle System provides procedural generation, rigging, and export of organic tentacles for horror creature characters, specifically **zombie mouth tentacles** that emerge from a character's mouth.

### Primary Use Case
Zombie/creature characters with parasitic or mutated tentacles that:
1. Live inside the mouth when hidden
2. Emerge between teeth when attacking/searching
3. Writhe, grab, and squeeze objects/victims
4. Retract back into the mouth

---

## Requirements Index

| ID | Category | Priority | Description |
|----|----------|----------|-------------|
| REQ-TENT-01 | Geometry | P0 | Procedural body generation |
| REQ-TENT-02 | Geometry | P1 | Sucker system |
| REQ-TENT-03 | Animation | P0 | Squeeze/expand animation |
| REQ-TENT-04 | Materials | P1 | Procedural skin materials |
| REQ-TENT-05 | Export | P0 | Unreal Engine export |
| REQ-TENT-06 | Integration | P0 | Zombie mouth integration |
| REQ-TENT-07 | Animation | P1 | Animation state machine |
| REQ-TENT-08 | Materials | P2 | Slime/saliva effects |

---

## REQ-TENT-01: Procedural Geometry

**Priority:** P0 | **Phase:** 19.1

### Description
Generate procedural tentacle bodies with configurable parameters for shape, taper, and segmentation.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 01-01 | Configurable length | Length adjustable from 0.1m to 3.0m |
| 01-02 | Taper profile | Base diameter 2-3x tip diameter |
| 01-03 | Segmentation | 10-50 segments along length |
| 01-04 | Real-time preview | Changes visible in viewport immediately |
| 01-05 | Curve-based base | Bézier curve as foundation |
| 01-06 | Deterministic output | Same parameters = same mesh |
| 01-07 | Smooth surface | Auto-subdivision for organic look |

### Parameters

```yaml
TentacleGeometry:
  length: 1.0          # meters
  base_diameter: 0.08  # meters
  tip_diameter: 0.02   # meters
  segments: 20         # count
  curve_resolution: 64 # points per segment
  twist: 0.0           # degrees along length
```

### Technical Approach
- Geometry Nodes for procedural generation
- Curve → Mesh conversion with radius profile
- Subdivision surface for smoothing

---

## REQ-TENT-02: Sucker System

**Priority:** P1 | **Phase:** 19.2

### Description
Procedural sucker generation with placement controls and size gradients.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 02-01 | Row count | 2-8 rows along tentacle length |
| 02-02 | Column count | 4-12 columns around circumference |
| 02-03 | Size gradient | Larger at base, smaller at tip |
| 02-04 | Cup depth | Configurable from shallow to deep |
| 02-05 | Rim sharpness | Hard to soft edge control |
| 02-06 | Alternating rows | Offset odd rows for natural look |
| 02-07 | Optional | Can disable suckers entirely |
| 02-08 | Smooth style | Body horror smooth (not realistic papillae) |

### Parameters

```yaml
SuckerConfig:
  enabled: true
  rows: 6
  columns: 8
  base_size: 0.015    # meters
  tip_size: 0.003     # meters
  cup_depth: 0.005    # meters
  rim_sharpness: 0.7  # 0.0-1.0
  alternating: true
  style: smooth       # smooth, realistic, stylized
```

### Technical Approach
- Instance on Points node for placement
- Scale by curve parameter for gradient
- Separate sucker geometry merged to main mesh

---

## REQ-TENT-03: Squeeze/Expand Animation

**Priority:** P0 | **Phase:** 19.3

### Description
Animation system for compressing through small openings and expanding back out.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 03-01 | Compress diameter | Squish to 30-50% of original |
| 03-02 | Elongate length | Extend 1.5-2x when compressed |
| 03-03 | Smooth interpolation | No visible popping/jumping |
| 03-04 | Localized squeeze | Can squeeze at any point along length |
| 03-05 | Morph targets | Export as UE5 morph targets |
| 03-06 | Shape key presets | Base, Compressed, Expanded, Curled |
| 03-07 | Volume preservation | Approximate volume maintained |

### Shape Keys

| Shape Key | Description | Use Case |
|-----------|-------------|----------|
| `SK_Base` | Default shape | Normal state |
| `SK_Compress_50` | 50% diameter, 2x length | Squeezing through mouth |
| `SK_Compress_75` | 75% diameter, 1.3x length | Partial squeeze |
| `SK_Expand_125` | 125% diameter, 0.8x length | Bulging out |
| `SK_Curl_Tip` | Tip curled 180° | Grabbing objects |
| `SK_Curl_Full` | Full spiral curl | Defensive posture |

### Technical Approach
- Shape keys generated procedurally
- Spline IK for bone-based animation
- Driver-controlled blending between states

---

## REQ-TENT-04: Procedural Skin Materials

**Priority:** P1 | **Phase:** 19.4

### Description
Procedural material system with horror-specific themes and wet/slimy effects.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 04-01 | Subsurface scattering | Translucent, fleshy appearance |
| 04-02 | Color themes | 5+ horror presets available |
| 04-03 | Wet/slimy option | High specular, low roughness |
| 04-04 | Vein patterns | Subsurface vein visibility |
| 04-05 | Texture baking | Export to image maps for UE |
| 04-06 | Pattern variation | Noise-based organic variation |
| 04-07 | Material zones | Base, mid, tip can differ |

### Horror Theme Presets

| Theme | Base Color | Veins | Slime | SSS |
|-------|------------|-------|-------|-----|
| `rotting` | Gray-green | Dark purple | Yellow-brown | Strong red |
| `parasitic` | Flesh pink | Red | Clear | Medium pink |
| `demonic` | Deep red | Black | Black | Strong red |
| `mutated` | Pale flesh | Bioluminescent | Green | Cyan glow |
| `decayed` | Bone white | None | Brown | Weak |

### Technical Approach
- Principled BSDF with SSS
- Layered procedural textures
- Bake to 2K/4K textures for export

---

## REQ-TENT-05: Unreal Engine Export

**Priority:** P0 | **Phase:** 19.5

### Description
Complete FBX export pipeline for Unreal Engine 5.x.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 05-01 | FBX skeleton export | Bone hierarchy preserved |
| 05-02 | Morph targets | Shape keys export correctly |
| 05-03 | Material slots | Separate slots for zones |
| 05-04 | LOD generation | 4 LOD levels auto-generated |
| 05-05 | UV preservation | Non-overlapping UVs |
| 05-06 | Skin weights | Smooth deformation at joints |
| 05-07 | Root bone | Clean hierarchy for UE |

### Export Settings

```yaml
FBXExport:
  object_types: [armature, mesh]
  shape_keys: true
  apply_modifiers: true
  skin: true
  smoothing: face
  tangent_space: true
  embed_textures: false  # External for UE
```

### LOD Strategy

| LOD | Triangles | Screen Size |
|-----|-----------|-------------|
| LOD0 | 100% | > 50% |
| LOD1 | 50% | 25-50% |
| LOD2 | 25% | 10-25% |
| LOD3 | 12% | < 10% |

---

## REQ-TENT-06: Zombie Mouth Integration

**Priority:** P0 | **Phase:** 19.1 (partial), 19.3 (full)

### Description
Integration with character face rig for zombie mouth tentacle attachment.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 06-01 | Mouth anchor | Tentacle roots attach to mouth interior |
| 06-02 | Multi-tentacle | 1-6 tentacles per character |
| 06-03 | Size variation | Mix of thick/thin in same mouth |
| 06-04 | Teeth emergence | Tentacles emerge between teeth |
| 06-05 | Jaw parent | Tentacles follow jaw bone movement |
| 06-06 | Hidden state | Tentacles invisible when inside mouth |
| 06-07 | Staggered emergence | Tentacles don't all emerge at once |

### Bone Hierarchy

```
Character_Skeleton
└── Head
    └── Jaw
        └── Mouth_Inside (socket)
            ├── Tentacle_Root_01
            │   └── Tentacle_01_chain...
            ├── Tentacle_Root_02
            │   └── Tentacle_02_chain...
            └── Tentacle_Root_N
                └── Tentacle_N_chain...
```

### Multi-Tentacle Configuration

```yaml
ZombieMouthConfig:
  tentacle_count: 4
  distribution: staggered    # uniform, random, staggered
  size_mix: 0.5              # 0=all thin, 1=all thick
  emergence_delay: 0.1       # seconds between each tentacle
  spread_angle: 60           # degrees across mouth
```

---

## REQ-TENT-07: Animation State Machine

**Priority:** P1 | **Phase:** 19.3

### Description
Animation states for zombie mouth tentacle behavior.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 07-01 | State definitions | 6 states defined |
| 07-02 | State transitions | Smooth blending between states |
| 07-03 | Idle animation | Subtle undulation when searching |
| 07-04 | Emergence timing | Configurable emergence speed |
| 07-05 | UE animation blueprint | States map to UE anim graph |

### Animation States

| State | Description | Key Features |
|-------|-------------|--------------|
| `Hidden` | Inside mouth | Retracted, compressed, invisible |
| `Emerging` | Sliding out | Elongate + expand, staggered start |
| `Searching` | Looking for target | Idle undulation, waving |
| `Grabbing` | Reaching toward | Extend + curl toward target |
| `Attacking` | Fast strike | Rapid extension, grab, retract |
| `Retracting` | Pulling back | Compress + shorten, hide |

### State Machine Flow

```
Hidden → Emerging → Searching → Grabbing → Retracting → Hidden
                      ↓
                  Attacking → Retracting
```

---

## REQ-TENT-08: Slime/Saliva Effects

**Priority:** P2 | **Phase:** 19.4 (optional)

### Description
Wet stringers and saliva effects for emerging tentacles.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 08-01 | Stringer geometry | Thin strands between mouth and tentacle |
| 08-02 | Stringer dynamics | Stretch and break realistically |
| 08-03 | Drool particles | Drip from tentacle tips |
| 08-04 | Surface wetness | Higher spec where wet |
| 08-05 | Animated | Stringers stretch during emergence |

### Technical Approach
- Geometry Nodes stringer generation
- Particle system for drips
- Material blend for wet zones

---

## Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Viewport generation | < 100ms for single tentacle |
| NFR-02 | Export time | < 30s for 6 tentacles with LODs |
| NFR-03 | UE runtime | 60fps with 6 tentacles on screen |
| NFR-04 | Memory | < 50MB per tentacle at LOD0 |

### Compatibility

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-05 | Blender version | 5.0+ |
| NFR-06 | UE version | 5.3+ |
| NFR-07 | Rigify compatibility | Works with Rigify face rigs |
| NFR-08 | Auto-Rig Pro | Compatible with ARP exports |

### Quality

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-09 | Deformation quality | No visible collapse at joints |
| NFR-10 | Texture resolution | Up to 4K baking supported |
| NFR-11 | Morph target precision | < 1mm vertex drift |

---

## Dependencies

### Internal Dependencies
- `lib/pipeline/` - Stage pipeline framework
- `lib/nodekit/` - Geometry node utilities
- `lib/materials/` - Material system
- `lib/export/` - FBX export utilities

### External Dependencies
- Blender 5.0+
- Unreal Engine 5.3+ (for import)
- Rigify addon (optional, for face rig)

---

## Glossary

| Term | Definition |
|------|------------|
| **Spline IK** | Inverse kinematics using a curve to control bone chain |
| **Shape Key** | Blender term for morph target (stored mesh deformation) |
| **Morph Target** | UE term for shape key |
| **SSS** | Subsurface scattering - light penetrating translucent materials |
| **Stringer** | Thin strand of saliva/slime connecting surfaces |
| **Body Horror** | Horror subgenre focusing on grotesque body transformation |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-25 | Initial requirements from research phase |
