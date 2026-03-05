# Grease Pencil System Requirements

**Version:** 1.0
**Status:** Draft
**Created:** 2026-03-05
**Action Plan:** `docs/GREASE_PENCIL_ACTION_PLAN.md`
**Tutorial Reference:** `docs/GREASE_PENCIL_TUTORIAL_COMPILATION.md`

---

## Overview

The Grease Pencil System provides a **node-centric** 2D animation workflow within Blender's 3D environment. Following the GSD philosophy "Structure lives in nodes," this system emphasizes node-based materials, effects, and compositing over direct Python manipulation.

### Primary Use Cases
1. **2D Character Animation** - Frame-by-frame and cut-out rigging
2. **2D/3D Hybrid** - Drawing on 3D surfaces, NPR rendering
3. **Anime/NPR Styles** - Cel shading, Ghibli watercolor, 90s anime
4. **Motion Graphics** - Animated text, shapes, UI elements
5. **Rotoscoping** - Video reference tracing

### Node-Centric Philosophy

| Aspect | Node-Based Approach | Python Role |
|--------|---------------------|-------------|
| **Stroke Effects** | GP Modifiers (NOT Geometry Nodes) | Configure modifier stack |
| **Materials** | Shader Node groups | Create/configure node trees |
| **Animation** | Drivers + NLA system | Setup automation |
| **Compositing** | Compositor nodes | Pipeline integration |

**Why GP Modifiers (Not Geometry Nodes)?**
- **Geometry Nodes cannot process Grease Pencil data** - Geo Nodes operate on `bpy.types.Mesh`, `bpy.types.Curve`, `bpy.types.PointCloud`. `bpy.types.GreasePencil` is a distinct data type.
- **GP has its own modifier stack**: `GP_BUILD`, `GP_NOISE`, `GP_SMOOTH`, `GP_OPACITY`, `GP_COLOR`, `GP_ARMATURE`, etc.
- Non-destructive workflow
- Real-time preview
- Export-friendly (FBX, USD)
- Reusable presets
- GPU-accelerated performance

---

## Requirements Index

| ID | Category | Priority | Phase | Description |
|----|----------|----------|-------|-------------|
| REQ-GP-01 | Core | P1 | 21.0 | Core Grease Pencil module |
| REQ-GP-02 | Animation | P1 | 21.1 | Animation system integration |
| REQ-GP-03 | Hybrid | P2 | 21.2 | 2D/3D hybrid workflows |
| REQ-GP-04 | Styles | P2 | 21.3 | NPR/Anime style presets |
| REQ-GP-05 | Materials | P1 | 21.0 | Node-based material system |
| REQ-GP-06 | Effects | P2 | 21.0 | GP Modifier effects |
| REQ-GP-07 | Rotoscope | P2 | 21.2 | Video reference tracing |
| REQ-GP-08 | Export | P2 | 21.3 | Render and export pipeline |

---

## Stage Pipeline Mapping

The Grease Pencil system follows GSD's **Universal Stage Order**:

| Stage | Name | GP Operation | Description |
|-------|------|-------------|-------------|
| **0** | Normalize | `stage_normalize_gp()` | Parameter canonicalization, seed derivation, layer naming |
| **1** | Primary | `stage_primary_gp()` | Base GP object creation, layer stack, base strokes |
| **2** | Secondary | `stage_secondary_gp()` | Layer effects, transforms, rigging, boolean-like ops |
| **3** | Detail | `stage_detail_gp()` | GP modifiers (noise, smooth, build) with masks |
| **4** | OutputPrep | `stage_output_gp()` | Render prep, attribute baking, export conversion |

### Stage Functions

