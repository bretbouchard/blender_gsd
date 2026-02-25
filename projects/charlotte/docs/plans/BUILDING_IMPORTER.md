# Charlotte - Building Importer Plan

## Goal
Import 3,739 buildings from OSM data into Blender, preserving all attributes (addresses, names, types), organizing into neighborhood collections, and supporting batch processing for performance.

## Requirements
- Batch process buildings (100-200 per batch) to avoid memory issues
- Preserve all OSM tags as Blender custom properties
- Group buildings into collections by neighborhood/block
- Support LOD grouping based on building importance
- Handle buildings with and without address data

## Challenges

### Scale
- 3,739 buildings vs ~100 in msg-1998
- Need efficient batch processing
- Progress tracking and checkpointing

### Organization
- OSM may not have neighborhood tags
- Need spatial clustering for neighborhoods
- Block detection for contiguous buildings

### Address Preservation
- Only 920 buildings (~25%) have address data
- Need to preserve `addr:housenumber`, `addr:street`, `addr:city`
- Enable targeting by address: "100 N Tryon St"

## Implementation

### File: `scripts/lib/building_processor.py`

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
import math

@dataclass
class BuildingData:
    osm_id: int
    name: str
    building_type: str
    lod_level: int

    # Address
    housenumber: Optional[str]
    street: Optional[str]
    city: str = "Charlotte"

    # Physical
    height: Optional[float]
    levels: Optional[int]

    # Organization
    neighborhood: Optional[str]
    block_id: Optional[str]

    # Tags
    tags: Dict[str, str]

class BuildingClassifier:
    """Classifies buildings for LOD and priority."""

    # Building importance by type
    IMPORTANCE = {
        'commercial': 10,
        'retail': 9,
        'office': 9,
        'apartments': 7,
        'house': 5,
        'terrace': 5,
        'garage': 2,
        'shed': 1,
        'yes': 3,  # Generic
    }

    def get_lod_level(self, building: BuildingData) -> int:
        """Determine LOD level for a building."""
        # Named buildings are always LOD0
        if building.name:
            return 0

        # Buildings with addresses get LOD1
        if building.housenumber and building.street:
            return 1

        # By type importance
        importance = self.IMPORTANCE.get(building.building_type, 3)
        if importance >= 7:
            return 0
        elif importance >= 5:
            return 1
        else:
            return 2

class NeighborhoodDetector:
    """Groups buildings into neighborhoods."""

    # Charlotte neighborhoods with approximate centers
    NEIGHBORHOODS = {
        'Uptown': (35.227, -80.843),
        'South End': (35.217, -80.855),
        'Elizabeth': (35.216, -80.822),
        'Plaza Midwood': (35.226, -80.807),
        'NoDa': (35.235, -80.835),
        'Dilworth': (35.208, -80.848),
        'Myers Park': (35.195, -80.842),
        'Fourth Ward': (35.233, -80.850),
    }

    def __init__(self, max_distance: float = 500):
        self.max_distance = max_distance

    def assign_neighborhood(self, lat: float, lon: float) -> Optional[str]:
        """Find nearest neighborhood for coordinates."""
        best_neighborhood = None
        best_distance = float('inf')

        for name, (center_lat, center_lon) in self.NEIGHBORHOODS.items():
            dist = self._haversine(lat, lon, center_lat, center_lon)
            if dist < best_distance:
                best_distance = dist
                best_neighborhood = name

        if best_distance <= self.max_distance:
            return best_neighborhood
        return 'Other'

    def _haversine(self, lat1, lon1, lat2, lon2) -> float:
        """Calculate distance in meters between two points."""
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

