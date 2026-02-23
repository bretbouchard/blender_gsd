"""
MSG 1998 - Shared Types and Data Structures
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import bpy
    from mathutils import Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Matrix = Any


class ModelingStage(Enum):
    """Universal Stage Order for location building."""
    NORMALIZE = 0      # Scale to real-world units
    PRIMARY = 1        # Base geometry (walls, roof)
    SECONDARY = 2      # Windows, doors, details
    DETAIL = 3         # Textures, wear, signage
    OUTPUT_PREP = 4    # Render layer setup


class PeriodViolationSeverity(Enum):
    """Severity levels for period accuracy issues."""
    ERROR = "error"      # Must fix before render
    WARNING = "warning"  # Should fix if possible
    INFO = "info"        # Awareness only


# =============================================================================
# Phase 9.MSG-01 Types (fSpy Import & Handoff)
# =============================================================================

@dataclass
class FSpyImportResult:
    """Result of fSpy import operation."""
    camera: Optional[Any] = None  # bpy.types.Object
    reference_image: Optional[Any] = None  # bpy.types.Image
    original_fspy_path: Path = field(default_factory=lambda: Path())
    focal_length_mm: float = 35.0
    sensor_width_mm: float = 36.0
    rotation_matrix: Optional[Matrix] = None
    success: bool = False
    errors: List[str] = field(default_factory=list)


@dataclass
class ReferenceSet:
    """Set of reference images for a location."""
    location_id: str
    images: List[Path] = field(default_factory=list)
    fspy_files: List[Path] = field(default_factory=list)
    primary_angle: str = "north"  # "north", "south", "east", "west"


@dataclass
class LocationAsset:
    """Location asset from FDX handoff."""
    location_id: str
    name: str
    address: str
    coordinates: Tuple[float, float] = (0.0, 0.0)  # (lat, lon)
    period_year: int = 1998
    source_dir: Path = field(default_factory=lambda: Path())
    references: List[Path] = field(default_factory=list)
    fspy_files: List[Path] = field(default_factory=list)
    period_notes: str = ""


@dataclass
class FDXHandoffPackage:
    """Received handoff from FDX GSD."""
    scene_id: str
    locations: List[LocationAsset] = field(default_factory=list)
    received_at: datetime = field(default_factory=datetime.now)
    manifest: Dict[str, Any] = field(default_factory=dict)
    source_path: Path = field(default_factory=lambda: Path())
    valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class PeriodViolation:
    """Detected period accuracy issue."""
    element: str
    description: str
    severity: PeriodViolationSeverity = PeriodViolationSeverity.WARNING
    suggestion: str = ""
    location: str = ""  # File or object path


# =============================================================================
# Phase 9.MSG-02 Types (Modeling)
# =============================================================================

@dataclass
class BuildingSpec:
    """Specification for building geometry."""
    width_m: float = 10.0
    depth_m: float = 10.0
    height_m: float = 10.0
    floors: int = 1
    style: str = "commercial"  # "commercial", "residential", "industrial"


@dataclass
class WindowSpec:
    """Window specification for building."""
    width_m: float = 1.2
    height_m: float = 1.5
    frame_depth_m: float = 0.05
    glass_thickness_m: float = 0.01
    has_frame: bool = True


@dataclass
class LocationBuildState:
    """State tracker for location build."""
    location_id: str
    current_stage: ModelingStage = ModelingStage.NORMALIZE
    geometry_stats: Dict[str, Any] = field(default_factory=dict)
    period_issues: List[PeriodViolation] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    blend_path: Optional[Path] = None


# =============================================================================
# Phase 9.MSG-03 Types (Render Layers)
# =============================================================================

@dataclass
class MSGRenderPasses:
    """Render passes required for SD compositing."""
    beauty: bool = True
    depth: bool = True
    normal: bool = True
    object_id: bool = True
    diffuse: bool = True
    shadow: bool = True
    ao: bool = True
    cryptomatte: bool = True
    cryptomatte_layers: List[str] = field(default_factory=lambda: ["object", "material"])


@dataclass
class CompositeLayer:
    """Layer for compositing separation."""
    name: str  # "background", "midground", "foreground"
    objects: List[Any] = field(default_factory=list)  # bpy.types.Object
    render_passes: List[str] = field(default_factory=list)
    mask_color: Tuple[float, float, float] = (1.0, 0.0, 0.0)


@dataclass
class MSG1998RenderProfile:
    """Render settings for MSG 1998 output."""
    resolution: Tuple[int, int] = (4096, 1716)  # 2.39:1 aspect
    frame_rate: int = 24
    color_space: str = "ACEScg"
    samples: int = 256
    use_denoiser: bool = True
    beauty_format: str = "OPEN_EXR"
    pass_format: str = "OPEN_EXR"
    motion_blur: bool = False


# =============================================================================
# Phase 12.MSG-01 Types (ControlNet & SD)
# =============================================================================

@dataclass
class ControlNetConfig:
    """ControlNet configuration for SD generation."""
    depth_model: str = "control_v11f1p_sd15_depth"
    depth_weight: float = 1.0
    normal_model: str = "control_v11p_sd15_normalbae"
    normal_weight: float = 0.8
    guidance_start: float = 0.0
    guidance_end: float = 1.0
    canny_model: str = "control_v11p_sd15_canny"
    canny_weight: float = 0.5
    canny_enabled: bool = False


@dataclass
class SDShotConfig:
    """SD configuration for a shot (from FDX GSD)."""
    shot_id: str
    scene_id: str
    seeds: Dict[str, int] = field(default_factory=dict)  # layer -> seed
    positive_prompt: str = ""
    negative_prompt: str = ""
    controlnet_config: ControlNetConfig = field(default_factory=ControlNetConfig)
    layer_configs: Dict[str, Any] = field(default_factory=dict)
    steps: int = 30
    cfg_scale: float = 7.0
    sampler: str = "DPM++ 2M Karras"


@dataclass
class SDGenerationResult:
    """Result of SD generation."""
    layer_name: str
    seed: int
    output_path: Path = field(default_factory=lambda: Path())
    generation_time: float = 0.0
    controlnet_used: List[str] = field(default_factory=list)
    success: bool = False
    hash: str = ""


# =============================================================================
# Phase 12.MSG-02 Types (Compositing)
# =============================================================================

@dataclass
class FilmLook1998:
    """1998 film aesthetic parameters."""
    grain_intensity: float = 0.15
    grain_size: float = 1.0
    lens_distortion: float = 0.02
    chromatic_aberration: float = 0.003
    vignette_strength: float = 0.4
    color_temperature: float = 5500  # Slightly warm
    # Cooke S4 characteristics
    cooke_flare_intensity: float = 0.1
    cooke_breathing: float = 0.02


@dataclass
class ColorGradeConfig:
    """Color grading configuration."""
    lut_path: str = "luts/kodak_vision3_500t.cube"
    exposure_adjust: float = 0.0
    contrast_adjust: float = 1.0
    saturation_adjust: float = 1.0
    shadows_lift: float = 0.0
    highlights_roll: float = 1.0


@dataclass
class LayerInput:
    """Input layer for compositing."""
    name: str  # "background", "midground", "foreground"
    sd_output: Path = field(default_factory=lambda: Path())
    original_render: Path = field(default_factory=lambda: Path())
    mask: Path = field(default_factory=lambda: Path())
    depth_value: float = 0.5  # For depth-based effects


# =============================================================================
# Phase 12.MSG-03 Types (Output)
# =============================================================================

@dataclass
class OutputSpec:
    """Output specification for deliverables."""
    format: str = "OPEN_EXR"  # "exr", "prores", "h264"
    resolution: Tuple[int, int] = (4096, 1716)
    frame_rate: int = 24
    color_space: str = "ACEScg"
    compression: str = "ZIP"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QCIssue:
    """Quality control issue."""
    severity: str  # "error", "warning", "info"
    category: str  # "technical", "visual", "period"
    description: str = ""
    frame: int = 0
    region: Tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, w, h
    suggestion: str = ""


@dataclass
class ExportJob:
    """Batch export job."""
    shot_id: str
    scene_id: str
    composite_path: Path = field(default_factory=lambda: Path())
    outputs: List[OutputSpec] = field(default_factory=list)
    status: str = "pending"  # "pending", "running", "complete", "failed"


@dataclass
class EditorialPackage:
    """Complete package for editorial delivery."""
    scene_id: str
    shots: List[str] = field(default_factory=list)
    master_files: Dict[str, Path] = field(default_factory=dict)  # shot_id -> exr
    prores_files: Dict[str, Path] = field(default_factory=dict)  # shot_id -> prores
    preview_files: Dict[str, Path] = field(default_factory=dict)  # shot_id -> h264
    metadata: Dict[str, Any] = field(default_factory=dict)
    qc_report: Dict[str, Any] = field(default_factory=dict)
