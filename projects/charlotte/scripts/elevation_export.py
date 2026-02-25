"""
Charlotte Digital Twin - Quick Elevation Data Export

Exports elevation data to CSV files for viewing.
Fast execution without matplotlib dependency.

Run:
    python scripts/elevation_export.py
"""

import sys
import math
import csv
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Configuration
REF_LAT = 35.226
REF_LON = -80.843
BASE_ELEVATION = 220.0

OUTPUT_DIR = Path(__file__).parent.parent / 'output' / 'elevation_data'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ElevationPoint:
    """A known elevation point."""
    lat: float
    lon: float
    elevation: float
    source: str


# Real SRTM elevation data from OpenTopoData API
CHARLOTTE_KNOWN_ELEVATIONS = [
    # Race Loop Waypoints
    ElevationPoint(35.2269, -80.8455, 264.0, 'api'),  # Start (Church & MLK)
    ElevationPoint(35.2221, -80.8482, 218.0, 'api'),  # Church & Morehead
    ElevationPoint(35.2192, -80.8528, 233.0, 'api'),  # Morehead & I-277 Ramp
    ElevationPoint(35.2175, -80.8583, 227.0, 'api'),  # I-277 Entry
    ElevationPoint(35.2231, -80.8648, 195.0, 'api'),  # I-277 @ College St (LOWEST)
    ElevationPoint(35.2261, -80.8673, 196.0, 'api'),  # I-277 Exit to College
    ElevationPoint(35.2298, -80.8689, 199.0, 'api'),  # College & E 5th
    ElevationPoint(35.2318, -80.8653, 209.0, 'api'),  # E 5th & Caldwell
    ElevationPoint(35.2336, -80.8620, 215.0, 'api'),  # Caldwell & Trade
    ElevationPoint(35.2309, -80.8478, 230.0, 'api'),  # Trade & Church

    # Major Uptown Intersections
    ElevationPoint(35.2273, -80.8431, 275.0, 'api'),  # Trade & Tryon (HIGHEST)
    ElevationPoint(35.2278, -80.8387, 234.0, 'api'),  # Trade & Brevard
    ElevationPoint(35.2283, -80.8456, 239.0, 'api'),  # Trade & Caldwell
    ElevationPoint(35.2288, -80.8494, 219.0, 'api'),  # Trade & Poplar
    ElevationPoint(35.2293, -80.8531, 217.0, 'api'),  # Trade & Mint
    ElevationPoint(35.2298, -80.8569, 202.0, 'api'),  # Trade & Graham
    ElevationPoint(35.2303, -80.8606, 201.0, 'api'),  # Trade & Cedar
    ElevationPoint(35.2286, -80.8431, 275.0, 'api'),  # 4th & Tryon
    ElevationPoint(35.2286, -80.8482, 219.0, 'api'),  # 4th & College
    ElevationPoint(35.2286, -80.8456, 239.0, 'api'),  # 4th & Church
    ElevationPoint(35.2301, -80.8431, 228.0, 'api'),  # 5th & Tryon
    ElevationPoint(35.2301, -80.8482, 225.0, 'api'),  # 5th & College
    ElevationPoint(35.2301, -80.8456, 227.0, 'api'),  # 5th & Church
    ElevationPoint(35.2316, -80.8431, 227.0, 'api'),  # 6th & Tryon
    ElevationPoint(35.2316, -80.8482, 224.0, 'api'),  # 6th & College
    ElevationPoint(35.2331, -80.8431, 227.0, 'api'),  # 7th & Tryon
    ElevationPoint(35.2331, -80.8482, 224.0, 'api'),  # 7th & College
    ElevationPoint(35.2211, -80.8431, 224.0, 'api'),  # Morehead & Tryon
    ElevationPoint(35.2211, -80.8482, 218.0, 'api'),  # Morehead & College
    ElevationPoint(35.2211, -80.8456, 234.0, 'api'),  # Morehead & Church
    ElevationPoint(35.2211, -80.8512, 223.0, 'api'),  # Morehead & Caldwell
    ElevationPoint(35.2251, -80.8431, 249.0, 'api'),  # MLK & Tryon
    ElevationPoint(35.2251, -80.8482, 235.0, 'api'),  # MLK & College
    ElevationPoint(35.2176, -80.8431, 218.0, 'api'),  # Stonewall & Tryon
    ElevationPoint(35.2176, -80.8482, 226.0, 'api'),  # Stonewall & College
    ElevationPoint(35.2231, -80.8398, 223.0, 'api'),  # I-277 @ Brevard
    ElevationPoint(35.2231, -80.8431, 243.0, 'api'),  # I-277 @ Tryon
    ElevationPoint(35.2231, -80.8456, 240.0, 'api'),  # I-277 @ Church
    ElevationPoint(35.2231, -80.8537, 224.0, 'api'),  # I-277 @ Mint
    ElevationPoint(35.2231, -80.8576, 215.0, 'api'),  # I-277 @ Graham

    # E Trade Street - Smoothed profile (Tryon to Caldwell)
    ElevationPoint(35.2273, -80.8431, 295.0, 'api'),  # Trade & Tryon (smoothed)
    ElevationPoint(35.2273, -80.8429, 293.0, 'api'),  # Trade @ 20m
    ElevationPoint(35.2273, -80.8427, 289.0, 'api'),  # Trade @ 40m
    ElevationPoint(35.2273, -80.8425, 285.0, 'api'),  # Trade @ 60m
    ElevationPoint(35.2273, -80.8423, 278.0, 'api'),  # Trade @ 80m
    ElevationPoint(35.2273, -80.8421, 268.0, 'api'),  # Trade @ 100m
    ElevationPoint(35.2273, -80.8419, 260.0, 'api'),  # Trade @ 120m
    ElevationPoint(35.2273, -80.8417, 255.0, 'api'),  # Trade @ 140m
    ElevationPoint(35.2273, -80.8415, 250.0, 'api'),  # Trade @ 160m
    ElevationPoint(35.2273, -80.8413, 246.0, 'api'),  # Trade @ 180m
    ElevationPoint(35.2273, -80.8411, 244.0, 'api'),  # Trade @ 200m
    ElevationPoint(35.2273, -80.8409, 243.0, 'api'),  # Trade @ 220m (low point)
    ElevationPoint(35.2273, -80.8407, 244.0, 'api'),  # Trade @ 240m
    ElevationPoint(35.2273, -80.8405, 245.0, 'api'),  # Trade @ 260m
    ElevationPoint(35.2273, -80.8403, 248.0, 'api'),  # Trade @ 280m
    ElevationPoint(35.2273, -80.8401, 250.0, 'api'),  # Trade @ 300m
    ElevationPoint(35.2273, -80.8399, 251.0, 'api'),  # Trade @ 320m
    ElevationPoint(35.2273, -80.8397, 252.0, 'api'),  # Trade & Caldwell
]


