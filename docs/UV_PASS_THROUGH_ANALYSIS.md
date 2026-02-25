# UV Pass-Through Pattern Analysis & Recommendations

Analysis of existing UV workflows and opportunities to apply the UV pass-through pattern from Ducky 3D tutorial.

---

## Existing UV Work in Blender GSD

### 1. Cinematic Projection System (`lib/cinematic/projection/`)

**Current Implementation:**
- `uv_generation.py` - Generates UVs from camera projection
- `raycast.py` - Camera frustum raycasting
- Creates UV layers directly on mesh objects
- Used for anamorphic projection workflows

**How it works:**
```python
# Generate UVs from projection ray hits
projection_result = project_from_camera(camera_name, config)
uv_results = generate_uvs_from_projection(projection_result, uv_config)
```

**UV Pass-Through Opportunity:** ✅ HIGH

The system currently:
1. Generates UV coordinates from ray hits
2. Applies them directly to mesh UV layers
3. **Does NOT** use Geometry Nodes

**Improvement:**
The projection system could benefit from a **Geometry Nodes implementation** that:
- Stores UVs via `Store Named Attribute` node
- Allows shader access via `Attribute` node
- Enables real-time updates without re-baking

**Example Node Setup:**
```
# Geometry Nodes
[Input Geometry]
    → [Store Named Attribute]
        - Name: "ProjectionUV"
        - Domain: Face Corner
        - Value: [UV from projection calculation]
    → [Output Geometry]

# Shader
[Attribute Node: "ProjectionUV"]
    → [Texture Vector]
```

### 2. Road UV System (`lib/charlotte_digital_twin/geometry/road_uv.py`)

**Current Implementation:**
- `RoadUVGenerator` class
- Calculates UV coordinates based on road length/width
- Applies UVs directly to mesh data
- Supports multiple UV channels (base, AO, lane markings)

**How it works:**
```python
uv_gen = RoadUVGenerator(config)
uvs = uv_gen.calculate_road_uv(segment, texture_width=4.0)
uv_gen.apply_uv_to_mesh(mesh, uvs)
```

**UV Pass-Through Opportunity:** ✅ MEDIUM

The road system is **Python-based** and applies UVs directly. However, if roads are generated via Geometry Nodes, the pattern would be:

```
# Geometry Nodes (Road Generation)
[Curve Line] → [Mesh Line] → [Extrusion]
    → [Store Named Attribute]
        - Name: "RoadUV"
        - Domain: Face Corner
        - Value: [Position XZ scaled by texture width]
    → [Set Material: RoadMaterial]

# Shader (RoadMaterial)
[Attribute: "RoadUV"]
    → [Texture Coordinate for asphalt textures]
```

**Recommendation:**
If road geometry moves to Geometry Nodes (procedural generation), implement UV pass-through for:
- Length-based U tiling
- Width-based V mapping
- Lane marking UV channels

### 3. Ground Textures GN Integration (`lib/materials/ground_textures/gn_integration.py`)

**Current Implementation:**
- `GNOutputFormat` specifies `uv_attribute: "uv_map"`
- `GNMaskNodeGroup` uses `GeometryNodeInputNamedAttribute`
- **Already expects** UV pass-through pattern!

**Current Code:**
```python
# From gn_integration.py
{"type": "GeometryNodeInputNamedAttribute", "name": "uv_input",
 "attribute_name": "uv_map", "data_type": "FLOAT_VECTOR"}
```

**UV Pass-Through Opportunity:** ✅ ALREADY IMPLEMENTED

This system **already uses** the UV pass-through pattern! The GN nodes read UVs via `InputNamedAttribute`.

**However:** The system needs the UV attribute to be stored via `Store Named Attribute` before reaching the texture nodes.

### 4. Field Operations (`lib/geometry_nodes/fields.py`)

**Current Implementation:**
- `FieldOperations` class with utility methods
- `ray_cast()` method for Geometry Nodes raycasting
- `sample_surface()` for surface sampling

**UV Pass-Through Opportunity:** ✅ HELPER NEEDED

**Missing:** A helper method to store UVs for shader access.

**Recommendation:**
Add to `FieldOperations`:

