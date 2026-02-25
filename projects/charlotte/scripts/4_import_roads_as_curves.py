"""
Charlotte Digital Twin - Road Curve Importer

Imports roads from OSM manifest as Curve objects for use with
Geometry Nodes road builder system.

Each road becomes a separate curve with attributes for:
- Road class, width, lanes
- Street name
- Bridge status
- Elevation data
"""

import bpy
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.road_classification import RoadClass, RoadClassifier, CHARLOTTE_ROAD_SPECS
from lib.elevation import ElevationManager


class RoadCurveImporter:
    """
    Imports roads from OSM manifest as Curve objects.

    Curves are optimized for Geometry Nodes processing:
    - Clean splines from OSM node paths
    - Custom properties for road attributes
    - Named attributes for per-point data (elevation, width)
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
        """Import all roads and bridges as curves."""
        roads = self._get_roads()
        bridges = self._get_bridges()

        print(f"\n=== Importing {len(roads)} roads and {len(bridges)} bridges as curves ===")

        # Setup collections
        self._setup_collections()

        # Import roads
        road_count = 0
        for road in roads:
            if self._import_road_curve(road):
                road_count += 1
            if road_count % 1000 == 0:
                print(f"  Imported {road_count} road curves...")

        print(f"  Imported {road_count} road curves")

        # Import bridges
        bridge_count = 0
        for bridge in bridges:
            if self._import_road_curve(bridge, is_bridge=True):
                bridge_count += 1

        print(f"  Imported {bridge_count} bridge curves")

        # Organize into collections
        self._organize_collections()

        print("\nRoad curve import complete!")

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
        roads_coll = bpy.data.collections.get("Road_Curves")
        if not roads_coll:
            roads_coll = bpy.data.collections.new("Road_Curves")
            bpy.context.scene.collection.children.link(roads_coll)

        # Road class collections
        for road_class in RoadClass:
            name = f"{road_class.value.capitalize()}_Curves"
            coll = bpy.data.collections.get(name)
            if not coll:
                coll = bpy.data.collections.new(name)
                roads_coll.children.link(coll)

        # Bridges collection
        bridges_coll = bpy.data.collections.get("Bridge_Curves")
        if not bridges_coll:
            bridges_coll = bpy.data.collections.new("Bridge_Curves")
            roads_coll.children.link(bridges_coll)

    def _import_road_curve(self, road: Dict, is_bridge: bool = False) -> bool:
        """Import a single road as a curve object."""
        osm_id = road['osm_id']
        highway_type = road['subtype']
        node_ids = road['node_ids']
        tags = road.get('tags', {})

        if len(node_ids) < 2:
            return False

        # Get classification
        road_class = self.classifier.classify(highway_type)
        spec = self.classifier.get_spec(road_class)

        # Get points with elevation
        points = []
        for nid in node_ids:
            node = self.nodes.get(str(nid))
            if node:
                x, y = self._latlon_to_local(node['lat'], node['lon'])
                z = self.elevation.get_elevation(int(nid))

                # Add bridge elevation offset
                if is_bridge:
                    layer = int(tags.get('layer', '1'))
                    z += 5.5 * layer

                points.append((x, y, z))

        if len(points) < 2:
            return False

        # Create curve
        curve_data = bpy.data.curves.new(f"Road_{osm_id}", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 2  # Lower resolution for performance

        # Create spline
        spline = curve_data.splines.new('POLY')
        spline.points.add(len(points) - 1)  # Add N-1 points (1 exists by default)

        # Set point positions
        for i, (x, y, z) in enumerate(points):
            spline.points[i].co = (x, y, z, 1.0)  # W=1 for homogeneous coords

        # Create object
        obj_name = self._get_curve_name(road, road_class)
        obj = bpy.data.objects.new(obj_name, curve_data)

        # Add custom properties
        self._add_properties(obj, road, road_class, spec, is_bridge)

        # Create named attributes for geometry nodes
        self._create_attributes(curve_data, road, points)

        # Link to scene
        bpy.context.scene.collection.objects.link(obj)

        return True

    def _get_curve_name(self, road: Dict, road_class: RoadClass) -> str:
        """Get a name for the curve object."""
        tags = road.get('tags', {})

        if 'name' in tags:
            safe_name = tags['name'].replace(' ', '_').replace('/', '_')[:40]
            return f"Road_{safe_name}"

        if 'ref' in tags:
            return f"Road_{tags['ref']}"

        return f"Road_{road['osm_id']}"

    def _add_properties(
        self,
        obj,
        road: Dict,
        road_class: RoadClass,
        spec,
        is_bridge: bool
    ):
        """Add custom properties to curve object."""
        tags = road.get('tags', {})

        # Identity
        obj['osm_id'] = road['osm_id']
        obj['road_class'] = road_class.value
        obj['highway_type'] = road['subtype']

        # Name (critical for targeting)
        if 'name' in tags:
            obj['road_name'] = tags['name']

        if 'ref' in tags:
            obj['road_ref'] = tags['ref']

        # Physical properties
        width = float(tags.get('width', spec.width_meters))
        obj['road_width'] = width
        obj['lanes'] = int(tags.get('lanes', spec.lanes))
        obj['surface'] = tags.get('surface', 'asphalt')

        # Bridge properties
        obj['is_bridge'] = is_bridge
        if is_bridge:
            obj['bridge_layer'] = int(tags.get('layer', '1'))

        # LOD hint
        obj['lod_hint'] = road.get('lod_hint', 2)

        # Geometry nodes parameters
        obj['gn_width'] = width
        obj['gn_lanes'] = int(tags.get('lanes', spec.lanes))
        obj['gn_has_sidewalk'] = spec.has_sidewalk
        obj['gn_has_markings'] = spec.has_markings

        # Road class as int for geometry nodes selection
        class_to_int = {
            RoadClass.HIGHWAY: 0,
            RoadClass.ARTERIAL: 1,
            RoadClass.COLLECTOR: 2,
            RoadClass.LOCAL: 3,
            RoadClass.SERVICE: 4,
            RoadClass.PEDESTRIAN: 5,
        }
        obj['gn_road_class'] = class_to_int.get(road_class, 3)

    def _create_attributes(self, curve_data, road: Dict, points: List[Tuple]):
        """Create named attributes for geometry nodes."""
        # Elevation attribute (per control point)
        # This allows geometry nodes to access elevation data

        # Note: Blender curve point attributes are limited
        # For more complex attributes, we'd use mesh instead
        # For now, elevation is baked into point positions

        pass  # Curve positions already include elevation

    def _organize_collections(self):
        """Organize curves into collections by type."""
        roads_coll = bpy.data.collections.get("Road_Curves")
        bridges_coll = bpy.data.collections.get("Bridge_Curves")

        # Get all road curve objects
        curve_objects = [
            obj for obj in bpy.context.scene.objects
            if obj.type == 'CURVE' and obj.get('road_class')
        ]

        for obj in curve_objects:
            # Determine target collection
            if obj.get('is_bridge'):
                target = bridges_coll
            else:
                class_name = f"{obj['road_class'].capitalize()}_Curves"
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
    """Main entry point for road curve import."""
    import argparse

    parser = argparse.ArgumentParser(description='Import Charlotte roads as curves')
    parser.add_argument(
        '--manifest', '-m',
        default='output/osm_manifest.json',
        help='OSM manifest file'
    )

    args = parser.parse_args()

    # Import
    importer = RoadCurveImporter(args.manifest)
    importer.import_all()

    # Stats
    curve_count = len([o for o in bpy.context.scene.objects if o.type == 'CURVE'])
    print(f"\nTotal curves in scene: {curve_count}")

    print("\nRoad curve import complete!")


if __name__ == '__main__':
    main()
