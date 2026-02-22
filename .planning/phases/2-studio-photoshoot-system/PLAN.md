# Phase 2: Studio & Photoshoot System

**Status:** Planning
**Created:** 2026-02-21
**Target:** Scene Generation System

---

## Overview

Complete photoshoot lighting and backdrop presets with material library integration. This phase builds on the existing cinematic foundation (lib/cinematic/) to create a professional studio photography system with 12 portrait lighting patterns, 8 product photography categories, equipment simulation, and full Sanctus material library integration.

---

## Requirements Mapped

| ID | Name | Priority | Plan(s) |
|----|------|----------|---------|
| REQ-PH-01 | Portrait Lighting Presets | P0 | 01, 02 |
| REQ-PH-02 | Product Photography Presets | P0 | 03 |
| REQ-PH-03 | Equipment Simulation | P1 | 04 |
| REQ-PH-04 | Camera Presets | P1 | 05 |
| REQ-PH-05 | Backdrop System | P1 | 06 |
| REQ-PH-06 | Photoshoot Orchestrator | P0 | 07 |
| REQ-PH-07 | Atmospherics | P2 | 08 |
| REQ-PH-08 | Material Library System | P0 | 09 |
| REQ-PH-09 | Sanctus Integration | P0 | 09 |
| REQ-PH-10 | Material Variation System | P1 | 10 |

---

## Dependency Graph

```
Wave 1 (Foundation):
  01-portrait-lighting ────┐
  02-portrait-advanced ────┤
  03-product-presets ──────┼──► Wave 3
  04-equipment ────────────┤
  05-camera-presets ───────┤
  06-backdrop-system ──────┘

Wave 2 (Core Integration):
  09-material-library ────────────► Wave 3

Wave 3 (Orchestration):
  07-photoshoot-orchestrator
  10-material-variations

Wave 4 (Effects):
  08-atmospherics
```

---

## Plans

### Plan 01: Portrait Lighting Foundation (Wave 1)

**Goal:** Implement 6 core portrait lighting patterns

**Requirements:** REQ-PH-01 (partial)

**Files Modified:**
- lib/cinematic/light_rigs.py (EXTEND)
- configs/cinematic/lighting/portrait_presets.yaml (NEW)

**Tasks:**

#### Task 1.1: Core Portrait Patterns
<task type="auto">
<name>Implement 6 core portrait lighting patterns</name>
<files>
lib/cinematic/light_rigs.py
configs/cinematic/lighting/portrait_presets.yaml
</files>
<action>
Add the following portrait lighting pattern functions to lib/cinematic/light_rigs.py:

1. **Rembrandt Lighting** (create_rembrandt_lighting)
   - Key light at 45 degrees, elevated 45 degrees
   - Triangle of light on shadow-side cheek
   - Fill light at 2:1 ratio opposite key
   - Position: key_angle=45, key_elevation=45, fill_ratio=0.5

2. **Loop Lighting** (create_loop_lighting)
   - Key light creates small shadow loop from nose to cheek
   - Less dramatic than Rembrandt
   - Position: key_angle=30-45, key_elevation=30, fill_ratio=0.6

3. **Butterfly/Paramount Lighting** (create_butterfly_lighting)
   - Key light directly above and in front of subject
   - Butterfly-shaped shadow under nose
   - Optional reflector below for fill
   - Position: key directly above at 25-45 degrees, fill_ratio=0.3

4. **Split Lighting** (create_split_lighting)
   - Key light at 90 degrees (side)
   - Dramatic half-face illumination
   - Minimal or no fill
   - Position: key_angle=90, key_elevation=15, fill_ratio=0.1

5. **Broad Lighting** (create_broad_lighting)
   - Key illuminates the side of face turned toward camera
   - Makes face appear wider
   - Position: key_angle=-30 to -45, fill_ratio=0.4

6. **Short Lighting** (create_short_lighting)
   - Key illuminates the side of face turned away from camera
   - Makes face appear slimmer, more dramatic
   - Position: key_angle=30-45, fill_ratio=0.4

Each function should:
- Accept subject_position: Tuple[float, float, float]
- Accept optional intensity: float for key light power
- Return List[LightConfig] with key, fill, and optional rim/hair lights
- Follow existing function patterns in light_rigs.py

Also create portrait_presets.yaml with preset definitions referencing these functions.

DO NOT implement the remaining 6 patterns (Clamshell, High Key, Low Key, Rim/Edge, Flat/Fill, Dramatic) - those are in Plan 02.
</action>
<verify>
python -c "
from lib.cinematic.light_rigs import (
    create_rembrandt_lighting,
    create_loop_lighting,
    create_butterfly_lighting,
    create_split_lighting,
    create_broad_lighting,
    create_short_lighting,
)
# Test each function returns valid LightConfig list
for fn in [create_rembrandt_lighting, create_loop_lighting, create_butterfly_lighting,
           create_split_lighting, create_broad_lighting, create_short_lighting]:
    lights = fn((0, 0, 1))
    assert len(lights) >= 2, f'{fn.__name__} should have at least 2 lights'
    assert all(hasattr(l, 'name') for l in lights), 'All lights should have names'
print('All 6 core portrait patterns validated')
"
</verify>
<done>
All 6 core portrait lighting functions implemented and tested. Presets file created with pattern definitions.
</done>
</task>

---

### Plan 02: Portrait Lighting Advanced (Wave 1)

**Goal:** Implement remaining 6 portrait lighting patterns

