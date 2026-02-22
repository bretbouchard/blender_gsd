# PLAN: MSG 1998 Location Building - Render Layer Setup

**Phase:** 9.MSG-03
**Created:** 2026-02-22
**Depends On:** Phase 9.MSG-02 (Modeling Pipeline)
**Output To:** Phase 12.MSG (SD Compositing)

---

## Goal

Configure render passes and layer separation for SD compositing pipeline.

---

## Tasks

### Task 1: Render Pass Configuration
**File:** `lib/msg1998/render_passes.py`

```python
@dataclass
class MSGRenderPasses:
    """Render passes required for SD compositing."""
    beauty: bool = True
    depth: bool = True
    normal: bool = True
    object_id: bool = True
    diffuse: bool = True
    shadow: bool = True
    ao: bool = True
    cryptomatte: bool = True

def configure_render_passes(
    scene: bpy.types.Scene,
    passes: MSGRenderPasses
) -> None:
    """Enable/disable render passes for scene."""
    ...

def get_pass_output_path(base_path: Path, pass_name: str, frame: int) -> Path:
    """Generate output path for render pass."""
    ...
```

### Task 2: Layer Separation System
**File:** `lib/msg1998/layer_separation.py`

```python
@dataclass
class CompositeLayer:
    """Layer for compositing separation."""
    name: str  # "background", "midground", "foreground"
    objects: list[bpy.types.Object]
    render_passes: list[str]
    mask_color: tuple[float, float, float]  # For object ID

def create_composite_layers(
    scene: bpy.types.Scene,
    config: dict
) -> list[CompositeLayer]:
    """Create BG/MG/FG layer separation."""
    ...

def assign_layer_masks(layers: list[CompositeLayer]) -> None:
    """Assign object ID colors for layer masking."""
    ...

# Layer mask colors (distinct for compositing)
LAYER_COLORS = {
    "background": (1.0, 0.0, 0.0),   # Red
    "midground": (0.0, 1.0, 0.0),    # Green
    "foreground": (0.0, 0.0, 1.0),   # Blue
}
```

### Task 3: Export to Compositing
**File:** `lib/msg1998/export_compositing.py`

```python
@dataclass
class CompositingHandoff:
    """Handoff package for Phase 12.MSG."""
    location_id: str
    scene_id: str
    render_dir: Path
    passes: dict[str, Path]  # pass_name -> file_path
    masks: dict[str, Path]   # layer_name -> mask_path
    metadata: dict

def export_for_compositing(
    location_id: str,
    scene_id: str,
    output_dir: Path
) -> CompositingHandoff:
    """Export all renders and masks for compositing."""
    ...

def generate_metadata(
    render_settings: dict,
    camera_settings: dict,
    layer_config: dict
) -> dict:
    """Generate metadata.json for compositing phase."""
    ...
```

### Task 4: Render Profile for MSG 1998
**File:** `lib/msg1998/render_profile.py`

```python
@dataclass
class MSG1998RenderProfile:
    """Render settings for MSG 1998 output."""
    resolution: tuple[int, int] = (4096, 1716)  # 2.39:1 aspect
    frame_rate: int = 24
    color_space: str = "ACEScg"
    samples: int = 256
    use_denoiser: bool = True

    # Output format
    beauty_format: str = "OPEN_EXR"
    pass_format: str = "OPEN_EXR"

def apply_msg_profile(scene: bpy.types.Scene, profile: MSG1998RenderProfile) -> None:
    """Apply MSG 1998 render profile to scene."""
    ...
```

### Task 5: CLI Commands
**File:** `lib/msg1998/cli.py` (extend)

```python
# blender-gsd render-location LOC-XXX --passes all
@app.command()
def render_location(location_id: str, passes: str = "all"):
    """Render location with compositing passes."""
    ...

# blender-gsd export-compositing LOC-XXX --scene SCN-XXX
@app.command()
def export_compositing(location_id: str, scene: str):
    """Export renders for compositing phase."""
    ...
```

---

## Output Structure

```
handoff/compositing/{SCENE_ID}/
├── location_renders/
│   ├── LOC-XXX_beauty.exr
│   ├── LOC-XXX_depth.exr
│   ├── LOC-XXX_normal.exr
│   ├── LOC-XXX_object_id.exr
│   ├── LOC-XXX_diffuse.exr
│   ├── LOC-XXX_shadow.exr
│   └── LOC-XXX_ao.exr
├── masks/
│   ├── LOC-XXX_bg_mask.png
│   ├── LOC-XXX_mg_mask.png
│   └── LOC-XXX_fg_mask.png
└── metadata.json
```

---

## Validation Criteria

- [ ] All required passes render
- [ ] Layer masks separate correctly
- [ ] Metadata generates with correct values
- [ ] Files output to correct structure

---

## Estimated Time

**2-3 hours**
