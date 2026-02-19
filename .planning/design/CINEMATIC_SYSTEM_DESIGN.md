# Cinematic Rendering System - Complete Design

**Version**: 1.2
**Status**: Council-Approved
**Related**: REQ-CINE-* series, REQUIREMENTS_CINEMATIC.md
**Updated**: 2026-02-18 (Council of Ricks Review Fixes)

---

## Executive Summary

This document defines a complete cinematic rendering system for Blender GSD. The system enables:

1. **Camera systems** with real-world lenses, movements, and cinematic control
2. **Lighting rigs** that are modular, preset-driven, and resumable
3. **Backdrops/environments** for product and cinematic shots
4. **Color pipeline** with LUTs and color management
5. **Animation systems** for camera moves and turntables
6. **Shot presets** combining all elements into single "drop-in" configurations

**Core Philosophy** (aligned with GSD):
- Blender executes intent, never stores it
- All cinematic state lives in YAML configs
- Everything is resumable and editable
- Drop-in means: one YAML → complete shot setup

---

## Part 1: Things You Didn't Know to Ask For

### 1.1 PLUMB BOB SYSTEM (REQ-CINE-PLUMB)

**Problem**: When you orbit a camera around an object, where is the pivot point? Usually it's (0,0,0) but that's wrong for most shots.

**Solution**: A "plumb bob" defines the visual center of interest - the point the camera orbits around, and the point that focus pulls toward.

```
┌─────────────────────────────────────────────────────────┐
│                    Camera Orbit                         │
│                                                         │
│         ╭──────────────────────────────╮               │
│         │                              │               │
│         │      ┌─────────────┐         │               │
│         │      │   OBJECT    │         │               │
│         │      │      ⊕      │ ← Plumb │ Bob           │
│         │      │  (focus     │   Point │               │
│         │      │   target)   │         │               │
│         │      └─────────────┘         │               │
│         │                              │               │
│         ╰──────────────────────────────╯               │
│                      ▲                                  │
│                      │                                  │
│                   Camera                                │
└─────────────────────────────────────────────────────────┘
```

**Plumb Bob Parameters**:
```yaml
plumb_bob:
  mode: auto              # auto, manual, object
  offset: [0, 0, 0.02]    # Offset from object center (meters)
  object: null            # Optional: name of target object
  focus_distance: auto    # auto or explicit distance
```

**Why This Matters**:
- Orbit shots feel wrong without proper pivot
- Rack focus needs a target
- Dolly moves need a destination

---

### 1.2 SHUFFLER SYSTEM (REQ-CINE-SHUFFLE)

**Problem**: You have 50 knob renders to do. You want variety but consistent quality. How do you manage shot variation without manually configuring each?

**Solution**: A "Shuffler" generates shot variations from parameter ranges.

```yaml
shuffler:
  mode: random            # random, grid, custom
  seed: 42                # Reproducible randomness

  # Camera parameters to shuffle
  camera:
    angle:
      range: [-30, 30]    # Degrees around object
      samples: 5          # Number of variations
    elevation:
      range: [10, 45]     # Degrees above horizon
      samples: 3
    distance:
      range: [0.3, 0.8]   # Meters from plumb bob
      samples: 2

  # Lighting to shuffle
  lighting:
    key_angle:
      range: [-60, 60]
      samples: 3

  # Output: 5 × 3 × 2 × 3 = 90 shot variations
```

**Shuffler Output**:
```
shots/
├── shot_001_angle-15_elev-25_dist-0.4_key-30/
├── shot_002_angle-15_elev-25_dist-0.4_key--15/
├── shot_003_angle-15_elev-25_dist-0.6_key-30/
└── ... (90 total variations)
```

---

### 1.3 FRAME STORE SYSTEM (REQ-CINE-FRAME)

**Problem**: You're iterating on a shot. You try 20 lighting variations. How do you compare them? How do you go back to the one that worked?

**Solution**: A "Frame Store" captures complete shot state for A/B comparison.

```yaml
frame_store:
  enabled: true
  capture_on_render: true
  max_versions: 50        # Oldest auto-deleted

  # What to capture
  capture:
    camera_transform: true
    camera_settings: true
    light_transforms: true
    light_settings: true
    backdrop_state: true
    render_settings: true
    thumbnail: true       # Low-res preview
```

**Frame Store Structure**:
```
.gsd-state/frames/
├── shot_hero_001/
│   ├── state.yaml        # Complete shot state
│   ├── thumbnail.png     # Quick preview
│   └── render.png        # Actual render
├── shot_hero_002/
│   └── ...
└── frame_index.yaml      # Searchable index
```

**Frame Store Commands**:
```yaml
commands:
  frame_save: "Save current state as new frame"
  frame_load: "Load frame N"
  frame_compare: "Side-by-side N and M"
  frame_diff: "Show parameter differences"
  frame_revert: "Return to frame N"
```

---

### 1.4 DEPTH LAYER SYSTEM (REQ-CINE-DEPTH)

**Problem**: Cinematic shots need depth. Objects in foreground, midground, background. But you don't want to manually place things.

**Solution**: Automatic depth layering with parallax-aware camera moves.

```yaml
depth_layers:
  foreground:
    distance: 0.1-0.3     # Meters from camera
    blur: f/2.8           # Simulated DoF
    objects: auto         # Auto-assign by bounding box

  midground:
    distance: 0.3-0.8
    blur: f/8
    objects: [subject]    # Main subject here

  background:
    distance: 0.8-5.0
    blur: f/16
    objects: [backdrop]
```

**Parallax Animation**:
```yaml
animation:
  type: parallax_dolly
  distance: 0.5           # Total camera movement
  layers_respond:
    foreground: 1.0       # Full movement
    midground: 0.3        # Reduced
    background: 0.05      # Almost static
```

---

### 1.5 COMPOSITION GUIDES (REQ-CINE-COMPOSE)

**Problem**: How do you know a shot is well-composed without visual guides?

**Solution**: In-viewport composition overlays (render-safe, not in output).

```yaml
composition_guides:
  enabled: true

  guides:
    rule_of_thirds: true
    golden_ratio: true
    center_cross: true
    safe_areas: true      # Title/action safe
    diagonals: false

  # Custom guides
  custom:
    - type: circle
      center: [0.5, 0.5]
      radius: 0.3
    - type: line
      start: [0, 0.382]
      end: [1, 0.382]

  # Visual style
  color: [1, 0, 0]
  opacity: 0.5
  render_visible: false   # Never in output
```

---

### 1.6 MOTION PATH SYSTEM (REQ-CINE-PATH)

**Problem**: Camera moves along curves. But Blender's curve system is manual and not GSD-compatible.

**Solution**: Procedural motion path generation with easing.

```yaml
motion_path:
  type: spline            # spline, linear, bezier

  # Control points (auto-generated if not specified)
  points:
    - position: [0.5, -0.5, 0.3]
      rotation: [80, 0, 45]
      ease: ease_in
    - position: [0.3, -0.3, 0.2]
      rotation: [85, 0, 30]
      ease: linear
    - position: [0.5, -0.5, 0.3]
      rotation: [80, 0, 0]
      ease: ease_out

  # Path parameters
  duration: 120           # Frames
  interpolation: cubic
  look_at: plumb_bob      # Always face subject

  # Path presets
  preset: orbit_90        # orbit_90, orbit_180, dolly_in, crane_up
```

---

### 1.7 EXPOSURE/TONEMAP LOCK (REQ-CINE-EXPOSURE)

**Problem**: You change lighting, exposure shifts. You move camera, exposure shifts. Shots don't match.

**Solution**: Exposure lock maintains consistent brightness across variations.

```yaml
exposure_lock:
  enabled: true
  mode: luminance_target  # luminance_target, manual, auto_key

  target:
    mid_gray: 0.18        # 18% gray target
    highlight_max: 0.95   # Don't clip highlights
    shadow_min: 0.02      # Minimum shadow detail

  # Auto-adjust lighting
  auto_adjust:
    key_light: true       # Adjust key to hit target
    exposure_comp: true   # Adjust scene exposure
```

---

### 1.8 LENS FLARE/GIMP SYSTEM (REQ-CINE-GIMP)

**Problem**: Real lenses have character - flare, ghosting, bloom. Clean CGI looks fake.

**Solution**: Procedural lens imperfection system.

```yaml
lens_imperfections:
  flare:
    enabled: true
    intensity: 0.3
    streaks: 6
    streak_angle: 15

  ghosting:
    enabled: true
    count: 4
    falloff: 0.7

  bloom:
    enabled: true
    threshold: 0.8
    intensity: 0.2
    radius: 0.1

  chromatic_aberration:
    enabled: true
    strength: 0.002
    radial: true

  vignette:
    enabled: true
    intensity: 0.3
    radius: 0.8

  # Lens-specific presets
  preset: cooke_s4        # cooke_s4, arri_master, vintage_helios, clean
```

