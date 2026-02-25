"""
Charlotte Digital Twin - Building Importer

Imports buildings from OSM manifest into Blender with:
- Batch processing for performance
- Attribute preservation (addresses, names, types)
- Neighborhood and block organization
- LOD grouping
"""

import bpy
import bmesh
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.building_processor import BuildingClassifier, NeighborhoodDetector, BlockDetector
from lib.elevation import ElevationManager


class BuildingImporter:
    """
    Imports buildings from OSM manifest into Blender.

    Features:
    - Batch processing (150 buildings per batch)
    - Checkpoint/resume support
    - Neighborhood grouping
    - Block detection
    - Attribute preservation
    """

    BATCH_SIZE = 150
    CHECKPOINT_FILE = "output/building_progress.json"

    # Reference point for Charlotte
    REF_LAT = 35.226
    REF_LON = -80.843

    def __init__(self, manifest_path: str):
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest()
        self.nodes = self.manifest['nodes']
        self.ways = self.manifest['ways']

        # Initialize processors
        self.classifier = BuildingClassifier()
        self.neighborhood_detector = NeighborhoodDetector()
        self.block_detector = BlockDetector()

        # Elevation manager
        self.elevation = ElevationManager()
        self.elevation.nodes = {
            int(nid): {
                'lat': n['lat'],
                'lon': n['lon'],
                'ele': n.get('ele'),
                'tags': n.get('tags', {}),
            }
            for nid, n in self.nodes.items()
        }
        for nid, n in self.nodes.items():
            if n.get('ele') is not None:
                self.elevation.elevations[int(nid)] = n['ele']
                self.elevation.known_points.append((n['lat'], n['lon'], n['ele']))

        # Checkpoint
        self.checkpoint = self._load_checkpoint()

    def _load_manifest(self) -> Dict:
        """Load the OSM manifest."""
        print(f"Loading manifest from {self.manifest_path}...")
        with open(self.manifest_path, 'r') as f:
            return json.load(f)

    def _load_checkpoint(self) -> Dict:
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

    def _get_buildings(self) -> List[Dict]:
        """Extract all building ways from manifest."""
        buildings = []
        for wid, way in self.ways.items():
            if way['way_type'] == 'building':
                buildings.append(way)
        return buildings

    def import_all(self):
        """Import all buildings in batches."""
        buildings = self._get_buildings()
        total = len(buildings)

        print(f"\n=== Importing {total} buildings ===")

        # Sort by priority (higher priority first)
        buildings.sort(key=lambda b: b.get('priority', 3))

        # Detect blocks
        print("Detecting building blocks...")
        blocks = self.block_detector.detect_blocks(buildings, self.nodes)
        print(f"  Found {len(blocks)} blocks")

        # Build block lookup
        building_to_block = {}
        for block_id, osm_ids in blocks.items():
            for osm_id in osm_ids:
                building_to_block[osm_id] = block_id

        # Start from checkpoint
        start = self.checkpoint.get('last_processed', 0)

        # Create collections
        self._setup_collections()

        # Process in batches
        for batch_start in range(start, total, self.BATCH_SIZE):
            batch_end = min(batch_start + self.BATCH_SIZE, total)
            batch = buildings[batch_start:batch_end]

            print(f"  Processing batch {batch_start}-{batch_end} of {total}")

            for building in batch:
                self._import_building(building, building_to_block)

            # Save checkpoint
            self._save_checkpoint(batch_end)
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        print(f"\nImported {total} buildings!")

    def _setup_collections(self):
        """Create collection hierarchy."""
        # Main Buildings collection
        buildings_coll = bpy.data.collections.get("Buildings")
        if not buildings_coll:
            buildings_coll = bpy.data.collections.new("Buildings")
            bpy.context.scene.collection.children.link(buildings_coll)

        # Neighborhood collections
        neighborhoods = list(self.neighborhood_detector.NEIGHBORHOODS.keys()) + ['Other']
        for neighborhood in neighborhoods:
            name = neighborhood.replace(' ', '_')
            coll = bpy.data.collections.get(name)
            if not coll:
                coll = bpy.data.collections.new(name)
                buildings_coll.children.link(coll)

    def _import_building(self, building: Dict, block_lookup: Dict):
        """Import a single building."""
        osm_id = building['osm_id']
        node_ids = building['node_ids']
        tags = building.get('tags', {})

        # Get node positions
        vertices = []
        for nid in node_ids:
            node = self.nodes.get(str(nid))
            if node:
                x, y = self._latlon_to_local(node['lat'], node['lon'])
                z = self.elevation.get_elevation(int(nid))
                vertices.append((x, y, z))

        if len(vertices) < 3:
            return  # Need at least 3 vertices for a face

        # Close the polygon if needed
        if vertices[0] != vertices[-1]:
            vertices.append(vertices[0])

        # Create mesh
        mesh = bpy.data.meshes.new(f"Building_{osm_id}")

        bm = bmesh.new()
        bm_verts = [bm.verts.new(v) for v in vertices[:-1]]  # Exclude closing vertex
        bm.verts.ensure_lookup_table()

        # Create face
        try:
            bm.faces.new(bm_verts)
        except ValueError:
            bm.free()
            return

        # Extrude to height
        height = self._get_building_height(building)
        if height > 0:
            geom = bmesh.ops.extrude_face_region(bm, geom=bm.faces)
            verts = [v for v in geom['geom'] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=verts, vec=(0, 0, height))

        bm.to_mesh(mesh)
        bm.free()

        # Create object
        obj_name = self._get_building_name(building)
        obj = bpy.data.objects.new(obj_name, mesh)

        # Add custom properties
        self._add_properties(obj, building, block_lookup)

        # Add to scene
        bpy.context.scene.collection.objects.link(obj)

        # Move to neighborhood collection
        self._add_to_collection(obj, building)

    def _get_building_height(self, building: Dict) -> float:
        """Get building height from tags or estimate."""
        tags = building.get('tags', {})

        # Explicit height
        if 'height' in tags:
            try:
                return float(tags['height'])
            except ValueError:
                pass

        # Building levels
        if 'building:levels' in tags:
            try:
                levels = int(tags['building:levels'])
                return levels * 3.5  # ~3.5m per level
            except ValueError:
                pass

        # Default by type
        building_type = building.get('subtype', 'yes')
        if building_type in ('commercial', 'office', 'retail'):
            return 10.0
        elif building_type == 'apartments':
            return 15.0
        elif building_type in ('house', 'terrace'):
            return 6.0
        else:
            return 5.0

    def _get_building_name(self, building: Dict) -> str:
        """Get a name for the building object."""
        tags = building.get('tags', {})

        if 'name' in tags:
            return f"Building_{tags['name'][:30]}"

        if 'addr:housenumber' in tags and 'addr:street' in tags:
            addr = f"{tags['addr:housenumber']}_{tags['addr:street'][:20]}"
            return f"Building_{addr.replace(' ', '_')}"

        return f"Building_{building['osm_id']}"

    def _add_properties(self, obj, building: Dict, block_lookup: Dict):
        """Add custom properties to building object."""
        tags = building.get('tags', {})

        # Identity
        obj['osm_id'] = building['osm_id']
        obj['building_type'] = building.get('subtype', 'yes')

        # Name
        if 'name' in tags:
            obj['building_name'] = tags['name']

        # Address
        for key in ['addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode']:
            if key in tags:
                safe_key = key.replace(':', '_')
                obj[safe_key] = tags[key]

        # Physical
        obj['height'] = self._get_building_height(building)
        if 'building:levels' in tags:
            obj['building_levels'] = int(tags['building:levels'])

        # LOD
        obj['lod_level'] = building.get('lod_hint', 2)

        # Block
        osm_id = building['osm_id']
        if osm_id in block_lookup:
            obj['block_id'] = block_lookup[osm_id]

        # All other tags
        for key, value in tags.items():
            if not key.startswith('addr:') and key not in ('name', 'building', 'height'):
                safe_key = 'tag_' + key.replace(':', '_')
                if safe_key not in obj:
                    obj[safe_key] = value

    def _add_to_collection(self, obj, building: Dict):
        """Add building to neighborhood collection."""
        # Calculate center
        node_ids = building['node_ids']
        lats = []
        lons = []
        for nid in node_ids:
            node = self.nodes.get(str(nid))
            if node:
                lats.append(node['lat'])
                lons.append(node['lon'])

        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            neighborhood = self.neighborhood_detector.assign_neighborhood(
                center_lat, center_lon
            )
        else:
            neighborhood = 'Other'

        obj['neighborhood'] = neighborhood

        # Get collection
        coll_name = neighborhood.replace(' ', '_')
        coll = bpy.data.collections.get(coll_name)

        if not coll:
            # Create under Buildings
            buildings_coll = bpy.data.collections.get("Buildings")
            coll = bpy.data.collections.new(coll_name)
            if buildings_coll:
                buildings_coll.children.link(coll)
            else:
                bpy.context.scene.collection.children.link(coll)

        # Move to collection
        for c in obj.users_collection:
            c.objects.unlink(obj)
        coll.objects.link(obj)

    def _latlon_to_local(self, lat: float, lon: float) -> Tuple[float, float]:
        """Convert lat/lon to local coordinates."""
        meters_per_deg_lat = 111000
        meters_per_deg_lon = 111000 * math.cos(math.radians(self.REF_LAT))

        x = (lon - self.REF_LON) * meters_per_deg_lon
        y = (lat - self.REF_LAT) * meters_per_deg_lat

        return (x, y)


def main():
    """Main entry point for building import."""
    import argparse

    parser = argparse.ArgumentParser(description='Import Charlotte buildings')
    parser.add_argument(
        '--manifest', '-m',
        default='output/osm_manifest.json',
        help='OSM manifest file'
    )

    args = parser.parse_args()

    # Import
    importer = BuildingImporter(args.manifest)
    importer.import_all()

    # Save
    bpy.ops.wm.save_as_mainfile(filepath='output/charlotte_buildings.blend')
    print("\nSaved to output/charlotte_buildings.blend")


if __name__ == '__main__':
    main()