**Requirements:** REQ-PH-01 (complete)

**Files Modified:**
- lib/cinematic/light_rigs.py (EXTEND)
- configs/cinematic/lighting/portrait_presets.yaml (EXTEND)

**Tasks:**

#### Task 2.1: Advanced Portrait Patterns
<task type="auto">
<name>Implement 6 advanced portrait lighting patterns</name>
<files>
lib/cinematic/light_rigs.py
configs/cinematic/lighting/portrait_presets.yaml
</files>
<action>
Add the following portrait lighting pattern functions to lib/cinematic/light_rigs.py:

1. **Clamshell Lighting** (create_clamshell_lighting)
   - Key light above, reflector/fill below
   - Soft, beauty-focused lighting
   - Minimal shadows, even skin tones
   - Position: key_angle=0 (front), key_elevation=45, fill_below=True

2. **High Key Lighting** (create_high_key_portrait)
   - Bright, minimal shadows, optimistic mood
   - Multiple soft light sources
   - Low contrast ratio (1.5:1 or less)
   - Often uses large softboxes or diffusion

3. **Low Key Lighting** (create_low_key_portrait)
   - Dark, moody, dramatic
   - Single key light, minimal fill
   - High contrast ratio (8:1 or more)
   - Strong shadows, selective illumination

4. **Rim/Edge Lighting** (create_rim_lighting)
   - Light from behind subject
   - Creates outline/rim of light around subject
   - Often combined with fill for face
   - Separation from background

5. **Flat/Fill Lighting** (create_flat_lighting)
   - Even illumination across subject
   - Multiple lights at similar intensities
   - Used for beauty, catalog work
   - Minimal shadow depth

6. **Dramatic Lighting** (create_dramatic_lighting)
   - Single, hard key light
   - Strong directional shadows
   - Minimal fill (10% or less)
   - High contrast, artistic effect

Add these to list_light_rig_presets() function and portrait_presets.yaml.

Follow same patterns as Task 1.1 for function signatures and return values.
</action>
<verify>
python -c "
from lib.cinematic.light_rigs import (
    create_clamshell_lighting,
    create_high_key_portrait,
    create_low_key_portrait,
    create_rim_lighting,
    create_flat_lighting,
    create_dramatic_lighting,
    list_light_rig_presets,
)
# Test each function
for fn in [create_clamshell_lighting, create_high_key_portrait, create_low_key_portrait,
           create_rim_lighting, create_flat_lighting, create_dramatic_lighting]:
    lights = fn((0, 0, 1))
    assert len(lights) >= 1, f'{fn.__name__} should have at least 1 light'
# Verify all 12 patterns are listed
presets = list_light_rig_presets()
portrait_presets = [p for p in presets if any(name in p for name in
    ['rembrandt', 'loop', 'butterfly', 'split', 'broad', 'short',
     'clamshell', 'high_key_portrait', 'low_key_portrait', 'rim', 'flat', 'dramatic'])]
assert len(portrait_presets) >= 12, f'Expected 12 portrait presets, got {len(portrait_presets)}'
print('All 12 portrait patterns validated')
"
</verify>
<done>
All 12 portrait lighting patterns implemented and listed in preset registry.
</done>
</task>

---

### Plan 03: Product Photography Presets (Wave 1)

**Goal:** Implement 8 product photography lighting categories

**Requirements:** REQ-PH-02

**Files Modified:**
- lib/cinematic/light_rigs.py (EXTEND)
- configs/cinematic/lighting/product_presets.yaml (NEW)

**Tasks:**

#### Task 3.1: Product Photography Categories
<task type="auto">
<name>Implement 8 product photography lighting presets</name>
<files>
lib/cinematic/light_rigs.py
configs/cinematic/lighting/product_presets.yaml
</files>
<action>
Create product photography lighting presets for 8 categories:

1. **Electronics/Gadgets** (create_product_electronics)
   - Clean, bright key light overhead
   - Soft fill cards on sides
   - Rim light for edge definition
   - Good for phones, laptops, devices

2. **Cosmetics/Beauty** (create_product_cosmetics)
   - Soft, diffused lighting
   - Multiple fill sources for even coverage
   - Emphasis on texture and color accuracy
   - Clamshell-style for reflective surfaces

3. **Food/Beverage** (create_product_food)
   - Warm, appetizing tones
   - Large softbox for natural window light feel
   - Backlight for steam/freshness
   - Props and surface considerations

4. **Jewelry/Watches** (create_product_jewelry)
   - Multiple small point lights for sparkle
   - Tent/dome lighting for reflections
   - Clean white or black backgrounds
   - Macro-optimized positioning

5. **Fashion/Apparel** (create_product_fashion)
   - Large softboxes for fabric texture
   - Fill for fold details
   - Even illumination across surface
   - Optional hero lighting for draping

6. **Automotive** (create_product_automotive)
   - Large light banks for reflections
   - Gradient lighting on curves
   - Ground reflection plates
   - Multiple rim lights for body lines

7. **Furniture** (create_product_furniture)
   - Balanced area lighting
   - Accent for materials (wood grain, fabric)
   - Context/environmental lighting
   - Scale-appropriate softness

8. **Industrial/Technical** (create_product_industrial)
   - Clear, technical documentation style
   - Flat, even lighting for detail visibility
   - Minimal artistic interpretation
   - Multi-angle consistency