```python
@staticmethod
def store_uv_for_shader(
    geometry,
    uv_data,
    uv_name: str = "UV",
    builder=None,
    location: tuple[float, float] = (0, 0),
) -> Node:
    """
    Store UV coordinates for shader access.

    Uses Store Named Attribute with Face Corner domain
    to pass UVs from Geometry Nodes to shader.

    Args:
        geometry: Geometry to store UVs on
        uv_data: UV coordinate data (2D vector field)
        uv_name: Name for the UV attribute
        builder: NodeTreeBuilder
        location: Node position

    Returns:
        Store Named Attribute node
    """
    if builder is None:
        raise ValueError("builder required")

    store = builder.add_node(
        "GeometryNodeStoreNamedAttribute",
        location,
        name=f"Store_{uv_name}",
    )

    # Critical: Face Corner domain for UVs
    store.domain = 'CORNER'  # Face Corner

    # Set attribute name
    store.inputs["Name"].default_value = uv_name

    # Connect geometry
    if geometry is not None:
        builder.link(geometry, store.inputs["Geometry"])

    # Connect UV data
    if uv_data is not None:
        builder.link(uv_data, store.inputs["Value"])

    return store
```

---

## Raycast Node Analysis

### Existing Raycast Implementations

**1. Geometry Nodes (`lib/geometry_nodes/fields.py`)**

```python
@staticmethod
def ray_cast(
    geometry,
    source_position,
    ray_direction,
    max_distance: float = 100.0,
    builder=None,
    location: tuple[float, float] = (0, 0),
) -> Node:
    """
    Cast a ray against geometry for intersection testing.

    Returns node with outputs:
    - "Is Hit"
    - "Hit Position"
    - "Hit Normal"
    - "Hit Distance"
    - "Attribute"
    """
```

**2. Cinematic Projection (`lib/cinematic/projection/raycast.py`)**

- Python-based raycasting for camera frustum
- Generates rays from camera through image plane
- Used for projection mapping

**3. Vehicle Ground Detection (`lib/vehicle/launch_control/ground_detection.py`)**

- Uses raycasting for suspension physics
- Casts rays downward to detect ground

**4. Follow Cam Collision (`lib/cinematic/follow_cam/collision.py`)**

- Raycasting for camera avoidance
- Detects obstacles in camera path

### New Blender 5.1 Shader Raycast Node

The **new shader-based Raycast node** (from DECODED tutorial) enables:

| Use Case | Old Way | New Way (5.1) |
|----------|---------|---------------|
| Proximity AO | Baked AO map | Raycast in shader |
| Contact shadows | Manual setup | Raycast distance |
| Color bleeding | Texture baking | Raycast hit position |
| Edge detection | Geometry processing | Raycast normal |

**Shader Raycast Example:**
```
# Material Shader
[Texture Coordinate: Object]
    → [Raycast]
        - Source Object: "MainObject"
        - Length: 1.0
    → [Hit Distance]
    → [Map Range: 0-1 → 0-1]
    → [Mix RGB: Color bleeding]
```

**Integration Opportunities:**

1. **Ground Textures:** Use shader raycast for edge wear instead of geometry-based edge detection
2. **Vehicle Shadows:** Real-time contact shadows under cars
3. **Road Markings:** Proximity-based wear/fading
4. **Digital Twin:** Real-time ambient occlusion without baking

---

## Recommendations

### High Priority: UV Pass-Through Pattern

**1. Add Helper to FieldOperations**

```python
# lib/geometry_nodes/fields.py

@staticmethod
def store_uv_for_shader(geometry, uv_data, uv_name="UV", builder=None, location=(0,0)):
    """Store UV coordinates for shader access via Store Named Attribute."""
    store = builder.add_node("GeometryNodeStoreNamedAttribute", location)
    store.domain = 'CORNER'  # Critical: Face Corner for UVs
    store.inputs["Name"].default_value = uv_name
    builder.link(geometry, store.inputs["Geometry"])
    builder.link(uv_data, store.inputs["Value"])
    return store
```

**2. Update GN Integration to Enforce Pattern**

```python
# lib/materials/ground_textures/gn_integration.py

# In create_gn_node_tree():
# Add validation that UV attribute is stored before use

def validate_uv_attribute(node_tree, uv_attribute_name):
    """Validate that UV attribute is stored before texture sampling."""
    # Check for Store Named Attribute node with UV name
    # Before any texture sampling nodes
    pass
```

**3. Document Pattern in Node Tool Patterns**

Already added to `docs/NODE_TOOL_PATTERNS.md`:
- Pattern: UV Pass to Shader
- Critical: Face Corner domain
- Attribute node in shader

### Medium Priority: Shader Raycast Integration

**1. Create Shader Raycast Presets**

