# Physical Projector Mapping System Design

**Review Status**: APPROVED with changes (Geometry Rick, Pipeline Rick - 2026-02-25)
**Version**: 0.2.0

---

## Blender Ricks Review Summary

### Geometry Rick Review
| Issue | Priority | Resolution |
|-------|----------|------------|
| Throw ratio formula | **FIXED** | `focal_length = sensor_width * throw_ratio` |
| 3-point vs 4-point alignment | DOCUMENTED | 3-point assumes planar target; 4-point DLT for multi-surface |
| Geometry Nodes integration | ADDED | Added GN stage for UV projection + named attributes |
| SurfaceGeometry properties | ADDED | Added facing_ratio, distance_to_projector, calibration_error |

### Pipeline Rick Review
| Issue | Severity | Resolution |
|-------|----------|------------|
| File structure | FIXED | Nested under `lib/cinematic/projection/physical/` |
| Stage alignment | APPROVED | Documented explicit 5-stage functions |
| Determinism | FIXED | Added seed hashing, checksums for reproducibility |
| Operators location | FIXED | Moved to project root `operators/` |

---

## Research Summary: Compify Analysis

### What Compify Does
- **Purpose**: 3D compositing via camera projection (not physical projector output)
- **Authors**: Nathan Vegdahl, Ian Hubert (Blender 4.0+)
- **Core Technique**: Projects footage from a tracked camera onto 3D proxy geometry

### Key Compify Techniques We Can Adapt

#### 1. Camera Projection Shader (node_groups.py)
```python
# Camera projection with driven values:
- Lens (focal length)
- Sensor width
- Shift X/Y (lens shift)
- Aspect ratio
- Perspective division for projection coordinates
```
**Adaptation for Projectors**: Replace lens/sensor with throw ratio and output resolution

#### 2. 3-Point Camera Alignment (camera_align.py)
```python
# Transform computation from 3 track points to 3 scene points:
- Build orthogonal coordinate systems
- Compute scale from average distances
- Compute rotation from orthonormal bases
- Apply translation
```
**Adaptation for Projectors**: Use for real-world surface alignment

#### 3. UV Baking Workflow
- Smart project UV unwrapping for proxy geometry
- Bake lighting for compositing integration
- Material creation with node groups

---

## Physical Projector Mapping System Design

### Core Components

#### 1. Projector Profile System
**Location**: `lib/projection/projector/profiles.py`

```python
@dataclass
class ProjectorProfile:
    """Physical projector hardware specifications."""
    name: str                    # "Epson_Home_Cinema_2150"
    manufacturer: str            # "Epson"

    # Output specifications
    native_resolution: tuple     # (1920, 1080)
    aspect_ratio: float          # 16/9

    # Optical characteristics
    throw_ratio: float           # 1.32 (distance / width)
    throw_ratio_range: tuple     # (1.27, 1.37) for zoom lenses
    lens_shift_vertical: float   # ±0.15 (15% vertical shift)
    lens_shift_horizontal: float # ±0.05 (5% horizontal shift)

    # Calibration data
    keystone_correction: tuple   # (h, v) degrees
    brightness_lumens: int       # 2500
    contrast_ratio: int          # 70000

    # Blender camera equivalent
    blender_focal_length: float  # Computed from throw ratio
```

**Key Insight**: Throw ratio converts to Blender focal length:
```python
def throw_ratio_to_focal_length(throw_ratio: float, sensor_width: float,
                                sensor_height: float, aspect: str = 'horizontal') -> float:
    """Convert throw ratio to focal length with aspect ratio handling.

    CORRECTED: Geometry Rick identified the formula was wrong.
    Throw ratio = throw_distance / image_width
    focal_length = sensor_width * throw_ratio
    """
    if aspect == 'horizontal':
        return sensor_width * throw_ratio
    elif aspect == 'vertical':
        return sensor_height * throw_ratio * (sensor_width / sensor_height)
    elif aspect == 'diagonal':
        diagonal = math.sqrt(sensor_width**2 + sensor_height**2)
        return diagonal * throw_ratio
```

#### 2. Projector Calibration Workflow
**Location**: `lib/cinematic/projection/physical/projector/calibration.py`

