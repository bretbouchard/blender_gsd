# PLAN: MSG 1998 SD Compositing - Final Output Pipeline

**Phase:** 12.MSG-03
**Created:** 2026-02-22
**Depends On:** Phase 12.MSG-02 (Layer Compositing)
**Output To:** Editorial (Final deliverables)

---

## Goal

Implement final output pipeline for editorial deliverables with quality control validation.

---

## Tasks

### Task 1: Output Format Configuration
**File:** `lib/msg1998/output_formats.py`

```python
@dataclass
class OutputSpec:
    """Output specification for deliverables."""
    format: str  # "exr", "prores", "h264"
    resolution: tuple[int, int]
    frame_rate: int
    color_space: str
    compression: str
    metadata: dict

# Standard output formats
OUTPUT_FORMATS = {
    "master_exr": OutputSpec(
        format="OPEN_EXR",
        resolution=(4096, 1716),
        frame_rate=24,
        color_space="ACEScg",
        compression="ZIP",
    ),
    "prores_4444": OutputSpec(
        format="QUICKTIME",
        resolution=(4096, 1716),
        frame_rate=24,
        color_space="Rec709",
        compression="prores_4444",
    ),
    "prores_422": OutputSpec(
        format="QUICKTIME",
        resolution=(2048, 858),
        frame_rate=24,
        color_space="Rec709",
        compression="prores_422",
    ),
    "preview_h264": OutputSpec(
        format="FFMPEG",
        resolution=(1920, 804),
        frame_rate=24,
        color_space="Rec709",
        compression="h264_high",
    ),
}

def configure_output(scene: bpy.types.Scene, spec: OutputSpec) -> None:
    """Configure scene output settings."""
    ...
```

### Task 2: Color Space Conversion
**File:** `lib/msg1998/color_conversion.py`

```python
def convert_to_rec709(
    image: bpy.types.CompositorNode,
    from_space: str = "ACEScg"
) -> bpy.types.CompositorNode:
    """Convert from ACEScg to Rec.709 for delivery."""
    ...

def convert_to_srgb(
    image: bpy.types.CompositorNode,
    from_space: str = "ACEScg"
) -> bpy.types.CompositorNode:
    """Convert from ACEScg to sRGB for preview."""
    ...

def embed_color_profile(output_path: Path, profile: str = "Rec709") -> None:
    """Embed color profile metadata in output."""
    ...
```

### Task 3: Quality Control Validator
**File:** `lib/msg1998/qc_validator.py`

```python
@dataclass
class QCIssue:
    """Quality control issue."""
    severity: str  # "error", "warning", "info"
    category: str  # "technical", "visual", "period"
    description: str
    frame: int
    region: tuple  # x, y, w, h for region-specific issues

def validate_output(output_path: Path, config: dict) -> list[QCIssue]:
    """Run QC validation on output."""
    ...

def check_period_accuracy(output_path: Path) -> list[QCIssue]:
    """Check for period violations in final output."""
    ...

def check_technical_specs(output_path: Path, spec: OutputSpec) -> list[QCIssue]:
    """Validate technical specifications."""
    ...

# QC checks
QC_CHECKS = [
    "resolution_match",
    "frame_rate_correct",
    "color_space_valid",
    "no_clipped_highlights",
    "no_crushed_blacks",
    "grain_visible",
    "no_modern_elements",
    "layer_edges_invisible",
]
```

### Task 4: Batch Export
**File:** `lib/msg1998/batch_export.py`

```python
@dataclass
class ExportJob:
    """Batch export job."""
    shot_id: str
    scene_id: str
    composite_path: Path
    outputs: list[OutputSpec]
    status: str

def create_export_jobs(scene_id: str) -> list[ExportJob]:
    """Create export jobs for all shots in scene."""
    ...

def run_export_job(job: ExportJob) -> Path:
    """Execute single export job."""
    ...

def batch_export(scene_id: str, formats: list[str]) -> dict[str, Path]:
    """Export all shots in scene to specified formats."""
    ...
```

### Task 5: Editorial Package Generator
**File:** `lib/msg1998/editorial_package.py`

```python
@dataclass
class EditorialPackage:
    """Complete package for editorial delivery."""
    scene_id: str
    shots: list[str]
    master_files: dict[str, Path]  # shot_id -> exr
    prores_files: dict[str, Path]  # shot_id -> prores
    preview_files: dict[str, Path]  # shot_id -> h264
    metadata: dict
    qc_report: dict

def create_editorial_package(
    scene_id: str,
    output_dir: Path
) -> EditorialPackage:
    """Create complete editorial delivery package."""
    ...

def generate_shot_metadata(shot_id: str, render_config: dict) -> dict:
    """Generate metadata for editorial system."""
    ...
```

---

## Output Directory Structure

```
output/editorial/{SCENE_ID}/
├── masters/
│   ├── SHOT-XXX-XXX_master.exr
│   └── ...
├── prores/
│   ├── SHOT-XXX-XXX_prores4444.mov
│   └── ...
├── preview/
│   ├── SHOT-XXX-XXX_preview.mp4
│   └── ...
├── metadata/
│   ├── scene_metadata.json
│   └── shots/
│       ├── SHOT-XXX-001.json
│       └── ...
└── qc_report.json
```

---

## CLI Commands

```bash
# Export single shot
blender-gsd export-editorial --shot SHOT-002-001 --format prores

# Batch export scene
blender-gsd batch-export --scene SCN-002 --formats prores,exr

# Run QC validation
blender-gsd validate-output --scene SCN-002

# Create editorial package
blender-gsd create-package --scene SCN-002 --output packages/
```

---

## Validation Criteria

- [ ] All output formats generate correctly
- [ ] Color space conversion accurate
- [ ] QC catches period violations
- [ ] Editorial package structure correct

---

## Estimated Time

**2-3 hours**
