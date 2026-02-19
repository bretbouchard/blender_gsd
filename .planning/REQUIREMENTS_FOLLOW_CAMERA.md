# Blender GSD Framework - Follow Camera System Requirements

**Version**: 1.0
**Status**: Draft
**Related**: REQUIREMENTS_CINEMATIC.md, REQUIREMENTS_TRACKING.md
**Created**: 2026-02-18

---

## Executive Summary

This document defines an **Intelligent Follow Camera System** for the Blender GSD framework. The system provides:

1. **Multiple follow modes** - Side-scroller, over-shoulder, chase, orbit-follow
2. **Intelligent framing** - Automatic composition adjustment
3. **Obstacle avoidance** - Camera "operator" that prevents objects blocking the view
4. **Predictive tracking** - Look-ahead for smooth anticipation
5. **Pre-solve workflow** - Pre-compute complex camera moves for one-shot renders
6. **Environment awareness** - Collision detection with scene geometry

**Core Philosophy:**
- Camera behaves like a skilled camera operator
- Anticipates action and adjusts framing dynamically
- Never lets obstacles block the subject
- Smooth, cinematic motion at all times
- Pre-solvable for deterministic renders

---

## REQ-FOLLOW-01: Follow Camera Foundation
**Priority**: P1
**Status**: Planned

Core infrastructure for intelligent camera following.

### Module Structure
```
lib/cinematic/follow_cam/
├── __init__.py
├── types.py                 # Follow camera data types
├── follow_modes.py          # Side-scroller, over-shoulder, chase, orbit
├── framing.py               # Intelligent composition
├── obstacle_avoidance.py    # Collision detection and avoidance
├── prediction.py            # Look-ahead and anticipation
├── solver.py                # Pre-solve system for complex moves
└── constraints.py           # Camera constraint helpers
```

### Configuration Structure
```
configs/cinematic/follow_cam/
├── follow_modes.yaml        # Mode presets
├── framing_rules.yaml       # Composition rules
├── avoidance_presets.yaml   # Obstacle avoidance settings
└── prediction_settings.yaml # Look-ahead configuration
```

### State Persistence
```
.gsd-state/follow_cam/
├── solves/
│   └── {solve_name}/
│       ├── camera_path.yaml     # Baked camera animation
│       ├── avoidance_log.yaml   # Obstacles encountered
│       └── metadata.yaml        # Solve settings used
└── previews/
    └── {solve_name}.mp4         # Preview animation
```

### Core Types
```python
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum

class FollowMode(Enum):
    SIDE_SCROLLER = "side_scroller"      # 2.5D locked plane
    OVER_SHOULDER = "over_shoulder"      # Third-person behind
    CHASE = "chase"                      # Following from behind
    CHASE_SIDE = "chase_side"            # Following from side
    ORBIT_FOLLOW = "orbit_follow"        # Orbit while following
    LEAD = "lead"                        # Camera leads subject
    AERIAL = "aerial"                    # Top-down following
    FREE_ROAM = "free_roam"              # Game-style free camera

@dataclass
class FollowTarget:
    """Target for follow camera to track."""
    object_name: str
    offset: Tuple[float, float, float] = (0, 0, 0)
    look_ahead: float = 0.0              # Seconds to predict ahead
    smoothing: float = 0.1               # Position smoothing factor
    rotation_smoothing: float = 0.15     # Rotation smoothing factor

@dataclass
class ObstacleInfo:
    """Information about a detected obstacle."""
    object_name: str
    position: Tuple[float, float, float]
    bounding_box: Tuple[float, float, float]
    distance_to_camera: float
    blocks_view: bool
    suggested_avoidance: str             # "push", "orbit", "zoom"

@dataclass
class FollowCameraConfig:
    """Complete follow camera configuration."""
    mode: FollowMode
    target: FollowTarget

    # Distance/framing
    distance_min: float = 2.0
    distance_max: float = 10.0
    distance_ideal: float = 5.0

    # Height
    height_min: float = 0.5
    height_max: float = 10.0
    height_ideal: float = 2.0

    # Angle constraints
    horizontal_angle_range: Tuple[float, float] = (-180, 180)
    vertical_angle_range: Tuple[float, float] = (-30, 60)

    # Obstacle avoidance
    avoidance_enabled: bool = True
    avoidance_distance: float = 0.5      # Min distance to obstacles
    avoidance_method: str = "smooth_push"  # smooth_push, snap, orbit

    # Collision
    collision_enabled: bool = True
    collision_radius: float = 0.3

    # Prediction
    prediction_enabled: bool = True
    prediction_frames: int = 30          # Frames to look ahead

    # Smoothing
    position_damping: float = 0.1
    rotation_damping: float = 0.15
    fov_damping: float = 0.05
```

