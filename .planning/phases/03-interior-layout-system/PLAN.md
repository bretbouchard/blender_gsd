---
phase: 03-interior-layout-system
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - lib/interiors/__init__.py
  - lib/interiors/types.py
  - lib/interiors/bsp_solver.py
  - lib/interiors/floor_plan.py
  - lib/interiors/walls.py
  - lib/interiors/flooring.py
  - lib/interiors/ceiling.py
  - lib/interiors/staircase.py
  - lib/interiors/furniture.py
  - lib/interiors/details.py
  - lib/interiors/room_types.py
  - lib/interiors/preset_loader.py
  - configs/interiors/room_types.yaml
  - configs/interiors/furniture_library.yaml
  - configs/interiors/flooring_patterns.yaml
  - configs/interiors/detail_presets.yaml
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Python BSP algorithm generates valid floor plans with rooms"
    - "Floor plan exports to JSON format consumable by GN"
    - "GN Wall Builder consumes JSON and creates wall geometry"
    - "Door and window libraries provide reusable opening components"
    - "Flooring generator creates procedural patterns"
    - "Ceiling system creates ceilings with fixtures"
    - "Staircase generator creates procedural staircases"
    - "Furniture placement engine positions furniture in rooms"
    - "Interior detail system adds moldings and wainscoting"
  artifacts:
    - path: "lib/interiors/bsp_solver.py"
      provides: "BSP floor plan generation in Python"
      exports: ["BSPSolver", "FloorPlan", "Room", "Connection"]
    - path: "lib/interiors/floor_plan.py"
      provides: "Floor plan JSON export/import"
      exports: ["export_floor_plan", "load_floor_plan", "FloorPlanEncoder"]
    - path: "lib/interiors/walls.py"
      provides: "GN Wall Builder from JSON"
      exports: ["create_wall_builder_gn", "WallBuilderConfig"]
    - path: "lib/interiors/flooring.py"
      provides: "Procedural flooring patterns"
      exports: ["FlooringGenerator", "FlooringPattern"]
    - path: "lib/interiors/furniture.py"
      provides: "Furniture placement engine"
      exports: ["FurniturePlacer", "FurnitureItem", "PlacementRule"]
  key_links:
    - from: "lib/interiors/bsp_solver.py"
      to: "lib/interiors/floor_plan.py"
      via: "FloorPlan dataclass"
      pattern: "FloorPlan.*rooms.*connections"
    - from: "lib/interiors/floor_plan.py"
      to: "lib/interiors/walls.py"
      via: "JSON export/import"
      pattern: "export_floor_plan.*json"
    - from: "configs/interiors/room_types.yaml"
      to: "lib/interiors/room_types.py"
      via: "preset_loader"
      pattern: "load.*room.*preset"
---

<objective>
Implement the Interior Layout System for procedural room and interior generation.

Purpose: Create a hybrid Python + Geometry Nodes architecture where BSP floor plan generation runs in Python (because GN lacks recursion), outputting JSON consumed by GN wall builders and interior systems.

Output: Complete interior layout module with 8 requirements implemented (REQ-IL-01 through REQ-IL-08).
</objective>

<execution_context>
@/Users/bretbouchard/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bretbouchard/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
@lib/art/room_builder.py
@lib/art/set_types.py
@lib/geometry_nodes/node_builder.py

## Critical Architecture Decision

**BSP Algorithm runs in Python, NOT pure Geometry Nodes.**

Rationale:
- GN has no loops or recursion capabilities
- BSP requires arbitrary depth subdivision
- Python can iterate to any depth needed
- Output is JSON that GN can consume

This hybrid approach:
1. Python pre-processes floor plan layout
2. JSON encodes room polygons, connections, openings
3. GN reads JSON and builds geometry

## JSON Interchange Format

