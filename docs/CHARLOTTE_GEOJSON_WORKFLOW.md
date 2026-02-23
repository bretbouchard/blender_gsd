# Charlotte Digital Twin - GeoJSON to Blender Workflow

This guide explains how to generate 3D Charlotte buildings from GeoJSON building footprints.

## Overview

The Charlotte Digital Twin system uses real building data from OpenStreetMap to generate accurate 3D building models in Blender. The system includes:

- **1,069 Uptown Charlotte buildings** with accurate footprints
- **Height data** from OSM or estimated from floor count
- **LED facade integration** for illuminated buildings
- **PBR materials** (glass, granite, concrete, steel, brick)

## Quick Start

### In Blender

```python
import sys
sys.path.append('/path/to/blender_gsd')

from lib.charlotte_digital_twin.buildings.geojson_importer import generate_charlotte_scene

# Generate all Uptown Charlotte buildings with LED facades
buildings = generate_charlotte_scene(
    with_leds=True,
    with_materials=True
)

# Or generate only tall buildings (20+ floors)
tall_buildings = generate_charlotte_scene(min_floors=20)
```

### Convenience Functions

| Function | Description |
|----------|-------------|
| `generate_charlotte_scene()` | Full scene with all options |
| `generate_uptown_charlotte()` | All 1,069 Uptown buildings |
| `generate_charlotte_led_buildings()` | Only LED-equipped buildings |
| `generate_charlotte_tall_buildings(min_floors)` | Buildings with N+ floors |

## Data Sources

### GeoJSON Files

| File | Buildings | Size | Description |
|------|-----------|------|-------------|
| `charlotte_uptown_buildings.geojson` | 1,069 | 570 KB | Downtown core |
| `charlotte_buildings_named.geojson` | 4,002 | 2.1 MB | Named buildings |
| `charlotte_buildings.geojson` | 387,329 | 129 MB | Full Charlotte area |

### Building Properties

Each building includes:
- `osm_id` - OpenStreetMap ID
- `name` - Building name (if available)
- `height_m` - Height in meters
- `floors` - Number of floors
- `polygon` - Building footprint coordinates
- `building_type` - Office, residential, etc.
- `material` - Glass, concrete, brick, etc.

## LED Buildings

Charlotte has 10+ buildings with LED/illuminated facades:

| Building | LEDs | Type |
|----------|------|------|
| Duke Energy Center | 2,500 | Full facade |
| FNB Tower | 1,300 | Full facade |
| Ally Charlotte Center | 800 | Full facade |
| NASCAR Hall of Fame | 800 | Ribbon |
| Truist Center | 500 | Accent |
| One Wells Fargo Center | 520 | Crown |
| Honeywell Tower | 560 | Full facade |
| 200 South Tryon | 480 | Accent |
| Bank of America Center | 350 | Crown |
| Carillon Tower | 310 | Spire |

### LED Color Presets

```python
from lib.charlotte_digital_twin.buildings.led_facade import (
    LEDColor,
    LEDFacadeBuilder,
    LEDAnimator,
)

# Create LED buildings
builder = LEDFacadeBuilder()
duke = builder.create_duke_energy_facade()

# Set Panthers mode (blue)
LEDAnimator.apply_preset_panthers(duke)

# Set holiday modes
LEDAnimator.apply_preset_christmas(duke)
LEDAnimator.apply_preset_halloween(duke)
```

## Materials

The system uses PBR materials with presets:

| Material | Base Color | Roughness | Notes |
|----------|------------|-----------|-------|
| Glass | Dark blue-gray | 0.1 | IOR 1.45 |
| Granite | Warm gray | 0.7 | Bank of America |
| Concrete | Light gray | 0.8 | Parking structures |
| Steel | Silver | 0.3 | Metallic 0.8 |
| Brick | Terra cotta | 0.9 | Historic buildings |

### LED Materials

Buildings with LED facades get special materials with:
- Base PBR material
- Emission shader mixed via Fresnel
- Configurable emission color and strength

## Coordinate System