```python
# lib/grease_pencil/stages.py

def stage_normalize_gp(params: dict) -> dict:
    """
    Stage 0: Normalize parameters to canonical form.

    - Convert resolution to density
    - Normalize layer names
    - Derive seed from params hash
    - Validate required parameters
    """
    return {
        'stroke_count': params.get('stroke_count', 10),
        'layer_count': params.get('layer_count', 3),
        'seed': params.get('seed', hash(str(sorted(params.items()))) % (2**31)),
        'stroke_width': params.get('stroke_width', 5.0),
        'material_config': params.get('material_config', {}),
    }

def stage_primary_gp(params: dict) -> bpy.types.GreasePencil:
    """
    Stage 1: Create base GP object with layers.

    - Create GP data block
    - Generate layer stack
    - Create base strokes (procedural or from reference)
    """
    pass

def stage_secondary_gp(gp_obj: bpy.types.Object, params: dict):
    """
    Stage 2: Apply modifications to GP data.

    - Layer reordering, visibility, blend modes
    - Rigging integration (armature binding)
    - Transform operations
    """
    pass

def stage_detail_gp(gp_obj: bpy.types.Object, params: dict):
    """
    Stage 3: Apply GP modifiers with masking.

    - GP_NOISE, GP_SMOOTH, GP_BUILD modifiers
    - All effects support masking
    - Procedural variation via seed
    """
    pass

def stage_output_gp(gp_obj: bpy.types.Object, params: dict):
    """
    Stage 4: Prepare for final output.

    - Bake animation if needed
    - Convert to curves for export
    - Set render settings
    """
    pass
```

---

## Determinism Requirements

All procedural GP generation MUST follow these determinism rules:

### Seed Parameter

| Rule | Implementation |
|------|---------------|
| **Seed Required** | All generators accept `seed: int \| None` parameter |
| **Auto-Derivation** | If `seed=None`, derive from `hash(str(sorted(params.items()))) % (2**31)` |
| **Reproducibility** | Identical params + identical seed = identical output |
| **Logging** | Log seed value for debugging reproducibility |

### Deterministic Random

```python
import random
from typing import Optional

def generate_strokes_procedural(
    params: dict,
    seed: Optional[int] = None
) -> list:
    """
    Generate strokes deterministically.

    Args:
        params: Stroke parameters
        seed: Random seed (None = auto-derive from params)

    Returns:
        List of stroke data (deterministic for same params+seed)
    """
    # Derive seed if not provided
    if seed is None:
        seed = hash(str(sorted(params.items()))) % (2**31)

    # Log for reproducibility debugging
    print(f"[GP] Using seed: {seed}")

    # Set random state
    rng = random.Random(seed)

    # Generate strokes deterministically
    strokes = []
    for i in range(params.get('stroke_count', 10)):
        stroke = {
            'points': generate_points(rng, params),
            'width': params.get('stroke_width', 5.0),
        }
        strokes.append(stroke)

    return strokes
```

### Verification

```python
def verify_determinism():
    """Verify that same params produce same output."""
    params = {'stroke_count': 10, 'stroke_width': 5.0}
    seed = 12345

    result1 = generate_strokes_procedural(params, seed)
    result2 = generate_strokes_procedural(params, seed)

    assert result1 == result2, "Determinism violation: same params produced different output"
```

---

## Mask Infrastructure

**SLC Requirement**: Every GP effect must support masking.

### Mask Types

| Mask Type | Description | Implementation |
|-----------|-------------|----------------|
| **Layer Opacity** | Per-layer opacity mask | `layer.opacity` |
| **Stroke Weight** | Painted weights for effect falloff | Vertex groups on GP strokes |
| **Procedural** | Distance, height, angle-based | Math functions in shader nodes |
| **Texture** | Image-based mask | Texture node in shader graph |

### Mask Configuration

```yaml
GPMaskConfig:
  type: "procedural"  # layer, stroke_weight, procedural, texture
  invert: false
  blend_mode: "multiply"  # multiply, add, subtract, mix
  falloff: 0.5

  # For procedural masks
  procedural:
    mode: "distance"  # distance, height, angle
    origin: [0, 0, 0]
    radius: 1.0

  # For texture masks
  texture:
    path: "/path/to/mask.png"
    uv_map: "default"
```