---

### 1.9 SHOT TEMPLATE INHERITANCE (REQ-CINE-TEMPLATE)

**Problem**: You have a "product hero" shot. You want variations (different angles, different lighting moods) without duplicating config.

**Solution**: Template inheritance for shots.

```yaml
# base_hero_shot.yaml
name: base_hero_shot
abstract: true            # Can't render directly

camera:
  lens: 85mm
  sensor: full_frame
  aperture: f/4

lighting:
  rig: three_point_soft

backdrop:
  type: infinite_curve
  color: white

---

# hero_dramatic.yaml
extends: base_hero_shot

lighting:
  key_light:
    intensity: 1.5        # 50% brighter
    angle: 45             # More dramatic

backdrop:
  color: dark_gray

---

# hero_warm.yaml
extends: base_hero_shot

lighting:
  key_light:
    color: warm_3200k

color:
  lut: kodak_2383
```

---

### 1.10 RENDER FARM AWARENESS (REQ-CINE-FARM)

**Problem**: You're rendering 100 shots. Some machines are faster. How do you distribute work?

**Solution**: Built-in render farm chunking.

```yaml
render_farm:
  enabled: false          # Enable for distributed rendering

  chunking:
    mode: shot            # shot, frame, tile
    chunk_size: 10        # Shots per chunk

  # Output structure for farm
  output:
    path_template: "{project}/renders/{shot}/{frame:04d}.png"
    manifest: render_manifest.json

  # Resume capability
  resume:
    skip_existing: true
    verify_checksums: true
```

---

## Part 2: Core System Architecture

### 2.1 Module Structure

```
lib/
├── cinematic/
│   ├── __init__.py
│   │
│   ├── # Core Systems
│   ├── camera.py           # Camera rigs, lenses, transforms
│   ├── lenses.py           # Lens presets, DoF, imperfections
│   ├── lighting.py         # Light rigs, gels, HDRI
│   ├── backdrops.py        # Environments, curves, gradients
│   ├── color.py            # LUTs, color management
│   ├── animation.py        # Camera moves, keyframes
│   ├── render.py           # Render profiles, passes
│   │
│   ├── # Support Systems
│   ├── plumb_bob.py        # Focus/orbit target system
│   ├── shuffler.py         # Shot variation generator
│   ├── frame_store.py      # State capture/comparison
│   ├── depth_layers.py     # Fore/mid/background
│   ├── composition.py      # Guides and overlays
│   ├── motion_path.py      # Camera path generation
│   ├── exposure.py         # Exposure lock/management
│   ├── lens_fx.py          # Flare, bloom, aberration
│   ├── isometric.py        # Orthographic/isometric views
│   │
│   ├── # Catalog System
│   ├── catalog.py          # Asset catalog generator
│   ├── catalog_unit.py     # Test unit builder
│   ├── catalog_layouts.py  # Strip, grid, comparison layouts
│   ├── catalog_export.py   # GLTF/GLB export for 3D viewers
│   │
│   └── # Orchestration
│   ├── shot.py             # Complete shot assembly
│   └── template.py         # Template inheritance
```

### 2.2 Configuration Structure

```
configs/
├── cinematic/
│   ├── cameras/
│   │   ├── lens_presets.yaml        # 35mm, 50mm, 85mm, etc.
│   │   ├── sensor_presets.yaml      # Full frame, APS-C, etc.
│   │   ├── rig_presets.yaml         # tripod, dolly, crane, etc.
│   │   └── imperfection_presets.yaml # Cooke, ARRI, vintage
│   │
│   ├── lighting/
│   │   ├── rig_presets.yaml         # three_point, studio_hero, etc.
│   │   ├── gel_presets.yaml         # CTB, CTO, creative
│   │   └── hdri_presets.yaml        # Environment maps
│   │
│   ├── backdrops/
│   │   ├── infinite_curves.yaml     # Product backdrops
│   │   ├── gradients.yaml           # Gradient backgrounds
│   │   └── environments.yaml        # Pre-built scenes
│   │
│   ├── color/
│   │   ├── technical_luts.yaml      # Rec.709, sRGB, ACES
│   │   ├── film_luts.yaml           # Kodak, Fuji, Vision3
│   │   └── creative_luts.yaml       # Cinematic looks
│   │
│   ├── animation/
│   │   ├── camera_moves.yaml        # Orbit, dolly, crane
│   │   └── easing_curves.yaml       # Animation easing
│   │
│   ├── render/
│   │   ├── quality_profiles.yaml    # Preview, draft, final
│   │   └── pass_presets.yaml        # Beauty, cryptomatte, etc.
│   │
│   └── shots/
│       ├── base/                    # Abstract base templates
│       │   ├── base_product.yaml
│       │   ├── base_hero.yaml
│       │   └── base_turntable.yaml
│       │
│       ├── product/                 # Product shot presets
│       │   ├── product_hero.yaml
│       │   ├── product_detail.yaml
│       │   └── product_lifestyle.yaml
│       │
│       └── control_surface/         # Control surface specific
│           ├── console_overhead.yaml
│           ├── mixer_angle.yaml
│           └── knob_detail.yaml
```

### 2.3 State Persistence Structure

```
.gsd-state/
├── cinematic/
│   ├── camera/
│   │   └── {shot_name}.yaml         # Camera transform, settings
│   │
│   ├── lighting/
│   │   └── {shot_name}.yaml         # Light positions, intensities
│   │
│   ├── frames/
│   │   ├── frame_index.yaml         # Master index
│   │   └── {shot_name}/
│   │       ├── 001/
│   │       │   ├── state.yaml
│   │       │   └── thumbnail.png
│   │       └── 002/
│   │           └── ...
│   │
│   └── sessions/
│       └── {session_id}.yaml        # Resume state for interrupted work
```

---

## Part 3: Camera System Design

### 3.1 Camera Data Model

```yaml
camera:
  # Identity
  name: hero_camera

  # Lens
  lens:
    preset: 85mm_portrait       # References lens_presets.yaml
    focal_length: 85            # mm (override preset)
    focus_distance: auto        # auto, or distance in meters

  # Sensor
  sensor:
    preset: full_frame          # References sensor_presets.yaml
    size: [36, 24]              # mm (override preset)

  # Aperture / DoF
  aperture:
    f_stop: 4.0
    blades: 9                   # Bokeh shape
    bokeh:
      shape: circular           # circular, hexagonal, octagonal
      rotation: 0

  # Transform
  transform:
    position: [0.5, -0.5, 0.3]
    rotation: [80, 0, 45]       # Euler degrees

  # Rig (optional)
  rig:
    type: tripod                # tripod, dolly, crane, steadicam
    target: plumb_bob           # What to point at

  # Motion (optional)
  motion:
    path: orbit_90              # Motion path preset
    duration: 120               # Frames

  # Imperfections (optional)
  imperfections:
    preset: cooke_s4
    # Or individual overrides:
    flare_intensity: 0.3
    vignette: 0.2
```

### 3.2 Lens Preset Example

```yaml
# configs/cinematic/cameras/lens_presets.yaml

lenses:
  # Wide angle
  14mm_ultra_wide:
    focal_length: 14
    description: "Dramatic distortion, epic establishing shots"
    distortion: 0.08
    vignette: 0.4
    use_case: establishing

  24mm_wide:
    focal_length: 24
    description: "Environmental context, slight distortion"
    distortion: 0.03
    vignette: 0.2
    use_case: environmental

  # Normal
  35mm_documentary:
    focal_length: 35
    description: "Natural field of view, street feel"
    distortion: 0.01
    vignette: 0.1
    use_case: documentary

  50mm_normal:
    focal_length: 50
    description: "Most natural, human eye equivalent"
    distortion: 0.0
    vignette: 0.05
    use_case: hero

  # Portrait
  85mm_portrait:
    focal_length: 85
    description: "Flattering compression, background separation"
    distortion: 0.0
    vignette: 0.1
    use_case: portrait

  135mm_telephoto:
    focal_length: 135
    description: "Strong compression, isolated subject"
    distortion: 0.0
    vignette: 0.15
    use_case: detail

  # Macro
  90mm_macro:
    focal_length: 90
    description: "Close focus, extreme detail"
    minimum_focus: 0.15
    distortion: 0.0
    use_case: macro

  # Vintage / Character Lenses
  helios_44_2:
    focal_length: 58
    description: "Vintage Soviet, swirly bokeh"
    distortion: 0.02
    vignette: 0.5
    flare: intense
    bokeh_swirl: 0.7
    chromatic_aberration: 0.004
```

### 3.3 Camera Rig Presets

