# Tutorial Utilities Master Plan

**Goal:** Build comprehensive Python utilities from tutorial content covering:
1. **Launch Control** - Blender car rigging plugin
2. **Sanctus Library** - Procedural material plugin
3. **Blender 5.x** - New features (30+ topics)

---

## Research Summary

### 1. Launch Control (Auto Car Rig)
- **Version:** v1.9.1 (April 2025)
- **Purpose:** One-click vehicle rigging and animation
- **Features:** Suspension physics, steering, drift/jump physics, ground detection
- **Course:** "汽车动画 - 基础必备" by Daniel Vesterbaek (creator), ~3.5 hours
- **Supported:** Blender 3.6 - 4.3

### 2. Sanctus Library
- **Version:** v3.3.2
- **Purpose:** Procedural materials with damage/weathering/patterns
- **Features:** 1000+ materials, 32+ Shader Tools, Geometry Node generators
- **Shader Tools Panel:** In Shader Editor N-menu
- **Supported:** Blender 2.83 - 4.4

### 3. Blender 5.x
- **Released:** November 19, 2025 ("Hi Five")
- **Major Features:** ACES 2.0, Volume in GN, SDF modeling, new modifiers

---

## Part 1: Launch Control - Vehicle Rigging System

### Module: `lib/vehicle/launch_control/`

```
lib/vehicle/launch_control/
├── __init__.py
├── auto_rig.py           # One-click rigging
├── suspension.py         # Suspension physics
├── steering.py           # Steering with Ackermann
├── wheel_linking.py      # Speed-based wheel rotation
├── physics.py            # Drift, jump, offroad physics
├── ground_detection.py   # Terrain interaction
├── camera.py             # Camera follow systems
├── export.py             # FBX/GLTF export
└── presets.py            # Animation presets
```

#### 1.1 Auto Rig System (`auto_rig.py`)

```python
class LaunchControlRig:
    """One-click vehicle rigging system based on Launch Control plugin."""

    def __init__(self, vehicle_body: Object):
        self.body = vehicle_body
        self.wheels = []
        self.axles = []
        self.rig = None

    def detect_components(self,
                          wheel_naming: str = "auto",
                          axle_naming: str = "auto") -> dict:
        """
        Auto-detect vehicle components from naming conventions.

        Supported wheel naming:
        - wheel_fl, wheel_fr, wheel_rl, wheel_rr
        - wheel_01, wheel_02, wheel_03, wheel_04
        - FL, FR, RL, RR prefixes
        """

    def generate_rig(self,
                     suspension_type: str = "independent",
                     steering_type: str = "front") -> Object:
        """
        Generate complete armature with bones and controllers.

        Suspension types:
        - independent: Double wishbone/MacPherson
        - solid: Live axle
        - torsion_beam: Torsion beam axle
        """

    def apply_constraints(self) -> None:
        """Apply bone constraints for realistic movement."""

    def setup_drivers(self) -> None:
        """Setup drivers for speed-based wheel rotation."""

    def one_click_rig(self) -> Object:
        """Execute complete one-click rigging workflow."""


class WheelDetector:
    """Automatic wheel detection from mesh."""

    @staticmethod
    def by_name(obj: Object, pattern: str) -> list[Object]:
        """Detect wheels by naming pattern."""

    @staticmethod
    def by_geometry(obj: Object, radius_range: tuple) -> list[Object]:
        """Detect wheels by geometric properties."""

    @staticmethod
    def by_position(obj: Object, expected_positions: list) -> list[Object]:
        """Detect wheels by expected positions."""
```

#### 1.2 Suspension System (`suspension.py`)

