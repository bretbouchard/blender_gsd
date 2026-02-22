# Council of Ricks Review Report: Phases 5 & 6

**Review Date:** 2026-02-21
**Review Type:** Multi-Specialist Analysis
**Decision:** CONDITIONAL APPROVE (both phases require specific improvements)

---

## Executive Summary

| Phase | Decision | Critical Issues | High Issues | Medium Issues |
|-------|----------|-----------------|-------------|---------------|
| Phase 5: Orchestrator | CONDITIONAL APPROVE | 0 | 3 | 4 |
| Phase 6: GN Extensions | CONDITIONAL APPROVE | 0 | 2 | 3 |

---

## Phase 5: Scene Orchestrator Review

### Rick Prime (Design/UX) Review

**Status:** CONDITIONAL APPROVE

#### UX Tiers Assessment

The plan includes all 4 required UX tiers as specified in the SCENE_GENERATION_MASTER_PLAN.md:

| Tier | Name | Status | Completeness |
|------|------|--------|--------------|
| 1 | Templates | PRESENT | 85% |
| 2 | Wizard | PRESENT | 80% |
| 3 | YAML | PRESENT | 90% |
| 4 | Python API | PRESENT | 90% |

**Issues Found:**

##### HIGH: Missing Progressive Disclosure Implementation Details
- **Location:** Plan 5-07, line 726-1099
- **Description:** While UX tiers are defined, there is no explicit progressive disclosure strategy documented. Users should be able to start simple and graduate to more complex tiers without friction.
- **Recommendation:** Add explicit upgrade paths between tiers:
  ```python
  class TierMigration:
      """Enable seamless migration between UX tiers."""
      def wizard_to_yaml(self, wizard_responses: Dict) -> str:
          """Export wizard responses to YAML for manual editing."""
          pass

      def yaml_to_api(self, yaml_path: str) -> SceneBuilder:
          """Convert YAML to fluent API code."""
          pass
  ```

##### MEDIUM: Template Preview System Undefined
- **Location:** Plan 5-07, SceneTemplate dataclass, line 748-763
- **Description:** `preview_image` field exists but no mechanism for generating or serving previews.
- **Recommendation:** Add thumbnail generation to TemplateEngine:
  ```python
  def generate_preview(self, template: SceneTemplate, resolution: Tuple[int,int] = (256,256)) -> str:
      """Generate low-res preview for template browser."""
      pass
  ```

##### MEDIUM: Wizard Validation Insufficient
- **Location:** Plan 5-07, SceneWizard class, line 845-932
- **Description:** Wizard steps lack validation rules for responses (e.g., room count range, valid asset tags).
- **Recommendation:** Add validation to WizardQuestion:
  ```python
  @dataclass
  class WizardQuestion:
      ...
      validation: Optional[Callable[[Any], bool]] = None
      validation_error: str = ""
  ```

#### Templates Assessment

Built-in templates cover all required categories:

| Template | Category | Presets Defined |
|----------|----------|-----------------|
| Portrait Studio | portrait | rembrandt, butterfly, split |
| Product Shot | product | hero, catalog, dramatic |
| Interior Scene | interior | modern, victorian, minimalist |
| Street Scene | street | day, night, golden_hour |
| Full Environment | environment | forest, city, interior_complex |

**Rick Prime Verdict:** CONDITIONAL APPROVE - Add progressive disclosure migration tools before implementation.

---

### Automation Rick (CLI/Headless) Review

**Status:** CONDITIONAL APPROVE

#### CLI Specification Assessment

The CLI specification covers all required commands with appropriate options:

| Command Group | Commands | Coverage |
|---------------|----------|----------|
| Scene Generation | scene-generate, scene-list | COMPLETE |
| Asset Management | asset-index, asset-search, asset-info | COMPLETE |
| Validation | validate, validate-outline | COMPLETE |
| Rendering | render | COMPLETE |
| Variations | variations | COMPLETE |
| Review | review-create, review-list, review-approve, review-reject | COMPLETE |
| Utility | wizard, convert, info | COMPLETE |