**Phase A: Projector Setup in Blender**
1. Create projector camera object from profile
2. Set render resolution to projector native resolution
3. Configure lens shift and throw ratio
4. Position projector in scene

**Phase B: Real-World Surface Mapping**

**IMPORTANT (Geometry Rick)**: 3-point alignment assumes a **planar target surface**.
For multi-surface targets (reading room with cabinets, desks), use **4-point DLT alignment**:

```
3-Point Alignment (Planar Targets):
- Point 1: Bottom-left of projection area
- Point 2: Bottom-right of projection area
- Point 3: Top-left of projection area
- Assumes: Target is a single flat plane

4-Point DLT Alignment (Multi-Surface/Non-Planar):
- Point 1-4: Four corners of projection area
- Solves for full projection matrix P (3x4)
- Decomposes P → K, R, t (intrinsics, rotation, translation)
- Works with: Irregular surfaces, multiple depths
```

**Phase C: Content Mapping**
1. Create UV-mapped proxy geometry for target surface
2. Apply content texture via camera projection shader
3. Adjust for real-world surface irregularities
4. Bake final projection content

#### 3. Projection Output System
**Location**: `lib/cinematic/projection/physical/projector/output.py`

```python
class ProjectionOutput:
    """Generate output for physical projector display."""

    def render_for_projector(self, scene, projector_profile):
        """Render scene from projector perspective."""
        # Set render resolution to projector native
        # Configure aspect ratio
        # Apply keystone if needed
        # Output as video file or image sequence

    def generate_calibration_pattern(self, resolution):
        """Create test pattern for physical alignment."""
        # Checkerboard with known dimensions
        # Color bars for calibration
        # Edge markers for keystone adjustment
```

#### 4. Surface Target Presets
**Location**: `lib/cinematic/projection/physical/targets/`

**SurfaceGeometry Properties (Geometry Rick Addition)**:
```python
@dataclass
class ProjectionTarget:
    """Geometry properties for projection mapping target."""

    # Identity
    name: str
    surface_type: str  # 'planar', 'curved', 'irregular'

    # Geometry (Blender 5.x)
    mesh_data: bpy.types.Mesh  # Reference to mesh data
    bounding_box: Tuple[Vector, Vector]  # (min, max) in world space

    # Projection-specific
    surface_normal: Vector  # Dominant normal direction
    facing_ratio: float  # How much faces the projector (0-1)
    distance_to_projector: float

    # UV/Projection
    projector_uv_bounds: Tuple[Vector, Vector]  # UV min/max in projector space
    coverage_ratio: float  # What fraction of projector FOV this surface uses

    # Material
    albedo: float  # For brightness compensation
    glossiness: float  # For hot-spot avoidance

    # Calibration
    calibration_points: List[Vector]  # 3D points for alignment
    is_calibrated: bool
    calibration_error: float  # RMS error in pixels
```

**Reading Room Target**:
```python
@dataclass
class ReadingRoomTarget:
    """Cabinet and desk projection surface."""
    cabinets: List[ProjectionTarget]    # Multiple cabinet faces
    desks: List[ProjectionTarget]       # Desk surface areas
    walls: List[ProjectionTarget]       # Adjacent wall areas

    def create_proxy_geometry(self):
        """Generate simplified UV-mapped geometry."""
        # Combine surfaces into single UV layout
        # Optimize for projection content
```

