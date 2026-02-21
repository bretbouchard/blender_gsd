# Geometry Nodes Tutorial Utilities - Build Plan

**Goal:** Create reusable Python utilities from 13 CGMatter tutorials covering advanced Blender 5.x techniques.

---

## Overview

This plan organizes tutorial content into **6 core utility modules** with shared foundations. Each module provides Python APIs for programmatic control of techniques demonstrated in the tutorials.

### Cross-Cutting Patterns Identified

| Pattern | Tutorials | Reusability |
|---------|-----------|-------------|
| **Simulation Zones** | Grid Sim, Curl Noise, Erosion | Core simulation loop |
| **Volume/Grid Operations** | Volume Nodes, Volumetrics, Beginner Guide | Grid creation, sampling, conversion |
| **Particle Distribution** | Fur, Set Extension, Curl | Point distribution with variation |
| **Instance Control** | Triangle Parenting, Folding, Handwriting | Instance transform extraction |
| **Shader Integration** | Folding, Volumetrics | Shader-based effects from GN |
| **Proximity Effects** | Set Extension, Erosion | Distance-based calculations |

---

## Module Architecture

```
lib/
├── geometry_nodes/          # NEW: Core GN utilities
│   ├── __init__.py
│   ├── node_builder.py      # Programmatic node tree creation
│   ├── attributes.py        # Named attribute handling
│   ├── instances.py         # Instance extraction/control
│   ├── simulation.py        # Simulation zone helpers
│   └── fields.py            # Field operations
│
├── volumes/                 # NEW: Volume & grid operations
│   ├── __init__.py
│   ├── grid_ops.py          # Grid creation, sampling, conversion
│   ├── sdf_tools.py         # Signed distance field utilities
│   ├── vdb_io.py            # VDB import/export
│   └── shaders.py           # Volume shader presets
│
├── particles/               # NEW: Particle systems
│   ├── __init__.py
│   ├── curl_noise.py        # Divergence-free curl calculation
│   ├── distribution.py      # Point distribution with variation
│   ├── forces.py            # Force field integration
│   └── hair.py              # Fur/hair generation
│
├── mesh_ops/                # NEW: Mesh operations
│   ├── __init__.py
│   ├── erosion.py           # Edge/face erosion systems
│   ├── boolean_tools.py     # Advanced boolean operations
│   ├── proximity.py         # Geometry proximity effects
│   └── cleanup.py           # Floater removal, manifold fix
│
├── studio/                  # NEW: Studio/environment
│   ├── __init__.py
│   ├── backdrop.py          # Infinite sweep creation
│   ├── lighting.py          # Studio lighting presets
│   └── projection.py        # Camera projection setup
│
└── effects/                 # NEW: Special effects
    ├── __init__.py
    ├── folding.py           # Building folding effect
    ├── handwriting.py       # Handwriting text system
    └── compositing.py       # Compositor integration
```

---

## Phase 1: Foundation - Geometry Nodes Core

**Priority:** HIGH (required by all other modules)
**Tutorials:** All (cross-cutting)

### 1.1 Node Builder (`geometry_nodes/node_builder.py`)

Programmatic creation of node trees.

```python
# Proposed API
class NodeTreeBuilder:
    """Build geometry node trees programmatically."""

    def __init__(self, name: str):
        self.tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')

    def add_node(self, node_type: str, location: tuple, **inputs) -> Node:
        """Add node with optional input connections."""

    def link(self, from_node: Node, from_socket: str,
             to_node: Node, to_socket: str) -> Link:
        """Connect two nodes."""

    def add_simulation_zone(self) -> tuple[Node, Node]:
        """Create simulation input/output pair."""

    def add_repeat_zone(self, iterations: int) -> tuple[Node, Node]:
        """Create repeat zone for substeps."""

    def wrap_as_group(self, inputs: list, outputs: list) -> None:
        """Create node group interface."""
```