**Issues Found:**

##### HIGH: Missing Progress Reporting for Headless Execution
- **Location:** Plan 5-08, render command, line 1208-1219
- **Description:** The `--json-output` flag is mentioned but the JSON schema for progress reporting is not defined. Headless execution requires structured progress output for CI/CD integration.
- **Recommendation:** Define JSON output schema:
  ```json
  {
    "status": "in_progress",
    "stage": "place_assets",
    "progress": 0.45,
    "message": "Placing 234 of 500 assets",
    "timestamp": "2026-02-21T14:30:00Z",
    "elapsed_seconds": 45.2,
    "estimated_remaining_seconds": 55.1
  }
  ```

##### HIGH: Missing Exit Codes Documentation
- **Location:** Plan 5-08, line 1103-1306
- **Description:** CLI exit codes are not documented. Essential for scripting and CI/CD.
- **Recommendation:** Document exit codes:
  ```python
  # Exit codes
  EXIT_SUCCESS = 0
  EXIT_VALIDATION_ERROR = 1
  EXIT_ASSET_NOT_FOUND = 2
  EXIT_RENDER_FAILED = 3
  EXIT_CHECKPOINT_FAILED = 4
  EXIT_INTERRUPTED = 130  # SIGINT
  ```

##### MEDIUM: Missing Signal Handling Specification
- **Location:** Plan 5-08, Task 4, line 1304
- **Description:** Task mentions "signal handling for graceful shutdown" but provides no implementation guidance.
- **Recommendation:** Add signal handler specification:
  ```python
  import signal

  def setup_signal_handlers(checkpoint: Checkpoint):
      def handle_interrupt(signum, frame):
          checkpoint.save("interrupted", {"signal": signum})
          sys.exit(130)
      signal.signal(signal.SIGINT, handle_interrupt)
      signal.signal(signal.SIGTERM, handle_interrupt)
  ```

##### MEDIUM: Missing Batch/Queue Mode
- **Location:** Plan 5-08
- **Description:** No support for batch processing multiple scenes from a queue file.
- **Recommendation:** Add batch command:
  ```bash
  blender-gsd batch --queue scenes_queue.yaml --parallel 4
  ```

**Automation Rick Verdict:** CONDITIONAL APPROVE - Define JSON output schema and exit codes before implementation.

---

### Pipeline Rick (Checkpoint/Resume) Review

**Status:** APPROVE

#### Checkpoint System Assessment

The checkpoint/resume system is well-designed with:

| Feature | Status | Quality |
|---------|--------|---------|
| Stage-based checkpointing | PRESENT | Excellent |
| JSON serialization | PRESENT | Complete |
| Error tracking | PRESENT | Good |
| Cleanup utilities | PRESENT | Good |
| CLI integration | PRESENT | Good |

**Strengths:**
- ResumableGenerator class with 8 clearly defined stages
- CheckpointData dataclass with comprehensive state capture
- Partial checkpoint ID matching for convenience
- Automatic cleanup with configurable retention

**Issues Found:**

##### MEDIUM: Missing Blender Scene State Serialization
- **Location:** Plan 5-09, CheckpointData, line 1320-1345
- **Description:** Checkpoint stores outline/selections/placement JSON but does not specify how to serialize actual Blender scene state (objects, materials, lighting).
- **Recommendation:** Add Blender state serialization:
  ```python
  @dataclass
  class CheckpointData:
      ...
      # Blender state
      scene_state_json: str = ""  # Serialized bpy.data snapshot
      texture_paths: List[str] = field(default_factory=list)
  ```

