# Universal Control Surface Parameter Architecture

**Design Philosophy:** Maximum flexibility through hierarchical inheritance, logical grouping, and complete mutability.

---

## Core Concept: The Design Token System

Every parameter in the system is a "Design Token" that can be:
1. **Inherited** from parent levels
2. **Overridden** at any level
3. **Animated/Morphed** between values
4. **Linked** to other parameters
5. **Driven** by external data (MIDI, automation, etc.)

---

## Hierarchy Levels

```
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 0: UNIVERSE (Global Constants)                           │
│  - Physical units (mm, degrees, RGB)                            │
│  - Blender scene settings                                       │
│  - Render engine configuration                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 1: DESIGN SYSTEM (Style Framework)                       │
│  - Color palettes                                               │
│  - Material definitions                                         │
│  - Typography system                                            │
│  - Lighting presets                                             │
│  - Animation curves                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 2: CONTROL FAMILY (Element Category)                     │
│  - Knobs                                                        │
│  - Faders/Sliders                                               │
│  - Buttons/Switches                                             │
│  - LEDs/Indicators                                              │
│  - Encoders                                                     │
│  - Displays                                                     │
│  - Jacks/Connectors                                             │
│  - Labels/Text                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 3: CONTROL VARIANT (Specific Style)                      │
│  - Chicken Head Knob                                            │
│  - Cylindrical Knob                                             │
│  - Channel Fader                                                │
│  - Momentary Button                                             │
│  - RGB LED                                                      │
│  - etc.                                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 4: INSTANCE (Individual Control)                          │
│  - Position in scene                                            │
│  - Unique overrides                                             │
│  - Current value/state                                          │
│  - Label text                                                   │
│  - Interaction mappings                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Parameter Groups (Logical Organization)

### Group 1: GEOMETRY (Shape & Form)

```yaml
geometry:
  # Base Shape
  profile: "chicken_head|cylindrical|domed|flattop|..."
  profile_curve: "bezier_points" # For custom profiles

  # Primary Dimensions
  base_diameter: 8-50
  height: 8-40

  # Profile-Specific Dimensions
  # (These activate based on profile selection)
  top_diameter: 4-45        # For tapered profiles
  skirt_diameter: 10-60     # For skirted profiles
  skirt_depth: 0-20         # How deep the skirt extends
  dome_radius: 0-25         # For domed profiles
  cone_angle: 0-45          # For conical profiles

  # Edge Treatments
  edge_radius_top: 0-10     # Fillet on top edge
  edge_radius_bottom: 0-10  # Fillet on bottom edge
  edge_chamfer_top: 0-5     # Chamfer alternative
  edge_chamfer_bottom: 0-5

  # Surface Features
  knurling:
    enabled: true/false
    depth: 0-2
    count: 10-100
    pattern: "straight|diamond|helical"
    angle: 0-90              # For helical

  ribbing:
    enabled: true/false
    count: 3-20
    depth: 0-2
    spacing: 1-5
    profile: "rounded|sharp|flat"

  grooves:
    enabled: true/false
    count: 1-10
    depth: 0-3
    width: 0-3
    position: "0.3,0.7"      # Relative positions

  # Indicator Geometry
  indicator:
    type: "line|dot|pointer|skirt_marker|none"
    length: 0-20
    width: 0-5
    depth: 0-2               # Engraved depth
    angle: 0                 # Rotation offset
    position: "top|side|skirt"

  # Shaft/Mounting
  shaft:
    type: "round|d_shaft|knurled|splined|hex"
    diameter: 6|6.35|8
    depth: 5-20
    set_screw_count: 0|1|2
    set_screw_position: "90,270"  # Degrees

  # Collet (for collet knobs)
  collet:
    enabled: true/false
    diameter: 0-15
    height: 0-10
    grip_pattern: "ridged|smooth|knurled"
