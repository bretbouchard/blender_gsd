# Blender GSD Framework - Cinematic System Requirements

**Version**: 1.0
**Status**: Approved
**Related**: CINEMATIC_SYSTEM_DESIGN.md

---

## REQ-CINE-01: Cinematic System Foundation
**Priority**: P0
**Status**: Complete ✅
**Completed**: 2026-02-18

The framework MUST provide a complete cinematic rendering system with modular, resumable, and drop-in ready components.

### Core Capabilities
- Camera system with real-world lenses and movements
- Lighting rig system with presets and gels
- Backdrop and environment system
- Color pipeline with LUT management
- Animation system for camera and object movement
- Render profile system with quality tiers

### Acceptance Criteria
- [x] `lib/cinematic/` module structure created
- [x] Configuration directory structure established
- [x] State persistence framework implemented
- [ ] All REQ-CINE-* requirements have corresponding implementation (foundation in place, subsystems pending)

---

## REQ-CINE-CAM: Camera System
**Priority**: P0
**Status**: Planned

A comprehensive camera system supporting real-world lenses, sensor sizes, and camera rigs.

### Lens System
- Focal length presets (14mm ultra-wide to 135mm telephoto, plus macro)
- Sensor size presets (Full Frame, APS-C, M4/3, Cinema formats)
- Aperture control with f-stop range f/0.95 to f/22
- Bokeh shape control (circular, hexagonal, octagonal)
- Focus distance control (auto and manual)

### Lens Imperfections
- Lens flare system with customizable intensity and streaks
- Vignette control (intensity, radius)
- Chromatic aberration (strength, radial)
- Ghosting and bloom effects
- Lens-specific character presets (Cooke S4, ARRI Master Prime, vintage Helios)

### Camera Rigs
- Tripod (static with pan/tilt)
- Dolly (linear track)
- Crane (3D arc movement)
- Steadicam (smoothed handheld simulation)
- Drone (free-flight path)

### Multi-Camera Support
- Grid layouts (2x2, 3x3)
- Horizontal/vertical layouts
- Custom layouts
- Per-camera settings in single render
- Labels and spacing control

### Acceptance Criteria
- [ ] Camera transform system implemented
- [ ] 10+ lens presets available
- [ ] 5+ sensor presets available
- [ ] 5+ camera rig types implemented
- [ ] Multi-camera composite rendering works
- [ ] Lens imperfection system operational

---

## REQ-CINE-PLUMB: Plumb Bob System
**Priority**: P1
**Status**: Planned

A target system defining the visual center of interest for camera orbit, focus, and dolly operations.

### Positioning Specification
**Modes:**
- **auto**: Center of subject bounding box + offset, converted to world space
- **manual**: Use explicit world coordinates
- **object**: Use another object's location + offset

**Algorithm (auto mode):**
1. Get subject bounding box vertices
2. Calculate center: (sum of all vertices) / 8
3. Convert to world space via matrix_world
4. Apply offset in world space

**Focus Distance:**
- Calculated as Euclidean distance from camera position to plumb bob
- Used for DoF focus distance parameter

### Features
- Auto-calculation from subject bounding box
- Manual offset from object center (in world space)
- Object-based targeting
- Automatic focus distance calculation
- Integration with all camera rigs

### Acceptance Criteria
- [ ] Plumb bob position calculated correctly from bounding box
- [ ] Manual override works with offset specification
- [ ] Camera orbit uses plumb bob as pivot point
- [ ] Focus distance derived from camera-to-plumb-bob distance
- [ ] Dolly moves target plumb bob

---

## REQ-CINE-LIGHT: Lighting System
**Priority**: P0
**Status**: Planned

A modular lighting system with preset rigs, individual light control, and HDRI integration.

### Light Types
- Area lights (rectangle, disk, ellipse)
- Spot lights (cone, gobo support)
- Point lights
- Sun lights
- HDRI environment lighting

