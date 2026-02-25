# Camera Control System Guide

Complete guide to camera control in Blender GSD - unified API, procedural animation, and advanced features.

---

## Quick Start

### Basic Camera Creation

```python
from lib.cinematic.camera_control import CameraController, create_camera

# Simple creation
ctrl = create_camera(
    name="hero_camera",
    position=(0, -10, 2),
    focal_length=85.0,
    f_stop=2.8,
    focus_distance=5.0,
)

# Chainable API
ctrl.set_lens(50).set_aperture(4.0).focus_at((0, 0, 1.5))
```

### Camera Types

```python
from lib.cinematic.camera_control import CameraController, create_ortho_camera, create_isometric_camera

# Perspective (default)
ctrl = CameraController.create("persp_cam", camera_type=CameraType.PERSPECTIVE)

# Orthographic
ctrl = create_ortho_camera("ortho_cam", position=(0, -10, 15), scale=12.0)

# Isometric (game style)
ctrl = create_isometric_camera("iso_cam", distance=15, target=(0, 0, 0))
```

---

## Lens Control

### Focal Length (Zoom)

```python
# Set focal length
ctrl.set_lens(85)  # 85mm portrait lens

# Get field of view
fov = ctrl.get_fov()  # Returns degrees

# Set by FOV
ctrl.set_fov(45)  # 45° horizontal FOV

# Animated zoom
ctrl.zoom_to(200, start_frame=1, end_frame=60)  # Zoom to 200mm

# Zoom by factor
ctrl.zoom_by_factor(2.0, 1, 60)  # 2x zoom in
```

### Aperture / Depth of Field

```python
# Set aperture
ctrl.set_aperture(2.8)  # f/2.8

# Focus at distance
ctrl.focus_at(5.0)  # 5 meters

# Focus on object
ctrl.focus_on_object("Character")

# Focus by position
ctrl.focus_at((0, 0, 1.5))  # World position

# Bokeh shape
ctrl.set_bokeh_shape("hexagonal")  # circular, hexagonal, octagonal, rounded
ctrl.set_aperture_blades(8)  # Direct blade count
```

### Lens Presets

```python
from lib.cinematic.camera import LENS_PRESETS, get_lens_preset_config

# Available presets
presets = list(LENS_PRESETS.keys())
# ['portrait_50mm', 'portrait_85mm', 'portrait_135mm', 'macro_60mm',
#  'macro_100mm', 'product_45mm', 'product_90mm', 'wide_24mm',
#  'wide_35mm', 'telephoto_200mm', 'zoom_24_70mm', 'zoom_70_200mm']

# Get preset config
preset = get_lens_preset_config("portrait_85mm")
# LensPreset(focal_length=85.0, lens_type="prime", max_aperture=1.4, ...)
```

---

## Focus Pull / Rack Focus

```python
# Focus pull animation
ctrl.focus_pull(
    target_distance=10.0,  # Pull focus to 10 meters
    start_frame=1,
    end_frame=60,
    easing="EASE_IN_OUT",  # LINEAR, EASE_IN, EASE_OUT, EASE_IN_OUT
)

# Pull to object
ctrl.focus_pull_to_object("BackgroundObject", 1, 60)
```

---

## Camera Rigs

### Rig Types

```python
from lib.cinematic.camera_control import RigType

ctrl.set_rig(RigType.TRIPOD)        # Fixed position, rotation only
ctrl.set_rig(RigType.DOLLY)         # X-axis movement
ctrl.set_rig(RigType.CRANE)         # Rotation limits
ctrl.set_rig(RigType.STEADICAM)     # Smooth following
ctrl.set_rig(RigType.DRONE)         # Floating feel
ctrl.set_rig(RigType.FREE)          # No constraints
```

### Look At / Tracking

```python
# Track to object
ctrl.look_at("TargetObject")

# Track to position
ctrl.look_at((0, 5, 2))
```

---

## Camera Shake

### Preset Shake

```python
from lib.cinematic.camera_control import ShakeProfile

# Preset profiles
ctrl.add_shake_profile(ShakeProfile.SUBTLE)       # Very light
ctrl.add_shake_profile(ShakeProfile.HANDHELD)     # Natural handheld
ctrl.add_shake_profile(ShakeProfile.RUN_AND_GUN)  # Active shooting
ctrl.add_shake_profile(ShakeProfile.VEHICLE)      # Car/motion
ctrl.add_shake_profile(ShakeProfile.EARTHQUAKE)   # Heavy shake
ctrl.add_shake_profile(ShakeProfile.EXPLOSION)    # Shockwave

# Handheld shortcut
ctrl.add_handheld(amount=0.5)  # 0-1 intensity multiplier

# Clear shake
ctrl.clear_shake()
```

### Custom Shake

```python
ctrl.add_shake(
    intensity=0.05,      # Meters
    frequency=3.0,       # Hz
    rotation_intensity=1.0,  # Degrees
    seed=42,             # For reproducibility
)
```

---

## Path Following

### Follow Curve

```python
ctrl.follow_path(
    curve_name="camera_path",
    duration_frames=120,
    follow_curve=True,   # Rotate along path
    start_frame=1,
)
```

### Orbit Animation

```python
ctrl.orbit_around(
    center=(0, 0, 1),    # Center point
    radius=8.0,          # Meters
    start_angle=0,       # Degrees
    end_angle=360,       # Full circle
    height=2.0,          # Above center
    duration_frames=120,
    start_frame=1,
)
```

---

## Dolly Zoom (Vertigo Effect)

