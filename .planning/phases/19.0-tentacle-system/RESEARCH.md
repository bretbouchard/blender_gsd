# Tentacle System Research Phase

**Phase:** 19.0
**Status:** Research
**Target:** Blender 5.0 → Unreal Engine 5.x Pipeline
**Created:** 2026-02-25
**Updated:** 2026-02-25

---

## Executive Summary

This research phase explores procedural tentacle creation in Blender 5.0 with export to Unreal Engine. The primary use case is **zombie mouth tentacles** - parasitic or mutated appendages that emerge from a character's mouth as part of zombie/creature horror effects.

### Primary Use Case: Zombie Mouth Tentacles

| Behavior | Description |
|----------|-------------|
| **Emerge** | Slide out from between teeth/gums, squeeze through mouth opening |
| **Expand** | Widen once outside the mouth |
| **Writhe** | Idle undulation, searching movement |
| **Grab** | Reach toward and wrap around objects/victims |
| **Retract** | Pull back inside the mouth |

### Horror/Creature Context
- **Part of zombie character rig** - Must integrate with face/mouth skeleton
- **Multiple tentacles** - 2-6 emerging from single mouth (configurable)
- **Size variation** - Mix of thick "main" tentacles and thin "feeler" tentacles
- **Wet/slimy appearance** - Saliva, mucus coating
- **Style options** - Suckers (alien parasite) or smooth (body horror/mutation)

### Visual Reference
```
Zombie Mouth Cross-Section:

         ┌─────────────────────────┐
         │     Upper Jaw/Teeth     │
         │  ─────────────────────  │
         │     ╲    ╲    ╲    ╲    │ ← Tentacles emerging
         │      ╲    ╲    ╲    ╲   │   between teeth
         │       │    │    │    │  │
         │   [Tentacle Array]      │
         │       │    │    │    │  │
         │      ╱    ╱    ╱    ╱   │
         │     ╱    ╱    ╱    ╱    │
         │  ─────────────────────  │
         │     Lower Jaw/Teeth     │
         └─────────────────────────┘
```

---

## Core Requirements

### REQ-TENT-01: Procedural Geometry
- Configurable tentacle length, taper, and segmentation
- Real-time parameter adjustment in viewport
- Deterministic output for consistent results