```json
{
  "version": "1.0",
  "dimensions": {"width": 10.0, "height": 8.0},
  "rooms": [
    {
      "id": "room_0",
      "type": "living_room",
      "polygon": [[0,0], [5,0], [5,4], [0,4]],
      "doors": [{"wall": 1, "position": 0.5, "width": 0.9}],
      "windows": [{"wall": 0, "position": 0.3, "width": 1.2}]
    }
  ],
  "connections": [
    {"room_a": "room_0", "room_b": "room_1", "door_id": "door_0"}
  ]
}
```
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create Interior Types and BSP Solver Foundation</name>
  <files>
    lib/interiors/__init__.py
    lib/interiors/types.py
    lib/interiors/bsp_solver.py
  </files>
  <action>
    Create the foundation types and BSP solver for floor plan generation.

    **lib/interiors/types.py:**
    - Import dataclasses, enums, typing
    - Define RoomType enum: living_room, bedroom, kitchen, bathroom, dining, office, hallway, closet, utility
    - Define Room dataclass: id, type, polygon (List[Tuple[float,float]]), doors, windows, height, tags
    - Define Door dataclass: wall_index, position (0-1 normalized), width, height, style
    - Define Window dataclass: wall_index, position, width, height, sill_height, style
    - Define Connection dataclass: room_a_id, room_b_id, door_id, connection_type (doorway/arch/none)
    - Define FloorPlan dataclass: version, dimensions, rooms, connections, metadata
    - Define BSPNode dataclass: is_leaf, bounds, split_axis, split_position, left_child, right_child, room (if leaf)
    - Add to_dict/from_dict methods for serialization
    - Add validation methods for polygon validity, door/window placement constraints

    **lib/interiors/bsp_solver.py:**
    - Import random, math, typing
    - Define Rect helper class: x, y, width, height with contains, intersects, area methods
    - Define BSPConfig dataclass: min_room_area, max_room_area, split_ratio_range, room_height_default
    - Define BSPSolver class:
      - __init__(self, config: BSPConfig = None, seed: int = None)
      - generate(self, width: float, height: float, room_count: int) -> FloorPlan
      - _subdivide(self, rect: Rect, depth: int, max_rooms: int) -> BSPNode
      - _should_split(self, node: BSPNode, remaining_rooms: int) -> bool
      - _choose_split_axis(self, rect: Rect) -> str (horizontal/vertical)
      - _choose_split_position(self, rect: Rect, axis: str) -> float
      - _leaf_nodes(self, root: BSPNode) -> List[BSPNode]
      - _create_room_from_leaf(self, leaf: BSPNode, room_type: RoomType) -> Room
      - _connect_rooms(self, rooms: List[Room]) -> List[Connection]
      - _find_adjacent_walls(self, room_a: Room, room_b: Room) -> List[Tuple[int, int]]
      - _create_door_in_wall(self, room: Room, wall_index: int, position: float) -> Door
    - Ensure deterministic output via seed parameter
    - Handle edge cases: too small rooms, invalid splits, max depth exceeded

    **lib/interiors/__init__.py:**
    - Create package with version = "0.1.0"
    - Export key types and BSPSolver
    - Add __all__ list

    **Do NOT:**
    - Do not implement pure GN BSP (impossible without recursion)
    - Do not use bpy in bsp_solver.py (pure Python, testable outside Blender)
    - Do not hardcode room dimensions (use config)
  </action>
  <verify>
    python3 -c "from lib.interiors import BSPSolver, FloorPlan, Room, RoomType; s = BSPSolver(seed=42); fp = s.generate(10, 8, 4); assert len(fp.rooms) == 4; print('BSP test passed')"
  </verify>
  <done>
    BSPSolver generates deterministic floor plans with specified room counts, FloorPlan serializes to dict, Room polygons are valid convex shapes.
  </done>
</task>