**Reusable Patterns:**
- Simulation zone setup (grid sim, curl noise)
- Repeat zone for substeps
- Named attribute storage
- Field math operations

### 1.2 Instance Control (`geometry_nodes/instances.py`)

Extract and control instance transforms (Triangle Parenting pattern).

```python
# Proposed API
class InstanceController:
    """Control instances via geometry nodes."""

    @staticmethod
    def create_triangle_proxy(name: str = "Triangle_Proxy") -> Object:
        """Create 3-vertex triangle mesh for vertex parenting."""

    @staticmethod
    def parent_to_triangle(child: Object, triangle: Object) -> None:
        """Parent object to triangle via vertex triangle mode."""

    @staticmethod
    def extract_transform_matrix(instances: Geometry) -> list[Matrix]:
        """Extract 4x4 matrices from instances."""

    @staticmethod
    def apply_transform_to_instances(geometry: Geometry,
                                      matrices: list[Matrix]) -> Geometry:
        """Apply transform matrices to instances."""
```

**From Tutorial:** Triangle Parenting
**Reused In:** Folding Effect, Set Extension

### 1.3 Simulation Helpers (`geometry_nodes/simulation.py`)

```python
# Proposed API
class SimulationBuilder:
    """Build simulation zones with common patterns."""

    def __init__(self, builder: NodeTreeBuilder):
        self.builder = builder

    def create_advection_step(self, velocity_grid, dt: float):
        """Create grid advection for smoke/fluid."""

    def create_pressure_iteration(self, iterations: int = 4):
        """Create pressure solve for incompressibility."""

    def create_substep_loop(self, substeps: int = 5):
        """Create repeat zone for substeps."""

    def store_state(self, name: str, geometry: Geometry):
        """Store simulation state for next frame."""
```

**From Tutorials:** Grid-Based Simulation, Curl Noise Particles
**Reused In:** Erosion, Hair dynamics

---

## Phase 2: Volume System

**Priority:** HIGH
**Tutorials:** Volume Nodes System, Volume Nodes Beginner Guide, Volumetric Rendering

### 2.1 Grid Operations (`volumes/grid_ops.py`)

```python
# Proposed API
class GridOperations:
    """Volume grid manipulation utilities."""

    @staticmethod
    def create_density_grid(resolution: tuple[int, int, int],
                            name: str = "density") -> Volume:
        """Create empty density grid."""

    @staticmethod
    def points_to_sdf(points: Points,
                      voxel_size: float = 0.1) -> Volume:
        """Convert point cloud to SDF grid."""

    @staticmethod
    def mesh_to_sdf(mesh: Mesh,
                    voxel_size: float = 0.05) -> Volume:
        """Convert mesh to SDF grid."""

    @staticmethod
    def sample_grid(volume: Volume,
                    positions: list[Vector],
                    grid_name: str = "density") -> list[float]:
        """Sample grid values at positions."""

    @staticmethod
    def grid_to_mesh(sdf_grid: Volume,
                     iso_level: float = 0.0) -> Mesh:
        """Convert SDF grid to polygon mesh."""

    @staticmethod
    def dilate(grid: Volume, amount: float) -> Volume:
        """Expand grid values (OpenVDB dilate)."""

    @staticmethod
    def erode(grid: Volume, amount: float) -> Volume:
        """Contract grid values (OpenVDB erode)."""
```

### 2.2 SDF Tools (`volumes/sdf_tools.py`)

```python
# Proposed API
class SDFTools:
    """Signed Distance Field utilities."""

    @staticmethod
    def set_background(grid: Volume, value: float = -1.0) -> Volume:
        """Set background value (outside = negative for SDF)."""

    @staticmethod
    def compute_gradient(sdf_grid: Volume) -> Volume:
        """Get surface normals from SDF gradient."""

    @staticmethod
    def boolean_union(sdf_a: Volume, sdf_b: Volume) -> Volume:
        """SDF boolean union (min)."""

    @staticmethod
    def boolean_difference(sdf_a: Volume, sdf_b: Volume) -> Volume:
        """SDF boolean difference (max with negation)."""

    @staticmethod
    def smooth_union(sdf_a: Volume, sdf_b: Volume,
                     smoothness: float = 0.1) -> Volume:
        """Smooth SDF blending."""
```