Each function should accept subject_position and optional parameters for customization.
Create product_presets.yaml with all preset definitions.
</action>
<verify>
python -c "
from lib.cinematic.light_rigs import (
    create_product_electronics,
    create_product_cosmetics,
    create_product_food,
    create_product_jewelry,
    create_product_fashion,
    create_product_automotive,
    create_product_furniture,
    create_product_industrial,
)
import os

# Test each product preset
for fn in [create_product_electronics, create_product_cosmetics, create_product_food,
           create_product_jewelry, create_product_fashion, create_product_automotive,
           create_product_furniture, create_product_industrial]:
    lights = fn((0, 0, 0.5))
    assert len(lights) >= 2, f'{fn.__name__} should have at least 2 lights'

# Verify YAML exists
assert os.path.exists('configs/cinematic/lighting/product_presets.yaml'), 'product_presets.yaml should exist'
print('All 8 product photography categories validated')
"
</verify>
<done>
All 8 product photography presets implemented and configuration file created.
</done>
</task>

---

### Plan 04: Equipment Simulation (Wave 1)

**Goal:** Implement studio equipment simulation with 15+ equipment types

**Requirements:** REQ-PH-03

**Files Modified:**
- lib/cinematic/equipment.py (NEW)
- lib/cinematic/types.py (EXTEND)
- configs/cinematic/equipment/equipment_library.yaml (NEW)

**Tasks:**

#### Task 4.1: Equipment Types and Data Structures
<task type="auto">
<name>Create equipment types and configuration structures</name>
<files>
lib/cinematic/types.py
</files>
<action>
Add to lib/cinematic/types.py:

1. **EquipmentConfig dataclass**
   - name: str (equipment identifier)
   - equipment_type: str (softbox, umbrella, etc.)
   - manufacturer: str (optional brand)
   - model: str (specific model)
   - light_output: float (watts or equivalent)
   - color_temp: float (kelvin, default 5500)
   - dimensions: Tuple[float, float, float] (width, height, depth in meters)
   - weight: float (kg)
   - mount_type: str (light_stand, boom, ceiling, floor)
   - modifiers: List[str] (attached modifiers like grids, diffusion)
   - properties: Dict[str, Any] (type-specific properties)

2. **EquipmentType enum**
   - SOFTBOX_RECTANGULAR
   - SOFTBOX_STRIP
   - SOFTBOX_OCTAGONAL
   - UMBRELLA_TRANSPARENT
   - UMBRELLA_SILVER
   - UMBRELLA_WHITE
   - BEAUTY_DISH
   - PARABOLIC
   - FRESNEL
   - SPOTLIGHT
   - FLOODLIGHT
   - RING_LIGHT
   - LED_PANEL
   - TUNGSTEN
   - STROBE
   - FLUORESCENT

3. **ModifierConfig dataclass**
   - modifier_type: str (grid, diffusion, gel, barn_doors, snoot)
   - size: str (full, half, quarter)
   - transmission: float (0-1)
   - color_shift: Tuple[float, float, float] (RGB multiplier)

Include from_dict() and to_dict() methods for all dataclasses.
</action>
<verify>
python -c "
from lib.cinematic.types import EquipmentConfig, EquipmentType, ModifierConfig

# Test EquipmentConfig
config = EquipmentConfig(
    name='test_softbox',
    equipment_type='softbox_rectangular',
    light_output=500.0
)
assert config.color_temp == 5500.0, 'Default color temp should be 5500K'

# Test serialization
d = config.to_dict()
config2 = EquipmentConfig.from_dict(d)
assert config2.name == config.name, 'Serialization round-trip failed'

# Test EquipmentType enum
assert hasattr(EquipmentType, 'SOFTBOX_RECTANGULAR'), 'Missing SOFTBOX_RECTANGULAR'
assert hasattr(EquipmentType, 'RING_LIGHT'), 'Missing RING_LIGHT'
assert len(list(EquipmentType)) >= 15, 'Need at least 15 equipment types'

print('Equipment types and configs validated')
"
</verify>
<done>
EquipmentConfig, EquipmentType, and ModifierConfig dataclasses created with full serialization support.
</done>
</task>

#### Task 4.2: Equipment Library Module
<task type="auto">
<name>Create equipment simulation module</name>
<files>
lib/cinematic/equipment.py
configs/cinematic/equipment/equipment_library.yaml
</files>
<action>
Create lib/cinematic/equipment.py with:

1. **create_equipment_light(equipment_config: EquipmentConfig) -> LightConfig**
   - Converts equipment specifications to LightConfig
   - Maps equipment dimensions to light size/shape
   - Applies color temperature
   - Sets appropriate intensity based on equipment type

2. **EquipmentLibrary class**
   - load_from_yaml(path: Path) -> Dict[str, EquipmentConfig]
   - get_equipment(name: str) -> EquipmentConfig
   - list_equipment_by_type(equipment_type: str) -> List[str]
   - apply_modifier(config: EquipmentConfig, modifier: ModifierConfig) -> EquipmentConfig

3. **Pre-defined equipment presets:**
   - softbox_2x3_rectangular: Standard 2x3ft softbox
   - softbox_strip_1x4: Strip softbox for rim lighting
   - octabox_60cm: 60cm octagonal softbox
   - beauty_dish_56cm: 56cm beauty dish
   - umbrella_105cm_translucent: Large shoot-through umbrella
   - umbrella_85cm_silver: Silver reflective umbrella
   - parabolic_180cm: Large parabolic reflector
   - fresnel_2k: 2000W fresnel spotlight
   - led_panel_1x1: 1x1ft LED panel
   - ring_light_45cm: 45cm ring light
   - strobe_500ws: 500 watt-second strobe
   - tungsten_1k: 1000W tungsten
   - fluorescent_4bank: 4-tube fluorescent bank
   - spotlight_hard: Hard edge spotlight
   - floodlight_broad: Broad floodlight

