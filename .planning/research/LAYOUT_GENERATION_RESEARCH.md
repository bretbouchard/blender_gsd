# Interior/Architectural Layout Generation - Research

**Researched:** 2026-02-21
**Domain:** Procedural floor plan generation, interior layout algorithms, architectural modeling in Blender
**Confidence:** MEDIUM

## Summary

This research covers algorithms and techniques for procedurally generating interior spaces including houses, apartments, and rooms. The primary focus is on approaches implementable with Blender Geometry Nodes and Python scripting.

Key implementation areas include:
1. BSP (Binary Space Partitioning) for room division - most practical for Blender implementation
2. Room adjacency graphs for spatial relationship modeling
3. Rule-based furniture placement with ergonomic constraints
4. Procedural wall generation with door/window openings
5. Interior detail systems (stairs, cabinets, trim)

**Primary recommendation:** Use BSP for floor plan subdivision combined with room adjacency graphs for spatial relationships. Implement wall generation using CSG operations for door/window openings. Use constraint-based furniture placement algorithms.

---

## Part 1: Layout Generation Approaches

### 1.1 BSP (Binary Space Partitioning) - RECOMMENDED

**What:** Recursively divides space into rectangular regions using horizontal/vertical cuts

**Algorithm:**
```python
# Source: BSP tree floor plan generation
# Based on game development dungeon generation techniques

def binary_space_partition(space, min_width, min_height):
    """
    BSP Algorithm for room division.

    1. Start with bounding rectangle
    2. Randomly choose horizontal or vertical split
    3. Split if resulting regions meet minimum size
    4. Recursively split until minimum size reached
    5. Generate rooms within leaf nodes
    6. Connect rooms with corridors
    """
    rooms = []
    queue = [space]

    while queue:
        region = queue.pop(0)

        # Check if region is large enough to split
        if region.width < min_width * 2 or region.height < min_height * 2:
            rooms.append(region)
            continue

        # Choose split direction based on proportions
        if region.width > region.height:
            split_horizontal = False
        elif region.height > region.width:
            split_horizontal = True
        else:
            split_horizontal = random() > 0.5

        # Perform split
        if split_horizontal:
            split_at = random(min_height, region.height - min_height)
            queue.append(region.subregion(0, split_at))
            queue.append(region.subregion(split_at, region.height))
        else:
            split_at = random(min_width, region.width - min_width)
            queue.append(region.subregion(0, split_at))
            queue.append(region.subregion(split_at, region.width))

    return rooms
```

**When to use:** Default approach for residential layouts, most compatible with Blender

**Pros:**
- Simple implementation
- Produces rectangular rooms (standard in architecture)
- Easy to control room sizes with minimum constraints
- Natural corridor generation between regions

**Cons:**
- Can produce monotonous layouts without variation
- Rectangular-only room shapes
- Requires post-processing for more organic designs

---

### 1.2 Wave Function Collapse (WFC)

**What:** Constraint-based tile generation inspired by quantum mechanics

**Algorithm:**
1. **Observation Phase:** Find cell with lowest entropy (fewest possible states)
2. **Collapse:** Randomly select state for that cell
3. **Propagation:** Update adjacent cells based on adjacency rules
4. **Iteration:** Repeat until all cells collapsed or contradiction occurs

**Key Parameters:**
- N value: Pattern size (typically 3x3)
- Periodic: Whether boundaries loop
- Heuristic: Selection strategy (Entropy, MRV, Scanline)
- Symmetry: Rotation/reflection operations

**When to use:** Complex tile-based interior layouts with strict adjacency rules (e.g., dungeon generation with room types)

**Implementation Note:** Best suited for modular room tiles rather than continuous floor plans. Consider for interior decoration placement.

---

### 1.3 Room Adjacency Graph

**What:** Represents rooms as nodes and connections as edges in a graph structure

**Room Categorization:**
```
Social Zones:    Living room, dining room, bathroom
Service Zones:   Kitchen, pantry, laundry
Private Zones:   Bedrooms, master bedroom, private bathrooms
Circulation:     Hallways, corridors, foyers
```

**Graph Structure:**
```python
class RoomNode:
    room_type: str          # bedroom, living, kitchen, etc.
    min_area: float         # Minimum square meters
    preferred_aspect: float # Width/height ratio
    windows_required: bool
    natural_light: bool
    privacy_level: int      # 1-5 scale

class RoomEdge:
    room_a: RoomNode
    room_b: RoomNode
    connection_type: str    # door, open, archway
    preferred_adjacency: float  # -1 to 1 (avoid to require)
```

