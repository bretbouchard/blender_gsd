# Charlotte - Road Importer Plan

## Goal
Import all roads from OSM data with proper elevation handling, bridge separation, name preservation, and classification for the Charlotte digital twin.

## Requirements
- Import all highway types (motorways to footways)
- Handle bridges as special elevated segments
- Preserve road names for targeting
- Apply elevation to road vertices
- Separate into collections by road type

## Data Inventory (Charlotte)

| Highway Type | Count | Classification |
|-------------|-------|---------------|
| motorway | 131 | Highway (I-77, I-85, I-277) |
| motorway_link | 136 | Highway ramps |
| primary | 253 | Arterial |
| secondary | 478 | Collector |
| tertiary | 126 | Collector |
| residential | 333 | Local |
| service | 3,378 | Service |
| footway | 5,409 | Pedestrian |
| Bridges | 265 | Special handling |

## Implementation

### File: `scripts/lib/road_classification.py`

```python
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum

class RoadClass(Enum):
    """Charlotte road classification."""
    HIGHWAY = "highway"        # Motorways (I-77, I-85)
    ARTERIAL = "arterial"      # Primary roads
    COLLECTOR = "collector"    # Secondary/tertiary
    LOCAL = "local"            # Residential
    SERVICE = "service"        # Driveways, parking
    PEDESTRIAN = "pedestrian"  # Footways, paths

@dataclass
class CharlotteRoadSpec:
    """Specifications for Charlotte road types."""
    road_class: RoadClass
    width_meters: float
    lanes: int
    has_sidewalk: bool
    has_markings: bool
    default_material: str
    lod_default: int

# Charlotte road specifications
CHARLOTTE_ROAD_SPECS: Dict[RoadClass, CharlotteRoadSpec] = {
    RoadClass.HIGHWAY: CharlotteRoadSpec(
        road_class=RoadClass.HIGHWAY,
        width_meters=25.0,
        lanes=6,
        has_sidewalk=False,
        has_markings=True,
        default_material="asphalt_highway",
        lod_default=1,
    ),
    RoadClass.ARTERIAL: CharlotteRoadSpec(
        road_class=RoadClass.ARTERIAL,
        width_meters=15.0,
        lanes=4,
        has_sidewalk=True,
        has_markings=True,
        default_material="asphalt_arterial",
        lod_default=1,
    ),
    RoadClass.COLLECTOR: CharlotteRoadSpec(
        road_class=RoadClass.COLLECTOR,
        width_meters=12.0,
        lanes=2,
        has_sidewalk=True,
        has_markings=True,
        default_material="asphalt_collector",
        lod_default=2,
    ),
    RoadClass.LOCAL: CharlotteRoadSpec(
        road_class=RoadClass.LOCAL,
        width_meters=9.0,
        lanes=2,
        has_sidewalk=True,
        has_markings=True,
        default_material="asphalt_local",
        lod_default=2,
    ),
    RoadClass.SERVICE: CharlotteRoadSpec(
        road_class=RoadClass.SERVICE,
        width_meters=5.0,
        lanes=1,
        has_sidewalk=False,
        has_markings=False,
        default_material="asphalt_service",
        lod_default=3,
    ),
    RoadClass.PEDESTRIAN: CharlotteRoadSpec(
        road_class=RoadClass.PEDESTRIAN,
        width_meters=2.0,
        lanes=0,
        has_sidewalk=False,
        has_markings=False,
        default_material="concrete_path",
        lod_default=3,
    ),
}

class RoadClassifier:
    """Classifies Charlotte roads from OSM data."""

    OSM_HIGHWAY_MAP = {
        'motorway': RoadClass.HIGHWAY,
        'motorway_link': RoadClass.HIGHWAY,
        'trunk': RoadClass.HIGHWAY,
        'trunk_link': RoadClass.HIGHWAY,
        'primary': RoadClass.ARTERIAL,
        'primary_link': RoadClass.ARTERIAL,
        'secondary': RoadClass.COLLECTOR,
        'secondary_link': RoadClass.COLLECTOR,
        'tertiary': RoadClass.COLLECTOR,
        'tertiary_link': RoadClass.COLLECTOR,
        'residential': RoadClass.LOCAL,
        'unclassified': RoadClass.LOCAL,
        'living_street': RoadClass.LOCAL,
        'service': RoadClass.SERVICE,
        'driveway': RoadClass.SERVICE,
        'parking_aisle': RoadClass.SERVICE,
        'footway': RoadClass.PEDESTRIAN,
        'pedestrian': RoadClass.PEDESTRIAN,
        'path': RoadClass.PEDESTRIAN,
        'cycleway': RoadClass.PEDESTRIAN,
        'steps': RoadClass.PEDESTRIAN,
    }

    def classify(self, osm_highway: str) -> RoadClass:
        """Classify road from OSM highway tag."""
        return self.OSM_HIGHWAY_MAP.get(osm_highway, RoadClass.LOCAL)

    def get_spec(self, road_class: RoadClass) -> CharlotteRoadSpec:
        """Get specifications for a road class."""
        return CHARLOTTE_ROAD_SPECS[road_class]
```