### 2.3 Volume Shaders (`volumes/shaders.py`)

```python
# Proposed API
class VolumeShaderPresets:
    """Pre-built volume shader setups."""

    @staticmethod
    def create_fog(density: float = 0.5,
                   anisotropy: float = 0.0) -> Material:
        """Create basic fog material."""

    @staticmethod
    def create_smoke(density: float = 10.0,
                     color: tuple = (0.2, 0.2, 0.2)) -> Material:
        """Create smoke material."""

    @staticmethod
    def create_god_rays(density: float = 0.3,
                        anisotropy: float = 0.7) -> Material:
        """Create god rays material with forward scatter."""

    @staticmethod
    def create_cloud(density: float = 5.0,
                     density_variation: float = 0.5) -> Material:
        """Create cloud material with noise."""

# Density reference table (from tutorial)
DENSITY_PRESETS = {
    "thin_fog": 0.1,
    "thick_fog": 1.0,
    "clouds": 10.0,
    "smoke": 50.0,
    "heavy_smoke": 100.0,
}
```

---

## Phase 3: Particle Systems

**Priority:** MEDIUM-HIGH
**Tutorials:** Curl Noise Particles, Fur/Hair Systems, Set Extension

### 3.1 Curl Noise (`particles/curl_noise.py`)

```python
# Proposed API
class CurlNoise:
    """Divergence-free curl noise for particles."""

    @staticmethod
    def curl_2d(scalar_field: callable,
                position: Vector,
                epsilon: float = 0.001) -> Vector:
        """
        Calculate 2D curl from scalar field.

        For field V with only Z component:
            Curl X = dVz/dY
            Curl Y = -dVz/dX
            Curl Z = 0
        """

    @staticmethod
    def curl_3d(vector_field: callable,
                position: Vector,
                epsilon: float = 0.001) -> Vector:
        """
        Calculate full 3D curl.

        Curl X = dVz/dY - dVy/dZ
        Curl Y = dVx/dZ - dVz/dX
        Curl Z = dVy/dX - dVx/dY
        """

    @staticmethod
    def from_noise_texture(position: Vector,
                           scale: float = 1.0,
                           detail: int = 3) -> Vector:
        """Curl from Blender noise texture."""

    @staticmethod
    def from_voronoi_distance(position: Vector,
                               scale: float = 1.0) -> Vector:
        """Curl from Voronoi distance field."""

    @staticmethod
    def from_wave_texture(position: Vector,
                          scale: float = 1.0,
                          distortion: float = 1.0) -> Vector:
        """Curl from wave texture (periodic whirlpools)."""

    @staticmethod
    def from_sine_waves(position: Vector,
                        frequency: float = 1.0) -> Vector:
        """Curl from sine waves (regular spirals)."""


class CurlParticleSystem:
    """Build curl-based particle simulation."""

    def __init__(self, particle_count: int):
        self.particles = particle_count

    def add_layer(self, curl_generator: CurlNoise,
                  scale: float, strength: float):
        """Add multi-scale curl layer."""

    def set_substeps(self, count: int):
        """Set simulation substeps."""

    def add_force(self, force_type: str, **params):
        """Add gravity, wind, attraction forces."""

    def build_node_tree(self) -> NodeTree:
        """Generate complete GN tree."""
```

### 3.2 Point Distribution (`particles/distribution.py`)