The system converts GPS coordinates to local Blender units:

- **Origin**: 35.227°N, 80.843°W (center of Uptown)
- **Units**: Meters
- **Conversion**: 1° lat ≈ 111km, 1° lon ≈ 91km (at Charlotte latitude)

```python
from lib.charlotte_digital_twin.buildings.geojson_importer import CoordinateConverter

converter = CoordinateConverter()
local_x, local_y = converter.to_local(-80.8467, 35.2267)  # Duke Energy Center
```

## Generation Options

### CharlotteBuildingGenerator

```python
from lib.charlotte_digital_twin.buildings.geojson_importer import CharlotteBuildingGenerator

generator = CharlotteBuildingGenerator()
generator.load_geojson("charlotte_uptown_buildings.geojson")

# Filter by height
buildings = generator.generate_all_buildings(min_height=50.0)

# Filter by floors
tall = generator.generate_all_buildings(min_floors=20)

# Only named buildings
named = generator.generate_all_buildings(named_only=True)

# Get statistics
stats = generator.get_building_stats()
```

### IntegratedCharlotteGenerator

For full integration with LED facades and materials:

```python
from lib.charlotte_digital_twin.buildings.geojson_importer import IntegratedCharlotteGenerator

generator = IntegratedCharlotteGenerator()
generator.load_geojson("charlotte_uptown_buildings.geojson")

objects = generator.generate_scene(
    min_height=0.0,
    min_floors=0,
    include_led=True,
    apply_materials=True,
)
```

## Example: Night Scene

```python
import bpy
import sys
sys.path.append('/path/to/blender_gsd')

from lib.charlotte_digital_twin.buildings.geojson_importer import generate_charlotte_scene
from lib.charlotte_digital_twin.buildings.led_facade import LEDColor, LEDFacadeBuilder

# Generate buildings
buildings = generate_charlotte_scene(with_leds=True)

# Set Panthers mode on all LED buildings
builder = LEDFacadeBuilder()
all_led = builder.create_all_charlotte_led_facades()
builder.set_panthers_mode_all()

# Configure render for night
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 128
bpy.context.scene.view_settings.view_transform = 'Filmic'
```

## Data Quality Notes

### Height Data Coverage

- **With height data**: 259 buildings (24%)
- **With floor data**: 113 buildings (11%)
- **Estimated**: Remaining buildings use floor-based estimation (4m/floor) or default (15m)

### Known Issues

1. **Bank of America** - OSM has 88 floors, CTBUH says 60 (use CTBUH)
2. **550 South Tryon** - OSM height incorrect, corrected to 240m
3. **Duke Energy Plaza** - OSM height 74m, corrected to 192m

## Files Reference

```
lib/charlotte_digital_twin/
├── buildings/
│   ├── __init__.py              # Module exports
│   ├── geojson_importer.py      # GeoJSON to Blender generator
│   ├── led_facade.py            # LED facade system
│   ├── charlotte_skyline.py     # Building specifications
│   ├── building_materials.py    # PBR materials
│   └── building_extraction.py   # OSM extraction
├── data/
│   ├── building_data.py         # Data fetching/caching
│   ├── charlotte_uptown_buildings.geojson
│   ├── charlotte_buildings_named.geojson
│   ├── charlotte_buildings.geojson
│   └── charlotte_osm_buildings.json
```

## Performance

| Scene | Buildings | Generation Time |
|-------|-----------|-----------------|
| LED only | ~10 | <1 sec |
| Tall (20+ floors) | ~16 | ~2 sec |
| Uptown all | 1,069 | ~30 sec |
| Full Charlotte | 387,329 | ~10 min |

## See Also

- [Charlotte Building Data Sources](../../.planning/research/CHARLOTTE_BUILDING_DATA_SOURCES.md)
- [LED Facade Research](../../.planning/research/CHARLOTTE_LED_IMAGE_URLS.md)
- [Duke Energy Center LED Specs](../../.planning/research/DUKE_ENERGY_CENTER_LED_FACADE.md)