```python
class SuspensionSystem:
    """Physics-based suspension simulation."""

    TYPES = {
        "double_wishbone": "Independent front/rear",
        "macpherson": "MacPherson strut",
        "solid_axle": "Live axle",
        "torsion_beam": "Torsion beam",
        "air_suspension": "Adjustable air bags"
    }

    def __init__(self, rig: Object):
        self.rig = rig

    def configure(self,
                  travel: float = 0.3,           # meters
                  spring_stiffness: float = 25000, # N/m
                  damping: float = 1500,          # Ns/m
                  preload: float = 0.0) -> None:
        """Set suspension parameters."""

    def enable_physics(self,
                       mode: str = "automatic",
                       substeps: int = 10) -> None:
        """
        Enable physics-based suspension.

        Modes:
        - automatic: Based on terrain
        - manual: Keyframe-driven
        - hybrid: Mix of both
        """

    def bake_animation(self,
                       frame_start: int,
                       frame_end: int,
                       sample_rate: int = 1) -> None:
        """Bake physics simulation to keyframes."""

    def get_displacement(self, wheel_index: int) -> float:
        """Get current suspension displacement."""

    def set_travel_limit(self, max_compression: float,
                         max_extension: float) -> None:
        """Set suspension travel limits."""


class DampingCurve:
    """Custom damping curve for suspension."""

    @staticmethod
    def linear(velocity: float, coefficient: float) -> float:
        """Linear damping."""

    @staticmethod
    def progressive(velocity: float,
                    base: float,
                    factor: float) -> float:
        """Progressive damping (stiffer at high speeds)."""

    @staticmethod
    def digressive(velocity: float,
                   base: float,
                   threshold: float) -> float:
        """Digressive damping (softer at high speeds)."""
```

#### 1.3 Steering System (`steering.py`)

```python
class SteeringSystem:
    """Vehicle steering control with Ackermann geometry."""

    def __init__(self, rig: Object):
        self.rig = rig

    def configure(self,
                  max_angle: float = 35.0,        # degrees
                  ackermann: bool = True,
                  four_wheel_steering: bool = False,
                  rear_ratio: float = 0.0) -> None:
        """
        Configure steering parameters.

        Args:
            max_angle: Maximum steering angle in degrees
            ackermann: Enable Ackermann steering geometry
            four_wheel_steering: Enable rear wheel steering
            rear_ratio: Rear wheel angle as ratio of front (0-1)
        """

    def create_controller(self,
                          location: tuple = (0, -0.3, 0.8),
                          shape: str = "steering_wheel") -> Object:
        """Create steering control object."""

    def apply_ackermann(self,
                        wheelbase: float,
                        track_width: float) -> None:
        """
        Apply Ackermann steering geometry.

        Ensures inner wheel turns more than outer wheel
        for proper turning circle.
        """

    def set_angle(self,
                  angle: float,
                  frame: int = None) -> None:
        """Set steering angle (optionally at specific frame)."""

    def create_animation(self,
                         keyframes: list[tuple[int, float]]) -> None:
        """Create steering animation from keyframe list."""


class AckermannGeometry:
    """Ackermann steering geometry calculations."""

    @staticmethod
    def calculate_angles(steering_input: float,
                         wheelbase: float,
                         track_width: float) -> tuple[float, float]:
        """
        Calculate inner and outer wheel angles.

        Returns:
            (inner_angle, outer_angle) in degrees
        """

    @staticmethod
    def turning_radius(steering_angle: float,
                       wheelbase: float) -> float:
        """Calculate turning radius."""
```

#### 1.4 Physics System (`physics.py`)

```python
class VehiclePhysics:
    """Physics-based vehicle movement."""

    def __init__(self, rig: Object):
        self.rig = rig

    def configure(self,
                  mass: float = 1500,              # kg
                  drag_coefficient: float = 0.3,
                  frontal_area: float = 2.2,       # m²
                  engine_power: float = 150000,    # watts
                  braking_force: float = 30000,    # N
                  center_of_mass: Vector = (0, 0, 0.5)) -> None:
        """Set vehicle physics parameters."""

    def drive_path(self,
                   path: Curve,
                   speed: float = 10.0,
                   follow_terrain: bool = True) -> None:
        """
        Drive vehicle along path with physics.

        Args:
            path: Curve object to follow
            speed: Target speed in m/s
            follow_terrain: Adjust to terrain height
        """

    def enable_drift_mode(self,
                          drift_factor: float = 0.7,
                          countersteer: bool = True) -> None:
        """
        Enable drifting physics.

        Args:
            drift_factor: 0 = grip, 1 = full slide
            countersteer: Auto countersteer for control
        """

    def simulate_jump(self,
                      launch_velocity: Vector,
                      rotation_axis: Vector = (1, 0, 0),
                      rotation_speed: float = 0.0) -> None:
        """
        Simulate vehicle jump with physics.

        Args:
            launch_velocity: Initial velocity vector
            rotation_axis: Axis for mid-air rotation
            rotation_speed: Rotation in radians/sec
        """

    def offroad_mode(self,
                     roughness: float = 0.5,
                     suspension_travel: float = 0.4) -> None:
        """
        Configure for off-road driving.

        Args:
            roughness: Terrain roughness factor
            suspension_travel: Increased suspension travel
        """

    def simulate_crash(self,
                       impact_force: Vector,
                       deform_amount: float = 0.1) -> None:
        """Simulate crash impact with deformation."""


class SpeedSegments:
    """Speed-based animation workflow from Launch Control."""

    def __init__(self, rig: Object):
        self.rig = rig
        self.segments = []

    def add_segment(self,
                    frame_start: int,
                    frame_end: int,
                    target_speed: float,
                    acceleration: float = None) -> None:
        """Add speed segment."""

    def generate_animation(self) -> None:
        """Generate animation from segments."""
```

