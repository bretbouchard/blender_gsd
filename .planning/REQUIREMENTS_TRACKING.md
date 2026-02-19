# Blender GSD Framework - Motion Tracking Requirements

**Version**: 1.0
**Status**: Draft
**Related**: REQUIREMENTS_CINEMATIC.md, CINEMATIC_SYSTEM_DESIGN.md
**Created**: 2026-02-18

---

## Executive Summary

This document defines a comprehensive motion tracking system for the Blender GSD framework. The system enables:

1. **Point tracking** from any video footage (not just iPhone)
2. **Camera solving** to extract 3D camera motion from 2D footage
3. **Object tracking** to track physical objects for animation reference
4. **External tracking import** from professional match-move software
5. **LiDAR/scan import** for environment reconstruction
6. **Motion capture import** for performance animation

**Core Philosophy:**
- Support any footage source (iPhone, cinema camera, archival footage)
- Leverage Blender's built-in tracking + external professional tools
- Integrate seamlessly with cinematic shot assembly (REQ-CINE-SHOT)
- Enable compositing workflows with tracked camera data

---

## REQ-TRACK-01: Motion Tracking Foundation
**Priority**: P1
**Status**: Planned

Core infrastructure for motion tracking operations.

### Module Structure
```
lib/cinematic/
├── tracking/
│   ├── __init__.py
│   ├── types.py              # Tracking data types
│   ├── footage.py            # Footage analysis and import
│   ├── point_tracker.py      # Point/feature tracking
│   ├── camera_solver.py      # Camera solve integration
│   ├── object_tracker.py     # Object tracking
│   ├── import_export.py      # External format support
│   └── calibration.py        # Lens/camera calibration
```

### Configuration Structure
```
configs/cinematic/tracking/
├── camera_profiles.yaml      # Device-specific lens data
├── tracking_presets.yaml     # Common tracking setups
├── solver_settings.yaml      # Camera solver configurations
└── import_formats.yaml       # External format mappings
```

### State Persistence
```
.gsd-state/tracking/
├── footage/
│   └── {footage_name}/
│       ├── analysis.yaml     # Auto-detected metadata
│       └── thumbnails/       # Frame thumbnails
├── solves/
│   └── {solve_name}/
│       ├── camera.yaml       # Solved camera data
│       ├── tracks.yaml       # Point tracks
│       └── report.yaml       # Solve quality report
└── sessions/
    └── {session_id}.yaml     # Resume state
```

### Acceptance Criteria
- [ ] Module structure created
- [ ] Configuration directories established
- [ ] State persistence framework implemented
- [ ] Basic footage import works

---

## REQ-TRACK-FOOTAGE: Footage Analysis & Import
**Priority**: P1
**Status**: Planned

Comprehensive footage handling with automatic metadata extraction.

### Supported Sources
| Source | Formats | Notes |
|--------|---------|-------|
| **iPhone** | MOV, MP4 (HEVC, H.264, ProRes) | Metadata extraction enabled |
| **Cinema Cameras** | MOV, MP4, MXF, ARRI, RED | Various codecs |
| **DSLR/Mirrorless** | MOV, MP4, AVCHD | Standard consumer formats |
| **Archival** | AVI, DV, ProRes, DNxHD | Legacy format support |
| **Image Sequences** | PNG, JPEG, EXR, DPX | Frame-by-frame workflows |

### Automatic Metadata Extraction
```yaml
footage_analysis:
  # Auto-detected from file
  file_metadata:
    - filename
    - resolution
    - frame_rate
    - duration_frames
    - codec
    - bit_depth
    - color_space  # If embedded

  # Auto-detected from video content
  content_analysis:
    - motion_blur_level      # High/Medium/Low
    - rolling_shutter_artifacts # Detect skew
    - noise_level
    - contrast_suitability   # For tracking
    - dominant_motion_type   # Pan/Tilt/Zoom/Handheld

  # Device-specific (if metadata available)
  device_metadata:
    - camera_model           # From QuickTime metadata
    - lens_model
    - focal_length           # 35mm equivalent
    - aperture
    - iso
    - white_balance
```