### Acceptance Criteria
- [ ] Module structure created
- [ ] Core types defined
- [ ] Configuration system works
- [ ] State persistence functional

---

## REQ-FOLLOW-MODE: Follow Camera Modes
**Priority**: P0
**Status**: Planned

Multiple camera following modes for different scenarios.

### Mode Definitions

#### 1. Side-Scroller Mode
```yaml
side_scroller:
  description: "Camera locked to side plane, following subject along axis"

  # Movement plane
  plane: "xz"               # xy, xz, yz - plane camera moves on
  lock_axis: "y"            # Axis locked (depth)

  # Following behavior
  follow_axis: "x"          # Primary axis to follow
  lead_distance: 0.0        # How far ahead camera sits
  lag_distance: 0.5         # Smooth follow lag

  # Framing
  vertical_alignment: "center"  # top, center, bottom
  horizontal_alignment: "left"  # left, center, right (leading room)

  # Constraints
  allowed_area:
    x: [-100, 100]
    y: [0, 0]               # Locked
    z: [-10, 50]

  # Example: Classic 2.5D platformer view
  preset_classic:
    plane: "xz"
    lock_axis: "y"
    distance: 15
    height: 3
```

#### 2. Over-Shoulder Mode
```yaml
over_shoulder:
  description: "Third-person camera behind and above subject shoulder"

  # Positioning
  offset:
    behind: 3.0             # Distance behind subject
    height: 1.5             # Height above subject
    horizontal: 0.3         # Slight offset to side (for shoulder)

  # Rotation
  look_offset:
    pitch: -10              # Degrees down
    yaw: 0                  # Left/right offset

  # Behavior
  rotation_follows_subject: true
  interpolate_rotation: true

  # Obstacle handling
  on_obstacle:
    action: "zoom_in"       # zoom_in, push_forward, orbit_away

  # Examples
  preset_third_person:
    offset: [0, 1.8, 4.0]
    look_offset: [0, 0, 0]
    smoothing: 0.1

  preset_shooter:
    offset: [0.5, 1.5, 2.5]
    look_offset: [0, 5, 0]
    smoothing: 0.05         # Faster response

  preset_cinematic:
    offset: [0.8, 2.0, 5.0]
    look_offset: [-5, 0, 0]
    smoothing: 0.2          # Slower, more dramatic
```

#### 3. Chase Mode
```yaml
chase:
  description: "Camera follows subject from behind, maintaining pursuit angle"

  # Distance
  distance:
    min: 3.0
    max: 20.0
    ideal: 8.0
    dynamic: true           # Adjust based on speed

  # Position
  position_mode: "behind"   # behind, side_left, side_right, above

  # Speed-based behavior
  speed_response:
    enabled: true
    # Camera backs off when subject moves fast
    distance_multiplier: 1.5  # At max speed
    speed_threshold: 10.0     # m/s

  # Cornering
  corner_prediction:
    enabled: true
    look_ahead_distance: 5.0  # Meters
    smooth_cornering: true

  # Examples
  preset_car_chase:
    distance: [5, 15]
    height: 1.5
    position_mode: "behind"
    speed_response: true

  preset_spaceship:
    distance: [10, 50]
    height: 0
    position_mode: "behind"
    roll_follows_subject: true

  preset_runner:
    distance: [3, 8]
    height: 1.2
    position_mode: "behind"
    speed_response: true
```

#### 4. Chase-Side Mode
```yaml
chase_side:
  description: "Camera follows subject from the side"

  # Positioning
  side: "right"             # left, right, auto (based on action)
  distance: 5.0
  height: 1.5

  # Behavior
  maintain_side: true       # Stay on same side always
  switch_threshold: 0.0     # When to switch sides (0 = never)

  # Lead
  lead_subject: false       # Camera ahead of subject
  lead_distance: 0.0

  # Examples
  preset_car_side:
    side: "right"
    distance: 8.0
    height: 1.0
    lead_subject: true
    lead_distance: 3.0
```

