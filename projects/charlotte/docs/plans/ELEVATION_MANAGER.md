# Charlotte - Elevation Manager Plan

## Goal
Create a robust elevation system that handles terrain variation, bridge clearances, and elevation interpolation for the Charlotte digital twin.

## Requirements
- Process elevation data from OSM `ele` tags
- Interpolate elevations for nodes without explicit data
- Calculate bridge clearance heights
- Detect and report elevation conflicts at intersections
- Support terrain-aware road profiles

## Data Sources

### Primary: OSM Elevation Tags
```xml
<node id="123" lat="35.22" lon="-80.84" ele="215.5"/>
```

### Secondary: Interpolation
- Inverse distance weighting from known points
- Consider terrain features (roads follow contours)

## Implementation

### File: `scripts/lib/elevation.py`

```python
class ElevationManager:
    """Manages elevation data for all scene elements."""

    def __init__(self, osm_data):
        self.nodes = {}          # node_id -> (lat, lon, ele)
        self.known_elevations = {}  # node_id -> elevation
        self.terrain_grid = None   # Optional DEM grid

    def load_from_osm(self, osm_root):
        """Extract all elevation data from OSM."""
        pass

    def get_elevation(self, node_id) -> float:
        """Get elevation for a node, interpolating if needed."""
        pass

    def get_elevation_at_point(self, lat, lon) -> float:
        """Get elevation at arbitrary coordinates."""
        pass

    def interpolate_elevation(self, lat, lon) -> float:
        """Interpolate elevation from nearby known points."""
        # Use inverse distance weighting
        # Consider up to 5 nearest known points
        pass

    def get_road_profile(self, way_id, node_ids) -> List[float]:
        """Get elevation at each vertex of a road."""
        pass

class BridgeElevationCalculator:
    """Calculates proper elevations for bridges."""

    CLEARANCES = {
        'road': 4.5,    # Minimum clearance over road
        'highway': 5.5, # Highway overpass
        'rail': 6.5,    # Railway overpass
        'pedestrian': 3.0,
    }

    def calculate_bridge_elevation(self, bridge_way, crossing_roads):
        """Calculate required bridge deck elevation."""
        pass

    def generate_approach_slopes(self, bridge_start, bridge_end):
        """Generate approach ramps (max 5% grade)."""
        pass

    def validate_clearance(self, bridge_way, under_road) -> bool:
        """Check if bridge provides adequate clearance."""
        pass

class ElevationValidator:
    """Validates elevation consistency across the scene."""

    def check_road_continuity(self, road_network):
        """Check for sudden elevation jumps in roads."""
        pass

    def check_intersection_conflicts(self, intersections):
        """Find intersections where roads at different layers meet."""
        pass

    def generate_report(self) -> ElevationReport:
        """Generate human-readable elevation analysis."""
        pass
```

## Interpolation Algorithm

```python
def inverse_distance_weighting(known_points, target_point, power=2, max_distance=500):
    """
    Calculate elevation using inverse distance weighting.

    Args:
        known_points: List of (lat, lon, elevation) tuples
        target_point: (lat, lon) to calculate elevation for
        power: Exponent for distance weighting (default 2)
        max_distance: Maximum distance to consider (meters)

    Returns:
        Interpolated elevation in meters
    """
    weighted_sum = 0
    weight_sum = 0

    for lat, lon, ele in known_points:
        dist = haversine_distance(lat, lon, target_point[0], target_point[1])
        if dist > max_distance or dist < 0.1:
            continue
        weight = 1 / (dist ** power)
        weighted_sum += weight * ele
        weight_sum += weight

    return weighted_sum / weight_sum if weight_sum > 0 else None
```

## Bridge Processing Logic

```
For each bridge way:
1. Get start/end node elevations
2. Find all crossing roads under bridge
3. Calculate max crossing road elevation
4. Add appropriate clearance (5.5m for highway, 4.5m for road)
5. Validate bridge deck elevation >= required
6. If bridge is too low:
   - Flag for manual review
   - Optionally auto-adjust with approach slopes
```

## Output Files
- `scripts/lib/elevation.py` - Main elevation module
- `output/elevation_report.json` - Validation report

## Success Criteria
- [ ] All nodes have elevation values (explicit or interpolated)
- [ ] Bridge clearances validated
- [ ] No roads with impossible grade (>15%)
- [ ] Elevation conflicts reported for manual review

## Estimated Effort
- Core elevation manager: 2-3 hours
- Bridge calculator: 2 hours
- Validation and reporting: 1-2 hours
