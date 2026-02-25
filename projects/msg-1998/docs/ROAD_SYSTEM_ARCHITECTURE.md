# MSG-1998 Road System Architecture

## Overview

Realistic NYC 1998 road system with proper sidewalks, curbs, lane markings,
intersections, and street furniture distribution. Designed to handle both
hero blocks (high detail) and city-wide roads (low LOD).

## Current State

### Existing Data
- **Streets_Roads collection:** ~100+ road mesh segments from OSM
- **Non-contiguous:** Roads are broken into individual pieces
- **Overlapping endpoints:** Roads touching/overlapping need intersection detection
- **Basic materials:** NYC_Asphalt_1998 (dark, rough)

### Existing Infrastructure
- `lib/urban/road_network.py` - L-system generator (for procedural roads)
- `lib/urban/road_geometry.py` - Segment/geometry data structures
- `lib/geometry_nodes/road_builder.py` - Road templates, lane specs
- `lib/charlotte_digital_twin/geometry/road_processor.py` - Intersection detection

## Requirements

### P0: Core Geometry
- [ ] **Road Classification** - Classify roads by type (arterial, local, residential)
- [ ] **Width Resolution** - Determine width from OSM tags + class defaults
- [ ] **Intersection Detection** - Find where roads meet/overlap
- [ ] **Intersection Geometry** - Create proper intersection surfaces
- [ ] **Sidewalk Builder** - Generate sidewalks along road edges
- [ ] **Curb Builder** - Generate curbs with proper height/slope

### P1: Detail Geometry
- [ ] **Lane Markings** - Center lines, edge lines, lane dividers
- [ ] **Crosswalks** - At intersections with crosswalk markings
- [ ] **Pavement Variations** - Patchwork, repairs, wear patterns
- [ ] **Special Road Classes** - Mark hero roads, one-way streets

### P2: Street Furniture
- [ ] **Manhole Covers** - Distribute along roads with variety
- [ ] **Street Signs** - Stop signs, street names, parking signs
- [ ] **Fire Hydrants** - Place at sidewalk edges
- [ ] **Trash Cans** - Corner placements
- [ ] **LOD System** - High detail hero blocks, low detail city-wide

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MSG Road Processor                              │
│  (Orchestrator - reads Streets_Roads, builds complete road system)  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Classification │    │   Geometry    │    │ Distribution  │
│               │    │               │    │               │
│ • RoadClass   │    │ • Pavement    │    │ • Manholes    │
│ • Width       │    │ • Sidewalk    │    │ • Signs       │
│ • LOD Level   │    │ • Curb        │    │ • Lamps       │
│ • Hero Flag   │    │ • Markings    │    │ • Hydrants    │
│ • One-way     │    │ • Intersection│    │ • LOD Manager │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Road Classification System

### NYC Road Types (1998)

| Class | Width | Lanes | Sidewalk | Markings | Examples |
|-------|-------|-------|----------|----------|----------|
| **Arterial** | 15-20m | 4+ | Yes | Full | 7th Ave, 34th St |
| **Collector** | 10-14m | 2-3 | Yes | Full | Side streets |
| **Local** | 7-10m | 2 | Yes | Minimal | Residential |
| **Service** | 4-6m | 1 | No | None | Alleys, driveways |
| **Hero** | Custom | Custom | High Detail | Full | MSG block |

### Classification Sources

1. **OSM Tags** (primary)
   - `highway=primary/secondary/tertiary/residential/service`
   - `lanes=N`
   - `width=X m`
   - `oneway=yes`

2. **Name Patterns** (secondary)
   - "Avenue", "Street" → likely 2-way arterial
   - "Place", "Lane" → local
   - "Drive" → could be anything

3. **Manual Override** (hero roads)
   - Custom property: `road_class = "hero"`
   - Or collection membership: `Hero_Roads`

## Intersection System

### Detection Strategy

```python
# 1. Endpoint Proximity Detection
# Roads with endpoints within 2m of each other = intersection candidate

# 2. Overlap Detection
# Roads that share vertices or have overlapping bounding boxes

# 3. Merge Strategy
# - Group roads by intersection cluster
# - Calculate union of widths
# - Generate intersection polygon
# - Apply intersection material
```

### Intersection Geometry

```
                    Sidewalk
        ┌───────────────────────────────┐
        │                               │
        │   ┌───────────────────────┐   │
        │   │                       │   │
        │   │    INTERSECTION       │   │ ← Different material
        │   │    (smoother asphalt) │   │
        │   │                       │   │
        │   └───────────────────────┘   │
        │                               │
        └───────────────────────────────┘
                    Curb
```

## Sidewalk/Curb System

### Sidewalk Profile