```yaml
# configs/cinematic/cameras/rig_presets.yaml

rigs:
  tripod:
    description: "Static with pan/tilt"
    degrees_of_freedom: [pan, tilt]
    constraints:
      position_locked: true

  tripod_orbit:
    description: "Orbit around plumb bob"
    motion:
      type: orbit
      axis: z
      range: [0, 360]

  dolly:
    description: "Linear track movement"
    track:
      type: linear
      direction: forward
    wheels: false

  dolly_curved:
    description: "Curved track for arc shots"
    track:
      type: bezier
      control_points: auto

  crane:
    description: "3D arc movement"
    arm_length: 3.0
    max_height: 5.0
    motion:
      type: arc_3d

  steadicam:
    description: "Smooth handheld simulation"
    smoothing:
      position: 0.8
      rotation: 0.9
    human_motion: true

  drone:
    description: "Free-flight path following"
    motion:
      type: path
      speed: constant
    constraints: none
```

---

## Part 4: Lighting System Design

### 4.1 Light Data Model

```yaml
light:
  name: key_light

  # Type
  type: area               # area, spot, point, sun

  # Transform
  transform:
    position: [1.5, -0.5, 2.0]
    rotation: [-30, 0, 0]

  # Intensity
  intensity:
    power: 1200            # Watts
    exposure: 0            # EV compensation

  # Color
  color:
    temperature: 5600      # Kelvin
    # OR
    rgb: [1.0, 0.98, 0.95]

  # Shape (for area lights)
  shape:
    type: rectangle        # rectangle, disk, ellipse
    size: [1.0, 0.5]

  # Softness
  softness:
    radius: 0.1
    spread: 0.5

  # Gels (optional)
  gels:
    - type: CTO
      intensity: 0.5       # 50% strength
    - type: diffusion
      grade: quarter        # quarter, half, full

  # Shadows
  shadows:
    enabled: true
    softness: 0.3
    max_distance: 10.0

  # Linking
  collection: subject_only  # Only affect specific objects
```

### 4.2 Lighting Rig Presets

```yaml
# configs/cinematic/lighting/rig_presets.yaml

rigs:
  # Classic Setups
  three_point_soft:
    description: "Classic 3-point with soft shadows"
    lights:
      key:
        position_mode: angle_distance
        angle: 45           # Degrees from camera
        elevation: 30       # Degrees above subject
        distance: 1.5
        intensity_ratio: 1.0
        softness: 0.8

      fill:
        position_mode: angle_distance
        angle: -45
        elevation: 15
        distance: 2.0
        intensity_ratio: 0.4
        softness: 0.9

      rim:
        position_mode: angle_distance
        angle: 160
        elevation: 45
        distance: 1.5
        intensity_ratio: 0.7
        softness: 0.3

  three_point_hard:
    description: "Dramatic 3-point with hard shadows"
    extends: three_point_soft
    lights:
      key:
        softness: 0.1
      fill:
        intensity_ratio: 0.2
        softness: 0.3

  # Product Lighting
  product_hero:
    description: "Clean product photography"
    lights:
      overhead_softbox:
        type: area
        position: [0, 0, 2.0]
        rotation: [-90, 0, 0]
        size: [2.0, 2.0]
        intensity: 1500
        softness: 1.0

      fill_card_left:
        type: area
        position: [-1.0, 0, 0.5]
        rotation: [0, 60, 0]
        size: [0.5, 1.0]
        intensity: 200
        softness: 1.0

      fill_card_right:
        type: area
        position: [1.0, 0, 0.5]
        rotation: [0, -60, 0]
        size: [0.5, 1.0]
        intensity: 200
        softness: 1.0

  product_dramatic:
    description: "Dramatic product shot with mood"
    lights:
      key_spot:
        type: spot
        angle: 45
        elevation: 60
        distance: 1.0
        intensity: 2000
        spot_size: 30
        softness: 0.2

      rim:
        type: area
        angle: 170
        elevation: 30
        distance: 1.2
        intensity: 800

  # Studio Environments
  studio_high_key:
    description: "Bright, minimal shadows"
    hdri:
      file: studio_bright.hdr
      intensity: 1.5
      rotation: 0

    lights:
      fill_ambient:
        type: area
        position: [0, 0, 3.0]
        rotation: [-90, 0, 0]
        size: [5.0, 5.0]
        intensity: 500

  studio_low_key:
    description: "Dark, dramatic, selective lighting"
    hdri:
      file: black.hdr
      intensity: 0

    lights:
      key_narrow:
        type: spot
        angle: 30
        elevation: 45
        distance: 0.8
        intensity: 3000
        spot_size: 15
        gobo: barn_doors

  # Control Surface Specific
  console_overhead:
    description: "Top-down console view"
    lights:
      overhead:
        type: area
        position: [0, -0.5, 1.5]
        rotation: [-70, 0, 0]
        size: [1.0, 0.8]
        intensity: 1200

      screen_glow:
        type: area
        position: [0, -0.3, 0.1]
        rotation: [-90, 0, 0]
        size: [0.3, 0.2]
        intensity: 50
        color: [0.8, 0.9, 1.0]

  mixer_angle:
    description: "Angled mixer shot"
    lights:
      key:
        angle: 60
        elevation: 35
        distance: 1.2
        intensity: 1000

      fill:
        angle: -30
        elevation: 20
        distance: 1.8
        intensity: 300

      indicator_glow:
        type: point
        position: [0, 0, 0.05]
        intensity: 100
        color: [0.2, 0.8, 1.0]
        radius: 0.01
```

### 4.3 HDRI Presets

```yaml
# configs/cinematic/lighting/hdri_presets.yaml

hdri:
  # Studio HDRIs
  studio_bright:
    file: assets/hdri/studio_bright_4k.hdr
    description: "Clean bright studio"
    exposure: 0
    rotation: 0
    background_visible: false

  studio_soft:
    file: assets/hdri/studio_soft_4k.hdr
    description: "Soft diffused studio light"
    exposure: 0.5
    rotation: 0

  # Environment HDRIs
  overcast_day:
    file: assets/hdri/overcast_4k.hdr
    description: "Soft outdoor light"
    exposure: 0
    rotation: auto          # Auto-orient sun

  golden_hour:
    file: assets/hdri/golden_hour_4k.hdr
    description: "Warm sunset light"
    exposure: -0.5
    rotation: auto

  night_city:
    file: assets/hdri/night_city_4k.hdr
    description: "Urban night environment"
    exposure: 1.0
    background_visible: true

  # Abstract HDRIs
  cyberpunk_neon:
    file: assets/hdri/cyberpunk_neon_4k.hdr
    description: "Neon-lit cyberpunk environment"
    exposure: 0
    saturation: 1.2
```

---

## Part 5: Backdrop System Design

### 5.1 Backdrop Data Model

```yaml
backdrop:
  type: infinite_curve      # infinite_curve, gradient, hdri, mesh

  # For infinite_curve
  curve:
    radius: 5.0
    color_bottom: [0.95, 0.95, 0.95]
    color_top: [1.0, 1.0, 1.0]
    gradient_height: 0.3
    shadow_catcher: true

  # For gradient
  gradient:
    type: linear            # linear, radial, angular
    stops:
      - position: 0.0
        color: [0.1, 0.1, 0.15]
      - position: 0.5
        color: [0.2, 0.2, 0.25]
      - position: 1.0
        color: [0.15, 0.15, 0.2]

  # For HDRI
  hdri:
    preset: studio_bright
    visible_in_render: false
    camera_projection: true

  # For mesh
  mesh:
    file: assets/environments/studio_set_01.blend
    scale: 1.0
    visible_to_camera: true
    shadow_catcher: false
```

### 5.2 Backdrop Presets

```yaml
# configs/cinematic/backdrops/infinite_curves.yaml

curves:
  white_studio:
    color_bottom: [0.95, 0.95, 0.95]
    color_top: [1.0, 1.0, 1.0]
    radius: 5.0

  gray_studio:
    color_bottom: [0.3, 0.3, 0.3]
    color_top: [0.5, 0.5, 0.5]
    radius: 4.0

  dark_studio:
    color_bottom: [0.05, 0.05, 0.05]
    color_top: [0.15, 0.15, 0.15]
    radius: 6.0

  gradient_warm:
    color_bottom: [0.8, 0.6, 0.4]
    color_top: [0.9, 0.85, 0.8]
    radius: 5.0

  gradient_cool:
    color_bottom: [0.2, 0.3, 0.4]
    color_top: [0.4, 0.5, 0.6]
    radius: 5.0
```

---

## Part 6: Color Pipeline Design

### 6.1 LUT System

```yaml
# configs/cinematic/color/technical_luts.yaml

technical:
  rec709:
    file: luts/rec709.cube
    description: "Standard Rec.709 display"
    type: display

  srgb:
    file: luts/srgb.cube
    description: "sRGB display"
    type: display

  p3_dci:
    file: luts/p3_dci.cube
    description: "DCI-P3 display"
    type: display

  aces_cg:
    file: luts/aces_cg.cube
    description: "ACEScg working space"
    type: working
```