#### 1.5 Ground Detection (`ground_detection.py`)

```python
class GroundDetection:
    """Terrain interaction system."""

    def __init__(self, rig: Object):
        self.rig = rig

    def set_ground_object(self,
                          ground: Object,
                          offset: float = 0.0) -> None:
        """Set ground mesh for detection."""

    def enable_auto_height(self,
                           ray_direction: Vector = (0, 0, -1)) -> None:
        """Enable automatic height adjustment."""

    def set_wheel_contact_points(self,
                                  points: list[Vector]) -> None:
        """Set custom wheel contact points."""

    def get_surface_normal(self, position: Vector) -> Vector:
        """Get surface normal at position."""

    def get_surface_type(self, position: Vector) -> str:
        """Get surface type at position (asphalt, dirt, grass)."""
```

#### 1.6 Animation Presets (`presets.py`)

```python
class AnimationPresets:
    """Pre-built animation presets from Launch Control."""

    @staticmethod
    def drift_donut(rig: Object,
                    duration: int = 120,
                    direction: str = "left") -> None:
        """Create drifting donut animation."""

    @staticmethod
    def figure_eight(rig: Object,
                     duration: int = 240) -> None:
        """Create figure-8 driving pattern."""

    @staticmethod
    def slalom(rig: Object,
               cone_count: int = 5,
               spacing: float = 10.0) -> None:
        """Create slalom driving pattern."""

    @staticmethod
    def jump_ramp(rig: Object,
                  approach_speed: float = 15.0,
                  ramp_angle: float = 30.0) -> None:
        """Create jump animation."""

    @staticmethod
    def offroad_bounce(rig: Object,
                       roughness: float = 0.3) -> None:
        """Create off-road bouncing effect."""

    @staticmethod
    def emergency_brake(rig: Object,
                        initial_speed: float = 20.0,
                        frame: int = 60) -> None:
        """Create emergency braking with nose dive."""

    @staticmethod
    def acceleration_squat(rig: Object,
                           acceleration: float = 5.0) -> None:
        """Create acceleration squat effect."""
```

---

## Part 2: Sanctus Library - Procedural Materials

### Module: `lib/materials/sanctus/`

```
lib/materials/sanctus/
├── __init__.py
├── shader_tools.py       # 32+ shader tools API
├── damage.py             # Damage/wear generators
├── weathering.py         # Weathering effects
├── patterns.py           # Pattern generators
├── materials.py          # Material presets
├── baker.py              # Texture baking
└── geometry_nodes.py     # GN-based generators
```

#### 2.1 Shader Tools (`shader_tools.py`)