#### 5. Orbit-Follow Mode
```yaml
orbit_follow:
  description: "Camera orbits around subject while following movement"

  # Orbit parameters
  orbit_radius:
    min: 2.0
    max: 15.0
    current: 5.0

  orbit_speed: 0.5          # Rotations per second
  orbit_direction: "cw"     # cw, ccw, auto

  # Following
  follow_strength: 0.8      # How much to follow vs orbit
  center_offset: [0, 1, 0]  # Offset from subject center

  # Auto-orbit triggers
  auto_orbit:
    on_idle: true           # Orbit when subject stationary
    idle_threshold: 2.0     # Seconds of no movement
    on_action: false        # Orbit during action

  # Examples
  preset_slow_orbit:
    orbit_speed: 0.2
    follow_strength: 0.5

  preset_action_orbit:
    orbit_speed: 0.1
    follow_strength: 0.9    # Mostly following, slight orbit
```

#### 6. Lead Mode
```yaml
lead:
  description: "Camera leads subject, showing where they're going"

  # Positioning
  lead_distance: 10.0       # Distance ahead of subject
  lead_angle: 0             # Degrees from subject's forward
  height: 3.0

  # Look direction
  look_at_subject: true     # Camera faces subject
  look_ahead: false         # Camera faces forward

  # Dynamic adjustment
  adjust_to_path: true      # Lead based on predicted path

  # Examples
  preset_car_lead:
    lead_distance: 15.0
    height: 2.0
    look_at_subject: true

  preset_runner_lead:
    lead_distance: 5.0
    height: 1.5
    look_at_subject: true
```

#### 7. Aerial Mode
```yaml
aerial:
  description: "Top-down or high-angle following view"

  # Positioning
  height: 20.0
  angle: 45                 # Degrees from vertical (0 = straight down)

  # Following
  follow_speed: 0.5
  center_offset: [0, 0, 0]

  # Zoom
  auto_zoom:
    enabled: true
    height_range: [10, 50]
    speed_based: true       # Higher when fast

  # Examples
  preset_top_down:
    height: 15.0
    angle: 90               # Straight down

  preset_isometric:
    height: 20.0
    angle: 45

  preset_drone_follow:
    height: 30.0
    angle: 30
    auto_zoom: true
```

#### 8. Free Roam Mode
```yaml
free_roam:
  description: "Game-style free camera with collision"

  # Constraints
  max_distance: 50.0        # From subject
  min_distance: 2.0

  # Collision
  collision_enabled: true
  collision_radius: 0.5

  # Input response
  position_smoothing: 0.1
  rotation_smoothing: 0.15

  # Examples
  preset_game_camera:
    collision_enabled: true
    position_smoothing: 0.08
```

### Mode Transitions
```yaml
transitions:
  # Smooth transitions between modes
  enabled: true
  duration: 1.0             # Seconds for transition

  # Transition types
  types:
    - cut                   # Instant switch
    - blend                 # Smooth interpolation
    - orbit                 # Orbit to new position
    - dolly                 # Physical camera move

  # When to transition
  triggers:
    on_script: true         # Scripted transitions
    on_obstacle: false      # Don't auto-transition for obstacles
    on_action: false        # Don't auto-transition for actions
```

### Acceptance Criteria
- [ ] All 8 follow modes implemented
- [ ] Mode transitions work smoothly
- [ ] Presets for each mode available
- [ ] Modes configurable via YAML

---

## REQ-FOLLOW-FRAME: Intelligent Framing
**Priority**: P1
**Status**: Planned

Automatic composition and framing that adjusts dynamically.

### Framing Rules
```yaml
framing:
  # Rule of thirds grid
  rule_of_thirds:
    enabled: true
    subject_position: "left_third"  # left_third, center, right_third
    vertical_position: "top_third"  # top_third, center, bottom_third

  # Headroom
  headroom:
    enabled: true
    amount: 0.15            # Percentage of frame

  # Look room (leading room)
  look_room:
    enabled: true
    amount: 0.2             # Percentage of frame in direction of look

  # Dead zone (center area where small movements don't trigger camera)
  dead_zone:
    enabled: true
    size: [0.1, 0.1]        # Width, height as fraction of frame
```

