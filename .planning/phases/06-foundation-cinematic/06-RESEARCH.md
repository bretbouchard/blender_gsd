# Phase 6.0: Foundation (REQ-CINE-01) - Research

**Researched:** 2026-02-18
**Domain:** Blender Python Module Architecture, State Persistence, Configuration Systems
**Confidence:** HIGH

## Summary

This research investigated how to establish the foundational module structure, configuration directories, and state persistence framework for the Blender GSD Cinematic System. The system must support 23 REQ-CINE-* requirements across camera, lighting, backdrops, color, animation, and rendering subsystems.

Key findings align with existing GSD project patterns: the project already uses dataclasses for type-safe configurations (see `lib/control_system/profiles.py`), hierarchical parameter resolution (see `lib/control_system/parameters.py`), and YAML-based task loading (see `lib/gsd_io.py`). The cinematic system should extend these patterns rather than introduce new architectures.

**Primary recommendation:** Create `lib/cinematic/` as a sibling module to `lib/control_system/`, using identical patterns: dataclasses for config types, enums for type-safe constants, preset dictionaries for built-in values, and YAML serialization for state persistence. The state directory should be `.gsd-state/cinematic/` at project root.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python dataclasses | 3.10+ | Type-safe data structures | Already used in `lib/control_system/` |
| Python Enum | 3.10+ | Type-safe constants | Used extensively in existing code |
| PyYAML | 6.x | Configuration serialization | Already used in `lib/gsd_io.py` |
| pathlib | stdlib | Path handling | Used throughout codebase |
| Blender bpy | 5.x | Blender API | Required for all Blender operations |
| Blender mathutils | 5.x | Vector/Matrix types | Required for transforms |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing.Protocol | 3.8+ | Interface definitions | For state manager contracts |
| typing.TypedDict | 3.8+ | Dictionary type hints | For complex nested configs |
| dataclasses.field | stdlib | Default factories | For mutable defaults (lists, dicts) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dataclasses | Pydantic | Pydantic adds validation but requires dependency; dataclasses already in codebase |
| raw YAML | JSON | YAML supports comments and multi-doc; already used in project |
| custom serialization | pickle | Pickle is unsafe; YAML is human-readable and editable |

**Note:** PyYAML must be available in Blender Python. If not bundled, use JSON fallback as shown in `lib/gsd_io.py`.

## Architecture Patterns

### Recommended Project Structure

Based on the design document and existing `lib/control_system/` pattern:

```
lib/
├── cinematic/
│   ├── __init__.py              # Package exports, version
│   │
│   ├── # Core Types (Phase 6.0 Foundation)
│   ├── types.py                 # ShotState, CameraConfig, LightConfig, etc.
│   ├── enums.py                 # All enum types for cinematic system
│   ├── state_manager.py         # State persistence (YAML serialize/deserialize)
│   │
│   ├── # Subsystems (Future Phases)
│   ├── camera.py                # Camera rigs, lenses (Phase 6.1)
│   ├── lenses.py                # Lens presets, DoF (Phase 6.1)
│   ├── lighting.py              # Light rigs, gels (Phase 6.2)
│   ├── backdrops.py             # Environments, curves (Phase 6.3)
│   ├── color.py                 # LUTs, color management (Phase 6.4)
│   ├── animation.py             # Camera moves, keyframes (Phase 6.5)
│   ├── render.py                # Render profiles, passes (Phase 6.6)
│   │
│   ├── # Support Systems (Phase 6.7)
│   ├── plumb_bob.py             # Focus/orbit target system
│   ├── shuffler.py              # Shot variation generator
│   ├── frame_store.py           # State capture/comparison
│   ├── depth_layers.py          # Fore/mid/background
│   ├── composition.py           # Guides and overlays
│   ├── motion_path.py           # Camera path generation
│   ├── exposure.py              # Exposure lock/management
│   ├── lens_fx.py               # Flare, bloom, aberration
│   │
│   ├── # Orchestration (Phase 6.8)
│   ├── shot.py                  # Complete shot assembly
│   └── template.py              # Template inheritance
```

### Configuration Directory Structure

