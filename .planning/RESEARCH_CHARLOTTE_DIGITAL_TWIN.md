# Charlotte NC Digital Twin - Research Summary & Implementation Plan

## Project Overview

**Goal:** Create a digital twin of Charlotte, NC road network including highways, bridges, overpasses, traffic flow, 3D buildings, and POIs (gas stations, stadiums, etc.).

**Key Features Required:**
- Procedural road/bridge/highway generation
- Automatic material application
- Vehicle pathfinding/traffic simulation
- Real-world elevation data
- 3D building models (skyscrapers, stadiums)
- Gas stations and other POIs
- Traffic flow data integration

---

## Part 1: Blender Road/Bridge Tutorials & Tools

### Recommended: "The Roads Must Roll" Addon

| Feature | Details |
|---------|---------|
| **Type** | Blender addon for procedural roads |
| **Version Support** | Blender 4.1, 4.2, 4.3, 4.4+ |
| **Renderer** | Cycles |
| **Features** | Curve-based roads, bridges, highways, intersections |
| **Includes** | 160+ customizable settings, 12 preset intersections |
| **Vehicle System** | Built-in car animation system |
| **Assets** | Traffic lights, road markings, signs |

**Links:**
- [CGZY Tutorial](https://www.cgzy.net/52325.html)
- [GFXCamp](https://www.gfxcamp.com/the-roads-must-roll/)
- [Bilibili Demo](https://m.bilibili.com/video/BV1xk5Pz3EEb)

### Alternative: Geometry Nodes Procedural Bridges

- Create custom procedural bridge generators using Blender's Geometry Nodes
- Suitable for custom bridge types specific to Charlotte

---

## Part 2: Data Sources for Charlotte NC

### 2.1 Road Network Data

| Source | Data Type | Format | Cost |
|--------|-----------|--------|------|
| **Geofabrik** | OSM road extracts | Shapefile, OSM XML | Free |
| **OpenStreetMap** | Complete road network | Multiple | Free |
| **NCDOT** | Official road data | GIS | Free (request) |

**Download:** `download.geofabrik.de/north-america/us/north-carolina.html`

### 2.2 Elevation/Terrain Data

| Source | Resolution | Coverage | Cost |
|--------|------------|----------|------|
| **OpenTopography** | LiDAR point clouds | US including NC | Free |
| **USGS 3DEP** | 1m DEM | Nationwide | Free |
| **USGS Earth Explorer** | SRTM DEM | Global | Free |
| **NCALM** | High-res LiDAR | Select areas | Free |

**Charlotte Elevation:** ~229m (751 ft) average
**Key Elevations:**
- Charlotte Douglas Airport: ~228m
- Downtown/Uptown: ~240-250m

**Download:** `opentopography.org`, `earthexplorer.usgs.gov`

### 2.3 3D Building Data

| Source | Data Type | Coverage |
|--------|-----------|----------|
| **Cesium OSM Buildings** | 3D tileset | 350M+ buildings globally |
| **OpenStreetMap** | Building footprints + heights | Charlotte included |
| **OSM Buildings** | 3D extrusion | Global |

**Major Charlotte Buildings to Include:**
- Bank of America Corporate Center (312m / 60 floors)
- Duke Energy Center (240m / 48 floors)
- Wells Fargo Capital Center (176m)
- Truist Center (150m)
- The Vue (207m residential)
- Bank of America Stadium
- Spectrum Center
- Charlotte Convention Center

### 2.4 Traffic Flow Data

| Source | Data Type | Access |
|--------|-----------|--------|
| **RITIS API** | Real-time & historical traffic | Requires account |
| **NCDOT DriveNC** | Traffic conditions | Free |
| **iTRE Data Lab** | NC-specific analysis | Free tools |
| **TomTom Traffic API** | Commercial traffic data | Paid API |
| **FHWA AADT** | Annual traffic counts | Free |

**Key Charlotte Highways:**
- I-77 (North-South) - ~150,000 AADT
- I-85 (Northeast-Southwest) - ~140,000 AADT
- I-277 (Inner Loop)
- I-485 (Outer Loop/Beltway)
- US-74 (Independence Boulevard)

### 2.5 POI Data (Gas Stations, etc.)

| Source | Data Type | Access |
|--------|-----------|--------|
| **OpenStreetMap** | amenity=fuel tags | Free |
| **Overpass API** | Query-based extraction | Free |
| **Geofabrik POI layers** | Pre-extracted POIs | Free |

**Charlotte POI Categories to Extract:**
- Gas stations (`amenity=fuel`)
- Parking (`amenity=parking`)
- Hospitals (`amenity=hospital`)
- Schools (`amenity=school`)
- Stadiums (`leisure=stadium`)
- Banks (`amenity=bank`)
- Restaurants (`amenity=restaurant`)

---

## Part 3: Charlotte Highway Infrastructure

### Major Interstates

| Highway | Description | Length in Area |
|---------|-------------|----------------|
| **I-77** | North-South corridor | ~30 miles |
| **I-85** | Northeast-Southwest | ~25 miles |
| **I-277** | Inner loop (Brookshire/John Belk) | ~5 miles |
| **I-485** | Outer beltway | ~67 miles |
| **I-277** | Brookshire Freeway / John Belk Freeway | - |

### Major Bridges/Overpasses

**I-77 Bridges:**
- I-77 over I-85 (interchange)
- I-77 over Sugar Creek
- Multiple overpasses along corridor

**I-85 Bridges:**
- I-85 over I-77 (interchange)
- Various creek crossings

**Downtown Elevated Sections:**
- John Belk Freeway (I-277) elevated section
- Brookshire Freeway (I-277) elevated section

**Data Source:** NCDOT Bridge Inventory, FHWA National Bridge Inventory

---

## Part 4: Implementation Plan

### Phase 1: Data Acquisition (Week 1-2)

```
Tasks:
1. Download Charlotte OSM data from Geofabrik
2. Download DEM/LiDAR from OpenTopography
3. Extract road network from OSM
4. Extract building footprints and heights
5. Query gas stations via Overpass API
6. Request RITIS API access
```

**Commands to acquire data:**
```bash
# OSM data for North Carolina
wget https://download.geofabrik.de/north-america/us/north-carolina-latest.osm.pbf

# Extract Charlotte bounding box
# Charlotte: 35.0 to 35.4 N, -81.1 to -80.6 W
osmium extract -b -80.9,35.0,-80.5,35.4 north-carolina-latest.osm.pbf -o charlotte.osm.pbf

# Query gas stations via Overpass API
# (using Overpass Turbo or API)
[out:json][bbox:35.0,-81.1,35.4,-80.6];
node["amenity"="fuel"];
out;
```

### Phase 2: Data Processing Pipeline (Week 2-4)

```python
# Proposed pipeline structure
lib/charlotte_digital_twin/
├── __init__.py
├── data_acquisition/
│   ├── osm_downloader.py      # OSM data download
│   ├── elevation_fetcher.py   # DEM/LiDAR download
│   ├── traffic_importer.py    # Traffic data import
│   └── poi_extractor.py       # POI extraction
├── data_processing/
│   ├── road_processor.py      # Road network to JSON
│   ├── building_processor.py  # Buildings to geometry
│   ├── elevation_processor.py # Terrain generation
│   └── traffic_processor.py   # Traffic flow data
├── geometry_generation/
│   ├── road_geometry.py       # Road mesh generation
│   ├── bridge_geometry.py     # Bridge/overpass generation
│   ├── building_geometry.py   # Building generation
│   └── terrain_geometry.py    # Terrain mesh
├── material_system/
│   ├── road_materials.py      # Using ground_textures module
│   ├── building_materials.py  # Building materials
│   └── bridge_materials.py    # Bridge materials
├── traffic_simulation/
│   ├── vehicle_paths.py       # Path generation
│   ├── traffic_flow.py        # Traffic simulation
│   └── intersection_logic.py  # Traffic lights/signals
└── scene_builder/
    ├── scene_assembler.py     # Put it all together
    └── export_pipeline.py     # Export options
```

### Phase 3: Road Network Generation (Week 4-6)

1. **Parse OSM road data** → JSON format for our existing urban system
2. **Generate road geometry** using L-system or direct conversion
3. **Apply ground textures** using our new texture system
4. **Create bridges/overpasses** from OSM bridge tags + elevation data

**OSM Highway Tags to Process:**
- `highway=motorway` → Interstate
- `highway=trunk` → Major highway
- `highway=primary` → Major road
- `highway=secondary` → Secondary road
- `bridge=yes` → Bridge geometry
- `tunnel=yes` → Tunnel geometry
- `layer=*` → Elevation layer

### Phase 4: Building Generation (Week 6-8)

1. **Extract OSM building data**
2. **Get heights from OSM or estimate**
3. **Generate procedural building geometry**
4. **Apply appropriate materials**

**Building Height Estimation:**
```python
# If height not in OSM, estimate from building:levels
height = levels * 3.5  # meters per floor average

# Or from building type
height_estimates = {
    "skyscraper": 150,
    "apartments": 30,
    "commercial": 20,
    "house": 8,
    "stadium": 25,
}
```

### Phase 5: Traffic Simulation (Week 8-10)

1. **Generate vehicle paths** from road network
2. **Import traffic flow data** (AADT, real-time if available)
3. **Create traffic density simulation**
4. **Vehicle animation system**

**Traffic Flow Implementation:**
```python
class TrafficFlow:
    """Traffic simulation using imported AADT data."""

    def __init__(self, road_network):
        self.network = road_network
        self.aadt_data = {}  # Road segment → vehicles/day

    def get_vehicle_density(self, segment_id, hour):
        """Calculate vehicles at given hour."""
        base_aadt = self.aadt_data.get(segment_id, 10000)
        hour_factor = HOURLY_FACTORS[hour]  # Peak/off-peak
        return base_aadt * hour_factor / 24

    def generate_vehicles(self, time_of_day):
        """Spawn vehicles based on traffic data."""
        pass
```

### Phase 6: POI Integration (Week 10-11)

1. **Import gas station locations**
2. **Create gas station geometry**
3. **Link to road network for navigation**

### Phase 7: Scene Assembly (Week 11-12)

1. **Combine all geometry**
2. **Apply materials**
3. **Set up lighting**
4. **Configure render settings**

---

## Part 5: Technical Specifications

### Coordinate System

```
Origin: Charlotte City Center (35.2271° N, 80.8431° W)
Projection: UTM Zone 17N (EPSG:32617) or local tangent plane
Units: Meters
Elevation: Relative to sea level (using DEM data)
```

### Data Format Standards

| Data Type | Format |
|-----------|--------|
| Road Network | JSON (our existing format) |
| Buildings | OBJ/FBX with metadata |
| Terrain | Heightmap PNG + mesh |
| Traffic | CSV/JSON with timestamps |
| POIs | GeoJSON |

### Performance Targets

| Metric | Target |
|--------|--------|
| Road segments | 5,000+ |
| Buildings | 1,000+ |
| Vehicles | 100-500 active |
| Frame rate | 24+ fps (viewport) |
| Render time | <5 min/frame |

---

## Part 6: Required APIs & Accounts

### Free Resources
- [ ] OpenStreetMap account (optional)
- [ ] OpenTopography account
- [ ] USGS Earth Explorer account

### Request Required
- [ ] RITIS API access (through NCDOT or research)
- [ ] NCDOT GIS data access

### Paid (Optional)
- [ ] TomTom Traffic API
- [ ] Google Maps API (for verification)

---

## Next Steps

1. **Immediate:** Create data acquisition scripts
2. **Week 1:** Download and process OSM/DEM data
3. **Week 2:** Build road network parser
4. **Week 3:** Integrate with existing urban module

---

## File Locations

```
lib/charlotte_digital_twin/     # New module
data/charlotte/                  # Downloaded data
  ├── osm/                       # OSM extracts
  ├── elevation/                 # DEM/LiDAR
  ├── traffic/                   # Traffic data
  └── poi/                       # POI extracts
.planning/charlotte/             # Planning docs
```

---

*Research completed: 2026-02-21*
*Ready to begin implementation upon approval*