### REQ-TENT-02: Sucker System
- Control for number of rows and columns
- Size gradient (larger at base, smaller at tip)
- Depth, rim sharpness, spacing controls
- Optional suckers (some tentacles don't have them)

### REQ-TENT-03: Squeeze/Expand Animation
- **Squish through hole** - compress diameter, elongate length
- **Expand** - return to normal or expand beyond
- **Grab/squeeze** - curl around objects
- Smooth interpolation between states

### REQ-TENT-04: Material System
- Procedural skin textures
- Color themes/presets (octopus, alien, mechanical, horror)
- Subsurface scattering for organic look
- Wet/slimy surface option
- Pattern variations (spots, stripes, gradients)

### REQ-TENT-05: Unreal Engine Export
- FBX export with skeleton
- Morph targets (shape keys) for squeeze animations
- Material ID zones for UE materials
- LOD support for game performance

### REQ-TENT-06: Zombie Mouth Integration
- **Mouth anchor point** - Attach tentacle root to mouth interior
- **Jaw deformation** - Optional jaw bulge when tentacles inside
- **Teeth collision** - Tentacles weave between existing teeth
- **Multi-tentacle array** - 2-6 tentacles per character
- **Size variation** - Mix of thick and thin tentacles in same mouth
- **Emergence animation** - Smooth slide-out from mouth
- **Retraction animation** - Smooth slide-back into mouth
- **Saliva/slime connection** - Wet stringers when emerging

---

## Zombie Mouth Integration Research

### Mouth Anatomy Considerations

| Element | Integration Challenge |
|---------|----------------------|
| **Teeth** | Tentacles emerge between teeth, not through them |
| **Gums** | Tentacle base hidden under gum line |
| **Tongue** | May be displaced or replaced by tentacles |
| **Cheeks** | May bulge when tentacles stored inside |
| **Jaw** | Optional: jaw unhinges to allow emergence |

### Attachment Strategy

```
Character Face Rig
    └── Head Bone
        └── Jaw Bone
            └── Mouth_Inside (empty socket)
                ├── Tentacle_Root_01
                │   └── [Tentacle chain]
                ├── Tentacle_Root_02
                │   └── [Tentacle chain]
                └── Tentacle_Root_N
                    └── [Tentacle chain]
```

### Multi-Tentacle Configuration

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Count** | 1-6 | Number of tentacles per character |
| **Distribution** | Uniform/Random | Spacing across mouth |
| **Size Mix** | 0.0-1.0 | Ratio of thick:thin tentacles |
| **Stagger** | 0.0-1.0 | Emergence timing offset |

### Horror-Specific Material Themes

| Theme | Base Color | Veins | Slime | Use Case |
|-------|------------|-------|-------|----------|
| **Rotting** | Gray-green | Dark purple | Yellow-brown | Classic zombie |
| **Parasitic** | Flesh pink | Red | Clear | Alien parasite |
| **Demonic** | Deep red | Black | Black | Supernatural |
| **Mutated** | Pale flesh | Bioluminescent | Green | Radiation/mutation |
| **Decayed** | Bone white | None | Brown | Long-dead zombie |

### Animation States for Zombie Mouth Tentacles

| State | Description | Animation |
|-------|-------------|-----------|
| **Hidden** | Inside mouth, not visible | Retracted, compressed |
| **Emerging** | Sliding out between teeth | Elongate + expand |
| **Searching** | Waving, looking for target | Idle undulation |
| **Grabbing** | Reaching toward object/victim | Extend + curl |
| **Retracting** | Pulling back into mouth | Compress + shorten |
| **Aggressive** | Rapid, jerky movement | Fast undulation |

---

## Technical Research

### 1. Geometry Nodes Approach (Procedural Generation)

**Best For:** Procedural variation, suckers, real-time adjustment
**Limitation:** Must bake for Unreal export

#### Node Structure:
```
Input (Parameters)
    ↓
Curve Line / Bezier Curve (base shape)
    ↓
Resample Curve (segmentation)
    ↓
Set Curve Radius (taper profile)
    ↓
Curve to Mesh (convert to geometry)
    ↓
Subdivision Surface (smooth)
    ↓
Instance on Points (suckers)
    ↓
Realize Instances (bake for export)
    ↓
Output Mesh
```

#### Key Nodes:
| Node | Purpose |
|------|---------|
| `Curve Line` | Base tentacle path |
| `Resample Curve` | Control segment count |
| `Set Curve Radius` | Taper from base to tip |
| `Curve to Mesh` | Convert curve to mesh |
| `Instance on Points` | Place suckers along body |
| `Scale Elements` | Vary sucker sizes |
| `Transform` | Rotate/orient suckers |
| `Realize Instances` | Bake for export |

#### Sucker Placement Strategy:
```
Tentacle Surface → Distribute Points on Faces
                      ↓
                 Point Density (rows × columns)
                      ↓
                 Align to Face Normal
                      ↓
                 Instance Sucker Geometry
                      ↓
                 Scale by Factor (gradient curve)
```

### 2. Spline IK Rigging (Animation)

**Best For:** Bone-based animation, Unreal export
**Advantage:** Native FBX support, industry standard

#### Bone Chain Setup:
```
Root
  └── Tentacle_01
      └── Tentacle_02
          └── Tentacle_03
              └── ... (N bones)
                  └── Tentacle_Tip
```

#### Spline IK Configuration:
| Setting | Value | Purpose |
|---------|-------|---------|
| Chain Length | N bones | Full tentacle |
| Curve | Bezier | Control curve |
| Binding Mode | Curve Center | Predictable deformation |

#### Control Rig:
- **Master Control** - Move entire tentacle
- **Curve Controls** - 3-5 control points for Spline IK curve
- **FK Controls** - Individual bone rotation overrides
- **Tip Control** - Precise end positioning

### 3. Shape Keys (Morph Targets)

**Best For:** Squeeze/expand animations, Unreal morph targets
**Advantage:** Direct UE5 support as morph targets

#### Required Shape Keys:
| Shape Key | Description | Use Case |
|-----------|-------------|----------|
| `Base` | Default tentacle shape | Starting state |
| `Squish_Compress` | Compressed diameter, elongated | Squeezing through hole |
| `Squish_Expand` | Expanded diameter, shortened | Bulging out |
| `Grab_Curl` | Curled tip for gripping | Wrapping around objects |
| `Tense` | Tightened muscles | Alert/ready state |
| `Relaxed` | Soft, droopy | Idle state |

#### Shape Key Workflow:
```python
# Pseudo-code for shape key generation
def create_squeeze_shapekey(mesh, compression_factor):
    for vertex in mesh.vertices:
        # Compress X/Y, extend Z
        vertex.co.x *= compression_factor
        vertex.co.y *= compression_factor
        vertex.co.z /= compression_factor
```

### 4. Curve-Based Deformation (Hole Squeeze)

**Best For:** Dynamic squeeze-through-hole animation

#### Approach:
1. Create hole geometry (circle/rectangle)
2. Add Shrinkwrap modifier to tentacle
3. Target = hole geometry
4. Animate tentacle moving through
5. Shrinkwrap creates squeeze deformation

#### Alternative: Lattice Deformation
```
Lattice around hole area
    ↓
Animate lattice points to squeeze
    ↓
Tentacle deforms through lattice
```

### 5. Material System

#### Subsurface Scattering (SSS) Setup:
```
Principled BSDF
├── Base Color: Procedural mix (skin tones)
├── Subsurface Weight: 0.1-0.4 (organic)
├── Subsurface Radius: RGB (blood/flesh colors)
├── Subsurface Color: Inner flesh tint
├── Roughness: 0.3-0.6 (wet to dry)
└── Normal: Bump/displacement for detail
```

#### Procedural Texture Layers:
| Layer | Node | Purpose |
|-------|------|---------|
| Base Color | Noise + Color Ramp | Skin tone variation |
| Pattern | Voronoi + Math | Spots, cells |
| Veins | Wave Texture | Subsurface veins |
| Bump | Noise + Bump | Surface irregularity |
| Wet Layer | Layer Weight + Mix | Specular highlights |

#### Color Theme Presets:
| Theme | Base | Accent | SSS |
|-------|------|--------|-----|
| Octopus | Pink/Coral | Purple spots | Red |
| Alien | Green/Teal | Bioluminescent | Cyan |
| Horror | Pale/Flesh | Red veins | Deep red |
| Mechanical | Dark metal | Orange glow | None |
| Deep Sea | Dark purple | Blue glow | Blue |

---

## Unreal Engine Export Considerations

### FBX Export Settings:
| Setting | Value | Reason |
|---------|-------|--------|
| Object Types | Armature, Mesh | Skeleton + geometry |
| Shape Keys | ✓ Enabled | Morph targets |
| Apply Modifiers | ✓ (except Armature) | Bake geometry |
| Skin | ✓ Enabled | Bone weights |
| Smoothing | Face | Normals |

### Material Export:
1. **Bake procedural textures** to image maps
2. **Export material zones** as vertex color
3. **Create UE materials** from baked maps
4. **Morph targets** carry shape animations

### LOD Strategy:
| LOD | Triangles | Use Case |
|-----|-----------|----------|
| LOD0 | 100% | Close-up hero |
| LOD1 | 50% | Mid-distance |
| LOD2 | 25% | Far distance |
| LOD3 | 12% | Very far |

---

## Reference Tutorials

### Primary Tutorial:
**Grant Abbitt - Alien Tentacle Animation (5+ hours)**
- Platform: Udemy / various
- Topics: Geometry Nodes, procedural creatures, animation
- URL: Referenced in Chinese tutorial sites (sohu.com, bilibili)

### Key Techniques from Tutorials:
1. **Non-destructive workflow** - Keep everything procedural
2. **Geometry Nodes instancing** - Efficient sucker placement
3. **Weight painting** - Control deformation zones
4. **Loop animation** - Idle movement cycles
5. **Noise deformation** - Organic movement variation

---

## Fine Points of Tentacle Anatomy

### Biological Reference (Octopus/Squid):
| Feature | Description |
|---------|-------------|
| **Muscular Hydrostat** | No bones, pure muscle control |
| **Taper Profile** | Thick base (2x diameter) to thin tip |
| **Sucker Arrangement** | Alternating rows, not straight columns |
| **Sucker Anatomy** | Cup + rim + papillae (small bumps) |
| **Skin Texture** | Papillae, chromatophores, smooth zones |
| **Flexibility** | Can bend at any point along length |

### Sucker Details:
```
Sucker Anatomy:
    ┌─────────────┐  ← Rim (raised edge)
    │   ○ ○ ○     │  ← Papillae (grip bumps)
    │             │
    │   (cup)     │  ← Cup depth
    │             │
    └─────────────┘

Size Gradient:
    Base ████████░░░░░░░░░░░░ Tip
    Size: Large → Medium → Small → Tiny
```

### Movement Characteristics:
- **Undulation** - Wave-like motion along body
- **Curling** - Tip can curl 360°+
- **Extension** - Can stretch 1.5-2x length
- **Compression** - Can compress to 0.5x diameter
- **Twisting** - Can rotate along axis

---

## Proposed Module Structure

```
lib/tentacle/
├── __init__.py              # Package exports
├── types.py                 # TentacleConfig, SuckerConfig, MaterialTheme, ZombieMouthConfig
├── geometry/
│   ├── __init__.py
│   ├── body.py              # TentacleBodyGenerator (curve-based)
│   ├── taper.py             # TaperProfile, taper functions
│   └── segments.py          # Segmentation controls
├── suckers/
│   ├── __init__.py
│   ├── generator.py         # SuckerGenerator
│   ├── placement.py         # Row/column placement logic
│   └── geometry.py          # Sucker mesh creation
├── animation/
│   ├── __init__.py
│   ├── rig.py               # Spline IK rig creation
│   ├── shape_keys.py        # Squeeze/expand shape keys
│   ├── controls.py          # Control rig setup
│   └── states.py            # Zombie animation states (hidden, emerging, searching, etc.)
├── materials/
│   ├── __init__.py
│   ├── skin.py              # Procedural skin shader
│   ├── themes.py            # Color theme presets
│   ├── horror.py            # Horror-specific themes (rotting, parasitic, etc.)
│   ├── slime.py             # Saliva/slime stringers and wet effects
│   └── baker.py             # Texture baking for export
├── zombie/
│   ├── __init__.py
│   ├── mouth_attach.py      # Attach tentacles to character mouth
│   ├── multi_array.py       # Multi-tentacle configuration
│   └── face_integration.py  # Integration with face rig
└── export/
    ├── __init__.py
    ├── fbx.py               # Unreal FBX export
    └── lod.py               # LOD generation

configs/tentacle/
├── presets.yaml             # Tentacle presets (octopus, alien, etc.)
├── themes.yaml              # Material theme definitions
├── horror_themes.yaml       # Horror-specific material themes
├── zombie_presets.yaml      # Zombie mouth configurations
└── export.yaml              # Export settings
```

---

## Open Questions

### For Discussion:
1. **Sucker Style** - Realistic (with papillae) or stylized (smooth cups) or **none** (body horror smooth)?
2. **Animation Complexity** - Full spline IK or simplified bone chain?
3. **Material Depth** - Full procedural or bake-to-texture workflow?
4. **Multi-Tentacle** - ✅ CONFIRMED - Support for arrays/groups (2-6 per zombie)
5. **Integration** - Connect to existing cinematic system?

### Zombie-Specific Questions:
1. **Teeth Style** - Do tentacles emerge between existing teeth, or are teeth removed/replaced?
2. **Jaw Behavior** - Does jaw unhinge when tentacles emerge, or just open wide?
3. **Saliva Effects** - Include slime stringers/drool as part of system?
4. **Tongue** - Keep tongue visible or replace with tentacle cluster?
5. **Cheek Bulge** - Animate cheek deformation when tentacles stored inside?

### Technical Decisions:
1. **Geometry Nodes vs Mesh Generation** - Which is primary?
2. **Bone Count** - How many bones for typical tentacle? (10? 20? 50?)
3. **Shape Key Count** - How many morph targets for squeeze?
4. **LOD Levels** - How many LODs for game use?
5. **Face Rig Integration** - Connect to Rigify face rig or custom?

---

## Next Steps

After this research phase:

1. **Define Requirements Document** - `REQUIREMENTS_TENTACLE.md`
2. **Create Phase Plans** - Break into implementation phases
3. **Prototype** - Quick proof-of-concept in Blender
4. **Iterate** - Refine based on testing

---

## References

- Blender 5.0 Geometry Nodes documentation
- Unreal Engine 5 FBX import pipeline
- Octopus anatomy references
- Grant Abbitt tentacle tutorial series
- Compify addon (projection techniques)
- Rigify tentacle rig templates
