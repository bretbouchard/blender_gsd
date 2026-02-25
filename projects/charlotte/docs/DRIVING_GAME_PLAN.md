# Charlotte Digital Twin - Driving Game Implementation Plan

## Overview

Transform the Charlotte digital twin into a realistic driving game environment using
geometry nodes, the blender_gsd lib tools (NodeKit, Pipeline, scene_ops), and existing
Charlotte-specific geometry modules.

## Available Tools

### From blender_gsd/lib
| Tool | Location | Use |
|------|----------|-----|
| **NodeKit** | `lib/nodekit.py` | Build geometry/shader node trees programmatically |
| **Pipeline** | `lib/pipeline.py` | Linear stage execution (Normalize → Primary → Secondary → Detail → Output) |
| **scene_ops** | `lib/scene_ops.py` | Collection management, object selection |
| **exports** | `lib/exports.py` | STL/GLTF export for game engines |

### From lib/charlotte_digital_twin/geometry
| Module | Use |
|--------|-----|
| `road_geometry.py` | RoadSegment, RoadGeometryGenerator, curve/mesh creation |
| `building_geometry.py` | Building mesh generation with LOD |
| `poi_geometry.py` | Points of interest markers |

### From lib/urban
| Module | Use |
|--------|-----|
| `road_geometry.py` | RoadNetwork → RoadGeometry conversion, LaneConfig |

### Charlotte Project Scripts
| Script | Purpose |
|--------|---------|
| `lib/geo_nodes_road.py` | Geometry nodes road builder |
| `lib/road_markings_geo_nodes.py` | Lane markings, manholes, street lights |
| `lib/crosswalk_generator.py` | Crosswalk mesh generation |

---

## Phase 1: Road Surface & Collision

**Goal:** Convert road curves to actual driveable surfaces with physics collision.

### 1.1 Road Surface Mesh Generator (Geometry Nodes)

**Node Group:** `RoadSurface_from_Curve`

```
Inputs:
  - Curve (Curve)
  - Width (Float, default from road_width attribute)
  - Thickness (Float, 0.15m asphalt layer)
  - Crown_Angle (Float, 2% for drainage)
  - Has_Curb (Boolean)
  - Curb_Height (Float, 0.15m)
  - Curb_Width (Float, 0.20m)

Outputs:
  - Mesh (road surface + curbs)
  - Road_Material_ID (attribute for shading)
  - Collision_Simple (simplified for physics)
```

**Pipeline Stages:**
1. **Normalize** - Read curve attributes (width, lanes, road_class)
2. **Primary** - Convert curve to mesh with width, add thickness
3. **Secondary** - Add crown/camber (2% slope from center)
4. **Detail** - Add curbs, store material zones as attributes
5. **Output** - Store UVs, material IDs, create collision proxy

**Using NodeKit:**
```python
nk = NodeKit(tree).clear()
gi = nk.group_input(x=0)
# ... build node graph
go = nk.group_output(x=1200)
nk.link(geo_socket, go.inputs["Geometry"])
```

### 1.2 Collision Mesh Generator

**Node Group:** `RoadCollision_from_Surface`

```
Inputs:
  - Road_Surface (Mesh)
  - Simplify_Level (Int, 0-2)

Outputs:
  - Collision_Mesh (simplified convex or trimesh)
```

- LOD0: Full trimesh for near-player roads
- LOD1: Simplified (every 4th vertex)
- LOD2: Convex hull per road segment

### 1.3 Road Friction Zones

Store as vertex attribute `friction_multiplier`:
- Normal asphalt: 1.0
- Painted markings: 0.85 (slicker)
- Metal (manholes): 0.7
- Concrete: 1.1 (more grip)
- Wet zones: 0.6

**Script:** `scripts/10_generate_road_surface.py`

---

## Phase 2: Traffic Infrastructure

### 2.1 Traffic Signal System

**Node Group:** `TrafficSignal_Generator`