### Mask Application

```python
def apply_effect_with_mask(
    gp_obj: bpy.types.Object,
    effect_type: str,
    params: dict,
    mask_config: Optional[GPMaskConfig] = None
):
    """
    Apply GP effect with optional masking.

    All effects MUST support masking per SLC requirement.
    """
    modifier = gp_obj.grease_pencil_modifiers.new(effect_type, f'GP_{effect_type.upper()}')

    # Apply effect parameters
    for key, value in params.items():
        setattr(modifier, key, value)

    # Apply mask if provided
    if mask_config:
        apply_mask_to_modifier(modifier, mask_config)

    return modifier
```

---

## REQ-GP-01: Core Grease Pencil Module

**Priority:** P1 | **Phase:** 21.0

### Description
Create the foundational `lib/grease_pencil/` module with stroke utilities, types, and node-centric architecture.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 01-01 | Stroke creation | Create GP strokes from Python with configurable parameters |
| 01-02 | Stroke manipulation | Modify stroke points, width, strength programmatically |
| 01-03 | Layer management | Create, organize, and configure GP layers |
| 01-04 | Deterministic output | Same parameters + seed produce identical results |
| 01-05 | YAML presets | Stroke configurations loadable from YAML |
| 01-06 | Real-time preview | Changes visible in viewport immediately |
| 01-07 | Works without Blender | Numpy-only mode for unit testing |
| 01-08 | Brush presets | Load brush presets for artist-assisted drawing workflows |

### Module Structure

```
lib/grease_pencil/
├── __init__.py          # Main exports (see Public API below)
├── types.py             # GPStrokeConfig, GPAnimationConfig, GPLayerConfig
├── stages.py            # Stage pipeline functions (normalize, primary, etc.)
├── stroke_utils.py      # Stroke creation and manipulation
├── materials.py         # GP shader node groups (stroke/fill)
├── rigging.py           # Bone rigging for GP strokes
├── animation.py         # Frame-by-frame, cut-out animation helpers
├── modifiers.py         # GP modifier presets (Build, Opacity, Mirror)
├── gp_effects.py        # GP modifier-based effects (NOT Geometry Nodes)
├── brush_config.py      # Brush presets for artist-assisted workflows
├── rotoscope.py         # Video reference tracing
├── hybrid.py            # 2D/3D hybrid workflow utilities
└── presets/
    ├── stroke_presets.yaml
    ├── material_presets.yaml
    ├── brush_presets.yaml
    └── animation_presets.yaml
```

### Public API (`__init__.py`)

```python
# lib/grease_pencil/__init__.py

"""
Grease Pencil System - Node-centric 2D animation in Blender.

This module provides procedural GP generation following GSD's
Universal Stage Order with deterministic output.
"""

from .types import (
    GPStrokeConfig,
    GPLayerConfig,
    GPAnimationConfig,
    GPMaterialConfig,
    GPMaskConfig,
    GPRiggingConfig,
)
from .stages import (
    stage_normalize_gp,
    stage_primary_gp,
    stage_secondary_gp,
    stage_detail_gp,
    stage_output_gp,
)
from .stroke_utils import (
    create_gp_object,
    create_stroke,
    generate_strokes_procedural,
)
from .materials import (
    create_material_node_group,
    apply_material_to_gp,
)
from .modifiers import (
    apply_build_effect,
    apply_noise_effect,
    apply_smooth_effect,
    apply_effect_with_mask,
)
from .brush_config import (
    BrushPreset,
    load_brush_preset,
    list_brush_presets,
)

__all__ = [
    # Types
    'GPStrokeConfig',
    'GPLayerConfig',
    'GPAnimationConfig',
    'GPMaterialConfig',
    'GPMaskConfig',
    'GPRiggingConfig',
    # Stages
    'stage_normalize_gp',
    'stage_primary_gp',
    'stage_secondary_gp',
    'stage_detail_gp',
    'stage_output_gp',
    # Stroke utilities
    'create_gp_object',
    'create_stroke',
    'generate_strokes_procedural',
    # Materials
    'create_material_node_group',
    'apply_material_to_gp',
    # Modifiers
    'apply_build_effect',
    'apply_noise_effect',
    'apply_smooth_effect',
    'apply_effect_with_mask',
    # Brush configuration
    'BrushPreset',
    'load_brush_preset',
    'list_brush_presets',
]
```