<task type="auto">
  <name>Task 2: Create Floor Plan JSON Export/Import and GN Wall Builder</name>
  <files>
    lib/interiors/floor_plan.py
    lib/interiors/walls.py
  </files>
  <action>
    Create floor plan serialization and Geometry Nodes wall builder.

    **lib/interiors/floor_plan.py:**
    - Import json, dataclasses
    - Define FloorPlanEncoder(json.JSONEncoder) for FloorPlan serialization
    - export_floor_plan(floor_plan: FloorPlan, filepath: str) -> None
      - Write JSON with version, dimensions, rooms, connections
      - Include validation before export
      - Pretty-print with indent=2 for human readability
    - load_floor_plan(filepath: str) -> FloorPlan
      - Parse JSON and reconstruct FloorPlan
      - Validate version compatibility
      - Handle missing/malformed data gracefully
    - export_floor_plan_dict(floor_plan: FloorPlan) -> Dict
      - Convert to JSON-serializable dict without file I/O
    - validate_floor_plan(plan: FloorPlan) -> List[str]
      - Check room polygon validity
      - Verify door/window positions within bounds
      - Check connections reference valid rooms
      - Return list of error messages (empty = valid)

    **lib/interiors/walls.py:**
    - Import from geometry_nodes.node_builder import NodeTreeBuilder
    - Define WallBuilderConfig dataclass:
      - wall_height, wall_thickness
      - default_material
      - opening_margin (space around doors/windows)
    - Define WallSegment dataclass:
      - start_point, end_point (2D coords)
      - height, thickness
      - openings: List[Union[Door, Window]]
    - create_wall_builder_gn(config: WallBuilderConfig) -> GeometryNodeTree
      - Use NodeTreeBuilder to create "Interior_Wall_Builder" node group
      - Inputs: wall_segments (collection of WallSegment data via JSON string)
      - Process:
        1. Parse JSON input string
        2. For each wall segment, create extruded curve
        3. Apply boolean subtraction for openings
        4. Join all walls into single geometry
      - Outputs: Geometry
    - build_walls_from_floor_plan(plan: FloorPlan, config: WallBuilderConfig) -> bpy.types.Object
      - Convert floor plan to wall segments
      - Create wall object with geometry nodes modifier
      - Pass floor plan JSON as modifier input
      - Return the wall mesh object
    - create_wall_opening_gn(opening_type: str, width: float, height: float) -> GeometryNodeTree
      - Create reusable node group for door/window openings
      - Support door, window, arch opening types
      - Return geometry ready for boolean subtraction

    **Do NOT:**
    - Do not use bpy.ops (use bmesh and direct API)
    - Do not create geometry in Python loop (use GN for mesh generation)
    - Do not hardcode wall dimensions
  </action>
  <verify>
    python3 -c "
from lib.interiors import BSPSolver, export_floor_plan, load_floor_plan
s = BSPSolver(seed=42)
fp = s.generate(10, 8, 3)
export_floor_plan(fp, '/tmp/test_floor_plan.json')
loaded = load_floor_plan('/tmp/test_floor_plan.json')
assert len(loaded.rooms) == len(fp.rooms)
print('Floor plan I/O test passed')
"
  </verify>
  <done>
    Floor plans export to valid JSON, load correctly, and GN wall builder can create wall geometry from JSON input.
  </done>
</task>

