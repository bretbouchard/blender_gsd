# Physical Projection Mapping

Complete system for mapping Blender content to real-world projection surfaces with accurate calibration.

## Overview

The Physical Projection Mapping system enables you to:
- Select projector hardware profiles from a database
- Calibrate to real-world surfaces using 3-point or 4-point methods
- Map content to surfaces with proper UV alignment
- Render at projector native resolution

## Quick Start

### 1. Basic Setup

```python
from lib.cinematic.projection.physical import (
    load_profile,
    CalibrationPoint,
    CalibrationType,
    SurfaceCalibration,
    render_for_projector,
)

# Load projector profile
profile = load_profile("Epson_Home_Cinema_2150")

# Define calibration points (3-point for planar surface)
# Format: (world_position, projector_uv)
calibration_points = [
    ((0, 0, 0), (0, 0)),       # Bottom-left: world position, projector UV
    ((2, 0, 0), (1, 0)),       # Bottom-right
    ((0, 1.5, 0), (0, 1)),     # Top-left
]

# Render for projector
output_files = render_for_projector(
    content_path="//content/animation.mp4",
    projector_profile_name="Epson_Home_Cinema_2150",
    calibration_points=calibration_points,
    output_dir="//projector_output/"
)
```

### 2. Using Target Presets

```python
from lib.cinematic.projection.physical import (
    load_profile,
    ContentMappingWorkflow,
)
from lib.cinematic.projection.physical.targets import (
    load_target_preset,
    list_target_presets,
)

# List available presets
presets = list_target_presets()
# ['reading_room', 'garage_door', 'building_facade']

# Load reading room preset
target = load_target_preset("garage_door")

# Create workflow
workflow = ContentMappingWorkflow(
    name="garage_projection",
    projector_profile=load_profile("Epson_Home_Cinema_2150"),
    calibration=target.calibration,
)

# Execute
workflow.setup().calibrate().create_proxy().map_content("//content/video.mp4")
workflow.render("//output/garage/")
```

### 3. Shot YAML Integration

Create a shot YAML file:

```yaml
# shots/garage_projection.yaml
name: "Garage Door Projection"
description: "Halloween projection on garage door"

camera:
  type: projection
  projector_profile: Epson_Home_Cinema_2150
  calibration:
    type: three_point
    points:
      - label: Bottom Left
        world_position: [0, 0, 0]
        projector_uv: [0, 0]
      - label: Bottom Right
        world_position: [4.88, 0, 0]  # 16ft
        projector_uv: [1, 0]
      - label: Top Left
        world_position: [0, 0, 2.13]  # 7ft
        projector_uv: [0, 1]

content:
  source: //content/halloween.mp4
  blend_mode: mix
  intensity: 1.0

output:
  resolution: [1920, 1080]
  format: video
  codec: H264
  color_space: sRGB
  output_path: //output/garage/
```

Build and render:

```python
from lib.cinematic.projection.physical.integration import build_projection_shot

# Build from YAML
result = build_projection_shot("shots/garage_projection.yaml")

if result.success:
    print(f"Profile: {result.profile.name}")
    print(f"Calibration: {result.calibration.name}")

    # Render
    output_files = result.builder.render(frame_start=1, frame_end=250)
    print(f"Rendered {len(output_files)} frames")
else:
    for error in result.errors:
        print(f"Error: {error}")
```

## Calibration

### 3-Point Alignment (Planar Surfaces)

For flat surfaces like walls, screens, garage doors:

```python
from lib.cinematic.projection.physical import (
    CalibrationPoint,
    CalibrationType,
    SurfaceCalibration,
)

calibration = SurfaceCalibration(
    name="garage_door",
    calibration_type=CalibrationType.THREE_POINT,
    points=[
        CalibrationPoint(
            world_position=(0, 0, 0),      # Bottom-left corner
            projector_uv=(0, 0),            # UV origin
            label="Bottom-Left"
        ),
        CalibrationPoint(
            world_position=(4.88, 0, 0),   # Bottom-right (16ft)
            projector_uv=(1, 0),            # UV right edge
            label="Bottom-Right"
        ),
        CalibrationPoint(
            world_position=(0, 0, 2.13),   # Top-left (7ft)
            projector_uv=(0, 1),            # UV top edge
            label="Top-Left"
        ),
    ]
)
```

