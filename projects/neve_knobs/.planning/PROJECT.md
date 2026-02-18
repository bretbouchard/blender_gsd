# Neve Knobs Project

## Project Context

**Purpose**: Create procedural Neve-style audio knobs using Blender Geometry Nodes and Shader Nodes.

**Reference**: `neve_knobs.jpg` - Shows 5 distinct knob styles

## Knob Styles Identified

| Style | Color | Features |
|-------|-------|----------|
| **Style 1** | Blue | Cylindrical cap, smooth, no pointer, single-piece |
| **Style 2** | Silver | Medium, ridged skirt, thin white pointer |
| **Style 3** | Silver | Medium, deep ridged skirt, thin white pointer |
| **Style 4** | Silver | Small, shallow ridged skirt, thin white pointer |
| **Style 5** | Red | Tall, smooth skirt, prominent white pointer |

## Common Elements

- Circular top surface
- Pointer/indicator line (except Style 1)
- Shaft mount (6mm/1/4" standard)
- Professional finish (glossy or metallic)
- Skirt for grip and stability

## Parameters to Expose

### Geometry Parameters
- `cap_height` - Height of the cap
- `cap_diameter` - Diameter of the cap
- `skirt_height` - Height of the skirt section
- `skirt_diameter` - Diameter at skirt base
- `ridge_count` - Number of grip ridges (0 for smooth)
- `ridge_depth` - Depth of ridges
- `pointer_width` - Width of indicator line
- `pointer_length` - Length of indicator line

### Material Parameters
- `base_color` - Primary color (blue, silver, red)
- `metallic` - Metallic value (0-1)
- `roughness` - Surface roughness (0-1)
- `pointer_color` - Color of pointer line
- `coat_clearcoat` - Clearcoat intensity for glossy knobs

## Stage Pipeline

1. **Normalize** - Convert parameters to canonical ranges
2. **Primary** - Generate base cylinder geometry
3. **Secondary** - Add skirt, ridges, and pointer
4. **Detail** - Add surface details, bevels
5. **Output** - Store attributes, apply materials

## Output Artifacts

- `neve_knob_style1_blue.glb`
- `neve_knob_style2_silver.glb`
- `neve_knob_style3_silver.glb`
- `neve_knob_style4_silver.glb`
- `neve_knob_style5_red.glb`

## Status

**Phase**: Planning
**Started**: 2026-02-17