```python
from lib.cinematic.camera_control import create_dolly_zoom

# Create dolly zoom
ctrl = create_dolly_zoom(
    camera_name="vertigo_cam",
    start_distance=5.0,
    end_distance=15.0,
    start_fov=45.0,  # Degrees
    end_fov=15.0,
    frames=120,
)
```

---

## State Management

```python
# Save state
state = ctrl.get_state()

# ... make changes ...

# Restore state
ctrl.restore_state(state)
```

---

## Geometry Nodes Camera Control

For procedural, real-time camera animation without keyframes:

```python
from lib.cinematic.gn_camera_control import GNCameraController, create_shake_camera

# Create GN-controlled camera
gn_cam = GNCameraController("procedural_camera")

# Add shake layers (stackable)
gn_cam.add_shake_layer("subtle", intensity=0.02, frequency=2.0)
gn_cam.add_handheld(0.5)
gn_cam.add_vehicle_shake(1.0)

# Follow target with offset
gn_cam.follow_target(
    target_name="Vehicle",
    offset=(-8, 2, 3),
)

# Add orbital motion
gn_cam.add_orbit(radius=12.0, speed=0.25, height=2.0)

# Apply to camera
gn_cam.apply()

# Get spec for documentation
spec = gn_cam.create_spec()
```

### GN Preset Setups

```python
from lib.cinematic.gn_camera_control import (
    create_shake_camera,
    create_follow_orbit_camera,
)

# Shake camera
gn_cam = create_shake_camera("action_cam", shake_profile="vehicle", intensity=1.5)

# Follow + orbit
gn_cam = create_follow_orbit_camera(
    camera_name="orbit_cam",
    target_name="Subject",
    radius=10.0,
    orbit_speed=0.25,
    height=2.0,
)
```

---

## Multi-Camera Control

```python
from lib.cinematic.camera_control import MultiCameraController

# Control multiple cameras
multi = MultiCameraController(["cam1", "cam2", "cam3"])

# Apply to all
multi.set_lens(50).set_aperture(2.8)
multi.add_shake_all(0.02, 2.0)

# Switch active camera
multi.cut_to("cam2")

# Access individual
multi["cam1"].focus_at(5.0)
```

---

## Complete Example

```python
from lib.cinematic.camera_control import (
    CameraController,
    RigType,
    ShakeProfile,
)

# Create camera
ctrl = CameraController.create(
    name="cinematic_camera",
    position=(0, -8, 2),
    focal_length=50.0,
)

# Setup lens
ctrl.set_aperture(2.8).enable_dof()
ctrl.focus_on_object("Actor")
ctrl.set_bokeh_shape("rounded")

# Setup rig
ctrl.set_rig(RigType.STEADICAM, target_name="Actor")

# Add movement
ctrl.orbit_around(
    center=(0, 0, 1),
    radius=6.0,
    start_angle=-30,
    end_angle=30,
    duration_frames=120,
)

# Add subtle handheld feel
ctrl.add_handheld(0.3)

# Focus pull during shot
ctrl.focus_pull(8.0, start_frame=60, end_frame=120)

# Set as active
ctrl.set_active()
```

---

## Reference

### CameraController Methods

| Method | Purpose |
|--------|---------|
| `set_lens(mm)` | Set focal length |
| `set_aperture(f_stop)` | Set aperture |
| `set_fov(degrees)` | Set by field of view |
| `focus_at(target)` | Set focus distance |
| `focus_on_object(name)` | Focus track object |
| `set_bokeh_shape(shape)` | Set bokeh (circular/hex/etc) |
| `enable_dof(bool)` | Enable DoF |
| `set_perspective()` | Perspective projection |
| `set_ortho(scale)` | Ortho projection |
| `zoom_to(mm, start, end)` | Animated zoom |
| `focus_pull(dist, start, end)` | Rack focus |
| `add_shake(intensity, freq)` | Camera shake |
| `add_handheld(amount)` | Handheld preset |
| `follow_path(curve, duration)` | Path following |
| `orbit_around(center, radius)` | Orbit animation |
| `set_rig(type, target)` | Setup rig |
| `look_at(target)` | Track to target |
| `get_state()` | Capture state |
| `restore_state(state)` | Restore state |

### Shake Profiles

| Profile | Intensity | Use Case |
|---------|-----------|----------|
| SUBTLE | 0.005m | Light natural movement |
| HANDHELD | 0.02m | Shoulder-mounted camera |
| RUN_AND_GUN | 0.05m | Active/documentary |
| VEHICLE | 0.03m | Car/mounted camera |
| EARTHQUAKE | 0.15m | Heavy impact |
| EXPLOSION | 0.2m | Shockwave effect |

### Rig Types

| Type | Movement | Use Case |
|------|----------|----------|
| FREE | Full | No constraints |
| TRIPOD | Rotation only | Static shots |
| DOLLY | X + rotation | Tracking shots |
| CRANE | Limited rotation | Jib shots |
| STEADICAM | Smooth follow | Walking shots |
| DRONE | Floating | Aerial shots |

---

## Related Files

- `lib/cinematic/camera_control.py` - Unified controller
- `lib/cinematic/gn_camera_control.py` - GN procedural control
- `lib/cinematic/camera.py` - Core camera functions
- `lib/cinematic/rigs.py` - Rig systems
- `lib/cinematic/motion_path.py` - Path generation
- `lib/cinematic/follow_cam/` - Dynamic following

---

*Camera Control Guide - February 2026*