```python
class SanctusShaderTools:
    """Access to Sanctus Library 32+ shader tools."""

    # Color coding for performance:
    # 🟢 Green = Fast
    # 🟡 Yellow = Medium
    # 🔴 Red = Slow
    # E = Eevee compatible
    # C = Cycles compatible

    def __init__(self):
        self.tools = self._load_tools()

    def get_tool(self, tool_name: str) -> NodeTree:
        """Get shader tool by name."""

    def apply_damage(self,
                     material: Material,
                     damage_type: str = "scratches",
                     intensity: float = 0.5,
                     seed: int = 0) -> Material:
        """
        Apply damage shader tool to material.

        Damage types:
        - scratches: Fine scratch marks
        - dents: Surface dents
        - chips: Paint chips
        - cracks: Surface cracking
        - rust: Rust spots
        - burns: Burn marks
        """

    def apply_weathering(self,
                         material: Material,
                         weather_type: str = "dust",
                         amount: float = 0.5) -> Material:
        """
        Apply weathering shader tool.

        Weather types:
        - dust: Dust accumulation
        - dirt: Dirt and grime
        - rain_streaks: Water streaking
        - sun_bleach: Sun fading
        - moss: Moss growth
        - oxidation: Metal oxidation
        """

    def apply_pattern(self,
                      material: Material,
                      pattern_type: str = "tiles",
                      scale: float = 1.0) -> Material:
        """
        Apply pattern shader tool.

        Pattern types:
        - tiles: Tile pattern
        - bricks: Brick pattern
        - planks: Wood planks
        - fabric: Fabric weave
        - noise: Noise pattern
        - voronoi: Cell pattern
        """

    def layer_materials(self,
                        base: Material,
                        overlay: Material,
                        mask_type: str = "edge_wear",
                        blend_mode: str = "mix") -> Material:
        """Layer two materials with masking."""


class DamageGenerator:
    """Procedural damage generation tools."""

    @staticmethod
    def scratches(length: float = 0.1,
                  width: float = 0.002,
                  density: float = 50.0,
                  direction: Vector = (1, 0, 0)) -> NodeTree:
        """Generate scratch pattern node group."""

    @staticmethod
    def dents(depth: float = 0.01,
              size: float = 0.05,
              density: float = 20.0) -> NodeTree:
        """Generate dent pattern node group."""

    @staticmethod
    def paint_chips(size_range: tuple = (0.01, 0.05),
                    edge_sharpness: float = 0.8) -> NodeTree:
        """Generate paint chip pattern."""

    @staticmethod
    def cracks(width: float = 0.005,
               branching: int = 3,
               seed: int = 0) -> NodeTree:
        """Generate crack pattern."""


class WeatheringGenerator:
    """Procedural weathering effects."""

    @staticmethod
    def edge_wear(intensity: float = 0.5,
                  sharpness: float = 0.3) -> NodeTree:
        """Generate edge wear mask."""

    @staticmethod
    def dust_accumulation(amount: float = 0.3,
                          gravity_direction: Vector = (0, 0, -1)) -> NodeTree:
        """Generate dust accumulation on horizontal surfaces."""

    @staticmethod
    def water_streaks(length: float = 0.5,
                      width: float = 0.02,
                      density: float = 10.0) -> NodeTree:
        """Generate water streak pattern."""

    @staticmethod
    def moss_growth(amount: float = 0.3,
                    prefer_shade: bool = True) -> NodeTree:
        """Generate moss growth pattern."""

    @staticmethod
    def rust_spots(size: float = 0.1,
                   spread: float = 0.5,
                   color: tuple = (0.4, 0.2, 0.1)) -> NodeTree:
        """Generate rust spot pattern."""
```

#### 2.2 Material Presets (`materials.py`)

```python
class SanctusMaterials:
    """Access to 1000+ procedural material presets."""

    CATEGORIES = [
        "stone_brick",
        "flooring",
        "fabric",
        "wood",
        "metal",
        "hair_fur",
        "cardboard",
        "superhero",
        "knit_wool",
        "weathered"
    ]

    def __init__(self):
        self.materials = self._load_library()

    def get_material(self,
                     category: str,
                     name: str,
                     apply_damage: bool = False) -> Material:
        """Get material from library by category and name."""

    def search(self, query: str) -> list[Material]:
        """Search materials by keyword."""

    def list_category(self, category: str) -> list[str]:
        """List all materials in category."""

    def create_variant(self,
                       base: Material,
                       damage_level: float = 0.0,
                       weathering_level: float = 0.0,
                       color_variation: float = 0.0) -> Material:
        """Create variant of existing material."""


# Material presets organized by category
MATERIAL_PRESETS = {
    "stone_brick": {
        "stone_brick_floor": "Procedural stone brick flooring",
        "weathered_brick_wall": "Old weathered brick wall",
        "cobblestone": "Cobblestone pattern",
    },
    "wood": {
        "wood_planks": "Wooden plank flooring",
        "old_wood": "Aged weathered wood",
        "bark": "Tree bark texture",
    },
    "fabric": {
        "superhero_fabric": "Superhero suit material",
        "knit_wool": "Knitted wool texture",
        "denim": "Denim fabric",
    },
    "metal": {
        "brushed_metal": "Brushed metal surface",
        "rusted_metal": "Rusted iron/steel",
        "chrome": "Chrome finish",
    },
    "hair_fur": {
        "fur_short": "Short animal fur",
        "fur_long": "Long shaggy fur",
        "hair_strands": "Human hair strands",
    }
}
```