### File: `scripts/4_import_roads.py`

```python
import bpy
import bmesh
from typing import List, Dict, Optional
import math

from lib.road_classification import RoadClass, RoadClassifier
from lib.elevation import ElevationManager

class RoadImporter:
    """Imports roads from OSM data with elevation."""

    def __init__(self, osm_manifest_path: str, elevation_manager: ElevationManager):
        self.manifest = self._load_manifest(osm_manifest_path)
        self.elevation = elevation_manager
        self.classifier = RoadClassifier()

    def import_all(self):
        """Import all roads."""
        roads = self._extract_roads()
        bridges = self._extract_bridges()

        print(f"Importing {len(roads)} roads and {len(bridges)} bridges")

        # Import regular roads
        for road_data in roads:
            self._import_road(road_data)

        # Import bridges (special handling)
        for bridge_data in bridges:
            self._import_bridge(bridge_data)

        self._organize_collections()
        print("Road import complete!")

    def _import_road(self, data: dict):
        """Import a single road segment."""
        # Get classification
        highway_type = data['tags'].get('highway', 'unclassified')
        road_class = self.classifier.classify(highway_type)
        spec = self.classifier.get_spec(road_class)

        # Get node positions with elevation
        vertices = []
        for node_id in data['node_ids']:
            node = self.manifest['nodes'][str(node_id)]
            x, y = self._latlon_to_local(node['lat'], node['lon'])
            z = self.elevation.get_elevation(node_id)
            vertices.append((x, y, z))

        # Create curve or mesh
        obj = self._create_road_mesh(data['osm_id'], vertices, spec.width)

        # Add custom properties
        self._add_properties(obj, data, road_class, spec)

    def _import_bridge(self, data: dict):
        """Import a bridge segment with elevated geometry."""
        highway_type = data['tags'].get('highway', 'unclassified')
        road_class = self.classifier.classify(highway_type)
        spec = self.classifier.get_spec(road_class)

        # Get vertices with bridge elevation
        vertices = []
        for i, node_id in enumerate(data['node_ids']):
            node = self.manifest['nodes'][str(node_id)]
            x, y = self._latlon_to_local(node['lat'], node['lon'])

            # Calculate bridge deck elevation
            base_z = self.elevation.get_elevation(node_id)
            bridge_z = self._calculate_bridge_elevation(data, i, base_z)

            vertices.append((x, y, bridge_z))

        obj = self._create_road_mesh(f"Bridge_{data['osm_id']}", vertices, spec.width)

        # Mark as bridge
        obj['is_bridge'] = True
        obj['bridge_layer'] = data['tags'].get('layer', '1')

        self._add_properties(obj, data, road_class, spec)

    def _calculate_bridge_elevation(self, data: dict, vertex_index: int, base_z: float) -> float:
        """Calculate the deck elevation for a bridge vertex."""
        # Get layer (default 1)
        layer = int(data['tags'].get('layer', '1'))

        # Standard clearance per layer
        clearance = 5.5 * layer

        # For interior vertices, interpolate between endpoints
        # For endpoints, use clearance above ground
        return base_z + clearance

    def _create_road_mesh(self, name: str, vertices: List[tuple], width: float) -> bpy.types.Object:
        """Create a road mesh from vertices."""
        mesh = bpy.data.meshes.new(name)

        bm = bmesh.new()

        # Create vertices
        bm_verts = [bm.verts.new(v) for v in vertices]

        # Create road surface (simple ribbon)
        if len(bm_verts) >= 2:
            # For each segment, create a quad
            for i in range(len(bm_verts) - 1):
                # Calculate perpendicular direction for width
                v1 = vertices[i]
                v2 = vertices[i + 1]

                direction = (
                    v2[0] - v1[0],
                    v2[1] - v1[1],
                    0  # Ignore Z for direction
                )
                length = math.sqrt(direction[0]**2 + direction[1]**2)
                if length > 0:
                    direction = (direction[0]/length, direction[1]/length)
                else:
                    direction = (1, 0)

                # Perpendicular
                perp = (-direction[1], direction[0])

                # Half width offset
                offset = width / 2

                # Create quad vertices
                p1 = (v1[0] + perp[0]*offset, v1[1] + perp[1]*offset, v1[2])
                p2 = (v1[0] - perp[0]*offset, v1[1] - perp[1]*offset, v1[2])
                p3 = (v2[0] - perp[0]*offset, v2[1] - perp[1]*offset, v2[2])
                p4 = (v2[0] + perp[0]*offset, v2[1] + perp[1]*offset, v2[2])

                bv1 = bm.verts.new(p1)
                bv2 = bm.verts.new(p2)
                bv3 = bm.verts.new(p3)
                bv4 = bm.verts.new(p4)

                bm.faces.new([bv1, bv2, bv3, bv4])

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)

        return obj

    def _add_properties(self, obj, data: dict, road_class: RoadClass, spec):
        """Add custom properties to road object."""
        obj['osm_id'] = data['osm_id']
        obj['road_class'] = road_class.value
        obj['highway_type'] = data['tags'].get('highway', 'unknown')

        # Name (critical for targeting)
        if 'name' in data['tags']:
            obj['road_name'] = data['tags']['name']
            # Also set Blender object name
            obj.name = f"Road_{data['tags']['name'].replace(' ', '_')}"

        # Physical properties
        obj['width'] = spec.width_meters
        obj['lanes'] = data['tags'].get('lanes', spec.lanes)

        # Other tags
        for key in ['surface', 'oneway', 'maxspeed', 'ref']:
            if key in data['tags']:
                safe_key = key.replace(':', '_')
                obj[f'tag_{safe_key}'] = data['tags'][key]

    def _organize_collections(self):
        """Organize roads into collections by type."""
        # Create collection hierarchy
        roads_coll = self._get_or_create_collection("Roads")
        bridges_coll = self._get_or_create_collection("Bridges", parent="Roads")

        # Sub-collections for road types
        for road_class in RoadClass:
            self._get_or_create_collection(road_class.value.capitalize(), parent="Roads")

        # Move objects to appropriate collections
        for obj in bpy.context.scene.objects:
            if obj.get('road_class'):
                if obj.get('is_bridge'):
                    target = bridges_coll
                else:
                    class_name = obj['road_class'].capitalize()
                    target = self._get_or_create_collection(class_name, parent="Roads")

                # Move to collection
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                target.objects.link(obj)

    def _get_or_create_collection(self, name: str, parent: str = None) -> bpy.types.Collection:
        """Get or create a collection."""
        coll = bpy.data.collections.get(name)
        if not coll:
            coll = bpy.data.collections.new(name)
            if parent:
                parent_coll = bpy.data.collections.get(parent)
                if parent_coll:
                    parent_coll.children.link(coll)
                else:
                    bpy.context.scene.collection.children.link(coll)
            else:
                bpy.context.scene.collection.children.link(coll)
        return coll

    def _latlon_to_local(self, lat: float, lon: float) -> tuple:
        """Convert lat/lon to local coordinates."""
        ref_lat = 35.226
        ref_lon = -80.843

        meters_per_deg_lat = 111000
        meters_per_deg_lon = 111000 * math.cos(math.radians(ref_lat))

        x = (lon - ref_lon) * meters_per_deg_lon
        y = (lat - ref_lat) * meters_per_deg_lat

        return (x, y)

def main():
    """Main entry point."""
    from lib.elevation import ElevationManager

    elevation = ElevationManager()
    elevation.load_from_manifest('output/osm_manifest.json')

    importer = RoadImporter('output/osm_manifest.json', elevation)
    importer.import_all()

if __name__ == '__main__':
    main()
```