<task type="auto">
  <name>Task 3: Create Door/Window Library and Flooring Generator</name>
  <files>
    lib/interiors/doors_windows.py
    lib/interiors/flooring.py
    configs/interiors/flooring_patterns.yaml
  </files>
  <action>
    Create door/window component library and procedural flooring generator.

    **lib/interiors/doors_windows.py:**
    - Define DoorStyle enum: PANEL_6, PANEL_4, FLUSH, BARN, FRENCH, POCKET, DUTCH, LOUVER, GLASS
    - Define WindowStyle enum: DOUBLE_HUNG, SINGLE_HUNG, CASEMENT, AWNING, PICTURE, BAY, SLIDER, SKYLIGHT
    - Define DoorGeometry dataclass: style, width, height, thickness, frame_width, panel_count
    - Define WindowGeometry dataclass: style, width, height, frame_width, num_panes, glass_thickness
    - Define DoorLibrary class:
      - __init__(self, preset_path: str = None)
      - get_door(style: DoorStyle, width: float = 0.9, height: float = 2.1) -> DoorGeometry
      - create_door_mesh(door: DoorGeometry) -> bpy.types.Mesh
      - create_door_gn(style: DoorStyle) -> GeometryNodeTree (procedural door GN)
    - Define WindowLibrary class:
      - __init__(self, preset_path: str = None)
      - get_window(style: WindowStyle, width: float = 1.2, height: float = 1.4) -> WindowGeometry
      - create_window_mesh(window: WindowGeometry) -> bpy.types.Mesh
      - create_window_gn(style: WindowStyle) -> GeometryNodeTree
    - create_door_frame(width: float, height: float, frame_width: float, frame_depth: float) -> bmesh
    - create_window_frame(width: float, height: float, frame_width: float, num_panes: int) -> bmesh
    - Add presets for common door/window sizes (residential, commercial)

    **lib/interiors/flooring.py:**
    - Define FlooringPattern enum: PLANK, TILE, HERRINGBONE, CHEVRON, PARQUET, CHECKERBOARD, HEXAGON, RANDOM_STONE
    - Define FlooringConfig dataclass:
      - pattern: FlooringPattern
      - plank_width, plank_length, gap_width
      - tile_width, tile_length, grout_width
      - random_seed, variation_amount (color/size variation)
      - material_a, material_b (for two-material patterns)
    - Define FlooringGenerator class:
      - __init__(self, config: FlooringConfig)
      - generate_flooring(room_polygon: List[Tuple[float,float]]) -> bpy.types.Object
      - create_pattern_gn(config: FlooringConfig) -> GeometryNodeTree
        - Create GN tree that generates flooring pattern
        - Use grid + randomization for variation
        - Apply UV coordinates for material mapping
      - calculate_pattern_bounds(config: FlooringConfig) -> Tuple[float, float]
    - create_plank_pattern(config: FlooringConfig) -> GeometryNodeTree
    - create_tile_pattern(config: FlooringConfig) -> GeometryNodeTree
    - create_herringbone_pattern(config: FlooringConfig) -> GeometryNodeTree
    - create_chevron_pattern(config: FlooringConfig) -> GeometryNodeTree
    - create_parquet_pattern(config: FlooringConfig) -> GeometryNodeTree
    - create_hexagon_pattern(config: FlooringConfig) -> GeometryNodeTree

    **configs/interiors/flooring_patterns.yaml:**
    - Define presets for common flooring:
      - hardwood_oak_plank: {pattern: PLANK, plank_width: 0.12, plank_length: 1.2}
      - hardwood_walnut_herringbone: {pattern: HERRINGBONE, plank_width: 0.08, plank_length: 0.4}
      - tile_ceramic_12x12: {pattern: TILE, tile_width: 0.3, tile_length: 0.3}
      - tile_marble_hexagon: {pattern: HEXAGON, tile_width: 0.15}
      - parquet_english: {pattern: PARQUET, plank_width: 0.05}
      - checkerboard_marble: {pattern: CHECKERBOARD, tile_width: 0.6}
    - Include material hints and variation settings

    **Do NOT:**
    - Do not use bpy.ops for mesh creation
    - Do not hardcode dimensions (use config/presets)
    - Do not create overly complex GN trees (keep maintainable)
  </action>
  <verify>
    python3 -c "
from lib.interiors import DoorLibrary, WindowLibrary, FlooringGenerator, FlooringPattern
dl = DoorLibrary()
door = dl.get_door('panel_6')
assert door.width == 0.9
wl = WindowLibrary()
win = wl.get_window('double_hung')
assert win.width == 1.2
fg = FlooringGenerator(FlooringPattern.PLANK)
print('Doors/windows/flooring test passed')
"
  </verify>
  <done>
    Door and window libraries provide reusable components, flooring generator creates procedural patterns via GN.
  </done>
</task>

