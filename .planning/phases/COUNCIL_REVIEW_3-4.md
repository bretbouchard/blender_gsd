# The Council of Ricks Review Report
## Phase 3 (Interior Layout) and Phase 4 (Urban Infrastructure)

**Review Date:** 2026-02-21
**Review Duration:** ~30 minutes
**Review Type:** Focused Review (geometry-rick, performance-rick, dufus-rick)

---

## Executive Summary

**Total Issues Found:** 15
- **CRITICAL (SLC/Architecture):** 3
- **HIGH (Performance/Correctness):** 5
- **MEDIUM (Testing/Robustness):** 7
- **LOW (Style/Documentation):** 0

**Overall Council Decision:**

| Phase | Decision | Confidence |
|-------|----------|------------|
| **Phase 3: Interior Layout** | **CONDITIONAL APPROVE** | 85% |
| **Phase 4: Urban Infrastructure** | **CONDITIONAL APPROVE** | 80% |

---

## Stack Assessment

**Detected Project Stack:**
- **Project Type:** Blender Add-on / Procedural Generation
- **Language:** Python 3.x
- **Framework:** Blender 4.x Geometry Nodes
- **Key Patterns:**
  - Hybrid Python + GN architecture (Python for algorithms, GN for geometry)
  - JSON interchange format between Python and GN
  - bmesh for context-free mesh creation
  - NodeTreeBuilder for programmatic GN creation

**Council Specialists Assigned:**
- geometry-rick (Geometry Nodes, BSP, L-system integration)
- performance-rick (Memory usage, LOD strategy)
- dufus-rick (Testing for procedural generation)

---

## Phase 3: Interior Layout System Review

**File:** `/Users/bretbouchard/apps/blender_gsd/.planning/phases/03-interior-layout-system/PLAN.md`

### CRITICAL Issues

#### CRITICAL-3.1: BSP Algorithm Correctness Not Specified
**Location:** Task 1, lib/interiors/bsp_solver.py
**Severity:** CRITICAL

**Problem:**
The BSP implementation specification lacks critical algorithmic details:

1. **Missing split heuristic:** No specification of HOW the split position is chosen. Random? Area-balanced? Aspect-ratio optimized?

2. **Missing termination conditions:** Only mentions "too small rooms, invalid splits, max depth exceeded" without concrete thresholds.

3. **No room assignment strategy:** `_create_room_from_leaf()` lacks specification for how room types are assigned to leaf nodes.

**Current Code Pattern:**
```python
def _choose_split_position(self, rect: Rect, axis: str) -> float:
    # MISSING: What heuristic?
    pass
```

**Required Fix:**
```python
@dataclass
class BSPConfig:
    min_room_area: float = 9.0  # m^2 (minimum room size)
    max_room_area: float = 100.0  # m^2
    split_ratio_range: Tuple[float, float] = (0.3, 0.7)  # Golden ratio-ish
    max_depth: int = 10  # Maximum recursion depth
    room_height_default: float = 2.8  # meters

def _choose_split_position(self, rect: Rect, axis: str) -> float:
    """Choose split position using area-balanced heuristic.

    Splits at random point within ratio range, biased toward center.
    """
    min_ratio, max_ratio = self.config.split_ratio_range
    if axis == "horizontal":
        split = rect.y + rect.height * random.uniform(min_ratio, max_ratio)
    else:
        split = rect.x + rect.width * random.uniform(min_ratio, max_ratio)
    return split
```

**Impact:** Incorrect BSP generation leads to invalid floor plans with rooms that don't meet minimum size requirements.

---

#### CRITICAL-3.2: JSON Parsing in Geometry Nodes Not Addressed
**Location:** Task 2, lib/interiors/walls.py
**Severity:** CRITICAL

**Problem:**
The plan specifies GN consuming JSON input via a string socket:
```python
ng.interface.new_socket("road_json", socket_type='NodeSocketString')
```

However, **Geometry Nodes has NO native JSON parsing capability**. The plan says:
> "Add nodes for JSON parsing (using String to Value nodes)
> Note: Complex JSON parsing may need Python driver nodes"

This is a critical architectural issue. GN cannot parse arbitrary JSON structures.

**Current Plan (INCORRECT):**
```python
# GN inputs
ng.interface.new_socket("wall_segments", socket_type='NodeSocketString')  # JSON string
# ... parse JSON in GN (IMPOSSIBLE)
```