### Light Properties
- Intensity (power in watts, exposure compensation)
- Color (RGB or Kelvin temperature)
- Shape and size (for area lights)
- Softness (radius, spread)
- Shadow control (enabled, softness, max distance)
- Gel system (CTB, CTO, creative colors, diffusion grades)

### Light Linking Configuration (HIGH Priority)
- Selective illumination via collections
- Blender 4.0+: `light.light_linking.receiver_collection`
- Legacy: Render layers with light groups
- Use cases: Key light on subject only, rim light separation

### Lighting Rigs
- Three-point soft (classic studio)
- Three-point hard (dramatic)
- Product hero (overhead + fill cards)
- Product dramatic (spot + rim)
- Studio high-key (bright, minimal shadows)
- Studio low-key (dark, selective lighting)
- Console-specific presets (overhead, angled)

### HDRI System
- Multi-path search (project local, GSD bundled, external library)
- Auto-download from public sources (Polyhaven)
- Exposure and rotation control
- Background visibility toggle

### Acceptance Criteria
- [ ] All 5 light types supported
- [ ] 8+ lighting rig presets available
- [ ] Gel system with CTB/CTO/diffusion
- [ ] HDRI system with search paths
- [ ] Individual light override system works
- [ ] Light linking configured for selective illumination

---

## REQ-CINE-ENV: Backdrop System
**Priority**: P1
**Status**: Planned

A system for creating product photography backdrops and environments.

### Backdrop Types
- Infinite curve (seamless sweep)
- Gradient (linear, radial, angular)
- HDRI dome
- Mesh environments (pre-built scenes)

### Infinite Curve (Procedural Specification)
**Algorithm:**
1. Calculate floor extent from subject bounding box
2. Generate smooth curve from floor to wall (quadratic bezier)
3. Create mesh with proper UVs for gradient shading
4. Apply shadow catcher material if enabled

**Parameters:**
- radius: Distance from subject to curve start (meters)
- curve_height: Height of vertical portion (meters)
- curve_segments: Resolution of curve (default: 32)
- shadow_catcher: Enable shadow catching

**Output:**
- Blender mesh object named "gsd_backdrop_curve"
- Material "gsd_backdrop_mat" with Z-position gradient

### Shadow Catcher Contract
**Geometry Requirements:**
- Single-sided faces (use backface culling)
- No overlapping geometry
- Proper UV unwrapping (for gradient materials)

**Material Requirements:**
- shadow_method: CLIP (not HASHED or STOCHASTIC)
- alpha_blend: true
- backface_culling: true

**Render Requirements:**
- film_transparent: true (enable alpha in output)
- passes_required: [shadow, combined]

### Acceptance Criteria
- [ ] Infinite curve generation works with bounding box
- [ ] 5+ backdrop presets available
- [ ] Shadow catcher mode functions with proper alpha
- [ ] HDRI backdrop integration works

---

## REQ-CINE-LUT: Color Pipeline
**Priority**: P1
**Status**: Planned

Complete color management system with LUT support and exposure control.

### Color Management
- Working space selection (AgX recommended, ACEScg, Filmic, Standard)
- View transform presets
- Look development system
- Per-shot color overrides (exposure, gamma, saturation, contrast)

### Color Management Presets
- **srgb_standard**: Basic sRGB display
- **agx_default**: AgX Medium High Contrast (recommended)
- **agx_product**: AgX Low Contrast (product shots)
- **agx_dramatic**: AgX High Contrast (dramatic shots)
- **acescg**: ACEScg workflow
- **filmic**: Legacy Filmic (fallback)

### LUT Technical Specifications
**Technical LUTs** (65³ precision):
- Rec.709 to sRGB display transform
- Linear to sRGB
- ACEScg to Rec.709
- Linear to Log encoding

**Film LUTs** (33³ sufficient):
- Kodak 2383 (classic print film)
- Fuji 3510 (cool tones)
- Cineon (log film scan look)
- Intensity blend control (default 0.8)

