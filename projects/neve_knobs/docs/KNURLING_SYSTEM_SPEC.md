# Knob Knurling System Specification

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| Zone Controls (z_start, z_end, fade) | Implemented | `neve_knob_gn.py` v2 |
| Profile Control (flat/round/sharp) | Implemented | `neve_knob_gn.py` v2 |
| Ridge Count | Implemented | |
| Ridge Depth | Implemented | |
| Orientation/Slant | Not implemented | Future enhancement |
| Edge Bevel | Not implemented | Future enhancement |

---

## Problem Statement

The current knurling implementation in `/Users/bretbouchard/apps/schill/Knobs/knob.blend` has:
- Confusing zone parameters (Knurl Top, Knur Bottom - unclear what they do)
- Inputs/values potentially reversed
- Unpredictable bevel behavior
- No clear control over knurl profile shape
- Loose control over depth and tape

## Required Knurling Controls

### 1. **Zone Controls** (Where knurling appears) - IMPLEMENTED
- `knurl_z_start`: Z position where knurling begins (normalized 0-1, 0.0 = bottom of skirt)
- `knurl_z_end`: Z position where knurling ends (normalized 0-1, 1.0 = top of cap)
- `knurl_fade`: Smooth transition distance at edges (0 = hard edge, >0 = gradual fade)

### 2. **Pattern Controls** (What the knurl looks like)
- `ridge_count`: Number of ridges around circumference (e.g., 24, 32, 48) - IMPLEMENTED
- `ridge_depth`: How deep/wide the ridges are (e.g., 0.0008 - 0.002 meters) - IMPLEMENTED
- `knurl_profile`: Shape of each ridge - IMPLEMENTED
  - 0 = flat bottom (trapezoid) - Neve style
  - 0.5 = rounded (sinusoidal)
  - 1 = sharp V (triangular)

### 3. **Orientation Controls** - NOT IMPLEMENTED
- `knurl_style`: Pattern direction
  - 0 = vertical lines (standard) - currently only option
  - 1 = diamond/cross pattern
  - 2 = horizontal rings
- `knurl_slant`: Angle of knurl lines (0 = vertical, 45 = diagonal)

### 4. **Edge Treatment** - NOT IMPLEMENTED
- `knurl_top_edge`: How knurling ends at top
  - 0 = sharp cutoff
  - 1 = beveled fade
  - 2 = rounded cap
- `knurl_bottom_edge`: How knurling ends at bottom
  - 0 = sharp cutoff
  - 1 = beveled fade
  - 2 = rounded cap

## Implementation Details

### Current Implementation (neve_knob_gn.py)

The knurling is implemented using Geometry Nodes with real mesh displacement:

```
1. Calculate normalized Z position (0 = bottom of skirt, 1 = top of cap)
2. Build zone mask using smoothstep for soft edges (or hard edges if fade=0)
3. Calculate angular position around Z axis using atan2(x, y)
4. Create sawtooth pattern based on ridge_count
5. Generate three profile types: flat, round, sharp
6. Interpolate between profiles based on knurl_profile value
7. Apply zone mask to displacement
8. Scale by ridge_depth and displace along normals
```

### Parameter Reference

```yaml
# Zone Controls
knurl_z_start: 0.0    # Start at bottom (0.0 = bottom of skirt)
knurl_z_end: 0.6      # End partway up (1.0 = top of cap)
knurl_fade: 0.05      # Soft transition at edges (0 = hard edge)

# Profile
knurl_profile: 0.0    # 0=flat, 0.5=round, 1=sharp
```

## Reference: Real Knob Knurling Types

### Neve Style (Target)
- Vertical parallel lines
- Flat-bottom grooves (trapezoidal)
- Covers grip section only
- Clean edges, no fade

### Other Common Styles
- **Diamond**: Cross-hatched pattern
- **Ring**: Horizontal ridges
- **Soft**: Rounded grooves
- **Sharp**: V-shaped grooves

---

## Original Blend File Analysis (Reference)

### Existing Parameters (WR_Knob_Generator_SSL.005)
```
Knurl Amount: 0 (currently unused)
Knurl Frequency: 28.0 (ridge counts)
Knurl Top: 0.0 (unclear purpose)
Knur Bottom: 0.0 (unclear purpose)
```

### Existing Node Structure
```
Cylinder -> Extrude Mesh -> Scale Elements -> (knurl pattern)
                |
           Selection mask from zone nodes
```

### Issues Found (Original)
1. Zone mask (Map Range.003) uses Knurl Top/Bottom but values are 0
2. No profile control - just basic sine wave
3. No edge treatment options
4. Bevel modifier applied after GN - affects everything, not just knurling