### Stroke Configuration

```yaml
GPStrokeConfig:
  points: []              # List of (x, y, z, pressure, strength)
  line_width: 2.0         # Base stroke width
  hardness: 1.0           # Edge hardness (0-1)
  use_cyclic: false       # Close stroke
  material_index: 0       # Material slot
  display_mode: "3DSPACE" # 3DSPACE, 2DIMAGE, 2DSCREEN
```

### Technical Approach
- Python creates GP objects and strokes
- Node graphs handle materials and effects
- Modifier presets configure GP modifiers

---

## REQ-GP-02: Animation System Integration

**Priority:** P1 | **Phase:** 21.1

### Description
Integrate Grease Pencil with the existing `lib/animation/` system for rigging and animation workflows.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 02-01 | Weight painting | Paint weights on GP strokes for armature deformation |
| 02-02 | Bone rigging | Rig GP objects with armature constraints |
| 02-03 | Pose library | Save/recall GP poses (stroke positions, layer visibility) |
| 02-04 | Onion skinning | GP-specific onion skin display options |
| 02-05 | Frame-by-frame | Create/edit keyframes on GP layers |
| 02-06 | Cut-out rigging | Parent strokes to bones for puppet animation |
| 02-07 | Driver integration | Control GP properties via drivers |

### Animation Types

| Type | Description | Use Case |
|------|-------------|----------|
| Frame-by-Frame | Drawing each frame | Organic character animation |
| Cut-out | Rigged puppet animation | Limited animation, motion graphics |
| Hybrid | Combination of both | Complex character animation |

### Bone Rigging Configuration

```yaml
GPRiggingConfig:
  armature: "Character_Armature"
  bind_mode: "with_automatic_weights"  # or "manual"
  vertex_groups:
    - name: "Head"
      bones: ["Head", "Neck"]
    - name: "Arm_L"
      bones: ["UpperArm_L", "LowerArm_L", "Hand_L"]
```

### Technical Approach
- Extend `lib/animation/weight_painter.py` for GP support
- Extend `lib/animation/rig_builder.py` for GP armatures
- Extend `lib/animation/pose_library.py` for GP poses

---

## REQ-GP-03: 2D/3D Hybrid Workflows

**Priority:** P2 | **Phase:** 21.2

### Description
Utilities for hybrid 2D/3D workflows where GP strokes interact with 3D geometry.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 03-01 | Draw on surface | GP strokes snap to mesh surface |
| 03-02 | UV space drawing | Strokes stored in UV coordinates |
| 03-03 | 3D to 2D projection | Project GP strokes to 2D for compositing |
| 03-04 | Cut-out conversion | Convert frame-by-frame to rigged cut-out |
| 03-05 | Depth sorting | Correct z-ordering of GP layers |
| 03-06 | Shadow casting | GP strokes can cast/receive shadows |
| 03-07 | Compositor integration | GP layers as compositor inputs |

### Hybrid Workflow Functions

```python
# lib/grease_pencil/hybrid.py

def draw_on_mesh_surface(mesh, stroke_config):
    """Draw GP strokes on 3D mesh UV space."""
    pass

def project_3d_to_2d(camera, gp_object):
    """Project 3D GP strokes to 2D plane for compositing."""
    pass

def convert_to_cutout_character(gp_object):
    """Convert frame-by-frame GP to cut-out rigged character."""
    pass

def setup_gp_shadow_catcher(gp_object):
    """Configure GP to cast shadows onto 3D geometry."""
    pass
```

