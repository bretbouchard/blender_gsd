# Blender 5.x Geometry Nodes Knowledge Base

Compiled from 8 CGMatter tutorials covering advanced Geometry Nodes techniques.

---

## Table of Contents

1. [Triangle Parenting](#1-triangle-parenting)
2. [Volume Nodes System](#2-volume-nodes-system)
3. [Grid-Based Simulations](#3-grid-based-simulations)
4. [Erosion Systems](#4-erosion-systems)
5. [Fur/Hair Systems](#5-furhair-systems)
6. [Handwriting System](#6-handwriting-system)
7. [Curl Noise Particles](#7-curl-noise-particles)
8. [Set Extension](#8-set-extension)
9. [Blender 5.1 New Features](#9-blender-51-new-features)

---

## 1. Triangle Parenting

**Use Case:** Control real Blender objects (cameras, lights) via Geometry Nodes

### Core Concept
Use a 3-vertex mesh as a proxy that can be transformed via Geometry Nodes, with real objects inheriting position/rotation through Blender's vertex triangle parenting mode.

### Setup Steps

1. **Create Triangle Mesh:**
```python
def create_triangle_mesh(name="Triangle_Proxy"):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    verts = [(0, 0, 0), (1, 0, 0), (0.5, 0.866, 0)]
    faces = [(0, 1, 2)]
    mesh.from_pydata(verts, [], faces)
    bpy.context.collection.objects.link(obj)
    return obj
```

2. **Parent Object to Triangle:**
   - Select child object, then triangle
   - `Ctrl + P` → "Vertex Triangle"

3. **Drive from Geometry Nodes:**
```
Instances → Sample Index → Transform Geometry (Matrix mode, Relative)
```

### Limitations
| Feature | Support |
|---------|---------|
| Location | ✅ |
| Rotation | ✅ |
| Scale | ❌ Not supported |

---

## 2. Volume Nodes System

**20+ Volume Nodes** available in Blender 5.0

### Core Concepts

- **Volume**: Container that holds multiple grids
- **Grid**: Actual voxel data (density, SDF, velocity)
- **Transform**: Each grid has its own 4x4 transform matrix

### Essential Nodes

| Node | Purpose |
|------|---------|
| `Get Named Grid` | Extract grid from volume (Remove checkbox extracts) |
| `Store Named Grid` | Store grid with name |
| `Sample Grid` | Sample values at positions |
| `Grid to Mesh` | Convert SDF to polygon mesh |
| `Points to SDF Grid` | Create SDF from point cloud |
| `Grid Gradient` | Get surface normals from SDF |
| `Set Grid Background` | Set empty space value (-1 for SDF outside) |

### Common Grid Names
- `density` - Standard density
- `color` - Auto-detected by shader
- `velocity` - Vector velocity data

### Workflow Pattern
```
Volume Cube → Get Named Grid → Voxel Grid → [Operations] → Store Named Grid → Output
```

### Tips
- Use **Voxel Grid** to fix sparse grid artifacts
- Background = -1 for SDF grids (outside = negative)
- Grid transform scale affects physical size

---

## 3. Grid-Based Simulations

### Simulation Zone Structure
```
1. Create cube grid topology (set resolution)
2. Transform for even spacing
3. Initialize grids (multiply by zero, add initial values)
4. Simulation Zone:
   - Advection step
   - Divergence calculation
   - Pressure iteration (most expensive)
   - Pressure subtraction from velocity
5. Output: smoke, pressure, velocity grids
```

### Performance Notes
- Pressure iteration is most expensive
- 256x256x1 grid: ~12ms for 4 iterations
- Shadows in Eevee Next are extremely expensive

---

## 4. Erosion Systems

### Edge Erosion Algorithm

```
Mesh Input
    → Edge Angle (threshold ~6 radians)
    → Separate Geometry
    → Delete Geometry (faces only)
    → Mesh to Curve
    → Resample Curve (100+ points)
    → Tube Node (noise-controlled radius)
    → SDF Remesh
    → Distort Node
    → Mesh Boolean (difference, manifold)
```

### Face Erosion Algorithm

```
Mesh Input
    → Distribute Points on Faces (1500+)
    → Noise Texture (normalized OFF)
    → Delete Geometry (threshold-based)
    → Points to SDF
    → Grid to Mesh
    → [Optional] Subdivide + Distort
    → Mesh Boolean (difference)
    → Delete Floaters (island + face area check)
```

### Floater Removal
```
Mesh Island → Accumulate Field (face area) → Delete if total < threshold
```

---

## 5. Fur/Hair Systems

### Hair Clump Node Group

```
Spiral Node
    → Random: Start Radius (0.5-1.5)
    → Random: Rotation (0.5-1.2 × 8)
    → Random: Height (2-1)
    → Random: End Radius (0.3-0.7)
    → Random: Trim (0.5-1.0)
    → Distort Node (10% strength)
    → Resample Curve (~60)
    → Curve to Mesh (profile res 3)
```

### Main Fur Setup

```
Surface Geometry
    → Distribute Points on Faces (300-1000)
    → Instance on Points
        - Pick Instance: ON
        - Scale: Random 0.03-0.08 (Z-biased)
        - Rotation: Aligned to normal
    → Realize Instances
    → Bake Node (cache)
    → Final Distortion (0.5%)
    → Set Material (Principled Hair BSDF)
```

### Material Tips
- Use **Melanin** slider for intuitive color
- Low melanin = blonde/white
- Match skin color to hair for seamless transition

---

## 6. Handwriting System

### Letter Preparation
1. Write 3 variants per letter (a_1, a_2, a_3)
2. Scan and crop to bounding box
3. Import as planes with consistent naming

### Core Node Groups

**Index Finder:**
```
String + Position → Slice String (length=1) → Find in String → Index
```

**Letter Selector:**
```
Index × 3 + Random(0-2) → Separate by Index → Letter Instance
```

**Positioning:**
```
Instance Bounds (width) → Accumulate Field (trailing) → Translate Instances
```

### Alphabet String
```
" abcdefghijklmnopqrstuvwxyz"  (space at index 0)
```

### Sort Order Fix
```
Index → Multiply(-1) → Sort Elements (Group ID)
```

---

## 7. Curl Noise Particles

### Problem with Direct Noise
- Creates sinks (particles cluster)
- Creates sources (particles spread)
- Results in unnatural compression/expansion

### Curl Solution
Curl of any vector field has **zero divergence**.

### 2D Simplification
```
For vector field V with only Z component:
    Curl X = dVz/dY
    Curl Y = -dVz/dX
    Curl Z = 0
```

### Derivative Calculation (Finite Differences)
```
epsilon = 0.001  (smaller for high-detail noise)
dVz/dX = (Vz(position + epsilon_x) - Vz(position)) / epsilon
dVz/dY = (Vz(position + epsilon_y) - Vz(position)) / epsilon
```

### Complete Setup
```
Grid of Points
    → Simulation Zone
        → Repeat Zone (substeps: 5-10)
            → Set Position (offset)
                → Curl Field × Delta Time × Speed
```

### Speed Factor
- Typical: 0.001 to 0.0001
- Substeps improve accuracy

### Any Scalar Field Works
- Noise Texture
- Wave Texture
- Voronoi Distance
- Custom math (sine waves create whirlpools)

---

## 8. Set Extension

### Edge Gravity System

```
Distribute Points on Faces
    → Geometry Proximity (nearest edge)
    → Map Range (distance → factor)
    → Noise Texture (variation)
    → Mix Vector (original ↔ edge position)
```

### Dual-Layer Particles
| Layer | Density | Size |
|-------|---------|------|
| Edge particles | ~200 | 0.007 |
| Fill particles | ~3000 | 0.002 |

### Size Distribution
```
Random Value (0-1) → Float Curve (bias small) → Multiply × size
```

### Camera Projection
- Use **Window Coordinates** (not UV)
- Enable **Auto Refresh** for movie clips

### Compositing Integration
```
Cryptomatte → Separate CGI
    → Pixelate
    → Kuwahara filter
    → Match black levels
    → Bloom (CGI only)
    → Lens Distortion (everything)
```

---

## 9. Blender 5.1 New Features

### New Nodes
| Node | Description |
|------|-------------|
| Cube Grid Topology | Create base grids with resolution |
| Grid Dilate/Erode | OpenVDB operations |
| Grid Mean/Median | Statistical operations |
| Matrix SVD | Singular Value Decomposition |
| Font Socket | New text handling type |
| Get/Store Bundle Item | Complex data packaging |

### Enhanced Nodes
- **Pack UV Islands**: Custom packing region, warnings search
- **UV Unwrap**: SLIM option, no-flip option
- **String to Curves**: New input sockets

### Eevee Next
- Planar reflections with glossy
- AOVs bumped to 128
- Shader to RGB transparency
- Jitter DoF (render only)

### Performance Overlay
Shows evaluation, sync, and total times (CPU/GPU breakdown)

### Coming in 5.2
- Lists in Geometry Nodes
- Word ID for String to Curves
- Geometry Attribute Node for Armatures

---

## Quick Reference: Common Patterns

### Instance Transform Extraction
```
Instances → Sample Index (transform) → Transform Geometry (matrix)
```

### Boolean Cut Pattern
```
Mesh A → Mesh Boolean (difference, manifold) → Result
              ↑
         Mesh B (cutter)
```

### Point Distribution with Variation
```
Distribute Points → Random Value → Float Curve → Set Point Radius
```

### Proximity-Based Effects
```
Points → Geometry Proximity (target) → Distance → Map Range → Factor
```

### Simulation Zone Pattern
```
Input → Simulation Zone
           ↓
        State Update (position, velocity, etc.)
           ↓
       Output
```

---

## Node Naming Conventions

| Category | Examples |
|----------|----------|
| **Grid** | Get Named Grid, Store Named Grid, Grid to Mesh |
| **Field** | Sample Grid, Grid Gradient, Grid Divergence |
| **Transform** | Set Grid Transform, Transform Geometry |
| **Convert** | Points to SDF, Field to Grid, Voxel Grid |

---

*Compiled from CGMatter tutorials - February 2026*
