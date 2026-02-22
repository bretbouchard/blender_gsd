---
phase: 06-gn-extensions
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - lib/geometry_nodes/room_builder.py
  - lib/geometry_nodes/road_builder.py
  - lib/geometry_nodes/scatter.py
  - lib/geometry_nodes/asset_instances.py
  - lib/geometry_nodes/lod_system.py
  - lib/geometry_nodes/culling.py
  - lib/geometry_nodes/style_transfer.py
  - lib/geometry_nodes/__init__.py
  - assets/node_groups/room_builder.blend
  - assets/node_groups/road_builder.blend
  - tests/unit/test_gn_room_builder.py
  - tests/unit/test_gn_road_builder.py
  - tests/unit/test_gn_scatter.py
  - tests/unit/test_gn_lod.py
autonomous: true

must_haves:
  truths:
    - "Room Builder creates valid room geometry from JSON floor plans"
    - "Road Builder creates road meshes from JSON network data"
    - "Furniture scatter distributes instances on valid surfaces"
    - "Asset Instance Library normalizes scales across sources"
    - "LOD system switches geometry based on distance and instance count"
    - "Culling strategy removes off-screen instances from viewport"
  artifacts:
    - path: "lib/geometry_nodes/room_builder.py"
      provides: "RoomBuilder class consuming JSON floor plans"
      exports: ["RoomBuilder", "RoomConfig", "build_room_from_json"]
    - path: "lib/geometry_nodes/road_builder.py"
      provides: "RoadBuilder class consuming JSON road networks"
      exports: ["RoadBuilder", "RoadConfig", "build_road_from_json"]
    - path: "lib/geometry_nodes/scatter.py"
      provides: "Furniture scatter system with collision avoidance"
      exports: ["FurnitureScatter", "ScatterConfig", "scatter_on_surface"]
    - path: "lib/geometry_nodes/asset_instances.py"
      provides: "Asset instance library with scale normalization"
      exports: ["AssetInstanceLibrary", "NormalizedAsset", "create_instance_pool"]
    - path: "lib/geometry_nodes/lod_system.py"
      provides: "3-tier LOD system with distance/instance thresholds"
      exports: ["LODSystem", "LODConfig", "LODLevel", "apply_lod"]
    - path: "lib/geometry_nodes/culling.py"
      provides: "Frustum culling and distance-based culling"
      exports: ["CullingSystem", "CullingConfig", "apply_culling"]
    - path: "lib/geometry_nodes/style_transfer.py"
      provides: "Style transfer between asset collections"
      exports: ["StyleTransfer", "transfer_style"]
  key_links:
    - from: "lib/geometry_nodes/room_builder.py"
      to: "lib/geometry_nodes/node_builder.py"
      via: "NodeTreeBuilder for node creation"
      pattern: "NodeTreeBuilder\\("
    - from: "lib/geometry_nodes/road_builder.py"
      to: "lib/geometry_nodes/node_builder.py"
      via: "NodeTreeBuilder for node creation"
      pattern: "NodeTreeBuilder\\("
    - from: "lib/geometry_nodes/lod_system.py"
      to: "lib/geometry_nodes/instances.py"
      via: "InstanceController for LOD switching"
      pattern: "InstanceController\\."
---

<objective>
Build Geometry Nodes extension system for scene generation with LOD and culling.

Purpose: Fill gaps in GN capabilities for the Scene Generation System (Phase 5), enabling procedural room/road building from JSON, furniture scattering, asset scale normalization, and performance optimization through LOD/culling.

Output: 7 new Python modules, 2 blend files with node groups, unit tests for all modules. The LOD system implements 3-tier detail levels (full, decimated, billboard) with memory budget enforcement.
</objective>

<execution_context>
@/Users/bretbouchard/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bretbouchard/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/SCENE_GENERATION_MASTER_PLAN.md

# Existing GN patterns to follow
@lib/geometry_nodes/node_builder.py
@lib/geometry_nodes/instances.py
@lib/geometry_nodes/__init__.py

# Research for road building
@.planning/research/ROAD_SYSTEMS_RESEARCH.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create Room Builder Node Group System</name>
  <files>lib/geometry_nodes/room_builder.py</files>
  <action>
Create `lib/geometry_nodes/room_builder.py` implementing RoomBuilder class.

The RoomBuilder consumes JSON floor plan output from BSP solver (Phase 3) and creates Blender geometry node trees.