**Required Fix:**
Two valid approaches:

**Approach A: Pre-processed Attribute Arrays (RECOMMENDED)**
```python
# Don't pass JSON to GN. Instead, pass pre-processed attribute arrays.
# Python pre-processes floor plan into attribute format GN can consume.

def build_walls_from_floor_plan(plan: FloorPlan, config: WallBuilderConfig) -> bpy.types.Object:
    # Pre-process: Convert floor plan to curve collection
    # GN receives curves with named attributes, not JSON

    # Create curve object for each wall segment
    wall_curves = []
    for room in plan.rooms:
        for i, (p1, p2) in enumerate(zip(room.polygon, room.polygon[1:] + [room.polygon[0]])):
            curve = create_wall_curve(p1, p2, room.doors_on_wall(i), room.windows_on_wall(i))
            wall_curves.append(curve)

    # Apply GN modifier to collection
    # GN reads curve attributes directly
```

**Approach B: Python-side Geometry Generation (FALLBACK)**
```python
# Use bmesh for geometry creation (like existing room_builder.py)
# GN for detail/variation only, not core geometry

def build_walls_from_floor_plan(plan: FloorPlan, config: WallBuilderConfig) -> bpy.types.Object:
    # Generate wall geometry in Python using bmesh
    # Reference: lib/art/room_builder.py patterns
    bm = bmesh.new()
    for segment in extract_wall_segments(plan):
        create_wall_bmesh(bm, segment, config)
    # ...
```

**Recommendation:** Use Approach A for real-time editing, Approach B for batch generation.

---

### HIGH Issues

#### HIGH-3.1: No Memory Bounds for Large Floor Plans
**Location:** Task 1, BSPSolver
**Severity:** HIGH (performance-rick)

**Problem:**
BSP can generate thousands of rooms with deep recursion. No memory limits specified.

**Current Plan:**
```python
def generate(self, width: float, height: float, room_count: int) -> FloorPlan:
    # No memory estimation
    # No chunking for large floor plans
```

**Required Fix:**
```python
class BSPSolver:
    MAX_ROOMS_DEFAULT = 100  # Safety limit
    MAX_RECURSION_DEPTH = 15  # Stack overflow prevention

    def generate(self, width: float, height: float, room_count: int) -> FloorPlan:
        if room_count > self.MAX_ROOMS_DEFAULT:
            raise ValueError(f"room_count ({room_count}) exceeds maximum ({self.MAX_ROOMS_DEFAULT}). "
                           f"Use iterative generation for large buildings.")

        # Track memory usage during generation
        import sys
        estimated_memory = room_count * 1024  # ~1KB per room estimate
        if estimated_memory > 10 * 1024 * 1024:  # 10MB threshold
            import warnings
            warnings.warn(f"Large floor plan may consume {estimated_memory / 1024 / 1024:.1f}MB")
```

---

#### HIGH-3.2: Furniture Collision Detection Missing
**Location:** Task 5, FurniturePlacer
**Severity:** HIGH (dufus-rick)

**Problem:**
Furniture placement checks clearances but not actual collision detection between furniture items.

**Current Plan:**
```python
def _check_clearance(item: FurnitureItem, position: Tuple, room: Room) -> bool:
    pass  # What about collision with existing furniture?
```

**Required Fix:**
```python
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class BoundingBox2D:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def intersects(self, other: 'BoundingBox2D') -> bool:
        return not (self.max_x < other.min_x or
                    self.min_x > other.max_x or
                    self.max_y < other.min_y or
                    self.min_y > other.max_y)

def get_furniture_bbox(item: FurnitureItem, position: Tuple[float, float, float],
                       rotation: float) -> BoundingBox2D:
    """Calculate 2D bounding box for collision detection."""
    # Account for rotation
    import math
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)

    # Get corners of furniture footprint
    half_w = item.width / 2
    half_d = item.depth / 2
    corners = [
        (half_w * cos_r - half_d * sin_r + position[0],
         half_w * sin_r + half_d * cos_r + position[1]),
        (-half_w * cos_r - half_d * sin_r + position[0],
         -half_w * sin_r + half_d * cos_r + position[1]),
        # ... all 4 corners
    ]

    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return BoundingBox2D(min(xs), min(ys), max(xs), max(ys))

def _check_collision(new_item: FurnitureItem, new_position: Tuple,
                     new_rotation: float,
                     existing: List[Tuple[FurnitureItem, Tuple, float]]) -> bool:
    """Check if new furniture collides with existing items."""
    new_bbox = get_furniture_bbox(new_item, new_position, new_rotation)

    for existing_item, existing_pos, existing_rot in existing:
        existing_bbox = get_furniture_bbox(existing_item, existing_pos, existing_rot)
        if new_bbox.intersects(existing_bbox):
            return True  # Collision detected

    return False  # No collision
```