### Technical Approach
- Geometry Nodes for surface projection effects
- Compositor nodes for 2D/3D layering
- Shader nodes for NPR-to-3D material blending

---

## REQ-GP-04: NPR/Anime Style Presets

**Priority:** P2 | **Phase:** 21.3

### Description
Pre-configured NPR (Non-Photorealistic Rendering) style presets using shader node groups.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 04-01 | Cel shading | Clean anime-style cel shading |
| 04-02 | Ghibli style | Watercolor/soft gradient look |
| 04-03 | 90s anime | Limited palette with film grain |
| 04-04 | Custom styles | User can create new style presets |
| 04-05 | Node group presets | Styles defined as shader node groups |
| 04-06 | Real-time preview | Style changes visible immediately |
| 04-07 | Export-friendly | Styles bake to textures for export |

### Style Presets

| Preset | Description | Node Group |
|--------|-------------|------------|
| `anime_cel` | Clean cel shading with posterization | `NPR_AnimeCel` |
| `ghibli_style` | Watercolor/soft gradient look | `NPR_Ghibli` |
| `90s_anime` | Limited palette with film grain | `NPR_90sAnime` |
| `comic_book` | Bold outlines, halftone shading | `NPR_Comic` |
| `pencil_sketch` | Hand-drawn pencil look | `NPR_Sketch` |

### Style Configuration

```yaml
# lib/grease_pencil/presets/style_presets.yaml

anime_cel:
  stroke_style: "cel_shaded"
  fill_style: "flat_color"
  line_width: 2.0
  antialiasing: minimal
  shader_node_group: "NPR_AnimeCel"
  posterize_levels: 4
  rim_light: true

ghibli_style:
  stroke_style: "pencil"
  fill_style: "watercolor"
  line_width: 1.5
  texture_overlay: true
  shader_node_group: "NPR_Ghibli"
  gradient_softness: 0.7
  color_bleed: 0.2

90s_anime:
  stroke_style: "hard_edge"
  fill_style: "flat"
  limited_palette: true
  film_grain: 0.3
  shader_node_group: "NPR_90sAnime"
  color_depth: 6  # bits
  scanlines: false
```

### Technical Approach
- Each style is a Shader Node Group
- Python generates node graphs from YAML config
- Use `lib/geometry_nodes/node_tree_builder.py` pattern

---

## REQ-GP-05: Node-Based Material System

**Priority:** P1 | **Phase:** 21.0

### Description
Create GP materials using shader node groups instead of direct GP material settings.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 05-01 | Stroke materials | Node-based stroke appearance |
| 05-02 | Fill materials | Node-based fill with gradients/textures |
| 05-03 | Material blending | Blend multiple materials on single stroke |
| 05-04 | UV control | Control material UV mapping |
| 05-05 | Mask support | Use masks to control material application |
| 05-06 | Preset library | Pre-built material node groups |

### GP Material Types

**GP materials differ from mesh materials.** They have specific properties for stroke and fill rendering:

```yaml
GPMaterialConfig:
  name: "Character_Outline"

  # Material mode (required)
  mode: "STROKE_AND_FILL"  # STROKE, FILL, or STROKE_AND_FILL

  # Stroke properties
  stroke_style: "SOLID"    # SOLID, TEXTURE, or GRADIENT
  stroke_color: [0.0, 0.0, 0.0, 1.0]
  stroke_width: 2.0

  # Fill properties
  fill_style: "SOLID"      # SOLID, GRADIENT, TEXTURE, or PATTERN
  fill_color: [1.0, 0.5, 0.5, 1.0]

  # GP-specific properties
  overlap_mode: "DEFAULT"  # DEFAULT, OVERLAP, or BELOW
  overlap_threshold: 0.1

  # Holdout for compositing
  holdout: false

  # Shader node group (optional)
  node_group: "GP_Stroke_Gradient"
  node_parameters:
    color_start: [0.0, 0.0, 0.0, 1.0]
    color_end: [0.2, 0.2, 0.2, 1.0]
    mix_factor: 0.5
```