JSON input format (from Phase 3 BSP):
```json
{
  "version": "1.0",
  "rooms": [
    {
      "id": "room_0",
      "type": "living_room",
      "polygon": [[0,0], [5,0], [5,4], [0,4]],
      "doors": [{"wall": 1, "position": 0.5, "width": 0.9}],
      "windows": [{"wall": 0, "position": 0.3, "width": 1.2}]
    }
  ]
}
```

Implementation requirements:
1. RoomConfig dataclass with:
   - room_type: str
   - polygon: list of (x, y) tuples
   - height: float (default 2.8m)
   - wall_thickness: float (default 0.15m)
   - floor_material: str
   - wall_material: str

2. RoomBuilder class:
   - `__init__(self, builder: NodeTreeBuilder)`
   - `build_floor(config: RoomConfig) -> Node` - Creates floor mesh from polygon
   - `build_walls(config: RoomConfig, openings: list) -> Node` - Creates wall mesh with door/window cutouts
   - `build_ceiling(config: RoomConfig) -> Node` - Creates ceiling mesh
   - `build_room_from_json(json_data: dict) -> NodeTree` - Main entry point

3. Node tree structure:
   - Input: JSON string socket
   - Parse JSON -> Extract room configs
   - For each room: floor + walls + ceiling -> Join
   - Apply materials by room type
   - Output: Combined room geometry

Use NodeTreeBuilder from lib/geometry_nodes/node_builder.py for all node creation.

DO NOT use bpy.ops - use direct API calls (bpy.data.node_groups.new, etc.)
DO NOT hardcode node positions - use relative positioning
</action>
  <verify>
```bash
# Verify module created
test -f lib/geometry_nodes/room_builder.py && echo "room_builder.py exists"

# Verify imports work
python3 -c "from lib.geometry_nodes.room_builder import RoomBuilder, RoomConfig; print('Imports OK')"

# Verify class structure
python3 -c "
from lib.geometry_nodes.room_builder import RoomBuilder
assert hasattr(RoomBuilder, 'build_floor')
assert hasattr(RoomBuilder, 'build_walls')
assert hasattr(RoomBuilder, 'build_ceiling')
assert hasattr(RoomBuilder, 'build_room_from_json')
print('RoomBuilder methods OK')
"
```
  </verify>
  <done>
- RoomBuilder class with all methods implemented
- RoomConfig dataclass with room parameters
- build_room_from_json creates valid node tree from JSON input
- All tests pass
  </done>
</task>

<task type="auto">
  <name>Task 2: Create Road Builder Node Group System</name>
  <files>lib/geometry_nodes/road_builder.py</files>
  <action>
Create `lib/geometry_nodes/road_builder.py` implementing RoadBuilder class.

The RoadBuilder consumes JSON road network output from L-system (Phase 4) and creates Blender geometry node trees.

JSON input format (from Phase 4 L-System):
```json
{
  "version": "1.0",
  "nodes": [
    {"id": "node_0", "position": [0, 0], "type": "intersection_4way"},
    {"id": "node_1", "position": [50, 0], "type": "intersection_3way"}
  ],
  "edges": [
    {
      "id": "edge_0",
      "from": "node_0",
      "to": "node_1",
      "curve": [[0,0], [25,0], [50,0]],
      "lanes": 2,
      "width": 7.0
    }
  ]
}
```

Implementation requirements:
1. RoadConfig dataclass with:
   - lanes: int (1-4)
   - width: float (per lane: 3.5m)
   - has_sidewalk: bool
   - has_median: bool
   - surface_material: str ("asphalt", "concrete")
   - marking_style: str ("solid", "dashed", "double")

2. IntersectionConfig dataclass with:
   - type: str ("4way", "3way", "roundabout")
   - radius: float (for roundabout)
   - has_crosswalk: bool

3. RoadBuilder class:
   - `__init__(self, builder: NodeTreeBuilder)`
   - `build_road_segment(config: RoadConfig, curve_points: list) -> Node` - Creates road mesh from curve
   - `build_intersection(config: IntersectionConfig, position: tuple) -> Node` - Creates intersection geometry
   - `build_road_network(json_data: dict) -> NodeTree` - Main entry point

