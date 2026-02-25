"""
Charlotte Digital Twin - Elevation Visualization

Creates visual representations of the elevation data to make hills
and grades clearly visible in the Blender viewport.

Features:
- Elevation profile graph (side view of race loop)
- Color-coded path markers (blue=low, red=high)
- Terrain grid with elevation
- Grade indicators at steep sections

Run in Blender:
    bpy.ops.script.python_file_run(filepath="scripts/17_elevation_viz.py")
"""

import bpy
import sys
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from lib.elevation_real import get_real_elevation_manager, RealElevationManager
    from lib.race_loop import RACE_LOOP_WAYPOINTS, Waypoint, RaceLoopManager
    ELEVATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import elevation modules: {e}")
    ELEVATION_AVAILABLE = False


def create_elevation_profile_graph(
    manager: RaceLoopManager,
    name: str = "ElevationProfile",
    scale_x: float = 0.1,  # Scale horizontal distance
    scale_z: float = 1.0,  # Scale elevation (1.0 = real, higher = exaggerated)
    offset_z: float = 0.0
) -> Optional[bpy.types.Object]:
    """
    Create a 2D graph showing elevation profile along the race loop.

    This creates a side-view visualization where:
    - X axis = distance from start
    - Z axis = elevation

    Args:
        manager: RaceLoopManager with elevation data
        name: Object name
        scale_x: Horizontal scale factor
        scale_z: Vertical scale factor (use >1 to exaggerate hills)
        offset_z: Z offset for positioning
    """
    if not bpy.context or not manager.waypoints:
        return None

    # Ensure elevation is populated
    if manager.waypoints[0].elevation == 0 and manager.elevation_manager:
        manager._populate_elevations()

    # Get base elevation for relative display
    base_elevation = min(wp.elevation for wp in manager.waypoints if wp.elevation > 0)
    base_elevation = base_elevation if base_elevation > 0 else 220.0

    # Create curve
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 4
    curve_data.fill_mode = 'BOTH'

    spline = curve_data.splines.new('POLY')

    # Add points
    points = []
    cumulative_distance = 0.0
    prev_x, prev_y = None, None

    for wp in manager.waypoints:
        if prev_x is not None:
            x, y = manager.latlon_to_local(wp.lat, wp.lon)
            dx = x - prev_x
            dy = y - prev_y
            cumulative_distance += math.sqrt(dx*dx + dy*dy)
        else:
            x, y = manager.latlon_to_local(wp.lat, wp.lon)

        # Calculate display position
        display_x = cumulative_distance * scale_x
        display_z = (wp.elevation - base_elevation) * scale_z + offset_z

        points.append((display_x, 0, display_z))
        prev_x, prev_y = x, y

    # Create spline points
    spline.points.add(len(points) - 1)
    for i, (x, y, z) in enumerate(points):
        spline.points[i].co = (x, y, z, 1.0)

    # Create object
    obj = bpy.data.objects.new(name, curve_data)

    # Store metadata
    obj["visualization_type"] = "elevation_profile"
    obj["scale_x"] = scale_x
    obj["scale_z"] = scale_z
    obj["base_elevation"] = base_elevation

    return obj


def create_color_coded_path(
    manager: RaceLoopManager,
    name: str = "ElevationPath",
    exaggeration: float = 3.0
) -> Optional[bpy.types.Object]:
    """
    Create a path with vertex colors showing elevation.

    Blue = low elevation, Red = high elevation
    """
    if not bpy.context or not manager.waypoints:
        return None

    # Ensure elevation is populated
    if manager.waypoints[0].elevation == 0 and manager.elevation_manager:
        manager._populate_elevations()

    # Get elevation range
    elevations = [wp.elevation for wp in manager.waypoints if wp.elevation > 0]
    if not elevations:
        return None

    min_ele = min(elevations)
    max_ele = max(elevations)
    ele_range = max_ele - min_ele if max_ele > min_ele else 1.0

    # Create curve
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 4

    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(len(manager.waypoints) - 1)

    base_elevation = 220.0

    for i, wp in enumerate(manager.waypoints):
        x, y = manager.latlon_to_local(wp.lat, wp.lon)
        z = (wp.elevation - base_elevation) * exaggeration if wp.elevation > 0 else 0

        point = spline.bezier_points[i]
        point.co = (x, y, z)
        point.handle_type_left = 'AUTO'
        point.handle_type_right = 'AUTO'

        # Calculate color based on elevation
        if ele_range > 0:
            t = (wp.elevation - min_ele) / ele_range
        else:
            t = 0.5

        # Store as custom property for later material use
        point.radius = t  # Hack: use radius to store color value

    obj = bpy.data.objects.new(name, curve_data)

    # Store elevation range for material
    obj["elevation_min"] = min_ele
    obj["elevation_max"] = max_ele
    obj["elevation_range"] = ele_range
    obj["exaggeration"] = exaggeration

    return obj