**Garage Door Target**:
```python
@dataclass
class GarageDoorTarget:
    """White garage door projection surface."""
    door_panel: ProjectionTarget  # Main door surface
    frame: ProjectionTarget       # Door frame edges

    def create_proxy_geometry(self):
        """Generate flat projection surface."""
        # Single flat plane
        # Handle door seam if visible
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (GSD Phase 13.0)
- [ ] Create `lib/projection/` directory structure
- [ ] Implement `ProjectorProfile` dataclass
- [ ] Create projector profile database (common models)
- [ ] Implement throw ratio → focal length conversion
- [ ] Create projector camera factory

### Phase 2: Calibration System (GSD Phase 14.0)
- [ ] Implement 3-point surface alignment (adapt from compify)
- [ ] Create calibration pattern generator
- [ ] Build projector-to-surface transform calculator
- [ ] Implement keystone correction helpers

### Phase 3: Content Workflow (GSD Phase 15.0)
- [ ] Create UV-mapped proxy geometry generator
- [ ] Implement camera projection shader (adapt from compify)
- [ ] Build content-to-surface mapping system
- [ ] Create projection output renderer

### Phase 4: Target Presets (GSD Phase 16.0)
- [ ] Implement ReadingRoomTarget configuration
- [ ] Implement GarageDoorTarget configuration
- [ ] Create target geometry import from measurements
- [ ] Build target preview system

---

## Blender 5.x Geometry Nodes Integration (Geometry Rick)

### Hybrid Approach: Geometry Nodes + Shader Nodes

For physical projection mapping, use a **hybrid approach**:

1. **Geometry Nodes Stage**: Project UV coordinates from projector POV
2. **Shader Stage**: Sample texture using stored UV coordinates

```python
def create_projector_uv_projection(nk: NodeKit, params: dict):
    """Project UV coordinates from projector position onto target geometry.

    Geometry Rick: Use named attributes to pass UV data to shaders.
    This enables per-surface debugging and deterministic output.
    """
    geometry = params['target_geometry']

    # Transform to projector space (inverse of projector transform)
    transform = nk.n("GeometryNodeTransform", "To Projector Space", 100, 0)
    transform.inputs['Geometry'] = geometry
    transform.inputs['Translation'] = params['projector_location']
    transform.inputs['Rotation'] = params['projector_rotation_inverse']

    # Project to UV (perspective division)
    # In projector space, X/Y map to UV, Z is depth
    sep = nk.n("ShaderNodeSeparateXYZ", "Separate", 200, 0)

    # Normalize to 0-1 range (frustum bounds at Z=1)
    u = nk.n("ShaderNodeMath", "Calc U", 300, 0)
    u.operation = 'DIVIDE'
    u.inputs[0] = sep.outputs['X']
    u.inputs[1] = params['frustum_width_at_unit']

    v = nk.n("ShaderNodeMath", "Calc V", 300, 50)
    v.operation = 'DIVIDE'
    v.inputs[0] = sep.outputs['Y']
    v.inputs[1] = params['frustum_height_at_unit']

    # Combine to UV vector
    combine = nk.n("ShaderNodeCombineXYZ", "Combine UV", 400, 0)
    combine.inputs['X'] = u.outputs['Value']
    combine.inputs['Y'] = v.outputs['Value']

    # Store as named attribute for shader access
    store = nk.n("GeometryNodeStoreNamedAttribute", "Store Projector UV", 500, 0)
    store.inputs['Geometry'] = geometry
    store.inputs['Name'] = "projector_uv"
    store.inputs['Value'] = combine.outputs['Vector']

    return store.outputs['Geometry']
```

### Determinism Requirements (Pipeline Rick)

**Critical for calibration reproducibility:**

```python
def stage_normalize(state: dict, context: dict) -> dict:
    """Stage 0: Normalize projector parameters with deterministic seed."""
    params = context['parameters']

    # Deterministic seed from all inputs
    seed_input = (
        params.get('projector_model', ''),
        params.get('serial_number', ''),
        str(params.get('calibration_points', [])),
        params.get('target_id', ''),
    )
    seed = hash('|'.join(seed_input)) % (2**31)

    return {
        'seed': seed,
        'profile': load_profile(params['projector_model']),
        'target_checksum': mesh_checksum(params['target_id']),
    }
