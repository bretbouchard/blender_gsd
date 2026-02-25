# Blender 5.0 Array Modifier Knowledge Base

Compiled from yojigraphics tutorial covering the new Geometry Nodes-based Array Modifier in Blender 5.0.

---

## Overview

**Blender 5.0** introduces a completely redesigned Array Modifier built on **Geometry Nodes**. This replaces the simple array modifier with a powerful, procedural system.

**Source:** [Blender 5.0 Create a plant with the new array modifier](https://www.youtube.com/watch?v=C9Txf9ToROg)
**Channel:** yojigraphics
**Duration:** 25:50

---

## Key Differences: Old vs New Array

| Feature | Old Array | New Array (5.0) |
|---------|-----------|-----------------|
| **Backend** | Simple modifier | Geometry Nodes setup |
| **Rotation** | Fixed | Randomizable per instance |
| **Scale** | Fixed | Randomizable per instance |
| **Alignment** | Line only | Line, Circle, Curve |
| **Distribution** | Linear factor | Curve/Path following |
| **Customization** | Limited | Full GN access |

---

## New Array Modifier Features

### 1. Line Alignment
- Classic linear array behavior
- Adjustable count and factor
- Simple translation-based distribution

### 2. Circle Alignment
- Distribute instances in circular pattern
- Adjustable radius
- Perfect for radial arrangements

### 3. Curve/Path Following
- Use Bezier or NURBS paths as distribution guides
- Instances follow curve shape
- Combine with curve deform for stems

### 4. Per-Instance Randomization

**Rotation Randomization:**
```
Randomize Rotation:
- X axis: 0-360°
- Y axis: 0-360°
- Z axis: 0-360°
```

**Scale Randomization:**
```
Randomize Scale:
- X axis: min/max
- Y axis: min/max
- Z axis: min/max
```

---

## Geometry Nodes Deep Dive

The new Array modifier is a **Geometry Node group** that can be unpacked and modified.

### Default Node Structure

```
Array Modifier (Node Group)
├── Align Rotation
│   └── Align to: X/Y/Z axis
├── Randomize Transform
│   ├── Rotation (X, Y, Z)
│   ├── Scale (X, Y, Z)
│   └── Translation
└── Instance on Points
```

### Customizing the Node Tree

**To modify internal nodes:**

1. Select Array modifier
2. Go to Geometry Nodes workspace
3. **Pack** the node group (if editing)
4. Enter the node group
5. Add/modify nodes

### Adding Height-Based Scale

**Use Case:** Plants with smaller leaves at top

```python
# Node setup for height-based scaling
Position Node
    → Separate XYZ
        → Z output
            → Math (Multiply Add)
                - Multiply: -2 to -3 (invert)
                - Add: adjust for base scale
            → Scale Instances (Z axis)
```

**Pattern:**
```
# As position goes up (Z+), scale decreases
Position.Z → Math (Multiply, -value) → Math (Add, offset) → Scale
```

### Adding Multiple Scale Nodes

The default Randomize Transform only has one scale. To add more:

1. Enter the Randomize Transform node group
2. **Duplicate** the Scale Instances node (Shift+D)
3. Position the duplicate in the flow
4. Connect custom drivers (Position, Index, etc.)

---

## Practical Workflow: Creating a Plant

### Step 1: Create the Leaf Geometry

```
1. Import leaf texture reference (cc0textures.com)
2. Create simple plane geometry
3. Model basic leaf shape with extrusions
4. Add edge loops (Ctrl+R) for shaping
5. Use Proportional Editing (Sharp falloff) for organic shape
6. Position vertices at origin for proper rotation
```

**Modeling Tips:**
- Keep geometry simple
- Use proportional editing with sharp falloff
- Center base vertices at origin (important for array rotation)

### Step 2: Texture the Leaf

```
1. Enable Node Wrangler addon
2. Ctrl+Shift+T → Load texture set (Color, Normal, Roughness, Opacity, Displacement)
3. UV Editor → Project from View (top view)
4. Scale UV to match texture
```

### Step 3: Create Distribution Path

```
1. Add Path curve (not Bezier)
2. Edit mode → Front view
3. Rotate 90° to stand vertical
4. Shape into organic stem curve
5. Adjust from side view for 3D interest
```

### Step 4: Apply Array Modifier

```
1. Add Array modifier to leaf
2. Set Align to: Curve
3. Select the path curve as target
4. Align Rotation to Z-axis
5. Set Count (e.g., 25)
6. Randomize Rotation Z: 360°
7. Randomize Rotation X/Y: 10-15°
8. Add height-based scale (via GN customization)
```

### Step 5: Create the Stem

```
1. Add Cylinder (12 vertices)
2. Scale to stem size
3. Add edge loops (Ctrl+R scroll)
4. Parent to curve with Curve Deform (Ctrl+P)
5. Set deformation axis to Z
6. UV Project from View for texturing
```

### Step 6: Add Variation

**Multiple Leaf Types:**
```
1. Duplicate original leaf (Shift+D)
2. Use different rotation randomization
3. Adjust UV for different texture region
4. Vary scale ranges
```

**Shader Variation:**
```
Color → Color Ramp → Hue Saturation Value
                 ↑
            Noise Texture (Object coordinates)
                 ↓
            Factor: 0.2
```

---

## Key Techniques

### 1. Height-Based Scaling (Growing Plants)

**Problem:** Arrays distribute identical instances
**Solution:** Drive scale from position

```
Position Node → Separate XYZ → Z
    → Math (Multiply, -2 to -3)
    → Math (Add, offset)
    → Scale Instances
```

**Result:** Smaller leaves at top, larger at bottom

### 2. Multiple Randomization Sources

Combine different random seeds for variety:

```
Index → Math (Multiply, seed1) → Rotation
Index → Math (Multiply, seed2) → Scale
Position → Math (Multiply) → Color variation
```

### 3. Curve Following with Deformation

```
Array on Curve Path
    +
Curve Deform on Stem Mesh
    =
Organic plant with leaves following stem
```

### 4. Texture Variation

```
# Add natural color variation
Principled BSDF
    ↑ (Color)
Mix Color (Factor from Noise)
    ├── Base color texture
    └── HSV-adjusted texture

Noise Texture → Object coordinates
    → Factor: 0.1-0.3
```

---

## Node Patterns

### Pattern: Position-Driven Scale

```
Position
    → Separate XYZ
    → Z
    → Math (Multiply Add)
        - Multiply: -value (inverts so top = smaller)
        - Add: base_scale
    → Scale Instances
```

### Pattern: Index-Based Rotation Variation

```
Index
    → Math (Multiply, random_factor)
    → Combine XYZ (rotation)
    → Rotate Instances
```

### Pattern: Curve-Aligned Distribution

```
Curve (Path)
    → Resample Curve (count)
    → Instance on Points
        - Instance: Leaf mesh
        - Rotation: Align to Euler (Normal → Y)
```

### Pattern: Multi-Source Randomization

```
Random Value (Boolean) → Selection
    → Delete Geometry (random removal)

Position → Noise Texture → Color Ramp
    → Set Material (color variation)
```

---

## Common Pitfalls

### Wrong Axis for Curve Deform
❌ **Wrong:** Default axis (often X)
✅ **Right:** Set to Z axis for vertical stems

### Origin Not at Base
❌ **Wrong:** Origin at center of leaf
✅ **Right:** Origin at base of leaf (where it connects)

### UV Not Matching Texture
❌ **Wrong:** Using generated coordinates
✅ **Right:** Project from View → Scale to match texture

### Identical Instances
❌ **Wrong:** No randomization
✅ **Right:** Randomize rotation Z: 360°, add scale variation

### Cannot Edit GN Internals
❌ **Wrong:** Trying to add nodes inside packed group
✅ **Right:** Pack/Unpack to access internal nodes

---

## Quick Reference

| Modifier Setting | Use Case |
|-----------------|----------|
| **Align: Line** | Linear arrays (fences, walls) |
| **Align: Circle** | Radial patterns (flowers, gears) |
| **Align: Curve** | Organic paths (plants, vines) |
| **Randomize Rotation Z: 360** | Natural rotation spread |
| **Randomize Scale** | Size variation |
| **Position → Scale** | Height-based sizing |

---

## Related Codebase Implementations

### Geometry Nodes Helpers (`lib/geometry_nodes/`)

The array modifier patterns align with existing codebase utilities:

```python
from lib.geometry_nodes.fields import FieldOperations

# Position-driven operations
FieldOperations.separate_xyz(position)

# Random value generation
FieldOperations.random_value(min=0, max=1, seed=42)
```

### Instancing Patterns (`lib/geometry_nodes/instances.py`)

```python
from lib.geometry_nodes.instances import InstanceOperations

# Instance on curve points
InstanceOperations.instance_on_points(
    points=curve_points,
    instance=leaf_mesh,
    rotation=align_rotation
)
```

### Curve Utilities (`lib/geometry/curve_utils.py`)

```python
from lib.geometry.curve_utils import CurveBuilder

# Create distribution path
path = CurveBuilder.create_path_curve(
    points=[(0, 0, 0), (0, 0, 1), (0.5, 0, 2)],
    name="StemPath"
)
```

---

## Tutorial Source

**Video:** [Blender 5.0 Create a plant with the new array modifier](https://www.youtube.com/watch?v=C9Txf9ToROg)
**Channel:** yojigraphics
**Published:** October 2025
**Duration:** 25:50

**Resources Mentioned:**
- CC0 Textures: https://cc0textures.com
- Node Wrangler addon (built-in)
- Bone Widget addon: https://github.com/waylow/boneWidget

---

*Compiled February 2026*
