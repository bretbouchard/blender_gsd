"""
Charlotte Digital Twin - Road Importer

Imports roads from OSM manifest into Blender with:
- Elevation handling
- Bridge separation
- Name preservation
- Type-based organization
"""

import bpy
import bmesh
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.road_classification import RoadClass, RoadClassifier, CHARLOTTE_ROAD_SPECS
from lib.elevation import ElevationManager


class RoadImporter:
    """
    Imports roads from OSM manifest into Blender.

    Features:
    - Road classification by type
    - Bridge handling with elevation
    - Name preservation for targeting
    - Collection organization by road class
    """

    # Reference point for Charlotte
    REF_LAT = 35.226
    REF_LON = -80.843

    def __init__(self, manifest_path: str):
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest()
        self.nodes = self.manifest['nodes']
        self.ways = self.manifest['ways']

        # Initialize classifier
        self.classifier = RoadClassifier()

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

    def _load_manifest(self) -> Dict:
        """Load the OSM manifest."""
        print(f"Loading manifest from {self.manifest_path}...")
        with open(self.manifest_path, 'r') as f:
            return json.load(f)

    def import_all(self):
        """Import all roads and bridges."""
        roads = self._get_roads()
        bridges = self._get_bridges()

        print(f"\n=== Importing {len(roads)} roads and {len(bridges)} bridges ===")

        # Setup collections
        self._setup_collections()

        # Import roads
        for i, road in enumerate(roads):
            if i % 500 == 0:
                print(f"  Processing road {i}/{len(roads)}")
            self._import_road(road)

        print(f"  Imported {len(roads)} roads")

        # Import bridges
        for i, bridge in enumerate(bridges):
            if i % 50 == 0:
                print(f"  Processing bridge {i}/{len(bridges)}")
            self._import_bridge(bridge)

        print(f"  Imported {len(bridges)} bridges")

        # Organize into collections
        self._organize_collections()

        print("\nRoad import complete!")

    def _get_roads(self) -> List[Dict]:
        """Extract all road ways (not bridges)."""
        roads = []
        for wid, way in self.ways.items():
            if way['way_type'] == 'road':
                roads.append(way)
        return roads

    def _get_bridges(self) -> List[Dict]:
        """Extract all bridge ways."""
        bridges = []
        for wid, way in self.ways.items():
            if way['way_type'] == 'bridge':
                bridges.append(way)
        return bridges

    def _setup_collections(self):
        """Create collection hierarchy."""
        # Main Roads collection
        roads_coll = bpy.data.collections.get("Roads")
        if not roads_coll:
            roads_coll = bpy.data.collections.new("Roads")
            bpy.context.scene.collection.children.link(roads_coll)

        # Bridges collection
        bridges_coll = bpy.data.collections.get("Bridges")
        if not bridges_coll:
            bridges_coll = bpy.data.collections.new("Bridges")
            roads_coll.children.link(bridges_coll)

        # Road class collections
        for road_class in RoadClass:
            name = road_class.value.capitalize()
            coll = bpy.data.collections.get(name)
            if not coll:
                coll = bpy.data.collections.new(name)
                roads_coll.children.link(coll)

    def _import_road(self, road: Dict):
        """Import a single road segment."""
        osm_id = road['osm_id']
        highway_type = road['subtype']
        node_ids = road['node_ids']
        tags = road.get('tags', {})

        if len(node_ids) < 2:
            return

        # Get classification
        road_class = self.classifier.classify(highway_type)
        spec = self.classifier.get_spec(road_class)

        # Get vertices with elevation
        vertices = []
        for nid in node_ids:
            node = self.nodes.get(str(nid))
            if node:
                x, y = self._latlon_to_local(node['lat'], node['lon'])
                z = self.elevation.get_elevation(int(nid))
                vertices.append((x, y, z))

        if len(vertices) < 2:
            return

        # Get width
        width = float(tags.get('width', spec.width_meters))

        # Create road mesh
        obj = self._create_road_mesh(
            f"Road_{osm_id}",
            vertices,
            width
        )

        if obj:
            self._add_properties(obj, road, road_class, spec)

    def _import_bridge(self, bridge: Dict):
        """Import a bridge segment with elevated geometry."""
        osm_id = bridge['osm_id']
        highway_type = bridge['subtype']
        node_ids = bridge['node_ids']
        tags = bridge.get('tags', {})

        if len(node_ids) < 2:
            return

        # Get classification
        road_class = self.classifier.classify(highway_type)
        spec = self.classifier.get_spec(road_class)

        # Get vertices with bridge elevation
        vertices = []
        layer = int(tags.get('layer', '1'))

        for nid in node_ids:
            node = self.nodes.get(str(nid))
            if node:
                x, y = self._latlon_to_local(node['lat'], node['lon'])
                base_z = self.elevation.get_elevation(int(nid))
                # Add clearance based on layer
                bridge_z = base_z + (5.5 * layer)
                vertices.append((x, y, bridge_z))

        if len(vertices) < 2:
            return

        # Get width
        width = float(tags.get('width', spec.width_meters))

        # Create bridge mesh
        obj = self._create_road_mesh(
            f"Bridge_{osm_id}",
            vertices,
            width
        )

        if obj:
            self._add_properties(obj, bridge, road_class, spec)
            obj['is_bridge'] = True
            obj['bridge_layer'] = layer

    def _create_road_mesh(
        self,
        name: str,
        vertices: List[Tuple[float, float, float]],
        width: float
    ) -> bpy.types.Object:
        """Create a road ribbon mesh from vertices."""
        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()

        if len(vertices) < 2:
            bm.free()
            return None

        # For each segment, create a quad
        faces_created = 0

        for i in range(len(vertices) - 1):
            v1 = vertices[i]
            v2 = vertices[i + 1]

            # Calculate direction
            dx = v2[0] - v1[0]
            dy = v2[1] - v1[1]
            length = math.sqrt(dx * dx + dy * dy)

            if length < 0.01:
                continue

            # Normalize direction
            dx /= length
            dy /= length

            # Perpendicular (for width)
            perp_x = -dy
            perp_y = dx

            # Half width
            hw = width / 2

            # Create quad vertices
            p1 = (v1[0] + perp_x * hw, v1[1] + perp_y * hw, v1[2])
            p2 = (v1[0] - perp_x * hw, v1[1] - perp_y * hw, v1[2])
            p3 = (v2[0] - perp_x * hw, v2[1] - perp_y * hw, v2[2])
            p4 = (v2[0] + perp_x * hw, v2[1] + perp_y * hw, v2[2])

            # Add vertices
            bv1 = bm.verts.new(p1)
            bv2 = bm.verts.new(p2)
            bv3 = bm.verts.new(p3)
            bv4 = bm.verts.new(p4)

            bm.verts.ensure_lookup_table()

            # Create face
            try:
                face = bm.faces.new([bv1, bv2, bv3, bv4])
                faces_created += 1
            except ValueError:
                pass

        if faces_created == 0:
            bm.free()
            return None

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)

        return obj

    def _add_properties(self, obj, road: Dict, road_class: RoadClass, spec):
        """Add custom properties to road object."""
        tags = road.get('tags', {})

        # Identity
        obj['osm_id'] = road['osm_id']
        obj['road_class'] = road_class.value
        obj['highway_type'] = road['subtype']

        # Name (critical for targeting)
        if 'name' in tags:
            obj['road_name'] = tags['name']
            # Update object name
            safe_name = tags['name'].replace(' ', '_').replace('/', '_')[:50]
            obj.name = f"Road_{safe_name}"

        # Reference number (for highways)
        if 'ref' in tags:
            obj['road_ref'] = tags['ref']

        # Physical properties
        obj['width'] = float(tags.get('width', spec.width_meters))
        obj['lanes'] = int(tags.get('lanes', spec.lanes))

        # Other tags
        for key in ['surface', 'oneway', 'maxspeed', 'layer']:
            if key in tags:
                obj[f'tag_{key}'] = tags[key]

    def _organize_collections(self):
        """Organize roads into collections by type."""
        roads_coll = bpy.data.collections.get("Roads")
        bridges_coll = bpy.data.collections.get("Bridges")

        # Get all road objects
        road_objects = [
            obj for obj in bpy.context.scene.objects
            if obj.get('road_class')
        ]

        for obj in road_objects:
            # Determine target collection
            if obj.get('is_bridge'):
                target = bridges_coll
            else:
                class_name = obj['road_class'].capitalize()
                target = bpy.data.collections.get(class_name, roads_coll)

            # Move to collection
            for coll in obj.users_collection:
                coll.objects.unlink(obj)

            if target:
                target.objects.link(obj)

    def _latlon_to_local(self, lat: float, lon: float) -> Tuple[float, float]:
        """Convert lat/lon to local coordinates."""
        meters_per_deg_lat = 111000
        meters_per_deg_lon = 111000 * math.cos(math.radians(self.REF_LAT))

        x = (lon - self.REF_LON) * meters_per_deg_lon
        y = (lat - self.REF_LAT) * meters_per_deg_lat

        return (x, y)


def main():
    """Main entry point for road import."""
    import argparse

    parser = argparse.ArgumentParser(description='Import Charlotte roads')
    parser.add_argument(
        '--manifest', '-m',
        default='output/osm_manifest.json',
        help='OSM manifest file'
    )

    args = parser.parse_args()

    # Import
    importer = RoadImporter(args.manifest)
    importer.import_all()

    print("\nRoad import complete!")


if __name__ == '__main__':
    main()
