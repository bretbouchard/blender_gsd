# Plan Standards & Contracts

**Purpose**: Enforce quality, testability, and consistency across all phase plans

---

## Required Plan Header

Every PLAN.md file MUST start with this YAML front matter:

```yaml
---
phase: X.Y
plan: ZZ
title: Descriptive Title
depends_on:
  - X.Y-ZZ  # List of phase.plan dependencies
enables:
  - X.Y-ZZ  # List of phases this enables
parallel_safe: true/false
universal_stages:
  normalize: Description of input normalization
  primary: Description of main processing
  secondary: Description of refinement
  detail: Description of final touches
  output: Description of deliverables
critical_path: true/false
estimated_time: Xm
test_coverage: X%
---
```

---

## Measurable Acceptance Criteria Standards

### ❌ BAD (Vague, Untestable)

```markdown
## Acceptance Criteria
- [ ] Camera system works correctly
- [ ] Performance is good
- [ ] Output looks correct
- [ ] Code is clean
```

### ✅ GOOD (Specific, Measurable, Testable)

```markdown
## Acceptance Criteria

### Functional (Oracle Validation)
- [ ] `compare_numbers(camera.focal_length, 50.0, tolerance=0.1)` passes
- [ ] `compare_vectors(camera.position, (0, -5, 2), tolerance=0.001)` passes
- [ ] `file_exists(output_path, "Render output")` passes
- [ ] `exit_code_zero(render_result, "Render process")` passes

### Performance (Threshold-Based)
- [ ] Preset load completes in < 100ms (measured via `time.perf_counter()`)
- [ ] Camera creation takes < 10ms per camera
- [ ] Memory usage < 50MB for 1000 presets

### Quality (Regression Testing)
- [ ] `image_not_blank(render_output)` passes
- [ ] `images_similar(baseline, current, pixel_tolerance=0.01)` passes
- [ ] `video_valid(output_video)` passes
- [ ] `video_properties(output, codec="h264", width=1920, height=1080)` passes

### Coverage (Quantified)
- [ ] Unit test coverage >= 80% (measured via `pytest --cov`)
- [ ] All public functions have at least 1 test
- [ ] Edge cases documented and tested
```

---

## Oracle Validation Functions

Import from `lib.oracle`:

```python
from lib.oracle import (
    # Number/Vector comparison
    compare_numbers,
    compare_numbers_relative,
    compare_within_range,
    compare_vectors,
    compare_vectors_length,

    # File validation
    file_exists,
    directory_exists,
    files_exist,

    # Subprocess validation
    exit_code_zero,
    no_stderr,

    # Image validation
    image_not_blank,
    image_resolution,
    images_similar,

    # Video validation
    video_valid,
    video_properties,

    # Utilities
    all_pass,
)
```

---

## Test Structure Requirements

Every phase MUST have corresponding tests:

```
tests/
├── unit/
│   ├── test_phase_06_1_camera.py      # Phase 6.1 unit tests
│   ├── test_phase_06_2_lighting.py    # Phase 6.2 unit tests
│   └── ...
├── integration/
│   ├── test_phase_06_1_integration.py # Blender integration tests
│   └── ...
├── regression/
│   ├── test_phase_06_visual.py        # Visual regression tests
│   └── baselines/
│       └── phase_06/                  # Baseline images
└── fixtures/
    └── phase_06/                      # Test data
```

---

## Universal Stage Order Mapping

Every plan must map its tasks to the 5-stage pipeline:

| Stage | Purpose | Example Activities |
|-------|---------|-------------------|
| **Normalize** | Input validation & standardization | Load JSON, validate schema, convert types |
| **Primary** | Core processing | Create object, apply config, build structure |
| **Secondary** | Refinement | Apply rules, add constraints, link dependencies |
| **Detail** | Final touches | Validate constraints, optimize, polish |
| **Output** | Deliverables | Return result, write file, export data |

### Stage Mapping Template