#### 2.3 Texture Baker (`baker.py`)

```python
class SanctusBaker:
    """Bake procedural materials to textures."""

    def __init__(self, material: Material):
        self.material = material

    def bake_all(self,
                 resolution: int = 2048,
                 output_path: str = None) -> dict:
        """
        Bake all texture maps.

        Returns dict with paths to:
        - diffuse/albedo
        - normal
        - roughness
        - metallic
        - displacement
        - ao
        """

    def bake_channel(self,
                     channel: str,
                     resolution: int = 2048) -> Image:
        """Bake single channel to image."""

    def bake_to_udim(self,
                     resolution: int = 2048,
                     tile_range: tuple = (1001, 1010)) -> list[Image]:
        """Bake to UDIM tiles."""

    def export_for_game(self,
                        engine: str = "unreal",
                        resolution: int = 1024) -> dict:
        """
        Export game-ready textures.

        Args:
            engine: "unreal", "unity", "godot"
        """
```

---

## Part 3: Blender 5.x New Features

### Module: `lib/blender5x/`

```
lib/blender5x/
├── __init__.py
├── color_management/
│   ├── __init__.py
│   ├── aces.py            # ACES 1.3/2.0 workflows
│   ├── hdr_export.py      # HDR video/image export
│   └── view_transforms.py # View transform utilities
├── geometry_nodes/
│   ├── __init__.py
│   ├── volume_ops.py      # Volume data in GN
│   ├── sdf_modeling.py    # SDF boolean operations
│   └── bundles.py         # Bundles & closures
├── rendering/
│   ├── __init__.py
│   ├── thin_film.py       # Iridescence effects
│   ├── sss.py             # Improved subsurface
│   ├── nano_vdb.py        # NanoVDB integration
│   └── volume_render.py   # New volume algorithm
├── modifiers/
│   ├── __init__.py
│   ├── array_new.py       # New array modifier
│   ├── distribute.py      # Surface distribute
│   └── instances.py       # Instance modifiers
├── compositor/
│   ├── __init__.py
│   ├── vse_integration.py # Compositor in VSE
│   └── asset_shelf.py     # Drag & drop effects
└── animation/
    ├── __init__.py
    ├── shape_keys.py      # Multi-select shape keys
    └── dope_sheet.py      # Dope Sheet utilities
```

#### 3.1 ACES/HDR Color Management (`color_management/aces.py`)

```python
class ACESWorkflow:
    """ACES 1.3/2.0 color management utilities for Blender 5.0."""

    @staticmethod
    def setup_acescg() -> None:
        """Set ACEScg as working color space."""

    @staticmethod
    def configure_display(display: str = "sRGB",
                          view: str = "ACES 1.0 SDR-video") -> None:
        """Configure display and view transform."""

    @staticmethod
    def setup_rec2100() -> None:
        """Set up Rec.2100 PQ/HLG for HDR output."""

    @staticmethod
    def get_available_views() -> list[str]:
        """List available view transforms."""


class HDRVideoExport:
    """HDR video export utilities."""

    @staticmethod
    def configure_h264_hdr(transfer: str = "PQ") -> dict:
        """
        Configure H.264 with HDR metadata.

        Transfer options: PQ, HLG
        """

    @staticmethod
    def configure_prores_hdr(profile: str = "4444 XQ") -> dict:
        """Configure ProRes HDR export."""

    @staticmethod
    def set_hdr_metadata(max_cll: tuple[int, int] = None,
                         max_fall: int = None,
                         primaries: tuple = None) -> None:
        """Set HDR metadata for video export."""

    @staticmethod
    def export_hdr_frame(filepath: str,
                         format: str = "OPEN_EXR",
                         color_space: str = "Rec.2020") -> None:
        """Export HDR image with correct color space."""
```