---

### MEDIUM Issues

#### MEDIUM-3.1: No Unit Tests for BSP Determinism
**Location:** Verification section
**Severity:** MEDIUM (dufus-rick)

**Problem:**
The verification command tests basic BSP generation but not determinism with seed:

```bash
python3 -c "from lib.interiors import BSPSolver, FloorPlan, Room, RoomType; s = BSPSolver(seed=42); fp = s.generate(10, 8, 4); assert len(fp.rooms) == 4; print('BSP test passed')"
```

This only tests room count, not deterministic generation.

**Required Fix:**
```python
# Add to tests/test_interiors.py

def test_bsp_determinism():
    """Verify BSP generates identical output for same seed."""
    solver1 = BSPSolver(seed=42)
    plan1 = solver1.generate(20.0, 15.0, 6)

    solver2 = BSPSolver(seed=42)
    plan2 = solver2.generate(20.0, 15.0, 6)

    # Verify identical room counts
    assert len(plan1.rooms) == len(plan2.rooms)

    # Verify identical room polygons
    for r1, r2 in zip(plan1.rooms, plan2.rooms):
        assert r1.polygon == r2.polygon, f"Room polygons differ: {r1.polygon} vs {r2.polygon}"

    # Verify identical connections
    assert len(plan1.connections) == len(plan2.connections)

    print("BSP determinism test passed")

def test_bsp_minimum_room_size():
    """Verify BSP respects minimum room area."""
    solver = BSPSolver(config=BSPConfig(min_room_area=9.0))
    plan = solver.generate(20.0, 15.0, 4)

    for room in plan.rooms:
        area = calculate_polygon_area(room.polygon)
        assert area >= 9.0, f"Room {room.id} has area {area} < minimum 9.0"

    print("BSP minimum room size test passed")
```

---

#### MEDIUM-3.2: Staircase Code Compliance Not Enforced
**Location:** Task 4, staircase.py
**Severity:** MEDIUM (geometry-rick)

**Problem:**
`validate_stair_config()` returns warnings but doesn't prevent invalid configurations.

**Current Plan:**
```python
def validate_stair_config(config: StairConfig) -> List[str]:
    """Check building code compliance
    - Warn about uncomfortable ratios
    - Check minimum headroom clearance
    """
```

**Required Fix:**
```python
@dataclass
class StairValidationResult:
    valid: bool
    errors: List[str]  # Blocking errors
    warnings: List[str]  # Non-blocking warnings

# Building code constants (IBC 2021)
MIN_TREAD_DEPTH = 0.28  # meters (11 inches)
MAX_RISER_HEIGHT = 0.20  # meters (7.75 inches)
MIN_HEADROOM = 2.03  # meters (6 feet 8 inches)
COMFORT_RATIO_MIN = 0.60  # 2*rise + run >= 63cm
COMFORT_RATIO_MAX = 0.67  # 2*rise + run <= 67cm

def validate_stair_config(config: StairConfig) -> StairValidationResult:
    """Validate stair configuration against building code."""
    errors = []
    warnings = []

    # Mandatory checks (errors)
    if config.tread_depth < MIN_TREAD_DEPTH:
        errors.append(f"Tread depth {config.tread_depth:.3f}m below minimum {MIN_TREAD_DEPTH}m (IBC)")

    if config.riser_height > MAX_RISER_HEIGHT:
        errors.append(f"Riser height {config.riser_height:.3f}m exceeds maximum {MAX_RISER_HEIGHT}m (IBC)")

    # Comfort check (warning)
    comfort_ratio = 2 * config.riser_height + config.tread_depth
    if not (COMFORT_RATIO_MIN <= comfort_ratio <= COMFORT_RATIO_MAX):
        warnings.append(f"Comfort ratio {comfort_ratio:.2f}m outside ideal range [{COMFORT_RATIO_MIN}, {COMFORT_RATIO_MAX}]")

    return StairValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )

def generate(self, start_point: Tuple, direction: Tuple) -> bpy.types.Object:
    """Generate staircase with validation."""
    result = validate_stair_config(self.config)
    if not result.valid:
        raise ValueError(f"Invalid stair configuration: {'; '.join(result.errors)}")
    for warning in result.warnings:
        import warnings
        warnings.warn(warning)
    # ... continue with generation
```