### Dynamic Framing
```yaml
dynamic_framing:
  # Adjust based on subject size
  subject_size:
    auto_zoom: true         # Zoom out when subject large in frame
    target_size: 0.3        # Target subject size as fraction of frame

  # Adjust based on speed
  speed_based:
    enabled: true
    # Wider shot when moving fast
    fov_increase_rate: 0.1  # Degrees per m/s

  # Action framing
  action:
    # Tighten on subject during action
    enabled: true
    detection: "animation_velocity"  # How to detect action
    fov_decrease: 5         # Degrees to tighten

  # Multiple subjects
  multi_subject:
    enabled: true
    mode: "fit_all"         # fit_all, focus_primary, dynamic
    padding: 0.1            # Extra space around group
```

### Shot Types
```yaml
shot_types:
  extreme_wide:
    subject_size: 0.05
    distance_factor: 3.0

  wide:
    subject_size: 0.15
    distance_factor: 1.5

  medium:
    subject_size: 0.3
    distance_factor: 1.0

  medium_close:
    subject_size: 0.5
    distance_factor: 0.7

  close:
    subject_size: 0.7
    distance_factor: 0.5

  extreme_close:
    subject_size: 0.9
    distance_factor: 0.3
```

### Acceptance Criteria
- [ ] Rule of thirds framing works
- [ ] Headroom and look room maintained
- [ ] Dead zone prevents jittery camera
- [ ] Dynamic framing adjusts to subject speed
- [ ] Multi-subject framing works

---

## REQ-FOLLOW-AVOID: Obstacle Avoidance System
**Priority**: P0
**Status**: Planned

Intelligent obstacle detection and avoidance - the "camera operator" behavior.

### Collision Detection
```yaml
collision_detection:
  # Detection methods
  methods:
    # Ray casting from camera to subject
    raycast:
      enabled: true
      resolution: 9         # 3x3 grid of rays
      max_distance: 100.0

    # Sphere cast for wider detection
    spherecast:
      enabled: true
      radius: 0.5
      max_distance: 100.0

    # Frustum check for objects in view
    frustum_check:
      enabled: true
      check_occlusion: true

  # Collision layers
  layers:
    - "geometry"            # Static environment
    - "dynamic"             # Moving objects
    - "foliage"             # Trees, grass (may ignore)

  # Ignore list
  ignore:
    - "subject"             # Never collide with subject
    - "transparent"         # Glass, water
    - "triggers"            # Game trigger volumes
```

### Obstacle Response
```yaml
obstacle_response:
  # When obstacle detected between camera and subject
  between_camera_and_subject:
    # Priority order of responses
    responses:
      - name: "push_forward"
        condition: "distance < 5"
        action: "move_camera_closer"
        min_distance: 1.0

      - name: "orbit_away"
        condition: "can_orbit"
        action: "rotate_around_subject"
        angle: 45           # Degrees to try

      - name: "raise_up"
        condition: "can_raise"
        action: "move_camera_higher"
        max_height: 10.0

      - name: "zoom_through"
        condition: "transparent_obstacle"
        action: "allow_occlusion"

  # When obstacle is behind camera (camera too close to wall)
  camera_backing:
    action: "push_forward"
    min_distance: 0.5

  # When obstacle is beside camera
  camera_side:
    action: "slide_away"
    slide_distance: 0.5

  # Smoothing
  smoothing:
    position: 0.1
    rotation: 0.15
    avoid_jitter: true      # Don't oscillate between positions
```

### Prediction-Based Avoidance
```yaml
prediction_avoidance:
  # Look ahead to anticipate obstacles
  enabled: true

  # Prediction settings
  frames_ahead: 30          # Frames to predict
  sample_rate: 5            # Check every N frames

  # Pre-avoidance
  pre_avoid:
    enabled: true
    start_distance: 3.0     # Start avoiding at this distance
    blend_duration: 0.5     # Seconds to blend avoidance
```

### Occlusion Handling
```yaml
occlusion_handling:
  # What to do when subject is occluded
  on_occlusion:
    detection:
      method: "raycast"     # raycast, visibility_buffer
      sample_points: 9      # Points to check on subject

    response:
      # Priority order
      - reposition_camera   # Move to better angle
      - push_through        # Move through obstacle (if transparent)
      - cut_away            # Cut to different angle (if pre-solved)

  # Partial occlusion (subject partially visible)
  on_partial_occlusion:
    threshold: 0.5          # Fraction visible before action
    action: "subtle_adjust" # subtle_adjust, major_reposition
```