4. Node tree structure:
   - Input: JSON string socket
   - Parse JSON -> Extract edges and nodes
   - For each edge: Create curve -> Set radius -> Curve to Mesh -> Set material
   - For each node: Create intersection at position
   - Add lane markings (instance rectangles along centerline)
   - Join all geometry
   - Output: Combined road network

Reference ROAD_SYSTEMS_RESEARCH.md for standard dimensions:
- Lane width: 3.5-3.75m
- Shoulder: 1.5-3.0m
- Sidewalk: 1.5-2.5m

Use NodeTreeBuilder for all node creation.
</action>
  <verify>
```bash
# Verify module created
test -f lib/geometry_nodes/road_builder.py && echo "road_builder.py exists"

# Verify imports work
python3 -c "from lib.geometry_nodes.road_builder import RoadBuilder, RoadConfig, IntersectionConfig; print('Imports OK')"

# Verify class structure
python3 -c "
from lib.geometry_nodes.road_builder import RoadBuilder
assert hasattr(RoadBuilder, 'build_road_segment')
assert hasattr(RoadBuilder, 'build_intersection')
assert hasattr(RoadBuilder, 'build_road_network')
print('RoadBuilder methods OK')
"
```
  </verify>
  <done>
- RoadBuilder class with all methods implemented
- RoadConfig and IntersectionConfig dataclasses
- build_road_network creates valid node tree from JSON input
- All tests pass
  </done>
</task>

<task type="auto">
  <name>Task 3: Create Furniture Scatter System</name>
  <files>lib/geometry_nodes/scatter.py</files>
  <action>
Create `lib/geometry_nodes/scatter.py` implementing FurnitureScatter class.

The scatter system distributes furniture instances on room surfaces with collision avoidance and density control.

Implementation requirements:
1. ScatterConfig dataclass with:
   - density: float (instances per square meter, 0.1-2.0)
   - min_distance: float (minimum spacing between instances, 0.3m)
   - edge_offset: float (distance from walls, 0.1m)
   - collision_avoidance: bool
   - seed: int (for deterministic random)
   - weight_by_surface: dict (floor types -> weight multipliers)

2. FurnitureCategory enum:
   - SEATING (chairs, sofas)
   - TABLE (dining, coffee, desks)
   - STORAGE (cabinets, shelves)
   - DECOR (plants, lamps, art)
   - APPLIANCE (TVs, electronics)

3. FurnitureScatter class:
   - `__init__(self, builder: NodeTreeBuilder)`
   - `scatter_on_floor(surface_geometry, config: ScatterConfig, category: FurnitureCategory) -> Node`
   - `scatter_on_walls(surface_geometry, config: ScatterConfig, category: FurnitureCategory) -> Node`
   - `scatter_along_path(path_curve, config: ScatterConfig, category: FurnitureCategory) -> Node`
   - `apply_collision_detection(instances: Node, min_distance: float) -> Node`

4. Node tree pattern:
   ```
   Input Surface -> Distribute Points on Faces (density)
                -> Points to Vertices
                -> Attribute Randomize (for variation)
                -> Instance on Points (with Pick Instance)
                -> Align Rotation to Vector (face normal)
                -> Scale Instances (random variation)
                -> [Optional] Collision Detection via simulation zone
                -> Output Instances
   ```

5. Collision avoidance approach:
   - Use simulation zone with iteration
   - Each iteration: Check distances, remove overlapping instances
   - Max 5 iterations to prevent infinite loops

Use NodeTreeBuilder and InstanceController patterns.
</action>
  <verify>
```bash
# Verify module created
test -f lib/geometry_nodes/scatter.py && echo "scatter.py exists"

# Verify imports work
python3 -c "from lib.geometry_nodes.scatter import FurnitureScatter, ScatterConfig, FurnitureCategory; print('Imports OK')"

# Verify class structure
python3 -c "
from lib.geometry_nodes.scatter import FurnitureScatter, FurnitureCategory
assert hasattr(FurnitureScatter, 'scatter_on_floor')
assert hasattr(FurnitureScatter, 'scatter_on_walls')
assert hasattr(FurnitureScatter, 'scatter_along_path')
assert hasattr(FurnitureScatter, 'apply_collision_detection')
assert hasattr(FurnitureCategory, 'SEATING')
assert hasattr(FurnitureCategory, 'TABLE')
print('FurnitureScatter methods and enum OK')
"
```
  </verify>
  <done>