Create configs/cinematic/equipment/equipment_library.yaml with all presets.

Reference lib/cinematic/lighting.py patterns for bpy import guards.
</action>
<verify>
python -c "
from lib.cinematic.equipment import (
    create_equipment_light,
    EquipmentLibrary,
)
from lib.cinematic.types import EquipmentConfig, EquipmentType
import os

# Test library loading
lib = EquipmentLibrary()
lib.load_from_yaml('configs/cinematic/equipment/equipment_library.yaml')

# Verify equipment count
equipment = lib.list_equipment_by_type('softbox_rectangular')
assert len(equipment) >= 1, 'Should have at least one softbox'

# Test conversion to LightConfig
config = lib.get_equipment('softbox_2x3_rectangular')
light_config = create_equipment_light(config)
assert light_config is not None, 'Should create LightConfig'
assert light_config.light_type == 'area', 'Softbox should be area light'

# Verify YAML exists
assert os.path.exists('configs/cinematic/equipment/equipment_library.yaml'), 'equipment_library.yaml should exist'
print('Equipment library module validated')
"
</verify>
<done>
Equipment module created with 15+ equipment presets and LightConfig conversion.
</done>
</task>

---

### Plan 05: Camera Presets (Wave 1)

**Goal:** Implement 8 focal length presets for portrait and product work

**Requirements:** REQ-PH-04

**Files Modified:**
- lib/cinematic/camera.py (EXTEND)
- configs/cinematic/cameras/portrait_lens_presets.yaml (NEW)
- configs/cinematic/cameras/product_lens_presets.yaml (NEW)

**Tasks:**

#### Task 5.1: Portrait and Product Lens Presets
<task type="auto">
<name>Create specialized lens presets for photoshoot work</name>
<files>
lib/cinematic/camera.py
configs/cinematic/cameras/portrait_lens_presets.yaml
configs/cinematic/cameras/product_lens_presets.yaml
</files>
<action>
Extend lib/cinematic/camera.py with:

1. **apply_portrait_lens_preset(camera: Any, preset_name: str) -> Dict[str, Any]**
   - Loads preset from portrait_lens_presets.yaml
   - Applies focal_length, f_stop, focus_distance
   - Returns applied settings

2. **apply_product_lens_preset(camera: Any, preset_name: str) -> Dict[str, Any]**
   - Loads preset from product_lens_presets.yaml
   - Applies focal_length, f_stop, focus_distance
   - Returns applied settings

Create portrait_lens_presets.yaml with 8 focal lengths:

1. **35mm_environmental** - f/4, environmental portraits
2. **50mm_standard** - f/2.8, standard portrait
3. **85mm_classic** - f/1.8, classic portrait
4. **105mm_beauty** - f/2.8, beauty/headshot
5. **135mm_telephoto** - f/2, compressed perspective
6. **24mm_wide** - f/5.6, full body/environmental
7. **70mm_short_telephoto** - f/2.8, versatile portrait
8. **200mm_long_telephoto** - f/2.8, distant/candid

Create product_lens_presets.yaml with 8 focal lengths:

1. **50mm_general** - f/8, general product
2. **85mm_hero** - f/5.6, hero shots
3. **100mm_macro** - f/11, macro/close-up
4. **24mm_wide** - f/11, large products
5. **35mm_environment** - f/8, product in context
6. **70mm_perspective** - f/8, controlled perspective
7. **135mm_flattering** - f/8, flattering product
8. **180mm_macro** - f/16, extreme macro

Each preset should include:
- focal_length: mm
- f_stop: aperture
- focus_distance: meters (typical working distance)
- sensor_crop: optional crop factor
- description: human-readable description
</action>
<verify>
python -c "
from lib.cinematic.camera import apply_portrait_lens_preset, apply_product_lens_preset
import yaml
import os

# Verify YAML files exist
assert os.path.exists('configs/cinematic/cameras/portrait_lens_presets.yaml'), 'portrait presets missing'
assert os.path.exists('configs/cinematic/cameras/product_lens_presets.yaml'), 'product presets missing'

# Verify preset counts
with open('configs/cinematic/cameras/portrait_lens_presets.yaml') as f:
    portrait = yaml.safe_load(f)
    assert len(portrait.get('presets', {})) >= 8, 'Need 8 portrait presets'

with open('configs/cinematic/cameras/product_lens_presets.yaml') as f:
    product = yaml.safe_load(f)
    assert len(product.get('presets', {})) >= 8, 'Need 8 product presets'

print('Camera presets validated')
"
</verify>
<done>
8 portrait and 8 product lens presets created with associated YAML configuration files.
</done>
</task>

---

### Plan 06: Backdrop System Extension (Wave 1)

**Goal:** Implement 7 backdrop types for studio photography

**Requirements:** REQ-PH-05

**Files Modified:**
- lib/cinematic/backdrops.py (EXTEND)
- configs/cinematic/backdrops/studio_presets.yaml (NEW)

**Tasks:**

