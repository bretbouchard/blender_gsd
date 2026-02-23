# City Chase System - Production Ready

A complete city generation and car chase system for Blender 5.x.

**Total: 9,200+ lines of code across 13 modules**

## Quick Start

### Run in Blender

```bash
# Quick test scene
blender --python projects/city_chase/demo_city_chase.py -- --preset test

# Charlotte NC chase
blender --python projects/city_chase/demo_city_chase.py -- --preset charlotte

# Hollywood action
blender --python projects/city_chase/demo_city_chase.py -- --preset hollywood
```

### Install as Add-on

```bash
# In Blender:
# 1. Edit -> Preferences -> Add-ons -> Install
# 2. Select lib/animation/city/blender_addon.py
# 3. Enable "City Chase System"
# 4. Access via 3D Viewport -> Sidebar (N) -> City Chase
```

### Python API

```python
from lib.animation.city import create_city, start_traffic_animation, render_chase

# Create scene
builder = create_city("hollywood_chase")

# Start traffic animation
animator = start_traffic_animation()

# Render
render_chase("//output/my_chase_")
```

---

## Complete Module Reference

### Core Systems (7 modules)

| Module | Lines | Purpose |
|--------|-------|---------|
| `geo_data.py` | 892 | Geo/OSM data import, coordinate transforms |
| `road_network.py` | 737 | Road generation, lanes, intersections |
| `buildings.py` | 708 | Procedural building generator |
| `street_elements.py` | 502 | Lights, signs, banners, utilities |
| `traffic_ai.py` | 585 | Traffic AI with chase avoidance |
| `chase_coordinator.py` | 626 | Chase orchestration, crash points |
| `chase_cameras.py` | 647 | Follow, aerial, in-car, static cameras |

### Runtime Systems (4 modules)

| Module | Lines | Purpose |
|--------|-------|---------|
| `city_builder.py` | 550 | Unified orchestrator with fluent API |
| `traffic_animator.py` | 450 | Real-time vehicle animation |
| `osm_importer.py` | 650 | Real OSM data import for Charlotte NC |
| `render_pipeline.py` | 450 | Render setup and execution |

### Integration (2 modules)

| Module | Lines | Purpose |
|--------|-------|---------|
| `blender_addon.py` | 850 | UI panels, operators, frame handlers |
| `__init__.py` | 320 | Public API exports |

---

## What's Now Production-Ready

### Full Blender Integration
- **UI Panel**: Sidebar -> City Chase tab
- **Menu**: Shift+A -> City Chase
- **Operators**: Create City, Start/Stop Traffic, Camera Switching
- **Frame Handlers**: Automatic traffic animation, camera switching

### Traffic Animation
- Vehicles follow roads with physics-based movement
- Lane following with steering behavior
- Chase avoidance (traffic slows/pulls over for hero)
- Collision detection between vehicles

### Real OSM Import
- Import any location by name ("Charlotte, NC")
- Charlotte presets: uptown, downtown, South End, NoDa, etc.
- Building heights from OSM tags
- Road network from OpenStreetMap

### Camera Auto-Switching
- Configurable switch interval
- Cycles through follow/aerial/in-car/static
- Frame-change handler for automatic switching
- Manual next camera operator

### Render Pipeline
- Presets: preview, standard, high_quality, 4k, production
- Compositor setup (color correction, glare, vignette)
- Multi-camera batch rendering
- Quick playblast mode

---

## Full Usage Examples

### 1. One-Line City Creation

```python
from lib.animation.city import create_city
builder = create_city("charlotte_uptown")
```

### 2. Fluent Builder API

```python
from lib.animation.city import CityBuilder

builder = (CityBuilder("My_Chase")
    .set_location("charlotte_uptown")
    .add_roads(grid_size=6, lanes=4)
    .add_downtown(building_count=50, height_range=(50, 300))
    .add_traffic(count=40)
    .add_hero_car(style="sports", color="red")
    .add_pursuit(count=3)
    .setup_chase(duration=30.0)
    .setup_cameras(types=["follow", "aerial"])
    .build()
)
```

### 3. Real Charlotte Data

```python
from lib.animation.city import OSMCityImporter, import_charlotte

# Method 1: Preset
city = import_charlotte("uptown")

# Method 2: Custom location
importer = OSMCityImporter()
city = importer.import_city("Trade & Tryon, Charlotte NC", radius_km=1.0)

# Create Blender scene
importer.create_blender_scene(city)
```

### 4. Start Traffic Animation

```python
from lib.animation.city import start_traffic_animation, stop_traffic_animation

# Start
animator = start_traffic_animation()

# Vehicles now move automatically each frame

# Stop
stop_traffic_animation()
```

### 5. Render Chase

```python
from lib.animation.city import ChaseRenderPipeline, render_chase

# Quick render
render_chase("//output/chase_")

# Full control
pipeline = ChaseRenderPipeline.from_preset("production")
pipeline.setup_scene()
pipeline.setup_compositor()
pipeline.render_animation("//output/final_chase_")
```

---

## Charlotte NC Presets

| Preset | Center | Radius | Description |
|--------|--------|--------|-------------|
| `uptown` | 35.227, -80.843 | 1.5km | Downtown skyscrapers |
| `downtown_full` | 35.227, -80.843 | 3.0km | Full downtown |
| `south_end` | 35.210, -80.855 | 1.0km | South End district |
| `noDa` | 35.245, -80.815 | 0.8km | Arts district |
| `plaza_midwood` | 35.235, -80.800 | 0.8km | Plaza Midwood |
| `myers_park` | 35.200, -80.830 | 1.5km | Residential |
| `airport` | 35.215, -80.945 | 2.0km | Airport area |
| `university` | 35.310, -80.730 | 2.0km | UNC Charlotte |

---

## File Structure

```
lib/animation/city/
├── __init__.py          # Public API (320 lines)
├── geo_data.py          # Geo/OSM import (892 lines)
├── road_network.py      # Roads (737 lines)
├── buildings.py         # Buildings (708 lines)
├── street_elements.py   # Street furniture (502 lines)
├── traffic_ai.py        # Traffic AI (585 lines)
├── chase_coordinator.py # Chase orchestration (626 lines)
├── chase_cameras.py     # Camera systems (647 lines)
├── city_builder.py      # Orchestrator (550 lines)
├── traffic_animator.py  # Runtime animation (450 lines)
├── osm_importer.py      # OSM import (650 lines)
├── render_pipeline.py   # Render system (450 lines)
└── blender_addon.py     # UI/Operators (850 lines)

projects/city_chase/
├── demo_city_chase.py   # Executable demo (600 lines)
└── README.md            # This file
```

---

## Integration with Vehicle System

The city system integrates with the procedural vehicle system:

```python
from lib.animation.city import CityBuilder

builder = CityBuilder()
builder.add_hero_car(style="muscle", color="red")
builder.build()
# Uses ProceduralCarFactory if available for realistic cars
```