- FurnitureScatter class with all methods implemented
- ScatterConfig dataclass with density parameters
- FurnitureCategory enum for categorization
- Collision detection via simulation zones
- All tests pass
  </done>
</task>

<task type="auto">
  <name>Task 4: Create Asset Instance Library with Scale Normalization</name>
  <files>lib/geometry_nodes/asset_instances.py</files>
  <action>
Create `lib/geometry_nodes/asset_instances.py` implementing AssetInstanceLibrary class.

The library normalizes scales across heterogeneous asset sources (KitBash3D, personal models, etc.) and creates instance pools for Geometry Nodes.

Implementation requirements:
1. AssetSource enum:
   - KITBASH3D
   - PERSONAL
   - EXTERNAL
   - PROCEDURAL

2. NormalizedAsset dataclass with:
   - original_path: str
   - normalized_scale: float (multiplier to reach 1m reference)
   - bounding_box: tuple (min, max vectors)
   - category: str
   - source: AssetSource
   - tags: list[str]
   - thumbnail_path: str (optional)

3. AssetInstanceLibrary class:
   - `__init__(self, reference_height: float = 1.0)` - 1m reference for human-scale assets
   - `add_asset(path: str, category: str, source: AssetSource, tags: list = None) -> NormalizedAsset`
   - `calculate_normalization_scale(obj) -> float` - Computes scale to fit reference
   - `create_instance_pool(assets: list[NormalizedAsset], builder: NodeTreeBuilder) -> Node`
   - `get_random_instance_selector(pool: Node, seed: int) -> Node`
   - `filter_by_category(pool: Node, category: str) -> Node`
   - `filter_by_tags(pool: Node, tags: list[str]) -> Node`

4. Scale normalization algorithm:
   ```
   For each asset:
   1. Load bounding box (from metadata or calculate)
   2. Find largest dimension (height, width, depth)
   3. Compute scale = reference_height / largest_dimension
   4. Store as normalized_scale
   5. When instancing: Apply scale * normalized_scale
   ```

5. Instance pool creation:
   - Create collection of objects
   - Store normalized scales as attributes
   - Output as geometry that can be used with Instance on Points

6. Reference scales by asset type:
   - Human/Character: 1.8m
   - Furniture (chair): 0.9m seat height
   - Furniture (table): 0.75m surface height
   - Vehicle: 1.5m height
   - Building: 3.0m per floor

Integration with existing InstanceController from lib/geometry_nodes/instances.py.
</action>
  <verify>
```bash
# Verify module created
test -f lib/geometry_nodes/asset_instances.py && echo "asset_instances.py exists"

# Verify imports work
python3 -c "from lib.geometry_nodes.asset_instances import AssetInstanceLibrary, NormalizedAsset, AssetSource; print('Imports OK')"

# Verify class structure
python3 -c "
from lib.geometry_nodes.asset_instances import AssetInstanceLibrary, AssetSource
assert hasattr(AssetInstanceLibrary, 'add_asset')
assert hasattr(AssetInstanceLibrary, 'calculate_normalization_scale')
assert hasattr(AssetInstanceLibrary, 'create_instance_pool')
assert hasattr(AssetInstanceLibrary, 'get_random_instance_selector')
assert hasattr(AssetSource, 'KITBASH3D')
assert hasattr(AssetSource, 'PERSONAL')
print('AssetInstanceLibrary methods and enum OK')
"
```
  </verify>
  <done>
- AssetInstanceLibrary class with all methods implemented
- NormalizedAsset dataclass for scale-tracked assets
- AssetSource enum for categorization
- Scale normalization algorithm working
- All tests pass
  </done>
</task>

<task type="auto">
  <name>Task 5: Create LOD System with 3-Tier Detail Levels</name>
  <files>lib/geometry_nodes/lod_system.py</files>
  <action>
Create `lib/geometry_nodes/lod_system.py` implementing LODSystem class.

The LOD (Level of Detail) system switches geometry based on distance from camera and instance count, enforcing memory budgets.

LOD Tiers (per SCENE_GENERATION_MASTER_PLAN.md):
```
LOD0: Full detail (<100 instances, <10m distance)
- Full geometry
- All materials
- High-res textures

LOD1: Reduced polys (100-1000 instances, 10-50m)
- Decimated geometry (25% polys)
- Simplified materials
- Medium textures

LOD2: Billboard/impostor (1000+ instances, >50m)
- Camera-facing quad
- Baked texture
- Minimal shader
```