```yaml
# configs/cinematic/color/film_luts.yaml

film:
  kodak_2383:
    file: luts/kodak_2383.cube
    description: "Classic Kodak Vision3 print film"
    intensity: 1.0
    use_case: [cinematic, warm]

  fuji_3510:
    file: luts/fuji_3510.cube
    description: "Fuji film stock"
    intensity: 1.0
    use_case: [cinematic, cool]

  cineon:
    file: luts/cineon.cube
    description: "Log film scan look"
    intensity: 0.8
    use_case: [cinematic, flat]
```

### 6.2 Color Management

```yaml
color_management:
  # Working space
  working_space: AgX        # AgX, ACEScg, Filmic, Standard

  # View transform
  view_transform: AgX Default Medium High Contrast

  # Look (applied after view transform)
  look:
    enabled: true
    preset: kodak_2383
    intensity: 0.8

  # Per-shot overrides
  overrides:
    exposure: 0.0
    gamma: 1.0
    saturation: 1.0
    contrast: 1.0
```

---

## Part 7: Animation System Design

### 7.1 Camera Move Presets

```yaml
# configs/cinematic/animation/camera_moves.yaml

moves:
  orbit_90:
    type: orbit
    angle_range: [0, 90]
    axis: z
    duration: 90
    easing: ease_in_out

  orbit_180:
    type: orbit
    angle_range: [0, 180]
    axis: z
    duration: 180
    easing: ease_in_out

  orbit_360:
    type: orbit
    angle_range: [0, 360]
    axis: z
    duration: 360
    easing: linear

  dolly_in:
    type: dolly
    direction: forward
    distance: 0.5
    duration: 60
    easing: ease_out

  dolly_out:
    type: dolly
    direction: backward
    distance: 0.5
    duration: 60
    easing: ease_in

  push_in:
    type: combined
    moves:
      - type: dolly
        distance: 0.3
      - type: focal_length
        from: 35
        to: 50
    duration: 120

  rack_focus:
    type: focus
    from: 0.5
    to: 2.0
    duration: 30
    easing: ease_in_out

  crane_up:
    type: crane
    elevation_range: [0, 45]
    distance: 2.0
    duration: 90

  reveal:
    type: sequence
    steps:
      - move: dolly_in
        duration: 60
      - hold: 30
      - move: orbit_90
        duration: 90
```

### 7.2 Turntable System

```yaml
turntable:
  enabled: true
  subject_rotation: true    # Rotate object, not camera

  rotation:
    axis: z
    angle_range: [0, 360]
    duration: 120           # Frames for full rotation

  # Optional camera movement during turntable
  camera:
    mode: static            # static, gentle_orbit, push_in
```

---

## Part 8: Shot Assembly System

### 8.1 Complete Shot Definition

```yaml
# Example: Complete shot configuration

shot:
  name: hero_knob_01

  # Subject
  subject:
    type: artifact
    artifact: my_knob
    position: [0, 0, 0]
    rotation: [0, 0, 15]     # Slight angle

  # Plumb Bob (focus/orbit target)
  plumb_bob:
    mode: auto
    offset: [0, 0, 0.015]    # Center on knob's visual center

  # Camera
  camera:
    lens:
      preset: 85mm_portrait
      aperture: f/4
      focus_distance: auto

    transform:
      position_mode: angle_distance
      angle: 30
      elevation: 25
      distance: 0.4

    rig:
      type: tripod

  # Lighting
  lighting:
    rig: three_point_soft
    intensity_scale: 1.0

    # Overrides
    key_light:
      angle: 45
      softness: 0.9

  # Backdrop
  backdrop:
    type: infinite_curve
    preset: gray_studio

  # Color
  color:
    view_transform: AgX Default Medium High Contrast
    look:
      preset: kodak_2383
      intensity: 0.6

  # Render
  render:
    profile: product_4k
    passes: [beauty, cryptomatte]

  # Animation (optional)
  animation:
    enabled: false
```

### 8.2 Shot Inheritance Example

```yaml
# shots/base/control_surface_base.yaml
name: control_surface_base
abstract: true

camera:
  lens:
    preset: 50mm_normal
    aperture: f/5.6

lighting:
  rig: three_point_soft

backdrop:
  type: infinite_curve
  preset: gray_studio

color:
  look:
    preset: kodak_2383
    intensity: 0.5

---

# shots/control_surface/knob_detail.yaml
extends: control_surface_base

camera:
  lens:
    preset: 90mm_macro
    aperture: f/8
  transform:
    distance: 0.25

lighting:
  key_light:
    intensity_ratio: 1.2

---

# shots/control_surface/console_overhead.yaml
extends: control_surface_base

camera:
  lens:
    preset: 35mm_documentary
  transform:
    elevation: 70
    distance: 0.8

lighting:
  rig: console_overhead
```

---

## Part 9: Resume & Edit System

### 9.1 Resume Workflow

```yaml
# Task file with resume capability
task:
  name: render_knob_hero

  resume:
    enabled: true
    state_file: .gsd-state/cinematic/sessions/hero_knob.yaml

  shot:
    # ... shot configuration

    # If resuming, these can be omitted:
    # camera.transform.position - uses saved state
    # lighting positions - uses saved state
```

### 9.2 Edit Workflow

```yaml
# Edit existing shot
task:
  name: edit_knob_hero

  load:
    frame: hero_knob_001    # Load from frame store

  # Only specify what to change
  edit:
    camera:
      transform:
        elevation: 35       # Change angle

    lighting:
      key_light:
        intensity_ratio: 1.3  # Brighter key
```

---

## Part 10: Plugin Integration Strategy

### 10.1 Plugin Roles

| Plugin | Cinematic Use | Integration Point |
|--------|--------------|-------------------|
| **Hard Ops** | Topology cleanup before render | Pre-render asset freeze |
| **Boxcutter** | Custom gobo shapes | Asset creation phase |
| **KitOps** | Browse studio environments | Human curation only |
| **Sanctus** | Surface wear, material polish | Pre-render finalization |

### 10.2 Handoff Protocol

```yaml
# Asset handoff to cinematic system
handoff:
  # 1. Geometry must be frozen
  geometry:
    status: frozen          # Hard Ops cleanup done
    modifiers_applied: true

  # 2. Materials must be finalized
  materials:
    status: finalized       # Sanctus surface work done
    textures_baked: true

  # 3. Asset is ready for cinematic
  ready_for: cinematic_render
```

---

## Part 11: Phase Breakdown

### Phase 6.0: Foundation (REQ-CINE-01)
- Create `lib/cinematic/` module structure
- Define base classes and types
- Create configuration directory structure
- Implement state persistence framework

### Phase 6.1: Camera System (REQ-CINE-CAM)
- Implement camera.py (transforms, rig mounting)
- Implement lenses.py (presets, DoF, imperfections)
- Create camera configuration files
- Implement plumb_bob.py

### Phase 6.2: Lighting System (REQ-CINE-LIGHT)
- Implement lighting.py (rigs, individual lights)
- Create lighting rig presets
- Create HDRI system
- Implement gel/diffusion system

### Phase 6.3: Backdrop System (REQ-CINE-ENV)
- Implement backdrops.py (curves, gradients, HDRI)
- Create backdrop presets
- Implement shadow catcher system

### Phase 6.4: Color Pipeline (REQ-CINE-LUT)
- Implement color.py (LUT management, color management)
- Create LUT preset library
- Implement exposure lock system

### Phase 6.5: Animation System (REQ-CINE-ANIM)
- Implement animation.py (camera moves, keyframes)
- Implement motion_path.py
- Create animation presets
- Implement turntable system

### Phase 6.6: Render Profiles (REQ-CINE-RENDER)
- Extend render.py for cinematic profiles
- Implement render pass system
- Create quality tier presets

### Phase 6.7: Support Systems
- Implement shuffler.py
- Implement frame_store.py
- Implement depth_layers.py
- Implement composition.py

### Phase 6.8: Shot Assembly (REQ-CINE-SHOT)
- Implement shot.py (complete shot assembly)
- Implement template.py (inheritance)
- Create shot preset library
- Implement resume/edit system

### Phase 6.9: Integration & Testing
- Integration with control surface system
- End-to-end shot rendering tests
- Performance optimization
- Documentation

---

## Part 12: Architectural Decisions (Approved)

The following decisions were made during design review on 2026-02-18:

### Q1: Multi-Camera Shots
**Decision: B) Multi-camera with composite layout**

Product shots often need multiple angles in one image (front + side + detail). This is a native capability.

```yaml
multi_camera:
  layout: grid_2x2         # grid_2x2, grid_3x3, horizontal, vertical, custom
  cameras:
    - name: hero_front
      position: [0.5, -0.5, 0.3]
    - name: hero_side
      position: [0.5, 0, 0.3]
    - name: detail_macro
      position: [0.2, -0.3, 0.15]
      lens: 90mm_macro
    - name: overhead
      position: [0, -0.3, 0.8]
  spacing: 20              # Pixels between views
  labels: true             # Optional camera name labels
```