#### Task 6.1: Studio Backdrop Types
<task type="auto">
<name>Add 7 studio backdrop types</name>
<files>
lib/cinematic/backdrops.py
configs/cinematic/backdrops/studio_presets.yaml
</files>
<action>
Extend lib/cinematic/backdrops.py with 7 backdrop types:

1. **Seamless Paper** (create_seamless_paper_backdrop)
   - Wide roll of paper, floor sweep
   - Available in multiple colors
   - Smooth, wrinkle-free surface
   - Parameters: color, width, sweep_angle

2. **Muslin/Canvas** (create_muslin_backdrop)
   - Textured fabric backdrop
   - Painted or dyed patterns
   - Draped or hung flat
   - Parameters: color, pattern, drape_amount

3. **Chroma Key** (create_chroma_key_backdrop)
   - Solid green or blue for keying
   - Even illumination critical
   - Parameters: color (green/blue), width

4. **Vinyl/Reflective** (create_vinyl_backdrop)
   - High-gloss reflective surface
   - Shows product reflections
   - Parameters: color, reflectivity

5. **Textured Surface** (create_textured_backdrop)
   - Wood, concrete, marble textures
   - Procedural or image-based
   - Parameters: texture_type, scale

6. **Cyclorama/Wall** (create_cyclorama_backdrop)
   - Large permanent curve installation
   - Painted surfaces
   - Parameters: curve_radius, color

7. **Modular Panel** (create_modular_panel_backdrop)
   - Interlocking panels
   - Customizable patterns
   - Parameters: panel_type, arrangement

Create studio_presets.yaml with presets like:
- studio_white_seamless
- studio_black_velvet
- studio_gray_gradient
- studio_green_screen
- studio_wood_texture
- studio_concrete_industrial

Update create_backdrop() to dispatch to these new functions based on backdrop_type.
</action>
<verify>
python -c "
from lib.cinematic.backdrops import (
    create_seamless_paper_backdrop,
    create_muslin_backdrop,
    create_chroma_key_backdrop,
    create_vinyl_backdrop,
    create_textured_backdrop,
    create_cyclorama_backdrop,
    create_modular_panel_backdrop,
    create_backdrop_from_preset,
)
import os

# Verify each function exists and returns None (Blender not available in test)
for fn in [create_seamless_paper_backdrop, create_muslin_backdrop,
           create_chroma_key_backdrop, create_vinyl_backdrop,
           create_textured_backdrop, create_cyclorama_backdrop,
           create_modular_panel_backdrop]:
    result = fn()  # Call with defaults
    # Should not raise exception

# Verify YAML exists
assert os.path.exists('configs/cinematic/backdrops/studio_presets.yaml'), 'studio_presets.yaml missing'
print('Studio backdrop types validated')
"
</verify>
<done>
7 studio backdrop types implemented with studio_presets.yaml configuration.
</done>
</task>

---

### Plan 07: Photoshoot Orchestrator (Wave 3)

**Goal:** Create orchestrator that combines all photoshoot elements

**Requirements:** REQ-PH-06

**Depends on:** Plans 01-06, 09

**Files Modified:**
- lib/cinematic/photoshoot.py (NEW)
- lib/cinematic/types.py (EXTEND)
- configs/cinematic/photoshoot_presets.yaml (NEW)

**Tasks:**

#### Task 7.1: Photoshoot Configuration Types
<task type="auto">
<name>Create photoshoot configuration data structures</name>
<files>
lib/cinematic/types.py
</files>
<action>
Add to lib/cinematic/types.py:

1. **PhotoshootConfig dataclass**
   - name: str (photoshoot identifier)
   - style: str (portrait, product, fashion, food, etc.)
   - subject_position: Tuple[float, float, float]
   - camera_preset: str (lens preset name)
   - lighting_preset: str (lighting rig name)
   - backdrop_preset: str (backdrop name)
   - equipment_configs: List[EquipmentConfig]
   - color_temperature: float (kelvin)
   - exposure_compensation: float (stops)
   - aspect_ratio: str ("16:9", "4:3", "1:1", etc.)
   - custom_settings: Dict[str, Any]

2. **PhotoshootResult dataclass**
   - success: bool
   - camera_name: str
   - light_names: List[str]
   - backdrop_name: str
   - warnings: List[str]
   - errors: List[str]

Include from_dict() and to_dict() methods.
</action>
<verify>
python -c "
from lib.cinematic.types import PhotoshootConfig, PhotoshootResult

# Test PhotoshootConfig
config = PhotoshootConfig(
    name='test_shoot',
    style='portrait',
    subject_position=(0, 0, 1),
    camera_preset='85mm_classic',
    lighting_preset='rembrandt',
    backdrop_preset='studio_white_seamless'
)
assert config.color_temperature == 5500.0, 'Default color temp'

# Test serialization
d = config.to_dict()
config2 = PhotoshootConfig.from_dict(d)
assert config2.name == config.name, 'Round-trip failed'

# Test PhotoshootResult
result = PhotoshootResult(
    success=True,
    camera_name='camera_01',
    light_names=['key', 'fill'],
    backdrop_name='backdrop_01',
    warnings=[],
    errors=[]
)
assert result.success == True

print('Photoshoot config types validated')
"
</verify>
<done>
PhotoshootConfig and PhotoshootResult dataclasses created with serialization support.
</done>
</task>

#### Task 7.2: Photoshoot Orchestrator Module
<task type="auto">
<name>Create photoshoot orchestrator that assembles complete shoots</name>
<files>
lib/cinematic/photoshoot.py
configs/cinematic/photoshoot_presets.yaml
</files>
<action>
Create lib/cinematic/photoshoot.py with:

1. **PhotoshootOrchestrator class**
   - __init__(self, config: PhotoshootConfig)
   - setup_camera() -> str (returns camera name)
   - setup_lighting() -> List[str] (returns light names)
   - setup_backdrop() -> str (returns backdrop name)
   - setup_equipment() -> List[str] (returns equipment light names)
   - setup_all() -> PhotoshootResult (complete setup)
   - apply_style(style_name: str) -> None (apply preset style)

2. **Preset Styles in photoshoot_presets.yaml:**
   - **portrait_studio_classic**: Rembrandt lighting, 85mm, seamless white
   - **portrait_high_fashion**: Butterfly lighting, 105mm, textured backdrop
   - **portrait_editorial**: Dramatic lighting, 50mm, environmental
   - **product_hero**: Product hero lighting, 85mm, reflective vinyl
   - **product_catalog**: Flat lighting, 50mm, seamless white
   - **product_lifestyle**: Natural lighting, 35mm, textured
   - **food_appetizing**: Food lighting, 50mm, warm tones
   - **jewelry_sparkle**: Jewelry lighting, 100mm macro, black velvet

3. **create_photoshoot(config: PhotoshootConfig) -> PhotoshootOrchestrator**
   - Factory function for creating orchestrator

4. **apply_photoshoot_preset(preset_name: str) -> PhotoshootResult**
   - Load preset from YAML and execute complete setup

Follow existing patterns from lib/cinematic/light_rigs.py and lib/cinematic/camera.py.
</action>
<verify>
python -c "
from lib.cinematic.photoshoot import (
    PhotoshootOrchestrator,
    create_photoshoot,
    apply_photoshoot_preset,
)
from lib.cinematic.types import PhotoshootConfig
import os

# Test orchestrator creation
config = PhotoshootConfig(
    name='test',
    style='portrait',
    subject_position=(0, 0, 1),
    camera_preset='85mm_classic',
    lighting_preset='rembrandt',
    backdrop_preset='studio_white_seamless'
)
orchestrator = create_photoshoot(config)
assert orchestrator is not None, 'Should create orchestrator'

# Verify YAML exists
assert os.path.exists('configs/cinematic/photoshoot_presets.yaml'), 'photoshoot_presets.yaml missing'

print('Photoshoot orchestrator validated')
"
</verify>
<done>
PhotoshootOrchestrator created with 8 preset styles and full setup pipeline.
</done>
</task>

---

### Plan 08: Atmospherics System (Wave 4)

**Goal:** Implement fog, haze, and god rays effects

**Requirements:** REQ-PH-07

**Files Modified:**
- lib/cinematic/atmospherics.py (NEW)
- lib/cinematic/types.py (EXTEND)
- configs/cinematic/atmospherics_presets.yaml (NEW)

**Tasks:**

#### Task 8.1: Atmospheric Effects
<task type="auto">
<name>Create atmospheric effects system</name>
<files>
lib/cinematic/atmospherics.py
lib/cinematic/types.py
configs/cinematic/atmospherics_presets.yaml
</files>
<action>
Create lib/cinematic/atmospherics.py with:

1. **AtmosphericsConfig dataclass** (in types.py)
   - effect_type: str (fog, haze, volumetric_light, dust, smoke)
   - density: float (0-1)
   - color: Tuple[float, float, float] (tint color)
   - height_range: Tuple[float, float] (min/max Z)
   - falloff: str (linear, exponential, quadratic)
   - noise_scale: float (for volumetric variation)
   - noise_depth: int (detail level)
   - anisotropy: float (-1 to 1, light scattering direction)

2. **create_volume_domain(config: AtmosphericsConfig) -> Optional[Any]**
   - Creates volume domain object in Blender
   - Uses shader nodes for volumetric effects
   - Returns domain object

3. **create_fog_plane(height: float, density: float) -> Optional[Any]**
   - Creates ground-level fog
   - Limited height, high density at floor
   - Returns fog object

4. **create_haze_layer(height_range: Tuple[float, float], density: float) -> Optional[Any]**
   - Creates atmospheric haze
   - For depth and mood
   - Returns haze object

5. **create_god_rays(light_name: str, density: float, length: float) -> bool**
   - Creates volumetric light shafts
   - Requires existing spotlight
   - Returns success status

6. **create_dust_particles(count: int, volume: Tuple[float, float, float]) -> Optional[Any]**
   - Creates floating dust motes
   - Animated subtle motion
   - Returns particle system

7. **AtmosphericsPresets:**
   - light_fog: Subtle ground fog
   - heavy_fog: Dense atmosphere
   - light_haze: Atmospheric depth
   - dramatic_haze: Strong mood
   - god_rays_interior: Window light beams
   - god_rays_studio: Spotlight shafts
   - dust_motes: Visible particles
   - smoke_film: Cinematic smoke

Create configs/cinematic/atmospherics_presets.yaml with all presets.

Note: Blender 4.0+ uses volume objects with Principled Volume shader.
</action>
<verify>
python -c "
from lib.cinematic.atmospherics import (
    create_fog_plane,
    create_haze_layer,
    create_god_rays,
    create_dust_particles,
)
from lib.cinematic.types import AtmosphericsConfig
import os

# Test AtmosphericsConfig
config = AtmosphericsConfig(
    effect_type='fog',
    density=0.5
)
assert config.height_range == (0.0, 2.0), 'Default height range'
assert config.falloff == 'exponential', 'Default falloff'