#### 3.2 Volume Operations in GN (`geometry_nodes/volume_ops.py`)

```python
class VolumeGeometryNodes:
    """Volume data operations in Geometry Nodes (Blender 5.0)."""

    @staticmethod
    def smoke_to_points(volume: Volume,
                        density_threshold: float = 0.1) -> Points:
        """Convert smoke simulation to point cloud."""

    @staticmethod
    def fire_to_points(volume: Volume,
                       temperature_threshold: float = 500) -> Points:
        """Convert fire simulation to points."""

    @staticmethod
    def cloud_to_mesh(volume: Volume,
                      iso_level: float = 0.5) -> Mesh:
        """Convert cloud density to mesh."""

    @staticmethod
    def sample_volume(volume: Volume,
                      positions: list[Vector],
                      grid_name: str = "density") -> list[float]:
        """Sample volume values at positions."""

    @staticmethod
    def advect_points(points: Points,
                      velocity_grid: Volume,
                      dt: float = 0.1) -> Points:
        """Advect points through velocity field."""


class VolumeGrid:
    """Volume grid manipulation."""

    @staticmethod
    def get_grid(volume: Volume, name: str) -> Grid:
        """Get named grid from volume."""

    @staticmethod
    def create_density_grid(resolution: tuple[int, int, int],
                            name: str = "density") -> Volume:
        """Create empty density grid."""

    @staticmethod
    def set_background(grid: Grid, value: float) -> Grid:
        """Set grid background value."""
```

#### 3.3 SDF Modeling (`geometry_nodes/sdf_modeling.py`)

```python
class SDFModeling:
    """Signed Distance Field modeling utilities (Blender 5.0)."""

    @staticmethod
    def mesh_to_sdf(mesh: Mesh,
                    voxel_size: float = 0.01,
                    half_band: float = 3.0) -> Volume:
        """Convert mesh to SDF volume."""

    @staticmethod
    def sdf_to_mesh(sdf: Volume,
                    iso_level: float = 0.0,
                    adaptivity: float = 0.0) -> Mesh:
        """Convert SDF back to mesh."""

    @staticmethod
    def boolean_union(a: Volume, b: Volume) -> Volume:
        """SDF boolean union (smooth blending)."""

    @staticmethod
    def boolean_difference(a: Volume, b: Volume) -> Volume:
        """SDF boolean difference."""

    @staticmethod
    def boolean_intersection(a: Volume, b: Volume) -> Volume:
        """SDF boolean intersection."""

    @staticmethod
    def smooth_union(a: Volume, b: Volume,
                     smoothness: float = 0.1) -> Volume:
        """Smooth SDF blending."""

    @staticmethod
    def dilate(sdf: Volume, amount: float) -> Volume:
        """Dilate SDF (expand surface)."""

    @staticmethod
    def erode(sdf: Volume, amount: float) -> Volume:
        """Erode SDF (shrink surface)."""

    @staticmethod
    def blend_shapes(shapes: list[Volume],
                     weights: list[float],
                     smoothness: float = 0.1) -> Volume:
        """Blend multiple SDF shapes with weights."""
```

#### 3.4 Thin Film Iridescence (`rendering/thin_film.py`)

```python
class ThinFilmIridescence:
    """Thin film iridescence shader utilities (Blender 5.0)."""

    @staticmethod
    def create_soap_bubble() -> Material:
        """Create soap bubble iridescent material."""

    @staticmethod
    def create_oil_slick() -> Material:
        """Create oil slick iridescent material."""

    @staticmethod
    def create_oxidized_metal(base_color: tuple = (0.8, 0.5, 0.2)) -> Material:
        """Create oxidized metal with iridescence."""

    @staticmethod
    def configure_principled(material: Material,
                              thickness: float = 300,  # nm
                              ior: float = 1.5) -> None:
        """Configure thin film on Principled BSDF."""

    @staticmethod
    def configure_metallic(material: Material,
                            thickness: float = 400) -> None:
        """Configure thin film on Metallic BSDF."""

    @staticmethod
    def rainbow_coating(base_material: Material,
                        thickness_range: tuple = (200, 600)) -> Material:
        """Add rainbow coating effect."""
```

