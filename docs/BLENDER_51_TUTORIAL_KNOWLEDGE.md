# Blender 5.1+ Advanced Tutorial Knowledge Base

Compiled from three advanced Blender tutorials covering new features, generative art, and isometric modeling.

---

## Table of Contents

1. [Blender 5.1 New Features (DECODED)](#1-blender-51-new-features-decoded)
2. [Geometric Minimalism & Generative Art (Ducky 3D)](#2-geometric-minimalism--generative-art-ducky-3d)
3. [Isometric/RTS Modeling (Polygon Runway)](#3-isometricrts-modeling-polygon-runway)

---

## 1. Blender 5.1 New Features (DECODED)

### Vulkan as Default Backend
- **Vulkan** is now the **default** graphics backend (was optional in 5.0)
- Exception: Mac uses Metal backend
- Location: Preferences → System → Display Graphics

### Preferences Search Enhancement
**Major UX Improvement:**
- Search bar now **highlights** all occurrences of search term
- Click results to navigate directly
- Searches across dropdowns and nested sections
- **Huge time saver** for finding settings

### Extension Management
- **Update All** button for extensions
- Shows **current version** and **update-to version**
- Download from internet if enabled

### Raycast Node in Shader Editor
**Game-changer for materials:**

| Output | Description | Use Case |
|--------|-------------|----------|
| **Is Hit** | Boolean: did ray collide? | Visibility detection |
| **Self Hit** | Ray hit same mesh | Cavity/crevice detection |
| **Hit Distance** | Distance gradient | Proximity effects, AO |
| **Hit Position** | World position of hit | Color bleeding |
| **Hit Normal** | Normal direction of hit surface | Edge detection |

**Workflow Pattern:**
```
Material Output
    ↑
Raycast Node
    - Source Object (emits rays)
    - Length (max ray distance)
    - Outputs → Color mixing, masks
```

**Example Applications:**
- Object-to-object communication in shaders
- Real-time AO without baking
- Contact shadows
- Proximity-based color changes

### Normal Map DirectX/OpenGL Toggle
**Finally built-in:**
- Normal Map node now has **DirectX/OpenGL** selector
- No more manual green channel inversion
- Check texture name for hint (e.g., "_DX" suffix)

### Face Center Snapping
**New snap mode:**
- Snap to **center of face** (not corners/edges)
- Location: Snapping menu → Face Center
- Combine with "Snap With: Active" to snap origin

**Usage:**
```
1. Enable snapping (Shift+Tab)
2. Select Face Center mode
3. Hold Ctrl while moving
4. Object corner snaps to face center
```

### Resizable Quad View
- **Ctrl+Alt+Q** toggles quad view
- Now **resizable** by dragging center
- Perfect for modeling with multiple references
- Lock camera on 3 views, work in 1

### Grease Pencil Boolean Cutout
**Long-awaited feature:**
- Draw shapes → Edit mode → Select all
- **Stroke → Join Fills** (Shift+J)
- Creates cutouts in grease pencil fills
- Native boolean operation

### Animation Performance
- **150-300% improvement** for shape key animations
- Background performance optimizations
- Especially beneficial for heavy character animation

---

## 2. Geometric Minimalism & Generative Art (Ducky 3D)

### Style Definition
**Three pillars:**
1. **Optical Art** — Visual trickery, patterns
2. **Geometric Minimalism** — Simple forms, intricate builds
3. **Retro Future** — Clean, nostalgic aesthetic

### Core Philosophy
> "Simple to look at, intricate to build. Based on simple ideas."

**Key attributes:**
- Black and white (or limited palette)
- Emission materials only
- Transparency effects
- Looping animations
- Proximity-based reactions

### Essential Skills for This Style

| Skill | Application |
|-------|-------------|
| **Emission** | Self-illuminated materials |
| **Transparency** | Glass/ghost effects |
| **Index** | Individual element control |
| **Proximity** | Reaction to objects |
| **Curves + Wave Texture** | Flowing line animations |
| **Geometry Nodes** | Pattern generation |

### Tutorial 1: Radial Cube Rotation

**Setup:**
```
1. Curve Circle (radius 7, resolution 80)
2. Instance on Points → Cube
3. Align Rotation to Vector (Y-axis, from Normal)
4. Cube size: X=32, YZ=3.3
```

**Rotation Animation via Index:**
```
Index → Math (Multiply, factor) → Combine XYZ (X rotation)
    → Rotate Instances

# Key insight: Use integers for exact patterns
# Index 3 = Perfect spiral
# Index 5 = More rotations
```

**Looping with Pi:**
```
# DON'T type 360 for rotation
# DO use: 2 * pi (full rotation)

Frame 0: 0
Frame N: 2 * pi  (perfect loop)
```

**Wireframe Conversion:**
```
Mesh → Mesh to Curve → Curve to Mesh (with Curve Circle profile)
    → Join Geometry (merge with original for fill)
    → Set Material (Emission)
```

### Tutorial 2: Cylindrical Wave Field

**Core Setup:**
```
1. Mesh Line (count 21)
2. Instance on Points → Cylinder
3. Cylinder: Vertices=80, Radius=2, Depth=0.7
4. Cap Type: None (creates ribbons)
```

**Gradient Texture Scale Control:**
```
Position → Vector Math (Multiply, scale control)
    → Gradient Texture (Spherical)
    → Float Curve (shape the gradient)
    → Map Range (min/max scale)
    → Combine XYZ (X and Y only)
    → Instance Scale
```

**UV Mapping in Geometry Nodes:**
```
# Critical for wave texture alignment
Store Named Attribute:
    - Type: 2D Vector
    - Domain: Face Corner
    - Name: "UV"
    - Value: UV Map output from Cylinder
```

**Shader Setup:**
```
Attribute Node ("UV") → Vector input
Wave Texture:
    - Scale: 3
    - Type: Saw (hard→soft edge)
    - Phase Offset: Animated (20 * pi for loop)
Color Ramp → Emission Strength
```

**Compositor Glow:**
```
Render Layers
    → Glare (Bloom mode)
    → Chromatic Aberration (optional)
    → Color Ramp (simplify aberration)
    → Film Grain (subtle)
```

**Chromatic Aberration Trick:**
```
# Don't want full chromatic effect?
# Use Color Ramp to convert back to single color
# Creates "bonus lines" effect
```

### Animation Looping Secrets

**Perfect Loop Math:**
```
# Method 1: Position animation
Frame 0: Z = -5
Frame N: Z = 5 (or any equal offset)

# Method 2: Rotation (use pi)
Frame 0: 0
Frame N: 2 * pi (or any multiple)

# Method 3: Phase offset
Frame 0: 0
Frame N: N * pi (where N creates desired speed)
```

**Linear Interpolation:**
- Set Preferences → Animation → Default Interpolation → **Linear**
- Prevents ease-in/out on looping animations

### Pro Tips

**Index Math:**
- `Index → Math (Add, integer)` = exact rotation per instance
- `Index → Math (Multiply, factor)` = speed control
- Integer multipliers create cleaner patterns

**Gradient Positioning:**
```
# To animate gradient position:
Mesh Line Start Location (Z) → Keyframe
# Trial and error for perfect loop
```

**Material Setup:**
```
1. World → Background Color → Black
2. Material → Surface → Emission
3. Render Engine → Eevee
4. Compositor → Glare (Bloom)
```

---

## 3. Isometric/RTS Modeling (Polygon Runway)

### Aesthetic Definition
- **Top-down view** with **isometric perspective**
- "Lightyear" style — stylized, clean
- RTS (Real-Time Strategy) game aesthetic
- Off-world colony vibe

### Key Techniques (From Description)

**Isometric Setup:**
- Camera at 45° angle
- Orthographic projection
- Consistent scale across elements

**RTS Elements:**
- Modular building pieces
- Clean geometric shapes
- Functional aesthetic
- Ground-level detail

### Related Concepts

**Isometric Projection Math:**
```
# Camera rotation for true isometric
Rotation X: 35.264° (arctan(1/√2))
Rotation Z: 45°

# Or approximate (commonly used)
Rotation X: 60°
Rotation Z: 45°
```

**Modular Design:**
- Create reusable components
- Consistent edge loops
- Grid-aligned positioning
- Clean topology for subdivision

---

## 4. Cross-Cutting Patterns

### Emission-Only Workflow
**When to use:**
- Abstract/generative art
- Isometric illustrations
- Motion graphics
- Non-photorealistic renders

**Setup:**
```
1. World → Black background
2. Material → Emission (no BSDF)
3. Eevee renderer
4. Compositor → Bloom
```

### Index-Based Animation
**Pattern:**
```
Index → Math Operation → Transform
```

**Common Operations:**
- `Add integer` → Sequential delay
- `Multiply` → Speed/spacing control
- `Modulo` → Grouping patterns
- `Divide` → Phasing effects

### Perfect Loop Checklist
- [ ] Linear interpolation (not Bezier)
- [ ] Start/end values are equal or offset by known amount
- [ ] Use `pi` for rotations (not 360)
- [ ] Test at frame boundaries
- [ ] Match frame count to animation speed

### Geometry Nodes + Shader Integration
**UV Pass-through:**
```
Geometry Nodes:
    Store Named Attribute ("UV", UV Map)

Shader:
    Attribute Node ("UV") → Texture Vector
```

**Proximity in Shaders:**
```
Raycast Node → Distance/Hit → Mix RGB/Multiply
```

### Performance Tips

**For heavy instancing:**
- Use **Instance on Points** (not realize)
- Keep source geometry simple
- Profile with Performance Overlay

**For animations:**
- Blender 5.1 has 150-300% shape key improvement
- Use simple geometry for motion tests
- Bake/cache simulations

---

## 5. Node Tool Patterns

### Pattern: Radial Instance Array
```
Curve Circle
    → Instance on Points
    → Align Rotation to Vector (Normal → Y)
    → [Transform nodes]
    → [Material assignment]
```

### Pattern: Index-Driven Rotation
```
Index
    → Math (Multiply, factor)
    → Combine XYZ (X = rotation)
    → Rotate Instances

# Animate with:
Scene Time → Math (Add) → Multiply factor input
```

### Pattern: Gradient Scale Control
```
Position
    → Vector Math (Multiply, scale)
    → Gradient Texture (Spherical)
    → Float Curve (shape)
    → Map Range (remap to scale range)
    → Instance Scale
```

### Pattern: Wireframe from Solid
```
Mesh
    → Mesh to Curve
    → Curve to Mesh (profile: Curve Circle, r=0.1)
    → Join Geometry (merge with original)
    → Set Material (Emission)
```

### Pattern: UV Pass to Shader
```
# Geometry Nodes
[Geometry with UV Map]
    → Store Named Attribute
        - Type: 2D Vector
        - Domain: Face Corner
        - Name: "UV"
        - Value: UV Map output

# Shader
Attribute Node ("UV")
    → Texture Vector input
```

### Pattern: Perfect Loop Rotation
```
Scene Time → Seconds
    → Math (Multiply, 2*pi/FPS*frame_count)
    → Rotation input

# Or keyframe method:
Frame 0: 0
Frame N: 2 * pi
```

### Pattern: Proximity Reaction
```
# Geometry Nodes
Distribute Points
    → Geometry Proximity (Target)
    → Distance
    → Map Range (0-1 factor)
    → [Scale/Color/Transform]

# Shader
Raycast Node
    → Hit Distance
    → Map Range
    → [Color/Mix/Alpha]
```

---

## 6. Quick Reference: New Blender 5.1 Features

| Feature | Location | Use Case |
|---------|----------|----------|
| Vulkan Default | Prefs → System | Better performance |
| Preferences Search | Prefs → Search | Find settings fast |
| Update All Extensions | Prefs → Extensions | Batch updates |
| Raycast Node | Shader Editor | Proximity/visibility |
| Normal Map DX/GL | Normal Map Node | Fix imported maps |
| Face Center Snap | Snap Menu | Precise placement |
| Resizable Quad View | Ctrl+Alt+Q | Custom layouts |
| GP Boolean Cut | Stroke → Join Fills | Cutouts |
| Animation Perf | Background | 150-300% faster |

---

## 7. Style-Specific Recommendations

### For Geometric Minimalism:
- Use emission materials exclusively
- Black world background
- Limited color palette (or B&W)
- Focus on animation patterns
- Compositor bloom for glow

### For Isometric/RTS:
- Orthographic camera
- 45° rotation angles
- Modular components
- Clean topology
- Consistent scale

### For Generative Art:
- Index-based patterns
- Proximity reactions
- Loop animations
- Geometry Nodes heavy
- Simple source geometry

---

## 8. Common Pitfalls

### Rotation Animation
❌ **Wrong:** Keyframe 0° → 360°
✅ **Right:** Keyframe 0 → 2*pi

### Normal Maps
❌ **Wrong:** Use DirectX map directly
✅ **Right:** Select "DirectX" in node OR convert

### Loop Interpolation
❌ **Wrong:** Bezier interpolation (ease in/out)
✅ **Right:** Linear interpolation for perfect loops

### UV in Geometry Nodes
❌ **Wrong:** Assume UVs pass through
✅ **Right:** Use Store Named Attribute explicitly

### Index as Rotation
❌ **Wrong:** Plug Index directly to rotation
✅ **Right:** Use integer multipliers for clean patterns

---

## 9. Project Implementations

The patterns from these tutorials have been implemented in our codebase:

### Shader Raycast System
**File:** `lib/materials/shader_raycast.py`

Implements Blender 5.1 Raycast node patterns with presets:
- **Proximity AO** - Real-time ambient occlusion
- **Contact Shadows** - Object-to-object shadows
- **Edge Wear** - Proximity-based weathering
- **Color Bleeding** - Surface-to-surface color transfer

```python
from lib.materials.shader_raycast import create_edge_wear_material

# Create edge wear using shader raycast
material_config = create_edge_wear_material(
    intensity=0.6,
    max_distance=0.3,
    wear_color=(0.8, 0.6, 0.4)
)
```

### UV Pass-Through Helpers
**File:** `lib/geometry_nodes/fields.py`

Implements the UV pass-through pattern from Ducky 3D tutorial:
- `store_uv_for_shader()` - Store UVs with CORNER domain for shader access
- `create_uv_from_position()` - Generate and store UVs from position data
- `get_named_attribute()` - Retrieve stored attributes in shaders

```python
from lib.geometry_nodes.fields import FieldOperations

# Store UVs for shader access (Ducky 3D pattern)
FieldOperations.store_uv_for_shader(
    geometry=geometry_socket,
    uv_data=uv_vector,
    uv_name="WaveUV",
    builder=node_builder
)
```

### Ground Texture Validation
**File:** `lib/materials/ground_textures/gn_integration.py`

Validates UV storage before shader use:
- `UVStorageSpec` - Configuration for UV storage requirements
- `validate_uv_storage()` - Ensure UVs are properly stored for shaders

### Weathering with Raycast
**File:** `lib/materials/sanctus/weathering.py`

Edge wear implementation using shader raycast:
```python
from lib.materials.sanctus.weathering import WeatheringEffects

# Create edge wear with shader raycast (Blender 5.1+)
config = WeatheringEffects.create_edge_wear_with_raycast(
    intensity=0.5,
    max_distance=0.2
)
```

### GN Camera Projection
**File:** `lib/cinematic/projection/gn_projection.py`

Geometry Nodes alternative to Python raycasting for real-time camera projection:
- Real-time updates (no re-baking)
- Works with animated cameras
- GPU-accelerated projection

```python
from lib.cinematic.projection import create_gn_projection

# Create real-time GN projection
gn_proj = create_gn_projection(
    camera_name="MainCamera",
    target_object="ProjectOnMesh",
    uv_attribute_name="ProjUV"
)
```

### Pattern Documentation
**File:** `docs/NODE_TOOL_PATTERNS.md`

Reusable node patterns extracted from tutorials:
- Index-based animation
- UV pass-through
- Proximity reactions
- Perfect loop rotation

---

*Compiled from DECODED, Ducky 3D, and Polygon Runway tutorials - February 2026*
*Implementation cross-references added February 2026*