##### MEDIUM: No Distributed Checkpoint Support
- **Location:** Plan 5-09
- **Description:** For large scene generation, checkpoint storage should support network storage or database backends.
- **Recommendation:** Add abstract checkpoint backend:
  ```python
  class CheckpointBackend(ABC):
      @abstractmethod
      def save(self, checkpoint_id: str, data: bytes) -> None: pass
      @abstractmethod
      def load(self, checkpoint_id: str) -> Optional[bytes]: pass

  class FileCheckpointBackend(CheckpointBackend): ...
  class S3CheckpointBackend(CheckpointBackend): ...
  ```

**Pipeline Rick Verdict:** APPROVE - Minor improvements recommended but current design is solid.

---

### Phase 5 Summary

| Specialist | Verdict | Key Requirement |
|------------|---------|-----------------|
| Rick Prime (UX) | CONDITIONAL APPROVE | Add tier migration tools |
| Automation Rick (CLI) | CONDITIONAL APPROVE | Define JSON output schema |
| Pipeline Rick (Checkpoint) | APPROVE | None |

**Final Phase 5 Rating:** CONDITIONAL APPROVE

**Required Actions Before Implementation:**
1. Define JSON output schema for `--json-output` flag
2. Document CLI exit codes
3. Add TierMigration class for progressive disclosure
4. Add preview generation for templates

---

## Phase 6: GN Extensions Review

### Performance Rick (LOD/Culling) Review

**Status:** CONDITIONAL APPROVE

#### LOD System Assessment

The LOD system implements all 3 required tiers per SCENE_GENERATION_MASTER_PLAN.md:

| LOD Level | Distance | Instance Count | Geometry | Memory Budget |
|-----------|----------|----------------|----------|---------------|
| LOD0_FULL | <10m | <100 | Full detail | Per-asset |
| LOD1_DECIMATED | 10-50m | 100-1000 | 25% polys | Reduced |
| LOD2_BILLBOARD | >50m | 1000+ | Camera quad | Minimal |

**Memory Budget Configuration (Present):**
```python
@dataclass
class MemoryBudget:
    texture_pool_mb: int = 4096  # 4GB
    geometry_pool_mb: int = 2048  # 2GB
    instance_buffer_mb: int = 1024  # 1GB
```

**Issues Found:**

##### HIGH: Missing LOD Transition Smoothing
- **Location:** Task 5, line 488-500
- **Description:** LOD switching logic is abrupt (hard distance thresholds). This will cause visible "popping" when objects transition between LOD levels.
- **Recommendation:** Add hysteresis and dithering:
  ```python
  @dataclass
  class LODConfig:
      ...
      # Transition smoothing
      hysteresis_distance: float = 5.0  # Prevent rapid switching
      dither_enabled: bool = True  # Dither between LODs
      dither_range: float = 3.0  # Distance range for dithering
  ```

##### HIGH: Missing Memory Budget Enforcement Implementation
- **Location:** Task 5, MemoryBudget dataclass, line 476-479
- **Description:** MemoryBudget is defined but `check_memory_budget()` method is only listed as a stub. No actual memory tracking or enforcement mechanism is specified.
- **Recommendation:** Add memory tracking:
  ```python
  class MemoryTracker:
      def __init__(self, budget: MemoryBudget):
          self.budget = budget
          self.current_texture_mb = 0.0
          self.current_geometry_mb = 0.0

      def track_asset(self, asset_path: str) -> bool:
          """Returns False if adding asset would exceed budget."""
          tex_size, geo_size = self._estimate_asset_memory(asset_path)
          if self.current_texture_mb + tex_size > self.budget.texture_pool_mb:
              return False
          self.current_texture_mb += tex_size
          self.current_geometry_mb += geo_size
          return True
  ```

##### MEDIUM: Billboard Implementation Underspecified
- **Location:** Task 5, line 505-509
- **Description:** "Sample texture from original geometry at render time" is not feasible in Geometry Nodes - billboards require pre-baked impostor textures.
- **Recommendation:** Add impostor baking step:
  ```python
  def bake_impostor(self, asset: bpy.types.Object, resolution: int = 256) -> bpy.types.Image:
      """Bake 8-angle impostor texture for billboard LOD."""
      pass
  ```

