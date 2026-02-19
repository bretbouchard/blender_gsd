# Shot Presets Requirements

## Overview

Universal shot preset system that can transform any scene into classic photography setups.

## Shot Categories

### 1. Studio Shots (Controlled Environment)

| Preset | Description | Lighting | Background |
|--------|-------------|----------|------------|
| `studio_white` | Clean white infinity curve | Soft 3-point (key/fill/rim) | White infinite curve |
| `studio_black` | Dramatic black | Single hard key, subtle rim | Black void |
| `studio_gray_gradient` | Professional gray fade | Soft even lighting | Gray gradient backdrop |
| `studio_sweep` | Classic draped fabric look | Large softbox overhead | White/gray sweep |
| `studio_laser_grid` | 90s school photo vibe | Even front lighting | Laser background pattern |
| `studio_high_key` | Bright, minimal shadow | Overhead flood + fill | Pure white |
| `studio_low_key` | Moody, dramatic | Single hard key | Black |
| `studio_ring_light` | Beauty/fashion | Ring light frontal | White or black |

### 2. Product Shots

| Preset | Description | Use Case |
|--------|-------------|----------|
| `product_hero` | Apple-style hero shot | Tech products, luxury goods |
| `product_floating` | Object appears to float | Jewelry, small items |
| `product_ghost_mannequin` | Invisible support | Clothing |
| `product_lifestyle` | In-context usage | Consumer goods |
| `product_detail` | Macro close-up | Textures, details |

### 3. Model/Portrait Shots

| Preset | Description | Lighting |
|--------|-------------|----------|
| `portrait_classic` | Timeless studio portrait | Rembrandt lighting |
| `portrait_beauty` | Fashion/glamour | Ring light + soft fill |
| `portrait_dramatic` | High contrast artistic | Hard key, no fill |
| `portrait_environmental` | In-context | Natural + fill |

### 4. Automotive Shots

| Preset | Description | Environment |
|--------|-------------|-------------|
| `car_studio` | Clean studio car | Infinity curve |
| `car_twilight` | Golden/blue hour | Urban/studio blend |
| `car_motion` | Implied motion blur | Streaked lights |
| `car_desert` | Dramatic landscape | Desert at golden hour |
| `car_night_city` | Neon reflections | Wet city street |

### 5. Environment Shots

| Preset | Description | Lighting/Mood |
|--------|-------------|---------------|
| `golden_hour_ocean` | Sunset over water | Warm, long shadows |
| `arizona_midnight` | Desert night sky | Moonlight, stars |
| `deep_space` | Sci-fi void | Distant stars, rim light |
| `forest_mist` | Mystical woodland | Diffuse, foggy |
| `urban_night` | City lights | Neon, reflections |
| `snow_day` | Bright winter | Overcast, soft |

### 6. Signature Looks

| Preset | Description | Inspired By |
|--------|-------------|-------------|
| `apple_hero` | Minimalist product | Apple advertising |
| `ikea_catalog` | Clean lifestyle | IKEA |
| `cosmopolitan` | Magazine glamour | Cosmo covers |
| `national_geo` | Documentary | National Geographic |
| `bladerunner` | Neo-noir sci-fi | Blade Runner 2049 |
| `wes_anderson` | Symmetrical pastel | Wes Anderson films |

## Technical Requirements

### ShotConfig Dataclass

```python
@dataclass
class ShotConfig:
    """Complete shot configuration preset."""
    name: str
    category: str  # studio, product, portrait, automotive, environment

    # Lighting
    lights: List[LightConfig]
    light_setup: str  # "three_point", "ring", "single", "natural"

    # Environment
    backdrop: BackdropConfig
    hdri: Optional[str]  # HDRI environment map
    fog: Optional[FogConfig]
    ground_plane: bool

    # Camera suggestions
    suggested_lens: str  # Preset name
    suggested_fstop: float
    suggested_angle: str  # "front", "three_quarter", "top_down"

    # Post-processing hints
    color_grade: str  # "warm", "cool", "neutral", "dramatic"
    contrast: str  # "high", "medium", "low"
    saturation: float  # 0.0 to 2.0
```

### Functions Needed

1. `load_shot_preset(name: str) -> ShotConfig`
2. `apply_shot_preset(config: ShotConfig, subject_name: str) -> bool`
3. `setup_studio_lighting(setup_type: str) -> List[LightConfig]`
4. `create_backdrop(config: BackdropConfig) -> Any`
5. `list_shot_presets(category: Optional[str]) -> List[str]`

## Files to Create

```
configs/cinematic/shots/
├── studio_presets.yaml      # Studio setups
├── product_presets.yaml     # Product photography
├── portrait_presets.yaml    # Model/portrait
├── automotive_presets.yaml  # Car photography
├── environment_presets.yaml # Location shots
├── signature_presets.yaml   # Famous looks

lib/cinematic/
├── shot_builder.py          # Shot preset system
└── types.py                 # Add ShotConfig, FogConfig
```

## Implementation Phases

### Phase 1: Foundation
- Add `ShotConfig`, `FogConfig` to types.py
- Create shot preset YAML files
- Create `shot_builder.py` with preset loading

### Phase 2: Studio Shots
- Implement studio lighting setups
- Implement backdrop creation (infinite curve, gradient, laser grid)
- Implement fog/atmosphere

### Phase 3: Environment Shots
- HDRI environment support
- Sun/sky system integration
- Ground plane with shadow catching

### Phase 4: One-Click Application
- `apply_shot_preset()` complete workflow
- Subject detection and framing
- Camera position suggestions