Implementation requirements:
1. LODLevel enum:
   - LOD0_FULL (0)
   - LOD1_DECIMATED (1)
   - LOD2_BILLBOARD (2)

2. LODConfig dataclass with:
   - lod0_max_distance: float = 10.0
   - lod1_max_distance: float = 50.0
   - lod0_max_instances: int = 100
   - lod1_max_instances: int = 1000
   - decimation_ratio: float = 0.25
   - billboard_size: tuple = (1.0, 1.0)

3. MemoryBudget dataclass with:
   - texture_pool_mb: int = 4096  # 4GB
   - geometry_pool_mb: int = 2048  # 2GB
   - instance_buffer_mb: int = 1024  # 1GB

4. LODSystem class:
   - `__init__(self, builder: NodeTreeBuilder, config: LODConfig, budget: MemoryBudget)`
   - `create_lod_geometry(base_geometry: Node, lod_level: LODLevel) -> Node`
   - `create_lod_switch(camera_position: Node, instances: Node, config: LODConfig) -> Node`
   - `apply_lod(instances: Node, camera: Node) -> Node` - Main entry point
   - `check_memory_budget(instances: Node, budget: MemoryBudget) -> bool`

5. Node tree pattern for LOD switching:
   ```
   Input: Instances with position attribute

   For each instance:
   1. Get instance position
   2. Calculate distance to camera
   3. Count total instances
   4. Select LOD level based on:
      - If distance < 10m AND count < 100: LOD0
      - Else if distance < 50m AND count < 1000: LOD1
      - Else: LOD2
   5. Switch geometry based on LOD level

   Use Switch node with index from distance/instance calculation
   ```

6. Billboard creation for LOD2:
   - Create quad facing camera
   - Sample texture from original geometry at render time
   - Use billboard shader (no PBR, just emission)

7. Decimation for LOD1:
   - Use limited dissolve modifier approach
   - Target 25% of original polygon count
   - Preserve silhouette edges

Use NodeTreeBuilder and simulation zones for dynamic LOD.
</action>
  <verify>
```bash
# Verify module created
test -f lib/geometry_nodes/lod_system.py && echo "lod_system.py exists"

# Verify imports work
python3 -c "from lib.geometry_nodes.lod_system import LODSystem, LODConfig, LODLevel, MemoryBudget; print('Imports OK')"

# Verify class structure
python3 -c "
from lib.geometry_nodes.lod_system import LODSystem, LODLevel
assert hasattr(LODSystem, 'create_lod_geometry')
assert hasattr(LODSystem, 'create_lod_switch')
assert hasattr(LODSystem, 'apply_lod')
assert hasattr(LODSystem, 'check_memory_budget')
assert hasattr(LODLevel, 'LOD0_FULL')
assert hasattr(LODLevel, 'LOD1_DECIMATED')
assert hasattr(LODLevel, 'LOD2_BILLBOARD')
print('LODSystem methods and enum OK')
"
```
  </verify>
  <done>
- LODSystem class with all methods implemented
- LODConfig and MemoryBudget dataclasses
- LODLevel enum with 3 tiers
- Distance-based LOD switching working
- Memory budget checking implemented
- All tests pass
  </done>
</task>

<task type="auto">
  <name>Task 6: Create Culling Strategy System</name>
  <files>lib/geometry_nodes/culling.py</files>
  <action>
Create `lib/geometry_nodes/culling.py` implementing CullingSystem class.

The culling system removes off-screen and distant instances to improve viewport/render performance.

Implementation requirements:
1. CullingType enum:
   - FRUSTUM (off-screen)
   - DISTANCE (beyond max range)
   - OCCLUSION (hidden behind geometry)
   - SIZE (too small to see)

2. CullingConfig dataclass with:
   - frustum_culling: bool = True
   - distance_culling: bool = True
   - max_view_distance: float = 500.0  # meters
   - min_screen_size: float = 0.01  # 1% of screen
   - occlusion_culling: bool = False  # expensive, optional
   - update_rate: int = 1  # every N frames

3. CullingSystem class:
   - `__init__(self, builder: NodeTreeBuilder, config: CullingConfig)`
   - `apply_frustum_culling(instances: Node, camera: Node) -> Node`
   - `apply_distance_culling(instances: Node, camera: Node, max_distance: float) -> Node`
   - `apply_size_culling(instances: Node, camera: Node, min_size: float) -> Node`
   - `apply_occlusion_culling(instances: Node, occluders: Node) -> Node`
   - `apply_culling(instances: Node, camera: Node) -> Node` - Main entry point combining all types