class BlockDetector:
    """Groups buildings into city blocks."""

    def __init__(self, max_distance: float = 30):
        """
        Args:
            max_distance: Maximum distance (meters) for buildings to be in same block
        """
        self.max_distance = max_distance

    def detect_blocks(self, buildings: List[BuildingData]) -> Dict[str, List[int]]:
        """
        Cluster buildings into blocks.

        Returns:
            Dict mapping block_id -> list of building osm_ids
        """
        # Use simple distance-based clustering
        blocks = {}
        assigned = set()
        block_num = 0

        for i, b1 in enumerate(buildings):
            if b1.osm_id in assigned:
                continue

            block_id = f"Block_{block_num:04d}"
            blocks[block_id] = [b1.osm_id]
            assigned.add(b1.osm_id)

            # Find nearby buildings
            for j, b2 in enumerate(buildings):
                if b2.osm_id in assigned:
                    continue
                if self._is_nearby(b1, b2):
                    blocks[block_id].append(b2.osm_id)
                    assigned.add(b2.osm_id)

            block_num += 1

        return blocks

    def _is_nearby(self, b1: BuildingData, b2: BuildingData) -> bool:
        """Check if two buildings are in the same block."""
        # Need lat/lon for buildings - would be added during processing
        pass
```

### File: `scripts/3_import_buildings.py`

```python
import bpy
import bmesh
from typing import List, Dict
import json