### Frame Rate Handling
```yaml
frame_rate:
  # Common frame rates
  rates:
    - 23.976  # Film
    - 24      # Cinema
    - 25      # PAL
    - 29.97   # NTSC
    - 30      # Standard
    - 50      # PAL progressive
    - 59.94   # NTSC progressive
    - 60      # High frame rate
    - 120     # Slow motion
    - 240     # Ultra slow motion

  # Interpretation rules
  interpretation:
    detect_from_metadata: true
    override_allowed: true
    pulldown_removal: auto  # For interlaced sources
```

### Rolling Shutter Compensation
```yaml
rolling_shutter:
  # Detection
  auto_detect: true         # Analyze footage for skew

  # Common sensor read times (in seconds)
  sensor_presets:
    iphone_14_pro: 0.008
    iphone_15_pro: 0.007
    sony_a7iv: 0.015
    canon_r5: 0.012
    red_komodo: 0.005
    arri_alexa: 0.003

  # Compensation
  compensation:
    enabled: auto           # auto, always, never
    method: pixel_motion    # pixel_motion, simple_warp
```

### Acceptance Criteria
- [ ] All major video formats import correctly
- [ ] Image sequences load with correct frame rate
- [ ] Metadata extraction works for iPhone footage
- [ ] Rolling shutter detection identifies problematic footage
- [ ] Footage analysis completes in <30 seconds for 10-second clip

---

## REQ-TRACK-CAMPROF: Camera & Lens Profiles
**Priority**: P1
**Status**: Planned

Device-specific camera and lens profiles for accurate solving.

### Profile Structure
```yaml
# configs/cinematic/tracking/camera_profiles.yaml

devices:
  # iPhone Series
  iphone_14:
    sensor_width: 7.71      # mm
    sensor_height: 5.81
    main_camera:
      focal_length_equiv: 26  # 35mm equivalent
      actual_focal: 6.68      # mm (calculated)
      aperture: f/1.5
      lens_distortion: 0.02   # Barrel distortion
    ultrawide:
      focal_length_equiv: 13
      actual_focal: 2.32
      aperture: f/2.4
      lens_distortion: 0.08   # Significant barrel

  iphone_14_pro:
    sensor_width: 8.08
    sensor_height: 6.01
    main_camera:
      focal_length_equiv: 24
      actual_focal: 6.86
      aperture: f/1.8
      lens_distortion: 0.015
    ultrawide:
      focal_length_equiv: 13
      actual_focal: 2.37
      aperture: f/2.2
      lens_distortion: 0.07

  iphone_15_pro:
    sensor_width: 8.08
    sensor_height: 6.01
    main_camera:
      focal_length_equiv: 24
      actual_focal: 6.86
      aperture: f/1.8
      lens_distortion: 0.012

  # Cinema Cameras
  red_komodo:
    sensor_width: 27.03     # Super 35
    sensor_height: 14.26
    lens_mount: RF
    lens_distortion: 0.0

  arri_alexa_mini:
    sensor_width: 28.25
    sensor_height: 18.17
    lens_mount: PL
    lens_distortion: 0.0

  # DSLR/Mirrorless
  sony_a7iv:
    sensor_width: 35.9      # Full frame
    sensor_height: 23.9
    lens_mount: E
    lens_distortion: lens_specific

  canon_r5:
    sensor_width: 36.0
    sensor_height: 24.0
    lens_mount: RF
    lens_distortion: lens_specific
```

### Lens Distortion Models
```yaml
lens_distortion:
  models:
    # Brown-Conrady (most common)
    brown_conrady:
      parameters:
        - k1                # Radial distortion
        - k2
        - k3
        - p1                # Tangential distortion
        - p2

    # Simple radial (faster)
    simple_radial:
      parameters:
        - k1

    # Division model (for undistortion)
    division:
      parameters:
        - k1

  # Apply to footage
  undistort_workflow:
    method: st_map          # ST-Map for compositing
    generate_stmap: true
    output_format: EXR
```

### Focal Length Estimation
```yaml
focal_length:
  estimation:
    # From device profile
    from_profile: auto     # Auto-detect device

    # From metadata
    from_metadata: true    # Use embedded focal length

    # From image analysis
    from_analysis:
      method: vanishing_points
      min_lines: 4
      confidence_threshold: 0.8

  # Constraints for solver
  constraints:
    allow_zoom: false      # Fixed focal length
    zoom_range: [20, 100]  # If zoom allowed
    tolerance: 0.5         # mm tolerance
```

