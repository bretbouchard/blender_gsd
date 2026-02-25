# Charlotte Digital Twin - Architecture

## Overview

A procedural urban environment for Charlotte, NC with elevation-aware road networks,
bridges, and buildings. This project builds on patterns from msg-1998 but adds
critical elevation handling and hierarchical organization.

## Key Differences from MSG-1998

| Aspect | MSG-1998 (NYC) | Charlotte |
|--------|---------------|-----------|
| Elevation | Flat (~sea level) | Variable terrain (190-260m) |
| Bridges | Minimal | 265 bridges - critical infrastructure |
| Scale | ~100 buildings | 3,739 buildings - needs batching |
| Roads | Grid system | Organic + highway interchanges |
| LOD | Hero block focus | Neighborhood/collection focus |

## Data Inventory

### Merged OSM Data (`charlotte-merged.osm`)

```
Nodes:      132,381
Ways:       18,418
Relations:  412

Coverage:
  minlat: 35.213160  minlon: -80.879550
  maxlat: 35.237720  maxlon: -80.819420
```

### Highway Types

| Type | Count | Notes |
|------|-------|-------|
| footway | 5,409 | Sidewalks, paths |
| service | 3,378 | Driveways, parking |
| secondary | 478 | Major connectors |
| residential | 333 | Local streets |
| primary | 253 | Arterial roads |
| motorway | 131 | I-77, I-85, I-277 |
| tertiary | 126 | Minor connectors |

### Buildings

| Type | Count | Notes |
|------|-------|-------|
| Generic (yes) | 2,888 | Basic buildings |
| House | 364 | Single family |
| Apartments | 96 | Multi-family |
| Commercial | 41 | Retail/office |
| **Total** | **3,739** | Needs batching |
| With addresses | 920 | ~25% have addr: tags |

### Bridges

- **265 bridges** - Critical for highway interchanges
- Must handle elevation stacking
- Need proper clearance for underpasses

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Charlotte Pipeline Orchestrator                   │
│  (Processes OSM → Creates organized Blender scene with elevation)   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Elevation   │    │    Import     │    │  Organization │
│               │    │               │    │               │
│ • DEM/Contour │    │ • OSM Parser  │    │ • Collections │
│ • Node heights│    │ • Way builder │    │ • Neighborhood│
│ • Bridge calc │    │ • Tag extract │    │ • LOD Groups  │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Buildings   │    │    Roads      │    │  Intersections│
│               │    │               │    │               │
│ • Batch proc  │    │ • Classify    │    │ • Detect      │
│ • Address tag │    │ • Elevation   │    │ • Bridges     │
│ • LOD levels  │    │ • Bridges     │    │ • Crosswalks  │
│ • Collections │    │ • Name tags   │    │ • Signals     │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Elevation System (NEW)

### Data Sources

1. **OSM elevation tags** - `ele` tags on nodes/ways
2. **DEM data** - External elevation tiles (if available)
3. **Interpolation** - Calculate from known points
4. **Bridge inference** - Calculate clearance heights

### Elevation Pipeline

```python
class ElevationManager:
    """Manages terrain elevation for all elements."""

    def get_node_elevation(node_id) -> float:
        """Get elevation for a node, interpolating if needed."""

    def get_road_elevation_profile(way_id) -> List[float]:
        """Get elevation at each vertex of a road."""

    def calculate_bridge_clearance(bridge_way) -> float:
        """Calculate minimum clearance under bridge."""

    def validate_intersections() -> List[ConflictReport]:
        """Check for elevation conflicts at intersections."""
```

### Bridge Handling

```python
class BridgeProcessor:
    """Handles bridge elevation and geometry."""

    # Standard clearances
    CLEARANCE_MIN = 4.5m    # Minimum road underpass
    CLEARANCE_STD = 5.5m    # Standard highway
    CLEARANCE_RAIL = 6.5m   # Railway overpass

    def process_bridge(way):
        # 1. Get road elevation at bridge start/end
        # 2. Calculate required rise for clearance
        # 3. Generate approach slopes (max 5% grade)
        # 4. Validate against crossing roads
        pass
```