```
Inputs:
  - Position (Vector)
  - Rotation (Float, facing direction)
  - Signal_Type (Enum: 3_LIGHT, 5_LIGHT, PEDESTRIAN)
  - Pole_Height (Float, 5.0m standard)
  - Mast_Length (Float, 3.0m)

Outputs:
  - Mesh (signal pole + housing)
  - Light_Positions (attribute for emissive materials)
```

**Signal Types:**
- `3_LIGHT`: Standard R/Y/G vertical
- `5_LIGHT`: With left/right arrows
- `PEDESTRIAN`: Walk/Don't Walk

**Placement Rules (Python):**
```python
def place_traffic_signals(intersections: List[Intersection]) -> List[SignalPlacement]:
    # At each intersection:
    # - Primary roads: full signals on all approaches
    # - Secondary + Primary: signals on primary only
    # - Residential: stop signs or yield
    # - Roundabouts: yield signs only
```

### 2.2 Traffic Sign Generator

**Node Group:** `TrafficSign_Generator`

```
Inputs:
  - Position (Vector)
  - Rotation (Float)
  - Sign_Type (Enum)
  - Sign_Height (Float, 2.1m to bottom)

Outputs:
  - Mesh (post + sign face)
  - Sign_Face_Normal (for text/decals)
```

**Sign Types:**
| Type | Placement |
|------|-----------|
| STOP | 4-way stops, T-intersections |
| YIELD | Roundabouts, merge lanes |
| SPEED_LIMIT | Every 500m, after intersections |
| NO_ENTRY | One-way streets |
| TURN_RESTRICTION | No left/right turn |

### 2.3 Turn Lane Arrows

**Node Group:** `TurnArrow_Distributor`

```
Inputs:
  - Road_Curve (Curve)
  - Arrow_Type (Enum: LEFT, RIGHT, STRAIGHT, COMBO)
  - Distance_From_Stop (Float, 15m)
  - Arrow_Size (Float, 1.5m)

Outputs:
  - Arrow_Meshes (instances on curve)
```

**Script:** `scripts/11_generate_traffic_infrastructure.py`

---

## Phase 3: Terrain & Environment

### 3.1 Terrain from Elevation

**Using existing ElevationManager:**

```python
from lib.charlotte_digital_twin.elevation import ElevationManager

# Load elevation data
elevation = ElevationManager()
elevation.load_from_osm(osm_data)

# Generate terrain mesh
terrain = generate_terrain_mesh(
    bounds=(min_lat, min_lon, max_lat, max_lon),
    resolution=10.0,  # 10m grid
    elevation_manager=elevation
)
```

**Node Group:** `Terrain_with_Drainage`

```
Inputs:
  - Bounds (Box)
  - Resolution (Float)
  - Elevation_Data (attribute or texture)

Outputs:
  - Mesh (terrain surface)
  - Water_Flow_Attribute (for puddle placement)
```

### 3.2 Sidewalk Generator

**Node Group:** `Sidewalk_from_Footway`

```
Inputs:
  - Footway_Curve (Curve)
  - Width (Float, 1.5m standard)
  - Height (Float, 0.15m above road)
  - Material (Enum: CONCRETE, BRICK, ASPHALT)

Outputs:
  - Mesh (sidewalk surface)
  - Curb_Mesh (connection to road)
```

**Source:** Use OSM footway ways (5,409 in Charlotte data)

### 3.3 Vegetation Distributor

**Node Group:** `Vegetation_Scatter`

```
Inputs:
  - Terrain (Mesh)
  - Building_Footprints (Mesh collection)
  - Road_Buffers (Mesh)
  - Tree_Density (Float)
  - Grass_Coverage (Float, 0-1)

Outputs:
  - Tree_Instances
  - Grass_Patches
  - Bush_Layer
```

**Tree Placement Rules:**
- Avoid building footprints
- 2m minimum from road edge
- Cluster in parks, sparse along streets
- Use local species (oak, maple, pine)

### 3.4 Street Furniture

**Node Group:** `StreetFurniture_Distributor`

