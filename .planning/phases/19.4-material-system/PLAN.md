# Phase 19.4: Material System (REQ-TENT-04)

**Priority:** P1 | **Est. Effort:** 3-4 days
**Depends on:** 19.1 (Geometry)
**Status:** Planning

---

## Goal

Procedural tentacle skin materials with horror-specific themes, subsurface scattering, and wet/slimy effects for Unreal Engine export.

---

## Requirements Coverage

| ID | Requirement | Plan |
|----|-------------|------|
| REQ-TENT-04-01 | Subsurface scattering | 19.4-01 |
| REQ-TENT-04-02 | Color themes (5+ horror presets) | 19.4-01 |
| REQ-TENT-04-03 | Wet/slimy option | 19.4-01 |
| REQ-TENT-04-04 | Vein patterns | 19.4-02 |
| REQ-TENT-04-05 | Texture baking for export | 19.4-03 |
| REQ-TENT-04-06 | Pattern variation | 19.4-02 |
| REQ-TENT-04-07 | Material zones (base/mid/tip) | 19.4-01 |

---

## Module Structure

```
lib/tentacle/materials/
├── __init__.py           # Package exports
├── types.py              # MaterialConfig, ThemePreset, SSSConfig
├── themes.py             # Theme definitions, preset loader
├── skin.py               # SkinShaderGenerator
├── veins.py              # VeinPatternGenerator
├── baking.py             # TextureBaker
└── presets.py            # Preset loader and convenience functions

configs/tentacle/
└── material_presets.yaml  # Theme presets, SSS configs, zone configs
```

---

## Plans

| Plan | Name | Est. Hours | Description |
|------|------|------------|-------------|
| 19.4-01 | Types & Themes | 3-4h | MaterialConfig, ThemePreset, SSSConfig, 5 horror themes |
| 19.4-02 | Skin & Veins | 4-5h | SkinShaderGenerator, VeinPatternGenerator, procedural textures |
| 19.4-03 | Baking & Exports | 2-3h | TextureBaker, package exports, unit tests |

---

## Plan 19.4-01: Types & Themes

### Files to Create

1. **`lib/tentacle/materials/types.py`** - Core data structures
   - `MaterialTheme` enum (rotting, parasitic, demonic, mutated, decayed)
   - `SSSConfig` - Subsurface scattering parameters
   - `WetnessConfig` - Wet/slimy surface settings
   - `VeinConfig` - Vein pattern configuration
   - `MaterialZone` - Zone-based material variation
   - `TentacleMaterialConfig` - Full material configuration

2. **`lib/tentacle/materials/themes.py`** - Theme definitions
   - `THEME_PRESETS` dictionary with 5 horror themes
   - `get_theme_preset()` function
   - Theme blending/mixing utilities

3. **`configs/tentacle/material_presets.yaml`** - YAML configurations
   - 5 horror theme presets with full parameters
   - SSS presets (fleshy, translucent, bone)
   - Wetness presets (dry, moist, slimy, dripping)
   - Zone presets (uniform, gradient, zones)

### Horror Theme Specifications

| Theme | Base Color | SSS Color | Veins | Wetness | Key Features |
|-------|------------|-----------|-------|---------|--------------|
| `rotting` | Gray-green (#6B7B5A) | Strong red | Dark purple | Yellow-brown slime | Necrotic, dead flesh |
| `parasitic` | Flesh pink (#E8B4B8) | Medium pink | Red | Clear slime | Living, infested |
| `demonic` | Deep red (#8B0000) | Strong red | Black | Black oil | Hellish, corrupted |
| `mutated` | Pale flesh (#F5E6D3) | Cyan glow | Bioluminescent | Green slime | Radioactive, alien |
| `decayed` | Bone white (#E8E4D9) | Weak pink | None | Brown ichor | Skeletal, ancient |

### SSS Parameters

```python
@dataclass
class SSSConfig:
    """Subsurface scattering configuration."""
    radius: float = 1.0          # SSS radius in mm
    color: Tuple[float, ...]     # SSS tint color
    weight: float = 1.0          # SSS influence (0-1)
    anisotropy: float = 0.0      # Directional SSS (0-1)
    ior: float = 1.4             # Index of refraction
```

---

## Plan 19.4-02: Skin & Veins

### Files to Create

1. **`lib/tentacle/materials/skin.py`** - Skin shader generator
   - `SkinShaderGenerator` class
   - `create_skin_material()` function
   - Zone-based material blending
   - Dual-mode (Blender nodes / numpy for testing)

2. **`lib/tentacle/materials/veins.py`** - Vein pattern generator
   - `VeinPatternGenerator` class
   - Procedural vein textures using noise
   - Voronoi-based vein networks
   - Bioluminescent glow support

### Skin Shader Features

- Principled BSDF with SSS
- Layered noise for organic variation
- Zone-based color/roughness variation
- Wetness layer with high specularity
- Normal map variation for texture

### Vein Pattern Features

- Voronoi noise for vein network
- Color ramp for vein coloring
- Opacity/visibility control
- Bioluminescent emission for mutated theme

---

## Plan 19.4-03: Baking & Exports

### Files to Create

1. **`lib/tentacle/materials/baking.py`** - Texture baking
   - `TextureBaker` class
   - `bake_material_to_textures()` function
   - Support for Albedo, Normal, Roughness, SSS, Emission maps
   - Resolution control (1K, 2K, 4K)

2. **`lib/tentacle/materials/presets.py`** - Preset loader
   - `MaterialPresetLoader` class
   - `load_material_preset()` convenience function
   - Caching support

3. **`lib/tentacle/materials/__init__.py`** - Package exports
   - Export all types, generators, and utilities

### Bake Map Types

| Map | Resolution | Format | Use Case |
|-----|------------|--------|----------|
| Albedo | 2K/4K | PNG | Base color |
| Normal | 2K/4K | PNG | Surface detail |
| Roughness | 1K/2K | PNG | Specular variation |
| SSS | 1K/2K | PNG | Subsurface mask |
| Emission | 1K/2K | PNG | Bioluminescence |

---

## Testing Strategy

### Unit Tests (`tests/unit/test_tentacle_materials.py`)

- Test all type dataclasses
- Test theme preset loading
- Test skin shader generation (numpy mode)
- Test vein pattern generation
- Test zone-based blending
- Test material preset loader

### Test Count Estimate

| Plan | Unit Tests | Integration |
|------|------------|-------------|
| 19.4-01 | 25-30 | 0 |
| 19.4-02 | 20-25 | 0 |
| 19.4-03 | 15-20 | 5 |
| **Total** | **60-75** | **5** |

---

## Dependencies

### Internal
- `lib/tentacle/types.py` - TentacleConfig for geometry reference
- `lib/tentacle/geometry/` - For UV coordinate generation

### External
- Blender 5.0+ (for material nodes)
- numpy (for testing without Blender)

---

## Success Criteria

1. All 5 horror themes render correctly in Blender
2. SSS produces realistic translucent skin appearance
3. Vein patterns are procedural and configurable
4. Zone-based materials blend smoothly
5. Texture baking produces valid image maps
6. 60+ unit tests passing
7. Materials export-ready for Unreal Engine

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| SSS performance in viewport | Provide simplified viewport mode |
| Texture baking complexity | Start with simple bake, add complexity incrementally |
| UE material compatibility | Use standard Principled BSDF workflow |
| Theme color accuracy | Provide hex values in presets for precision |