**Points must define:**
- Point 1: Bottom-left corner (origin)
- Point 2: Bottom-right corner (defines width)
- Point 3: Top-left corner (defines height)

### 4-Point DLT (Non-Planar/Multi-Surface)

For complex surfaces like reading rooms with cabinets:

```python
calibration = SurfaceCalibration(
    name="reading_room",
    calibration_type=CalibrationType.FOUR_POINT_DLT,
    points=[
        CalibrationPoint((0, 0, 0), (0, 0), "BL"),
        CalibrationPoint((2.5, 0, 0), (1, 0), "BR"),
        CalibrationPoint((2.5, 0, 2.0), (1, 1), "TR"),
        CalibrationPoint((0, 0, 2.0), (0, 1), "TL"),
    ]
)
```

**Points must define:**
- Four corners of projection area (clockwise or counter-clockwise)
- Solves full projection matrix using Direct Linear Transform
- Works with irregular/non-planar surfaces

## Supported Projectors

| Manufacturer | Model | Resolution | Throw Ratio | Type |
|-------------|-------|-----------|-------------|------|
| Epson | Home Cinema 2150 | 1920x1080 | 1.32 | Standard |
| Epson | Home Cinema 3800 | 1920x1080 | 1.32 | Standard |
| Epson | Pro Cinema 6050UB | 1920x1080 | 1.0 | Short Throw |
| Epson | LS12000 | 1920x1080 | 1.0 | Short Throw |
| BenQ | MW632ST | 1920x1080 | 0.77 | Short Throw |
| BenQ | TH685 | 1920x1080 | 1.5 | Standard |
| BenQ | W2700 | 1920x1080 | 1.13 | Standard |
| Optoma | UHD38 | 3840x2160 | 1.2 | 4K |
| Optoma | GT1080HDR | 1920x1080 | 0.5 | Ultra Short |
| Optoma | EH412 | 1920x1080 | 1.3 | Standard |
| Sony | VPL-HW45ES | 1920x1080 | 1.0 | Standard |
| Sony | VPL-VW295ES | 3840x2160 | 1.0 | 4K |

### Finding Profiles

```python
from lib.cinematic.projection.physical import (
    list_profiles,
    get_short_throw_profiles,
    get_4k_profiles,
    get_profiles_by_throw_ratio,
)

# List all profiles
all_profiles = list_profiles()

# Get short throw projectors
short_throw = get_short_throw_profiles()

# Get 4K projectors
four_k = get_4k_profiles()

# Get projectors with throw ratio between 1.0 and 1.5
mid_throw = get_profiles_by_throw_ratio(1.0, 1.5)
```

## Target Presets

### Available Presets

| Preset | Type | Dimensions | Use Case |
|--------|------|------------|----------|
| `reading_room` | Multi-surface | 2.5m x 2.0m x 0.6m | Indoor cabinet projection |
| `garage_door` | Planar | 4.88m x 2.13m (16ft x 7ft) | Standard garage door |
| `building_facade` | Multi-surface | 20m x 15m | Large building projection |

### Creating Custom Targets

```python
from lib.cinematic.projection.physical.targets import (
    TargetType,
    ProjectionTarget,
    ProjectionSurface,
    PlanarTargetBuilder,
    TargetImporter,
)

# Method 1: Direct construction
target = ProjectionTarget(
    name="custom_wall",
    description="Living room wall",
    target_type=TargetType.PLANAR,
    width_m=3.0,
    height_m=2.0,
)

# Build geometry
builder = PlanarTargetBuilder(target)
geometry = builder.create_geometry()

# Method 2: From measurements
importer = TargetImporter()
importer.add_point_measurement("corner_bl", (0, 0, 0))
importer.add_point_measurement("corner_br", (3, 0, 0))
importer.add_point_measurement("corner_tl", (0, 0, 2))
importer.add_distance_measurement("width", (0, 0, 0), (3, 0, 0))

target = importer.compute_target()
```