4. Node tree pattern for frustum culling:
   ```
   Input: Instances with position attribute

   For each instance:
   1. Get camera frustum planes (6 planes)
   2. Transform instance position to camera space
   3. Check if inside all 6 planes
   4. Output: Selection mask (True = visible)
   5. Delete instances where selection = False

   Use Separate Geometry node with selection mask
   ```

5. Distance culling formula:
   ```
   visible = distance(instance_pos, camera_pos) < max_view_distance
   ```

6. Size culling formula:
   ```
   screen_size = (bounding_radius / distance) * fov_factor
   visible = screen_size > min_screen_size
   ```

7. Occlusion culling (simplified approach):
   - Use raycast from camera to instance center
   - If raycast hits occluder before instance: culled
   - Note: This is expensive, use sparingly

8. Combined culling pipeline:
   ```
   Instances -> Frustum Cull -> Distance Cull -> Size Cull -> [Optional] Occlusion Cull -> Output
   ```

Use NodeTreeBuilder patterns. Store culling stats as named attributes for debugging.
</action>
  <verify>
```bash
# Verify module created
test -f lib/geometry_nodes/culling.py && echo "culling.py exists"

# Verify imports work
python3 -c "from lib.geometry_nodes.culling import CullingSystem, CullingConfig, CullingType; print('Imports OK')"

# Verify class structure
python3 -c "
from lib.geometry_nodes.culling import CullingSystem, CullingType
assert hasattr(CullingSystem, 'apply_frustum_culling')
assert hasattr(CullingSystem, 'apply_distance_culling')
assert hasattr(CullingSystem, 'apply_size_culling')
assert hasattr(CullingSystem, 'apply_occlusion_culling')
assert hasattr(CullingSystem, 'apply_culling')
assert hasattr(CullingType, 'FRUSTUM')
assert hasattr(CullingType, 'DISTANCE')
print('CullingSystem methods and enum OK')
"
```
  </verify>
  <done>
- CullingSystem class with all methods implemented
- CullingConfig dataclass with parameters
- CullingType enum for culling modes
- Frustum, distance, size culling working
- All tests pass
  </done>
</task>

<task type="auto">
  <name>Task 7: Create Style Transfer Nodes</name>
  <files>lib/geometry_nodes/style_transfer.py</files>
  <action>
Create `lib/geometry_nodes/style_transfer.py` implementing StyleTransfer class.

The style transfer system allows transferring material and color styles between asset collections while preserving geometry.

Implementation requirements:
1. StyleSource dataclass with:
   - materials: dict (material_name -> material_data)
   - color_palette: list[tuple] (RGB colors)
   - roughness_range: tuple
   - metallic_range: tuple
   - normal_intensity: float

2. StyleTransferConfig dataclass with:
   - blend_factor: float = 0.5  # 0=original, 1=full transfer
   - preserve_patterns: bool = True  # keep texture patterns
   - color_match_method: str = "lab"  # "rgb", "hsv", "lab"

3. StyleTransfer class:
   - `__init__(self, builder: NodeTreeBuilder)`
   - `extract_style(source_geometry: Node) -> StyleSource`
   - `apply_style(target_geometry: Node, style: StyleSource, config: StyleTransferConfig) -> Node`
   - `transfer_style(source: Node, target: Node, config: StyleTransferConfig) -> Node` - Main entry
   - `blend_color_palettes(source: list, target: list, factor: float) -> list`

4. Style extraction process:
   ```
   1. Sample materials from source geometry
   2. Extract dominant colors (k-means clustering, k=5)
   3. Calculate average roughness/metallic ranges
   4. Capture normal map intensity
   5. Store as StyleSource
   ```

5. Style application process:
   ```
   1. For each material in target:
      a. Find closest source material by name/pattern
      b. Blend base colors using lab interpolation
      c. Blend roughness/metallic values
      d. Apply with blend_factor
   2. Update geometry with new material assignments
   ```

6. Node tree pattern:
   ```
   Input: Target geometry, Style source data

   For each face/instance:
   1. Get current material index
   2. Look up style from source
   3. Mix RGB (original, style_color, blend_factor)
   4. Mix shader values (roughness, metallic)
   5. Set Material with new values

   Output: Styled geometry
   ```