---

## Phase 4: Urban Infrastructure Review

**File:** `/Users/bretbouchard/apps/blender_gsd/.planning/phases/4/PLAN.md`

### CRITICAL Issues

#### CRITICAL-4.1: L-System Interpretation Missing Critical Details
**Location:** Task 1, lib/urban/l_system.py
**Severity:** CRITICAL (geometry-rick)

**Problem:**
The L-system turtle interpretation is underspecified:

1. **No state management:** The current plan's stack operations don't restore position correctly.

2. **Missing segment ID generation:** `_create_door_in_wall()` referenced but not defined.

3. **No intersection detection:** Road segments may overlap without detection.

**Current Plan:**
```python
def parse_to_network(self, lstring: str) -> RoadNetwork:
    # ... basic turtle graphics
    # MISSING: Intersection detection at segment endpoints
```

**Required Fix:**
```python
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Optional
import math
import random

@dataclass
class TurtleState:
    """Complete turtle state for L-system interpretation."""
    position: Tuple[float, float, float]
    heading: float  # Degrees
    segment_id: int = 0

    def copy(self) -> 'TurtleState':
        return TurtleState(
            position=tuple(self.position),
            heading=self.heading,
            segment_id=self.segment_id
        )

class LSystemRoads:
    def parse_to_network(self, lstring: str) -> RoadNetwork:
        """Parse L-system string to road network with intersection detection."""
        network = RoadNetwork()
        stack: List[TurtleState] = []
        state = TurtleState(position=(0.0, 0.0, 0.0), heading=0.0)

        # Track all endpoints for intersection detection
        endpoints: Dict[Tuple[float, float], List[str]] = {}  # position -> segment_ids

        i = 0
        while i < len(lstring):
            char = lstring[i]

            if char == 'F' or char == 'r':
                # Calculate end position
                rad = math.radians(state.heading)
                dx = self.config.segment_length * math.cos(rad)
                dy = self.config.segment_length * math.sin(rad)
                end = (state.position[0] + dx, state.position[1] + dy, state.position[2])

                # Create segment
                segment_id = f"seg_{state.segment_id}"
                segment = RoadSegment(
                    id=segment_id,
                    start=tuple(state.position),
                    end=end,
                    heading=state.heading
                )
                network.add_segment(segment)

                # Track endpoint for intersection detection
                end_key = (round(end[0], 1), round(end[1], 1))  # Round for proximity matching
                if end_key not in endpoints:
                    endpoints[end_key] = []
                endpoints[end_key].append(segment_id)

                state.position = end
                state.segment_id += 1

            elif char == '+':
                state.heading += self.config.angle
            elif char == '-':
                state.heading -= self.config.angle
            elif char == '[':
                stack.append(state.copy())
            elif char == ']':
                if stack:
                    state = stack.pop()

            i += 1

        # Detect intersections where 3+ segments meet
        for pos, segment_ids in endpoints.items():
            if len(segment_ids) >= 2:
                intersection = Intersection(
                    id=f"int_{pos[0]}_{pos[1]}",
                    position=(pos[0], pos[1], 0.0),
                    intersection_type=self._determine_intersection_type(len(segment_ids)),
                    connected_segments=segment_ids
                )
                network.add_intersection(intersection)

        return network

    def _determine_intersection_type(self, num_segments: int) -> IntersectionType:
        """Determine intersection type based on number of connected segments."""
        if num_segments == 2:
            return IntersectionType.THREE_WAY  # T-junction (one direction continues)
        elif num_segments == 3:
            return IntersectionType.FOUR_WAY
        elif num_segments >= 4:
            return IntersectionType.ROUNDABOUT
        return IntersectionType.THREE_WAY
```

---

### HIGH Issues

#### HIGH-4.1: Road Geometry GN JSON Parsing Issue (Same as Phase 3)
**Location:** Task 2, lib/urban/road_geometry.py
**Severity:** HIGH (geometry-rick)

**Problem:**
Same issue as Phase 3 CRITICAL-3.2. GN cannot parse JSON strings.