```
Inputs:
  - Sidewalk_Mesh
  - Furniture_Type (Enum)
  - Spacing (Float)

Outputs:
  - Bench_Instances
  - Trash_Can_Instances
  - Mailbox_Instances
  - Fire_Hydrant_Instances
```

**Script:** `scripts/12_generate_environment.py`

---

## Phase 4: Visual Realism (Materials)

### 4.1 PBR Material Library

**Create materials using NodeKit for ShaderNodeTree:**

| Material | Properties |
|----------|------------|
| **asphalt_fresh** | Dark gray, uniform, slight roughness |
| **asphalt_worn** | Lighter, cracked pattern, patches |
| **concrete_sidewalk** | Light gray, expansion joints |
| **road_paint_white** | High emissive, reflective |
| **road_paint_yellow** | Yellow emissive, reflective |
| **metal_manhole** | Reflective, circular pattern |
| **grass** | Green, slight bump |
| **brick_sidewalk** | Red/brown, brick pattern |

### 4.2 Road Wear System

**Node Group:** `RoadWear_Mixer`

```
Inputs:
  - Base_Material (Material)
  - Wear_Amount (Float, 0-1)
  - Patch_Mask (attribute)

Outputs:
  - Mixed_Material
```

**Wear Types:**
- Crack patterns (procedural noise)
- Oil stains (at intersections, parking)
- Patch repairs (rectangular overlays)
- Rutting (depression in wheel paths)

### 4.3 Weather Effects

**Materials with weather variants:**
- Dry (base state)
- Wet (increased specularity, reflections)
- Snow (white overlay, reduced friction)

**Script:** `scripts/13_setup_materials.py`

---

## Phase 5: Game Integration

### 5.1 Collision Setup

```python
def setup_collision(road_objects: List[bpy.types.Object]):
    """Configure collision for game engine export."""
    for obj in road_objects:
        # Create collision modifier
        obj.modifiers.new(name="Collision", type='COLLISION')

        # Export settings for Unity/Unreal
        obj["collision_type"] = "TRIMESH"
        obj["collision_complexity"] = "USE_SIMPLE_COMPLEX"
```

### 5.2 LOD System

**Using existing LOD system from `lib/lod_system.py`:**

| LOD | Distance | Road Detail |
|-----|----------|-------------|
| LOD0 | 0-100m | Full surface, markings, cracks |
| LOD1 | 100-300m | Surface + major markings |
| LOD2 | 300m-1km | Surface only, baked texture |
| LOD3 | 1km+ | Flat plane, single color |

### 5.3 Export Profiles

```python
from lib.exports import export_mesh

# Unity export
export_mesh(
    root_objects=roads,
    mesh_out_cfg={"file": "exports/roads_unity.fbx", "profile": "fbx_unity"},
    root=project_root
)

# Unreal export
export_mesh(
    root_objects=roads,
    mesh_out_cfg={"file": "exports/roads_unreal.fbx", "profile": "fbx_unreal"},
    root=project_root
)
```

### 5.4 NPC Path Generation

**From road curves, generate lane centerlines:**

```python
def generate_npc_paths(road_curves: List[bpy.types.Object]) -> List[NPCPath]:
    """Generate driveable paths for AI traffic."""
    paths = []
    for curve in road_curves:
        lanes = curve.get('lanes', 2)
        width = curve.get('road_width', 10.0)
        lane_width = width / lanes

        for lane_idx in range(lanes):
            # Offset from center
            offset = -width/2 + lane_width * (lane_idx + 0.5)

            # Generate path along curve with offset
            path = create_offset_path(curve, offset)
            path.direction = 'forward' if lane_idx < lanes/2 else 'backward'
            paths.append(path)

    return paths
```

**Script:** `scripts/14_game_integration.py`

---

## File Structure