7. LAB color interpolation (for perceptual blending):
   - Convert RGB to LAB
   - Interpolate in LAB space
   - Convert back to RGB
   - More natural color transitions than RGB blending

Use NodeTreeBuilder for node creation. Store style data as named attributes.
</action>
  <verify>
```bash
# Verify module created
test -f lib/geometry_nodes/style_transfer.py && echo "style_transfer.py exists"

# Verify imports work
python3 -c "from lib.geometry_nodes.style_transfer import StyleTransfer, StyleTransferConfig, StyleSource; print('Imports OK')"

# Verify class structure
python3 -c "
from lib.geometry_nodes.style_transfer import StyleTransfer
assert hasattr(StyleTransfer, 'extract_style')
assert hasattr(StyleTransfer, 'apply_style')
assert hasattr(StyleTransfer, 'transfer_style')
assert hasattr(StyleTransfer, 'blend_color_palettes')
print('StyleTransfer methods OK')
"
```
  </verify>
  <done>
- StyleTransfer class with all methods implemented
- StyleSource and StyleTransferConfig dataclasses
- Style extraction and application working
- LAB color interpolation implemented
- All tests pass
  </done>
</task>

<task type="auto">
  <name>Task 8: Update Package Exports and Create Blend Files</name>
  <files>
    lib/geometry_nodes/__init__.py
    assets/node_groups/room_builder.blend
    assets/node_groups/road_builder.blend
    tests/unit/test_gn_room_builder.py
    tests/unit/test_gn_road_builder.py
    tests/unit/test_gn_scatter.py
    tests/unit/test_gn_lod.py
  </files>
  <action>
Update `lib/geometry_nodes/__init__.py` with all new exports and create blend files with node groups.

1. Update __init__.py exports:
```python
__all__ = [
    # Existing (keep all current exports)
    "NodeTreeBuilder",
    "InstanceController",
    "InstanceExtractor",
    "SimulationBuilder",
    "FieldOperations",
    "AttributeManager",
    # ... existing exports ...

    # NEW: Room Builder
    "RoomBuilder",
    "RoomConfig",
    "build_room_from_json",

    # NEW: Road Builder
    "RoadBuilder",
    "RoadConfig",
    "IntersectionConfig",
    "build_road_network",

    # NEW: Scatter System
    "FurnitureScatter",
    "ScatterConfig",
    "FurnitureCategory",
    "scatter_on_surface",

    # NEW: Asset Instances
    "AssetInstanceLibrary",
    "NormalizedAsset",
    "AssetSource",
    "create_instance_pool",

    # NEW: LOD System
    "LODSystem",
    "LODConfig",
    "LODLevel",
    "MemoryBudget",
    "apply_lod",

    # NEW: Culling
    "CullingSystem",
    "CullingConfig",
    "CullingType",
    "apply_culling",

    # NEW: Style Transfer
    "StyleTransfer",
    "StyleSource",
    "StyleTransferConfig",
    "transfer_style",
]

# Update version
__version__ = "3.0.0"

# Add imports
from .room_builder import RoomBuilder, RoomConfig, build_room_from_json
from .road_builder import RoadBuilder, RoadConfig, IntersectionConfig, build_road_network
from .scatter import FurnitureScatter, ScatterConfig, FurnitureCategory, scatter_on_surface
from .asset_instances import AssetInstanceLibrary, NormalizedAsset, AssetSource, create_instance_pool
from .lod_system import LODSystem, LODConfig, LODLevel, MemoryBudget, apply_lod
from .culling import CullingSystem, CullingConfig, CullingType, apply_culling
from .style_transfer import StyleTransfer, StyleSource, StyleTransferConfig, transfer_style
```

2. Create assets/node_groups/ directory if not exists:
```bash
mkdir -p assets/node_groups
```

3. Create placeholder blend files with README:
- Create assets/node_groups/room_builder.blend (can be empty or have placeholder node group)
- Create assets/node_groups/road_builder.blend (can be empty or have placeholder node group)
- Create assets/node_groups/README.md documenting purpose

4. Create unit tests:
- tests/unit/test_gn_room_builder.py - Test RoomBuilder class
- tests/unit/test_gn_road_builder.py - Test RoadBuilder class
- tests/unit/test_gn_scatter.py - Test FurnitureScatter class
- tests/unit/test_gn_lod.py - Test LODSystem class