```

### Group 2: MATERIAL (Surface Properties)

```yaml
material:
  # Base Material
  type: "plastic|metal|rubber|wood|glass|composite|led_emissive"

  # Physical Properties (PBR)
  base_color: "#RRGGBB"
  base_color_map: "path/to/texture"

  metallic: 0.0-1.0
  roughness: 0.0-1.0
  roughness_map: "path/to/texture"

  specular: 0.0-1.0
  specular_tint: 0.0-1.0

  normal_strength: 0.0-2.0
  normal_map: "path/to/texture"

  # Advanced Properties
  subsurface_weight: 0.0-1.0    # For plastics/skin
  subsurface_radius: "R,G,B"    # SSS color spread
  subsurface_color: "#RRGGBB"

  coat_weight: 0.0-1.0          # Clearcoat
  coat_roughness: 0.0-1.0
  coat_normal: "path/to/texture"

  sheen_weight: 0.0-1.0         # For fabrics/velvet
  sheen_roughness: 0.0-1.0
  sheen_tint: 0.0-1.0

  anisotropic: 0.0-1.0          # For brushed metals
  anisotropic_rotation: 0.0-1.0

  # Transmission (for glass/clear plastic)
  transmission_weight: 0.0-1.0
  transmission_color: "#RRGGBB"
  transmission_depth: 0-100

  # Emission (for LEDs/backlit elements)
  emission_color: "#RRGGBB"
  emission_strength: 0.0-100.0
  emission_map: "path/to/texture"

  # Index of Refraction
  ior: 1.0-2.5

  # Texture Transforms
  texture_scale: "1.0,1.0"
  texture_rotation: 0-360
  texture_offset: "0.0,0.0"

  # Material Variants (for multi-part controls)
  variants:
    body:
      inherit: "default"
      overrides: {...}
    cap:
      inherit: "default"
      overrides: {...}
    indicator:
      inherit: "default"
      overrides: {...}
    ring:
      inherit: "metal_chrome"
      overrides: {...}
```

### Group 3: COLOR SYSTEM (Palette & Theming)

```yaml
color_system:
  # Semantic Colors (used throughout)
  semantics:
    primary: "#RRGGBB"        # Main accent
    secondary: "#RRGGBB"      # Secondary accent
    background: "#RRGGBB"     # Panel background
    foreground: "#RRGGBB"     # Text/indicators
    muted: "#RRGGBB"          # Disabled/subtle
    accent: "#RRGGBB"         # Highlight
    danger: "#RRGGBB"         # Warning/error
    success: "#RRGGBB"        # Active/safe

  # Control-Specific Colors
  controls:
    knob_body: "semantics.primary"
    knob_indicator: "semantics.foreground"
    knob_cap: "semantics.secondary"
    button_default: "semantics.background"
    button_active: "semantics.accent"
    led_off: "semantics.muted"
    led_on: "semantics.success"

  # Functional Colors (by parameter type)
  functions:
    gain: "#RRGGBB"           # Usually red/warm
    eq: "#RRGGBB"             # Usually blue
    dynamics: "#RRGGBB"       # Usually yellow/orange
    aux: "#RRGGBB"            # Usually green
    master: "#RRGGBB"         # Usually distinct

  # State Colors
  states:
    default: "semantics.background"
    hover: "semantics.muted"
    active: "semantics.accent"
    disabled: "semantics.muted"
    error: "semantics.danger"
    selected: "semantics.success"

  # Gradients
  gradients:
    panel_gradient:
      type: "linear|radial"
      colors: ["#RRGGBB", "#RRGGBB"]
      positions: [0.0, 1.0]
      angle: 90

  # Color Modulation
  modulation:
    temperature: -100 to 100    # Warm/cool shift
    saturation: -100 to 100     # Saturation adjustment
    brightness: -100 to 100     # Brightness adjustment
    contrast: -100 to 100       # Contrast adjustment