### Acceptance Criteria
- [ ] iPhone 14/15/16 series profiles available
- [ ] 10+ cinema/DSLR camera profiles available
- [ ] Focal length estimation from vanishing points works
- [ ] Lens distortion models apply correctly
- [ ] ST-Map generation for compositing

---

## REQ-TRACK-POINT: Point Tracking System
**Priority**: P0
**Status**: Planned

Robust point tracking for feature detection and correlation.

### Tracking Features
```yaml
point_tracking:
  # Feature Detection
  detection:
    methods:
      - fast               # FAST corner detection
      - harris             # Harris corners
      - sift               # Scale-invariant (slower)
      - surf               # Speeded-up robust features

    selection:
      min_corners: 50      # Minimum features to track
      max_corners: 500     # Maximum features
      quality_level: 0.01  # Corner quality threshold
      min_distance: 10     # Pixels between features

    # Region of interest
    roi:
      enabled: true
      auto_mask_subject: true  # Mask out moving objects

  # Tracking Algorithm
  algorithm:
    method: lucas_kanade   # KLT optical flow
    window_size: 21        # Search window
    max_levels: 3          # Pyramid levels

    # Motion model
    motion_model:
      translation: true    # X/Y only
      affine: false        # Include rotation/scale
      perspective: false   # Full homography

  # Track Management
  track_management:
    # When to drop tracks
    drop_threshold:
      correlation: 0.7     # Minimum correlation
      error: 5.0           # Maximum tracking error (pixels)

    # Track filtering
    filtering:
      smooth_tracks: true
      filter_window: 5     # Frames
      outlier_removal: true

  # Manual Intervention
  manual_tools:
    add_track: true        # Manually place tracks
    delete_track: true     # Remove bad tracks
    adjust_track: true     # Reposition per-frame
    refine_track: true     # Sub-pixel refinement
```

### Tracking Presets
```yaml
# configs/cinematic/tracking/tracking_presets.yaml

presets:
  # High-quality tracking (slower)
  high_quality:
    detection:
      method: sift
      min_corners: 200
      quality_level: 0.02
    algorithm:
      window_size: 31
      max_levels: 5
    track_management:
      drop_threshold:
        correlation: 0.8

  # Balanced (default)
  balanced:
    detection:
      method: fast
      min_corners: 100
      quality_level: 0.01
    algorithm:
      window_size: 21
      max_levels: 3
    track_management:
      drop_threshold:
        correlation: 0.7

  # Fast tracking (lower quality)
  fast:
    detection:
      method: fast
      min_corners: 50
      quality_level: 0.005
    algorithm:
      window_size: 15
      max_levels: 2
    track_management:
      drop_threshold:
        correlation: 0.6

  # Architectural (for buildings/interiors)
  architectural:
    detection:
      method: harris
      min_corners: 150
      quality_level: 0.015
    algorithm:
      window_size: 25
      max_levels: 4
    constraints:
      prefer_lines: true
      prefer_corners: true
```

### Track Visualization
```yaml
visualization:
  display_tracks: true
  display_paths: true
  display_errors: true

  colors:
    good_track: [0, 1, 0]        # Green
    warning_track: [1, 1, 0]     # Yellow
    bad_track: [1, 0, 0]         # Red
    selected_track: [0, 0.5, 1]  # Cyan

  path_length: 50          # Frames of path to show
```

### Acceptance Criteria
- [ ] Automatic feature detection finds 50+ trackable points
- [ ] KLT tracking maintains correlation through moderate motion blur
- [ ] Track filtering removes jitter without over-smoothing
- [ ] Manual track placement/refinement works
- [ ] Track visualization clearly shows quality

---

## REQ-TRACK-SOLVE: Camera Solver Integration
**Priority**: P0
**Status**: Planned

Integration with Blender's camera solver and external solvers.

### Blender libmv Integration
```yaml
camera_solver:
  # Built-in solver (libmv)
  blender_solver:
    enabled: true

    # Solver settings
    settings:
      refinement:
        refine_focal_length: true
        refine_principal_point: false
        refine_radial_distortion: k1_only  # k1_only, k1_k2, none

      # Motion model
      motion:
        type: perspective   # perspective, affine

      # Keyframe selection
      keyframes:
        auto_select: true
        min_keyframes: 8
        method: motion_analysis  # Select frames with good parallax

    # Solve quality thresholds
    quality:
      max_reprojection_error: 1.0  # Pixels
      min_tracks_per_frame: 8
      acceptable_error: 0.5

  # External solvers (import only)
  external_solvers:
    - syntheyes
    - 3dequalizer
    - pftrack
    - nuke
    - after_effects
```