### LUT Categories
- Technical (Rec.709, sRGB, P3, ACES) - Applied EARLY (stage 8)
- Film emulation (Kodak 2383, Fuji 3510, Vision3) - Applied LATE (stage 9)
- Creative (cinematic looks, product-specific) - Applied LATE (stage 9)

### Exposure Lock
- Luminance targeting (18% gray standard)
- Highlight protection (max 0.95)
- Shadow protection (min 0.02)
- Auto-adjust key light to maintain exposure

### Acceptance Criteria
- [ ] Color management system implemented
- [ ] Color management presets available (agx_default, agx_product, etc.)
- [ ] 5+ technical LUTs available (65³ precision)
- [ ] 5+ film emulation LUTs available (33³ precision)
- [ ] Exposure lock maintains consistent brightness
- [ ] LUT intensity blend control works
- [ ] Technical LUTs applied at stage 8, Creative LUTs at stage 9

---

## REQ-CINE-ANIM: Animation System
**Priority**: P1
**Status**: Planned

Unified animation system for camera movements, object animation, and timeline management.

### Camera Moves
- Orbit (axis, angle range, duration)
- Dolly (direction, distance)
- Crane (elevation, arc)
- Push-in (combined dolly + focal length change)
- Rack focus (near/far targets)
- Path following (spline, bezier)

### Animation Presets
- orbit_90, orbit_180, orbit_360
- dolly_in, dolly_out
- push_in
- crane_up
- reveal (sequence of moves)

### Unified Timeline
- Single timeline for camera + object animation
- Track-based system with ranges
- Easing curves (ease_in, ease_out, ease_in_out, linear)
- Audio sync with beat markers

### Turntable System
- Object rotation mode (rotate subject, not camera)
- Configurable duration and rotation axis

### Acceptance Criteria
- [ ] 8+ camera move presets available
- [ ] Track-based timeline implemented
- [ ] Easing curves work correctly
- [ ] Turntable rotation functions
- [ ] Camera and object animations can be synchronized

---

## REQ-CINE-PATH: Motion Path System
**Priority**: P2
**Status**: Planned

Procedural motion path generation for camera movements.

### Path Types
- Linear
- Spline (cubic interpolation)
- Bezier (control points)

### Procedural Orbit Path Specification
**Algorithm:**
1. Calculate orbit points around plumb bob center
2. Apply height variation if elevation range specified
3. Generate quaternion look-at for each point
4. Return list of (position, rotation, easing) tuples

**Inputs:**
- center: [x, y, z] plumb bob position
- radius: Distance from center
- angle_range: [start, end] in degrees
- elevation: Fixed height or [min, max] range
- duration: Total frames
- easing: ease_in, ease_out, ease_in_out, linear

**Outputs:**
- List of (Vector, Quaternion, easing) for each frame

### Easing Functions
- linear: t (no modification)
- ease_in: t² (quadratic acceleration)
- ease_out: 1 - (1-t)² (quadratic deceleration)
- ease_in_out: Combined quadratic

### Path Features
- Control point specification
- Per-point easing
- Look-at constraint (always face subject/plumb bob)
- Path presets (orbit_90, dolly_in, crane_up)

### Acceptance Criteria
- [ ] Path generation from control points works
- [ ] Spline and bezier interpolation implemented
- [ ] Look-at constraint maintains subject framing
- [ ] Easing functions produce smooth motion

---

## REQ-CINE-RENDER: Render System
**Priority**: P0
**Status**: Planned

Extended render system with quality tiers, output formats, and render passes.

### Engine Configuration (CRITICAL)
- **BLENDER_EEVEE_NEXT** for draft/preview (NOT deprecated 'BLENDER_EEVEE')
- **CYCLES** for production/archive
- **BLENDER_WORKBENCH** for viewport capture

### Quality Tiers with Resolution Scaling
- Viewport capture (instant, 512px, scale 100%, Workbench)
- EEVEE Next draft (seconds, 1024px effective, 50% scale, 16 samples)
- Cycles preview (minutes, 2048px, 100% scale, 64 samples, adaptive threshold 0.02)
- Cycles production (hours, 4096px, 100% scale, 256 samples, adaptive threshold 0.01)
- Cycles archive (overnight, 4096px, 100% scale, 1024+ samples, adaptive threshold 0.005)

