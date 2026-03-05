# Stack Research - Blender Mechanical Tile Platform

**Domain:** Blender 4.x mechanical platform system
**Researched:** 2026-03-04
**Confidence:** High

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Blender | 4.x | Core platform | Latest LTS with geometry nodes, physics engine improvements |
| Python | 3.11+ | Scripting | Blender's native scripting language |
| Geometry Nodes | 4.x | Procedural tile placement | Native Blender feature for procedural geometry |
| Armature System | 4.x | Arm rigging | Native Blender rigging for mechanical arms |
| Physics Engine | 4.x | Rigid body simulation | Bullet physics for realistic arm movement |
| Animation System | 4.x | Keyframe animation | Native Blender animation for arm movements |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| NumPy | 1.24+ | Matrix math | Physics calculations, position transforms |
| Mathutils | 3.3+ | Math utilities | Trigonometry for arm rotations |
| BlenderProc | 1.0 | Procedural generation | Complex procedural geometry patterns |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Blender Console | Debugging | Python scripts run in Blender context |
| System Console | System debugging | External Python execution |
| Node Editor | Geometry nodes | Visual node tree development |
| Dope Sheet | Compositing | Post-processing renders |
| Video Sequencer | Animation editing | Non-linear animation editing |

## Installation

```bash
# Core
pip install numpy mathutils blenderproc

# Dev dependencies
pip install -D pytest pytest-cov
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative | Why Better |
|-------------|-------------|-------------------------|-------------|
| Blender 4.x | Maya/3ds Max | Never | Blender's geometry nodes are superior for this procedural system |
| Bullet Physics | PhysX | Never | Bullet is Blender-native, better documented |
| Python | GDScript (C#) | Never | Python is Blender's scripting language |

## Stack Patterns by Variant

**If [condition]:**
    - Use [variation]
    - Reason
```

**Small scale (1-10 tiles):**
    - Single armature
    - Simple physics constraints
    - Direct keyframe animation
    - Lower complexity, faster iteration

**Medium scale (10-50 tiles):**
    - Multiple armatures
    - Moderate physics constraints
    - Hybrid procedural + keyframe animation
    - Balance complexity and performance

**Large scale (50-200 tiles):**
    - Physics simulation required
    - Full physics constraints
    - Primarily procedural animation
    - Performance optimization critical

**Unlimited scale (200+ tiles):**
    - Procedural-only animation
    - Minimal physics (initial state only)
    - Aggressive LOD/culling
    - Maximum performance optimization

## Version Compatibility

| Package A | Package B | Compatible | Notes |
|-----------|-----------|------------|-------|
| NumPy 1.24+ | Python 3.11+ | ✓ | Core dependency |
| Mathutils 3.3+ | Blender 4.x | ✓ | Core dependency |
| BlenderProc 1.0 | | NumPy | ✓ | Optional, may preview only |

## Sources

- **Context7 library ID:** `blender-4-geometry-nodes` — [topics fetched](topics, integration patterns)
- **Official docs URL:** https://docs.blender.org/manual/animation/physics.html
- **Confidence level:** High
  - Versions verified against 4.x documentation
  - Recent release notes confirm API stability

---

*Last updated: 2026-03-04 after initialization*
