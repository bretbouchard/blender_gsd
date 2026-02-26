# Eyes Project Roadmap

## Milestone v0.1 - Core Eye System

### Phase 1: Foundation
**Goal**: Basic eye geometry generation with Geometry Nodes

**Requirements**: REQ-EYE-01, REQ-EYE-10

**Tasks**:
1. Create base eye geometry node group
   - Spherical primitive
   - Size parameter
   - Position distribution
2. Implement instance-based eye generation
   - Point cloud distribution
   - Instance on points
   - Random size variation
3. Add nested sphere architecture
   - Inner sphere (pupil)
   - Middle sphere (iris)
   - Outer sphere (sclera/cornea)
4. Performance baseline
   - Test with 10,000 eyes
   - Optimize instance usage

**Deliverable**: Geometry Nodes setup that generates N eyes with nested spheres

---

### Phase 2: Animation System
**Goal**: Eye emergence and rotation animations

**Requirements**: REQ-EYE-02, REQ-EYE-03

**Tasks**:
1. Implement blink-into-existence
   - Scale animation from 0 to 1
   - Emergence curve (ease-out)
   - Per-eye offset control
2. Add rotation system
   - Size-based rotation speed
   - Edge vs center rotation variance
   - Multi-axis rotation
3. Create animation controls
   - Global speed multiplier
   - Pause/freeze option
   - Frame range parameters

**Deliverable**: Animated eye cluster with emergence and rotation

---

### Phase 3: Material System
**Goal**: Reflective and emissive eye materials

**Requirements**: REQ-EYE-04, REQ-EYE-05

**Tasks**:
1. Create reflective eye material
   - Environment capture
   - Fresnel-based reflection
   - Size-based reflection distance
2. Add emission system
   - Emissive zones
   - Focused light projection
   - Glow without self-emission option
3. Implement material variation
   - Per-eye color variation
   - Intensity controls
   - Global vs per-eye parameters

**Deliverable**: Eyes with working reflection and emission materials

---

### Phase 4: Atmospheric Effects
**Goal**: Heat waves, condensation, and halo

**Requirements**: REQ-EYE-06, REQ-EYE-07, REQ-EYE-08

**Tasks**:
1. Implement heat wave distortion
   - Shader-based ripple
   - Animation system
   - Intensity control
2. Add condensation effect
   - Edge-positioned moisture
   - Rotation tied to position
   - Droplet appearance
3. Create halo system
   - Central glow generation
   - Rotation animation
   - Fire/light presets

**Deliverable**: Complete atmospheric effect system

---

### Phase 5: Polish & Presets
**Goal**: Performance optimization and preset library

**Requirements**: REQ-EYE-09, REQ-EYE-10, REQ-EYE-11, REQ-EYE-12

**Tasks**:
1. Performance optimization
   - LOD system for distant eyes
   - Frustum culling
   - Memory optimization
2. Space transition effect
   - Distance-based black fade
   - Small eye targeting
3. Create preset library
   - Cosmic preset
   - Organic preset
   - Mechanical preset
   - Fire preset
4. Animation export setup
   - Frame range controls
   - Format options
   - Alpha support

**Deliverable**: Production-ready eye effect system with presets

---

## Future Milestones

### v0.2 - Interactive Controls
- Real-time parameter adjustment
- Interactive eye placement
- Camera-aware effects

### v0.3 - Advanced Effects
- Multiple lens separation/combination
- Time-based moment capture
- Advanced physics simulation

---

## Progress Tracking

| Phase | Status | Requirements |
|-------|--------|--------------|
| Phase 1 | ✅ Complete | REQ-EYE-01, REQ-EYE-10 |
| Phase 2 | Not Started | REQ-EYE-02, REQ-EYE-03 |
| Phase 3 | Not Started | REQ-EYE-04, REQ-EYE-05 |
| Phase 4 | Not Started | REQ-EYE-06, REQ-EYE-07, REQ-EYE-08 |
| Phase 5 | Not Started | REQ-EYE-09, REQ-EYE-10, REQ-EYE-11, REQ-EYE-12 |

---

## Technical Notes

### Geometry Nodes Architecture
```
EyeGenerator (Node Group)
├── Point Distribution
│   ├── Count input (12 to 1M)
│   ├── Distribution type (random/grid/poisson)
│   └── Surface/Volume selection
├── Eye Instance
│   ├── Outer Sphere (cornea)
│   ├── Middle Sphere (iris)
│   └── Inner Sphere (pupil)
├── Size Variation
│   ├── Min/Max size
│   ├── Distribution curve
│   └── Position-based bias
└── Animation
    ├── Emergence (scale 0→1)
    ├── Rotation (size-based speed)
    └── Global controls
```

### Material Nodes Architecture
```
EyeMaterial (Node Group)
├── Base Reflection
│   ├── Environment texture
│   ├── Fresnel factor
│   └── Roughness variation
├── Emission Layer
│   ├── Emissive zone mask
│   ├── Focus direction
│   └── Intensity control
├── Atmospheric Effects
│   ├── Heat distortion
│   ├── Condensation
│   └── Edge glow
└── Output
    ├── Surface BSDF
    └── Volume (optional)
```