```

### Group 4: TYPOGRAPHY (Text & Labels)

```yaml
typography:
  # Font System
  fonts:
    primary:
      family: "Helvetica"
      weight: "regular|bold|light|..."
      style: "normal|italic|oblique"
    secondary:
      family: "Futura"
      weight: "bold"
    mono:
      family: "Roboto Mono"
      weight: "regular"

  # Label Styles
  labels:
    default:
      font: "primary"
      size: 8                  # mm
      color: "color_system.semantics.foreground"
      alignment: "center"
      vertical_alignment: "middle"
      letter_spacing: 0
      line_spacing: 1.2

    small:
      inherit: "default"
      size: 6

    large:
      inherit: "default"
      size: 12

    value:
      font: "mono"
      size: 10

  # Label Placement
  placement:
    position: "above|below|left|right|overlay"
    offset: 2                  # mm from control
    rotation: 0                # Degrees
    follow_curve: true/false   # For curved labels

  # Label Rendering
  rendering:
    method: "text_object|decal|geometry|shader"
    depth: 0.1                 # For embossed/debossed
    bevel: 0.02                # For 3D text
    extrude: 0.1               # For raised text
```

### Group 5: ANIMATION (Motion & Behavior)

```yaml
animation:
  # Rotation Animation (for knobs)
  rotation:
    range: 270|300|320|360    # Degrees of rotation
    direction: "cw|ccw"        # Clockwise or counter
    mapping: "linear|log|anti_log|custom"
    custom_curve: "bezier_points"

    # Detent Feel
    detent:
      enabled: true/false
      count: 0-100
      force: 0-10              # Resistance strength
      positions: "custom_list" # For non-uniform detents

  # Value Animation
  value:
    easing: "linear|ease_in|ease_out|ease_in_out|bounce|elastic|custom"
    duration: 0-1000           # ms
    custom_curve: "bezier_points"

  # State Animation
  state:
    press:
      travel: 0.5-5            # mm
      duration: 0-100          # ms
      easing: "ease_out"
    release:
      duration: 0-100
      easing: "ease_out"

  # LED Animation
  led:
    pulse:
      enabled: true/false
      speed: 0.1-10            # Hz
      depth: 0-1               # Brightness variation
      shape: "sine|square|triangle|sawtooth"
    flash:
      enabled: true/false
      duration: 50-500         # ms
      color: "#RRGGBB"

  # Morph Animation (style transitions)
  morph:
    geometry_duration: 0-2000  # ms
    material_duration: 0-1000  # ms
    stagger: 0-100             # ms between elements
    stagger_pattern: "random|sequential|distance|custom"
    easing: "ease_in_out"
```

### Group 6: LIGHTING (Scene Illumination)

```yaml
lighting:
  # Preset
  preset: "studio|ambient|dramatic|neon|natural|custom"

  # Key Light
  key_light:
    enabled: true/false
    type: "sun|area|spot|point"
    intensity: 0-1000
    color: "#RRGGBB" or "color_temperature"
    color_temperature: 2000-10000  # Kelvin
    angle: 0-360
    elevation: 0-90
    size: 0-100                # For soft shadows
    shadow_softness: 0-1

  # Fill Light
  fill_light:
    enabled: true/false
    intensity_ratio: 0-1       # Relative to key
    color: "#RRGGBB"
    angle: 0-360
    elevation: 0-90

  # Rim/Back Light
  rim_light:
    enabled: true/false
    intensity: 0-500
    color: "#RRGGBB"
    angle: 0-360

  # Ambient
  ambient:
    intensity: 0-2
    color: "#RRGGBB"
    hdri_map: "path/to/hdri"
    hdri_rotation: 0-360
    hdri_strength: 0-2

  # Environment
  environment:
    type: "hdri|solid_color|gradient|sky"
    color: "#RRGGBB"
    gradient_top: "#RRGGBB"
    gradient_bottom: "#RRGGBB"