### GP Material Properties Reference

| Property | Type | Values | Description |
|----------|------|--------|-------------|
| `mode` | enum | `STROKE`, `FILL`, `STROKE_AND_FILL` | What the material affects |
| `stroke_style` | enum | `SOLID`, `TEXTURE`, `GRADIENT` | Stroke appearance mode |
| `fill_style` | enum | `SOLID`, `GRADIENT`, `TEXTURE`, `PATTERN` | Fill appearance mode |
| `overlap_mode` | enum | `DEFAULT`, `OVERLAP`, `BELOW` | How overlapping strokes render |
| `holdout` | bool | `true`, `false` | Cut out background in compositing |

### Material Node Groups

| Node Group | Purpose | Inputs | Outputs |
|------------|---------|--------|---------|
| `GP_Stroke_Basic` | Simple colored stroke | Color, Width | Stroke |
| `GP_Stroke_Gradient` | Gradient along stroke length | Color Start, Color End, Mix | Stroke |
| `GP_Stroke_Texture` | Texture-mapped stroke | Texture, UV Scale | Stroke |
| `GP_Fill_Flat` | Flat color fill | Color | Fill |
| `GP_Fill_Gradient` | Gradient fill | Color 1, Color 2, Type | Fill |
| `GP_Fill_Pattern` | Pattern/texture fill | Texture, Scale, Rotation | Fill |

### NPR Shader Node Groups (for REQ-GP-04)

| Node Group | Style | Inputs | Outputs |
|------------|-------|--------|---------|
| `NPR_AnimeCel` | Anime cel shading | Base Color, Shadow Color, Rim Color, Posterize Levels | Color |
| `NPR_Ghibli` | Ghibli watercolor | Base Color, Gradient Softness, Color Bleed, Texture Overlay | Color |
| `NPR_90sAnime` | 90s anime | Base Color, Color Depth (bits), Film Grain, Scanlines | Color |
| `NPR_Comic` | Comic book | Base Color, Outline Width, Halftone Scale | Color |
| `NPR_Sketch` | Pencil sketch | Base Color, Pencil Texture, Paper Texture, Line Noise | Color |

### Technical Approach
- `materials.py` creates ShaderNodeTree objects
- Python generates node connections from config
- Follow `NodeTreeBuilder` pattern from `lib/geometry_nodes/`
- GP materials use `bpy.types.GreasePencil` material slots

---

## REQ-GP-06: GP Modifier Effects

**Priority:** P2 | **Phase:** 21.0

### Description
GP modifier-based effects for Grease Pencil strokes.

**IMPORTANT**: Grease Pencil has its own modifier stack. Geometry Nodes cannot process GP data. This requirement uses `bpy.types.GreasePencilModifiers`, NOT Geometry Nodes.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 06-01 | Build effect | Animate stroke drawing/reveal using GP_BUILD modifier |
| 06-02 | Noise effect | Add procedural noise to strokes using GP_NOISE modifier |
| 06-03 | Smooth effect | Smooth stroke curves using GP_SMOOTH modifier |
| 06-04 | Opacity effect | Control stroke opacity using GP_OPACITY modifier |
| 06-05 | Color effect | Tint/adjust stroke colors using GP_COLOR modifier |
| 06-06 | Mirror effect | Mirror strokes using GP array modifier |
| 06-07 | Custom effects | User can create new GP modifier presets |

### Available GP Modifiers

