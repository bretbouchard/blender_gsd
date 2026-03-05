# GSD Utilities Guide

**Safe, production-ready utilities for the Blender GSD pipeline.**

---

## Table of Contents

1. [Overview](#overview)
2. [When to Use Each Module](#when-to-use-each-module)
3. [Safety Module](#safety-module)
4. [Limits Module](#limits-module)
5. [Math Safe Module](#math-safe-module)
6. [Drivers Module](#drivers-module)
7. [Tips Module](#tips-module)
8. [Generative Module](#generative-module)
9. [Common Patterns](#common-patterns)
10. [Migration Guide](#migration-guide)

---

## Overview

The `lib/utils` package provides four core modules that address limitations identified during the Council of Ricks review:

| Module | Problem Solved | Key Benefit |
|--------|---------------|-------------|
| **safety** | File corruption, data loss | Atomic writes, validation |
| **limits** | System crashes, slow performance | Proactive warnings, benchmarks |
| **math_safe** | Gimbal lock, incorrect blending | Quaternion interpolation, safe math |
| **drivers** | Broken drivers after rename | Named variables, repair tools |
| **tips** | Slow workflows, repetitive tasks | 30+ advanced Blender tips |
| **generative** | Complex layered geometry | Multi-layer shells, faceted remesh |

---

## When to Use Each Module

### Decision Flowchart

```
┌─────────────────────────────────────────────────────────────┐
│ What are you doing?                                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   Saving/Loading        Math/Rotation        Creating Drivers
   YAML files?           operations?          or constraints?
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌──────────┐         ┌──────────┐
   │ safety  │          │math_safe │         │ drivers  │
   └─────────┘          └──────────┘         └──────────┘
        │                     │                     │
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Creating lots of │
                    │ objects/particles?│
                    └──────────────────┘
                              │
                              ▼
                       ┌──────────┐
                       │  limits  │
                       └──────────┘
```

### Quick Reference

| Task | Module | Function |
|------|--------|----------|
| Save pose/rig config | `safety` | `SafeYAML.save()` |
| Load any YAML file | `safety` | `SafeYAML.load()` |
| Check particle count | `limits` | `check_limit('max_particles', count)` |
| Time a function | `limits` | `@timed('name', target_ms=10)` |
| Interpolate rotation | `math_safe` | `interpolate_rotation(a, b, t, mode='quaternion')` |
| Smooth steering cutoff | `math_safe` | `smooth_falloff(value, threshold)` |
| Blend scale values | `math_safe` | `safe_scale_blend(current, delta, opacity)` |
| Create wheel driver | `drivers` | `create_wheel_rotation_driver()` |
| Fix broken drivers | `drivers` | `repair_drivers(obj)` |

---

## Safety Module

**File:** `lib/utils/safety.py`

### Why Use It

The safety module prevents the most common causes of data loss and corruption:

1. **File corruption on crash** - Atomic writes ensure files are never half-written
2. **Invalid data loading** - Schema validation catches malformed YAML
3. **ID collisions** - Automatic unique ID generation prevents overwrites

### When to Use

| Situation | Use This |
|-----------|----------|
| Saving pose files | `SafeYAML.save(path, data, schema='pose')` |
| Saving rig configs | `SafeYAML.save(path, data, schema='rig')` |
| Saving vehicle configs | `SafeYAML.save(path, data, schema='vehicle')` |
| Loading any config | `SafeYAML.load(path, schema='...')` |
| Creating new pose IDs | `generate_unique_id(base_name, existing_ids)` |

### Examples

#### Atomic Write with Validation

```python
from lib.utils import SafeYAML

# OLD WAY (unsafe):
# with open('pose.yaml', 'w') as f:
#     yaml.dump(data, f)  # Can corrupt on crash!

# NEW WAY (safe):
SafeYAML.save('pose.yaml', pose_data, schema='pose')
# - Validates against pose schema
# - Writes atomically (temp file, then rename)
# - Creates backup of existing file
```

#### Load with Validation

```python
from lib.utils import SafeYAML

# Load with validation (raises on invalid)
config = SafeYAML.load('pose.yaml', schema='pose', strict=True)

# Load with default fallback
config = SafeYAML.load('optional.yaml', schema='pose', default={'bones': {}})

# Load without validation (not recommended)
config = SafeYAML.load('legacy.yaml')
```

#### Unique ID Generation

```python
from lib.utils import generate_unique_id

existing = {'walk', 'walk_1', 'run'}

# Generate new ID
new_id = generate_unique_id('walk', existing)  # Returns 'walk_2'

# Would return 'jump' (doesn't exist yet)
new_id = generate_unique_id('jump', existing)  # Returns 'jump'
```

#### Direct Atomic Write (without validation)

```python
from lib.utils import atomic_write

atomic_write('data.yaml', data, create_backup=True)
```

### Available Schemas

| Schema Name | Validates |
|-------------|-----------|
| `pose` | Pose files with bones, rotations, metadata |
| `rig` | Rig definitions with bone hierarchy |
| `vehicle` | Vehicle configs with wheels, dimensions |
| `crowd` | Crowd simulation configs |
| `layer_stack` | Animation layer definitions |

---

## Limits Module

**File:** `lib/utils/limits.py`

### Why Use It

The limits module prevents:

1. **System crashes** from too many particles/objects
2. **Slow playback** from too many shape keys or layers
3. **Memory exhaustion** from large files
4. **Unexpected performance** by benchmarking operations

### When to Use

| Situation | Use This |
|-----------|----------|
| Creating crowds/particles | `check_limit('max_particles', count)` |
| Creating onion skins | `check_limit('max_onion_skins', count)` |
| Adding shape keys | `check_limit('max_shape_keys', count)` |
| Adding animation layers | `check_limit('max_layers', count)` |
| Timing functions | `@timed('name', target_ms=10)` |
| Timing code blocks | `with performance_block('name'):` |

### Default Limits

```python
from lib.utils import LIMITS, get_all_limits

# View all limits
limits = get_all_limits()
# {
#   'max_particles': {'value': 5000, 'description': '...'},
#   'max_onion_skins': {'value': 10, ...},
#   'max_shape_keys': {'value': 100, ...},
#   'max_layers': {'value': 50, ...},
#   ...
# }

# Get specific limit
max_particles = get_limit('max_particles')  # 5000

# Override for specific project
set_limit('max_particles', 10000, "High-end machine")
```

### Examples

#### Check Before Creating

```python
from lib.utils import check_limit

def create_crowd(count):
    # Check limit first
    if not check_limit('max_particles', count):
        # Limit exceeded, reduce count
        count = get_limit('max_particles')
        print(f"Reduced crowd to {count}")

    # Create crowd...
```

#### Decorator for Timing

```python
from lib.utils import timed

@timed('layer_blend', target_ms=10)
def blend_layers(system, frame):
    # If this takes >10ms, you'll get a warning
    return system.blend(frame)

# Get performance report
from lib.utils import get_performance_report
report = get_performance_report()
# {'layer_blend': {'avg_time_ms': 8.5, 'max_time_ms': 15.2, ...}}
```

#### Context Manager for Timing

```python
from lib.utils import performance_block

def complex_operation():
    with performance_block('expensive_op', target_ms=100) as metric:
        # Do expensive stuff
        result = calculate_everything()

    print(f"Operation took {metric.elapsed_ms:.1f}ms")
    return result
```

#### Temporarily Change Limit

```python
from lib.utils import limit_context

# Temporarily allow more particles
with limit_context('max_particles', 10000):
    create_large_battle_scene()

# Limit restored to original value
```

---

## Math Safe Module

**File:** `lib/utils/math_safe.py`

### Why Use It

The math_safe module prevents:

1. **Gimbal lock** - Using quaternion interpolation instead of Euler linear
2. **Incorrect blending** - Safe scale blending that handles negative values
3. **Jerky animations** - Smooth falloff functions instead of hard cutoffs
4. **Numerical instability** - Properly normalized operations

### When to Use

| Situation | Problem | Solution |
|-----------|---------|----------|
| Blending rotations | Gimbal lock | `interpolate_rotation(a, b, t, mode='quaternion')` |
| Steering at low angles | Jerky motion | `smooth_falloff(angle, threshold)` |
| Blending scale values | Negative value bugs | `safe_scale_blend(current, delta, opacity)` |
| Interpolating anything | Harsh transitions | `smoothstep()` or `smootherstep()` |
| Normalizing angles | Wrap-around bugs | `normalize_angle(angle)` |

### Examples

#### Safe Rotation Interpolation

```python
from lib.utils import interpolate_rotation, euler_degrees_to_radians
from math import degrees

# Euler angles in degrees
rot_a = euler_degrees_to_radians((0, 0, 0))
rot_b = euler_degrees_to_radians((0, 90, 0))

# OLD WAY (can cause gimbal lock):
# result = tuple(rot_a[i] + t * (rot_b[i] - rot_a[i]) for i in range(3))

# NEW WAY (safe):
result = interpolate_rotation(rot_a, rot_b, t=0.5, mode='quaternion')
# Returns smooth, correct interpolation
```

#### Smooth Falloff for Steering

```python
from lib.utils import smooth_falloff

# OLD WAY (hard cutoff):
# if abs(angle) < 0.1:
#     return (0, 0)  # Jerky at low angles

# NEW WAY (smooth):
angle = smooth_falloff(angle, threshold=0.5)
# Returns 0 at angle=0, smoothly increases to full value at threshold
```

#### Safe Scale Blending

```python
from lib.utils import safe_scale_blend

current = (1.0, 1.0, 1.0)
delta = (1.5, 0.8, -0.5)  # Note: negative scale!
opacity = 0.7

# OLD WAY (broken for negative):
# result = scale[i] * delta[i] ** opacity  # NaN for negative!

# NEW WAY (safe):
result = safe_scale_blend(current, delta, opacity, mode='multiplicative')
# Returns: (1.35, 0.94, 0.68) - correct values
```

#### Smooth Transitions

```python
from lib.utils import smoothstep, smootherstep

# Linear (harsh)
t = 0.5
linear = t  # 0.5

# Smooth (gentle S-curve)
smooth = smoothstep(0, 1, t)  # 0.5, but curved

# Smoother (Perlin's improved)
smoother = smootherstep(0, 1, t)  # 0.5, more pronounced curve

# Use in animation
def blend_poses(pose_a, pose_b, t):
    t = smoothstep(0, 1, t)  # Smooth the transition
    return lerp_pose(pose_a, pose_b, t)
```

#### Angle Utilities

```python
from lib.utils import normalize_angle, angle_difference

# Normalize to [-pi, pi]
angle = normalize_angle(7.5)  # Returns ~1.22 (wrapped)

# Shortest difference between angles
diff = angle_difference(0.1, 6.2)  # Returns ~-0.18 (shortest path)
```

---

## Drivers Module

**File:** `lib/utils/drivers.py`

### Why Use It

The drivers module prevents:

1. **Broken drivers on rename** - Using variable references instead of hardcoded names
2. **Driver expression errors** - Validation before creation
3. **Lost driver connections** - Repair tools for fixing broken references

### When to Use

| Situation | Use This |
|-----------|----------|
| Creating wheel rotation driver | `create_wheel_rotation_driver()` |
| Creating IK/FK blend driver | `create_ik_influence_driver()` |
| Creating custom driver | `add_safe_driver()` or `DriverBuilder` |
| After renaming objects | `repair_drivers(obj)` |
| Checking driver health | `validate_all_drivers()` |

### Examples

#### Safe Driver Creation

```python
from lib.utils import add_safe_driver

# OLD WAY (breaks on rename):
# driver.expression = f"{vehicle.name}.location[0] / (2 * pi * 0.35)"
# If vehicle is renamed, driver breaks!

# NEW WAY (safe):
add_safe_driver(
    wheel,
    "rotation_euler", 1,
    expression="distance / (2 * pi * radius)",
    variables={
        'distance': (vehicle, "location[0]"),  # Reference, not name
        'radius': (None, "0.35"),  # Constant value
    }
)
# Driver uses named variables that update on rename
```

#### Fluent Builder Pattern

```python
from lib.utils import DriverBuilder

# More readable for complex drivers
driver = (
    DriverBuilder(wheel, "rotation_euler", 1)
    .expression("distance / (2 * pi * radius)")
    .variable("distance", vehicle, "location[0]")
    .variable("pi", None, "3.14159265359")
    .variable("radius", None, str(wheel_radius))
    .build()
)
```

#### Common Pattern: Wheel Rotation

```python
from lib.utils import create_wheel_rotation_driver

# One-liner for common wheel setup
driver = create_wheel_rotation_driver(
    wheel_obj=wheel,
    vehicle_obj=vehicle,
    radius=0.35,
    axis='Y'
)
```

#### Repair After Rename

```python
from lib.utils import repair_drivers

# Rename an object
old_name = vehicle.name
vehicle.name = "hero_car"

# Repair drivers that referenced old name
repaired = repair_drivers(vehicle, rename_map={old_name: "hero_car"})
print(f"Repaired: {repaired}")
# ['distance: vehicle -> hero_car', ...]
```

#### Validate All Drivers

```python
from lib.utils import validate_all_drivers

# Check entire scene for driver issues
issues = validate_all_drivers()
# {
#   'wheel_FL': ['rotation_euler: Variable "dist" references missing object "old_vehicle"'],
#   ...
# }

for obj_name, obj_issues in issues.items():
    print(f"{obj_name}:")
    for issue in obj_issues:
        print(f"  - {issue}")
```

---

## Common Patterns

### Saving a Pose

```python
from lib.utils import SafeYAML, generate_unique_id, check_limit

def save_pose(armature, name, category='custom'):
    # Check bone count
    bone_count = len(armature.pose.bones)
    check_limit('max_pose_bones', bone_count)

    # Generate unique ID
    existing = get_existing_pose_ids()
    pose_id = generate_unique_id(name, existing)

    # Build pose data
    pose_data = {
        'id': pose_id,
        'name': name,
        'category': category,
        'bones': capture_bones(armature),
    }

    # Safe save with validation
    path = f'configs/poses/{category}/{pose_id}.yaml'
    SafeYAML.save(path, pose_data, schema='pose')

    return pose_id
```

### Creating a Crowd

```python
from lib.utils import check_limit, get_limit, performance_block

def create_crowd(config):
    count = config['spawn']['count']

    # Check limit
    if not check_limit('max_particles', count):
        count = get_limit('max_particles')
        config['spawn']['count'] = count

    # Create with timing
    with performance_block('crowd_creation', target_ms=1000) as metric:
        crowd = create_boids_system(config)

    print(f"Created {count} agents in {metric.elapsed_ms:.0f}ms")
    return crowd
```

### Blending Animation Layers

```python
from lib.utils import (
    interpolate_rotation,
    safe_scale_blend,
    smoothstep,
    timed,
)
from math import radians, degrees

@timed('layer_blend', target_ms=10)
def blend_layer_bones(base_pose, layer_data, opacity, bone_mask=None):
    """Blend a layer onto base pose safely."""
    result = {}

    for bone_name, base_bone in base_pose.items():
        if bone_name not in layer_data:
            result[bone_name] = base_bone
            continue

        if bone_mask and bone_name not in bone_mask:
            result[bone_name] = base_bone
            continue

        layer_bone = layer_data[bone_name]

        # Smooth opacity
        t = smoothstep(0, 1, opacity)

        # Safe rotation interpolation (quaternion)
        rot = interpolate_rotation(
            base_bone['rotation'],
            layer_bone['rotation'],
            t,
            mode='quaternion'
        )

        # Safe scale blending
        scale = safe_scale_blend(
            base_bone['scale'],
            layer_bone['scale'],
            t,
            mode='multiplicative'
        )

        result[bone_name] = {
            'location': lerp_vector(base_bone['location'], layer_bone['location'], t),
            'rotation': rot,
            'scale': scale,
        }

    return result
```

### Setting Up a Vehicle

```python
from lib.utils import (
    SafeYAML,
    create_wheel_rotation_driver,
    smooth_falloff,
)

def setup_vehicle(vehicle_config_path):
    # Load config safely
    config = SafeYAML.load(vehicle_config_path, schema='vehicle')

    vehicle = get_vehicle_object()
    wheels = get_wheel_objects()

    # Setup each wheel
    for wheel_config in config['wheels']:
        wheel = wheels[wheel_config['id']]

        # Create rotation driver
        create_wheel_rotation_driver(
            wheel_obj=wheel,
            vehicle_obj=vehicle,
            radius=wheel_config['radius'],
            axis='Y'
        )

        # Setup steering with smooth falloff
        if wheel_config['steering']:
            steering_angle = get_steering_input()
            # Apply smooth falloff for low angles
            smooth_angle = smooth_falloff(steering_angle, threshold=0.5)
            wheel.rotation_euler[2] = smooth_angle

    return vehicle
```

---

## Migration Guide

### From Unsafe YAML Writes

```python
# BEFORE (unsafe)
with open('pose.yaml', 'w') as f:
    yaml.dump(data, f)

# AFTER (safe)
from lib.utils import SafeYAML
SafeYAML.save('pose.yaml', data, schema='pose')
```

### From Hardcoded Driver Expressions

```python
# BEFORE (breaks on rename)
driver.expression = f"{obj.name}.location[0] * 2"

# AFTER (safe)
from lib.utils import add_safe_driver
add_safe_driver(
    target, "location", 0,
    expression="pos * 2",
    variables={'pos': (obj, "location[0]")}
)
```

### From Euler Linear Interpolation

```python
# BEFORE (gimbal lock risk)
result = tuple(a[i] + t * (b[i] - a[i]) for i in range(3))

# AFTER (safe)
from lib.utils import interpolate_rotation
result = interpolate_rotation(a, b, t, mode='quaternion')
```

### From Hard Cutoffs

```python
# BEFORE (jerky)
if abs(value) < threshold:
    value = 0

# AFTER (smooth)
from lib.utils import smooth_falloff
value = smooth_falloff(value, threshold)
```

### From Power-Based Scale Blending

```python
# BEFORE (broken for negative)
result = scale[i] ** opacity

# AFTER (safe)
from lib.utils import safe_scale_blend
result = safe_scale_blend(current, delta, opacity)
```

---

## Tips Module

**File:** `lib/tips/__init__.py`

### Why Use It

The tips module provides 30+ advanced Blender workflow utilities from Robin Squares' tutorial:

1. **Render presets** - Quick switch between preview/final/animation renders
2. **Material presets** - Pre-configured surface materials (metal, plastic, glass)
3. **Scene organization** - Auto-sort objects, batch material assignment
4. **Animation helpers** - Camera shake, seamless loops, secondary motion
5. **Procedural effects** - Wear edges, dirt accumulation, subsurface scatter

### When to Use

| Situation | Use This |
|-----------|----------|
| Quick render setup | `apply_render_preset("preview")` |
| Fast material prototyping | `apply_material_preset(mat, "metal_shiny")` |
| Organizing scenes | `auto_organize_collections()` |
| Adding camera shake | `setup_camera_shake(camera, intensity=0.05)` |
| Scene analysis | `show_scene_stats()` |
| Batch material assign | `batch_material_assign("MyMaterial")` |

### Available Render Presets

| Preset | Resolution | Samples | Use Case |
|--------|------------|---------|----------|
| `preview` | 25% | 64 | Fast viewport previews |
| `final` | 100% | 256 | Production renders |
| `animation` | 50% | 128 | Animation renders |

### Available Material Presets

| Preset | Metallic | Roughness | Use Case |
|--------|----------|-----------|----------|
| `metal_shiny` | 0.9 | 0.1 | Polished metal |
| `metal_brushed` | 0.8 | 0.4 | Brushed metal |
| `plastic_glossy` | 0.0 | 0.0 | Glossy plastic |
| `plastic_matte` | 0.0 | 0.8 | Matte plastic |
| `rubber` | 0.0 | 0.9 | Rubber/grip surfaces |
| `glass` | 0.0 | 0.0 | Transparent glass |

### Examples

#### Quick Render Setup

```python
from lib.tips import apply_render_preset, RENDER_PRESETS

# Apply preview preset for fast testing
apply_render_preset("preview")

# View available presets
print(RENDER_PRESETS.keys())  # ['preview', 'final', 'animation']
```

#### Material Prototyping

```python
from lib.tips import apply_material_preset, MATERIAL_PRESETS
import bpy

# Create and apply preset
mat = bpy.data.materials.new("MyMetal")
apply_material_preset(mat, "metal_shiny")

# View available presets
print(MATERIAL_PRESETS.keys())
```

#### Scene Organization

```python
from lib.tips import auto_organize_collections, show_scene_stats

# Auto-sort selected objects by type
collections = auto_organize_collections()
# Creates: Auto_Mesh, Auto_Light, Auto_Camera, etc.

# Get scene statistics
stats = show_scene_stats()
print(f"Polygons: {stats['polygons']:,}")
```

#### Animation Helpers

```python
from lib.tips import setup_camera_shake, setup_animation_loop

# Add camera shake
setup_camera_shake(
    camera,
    intensity=0.05,   # Shake amount
    frequency=2.0,    # Hz
    frames=60         # Duration
)

# Create seamless loop
setup_animation_loop(action, loop_start=50, loop_end=100)
```

---

## Generative Module

**File:** `lib/geometry_nodes/generative.py`

### Why Use It

The generative module provides multi-layer shell and faceted remesh utilities from Curtis Holt's tutorial:

1. **MultiLayerShell** - Create complex layered geometry for visual depth
2. **FacetedRemesh** - Prepare geometry for stylized low-poly look
3. **GenerativeShell** - Extended shell with noise/rotation/scale variation
4. **ShellLayer** - Dataclass for individual layer configuration

### When to Use

| Situation | Use This |
|-----------|----------|
| Layered armor/panels | `MultiLayerShell` |
| Stylized low-poly look | `FacetedRemesh` |
| Quick shell creation | `create_generative_shell()` |
| Custom layer config | `ShellLayer` dataclass |

### Examples

#### Multi-Layer Shell

```python
from lib.geometry_nodes import MultiLayerShell

# Create layered shell
shell = MultiLayerShell(builder)
shell.add_layer(scale=0.95, offset=-0.02, material="inner")
shell.add_layer(scale=1.0, material="outer")
shell.add_layer(scale=1.02, offset=0.01, material="detail")

result = shell.build(input_mesh)
```

#### Faceted Remesh

```python
from lib.geometry_nodes import FacetedRemesh

# Create faceted remesh setup
faceted = FacetedRemesh(builder)
faceted.set_voxel_size(0.05)
faceted.preserve_edges(angle=30.0)
faceted.store_normals(True)

prepared = faceted.build(input_mesh)
```

#### Generative Shell with Noise

```python
from lib.geometry_nodes import GenerativeShell

# Create shell with variations
shell = GenerativeShell(builder)
shell.add_layer(scale=0.95).add_noise(0.02)
shell.add_layer(scale=1.0).add_rotation_variation(10.0)
shell.add_layer(scale=1.02).add_scale_variation(0.1)

result = shell.build(input_mesh)
```

#### Quick Shell Creation

```python
from lib.geometry_nodes import create_generative_shell

# Create 3-layer shell with noise
result = create_generative_shell(
    builder,
    input_mesh,
    layers=3,
    base_scale=1.0,
    scale_step=-0.02,
    add_noise=True,
    noise_scale=0.02
)
```

---

## Summary

| Module | Key Functions | When to Use |
|--------|--------------|-------------|
| `safety` | `SafeYAML.save()`, `SafeYAML.load()`, `generate_unique_id()` | Any file I/O, config management |
| `limits` | `check_limit()`, `@timed`, `performance_block` | Before creating many objects, timing operations |
| `math_safe` | `interpolate_rotation()`, `smooth_falloff()`, `safe_scale_blend()` | Any rotation/scale blending, smooth transitions |
| `drivers` | `add_safe_driver()`, `DriverBuilder`, `repair_drivers()` | Creating or fixing Blender drivers |
| `tips` | `apply_render_preset()`, `apply_material_preset()`, `auto_organize_collections()` | Quick render setup, material prototyping, scene organization |
| `generative` | `MultiLayerShell`, `FacetedRemesh`, `GenerativeShell` | Layered geometry, stylized remeshing |

**Golden Rules:**

1. **Always use `SafeYAML` for file I/O** - Prevents corruption
2. **Check limits before bulk operations** - Prevents crashes
3. **Use quaternion interpolation for rotations** - Prevents gimbal lock
4. **Use named driver variables** - Prevents broken references
5. **Use smooth falloff instead of hard cutoffs** - Prevents jerky motion
6. **Use render presets for consistent output** - Speeds up workflow
7. **Use generative shells for layered effects** - Adds visual depth

**Golden Rules:**

1. **Always use `SafeYAML` for file I/O** - Prevents corruption
2. **Check limits before bulk operations** - Prevents crashes
3. **Use quaternion interpolation for rotations** - Prevents gimbal lock
4. **Use named driver variables** - Prevents broken references
5. **Use smooth falloff instead of hard cutoffs** - Prevents jerky motion