```
configs/
├── cinematic/
│   ├── cameras/
│   │   ├── lens_presets.yaml        # 35mm, 50mm, 85mm, etc.
│   │   ├── sensor_presets.yaml      # Full frame, APS-C, etc.
│   │   ├── rig_presets.yaml         # tripod, dolly, crane, etc.
│   │   └── imperfection_presets.yaml # Cooke, ARRI, vintage
│   │
│   ├── lighting/
│   │   ├── rig_presets.yaml         # three_point, studio_hero, etc.
│   │   ├── gel_presets.yaml         # CTB, CTO, creative
│   │   └── hdri_presets.yaml        # Environment maps
│   │
│   ├── backdrops/
│   │   ├── infinite_curves.yaml     # Product backdrops
│   │   ├── gradients.yaml           # Gradient backgrounds
│   │   └── environments.yaml        # Pre-built scenes
│   │
│   ├── color/
│   │   ├── technical_luts.yaml      # Rec.709, sRGB, ACES
│   │   ├── film_luts.yaml           # Kodak, Fuji, Vision3
│   │   └── creative_luts.yaml       # Cinematic looks
│   │
│   ├── animation/
│   │   ├── camera_moves.yaml        # Orbit, dolly, crane
│   │   └── easing_curves.yaml       # Animation easing
│   │
│   ├── render/
│   │   ├── quality_profiles.yaml    # Preview, draft, final
│   │   └── pass_presets.yaml        # Beauty, cryptomatte, etc.
│   │
│   └── shots/
│       ├── base/                    # Abstract base templates
│       │   ├── base_product.yaml
│       │   ├── base_hero.yaml
│       │   └── base_turntable.yaml
│       │
│       ├── product/                 # Product shot presets
│       │   ├── product_hero.yaml
│       │   └── product_detail.yaml
│       │
│       └── control_surface/         # Control surface specific
│           ├── console_overhead.yaml
│           └── knob_detail.yaml
```

### State Persistence Structure

```
.gsd-state/
├── cinematic/
│   ├── camera/
│   │   └── {shot_name}.yaml         # Camera transform, settings
│   │
│   ├── lighting/
│   │   └── {shot_name}.yaml         # Light positions, intensities
│   │
│   ├── frames/
│   │   ├── frame_index.yaml         # Master index
│   │   └── {shot_name}/
│   │       ├── 001/
│   │       │   ├── state.yaml
│   │       │   └── thumbnail.png
│   │       └── 002/
│   │           └── ...
│   │
│   └── sessions/
│       └── {session_id}.yaml        # Resume state for interrupted work
```

### Pattern 1: Dataclass-Based Configuration Types

**What:** Use Python dataclasses for type-safe configuration objects, matching existing `lib/control_system/profiles.py` pattern.

**When to use:** All configuration data structures (CameraConfig, LightConfig, ShotState, etc.)

**Example:**
```python
# lib/cinematic/types.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum

@dataclass
class Transform3D:
    """3D transform with position, rotation, scale."""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Euler degrees
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    def to_blender(self):
        """Convert to Blender-compatible format."""
        return {
            'location': self.position,
            'rotation_euler': [r * (3.14159 / 180) for r in self.rotation],
            'scale': self.scale
        }

@dataclass
class CameraConfig:
    """Complete camera configuration."""
    name: str = "hero_camera"

    # Lens
    focal_length: float = 50.0  # mm
    focus_distance: float = 1.0  # meters (0 = auto)

    # Sensor
    sensor_width: float = 36.0  # mm
    sensor_height: float = 24.0  # mm

    # Aperture / DoF
    f_stop: float = 4.0
    aperture_blades: int = 9

    # Transform
    transform: Transform3D = field(default_factory=Transform3D)

    def to_params(self) -> Dict[str, Any]:
        """Convert to parameter dictionary for Blender."""
        return {
            'focal_length': self.focal_length,
            'focus_distance': self.focus_distance,
            'sensor_width': self.sensor_width,
            'sensor_height': self.sensor_height,
            'f_stop': self.f_stop,
            **self.transform.to_blender()
        }

@dataclass
class ShotState:
    """Complete state of a cinematic shot for persistence."""
    shot_name: str
    version: int = 1
    timestamp: str = ""

    # Camera state
    camera: CameraConfig = field(default_factory=CameraConfig)

    # Lighting state (light name -> config)
    lights: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Backdrop state
    backdrop: Dict[str, Any] = field(default_factory=dict)

    # Render settings
    render_settings: Dict[str, Any] = field(default_factory=dict)

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dictionary."""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> "ShotState":
        """Create from YAML-loaded dictionary."""
        # Reconstruct nested dataclasses
        if 'camera' in data:
            cam_data = data['camera']
            if 'transform' in cam_data:
                cam_data['transform'] = Transform3D(**cam_data['transform'])
            data['camera'] = CameraConfig(**cam_data)
        return cls(**data)
```

