# PLAN: MSG 1998 Location Building - Modeling Pipeline

**Phase:** 9.MSG-02
**Created:** 2026-02-22
**Depends On:** Phase 9.MSG-01 (fSpy Import)
**Output To:** Phase 9.MSG-03 (Render Layers)

---

## Goal

Implement Universal Stage Order pipeline for building period-accurate 3D locations from fSpy-matched cameras.

---

## Tasks

### Task 1: Universal Stage Order Implementation
**File:** `lib/msg1998/modeling_pipeline.py`

```python
class ModelingStage(Enum):
    """Universal Stage Order for location building."""
    NORMALIZE = 0      # Scale to real-world units
    PRIMARY = 1        # Base geometry (walls, roof)
    SECONDARY = 2      # Windows, doors, details
    DETAIL = 3         # Textures, wear, signage
    OUTPUT_PREP = 4    # Render layer setup

@dataclass
class LocationBuildState:
    """State tracker for location build."""
    location_id: str
    current_stage: ModelingStage
    geometry_stats: dict
    period_issues: list[PeriodViolation]
    completed_tasks: list[str]

def advance_stage(state: LocationBuildState, next_stage: ModelingStage) -> LocationBuildState:
    """Advance to next modeling stage with validation."""
    ...
```

### Task 2: Geometry Builders
**File:** `lib/msg1998/geometry_builders.py`

```python
@dataclass
class BuildingSpec:
    """Specification for building geometry."""
    width_m: float
    depth_m: float
    height_m: float
    floors: int
    style: str  # "commercial", "residential", "industrial"

def create_building_base(spec: BuildingSpec, context: bpy.context) -> bpy.types.Object:
    """Create primary building geometry."""
    ...

def add_windows(building: bpy.types.Object, window_spec: dict) -> list[bpy.types.Object]:
    """Add window geometry to building."""
    ...

def add_doors(building: bpy.types.Object, door_spec: dict) -> list[bpy.types.Object]:
    """Add door geometry to building."""
    ...

def add_architectural_details(building: bpy.types.Object, detail_spec: dict) -> None:
    """Add secondary architectural details."""
    ...
```

### Task 3: Period-Accurate Material Library
**File:** `lib/msg1998/materials_1998.py`

```python
# Period-accurate materials for 1998 NYC

MATERIALS_1998 = {
    # Building materials
    "concrete_1998": {
        "base_color": (0.5, 0.5, 0.5),
        "roughness": 0.85,
        "wear_level": "moderate",
    },
    "brick_nyc": {
        "base_color": (0.6, 0.35, 0.25),
        "roughness": 0.9,
        "mortar_visible": True,
    },
    # Signage (pre-LED)
    "illuminated_sign_fluorescent": {
        "emission_type": "fluorescent",
        "color_temperature": 4500,  # Warm fluorescent
    },
    "neon_sign": {
        "emission_type": "neon",
        "glow_radius": 0.02,
    },
    # Street elements
    "pay_phone_metal": {
        "base_color": (0.4, 0.4, 0.4),
        "metallic": 0.8,
    },
}

def create_period_material(material_id: str) -> bpy.types.Material:
    """Create period-accurate material."""
    ...
```

### Task 4: Photo Projection System
**File:** `lib/msg1998/photo_projection.py`

```python
@dataclass
class ProjectionSetup:
    """Camera-based photo projection setup."""
    source_image: bpy.types.Image
    camera: bpy.types.Object
    target_mesh: bpy.types.Object
    uv_layer_name: str

def setup_photo_projection(
    image_path: Path,
    camera: bpy.types.Object,
    target_mesh: bpy.types.Object
) -> ProjectionSetup:
    """Set up photo projection from matched camera."""
    ...

def bake_projection(projection: ProjectionSetup, resolution: int = 4096) -> bpy.types.Image:
    """Bake projected texture to UV map."""
    ...
```

### Task 5: Location Asset Manager
**File:** `lib/msg1998/location_asset.py`

```python
@dataclass
class LocationAsset:
    """Complete location asset."""
    location_id: str
    name: str
    address: str
    coordinates: tuple[float, float]
    period_year: int
    blend_file: Path
    render_layers: list[str]
    metadata: dict

def create_location_asset(
    location_id: str,
    source_dir: Path,
    dest_dir: Path
) -> LocationAsset:
    """Create complete location asset from source materials."""
    ...

def export_location_package(asset: LocationAsset, output_dir: Path) -> Path:
    """Export location package for compositing phase."""
    ...
```

---

## File Structure

```
lib/msg1998/
├── modeling_pipeline.py   # Task 1
├── geometry_builders.py   # Task 2
├── materials_1998.py      # Task 3
├── photo_projection.py    # Task 4
├── location_asset.py      # Task 5
└── ...
```

---

## Validation Criteria

- [ ] Universal Stage Order enforced
- [ ] Period-accurate materials available
- [ ] Photo projection bakes correctly
- [ ] Location assets export properly

---

## Estimated Time

**3-4 hours**