```

### Group 7: INTERACTION (User Feedback)

```yaml
interaction:
  # Haptic Feedback
  haptic:
    enabled: true/false
    press_intensity: 0-1
    release_intensity: 0-1
    detent_intensity: 0-1

  # Visual Feedback
  visual:
    hover:
      enabled: true/false
      highlight_color: "#RRGGBB"
      highlight_intensity: 0-1
      scale_factor: 1.0-1.2
    active:
      enabled: true/false
      color: "#RRGGBB"
      glow_intensity: 0-5
    disabled:
      opacity: 0.3-1.0
      grayscale: true/false

  # Sound Feedback
  sound:
    enabled: true/false
    click: "path/to/sound"
    detent: "path/to/sound"
    volume: 0-1

  # Value Display
  value_display:
    enabled: true/false
    position: "above|below|tooltip"
    format: "number|percentage|db|custom"
    decimals: 0-3
    update_rate: 0-60          # FPS
```

### Group 8: LAYOUT (Arrangement & Spacing)

```yaml
layout:
  # Grid System
  grid:
    enabled: true/false
    spacing_x: 10-50           # mm
    spacing_y: 10-50
    snap: true/false
    visible: true/false

  # Alignment
  alignment:
    horizontal: "left|center|right|justify"
    vertical: "top|middle|bottom"

  # Spacing
  spacing:
    between_controls: 5-30     # mm
    margin_top: 0-20
    margin_bottom: 0-20
    margin_left: 0-20
    margin_right: 0-20

  # Grouping
  grouping:
    enabled: true/false
    border_style: "line|box|none"
    border_color: "#RRGGBB"
    border_width: 0-2
    padding: 5-20
    background_color: "#RRGGBB"
    background_opacity: 0-1
    label_position: "top|left|inside"

  # Responsive
  responsive:
    scale_with_distance: true/false
    min_size: 0.5
    max_size: 2.0
```

### Group 9: RENDER (Output Settings)

```yaml
render:
  # Resolution
  resolution:
    width: 1920
    height: 1080
    scale: 50-200              # %

  # Sampling
  samples: 1-4096
  denoiser: "none|optix|intel"

  # Output
  format: "png|jpeg|exr|webp"
  quality: 1-100               # For lossy formats
  color_depth: "8|16|32"
  color_space: "sRGB|ACES|Linear"

  # Passes/Layers
  passes:
    beauty: true
    diffuse: false
    specular: false
    normal: false
    depth: false
    object_index: false
    material_index: false

  # Camera
  camera:
    type: "perspective|orthographic|panoramic"
    focal_length: 10-200
    f_stop: 1.4-22
    focus_distance: 0-1000
    sensor_size: "auto|custom"

  # Background
  background:
    type: "transparent|color|hdri|gradient"
    color: "#RRGGBB"
    transparent: true/false
```

---

## Style Preset Schema

```yaml
# Example: Neve 1073 Style Preset
name: "Neve 1073"
version: "1.0"
category: "console"
era: "1970s"
description: "Classic Neve 1073 preamp/EQ module"

inherit: "console_base"  # Inherit from base console style

# Override/Define at each group level
global:
  color_system:
    semantics:
      primary: "#1A1A1A"
      secondary: "#2A2D2E"
      foreground: "#FFFFFF"
      accent: "#E53935"
    functions:
      gain: "#E53935"
      eq: "#1E88E5"
      aux: "#43A047"

  lighting:
    preset: "studio_warm"
    key_light:
      intensity: 300
      color_temperature: 4500

  typography:
    labels:
      default:
        font: "Helvetica Condensed"
        size: 6

knobs:
  geometry:
    profile: "chicken_head"
    base_diameter: 22
    height: 18
    skirt_diameter: 28
    skirt_depth: 8
    edge_radius_bottom: 1

    indicator:
      type: "pointer"
      length: 12
      position: "side"

  material:
    type: "plastic"
    base_color: "color_system.semantics.primary"
    roughness: 0.6
    subsurface_weight: 0.2

  color_system:
    controls:
      knob_body: "#1A1A1A"
      knob_indicator: "#FFFFFF"

  animation:
    rotation:
      range: 300
      direction: "cw"
      detent:
        enabled: false