##### MEDIUM: Missing Per-Category LOD Configuration
- **Location:** Task 5, LODConfig
- **Description:** LOD thresholds should be configurable per asset category (characters need higher detail than props).
- **Recommendation:** Add category-specific configs:
  ```python
  LOD_CATEGORY_CONFIGS = {
      "character": LODConfig(lod0_max_distance=20.0, lod1_max_distance=100.0),
      "vehicle": LODConfig(lod0_max_distance=15.0, lod1_max_distance=75.0),
      "prop": LODConfig(lod0_max_distance=5.0, lod1_max_distance=25.0),
      "vegetation": LODConfig(lod0_max_distance=3.0, lod1_max_distance=15.0),
  }
  ```

#### Culling System Assessment

| Culling Type | Status | Coverage |
|--------------|--------|----------|
| Frustum Culling | PRESENT | Complete |
| Distance Culling | PRESENT | Complete |
| Size Culling | PRESENT | Complete |
| Occlusion Culling | PRESENT | Optional (expensive) |

**Strengths:**
- Combined culling pipeline design
- Configurable update rate for performance
- Named attributes for debugging

**Issues Found:**

##### MEDIUM: Missing Culling Statistics API
- **Location:** Task 6, CullingSystem
- **Description:** While "culling stats as named attributes" is mentioned, no API is provided for retrieving statistics.
- **Recommendation:** Add statistics retrieval:
  ```python
  @dataclass
  class CullingStats:
      total_instances: int
      frustum_culled: int
      distance_culled: int
      size_culled: int
      visible_instances: int

  class CullingSystem:
      def get_stats(self, geometry: Node) -> CullingStats:
          """Retrieve culling statistics from geometry attributes."""
          pass
  ```

**Performance Rick Verdict:** CONDITIONAL APPROVE - Add LOD transition smoothing and memory budget enforcement before implementation.

---

### Phase 6 Summary

| Specialist | Verdict | Key Requirement |
|------------|---------|-----------------|
| Performance Rick (LOD) | CONDITIONAL APPROVE | Add transition smoothing |
| Performance Rick (Culling) | APPROVE | Minor: Add stats API |

**Final Phase 6 Rating:** CONDITIONAL APPROVE

**Required Actions Before Implementation:**
1. Add LOD hysteresis/dithering for smooth transitions
2. Implement MemoryTracker class with actual budget enforcement
3. Add impostor baking for billboards
4. Add per-category LOD configuration

---

## Council Consensus

### Phase 5: Scene Orchestrator
| Council Member | Vote |
|----------------|------|
| Rick Prime (UX) | CONDITIONAL APPROVE |
| Automation Rick (CLI) | CONDITIONAL APPROVE |
| Pipeline Rick (Checkpoint) | APPROVE |
| **Evil Morty (Final)** | **CONDITIONAL APPROVE** |

### Phase 6: GN Extensions
| Council Member | Vote |
|----------------|------|
| Performance Rick (LOD) | CONDITIONAL APPROVE |
| Performance Rick (Culling) | APPROVE |
| **Evil Morty (Final)** | **CONDITIONAL APPROVE** |

---

## Required Actions Summary

### Phase 5 - Before Implementation

| Priority | Issue | Owner | Effort |
|----------|-------|-------|--------|
| HIGH | Define JSON output schema for `--json-output` | Automation Rick | 1 hour |
| HIGH | Document CLI exit codes | Automation Rick | 30 min |
| HIGH | Add TierMigration class | Rick Prime | 2 hours |
| MEDIUM | Add template preview generation | Rick Prime | 2 hours |
| MEDIUM | Add wizard validation rules | Rick Prime | 1 hour |
| MEDIUM | Add signal handling specification | Automation Rick | 1 hour |
| MEDIUM | Add Blender scene state to checkpoints | Pipeline Rick | 3 hours |