<task type="auto">
  <name>Task 4: Create Ceiling System and Staircase Generator</name>
  <files>
    lib/interiors/ceiling.py
    lib/interiors/staircase.py
    configs/interiors/ceiling_fixtures.yaml
  </files>
  <action>
    Create ceiling system with fixtures and procedural staircase generator.

    **lib/interiors/ceiling.py:**
    - Define CeilingType enum: FLAT, VAULTED, COFFERED, CATHEDRAL, TRAY, DROP
    - Define FixtureType enum: RECESSED_LIGHT, PENDANT, CHANDELIER, CEILING_FAN, SKYLIGHT, SPEAKER, VENT
    - Define CeilingConfig dataclass:
      - ceiling_type: CeilingType
      - height: float
      - thickness: float
      - vault_angle: float (for vaulted/cathedral)
      - coffer_depth, coffer_width (for coffered)
      - tray_depth, tray_levels (for tray)
    - Define Fixture dataclass:
      - fixture_type: FixtureType
      - position: Tuple[float, float, float]
      - rotation: float
      - scale: float
      - model_path: str (optional external asset)
    - Define CeilingSystem class:
      - __init__(self, config: CeilingConfig)
      - create_ceiling(room_polygon: List[Tuple[float,float]]) -> bpy.types.Object
      - create_ceiling_gn(config: CeilingConfig) -> GeometryNodeTree
        - Generate ceiling based on type
        - Handle different ceiling geometries
      - add_fixture(fixture: Fixture) -> bpy.types.Object
      - layout_recessed_lights(room_polygon, spacing: float) -> List[Fixture]
        - Calculate optimal light placement grid
      - layout_ceiling_fan(room_polygon) -> Fixture
        - Center placement
    - create_coffered_pattern(width: float, depth: float, beam_width: float) -> GeometryNodeTree
    - create_tray_ceiling(depth: float, levels: int) -> GeometryNodeTree

    **lib/interiors/staircase.py:**
    - Define StairType enum: STRAIGHT, L_SHAPED, U_SHAPED, SPIRAL, CURVED, WINDER
    - Define StairConfig dataclass:
      - stair_type: StairType
      - total_rise: float (floor to floor height)
      - total_run: float (horizontal distance)
      - tread_depth, tread_height, tread_width
      - riser_height, nosing_overhang
      - handrail_height, handrail_width
      - stringer_type: string, mono_stringer, floating
      - landing_width (for L/U shaped)
    - Define StaircaseGenerator class:
      - __init__(self, config: StairConfig)
      - generate(start_point: Tuple[float,float,float], direction: Tuple[float,float]) -> bpy.types.Object
      - calculate_step_count(total_rise: float, riser_height: float) -> int
      - calculate_comfort_ratio(tread_depth: float, riser_height: float) -> float
        - Use building code rule: 2*rise + run = 63-65cm
      - create_straight_stair_gn(config: StairConfig) -> GeometryNodeTree
      - create_l_shaped_stair_gn(config: StairConfig) -> GeometryNodeTree
      - create_u_shaped_stair_gn(config: StairConfig) -> GeometryNodeTree
      - create_spiral_stair_gn(config: StairConfig) -> GeometryNodeTree
    - create_treads_gn(tread_count: int, config: StairConfig) -> GeometryNodeTree
    - create_risers_gn(config: StairConfig) -> GeometryNodeTree
    - create_handrail_gn(config: StairConfig) -> GeometryNodeTree
    - create_stringer_gn(config: StairConfig) -> GeometryNodeTree
    - validate_stair_config(config: StairConfig) -> List[str]
      - Check building code compliance
      - Warn about uncomfortable ratios
      - Check minimum headroom clearance

    **configs/interiors/ceiling_fixtures.yaml:**
    - Define fixture presets:
      - recessed_light_4in: {diameter: 0.1, trim_width: 0.02}
      - recessed_light_6in: {diameter: 0.15, trim_width: 0.025}
      - pendant_minimal: {shade_diameter: 0.25, cord_length: 0.6}
      - chandelier_3arm: {arm_count: 3, drop: 0.5}
      - ceiling_fan_52in: {blade_count: 5, blade_length: 0.66}

    **Do NOT:**
    - Do not violate building code rules for stairs
    - Do not create unsupported ceiling types
    - Do not ignore headroom clearance in stair design
  </action>
  <verify>
    python3 -c "