### Solve Workflow
```yaml
solve_workflow:
  # Step 1: Prepare footage
  prepare:
    - load_footage
    - detect_features
    - track_features
    - filter_tracks

  # Step 2: Configure solver
  configure:
    - set_camera_profile
    - set_focal_length_constraint
    - set_distortion_model
    - select_keyframes

  # Step 3: Solve
  solve:
    - initial_solve
    - check_error
    - refine_solve  # Iterate

  # Step 4: Apply
  apply:
    - create_camera_object
    - set_keyframes
    - create_tracking_empty  # For compositing reference
```

### Solve Quality Metrics
```yaml
solve_report:
  metrics:
    - reprojection_error_avg   # Average error in pixels
    - reprojection_error_max   # Maximum error
    - tracks_used              # Number of tracks
    - frames_solved            # Frames with valid camera
    - focal_length_variance    # If zoom allowed
    - confidence_score         # Overall confidence 0-1

  # Quality assessment
  assessment:
    excellent:
      reprojection_error_avg: < 0.3
      confidence: > 0.95

    good:
      reprojection_error_avg: < 0.5
      confidence: > 0.85

    acceptable:
      reprojection_error_avg: < 1.0
      confidence: > 0.70

    poor:
      reprojection_error_avg: > 1.0
      confidence: < 0.70
```

### Blender Camera Creation
```yaml
camera_creation:
  # Camera settings from solve
  apply_solve:
    create_camera: true
    camera_name: "{footage_name}_solved"

    # Animation
    keyframe_all_frames: true   # Or just key poses
    interpolation: linear       # linear, bezier

    # Optional constraints
    constraints:
      track_to_empty: true      # Look-at constraint
      follow_path: false        # For smooth paths

  # Coordinate system
  coordinate_system:
    up_axis: Z
    forward_axis: Y
    scale: 1.0                  # Scene units per meter
```

### Acceptance Criteria
- [ ] Blender libmv solver accessible from GSD workflow
- [ ] Auto keyframe selection based on parallax analysis
- [ ] Solve produces accurate camera with <1px reprojection error
- [ ] Camera animation keyframes created in Blender
- [ ] Solve quality report generated automatically

---

## REQ-TRACK-IMPORT: External Tracking Import
**Priority**: P1
**Status**: Planned

Import tracking data from professional match-move software.

### Supported Formats
```yaml
import_formats:
  # Camera tracking data
  camera_formats:
    - fbx                    # Filmbox format
    - alembic                # .abc - animation cache
    - collada                # .dae - interchange
    - nuke_cam               # .nk - Nuke camera
    - chan                   # .chan - simple camera
    - rzml                   # RealityCapture
    - wml                    # 3DEqualizer

  # Motion capture
  mocap_formats:
    - bvh                    # Biovision Hierarchy
    - fbx                    # With skeleton
    - c3d                    # Marker data

  # Point clouds / Scans
  scan_formats:
    - obj                    # Mesh export
    - ply                    # Point cloud
    - las                    # LiDAR data
    - e57                    # Point cloud
    - usdz                   # Apple AR format
```

### Format-Specific Importers
```yaml
# configs/cinematic/tracking/import_formats.yaml

importers:
  # FBX (most common)
  fbx:
    coordinate_system:
      up: Y                  # FBX default is Y-up
      forward: -Z
      convert_to_blender: true  # Blender is Z-up

    camera_import:
      import_focal: true
      import_aperture: true
      import_animation: true
      import_lens_distortion: true  # If present

    scale_factor: 0.01       # cm to m

  # Alembic
  alembic:
    import_camera: true
    import_transforms: true
    import_geometry: true
    frame_rate: from_file

  # BVH (motion capture)
  bvh:
    import_skeleton: true
    import_animation: true
    retarget_to_metarig: false  # Optional auto-retarget

  # Nuke .chan
  nuke_chan:
    columns: [tx, ty, tz, rx, ry, rz, focal]
    frame_column: 0
    delimiter: space
    rotation_order: XYZ
```