| Modifier | Type | Description |
|----------|------|-------------|
| `GP_BUILD` | Build | Animate stroke drawing/reveal |
| `GP_NOISE` | Noise | Procedural noise on strokes |
| `GP_SMOOTH` | Smooth | Smooth stroke curves |
| `GP_SIMPLIFY` | Simplify | Reduce stroke point count |
| `GP_OPACITY` | Opacity | Control stroke opacity |
| `GP_COLOR` | Color | Tint/adjust colors |
| `GP_OFFSET` | Offset | Offset strokes in 3D space |
| `GP_TEXTURE` | Texture | Texture mapping on strokes |
| `GP_ARMATURE` | Armature | Bone-based deformation |
| `GP_HOOK` | Hook | Hook modifier for points |

### Effect Presets

| Effect | Description | GP Modifier |
|--------|-------------|-------------|
| `build_reveal` | Animate stroke from start to end | `GP_BUILD` |
| `noise_wiggle` | Add procedural wiggle | `GP_NOISE` |
| `smooth_lines` | Smooth stroke curves | `GP_SMOOTH` |
| `fade_in` | Gradual opacity increase | `GP_OPACITY` |
| `color_shift` | Color/tint adjustment | `GP_COLOR` |

### Effect Configuration

```yaml
GPEffectConfig:
  effect_type: "build_reveal"
  modifier_type: "GP_BUILD"
  seed: null  # Auto-derive from params
  parameters:
    mode: "GROWTH"  # or "CONCURRENT"
    start_frame: 1
    end_frame: 24
    direction: "start_to_end"  # or "end_to_start"
  mask:
    type: null  # Optional mask config
```

### Technical Approach
- `gp_effects.py` configures GP modifiers via Python
- Effects use GP's native modifier stack (NOT Geometry Nodes)
- Modifiers are non-destructive and real-time
- Can be baked to keyframes for export

### Example Implementation

```python
# lib/grease_pencil/gp_effects.py

import bpy
from typing import Optional, Dict, Any

def apply_build_effect(
    gp_obj: bpy.types.Object,
    params: Dict[str, Any],
    seed: Optional[int] = None
) -> bpy.types.GreasePencilModifier:
    """
    Apply GP Build modifier for stroke reveal animation.

    Uses GP_BUILD modifier (NOT Geometry Nodes).
    """
    # Derive seed if not provided
    if seed is None:
        seed = hash(str(sorted(params.items()))) % (2**31)

    modifier = gp_obj.grease_pencil_modifiers.new("Build", 'GP_BUILD')
    modifier.mode = params.get('mode', 'GROWTH')
    modifier.start_frame = params.get('start_frame', 1)
    modifier.end_frame = params.get('end_frame', 24)

    return modifier

def apply_noise_effect(
    gp_obj: bpy.types.Object,
    params: Dict[str, Any],
    seed: Optional[int] = None
) -> bpy.types.GreasePencilModifier:
    """
    Apply GP Noise modifier for procedural wiggle.

    Uses GP_NOISE modifier (NOT Geometry Nodes).
    """
    if seed is None:
        seed = hash(str(sorted(params.items()))) % (2**31)

    modifier = gp_obj.grease_pencil_modifiers.new("Noise", 'GP_NOISE')
    modifier.factor = params.get('factor', 0.5)
    modifier.seed = seed

    return modifier
```

---

## REQ-GP-07: Rotoscope Support

**Priority:** P2 | **Phase:** 21.2

### Description
Tools for tracing video reference and integrating with motion tracking.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 07-01 | Video import | Load video as GP background |
| 07-02 | Frame navigation | Navigate video frames |
| 07-03 | Onion skin video | Show previous/next frames |
| 07-04 | Tracking integration | Link to `lib/cinematic/tracking/` |
| 07-05 | Auto-trace | Convert video edges to strokes (optional) |
| 07-06 | Speed control | Variable playback speed |

### Rotoscope Configuration

```yaml
RotoscopeConfig:
  video_path: "/path/to/reference.mp4"
  frame_offset: 0
  opacity: 0.5
  onion_skin:
    enabled: true
    frames_before: 2
    frames_after: 2
    opacity_falloff: 0.5
```

