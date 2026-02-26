# Phase 19.3: Squeeze/Expand Animation

**Phase:** 19.3
**Status:** In Progress
**Started:** 2026-02-25
**Requirements:** REQ-TENT-03, REQ-TENT-07

---

## Overview

Implement animation system for tentacle squeeze/expand effects with shape keys, spline IK rigging, and state machine for zombie mouth tentacle behaviors.

---

## Goals

1. **Shape Key System** - Procedural shape key generation for compress/expand/curl
2. **Spline IK Rig** - Bone-based animation with curve control
3. **State Machine** - Animation states for zombie tentacle behavior
4. **UE5 Export Ready** - Morph targets compatible with Unreal Engine

---

## Requirements Coverage

| ID | Requirement | Plan |
|----|-------------|------|
| REQ-TENT-03-01 | Compress diameter (30-50%) | shape_keys.py |
| REQ-TENT-03-02 | Elongate length (1.5-2x) | shape_keys.py |
| REQ-TENT-03-03 | Smooth interpolation | shape_keys.py |
| REQ-TENT-03-04 | Localized squeeze | shape_keys.py |
| REQ-TENT-03-05 | Morph targets | rig.py |
| REQ-TENT-03-06 | Shape key presets | types.py |
| REQ-TENT-03-07 | Volume preservation | shape_keys.py |
| REQ-TENT-07-01 | State definitions (6) | state_machine.py |
| REQ-TENT-07-02 | State transitions | state_machine.py |
| REQ-TENT-07-03 | Idle animation | state_machine.py |
| REQ-TENT-07-04 | Emergence timing | state_machine.py |
| REQ-TENT-07-05 | UE animation blueprint | state_machine.py |

---

## Module Structure

```
lib/tentacle/animation/
├── __init__.py           # Package exports
├── types.py              # ShapeKeyConfig, AnimationState, StateTransition
├── shape_keys.py         # ShapeKeyGenerator, shape key creation
├── rig.py                # SplineIKRig, bone chain creation
└── state_machine.py      # TentacleStateMachine, state management

configs/tentacle/
└── animation_presets.yaml # Shape key presets, state configs
```

---

## Implementation Plan

### Plan 19.3-01: Types & Configuration (2-3 hours)

**Goal:** Define data structures for shape keys, animation states, and rigging.

**Files:**
- `lib/tentacle/animation/types.py`
- `configs/tentacle/animation_presets.yaml`

**Classes:**
```python
@dataclass
class ShapeKeyConfig:
    name: str                    # Shape key name
    compression: float = 1.0     # Diameter multiplier (0.3-1.25)
    elongation: float = 1.0      # Length multiplier (0.8-2.0)
    curl_angle: float = 0.0      # Tip curl in degrees
    curl_position: float = 0.5   # Where curl starts (0=base, 1=tip)
    localized: bool = False      # Localized vs full-body effect
    localize_position: float = 0.5  # Position of localized effect
    localize_width: float = 0.2  # Width of localized effect
    volume_preserve: bool = True # Maintain approximate volume

@dataclass
class AnimationState:
    name: str                    # State name (Hidden, Emerging, etc.)
    shape_keys: Dict[str, float] # Shape key name -> value
    duration: float = 1.0        # Default duration in seconds
    loop: bool = False           # Loop animation
    idle_motion: bool = False    # Add idle undulation

class TentacleState(Enum):
    HIDDEN = "hidden"
    EMERGING = "emerging"
    SEARCHING = "searching"
    GRABBING = "grabbing"
    ATTACKING = "attacking"
    RETRACTING = "retracting"

@dataclass
class StateTransition:
    from_state: TentacleState
    to_state: TentacleState
    duration: float = 0.5        # Transition time
    easing: str = "ease_in_out"  # Easing function
```

**Tests:**
- Test ShapeKeyConfig validation
- Test AnimationState creation
- Test TentacleState enum
- Test StateTransition validation

---

### Plan 19.3-02: Shape Key Generator (3-4 hours)

**Goal:** Generate procedural shape keys for tentacle mesh.

**Files:**
- `lib/tentacle/animation/shape_keys.py`

**Key Functions:**
```python
class ShapeKeyGenerator:
    def __init__(self, mesh: Object, config: TentacleConfig):
        pass

    def create_shape_key(self, config: ShapeKeyConfig) -> str:
        """Create a single shape key from config."""
        pass

    def create_preset_shape_keys(self) -> List[str]:
        """Create all preset shape keys (Base, Compress_50, etc.)."""
        pass

    def apply_compression(self, vertices: np.ndarray, factor: float,
                          position: float, width: float) -> np.ndarray:
        """Apply compression transformation to vertices."""
        pass

    def apply_elongation(self, vertices: np.ndarray, factor: float) -> np.ndarray:
        """Apply elongation transformation along length."""
        pass

    def apply_curl(self, vertices: np.ndarray, angle: float,
                   position: float) -> np.ndarray:
        """Apply curl transformation to tip or full body."""
        pass

    def preserve_volume(self, vertices: np.ndarray,
                        original: np.ndarray) -> np.ndarray:
        """Adjust vertices to maintain approximate volume."""
        pass
```

