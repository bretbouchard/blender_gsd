# Blender Hair & Fur Knowledge Base

**Comprehensive guide to procedural hair and fur techniques using Geometry Nodes and Hair Curves.**

*Compiled from top tutorials, official documentation, and community resources (Blender 3.3 - 5.1)*

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Top 20 Hair/Fur Tutorials](#top-20-hairfur-tutorials)
3. [Blender Hair System Overview](#blender-hair-system-overview)
4. [Geometry Nodes Hair Patterns](#geometry-nodes-hair-patterns)
5. [Hair Curve Nodes Reference](#hair-curve-nodes-reference)
6. [Procedural Fur Techniques](#procedural-fur-techniques)
7. [Material & Shader Setup](#material--shader-setup)
8. [Plugins & Assets](#plugins--assets)
9. [Quick Reference Cards](#quick-reference-cards)

---

## Executive Summary

Blender's hair system has evolved from traditional particle systems to a modern **Curve-based Hair System** deeply integrated with **Geometry Nodes**. This enables fully procedural hair/fur generation, styling, and simulation.

### Key Evolution

| Version | Hair System | Key Features |
|---------|-------------|--------------|
| **Pre-3.3** | Particle System | Hair particles, limited procedural control |
| **3.3 LTS** | Hair Curves (New) | Curve-based, geometry nodes integration begins |
| **3.5+** | Full GN Integration | 26+ hair nodes, Essentials asset library |
| **4.0+** | Deep GN Integration | Curve editor, custom node trees for hair |
| **5.0+** | Advanced GN | Closures, bundles, simulation improvements |

### Why Geometry Nodes for Hair?

1. **Non-destructive** - Edit parameters anytime
2. **Procedural** - Generate complex styles from simple inputs
3. **Reusable** - Create node groups for common styles
4. **Customizable** - Build custom tools without Python
5. **Performance** - Optimized for real-time preview

---

## Top 20 Hair/Fur Tutorials

### Essential Tutorials (Ranked by Quality/Relevance)

| # | Title | Creator | Level | Focus | Source |
|---|-------|---------|-------|-------|--------|
| 1 | **Procedural Fur System** (Nodevember) | CGMatter | Advanced | Spiral-based fur, clumping | [YouTube](https://youtube.com/watch?v=yrUiVsdImLI) |
| 2 | **Get Into Geometry Node Hair Fast** | Martin Klekner | Beginner-Intermediate | Guide curves, interpolation | YouTube |
| 3 | **Blender Hair & Fur Complete Workflow** | Udemy | All Levels | Classic + GN workflows | [Udemy](https://www.udemy.com/course/blender-hair-fur-workflow/) |
| 4 | **Dynamic Hair with Proximity Nodes** | Bilibili | Intermediate | Proximity effects, empties | [Bilibili](https://www.bilibili.com/video/BV1wK28Y5EPb) |
| 5 | **Curve Hair to Mesh Physics** | Community | Intermediate | Physics simulation | [Bilibili](https://m.bilibili.com/video/BV15H1yYiE7Z) |
| 6 | **Rig and Simulate Hair Curves 3.3** | Blender Studio | Intermediate | Hair physics | YouTube |
| 7 | **Hair Curves Workshop** | Blender Studio | All Levels | Official workflow | blender.org |
| 8 | **Medusa Nodes Tutorial** | Plugin Creator | All Levels | Procedural hair system | Included with plugin |
| 9 | **Stylized Hair Pro Tutorial** | Plugin Creator | All Levels | Stylized techniques | Included with plugin |
| 10 | **Erindale Geometry Nodes Hair** | Erindale | Advanced | Advanced GN techniques | YouTube |
| 11 | **Cartesian Caramel Hair** | Cartesian Caramel | Advanced | Rigging, simulation | YouTube |
| 12 | **Johnny Matthews GN Hair** | Johnny Matthews | Beginner | Fundamentals | YouTube |
| 13 | **DefoQ Hair System Tutorial** | DefoQ | All Levels | Realistic fur | Community |
| 14 | **Hair Tool v4.0 Tutorial** | Plugin Creator | All Levels | Card generation | Included with plugin |
| 15 | **Facial Hair Toolkit** | Plugin Creator | Intermediate | Beards, eyebrows | Included with plugin |
| 16 | **3D Hair Brush Tutorial** | Plugin Creator | Beginner | Drawing workflow | Included with plugin |
| 17 | **B-GEN Groom Tutorial** | B-GEN | All Levels | Brush tools, physics | [Bilibili](https://m.bilibili.com/video/BV164dnY3EmJ) |
| 18 | **Blender 5.0 Hair Features** | Multiple | Intermediate | New features overview | YouTube/Bilibili |
| 19 | **Eyelashes with GN Curves** | Community | Beginner | Eyelash creation | [Bilibili](https://m.bilibili.com/video/BV175QSYMESs) |
| 20 | **Animal Fur Demo** | Simon Thommes | Advanced | Realistic animal fur | Blender Demo Files |

### Official Demo Files

| File | Creator | Description |
|------|---------|-------------|
| **GEOMETRY NODES Hair Styles** | Daniel Bystedt | Female hair style examples |
| **Animal Fur Examples** | Simon Thommes | Animal fur with various techniques |

**Download:** [blender.org/download/demo-files](https://www.blender.org/download/demo-files/)

---

## Blender Hair System Overview

### Two Approaches to Hair/Fur

#### 1. Traditional Particle Hair (Legacy)

```
Object → Particle System → Hair
    ├── Children (interpolated)
    ├── Dynamics (cloth sim)
    └── Manual grooming
```

**Pros:**
- Mature system
- Good physics
- Brush-based grooming

**Cons:**
- Limited procedural control
- Destructive workflow
- No geometry nodes access

#### 2. Geometry Nodes Hair Curves (Modern)

```
Object → Hair Curves → Geometry Nodes
    ├── Generate Hair Curves
    ├── Interpolate Hair Curves
    ├── Deformation Nodes
    │   ├── Clump
    │   ├── Curl
    │   ├── Frizz
    │   └── Noise
    └── Custom Node Trees
```

**Pros:**
- Fully procedural
- Non-destructive
- Deep GN integration
- Custom tools possible

**Cons:**
- Steeper learning curve
- Newer system (still evolving)

### Hair Curve Data Structure

```
Hair Curves
    ├── Points (positions along curve)
    ├── Radius (per-point thickness)
    ├── Surface UV (attachment point)
    └── Custom Attributes
        ├── Color
        ├── Roughness
        └── Any named attribute
```

---

## Geometry Nodes Hair Patterns

### Pattern 1: Spiral-Based Fur Clumps (CGMatter)

**Best for:** Wool, fur, fuzzy surfaces

```
Spiral Node
    ├── Start Radius: Random (0.5-1.5) × index
    ├── Rotations: Random (0.5-1.2) × 8
    ├── Height: Random (2-1)
    ├── End Radius: Random (6.3-7)
    └── Trim Curve: Random (0.5-1)
        │
        └── Distort Node
            ├── Strength: 10%
            ├── Scale: Low frequency
            └── Seed: Index (independent behavior)
                │
                └── Curve to Mesh
                    ├── Profile: Curve Circle (res: 3)
                    └── Scale: 0.03-0.08
```

**Key Parameters:**

| Parameter | Range | Effect |
|-----------|-------|--------|
| Start Radius | 0.5-1.5 | Base thickness |
| Rotations | 4-12 | Curl tightness |
| Height | 1-3 | Strand length |
| End Radius | 0.05-0.2 | Tip sharpness |
| Distort Strength | 0.05-0.15 | Organic variation |

**Clump Creation:**
```
1. Create 3+ clump variants with different seeds
2. Geometry to Instance each variant
3. Join instances into collection
4. Instance on Points with Pick Instance
```

### Pattern 2: Guide Curves Workflow

**Best for:** Hairstyles, controlled direction

```
1. Draw Guide Curves (manually or procedurally)
    │
    └── Interpolate Hair Curves
        ├── Guides: Your drawn curves
        ├── Surface: Scalp mesh
        ├── Points per Guide: 10-100
        └── Interpolation: Smooth/Cubic
            │
            └── Deformation Chain
                ├── Clump Hair Curves
                ├── Curl Hair Curves
                └── Frizz Hair Curves
```

**Node Setup:**
```
Guide Curves Object
    │
    └── Object Info
        └── Interpolate Hair Curves
            ├── Surface: Scalp mesh
            ├── Curves: Guide curves
            ├── Amount: 50-500
            └── Interpolation: Smooth
```

### Pattern 3: Procedural Distribution

**Best for:** Fur, grass, generic coverage

```
Surface Mesh
    │
    └── Distribute Points on Faces
        ├── Density: 100-1000
        ├── Seed: Random
        └── Selection: Vertex group (optional)
            │
            └── Generate Hair Curves
                ├── Surface: Surface Mesh
                ├── Points: Distributed points
                ├── Curve Length: 0.1-0.5
                └── Profile: Taper curve
```

### Pattern 4: Index-Based Variation

**Critical for natural-looking hair:**

```
Index → Random Value
    ├── Seed: Index
    └── Range: 0-1
        │
        ├── → Length variation
        ├── → Curl variation
        ├── → Clump strength
        └── → Rotation offset
```

**Why it works:** Same index always returns same random value, ensuring consistency across parameters while varying between strands.

### Pattern 5: Clump Convergence (Advanced)

**Creates natural grouping:**

```
Distribute Points (convergence targets)
    │
    └── For Each Zone / Repeat Zone
        └── Sample Nearest Surface
            └── Blend hair positions toward target
                └── Smooth falloff by distance
```

---

## Hair Curve Nodes Reference

### Generation Nodes

| Node | Purpose | Key Inputs |
|------|---------|------------|
| **Generate Hair Curves** | Create curves from points | Surface, Points, Length, Profile |
| **Interpolate Hair Curves** | Create from guides | Guides, Surface, Amount |
| **Duplicate Hair Curves** | Clone existing curves | Count, Seed |

### Deformation Nodes

| Node | Purpose | Key Parameters |
|------|---------|----------------|
| **Clump Hair Curves** | Group strands together | Clump Factor, Shape |
| **Curl Hair Curves** | Add spiral curls | Curl Radius, Curl Frequency |
| **Frizz Hair Curves** | Add frizz/flyaways | Frizz Amount, Frequency |
| **Smooth Hair Curves** | Smooth out kinks | Smooth Factor, Iterations |
| **Trim Hair Curves** | Cut to length | Length, Selection |
| **Noise Hair Curves** | Add noise displacement | Scale, Factor |
| **Roll Hair Curves** | Roll around axis | Angle |
| **Braid Hair Curves** | Create braids | Braid Parameters |

### Utility Nodes

| Node | Purpose |
|------|---------|
| **Attach Hair Curves to Surface** | Re-attach to new surface |
| **Set Hair Curve Profile** | Control thickness along curve |
| **Redistribute Curve Points** | Even point distribution |
| **Restore Curve Segment Length** | Maintain length after deformation |

### Read Nodes

| Node | Output |
|------|--------|
| **Curve Root Info** | Position, normal at root |
| **Curve Tip Info** | Position at tip |
| **Curve Segment Info** | Per-segment data |
| **Attachment Info** | UV coordinates on surface |

---

## Procedural Fur Techniques

### Technique 1: Multi-Layer Fur

**Creates realistic depth:**

```
Layer 1: Undercoat (dense, short)
    ├── Length: 0.05-0.1
    ├── Density: 1000+
    └── Curl: High

Layer 2: Guard hairs (longer, sparse)
    ├── Length: 0.2-0.4
    ├── Density: 100-200
    └── Curl: Low

Layer 3: Whiskers (very long, very sparse)
    ├── Length: 0.5-1.0
    ├── Density: 10-20
    └── Curl: None
```

### Technique 2: Directional Flow

**Controls fur direction:**

```
Curve Guide Object
    │
    └── Sample Nearest Surface
        └── Get tangent direction
            └── Align hair rotation
                └── Add noise variation
```

### Technique 3: Length Variation by Region

**Natural length patterns:**

```
Position → Separate XYZ
    └── Z (height)
        └── Map Range
            ├── Belly: Short (0.05)
            ├── Sides: Medium (0.15)
            └── Back: Long (0.3)
                └── → Hair Length
```

### Technique 4: Density Control

**Procedural density variation:**

```
Texture (Noise/Musgrave)
    │
    └── Math (Greater Than)
        └── Threshold controls density
            └── Selection for Distribute Points
```

### Technique 5: Color Variation

**Store color in attributes:**

```
Random Value (per curve)
    │
    └── Color Ramp
        ├── Root: Dark
        ├── Mid: Base color
        └── Tip: Lighter
            │
            └── Store Named Attribute
                ├── Name: "hair_color"
                └── Domain: Curve
```

**In Shader:**
```
Attribute Node ("hair_color")
    └── Hair BSDF Color
```

---

## Material & Shader Setup

### Principled Hair BSDF

**Works on ANY geometry (not just particle hair):**

```
Material Output
    └── Principled Hair BSDF
        ├── Parametrization: Melanin (intuitive)
        │   ├── 0.0 = White
        │   ├── 0.3 = Blonde
        │   ├── 0.5 = Brown
        │   └── 1.0 = Black
        ├── Roughness: 0.2-0.5 (fiber texture)
        ├── Radial Roughness: 0.3-0.6 (cross-section)
        └── Coat: Optional shine
```

### Emission Fur (Stylized)

```
Material Output
    └── Emission
        ├── Color: Attribute "hair_color" or solid
        └── Strength: 1.0-2.0
            └── No BSDF needed
```

### Dual Material Setup (Skin + Hair)

```
In Geometry Nodes:
    ├── Skin geometry → Set Material (object BSDF)
    └── Hair geometry → Set Material (hair BSDF)

In Shader:
    ├── Object Material: Rough skin BSDF
    └── Hair Material: Principled Hair BSDF
        └── Match colors for seamless look
```

### Transmission for Thin Hair

```
Principled BSDF
    ├── Transmission: 0.3-0.5
    ├── Roughness: 0.1-0.2
    └── IOR: 1.45
        └── Creates translucent effect
```

---

## Plugins & Assets

### Geometry Nodes-Based Plugins

| Plugin | Version | Price | Description |
|--------|---------|-------|-------------|
| **Stylized Hair Pro** | 4.0.1 | Paid | Stylized hair with GN |
| **Medusa Nodes** | 1.1.0 | Paid | Full procedural system |
| **DefoQ Hair System** | - | Free | Realistic hair presets |
| **Hair Tool** | 4.4.0 | Paid | Card generation, auto UV |
| **3D Hair Brush** | 3.2 | Paid | Drawing workflow |
| **Facial Hair Toolkit** | 2.0 | Paid | Beards, eyebrows |
| **Fluffy Maker** | 1.0 | Paid | One-click cartoon fur |
| **HairTG** | 2.7.2 | Paid | Blender + Substance |
| **N_Hair_Nodes** | 2 | Free | GN-based system |

### Essentials Asset Library (Built-in)

**26 Hair Assets included in Blender 3.5+:**

| Category | Nodes |
|----------|-------|
| **Generation** | Generate, Interpolate, Duplicate |
| **Deformation** | Clump, Curl, Frizz, Smooth, Trim |
| **Guides** | Clump, Curl, Braid, Children |
| **Utility** | Attach, Profile, Redistribute |

**Access:** Asset Browser → Essentials → Hair

### Free Resources

| Resource | Where |
|----------|-------|
| **Blender Demo Files** | blender.org/download/demo-files |
| **CGMatter Free Nodes** | cgmatter.com/free-nodes |
| **DefoQ Presets** | Community platforms |

---

## Quick Reference Cards

### Spiral Fur Parameters

| Effect | Parameter | Range |
|--------|-----------|-------|
| Curlier | Rotations | 8 → 15 |
| Longer | Height | 1 → 3 |
| Thinner tip | End Radius | 0.1 → 0.05 |
| More variation | Random Range | 0.5-1.5 |
| Organic look | Distort | 10% |

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Too uniform | No randomization | Add index-based variation |
| Clipping | Same Z position | Offset by curve index |
| Bald spots | Low density | Increase to 300-1000 |
| Performance | Too many curves | Use children/interpolation |
| Sharp edges | No smoothing | Add Smooth Hair Curves |
| Unnatural direction | Missing alignment | Use surface normals |

### Performance Tips

| Technique | Impact | Use Case |
|-----------|--------|----------|
| **Children** | 90%+ reduction | Background fur |
| **Interpolation** | 80%+ reduction | Hairstyles |
| **Baking** | Variable | Heavy GN setups |
| **LOD** | 50-90% | Distance-based |
| **Culling** | 30-50% | Off-screen |

### Hair Node Categories

```
Generation:    Generate, Interpolate, Duplicate
Deformation:   Clump, Curl, Frizz, Noise, Smooth, Trim
Guides:        Clump Guide, Curl Guide, Braid
Utility:       Attach, Profile, Redistribute, Restore
Read:          Root Info, Tip Info, Segment Info, Attachment
```

### Workflow Decision Tree

```
Need hair/fur?
├── Stylized cartoon?
│   └── Use: Spiral Fur Pattern + Emission
├── Realistic animal?
│   └── Use: Multi-layer fur + Principled Hair
├── Human hairstyle?
│   └── Use: Guide Curves + Interpolation
├── Game-ready cards?
│   └── Use: Hair Tool plugin
└── Quick coverage?
    └── Use: Distribute Points + Generate Hair Curves
```

---

## Related Documentation

| Document | Content |
|----------|---------|
| [NODEVEMBER_SYNTHESIS.md](NODEVEMBER_SYNTHESIS.md) | CGMatter fur tutorial details |
| [BLENDER_50_KNOWLEDGE_SYNTHESIS.md](BLENDER_50_KNOWLEDGE_SYNTHESIS.md) | Blender 5.0 features |
| [GENERATIVE_ART_TECHNIQUES.md](GENERATIVE_ART_TECHNIQUES.md) | Seamless loops, emission |
| [GEOMETRY_NODES_KNOWLEDGE.md](GEOMETRY_NODES_KNOWLEDGE.md) | GN fundamentals |

---

## Tutorial Transcript Index

### Hair/Fur Related Transcripts in Repository

| File ID | Title | Creator | Focus |
|---------|-------|---------|-------|
| yrUiVsdImLI | Procedural Fur | CGMatter | Spiral-based fur system |
| DYMEQuYVUAs | Hand Rig | CGMatter | Hair on rigged character |
| 16_creature | Creature Rigging | CGMatter | Creature hair workflow |
| 31_monster | Monster Sculpting | CGMatter | Sculpting with hair |

---

*Compiled from official Blender documentation, tutorial transcripts, and community resources - March 2026*

*Note: Blender 5.0+ introduces Closures and Bundles which enable even more advanced procedural hair systems*
