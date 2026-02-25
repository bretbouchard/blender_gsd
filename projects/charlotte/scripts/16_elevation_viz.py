"""
Charlotte Digital Twin - Elevation Visualization & Verification

This script:
1. Analyzes elevation data in the scene
2. Creates elevation-aware race loop paths
3. Exaggerates elevation for visual verification
4. Reports elevation changes along the race route

The elevation data in Charlotte ranges from ~188m to ~241m (53m variation).
For driving feel, these subtle changes ARE important - they affect:
- Acceleration on uphill sections
- Braking on downhill
- Sight lines over crests
- Corner entry speeds
"""

import bpy
import sys
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.elevation import ElevationManager, create_elevation_manager
from lib.race_loop import RACE_LOOP_WAYPOINTS, Waypoint


@dataclass
class ElevationProfile:
    """Elevation profile for a route segment."""
    waypoint_name: str
    lat: float
    lon: float
    elevation: float
    distance_from_start: float
    grade_percent: float  # Grade from previous point
    cumulative_climb: float  # Total uphill meters


def analyze_race_loop_elevation() -> List[ElevationProfile]:
    """
    Analyze elevation changes along the race loop.

    Returns elevation profile with grades and cumulative climb.
    """
    # Load elevation data
    osm_path = Path(__file__).parent.parent / 'maps' / 'charlotte-merged.osm'

    if not osm_path.exists():
        print(f"ERROR: OSM file not found at {osm_path}")
        return []

    elevation = create_elevation_manager(str(osm_path))

    profile = []
    cumulative_climb = 0.0
    total_distance = 0.0

    # Reference for coordinate conversion
    REF_LAT = 35.226
    REF_LON = -80.843

    prev_x, prev_y, prev_z = None, None, None

    for i, wp in enumerate(RACE_LOOP_WAYPOINTS):
        # Get elevation for this waypoint
        # Find nearest node in elevation data
        nearest_node = None
        min_dist = float('inf')

        for node_id, node_data in elevation.nodes.items():
            dist = math.sqrt(
                (node_data['lat'] - wp.lat)**2 +
                (node_data['lon'] - wp.lon)**2
            )
            if dist < min_dist:
                min_dist = dist
                nearest_node = node_id

        if nearest_node:
            z = elevation.get_elevation(nearest_node)
        else:
            # Interpolate
            z = elevation.interpolate_elevation(wp.lat, wp.lon)

        # Calculate distance from previous
        meters_per_deg_lat = 111000
        meters_per_deg_lon = 111000 * math.cos(math.radians(REF_LAT))

        x = (wp.lon - REF_LON) * meters_per_deg_lon
        y = (wp.lat - REF_LAT) * meters_per_deg_lat

        if prev_x is not None:
            dx = x - prev_x
            dy = y - prev_y
            horizontal_dist = math.sqrt(dx*dx + dy*dy)
            total_distance += horizontal_dist

            # Calculate grade
            dz = z - prev_z
            grade = (dz / horizontal_dist * 100) if horizontal_dist > 0 else 0

            # Track cumulative climb (only uphill)
            if dz > 0:
                cumulative_climb += dz
        else:
            grade = 0

        profile.append(ElevationProfile(
            waypoint_name=wp.name,
            lat=wp.lat,
            lon=wp.lon,
            elevation=z,
            distance_from_start=total_distance,
            grade_percent=grade,
            cumulative_climb=cumulative_climb,
        ))

        prev_x, prev_y, prev_z = x, y, z

    return profile


def print_elevation_report(profile: List[ElevationProfile]):
    """Print detailed elevation analysis."""
    print("\n" + "=" * 70)
    print("CHARLOTTE RACE LOOP - ELEVATION ANALYSIS")
    print("=" * 70)

    if not profile:
        print("No elevation data available!")
        return

    min_ele = min(p.elevation for p in profile)
    max_ele = max(p.elevation for p in profile)
    total_climb = profile[-1].cumulative_climb if profile else 0
    total_dist = profile[-1].distance_from_start if profile else 0

    print(f"\nSUMMARY:")
    print(f"  Total distance: {total_dist/1000:.2f} km")
    print(f"  Elevation range: {min_ele:.1f}m - {max_ele:.1f}m ({max_ele-min_ele:.1f}m variation)")
    print(f"  Total climb: {total_climb:.1f}m")

    print(f"\nWAYPOINT DETAILS:")
    print(f"{'Waypoint':<20} {'Elev(m)':<10} {'Dist(m)':<10} {'Grade%':<10} {'Climb(m)':<10}")
    print("-" * 70)

    for p in profile:
        grade_str = f"{p.grade_percent:+.1f}%" if abs(p.grade_percent) > 0.1 else "~flat"
        print(f"{p.waypoint_name:<20} {p.elevation:<10.1f} {p.distance_from_start:<10.0f} {grade_str:<10} {p.cumulative_climb:<10.1f}")

    # Find notable sections
    print(f"\nNOTABLE ELEVATION CHANGES:")

    for i, p in enumerate(profile):
        if abs(p.grade_percent) > 3.0:
            direction = "UPHILL" if p.grade_percent > 0 else "DOWNHILL"
            print(f"  {p.waypoint_name}: {direction} {abs(p.grade_percent):.1f}% grade")

    print("\n" + "=" * 70)


