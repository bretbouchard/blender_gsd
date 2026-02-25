# Charlotte - Master Implementation Plan

## Overview

This plan coordinates the implementation of all Charlotte digital twin components.
Each phase builds on the previous, creating a complete urban environment from OSM data.

## Phase Order

```
Phase 1: Foundation
├── Elevation Manager (lib/elevation.py)
└── OSM Parser (1_parse_osm.py)

Phase 2: Import
├── Building Importer (3_import_buildings.py)
└── Road Importer (4_import_roads.py)

Phase 3: Infrastructure
└── Intersection Builder (5_build_intersections.py)

Phase 4: Optimization
└── LOD System (6_setup_lod.py)
```

## Phase 1: Foundation

### 1.1 Elevation Manager
**File:** `scripts/lib/elevation.py`
**Time:** 3-4 hours
**Dependencies:** None

**Tasks:**
- [ ] Create `ElevationManager` class
- [ ] Implement `load_from_osm()` to extract `ele` tags
- [ ] Implement `inverse_distance_weighting()` interpolation
- [ ] Implement `get_elevation()` with fallback
- [ ] Create `BridgeElevationCalculator`
- [ ] Add validation methods

**Output:**
- `scripts/lib/elevation.py`
- Can query elevation for any node

### 1.2 OSM Parser
**File:** `scripts/1_parse_osm.py`
**Time:** 2-3 hours
**Dependencies:** Elevation Manager

**Tasks:**
- [ ] Create `OSMParser` class
- [ ] Parse all nodes with positions
- [ ] Parse and classify all ways
- [ ] Extract buildings (has `building` tag)
- [ ] Extract roads (has `highway` tag)
- [ ] Flag bridges (`bridge=yes`)
- [ ] Generate statistics
- [ ] Save manifest to JSON

**Output:**
- `scripts/1_parse_osm.py`
- `output/osm_manifest.json`

---

## Phase 2: Import

### 2.1 Building Importer
**File:** `scripts/3_import_buildings.py`
**Time:** 4-5 hours
**Dependencies:** OSM Parser, Elevation Manager

**Tasks:**
- [ ] Create `BuildingImporter` class
- [ ] Implement batch processing (150 buildings/batch)
- [ ] Create building meshes from OSM footprints
- [ ] Add all OSM tags as custom properties
- [ ] Implement `NeighborhoodDetector`
- [ ] Organize into neighborhood collections
- [ ] Add checkpoint/resume support

**Output:**
- `scripts/lib/building_processor.py`
- `scripts/3_import_buildings.py`
- Buildings in Blender scene with attributes

### 2.2 Road Importer
**File:** `scripts/4_import_roads.py`
**Time:** 4-5 hours
**Dependencies:** OSM Parser, Elevation Manager

**Tasks:**
- [ ] Create `RoadClassifier` (adapt from msg-1998)
- [ ] Create `RoadImporter` class
- [ ] Build road mesh ribbons from vertices
- [ ] Apply elevation to road vertices
- [ ] Handle bridges as elevated segments
- [ ] Add all OSM tags as custom properties
- [ ] Organize into road type collections

**Output:**
- `scripts/lib/road_classification.py`
- `scripts/4_import_roads.py`
- Roads in Blender scene with attributes

---

## Phase 3: Infrastructure

### 3.1 Intersection Builder
**File:** `scripts/5_build_intersections.py`
**Time:** 4-5 hours
**Dependencies:** Road Importer

**Tasks:**
- [ ] Create `IntersectionDetector` (adapt from msg-1998)
- [ ] Add grade-separation detection
- [ ] Create `IntersectionBuilder`
- [ ] Build at-grade intersection geometry
- [ ] Create `CrosswalkBuilder`
- [ ] Mark grade-separated interchanges
- [ ] Organize into collections

**Output:**
- `scripts/lib/intersection_detector.py`
- `scripts/lib/intersection_builder.py`
- `scripts/5_build_intersections.py`
- Intersections in Blender scene

---

## Phase 4: Optimization

### 4.1 LOD System
**File:** `scripts/6_setup_lod.py`
**Time:** 2-3 hours
**Dependencies:** All importers

**Tasks:**
- [ ] Create `LODAssigner`
- [ ] Create `LODOrganizer`
- [ ] Create LOD collection hierarchy
- [ ] Assign buildings to LOD levels
- [ ] Assign roads to LOD levels
- [ ] Add visibility toggles

**Output:**
- `scripts/lib/lod_system.py`
- `scripts/6_setup_lod.py`
- All objects organized by LOD

---

## File Structure

```
projects/charlotte/
├── maps/
│   └── charlotte-merged.osm
│
├── scripts/
│   ├── lib/
│   │   ├── __init__.py
│   │   ├── elevation.py
│   │   ├── building_processor.py
│   │   ├── road_classification.py
│   │   ├── intersection_detector.py
│   │   ├── intersection_builder.py
│   │   └── lod_system.py
│   │
│   ├── 1_parse_osm.py
│   ├── 3_import_buildings.py
│   ├── 4_import_roads.py
│   ├── 5_build_intersections.py
│   └── 6_setup_lod.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── plans/
│       ├── ELEVATION_MANAGER.md
│       ├── OSM_PARSER.md
│       ├── BUILDING_IMPORTER.md
│       ├── ROAD_IMPORTER.md
│       ├── INTERSECTION_BUILDER.md
│       └── LOD_SYSTEM.md
│
└── output/
    ├── osm_manifest.json
    ├── elevation_report.json
    └── charlotte.blend
```

## Execution Order

```bash
# Phase 1: Foundation
python scripts/1_parse_osm.py

# Phase 2: Import (in Blender)
blender --python scripts/3_import_buildings.py
blender --python scripts/4_import_roads.py

# Phase 3: Infrastructure (in Blender)
blender --python scripts/5_build_intersections.py

# Phase 4: Optimization (in Blender)
blender --python scripts/6_setup_lod.py
```

## Estimated Total Time

| Phase | Time |
|-------|------|
| Phase 1: Foundation | 5-7 hours |
| Phase 2: Import | 8-10 hours |
| Phase 3: Infrastructure | 4-5 hours |
| Phase 4: Optimization | 2-3 hours |
| **Total** | **19-25 hours** |

## Success Criteria

- [ ] All 3,739 buildings imported with attributes
- [ ] All 5,500+ roads imported with names
- [ ] 265 bridges properly elevated
- [ ] Intersections detected and built
- [ ] LOD collections organized
- [ ] Can query by address/street name
- [ ] Viewport performance acceptable

## Next Action

Start implementation with **Phase 1.1: Elevation Manager**