def create_elevation_markers(
    manager: RaceLoopManager,
    exaggeration: float = 3.0
) -> List[bpy.types.Object]:
    """
    Create markers at each waypoint showing elevation.

    Uses spheres with size/color indicating elevation.
    """
    if not bpy.context or not manager.waypoints:
        return []

    # Ensure elevation is populated
    if manager.waypoints[0].elevation == 0 and manager.elevation_manager:
        manager._populate_elevations()

    markers = []
    base_elevation = 220.0

    # Get elevation range for color coding
    elevations = [wp.elevation for wp in manager.waypoints if wp.elevation > 0]
    min_ele = min(elevations) if elevations else 220.0
    max_ele = max(elevations) if elevations else 230.0
    ele_range = max_ele - min_ele if max_ele > min_ele else 1.0

    for wp in manager.waypoints:
        x, y = manager.latlon_to_local(wp.lat, wp.lon)
        z = (wp.elevation - base_elevation) * exaggeration if wp.elevation > 0 else 0

        # Create marker
        marker = bpy.data.objects.new(f"ElevMarker_{wp.name}", None)
        marker.empty_display_type = 'SPHERE'
        marker.empty_display_size = 3.0
        marker.location = (x, y, z)

        # Calculate color value (0-1)
        if ele_range > 0:
            color_value = (wp.elevation - min_ele) / ele_range
        else:
            color_value = 0.5

        # Store metadata
        marker["elevation"] = wp.elevation
        marker["elevation_normalized"] = color_value
        marker["grade_percent"] = wp.grade_percent
        marker["waypoint_name"] = wp.name

        # Use color based on grade (for visibility)
        if abs(wp.grade_percent) > 2:
            marker.empty_display_type = 'CONE'  # Steep sections
            marker.empty_display_size = 5.0
        elif abs(wp.grade_percent) > 1:
            marker.empty_display_type = 'CUBE'  # Moderate sections
            marker.empty_display_size = 4.0

        bpy.context.collection.objects.link(marker)
        markers.append(marker)

    return markers


def create_terrain_grid(
    elevation_manager: RealElevationManager,
    center_lat: float = 35.226,
    center_lon: float = -80.843,
    size_meters: float = 1500.0,
    resolution: float = 50.0,
    exaggeration: float = 3.0
) -> Optional[bpy.types.Object]:
    """
    Create a terrain grid showing elevation across the area.

    Args:
        elevation_manager: Enhanced elevation manager
        center_lat: Center latitude
        center_lon: Center longitude
        size_meters: Size of grid in meters
        resolution: Grid cell size in meters
        exaggeration: Elevation exaggeration factor
    """
    if not bpy.context or not elevation_manager:
        return None

    # Calculate grid dimensions
    half_size = size_meters / 2
    cols = int(size_meters / resolution) + 1
    rows = int(size_meters / resolution) + 1

    # Reference for coordinate conversion
    REF_LAT = 35.226
    REF_LON = -80.843
    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * math.cos(math.radians(REF_LAT))

    # Calculate center in local coords
    center_x = (center_lon - REF_LON) * meters_per_deg_lon
    center_y = (center_lat - REF_LAT) * meters_per_deg_lat

    # Get base elevation
    base_elevation = 220.0

    # Generate vertices
    vertices = []
    colors = []  # For vertex colors

    min_ele = float('inf')
    max_ele = float('-inf')

    for row in range(rows):
        for col in range(cols):
            x = center_x - half_size + col * resolution
            y = center_y - half_size + row * resolution

            # Convert back to lat/lon
            lat = REF_LAT + y / meters_per_deg_lat
            lon = REF_LON + x / meters_per_deg_lon

            elevation = elevation_manager.get_elevation(lat, lon)
            z = (elevation - base_elevation) * exaggeration

            vertices.append((x, y, z))

            min_ele = min(min_ele, elevation)
            max_ele = max(max_ele, elevation)

    # Generate faces
    faces = []
    for row in range(rows - 1):
        for col in range(cols - 1):
            i = row * cols + col
            faces.append((i, i + 1, i + cols + 1, i + cols))

    # Create mesh
    mesh = bpy.data.meshes.new("TerrainGrid")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("TerrainGrid", mesh)

    # Store metadata
    obj["visualization_type"] = "terrain_grid"
    obj["resolution"] = resolution
    obj["exaggeration"] = exaggeration
    obj["elevation_min"] = min_ele
    obj["elevation_max"] = max_ele
    obj["grid_size"] = (cols, rows)

    return obj


