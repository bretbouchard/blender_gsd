# Phase 1: Foundation - Eye Geometry Generation

**Goal**: Create procedural eye geometry with Geometry Nodes, supporting variable counts (12 to millions) with nested sphere architecture.

**Requirements**: REQ-EYE-01, REQ-EYE-10

---

## Overview

This phase establishes the core geometry system for the eye effect. We'll create a Geometry Nodes setup that generates eyes procedurally using instances for performance at scale.

## Technical Approach

### Architecture
```
EyeGenerator (NodeTree)
├── Input Parameters
│   ├── eye_count (Integer, 12 to 1M)
│   ├── distribution_type (Enum: random/grid/sphere)
│   ├── size_min (Float, 0.01 to 1.0)
│   ├── size_max (Float, 0.1 to 5.0)
│   └── seed (Integer)
├── Point Distribution
│   ├── Distribute points on/in sphere
│   ├── Apply size variation
│   └── Random rotation per point
├── Eye Geometry
│   ├── Outer Sphere (cornea) - largest
│   ├── Middle Sphere (iris) - medium
│   └── Inner Sphere (pupil) - smallest
└── Output
    └── Combined instances
```

### Performance Strategy
- Use `Instance on Points` for all eye geometry
- Share single eye node group across all instances
- Keep base geometry minimal (low poly spheres)
- Store attributes for size variation

---

## Tasks

### Task 1.1: Create Base Eye Node Group
**Estimate**: 30 minutes

Create a reusable node group for a single eye with nested spheres.

```python
# Location: projects/eyes/scripts/eye_geometry.py

def create_eye_node_group():
    """
    Creates a node group for a single eye with:
    - Outer sphere (cornea)
    - Middle sphere (iris)
    - Inner sphere (pupil)

    Inputs:
    - Size: Overall eye scale
    - Pupil Ratio: Size of pupil relative to eye
    - Iris Ratio: Size of iris relative to eye

    Outputs:
    - Geometry: Combined spheres
    """
    pass
```

**Acceptance**:
- [ ] Node group appears in Blender
- [ ] Three nested spheres visible
- [ ] Size parameter works
- [ ] Ratios control relative sizes

---

### Task 1.2: Create Eye Distribution Node Group
**Estimate**: 45 minutes

Create a node group that distributes points and instances eyes on them.

```python
def create_distribution_node_group():
    """
    Creates a node group for distributing eyes:
    - Point distribution on sphere surface
    - Random size variation
    - Per-point rotation

    Inputs:
    - Count: Number of eyes
    - Radius: Distribution sphere radius
    - Size Min/Max: Eye size range
    - Seed: Random seed

    Outputs:
    - Geometry: Eye instances
    """
    pass
```

**Acceptance**:
- [ ] Points distributed on sphere surface
- [ ] Eye count matches input
- [ ] Size variation works
- [ ] Random seed changes distribution

---

### Task 1.3: Implement Size Variation
**Estimate**: 30 minutes

Add size variation with controllable distribution curve.

```python
def add_size_variation(nodes, size_min, size_max, distribution_curve):
    """
    Adds size variation to distributed eyes:
    - Random value per point
    - Map to size range via curve
    - Store as named attribute
    """
    pass
```

**Acceptance**:
- [ ] Size varies between min and max
- [ ] Distribution curve affects probability
- [ ] Values stored as attributes

---

### Task 1.4: Create Main Generator Script
**Estimate**: 1 hour

Create the main script that orchestrates eye generation.

```python
# Location: projects/eyes/scripts/generate_eyes.py

def generate_eyes(
    count: int = 100,
    distribution: str = "sphere",
    size_min: float = 0.1,
    size_max: float = 1.0,
    radius: float = 10.0,
    seed: int = 42
) -> bpy.types.Object:
    """
    Generates a complete eye cluster.

    Args:
        count: Number of eyes (12 to 1M)
        distribution: Distribution type
        size_min: Minimum eye size
        size_max: Maximum eye size
        radius: Distribution sphere radius
        seed: Random seed

    Returns:
        The generated object
    """
    pass
```

**Acceptance**:
- [ ] Script runs without errors
- [ ] Creates object in scene
- [ ] All parameters work
- [ ] Can regenerate with different seed

---

### Task 1.5: Performance Testing
**Estimate**: 30 minutes

Test performance at various eye counts.

```python
def benchmark_eye_generation():
    """
    Benchmarks eye generation at different scales:
    - 100 eyes (baseline)
    - 1,000 eyes
    - 10,000 eyes
    - 100,000 eyes
    - 1,000,000 eyes

    Measures:
    - Generation time
    - Memory usage
    - Viewport FPS
    """
    pass
```

**Acceptance**:
- [ ] 100 eyes: < 1s generation
- [ ] 10,000 eyes: < 5s generation, 30+ FPS
- [ ] 100,000 eyes: < 30s generation, 15+ FPS
- [ ] 1,000,000 eyes: Loads without crash

---

## Deliverables

1. `projects/eyes/scripts/eye_geometry.py` - Eye node group creation
2. `projects/eyes/scripts/eye_distribution.py` - Distribution node group
3. `projects/eyes/scripts/generate_eyes.py` - Main generation script
4. `projects/eyes/configs/default_eyes.yaml` - Default configuration
5. `projects/eyes/.planning/phases/1/SUMMARY.md` - Completion summary

---

## Risks

| Risk | Mitigation |
|------|------------|
| Performance at 1M eyes | Use instances, low-poly base, LOD later |
| Complex nested sphere setup | Start simple, add complexity incrementally |
| Random distribution artifacts | Use Poisson disk distribution option |

---

## Next Phase Preview

Phase 2 will add:
- Blink-into-existence animation
- Size-based rotation system
- Animation control parameters