**Shape Key Presets:**
| Name | Compression | Elongation | Curl |
|------|-------------|------------|------|
| SK_Base | 1.0 | 1.0 | 0° |
| SK_Compress_50 | 0.5 | 2.0 | 0° |
| SK_Compress_75 | 0.75 | 1.3 | 0° |
| SK_Expand_125 | 1.25 | 0.8 | 0° |
| SK_Curl_Tip | 1.0 | 1.0 | 180° |
| SK_Curl_Full | 0.9 | 0.9 | 360° |

**Tests:**
- Test compression transformation
- Test elongation transformation
- Test curl transformation
- Test volume preservation
- Test localized squeeze
- Test preset shape key generation

---

### Plan 19.3-03: Spline IK Rig (3-4 hours)

**Goal:** Create bone rig with spline IK for animation.

**Files:**
- `lib/tentacle/animation/rig.py`

**Key Classes:**
```python
@dataclass
class SplineIKConfig:
    bone_count: int = 15         # Number of bones
    bone_length: float = 0.067   # Length per bone (length / bone_count)
    chain_name: str = "Tentacle"
    curve_resolution: int = 64   # Curve points

class SplineIKRig:
    def __init__(self, tentacle_object: Object, config: SplineIKConfig):
        pass

    def create_armature(self) -> Object:
        """Create armature with bone chain."""
        pass

    def create_control_curve(self) -> Object:
        """Create Bézier curve for IK control."""
        pass

    def setup_spline_ik(self) -> None:
        """Add Spline IK constraint to bone chain."""
        pass

    def parent_mesh_to_rig(self) -> None:
        """Parent tentacle mesh to armature with auto-weights."""
        pass

    def get_bone_names(self) -> List[str]:
        """Return list of bone names in chain."""
        pass
```

**Bone Hierarchy:**
```
Tentacle_Root
├── Tentacle_01
├── Tentacle_02
├── ...
└── Tentacle_N (tip)
```

**Tests:**
- Test armature creation
- Test control curve creation
- Test Spline IK setup
- Test bone naming
- Test mesh parenting

---

### Plan 19.3-04: State Machine (2-3 hours)

**Goal:** Implement animation state machine for zombie tentacle behavior.

**Files:**
- `lib/tentacle/animation/state_machine.py`

**Key Classes:**
```python
class TentacleStateMachine:
    def __init__(self, states: List[AnimationState],
                 transitions: List[StateTransition]):
        pass

    @property
    def current_state(self) -> TentacleState:
        """Return current state."""
        pass

    def transition_to(self, state: TentacleState,
                      immediate: bool = False) -> float:
        """Transition to new state. Returns transition duration."""
        pass

    def update(self, delta_time: float) -> Dict[str, float]:
        """Update state machine, return shape key values."""
        pass

    def get_shape_key_values(self) -> Dict[str, float]:
        """Get current interpolated shape key values."""
        pass

    def is_transitioning(self) -> bool:
        """Check if currently transitioning between states."""
        pass
```

**State Definitions:**
| State | Shape Keys | Duration | Loop |
|-------|------------|----------|------|
| Hidden | Compress_50=1.0 | - | No |
| Emerging | Compress_50→Base | 0.5s | No |
| Searching | Base + idle | - | Yes |
| Grabbing | Curl_Tip + Elongate | 0.3s | No |
| Attacking | Curl_Full + Compress | 0.2s | No |
| Retracting | Base→Compress_50 | 0.4s | No |

**Tests:**
- Test state transitions
- Test shape key interpolation
- Test idle motion generation
- Test state machine cycling

---

## Acceptance Criteria

- [ ] Shape keys generated procedurally from config
- [ ] 6 preset shape keys available (Base, Compress_50, Compress_75, Expand_125, Curl_Tip, Curl_Full)
- [ ] Volume preservation maintains approximate volume
- [ ] Localized squeeze works at any point
- [ ] Spline IK rig creates bone chain
- [ ] State machine implements 6 states
- [ ] State transitions smooth with easing
- [ ] 80%+ test coverage

---

## Dependencies

- Phase 19.1 (Tentacle Geometry) - COMPLETE
- Phase 19.2 (Sucker System) - COMPLETE

---

## Estimated Effort

| Plan | Hours | Priority |
|------|-------|----------|
| 19.3-01 Types & Config | 2-3h | P0 |
| 19.3-02 Shape Key Generator | 3-4h | P0 |
| 19.3-03 Spline IK Rig | 3-4h | P0 |
| 19.3-04 State Machine | 2-3h | P0 |

**Total:** 10-14 hours