from lib.interiors import CeilingSystem, StaircaseGenerator, StairType, CeilingType
cs = CeilingSystem(CeilingType.COFFERED)
sg = StaircaseGenerator(StairType.STRAIGHT)
ratio = sg.calculate_comfort_ratio(0.28, 0.18)
assert 0.62 <= ratio <= 0.65, f'Comfort ratio {ratio} out of range'
print('Ceiling/staircase test passed')
"
  </verify>
  <done>
    Ceiling system creates various ceiling types with fixtures, staircase generator creates code-compliant stairs via GN.
  </done>
</task>

<task type="auto">
  <name>Task 5: Create Furniture Placement Engine and Interior Details</name>
  <files>
    lib/interiors/furniture.py
    lib/interiors/details.py
    lib/interiors/room_types.py
    lib/interiors/preset_loader.py
    configs/interiors/room_types.yaml
    configs/interiors/furniture_library.yaml
    configs/interiors/detail_presets.yaml
  </files>
  <action>
    Create furniture placement engine and interior detail system.

    **lib/interiors/room_types.py:**
    - Define RoomTypeConfig dataclass:
      - room_type: str
      - min_area, max_area: float
      - typical_furniture: List[str] (furniture IDs)
      - required_fixtures: List[str] (for kitchens/baths)
      - wall_clearance: float
      - traffic_paths: List[Tuple[float, float]] (waypoint pairs)
    - Define RoomTypeManager class:
      - __init__(self, preset_path: str = None)
      - get_config(room_type: str) -> RoomTypeConfig
      - get_furniture_list(room_type: str, area: float) -> List[str]
      - get_clearance_requirements(room_type: str) -> Dict[str, float]
    - Define TrafficPathPlanner class:
      - calculate_traffic_paths(room: Room) -> List[Tuple[Door, Door]]
      - check_furniture_blocking(furniture: FurnitureItem, paths: List) -> bool

    **lib/interiors/furniture.py:**
    - Define FurnitureCategory enum: SEATING, TABLE, STORAGE, BED, DESK, DECOR, APPLIANCE, LIGHTING
    - Define FurnitureItem dataclass:
      - id: str
      - name: str
      - category: FurnitureCategory
      - width, depth, height: float
      - clearance_front, clearance_sides: float
      - wall_adjacent: bool (needs wall behind)
      - center_allowed: bool (can be in room center)
      - model_path: str (optional)
      - variations: List[str] (alternative IDs)
    - Define PlacementRule dataclass:
      - furniture_id: str
      - allowed_walls: List[int] (wall indices, or [-1] for any)
      - distance_from_wall: float
      - distance_from_door: float
      - align_with: List[str] (other furniture IDs to align)
      - avoid_overlap: List[str]
    - Define FurniturePlacer class:
      - __init__(self, library_path: str = None)
      - load_library(filepath: str) -> None
      - place_furniture(room: Room, furniture_list: List[str]) -> List[FurnitureItem]
      - _find_valid_position(item: FurnitureItem, room: Room, existing: List) -> Tuple[float,float,float]
      - _check_clearance(item: FurnitureItem, position: Tuple, room: Room) -> bool
      - _check_traffic_paths(item: FurnitureItem, position: Tuple, room: Room) -> bool
      - _apply_placement_rules(item: FurnitureItem, room: Room, rules: List[PlacementRule]) -> Tuple
      - optimize_layout(room: Room, furniture: List[FurnitureItem]) -> List[FurnitureItem]
        - Try to improve placement based on spacing and balance
    - create_furniture_object(item: FurnitureItem, position: Tuple, rotation: float) -> bpy.types.Object

    **lib/interiors/details.py:**
    - Define DetailType enum: BASEBOARD, CROWN_MOLDING, CHAIR_RAIL, WAINSCOTING, PICTURE_RAIL, COVE_MOLDING
    - Define MoldingProfile enum: RECTANGULAR, QUARTER_ROUND, OGE, COVE, DENTIL, EGG_AND_DART
    - Define InteriorDetail dataclass:
      - detail_type: DetailType
      - profile: MoldingProfile
      - height: float
      - depth: float
      - material: str
    - Define WainscotingStyle enum: RAISED_PANEL, FLAT_PANEL, BEADBOARD, BOARD_AND_BATTEN, SHIPLAP
    - Define WainscotingConfig dataclass:
      - style: WainscotingStyle
      - height: float
      - rail_height, stile_width: float
      - panel_inset: float
      - cap_molding: bool
    - Define InteriorDetailSystem class:
      - __init__(self, preset_path: str = None)
      - add_baseboard(wall_length: float, config: InteriorDetail) -> bpy.types.Object
      - add_crown_molding(wall_length: float, config: InteriorDetail) -> bpy.types.Object
      - add_chair_rail(wall_length: float, height: float, config: InteriorDetail) -> bpy.types.Object
      - add_wainscoting(wall: WallSegment, config: WainscotingConfig) -> bpy.types.Object
      - create_molding_profile_gn(profile: MoldingProfile) -> GeometryNodeTree
      - create_wainscoting_gn(config: WainscotingConfig) -> GeometryNodeTree
    - calculate_molding_length(room: Room) -> float

    **lib/interiors/preset_loader.py:**
    - load_room_types(filepath: str) -> Dict[str, RoomTypeConfig]
    - load_furniture_library(filepath: str) -> Dict[str, FurnitureItem]
    - load_detail_presets(filepath: str) -> Dict[str, InteriorDetail]
    - load_flooring_presets(filepath: str) -> Dict[str, FlooringConfig]
    - Generic YAML/JSON preset loading with caching

    **configs/interiors/room_types.yaml:**
    ```yaml
    living_room:
      min_area: 12.0
      max_area: 50.0
      typical_furniture:
        - sofa_3seat
        - coffee_table
        - armchair
        - tv_stand
        - side_table
      required_fixtures: []
      wall_clearance: 0.05
      traffic_paths:
        - [door_0, window_0]
    bedroom:
      min_area: 9.0
      max_area: 25.0
      typical_furniture:
        - bed_queen
        - nightstand
        - dresser
        - wardrobe
      wall_clearance: 0.05
    kitchen:
      min_area: 7.0
      max_area: 25.0
      required_fixtures:
        - sink
        - refrigerator
        - stove
      wall_clearance: 0.1
    bathroom:
      min_area: 4.0
      max_area: 12.0
      required_fixtures:
        - toilet
        - sink
        - shower_or_tub
      wall_clearance: 0.02
    ```

    **configs/interiors/furniture_library.yaml:**
    ```yaml
    sofa_3seat:
      name: 3-Seat Sofa
      category: seating
      width: 2.2
      depth: 0.9
      height: 0.85
      clearance_front: 0.6
      clearance_sides: 0.3
      wall_adjacent: true
      center_allowed: false
    bed_queen:
      name: Queen Bed
      category: bed
      width: 1.5
      depth: 2.0
      height: 0.5
      clearance_front: 0.6
      clearance_sides: 0.4
      wall_adjacent: true
    coffee_table:
      name: Coffee Table
      category: table
      width: 1.2
      depth: 0.6
      height: 0.4
      clearance_front: 0.4
      clearance_sides: 0.3
      wall_adjacent: false
      center_allowed: true
    ```

    **configs/interiors/detail_presets.yaml:**
    ```yaml
    baseboard_modern:
      detail_type: baseboard
      profile: rectangular
      height: 0.1
      depth: 0.02
      material: wood_white
    crown_molding_victorian:
      detail_type: crown_molding
      profile: oge
      height: 0.15
      depth: 0.1
      material: plaster_white
    wainscoting_raised:
      style: raised_panel
      height: 1.0
      rail_height: 0.08
      stile_width: 0.08
      panel_inset: 0.02
      cap_molding: true
    ```

    **Do NOT:**
    - Do not place furniture blocking doors or traffic paths
    - Do not ignore clearance requirements
    - Do not place wall-adjacent furniture in room center
  </action>
  <verify>
    python3 -c "