buttons:
  geometry:
    shape: "square"
    width: 10
    depth_unpressed: 8

  material:
    type: "plastic"
    base_color: "color_system.semantics.primary"

  color_system:
    states:
      default: "#1A1A1A"
      active: "color_system.functions.gain"

faders:
  geometry:
    type: "channel"
    travel_length: 100

  material:
    type: "metal"
    base_color: "#2A2D2E"
    metallic: 0.9
    roughness: 0.3

panel:
  geometry:
    width: 50
    height: 300
    corner_radius: 0

  material:
    type: "metal"
    base_color: "#2A2D2E"
    metallic: 0.95
    roughness: 0.4

  color_system:
    background: "#2A2D2E"
```

---

## Morphing System

### Morph Definition

```yaml
morph:
  source: "Neve 1073"
  target: "SSL 4000 E"

  # Global morph factor (0.0 = source, 1.0 = target)
  factor: 0.5

  # Per-group morph factors (override global)
  groups:
    geometry: 0.5
    material: 0.3
    color_system: 0.7
    animation: 0.0

  # Per-control morph factors
  controls:
    "gain_knob": 0.8
    "eq_knobs": 0.2

  # Animation settings
  animation:
    duration: 1000           # ms
    easing: "ease_in_out"
    stagger: 20              # ms between controls
    stagger_pattern: "distance_from_center"
```

### Morphable Properties

| Property Type | Morph Method |
|--------------|--------------|
| **Scalar** (diameter, height) | Linear interpolation |
| **Color** (RGB) | Color space interpolation (LAB/HSV) |
| **Vector** (position, rotation) | Linear or spherical interpolation |
| **Profile** (shape) | Vertex interpolation or blend shapes |
| **Material** | Property-by-property interpolation |
| **Boolean** | Threshold-based (morph at 0.5) |
| **Enum** (profile type) | Weighted blend or threshold |

---

## Implementation Notes

### Blender Integration

```python
# Example: Parameter binding to Blender
class ControlSurfaceParameters(bpy.types.PropertyGroup):
    # Geometry
    profile: EnumProperty(items=PROFILE_TYPES)
    base_diameter: FloatProperty(min=8, max=50, default=22)
    height: FloatProperty(min=8, max=40, default=18)

    # Material
    base_color: FloatVectorProperty(
        subtype='COLOR',
        min=0, max=1, size=4,
        default=(0.1, 0.1, 0.1, 1.0)
    )
    metallic: FloatProperty(min=0, max=1, default=0.0)
    roughness: FloatProperty(min=0, max=1, default=0.5)

    # Animation
    rotation_range: FloatProperty(min=180, max=360, default=270)

    # Morphing
    morph_factor: FloatProperty(min=0, max=1, default=0.0)
    morph_target: StringProperty(default="")
```

### File Structure

```
control_surface_system/
├── presets/
│   ├── consoles/
│   │   ├── neve_1073.yaml
│   │   ├── ssl_4000_e.yaml
│   │   └── api_2500.yaml
│   ├── synths/
│   │   ├── moog_minimoog.yaml
│   │   ├── roland_808.yaml
│   │   └── sequential_prophet5.yaml
│   └── pedals/
│       ├── boss_compact.yaml
│       └── mxr_classic.yaml
├── profiles/
│   ├── knobs/
│   │   ├── chicken_head.svg
│   │   ├── cylindrical.svg
│   │   └── domed.svg
│   └── faders/
│       ├── channel.svg
│       └── mini.svg
├── materials/
│   ├── plastic.yaml
│   ├── metal.yaml
│   └── rubber.yaml
├── lighting/
│   ├── studio.yaml
│   ├── dramatic.yaml
│   └── ambient.yaml
└── core/
    ├── parameter_system.py
    ├── geometry_generator.py
    ├── material_system.py
    └── morph_engine.py
```

---

*This architecture enables complete flexibility while maintaining logical organization and efficient inheritance.*