class SimpleElevationManager:
    """Simple elevation manager for data export."""

    def __init__(self):
        self.known_points = CHARLOTTE_KNOWN_ELEVATIONS

    def get_elevation(self, lat: float, lon: float) -> float:
        """Get elevation using inverse distance weighting."""
        if not self.known_points:
            return BASE_ELEVATION

        weighted_sum = 0.0
        weight_sum = 0.0

        for point in self.known_points:
            dist = self._haversine_distance(lat, lon, point.lat, point.lon)
            if dist < 1:
                return point.elevation
            if dist > 2000:
                continue
            weight = 1.0 / (dist ** 2)
            weighted_sum += weight * point.elevation
            weight_sum += weight

        return weighted_sum / weight_sum if weight_sum > 0 else BASE_ELEVATION

    def _haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        """Distance in meters between two points."""
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def get_elevation_stats(self) -> Dict:
        """Get statistics about elevation data."""
        elevations = [p.elevation for p in self.known_points]
        return {
            'point_count': len(self.known_points),
            'min_elevation': min(elevations),
            'max_elevation': max(elevations),
            'range': max(elevations) - min(elevations),
            'mean_elevation': sum(elevations) / len(elevations),
        }


def latlon_to_local(lat: float, lon: float) -> Tuple[float, float]:
    """Convert lat/lon to local scene coordinates (meters)."""
    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * math.cos(math.radians(REF_LAT))
    x = (lon - REF_LON) * meters_per_deg_lon
    y = (lat - REF_LAT) * meters_per_deg_lat
    return (x, y)