# Test serialization
d = config.to_dict()
config2 = AtmosphericsConfig.from_dict(d)
assert config2.effect_type == config.effect_type

# Verify YAML exists
assert os.path.exists('configs/cinematic/atmospherics_presets.yaml'), 'atmospherics_presets.yaml missing'

print('Atmospherics system validated')
"
</verify>
<done>
Atmospherics system created with fog, haze, god rays, and dust effects.
</done>
</task>

---

### Plan 09: Material Library Integration (Wave 2)

**Goal:** Full Sanctus material library integration for photoshoot surfaces

**Requirements:** REQ-PH-08, REQ-PH-09

**Depends on:** Existing lib/materials/sanctus/

**Files Modified:**
- lib/cinematic/material_library.py (NEW)
- lib/cinematic/types.py (EXTEND)
- configs/cinematic/materials/photoshoot_materials.yaml (NEW)

**Tasks:**

#### Task 9.1: Material Library Wrapper
<task type="auto">
<name>Create material library integration for photoshoot surfaces</name>
<files>
lib/cinematic/material_library.py
lib/cinematic/types.py
configs/cinematic/materials/photoshoot_materials.yaml
</files>
<action>
Create lib/cinematic/material_library.py with:

1. **PhotoshootMaterialConfig dataclass** (in types.py)
   - name: str
   - category: str (backdrop, surface, prop, subject)
   - sanctus_material: str (Sanctus preset name)
   - color_variation: Tuple[float, float, float] (RGB offset)
   - roughness_modifier: float (-0.5 to 0.5)
   - metallic_modifier: float (-0.5 to 0.5)
   - apply_damage: bool
   - damage_type: str (scratches, wear, dust)
   - damage_intensity: float (0-1)

2. **PhotoshootMaterialLibrary class**
   - __init__(self)
   - get_backdrop_materials() -> List[str]
   - get_surface_materials() -> List[str]
   - apply_material(object_name: str, config: PhotoshootMaterialConfig) -> bool
   - create_material_variant(base: str, variations: Dict) -> str
   - list_available_materials() -> List[str]

3. **Integration with Sanctus:**
   - Import from lib.materials.sanctus
   - Use SanctusMaterials.get_material() for base materials
   - Apply variations using SanctusShaderTools
   - Add damage/weathering if enabled

4. **Pre-defined backdrop materials:**
   - backdrop_white_studio: Clean white seamless
   - backdrop_gray_gradient: Gray gradient sweep
   - backdrop_black_velvet: Deep black velvet
   - backdrop_cyclorama_painted: Painted wall texture
   - backdrop_paper_textured: Subtle paper texture
   - backdrop_vinyl_glossy: High-gloss vinyl

5. **Pre-defined surface materials:**
   - surface_wood_oak: Oak wood grain
   - surface_concrete_polished: Polished concrete
   - surface_marble_white: White marble
   - surface_metal_brushed: Brushed metal
   - surface_fabric_canvas: Canvas texture
   - surface_leather_black: Black leather

Create configs/cinematic/materials/photoshoot_materials.yaml with all presets.

Reference existing lib/materials/sanctus/__init__.py for API patterns.
</action>
<verify>
python -c "
from lib.cinematic.material_library import (
    PhotoshootMaterialLibrary,
)
from lib.cinematic.types import PhotoshootMaterialConfig
import os

# Test material library
lib = PhotoshootMaterialLibrary()
backdrops = lib.get_backdrop_materials()
assert len(backdrops) >= 6, 'Need at least 6 backdrop materials'

surfaces = lib.get_surface_materials()
assert len(surfaces) >= 6, 'Need at least 6 surface materials'

# Test config
config = PhotoshootMaterialConfig(
    name='test_material',
    category='backdrop',
    sanctus_material='backdrop_white_studio'
)
assert config.apply_damage == False, 'Default no damage'

# Verify YAML exists
assert os.path.exists('configs/cinematic/materials/photoshoot_materials.yaml'), 'photoshoot_materials.yaml missing'

print('Material library integration validated')
"
</verify>
<done>
PhotoshootMaterialLibrary created with Sanctus integration and preset materials.
</done>
</task>

---

### Plan 10: Material Variation System (Wave 3)

**Goal:** System for creating material variations per shot

**Requirements:** REQ-PH-10

**Depends on:** Plan 09

**Files Modified:**
- lib/cinematic/material_library.py (EXTEND)
- lib/cinematic/types.py (EXTEND)
- configs/cinematic/materials/variation_presets.yaml (NEW)

**Tasks:**

#### Task 10.1: Material Variation Engine
<task type="auto">
<name>Create material variation and randomization system</name>
<files>
lib/cinematic/material_library.py
lib/cinematic/types.py
configs/cinematic/materials/variation_presets.yaml
</files>
<action>
Extend lib/cinematic/material_library.py with:

1. **MaterialVariationConfig dataclass** (in types.py)
   - base_material: str
   - color_range: Tuple[Tuple[float,float,float], Tuple[float,float,float]] (min/max RGB)
   - roughness_range: Tuple[float, float] (min/max)
   - metallic_range: Tuple[float, float] (min/max)
   - pattern_scale_range: Tuple[float, float] (min/max)
   - damage_probability: float (0-1)
   - damage_types: List[str] (available damage types)
   - seed: Optional[int] (for reproducible variations)