### Q2: Real-time Preview
**Decision: C) Viewport render + EEVEE draft + Cycles final**

Three-tier system for maximum iteration speed:

| Tier | When | Speed | Quality |
|------|------|-------|---------|
| Viewport Capture | Live editing | Instant | Preview |
| EEVEE Draft | Quick review | Seconds | Good |
| Cycles Final | Production | Minutes-Hours | Perfect |

### Q3: Asset Library HDRI
**Decision: C) Both with fallback + Auto-download**

Search order:
1. Project local: `{project}/assets/hdri/`
2. GSD bundled: `lib/cinematic/assets/hdri/`
3. External library: `/Volumes/Storage/3d/hdri/`
4. Auto-download from Polyhaven (if configured)

### Q4: Animation Timeline Integration
**Decision: B) Unified timeline, camera/object animations linked**

Single animation system coordinates both object animation (REQ-CTRL-05 morphs) and camera movement. Enables synchronized effects like "dolly in while morphing style."

### Q5: Compositor Integration
**Decision: C) Hybrid (some render, some comp)**

Split based on physical accuracy vs. artistic:

| Effect | Where | Why |
|--------|-------|-----|
| DoF | Render | Physically accurate, needs geometry |
| Motion Blur | Render | Needs geometry/velocity |
| Bloom | Compositor | Post-effect, faster to tweak |
| Lens Flare | Compositor | Artistic, needs compositing control |
| Vignette | Compositor | Easy to adjust, no re-render |
| Chromatic Aberration | Compositor | Post-effect |
| Grain | Compositor | Post-effect |

### Q6: Output Formats
**Decision: PNG preview, EXR production, JPEG delivery**

| Format | Use Case |
|--------|----------|
| PNG | Web, quick preview |
| EXR (multi-layer) | Production, compositing |
| JPEG | Delivery, smaller files |

### Q7: Batch Rendering
**Decision: Render queue with dependency management**

```yaml
render_queue:
  tasks:
    - shot: hero_knob_01
      depends_on: []
    - shot: hero_knob_02
      depends_on: [hero_knob_01]  # Sequential
    - shot: detail_knob_01
      depends_on: []              # Parallel with hero_knob_01
  parallel_jobs: 4
  resume_on_failure: true
```

### Q8: Metadata/Shot Info
**Decision: Yes - EXIF-like metadata in EXR outputs**

```yaml
metadata:
  embed_in_exr: true
  include:
    - shot_name
    - camera_settings
    - lighting_setup
    - render_time
    - gsd_version
    - git_commit
```

### Q9: Camera Matching / Import
**Decision: Yes - camera matching from reference images**

```yaml
camera_matching:
  from_reference:
    image: reference_photo.jpg
    focal_length: estimate      # estimate, or explicit
    match_horizon: true
  from_tracking:
    file: camera_track.nk
    format: auto
```

### Q10: Audio for Animation
**Decision: Yes - audio track support for timing**

```yaml
animation:
  audio:
    file: soundtrack.wav
    sync_beats: true
    markers:
      - frame: 24
        label: "drop"
      - frame: 72
        label: "chorus"
```

---

## Part 13: Technical Specifications (Council-Approved)

This section addresses technical implementation details required by the Council of Ricks review.

### 13.1 Render Engine Configuration

#### Engine Names (Blender 5.x API)

```python
# CRITICAL: Correct engine identifiers for Blender 5.x
ENGINES = {
    'CYCLES': 'CYCLES',
    'EEVEE_NEXT': 'BLENDER_EEVEE_NEXT',  # NOT 'BLENDER_EEVEE' (deprecated)
    'WORKBENCH': 'BLENDER_WORKBENCH'
}

def set_render_engine(engine: str):
    """Set render engine with correct Blender 5.x identifier."""
    bpy.context.scene.render.engine = ENGINES[engine]
```

#### Quality Tiers with Resolution Scaling

```yaml
# configs/cinematic/render/quality_profiles.yaml

profiles:
  viewport_capture:
    engine: BLENDER_WORKBENCH
    resolution:
      base: 512
      scale: 100%           # No scaling
    description: "Instant viewport grab, preview only"

  eevee_draft:
    engine: BLENDER_EEVEE_NEXT  # CRITICAL: Use EEVEE Next
    resolution:
      base: 2048
      scale: 50%           # MEDIUM: Render at 1024px for speed
    samples: 16
    raytracing: false      # Disable for speed
    description: "Quick review, seconds to render"

  cycles_preview:
    engine: CYCLES
    resolution:
      base: 2048
      scale: 100%
    samples: 64
    adaptive_sampling:
      enabled: true
      threshold: 0.02
      min_samples: 8
    description: "Review quality, minutes to render"

  cycles_production:
    engine: CYCLES
    resolution:
      base: 4096
      scale: 100%
    samples: 256
    adaptive_sampling:
      enabled: true
      threshold: 0.01
      min_samples: 16
    description: "Production quality"

  cycles_archive:
    engine: CYCLES
    resolution:
      base: 4096
      scale: 100%
    samples: 1024
    adaptive_sampling:
      enabled: true
      threshold: 0.005
      min_samples: 32
    description: "Archive quality, overnight renders"
```

### 13.2 Render Pass API Configuration

```python
# lib/cinematic/render.py

def configure_render_passes(view_layer, passes: list[str]):
    """
    Configure render passes via Blender API.

    CRITICAL: Must set use_pass_* attributes on view_layer.
    """
    # Disable all passes first
    for attr in dir(view_layer):
        if attr.startswith('use_pass_'):
            setattr(view_layer, attr, False)

    # Pass mapping: config name -> API attribute
    PASS_MAPPING = {
        'beauty': None,  # Always enabled
        'combined': 'use_pass_combined',

        # Diffuse
        'diffuse_direct': 'use_pass_diffuse_direct',
        'diffuse_indirect': 'use_pass_diffuse_indirect',
        'diffuse_color': 'use_pass_diffuse_color',

        # Glossy
        'glossy_direct': 'use_pass_glossy_direct',
        'glossy_indirect': 'use_pass_glossy_indirect',
        'glossy_color': 'use_pass_glossy_color',

        # Transmission
        'transmission_direct': 'use_pass_transmission_direct',
        'transmission_indirect': 'use_pass_transmission_indirect',
        'transmission_color': 'use_pass_transmission_color',

        # Emission
        'emission': 'use_pass_emit',

        # Cryptomatte - CRITICAL: Must enable for object isolation
        'cryptomatte_object': 'use_pass_cryptomatte_object',
        'cryptomatte_material': 'use_pass_cryptomatte_material',
        'cryptomatte_asset': 'use_pass_cryptomatte_asset',

        # Data passes
        'depth': 'use_pass_z',
        'normal': 'use_pass_normal',
        'vector': 'use_pass_vector',  # Motion vectors

        # Environment
        'environment': 'use_pass_environment',
        'shadow': 'use_pass_shadow',
        'ao': 'use_pass_ambient_occlusion',
    }

    for pass_name in passes:
        if pass_name == 'beauty':
            continue  # Always present
        attr = PASS_MAPPING.get(pass_name)
        if attr:
            setattr(view_layer, attr, True)

    # CRITICAL: Cryptomatte requires additional setup
    if 'cryptomatte_object' in passes:
        view_layer.cryptomatte_levels = 6  # Standard levels
        view_layer.use_pass_cryptomatte_accurate = True
```

#### Render Pass Dependencies

```yaml
# Some passes require others to be enabled

dependencies:
  cryptomatte_object:
    requires: [combined]
  cryptomatte_material:
    requires: [combined]
  vector:
    requires: [combined]  # Motion vectors need beauty pass
  normal:
    requires: [combined]
  depth:
    requires: []  # Independent
```

### 13.3 Compositor Effect Pipeline

#### Effect Ordering (CRITICAL)

Effects MUST be applied in this exact order for physically-correct results:

```python
# lib/cinematic/lens_fx.py

COMPOSITOR_PIPELINE = [
    # Stage 1: Geometric distortions (before color)
    ('lens_distortion', 1),      # Barrel/pincushion
    ('chromatic_aberration', 2), # RGB channel separation

    # Stage 2: Luminance adjustments
    ('vignette', 3),             # Edge darkening
    ('exposure_adjust', 4),      # Exposure correction

    # Stage 3: Glow/bloom effects
    ('bloom', 5),                # Bright area glow
    ('glare', 6),                # Lens flare/glare

    # Stage 4: Color grading
    ('color_correction', 7),     # Basic CC
    ('technical_lut', 8),        # Technical transform (early)
    ('creative_lut', 9),         # Creative look (late)

    # Stage 5: Film effects (final)
    ('film_grain', 10),          # Add grain last
]

def build_compositor_tree(node_tree, config):
    """Build compositor node tree in correct order."""
    # Clear existing nodes
    nodes = node_tree.nodes
    links = node_tree.links
    nodes.clear()

    # Create render layers input
    render_layers = nodes.new('CompositorNodeRLayers')

    # Create output
    composite = nodes.new('CompositorNodeComposite')

    # Build chain in order
    prev_node = render_layers
    prev_socket = 'Image'

    for effect_name, order in COMPOSITOR_PIPELINE:
        if config.get(effect_name, {}).get('enabled', False):
            effect_node = create_effect_node(nodes, effect_name, config[effect_name])
            links.new(prev_node.outputs[prev_socket], effect_node.inputs['Image'])
            prev_node = effect_node
            prev_socket = 'Image'

    # Connect to output
    links.new(prev_node.outputs['Image'], composite.inputs['Image'])
```

