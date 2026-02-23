# Consolidated Council of Ricks Review Summary
## Scene Generation System - All 9 Phases

**Review Date:** 2026-02-21
**Mode:** All Hands on Deck (9 Specialists across 4 review groups)

---

## Overall Assessment

| Phase | Status | Critical | High | Medium |
|-------|--------|----------|------|--------|
| 0: Testing Infrastructure | REJECT (not found) | 1 | 0 | 0 |
| 1: Asset Vault | CONDITIONAL APPROVE | 0 | 2 | 4 |
| 2: Photoshoot | CONDITIONAL APPROVE | 0 | 1 | 5 |
| 3: Interiors | CONDITIONAL APPROVE | 2 | 2 | 2 |
| 4: Urban | CONDITIONAL APPROVE | 1 | 3 | 3 |
| 5: Orchestrator | CONDITIONAL APPROVE | 0 | 3 | 4 |
| 6: GN Extensions | CONDITIONAL APPROVE | 0 | 2 | 3 |
| 7: Characters | CONDITIONAL APPROVE | 0 | 2 | 2 |
| 8: Review | CONDITIONAL APPROVE | 1 | 1 | 3 |

---

## Critical Issues (MUST FIX)

### Phase 0: Testing Infrastructure Plan Missing
**Issue:** No PLAN.md found at expected location
**Fix:** Plan exists at `.planning/phases/0/0-01-PLAN.md` - will use this

### Phase 3: BSP Algorithm Correctness
**Issue:** Split heuristic, termination conditions, room assignment underspecified
**Fix:** Add BSPConfig with min_room_area, split_ratio_range, max_depth

### Phase 3: GN Cannot Parse JSON
**Issue:** Geometry Nodes has no JSON parsing capability
**Fix:** Use pre-processed attribute arrays OR Python bmesh for geometry creation

### Phase 4: L-System Intersection Detection Missing
**Issue:** No intersection detection at segment endpoints
**Fix:** Add endpoint tracking and intersection creation in parse_to_network()

### Phase 8: OpenEXR Library Dependency
**Issue:** No fallback when OpenEXR library unavailable
**Fix:** Add try/except import with graceful degradation to sidecar JSON

---

## High Priority Issues (SHOULD FIX)

### Phase 1: Security
1. Symlink TOCTOU vulnerability in sanitize_path
2. No yaml.safe_load requirement

### Phase 2: Testing
1. No unit test specifications with coverage target

### Phase 3: Performance/Testing
1. No memory bounds for large floor plans
2. Furniture collision detection missing

### Phase 4: Implementation
1. GN JSON parsing issue (same as Phase 3)
2. MUTCD sign dimensions need validation
3. Street light placement needs boundary check

### Phase 5: UX/CLI
1. Missing JSON output schema for --json-output
2. Missing CLI exit codes documentation
3. Missing tier migration tools

### Phase 6: Performance
1. Missing LOD transition smoothing (hysteresis)
2. Missing MemoryTracker implementation

### Phase 7: Asset Management
1. Hardcoded asset paths without environment variable support
2. No attachment point compatibility validation

### Phase 8: Implementation
1. SSIM/PSNR implementations not specified

---

## Key Architectural Decisions Confirmed

### BSP and L-System: Python Pre-Processing (CORRECT)
- Both algorithms run in Python (NOT pure GN)
- GN consumes pre-processed data (NOT JSON strings)
- Use attribute arrays or bmesh for geometry creation

### JSON Interchange Format
- Python generates JSON for serialization/transport
- Python pre-processes JSON into curves with attributes
- GN reads typed attributes, NOT JSON strings

### LOD System
- 3-tier system: LOD0 (<10m), LOD1 (10-50m), LOD2 (>50m)
- Add hysteresis to prevent visible "popping"
- Per-category LOD configuration

### Security
- Path sanitization with TOCTOU protection
- yaml.safe_load for all YAML parsing
- Environment variable expansion for asset paths

---

## Execution Order

Based on Council recommendations, execute in this order:

1. **Phase 0** - Testing Infrastructure (foundation)
2. **Phase 1** - Asset Vault (core dependency)
3. **Phase 2** - Photoshoot (parallel with 1)
4. **Phase 3** - Interiors (depends on 1)
5. **Phase 4** - Urban (parallel with 3)
6. **Phase 5** - Orchestrator (depends on 1-4)
7. **Phase 6** - GN Extensions (parallel with 5)
8. **Phase 7** - Characters (parallel with 5)
9. **Phase 8** - Review (depends on all)

---

## Code Snippets to Include During Implementation

### sanitize_path (Phase 1)
```python
def sanitize_path(path: str | Path) -> Path:
    """Sanitize path with TOCTOU protection."""
    abs_path = Path(path).absolute()
    path_str = str(abs_path)
    if ".." in path_str or "~" in path_str:
        raise SecurityError(f"Path traversal detected: {path}")
    resolved = abs_path.resolve()
    for allowed in ALLOWED_PATHS:
        try:
            resolved.relative_to(allowed.resolve())
            return resolved
        except ValueError:
            continue
    raise SecurityError(f"Path not in allowed paths: {resolved}")
```

### BSPConfig (Phase 3)
```python
@dataclass
class BSPConfig:
    min_room_area: float = 9.0  # m^2
    max_room_area: float = 100.0
    split_ratio_range: Tuple[float, float] = (0.3, 0.7)
    max_depth: int = 10
    room_height_default: float = 2.8
```

### LODConfig (Phase 6)
```python
@dataclass
class LODConfig:
    lod0_max_distance: float = 10.0
    lod1_max_distance: float = 50.0
    hysteresis_distance: float = 5.0
    dither_enabled: bool = True
    dither_range: float = 3.0
```

### CLI Exit Codes (Phase 5)
```python
class ExitCode:
    SUCCESS = 0
    VALIDATION_ERROR = 1
    ASSET_NOT_FOUND = 2
    RENDER_FAILED = 3
    CHECKPOINT_FAILED = 4
    INTERRUPTED = 130
```

---

## Council Motto

> "The Council of Ricks doesn't approve mediocre code. We enforce SLC, security, and quality because production doesn't forgive compromise."

---

**Review Complete:** 2026-02-21
**Next Step:** Begin autonomous execution with fixes incorporated