## Collection Structure

```
Roads/
├── Bridges/              # All bridge segments
│   ├── Bridge_123456789  # Named by OSM ID
│   └── ...
├── Highway/              # Motorways
│   ├── Road_I_77
│   └── Road_I_85
├── Arterial/             # Primary roads
│   ├── Road_South_Boulevard
│   └── Road_N_Tryon_St
├── Collector/            # Secondary/tertiary
├── Local/                # Residential
├── Service/              # Driveways, parking
└── Pedestrian/           # Footways, paths
```

## Road Custom Properties

```python
# Identity
obj['osm_id'] = 987654321
obj['road_name'] = "South Boulevard"  # For targeting
obj['road_class'] = "arterial"
obj['highway_type'] = "primary"

# Physical
obj['width'] = 15.0
obj['lanes'] = 4
obj['surface'] = "asphalt"

# Traffic
obj['tag_oneway'] = "no"
obj['tag_maxspeed'] = "45 mph"
obj['tag_ref'] = "NC-16"

# Bridge-specific
obj['is_bridge'] = True
obj['bridge_layer'] = "1"
```

## Bridge Handling

### Elevation Calculation
```
Bridge deck Z = Ground Z + (Layer * Clearance)

Where:
- Ground Z = elevation at bridge location
- Layer = OSM layer tag (1, 2, 3...)
- Clearance = 5.5m (standard highway clearance)
```

### Approach Slopes
```
For bridge approaches:
- Max grade: 5%
- Calculate slope length from elevation change
- Interpolate intermediate vertices
```

## Success Criteria
- [ ] All 5,500+ road segments imported
- [ ] 265 bridges separated and elevated
- [ ] Road names preserved for targeting
- [ ] Elevation applied to all vertices
- [ ] Organized into type-based collections
- [ ] Bridge clearances validated

## Estimated Effort
- Road classification: 1 hour (adapt from msg-1998)
- Road importer: 2-3 hours
- Bridge processing: 2 hours
- Collection organization: 1 hour