### Pattern 2: Enum-Based Type Safety

**What:** Use Python Enum for type-safe constants, matching existing `lib/control_system/` pattern.

**When to use:** All categorical values (lens types, light types, quality tiers, etc.)

**Example:**
```python
# lib/cinematic/enums.py
from enum import Enum

class LensType(Enum):
    """Available lens types."""
    WIDE_14MM = "14mm_ultra_wide"
    WIDE_24MM = "24mm_wide"
    NORMAL_35MM = "35mm_documentary"
    NORMAL_50MM = "50mm_normal"
    PORTRAIT_85MM = "85mm_portrait"
    TELEPHOTO_135MM = "135mm_telephoto"
    MACRO_90MM = "90mm_macro"

class LightType(Enum):
    """Available light types."""
    AREA = "area"
    SPOT = "spot"
    POINT = "point"
    SUN = "sun"

class QualityTier(Enum):
    """Render quality tiers."""
    VIEWPORT_CAPTURE = "viewport_capture"
    EEVEE_DRAFT = "eevee_draft"
    CYCLES_PREVIEW = "cycles_preview"
    CYCLES_PRODUCTION = "cycles_production"
    CYCLES_ARCHIVE = "cycles_archive"

class ColorSpace(Enum):
    """Color space options."""
    SRGB = "srgb"
    AGX = "AgX"
    ACESCG = "ACEScg"
    FILMIC = "Filmic"
```

### Pattern 3: State Manager with YAML Persistence

**What:** Centralized state persistence using YAML, following `lib/gsd_io.py` pattern.

**When to use:** All state save/load operations (frame store, session persistence, resume)