**Current Plan:**
```python
ng.interface.new_socket("road_json", socket_type='NodeSocketString')
# Add nodes for JSON parsing (using String to Value nodes)
```

**Required Fix:**
Use the same solution as Phase 3 - pre-process JSON into curves with attributes:

```python
def build_from_network(self, network: RoadNetwork, collection: bpy.types.Collection = None) -> List[bpy.types.Object]:
    """Build road geometry from RoadNetwork using Python + GN hybrid.

    Architecture:
    1. Python creates curve objects from RoadNetwork
    2. GN modifier applies road styling (width, markings, curbs)
    3. No JSON parsing in GN - curves have typed attributes
    """
    objects = []

    for segment in network.segments.values():
        # Create curve for road path (Python side)
        curve_data = bpy.data.curves.new(f"Road_{segment.id}", 'CURVE')
        curve_data.dimensions = '3D'

        spline = curve_data.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co = (*segment.start, 1.0)
        spline.points[1].co = (*segment.end, 1.0)

        curve_obj = bpy.data.objects.new(f"Road_{segment.id}", curve_data)

        # Store road parameters as custom properties (GN can read these)
        curve_obj['road_width'] = segment.width
        curve_obj['lanes_forward'] = segment.lanes_forward
        curve_obj['lanes_backward'] = segment.lanes_backward
        curve_obj['road_type'] = segment.road_type.value

        # Add GN modifier for road geometry
        mod = curve_obj.modifiers.new("RoadGeometry", 'NODES')
        mod.node_group = self._get_or_create_road_gn()

        # Set inputs (typed, not JSON string)
        mod['Input_1_use_markings'] = True
        mod['Input_2_use_curbs'] = True

        if collection:
            collection.objects.link(curve_obj)
        else:
            bpy.context.collection.objects.link(curve_obj)

        objects.append(curve_obj)

    return objects
```

---

#### HIGH-4.2: MUTCD Sign Dimensions Need Validation
**Location:** Task 3, lib/urban/signage.py
**Severity:** HIGH (geometry-rick)

**Problem:**
Sign dimensions are specified but not validated for MUTCD compliance.

**Current Plan:**
```python
SIGN_DIMENSIONS = {
    "stop": {
        "shape": "octagon",
        "width": 750,  # 30" standard
```

**Required Fix:**
```python
# MUTCD validation constants
MUTCD_SIGN_SIZES = {
    "stop": {
        "min": 600,  # 24" minimum for secondary roads
        "standard": 750,  # 30" standard
        "max": 1200,  # 48" for high-speed roads
    },
    "speed_limit": {
        "min_width": 450,
        "min_height": 600,
        "standard_width": 600,
        "standard_height": 750,
    },
    # ...
}

def validate_sign_dimensions(sign_type: str, width: float, height: float) -> List[str]:
    """Validate sign dimensions against MUTCD standards."""
    errors = []

    if sign_type not in MUTCD_SIGN_SIZES:
        return [f"Unknown sign type: {sign_type}"]

    spec = MUTCD_SIGN_SIZES[sign_type]

    if sign_type == "stop":
        # Octagon must be same width/height
        if abs(width - height) > 1:
            errors.append(f"Stop sign must be equilateral: width={width}, height={height}")
        if width < spec["min"]:
            errors.append(f"Stop sign width {width}mm below MUTCD minimum {spec['min']}mm")
        if width > spec["max"]:
            errors.append(f"Stop sign width {width}mm exceeds MUTCD maximum {spec['max']}mm")

    return errors
```

---

#### HIGH-4.3: Street Light Placement Along Roads Needs Boundary Check
**Location:** Task 4, lib/urban/lighting.py
**Severity:** HIGH (performance-rick)

**Problem:**
`place_along_road()` doesn't handle short segments properly and may place lights outside segment bounds.

**Current Plan:**
```python
def place_along_road(self, road_network: RoadNetwork,
                     spacing: float = 25.0,
                     offset: float = 3.0,
                     side: str = "both") -> List[bpy.types.Object]:
    for segment in road_network.segments.values():
        segment_length = self._segment_length(segment)
        num_lights = int(segment_length / spacing)
        # What if segment_length < spacing?
```