```python
# Proposed API
class PointDistributor:
    """Advanced point distribution with variation."""

    @staticmethod
    def on_faces(mesh: Mesh,
                 count: int,
                 seed: int = 0,
                 density_texture: str = None) -> Points:
        """Distribute points on mesh faces."""

    @staticmethod
    def with_size_variation(points: Points,
                            base_size: float,
                            min_factor: float = 0.1,
                            curve: str = "bias_small") -> Points:
        """Add size variation with curve control."""

    @staticmethod
    def edge_gravity(points: Points,
                     target_edges: Mesh,
                     falloff: float = 1.0,
                     noise: float = 0.5) -> Points:
        """Pull points toward nearest edges."""

    @staticmethod
    def dual_layer(mesh: Mesh,
                   edge_count: int,
                   fill_count: int,
                   edge_size: float,
                   fill_size: float) -> Points:
        """Create dual-layer particle system (Set Extension pattern)."""


# Size distribution curves (from tutorial)
SIZE_CURVES = {
    "uniform": lambda x: x,
    "bias_small": lambda x: x ** 2,
    "bias_large": lambda x: x ** 0.5,
    "bell": lambda x: 0.5 + 0.5 * math.sin((x - 0.5) * math.pi),
}
```

### 3.3 Hair/Fur System (`particles/hair.py`)

```python
# Proposed API
class HairClumpGenerator:
    """Generate procedural hair clumps."""

    @staticmethod
    def create_spiral_clump(height: float = 2.0,
                            start_radius: float = 1.0,
                            end_radius: float = 0.5,
                            rotations: float = 8.0) -> Curve:
        """Create spiral hair clump."""

    @staticmethod
    def add_variation(clump: Curve,
                      seed: int = 0,
                      radius_range: tuple = (0.5, 1.5),
                      rotation_range: tuple = (0.5, 1.2),
                      height_range: tuple = (1.0, 2.0)) -> Curve:
        """Add random variation to clump parameters."""

    @staticmethod
    def distort(clump: Curve,
                strength: float = 0.1,
                noise_scale: float = 1.0) -> Curve:
        """Apply noise distortion to clump."""

    @staticmethod
    def clump_to_mesh(clump: Curve,
                      profile_resolution: int = 3) -> Mesh:
        """Convert curve to renderable mesh."""


class FurSystem:
    """Complete fur/hair system."""

    def __init__(self, surface: Mesh):
        self.surface = surface

    def set_density(self, count: int):
        """Set fur density."""

    def add_clump_variants(self, count: int = 5):
        """Add multiple clump variations."""

    def set_scale_range(self, min_scale: float, max_scale: float):
        """Set fur scale range."""

    def create_material(self, melanin: float = 0.5) -> Material:
        """Create Principled Hair BSDF material."""

    def build(self) -> Geometry:
        """Generate complete fur geometry."""
```

---

## Phase 4: Mesh Operations

**Priority:** MEDIUM
**Tutorials:** Erosion Systems, Building Folding, Set Extension

### 4.1 Erosion System (`mesh_ops/erosion.py`)

```python
# Proposed API
class EdgeErosion:
    """Erode mesh edges for weathered look."""

    @staticmethod
    def by_angle(mesh: Mesh,
                 angle_threshold: float = 6.0,  # radians
                 noise_scale: float = 1.0) -> Mesh:
        """
        Erode edges based on angle.

        Flow: Edge Angle → Separate → Delete Faces → Mesh to Curve
              → Resample → Tube → SDF Remesh → Boolean
        """

    @staticmethod
    def create_tube_cutter(points: Points,
                           base_radius: float,
                           noise_amplitude: float) -> Mesh:
        """Create noise-controlled tube for boolean cutting."""


class FaceErosion:
    """Erode mesh faces with pitting."""

    @staticmethod
    def by_noise(mesh: Mesh,
                 point_count: int = 1500,
                 threshold: float = 0.5,
                 noise_scale: float = 1.0) -> Mesh:
        """
        Erode faces based on noise threshold.

        Flow: Distribute Points → Noise → Delete by threshold
              → Points to SDF → Grid to Mesh → Boolean
        """

    @staticmethod
    def remove_floaters(mesh: Mesh,
                        min_area: float = 0.001) -> Mesh:
        """
        Remove disconnected floating pieces.

        Flow: Mesh Island → Accumulate Field (face area)
              → Delete if total < threshold
        """


class ErosionSystem:
    """Combined edge and face erosion."""

    def __init__(self, mesh: Mesh):
        self.mesh = mesh

    def erode_edges(self, **kwargs) -> 'ErosionSystem':
        """Apply edge erosion."""

    def erode_faces(self, **kwargs) -> 'ErosionSystem':
        """Apply face erosion."""

    def add_subdivision(self, levels: int = 1) -> 'ErosionSystem':
        """Add subdivision for detail."""

    def finalize(self) -> Mesh:
        """Return eroded mesh."""
```

