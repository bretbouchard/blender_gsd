"""
Charlotte Digital Twin - Build Map with Real Elevations

Rebuilds the Charlotte map with accurate SRTM elevation data:
- Applies real elevations to all road curves
- Generates terrain mesh with correct heights
- Creates elevation-based materials
- Sets up driver camera view

Run in Blender:
    bpy.ops.script.python_file_run(filepath="scripts/18_build_elevation_map.py")
"""

import bpy
import sys
import math
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from lib.elevation_enhanced import create_enhanced_elevation_manager, EnhancedElevationManager
    ELEVATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import elevation modules: {e}")
    ELEVATION_AVAILABLE = False

try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


class ElevationMapBuilder:
    """
    Builds the Charlotte map with accurate real-world elevations.

    Uses SRTM 30m data from OpenTopoData API for realistic terrain.
    """

    # Reference point for Charlotte
    REF_LAT = 35.226
    REF_LON = -80.843
    BASE_ELEVATION = 220.0  # Base for relative Z coordinates

    def __init__(self):
        self.elevation_manager = None
        if ELEVATION_AVAILABLE:
            self.elevation_manager = create_enhanced_elevation_manager()
            print(f"Elevation manager loaded with {len(self.elevation_manager.known_points)} points")

    def latlon_to_local(self, lat: float, lon: float) -> Tuple[float, float]:
        """Convert lat/lon to local scene coordinates (meters)."""
        meters_per_deg_lat = 111000
        meters_per_deg_lon = 111000 * math.cos(math.radians(self.REF_LAT))

        x = (lon - self.REF_LON) * meters_per_deg_lon
        y = (lat - self.REF_LAT) * meters_per_deg_lat

        return (x, y)

    def get_elevation_z(self, lat: float, lon: float) -> float:
        """Get Z coordinate for a lat/lon (relative to base elevation)."""
        if self.elevation_manager:
            elevation = self.elevation_manager.get_elevation(lat, lon)
            return elevation - self.BASE_ELEVATION
        return 0.0

    def update_road_curves(self):
        """Update all existing road curves with correct elevations."""
        if not BLENDER_AVAILABLE:
            print("Blender not available")
            return

        print("\n" + "=" * 60)
        print("Updating Road Curves with Real Elevations")
        print("=" * 60)

        # Find all road curves
        road_curves = [
            obj for obj in bpy.context.scene.objects
            if obj.type == 'CURVE' and obj.get('road_class')
        ]

        print(f"Found {len(road_curves)} road curves to update")

        updated = 0
        for obj in road_curves:
            if self._update_curve_elevation(obj):
                updated += 1
            if updated % 500 == 0:
                print(f"  Updated {updated} curves...")

        print(f"  Updated {updated} road curves with elevation data")

    def _update_curve_elevation(self, obj) -> bool:
        """Update a single curve object with elevation data."""
        if not obj.data or not hasattr(obj.data, 'splines'):
            return False

        # Get the first spline
        if not obj.data.splines:
            return False

        spline = obj.data.splines[0]

        # Update each point with elevation
        for point in spline.points:
            x, y = point.co.x, point.co.y

            # Convert back to lat/lon (approximate)
            lat = self.REF_LAT + y / 111000
            lon = self.REF_LON + x / (111000 * math.cos(math.radians(self.REF_LAT)))

            # Get elevation
            z = self.get_elevation_z(lat, lon)

            # Update point
            point.co.z = z

        return True

    def create_terrain_mesh(
        self,
        center_lat: float = 35.226,
        center_lon: float = -80.843,
        size_meters: float = 2000.0,
        resolution: float = 25.0
    ) -> Optional[bpy.types.Object]:
        """
        Create a terrain mesh with accurate elevations.

        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            size_meters: Size of terrain grid in meters
            resolution: Grid cell size in meters
        """
        if not BLENDER_AVAILABLE or not self.elevation_manager:
            return None

        print(f"\nCreating terrain mesh: {size_meters}m x {size_meters}m, resolution {resolution}m")

        # Calculate grid dimensions
        half_size = size_meters / 2
        cols = int(size_meters / resolution) + 1
        rows = int(size_meters / resolution) + 1

        # Calculate center in local coords
        center_x, center_y = self.latlon_to_local(center_lat, center_lon)

        # Generate vertices
        vertices = []
        min_z = float('inf')
        max_z = float('-inf')

        for row in range(rows):
            for col in range(cols):
                x = center_x - half_size + col * resolution
                y = center_y - half_size + row * resolution

                # Convert back to lat/lon
                lat = self.REF_LAT + y / 111000
                lon = self.REF_LON + x / (111000 * math.cos(math.radians(self.REF_LAT)))

                # Get elevation
                z = self.get_elevation_z(lat, lon)
                vertices.append((x, y, z))

                min_z = min(min_z, z)
                max_z = max(max_z, z)

        print(f"  Generated {len(vertices)} vertices")
        print(f"  Elevation range: {min_z:.1f}m to {max_z:.1f}m (relative)")

        # Generate faces
        faces = []
        for row in range(rows - 1):
            for col in range(cols - 1):
                i = row * cols + col
                faces.append((i, i + 1, i + cols + 1, i + cols))

        # Create mesh
        mesh = bpy.data.meshes.new("CharlotteTerrain")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()

        # Create object
        obj = bpy.data.objects.new("CharlotteTerrain", mesh)

        # Store metadata
        obj["terrain_type"] = "elevation_grid"
        obj["resolution"] = resolution
        obj["grid_size"] = (cols, rows)
        obj["elevation_min"] = min_z + self.BASE_ELEVATION
        obj["elevation_max"] = max_z + self.BASE_ELEVATION
        obj["base_elevation"] = self.BASE_ELEVATION

        # Link to scene
        bpy.context.collection.objects.link(obj)

        print(f"  Created terrain mesh: {obj.name}")

        return obj

    def create_elevation_markers(self) -> List[bpy.types.Object]:
        """Create markers at key elevation points for reference."""
        if not BLENDER_AVAILABLE or not self.elevation_manager:
            return []

        markers = []

        # Key points to mark
        key_points = [
            ("Trade & Tryon (Highest)", 35.2273, -80.8431, "The Hill"),
            ("Church & MLK (Start)", 35.2269, -80.8455, "Start/Finish"),
            ("I-277 @ College (Lowest)", 35.2231, -80.8648, "Low Point"),
            ("Trade & Caldwell", 35.2273, -80.8397, "End of Drop"),
            ("College & E 5th", 35.2298, -80.8689, "Uptown East"),
        ]

        for name, lat, lon, label in key_points:
            x, y = self.latlon_to_local(lat, lon)
            z = self.get_elevation_z(lat, lon)

            # Create marker
            marker = bpy.data.objects.new(f"ElevMarker_{name.replace(' ', '_')}", None)
            marker.empty_display_type = 'SPHERE'
            marker.empty_display_size = 10.0
            marker.location = (x, y, z + 5)  # Offset above ground

            # Store metadata
            marker["elevation"] = z + self.BASE_ELEVATION
            marker["label"] = label
            marker["lat"] = lat
            marker["lon"] = lon

            bpy.context.collection.objects.link(marker)
            markers.append(marker)

        print(f"Created {len(markers)} elevation markers")
        return markers

    def create_elevation_profile_line(self) -> Optional[bpy.types.Object]:
        """Create a 3D line showing the race loop elevation profile."""
        if not BLENDER_AVAILABLE:
            return None

        # Race loop key points
        waypoints = [
            ("Start", 35.2269, -80.8455),
            ("Church & Morehead", 35.2221, -80.8482),
            ("I-277 Entry", 35.2175, -80.8583),
            ("I-277 @ College", 35.2231, -80.8648),
            ("College & E 5th", 35.2298, -80.8689),
            ("E 5th & Caldwell", 35.2318, -80.8653),
            ("Caldwell & Trade", 35.2336, -80.8620),
            ("Trade & Church", 35.2309, -80.8478),
            ("Finish", 35.2269, -80.8455),
        ]

        # Create curve
        curve_data = bpy.data.curves.new("RaceLoopElevation", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 4

        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(len(waypoints) - 1)

        for i, (name, lat, lon) in enumerate(waypoints):
            x, y = self.latlon_to_local(lat, lon)
            z = self.get_elevation_z(lat, lon)

            point = spline.bezier_points[i]
            point.co = (x, y, z)
            point.handle_type_left = 'AUTO'
            point.handle_type_right = 'AUTO'

        obj = bpy.data.objects.new("RaceLoopElevation", curve_data)
        obj["path_type"] = "race_loop_profile"
        obj["base_elevation"] = self.BASE_ELEVATION

        bpy.context.collection.objects.link(obj)

        print("Created race loop elevation profile")
        return obj

    def setup_camera_at_start(self, vehicle_type: str = 'sports_car') -> Optional[bpy.types.Object]:
        """Set up driver camera at race start position."""
        if not BLENDER_AVAILABLE:
            return None

        # Start position (Church & MLK)
        start_lat, start_lon = 35.2269, -80.8455
        x, y = self.latlon_to_local(start_lat, start_lon)
        z = self.get_elevation_z(start_lat, start_lon)

        # Driver eye height (sports car = 1.08m)
        eye_heights = {
            'sports_car': 1.08,
            'sedan': 1.15,
            'suv': 1.45,
        }
        eye_height = eye_heights.get(vehicle_type, 1.08)

        # Create camera
        cam_data = bpy.data.cameras.new("DriverCamera_Data")
        cam_obj = bpy.data.objects.new("DriverCamera", cam_data)

        # Position at driver eye height
        cam_obj.location = (x, y, z + eye_height)

        # Look toward next waypoint (Church & Morehead)
        next_lat, next_lon = 35.2221, -80.8482
        next_x, next_y = self.latlon_to_local(next_lat, next_lon)

        # Calculate rotation
        dx = next_x - x
        dy = next_y - y
        rotation = math.atan2(dy, dx)

        cam_obj.rotation_euler = (math.radians(80), 0, rotation)

        # Camera settings
        cam_data.lens = 28
        cam_data.angle = math.radians(75)
        cam_data.clip_start = 0.1
        cam_data.clip_end = 2000.0

        # Store metadata
        cam_obj["camera_type"] = "driver_view"
        cam_obj["vehicle_type"] = vehicle_type
        cam_obj["eye_height"] = eye_height
        cam_obj["ground_elevation"] = z + self.BASE_ELEVATION

        bpy.context.collection.objects.link(cam_obj)
        bpy.context.scene.camera = cam_obj

        print(f"Set up driver camera at ({x:.1f}, {y:.1f}, {z + eye_height:.1f})")
        print(f"  Ground elevation: {z + self.BASE_ELEVATION:.1f}m")
        print(f"  Eye height: {eye_height}m")

        return cam_obj

    def build_all(self):
        """Build complete elevation map."""
        print("\n" + "=" * 60)
        print("CHARLOTTE ELEVATION MAP BUILDER")
        print("=" * 60)

        if not BLENDER_AVAILABLE:
            print("ERROR: This script must run in Blender")
            return

        if not self.elevation_manager:
            print("ERROR: Elevation manager not available")
            return

        # Create collection
        if "ElevationMap" not in bpy.data.collections:
            coll = bpy.data.collections.new("ElevationMap")
            bpy.context.scene.collection.children.link(coll)
        else:
            coll = bpy.data.collections["ElevationMap"]

        # 1. Update road curves
        self.update_road_curves()

        # 2. Create terrain mesh
        terrain = self.create_terrain_mesh(
            center_lat=35.226,
            center_lon=-80.843,
            size_meters=2000.0,
            resolution=25.0
        )
        if terrain:
            coll.objects.link(terrain)

        # 3. Create elevation markers
        markers = self.create_elevation_markers()
        for m in markers:
            coll.objects.link(m)

        # 4. Create race loop profile
        profile = self.create_elevation_profile_line()
        if profile:
            coll.objects.link(profile)

        # 5. Setup camera
        camera = self.setup_camera_at_start()
        if camera:
            coll.objects.link(camera)

        print("\n" + "=" * 60)
        print("ELEVATION MAP BUILD COMPLETE")
        print("=" * 60)
        print(f"\nCreated:")
        print(f"  - Updated road curves with elevation")
        print(f"  - Terrain mesh (2000m x 2000m)")
        print(f"  - Elevation markers")
        print(f"  - Race loop profile")
        print(f"  - Driver camera at start")

        # Print elevation summary
        if self.elevation_manager:
            stats = self.elevation_manager.get_elevation_stats()
            print(f"\nElevation Statistics:")
            print(f"  Known points: {stats.get('point_count', 0)}")
            print(f"  Range: {stats.get('min_elevation', 0):.0f}m - {stats.get('max_elevation', 0):.0f}m")
            print(f"  Variation: {stats.get('range', 0):.0f}m")


def main():
    """Main entry point."""
    builder = ElevationMapBuilder()
    builder.build_all()


if __name__ == '__main__':
    main()