```
projects/charlotte/
├── scripts/
│   ├── lib/
│   │   ├── geo_nodes_road_surface.py     # NEW: Road surface GN
│   │   ├── geo_nodes_traffic.py          # NEW: Traffic signals/signs GN
│   │   ├── geo_nodes_environment.py      # NEW: Terrain/vegetation GN
│   │   ├── materials_pbr.py              # NEW: PBR material library
│   │   ├── game_export.py                # NEW: Game engine export
│   │   └── [existing files...]
│   │
│   ├── 10_generate_road_surface.py       # Phase 1
│   ├── 11_generate_traffic_infrastructure.py  # Phase 2
│   ├── 12_generate_environment.py        # Phase 3
│   ├── 13_setup_materials.py             # Phase 4
│   └── 14_game_integration.py            # Phase 5
│
├── assets/
│   ├── materials/
│   │   ├── asphalt_fresh.blend
│   │   ├── asphalt_worn.blend
│   │   └── ...
│   ├── models/
│   │   ├── traffic_signals.blend
│   │   ├── street_furniture.blend
│   │   └── vegetation.blend
│   └── textures/
│       ├── asphalt/
│       ├── concrete/
│       └── markings/
│
└── exports/
    ├── unity/
    └── unreal/
```

---

## Implementation Order

### Week 1: Foundation
1. [x] Road curves with markings (existing)
2. [x] **Road surface mesh with collision** ✅ Phase 1 Complete
3. [x] Curb geometry
4. [x] Friction attribute system

### Week 2: Traffic
5. [x] Traffic signal generator ✅ Phase 2 Complete
6. [x] Sign generator (STOP, YIELD, SPEED)
7. [x] Turn lane arrows
8. [x] Stop line placement

### Week 3: Environment
9. [x] Terrain mesh from elevation ✅ Phase 3 Complete
10. [x] Sidewalk generator
11. [x] Vegetation scatter
12. [x] Street furniture

### Week 4: Polish
13. [x] PBR material library ✅ Phase 4 Complete
14. [x] Road wear/debris system
15. [x] Weather variants
16. [x] Game engine export ✅ Phase 5 Complete

---

## Implementation Status

| Phase | Script | Status |
|-------|--------|--------|
| Phase 1: Road Surface | `10_generate_road_surface.py` | ✅ Complete |
| Phase 2: Traffic Infrastructure | `11_generate_traffic_infrastructure.py` | ✅ Complete |
| Phase 3: Environment & Terrain | `12_generate_environment.py` | ✅ Complete |
| Phase 4: PBR Materials | `13_setup_materials.py` | ✅ Complete |
| Phase 5: Game Integration | `14_game_integration.py` | ✅ Complete |
| Phase 6: Race Loop | `15_race_loop.py` | ✅ Complete |

---

## Phase 6: Race Loop & Vehicle System

### 6.1 Realistic Vehicle Dimensions

All vehicles use real-world dimensions for accurate scale:

| Vehicle Type | Length | Width | Height | Eye Height | Use Case |
|-------------|--------|-------|--------|------------|----------|
| **Sports Car** | 4.52m | 1.85m | 1.30m | 1.08m | Default player vehicle |
| **Mid-size Sedan** | 4.96m | 1.87m | 1.47m | 1.20m | Standard driving |
| **SUV** | 5.05m | 2.00m | 1.78m | 1.45m | Higher view |
| **Muscle Car** | 4.79m | 1.92m | 1.38m | 1.12m | American muscle feel |
| **Supercar** | 4.58m | 1.94m | 1.20m | 1.02m | Low, fast feel |

**Driver Camera Heights:**
- Sports car: 1.08m (low, sporty)
- SUV: 1.45m (commanding view)
- Sedan: 1.15-1.20m (standard)

### 6.2 Charlotte Race Loop

**Route (3.5 km):**
```
Start: Church St & MLK Jr Blvd
  ↓ S Church St south
  ↓ Right onto W Morehead St
  ↓ Ramp onto I-277 East
  ↓ Exit at College St
  ↓ College St north to E 5th St
  ↓ Right onto E 5th St
  ↓ Right onto N Caldwell St
  ↓ Right onto E Trade St
  ↓ Left onto S Church St
Finish: Back at Church & MLK
```

