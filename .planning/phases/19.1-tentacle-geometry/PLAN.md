# Phase 19.1: Tentacle Geometry (REQ-TENT-01, REQ-TENT-06)

**Priority:** P0
**Est. Effort:** 3-4 days
**Depends on:** 19.0 Research (COMPLETE)
**Enables:** 19.2 (Suckers), 19.3 (Animation)

---

## Goal

Implement procedural tentacle body generation with configurable parameters for shape, taper, and segmentation. Establish foundation for zombie mouth integration.

---

## Requirements Coverage

| ID | Requirement | Coverage |
|----|-------------|----------|
| REQ-TENT-01-01 | Configurable length (0.1m to 3.0m) | 19.1-02 |
| REQ-TENT-01-02 | Taper profile (base 2-3x tip) | 19.1-02 |
| REQ-TENT-01-03 | Segmentation (10-50 segments) | 19.1-02 |
| REQ-TENT-01-04 | Real-time viewport preview | 19.1-02 |
| REQ-TENT-01-05 | Curve-based base | 19.1-02 |
| REQ-TENT-01-06 | Deterministic output | 19.1-02 |
| REQ-TENT-01-07 | Smooth surface (auto-subdivision) | 19.1-02 |
| REQ-TENT-06-01 | Mouth anchor attachment | 19.1-03 |
| REQ-TENT-06-02 | Multi-tentacle support (1-6) | 19.1-03 |
| REQ-TENT-06-03 | Size variation (thick/thin mix) | 19.1-03 |

---

## Module Structure

```
lib/tentacle/
├── __init__.py              # Package exports
├── types.py                 # TentacleConfig, TaperProfile, SegmentConfig
├── geometry/
│   ├── __init__.py
│   ├── body.py              # TentacleBodyGenerator
│   ├── taper.py             # Taper profile functions
│   └── segments.py          # Segmentation utilities
├── zombie/
│   ├── __init__.py
│   ├── mouth_attach.py      # ZombieMouthConfig, attachment utilities
│   └── multi_array.py       # MultiTentacleArray
└── presets.py               # Preset loader

configs/tentacle/
├── presets.yaml             # Tentacle geometry presets
└── zombie_presets.yaml      # Zombie mouth configurations
```

---

## Wave Structure

### Wave 1: Types & Configuration (19.1-01)
- `types.py` - Core dataclasses
- `presets.py` - YAML preset loader
- `presets.yaml` - Configuration file

### Wave 2: Body Generation (19.1-02)
- `geometry/body.py` - TentacleBodyGenerator
- `geometry/taper.py` - TaperProfile functions
- `geometry/segments.py` - Segmentation utilities
- `geometry/__init__.py` - Package exports

### Wave 3: Zombie Mouth Foundation (19.1-03)
- `zombie/mouth_attach.py` - Attachment utilities
- `zombie/multi_array.py` - Multi-tentacle support
- `zombie/__init__.py` - Package exports
- `zombie_presets.yaml` - Zombie configurations

### Wave 4: Package Exports & Tests
- `__init__.py` - Complete package exports
- Unit tests for all modules

---

## Key Design Decisions

### 1. Curve-Based Generation
- Use Blender Bézier curves as base
- Convert to mesh with radius profile
- Deterministic via seeded random

### 2. Geometry Nodes vs Python
- **Python API** for generation (more control, export-friendly)
- **Geometry Nodes** optional for real-time preview (future)
- Bake to mesh for Unreal export

### 3. Taper Profile
- Stored as curve mapping (0-1 along length → radius factor)
- Built-in profiles: linear, smooth, organic
- Custom profiles via curve data

### 4. Deterministic Output
- Seed parameter for all random operations
- Same config = same mesh every time
- Required for pipeline reproducibility

---

## Acceptance Criteria

- [ ] Single tentacle generates with configurable length/taper/segments
- [ ] Changes visible in viewport in < 100ms
- [ ] Same parameters produce identical mesh
- [ ] Tentacle can attach to character mouth socket
- [ ] Multi-tentacle array generates 1-6 tentacles
- [ ] Size variation applies across tentacles in array
- [ ] 80%+ test coverage

---

## Dependencies

### Internal
- `lib/pipeline/` - Stage pipeline (optional, for integration)
- `lib/nodekit/` - Geometry node utilities (optional)

### External
- Blender 5.0+ (bpy module)
- NumPy for math operations

---

## Plans

| Plan | Name | Est. Hours | Status |
|------|------|------------|--------|
| 19.1-01 | Types & Configuration | 2-3h | Planned |
| 19.1-02 | Body Generation | 4-6h | Planned |
| 19.1-03 | Zombie Mouth Foundation | 3-4h | Planned |

**Total:** 9-13 hours (1.5-2 days)

---

## Next Phase

After 19.1 completion:
- **Phase 19.2** - Sucker System (REQ-TENT-02)
- **Phase 19.3** - Squeeze/Expand Animation (REQ-TENT-03)
