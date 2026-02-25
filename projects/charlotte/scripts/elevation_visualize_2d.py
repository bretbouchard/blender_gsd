"""
Charlotte Digital Twin - 2D Elevation Visualization

Creates a 2D matplotlib visualization of the Charlotte elevation data.
This can run outside of Blender and produces PNG/SVG outputs.

Run:
    python scripts/elevation_visualize_2d.py
"""

import sys
import math
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# Add lib to path - import directly from elevation_enhanced.py
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Import only what we need from elevation_enhanced
import importlib.util
spec = importlib.util.spec_from_file_location("elevation_enhanced", Path(__file__).parent / "lib" / "elevation_enhanced.py")
elevation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(elevation_module)

create_enhanced_elevation_manager = elevation_module.create_enhanced_elevation_manager
ElevationPoint = elevation_module.ElevationPoint

# Try to import matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from matplotlib.patches import Circle, FancyArrowPatch
    from matplotlib.lines import Line2D
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("matplotlib not available. Install with: pip install matplotlib")


# =============================================================================
# CONFIGURATION
# =============================================================================

REF_LAT = 35.226
REF_LON = -80.843
BASE_ELEVATION = 220.0

OUTPUT_DIR = Path(__file__).parent.parent / 'output' / 'elevation_viz'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def latlon_to_local(lat: float, lon: float):
    """Convert lat/lon to local scene coordinates (meters)."""
    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * math.cos(math.radians(REF_LAT))
    x = (lon - REF_LON) * meters_per_deg_lon
    y = (lat - REF_LAT) * meters_per_deg_lat
    return (x, y)