### 4.2 Proximity Effects (`mesh_ops/proximity.py`)

```python
# Proposed API
class ProximityEffects:
    """Geometry proximity-based effects."""

    @staticmethod
    def distance_to_geometry(points: Points,
                             target: Geometry,
                             mode: str = "edges") -> list[float]:
        """Calculate distance from points to target geometry."""

    @staticmethod
    def blend_to_nearest(points: Points,
                         target: Geometry,
                         max_distance: float,
                         falloff: str = "smooth") -> Points:
        """
        Blend point positions toward nearest target.

        Flow: Geometry Proximity → Map Range → Noise → Mix Vector
        """

    @staticmethod
    def proximity_mask(points: Points,
                       target: Geometry,
                       inner_distance: float,
                       outer_distance: float) -> list[float]:
        """Create 0-1 mask based on proximity."""


# Falloff curves
FALLOFF_CURVES = {
    "linear": lambda d, max_d: 1 - (d / max_d),
    "smooth": lambda d, max_d: 1 - (d / max_d) ** 2,
    "sharp": lambda d, max_d: 1 - math.sqrt(d / max_d),
}
```

### 4.3 Boolean Tools (`mesh_ops/boolean_tools.py`)

```python
# Proposed API
class BooleanOperations:
    """Advanced boolean operations."""

    @staticmethod
    def difference(base: Mesh, cutter: Mesh,
                   solver: str = "manifold") -> Mesh:
        """Boolean difference with solver selection."""

    @staticmethod
    def union(meshes: list[Mesh], solver: str = "manifold") -> Mesh:
        """Boolean union of multiple meshes."""

    @staticmethod
    def intersect(a: Mesh, b: Mesh, solver: str = "manifold") -> Mesh:
        """Boolean intersection."""

    @staticmethod
    def sdf_boolean(a: Volume, b: Volume, operation: str) -> Volume:
        """Boolean via SDF operations (faster, cleaner)."""
```

---

## Phase 5: Studio & Environment

**Priority:** MEDIUM
**Tutorials:** Infinite Background Studio, Blender 5.1 Features

### 5.1 Backdrop Creator (`studio/backdrop.py`)

```python
# Proposed API
class InfiniteBackdrop:
    """Create infinite studio backdrops."""

    @staticmethod
    def single_sweep(width: float = 10.0,
                     height: float = 5.0,
                     depth: float = 10.0,
                     curve_segments: int = 15) -> Mesh:
        """
        Create single-wall photo sweep.

        Flow: Plane → Extrude edge up → Bevel edges → Shade smooth
        """

    @staticmethod
    def corner_sweep(width: float = 10.0,
                     height: float = 5.0,
                     depth: float = 10.0,
                     corner_segments: int = 10,
                     curve_segments: int = 15) -> Mesh:
        """
        Create two-wall corner backdrop.

        Flow: Plane → Bevel vertex → Extrude edges → Bevel → Smooth
        """

    @staticmethod
    def cyc_curve(controls: list[tuple[float, float]],
                  segments: int = 20) -> Mesh:
        """Create custom cyc curve backdrop."""


class StudioSetup:
    """Complete studio lighting setup."""

    def __init__(self, backdrop: Mesh):
        self.backdrop = backdrop

    def add_key_light(self, power: float = 3000.0,
                      distance: float = 10.0,
                      size: float = 2.0) -> Object:
        """Add main key light."""

    def add_fill_light(self, power: float = 1500.0,
                       angle: float = 45.0) -> Object:
        """Add fill light."""

    def add_rim_light(self, power: float = 2000.0) -> Object:
        """Add rim/back light."""

    def configure_for_subject(self, subject: Object,
                               distance_factor: float = 3.0):
        """Auto-configure lights for subject size."""

    def set_engine(self, engine: str, **kwargs):
        """Set render engine (Cycles/Eevee) with optimizations."""
```