### 3DEqualizer Integration
```yaml
3dequalizer:
  # Export from 3DE
  export:
    format: python_script    # Generate Blender Python
    include_distortion: true
    include_point_cloud: true

  # Import to GSD
  import:
    camera_name: "3de_camera"
    create_point_cloud: true
    point_cloud_name: "tracking_points"
```

### SynthEyes Integration
```yaml
syntheyes:
  export:
    format: fbx              # Or direct Blender script
    include_tracks: true

  import:
    auto_align_scene: true   # Match ground plane
```

### Nuke Integration
```yaml
nuke:
  # Import camera from Nuke
  camera_import:
    formats:
      - nk                   # Nuke script (parse camera)
      - chan                 # Simple channel file
      - fbx                  # FBX export

  # Coordinate conversion
  coordinates:
    nuke_up: Y
    blender_up: Z
    conversion_matrix: auto
```

### Acceptance Criteria
- [ ] FBX camera import with coordinate conversion works
- [ ] Alembic import preserves animation
- [ ] BVH mocap import creates armature
- [ ] Nuke .chan import parses correctly
- [ ] Import creates Blender camera with animation

---

## REQ-TRACK-OBJECT: Object Tracking
**Priority**: P2
**Status**: Planned

Track objects in footage for animation reference and compositing.

### Object Tracking Modes
```yaml
object_tracking:
  modes:
    # Single point tracking
    point:
      description: "Track single point in space"
      use_case: "Reference point, attach object"

    # Planar tracking
    planar:
      description: "Track flat surface"
      use_case: "Screen replacement, billboard"

    # Rigid body tracking
    rigid_body:
      description: "Track 3D object with fixed shape"
      use_case: "Product insertion, prop tracking"
      requires: "Multiple tracks on same object"

    # Deformable tracking
    deformable:
      description: "Track deforming object"
      use_case: "Face tracking, cloth"
      requires: "Dense track points"
```

### Planar Tracking
```yaml
planar_tracking:
  # Track a plane in footage
  workflow:
    - define_corners         # 4 corners of plane
    - track_corners          # Track through frames
    - solve_homography       # Calculate plane transform
    - export_transform       # Corner pin or 3D plane

  export:
    formats:
      - corner_pin          # 2D compositing
      - 3d_plane            # 3D mesh plane
      - after_effects       # AE corner pin data
```

### Rigid Body Tracking
```yaml
rigid_body_tracking:
  # Track physical object
  workflow:
    - place_markers          # Physical or detected markers
    - track_all_markers      # Track through footage
    - solve_object           # Calculate object transform
    - apply_to_mesh          # Apply to 3D object

  # Marker configuration
  markers:
    min_markers: 4           # Minimum for 3D
    preferred: 8             # Better accuracy
    auto_detect: true        # Detect colored markers

  # Solve settings
  solver:
    bundle_adjustment: true
    refine_intrinsics: false  # Usually fixed camera
```

### Integration with Control Surfaces
```yaml
control_surface_tracking:
  # Track real knob/fader for animation reference
  workflow:
    - film_knob_interaction  # Capture real knob being turned
    - track_knob_rotation    # Extract rotation angle
    - apply_to_virtual       # Drive virtual knob

  # For knob rotation
  knob_tracking:
    method: planar_rotation  # Track knob face rotation
    output: rotation_curve   # F-Curve for rotation

  # For fader movement
  fader_tracking:
    method: point_tracking   # Track fader cap
    output: position_curve   # F-Curve for position
```

### Acceptance Criteria
- [ ] Planar tracking produces corner pin data
- [ ] Rigid body tracking solves object transform
- [ ] Tracked data exports to Blender animation
- [ ] Control surface tracking extracts rotation/position curves

---

## REQ-TRACK-SCAN: LiDAR & Scan Import
**Priority**: P2
**Status**: Planned

Import and utilize 3D scans and LiDAR data.

### Supported Scan Sources
```yaml
scan_sources:
  # iPhone LiDAR apps
  iphone_apps:
    polycam:
      formats: [obj, glb, fbx, usdz]
      quality: high
      features:
        - texture
        - color
        - multiple_scans

    realityscan:             # Epic Games
      formats: [fbx]
      quality: high
      features:
        - texture
        - photogrammetry

    scaniverse:
      formats: [obj, glb, usdz]
      quality: medium
      features:
        - texture
        - free

    sitescape:
      formats: [las, e57]
      quality: high
      features:
        - raw_point_cloud
        - survey_grade

  # Professional scanners
  professional:
    matterport:
      formats: [obj, e57]
      quality: very_high

    faro:
      formats: [e57, las, fls]
      quality: survey_grade

    leica:
      formats: [e57, las, ptg]
      quality: survey_grade
```

