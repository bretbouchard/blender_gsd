# Charlotte - Geometry Nodes Road Builder

## Overview

Instead of importing static road meshes, we'll create a geometry nodes system that:
1. Uses OSM road paths as curve data
2. Procedurally generates road geometry with proper width
3. Distributes lane markings, street lights, and signals
4. Handles elevation from the terrain

## Architecture

```
OSM Data → Curve Objects (per road) → Geometry Nodes Modifier → Final Road Geometry

Geometry Nodes Pipeline:
├── Input: Curve + Road Attributes (width, lanes, type, name)
├── Resample Curve (even spacing)
├── Sweep/Mesh to generate road surface
├── Store Named Attributes for downstream use
│   ├── Road centerline
│   ├── Lane positions
│   ├── Edge positions
│   └── Elevation
├── Distribute Instances along road:
│   ├── Lane markings (center line, edge lines, lane dividers)
│   ├── Street lights (spacing based on road type)
│   ├── Manholes
│   └── Traffic signals (at intersections)
└── Output: Combined road geometry
```

## Data Flow

### Stage 1: OSM → Curves
```python
# For each road way in OSM:
# - Create a Curve object
# - Set spline points from OSM nodes
# - Store attributes as custom properties:
#   - road_class: highway/arterial/local
#   - width: meters
#   - lanes: count
#   - name: street name
#   - surface: asphalt/concrete
#   - is_bridge: bool
#   - layer: elevation layer
```

### Stage 2: Geometry Nodes Processing
```
[Curve Input]
     │
     ├── Resample Curve (spacing: 1m)
     │
     ├── Set Position (apply elevation)
     │
     ├── Mesh to Curve → Sweep (create road surface)
     │        │
     │        └── Profile: Rectangle(width, 0.1)
     │
     ├── Instance on Points (lane markings)
     │        │
     │        └── Select by distance from center
     │
     ├── Instance on Points (street lights)
     │        │
     │        └── Select every N meters based on road type
     │
     └── [Output Geometry]
```

## Road Types and Parameters

| Road Class | Width | Lanes | Light Spacing | Markings |
|------------|-------|-------|---------------|----------|
| Highway | 25m | 6 | 50m | Full |
| Arterial | 15m | 4 | 30m | Full |
| Collector | 12m | 2 | 40m | Basic |
| Local | 9m | 2 | None | Minimal |
| Service | 5m | 1 | None | None |
| Pedestrian | 2m | 0 | None | None |

## Geometry Nodes Setup

### Node Group: `Road_Builder`

**Inputs:**
- `Road Curve` (Curve)
- `Width` (Float, default: 10.0)
- `Lanes` (Int, default: 2)
- `Road Class` (Int: 0=Highway, 1=Arterial, 2=Collector, 3=Local)
- `Elevation Attribute` (Vector)

**Internals:**
1. Resample curve to 1m segments
2. Create road surface mesh
3. Generate lane marking instances
4. Generate street light instances
5. Store intersection points

**Outputs:**
- `Road Geometry` (Mesh)
- `Lane Markings` (Instances)
- `Street Lights` (Instances)
- `Intersection Points` (Points)

### Node Group: `Lane_Markings_Generator`

**Inputs:**
- `Road Centerline` (Curve)
- `Width` (Float)
- `Lanes` (Int)
- `Marking Type` (Int: 0=Full, 1=Basic, 2=Minimal, 3=None)

**Generates:**
- Center line (yellow, double solid)
- Lane dividers (white, dashed)
- Edge lines (white, solid)
- Crosswalks (at marked points)

### Node Group: `Street_Light_Distributor`

**Inputs:**
- `Road Centerline` (Curve)
- `Spacing` (Float, default: 30.0)
- `Side` (Int: 0=Both, 1=Left, 2=Right)
- `Offset` (Float, default: 2.0)

**Generates:**
- Street light pole instances
- Positioned along road edges
- Oriented perpendicular to road

### Node Group: `Intersection_Builder`

**Inputs:**
- `Intersection Points` (Points)
- `Road Widths` (Float per point)

**Generates:**
- Intersection surface mesh
- Crosswalk markings
- Traffic signal positions

## Attribute Storage

Each curve object stores:

```python
# Object custom properties
obj['osm_id'] = int
obj['road_class'] = 'highway' | 'arterial' | 'collector' | 'local' | 'service'
obj['width'] = float  # meters
obj['lanes'] = int
obj['name'] = str  # street name
obj['surface'] = str
obj['is_bridge'] = bool
obj['layer'] = int

# Named attributes on curve (for geometry nodes)
curve.attributes['road_width'] = float per control point
curve.attributes['elevation'] = float per control point
```

## Implementation Files

```
scripts/
├── 4_import_roads_as_curves.py   # NEW: Import roads as curves
└── lib/
    └── geo_nodes_road.py          # Geometry nodes setup

geo_nodes/
├── Road_Builder.blend             # Main road builder node group
├── Lane_Markings.blend            # Lane marking assets
├── Street_Lights.blend            # Street light assets
└── Markings/
    ├── center_line.blend
    ├── lane_divider.blend
    └── crosswalk.blend
```

## Benefits Over Static Mesh

1. **Flexibility**: Change road width, lanes, markings without re-importing
2. **Performance**: Instances for lights/markings are more efficient
3. **Consistency**: Same road type always looks the same
4. **Elevation**: Can adjust terrain and roads update
5. **LOD**: Can easily switch detail levels
6. **Targeting**: Query by street name via curve object

## Next Steps

1. Create curve importer (`4_import_roads_as_curves.py`)
2. Build geometry nodes setup in Blender
3. Create marking/light assets
4. Test on subset of Charlotte roads