class BuildingImporter:
    """Imports buildings from OSM data into Blender."""

    BATCH_SIZE = 150  # Buildings per batch
    CHECKPOINT_FILE = "output/building_progress.json"

    def __init__(self, osm_manifest_path: str):
        self.manifest = self._load_manifest(osm_manifest_path)
        self.buildings = self._extract_buildings()
        self.processor = BuildingProcessor()
        self.checkpoint = self._load_checkpoint()

    def import_all(self):
        """Import all buildings in batches."""
        total = len(self.buildings)
        start = self.checkpoint.get('last_processed', 0)

        print(f"Importing {total} buildings starting from {start}")

        for batch_start in range(start, total, self.BATCH_SIZE):
            batch_end = min(batch_start + self.BATCH_SIZE, total)
            batch = self.buildings[batch_start:batch_end]

            print(f"  Processing batch {batch_start}-{batch_end} of {total}")
            self._process_batch(batch, batch_start)

            # Save checkpoint
            self._save_checkpoint(batch_end)

        print("Building import complete!")

    def _process_batch(self, batch: List[dict], batch_num: int):
        """Process a single batch of buildings."""
        for building_data in batch:
            try:
                obj = self._create_building_object(building_data)
                self._add_to_collection(obj, building_data)
            except Exception as e:
                print(f"Error processing building {building_data['osm_id']}: {e}")

    def _create_building_object(self, data: dict) -> bpy.types.Object:
        """Create a Blender object for a building."""
        # Get node positions for building footprint
        nodes = [self.manifest['nodes'][str(nid)] for nid in data['node_ids']]

        # Convert lat/lon to local coordinates
        vertices = [self._latlon_to_local(n['lat'], n['lon']) for n in nodes]

        # Create mesh
        mesh = bpy.data.meshes.new(f"Building_{data['osm_id']}")

        # Create face from vertices
        bm = bmesh.new()
        bm_verts = [bm.verts.new(v) for v in vertices]
        bm.verts.ensure_lookup_table()

        if len(bm_verts) >= 3:
            bm.faces.new(bm_verts)

        bm.to_mesh(mesh)
        bm.free()

        # Create object
        obj = bpy.data.objects.new(f"Building_{data['osm_id']}", mesh)

        # Add custom properties (all OSM tags)
        for key, value in data['tags'].items():
            # Blender property names can't have colons
            safe_key = key.replace(':', '_')
            obj[safe_key] = value

        # Add classification properties
        obj['osm_id'] = data['osm_id']
        obj['building_type'] = data.get('building', 'yes')
        obj['lod_level'] = data.get('lod_hint', 2)

        if 'addr:housenumber' in data['tags']:
            obj['addr_housenumber'] = data['tags']['addr:housenumber']
        if 'addr:street' in data['tags']:
            obj['addr_street'] = data['tags']['addr:street']

        return obj

    def _add_to_collection(self, obj: bpy.types.Object, data: dict):
        """Add building to appropriate collection."""
        # Determine neighborhood
        nodes = [self.manifest['nodes'][str(nid)] for nid in data['node_ids']]
        center_lat = sum(n['lat'] for n in nodes) / len(nodes)
        center_lon = sum(n['lon'] for n in nodes) / len(nodes)

        neighborhood = self.processor.neighborhood_detector.assign_neighborhood(
            center_lat, center_lon
        )

        # Get or create collection hierarchy
        neighborhood_coll = self._get_or_create_collection(
            neighborhood, parent="Buildings"
        )

        # Link object
        bpy.context.scene.collection.objects.link(obj)
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        neighborhood_coll.objects.link(obj)

    def _get_or_create_collection(self, name: str, parent: str) -> bpy.types.Collection:
        """Get or create a collection with given parent."""
        coll = bpy.data.collections.get(name)
        if not coll:
            coll = bpy.data.collections.new(name)
            parent_coll = bpy.data.collections.get(parent)
            if parent_coll:
                parent_coll.children.link(coll)
            else:
                bpy.context.scene.collection.children.link(coll)
        return coll

    def _latlon_to_local(self, lat: float, lon: float) -> tuple:
        """Convert lat/lon to local scene coordinates."""
        # Use a reference point (center of data)
        ref_lat = 35.226
        ref_lon = -80.843

        # Approximate meters per degree at this latitude
        meters_per_deg_lat = 111000
        meters_per_deg_lon = 111000 * math.cos(math.radians(ref_lat))

        x = (lon - ref_lon) * meters_per_deg_lon
        y = (lat - ref_lat) * meters_per_deg_lat

        return (x, y, 0)  # Z will be set by elevation

    def _load_checkpoint(self) -> dict:
        """Load processing checkpoint."""
        try:
            with open(self.CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_checkpoint(self, last_processed: int):
        """Save processing checkpoint."""
        with open(self.CHECKPOINT_FILE, 'w') as f:
            json.dump({'last_processed': last_processed}, f)

def main():
    """Main entry point."""
    importer = BuildingImporter('output/osm_manifest.json')
    importer.import_all()

if __name__ == '__main__':
    main()
```

## Blender Custom Properties

Every building object will have:

```python
# Identity
obj['osm_id'] = 123456789
obj['name'] = "Bank of America Plaza"  # if available

# Type classification
obj['building_type'] = 'commercial'
obj['lod_level'] = 0

# Address (if available)
obj['addr_housenumber'] = "100"
obj['addr_street'] = "N Tryon St"
obj['addr_city'] = "Charlotte"
obj['addr_postcode'] = "28202"

# Physical
obj['height'] = 150.0  # meters (if available)
obj['building_levels'] = 35

# Organization
obj['neighborhood'] = "Uptown"
obj['block_id'] = "Block_0042"

# All other OSM tags
obj['amenity'] = "bank"  # if present
obj['operator'] = "Bank of America"  # if present
```

## Collection Structure

```
Buildings/
├── Uptown/
│   ├── Block_0001/
│   │   ├── Building_123456789
│   │   └── Building_123456790
│   ├── Block_0002/
│   └── ...
├── South_End/
├── Elizabeth/
├── Other/  # Buildings outside known neighborhoods
└── Unorganized/  # Buildings not yet assigned
```

## Batch Processing Strategy

1. **Load checkpoint** - Resume from last processed building
2. **Process batch** - Create 150 buildings
3. **Update scene** - Ensure objects are linked
4. **Save checkpoint** - Record progress
5. **Repeat** - Until all buildings processed

## Success Criteria
- [ ] All 3,739 buildings imported
- [ ] All address data preserved as custom properties
- [ ] Buildings organized into neighborhood collections
- [ ] LOD levels assigned based on importance
- [ ] Processing can resume after interruption
- [ ] Memory usage stays reasonable (<4GB)

## Estimated Effort
- Building processor: 2 hours
- Blender importer: 2-3 hours
- Collection organization: 1 hour
- Testing and batch tuning: 1-2 hours