```

| Concern | Risk Level | Mitigation |
|---------|------------|------------|
| Calibration random seed | High | Add `seed` parameter, hash all inputs |
| Floating-point precision | Medium | Use consistent coordinate spaces |
| Profile database versioning | High | Include profile version in task hash |
| Target geometry changes | Medium | Hash target mesh checksum |

---

## Blender 5.x Shader Integration

### Shader Nodes (Adapted from Compify)
```python
def create_projector_shader(projector: bpy.types.Object,
                            content_texture: bpy.types.Image):
    """Create shader for projector content mapping."""
    mat = bpy.data.materials.new("ProjectorMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Camera projection node group (adapted from compify)
    proj_group = ensure_projector_projection_group()
    proj_node = nodes.new('ShaderNodeGroup')
    proj_node.node_tree = proj_group

    # Drive from projector object
    proj_node.inputs['Throw Ratio'].default_value = projector.throw_ratio
    proj_node.inputs['Resolution X'].default_value = projector.resolution_x
    proj_node.inputs['Resolution Y'].default_value = projector.resolution_y
    proj_node.inputs['Shift X'].default_value = projector.shift_x
    proj_node.inputs['Shift Y'].default_value = projector.shift_y

    # Content texture
    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.image = content_texture

    # Connect projection coordinates to texture
    links.new(proj_node.outputs['UV'], tex_node.inputs['Vector'])

    # Output to surface
    # ...
```

### UI Panel Design
```python
class PROJECTION_PT_projector_setup(bpy.types.Panel):
    """Projector setup and calibration panel."""
    bl_label = "Physical Projector Setup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Projection'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Projector profile selection
        layout.prop(scene, "projector_profile")

        # Target surface selection
        layout.prop(scene, "projection_target")

        # Calibration actions
        layout.operator("projection.create_projector_camera")
        layout.operator("projection.calibrate_surface")
        layout.operator("projection.render_for_projector")
```

---

## Image Extrusion / Depth-to-3D Workflow (Separate Feature)

**Note**: Compify does NOT do image extrusion. This is a separate feature.

### Potential Approaches:

1. **Depth Map to Displacement**
   - Generate depth map from image (AI or manual)
   - Apply as displacement modifier to plane
   - Subdivide and sculpt for detail

2. **ControlNet Depth-to-Mesh**
   - Use existing `lib/sd_projection/` infrastructure
   - Generate depth with ControlNet
   - Convert depth map to mesh via marching cubes

3. **Photogrammetry Integration**
   - Multi-angle image capture
   - Process through photogrammetry software
   - Import resulting mesh to Blender

### Recommendation for GSD Project
Create as separate feature in future milestone after projector mapping is complete.

---

## Files to Create (Pipeline Rick Approved Structure)

```
lib/cinematic/projection/
├── __init__.py
├── anamorphic/              # Existing anamorphic system
│   └── ...
└── physical/                # NEW: Physical projector mapping
    ├── __init__.py
    ├── stages/              # Pipeline stage functions (Pipeline Rick)
    │   ├── __init__.py
    │   ├── normalize.py     # Stage 0: Profile validation, seed hashing
    │   ├── primary.py       # Stage 1: Base frustum setup, projector camera
    │   ├── secondary.py     # Stage 2: Calibration/alignment
    │   ├── detail.py        # Stage 3: Content mapping, UV projection
    │   └── output.py        # Stage 4: Render/export
    ├── projector/
    │   ├── __init__.py
    │   ├── profiles.py          # ProjectorProfile dataclass
    │   ├── profile_database.py  # Common projector models
    │   └── calibration.py       # Calibration workflow
    ├── targets/
    │   ├── __init__.py
    │   ├── base.py              # ProjectionTarget base class
    │   ├── reading_room.py      # Reading room target
    │   └── garage_door.py       # Garage door target
    └── shaders/
        ├── __init__.py
        └── projector_nodes.py   # Camera projection shader nodes

operators/
├── physical_projection_setup.py    # Projector setup operators
├── physical_projection_calibrate.py # Calibration operators
└── physical_projection_render.py   # Output operators

configs/cinematic/projection/
├── projector_profiles.yaml     # Projector hardware specs
├── calibration_patterns.yaml   # Test patterns for alignment
└── targets/
    ├── reading_room.yaml       # Reading room measurements
    └── garage_door.yaml        # Garage door measurements
```

---

## Next Steps

1. **Create GSD Project** for Projection Mapping
2. **Phase 13.0**: Core projector infrastructure
3. **Phase 14.0**: Calibration system
4. **Phase 15.0**: Content workflow
5. **Phase 16.0**: Target presets

Ready to proceed with `/gsd:new-project` for "Projection Mapping System"?
