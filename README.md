# Blender GSD Framework

**A deterministic, code-first framework for building Blender node workflows, cinematic systems, and procedural pipelines.**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Blender 5.x](https://img.shields.io/badge/Blender-5.x-blue.svg)](https://www.blender.org/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://www.python.org/)

**Repository:** https://github.com/bretbouchard/blender_gsd

---

## Philosophy

> **Blender never stores intent. Blender only executes intent.**
>
> Intent lives in GSD. Logic lives in scripts. Structure lives in nodes.
> Files are disposable. Everything is reproducible.

---

## Core Capabilities

### Node Workflow System

Build complex Geometry Nodes and shader graphs programmatically:

```python
from lib.nodekit import NodeGraph, InputSocket

# Create node groups from code
graph = NodeGraph("MyGeometry")
graph.add_node("MeshPrimitiveCube", size=(1, 1, 1))
graph.add_node("SetMaterial", material="debug_material")
graph.output(geometry="mesh")
```

**Features:**
- Programmatic node group construction
- Socket routing and type validation
- Reusable node templates
- Debug material integration

### Mask Infrastructure

First-class mask system for controlling where effects apply:

```python
from lib.masks import Mask, MaskCombiner

# Create zone-based masks
height_mask = Mask.from_height(min=0.2, max=0.8)
angle_mask = Mask.from_angle(axis='Z', start=0, end=90)

# Combine with boolean operations
combined = MaskCombiner(height_mask).AND(angle_mask)
```

**Mask Types:**
- Height, angle, and radial masks
- UV-based selection masks
- Boolean combinations (AND, OR, XOR, NOT)
- Smooth falloff controls

### Universal Stage Pipeline

Every artifact flows through 5 deterministic stages:

| Stage | Purpose |
|-------|---------|
| **Normalize** | Parameter canonicalization and validation |
| **Primary** | Base geometry or material generation |
| **Secondary** | Modifications, cutouts, secondary elements |
| **Detail** | Surface effects controlled by masks |
| **OutputPrep** | Attributes, cleanup, export preparation |

---

## Cinematic System

A complete cinematic rendering pipeline with camera, lighting, and animation systems.

### Camera System

```python
from lib.cinematic import CameraConfig, PlumbBobConfig, RigConfig

camera = CameraConfig(
    name="hero_camera",
    focal_length=50.0,
    f_stop=2.8,
    focus_distance=3.0,
    transform=Transform3D(position=(0, -5, 2)),
)

# Plumb bob targeting (auto, manual, object modes)
plumb_bob = PlumbBobConfig(
    mode="object",
    target_object="Product",
)

# Camera rigs (tripod, dolly, crane, steadicam, drone)
rig = RigConfig(rig_type="dolly_curved", path_points=[...])
```

**Camera Features:**
- Sensor presets (Full Frame, Super 35, Micro 4/3, iPhone)
- Lens presets (24mm wide to 135mm telephoto)
- DoF configuration with plumb bob targeting
- Lens imperfections (vignette, chromatic aberration, flare)

### Lighting System

```python
from lib.cinematic import LightConfig, LightRigConfig, HDRIConfig

# Individual lights
key_light = LightConfig(
    name="key",
    light_type="area",
    intensity=1000.0,
    color=(1.0, 0.95, 0.9),  # Slightly warm
)

# Light rigs with presets
rig = LightRigConfig.from_preset("three_point")

# HDRI environments
hdri = HDRIConfig(
    filepath="//assets/hdri/studio.hdr",
    rotation=45.0,
    strength=1.0,
)
```

**Lighting Features:**
- Area, spot, point, and sun lights
- Gel system for colored lighting
- Light linking for selective illumination
- 8+ preset lighting rigs

### Animation System

```python
from lib.cinematic import AnimationConfig, MotionPathConfig

# Orbit animation
orbit = AnimationConfig(
    enabled=True,
    type="orbit",
    angle_range=(0, 360),
    radius=3.0,
    frame_range=(1, 120),
)

# Bezier motion paths
path = MotionPathConfig(
    points=[(0,0,0), (2,1,0), (4,0,0)],
    easing="ease_in_out",
)
```

**Animation Types:**
- Orbit, dolly, crane, pan, tilt
- Rack focus animations
- Turntable rotation
- Custom Bezier motion paths

### Render System

```python
from lib.cinematic import CinematicRenderSettings

settings = CinematicRenderSettings(
    quality_tier="production",  # preview, standard, production
    engine="BLENDER_EEVEE_NEXT",
    resolution_x=3840,
    resolution_y=2160,
    samples=256,
    use_pass_cryptomatte=True,
)
```

---

## Motion Tracking System

Full motion tracking pipeline with camera solving and compositing integration.

```python
from lib.cinematic.tracking import (
    TrackingSession,
    PointTracker,
    CameraSolver,
    Stabilization,
)

# Track features in footage
tracker = PointTracker()
tracks = tracker.detect_features(method="KLT", count=100)

# Solve camera motion
solver = CameraSolver()
solve = solver.solve(tracks, refine_focal_length=True)

# Apply stabilization
stabilize = Stabilization(smoothing=0.5)
stabilized = stabilize.apply(solve.camera_animation)
```

**Tracking Features:**
- Feature detection (FAST, Harris, KLT optical flow)
- Camera solving with libmv integration
- Device camera profiles (iPhone, RED, ARRI, Blackmagic)
- External format import (FBX, Alembic, BVH, Nuke .chan)
- ST-Map generation for lens distortion
- 2D video stabilization

---

## Follow Camera System

Intelligent camera following with obstacle avoidance and path prediction.

```python
from lib.cinematic.follow_cam import (
    FollowCameraConfig,
    FollowMode,
    CollisionDetector,
    MotionPredictor,
)

# Configure follow camera
config = FollowCameraConfig(
    mode=FollowMode.OVER_SHOULDER,
    target_object="Character",
    distance=3.0,
    height=1.6,
)

# Collision detection and avoidance
detector = CollisionDetector(
    method="spherecast",
    collision_layers=["geometry"],
    ignore_objects=["trigger_volumes"],
)

# Motion prediction for smooth following
predictor = MotionPredictor(
    look_ahead_frames=10,
    velocity_smoothing=0.3,
)
```

**Follow Modes:**
- Side-scroller (2.5D platformer)
- Over-shoulder (third-person)
- Chase (vehicle following)
- Orbit-follow, Lead, Aerial, Free roam

**Intelligent Behaviors:**
- Obstacle detection and avoidance
- Motion prediction and anticipation
- Pre-solve for deterministic rendering
- Navigation mesh with A* pathfinding
- Rule-of-thirds framing

---

## Anamorphic Projection System

Create forced perspective art that only appears correct from specific viewpoints.

```python
from lib.cinematic.projection import (
    FrustumConfig,
    project_from_camera,
    generate_uvs_from_projection,
    bake_projection_texture,
    create_sweet_spot,
    VisibilityController,
)

# Project image from camera viewpoint
config = FrustumConfig(resolution_x=1920, resolution_y=1080, fov=50.0)
result = project_from_camera("Camera", config, "artwork.png")

# Generate UVs for projection
uvs = generate_uvs_from_projection(result)

# Bake to texture
bake = bake_projection_texture(config, output_path="baked.png")

# Define sweet spot zone
zone = create_sweet_spot(
    camera_position=(0, 5, 1.6),
    radius=0.5,
    target_objects=["FloorArt"],
)

# Control visibility based on camera position
controller = VisibilityController()
controller.add_zone(zone)
visibility = controller.update(camera_position=(0, 5, 1.6))
```

**Projection Features:**
- Camera frustum raycasting
- Surface detection and classification (floor, wall, ceiling)
- UV generation from projection rays
- Texture baking (diffuse, emission, decal modes)
- Sweet spot zones for visibility
- Multi-surface corner projections

---

## Control Surface System

Generate procedural control surfaces (knobs, faders, buttons, LEDs).

```python
from lib.control_system import (
    ParameterHierarchy,
    KnobProfile,
    SurfaceFeatures,
    MorphingEngine,
)

# Define parameters with inheritance
params = ParameterHierarchy()
params.set_global("knob_diameter", 0.025)
params.set_category("knob", "profile", "chicken_head")
params.set_variant("neve_1073", "color", "#2D4A6B")

# Generate knob with features
knob = KnobProfile.from_preset("neve_1073")
knob.add_feature(SurfaceFeatures.KNURLING(pattern="diamond", density=24))

# Morph between styles
morph = MorphingEngine()
morph.animate(from_preset="neve_1073", to_preset="ssl_4000", frames=60)
```

**Control Elements:**
- 10+ knob profiles (chicken head, cylindrical, domed, collet, etc.)
- Surface features (knurling, ribbing, grooves, indicators)
- Faders (channel, short, mini with LED meters)
- Buttons (momentary, latching, illuminated, toggle)
- LEDs (single, bar, VU meter)

---

## Input System

Build custom input zone geometry with debug visualization.

```python
from lib.inputs import InputZoneBuilder, InputPreset

# Build input zone
zone = InputZoneBuilder("MyZone")
zone.add_section("A_Top", shape="cone", height=0.5)
zone.add_section("A_Mid", shape="cylinder", height=0.3)
zone.set_debug_mode(True)  # Per-section color visualization

# Apply preset
preset = InputPreset.from_yaml("presets/knob_neve_1073.yaml")
zone.apply_preset(preset)
```

---

## CLI & Project Tools

Create and manage Blender GSD projects from the command line:

```bash
# Create a new project
python -m lib.cli init my-project

# Create with a specific template
python -m lib.cli init my-film --template cinematic

# List available templates
python -m lib.cli templates list

# Validate a project
python -m lib.cli validate .

# Start debug dashboard
python -m lib.cli dashboard
```

**Project Templates:**
| Template | Description |
|----------|-------------|
| default | Standard project with tasks, scripts, planning |
| control-surface | Audio control surface design |
| cinematic | Cinematic rendering with camera/lighting |
| production | Full production with characters/locations |
| charlotte | Charlotte digital twin geometry |
| minimal | Bare-bones project |

**VS Code Integration:**
- Auto-generated `settings.json` with Python/YAML configuration
- Recommended extensions (Python, Pylance, YAML, TOML)
- Debug configurations for running tasks

---

## Testing & Validation

Oracle-based testing framework for deterministic validation:

```python
from lib.oracle import compare_numbers, compare_vectors, file_exists

def test_camera_focal_length():
    camera = CameraConfig(focal_length=50.0)
    compare_numbers(camera.focal_length, 50.0, tolerance=0.001)

def test_output_exists():
    assert file_exists("build/output.glb")
```

**Test Coverage:**
- 4,610+ unit tests
- Integration tests for pipelines
- Oracle comparison functions
- Works outside Blender (fallback implementations)

---

## Directory Structure

```
blender_gsd/
├── lib/                        # Core libraries
│   ├── pipeline.py             # Stage-based execution
│   ├── nodekit.py              # Node group construction
│   ├── masks.py                # Mask infrastructure
│   ├── oracle.py               # Testing utilities
│   ├── cinematic/              # Cinematic system
│   │   ├── camera.py           # Camera creation/DoF
│   │   ├── lighting.py         # Light management
│   │   ├── animation.py        # Animation system
│   │   ├── render.py           # Render pipeline
│   │   ├── tracking/           # Motion tracking
│   │   ├── follow_cam/         # Follow camera
│   │   └── projection/         # Anamorphic projection
│   ├── control_system/         # Control surfaces
│   └── inputs/                 # Input zone builder
├── configs/                    # YAML configurations
│   └── cinematic/              # Camera, lighting presets
├── tests/                      # Test suite
│   └── unit/                   # Unit tests
├── .planning/                  # GSD planning documents
└── .claude/                    # Claude configuration
```

---

## Specialist Agents

The Council of Ricks - domain-specific AI agents:

| Agent | Specialty |
|-------|-----------|
| geometry-rick | Geometry Nodes systems |
| shader-rick | Material/shader pipelines |
| compositor-rick | Compositor graphs |
| render-rick | Render pipeline configuration |
| pipeline-rick | GSD pipeline orchestration |

---

## Requirements

- Blender 5.x (Geometry Nodes + EEVEE Next)
- Python 3.11+
- PyYAML

---

## Project Status

### Codebase Statistics

| Metric | Count |
|--------|-------|
| Python Modules | 270+ |
| Test Files | 95+ |
| Lines of Code | 150,000+ |
| Tests | 4,700+ |
| Versioned Packages | 14 |
| Completed Phases | 51+ |

### Completed Milestones

| Milestone | Version | Status | Phases |
|-----------|---------|--------|--------|
| Core Infrastructure | v0.1 | Complete | 6.0 |
| Cinematic Rendering System | v0.3 | Complete | 6.1-6.10 |
| Motion Tracking System | v0.4 | Complete | 7.0-7.5 |
| Follow Camera System | v0.5 | Complete | 8.0-8.4 |
| Art & Locations | v0.6 | Complete | 9.1 |
| Character System | v0.7 | Complete | 10.1 |
| Audio & Editorial | v0.8 | Complete | 11.0-11.1 |
| VFX & Compositing | v0.9 | Complete | 12.0-12.1 |
| Retro Graphics | v0.10 | Complete | 13.0-13.7 |
| Production Tools | v0.11 | Complete | 14.1-14.2 |
| Control Surface System | v0.12 | Complete | 5.0-5.9 |

### Phase Categories (All Complete)

| Category | Phases | Features |
|----------|--------|----------|
| **Core Cinematic (6.x)** | 10 phases | Camera, lens, lighting, render, animation |
| **Motion & Tracking (7.x)** | 6 phases | Tracking, footage profiles, import/export, compositing |
| **Follow Camera (8.x)** | 5 phases | Follow modes, obstacle avoidance, script parser |
| **Art & Locations (9.x)** | 1 phase | Set builder with 12 style presets |
| **Character (10.x)** | 1 phase | Wardrobe system with continuity validation |
| **Sound & Editorial (11.x)** | 2 phases | Production tracking, timeline system |
| **VFX & Compositing (12.x)** | 2 phases | One-sheet generator, compositor |
| **Retro Graphics (13.x)** | 12 phases | Rigging, IK/FK, pixel art, dithering, CRT effects |
| **Production (14.x)** | 2 phases | Production orchestrator, master config |
| **Control Surfaces (5.x)** | 10 phases | Knobs, faders, buttons, LEDs, morphing |
| **Tentacle System (19.x)** | 5 phases | Procedural tentacles, suckers, animation, materials, export |
| **Quetzalcoatl (20.x)** | 12 phases | Feathered serpent generator with scales, wings, rigging |

### Latest Additions

| System | Version | Tests | Description |
|--------|---------|-------|-------------|
| **Tentacle System** | v1.0.0 | 266 | Procedural tentacle generation for horror characters with zombie mouth support |
| **Quetzalcoatl** | v1.0.0 | 446 | Feathered serpent creature generator with full procedural pipeline |

### CI/CD

- **Regression Guard**: Automated test collection and execution on push/PR
- **Coverage Reports**: Codecov integration for coverage tracking
- **SLC Validation**: Lint checks for TODO/FIXME and NotImplementedError

---

## License

MIT