### Camera "Operator" Behavior
```yaml
operator_behavior:
  # Simulate human camera operator tendencies
  human_like:
    # Slight delay in response (human reaction time)
    reaction_delay: 0.1     # Seconds

    # Prefer certain angles
    angle_preference:
      horizontal: [-45, 45]  # Prefer front-side angles
      vertical: [10, 30]     # Prefer slightly above

    # Smooth, intentional movements
    avoid_jerky_motion: true
    min_movement_time: 0.3   # Seconds for any adjustment

    # Natural breathing (subtle movement)
    breathing:
      enabled: true
      amplitude: 0.01       # Meters
      frequency: 0.25       # Hz (breaths per second)

  # Decision making
  decision:
    # Weight factors for camera position
    weights:
      visibility: 1.0       # Importance of seeing subject
      composition: 0.7      # Importance of good framing
      smoothness: 0.5       # Importance of smooth motion
      distance: 0.3         # Importance of ideal distance
```

### Acceptance Criteria
- [ ] Raycast collision detection works
- [ ] Camera pushes forward when wall behind
- [ ] Camera orbits around obstacles
- [ ] Prediction anticipates obstacles before contact
- [ ] No oscillation or jitter in avoidance
- [ ] Subject never fully occluded

---

## REQ-FOLLOW-PREDICT: Motion Prediction
**Priority**: P1
**Status**: Planned

Predictive tracking for smooth, anticipatory camera movement.

### Trajectory Prediction
```yaml
trajectory_prediction:
  # Predict subject's future position
  enabled: true

  # Methods
  methods:
    # Velocity-based (linear extrapolation)
    velocity:
      enabled: true
      frames: 30            # Frames to predict

    # Path-based (follow known path)
    path:
      enabled: false
      path_object: null     # Curve object to follow

    # Animation-based (read future keyframes)
    animation:
      enabled: true
      read_ahead: true      # Read animation data ahead of time

    # Physics-based (simulate physics)
    physics:
      enabled: false
      simulation_steps: 30

  # Blend predictions
  blend_method: "weighted"  # weighted, best_confidence
  weights:
    velocity: 0.5
    animation: 0.5
```

### Look-Ahead System
```yaml
look_ahead:
  # Camera anticipates subject movement
  enabled: true

  # Settings
  time_ahead: 0.5           # Seconds to look ahead
  blend_factor: 0.3         # How much to use prediction vs current

  # Application
  apply_to:
    position: true          # Camera position anticipates
    rotation: true          # Camera rotation anticipates
    fov: false              # Don't predict FOV changes

  # Smoothing
  smoothing: 0.2

  # Corner prediction (for vehicle following)
  corners:
    enabled: true
    detect_path_change: true
    early_turn_factor: 0.3  # Start turning early
```

### Speed Anticipation
```yaml
speed_anticipation:
  # Adjust camera based on predicted speed changes
  enabled: true

  # Camera behavior based on speed
  behaviors:
    accelerating:
      # Back off slightly when subject accelerating
      distance_multiplier: 1.2
      fov_increase: 5

    decelerating:
      # Move closer when slowing
      distance_multiplier: 0.9
      fov_decrease: 3

    turning:
      # Widen shot for turns
      distance_multiplier: 1.1
      orbit_bias: "outside" # Camera on outside of turn
```

### Acceptance Criteria
- [ ] Trajectory prediction within 10% of actual position
- [ ] Look-ahead reduces camera lag
- [ ] Corner prediction smooths turns
- [ ] Speed anticipation adjusts framing

---

## REQ-FOLLOW-SOLVE: Pre-Solve System
**Priority**: P0
**Status**: Planned

Pre-compute complex camera moves for deterministic, one-shot renders.

### Pre-Solve Workflow
```yaml
pre_solve:
  # Workflow stages
  stages:
    - name: "analyze_scene"
      description: "Analyze scene geometry and subject animation"
      outputs:
        - subject_path
        - obstacles_timeline
        - clearance_map

    - name: "compute_ideal_path"
      description: "Calculate ideal camera path without obstacles"
      outputs:
        - ideal_camera_path
        - ideal_rotation_path

    - name: "apply_avoidance"
      description: "Adjust path for obstacle avoidance"
      outputs:
        - adjusted_camera_path
        - avoidance_events

    - name: "smooth_path"
      description: "Apply smoothing and interpolation"
      outputs:
        - final_camera_path
        - final_rotation_path

    - name: "bake_keyframes"
      description: "Create Blender keyframes"
      outputs:
        - camera_object_with_animation

  # Solve settings
  settings:
    frame_range: "auto"     # auto, or [start, end]
    sample_rate: 1          # Keyframe every N frames
    interpolation: "bezier" # linear, bezier, constant
```