### Technical Approach
- Use Blender's background image feature
- Integration with existing tracking system
- Optional: OpenCV for edge detection

---

## REQ-GP-08: Export Pipeline

**Priority:** P2 | **Phase:** 21.3

### Description
Render and export pipeline for GP animations.

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| 08-01 | Image sequence | Export as PNG/JPEG sequence |
| 08-02 | Video export | Export as MP4/ProRes |
| 08-03 | EXR with layers | Multi-layer EXR with GP passes |
| 08-04 | SVG export | Vector export for print/web |
| 08-05 | PDF export | Animation sheets/storyboards |
| 08-06 | Batch rendering | Render multiple shots |

### Export Configuration

```yaml
GPExportConfig:
  format: "png_sequence"
  resolution: [1920, 1080]
  frame_range: [1, 100]
  output_path: "/renders/gp_animation/"
  layers:
    - name: "Line_Art"
      include_alpha: true
    - name: "Color"
      include_alpha: true
  compositing:
    merge_layers: true
    background_color: [1.0, 1.0, 1.0, 1.0]
```

### Technical Approach
- Integration with `lib/export/` module
- Use Blender's render pipeline
- Compositor nodes for layer management

---

## Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Stroke creation | < 10ms per stroke |
| NFR-02 | Material preview | Real-time in viewport |
| NFR-03 | Node graph generation | < 100ms per effect |
| NFR-04 | Render time | 30fps playback minimum |

### Compatibility

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-05 | Blender version | 4.0+ (GPv3) |
| NFR-06 | Export formats | PNG, MP4, EXR, SVG, PDF |
| NFR-07 | Integration | lib/animation, lib/cinematic |

### Quality

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-08 | Test coverage | 80%+ for all modules |
| NFR-09 | Documentation | All public APIs documented |
| NFR-10 | Determinism | Same config = same output |

---

## Dependencies

### Internal Dependencies

| Module | Status | Purpose |
|--------|--------|---------|
| `lib/geometry_nodes/` | ✓ Exists | NodeTreeBuilder pattern for shader node generation |
| `lib/animation/` | ✓ Exists | Rigging, poses, onion skinning integration |
| `lib/cinematic/` | ✓ Exists | Camera, compositing, tracking integration |
| `lib/export/` | ✓ Exists | FBX, image sequence export utilities |
| `lib/materials/` | ✓ Exists | PBR material integration |

### External Dependencies
- Blender 4.0+ (Grease Pencil v3)
- FFmpeg (video export)

### Dependency Usage

```python
# From lib/geometry_nodes - NodeTreeBuilder pattern for shader nodes
from lib.geometry_nodes import NodeTreeBuilder

# From lib/animation - Rigging integration
from lib.animation import RigBuilder, PoseLibrary

# From lib/cinematic - Camera and tracking
from lib.cinematic import CameraRig, MotionTracker

# From lib/export - Export utilities
from lib.export import FBXExporter, ImageSequenceExporter
```

---

## Glossary

| Term | Definition |
|------|------------|
| **GP** | Grease Pencil - Blender's 2D drawing in 3D space tool |
| **GPv3** | Grease Pencil version 3 (Blender 4.0+) |
| **NPR** | Non-Photorealistic Rendering |
| **Cut-out** | Puppet-style animation with rigged pieces |
| **Onion Skinning** | Showing adjacent frames for reference |
| **Stroke** | A single drawn line in Grease Pencil |
| **Layer** | Collection of strokes with shared properties |
| **Shader Node Group** | Reusable shader node tree |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-05 | Initial requirements from tutorial synthesis |
| 1.1 | 2026-03-05 | Council of Ricks review fixes: GP modifiers (not Geo Nodes), stage pipeline, determinism, mask infrastructure, GP material types, public API, brush_config clarification |