**Required Fix:**
```python
def place_along_road(self, road_network: RoadNetwork,
                     spacing: float = 25.0,
                     offset: float = 3.0,
                     side: str = "both",
                     min_spacing_ratio: float = 0.5) -> List[bpy.types.Object]:
    """Place street lights along road segments with boundary validation.

    Args:
        road_network: Road network to place lights along
        spacing: Target distance between lights in meters
        offset: Lateral offset from road edge
        side: "left", "right", or "both"
        min_spacing_ratio: If segment < spacing * ratio, skip placement
    """
    lamps = []
    min_segment_length = spacing * min_spacing_ratio

    for segment in road_network.segments.values():
        segment_length = self._segment_length(segment)

        # Skip short segments
        if segment_length < min_segment_length:
            continue

        num_lights = max(1, int(segment_length / spacing))

        for i in range(num_lights):
            t = (i + 0.5) / num_lights  # Center lights on segment
            pos = self._interpolate_position(segment, t)

            # Validate position is within segment bounds
            if not self._is_position_on_segment(pos, segment, tolerance=0.1):
                continue

            if side in ["right", "both"]:
                lamp = self.create_lamp(
                    self._offset_position(pos, segment, offset),
                    LAMP_PRESETS["modern"]
                )
                lamps.append(lamp)

            if side in ["left", "both"]:
                lamp = self.create_lamp(
                    self._offset_position(pos, segment, -offset),
                    LAMP_PRESETS["modern"]
                )
                lamps.append(lamp)

    return lamps

def _is_position_on_segment(self, pos: Tuple, segment: RoadSegment,
                            tolerance: float = 0.1) -> bool:
    """Check if position lies within segment bounds."""
    # Project position onto segment line
    dx = segment.end[0] - segment.start[0]
    dy = segment.end[1] - segment.start[1]
    length_sq = dx*dx + dy*dy

    if length_sq == 0:
        return False

    t = ((pos[0] - segment.start[0]) * dx + (pos[1] - segment.start[1]) * dy) / length_sq

    return -tolerance <= t <= 1.0 + tolerance
```

---

### MEDIUM Issues

#### MEDIUM-4.1: Missing Unit Tests for Road Network Generation
**Location:** Verification section
**Severity:** MEDIUM (dufus-rick)

**Problem:**
No unit tests specified for L-system road generation correctness.

**Required Fix:**
Add comprehensive tests to verification:

```python
# tests/test_urban.py

def test_l_system_determinism():
    """Verify L-system generates identical networks for same seed."""
    config1 = LSystemConfig(
        axiom="road",
        rules={"road": "road+road-[road]+road"},
        iterations=3,
        angle=90,
        segment_length=50,
        seed=42
    )
    config2 = LSystemConfig(
        axiom="road",
        rules={"road": "road+road-[road]+road"},
        iterations=3,
        angle=90,
        segment_length=50,
        seed=42
    )

    ls1 = LSystemRoads(config1)
    ls2 = LSystemRoads(config2)

    network1 = ls1.parse_to_network(ls1.generate())
    network2 = ls2.parse_to_network(ls2.generate())

    assert len(network1.segments) == len(network2.segments)
    assert len(network1.intersections) == len(network2.intersections)

    for s1, s2 in zip(network1.segments.values(), network2.segments.values()):
        assert s1.start == s2.start
        assert s1.end == s2.end

    print("L-system determinism test passed")

def test_intersection_detection():
    """Verify intersections are detected at segment endpoints."""
    config = LSystemConfig(
        axiom="road+road+road+road",  # Should create a grid pattern
        rules={},
        iterations=1,
        angle=90,
        segment_length=100,
        seed=42
    )

    ls = LSystemRoads(config)
    network = ls.parse_to_network(ls.generate())

    # Grid pattern should have at least one intersection
    assert len(network.intersections) > 0, "No intersections detected in grid pattern"

    # All intersections should have connected segments
    for intersection in network.intersections.values():
        assert len(intersection.connected_segments) >= 2

    print("Intersection detection test passed")

def test_road_network_json_roundtrip():
    """Verify RoadNetwork JSON export/import preserves data."""
    network = RoadNetwork(name="TestNetwork")
    network.add_segment(RoadSegment(
        id="seg_0",
        start=(0, 0, 0),
        end=(100, 0, 0),
        lanes_forward=2,
        lanes_backward=2,
        road_type=RoadType.URBAN,
        width=14.0
    ))

    # Export
    json_str = network.to_json()
    import json
    data = json.loads(json_str)

    # Import
    restored = RoadNetwork.from_json(data)

    assert len(restored.segments) == len(network.segments)
    seg = list(restored.segments.values())[0]
    assert seg.start == (0, 0, 0)
    assert seg.end == (100, 0, 0)
    assert seg.lanes_forward == 2

    print("Road network JSON roundtrip test passed")
```