### 13.4 LUT Application Points

```yaml
# CRITICAL: LUTs have different application points

lut_pipeline:
  technical:
    # Applied EARLY in pipeline (before creative grading)
    # Use for: color space conversion, display transforms
    stage: 8
    examples:
      - rec709_to_srgb      # Display conversion
      - linear_to_log       # Log encoding
      - acescg_to_rec709    # Working space conversion

  creative:
    # Applied LATE in pipeline (after color correction)
    # Use for: film looks, artistic grades
    stage: 9
    examples:
      - kodak_2383          # Film emulation
      - fuji_3510           # Film emulation
      - cinematic_teorange  # Teal & orange look
```

```python
# LUT technical specifications

LUT_SPECS = {
    # Technical LUTs
    'rec709': {
        'file': 'luts/rec709.cube',
        'size': 65,           # 65³ for technical
        'format': 'cube',
        'colorspace_in': 'Rec709',
        'colorspace_out': 'sRGB',
    },
    'srgb': {
        'file': 'luts/srgb.cube',
        'size': 65,
        'format': 'cube',
        'colorspace_in': 'Linear',
        'colorspace_out': 'sRGB',
    },

    # Film LUTs
    'kodak_2383': {
        'file': 'luts/kodak_2383.cube',
        'size': 33,           # 33³ sufficient for film looks
        'format': 'cube',
        'colorspace_in': 'Linear',
        'colorspace_out': 'sRGB',
        'intensity_default': 0.8,
    },
}
```

### 13.5 Procedural Backdrop Geometry Specification

```python
# lib/cinematic/backdrops.py

def create_infinite_curve(config: dict) -> bpy.types.Object:
    """
    Create procedural infinite curve backdrop.

    ALGORITHM:
    1. Calculate floor extent from subject bounding box
    2. Generate smooth curve from floor to wall
    3. Create mesh with proper UVs for gradient shading
    4. Apply shadow catcher material if enabled

    INPUTS:
    - radius: Distance from subject to curve start (meters)
    - curve_height: Height of vertical portion (meters)
    - curve_segments: Resolution of curve (default: 32)
    - shadow_catcher: Enable shadow catching

    OUTPUTS:
    - Blender mesh object named "gsd_backdrop_curve"
    - Material "gsd_backdrop_mat" with gradient
    """
    import bpy
    import bmesh
    import math

    # Extract config
    radius = config.get('radius', 5.0)
    curve_height = config.get('curve_height', 3.0)
    curve_segments = config.get('curve_segments', 32)
    shadow_catcher = config.get('shadow_catcher', True)
    color_bottom = config.get('color_bottom', [0.95, 0.95, 0.95])
    color_top = config.get('color_top', [1.0, 1.0, 1.0])

    # Create mesh
    mesh = bpy.data.meshes.new("gsd_backdrop_curve_mesh")
    obj = bpy.data.objects.new("gsd_backdrop_curve", mesh)

    # Build geometry with bmesh
    bm = bmesh.new()

    # Floor vertices (X-Z plane at Y=0)
    floor_verts = []
    for i in range(curve_segments + 1):
        t = i / curve_segments
        x = -radius + (2 * radius * t)
        v = bm.verts.new((x, 0, 0))
        floor_verts.append(v)

    # Curve vertices (smooth transition)
    curve_verts = []
    curve_radius = radius * 0.3  # Curve tightness
    for i in range(curve_segments + 1):
        t = i / curve_segments
        angle = math.pi / 2 * t
        x = -curve_radius + (curve_radius * math.cos(angle))
        z = curve_radius * math.sin(angle)
        v = bm.verts.new((x, 0, z))
        curve_verts.append(v)

    # Wall vertices (vertical)
    wall_verts = []
    for i in range(curve_segments + 1):
        t = i / curve_segments
        x = -curve_radius + (2 * curve_radius * t)
        v = bm.verts.new((x, 0, curve_height))
        wall_verts.append(v)

    # Create faces
    for i in range(curve_segments):
        # Floor to curve
        bm.faces.new([floor_verts[i], floor_verts[i+1],
                      curve_verts[i+1], curve_verts[i]])
        # Curve to wall
        bm.faces.new([curve_verts[i], curve_verts[i+1],
                      wall_verts[i+1], wall_verts[i]])

    bm.to_mesh(mesh)
    bm.free()

    # Create material
    mat = bpy.data.materials.new("gsd_backdrop_mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    # Gradient shader
    output = nodes.get('Material Output')
    principled = nodes.get('Principled BSDF')

    # Add color ramp for gradient
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*color_bottom, 1.0)
    ramp.color_ramp.elements[1].color = (*color_top, 1.0)

    # Connect gradient based on Z position
    separate = nodes.new('ShaderNodeSeparateXYZ')
    math_node = nodes.new('ShaderNodeMath')
    math_node.operation = 'DIVIDE'
    math_node.inputs[1].default_value = curve_height

    mat.node_tree.links.new(separate.outputs['Z'], math_node.inputs[0])
    mat.node_tree.links.new(math_node.outputs['Value'], ramp.inputs['Fac'])
    mat.node_tree.links.new(ramp.outputs['Color'], principled.inputs['Base Color'])

    # Shadow catcher setup
    if shadow_catcher:
        mat.shadow_method = 'CLIP'
        mat.use_backface_culling = True

    obj.data.materials.append(mat)

    # Link to scene
    bpy.context.collection.objects.link(obj)

    return obj
```

### 13.6 Shadow Catcher Geometry Contract

```yaml
# Shadow catcher requirements for compositing

shadow_catcher_contract:
  # Geometry must:
  geometry:
    - Single-sided faces (use backface culling)
    - No overlapping geometry
    - Proper UV unwrapping (for gradient materials)

  # Material must:
  material:
    shadow_method: CLIP      # Not 'HASHED' or 'STOCHASTIC'
    alpha_blend: true
    backface_culling: true

  # Render settings:
  render:
    film_transparent: true   # Enable alpha in output
    passes_required:
      - shadow
      - combined

  # Compositor integration:
  compositor:
    - Use Alpha Over node to composite shadows
    - Shadow pass for intensity control
    - Cryptomatte for isolation if needed
```

### 13.7 Hardware-Aware Denoiser Selection

```python
# lib/cinematic/render.py

def select_denoiser() -> str:
    """
    Select optimal denoiser based on hardware.

    Returns Blender denoiser identifier.
    """
    import bpy
    import platform

    prefs = bpy.context.preferences

    # Check OptiX availability (NVIDIA + OptiX)
    if _has_optix():
        return 'OPTIX'

    # Check Metal on Apple Silicon
    if platform.system() == 'Darwin':
        if _is_apple_silicon():
            return 'OPENIMAGEDENOISE'  # Metal-accelerated

    # Default to OpenImageDenoise (CPU)
    return 'OPENIMAGEDENOISE'


def _has_optix() -> bool:
    """Check if OptiX is available."""
    import bpy
    cycles_prefs = bpy.context.preferences.addons.get('cycles')
    if cycles_prefs:
        return cycles_prefs.preferences.compute_device_type == 'OPTIX'
    return False


def _is_apple_silicon() -> bool:
    """Check if running on Apple Silicon."""
    import platform
    return platform.processor() == 'arm'


# Denoiser configuration
DENOISER_CONFIG = {
    'OPTIX': {
        'quality': 'high',
        'memory_intensive': True,
        'nvidia_only': True,
    },
    'OPENIMAGEDENOISE': {
        'quality': 'high',
        'cpu_or_gpu': True,
        'apple_silicon_accelerated': True,
    },
}
```

### 13.8 Light Linking Configuration

```python
# lib/cinematic/lighting.py

def configure_light_linking(light: bpy.types.Object, config: dict):
    """
    Configure light linking for selective illumination.

    LIGHT LINKING allows lights to affect only specific objects.
    """
    import bpy

    # Get or create light linking collection
    collection_name = config.get('collection', 'subject_only')

    if collection_name == 'subject_only':
        # Create collection from subject objects
        collection = bpy.data.collections.get('gsd_subject')
        if not collection:
            collection = bpy.data.collections.new('gsd_subject')
            bpy.context.collection.children.link(collection)

    # Blender 4.0+ light linking
    if hasattr(light, 'light_linking'):
        light.light_linking.receiver_collection = collection
        light.light_linking.mode = 'INCLUDE'  # Only affect collection

    # Legacy approach for older Blender versions
    else:
        # Use render layers with light groups
        view_layer = bpy.context.view_layer
        light_group = view_layer.lightgroups.get(collection_name)
        if not light_group:
            light_group = view_layer.lightgroups.new(name=collection_name)
        light.lightgroup = light_group.name
```