**Example:**
```python
# lib/cinematic/state_manager.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import json
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

from .types import ShotState, CameraConfig, Transform3D

class StateManager:
    """
    Manages cinematic state persistence.

    Follows pattern from lib/gsd_io.py for YAML/JSON handling.
    """

    def __init__(self, state_root: Optional[Path] = None):
        self.state_root = state_root or Path(".gsd-state/cinematic")

    def save(self, state: ShotState, path: Path) -> None:
        """Save state to YAML file."""
        state.timestamp = datetime.now().isoformat()
        data = state.to_yaml_dict()

        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix.lower() in [".yaml", ".yml"]:
            if not yaml:
                raise RuntimeError("PyYAML not available. Use JSON or vendor yaml module.")
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

    def load(self, path: Path) -> ShotState:
        """Load state from YAML file."""
        data = path.read_text(encoding="utf-8")

        if path.suffix.lower() in [".yaml", ".yml"]:
            if not yaml:
                raise RuntimeError("PyYAML not available. Use JSON or vendor yaml module.")
            loaded = yaml.safe_load(data)
        else:
            loaded = json.loads(data)

        return ShotState.from_yaml_dict(loaded)

    def capture_current(self, shot_name: str) -> ShotState:
        """Capture current Blender state into ShotState."""
        import bpy

        # Get active camera
        camera = bpy.context.scene.camera
        if not camera:
            raise ValueError("No active camera in scene")

        # Build camera config
        cam_config = CameraConfig(
            name=camera.name,
            focal_length=camera.data.lens,
            focus_distance=camera.data.dof.focus_distance if camera.data.dof.use_dof else 0.0,
            sensor_width=camera.data.sensor_width,
            sensor_height=camera.data.sensor_height if hasattr(camera.data, 'sensor_height') else camera.data.sensor_width * 0.75,
            f_stop=camera.data.dof.aperture_fstop if camera.data.dof.use_dof else 4.0,
            transform=Transform3D(
                position=tuple(camera.location),
                rotation=tuple(r * (180 / 3.14159) for r in camera.rotation_euler),
                scale=tuple(camera.scale)
            )
        )

        return ShotState(
            shot_name=shot_name,
            camera=cam_config
        )

    def restore(self, state: ShotState) -> None:
        """Restore Blender to captured state."""
        import bpy

        # Find or create camera
        camera = bpy.data.objects.get(state.camera.name)
        if not camera:
            import mathutils
            cam_data = bpy.data.cameras.new(state.camera.name)
            camera = bpy.data.objects.new(state.camera.name, cam_data)
            bpy.context.collection.objects.link(camera)

        # Apply camera settings
        camera.data.lens = state.camera.focal_length
        camera.data.sensor_width = state.camera.sensor_width

        # Apply transform
        camera.location = state.camera.transform.position
        camera.rotation_euler = [r * (3.14159 / 180) for r in state.camera.transform.rotation]
        camera.scale = state.camera.transform.scale

        # Set as active camera
        bpy.context.scene.camera = camera

    def diff(self, state_a: ShotState, state_b: ShotState) -> Dict[str, Any]:
        """Compare two states, return differences."""
        def _diff_dict(a: dict, b: dict, path: str = "") -> Dict[str, Any]:
            diffs = {}
            all_keys = set(a.keys()) | set(b.keys())
            for key in all_keys:
                full_path = f"{path}.{key}" if path else key
                if key not in a:
                    diffs[full_path] = {"added": b[key]}
                elif key not in b:
                    diffs[full_path] = {"removed": a[key]}
                elif a[key] != b[key]:
                    if isinstance(a[key], dict) and isinstance(b[key], dict):
                        nested = _diff_dict(a[key], b[key], full_path)
                        diffs.update(nested)
                    else:
                        diffs[full_path] = {"from": a[key], "to": b[key]}
            return diffs

        return _diff_dict(state_a.to_yaml_dict(), state_b.to_yaml_dict())


class FrameStore:
    """Frame store for iteration workflow (A/B comparison)."""

    def __init__(self, base_path: Path, max_versions: int = 50):
        self.base_path = base_path
        self.max_versions = max_versions
        self.state_manager = StateManager()

    def save_frame(self, shot_name: str, state: ShotState) -> int:
        """Save state as new frame, return frame number."""
        shot_dir = self.base_path / "frames" / shot_name

        # Find next frame number
        existing = list(shot_dir.glob("*/state.yaml"))
        next_num = max([int(p.parent.name) for p in existing] + [0]) + 1

        # Save frame
        frame_path = shot_dir / f"{next_num:03d}" / "state.yaml"
        self.state_manager.save(state, frame_path)

        # Cleanup old frames
        self._cleanup_old_frames(shot_dir)

        return next_num

    def load_frame(self, shot_name: str, frame_num: int) -> ShotState:
        """Load frame by number."""
        frame_path = self.base_path / "frames" / shot_name / f"{frame_num:03d}" / "state.yaml"
        return self.state_manager.load(frame_path)

    def list_frames(self, shot_name: str) -> List[int]:
        """List available frame numbers."""
        shot_dir = self.base_path / "frames" / shot_name
        if not shot_dir.exists():
            return []
        return sorted([int(p.parent.name) for p in shot_dir.glob("*/state.yaml")])

    def _cleanup_old_frames(self, shot_dir: Path) -> int:
        """Remove frames beyond max_versions, return count deleted."""
        import shutil

        existing = sorted(shot_dir.glob("*/state.yaml"), key=lambda p: int(p.parent.name))
        to_remove = existing[:-self.max_versions] if len(existing) > self.max_versions else []

        for frame_path in to_remove:
            shutil.rmtree(frame_path.parent)

        return len(to_remove)
```

### Anti-Patterns to Avoid

- **Storing intent in Blender files**: Blender is the execution plane, not the storage plane. All configuration must be in YAML/configs.
- **Global mutable state**: Use state manager for persistence, not module-level globals.
- **Monolithic config files**: Split configs by subsystem (cameras/, lighting/, etc.) for maintainability.
- **Hardcoded paths**: Always use Path objects and respect project root.
- **Skipping validation**: Dataclasses with default factories ensure safe defaults.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML serialization | Custom parser | PyYAML safe_load/safe_dump | Edge cases, security |
| Deep dictionary merge | Recursive function | `ParameterHierarchy._deep_merge()` | Already exists |
| Parameter resolution | Custom hierarchy | `ParameterHierarchy` class | Already tested |
| Type-safe configs | Raw dicts | dataclasses with type hints | IDE support, validation |
| Frame versioning | Custom numbering | `FrameStore` class | Handles cleanup, indexing |