### One-Shot Configuration
```yaml
one_shot:
  # Configure a complex single-take shot
  name: "chase_through_city"

  # Timeline
  timeline:
    fps: 24
    duration: 60            # Seconds

  # Subject
  subject:
    object: "car_hero"
    animation: "car_chase_action"  # Animation data name

  # Camera configuration
  camera:
    mode: "chase"

    # Mode overrides at specific times
    mode_changes:
      - time: 10.0
        mode: "chase_side"
        transition: "blend"
        duration: 1.0

      - time: 25.0
        mode: "orbit_follow"
        transition: "orbit"

      - time: 40.0
        mode: "lead"
        transition: "dolly"

    # Framing changes
    framing_changes:
      - time: 0.0
        shot_type: "medium"

      - time: 15.0
        shot_type: "wide"
        reason: "entering_big_area"

      - time: 35.0
        shot_type: "close"
        reason: "tension_moment"

  # Pre-compute
  pre_compute:
    enabled: true
    output: "baked/chase_shot.camera"
    preview: true           # Generate preview video
```

### Solve Output
```yaml
solve_output:
  # Generated files
  files:
    # Baked camera data
    camera_path:
      format: "yaml"
      path: ".gsd-state/follow_cam/solves/{name}/camera_path.yaml"
      contents:
        - frame
        - position
        - rotation
        - fov
        - mode

    # Blender camera
    blender_camera:
      format: "blend"
      path: "output/{name}_camera.blend"
      contents:
        - camera_object
        - animation_curves

    # Preview video
    preview:
      format: "mp4"
      path: ".gsd-state/follow_cam/previews/{name}.mp4"
      resolution: [1920, 1080]
      fps: 24

    # Solve report
    report:
      format: "yaml"
      path: ".gsd-state/follow_cam/solves/{name}/report.yaml"
      contents:
        - obstacles_encountered
        - avoidance_events
        - mode_transitions
        - solve_time
        - quality_score
```

### Re-Solve on Changes
```yaml
re_solve:
  # When to re-compute camera path
  triggers:
    - subject_animation_changed
    - obstacles_added_removed
    - camera_config_changed
    - frame_range_changed

  # Incremental vs full re-solve
  incremental:
    enabled: true
    affected_range: "auto"  # auto, or frame range
```

### Acceptance Criteria
- [ ] Pre-solve produces deterministic camera path
- [ ] Baked camera animation renders identically every time
- [ ] One-shot configuration handles mode transitions
- [ ] Preview video shows camera movement
- [ ] Solve report documents all decisions

---

## REQ-FOLLOW-ENV: Environment Awareness
**Priority**: P1
**Status**: Planned

Camera awareness of scene geometry for intelligent navigation.

### Scene Analysis
```yaml
scene_analysis:
  # Analyze scene for camera planning
  enabled: true

  # Geometry analysis
  geometry:
    # Static obstacles
    static:
      scan_on_load: true
      cache_result: true
      layers: ["geometry", "architecture"]

    # Dynamic obstacles
    dynamic:
      scan_rate: 1          # Per frame
      layers: ["characters", "vehicles", "physics"]

  # Spatial analysis
  spatial:
    # Generate clearance map
    clearance_map:
      enabled: true
      resolution: 0.5       # Meters per cell
      height_layers: 5      # Vertical slices

    # Generate navigation mesh for camera
    navmesh:
      enabled: true
      agent_height: 2.0
      agent_radius: 0.5
      max_slope: 60         # Degrees

  # Analysis output
  output:
    path: ".gsd-state/follow_cam/scene_analysis/{scene_name}/"
    files:
      - clearance_map.bin
      - navmesh.obj
      - obstacle_list.yaml
```

### Volume Constraints
```yaml
volume_constraints:
  # Define areas where camera can/cannot go
  volumes:
    # Allowed volumes (camera only moves here)
    allowed:
      - name: "play_area"
        type: "box"
        bounds: [[-100, -100, 0], [100, 100, 50]]

    # Forbidden volumes (camera never enters)
    forbidden:
      - name: "interior"
        type: "mesh"
        object: "building_interior"

      - name: "water"
        type: "collection"
        collection: "water_volumes"

    # Preferred volumes (camera prefers these)
    preferred:
      - name: "overlook_positions"
        type: "empties"
        collection: "camera_positions"
```