### 13.9 Viewport Compositor Integration

```python
# lib/cinematic/compositor.py

def enable_viewport_compositor(scene, enable: bool = True):
    """
    Enable/disable viewport compositor for real-time preview.

    IMPORTANT: Viewport compositor must be enabled for
    real-time preview of lens effects.
    """
    scene.use_viewport_compositor = enable
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX Default Medium High Contrast'


def configure_viewport_preview(scene, config: dict):
    """
    Configure viewport compositor for draft preview.

    Only applies essential effects for real-time feedback.
    """
    node_tree = scene.node_tree
    if not node_tree:
        return

    # Disable heavy effects in viewport
    for node in node_tree.nodes:
        if node.type == 'GLARE':
            # Reduce glare quality for viewport
            node.quality = 'LOW' if config.get('draft_mode') else 'HIGH'
        if node.type == 'CURVE_RGB':
            # Simplify color correction for viewport
            pass  # Always fast
```

### 13.10 Output Color Space Configuration

```python
# lib/cinematic/render.py

OUTPUT_COLOR_SPACES = {
    'png': {
        'view_transform': 'Standard',
        'display_device': 'sRGB',
        'linear_colorspace': 'sRGB',  # PNG stores in sRGB
    },
    'exr': {
        'view_transform': 'Raw',      # Linear for compositing
        'display_device': 'None',
        'linear_colorspace': 'Linear Rec.709 (sRGB)',
    },
    'jpeg': {
        'view_transform': 'Standard',
        'display_device': 'sRGB',
        'linear_colorspace': 'sRGB',
    },
}


def configure_output_colorspace(scene, format: str):
    """Configure output color space for target format."""
    config = OUTPUT_COLOR_SPACES.get(format)
    if not config:
        raise ValueError(f"Unknown format: {format}")

    scene.view_settings.view_transform = config['view_transform']
    scene.display_settings.display_device = config['display_device']
```

### 13.11 Motion Path Procedural Specification

```python
# lib/cinematic/motion_path.py

def generate_orbit_path(config: dict) -> list[tuple]:
    """
    Generate procedural orbit camera path.

    ALGORITHM:
    1. Calculate orbit points around plumb bob
    2. Apply height variation if elevation range specified
    3. Generate quaternion look-at for each point
    4. Return list of (position, rotation, easing) tuples

    INPUTS:
    - center: [x, y, z] plumb bob position
    - radius: Distance from center
    - angle_range: [start, end] in degrees
    - elevation: Fixed height or [min, max] range
    - duration: Total frames
    - easing: ease_in, ease_out, ease_in_out, linear

    OUTPUTS:
    - List of (Vector, Quaternion, str) for each frame
    """
    import math
    from mathutils import Vector, Quaternion

    center = Vector(config['center'])
    radius = config['radius']
    angle_start, angle_end = config['angle_range']
    elevation = config.get('elevation', 0)
    duration = config['duration']
    easing = config.get('easing', 'linear')

    points = []

    for frame in range(duration + 1):
        t = frame / duration

        # Apply easing
        t = apply_easing(t, easing)

        # Calculate angle
        angle = math.radians(angle_start + (angle_end - angle_start) * t)

        # Calculate position
        x = center.x + radius * math.sin(angle)
        y = center.y - radius * math.cos(angle)
        z = center.z + elevation if isinstance(elevation, (int, float)) \
            else center.z + elevation[0] + (elevation[1] - elevation[0]) * t

        position = Vector((x, y, z))

        # Calculate look-at rotation (always face center)
        direction = (center - position).normalized()
        rotation = direction.to_track_quat('-Z', 'Y')

        points.append((position, rotation, easing))

    return points


def apply_easing(t: float, easing: str) -> float:
    """Apply easing function to normalized time."""
    if easing == 'linear':
        return t
    elif easing == 'ease_in':
        return t * t
    elif easing == 'ease_out':
        return 1 - (1 - t) * (1 - t)
    elif easing == 'ease_in_out':
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - pow(-2 * t + 2, 2) / 2
    return t
```

### 13.12 Plumb Bob Positioning Specification

```python
# lib/cinematic/plumb_bob.py

def calculate_plumb_bob(subject: bpy.types.Object, config: dict) -> Vector:
    """
    Calculate plumb bob position for camera orbit/focus.

    MODES:
    - auto: Center of subject bounding box + offset
    - manual: Use explicit coordinates
    - object: Use another object's location

    OFFSET: Applied in subject's local space, then converted to world

    FOCUS_DISTANCE: Calculated as distance from camera to plumb bob
    """
    from mathutils import Vector

    mode = config.get('mode', 'auto')
    offset = Vector(config.get('offset', [0, 0, 0]))

    if mode == 'auto':
        # Get bounding box center
        bbox = subject.bound_box
        center = Vector((
            sum(v[0] for v in bbox) / 8,
            sum(v[1] for v in bbox) / 8,
            sum(v[2] for v in bbox) / 8
        ))

        # Convert to world space
        world_center = subject.matrix_world @ center

        # Apply offset in world space
        return world_center + offset

    elif mode == 'manual':
        return Vector(config['position'])

    elif mode == 'object':
        target_name = config.get('object')
        target = bpy.data.objects.get(target_name)
        if target:
            return target.location + offset
        raise ValueError(f"Target object not found: {target_name}")


def calculate_focus_distance(camera_pos: Vector, plumb_bob: Vector) -> float:
    """Calculate focus distance from camera to plumb bob."""
    return (plumb_bob - camera_pos).length
```

### 13.13 Bloom Threshold Parameterization

```python
# lib/cinematic/lens_fx.py

def configure_bloom(glare_node, config: dict):
    """
    Configure bloom/glare effect.

    THRESHOLD: Luminance value above which bloom applies
    - 0.8: Only very bright areas bloom (default)
    - 0.6: Moderate bright areas bloom
    - 0.4: Most highlights bloom

    INTENSITY: Strength of bloom effect (0.0 - 1.0)
    RADIUS: Size of bloom glow (0.0 - 1.0)
    """
    glare_node.glare_type = 'BLOOM'
    glare_node.threshold = config.get('threshold', 0.8)
    glare_node.intensity = config.get('intensity', 0.2)
    glare_node.size = config.get('radius', 0.1)

    # Quality setting
    glare_node.quality = config.get('quality', 'MEDIUM')
```

### 13.14 Film Grain Implementation

```python
# lib/cinematic/lens_fx.py

def create_film_grain(node_tree, config: dict):
    """
    Create film grain effect using compositor.

    IMPLEMENTATION:
    - Use noise texture overlaid on image
    - Animate offset for temporal variation
    - Control grain size and intensity
    """
    import bpy

    nodes = node_tree.nodes
    links = node_tree.links

    # Create noise texture
    noise = nodes.new('CompositorNodeNoise')
    noise.noise_type = config.get('type', 'MULTIFRACTAL')
    noise.noise_scale = config.get('scale', 600)  # Fine grain
    noise.noise_depth = config.get('depth', 3)

    # Mix with image
    mix = nodes.new('CompositorNodeMixRGB')
    mix.blend_type = 'OVERLAY'
    mix.inputs['Fac'].default_value = config.get('intensity', 0.1)

    # Animate noise offset for temporal variation
    if config.get('animate', True):
        for frame in range(config.get('duration', 120)):
            noise.offset = (frame * 0.01, frame * 0.01)
            noise.keyframe_insert('offset', frame=frame)
```

### 13.15 Chromatic Aberration Implementation Order

```python
# CRITICAL: Chromatic aberration must come AFTER lens distortion

CHROMATIC_ABERRATION_ORDER = {
    'position': 2,  # After lens_distortion (1), before vignette (3)
    'reason': 'Must distort already-distorted RGB channels',
}

def create_chromatic_aberration(node_tree, config: dict):
    """
    Create chromatic aberration effect.

    IMPLEMENTATION:
    - Separate RGB channels
    - Apply different scale to each channel
    - R: +offset, G: no offset, B: -offset
    - Recombine channels
    """
    nodes = node_tree.nodes
    links = node_tree.links

    # Separate RGB
    separate = nodes.new('CompositorNodeSepRGBA')

    # Scale each channel differently
    scale_r = nodes.new('CompositorNodeScale')
    scale_g = nodes.new('CompositorNodeScale')
    scale_b = nodes.new('CompositorNodeScale')

    strength = config.get('strength', 0.002)
    scale_r.inputs['X'].default_value = 1 + strength
    scale_b.inputs['X'].default_value = 1 - strength

    # Combine RGB
    combine = nodes.new('CompositorNodeCombRGBA')

    # Link nodes
    links.new(separate.outputs['R'], scale_r.inputs['Image'])
    links.new(separate.outputs['G'], scale_g.inputs['Image'])
    links.new(separate.outputs['B'], scale_b.inputs['Image'])
    links.new(scale_r.outputs['Image'], combine.inputs['R'])
    links.new(scale_g.outputs['Image'], combine.inputs['G'])
    links.new(scale_b.outputs['Image'], combine.inputs['B'])
```