**Key insight:** The existing `lib/control_system/` package provides well-tested patterns for configuration types, parameter hierarchy, and preset management. Replicate these patterns rather than inventing new approaches.

## Common Pitfalls

### Pitfall 1: Blender Context Assumptions

**What goes wrong:** Assuming `bpy.context` is always available or has expected values.

**Why it happens:** Blender context varies by mode (object mode, edit mode, render mode).

**How to avoid:** Always check context availability, provide fallbacks:

```python
def capture_current(self, shot_name: str) -> ShotState:
    import bpy

    # Check context
    if not hasattr(bpy.context, 'scene'):
        raise RuntimeError("No active Blender scene")

    scene = bpy.context.scene
    camera = scene.camera

    if not camera:
        # Fallback: find any camera
        cameras = [obj for obj in scene.objects if obj.type == 'CAMERA']
        if cameras:
            camera = cameras[0]
        else:
            raise ValueError("No camera found in scene")
```

**Warning signs:** Code that accesses `bpy.context` without guards.

### Pitfall 2: Circular Imports in __init__.py

**What goes wrong:** Importing all modules in `__init__.py` causes circular dependencies.

**Why it happens:** Modules reference each other (e.g., `shot.py` imports `camera.py`, which imports `types.py`).

**How to avoid:** Use lazy imports or import only in `__all__`:

```python
# lib/cinematic/__init__.py
# GOOD: Only import types and enums (leaf dependencies)
from .types import ShotState, CameraConfig, Transform3D
from .enums import LensType, LightType, QualityTier, ColorSpace

__all__ = [
    # Core types
    "ShotState",
    "CameraConfig",
    "Transform3D",
    # Enums
    "LensType",
    "LightType",
    "QualityTier",
    "ColorSpace",
]
```

**Warning signs:** Import errors when loading the package.

### Pitfall 3: Dataclass Mutability with Defaults

**What goes wrong:** Using mutable default values directly in dataclass fields causes shared state.

**Why it happens:** Python evaluates default values once at class definition time.

**How to avoid:** Always use `field(default_factory=...)`:

```python
from dataclasses import dataclass, field
from typing import Dict, Any

# WRONG - shared dict across all instances
@dataclass
class BadConfig:
    metadata: Dict[str, Any] = {}  # DANGEROUS

# CORRECT - each instance gets fresh dict
@dataclass
class GoodConfig:
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Warning signs:** Changes to one instance affecting others.

### Pitfall 4: YAML Path Handling

**What goes wrong:** Assuming YAML files exist or using string paths.

**Why it happens:** Forgetting to create directories or mixing string/Path objects.

**How to avoid:** Always use Path and create parent directories:

```python
def save(self, state: ShotState, path: Path) -> None:
    path = Path(path)  # Ensure Path object
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        yaml.dump(data, f)
```

**Warning signs:** FileNotFoundError when saving.

## Code Examples

Verified patterns from existing codebase:

### Package Initialization Pattern

From `/Users/bretbouchard/apps/blender_gsd/lib/control_system/__init__.py`:

```python
"""
Cinematic Rendering System Package

A comprehensive system for cinematic camera, lighting, and rendering.

Modules:
- types: Core data structures (ShotState, CameraConfig, etc.)
- enums: Type-safe enumerations
- state_manager: State persistence

Quick Start:
    from lib.cinematic import (
        ShotState, CameraConfig, Transform3D,
        StateManager, FrameStore
    )

    # Create camera config
    camera = CameraConfig(
        name="hero_camera",
        focal_length=85.0,
        f_stop=4.0
    )

    # Create shot state
    state = ShotState(
        shot_name="hero_knob_01",
        camera=camera
    )

    # Save state
    manager = StateManager()
    manager.save(state, Path(".gsd-state/cinematic/sessions/hero.yaml"))
"""

from .types import (
    Transform3D,
    CameraConfig,
    LightConfig,
    BackdropConfig,
    RenderSettings,
    ShotState,
)
from .enums import (
    LensType,
    LightType,
    QualityTier,
    ColorSpace,
    EasingType,
)
from .state_manager import (
    StateManager,
    FrameStore,
)