2. **MaterialVariationEngine class**
   - generate_variation(config: MaterialVariationConfig) -> PhotoshootMaterialConfig
   - generate_batch(base: str, count: int) -> List[PhotoshootMaterialConfig]
   - apply_variation(object_name: str, config: MaterialVariationConfig) -> bool
   - create_variation_sequence(base: str, steps: int, interpolate: bool) -> List[PhotoshootMaterialConfig]

3. **Pre-defined variation presets:**
   - **wood_aged_vary**: Oak wood with varying age/wear
   - **metal_weathered_vary**: Metal with weathering variations
   - **fabric_worn_vary**: Fabric with wear patterns
   - **stone_textured_vary**: Stone with texture variations
   - **paint_faded_vary**: Paint with fading variations
   - **plastic_used_vary**: Plastic with use marks

4. **Variation Modes:**
   - random: Fully random within ranges
   - grid: Systematic sampling of parameter space
   - sequential: Gradual progression through variations
   - weighted: Weighted probability distribution

Create configs/cinematic/materials/variation_presets.yaml with all presets.
</action>
<verify>
python -c "
from lib.cinematic.material_library import (
    MaterialVariationEngine,
)
from lib.cinematic.types import MaterialVariationConfig
import os

# Test variation engine
engine = MaterialVariationEngine()

# Test variation config
config = MaterialVariationConfig(
    base_material='surface_wood_oak',
    color_range=((0.8, 0.6, 0.4), (1.0, 0.8, 0.6)),
    roughness_range=(0.3, 0.7),
    seed=42
)

# Generate variation
variation = engine.generate_variation(config)
assert variation is not None, 'Should generate variation'
assert variation.name.startswith('surface_wood_oak'), 'Variation should be based on base'

# Generate batch
batch = engine.generate_batch('surface_wood_oak', 5)
assert len(batch) == 5, 'Should generate 5 variations'

# Verify YAML exists
assert os.path.exists('configs/cinematic/materials/variation_presets.yaml'), 'variation_presets.yaml missing'

print('Material variation system validated')
"
</verify>
<done>
MaterialVariationEngine created with random, grid, sequential, and weighted variation modes.
</done>
</task>

---

## Verification

### Phase Verification Commands

```bash
# Test all portrait lighting patterns
python -c "
from lib.cinematic.light_rigs import list_light_rig_presets
presets = list_light_rig_presets()
portrait = [p for p in presets if any(x in p for x in ['rembrandt', 'loop', 'butterfly', 'split', 'broad', 'short', 'clamshell', 'high_key_portrait', 'low_key_portrait', 'rim', 'flat', 'dramatic'])]
assert len(portrait) >= 12, f'Expected 12 portrait presets, got {len(portrait)}'
print(f'OK: {len(portrait)} portrait presets available')
"

# Test all product presets
python -c "
from lib.cinematic.light_rigs import list_light_rig_presets
presets = list_light_rig_presets()
product = [p for p in presets if any(x in p for x in ['electronics', 'cosmetics', 'food', 'jewelry', 'fashion', 'automotive', 'furniture', 'industrial'])]
assert len(product) >= 8, f'Expected 8 product presets, got {len(product)}'
print(f'OK: {len(product)} product presets available')
"

# Test equipment library
python -c "
from lib.cinematic.equipment import EquipmentLibrary
lib = EquipmentLibrary()
lib.load_from_yaml('configs/cinematic/equipment/equipment_library.yaml')
print('OK: Equipment library loaded')
"

# Test photoshoot orchestrator
python -c "
from lib.cinematic.photoshoot import apply_photoshoot_preset
# This will return empty result outside Blender, but should not error
result = apply_photoshoot_preset('portrait_studio_classic')
print('OK: Photoshoot orchestrator functional')
"

# Test atmospherics
python -c "
from lib.cinematic.atmospherics import create_fog_plane, create_haze_layer
print('OK: Atmospherics functions available')
"

# Test material library
python -c "
from lib.cinematic.material_library import PhotoshootMaterialLibrary
lib = PhotoshootMaterialLibrary()
materials = lib.list_available_materials()
assert len(materials) >= 12, f'Expected 12+ materials, got {len(materials)}'
print(f'OK: {len(materials)} materials available')
"
```

### Acceptance Criteria

- [ ] 12 portrait lighting patterns implemented (REQ-PH-01)
- [ ] 8 product photography categories implemented (REQ-PH-02)
- [ ] 15+ equipment types in library (REQ-PH-03)
- [ ] 8 camera focal length presets (REQ-PH-04)
- [ ] 7 backdrop types implemented (REQ-PH-05)
- [ ] Photoshoot orchestrator combines all elements (REQ-PH-06)
- [ ] Atmospherics (fog, haze, god rays) working (REQ-PH-07)
- [ ] Material library integrated with Sanctus (REQ-PH-08, REQ-PH-09)
- [ ] Material variation system operational (REQ-PH-10)

---

## Success Criteria

1. **Portrait Lighting**: All 12 patterns produce correct shadow/light characteristics
2. **Product Presets**: Each category optimized for its subject type
3. **Equipment**: 15+ equipment types with accurate light characteristics
4. **Integration**: Photoshoot orchestrator correctly assembles all components
5. **Materials**: Sanctus integration provides high-quality procedural materials

---

## Output

After execution, create `.planning/phases/2-studio-photoshoot-system/2-SUMMARY.md` documenting:
- Files created/modified
- Presets available in each category
- Integration points with existing systems
- Test results and any notes