### 13.16 State Manager Interface Specification

```python
# lib/cinematic/state_manager.py
from typing import Protocol, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ShotState:
    """Complete state of a cinematic shot."""
    shot_name: str
    camera_transform: tuple[tuple[float, float, float], tuple[float, float, float]]
    camera_settings: dict[str, Any]
    light_transforms: dict[str, tuple]
    light_settings: dict[str, dict]
    backdrop_state: dict[str, Any]
    render_settings: dict[str, Any]
    timestamp: str
    version: int


class StateManager(Protocol):
    """Interface for shot state persistence."""

    def save(self, state: ShotState, path: Path) -> None:
        """Save state to YAML file."""
        ...

    def load(self, path: Path) -> ShotState:
        """Load state from YAML file."""
        ...

    def capture_current(self, shot_name: str) -> ShotState:
        """Capture current Blender state."""
        ...

    def restore(self, state: ShotState) -> None:
        """Restore Blender to captured state."""
        ...

    def diff(self, state_a: ShotState, state_b: ShotState) -> dict:
        """Compare two states, return differences."""
        ...


class FrameStore:
    """Frame store for iteration workflow."""

    def __init__(self, base_path: Path, max_versions: int = 50):
        self.base_path = base_path
        self.max_versions = max_versions

    def save_frame(self, state: ShotState) -> int:
        """Save state as new frame, return frame number."""
        ...

    def load_frame(self, shot_name: str, frame_num: int) -> ShotState:
        """Load frame by number."""
        ...

    def list_frames(self, shot_name: str) -> list[int]:
        """List available frame numbers."""
        ...

    def cleanup_old_frames(self) -> int:
        """Remove frames beyond max_versions, return count deleted."""
        ...
```

### 13.17 Template Resolution Trace Feature

```python
# lib/cinematic/template.py

def resolve_template(shot_config: dict, trace: bool = False) -> dict:
    """
    Resolve template inheritance chain.

    TRACE FEATURE:
    - Logs each template in inheritance chain
    - Shows which values came from which template
    - Useful for debugging shot configurations

    Returns fully resolved config with optional trace.
    """
    resolved = {}
    inheritance_chain = []

    def resolve_recursive(config: dict, depth: int = 0):
        if trace:
            inheritance_chain.append({
                'name': config.get('name', 'unnamed'),
                'depth': depth,
                'extends': config.get('extends'),
            })

        # First resolve parent if extending
        if 'extends' in config:
            parent_config = load_template(config['extends'])
            resolve_recursive(parent_config, depth + 1)

        # Then apply this config's values (override)
        deep_merge(resolved, config)

    resolve_recursive(shot_config)

    if trace:
        resolved['_trace'] = {
            'inheritance_chain': inheritance_chain,
            'resolution_order': [c['name'] for c in inheritance_chain],
        }

    return resolved


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base dictionary."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base
```

### 13.18 EXR Compression Settings

```yaml
# EXR output configuration for production

exr_settings:
  # Compression codec
  compression: ZIP           # ZIP (default), ZIPS, B44, B44A, DWAA, DWAB, PIZ, RLE, NONE

  # Depth
  depth: 32                  # 16 (half float), 32 (full float)

  # Multi-layer
  exr_codec: ZIP             # For multi-layer EXR

  # Preview (embedded in EXR)
  preview: true              # Generate preview image

  # Recommended by use case:
  recommendations:
    beauty_only:
      compression: DWAA      # Good for color data, lossy but fast
      depth: 16              # Half float sufficient

    multi_layer_compositing:
      compression: ZIP       # Lossless, good balance
      depth: 32              # Full float for passes

    archive_storage:
      compression: PIZ       # Best compression, lossless
      depth: 32
```

```python
# lib/cinematic/render.py

def configure_exr_output(scene, config: dict):
    """Configure EXR output settings."""
    scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
    scene.render.image_settings.exr_codec = config.get('compression', 'ZIP')
    scene.render.image_settings.color_depth = config.get('depth', '32')
    scene.render.image_settings.use_preview = config.get('preview', True)
```

### 13.19 Multi-Camera Alpha/Overlap Handling

```yaml
# Multi-camera composite configuration

multi_camera_composite:
  # Alpha handling
  alpha_mode: STRAIGHT       # STRAIGHT or PREMULTIPLIED

  # Overlap strategy
  overlap_handling:
    method: spacing          # spacing, blend, priority

    spacing:
      pixels: 20             # Gap between camera views
      background_color: [0, 0, 0, 0]

    blend:
      feather: 10            # Pixels of blend at edges

    priority:
      order: [hero_front, hero_side, detail_macro, overhead]

  # Labels
  labels:
    enabled: true
    font_size: 24
    color: [1, 1, 1, 0.8]
    position: bottom_left    # bottom_left, top_left, center
```

```python
# lib/cinematic/multi_camera.py

def composite_multi_camera(
    renders: list[bpy.types.Image],
    layout: str,
    config: dict
) -> bpy.types.Image:
    """
    Composite multiple camera renders into single image.

    HANDLING OVERLAP:
    - spacing: Add gap between views (default)
    - blend: Feather edges for smooth transition
    - priority: Z-order based on list order
    """
    import bpy
    from mathutils import Vector

    # Calculate layout positions
    positions = calculate_layout_positions(len(renders), layout, config)

    # Create composite canvas
    canvas_size = calculate_canvas_size(renders, positions, config)

    # Composite each render
    composite = create_empty_image(canvas_size)

    for render, pos in zip(renders, positions):
        # Handle alpha blending
        if config['alpha_mode'] == 'PREMULTIPLIED':
            render = unpremultiply_alpha(render)

        # Blend or place
        if config['overlap_handling']['method'] == 'blend':
            feather = config['overlap_handling']['blend']['feather']
            render = apply_edge_feather(render, feather)

        composite = blend_image(composite, render, pos)

    return composite
```

### 13.20 Color Management Preset Definitions

```yaml
# configs/cinematic/color/color_management_presets.yaml

presets:
  # Standard display
  srgb_standard:
    display_device: sRGB
    view_transform: Standard
    look: None
    exposure: 0.0
    gamma: 1.0

  # AgX default (recommended)
  agx_default:
    display_device: sRGB
    view_transform: AgX
    look: AgX Default Medium High Contrast
    exposure: 0.0
    gamma: 1.0

  # AgX for product shots
  agx_product:
    display_device: sRGB
    view_transform: AgX
    look: AgX Default Low Contrast
    exposure: 0.0
    gamma: 1.0

  # AgX for dramatic
  agx_dramatic:
    display_device: sRGB
    view_transform: AgX
    look: AgX Default High Contrast
    exposure: 0.0
    gamma: 1.0

  # ACEScg (if using ACES workflow)
  acescg:
    display_device: sRGB
    view_transform: ACEScg
    look: None
    exposure: 0.0
    gamma: 1.0

  # Filmic (legacy)
  filmic:
    display_device: sRGB
    view_transform: Filmic
    look: Filmic Medium High Contrast
    exposure: 0.0
    gamma: 1.0
```

```python
# lib/cinematic/color.py

def apply_color_management(scene, preset: str):
    """Apply color management preset to scene."""
    presets = load_presets('color_management_presets.yaml')
    config = presets.get(preset)

    if not config:
        raise ValueError(f"Unknown color management preset: {preset}")

    scene.display_settings.display_device = config['display_device']
    scene.view_settings.view_transform = config['view_transform']

    if config.get('look') and config['look'] != 'None':
        scene.view_settings.look = config['look']

    scene.view_settings.exposure = config['exposure']
    scene.view_settings.gamma = config['gamma']
```

---

## Part 14: Implementation Status

| Phase | Status | Description |
|-------|--------|-------------|
| 6.0 | Planned | Foundation |
| 6.1 | Planned | Camera System |
| 6.2 | Planned | Lighting System |
| 6.3 | Planned | Backdrop System |
| 6.4 | Planned | Color Pipeline |
| 6.5 | Planned | Animation System |
| 6.6 | Planned | Render Profiles |
| 6.7 | Planned | Support Systems |
| 6.8 | Planned | Shot Assembly |
| 6.9 | Planned | Integration & Testing |

See `REQUIREMENTS_CINEMATIC.md` for detailed acceptance criteria.