### Phase 6 - Before Implementation

| Priority | Issue | Owner | Effort |
|----------|-------|-------|--------|
| HIGH | Add LOD hysteresis/dithering | Performance Rick | 2 hours |
| HIGH | Implement MemoryTracker class | Performance Rick | 4 hours |
| MEDIUM | Add impostor baking for billboards | Performance Rick | 4 hours |
| MEDIUM | Add per-category LOD configs | Performance Rick | 1 hour |
| MEDIUM | Add culling statistics API | Performance Rick | 2 hours |

---

## Recommended Code Additions

### Phase 5: TierMigration (NEW)

```python
# lib/orchestrator/ux_tiers.py (addition)

class TierMigration:
    """Enable seamless migration between UX tiers."""

    def wizard_to_yaml(self, wizard_responses: Dict[str, Any]) -> str:
        """Export wizard responses to YAML for manual editing."""
        import yaml
        scene_dict = {
            "scene": {
                "name": wizard_responses.get("scene_name", "Untitled"),
                "type": wizard_responses.get("scene_type", "interior"),
                "structure": {
                    "mood": wizard_responses.get("mood", "neutral"),
                    "style": wizard_responses.get("style", "realistic"),
                },
                "assets": wizard_responses.get("asset_requirements", []),
            }
        }
        return yaml.dump(scene_dict, default_flow_style=False)

    def yaml_to_api(self, yaml_path: str) -> str:
        """Convert YAML to fluent API code for programmatic use."""
        import yaml
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        scene = data.get("scene", {})
        code_lines = [
            'from blender_gsd import SceneBuilder',
            '',
            f'scene = (SceneBuilder("{scene.get("name", "Untitled")}")',
            f'    .type("{scene.get("type", "interior")}")',
            f'    .style("{scene.get("structure", {}).get("style", "realistic")}")',
            f'    .mood("{scene.get("structure", {}).get("mood", "neutral")}")',
        ]

        for asset in scene.get("assets", []):
            tags = asset.get("tags", [])
            code_lines.append(
                f'    .asset("{asset.get("category", "prop")}", '
                f'"{asset.get("name", "")}", tags={tags})'
            )

        code_lines.append('    .generate("output.blend")')
        code_lines.append(')')

        return '\n'.join(code_lines)
```

### Phase 5: CLI Exit Codes (NEW)

```python
# lib/orchestrator/cli.py (addition)

# Exit codes for scripting and CI/CD integration
class ExitCode:
    SUCCESS = 0
    VALIDATION_ERROR = 1
    ASSET_NOT_FOUND = 2
    RENDER_FAILED = 3
    CHECKPOINT_FAILED = 4
    CONFIG_ERROR = 5
    PERMISSION_ERROR = 6
    INTERRUPTED = 130  # Standard SIGINT exit code
```

### Phase 5: JSON Output Schema (NEW)

```python
# lib/orchestrator/progress.py (NEW)

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json

@dataclass
class ProgressReport:
    """Structured progress output for headless execution."""
    status: str  # "started", "in_progress", "completed", "failed"
    stage: str
    progress: float  # 0.0 to 1.0
    message: str
    timestamp: str
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float] = None
    error: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def create(cls, stage: str, progress: float, message: str,
               elapsed: float, estimated: float = None) -> "ProgressReport":
        return cls(
            status="in_progress",
            stage=stage,
            progress=progress,
            message=message,
            timestamp=datetime.now().isoformat() + "Z",
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=estimated,
        )
```

### Phase 6: LOD Hysteresis (NEW)