__all__ = [
    # Core types
    "Transform3D",
    "CameraConfig",
    "LightConfig",
    "BackdropConfig",
    "RenderSettings",
    "ShotState",

    # Enums
    "LensType",
    "LightType",
    "QualityTier",
    "ColorSpace",
    "EasingType",

    # State management
    "StateManager",
    "FrameStore",
]

__version__ = "0.1.0"
```

### Dataclass Preset Pattern

From `/Users/bretbouchard/apps/blender_gsd/lib/control_system/profiles.py`:

```python
# Create presets dictionary following existing pattern
LENS_PRESETS: Dict[str, LensPreset] = {
    "85mm_portrait": LensPreset(
        name="85mm Portrait",
        focal_length=85,
        description="Flattering compression, background separation",
        use_case="portrait",
    ),
    "50mm_normal": LensPreset(
        name="50mm Normal",
        focal_length=50,
        description="Most natural, human eye equivalent",
        use_case="hero",
    ),
}

def get_lens_preset(name: str) -> LensPreset:
    """Get a lens preset by name."""
    if name not in LENS_PRESETS:
        available = ", ".join(LENS_PRESETS.keys())
        raise KeyError(f"Lens preset '{name}' not found. Available: {available}")
    return LENS_PRESETS[name]

def list_lens_presets() -> List[str]:
    """List available lens preset names."""
    return list(LENS_PRESETS.keys())
```

### Hierarchical Parameter Resolution

From `/Users/bretbouchard/apps/blender_gsd/lib/control_system/parameters.py`:

```python
class ParameterHierarchy:
    """
    Manages hierarchical parameter resolution.

    Resolution order (later overrides earlier):
    1. Global defaults
    2. Category presets
    3. Instance parameters
    """

    def _deep_merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw dict configs | Typed dataclasses | Project inception | Type safety, IDE support |
| JSON only | YAML with JSON fallback | lib/gsd_io.py | Comments, human-readable |
| Monolithic presets | Hierarchical resolution | lib/control_system/parameters.py | DRY, inheritance |
| Global state | State manager pattern | This phase | Resumability, A/B comparison |

**Deprecated/outdated:**
- Pickle for serialization: Security risk, not human-readable
- .blend files for intent: Blender is execution plane only
- Global module state: Use StateManager for persistence

## Open Questions

Things that couldn't be fully resolved:

1. **Asset path resolution strategy**

   - What we know: Design document specifies search order (project local > GSD bundled > external library > auto-download)
   - What's unclear: How to handle missing assets gracefully (error vs. fallback vs. placeholder)
   - Recommendation: Implement tiered fallback with clear error messages; create `AssetResolver` class

2. **Blender Python environment compatibility**

   - What we know: PyYAML may not be bundled in all Blender Python distributions
   - What's unclear: Which Blender versions include PyYAML by default
   - Recommendation: Maintain JSON fallback as shown in `lib/gsd_io.py`; document YAML requirement

3. **State migration strategy**

   - What we know: ShotState has version field
   - What's unclear: How to handle loading older state versions when schema changes
   - Recommendation: Implement `ShotState.migrate(data)` method for version-to-version upgrades

## Sources

### Primary (HIGH confidence)
- Existing codebase analysis: `/Users/bretbouchard/apps/blender_gsd/lib/` modules
- Design document: `.planning/design/CINEMATIC_SYSTEM_DESIGN.md`
- Existing patterns: `lib/control_system/__init__.py`, `lib/control_system/profiles.py`, `lib/control_system/parameters.py`, `lib/gsd_io.py`

### Secondary (MEDIUM confidence)
- Blender Python API conventions (established patterns in Blender community)

### Tertiary (LOW confidence)
- Web search results were unavailable; all recommendations based on codebase analysis and established Python/Blender patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Based on existing codebase analysis, direct reuse of established patterns
- Architecture: HIGH - Design document specifies structure, existing patterns provide implementation guidance
- Pitfalls: HIGH - Based on Python/Blender known issues and existing codebase patterns

**Research date:** 2026-02-18
**Valid until:** 30 days (stable patterns, version-independent)