def create_grade_labels(
    manager: RaceLoopManager,
    exaggeration: float = 3.0
) -> List[bpy.types.Object]:
    """
    Create text labels showing grade percentages at significant sections.
    """
    if not bpy.context or not manager.waypoints:
        return []

    labels = []
    base_elevation = 220.0

    for wp in manager.waypoints:
        # Only label significant grades
        if abs(wp.grade_percent) < 1.0:
            continue

        x, y = manager.latlon_to_local(wp.lat, wp.lon)
        z = (wp.elevation - base_elevation) * exaggeration if wp.elevation > 0 else 0

        # Create text object
        text_curve = bpy.data.curves.new(f"GradeLabel_{wp.name}", type='FONT')
        text_curve.body = f"{wp.grade_percent:+.1f}%"
        text_curve.size = 5.0
        text_curve.align_x = 'CENTER'
        text_curve.align_y = 'CENTER'

        text_obj = bpy.data.objects.new(f"GradeLabel_{wp.name}", text_curve)
        text_obj.location = (x, y, z + 5)  # Offset above path

        bpy.context.collection.objects.link(text_obj)
        labels.append(text_obj)

    return labels


def main():
    """Create all elevation visualizations."""
    print("\n" + "=" * 60)
    print("Charlotte Elevation Visualization")
    print("=" * 60)

    if not ELEVATION_AVAILABLE:
        print("ERROR: Elevation modules not available!")
        return

    # Create race loop manager
    print("\n[1/6] Initializing race loop with elevation...")
    manager = RaceLoopManager(RACE_LOOP_WAYPOINTS)

    # Create collection
    if "ElevationViz" not in bpy.data.collections:
        coll = bpy.data.collections.new("ElevationViz")
        bpy.context.scene.collection.children.link(coll)
    else:
        coll = bpy.data.collections["ElevationViz"]

    # Create elevation profile graph
    print("\n[2/6] Creating elevation profile graph...")
    profile = create_elevation_profile_graph(
        manager,
        name="ElevationProfile",
        scale_x=0.1,
        scale_z=2.0,  # 2x exaggeration
        offset_z=0
    )
    if profile:
        bpy.context.collection.objects.link(profile)
        coll.objects.link(profile)
        print(f"  Created: {profile.name}")

    # Create color-coded path
    print("\n[3/6] Creating color-coded elevation path...")
    color_path = create_color_coded_path(
        manager,
        name="ElevationPath_Coded",
        exaggeration=3.0
    )
    if color_path:
        bpy.context.collection.objects.link(color_path)
        coll.objects.link(color_path)
        print(f"  Created: {color_path.name}")
        print(f"  Elevation range: {color_path['elevation_min']:.1f}m - {color_path['elevation_max']:.1f}m")

    # Create elevation markers
    print("\n[4/6] Creating elevation markers...")
    markers = create_elevation_markers(manager, exaggeration=3.0)
    for m in markers:
        coll.objects.link(m)
    print(f"  Created {len(markers)} markers")

    # Create terrain grid
    print("\n[5/6] Creating terrain grid...")
    if manager.elevation_manager:
        terrain = create_terrain_grid(
            manager.elevation_manager,
            center_lat=35.226,
            center_lon=-80.843,
            size_meters=1000.0,
            resolution=50.0,
            exaggeration=3.0
        )
        if terrain:
            bpy.context.collection.objects.link(terrain)
            coll.objects.link(terrain)
            print(f"  Created: {terrain.name}")
            print(f"  Grid: {terrain['grid_size']}")
            print(f"  Elevation: {terrain['elevation_min']:.1f}m - {terrain['elevation_max']:.1f}m")

    # Create grade labels
    print("\n[6/6] Creating grade labels...")
    labels = create_grade_labels(manager, exaggeration=3.0)
    for l in labels:
        coll.objects.link(l)
    print(f"  Created {len(labels)} labels")

    # Print elevation summary
    print("\n" + "=" * 60)
    print("Elevation Summary")
    print("=" * 60)

    if manager.waypoints:
        elevations = [wp.elevation for wp in manager.waypoints if wp.elevation > 0]
        if elevations:
            print(f"Min elevation: {min(elevations):.1f}m")
            print(f"Max elevation: {max(elevations):.1f}m")
            print(f"Total variation: {max(elevations) - min(elevations):.1f}m")

            # Count significant grades
            steep_count = sum(1 for wp in manager.waypoints if abs(wp.grade_percent) > 2)
            moderate_count = sum(1 for wp in manager.waypoints if 1 < abs(wp.grade_percent) <= 2)

            print(f"\nGrade distribution:")
            print(f"  Steep (>2%): {steep_count} sections")
            print(f"  Moderate (1-2%): {moderate_count} sections")

    print("\n" + "=" * 60)
    print("Visualization complete!")
    print("=" * 60)

    # Save
    output_path = Path(__file__).parent.parent / 'output' / 'charlotte_elevation_viz.blend'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"\nSaved to {output_path}")


if __name__ == '__main__':
    main()