Each test file should have:
- Test class initialization
- Test config dataclasses
- Test basic functionality (mock NodeTreeBuilder if needed)
- At least 5 test methods per module

Test structure example:
```python
import unittest
from unittest.mock import MagicMock, patch

class TestRoomBuilder(unittest.TestCase):
    def setUp(self):
        self.mock_builder = MagicMock()
        self.room_builder = RoomBuilder(self.mock_builder)

    def test_room_config_defaults(self):
        config = RoomConfig(room_type="living_room", polygon=[(0,0), (5,0), (5,4), (0,4)])
        self.assertEqual(config.height, 2.8)
        self.assertEqual(config.wall_thickness, 0.15)

    def test_build_floor_creates_nodes(self):
        # Test that build_floor calls appropriate node methods
        pass

    # ... more tests
```
</action>
  <verify>
```bash
# Verify __init__.py updated
grep -q "RoomBuilder" lib/geometry_nodes/__init__.py && echo "RoomBuilder exported"
grep -q "LODSystem" lib/geometry_nodes/__init__.py && echo "LODSystem exported"
grep -q "__version__ = \"3.0.0\"" lib/geometry_nodes/__init__.py && echo "Version updated to 3.0.0"

# Verify all imports work
python3 -c "
from lib.geometry_nodes import (
    RoomBuilder, RoadBuilder, FurnitureScatter,
    AssetInstanceLibrary, LODSystem, CullingSystem, StyleTransfer
)
print('All new exports importable')
"

# Verify blend file directories
test -d assets/node_groups && echo "assets/node_groups exists"

# Verify test files exist
test -f tests/unit/test_gn_room_builder.py && echo "room_builder tests exist"
test -f tests/unit/test_gn_road_builder.py && echo "road_builder tests exist"
test -f tests/unit/test_gn_scatter.py && echo "scatter tests exist"
test -f tests/unit/test_gn_lod.py && echo "lod tests exist"

# Run tests (will pass if modules exist, may have some failures for unimplemented features)
python3 -m pytest tests/unit/test_gn_*.py -v --tb=short 2>&1 | head -50
```
  </verify>
  <done>
- __init__.py updated with all new exports
- Version bumped to 3.0.0
- assets/node_groups/ directory created with blend files
- Unit test files created for all modules
- All imports working
  </done>
</task>

</tasks>

<verification>
After all tasks complete, verify the complete system:

```bash
# 1. Verify all modules exist and import
python3 -c "
from lib.geometry_nodes import (
    RoomBuilder, RoomConfig,
    RoadBuilder, RoadConfig, IntersectionConfig,
    FurnitureScatter, ScatterConfig, FurnitureCategory,
    AssetInstanceLibrary, NormalizedAsset, AssetSource,
    LODSystem, LODConfig, LODLevel, MemoryBudget,
    CullingSystem, CullingConfig, CullingType,
    StyleTransfer, StyleSource, StyleTransferConfig
)
print('All GN extensions imported successfully')
"

# 2. Verify version
python3 -c "import lib.geometry_nodes; print(f'Version: {lib.geometry_nodes.__version__}')"

# 3. Run all unit tests
python3 -m pytest tests/unit/test_gn_*.py -v

# 4. Verify asset directories
ls -la assets/node_groups/
```
</verification>

<success_criteria>
- All 7 new Python modules created in lib/geometry_nodes/
- Each module follows NodeTreeBuilder pattern from existing codebase
- LOD system implements 3-tier switching with distance and instance thresholds
- Culling system supports frustum, distance, and size-based culling
- Room Builder consumes JSON floor plans from BSP solver
- Road Builder consumes JSON road networks from L-system
- Furniture scatter supports collision avoidance
- Asset instance library normalizes scales across sources
- Style transfer supports LAB color interpolation
- __init__.py updated with all exports, version 3.0.0
- Unit tests created for all modules
- All imports working correctly
</success_criteria>

<output>
After completion, create `.planning/phases/06-gn-extensions/06-01-SUMMARY.md`

Document:
- Modules created with line counts
- Exports added to __init__.py
- Test coverage for each module
- Integration points with Phase 3 (BSP) and Phase 4 (L-system)
- Memory budget configuration for LOD system
</output>
