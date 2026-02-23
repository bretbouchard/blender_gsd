# Charlotte 277 Highway Project

30-second animation of a car driving 120mph on I-277 in downtown Charlotte.

## Route
- Start: Mint St
- Path: I-277 highway loop
- End: Elizabeth Ave

## Project Structure

```
charlotte/
├── scenes/           # Blender scene files (.blend)
├── renders/          # Rendered output (frames, videos)
├── scripts/          # Python automation scripts
└── assets/           # Project-specific assets
```

## Quick Start

```bash
# Generate scene and render first frame
blender --background --python projects/charlotte/scripts/charlotte_277_scene.py

# Open in Blender for editing
open projects/charlotte/scenes/charlotte_277_scene.blend
```

## Scene Details

- **Duration**: 30 seconds (720 frames @ 24fps)
- **Speed**: 120 mph
- **Camera**: Top-down view following the car
- **Elements**:
  - Hero car (red sports car)
  - I-277 highway with road markings
  - Downtown Charlotte buildings
  - Ground plane
  - Sun lighting

## Renders

| File | Description |
|------|-------------|
| `charlotte_277_frame_001.png` | First frame preview |
