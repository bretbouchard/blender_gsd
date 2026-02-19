# Requirements: Anamorphic / Forced Perspective System

**Status**: 🚫 Blocked (Prerequisites Required)
**Priority**: P2 (Feature Request)
**Created**: 2026-02-19

---

## Overview

**What**: System to create anamorphic / forced perspective installations where markings on walls/floors form a coherent image from ONE specific camera viewpoint, but appear distorted/unrecognizable from any other angle.

**Use Case**: Multiple such installations throughout a scene, each only visible from specific camera positions.

**Also Known As**:
- Anamorphic art
- Forced perspective
- Projective anamorphosis
- 3D pavement art technique
- Camera-based projection mapping

---

## Core Concept

```
┌─────────────────────────────────────────────────────────────┐
│                         SCENE                               │
│                                                             │
│    ┌─────┐                    ┌─────┐                       │
│    │Wall │                    │Floor│                       │
│    │  X  │←── Projection ────→│  X  │                       │
│    └─────┘                    └─────┘                       │
│         ↑                          ↑                        │
│         │                          │                        │
│         └──────────┬───────────────┘                        │
│                    │                                        │
│              CAMERA POSITION                                │
│           (The "Sweet Spot")                                │
│                                                             │
│    From this angle: Image appears correct                   │
│    From any other: Image is distorted                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Requirements

### REQ-ANAM-01: Camera Frustum Projection

**Goal**: Project an image from a camera's viewpoint onto scene geometry.

**Details**:
- Define a "projection camera" with position, rotation, FOV
- Cast rays from camera through image pixels onto scene geometry
- Record hit positions on geometry (wall, floor, ceiling, objects)
- Generate UV coordinates or vertex colors for the projection

**Acceptance Criteria**:
- [ ] Image projects correctly onto multiple surfaces
- [ ] From camera position, projected image appears undistorted
- [ ] From other angles, image appears distorted

---

### REQ-ANAM-02: Projection Surface Detection

**Goal**: Automatically detect and select surfaces for projection.

**Details**:
- Raycast from camera to find intersecting geometry
- Filter by surface type (floor, wall, ceiling, custom objects)
- Handle occlusion (don't project onto hidden surfaces)
- Support multi-surface projections (floor + wall = corner)

**Acceptance Criteria**:
- [ ] Automatically finds floor surfaces in camera frustum
- [ ] Automatically finds wall surfaces in camera frustum
- [ ] Handles corners and complex geometry

---

### REQ-ANAM-03: Projection Baking

**Goal**: Bake projected image onto geometry as materials/textures.

**Details**:
- Generate UV coordinates for projection
- Bake to texture or use generated coordinates
- Support different material types (diffuse, emission, decal)
- Allow non-destructive workflow (keep projection setup)

**Acceptance Criteria**:
- [ ] Baked texture matches projection from sweet spot
- [ ] Non-destructive option preserves original materials
- [ ] Export-friendly (works in other renderers)

---

### REQ-ANAM-04: Multi-Viewpoint System

**Goal**: Support multiple anamorphic installations in one scene.

**Details**:
- Define multiple "sweet spot" camera positions
- Each installation has its own projection source
- Manage visibility (only one visible at a time, or layered)
- Support sequential reveal (walk through scene, see different images)

**Acceptance Criteria**:
- [ ] Multiple anamorphic installations in single scene
- [ ] Each installation tied to specific camera position
- [ ] Non-overlapping or controlled overlap

---

### REQ-ANAM-05: Camera-Triggered Visibility

**Goal**: Show/hide projections based on active camera position.

**Details**:
- Link projection to camera object
- Show projection only when camera is in "sweet spot" zone
- Smooth transition when entering/leaving zone
- Support animation (camera moves into position, image appears)

**Acceptance Criteria**:
- [ ] Projection visible only within defined zone
- [ ] Smooth fade in/out at zone boundaries
- [ ] Works with animated cameras

---

### REQ-ANAM-06: Arbitrary Geometry Projection

**Goal**: Project onto any geometry, not just flat surfaces.

**Details**:
- Project onto curved surfaces
- Project onto 3D objects (furniture, characters)
- Handle UV seams correctly
- Support vertex colors as alternative to UVs

**Acceptance Criteria**:
- [ ] Works on curved walls
- [ ] Works on 3D objects
- [ ] No visible seams or distortion at UV boundaries

---

### REQ-ANAM-07: Projection Preview

**Goal**: Real-time preview of anamorphic effect.

**Details**:
- Viewport preview from projection camera
- Side-by-side view (sweet spot vs. other angles)
- Interactive adjustment of camera position
- Preview resolution control

**Acceptance Criteria**:
- [ ] Real-time preview in viewport
- [ ] Easy comparison of sweet spot vs. other views

---

## Blockers / Prerequisites

These must be built first:

| Blocker | Why It's Needed | Current Status |
|---------|-----------------|----------------|
| **Camera frustum raycasting** | Need to cast rays from camera through image | Not implemented |
| **Surface detection** | Need to find geometry in frustum | Not implemented |
| **Projection UV generation** | Need to create UVs from projection | Not implemented |
| **Texture baking system** | Need to bake projection to texture | Partial (material system exists) |
| **Camera position zones** | Need to define "sweet spot" volumes | Not implemented |
| **Conditional visibility** | Need to show/hide based on camera | Not implemented |
| **Multi-camera support** | Already exists in CAP-CAM-06 | ✅ Complete |

---

## Proposed Phase Structure

### Phase X.1: Projection Foundation
- Camera frustum raycasting
- Basic projection math
- Single-surface projection

### Phase X.2: Surface Detection
- Automatic surface detection in frustum
- Multi-surface projection
- Occlusion handling

### Phase X.3: Projection Baking
- UV generation from projection
- Texture baking
- Material integration

### Phase X.4: Multi-Viewpoint System
- Multiple anamorphic installations
- Camera-triggered visibility
- Zone-based activation

### Phase X.5: Advanced Features
- Arbitrary geometry projection
- Animation support
- Preview system

---

## Technical Approach

### Core Algorithm

```python
def project_image_from_camera(
    image: Image,
    camera: Camera,
    scene_geometry: List[Object],
    resolution: Tuple[int, int]
) -> ProjectionResult:
    """
    Project image from camera viewpoint onto geometry.

    For each pixel in image:
    1. Cast ray from camera through pixel
    2. Find intersection with geometry
    3. Record UV coordinate and color at hit point

    Returns:
    - UV coordinates for each surface
    - Baked texture
    - Visibility from sweet spot
    """
    pass