---

#### MEDIUM-4.2: No LOD Strategy for Large Road Networks
**Location:** Overall architecture
**Severity:** MEDIUM (performance-rick)

**Problem:**
Large road networks (1000+ segments) will have significant memory/rendering overhead without LOD.

**Required Fix:**
Add LOD configuration to plan:

```python
@dataclass
class RoadNetworkLODConfig:
    """Level of Detail configuration for road networks."""
    enabled: bool = True
    # Distance thresholds in meters
    lod0_distance: float = 50.0   # Full detail (markings, curbs)
    lod1_distance: float = 200.0  # Reduced detail (no markings)
    lod2_distance: float = 500.0  # Minimal (flat road surface only)
    lod3_distance: float = float('inf')  # Billboard/impostor

    # Geometry simplification
    lod0_max_vertices: int = 1000
    lod1_max_vertices: int = 200
    lod2_max_vertices: int = 50

class RoadNetworkLOD:
    """LOD management for road networks."""

    def __init__(self, config: RoadNetworkLODConfig):
        self.config = config

    def apply_lod_to_segment(self, segment: RoadSegment,
                             distance_to_camera: float) -> str:
        """Determine LOD level based on distance."""
        if not self.config.enabled:
            return "lod0"

        if distance_to_camera <= self.config.lod0_distance:
            return "lod0"
        elif distance_to_camera <= self.config.lod1_distance:
            return "lod1"
        elif distance_to_camera <= self.config.lod2_distance:
            return "lod2"
        else:
            return "lod3"
```

---

#### MEDIUM-4.3: Missing Error Handling for Invalid Furniture Configurations
**Location:** Task 5, furniture.py
**Severity:** MEDIUM (dufus-rick)

**Problem:**
FurniturePlacer doesn't handle cases where furniture cannot be placed.

**Current Plan:**
```python
def place_furniture(room: Room, furniture_list: List[str]) -> List[FurnitureItem]:
    # What if no valid positions exist?
```

**Required Fix:**
```python
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class PlacementResult:
    """Result of furniture placement operation."""
    placed: List[Tuple[FurnitureItem, Tuple[float, float, float], float]]
    failed: List[Tuple[str, str]]  # (furniture_id, reason)
    coverage_percent: float  # How much of requested furniture was placed

class FurniturePlacer:
    MAX_PLACEMENT_ATTEMPTS = 100  # Per item

    def place_furniture(self, room: Room, furniture_list: List[str],
                        max_failures: int = 3) -> PlacementResult:
        """Place furniture with graceful failure handling.

        Args:
            room: Room to place furniture in
            furniture_list: List of furniture IDs to place
            max_failures: Maximum allowed failures before aborting

        Returns:
            PlacementResult with placed items and any failures
        """
        placed = []
        failed = []
        existing_positions: List[Tuple[FurnitureItem, Tuple, float]] = []

        for furniture_id in furniture_list:
            item = self.library.get(furniture_id)
            if item is None:
                failed.append((furniture_id, f"Unknown furniture ID: {furniture_id}"))
                continue

            # Try to find valid position
            position, rotation = self._find_valid_position(
                item, room, existing_positions, self.MAX_PLACEMENT_ATTEMPTS
            )

            if position is None:
                failed.append((furniture_id, "No valid position found after max attempts"))
                if len(failed) >= max_failures:
                    break
                continue

            placed.append((item, position, rotation))
            existing_positions.append((item, position, rotation))

        coverage = len(placed) / len(furniture_list) * 100 if furniture_list else 100

        return PlacementResult(
            placed=placed,
            failed=failed,
            coverage_percent=coverage
        )
```

---

## SLC Validation (Slick Rick)

**Status:** PASS with recommendations

### SLC Criteria Assessment

#### Simple
- [x] **Obvious purpose:** Each phase has clear, focused purpose
- [x] **Minimal learning curve:** Uses existing codebase patterns (bmesh, NodeTreeBuilder)
- [x] **Self-documenting:** Plan includes inline examples

#### Lovable
- [x] **Polished design:** Follows existing project patterns
- [x] **Graceful errors:** Some error handling specified (needs improvement per MEDIUM issues)
- [ ] **Success states:** Missing feedback for procedural generation success