## Content Mapping Workflow

### Full Workflow

```python
from lib.cinematic.projection.physical import (
    load_profile,
    ContentMappingWorkflow,
    CalibrationPoint,
    CalibrationType,
    SurfaceCalibration,
)

# 1. Setup
profile = load_profile("Epson_Home_Cinema_2150")
calibration = SurfaceCalibration(
    name="my_surface",
    calibration_type=CalibrationType.THREE_POINT,
    points=[...]
)

# 2. Create workflow
workflow = ContentMappingWorkflow(
    name="my_projection",
    projector_profile=profile,
    calibration=calibration,
)

# 3. Execute pipeline
workflow.setup()          # Initialize
workflow.calibrate()      # Compute alignment
workflow.create_proxy()   # Create proxy geometry
workflow.map_content("//content/video.mp4")  # Apply content

# 4. Render
output_files = workflow.render("//output/", frame_start=1, frame_end=100)
```

### Output Configuration

```python
from lib.cinematic.projection.physical import (
    ProjectionOutputConfig,
    OutputFormat,
    ColorSpace,
    VideoCodec,
)

config = ProjectionOutputConfig(
    resolution=(1920, 1080),
    format=OutputFormat.VIDEO,
    color_space=ColorSpace.SRGB,
    video_codec=VideoCodec.H264,
    output_path="//output/",
    frame_start=1,
    frame_end=250,
    fps=24,
)
```

**Output Formats:**
- `IMAGE_SEQUENCE` - PNG/JPEG frames
- `VIDEO` - MP4/MOV video file
- `EXR` - EXR multilayer for compositing

**Color Spaces:**
- `SRGB` - Standard sRGB
- `REC709` - Rec. 709 (HD video)
- `REC2020` - Rec. 2020 (UHD)
- `ACES` - ACES color space
- `FILMIC` - Filmic Blender

## API Reference

### Core Functions

```python
# Profile loading
profile = load_profile("Epson_Home_Cinema_2150")
profiles = list_profiles()

# Camera creation
camera_obj = create_projector_camera(profile, name="MyProjector")

# Calibration
result = compute_alignment_transform(projector_points, world_points)

# Rendering
output_files = render_for_projector(
    content_path,
    projector_profile_name,
    calibration_points,
    output_dir
)
```

### Integration Module

```python
from lib.cinematic.projection.physical.integration import (
    ProjectionShotConfig,
    ProjectionShotBuilder,
    build_projection_shot,
    build_projection_shot_from_dict,
)

# From YAML file
result = build_projection_shot("path/to/shot.yaml")

# From dict
result = build_projection_shot_from_dict({
    'name': 'My Shot',
    'camera': {
        'projector_profile': 'Epson_Home_Cinema_2150',
        'calibration': {...}
    },
    'output': {...}
})

# Programmatic
config = ProjectionShotConfig(name="test", ...)
builder = ProjectionShotBuilder(config)
result = builder.build()
```

## Troubleshooting

### Common Issues

**"Profile not found" error:**
```python
# Check available profiles
from lib.cinematic.projection.physical import list_profiles
print(list_profiles())
```

**Calibration error too high:**
- Ensure points are not collinear
- Check world position measurements are accurate
- Use 4-point DLT for non-planar surfaces

**Content not mapping correctly:**
- Verify calibration points are in correct order (BL, BR, TL)
- Check UV coordinates are in 0-1 range
- Ensure content resolution matches output config

## Examples

See `tests/e2e/test_projection_mapping.py` for complete examples.

## Version

Physical Projection Mapping v0.2.0

- Phase 18.0: Projector Profile System
- Phase 18.1: Surface Calibration
- Phase 18.2: Content Mapping Workflow
- Phase 18.3: Target Presets
- Phase 18.4: Integration & Testing