### 5.2 Camera Projection (`studio/projection.py`)

```python
# Proposed API
class CameraProjection:
    """Camera projection for set extension."""

    @staticmethod
    def setup_projector(camera: Object,
                        image: str,
                        use_window_coords: bool = True) -> Material:
        """
        Setup camera projection material.

        From tutorial: Use Window Coordinates (not UV)
        """

    @staticmethod
    def create_projection_geometry(camera: Object,
                                    distance: float) -> Mesh:
        """Create geometry to receive projection."""

    @staticmethod
    def enable_auto_refresh(material: Material):
        """Enable auto refresh for movie clips."""
```

---

## Phase 6: Special Effects

**Priority:** MEDIUM-LOW
**Tutorials:** Building Folding, Handwriting System

### 6.1 Folding Effect (`effects/folding.py`)

```python
# Proposed API
class BuildingFolder:
    """Doctor Strange-style building folding effect."""

    @staticmethod
    def calculate_alpha_angle(instance_count: int) -> float:
        """
        Calculate wedge angle for visibility masking.

        alpha = 2π / number_of_instances
        """
        return 2 * math.pi / instance_count

    @staticmethod
    def create_folding_material(instance_count: int) -> Material:
        """
        Create shader material for wedge masking.

        Flow: Texture Coord → Separate XYZ → Vector Rotate
              → Mask calculations → Alpha output
        """

    @staticmethod
    def setup_folding_geometry(base_mesh: Mesh,
                                instance_count: int,
                                radius: float) -> Geometry:
        """
        Setup geometry nodes for folding instances.

        Flow: Mesh Circle → Instance on Points → Transform
              → Store Named Attribute → Animated rotation
        """

    @staticmethod
    def create_animation_driver(duration: float = 5.0) -> Driver:
        """Create time-based animation driver."""


class FoldingSystem:
    """Complete folding effect system."""

    def __init__(self, subject_mesh: Mesh):
        self.subject = subject_mesh

    def set_instance_count(self, count: int):
        """Set number of wedge instances."""

    def set_rotation_axis(self, axis: str = "X"):
        """Set folding rotation axis."""

    def create_material(self) -> Material:
        """Create and apply folding material."""

    def build(self) -> Geometry:
        """Build complete folding system."""
```

### 6.2 Handwriting System (`effects/handwriting.py`)

```python
# Proposed API
class HandwritingSystem:
    """Procedural handwriting text system."""

    def __init__(self, alphabet_objects: dict[str, list[Object]]):
        """
        Initialize with letter variants.

        Expected format: {'a': [a_1, a_2, a_3], 'b': [b_1, b_2, b_3], ...}
        """
        self.letters = alphabet_objects

    @staticmethod
    def find_char_index(text: str, position: int,
                        alphabet: str = " abcdefghijklmnopqrstuvwxyz") -> int:
        """Find index of character in alphabet string."""

    @staticmethod
    def select_variant(char_index: int, variant_count: int = 3) -> int:
        """Select random variant index (index × 3 + random(0-2))."""

    @staticmethod
    def calculate_positions(instances: list[Geometry]) -> list[Vector]:
        """
        Calculate positions using Accumulate Field (trailing).

        Flow: Instance Bounds (width) → Accumulate Field → Translate
        """

    def generate_text(self, text: str, spacing: float = 1.0) -> Geometry:
        """Generate handwriting geometry for text."""

    def fix_sort_order(self, geometry: Geometry) -> Geometry:
        """
        Fix render order using Sort Elements.

        Flow: Index → Multiply(-1) → Sort Elements (Group ID)
        """
```