### Output Formats
- PNG (web, preview, sRGB colorspace)
- EXR multi-layer (production, Linear Rec.709, ZIP compression, 32-bit depth)
- JPEG (delivery, sRGB colorspace)

### Render Passes (with API Configuration)
- Beauty (always enabled)
- Diffuse (direct, indirect, color) - `use_pass_diffuse_*`
- Glossy (direct, indirect, color) - `use_pass_glossy_*`
- Transmission - `use_pass_transmission_*`
- Emission - `use_pass_emit`
- **Cryptomatte (object/material/asset)** - `use_pass_cryptomatte_object` (CRITICAL: must enable)
- Depth (Z) - `use_pass_z`
- Normal - `use_pass_normal`
- Vector (motion) - `use_pass_vector`

### Denoiser Selection (Hardware-Aware)
- OptiX (NVIDIA GPUs with RTX)
- OpenImageDenoise (CPU or Apple Silicon Metal)
- Automatic selection based on available hardware

### Batch Rendering
- Render queue with task list
- Dependency management
- Parallel job control
- Resume on failure

### Metadata
- Embed shot info in EXR outputs
- Include camera settings, lighting setup, render time, version info

### Acceptance Criteria
- [ ] 5 quality tier presets available
- [ ] All 3 output formats supported
- [ ] All render passes available
- [ ] Batch rendering with dependencies works
- [ ] Metadata embedding functions

---

## REQ-CINE-SHUFFLE: Shuffler System
**Priority**: P2
**Status**: Planned

Automatic shot variation generator from parameter ranges.

### Features
- Random, grid, and custom sampling modes
- Reproducible randomness with seed control
- Per-parameter range and sample count
- Automatic directory organization

### Shufflable Parameters
- Camera angle, elevation, distance
- Lighting key angle, intensity
- Backdrop variations

### Acceptance Criteria
- [ ] Random and grid modes implemented
- [ ] Reproducible with seed
- [ ] Output organized by variation parameters

---

## REQ-CINE-FRAME: Frame Store System
**Priority**: P2
**Status**: Planned

State capture and comparison system for iteration workflow.

### Features
- Automatic capture on render
- Complete shot state serialization
- Thumbnail generation
- Version limit with auto-cleanup

### Operations
- Save current state as new frame
- Load frame by number
- Side-by-side comparison
- Parameter diff display
- Revert to frame

### Acceptance Criteria
- [ ] Frame capture preserves complete state
- [ ] Thumbnail generation works
- [ ] Comparison view available
- [ ] Diff display shows parameter changes

---

## REQ-CINE-DEPTH: Depth Layer System
**Priority**: P2
**Status**: Planned

Automatic depth layering with parallax-aware camera moves.

### Features
- Foreground, midground, background layers
- Auto-assignment by bounding box
- Per-layer blur simulation
- Parallax response ratios

### Parallax Animation
- Differential camera movement per layer
- Configurable response ratios

### Acceptance Criteria
- [ ] Layer assignment works
- [ ] Parallax animation creates depth effect

---

## REQ-CINE-COMPOSE: Composition Guides
**Priority**: P3
**Status**: Planned

In-viewport composition overlays for shot framing.

### Guide Types
- Rule of thirds
- Golden ratio (phi grid)
- Center cross
- Safe areas (title/action)
- Diagonals
- Custom guides (circles, lines)

### Acceptance Criteria
- [ ] Standard guides available
- [ ] Custom guides supported
- [ ] Never visible in rendered output

---

## REQ-CINE-GIMP: Lens Imperfections
**Priority**: P2
**Status**: Planned

Procedural lens imperfection system for realistic rendering.

### Compositor Pipeline Order (CRITICAL)
Effects MUST be applied in this exact order for physically-correct results:

1. **Geometric Distortions** (before color)
   - Lens distortion (barrel/pincushion)
   - Chromatic aberration (RGB channel separation)

2. **Luminance Adjustments**
   - Vignette (edge darkening)
   - Exposure adjust

3. **Glow/Bloom Effects**
   - Bloom (bright area glow)
   - Glare (lens flare)

4. **Color Grading**
   - Color correction
   - Technical LUT (color space transforms - EARLY)
   - Creative LUT (film looks - LATE)

5. **Film Effects** (final)
   - Film grain (add last)

### LUT Application Points (CRITICAL)
- **Technical LUTs** (stage 8): Color space conversion, display transforms
  - Applied EARLY before creative grading
  - Examples: rec709_to_srgb, linear_to_log

- **Creative LUTs** (stage 9): Film looks, artistic grades
  - Applied LATE after color correction
  - Examples: kodak_2383, fuji_3510, cinematic_tealorange

### Effects (Compositor-based)
- Bloom (threshold 0.8 default, intensity, radius)
- Lens flare (intensity, streaks, streak angle)
- Ghosting (count, falloff)
- Chromatic aberration (strength 0.002 default, radial)
- Vignette (intensity 0.3 default, radius 0.8)
- Film grain (scale, intensity, animated offset)

### Lens Character Presets
- Cooke S4 (warm, organic)
- ARRI Master Prime (clean, sharp)
- Vintage Helios (swirly bokeh, heavy flare)
- Clean (minimal imperfections)

### Acceptance Criteria
- [ ] All effects implemented as compositing nodes
- [ ] Effects applied in correct pipeline order
- [ ] LUTs applied at correct stage (technical early, creative late)
- [ ] 4+ lens character presets available
- [ ] Effects configurable individually

---

## REQ-CINE-ISO: Isometric View System
**Priority**: P2
**Status**: Planned

Dedicated isometric and orthographic camera system for technical documentation and product catalogs.

### Orthographic Camera Mode
- Camera type: ORTHO (not PERSP)
- Orthographic scale control (zoom via scale, not distance)
- No perspective distortion - parallel lines stay parallel

### Isometric Angle Presets
- **True Isometric**: 35.264° elevation, 45° rotation (mathematically correct)
- **Dimetric 2:1**: 30° elevation, 45° rotation (classic pixel art style)
- **Trimetric**: Custom angles for dramatic effect
- **Plan View**: 90° elevation (top-down orthographic)
- **Front/Side/Back**: 0° elevation, cardinal rotations

### Grid Overlay System
- Isometric grid overlay (aligns with angle preset)
- Orthographic grid (square)
- Custom grid spacing
- Grid visibility toggle (viewport only, never in render)

### Flat Lighting Presets
- **flat_overhead**: Single overhead area light, no shadows
- **flat_softbox**: Large softbox above, minimal contrast
- **technical_documentation**: Even illumination, clear visibility
- **product_catalog**: Clean, consistent lighting for catalogs

### Pixel-Perfect Alignment
- Render resolution locked to grid units
- Anti-aliasing control for pixel art workflows
- Edge sharpening for crisp edges
- Snap-to-grid camera positioning

### Use Cases
- Technical documentation showing knob/control layouts
- Product catalogs with consistent orthographic views
- UI design elements (isometric icons)
- Equipment diagrams and schematics

### Acceptance Criteria
- [ ] Orthographic camera mode works with isometric presets
- [ ] 5+ isometric angle presets available
- [ ] Grid overlay system functional
- [ ] Flat lighting presets produce even illumination
- [ ] Renders show no perspective distortion

---

## REQ-CINE-TEMPLATE: Shot Template System
**Priority**: P1
**Status**: Planned

Template inheritance for shot configurations.

### Features
- Abstract base templates
- Extends/override pattern
- Multi-level inheritance
- Override at any parameter level

### Acceptance Criteria
- [ ] Template inheritance works
- [ ] Overrides apply correctly
- [ ] Abstract templates cannot render directly

---

## REQ-CINE-SHOT: Shot Assembly System
**Priority**: P0
**Status**: Planned