### Scan Processing Pipeline
```yaml
scan_pipeline:
  # Import scan
  import:
    - load_file
    - detect_scale          # Auto-detect real-world scale
    - align_to_ground       # Detect floor plane

  # Clean up
  cleanup:
    - remove_noise          # Statistical outlier removal
    - fill_holes            # If mesh
    - decimate              # Reduce poly count for viewport

  # Integration
  integrate:
    - create_backdrop       # Use as environment
    - extract_floor         # For shadow catcher
    - create_proxies        # Low-poly collision
```

### Scale Detection
```yaml
scale_detection:
  # Automatic scale estimation
  methods:
    # From known objects in scan
    reference_objects:
      - aruco_marker        # Known size marker
      - checkerboard        # Calibration pattern
      - known_object        # Detected furniture

    # From scan metadata
    metadata:
      - gps_coordinates     # If available
      - scanner_baseline    # Scanner-specific

    # Manual
    manual:
      - measure_distance    # User provides known distance
      - set_scale_factor    # Direct input

  # Default assumption
  default:
    assume_meters: true     # Most scans in meters
```

### Backdrop Integration
```yaml
scan_as_backdrop:
  # Use scan as cinematic backdrop
  workflow:
    - import_scan
    - position_relative_to_subject
    - configure_materials
    - set_shadow_catcher    # For compositing

  material_config:
    shadow_catcher: true
    diffuse_only: true      # No fancy shaders
    receive_shadows: true
    cast_shadows: false     # Usually backdrop
```

### Acceptance Criteria
- [ ] Polycam OBJ/GLB imports at correct scale
- [ ] Floor plane auto-detected from scan
- [ ] Scan can be used as backdrop environment
- [ ] Point cloud decimation for viewport performance

---

## REQ-TRACK-MOCAP: Motion Capture Import
**Priority**: P2
**Status**: Planned

Import and apply motion capture data for control surface animation.

### Mocap Sources
```yaml
mocap_sources:
  # iPhone-based mocap
  iphone_apps:
    move_ai:
      formats: [fbx, bvh]
      quality: high
      features:
        - full_body
        - hands
        - face

    rokoko_video:
      formats: [fbx, bvh]
      quality: medium
      features:
        - full_body

    deepmotion:
      formats: [fbx]
      quality: medium
      features:
        - full_body

  # Professional mocap
  professional:
    vicon:
      formats: [c3d, fbx, bvh]
      quality: production

    optitrack:
      formats: [c3d, fbx]
      quality: production
```

### Hand Animation for Control Surfaces
```yaml
hand_mocap:
  # Import hand animation
  workflow:
    - capture_hand_video    # iPhone recording
    - process_with_app      # Move.ai or similar
    - import_bvh_fbx        # Import to Blender
    - retarget_to_hand_rig  # Apply to hand rig
    - extract_finger_curves # Get individual finger motion

  # Finger tracking specific
  finger_tracking:
    precision_required: high  # For knob/fader interaction
    min_frame_rate: 60

  # Output
  output:
    - rotation_curves       # Per-joint rotation
    - position_curves       # For hand position
```

### Retargeting to Control Surfaces
```yaml
retargeting:
  # Map mocap to control surface animation
  workflow:
    - import_mocap
    - identify_interaction_frames  # When hand touches control
    - extract_control_motion       # Map to knob rotation

  # Knob turning from mocap
  knob_from_mocap:
    method: finger_angle    # Calculate from finger joints
    output: z_rotation      # Knob rotation axis

  # Fader movement from mocap
  fader_from_mocap:
    method: hand_position   # Track hand Y position
    output: y_translation   # Fader travel axis

  # Button press from mocap
  button_from_mocap:
    method: finger_tip_position
    threshold: 0.005        # 5mm press detection
    output: boolean_keyframe
```

### Acceptance Criteria
- [ ] BVH import creates armature with animation
- [ ] FBX mocap import preserves skeleton
- [ ] Hand animation extractable for control surfaces
- [ ] Mocap can drive morphing engine animations

---