```markdown
## Universal Stage Order Mapping

### Stage 0: Normalize
- Load preset JSON from disk
- Validate JSON schema against types
- Convert to Python dataclass

### Stage 1: Primary
- Create Blender camera object
- Apply basic settings (focal length, sensor size)
- Set transform (position, rotation)

### Stage 2: Secondary
- Apply cinematography rules (180° rule, etc.)
- Set depth of field based on f-stop
- Configure focus distance

### Stage 3: Detail
- Validate against physical constraints
- Apply lens imperfections if configured
- Link to rig if present

### Stage 4: Output
- Return configured camera object
- Log creation for debugging
- Update state management
```

---

## No Placeholder Policy (SLC Enforcement)

### ❌ FORBIDDEN Patterns

```python
# NO stub methods
def process_camera(self, config):
    pass  # TODO: implement

# NO NotImplemented errors in production
def get_preset(self, name):
    raise NotImplementedError("Coming soon")

# NO placeholder returns
def calculate_exposure(self):
    return None  # Placeholder

# NO vague TODOs
# TODO: fix this later
```

### ✅ REQUIRED Patterns

```python
# Complete implementation OR no function
def process_camera(self, config: CameraConfig) -> bpy.types.Camera:
    """Process camera configuration into Blender camera object."""
    camera = self._create_camera(config.name)
    self._apply_settings(camera, config)
    self._validate_camera(camera, config)
    return camera

# Clear error if feature not in scope
def get_preset(self, name: str) -> CameraConfig:
    """Get preset by name."""
    if name not in self._presets:
        raise PresetNotFoundError(f"Preset '{name}' not found. Available: {list(self._presets.keys())}")
    return self._presets[name]
```

---

## Test File Template

```python
"""
Phase X.Y - [Title] Tests

Tests for: lib/cinematic/[module].py
Coverage target: 80%+
"""

import pytest
from pathlib import Path
from lib.oracle import compare_numbers, compare_vectors, file_exists
from lib.cinematic import [module]


class Test[Feature]Unit:
    """Unit tests for [Feature] - no Blender required."""

    def test_basic_functionality(self):
        """Test basic case with expected values."""
        result = [module].function(arg1, arg2)
        compare_numbers(result.expected_property, expected_value, tolerance=0.001)

    def test_edge_case_empty_input(self):
        """Test handling of empty input."""
        with pytest.raises(ValueError):
            [module].function(None)

    def test_edge_case_extreme_values(self):
        """Test handling of extreme values."""
        result = [module].function(extreme_value)
        compare_within_range(result.value, min_allowed, max_allowed)


@pytest.mark.requires_blender
class Test[Feature]Integration:
    """Integration tests for [Feature] - requires Blender."""

    def test_blender_camera_creation(self, blender_available, temp_blend_file):
        """Test camera creation in Blender."""
        if not blender_available:
            pytest.skip("Blender not available")

        # Test implementation
        pass


@pytest.mark.visual
class Test[Feature]Regression:
    """Visual regression tests for [Feature]."""

    def test_render_matches_baseline(self, baseline_dir, current_output_dir):
        """Test that render output matches baseline."""
        baseline = baseline_dir / "phase_XY" / "expected.png"
        current = current_output_dir / "output.png"

        images_similar(baseline, current, pixel_tolerance=0.01)
```

---

## CI Workflow Requirements

Every phase MUST pass this CI pipeline:

```yaml
# .github/workflows/phase-validation.yml
name: Phase Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Lint (ruff)
        run: ruff check lib/ tests/

      - name: Type check (mypy)
        run: mypy lib/ --strict

      - name: Unit tests
        run: pytest tests/unit -v --cov=lib --cov-fail-under=80

      - name: Integration tests
        run: pytest tests/integration -v -m requires_blender
        continue-on-error: true  # Blender may not be available

      - name: Regression tests
        run: pytest tests/regression -v -m visual
```

---

## Plan Review Checklist

Before marking any plan as complete:

- [ ] YAML header complete with all fields
- [ ] All acceptance criteria are measurable
- [ ] Oracle validation functions specified
- [ ] Universal Stage Order mapping included
- [ ] No placeholders or TODOs in code
- [ ] Unit tests written (>= 80% coverage)
- [ ] Integration tests written (if Blender-dependent)
- [ ] Visual regression tests written (if output is visual)
- [ ] CI pipeline passes
- [ ] Documentation updated

---

*These standards are enforced by the Council of Ricks review process.*