def create_elevation_visualization(
    profile: List[ElevationProfile],
    exaggeration: float = 10.0
) -> Optional[bpy.types.Object]:
    """
    Create a 3D visualization of the elevation profile.

    Args:
        profile: Elevation profile data
        exaggeration: Multiply elevation changes for visibility

    Returns:
        Curve object showing elevation profile
    """
    if not bpy.context or not profile:
        return None

    # Create curve
    curve_data = bpy.data.curves.new("ElevationProfile_Viz", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 4

    spline = curve_data.splines.new('POLY')
    spline.points.add(len(profile) - 1)

    # Reference elevation (subtract to show relative changes)
    base_elevation = min(p.elevation for p in profile)

    for i, p in enumerate(profile):
        # Exaggerate elevation for visibility
        relative_elevation = (p.elevation - base_elevation) * exaggeration

        # Scale distance for visualization
        x = p.distance_from_start * 0.1  # Scale down for display
        y = 0
        z = relative_elevation

        spline.points[i].co = (x, y, z, 1.0)

    obj = bpy.data.objects.new("ElevationProfile_Viz", curve_data)
    bpy.context.collection.objects.link(obj)

    # Add label at start
    obj["base_elevation"] = base_elevation
    obj["exaggeration"] = exaggeration
    obj["total_climb"] = profile[-1].cumulative_climb

    return obj


def update_race_loop_with_elevation(
    profile: List[ElevationProfile],
    exaggeration: float = 1.0
) -> Optional[bpy.types.Object]:
    """
    Create the race loop path with actual elevation data.

    Args:
        profile: Elevation profile from analyze_race_loop_elevation()
        exaggeration: Multiply elevation changes (1.0 = real, 5.0 = visible)

    Returns:
        Curve object for the race path
    """
    if not bpy.context or not profile:
        return None

    # Reference point
    REF_LAT = 35.226
    REF_LON = -80.843

    # Base elevation to make relative
    base_elevation = min(p.elevation for p in profile)

    # Create curve
    curve_data = bpy.data.curves.new("RaceLoop_Elevated", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 4

    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(len(profile) - 1)

    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * math.cos(math.radians(REF_LAT))

    for i, p in enumerate(profile):
        # Convert to local coordinates
        x = (p.lon - REF_LON) * meters_per_deg_lon
        y = (p.lat - REF_LAT) * meters_per_deg_lat

        # Apply elevation with optional exaggeration
        z = (p.elevation - base_elevation) * exaggeration

        point = spline.bezier_points[i]
        point.co = (x, y, z)
        point.handle_type_left = 'AUTO'
        point.handle_type_right = 'AUTO'

    obj = bpy.data.objects.new("RaceLoop_Elevated", curve_data)
    obj["elevation_base"] = base_elevation
    obj["elevation_range"] = max(p.elevation for p in profile) - base_elevation
    obj["exaggeration"] = exaggeration

    bpy.context.collection.objects.link(obj)

    return obj


def create_road_elevation_markers(
    profile: List[ElevationProfile],
    exaggeration: float = 1.0
) -> List[bpy.types.Object]:
    """
    Create markers at each waypoint showing elevation.

    These help visualize where the road goes up/down.
    """
    if not bpy.context or not profile:
        return []

    markers = []
    base_elevation = min(p.elevation for p in profile)

    REF_LAT = 35.226
    REF_LON = -80.843
    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * math.cos(math.radians(REF_LAT))

    for p in profile:
        x = (p.lon - REF_LON) * meters_per_deg_lon
        y = (p.lat - REF_LAT) * meters_per_deg_lat
        z = (p.elevation - base_elevation) * exaggeration

        # Create marker
        empty = bpy.data.objects.new(f"ElevMarker_{p.waypoint_name}", None)
        empty.empty_display_type = 'SPHERE'
        empty.empty_display_size = 5.0
        empty.location = (x, y, z)

        # Color based on grade
        if p.grade_percent > 3:
            empty.empty_display_type = 'CONE'  # Uphill
        elif p.grade_percent < -3:
            empty.empty_display_type = 'CUBE'  # Downhill

        empty["elevation"] = p.elevation
        empty["grade_percent"] = p.grade_percent
        empty["cumulative_climb"] = p.cumulative_climb

        bpy.context.collection.objects.link(empty)
        markers.append(empty)

    return markers


def main():
    """Main function - analyze and visualize elevation."""
    print("\n" + "=" * 70)
    print("CHARLOTTE ELEVATION ANALYSIS")
    print("=" * 70)

    # Analyze elevation
    print("\n[1/4] Analyzing race loop elevation...")
    profile = analyze_race_loop_elevation()

    if not profile:
        print("ERROR: Could not load elevation data!")
        return

    # Print report
    print_elevation_report(profile)

    # Create visualizations
    print("\n[2/4] Creating elevation profile visualization...")
    viz = create_elevation_visualization(profile, exaggeration=10.0)
    if viz:
        print(f"  Created: {viz.name}")

    print("\n[3/4] Creating elevated race loop path...")
    elevated_path = update_race_loop_with_elevation(profile, exaggeration=1.0)
    if elevated_path:
        print(f"  Created: {elevated_path.name}")

    print("\n[4/4] Creating elevation markers...")
    markers = create_road_elevation_markers(profile, exaggeration=1.0)
    print(f"  Created {len(markers)} markers")

    # Summary
    print("\n" + "=" * 70)
    print("ELEVATION ANALYSIS COMPLETE")
    print("=" * 70)

    if profile:
        min_e = min(p.elevation for p in profile)
        max_e = max(p.elevation for p in profile)
        print(f"\nCharlotte Race Loop has {max_e - min_e:.1f}m of elevation variation")
        print(f"This WILL affect driving dynamics:")
        print(f"  - Uphill sections reduce acceleration")
        print(f"  - Downhill sections increase braking distance")
        print(f"  - Crests can hide obstacles")
        print(f"  - Total climb: {profile[-1].cumulative_climb:.1f}m")

    # Save
    output_path = Path(__file__).parent.parent / 'output' / 'charlotte_elevation_viz.blend'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"\nSaved to {output_path}")


if __name__ == '__main__':
    main()