### 6.3 Compositing Integration (`effects/compositing.py`)

```python
# Proposed API
class CompositorIntegration:
    """Compositor integration for set extension."""

    @staticmethod
    def setup_cryptomatte(scene: Scene,
                          object_names: list[str]) -> None:
        """Enable Cryptomatte for objects."""

    @staticmethod
    def create_stylized_composite():
        """
        Create stylized composite setup.

        From tutorial:
        Cryptomatte → Separate CGI → Pixelate → Kuwahara
        → Match black levels → Bloom → Lens Distortion
        """

    @staticmethod
    def add_volume_pass_separation():
        """Separate volume pass for optimization."""
```

---

## Implementation Priority Order

### Phase 1: Foundation (2-3 days)
1. `geometry_nodes/node_builder.py` - Core for all GN operations
2. `geometry_nodes/instances.py` - Triangle parenting, transform extraction
3. `geometry_nodes/simulation.py` - Simulation zone helpers

### Phase 2: Volume System (2-3 days)
4. `volumes/grid_ops.py` - Grid creation, sampling, conversion
5. `volumes/sdf_tools.py` - SDF utilities
6. `volumes/shaders.py` - Volume shader presets

### Phase 3: Particles (2-3 days)
7. `particles/curl_noise.py` - Curl noise calculations
8. `particles/distribution.py` - Point distribution
9. `particles/hair.py` - Fur/hair system

### Phase 4: Mesh Ops (1-2 days)
10. `mesh_ops/erosion.py` - Erosion systems
11. `mesh_ops/proximity.py` - Proximity effects
12. `mesh_ops/boolean_tools.py` - Boolean operations

### Phase 5: Studio (1 day)
13. `studio/backdrop.py` - Infinite backdrop
14. `studio/lighting.py` - Studio lighting
15. `studio/projection.py` - Camera projection

### Phase 6: Effects (1-2 days)
16. `effects/folding.py` - Building folding
17. `effects/handwriting.py` - Handwriting system
18. `effects/compositing.py` - Compositor integration

---

## Testing Strategy

Each module should have corresponding test files:

```
tests/unit/
├── test_geometry_nodes/
│   ├── test_node_builder.py
│   ├── test_instances.py
│   └── test_simulation.py
├── test_volumes/
│   ├── test_grid_ops.py
│   ├── test_sdf_tools.py
│   └── test_shaders.py
├── test_particles/
│   ├── test_curl_noise.py
│   ├── test_distribution.py
│   └── test_hair.py
├── test_mesh_ops/
│   ├── test_erosion.py
│   ├── test_proximity.py
│   └── test_boolean_tools.py
├── test_studio/
│   ├── test_backdrop.py
│   └── test_lighting.py
└── test_effects/
    ├── test_folding.py
    ├── test_handwriting.py
    └── test_compositing.py
```

---

## Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Foundation | 2-3 days | None |
| Phase 2: Volumes | 2-3 days | Phase 1 |
| Phase 3: Particles | 2-3 days | Phase 1 |
| Phase 4: Mesh Ops | 1-2 days | Phase 1 |
| Phase 5: Studio | 1 day | Phase 1 |
| Phase 6: Effects | 1-2 days | Phase 1, Phase 4 |
| **Total** | **9-14 days** | |

---

## Success Criteria

1. **Reusability**: Each utility can be used independently
2. **Documentation**: All public APIs documented with docstrings
3. **Test Coverage**: 80%+ coverage for all modules
4. **Tutorial Fidelity**: Techniques match CGMatter tutorials
5. **Performance**: Simulation utilities handle 10k+ particles efficiently
6. **Integration**: Modules work together seamlessly

---

*Plan created from 13 CGMatter tutorials - February 2026*