from lib.interiors import FurniturePlacer, Room, RoomType, InteriorDetailSystem
fp = FurniturePlacer()
room = Room(id='r1', type=RoomType.LIVING_ROOM, polygon=[(0,0),(5,0),(5,4),(0,4)])
furniture = fp.place_furniture(room, ['sofa_3seat', 'coffee_table'])
assert len(furniture) == 2
ids = InteriorDetailSystem()
print('Furniture/details test passed')
"
  </verify>
  <done>
    Furniture placement engine positions furniture with clearance checks, interior detail system adds moldings and wainscoting via GN.
  </done>
</task>

<task type="auto">
  <name>Task 6: Update Package Exports and Version Bump</name>
  <files>
    lib/interiors/__init__.py
  </files>
  <action>
    Update the __init__.py with all exports and bump version.

    **lib/interiors/__init__.py:**
    - Import all types from types.py
    - Import BSPSolver from bsp_solver.py
    - Import floor plan functions from floor_plan.py
    - Import wall functions from walls.py
    - Import door/window classes from doors_windows.py
    - Import flooring from flooring.py
    - Import ceiling from ceiling.py
    - Import staircase from staircase.py
    - Import furniture from furniture.py
    - Import details from details.py
    - Import room_types from room_types.py
    - Import preset_loader functions
    - Define __all__ list with all public exports (100+ exports)
    - Set __version__ = "0.1.0"
    - Add module docstring summarizing capabilities
  </action>
  <verify>
    python3 -c "