```python
# New file: lib/materials/shader_raycast.py

def create_proximity_ao_material(target_object, max_distance=1.0):
    """
    Create material with raycast-based AO.

    Uses Blender 5.1 shader raycast node for real-time AO.
    """
    # Create material with Raycast node
    # Distance → Color factor
    pass

def create_contact_shadow_material(target_object, max_distance=0.5):
    """Create material with raycast contact shadows."""
    pass

def create_color_bleeding_material(target_object, max_distance=2.0):
    """Create material with raycast color bleeding."""
    pass
```

**2. Update Ground Textures**

Replace geometry-based edge wear with shader raycast:

```python
# Old: Edge detection in Geometry Nodes
{"type": "GeometryNodeInputMeshEdgeAngle", "name": "edge_angle"}

# New: Shader raycast in material
# Raycast node in shader → Distance → Edge wear factor
```

### Low Priority: Documentation

**1. Add Tutorial References**

Update `docs/BLENDER_51_TUTORIAL_KNOWLEDGE.md` with:
- Cross-references to our implementations
- Examples from our codebase
- Migration guides for existing systems

**2. Create Migration Guide**

```
# docs/UV_PASS_THROUGH_MIGRATION.md

## Migrating Direct UV Assignment to Pass-Through Pattern

### Before (Direct):
```python
uv_layer.data[loop.index].uv = (u, v)
```

### After (Pass-Through):
```python
# Geometry Nodes
store_uv_for_shader(geometry, uv_field, "MyUV", builder)

# Shader
[Attribute: "MyUV"] → [Texture Vector]
```
```

---

## Summary

| System | UV Pass-Through Status | Action Needed |
|--------|------------------------|---------------|
| Cinematic Projection | ✅ DONE | GN alternative created |
| Road UV | ❌ Direct only | Future: GN roads with pass-through |
| Ground Textures GN | ✅ DONE | Validation added |
| Field Operations | ✅ DONE | Helpers added |
| Shader Raycast | ✅ DONE | Presets module created |

---

## Implementation Status

All high and medium priority recommendations have been implemented:

### ✅ High Priority: UV Pass-Through Pattern

1. **Added Helper to FieldOperations** - `lib/geometry_nodes/fields.py`
   - `store_uv_for_shader()` - Store UVs with CORNER domain
   - `create_uv_from_position()` - Generate and store UVs from position
   - `store_named_attribute()` - Generic attribute storage
   - `get_named_attribute()` - Generic attribute retrieval

2. **Updated GN Integration** - `lib/materials/ground_textures/gn_integration.py`
   - `UVStorageSpec` dataclass for UV storage configuration
   - `validate_uv_storage()` to check proper UV storage
   - `create_uv_storage_node_spec()` for node specifications

### ✅ Medium Priority: Shader Raycast Integration

1. **Created Shader Raycast Module** - `lib/materials/shader_raycast.py`
   - `RaycastConfig` and `RaycastMaterialPreset` dataclasses
   - Presets: Proximity AO, Contact Shadow, Edge Wear, Color Bleeding
   - `RaycastMaterialBuilder` with fluent interface
   - Convenience functions for common use cases

2. **Updated Weathering** - `lib/materials/sanctus/weathering.py`
   - Added `use_shader_raycast` parameter to `create_edge_wear()`
   - Added `create_edge_wear_with_raycast()` method

3. **Added GN Projection Alternative** - `lib/cinematic/projection/gn_projection.py`
   - `GNProjectionSystem` class for real-time projection
   - Migration helper from Python raycasting
   - No re-baking required for changes

### ✅ Low Priority: Documentation

1. **Updated Tutorial Knowledge** - `docs/BLENDER_51_TUTORIAL_KNOWLEDGE.md`
   - Added Section 9: Project Implementations
   - Cross-references to all implementations
   - Code examples for each module

2. **Created Migration Guide** - `docs/UV_PASS_THROUGH_MIGRATION_GUIDE.md`
   - Step-by-step migration patterns
   - Common pitfalls and solutions
   - Code examples for GN + Shader setup

---

## Related Documentation

- **Migration Guide:** `docs/UV_PASS_THROUGH_MIGRATION_GUIDE.md`
- **Tutorial Knowledge:** `docs/BLENDER_51_TUTORIAL_KNOWLEDGE.md` (Section 9)
- **Node Patterns:** `docs/NODE_TOOL_PATTERNS.md`

---

*Analysis completed February 2026*
*Implementation completed February 2026*