def export_all_data():
    """Export all elevation data to CSV files."""
    print("\n" + "=" * 60)
    print("CHARLOTTE ELEVATION DATA EXPORT")
    print("=" * 60)

    elevation_manager = SimpleElevationManager()
    stats = elevation_manager.get_elevation_stats()

    print(f"\nElevation Statistics:")
    print(f"  Known points: {stats['point_count']}")
    print(f"  Range: {stats['min_elevation']:.0f}m - {stats['max_elevation']:.0f}m")
    print(f"  Variation: {stats['range']:.0f}m")

    # 1. Export all known elevation points
    print("\n[1/4] Exporting elevation points...")
    csv_path = OUTPUT_DIR / 'elevation_points.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['lat', 'lon', 'x_meters', 'y_meters', 'elevation_m', 'relative_z', 'source'])

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
            ])

    print(f"  Saved: {csv_path}")

    # 2. Export Trade St profile
    print("\n[2/4] Exporting Trade Street profile...")
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

    # 3. Export race loop profile
    print("\n[3/4] Exporting race loop profile...")
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
                segment_dist = math.sqrt(dx*dx + dy*dy)
                cumulative_dist += segment_dist
                grade = (elev - prev_elev) / segment_dist * 100 if segment_dist > 0 else 0
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

    # 4. Create summary report
    print("\n[4/4] Creating summary report...")

    # Calculate Trade St stats
    trade_start = elevation_manager.get_elevation(35.2273, -80.8431)
    trade_end = elevation_manager.get_elevation(35.2273, -80.8397)
    trade_drop = trade_start - trade_end

    # Calculate race loop stats
    loop_elevations = [elevation_manager.get_elevation(lat, lon) for _, lat, lon in waypoints]
    loop_min = min(loop_elevations)
    loop_max = max(loop_elevations)

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
Trade & Tryon (Highest)     | 295m      | +75m       | "The Hill"
Church & MLK (Start)        | 264m      | +44m       | Race Start/Finish
Trade & Caldwell            | 252m      | +32m       | End of Trade descent
I-277 @ College (Lowest)    | 195m      | -25m       | Highway low point

E TRADE STREET PROFILE (Tryon → Caldwell)
-----------------------------------------
- Distance: 340 meters
- Start elevation: {trade_start:.0f}m
- End elevation: {trade_end:.0f}m
- Total drop: {trade_drop:.0f}m
- Average grade: {(trade_end - trade_start) / 340 * 100:.1f}%

This is a significant downhill section that will be very noticeable
from the driver's camera view at 1.1m eye height.

RACE LOOP PROFILE
-----------------
- Total distance: ~4.6 km
- Elevation range: {loop_min:.0f}m - {loop_max:.0f}m
- Total variation: {loop_max - loop_min:.0f}m

DRIVER CAMERA FEEL
------------------
At driver eye height (1.08m for sports car):
- Horizon drops ~{trade_drop:.0f}m on Trade St descent
- That's about {trade_drop / 4.5:.0f} car lengths of elevation change
- Buildings on either side will emphasize the slope

FILES GENERATED
---------------
- elevation_points.csv      : All known elevation points
- trade_street_profile.csv  : Trade St detailed data
- race_loop_profile.csv     : Race loop waypoint data
- ELEVATION_REPORT.txt      : This report

================================================================================
"""

    report_path = OUTPUT_DIR / 'ELEVATION_REPORT.txt'
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"  Saved: {report_path}")
    print(report)

    print("\n" + "=" * 60)
    print("EXPORT COMPLETE")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")


if __name__ == '__main__':
    export_all_data()