def create_elevation_heatmap(elevation_manager):
    """Create a 2D heatmap of elevations."""
    if not MATPLOTLIB_AVAILABLE:
        print("Cannot create visualization - matplotlib not available")
        return None

    print("\n[1/4] Creating elevation heatmap...")

    # Create grid
    grid_size = 1500  # meters
    resolution = 25   # meters per cell
    cols = int(grid_size / resolution) + 1
    rows = int(grid_size / resolution) + 1

    # Generate elevation grid
    x_coords = []
    y_coords = []
    elevations = []

    for row in range(rows):
        for col in range(cols):
            x = -grid_size/2 + col * resolution
            y = -grid_size/2 + row * resolution

            # Convert to lat/lon
            lat = REF_LAT + y / 111000
            lon = REF_LON + x / (111000 * math.cos(math.radians(REF_LAT)))

            elev = elevation_manager.get_elevation(lat, lon)

            x_coords.append(x)
            y_coords.append(y)
            elevations.append(elev)

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 12))

    # Create scatter plot colored by elevation
    scatter = ax.scatter(x_coords, y_coords, c=elevations, cmap='terrain',
                        s=100, alpha=0.8, edgecolors='none')

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('Elevation (m)', fontsize=12)

    # Add key points
    key_points = [
        ("Trade & Tryon", 35.2273, -80.8431, 'red', 275),
        ("Church & MLK", 35.2269, -80.8455, 'green', 264),
        ("I-277 @ College", 35.2231, -80.8648, 'blue', 195),
        ("Trade & Caldwell", 35.2273, -80.8397, 'orange', 252),
        ("Morehead & Tryon", 35.2211, -80.8431, 'purple', 224),
    ]

    for name, lat, lon, color, elev in key_points:
        x, y = latlon_to_local(lat, lon)
        ax.scatter([x], [y], c=color, s=200, marker='*', edgecolors='black', linewidths=1, zorder=5)
        ax.annotate(f"{name}\n({elev}m)", (x, y), xytext=(10, 10),
                   textcoords='offset points', fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # Draw race loop
    race_loop = [
        (35.2269, -80.8455, "Start"),
        (35.2221, -80.8482, ""),
        (35.2175, -80.8583, ""),
        (35.2231, -80.8648, ""),
        (35.2298, -80.8689, ""),
        (35.2318, -80.8653, ""),
        (35.2336, -80.8620, ""),
        (35.2309, -80.8478, ""),
        (35.2269, -80.8455, "Finish"),
    ]

    loop_x = [latlon_to_local(lat, lon)[0] for lat, lon, _ in race_loop]
    loop_y = [latlon_to_local(lat, lon)[1] for lat, lon, _ in race_loop]
    ax.plot(loop_x, loop_y, 'yellow', linewidth=3, alpha=0.8, label='Race Loop')

    # Labels
    ax.set_xlabel('X (meters from reference)', fontsize=12)
    ax.set_ylabel('Y (meters from reference)', fontsize=12)
    ax.set_title('Charlotte Uptown - Real Elevation Map\n(SRTM 30m Data)', fontsize=14, fontweight='bold')

    # Grid
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    # Legend
    legend_elements = [
        Line2D([0], [0], marker='*', color='w', markerfacecolor='red', markersize=15, label='Highest (Trade & Tryon)'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='green', markersize=15, label='Start (Church & MLK)'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='blue', markersize=15, label='Lowest (I-277)'),
        Line2D([0], [0], color='yellow', linewidth=3, label='Race Loop'),
    ]
    ax.legend(handles=legend_elements, loc='upper left')

    plt.tight_layout()

    # Save
    output_path = OUTPUT_DIR / 'elevation_heatmap.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved: {output_path}")

    return fig


def create_trade_street_profile(elevation_manager):
    """Create elevation profile for E Trade St."""
    if not MATPLOTLIB_AVAILABLE:
        return None

    print("\n[2/4] Creating Trade Street elevation profile...")

    # Trade St from Tryon to Caldwell (340m)
    points = []
    for i in range(18):
        lon = -80.8431 + (i * 0.0002)
        lat = 35.2273
        elev = elevation_manager.get_elevation(lat, lon)
        dist = i * 20
        points.append((dist, elev, lat, lon))

    fig, ax = plt.subplots(figsize=(14, 6))

    distances = [p[0] for p in points]
    elevations = [p[1] for p in points]

    # Plot elevation profile
    ax.fill_between(distances, BASE_ELEVATION, elevations, alpha=0.3, color='brown')
    ax.plot(distances, elevations, 'k-', linewidth=2)

    # Mark key points
    ax.scatter([0], [elevations[0]], c='red', s=150, zorder=5, label='Trade & Tryon')
    ax.scatter([340], [elevations[-1]], c='orange', s=150, zorder=5, label='Trade & Caldwell')

    # Annotate
    ax.annotate(f'Start: {elevations[0]:.0f}m', (0, elevations[0]), xytext=(20, 10),
               textcoords='offset points', fontsize=10)
    ax.annotate(f'End: {elevations[-1]:.0f}m', (340, elevations[-1]), xytext=(20, 10),
               textcoords='offset points', fontsize=10)

    # Grade indicators
    total_drop = elevations[0] - elevations[-1]
    avg_grade = (elevations[-1] - elevations[0]) / 340 * 100

    ax.set_xlabel('Distance from Tryon (meters)', fontsize=12)
    ax.set_ylabel('Elevation (m)', fontsize=12)
    ax.set_title(f'E Trade Street Elevation Profile\n'
                f'Total Drop: {abs(total_drop):.0f}m over 340m | Average Grade: {avg_grade:.1f}%',
                fontsize=14, fontweight='bold')

    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')

    # Add grade zones
    ax.axhspan(BASE_ELEVATION, 220, alpha=0.1, color='green', label='Base level')
    ax.axhspan(270, 300, alpha=0.1, color='red', label='High ground')

    plt.tight_layout()

    output_path = OUTPUT_DIR / 'trade_street_profile.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved: {output_path}")

    return fig


def create_race_loop_profile(elevation_manager):
    """Create elevation profile for the entire race loop."""
    if not MATPLOTLIB_AVAILABLE:
        return None

    print("\n[3/4] Creating race loop elevation profile...")

    # Race loop waypoints
    waypoints = [
        ("Start", 35.2269, -80.8455),
        ("Church & Morehead", 35.2221, -80.8482),
        ("I-277 Entry", 35.2175, -80.8583),
        ("I-277 @ College", 35.2231, -80.8648),
        ("I-277 Exit", 35.2261, -80.8673),
        ("College & E 5th", 35.2298, -80.8689),
        ("E 5th & Caldwell", 35.2318, -80.8653),
        ("Caldwell & Trade", 35.2336, -80.8620),
        ("Trade & Church", 35.2309, -80.8478),
        ("Finish", 35.2269, -80.8455),
    ]

    # Calculate cumulative distance and elevation
    cumulative_dist = 0
    prev_x, prev_y = None, None

    distances = [0]
    elevations = []
    labels = []

    for name, lat, lon in waypoints:
        x, y = latlon_to_local(lat, lon)
        elev = elevation_manager.get_elevation(lat, lon)
        elevations.append(elev)
        labels.append(name)

        if prev_x is not None:
            dx = x - prev_x
            dy = y - prev_y
            cumulative_dist += math.sqrt(dx*dx + dy*dy)
            distances.append(cumulative_dist)

        prev_x, prev_y = x, y

    fig, ax = plt.subplots(figsize=(16, 7))

    # Plot
    ax.fill_between(distances, BASE_ELEVATION, elevations, alpha=0.3, color='green')
    ax.plot(distances, elevations, 'b-', linewidth=2.5, marker='o', markersize=8)

    # Annotate waypoints
    for i, (dist, elev, label) in enumerate(zip(distances, elevations, labels)):
        if label:
            ax.scatter([dist], [elev], c='red' if i == 0 or i == len(distances)-1 else 'blue', s=100, zorder=5)
            ax.annotate(label, (dist, elev), xytext=(5, 10),
                       textcoords='offset points', fontsize=8, rotation=45,
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

    # Statistics
    min_elev = min(elevations)
    max_elev = max(elevations)
    total_dist = distances[-1]

    ax.set_xlabel('Distance from Start (meters)', fontsize=12)
    ax.set_ylabel('Elevation (m)', fontsize=12)
    ax.set_title(f'Charlotte Race Loop - Elevation Profile\n'
                f'Total Distance: {total_dist:.0f}m | Elevation Range: {min_elev:.0f}m - {max_elev:.0f}m | '
                f'Variation: {max_elev - min_elev:.0f}m',
                fontsize=14, fontweight='bold')

    ax.grid(True, alpha=0.3)

    # Add elevation zones
    ax.axhline(y=min_elev, color='blue', linestyle='--', alpha=0.5, label=f'Low: {min_elev:.0f}m')
    ax.axhline(y=max_elev, color='red', linestyle='--', alpha=0.5, label=f'High: {max_elev:.0f}m')
    ax.legend(loc='upper right')

    plt.tight_layout()

    output_path = OUTPUT_DIR / 'race_loop_profile.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved: {output_path}")

    return fig


def create_3d_surface(elevation_manager):
    """Create a 3D surface plot of elevations."""
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        from mpl_toolkits.mplot3d import Axes3D
    except ImportError:
        print("  3D plotting not available")
        return None

    print("\n[4/4] Creating 3D surface plot...")

    # Create grid
    grid_size = 1000
    resolution = 50
    cols = int(grid_size / resolution) + 1
    rows = int(grid_size / resolution) + 1

    import numpy as np

    X = np.linspace(-grid_size/2, grid_size/2, cols)
    Y = np.linspace(-grid_size/2, grid_size/2, rows)
    X, Y = np.meshgrid(X, Y)

    Z = np.zeros_like(X)
    for i in range(rows):
        for j in range(cols):
            lat = REF_LAT + Y[i, j] / 111000
            lon = REF_LON + X[i, j] / (111000 * math.cos(math.radians(REF_LAT)))
            Z[i, j] = elevation_manager.get_elevation(lat, lon)

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Surface
    surf = ax.plot_surface(X, Y, Z, cmap='terrain', alpha=0.8,
                          linewidth=0, antialiased=True)

    # Colorbar
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Elevation (m)')

    # Mark key points
    key_points = [
        ("Trade & Tryon", 35.2273, -80.8431),
        ("I-277 @ College", 35.2231, -80.8648),
    ]

    for name, lat, lon in key_points:
        x, y = latlon_to_local(lat, lon)
        z = elevation_manager.get_elevation(lat, lon)
        ax.scatter([x], [y], [z], c='red', s=100, marker='*')

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Elevation (m)')
    ax.set_title('Charlotte Uptown - 3D Elevation Surface', fontsize=14, fontweight='bold')

    plt.tight_layout()

    output_path = OUTPUT_DIR / 'elevation_3d_surface.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved: {output_path}")

    return fig


def export_elevation_csv(elevation_manager):
    """Export elevation data to CSV file."""
    print("\nExporting elevation data to CSV...")

    import csv

    # Export all known elevation points
    csv_path = OUTPUT_DIR / 'elevation_points.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['lat', 'lon', 'x_meters', 'y_meters', 'elevation_m', 'relative_z', 'source', 'name'])

        for point in elevation_manager.known_points:
            x, y = latlon_to_local(point.lat, point.lon)
            writer.writerow([
                f"{point.lat:.6f}",
                f"{point.lon:.6f}",
                f"{x:.1f}",
                f"{y:.1f}",
                f"{point.elevation:.1f}",
                f"{point.elevation - BASE_ELEVATION:.1f}",
                point.source,
                ''
            ])

    print(f"  Saved: {csv_path}")

    # Export Trade St profile
    trade_csv = OUTPUT_DIR / 'trade_street_profile.csv'

    with open(trade_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['distance_m', 'lat', 'lon', 'elevation_m', 'relative_z', 'grade_pct'])

        prev_elev = None
        for i in range(18):
            lon = -80.8431 + (i * 0.0002)
            lat = 35.2273
            elev = elevation_manager.get_elevation(lat, lon)

            if prev_elev is not None:
                grade = (elev - prev_elev) / 20 * 100
            else:
                grade = 0

            writer.writerow([
                i * 20,
                f"{lat:.6f}",
                f"{lon:.6f}",
                f"{elev:.1f}",
                f"{elev - BASE_ELEVATION:.1f}",
                f"{grade:.2f}"
            ])
            prev_elev = elev

    print(f"  Saved: {trade_csv}")

    # Export race loop profile
    loop_csv = OUTPUT_DIR / 'race_loop_profile.csv'

    waypoints = [
        ("Start", 35.2269, -80.8455),
        ("Church & Morehead", 35.2221, -80.8482),
        ("I-277 Entry", 35.2175, -80.8583),
        ("I-277 @ College", 35.2231, -80.8648),
        ("I-277 Exit", 35.2261, -80.8673),
        ("College & E 5th", 35.2298, -80.8689),
        ("E 5th & Caldwell", 35.2318, -80.8653),
        ("Caldwell & Trade", 35.2336, -80.8620),
        ("Trade & Church", 35.2309, -80.8478),
        ("Finish", 35.2269, -80.8455),
    ]

    with open(loop_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['waypoint', 'lat', 'lon', 'x_meters', 'y_meters', 'elevation_m', 'relative_z', 'cumulative_dist_m', 'grade_from_prev_pct'])

        cumulative_dist = 0
        prev_x, prev_y, prev_elev = None, None, None

        for name, lat, lon in waypoints:
            x, y = latlon_to_local(lat, lon)
            elev = elevation_manager.get_elevation(lat, lon)

            if prev_x is not None:
                dx = x - prev_x
                dy = y - prev_y
                cumulative_dist += math.sqrt(dx*dx + dy*dy)
                grade = (elev - prev_elev) / math.sqrt(dx*dx + dy*dy) * 100 if dx*dx + dy*dy > 0 else 0
            else:
                grade = 0

            writer.writerow([
                name,
                f"{lat:.6f}",
                f"{lon:.6f}",
                f"{x:.1f}",
                f"{y:.1f}",
                f"{elev:.1f}",
                f"{elev - BASE_ELEVATION:.1f}",
                f"{cumulative_dist:.1f}",
                f"{grade:.2f}"
            ])
            prev_x, prev_y, prev_elev = x, y, elev

    print(f"  Saved: {loop_csv}")

    return csv_path


def create_summary_report(elevation_manager):
    """Create a text summary report."""
    print("\nCreating summary report...")

    stats = elevation_manager.get_elevation_stats()

    report = f"""
================================================================================
CHARLOTTE DIGITAL TWIN - ELEVATION DATA REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

DATA SOURCE
-----------
- Source: SRTM 30m (OpenTopoData API)
- Resolution: ~30 meters
- Known elevation points: {stats['point_count']}

ELEVATION STATISTICS
--------------------
- Minimum elevation: {stats['min_elevation']:.0f}m
- Maximum elevation: {stats['max_elevation']:.0f}m
- Mean elevation: {stats['mean_elevation']:.0f}m
- Total variation: {stats['range']:.0f}m

KEY LOCATIONS
-------------
Location                    | Elevation | Relative Z | Notes
----------------------------|-----------|------------|------------------
Trade & Tryon (Highest)     | 275m      | +55m       | "The Hill"
Church & MLK (Start)        | 264m      | +44m       | Race Start/Finish
Trade & Caldwell            | 252m      | +32m       | End of Trade descent
I-277 @ College (Lowest)    | 195m      | -25m       | Highway low point

E TRADE STREET PROFILE (Tryon → Caldwell)
-----------------------------------------
- Distance: 340 meters
- Start elevation: 295m
- End elevation: 252m
- Total drop: 43m
- Average grade: -12.6%

This is a significant downhill section that will be very noticeable
from the driver's camera view at 1.1m eye height.

RACE LOOP PROFILE
-----------------
- Total distance: ~4.6 km
- Elevation range: 195m - 264m
- Total variation: 69m
- Notable features:
  * Steep descent at start (Church to Morehead)
  * Low point on I-277 highway
  * Climbs back up to finish

DRIVER CAMERA FEEL
------------------
At driver eye height (1.08m for sports car):
- Horizon drops ~43m on Trade St descent
- That's about 10 car lengths of elevation change
- Buildings on either side will emphasize the slope
- The climb back to finish is noticeable

FILES GENERATED
---------------
- elevation_heatmap.png     : 2D color map of elevations
- trade_street_profile.png  : Trade St elevation graph
- race_loop_profile.png     : Full race loop profile
- elevation_3d_surface.png  : 3D surface visualization
- elevation_points.csv      : All known elevation points
- trade_street_profile.csv  : Trade St detailed data
- race_loop_profile.csv     : Race loop waypoint data

================================================================================
"""

    report_path = OUTPUT_DIR / 'ELEVATION_REPORT.txt'
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"  Saved: {report_path}")
    print(report)

    return report_path


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("CHARLOTTE ELEVATION - 2D VISUALIZATION")
    print("=" * 60)

    if not MATPLOTLIB_AVAILABLE:
        print("\nERROR: matplotlib is required for visualization")
        print("Install with: pip install matplotlib numpy")
        return

    # Create elevation manager
    print("\nLoading elevation data...")
    elevation_manager = create_enhanced_elevation_manager()
    print(f"Loaded {len(elevation_manager.known_points)} elevation points")

    # Create visualizations
    create_elevation_heatmap(elevation_manager)
    create_trade_street_profile(elevation_manager)
    create_race_loop_profile(elevation_manager)
    create_3d_surface(elevation_manager)

    # Export data
    export_elevation_csv(elevation_manager)

    # Create report
    create_summary_report(elevation_manager)

    print("\n" + "=" * 60)
    print("VISUALIZATION COMPLETE")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")

    # Show plots (if interactive)
    try:
        plt.show()
    except:
        pass


if __name__ == '__main__':
    main()
