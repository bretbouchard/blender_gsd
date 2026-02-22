# PLAN: MSG 1998 SD Compositing - ControlNet Setup

**Phase:** 12.MSG-01
**Created:** 2026-02-22
**Depends On:** Phase 9.MSG-03 (Render Layers), FDX GSD SD Configs
**Output To:** Phase 12.MSG-02 (Layer Compositing)

---

## Goal

Implement ControlNet pipeline for SD style transfer using depth and normal maps from Blender renders.

---

## Tasks

### Task 1: ControlNet Configuration
**File:** `lib/msg1998/controlnet.py`

```python
@dataclass
class ControlNetConfig:
    """ControlNet configuration for SD generation."""
    depth_model: str = "control_v11f1p_sd15_depth"
    depth_weight: float = 1.0
    normal_model: str = "control_v11p_sd15_normalbae"
    normal_weight: float = 0.8
    guidance_start: float = 0.0
    guidance_end: float = 1.0

def load_controlnet_models(config: ControlNetConfig) -> dict:
    """Load ControlNet models into SD pipeline."""
    ...

def prepare_depth_map(depth_exr: Path, output_dir: Path) -> Path:
    """Convert depth EXR to ControlNet-compatible format."""
    ...

def prepare_normal_map(normal_exr: Path, output_dir: Path) -> Path:
    """Convert normal EXR to ControlNet-compatible format."""
    ...
```

### Task 2: SD Config Receiver
**File:** `lib/msg1998/sd_config.py`

```python
@dataclass
class SDShotConfig:
    """SD configuration for a shot (from FDX GSD)."""
    shot_id: str
    scene_id: str
    seeds: dict[str, int]  # layer -> seed
    positive_prompt: str
    negative_prompt: str
    controlnet_config: ControlNetConfig
    layer_configs: dict

def load_sd_config(config_path: Path) -> SDShotConfig:
    """Load SD config from FDX handoff."""
    ...

def validate_sd_config(config: SDShotConfig) -> list[str]:
    """Validate SD config has all required fields."""
    ...
```

### Task 3: 1998 Film Aesthetic Prompts
**File:** `lib/msg1998/prompts_1998.py`

```python
# Base prompts for 1998 film aesthetic
POSITIVE_BASE = """
1998 film stock, Kodak Vision3 500T 5219,
35mm anamorphic lens, 2.39:1 aspect ratio,
film grain, organic texture, practical lighting,
period accurate 1998 New York City,
Matthew Libatique cinematography style,
handheld camera, documentary feel,
no digital artifacts, no modern elements
"""

NEGATIVE_BASE = """
digital, clean, sharp, 4K, modern,
2020s, smartphones, LED screens,
CGI look, video game aesthetic,
over-processed, HDR, flat lighting,
anamorphic lens blur on edges,
modern cars, contemporary fashion
"""

# Scene-specific modifiers
SCENE_PROMPTS = {
    "msg_exterior": "Madison Square Garden exterior, daytime, establishing shot",
    "msg_interior": "arena concourse, fluorescent lighting, crowd",
    "subway_platform": "underground, tile walls, fluorescent, 1998 graffiti state",
    "subway_car": "MTA subway car interior, 1998 rolling stock",
    "night_exterior": "neon signs, wet pavement, streetlights, urban night",
    "hospital": "fluorescent hospital lighting, sterile, clinical",
    "apartment": "warm interior, cozy, golden hour through window",
}

def build_prompt(base: str, scene_type: str, layer: str) -> str:
    """Build complete prompt for generation."""
    ...
```

### Task 4: SD Generation Pipeline
**File:** `lib/msg1998/sd_generate.py`

```python
@dataclass
class SDGenerationResult:
    """Result of SD generation."""
    layer_name: str
    seed: int
    output_path: Path
    generation_time: float
    controlnet_used: list[str]

def generate_layer(
    config: SDShotConfig,
    layer_name: str,
    depth_map: Path,
    normal_map: Path,
    mask: Path,
    output_dir: Path
) -> SDGenerationResult:
    """Generate SD output for a single layer."""
    ...

def generate_all_layers(
    config: SDShotConfig,
    depth_map: Path,
    normal_map: Path,
    masks: dict[str, Path],
    output_dir: Path
) -> dict[str, SDGenerationResult]:
    """Generate SD output for all layers."""
    ...
```

### Task 5: Seed Verification
**File:** `lib/msg1998/seed_verify.py`

```python
def verify_seed_reproducibility(
    config: SDShotConfig,
    reference_output: Path,
    tolerance: float = 0.01
) -> bool:
    """Verify same seed produces same output."""
    ...

def compute_image_hash(image_path: Path) -> str:
    """Compute perceptual hash for image comparison."""
    ...
```

---

## File Structure

```
lib/msg1998/
├── controlnet.py          # Task 1
├── sd_config.py           # Task 2
├── prompts_1998.py        # Task 3
├── sd_generate.py         # Task 4
├── seed_verify.py         # Task 5
└── ...
```

---

## Validation Criteria

- [ ] ControlNet models load correctly
- [ ] Depth/normal maps convert properly
- [ ] Prompts generate 1998 aesthetic
- [ ] Seeds produce reproducible results

---

## Estimated Time

**3-4 hours**