```
          Sidewalk Surface (concrete)
              ┌──────────────┐
              │              │
    Building  │              │  Road
     Wall     │              │
       │      │              │
       ▼      │              │
       ████   │              │
       ████   └──────────────┘
       ████   │              │
       ████   │   CURB       │ ← 15cm rise
       ████████              │
              │   ROAD       │
              │              │
```

### Curb Geometry
- **Height:** 15cm (standard NYC)
- **Width:** 30cm (top) + 15cm (slope)
- **Material:** Concrete with dirt/grime

## Lane Markings System

### Marking Types

| Type | Color | Width | Placement |
|------|-------|-------|-----------|
| Center Line | Yellow | 10cm | Road center (double line) |
| Lane Divider | White | 10cm | Between lanes (dashed) |
| Edge Line | White | 15cm | Road edge (solid) |
| Crosswalk | White | 30cm | At intersections |
| Stop Line | White | 30cm | Before intersections |

### Marking Distribution

```python
# Distance-based distribution
DASH_LENGTH = 3.0  # meters
DASH_GAP = 6.0     # meters

# Generate markings along road centerline
for t in range(0, road_length, DASH_LENGTH + DASH_GAP):
    create_dash_marking(position=t, length=DASH_LENGTH)
```

## Street Furniture Distribution

### Manhole Covers
- **Spacing:** Every 30-50m along road
- **Placement:** Center of lane or offset
- **Variations:** Different cover types (water, sewer, gas, electric)
- **LOD:** High detail near intersections, low detail elsewhere

### Distribution Strategy

```python
class StreetFurnitureDistributor:
    def distribute_along_road(self, road, item_type, spacing, offset):
        """Distribute items along road with proper spacing."""

        # Calculate positions
        positions = []
        for t in range(0, road.length, spacing):
            pos = road.sample_position(t)

            # Check for intersection collision
            if not self.intersects_intersection(pos):
                positions.append(pos)

        return positions
```

## LOD System

### LOD Levels

| LOD | Distance | Features |
|-----|----------|----------|
| **LOD0** (Hero) | 0-50m | Full detail: individual markings, manholes, cracks |
| **LOD1** (High) | 50-200m | Simplified markings, merged furniture |
| **LOD2** (Medium) | 200-500m | No markings, implied furniture |
| **LOD3** (Low) | 500m+ | Flat textured surface only |

### LOD Switching

```python
# Based on camera distance or area classification
def get_lod_level(distance_or_area):
    if area == "hero_block":
        return LOD0  # Always high detail
    elif distance < 50:
        return LOD0
    elif distance < 200:
        return LOD1
    elif distance < 500:
        return LOD2
    else:
        return LOD3
```

## Implementation Phases

### Phase 1: Core Infrastructure (P0)
1. Read existing `Streets_Roads` mesh data
2. Classify roads by type/width
3. Detect intersections
4. Generate basic pavement + curb geometry

### Phase 2: Sidewalks & Markings (P1)
1. Generate sidewalk geometry
2. Add lane markings
3. Create crosswalks at intersections
4. Apply proper materials

### Phase 3: Street Furniture (P2)
1. Distribute manhole covers
2. Place street furniture
3. Implement LOD system
4. Hero block detailing

## File Structure

```
projects/msg-1998/
├── maps/
│   ├── msg_map.blend           # Main scene
│   └── road_system/            # NEW: Road system modules
│       ├── __init__.py
│       ├── classification.py   # Road classification
│       ├── intersections.py    # Intersection detection/building
│       ├── sidewalks.py        # Sidewalk generation
│       ├── curbs.py            # Curb generation
│       ├── markings.py         # Lane markings
│       ├── furniture.py        # Street furniture distribution
│       └── lod.py              # LOD management
│
├── assets/
│   └── road_system/            # NEW: Road assets
│       ├── materials/
│       │   ├── asphalt.blend
│       │   ├── concrete.blend
│       │   └── marking.blend
│       ├── furniture/
│       │   ├── manhole_covers.blend
│       │   ├── hydrants.blend
│       │   └── signs.blend
│       └── markings/
│           ├── center_line.blend
│           └── crosswalk.blend
│
└── docs/
    └── ROAD_SYSTEM_ARCHITECTURE.md  # This document
```

## Next Steps

1. **Analyze current road data** - Understand exact mesh structure in Streets_Roads
2. **Create classification system** - Map OSM types to NYC road classes
3. **Build intersection detector** - Find overlapping endpoint clusters
4. **Implement basic geometry** - Pavement + curbs first
5. **Add sidewalks** - With proper profiles
6. **Add markings** - Center lines, crosswalks
7. **Distribute furniture** - Manholes, signs
8. **Implement LOD** - Distance-based switching