#### 3.5 New Modifiers (`modifiers/array_new.py`)

```python
class NewArrayModifier:
    """Blender 5.0 new array modifier utilities."""

    @staticmethod
    def create_linear(target: Object,
                      count: int = 5,
                      offset: Vector = (2, 0, 0),
                      relative: bool = True) -> Modifier:
        """Create linear array with gizmo controls."""

    @staticmethod
    def create_radial(target: Object,
                      count: int = 12,
                      axis: str = "Z",
                      center: Vector = (0, 0, 0)) -> Modifier:
        """Create radial array around center."""

    @staticmethod
    def create_curve_array(target: Object,
                           curve: Curve,
                           count: int = 10,
                           fit_type: str = "FIT_CURVE") -> Modifier:
        """Create array along curve."""

    @staticmethod
    def enable_gizmo(modifier: Modifier) -> None:
        """Enable in-viewport gizmo controls."""


class SurfaceDistribute:
    """Surface distribution modifier."""

    @staticmethod
    def distribute_collection(surface: Object,
                              collection: Collection,
                              density: float = 1.0,
                              seed: int = 0) -> Modifier:
        """Distribute collection objects on surface."""

    @staticmethod
    def with_vertex_group(surface: Object,
                          collection: Collection,
                          vertex_group: str,
                          base_density: float = 1.0) -> Modifier:
        """Distribute with density controlled by vertex group."""

    @staticmethod
    def aligned_to_normal(surface: Object,
                          collection: Collection,
                          density: float = 1.0) -> Modifier:
        """Distribute aligned to surface normals."""
```

#### 3.6 Compositor in VSE (`compositor/vse_integration.py`)

```python
class CompositorVSE:
    """Compositor integration with Video Sequence Editor (Blender 5.0)."""

    @staticmethod
    def add_compositor_modifier(strip: Sequence,
                                node_tree: NodeTree = None) -> Modifier:
        """Add compositor modifier to video strip."""

    @staticmethod
    def create_color_correction() -> NodeTree:
        """Create color correction node group."""

    @staticmethod
    def create_glow(intensity: float = 1.0) -> NodeTree:
        """Create glow effect preset."""

    @staticmethod
    def create_lens_effects() -> NodeTree:
        """Create lens distortion/chromatic aberration preset."""

    @staticmethod
    def apply_to_all_strips(node_tree: NodeTree) -> None:
        """Apply compositor to all strips."""

    @staticmethod
    def create_master_compositor() -> NodeTree:
        """Create master compositor for all strips."""


class AssetShelf:
    """Compositor asset shelf utilities."""

    @staticmethod
    def get_presets() -> list[str]:
        """List available preset effects."""

    @staticmethod
    def apply_preset(effect_name: str) -> NodeTree:
        """Apply preset from asset shelf."""

    PRESETS = [
        "chromatic_aberration",
        "split_toning",
        "glow",
        "depth_of_field",
        "vignette",
        "film_grain",
        "lens_distortion"
    ]
```

---

## Part 4: Geometry Nodes Extended (From CGMatter Tutorials)

Already covered in `.planning/TUTORIAL_UTILITIES_PLAN.md`:

- Curl Noise Particles
- Erosion Systems
- Fur/Hair Systems
- Handwriting System
- Building Folding Effect
- Infinite Background Studio
- Volumetric Rendering
- Volume Nodes

---

## Implementation Phases

### Phase 1: Core Infrastructure (3-4 days)
**Priority: Foundation for all modules**

1. Geometry Nodes node builder (`lib/geometry_nodes/node_builder.py`)
2. Instance control system (`lib/geometry_nodes/instances.py`)
3. Simulation zone helpers (`lib/geometry_nodes/simulation.py`)
4. Base module structure