```python
# lib/geometry_nodes/lod_system.py (addition to LODConfig)

@dataclass
class LODConfig:
    """LOD configuration with transition smoothing."""
    lod0_max_distance: float = 10.0
    lod1_max_distance: float = 50.0
    lod0_max_instances: int = 100
    lod1_max_instances: int = 1000
    decimation_ratio: float = 0.25
    billboard_size: tuple = (1.0, 1.0)

    # Transition smoothing (NEW)
    hysteresis_distance: float = 5.0  # Prevent rapid LOD switching
    dither_enabled: bool = True  # Alpha dither between LODs
    dither_range: float = 3.0  # Distance range for dithering
    transition_frames: int = 5  # Frames to blend LODs (for animation)
```

### Phase 6: MemoryTracker (NEW)

```python
# lib/geometry_nodes/memory_tracker.py (NEW)

from dataclasses import dataclass, field
from typing import Dict, Optional
import os

@dataclass
class MemoryBudget:
    texture_pool_mb: int = 4096  # 4GB
    geometry_pool_mb: int = 2048  # 2GB
    instance_buffer_mb: int = 1024  # 1GB

@dataclass
class AssetMemoryInfo:
    texture_mb: float
    geometry_mb: float
    instance_count: int = 1

class MemoryTracker:
    """Track and enforce memory budgets during scene generation."""

    def __init__(self, budget: MemoryBudget):
        self.budget = budget
        self.current_texture_mb: float = 0.0
        self.current_geometry_mb: float = 0.0
        self.current_instances: int = 0
        self.asset_memory: Dict[str, AssetMemoryInfo] = {}

    def estimate_asset_memory(self, asset_path: str) -> AssetMemoryInfo:
        """Estimate memory usage for an asset."""
        # Simplified estimation based on file size
        file_size_mb = os.path.getsize(asset_path) / (1024 * 1024)
        # Rough split: 60% textures, 40% geometry
        return AssetMemoryInfo(
            texture_mb=file_size_mb * 0.6,
            geometry_mb=file_size_mb * 0.4,
        )

    def can_add_asset(self, asset_path: str, count: int = 1) -> bool:
        """Check if asset can be added without exceeding budget."""
        if asset_path not in self.asset_memory:
            self.asset_memory[asset_path] = self.estimate_asset_memory(asset_path)

        info = self.asset_memory[asset_path]
        new_texture = self.current_texture_mb + (info.texture_mb * count)
        new_geometry = self.current_geometry_mb + (info.geometry_mb * count)

        return (
            new_texture <= self.budget.texture_pool_mb and
            new_geometry <= self.budget.geometry_pool_mb
        )

    def add_asset(self, asset_path: str, count: int = 1) -> bool:
        """Add asset to tracking. Returns False if budget exceeded."""
        if not self.can_add_asset(asset_path, count):
            return False

        info = self.asset_memory.get(asset_path) or self.estimate_asset_memory(asset_path)
        self.current_texture_mb += info.texture_mb * count
        self.current_geometry_mb += info.geometry_mb * count
        self.current_instances += count
        return True

    def get_usage_report(self) -> Dict:
        """Get current memory usage report."""
        return {
            "texture_mb": {
                "used": round(self.current_texture_mb, 2),
                "budget": self.budget.texture_pool_mb,
                "percent": round(self.current_texture_mb / self.budget.texture_pool_mb * 100, 1),
            },
            "geometry_mb": {
                "used": round(self.current_geometry_mb, 2),
                "budget": self.budget.geometry_pool_mb,
                "percent": round(self.current_geometry_mb / self.budget.geometry_pool_mb * 100, 1),
            },
            "instances": self.current_instances,
        }
```

---

## Council Motto

> "The Council of Ricks doesn't approve mediocre plans. We enforce SLC, UX quality, and production-ready specifications because implementation doesn't forgive gaps in planning. Rick Prime ensures users can graduate from simple to complex. Automation Rick ensures scripts work reliably. Performance Rick ensures scenes actually render. No appeals."

---

**Review Completed:** 2026-02-21
**Review Duration:** ~15 minutes (parallel specialist review)
**Next Action:** Address required actions before implementation begins
