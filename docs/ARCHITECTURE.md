# Architecture Overview

## Core Philosophy

**Determinism First**: Same task + same parameters = identical output, always.

The Blender GSD Framework treats Blender as a pure execution engine. All intent, logic, and configuration live outside of Blender files. This enables:

- Version control of design intent
- Reproducible builds
- Parameter-driven variations
- Team collaboration via text-based configs

## Core Components

### 1. Pipeline (`lib/pipeline.py`)

Deterministic stage-based execution with debug breakpoints.

```python
class Pipeline:
    def register_stage(self, name: str, func: Callable)
    def run(self, task: dict, context: dict)
```

**Stage Order (Universal):**
1. **Normalize** - Clean scene, set units, canonicalize parameters
2. **Primary** - Core geometry/material generation
3. **Secondary** - Details and surface features
4. **Detail** - Fine details, masked effects
5. **Output** - Export, cleanup

### 2. NodeKit (`lib/nodekit.py`)

Clean API for generating Blender node trees programmatically.

```python
nk = NodeKit(node_tree)
node = nk.n("ShaderNodeBsdfPrincipled", "BSDF", x, y)
nk.link(output_socket, input_socket)
```

**Features:**
- Automatic layout positioning
- Type-safe socket connections
- Node grouping utilities
- Debug visualization

### 3. Masks (`lib/masks.py`)

Height-based and attribute-based masking for effects.

**Mask Types:**
- `HeightMask` - Z-position based
- `AttributeMask` - Named attribute based
- `AngleMask` - Angular position based
- `CombinedMask` - Boolean combinations

**Usage:**
```python
mask = HeightMask(z_min=0.2, z_max=0.8, falloff=0.1)
displacement = mask.apply(geometry, effect)
```

### 4. Scene Ops (`lib/scene_ops.py`)

Scene setup, lighting, and render configuration.

**Utilities:**
- `reset_scene()` - Clean slate
- `ensure_collection()` - Collection management
- `setup_render_rig()` - Camera and lighting
- `select_objects()` - Selection helper

### 5. Exports (`lib/exports.py`)

Mesh and preview export utilities.

**Profiles:**
- `stl_clean` - STL for 3D printing
- `gltf_preview` - GLB for web/game engines

**Features:**
- Modifier application before export
- Automatic cleanup
- Format-specific optimization

## Data Flow

```
Task YAML → Task Runner → Artifact Script → Geometry Nodes → Export
     ↓           ↓              ↓                ↓              ↓
 Parameters   Pipeline      NodeKit          Masks         GLB/STL
             Stages         Nodes           Attributes      Files
```

## Project Structure

Each project (e.g., `neve_knobs`) follows this pattern:

```
projects/neve_knobs/
├── scripts/
│   ├── neve_knob_gn.py       # Main artifact builder
│   ├── render_*.py           # Render scripts
│   └── test_*.py             # Test scripts
├── tasks/
│   ├── knob_style1_*.yaml    # Task definitions
│   └── knob_style2_*.yaml
├── docs/
│   └── KNURLING_SYSTEM_SPEC.md
└── build/                    # Output (gitignored)
    ├── *.glb
    └── *.png
```

## Geometry Nodes Integration

The framework uses Geometry Nodes as the primary geometry generation system:

1. **Empty Mesh Object** - Create container
2. **GN Modifier** - Add modifier
3. **Node Tree** - Build procedurally via NodeKit
4. **Parameters** - Wire from task config
5. **Material** - Set via GN nodes

**Benefits:**
- Non-destructive
- Parameter-driven
- Real geometry (not shader tricks)
- Exportable to any format

## Parameter System

Parameters flow through a hierarchy:

```
Global Defaults (presets/base.yaml)
    ↓
Category Presets (presets/knobs.yaml)
    ↓
Variant Overrides (task YAML)
    ↓
Instance Parameters (task YAML)
```

**Parameter Groups:**
- `GEOMETRY` - Size, segments, profile
- `MATERIAL` - Metallic, roughness, clearcoat
- `COLOR_SYSTEM` - Primary, secondary, indicator
- `KNURLING` - Count, depth, zone, profile
- `LIGHTING` - Intensity, color, position
- `EXPORT` - Format, quality, cleanup

## Determinism Guarantees

The framework ensures identical outputs through:

1. **Scene Reset** - Always start from clean slate
2. **Unit Canonicalization** - Meters as base unit
3. **Random Seed Control** - Deterministic pseudo-random
4. **Order Independence** - No reliance on Blender's internal ordering
5. **No State Leakage** - No global state between runs

## Extension Points

### Adding a New Project

1. Create directory under `projects/`
2. Add artifact script in `scripts/`
3. Create task YAMLs in `tasks/`
4. Document in project `README.md`

### Adding a New Stage

1. Register stage in pipeline
2. Implement stage function
3. Document in stage order

### Adding a New Mask Type

1. Extend base `Mask` class
2. Implement `apply()` method
3. Add to mask library

## Performance Considerations

- **Batch Export** - Process multiple tasks in single Blender session
- **Modifier Caching** - Reuse expensive GN trees
- **Viewport Optimization** - Simplify for interactive sessions
- **Export Optimization** - Apply modifiers, merge vertices

## Future Directions

- **Material Library** - Shared PBR materials
- **Animation Support** - Procedural animation rigs
- **Physics Presets** - Pre-configured physics setups
- **Composition Graphs** - Post-processing automation