```

### Data Structures

```python
@dataclass
class AnamorphicProjection:
    """Configuration for one anamorphic installation."""
    name: str
    source_image: Path
    projection_camera: CameraConfig
    target_surfaces: List[str]  # Object names
    sweet_spot_radius: float    # How close camera must be
    transition_distance: float  # Fade distance
    material_type: str          # "emission", "diffuse", "decal"
    visibility_zone: Optional[Transform3D]  # Optional zone volume

@dataclass
class AnamorphicScene:
    """Multiple anamorphic projections in a scene."""
    projections: List[AnamorphicProjection]
    active_camera: str  # Which camera determines visibility
    blend_mode: str     # "exclusive", "layered", "sequential"
```

---

## References / Inspiration

- **Felipe Pantone** - Anamorphic installations
- **Kurt Wenner** - 3D pavement art
- **Julian Beever** - Chalk art anamorphosis
- **Tracy Lee Stum** - Street painting
- **Google Earth anamorphic ads**
- **Sports field logos** (appear correct from broadcast camera)

---

## Questions to Resolve

1. **Resolution**: How high-res can projections be before performance issues?
2. **Animation**: Can the source image be animated/video?
3. **Multiple viewers**: What if multiple cameras need to see different things?
4. **Real-time**: Can this work in game engines (Unity/Unreal)?

---

## Next Steps

1. ✅ Create ABILITY_MATRIX.md for capability tracking
2. ✅ Document requirements (this file)
3. ⬜ Create beads for each blocker
4. ⬜ Research Blender camera projection techniques
5. ⬜ Prototype basic single-surface projection