from lib.interiors import (
    BSPSolver, FloorPlan, Room, RoomType,
    export_floor_plan, load_floor_plan,
    DoorLibrary, WindowLibrary,
    FlooringGenerator, FlooringPattern,
    CeilingSystem, CeilingType,
    StaircaseGenerator, StairType,
    FurniturePlacer, InteriorDetailSystem,
    __version__
)
print(f'lib.interiors v{__version__} - all exports verified')
"
  </verify>
  <done>
    lib.interiors package exports all public APIs, version is 0.1.0, module is importable.
  </done>
</task>

</tasks>

<verification>
## Module Verification
- BSPSolver generates valid floor plans with correct room counts
- Floor plan JSON export/import roundtrips correctly
- All preset YAML files are valid and loadable
- Geometry node trees are created without errors
- Furniture placement respects clearances and traffic paths
- Stair configs pass building code validation

## Integration Verification
- Floor plan JSON is consumable by GN wall builder
- Wall builder creates geometry from JSON input
- Door/window components fit in wall openings
- Flooring patterns cover room polygons completely
- Furniture placement works with room types

## Code Quality
- All functions have type hints
- All dataclasses have to_dict/from_dict methods
- No bpy imports in pure Python modules (bsp_solver, types)
- No bpy.ops usage anywhere
- Comprehensive __all__ exports
</verification>

<success_criteria>
- BSPSolver generates floor plans deterministically via seed
- Floor plan exports to JSON format consumable by GN
- GN wall builder creates wall geometry from JSON
- Door/window library provides 9 door styles, 8 window styles
- Flooring generator supports 8 pattern types
- Ceiling system supports 6 ceiling types with fixtures
- Staircase generator creates 5 stair types with code compliance
- Furniture placement engine places furniture with clearance checks
- Interior detail system adds 6 detail types including wainscoting
- Package exports 100+ public APIs
- Version 0.1.0
</success_criteria>

<output>
After completion, create `.planning/phases/03-interior-layout-system/03-SUMMARY.md` with:
- Implemented requirements (REQ-IL-01 through REQ-IL-08)
- Module summary with line counts
- Key integration points
- Configuration files created
</output>