### Path Planning
```yaml
path_planning:
  # Plan camera path around obstacles
  enabled: true

  # Algorithm
  algorithm: "a_star"       # a_star, rrt, navmesh

  # Settings
  settings:
    # Path smoothness
    smoothness: 0.8
    corner_radius: 2.0      # Min turn radius

    # Avoidance
    obstacle_margin: 1.0    # Extra distance from obstacles

    # Optimization
    optimize_path: true
    max_iterations: 100

  # Path constraints
  constraints:
    max_acceleration: 5.0   # m/s²
    max_velocity: 20.0      # m/s
    max_angular_velocity: 90  # deg/s
```

### Acceptance Criteria
- [ ] Scene analysis generates clearance map
- [ ] Camera respects volume constraints
- [ ] Path planning finds valid routes
- [ ] Dynamic obstacles detected in real-time

---

## REQ-FOLLOW-INTEGRATE: Cinematic System Integration
**Priority**: P1
**Status**: Planned

Integration with existing cinematic rendering system.

### Shot Assembly Integration
```yaml
# Example: Follow camera in shot YAML
shot:
  name: "car_chase_hero"

  # Subject
  subject:
    type: object
    object: "car_hero"
    animation: "chase_action"

  # Follow camera
  camera:
    type: follow            # follow, static, tracked

    follow:
      mode: chase
      preset: car_chase

      overrides:
        distance_ideal: 8.0
        height_ideal: 1.5

      avoidance:
        enabled: true
        method: smooth_push

      prediction:
        enabled: true
        frames_ahead: 30

    # Pre-solve for deterministic render
    pre_solve: true

  # Environment
  environment:
    scene: "city_street"
    obstacles: auto         # Auto-detect from scene

  # Render
  render:
    profile: cycles_production
    motion_blur: true
```

### Animation System Integration
```yaml
animation_integration:
  # Blend follow camera with animation system
  blend_modes:
    - follow_only           # Pure follow behavior
    - animation_only        # Use baked animation only
    - follow_plus_animation # Follow + animation offset
    - animation_with_follow # Animation primary, follow for avoidance

  # Follow camera as animation modifier
  as_modifier:
    enabled: true
    # Take baked animation and apply follow behavior
    apply_avoidance: true
    apply_smoothing: true
```

### Render Pipeline Integration
```yaml
render_integration:
  # Follow camera in render pipeline
  stages:
    - name: "pre_solve"
      when: "before_render"
      action: "compute_camera_path"

    - name: "validate_solve"
      when: "after_solve"
      action: "check_for_issues"

    - name: "apply_to_scene"
      when: "before_render"
      action: "create_camera_object"

  # Batch rendering with pre-solved cameras
  batch:
    pre_solve_all: true
    parallel_solve: true
    render_after_solve: true
```

### Acceptance Criteria
- [ ] Follow camera works in shot YAML
- [ ] Pre-solve integrates with render pipeline
- [ ] Blend modes work correctly
- [ ] Batch rendering supported

---

## REQ-FOLLOW-DEBUG: Debug & Visualization
**Priority**: P2
**Status**: Planned

Debugging and visualization tools for follow camera development.

### Debug Overlays
```yaml
debug_overlays:
  # Visualize camera behavior
  visualizations:
    # Camera frustum
    frustum:
      enabled: true
      color: [0, 1, 0, 0.3]

    # Target position
    target:
      enabled: true
      show_prediction: true
      prediction_color: [1, 1, 0, 0.5]

    # Obstacle detection
    obstacles:
      enabled: true
      show_rays: true
      show_collisions: true
      collision_color: [1, 0, 0, 0.5]

    # Path
    path:
      enabled: true
      show_ideal: true
      show_actual: true
      show_avoidance: true

    # Dead zones
    dead_zones:
      enabled: true
      color: [0, 0, 1, 0.2]

  # HUD display
  hud:
    enabled: true
    show:
      - current_mode
      - distance_to_subject
      - obstacle_count
      - prediction_accuracy
```

### Debug Output
```yaml
debug_output:
  # Log camera decisions
  logging:
    enabled: true
    level: "info"           # debug, info, warning, error
    file: ".gsd-state/follow_cam/debug.log"

  # Frame-by-frame analysis
  frame_analysis:
    enabled: true
    output: ".gsd-state/follow_cam/frames/"
    per_frame:
      - camera_position
      - camera_rotation
      - target_position
      - obstacles_detected
      - avoidance_action_taken
      - mode
      - prediction_error
```