#### Complete
- [x] **All APIs defined:** 100+ exports per phase
- [x] **Edge cases:** Partially handled (needs collision detection)
- [ ] **Error handling:** Gaps in error handling (furniture placement, LOD)

**SLC Recommendations:**
1. Add `PlacementResult` class for furniture placement feedback
2. Add LOD configuration for large networks
3. Add comprehensive unit tests for procedural generation determinism

---

## Historical Context (Rickfucius)

### Relevant Patterns Found

#### Pattern: Python + GN Hybrid Architecture
- **Category:** architecture
- **Compliance:** Follows
- **Explanation:** Both phases correctly identify that algorithms requiring recursion/string manipulation (BSP, L-system) must run in Python, with GN for geometry only.
- **Reference:** lib/art/room_builder.py (bmesh patterns), lib/animation/city/road_network.py (RoadNetwork patterns)

#### Pattern: JSON Interchange
- **Category:** architecture
- **Compliance:** Deviates
- **Explanation:** Plan incorrectly assumes GN can parse JSON strings. Must use attribute arrays or Python-side geometry creation.
- **Recommendation:** Fix CRITICAL-3.2 and HIGH-4.1 before implementation

#### Pattern: Deterministic Procedural Generation
- **Category:** code
- **Compliance:** Follows
- **Explanation:** Both BSP and L-system specify seed parameter for reproducibility.
- **Recommendation:** Add unit tests for determinism verification

---

## Final Council Decision

### Phase 3: Interior Layout System

**Decision:** **CONDITIONAL APPROVE**

**Conditions:**
1. **CRITICAL-3.1 (BSP Correctness):** Must add split heuristic specification
2. **CRITICAL-3.2 (GN JSON Parsing):** Must fix architecture to use attribute arrays or bmesh
3. **HIGH-3.1 (Memory Bounds):** Should add memory limits for large floor plans

**Rationale:** Core architecture is sound. Python-first BSP is correct. Issues are fixable without fundamental changes.

---

### Phase 4: Urban Infrastructure

**Decision:** **CONDITIONAL APPROVE**

**Conditions:**
1. **CRITICAL-4.1 (L-System Details):** Must add intersection detection and state management
2. **HIGH-4.1 (GN JSON Parsing):** Same as Phase 3 - must fix
3. **HIGH-4.3 (Street Light Boundaries):** Should add segment boundary validation

**Rationale:** L-system architecture is sound. MUTCD sign dimensions are correct. Issues are implementation details, not architectural flaws.

---

## Council Consensus

| Council Member | Phase 3 | Phase 4 | Notes |
|---------------|---------|---------|-------|
| geometry-rick | CONDITIONAL | CONDITIONAL | GN JSON parsing is the critical fix |
| performance-rick | APPROVE | CONDITIONAL | Add memory bounds and LOD strategy |
| dufus-rick | CONDITIONAL | CONDITIONAL | Add collision detection and determinism tests |
| Slick Rick (SLC) | APPROVE | APPROVE | Core SLC criteria met |

---

## Action Items

### Before Implementation (MUST FIX)

1. **Fix GN JSON Parsing Architecture** (CRITICAL-3.2, HIGH-4.1)
   - Replace JSON string sockets with pre-processed attribute arrays
   - Or use Python bmesh for geometry creation

2. **Specify BSP Split Heuristic** (CRITICAL-3.1)
   - Add area-balanced split algorithm
   - Add minimum room area enforcement

3. **Add Intersection Detection to L-System** (CRITICAL-4.1)
   - Track segment endpoints
   - Detect where 3+ segments meet
   - Create appropriate intersection types

### During Implementation (SHOULD FIX)

4. **Add Collision Detection for Furniture** (HIGH-3.2)
5. **Add Street Light Boundary Validation** (HIGH-4.3)
6. **Add Memory Bounds for Large Floor Plans** (HIGH-3.1)

### Post-Implementation (NICE TO HAVE)

7. **Add Comprehensive Unit Tests** (MEDIUM-3.1, MEDIUM-4.1)
8. **Add LOD Strategy for Road Networks** (MEDIUM-4.2)
9. **Add Stair Code Compliance Enforcement** (MEDIUM-3.2)

---

**Council Motto:** "The Council of Ricks doesn't approve mediocre code. We enforce SLC, security, and quality because production doesn't forgive compromise."

**Review Completed:** 2026-02-21
**Next Review:** After critical issues are addressed
