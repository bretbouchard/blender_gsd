# PLAN: MSG 1998 SD Compositing - Layer Compositing

**Phase:** 12.MSG-02
**Created:** 2026-02-22
**Depends On:** Phase 12.MSG-01 (ControlNet Setup)
**Output To:** Phase 12.MSG-03 (Final Output)

---

## Goal

Implement Blender compositor pipeline for combining SD-generated layers with 1998 film post-processing.

---

## Tasks

### Task 1: Layer Compositor Setup
**File:** `lib/msg1998/layer_compositor.py`

```python
@dataclass
class LayerInput:
    """Input layer for compositing."""
    name: str  # "background", "midground", "foreground"
    sd_output: Path
    original_render: Path
    mask: Path
    depth_value: float  # For depth-based effects

def setup_layer_nodes(
    tree: bpy.types.CompositorNodeTree,
    layer: LayerInput
) -> dict[str, bpy.types.CompositorNode]:
    """Set up compositor nodes for a layer."""
    ...

def composite_layers(
    layers: list[LayerInput],
    depth_map: Path
) -> bpy.types.CompositorNode:
    """Combine all layers with depth-based blending."""
    ...
```

### Task 2: 1998 Film Post-Processing
**File:** `lib/msg1998/film_look_1998.py`

```python
@dataclass
class FilmLook1998:
    """1998 film aesthetic parameters."""
    grain_intensity: float = 0.15
    grain_size: float = 1.0
    lens_distortion: float = 0.02
    chromatic_aberration: float = 0.003
    vignette_strength: float = 0.4
    color_temperature: float = 5500  # Slightly warm

def apply_film_grain(
    image: bpy.types.CompositorNode,
    params: FilmLook1998
) -> bpy.types.CompositorNode:
    """Apply 35mm film grain."""
    ...

def apply_lens_effects(
    image: bpy.types.CompositorNode,
    params: FilmLook1998
) -> bpy.types.CompositorNode:
    """Apply lens distortion and chromatic aberration."""
    ...

def apply_vignette(
    image: bpy.types.CompositorNode,
    params: FilmLook1998
) -> bpy.types.CompositorNode:
    """Apply lens vignette."""
    ...
```

### Task 3: Color Grading (Kodak LUT)
**File:** `lib/msg1998/color_grade.py`

```python
@dataclass
class ColorGradeConfig:
    """Color grading configuration."""
    lut_path: str = "luts/kodak_vision3_500t.cube"
    exposure_adjust: float = 0.0
    contrast_adjust: float = 1.0
    saturation_adjust: float = 1.0
    shadows_lift: float = 0.0
    highlights_roll: float = 1.0

def apply_color_grade(
    image: bpy.types.CompositorNode,
    config: ColorGradeConfig
) -> bpy.types.CompositorNode:
    """Apply color grading with LUT."""
    ...

def create_kodak_lut_node(
    tree: bpy.types.CompositorNodeTree,
    lut_path: Path
) -> bpy.types.CompositorNode:
    """Create Color Balance node with Kodak LUT."""
    ...
```

### Task 4: Depth-Based Effects
**File:** `lib/msg1998/depth_effects.py`

```python
def apply_depth_of_field(
    image: bpy.types.CompositorNode,
    depth_map: bpy.types.CompositorNode,
    focal_distance: float,
    aperture: float = 2.8
) -> bpy.types.CompositorNode:
    """Apply depth of field from depth map."""
    ...

def apply_atmospheric_haze(
    image: bpy.types.CompositorNode,
    depth_map: bpy.types.CompositorNode,
    haze_color: tuple = (0.7, 0.75, 0.8),
    intensity: float = 0.3
) -> bpy.types.CompositorNode:
    """Apply atmospheric perspective based on depth."""
    ...
```

### Task 5: Complete Compositor Graph
**File:** `lib/msg1998/compositor_graph.py`

```python
def build_msg_compositor_graph(
    scene: bpy.types.Scene,
    layers: list[LayerInput],
    depth_map: Path,
    film_look: FilmLook1998,
    color_grade: ColorGradeConfig
) -> None:
    """Build complete compositor node graph for MSG shot."""
    ...

def save_compositor_preset(name: str, tree: bpy.types.CompositorNodeTree) -> dict:
    """Save compositor setup as reusable preset."""
    ...

def load_compositor_preset(name: str, tree: bpy.types.CompositorNodeTree) -> None:
    """Load compositor preset."""
    ...
```

---

## Compositor Node Graph

```
[Layer BG] ───┐
              ├── [Alpha Over] ───┐
[Layer MG] ───┘                   │
                                  ├── [Alpha Over] ───┐
[Layer FG] ───────────────────────┘                   │
                                                      │
[Depth Map] ─── [DOF] ───────────────────────────────┤
                                                      │
                                 [Film Grain] ────────┤
                                 [Lens Distort] ──────┤
                                 [Vignette] ──────────┤
                                 [Color Grade] ───────┤
                                                      │
                                                      ▼
                                               [Composite Output]
```

---

## Validation Criteria

- [ ] Layers composite with correct depth
- [ ] Film grain visible but not excessive
- [ ] Color grade matches Kodak Vision3 look
- [ ] No visible layer edges in final output

---

## Estimated Time

**3-4 hours**