**Adjacency Rules:**
| Room A | Room B | Preferred Connection |
|--------|--------|---------------------|
| Kitchen | Dining | Direct/Open (0.9) |
| Living | Dining | Open (0.8) |
| Master Bedroom | Master Bath | Direct (0.9) |
| Bedrooms | Bathrooms | Nearby (0.6) |
| Kitchen | Garage | Direct (0.7) |
| Bedrooms | Living | Avoid direct (0.2) |

**When to use:** Planning phase before geometric layout; ensures functional relationships

---

### 1.4 Diffusion Models (AI-Assisted) - EMERGING

**State of Art (2024-2025):**
- **Floorplan-Diffusion:** Uses latent diffusion for floor plan generation
- **HouseDiffusion:** High-quality residential layouts
- **House-GAN:** Graph-constrained GAN for layouts

**Note:** These require significant ML infrastructure. Consider for future integration but not for initial Blender implementation.

---

### 1.5 L-System / Shape Grammar

**What:** Recursive rewriting rules for architectural generation

**CGA Grammar (Computer Generated Architecture):**
```
Rule: Facade -> GroundFloor | UpperFloors | Roof
Rule: GroundFloor -> Door | Window* | Base
Rule: UpperFloors -> Floor* (repeat)
Rule: Floor -> Window* | Ledge
Rule: Window -> Frame | Glass | Sill
```

**When to use:** Facade generation, building exteriors, complex hierarchical structures

**CityEngine Reference:** Esri's CityEngine uses CGA for procedural building generation

---

## Part 2: Room Generation Components

### 2.1 Wall Generation with Openings

**Algorithm: CSG (Constructive Solid Geometry)**

```python
# Source: THREE.js BSP wall generation patterns

def create_wall_with_openings(start, end, height, thickness, openings):
    """
    Create wall geometry with door/window openings using CSG.

    1. Generate solid wall segment
    2. For each opening, subtract cuboid from wall
    3. Merge resulting geometry
    """
    # Create base wall
    wall_mesh = create_box(
        width=(end - start).length,
        height=height,
        depth=thickness
    )

    # Subtract openings using CSG
    for opening in openings:
        opening_box = create_box(
            width=opening.width,
            height=opening.height,
            depth=thickness * 1.1  # Slightly larger for clean boolean
        )
        # Position opening
        opening_box.position = (
            opening.position_x,
            opening.height / 2 + opening.sill_height,
            0
        )
        # Boolean subtract
        wall_mesh = csg_subtract(wall_mesh, opening_box)

    return wall_mesh
```

**Opening Placement Rules:**
```python
# Door placement validation
def validate_door_placement(wall, door_position):
    # Check minimum distance from corners
    min_corner_distance = 0.4  # meters
    # Check wall is wide enough
    min_wall_width = 0.9  # meters
    # Check no overlap with other openings
    min_opening_spacing = 0.3  # meters

# Window placement validation
def validate_window_placement(wall, window_position):
    # Check minimum sill height
    min_sill_height = 0.9  # meters (standard)
    # Check minimum head height
    min_head_height = 2.1  # meters
    # Check exterior wall (has outdoor access)
    if not wall.is_exterior:
        return False
```

---

### 2.2 Floor/Ceiling Generation

**Blender Implementation:**
```python
# Using bmesh for procedural floor/ceiling

def create_floor_polygon(room_vertices, thickness=0.2):
    """
    Create floor mesh from room boundary vertices.

    Algorithm:
    1. Triangulate room polygon (ear clipping or constrained delaunay)
    2. Extrude downward for floor thickness
    """
    import bmesh

    bm = bmesh.new()

    # Create vertices
    verts = [bm.verts.new((v.x, v.y, 0)) for v in room_vertices]

    # Create face (assumes convex or proper vertex ordering)
    face = bm.faces.new(verts)

    # Extrude for thickness
    geom = bmesh.ops.extrude_face_region(bm, geom=[face])
    bmesh.ops.translate(bm, vec=(0, 0, -thickness), verts=geom['verts'])

    return bm
```

---

### 2.3 Traffic Flow Patterns

**Principles:**
1. Main circulation paths should be 1.0-1.2m minimum width
2. Avoid traffic through furniture conversation areas
3. Natural flow from entry to living spaces
4. Service access (kitchen to dining) should be direct