### Acceptance Criteria
- [ ] Debug overlays render in viewport
- [ ] Frame-by-frame analysis available
- [ ] Camera decisions logged

---

## Summary

| Requirement | Priority | Status | Est. Effort |
|-------------|----------|--------|-------------|
| REQ-FOLLOW-01: Foundation | P1 | Planned | 2-3 days |
| REQ-FOLLOW-MODE: Follow Modes | P0 | Planned | 5-7 days |
| REQ-FOLLOW-FRAME: Intelligent Framing | P1 | Planned | 3-4 days |
| REQ-FOLLOW-AVOID: Obstacle Avoidance | P0 | Planned | 5-7 days |
| REQ-FOLLOW-PREDICT: Motion Prediction | P1 | Planned | 3-4 days |
| REQ-FOLLOW-SOLVE: Pre-Solve System | P0 | Planned | 4-5 days |
| REQ-FOLLOW-ENV: Environment Awareness | P1 | Planned | 3-4 days |
| REQ-FOLLOW-INTEGRATE: Cinematic Integration | P1 | Planned | 2-3 days |
| REQ-FOLLOW-DEBUG: Debug & Visualization | P2 | Planned | 2-3 days |

**Total Requirements**: 9
**Total Estimated Effort**: 29-40 days

---

## Implementation Roadmap

### Phase 8.0: Follow Camera Foundation (REQ-FOLLOW-01)
- Module structure
- Core types
- Configuration system

### Phase 8.1: Core Follow Modes (REQ-FOLLOW-MODE)
- All 8 follow modes
- Mode transitions
- Presets

### Phase 8.2: Obstacle Avoidance (REQ-FOLLOW-AVOID, REQ-FOLLOW-PREDICT)
- Collision detection
- Avoidance responses
- Prediction system

### Phase 8.3: Pre-Solve System (REQ-FOLLOW-SOLVE, REQ-FOLLOW-ENV)
- Pre-compute workflow
- One-shot configuration
- Scene analysis

### Phase 8.4: Integration & Polish (REQ-FOLLOW-INTEGRATE, REQ-FOLLOW-FRAME, REQ-FOLLOW-DEBUG)
- Cinematic integration
- Intelligent framing
- Debug tools

---

## Dependencies

- **REQ-CINE-CAM**: Camera system for camera object creation
- **REQ-CINE-ANIM**: Animation system for baked paths
- **REQ-CINE-SHOT**: Shot assembly for YAML integration
- **Blender Python API**: For ray casting, collision detection

---

## Example Use Cases

### 1. Car Chase Sequence
```yaml
shot:
  name: "car_chase_downtown"

  subject:
    object: "hero_car"
    animation: "chase_path"

  camera:
    type: follow
    follow:
      mode: chase
      preset: car_chase
      speed_response: true
      corner_prediction: true

    avoidance:
      enabled: true
      method: smooth_push

  pre_solve: true
```

### 2. Spaceship Dogfight
```yaml
shot:
  name: "space_battle"

  subject:
    object: "fighter_01"
    animation: "combat_path"

  camera:
    type: follow
    follow:
      mode: chase
      preset: spaceship
      roll_follows_subject: true
      distance: [10, 50]

    avoidance:
      enabled: false  # No obstacles in space

    framing:
      dynamic: true
      action_aware: true

  pre_solve: true
```

### 3. Platformer Side-Scroller
```yaml
shot:
  name: "level_01"

  subject:
    object: "player"
    animation: "gameplay"

  camera:
    type: follow
    follow:
      mode: side_scroller
      preset: classic
      lag_distance: 0.5

    avoidance:
      enabled: false  # Locked plane

  render:
    profile: eevee_draft
```

### 4. Cinematic One-Shot
```yaml
one_shot:
  name: "building_assault"

  timeline:
    duration: 120

  subject:
    object: "squad_leader"

  camera:
    mode_changes:
      - time: 0
        mode: over_shoulder
      - time: 30
        mode: chase_side
        transition: dolly
      - time: 60
        mode: orbit_follow
      - time: 90
        mode: lead

    framing_changes:
      - time: 0
        shot: medium
      - time: 45
        shot: wide
      - time: 75
        shot: close

  pre_solve: true
  preview: true
```