**Deliverables:**
- NodeTreeBuilder class
- InstanceController class
- SimulationBuilder class

---

### Phase 2: Launch Control (4-5 days)
**Priority: High - Unique vehicle animation system**

| Day | Tasks |
|-----|-------|
| 1 | Auto-rig detection and generation |
| 2 | Suspension physics system |
| 3 | Steering with Ackermann geometry |
| 4 | Physics driving (drift, jump, offroad) |
| 5 | Ground detection, camera follow, presets |

**Deliverables:**
- LaunchControlRig class
- SuspensionSystem class
- SteeringSystem class
- VehiclePhysics class
- AnimationPresets class

---

### Phase 3: Sanctus Materials (3-4 days)
**Priority: High - Procedural material system**

| Day | Tasks |
|-----|-------|
| 1 | Shader tools API, damage generators |
| 2 | Weathering generators, pattern generators |
| 3 | Material presets, baking system |
| 4 | Geometry node generators integration |

**Deliverables:**
- SanctusShaderTools class
- DamageGenerator class
- WeatheringGenerator class
- SanctusMaterials class
- SanctusBaker class

---

### Phase 4: Blender 5.x Features (4-5 days)
**Priority: High - New Blender capabilities**

| Day | Tasks |
|-----|-------|
| 1 | ACES/HDR color management |
| 2 | Volume operations in GN, SDF modeling |
| 3 | Thin film iridescence, NanoVDB |
| 4 | New modifiers (Array, Distribute, Instance) |
| 5 | Compositor VSE integration |

**Deliverables:**
- ACESWorkflow class
- HDRVideoExport class
- VolumeGeometryNodes class
- SDFModeling class
- ThinFilmIridescence class
- CompositorVSE class

---

### Phase 5: Geometry Nodes Extended (2-3 days)
**Priority: Medium - From CGMatter tutorials**

Already planned in TUTORIAL_UTILITIES_PLAN.md:
- Curl noise particles
- Erosion systems
- Hair/fur systems
- Special effects

---

## Total Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1. Core Infrastructure | 3-4 days | None |
| 2. Launch Control | 4-5 days | Phase 1 |
| 3. Sanctus Materials | 3-4 days | Phase 1 |
| 4. Blender 5.x | 4-5 days | Phase 1 |
| 5. GN Extended | 2-3 days | Phase 1 |
| **Total** | **16-21 days** | |

---

## Tutorial Sources

### Launch Control (Auto Car Rig)
- **Plugin:** Launch Control v1.9.1
- **Course:** "汽车动画 - 基础必备" by Daniel Vesterbaek (~3.5 hours)
  - Vehicle/suspension types
  - Model preparation
  - Animation theory & keyframes
  - Speed segmentation & racing lines
  - Ground detection
  - Camera work & previz
- **Alternative plugins:** Rigicar v2.3.6, RBC Pro

### Sanctus Library
- **Plugin:** Sanctus Library v3.3.2
- **Features:** 1000+ procedural materials, 32+ Shader Tools
- **Categories:** Stone/brick, wood, fabric, metal, hair/fur
- **Tools:** Damage, weathering, pattern generators
- **Video tutorials:** Included with plugin downloads

### Blender 5.x
- **Official:** Blender 5.0 release notes (blender.org)
- **Bilibili:** "Blender 5.0 功能简介" (10 min)
- **Bilibili:** "Blender 5.0 改变游戏规则的十大功能"
- **Demo files:** blender.org/download/demo-files

### Geometry Nodes
- **13 CGMatter tutorials** (already ingested)
- **Erindale:** Geometry Nodes Toolkit
- **Ducky3D:** Particle tutorials
- **Blender Studio:** Official tutorials

---

## Success Criteria

1. **Reusability**: Each utility can be used independently
2. **Documentation**: All public APIs documented with docstrings
3. **Test Coverage**: 80%+ coverage for all modules
4. **Tutorial Fidelity**: Techniques match source tutorials
5. **Performance**: Vehicle physics handles real-time preview
6. **Integration**: Modules work together seamlessly

---

*Plan created February 2026*
*Sources: Launch Control v1.9.1, Sanctus Library v3.3.2, Blender 5.0, CGMatter*