**Flow Graph Generation:**
```python
def generate_traffic_flow(floor_plan):
    """
    Calculate optimal traffic flow paths.

    1. Identify entry points (doors)
    2. Create graph of accessible spaces
    3. Calculate shortest paths between key nodes
    4. Identify high-traffic corridors
    """
    entry_points = [d for d in floor_plan.doors if d.is_entry]

    # Key destinations
    destinations = [
        floor_plan.get_room('living'),
        floor_plan.get_room('kitchen'),
        floor_plan.get_room('master_bedroom')
    ]

    # Calculate paths using A* or Dijkstra
    paths = []
    for entry in entry_points:
        for dest in destinations:
            path = find_path(entry.center, dest.center, floor_plan)
            paths.append(path)

    # Identify high-traffic areas (overlap zones)
    traffic_heatmap = calculate_path_overlap(paths)

    return traffic_heatmap
```

---

## Part 3: Interior Detail Systems

### 3.1 Staircase Generation

**Standard Dimensions (IRC):**
| Parameter | Minimum | Typical | Maximum |
|-----------|---------|---------|---------|
| Tread Depth | 254mm (10") | 280mm (11") | 355mm (14") |
| Riser Height | - | 180mm (7") | 196mm (7.75") |
| Stair Width | 914mm (36") | 1067mm (42") | - |
| Headroom | 2032mm (6'8") | - | - |

**Golden Rule:** 2 * Riser + Tread = 630-650mm (comfortable stride)

**Stair Types:**
```python
STAIR_CONFIGS = {
    'straight': {
        'segments': 1,
        'angle_change': 0,
        'space_efficiency': 0.6
    },
    'l_shaped': {
        'segments': 2,
        'angle_change': 90,
        'space_efficiency': 0.8
    },
    'u_shaped': {
        'segments': 2,
        'angle_change': 180,
        'space_efficiency': 0.9
    },
    'spiral': {
        'segments': 1,
        'angle_change': 360,
        'space_efficiency': 0.5
    }
}

def generate_staircase(floor_height, stair_type='straight', config=None):
    """
    Generate procedural staircase.

    Algorithm:
    1. Calculate number of steps: floor_height / riser_height
    2. Calculate total run: steps * tread_depth
    3. Generate step geometry
    4. Add railings if needed
    """
    riser = config.get('riser_height', 0.18)
    tread = config.get('tread_depth', 0.28)

    num_steps = round(floor_height / riser)
    actual_riser = floor_height / num_steps

    steps = []
    for i in range(num_steps):
        step = create_step(
            depth=tread,
            width=config.get('width', 1.0),
            thickness=0.04,
            nosing=0.025  # Typical 25mm overhang
        )
        step.position = (i * tread, 0, i * actual_riser)
        steps.append(step)

    return steps
```

---

### 3.2 Kitchen Cabinet Layout

**Work Triangle Concept:**
- Connects refrigerator, sink, and stove
- Total perimeter: 3.6m - 6.6m (12-22 feet)
- Each leg: 1.2m - 2.7m (4-9 feet)
- Optimal distance between points: 90cm

**Layout Types:**
| Type | Description | Min Area | Efficiency |
|------|-------------|----------|------------|
| U-Shaped | 3 connected counters | 8 m2 | Highest |
| L-Shaped | 2 perpendicular counters | 6 m2 | High |
| Galley | 2 parallel counters | 5 m2 | Medium |
| Single Wall | All on one wall | 4 m2 | Lowest |

**Cabinet Generation:**
```python
def generate_kitchen_cabinets(room, layout_type='l_shaped'):
    """
    Generate kitchen cabinet layout based on room shape.

    Algorithm:
    1. Identify available wall lengths
    2. Place refrigerator (typically near entry)
    3. Place sink (under window if available, near plumbing)
    4. Place stove/range (with ventilation access)
    5. Fill remaining space with cabinets
    6. Validate work triangle constraints
    """
    cabinets = []

    # Standard cabinet dimensions
    BASE_HEIGHT = 0.87  # 870mm
    BASE_DEPTH = 0.60   # 600mm
    WALL_HEIGHT = 0.72  # 720mm
    WALL_DEPTH = 0.35   # 350mm

    # Find longest walls for layout
    walls = sorted(room.walls, key=lambda w: w.length, reverse=True)

    # Place appliances (simplified)
    refrigerator = place_appliance('refrigerator', walls[0])
    sink = place_appliance('sink', walls[1] if len(walls) > 1 else walls[0])
    stove = place_appliance('stove', walls[0])

    # Validate work triangle
    triangle_length = (
        distance(refrigerator, sink) +
        distance(sink, stove) +
        distance(stove, refrigerator)
    )

    if triangle_length < 3.6 or triangle_length > 6.6:
        # Adjust placement
        pass

    # Generate cabinets
    for wall in walls:
        wall_cabinets = generate_wall_cabinets(
            wall,
            base_height=BASE_HEIGHT,
            base_depth=BASE_DEPTH,
            exclude=[refrigerator, sink, stove]
        )
        cabinets.extend(wall_cabinets)

    return cabinets
```

---

### 3.3 Bathroom Fixture Placement

**Standard Dimensions:**
| Fixture | Width | Depth | Height | Clearance |
|---------|-------|-------|--------|-----------|
| Toilet | 380mm | 660mm | 400mm | 530mm front |
| Sink | 550mm | 410mm | 850mm | 530mm front |
| Bathtub | 720mm | 1520-1680mm | 580mm | 600mm |
| Shower | 900mm | 900mm | 2000mm | - |

**Placement Algorithm:**
```python
def place_bathroom_fixtures(room, fixtures_required):
    """
    Place bathroom fixtures based on room shape and plumbing constraints.

    Constraints:
    - Toilet needs 750mm width minimum
    - Sink needs 550mm width minimum
    - All fixtures need 530mm front clearance
    - Door swing shouldn't hit fixtures
    """
    placements = []

    # Prioritize plumbing wall (wet wall)
    plumbing_wall = identify_plumbing_wall(room)

    for fixture in fixtures_required:
        valid_positions = []

        for wall in room.walls:
            for position in wall.available_positions():
                if validate_fixture_placement(fixture, position, room):
                    valid_positions.append(position)

        # Score positions by efficiency
        best_position = max(valid_positions, key=lambda p: score_position(p, room))
        placements.append((fixture, best_position))

    return placements
```

---

### 3.4 Baseboards, Crown Molding, Chair Rails

**Standard Profiles:**
| Element | Height | Typical Use |
|---------|--------|-------------|
| Baseboard | 75-150mm | All rooms |
| Chair Rail | 750-900mm | Dining rooms |
| Crown Molding | 75-200mm | Formal rooms |
| Wainscoting | 900-1200mm | Dining, entryways |

**Procedural Generation:**
```python
def generate_baseboard(room, height=0.1, profile='colonial'):
    """
    Generate baseboard trim around room perimeter.

    Algorithm:
    1. Get room perimeter as curve
    2. Sweep profile along curve
    3. Handle corners (miter joints)
    4. Account for door openings
    """
    perimeter = room.get_perimeter_curve()
    profile_curve = load_profile(profile)

    # Sweep profile along perimeter
    baseboard = sweep_along_curve(profile_curve, perimeter)

    # Cut at door openings
    for door in room.doors:
        baseboard = cut_at_opening(baseboard, door)

    return baseboard
```

---

## Part 4: Flooring/Carpeting Systems

### 4.1 Hardwood Patterns

**Pattern Types:**
| Pattern | Description | Waste Factor | Difficulty |
|---------|-------------|--------------|------------|
| Straight | Parallel planks | 5-10% | Easy |
| Diagonal | 45-degree angle | 10-15% | Medium |
| Herringbone | 90-degree V-pattern | 15-20% | Hard |
| Chevron | 45/60-degree V-pattern | 20-25% | Hard |
| Parquet | Geometric squares | 15-20% | Medium |

**Herringbone Generation (Geometry Nodes):**
```python
def generate_herringbone_floor(bounds, plank_length, plank_width):
    """
    Generate herringbone pattern floor.

    Algorithm:
    1. Create single plank
    2. Rotate 45 degrees
    3. Instance in alternating directions
    4. Fill bounds with grid
    5. Trim to room boundary
    """
    planks = []

    # Calculate grid
    spacing_x = plank_length * 0.707  # cos(45)
    spacing_y = plank_width * 2 * 0.707

    # Generate alternating pattern
    for row in range(num_rows):
        for col in range(num_cols):
            x = col * spacing_x
            y = row * spacing_y

            # Alternate direction each cell
            rotation = 45 if (row + col) % 2 == 0 else -45

            plank = create_plank(plank_length, plank_width)
            plank.rotate(rotation)
            plank.position = (x, y, 0)
            planks.append(plank)

    # Trim to room boundary
    planks = trim_to_boundary(planks, bounds)

    return planks
```

---

### 4.2 Tile Patterns

**Common Patterns:**
| Pattern | Tile Shape | Description |
|---------|------------|-------------|
| Grid | Square | Simple aligned grid |
| Offset/Brick | Square/Rectangle | 50% offset rows |
| Hexagonal | Hexagon | Honeycomb pattern |
| Basket Weave | Rectangle | Interlocking pairs |
| Pinwheel | Square + Small | Small tiles at corners |

**Tile Generation:**
```python
def generate_tile_floor(bounds, tile_size, pattern='grid', grout_width=0.003):
    """
    Generate tiled floor with specified pattern.
    """
    if pattern == 'grid':
        return generate_grid_tiles(bounds, tile_size, grout_width)
    elif pattern == 'offset':
        return generate_offset_tiles(bounds, tile_size, grout_width)
    elif pattern == 'hexagonal':
        return generate_hexagonal_tiles(bounds, tile_size, grout_width)
```

---

## Part 5: Wall Decor Placement

### 5.1 Gallery Wall Layout Algorithm

**Layout Types:**
1. **Symmetric:** Formal, balanced grid
2. **Top-Aligned:** Unified top edge
3. **Bottom-Aligned:** Unified bottom edge
4. **Centered:** Expands from center
5. **Salon Style:** Organic, eclectic mix

**Algorithm:**
```python
def generate_gallery_wall(wall_bounds, artworks, layout_type='salon'):
    """
    Generate artwork placement on wall.

    Algorithm (Rectangle Packing):
    1. Sort artworks by size (largest first)
    2. Place largest as anchor
    3. Fill surrounding space with smaller pieces
    4. Optimize for visual balance
    """
    # Sort by height descending
    sorted_artworks = sorted(artworks, key=lambda a: a.height, reverse=True)

    placements = []
    available_space = wall_bounds

    for artwork in sorted_artworks:
        # Find best position using scoring
        best_pos = None
        best_score = -1

        for x, y in available_space.valid_positions(artwork.size):
            score = score_artwork_position(artwork, (x, y), placements)
            if score > best_score:
                best_score = score
                best_pos = (x, y)

        if best_pos:
            placements.append((artwork, best_pos))
            available_space = subtract_space(available_space, artwork.size, best_pos)

    return placements

def score_artwork_position(artwork, position, existing):
    """
    Score position based on:
    - Proximity to eye level (1450mm center)
    - Spacing from other artworks (40-50mm)
    - Wall margins (300mm+ from edges)
    - Visual balance
    """
    EYE_LEVEL = 1.45  # meters
    IDEAL_SPACING = 0.05  # 50mm

    score = 0

    # Eye level score
    center_y = position[1] + artwork.height / 2
    score -= abs(center_y - EYE_LEVEL) * 10

    # Spacing score
    for other, other_pos in existing:
        distance = calculate_distance(position, other_pos)
        if distance < IDEAL_SPACING:
            score -= 100  # Invalid
        else:
            score += min(distance, 0.1)  # Reward proper spacing

    return score
```

**Spacing Guidelines:**
- Frame spacing: 40-50mm between pieces
- Wall margins: 300mm+ from ceiling and side walls
- Bottom margin: 750mm+ from floor
- Eye level: 1450mm (center of artwork)

---

### 5.2 Mirror Placement Rules

```python
MIRROR_PLACEMENT_RULES = {
    'bathroom': {
        'above_vanity': True,
        'height': 'eye_level',
        'width': 'match_vanity',
        'min_height': 0.6
    },
    'entryway': {
        'position': 'opposite_door',
        'height': 'full_length',
        'width': 0.6
    },
    'bedroom': {
        'avoid': 'facing_bed',  # Feng shui / comfort
        'prefer': 'closet_adjacent',
        'type': 'full_length'
    },
    'living_room': {
        'position': 'reflect_window',  # Maximize light
        'height': 'eye_level',
        'width': 'proportional'
    }
}
```

---

## Part 6: Scale Reference - Standard Dimensions

### 6.1 Room Dimensions

**Bedroom (Master):**
| Comfort Level | Width | Depth | Area |
|--------------|-------|-------|------|
| Minimum | 3.6m | 4.8m | 17.3 m2 |
| Comfortable | 3.9m | 5.1m | 19.9 m2 |
| Luxury | 4.2m | 7.5m | 31.5 m2 |

**Bedroom (Secondary):**
| Comfort Level | Width | Depth | Area |
|--------------|-------|-------|------|
| Minimum | 3.3m | 4.5m | 14.9 m2 |

**Living Room:**
| Comfort Level | Width | Depth | Area |
|--------------|-------|-------|------|
| Minimum | 3.9m | 4.5m | 17.6 m2 |
| Comfortable | 4.5m | 5.1m | 23.0 m2 |
| Luxury | 5.1m | 6.6m | 33.7 m2 |

**Kitchen:**
| Configuration | Min Area | Aisle Width |
|--------------|----------|-------------|
| Single-sided | 4 m2 | 900mm |
| Double-sided | 5 m2 | 1200mm |
| U-shaped | 8 m2 | 1200mm |

**Bathroom:**
| Type | Area | Notes |
|------|------|-------|
| Three-fixture | 3+ m2 | Toilet, sink, shower/tub |
| Two-fixture | 2-2.5 m2 | - |
| Half-bath | 1.1+ m2 | Toilet and sink only |

### 6.2 Door Dimensions

| Location | Width | Height | Notes |
|----------|-------|--------|-------|
| Main Entry | 900-1000mm | 2030mm | 36" minimum |
| Bedroom | 800mm | 2030mm | 32" minimum |
| Bathroom | 700-800mm | 2030mm | 28-32" |
| Interior Passage | 800mm | 2030mm | - |

### 6.3 Window Dimensions

| Type | Width | Height | Sill Height |
|------|-------|--------|-------------|
| Standard | 600-1200mm | 900-1500mm | 900mm |
| Picture | 1200-2400mm | 900-1800mm | 600mm |
| Egress | 600mm min | 600mm min | 1100mm max |
| Sliding | 1200-2400mm | 1200-1800mm | 0-300mm |

### 6.4 Ceiling Heights

| Building Type | Standard | Minimum | Luxury |
|--------------|----------|---------|--------|
| Residential - Living | 2.74m (9') | 2.40m | 3.0m+ |
| Residential - Kitchen/Bath | 2.44m | 2.20m | 2.74m |
| Commercial - Office | 2.8-3.5m | 2.6m | 4.0m+ |
| Commercial - Retail | 3.5-5.0m | 3.0m | 7.0m+ |

### 6.5 Hallway/Corridor Widths

| Type | Minimum | Comfortable |
|------|---------|-------------|
| Residential hallway | 900mm | 1000-1200mm |
| Residential stair | 900mm | 1000mm |
| Commercial corridor | 1200mm | 1500-1800mm |

### 6.6 Furniture Clearance

| Item | Clearance Required |
|------|-------------------|
| Bed (one side) | 600mm |
| Bed (both sides) | 600mm each |
| Dresser (drawer open) | 900mm |
| Dining table (seated) | 600mm |
| Dining table (walk behind) | 900mm |
| Sofa (traffic path) | 600mm |
| Wardrobe (swing door) | 900mm |
| Wardrobe (sliding door) | 400mm |

---

## Part 7: Blender Geometry Nodes Implementation

### 7.1 Node Group Architecture

```
layout_generator/
  floor_plan_generator/
    bsp_subdivision/
    room_generator/
    corridor_connector/
  wall_generator/
    wall_segment/
    opening_boolean/
    window_inserter/
    door_inserter/
  floor_ceiling/
    floor_from_room/
    ceiling_from_room/
  interior_details/
    staircase_generator/
    cabinet_layout/
    trim_generator/
```

### 7.2 Key Node Groups

**BSP Subdivision Node:**
```
Inputs:
  - Bounding Box (Vector)
  - Min Room Size (Vector)
  - Max Rooms (Integer)
  - Random Seed (Integer)

Outputs:
  - Room Bounds (Geometry)
  - Room IDs (Integer)
  - Adjacency List (Attribute)
```

**Wall Generator Node:**
```
Inputs:
  - Room Bounds (Geometry)
  - Wall Height (Float)
  - Wall Thickness (Float)
  - Door Positions (Attribute)
  - Window Positions (Attribute)

Outputs:
  - Wall Geometry (Geometry)
  - Opening Meshes (Geometry)
```

### 7.3 Attribute System

```python
# Custom attributes for room geometry
ROOM_ATTRIBUTES = {
    'room_id': 'INT',           # Unique room identifier
    'room_type': 'INT',         # Enum: bedroom, living, kitchen, etc.
    'zone': 'INT',              # social, service, private
    'floor_material': 'INT',    # Material index
    'wall_material': 'INT',     # Material index
    'ceiling_height': 'FLOAT',  # Per-room ceiling height
    'has_window': 'BOOL',       # Window flag
    'adjacent_rooms': 'INT[]',  # List of adjacent room IDs
}
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Room triangulation | Custom ear clipping | Blender's bmesh triangulation | Handles convex/concave |
| Boolean operations | Custom CSG | Blender Boolean modifier | Robust, handles edge cases |
| Path finding | A* from scratch | scipy.spatial or networkx | Battle-tested implementations |
| Collision detection | Custom overlap | Blender BVH tree | Optimized spatial queries |
| UV unwrapping | Manual UV calculation | Blender's smart project | Automatic, good results |

---

## Common Pitfalls

### Pitfall 1: Invalid Room Adjacency
**What goes wrong:** Kitchen not connected to dining, bedroom opens to bathroom
**Why it happens:** Graph not validated before geometric generation
**How to avoid:** Validate adjacency graph before BSP subdivision
**Warning signs:** Unreachable rooms, awkward circulation

### Pitfall 2: Door/Window Overlap
**What goes wrong:** Door and window occupy same wall segment
**Why it happens:** Independent placement without conflict checking
**How to avoid:** Maintain opening list per wall, check spacing constraints
**Warning signs:** Openings too close together

### Pitfall 3: Non-Standard Dimensions
**What goes wrong:** Stairs with irregular rise/run, doors too narrow
**Why it happens:** Procedural generation ignores building codes
**How to avoid:** Validate all dimensions against code requirements
**Warning signs:** Uncomfortable navigation, failed inspections

### Pitfall 4: Floating Point Drift
**What goes wrong:** Walls don't meet at corners, gaps in geometry
**Why it happens:** Accumulated floating point errors in BSP
**How to avoid:** Snap to grid at each step, use integer math where possible
**Warning signs:** Visible cracks, light leaks in renders

### Pitfall 5: Texture Stretching
**What goes wrong:** Flooring textures stretched at irregular room shapes
**Why it happens:** UV coordinates not normalized per surface
**How to avoid:** Use triplanar projection or box mapping for floors
**Warning signs:** Skewed tile patterns, elongated wood grain

---

## Open Questions

1. **Multi-Story Generation**
   - What we know: BSP works for single floor
   - What's unclear: Best approach for connecting multiple floors with stairs
   - Recommendation: Generate floors independently, place stairs first, adjust floor plans around them

2. **Organic Room Shapes**
   - What we know: BSP produces rectangular rooms
   - What's unclear: How to introduce L-shaped or irregular rooms
   - Recommendation: Post-process BSP results with room merging and corner cutting

3. **Style Transfer**
   - What we know: AI diffusion models can generate styled floor plans
   - What's unclear: Integration with Blender's procedural systems
   - Recommendation: Use AI for layout inspiration, not direct generation

---

## Sources

### Primary (HIGH confidence)
- BSP algorithm references from game development (roguelike dungeon generation)
- IRC (International Residential Code) for building standards
- Blender Python API documentation for bmesh and geometry nodes

### Secondary (MEDIUM confidence)
- WebSearch results on floor plan generation (Chinese academic papers, 2024-2025)
- Kitchen work triangle concept from interior design references
- Furniture placement algorithms from interior design AI research

### Tertiary (LOW confidence)
- Wave Function Collapse algorithm descriptions (game dev community)
- Diffusion model floor plan generation (recent research papers)
- Gallery wall layout optimization (interior design blogs)

---

## Metadata

**Confidence breakdown:**
- Layout algorithms: MEDIUM - BSP is well-established, others are more experimental
- Standard dimensions: HIGH - Based on building codes and industry standards
- Blender implementation: MEDIUM - Based on API knowledge, needs testing
- Interior design rules: MEDIUM - Based on established design principles

**Research date:** 2026-02-21
**Valid until:** 30 days for AI/ML approaches, 1 year for building codes and algorithms