**Features:**
- 15 waypoints with turn instructions
- 2 checkpoint gates (start/finish)
- Path arrow markers at each segment
- Speed limits per segment (35-55 mph)
- Highway section on I-277

**Script:** `scripts/15_race_loop.py`

### 6.3 Path Highlight System

Visual guidance for the correct route:

| Marker Type | Use | Material |
|-------------|-----|----------|
| **Arrow** | Direction indicators | Yellow emissive |
| **Chevron** | Sharp turns | Orange emissive |
| **Checkpoint** | Start/Finish gates | Green emissive |
| **Glow line** | Continuous path | Cyan emissive |

---

## Launch Control Integration

**Launch Control** is a Blender add-on for fast camera navigation and scene management. For this project:

### Useful for:
- Quick camera positioning while testing the loop
- Scene organization and object selection
- Rapid iteration on camera angles

### Not needed for:
- Game runtime (it's Blender-only)
- Export to Unity/Unreal
- In-game camera systems

### Recommendation:
Launch Control is helpful during **development** in Blender but won't affect the game export. The driver camera system we created (`create_driver_camera_rig`) handles the in-game camera positioning.

---

## Elevation Accuracy

The elevation system now uses **real elevation data** from the Open-Elevation API (SRTM 30m resolution).

### Real Elevation Data:
- **Source:** Open-Elevation API (SRTM 30m satellite data)
- **Resolution:** ~30m (1 arc-second)
- **Coverage:** 60+ elevation points across Charlotte Uptown
- **Accuracy:** ±10m vertical, ±30m horizontal

### Charlotte Uptown Elevation Range:
| Location | Elevation | Notes |
|----------|-----------|-------|
| Trade & Tryon (center) | 275m | Highest point - "The Hill" |
| Church & MLK | 264m | Start/Finish line |
| I-277 @ College | 195m | Lowest point - highway section |
| **Total variation** | **80m** | Significant elevation change! |

### Race Loop Elevation Profile:
| Segment | Start Elev | End Elev | Change | Grade |
|---------|------------|----------|--------|-------|
| Start → Morehead | 264m | 218m | -46m | -6.2% (downhill) |
| Morehead → I-277 | 218m | 227m | +9m | +1.2% (slight up) |
| I-277 → College | 227m | 195m | -32m | -4.3% (downhill) |
| College → E 5th | 195m | 199m | +4m | +0.5% (slight up) |
| E 5th → Caldwell | 199m | 209m | +10m | +1.3% (uphill) |
| Caldwell → Trade | 209m | 215m | +6m | +0.8% (slight up) |
| Trade → Church | 215m | 230m | +15m | +2.0% (uphill) |
| Church → Finish | 230m | 264m | +34m | +4.5% (steep uphill!) |

### Driving Feel:
For realistic driving feel:
1. **Trade Street is "The Hill"** - you'll feel the climb
2. **I-277 is in a valley** - significant downhill then flat
3. **Church & MLK to Morehead** - steep descent (6.2% grade)
4. **Return climb** - noticeable 4.5% grade back to start

### Data Sources for Higher Resolution:
If 30m SRTM isn't accurate enough:
1. **USGS 3DEP** - 1m resolution LiDAR for Charlotte area
2. **NC OneMap** - State GIS portal with LiDAR data
3. **OpenTopography** - Custom DEM generation from LiDAR point clouds
4. **Google Elevation API** - High accuracy (requires API key)

### Scripts:
- `lib/elevation_real.py` - Real elevation manager with 60+ points
- `scripts/17_elevation_viz.py` - Visualization of elevation profile

---

## Dependencies on Existing Code

| New Feature | Uses | From |
|-------------|------|------|
| Road Surface | NodeKit, Pipeline | lib/ |
| Traffic Signs | RoadGeometryGenerator | lib/charlotte_digital_twin/geometry/ |
| Terrain | ElevationManager | lib/elevation.py |
| Materials | RoadType → material mapping | lib/charlotte_digital_twin/geometry/road_geometry.py |
| Export | export_mesh | lib/exports.py |
| Collections | ensure_collection | lib/scene_ops.py |