## Import Pipeline

### Stage 1: Parse & Classify

```python
# scripts/1_parse_osm.py
# Reads charlotte-merged.osm
# Classifies all ways into categories
# Extracts node positions with elevation
# Creates classification manifest
```

### Stage 2: Elevation Processing

```python
# scripts/2_process_elevation.py
# Builds elevation model from data
# Interpolates missing elevations
# Validates bridge clearances
# Creates elevation reports
```

### Stage 3: Buildings

```python
# scripts/3_import_buildings.py
# Batch processes buildings (100-200 per batch)
# Preserves address tags as custom properties
# Groups into collections by:
#   - Neighborhood (from OSM data or spatial)
#   - Block (contiguous buildings)
#   - LOD level (based on importance/detail)
```

### Stage 4: Roads

```python
# scripts/4_import_roads.py
# Creates road segments with elevation
# Separates bridges as special objects
# Preserves name tags for all roads
# Classifies by type (highway tag)
```

### Stage 5: Intersections

```python
# scripts/5_build_intersections.py
# Detects intersection clusters
# Handles grade-separated (bridges) vs at-grade
# Creates intersection geometry
# Places crosswalks where appropriate
```

## Collection Structure

```
Scene Collection
├── Terrain
│   └── Ground_Plane
│
├── Roads
│   ├── Motorways          # I-77, I-85, I-277
│   │   ├── Bridges        # Elevated sections
│   │   └── At_Grade       # Ground level
│   ├── Arterials          # Primary roads
│   ├── Collectors         # Secondary roads
│   ├── Local              # Residential + tertiary
│   └── Service            # Driveways, parking
│
├── Buildings
│   ├── Uptown             # Downtown Charlotte
│   │   ├── Block_001
│   │   ├── Block_002
│   │   └── ...
│   ├── South_End
│   ├── Elizabeth
│   └── Other_Neighborhoods
│
├── Intersections
│   ├── At_Grade           # Normal intersections
│   └── Grade_Separated    # Highway interchanges
│
└── Infrastructure
    ├── Bridges            # Bridge structures
    └── Signals            # Traffic signals
```

## LOD System

### Building LOD

| LOD | Distance | Detail |
|-----|----------|--------|
| LOD0 (Hero) | 0-100m | Full geometry, windows, details |
| LOD1 (High) | 100-500m | Simplified geometry, implied windows |
| LOD2 (Med) | 500m-2km | Box geometry, single material |
| LOD3 (Low) | 2km+ | Flat footprint, minimal detail |

### Road LOD

| LOD | Features |
|-----|----------|
| LOD0 | Lane markings, cracks, patches, manholes |
| LOD1 | Lane markings only, simplified curbs |
| LOD2 | Textured surface, implied lanes |
| LOD3 | Flat colored surface |

## Attribute Preservation

All objects must preserve OSM attributes for targeting:

### Building Attributes

```python
# Stored as Blender custom properties
{
    "osm_id": 123456789,
    "building": "commercial",
    "addr:housenumber": "100",
    "addr:street": "N Tryon St",
    "addr:city": "Charlotte",
    "name": "Bank of America Plaza",
    "height": "150",  # meters if available
    "levels": "35",
}
```

### Road Attributes

```python
{
    "osm_id": 987654321,
    "name": "South Boulevard",
    "highway": "secondary",
    "lanes": "4",
    "surface": "asphalt",
    "bridge": "yes",  # if applicable
    "layer": "1",     # elevation layer
    "maxspeed": "45 mph",
}
```

## Batch Processing

### Why Batching

- 3,739 buildings exceeds reasonable single-operation limits
- Blender edit mode operations slow with large selections
- Memory management for large meshes
- Progress visibility during long operations

### Batch Strategy