Complete shot assembly combining all cinematic elements.

### Features
- Single YAML defines complete shot
- Subject specification
- Camera configuration
- Lighting configuration
- Backdrop configuration
- Color configuration
- Render configuration
- Animation configuration (optional)

### Resume/Edit System
- Load from frame store
- Partial parameter override
- State persistence

### Acceptance Criteria
- [ ] Single YAML produces complete render
- [ ] Resume from saved state works
- [ ] Edit workflow applies partial changes

---

## REQ-CINE-FARM: Render Farm Support
**Priority**: P3
**Status**: Planned

Distributed rendering support with chunking.

### Features
- Chunk by shot, frame, or tile
- Manifest generation for farm coordination
- Skip existing frames
- Checksum verification

### Acceptance Criteria
- [ ] Chunking produces independent work units
- [ ] Manifest lists all chunks
- [ ] Resume skips completed chunks

---

## REQ-CINE-MATCH: Camera Matching
**Priority**: P3
**Status**: Planned

Camera import and matching from external sources.

### Features
- Import from reference images (focal estimation)
- Horizon line matching
- Import tracking data (Nuke, After Effects)
- Auto format detection

### Acceptance Criteria
- [ ] Reference image matching works
- [ ] Tracking data import supported

---

## REQ-CINE-AUDIO: Audio Sync
**Priority**: P3
**Status**: Planned

Audio track support for animation timing.

### Features
- Audio file loading
- Beat marker support
- Frame-based sync points

### Acceptance Criteria
- [ ] Audio loads and plays in timeline
- [ ] Markers can be placed on beats

---

## REQ-CINE-CATALOG: Asset Catalog Generator
**Priority**: P1
**Status**: Planned

Automated generation of visual assets for documentation, marketing, and interactive catalogs.

### Catalog Unit (Test Object)
A master test object containing all control surface elements:
- All 9 knob profiles in a row
- All surface features (knurling, ribbing, grooves)
- Fader at various positions
- Multiple button types
- LED indicators in various states
- Meters/VU displays

### Variation Capture System

#### Single-Parameter Variations
Generate all variations of a single parameter:
```yaml
catalog_capture:
  subject: "test_unit"

  variations:
    - parameter: "style_preset"
      values: [neve_classic, ssl_4000, api_vision, harrison_32c, mackie_cr]
      layout: horizontal_strip  # All in one image

    - parameter: "knob_profile"
      values: [standard, vintage_round, pointer, skirted, ...)
      layout: comparison_grid  # Side-by-side

    - parameter: "led_color"
      values: [red, green, blue, amber, white]
      layout: row
```

#### Multi-Parameter Matrix
Generate combinatorial variations:
```yaml
matrix_capture:
  parameters:
    style: [neve_classic, ssl_4000]
    knob_size: [20mm, 25mm, 30mm]
  output: "matrix_style_knobsize"  # 2x3 = 6 images
```

### Layout Modes

#### Strip Layout
All variations in a single horizontal or vertical strip:
- Good for: style comparisons, color variations
- Configurable spacing and labels

#### Grid Layout
Variations in N×M grid:
- Good for: multi-parameter comparisons
- Auto-calculated grid size

#### Comparison Layout (A/B)
Two versions side-by-side:
- Good for: before/after, style A vs style B
- Divider line optional

#### Isolated Layout
Single variation per image:
- Good for: website thumbnails, interactive viewers
- Transparent background option

### Shot Planning Workflow

```yaml
# 1. Plan the shot
shot:
  name: "knob_profile_comparison"
  template: "catalog_strip"

  camera:
    position: isometric_dimetric

  subject:
    artifacts: [knob_standard, knob_vintage, knob_pointer]
    arrangement: horizontal
    spacing: 0.05

  lighting:
    rig: flat_softbox

# 2. Capture initial shot
# 3. Edit specific settings
edit:
  subject:
    artifacts: [knob_skirted, knob_chicken_head]  # Swap artifacts

# 4. Re-capture with new settings
# Frame store tracks all versions
```