## REQ-TRACK-COMPOSITE: Compositing Integration
**Priority**: P1
**Status**: Planned

Integration with Blender compositor for VFX compositing workflows.

### Tracking Data in Compositor
```yaml
compositor_integration:
  # Export tracking data for compositor
  export:
    - camera_transform      # 3D camera for 3D compositing
    - point_tracks          # 2D tracks for stabilization
    - plane_tracks          # For corner pin effects
    - depth_data            # If depth from solve

  # Compositor nodes
  nodes:
    - stabilize_2d          # From point tracks
    - corner_pin            # From plane tracks
    - lens_distortion       # From calibration
    - camera_transform      # For 3D composite
```

### Background Plate Integration
```yaml
background_plate:
  workflow:
    - load_footage          # Original footage
    - apply_tracking        # Tracked camera
    - render_3d_elements    # Cycles render
    - composite_over        # Alpha over

  # Alpha handling
  alpha:
    premultiplied: true
    shadow_catcher: true    # For ground shadows
```

### Lens Distortion Workflow
```yaml
lens_distortion_workflow:
  # Option 1: Undistort footage
  undistort:
    method: st_map
    apply_before_composite: true
    redistort_after: true

  # Option 2: Apply distortion to CG
  distort_cg:
    method: render_undistorted
    apply_distortion_in_comp: true

  # ST-Map generation
  st_map:
    resolution: match_footage
    format: EXR
    channels: [R, G]       # UV coordinates
```

### Shadow Catcher Workflow
```yaml
shadow_catcher:
  setup:
    create_ground_plane: true
    material: shadow_catcher
    receive_shadows: true

  render:
    passes: [shadow, combined]
    film_transparent: true

  composite:
    shadow_only: true
    multiply_background: true
```

### Acceptance Criteria
- [ ] Tracking data creates compositor nodes
- [ ] 2D stabilization from point tracks works
- [ ] Lens distortion ST-Map generates correctly
- [ ] Shadow catcher composites over footage

---

## REQ-TRACK-SHOT: Shot Assembly Integration
**Priority**: P1
**Status**: Planned

Integrate tracking with cinematic shot assembly (REQ-CINE-SHOT).

### Tracked Shot Configuration
```yaml
# Example: Shot with tracking data

shot:
  name: composite_knob_hero

  # Source footage
  footage:
    file: footage/knob_hero_4k.mp4
    device: iphone_14_pro
    frame_range: [1, 150]

  # Tracking
  tracking:
    enabled: true
    preset: high_quality
    solve: true

    camera_profile: iphone_14_pro

    tracks:
      auto_detect: true
      min_tracks: 100

    solve_settings:
      refine_focal: true
      refine_distortion: k1_only

  # Subject (3D element to composite)
  subject:
    type: artifact
    artifact: neve_knob
    position: [0, 0, 0]

  # Camera from tracking
  camera:
    from_tracking: true
    tracking_solve: default

    # Overrides
    lens:
      aperture: f/4
      focus_distance: auto

  # Backdrop from scan
  backdrop:
    type: scan
    file: scans/desk_scan.glb

  # Render
  render:
    profile: cycles_production
    background: footage_frame  # Composite mode
    passes: [beauty, shadow, cryptomatte]

  # Composite
  composite:
    mode: over_footage
    shadow_catcher: true
    color_match: auto
```

### Resume Tracking Session
```yaml
# Resume interrupted tracking
resume:
  load_session: .gsd-state/tracking/sessions/knob_hero.yaml

  # Continue from last frame tracked
  continue_tracking:
    from_frame: 75
    to_frame: 150

  # Or just load existing solve
  load_solve: .gsd-state/tracking/solves/knob_hero/
```

### Acceptance Criteria
- [ ] Shot YAML can reference footage for tracking
- [ ] Tracking runs as part of shot assembly
- [ ] Solved camera integrates with cinematic camera system
- [ ] Composite mode renders over footage

---

## REQ-TRACK-BATCH: Batch Processing
**Priority**: P2
**Status**: Planned

Batch tracking and solving for multiple shots.

### Batch Configuration
```yaml
batch_tracking:
  shots:
    - footage: shots/angle_01.mp4
      output: tracking/angle_01
      preset: balanced

    - footage: shots/angle_02.mp4
      output: tracking/angle_02
      preset: balanced

    - footage: shots/close_up.mp4
      output: tracking/close_up
      preset: high_quality

  # Parallel processing
  parallel:
    enabled: true
    max_workers: 4

  # Resume on failure
  resume:
    skip_completed: true
    retry_failed: true
    max_retries: 3
```