```python
# Process in batches of 100-200
BATCH_SIZE = 150

def process_all_buildings():
    buildings = get_all_building_ways()
    total = len(buildings)

    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch = buildings[batch_start:batch_end]

        print(f"Processing {batch_start}-{batch_end} of {total}")

        # Process batch
        process_batch(batch)

        # Checkpoint
        save_progress(batch_end)
```

## Neighborhood Detection

Since OSM doesn't always have neighborhood tags, detect spatially:

```python
class NeighborhoodDetector:
    """Groups buildings into neighborhoods."""

    def detect_neighborhoods(buildings):
        # 1. Find buildings with explicit neighborhood tags
        # 2. For untagged, use nearest-neighbor with tagged
        # 3. Cluster by proximity (DBSCAN or similar)
        # 4. Assign to named neighborhoods

        return neighborhood_map
```

### Known Charlotte Neighborhoods

- Uptown (Downtown)
- South End
- Elizabeth
- Plaza Midwood
- NoDa (North Davidson)
- Dilworth
- Myers Park
- Fourth Ward

## File Structure

```
projects/charlotte/
├── maps/
│   └── charlotte-merged.osm    # Source data
│
├── scripts/
│   ├── 1_parse_osm.py          # Parse & classify
│   ├── 2_process_elevation.py  # Elevation handling
│   ├── 3_import_buildings.py   # Building import
│   ├── 4_import_roads.py       # Road import
│   ├── 5_build_intersections.py # Intersections
│   └── lib/
│       ├── elevation.py        # Elevation utilities
│       ├── classification.py   # Charlotte-specific classes
│       ├── neighborhoods.py    # Neighborhood detection
│       └── batching.py         # Batch processing utilities
│
├── docs/
│   ├── ARCHITECTURE.md         # This document
│   ├── ELEVATION.md            # Elevation system details
│   └── BATCHING.md             # Batch processing guide
│
└── output/
    └── charlotte.blend         # Output scene
```

## Implementation Phases

### Phase 1: Foundation
- [ ] Create elevation manager
- [ ] Parse OSM with classification
- [ ] Basic road import with elevation

### Phase 2: Buildings
- [ ] Batch building importer
- [ ] Address attribute preservation
- [ ] Neighborhood grouping

### Phase 3: Roads & Bridges
- [ ] Road classification (adapt from msg-1998)
- [ ] Bridge processing with elevation
- [ ] Grade-separated intersection handling

### Phase 4: Intersections
- [ ] Intersection detection (adapt from msg-1998)
- [ ] At-grade vs grade-separated logic
- [ ] Crosswalk placement

### Phase 5: LOD & Optimization
- [ ] LOD group creation
- [ ] Material assignment
- [ ] Scene optimization

## Key Patterns from MSG-1998

### Reusable Components

1. **Road Classification** (`road_system/classification.py`)
   - Adapt `RoadClass` enum for Charlotte road types
   - Keep `NYCRoadSpec` pattern, rename to `CharlotteRoadSpec`
   - OSM highway tag mapping still valid

2. **Intersection Detection** (`road_system/intersections.py`)
   - `IntersectionDetector` works for any road network
   - Add elevation-aware filtering for grade separation
   - `IntersectionCluster` handles clustering logic

3. **Batch Processing** (`5_separate_buildings_batch.py`)
   - Batch pattern with `BATCH_SIZE` and progress tracking
   - Vertex group separation approach
   - Collection organization

### New Requirements for Charlotte

1. **Elevation handling** - Not in msg-1998
2. **Bridge stacking** - Multiple layers at interchanges
3. **Neighborhood collections** - Organizational structure
4. **Higher scale batching** - 3700+ buildings vs ~100

## Next Steps

1. Create `scripts/lib/elevation.py` - Elevation manager
2. Create `scripts/lib/classification.py` - Charlotte-specific types
3. Create `scripts/1_parse_osm.py` - Parse and analyze
4. Test with subset of data
5. Iterate on full pipeline
