# Blender 5.x Node Tool Patterns

Reusable geometry node and shader patterns extracted from advanced tutorials.

---

## Table of Contents

1. [Animation Patterns](#1-animation-patterns)
2. [Instance Patterns](#2-instance-patterns)
3. [Material Patterns](#3-material-patterns)
4. [UV Patterns](#4-uv-patterns)
5. [Proximity Patterns](#5-proximity-patterns)
6. [Loop Patterns](#6-loop-patterns)

---

## 1. Animation Patterns

### Perfect Rotation Loop

**Problem:** 360° doesn't create perfect loop
**Solution:** Use `pi` multiplier

```
Scene Time → Seconds
    → Math (Multiply, 2*pi/duration)
    → Rotation input

# For N-frame animation at 24fps:
Factor = 2 * pi / (N / 24)

# Or keyframe method:
Frame 0: 0
Frame N: 2 * pi
```

**Node Setup:**
```
[Scene Time] → [Multiply: 2*pi] → [Multiply: speed_factor] → [Rotation]
```

### Index-Driven Sequential Animation

**Creates:** Wave/cascade effect across instances

```
[Index]
    → [Math: Add, offset]
    → [Math: Multiply, spacing]
    → [Math: Sin/Cos] (optional, for wave)
    → [Transform]
```

**Parameters:**
- `offset`: Shifts start point
- `spacing`: Distance between elements
- `sin/cos`: Creates smooth wave vs linear step

### Phase-Offset Wave Texture

```
[Scene Time] → [Multiply: 20*pi] → [Wave Texture: Phase Offset]

# Creates fast-moving wave
# Adjust multiplier for speed
```

---

## 2. Instance Patterns

### Radial Array with Alignment

**Creates:** Objects arranged in circle, facing center

```
[Curve Circle]
    → [Instance on Points]
        - Instance: Your Object
    → [Align Rotation to Vector]
        - Vector: [Normal]
        - Axis: Y
    → [Rotate Instances] (optional, for spiral)
```

**Key Insight:** `Normal` provides outward-facing direction

### Index-Based Rotation Spiral

**Creates:** Spiral arrangement of instances

```
[Index]
    → [Math: Multiply, factor]
    → [Combine XYZ: X=rotation]
    → [Rotate Instances]

# factor controls spiral tightness:
# 3 = clean spiral
# 5 = more rotations
```

### Gradient Scale Distribution

**Creates:** Size variation based on position

```
[Position]
    → [Vector Math: Multiply, scale]
    → [Gradient Texture: Spherical]
    → [Float Curve] (shape the gradient)
    → [Map Range]
        - From Min: 0
        - From Max: 1
        - To Min: min_scale
        - To Max: max_scale
    → [Combine XYZ] (X and Y only)
    → [Instance on Points: Scale]
```

### Wireframe Conversion

**Creates:** Wireframe from solid geometry

```
[Mesh]
    → [Mesh to Curve]
    → [Curve to Mesh]
        - Profile: [Curve Circle]
        - Radius: 0.1 (adjust for thickness)
    → [Join Geometry] (merge with original for fill)
    → [Set Material]
```

**Optional:** Add original mesh before Join for filled center

---

## 3. Material Patterns

### Emission-Only Setup

**For:** Abstract/generative/motion graphics

```
Shader:
[Light Path: Is Camera Ray] → [Mix Shader]
    - Fac: Is Camera Ray
    - Shader 1: [Emission] (color, strength)
    - Shader 2: [Transparent BSDF]

# Or simpler:
[Emission] → [Material Output: Surface]
```

**World Setup:**
```
[Background: Color=Black, Strength=1] → [World Output]
```

### Proximity-Based Color (Shader)

**Uses:** New Blender 5.1 Raycast Node

```
[Texture Coordinate: Object]
    → [Raycast]
        - Source: Object name
        - Length: max_distance
    → [Hit Distance]
    → [Map Range]
    → [Mix RGB] or [Color Ramp]
    → [Material Output]
```

**Applications:**
- Contact shadows
- Color bleeding
- Edge glow
- Distance fog

### UV-Mapped Wave Texture

```
[Attribute: "UV"]
    → [Wave Texture: Vector]
    → [Color Ramp]
    → [Emission: Color]

# Animate:
[Scene Time] → [Multiply: 20*pi] → [Wave Texture: Phase Offset]
```

---

## 4. UV Patterns

### Pass UV from Geometry Nodes to Shader

**Problem:** UVs don't automatically pass through Geo Nodes
**Solution:** Store Named Attribute

**Geometry Nodes:**
```
[Geometry with UV Map]
    → [Store Named Attribute]
        - Data Type: 2D Vector
        - Domain: Face Corner
        - Name: "UV" (or custom name)
        - Value: [UV Map] output
    → [Output]
```

**Shader:**
```
[Attribute: "UV"]
    → [Any Texture: Vector]
```

**Critical:** Domain must be **Face Corner**, not Point

---

## 5. Proximity Patterns

### Geometry Proximity Scale

**Creates:** Objects shrink/grow near target

```
[Distribute Points on Faces]
    → [Geometry Proximity]
        - Target: [Target Object]
        - Source Position: [Position]
    → [Distance]
    → [Map Range]
        - From Min: 0
        - From Max: max_distance
        - To Min: min_scale
        - To Max: max_scale
    → [Instance on Points: Scale]
```

### Edge Gravity (Set Extension)

**Creates:** Particles cluster near edges

```
[Distribute Points on Faces]
    → [Geometry Proximity: Target Edges]
    → [Distance]
    → [Map Range: 0-1 → 0-1]
    → [Noise Texture]
    → [Mix Vector]
        - A: [Position]
        - B: [Nearest Edge Position]
        - Fac: proximity_factor
    → [Set Position]
```

---

## 6. Loop Patterns

### Perfect Loop Checklist

```
✓ Linear interpolation (Preferences → Animation)
✓ Start/end values equal or offset by known amount
✓ Rotation uses pi (not degrees)
✓ Test at frame 0 and frame N-1
✓ Frame count divisible by desired speed
```

### Position-Based Loop

```
Frame 0:  position = start_value
Frame N:  position = start_value + offset

# offset must equal movement per cycle
# Example: move 2 units, return to start
start = -5
end = 5
offset = 10 (total movement = 2*5 = return distance)
```

### Rotation Loop

```
Frame 0:  rotation = 0
Frame N:  rotation = 2 * pi

# For multiple rotations:
rotation = M * 2 * pi

# For partial rotations:
rotation = fraction * 2 * pi
```

### Texture Offset Loop

```
Frame 0:  offset = 0
Frame N:  offset = 1 (or integer for repeating texture)

# Works for:
# - Mapping node offset
# - Texture phase
# - Wave texture offset
```

---

## 7. Compositor Patterns

### Bloom Glow

**For:** Emission materials that need actual glow

```
[Render Layers]
    → [Glare]
        - Type: Bloom
        - Threshold: adjust to taste
    → [Composite]
```

### Chromatic Aberration with Color Control

```
[Render Layers]
    → [Chromatic Aberration]
        - Factor: strength
    → [Color Ramp] (optional: simplify to single color)
    → [Composite]
```

**Pro Tip:** Color Ramp after Chromatic creates "bonus lines" effect without full chromatic look

### Film Grain

```
[Render Layers]
    → [Glare]
    → [Chromatic Aberration]
    → [Film Grain]
        - Luminance: high
        - Chroma Noise: low
        - Animate: ON
    → [Composite]
```

---

## 8. Quick Reference

### Common Node Connections

| From | To | Purpose |
|------|-----|---------|
| Index | Math → Rotation | Sequential animation |
| Position | Vector Math → Gradient | Location-based effects |
| Normal | Align Rotation | Face-instances |
| UV Map | Store Attribute | Pass to shader |
| Scene Time | Multiply → Texture | Animation |
| Distance | Map Range | Proximity effects |

### Key Multipliers

| Effect | Value |
|--------|-------|
| Full rotation | `2 * pi` |
| Half rotation | `pi` |
| Quarter rotation | `pi / 2` |
| Degree to radian | `degree * (pi/180)` |

### Domain Quick Reference

| Data Type | Domain |
|-----------|--------|
| UV coordinates | Face Corner |
| Vertex colors | Face Corner |
| Point positions | Point |
| Face area | Face |
| Edge length | Edge |

---

## 9. Troubleshooting

### Issue: Rotation doesn't loop
**Solution:** Use `2 * pi` for full rotation, not 360

### Issue: Index animation is choppy
**Solution:** Add `Math: Sin/Cos` for smoothing

### Issue: UV not working in shader
**Solution:** Use Store Named Attribute (Face Corner domain)

### Issue: Instances not facing center
**Solution:** Use Align Rotation to Vector with Normal

### Issue: Wave texture scrambled
**Solution:** Pass UV via Store Named Attribute + Attribute node

### Issue: Glow not showing
**Solution:** Enable Bloom in compositor, increase Emission Strength

---

*Extracted from DECODED, Ducky 3D, Polygon Runway tutorials - February 2026*