### Batch Output
```
tracking/
├── angle_01/
│   ├── solve.yaml         # Solved camera data
│   ├── tracks.yaml        # Point tracks
│   ├── report.yaml        # Quality report
│   └── preview.mp4        # Tracking visualization
├── angle_02/
│   └── ...
└── batch_report.yaml      # Overall batch status
```

### Acceptance Criteria
- [ ] Multiple shots process in parallel
- [ ] Resume skips completed shots
- [ ] Batch report summarizes all results

---

## Summary

| Requirement | Priority | Status | Est. Effort |
|-------------|----------|--------|-------------|
| REQ-TRACK-01: Foundation | P1 | Planned | 2-3 days |
| REQ-TRACK-FOOTAGE: Footage Analysis | P1 | Planned | 3-4 days |
| REQ-TRACK-CAMPROF: Camera Profiles | P1 | Planned | 2-3 days |
| REQ-TRACK-POINT: Point Tracking | P0 | Planned | 4-5 days |
| REQ-TRACK-SOLVE: Camera Solver | P0 | Planned | 5-6 days |
| REQ-TRACK-IMPORT: External Import | P1 | Planned | 3-4 days |
| REQ-TRACK-OBJECT: Object Tracking | P2 | Planned | 4-5 days |
| REQ-TRACK-SCAN: LiDAR/Scan Import | P2 | Planned | 3-4 days |
| REQ-TRACK-MOCAP: Motion Capture | P2 | Planned | 3-4 days |
| REQ-TRACK-COMPOSITE: Compositing | P1 | Planned | 3-4 days |
| REQ-TRACK-SHOT: Shot Integration | P1 | Planned | 2-3 days |
| REQ-TRACK-BATCH: Batch Processing | P2 | Planned | 2-3 days |

**Total Requirements**: 12
**Total Estimated Effort**: 36-48 days

---

## Implementation Roadmap

### Phase 7.0: Tracking Foundation (REQ-TRACK-01)
- Create module structure
- Establish configuration directories
- Implement state persistence

### Phase 7.1: Core Tracking (REQ-TRACK-POINT, REQ-TRACK-SOLVE)
- Implement point tracking
- Integrate Blender camera solver
- Create camera from solve

### Phase 7.2: Footage & Profiles (REQ-TRACK-FOOTAGE, REQ-TRACK-CAMPROF)
- Implement footage analysis
- Create camera profile database
- Add rolling shutter compensation

### Phase 7.3: Import/Export (REQ-TRACK-IMPORT)
- Implement FBX import
- Implement BVH import
- Implement Nuke .chan import

### Phase 7.4: Integration (REQ-TRACK-COMPOSITE, REQ-TRACK-SHOT)
- Compositor node integration
- Shot assembly integration
- Background plate workflow

### Phase 7.5: Advanced Features (REQ-TRACK-OBJECT, REQ-TRACK-SCAN, REQ-TRACK-MOCAP)
- Object tracking
- LiDAR scan import
- Motion capture import

### Phase 7.6: Batch & Polish (REQ-TRACK-BATCH)
- Batch processing
- Performance optimization
- Documentation

---

## Dependencies

- **REQ-CINE-CAM**: Camera system for solved camera integration
- **REQ-CINE-SHOT**: Shot assembly for tracking integration
- **REQ-CINE-RENDER**: Render system for compositing
- **Blender 4.x+**: Movie Clip Editor API, libmv

---

## External Tool Recommendations

For production work, consider these external tools that export compatible formats:

| Tool | Use Case | Export Format |
|------|----------|---------------|
| **SynthEyes** | Budget-friendly match move | FBX, Python |
| **3DEqualizer** | Industry standard | FBX, Python |
| **PFTrack** | High-end tracking | FBX, Alembic |
| **Nuke** | Compositing + tracking | .chan, FBX |
| **DaVinci Resolve** | Free + tracking | FBX |
| **Move.ai** | iPhone mocap | FBX, BVH |
| **Polycam** | iPhone LiDAR | OBJ, GLB, FBX |

The GSD tracking system is designed to complement, not replace, these specialized tools.