### Output Organization

```
catalog/
├── knobs/
│   ├── profiles/
│   │   ├── strip_all_profiles.png
│   │   ├── isolated/
│   │   │   ├── standard.png
│   │   │   ├── vintage_round.png
│   │   │   └── ...
│   ├── styles/
│   │   ├── grid_style_comparison.png
│   │   ├── neve_classic/
│   │   │   ├── hero.png
│   │   │   ├── detail.png
│   │   │   └── isometric.png
│   │   └── ...
│   └── sizes/
│       └── matrix_size_profile.png
├── faders/
│   └── ...
├── buttons/
│   └── ...
├── leds/
│   └── color_strip.png
└── full_unit/
    ├── all_styles_strip.png
    ├── feature_matrix.png
    └── interactive/
        └── (for 3D viewer)
```

### 3D Interactive Viewer Assets

Generate assets for web-based 3D viewers (Three.js, model-viewer):

```yaml
interactive_export:
  format: gltf  # or glb for single file

  variations:
    - name: "knob_standard"
      style: [neve_classic, ssl_4000, ...]
      output: "knob_standard_{style}.glb"

  optimization:
    draco_compression: true
    texture_size: 1024
    merge_materials: true

  features:
    auto_rotate: true
    shadow_plane: true
    environment_lighting: "studio_soft.hdr"
```

### Website Integration

```yaml
catalog_manifest:
  # Generated manifest.json for website
  version: "1.0.0"
  generated: "2026-02-18"

  categories:
    knobs:
      profiles: 9
      styles: 5
      total_variations: 45

    faders:
      types: 3
      styles: 5
      total_variations: 15

  assets:
    - id: "knob_standard_neve"
      thumbnail: "thumbnails/knob_standard_neve.png"
      model_3d: "models/knob_standard_neve.glb"
      metadata:
        profile: "standard"
        style: "neve_classic"
        diameter_mm: 25
```

### Automation Pipeline

```yaml
catalog_pipeline:
  # Define all catalog captures
  captures:
    - name: "all_knob_profiles"
      type: strip
      parameter: knob_profile
      values: [all]

    - name: "all_styles"
      type: grid
      parameter: style_preset
      values: [neve_classic, ssl_4000, api_vision, harrison_32c, mackie_cr]
      views: [hero, isometric, detail]

    - name: "feature_comparison"
      type: comparison
      left: [knurling]
      right: [ribbing, grooves]

  # Render settings
  render:
    quality: production
    format: png
    background: transparent

  # Post-processing
  post:
    thumbnail_size: 256
    webp_conversion: true
    optimize: true
```

### Acceptance Criteria
- [ ] Single-parameter variation capture works
- [ ] Multi-parameter matrix generation works
- [ ] All layout modes (strip, grid, comparison, isolated) implemented
- [ ] Shot planning/edit/re-capture workflow functional
- [ ] Output organized in configurable directory structure
- [ ] GLTF/GLB export for 3D viewers works
- [ ] Catalog manifest generated automatically

---

## Summary

| Priority | Count | Requirements |
|----------|-------|--------------|
| P0 | 5 | CINE-01, CINE-CAM, CINE-LIGHT, CINE-RENDER, CINE-SHOT |
| P1 | 6 | CINE-PLUMB, CINE-ENV, CINE-LUT, CINE-ANIM, CINE-TEMPLATE, CINE-CATALOG |
| P2 | 6 | CINE-PATH, CINE-SHUFFLE, CINE-FRAME, CINE-DEPTH, CINE-GIMP, CINE-ISO |
| P3 | 4 | CINE-COMPOSE, CINE-FARM, CINE-MATCH, CINE-AUDIO |

**Total**: 23 requirements

### New Requirements (v1.2)
- **REQ-CINE-ISO**: Isometric View System (P2) - Orthographic rendering for documentation
- **REQ-CINE-CATALOG**: Asset Catalog Generator (P1) - Automated screenshot/3D asset generation
