"""
Production Orchestrator Types

Master orchestrator data structures for one-command production execution.

Requirements:
- REQ-ORCH-01: Load complete production from YAML
- REQ-ORCH-02: Validate production before execution
- REQ-ORCH-03: Execute all phases in order
- REQ-ORCH-04: Progress tracking and resume
- REQ-ORCH-05: Parallel execution where possible
- REQ-ORCH-06: Error handling and rollback

Part of Phase 14.1: Production Orchestrator
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import uuid


class ExecutionPhase(str, Enum):
    """Production execution phases."""
    VALIDATE = "validate"
    PREPARE = "prepare"
    CHARACTERS = "characters"
    LOCATIONS = "locations"
    SHOTS = "shots"
    POST_PROCESS = "post_process"
    EXPORT = "export"
    FINALIZE = "finalize"


class ExecutionStatus(str, Enum):
    """Status of execution."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationSeverity(str, Enum):
    """Validation issue severity."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Execution phases in order
EXECUTION_PHASES = [
    ExecutionPhase.VALIDATE,
    ExecutionPhase.PREPARE,
    ExecutionPhase.CHARACTERS,
    ExecutionPhase.LOCATIONS,
    ExecutionPhase.SHOTS,
    ExecutionPhase.POST_PROCESS,
    ExecutionPhase.EXPORT,
    ExecutionPhase.FINALIZE,
]


@dataclass
class ProductionMeta:
    """
    Production metadata.

    Attributes:
        title: Production title
        version: Configuration version
        created: Creation timestamp
        modified: Last modification timestamp
        author: Author name
        description: Production description
        production_id: Unique identifier for this production
    """
    title: str = "Untitled Production"
    version: str = "1.0.0"
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    modified: str = field(default_factory=lambda: datetime.now().isoformat())
    author: str = ""
    description: str = ""
    production_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "version": self.version,
            "created": self.created,
            "modified": self.modified,
            "author": self.author,
            "description": self.description,
            "production_id": self.production_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProductionMeta:
        """Create from dictionary."""
        return cls(
            title=data.get("title", "Untitled Production"),
            version=data.get("version", "1.0.0"),
            created=data.get("created", datetime.now().isoformat()),
            modified=data.get("modified", datetime.now().isoformat()),
            author=data.get("author", ""),
            description=data.get("description", ""),
            production_id=data.get("production_id", str(uuid.uuid4())[:8]),
        )

    def touch(self) -> None:
        """Update modification timestamp."""
        self.modified = datetime.now().isoformat()


@dataclass
class CharacterConfig:
    """
    Character configuration for production.

    Attributes:
        name: Character name
        model: Path to character model file
        wardrobe_assignments: Scene range to costume name mappings
        variants: Variant configurations (e.g., stunt double)
        notes: Additional notes
    """
    name: str = ""
    model: str = ""
    wardrobe_assignments: Dict[str, str] = field(default_factory=dict)  # "scenes_1_10" -> "hero_casual"
    variants: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "model": self.model,
            "wardrobe_assignments": self.wardrobe_assignments,
            "variants": self.variants,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CharacterConfig:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            model=data.get("model", ""),
            wardrobe_assignments=data.get("wardrobe_assignments", {}),
            variants=data.get("variants", {}),
            notes=data.get("notes", ""),
        )

    def get_costume_for_scene(self, scene: int) -> Optional[str]:
        """Get costume name for a specific scene number."""
        for range_key, costume in self.wardrobe_assignments.items():
            # Parse range like "scenes_1_10" or "1-10"
            try:
                if "scenes_" in range_key:
                    parts = range_key.replace("scenes_", "").split("_")
                elif "-" in range_key:
                    parts = range_key.split("-")
                else:
                    continue

                if len(parts) == 2:
                    start, end = int(parts[0]), int(parts[1])
                    if start <= scene <= end:
                        return costume
            except (ValueError, IndexError):
                continue
        return None


@dataclass
class LocationConfig:
    """
    Location configuration for production.

    Attributes:
        name: Location name
        preset: Set builder preset name
        hdri: HDRI preset or file path
        notes: Additional notes
        scenes: List of scene numbers using this location
    """
    name: str = ""
    preset: str = ""
    hdri: str = ""
    notes: str = ""
    scenes: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "preset": self.preset,
            "hdri": self.hdri,
            "notes": self.notes,
            "scenes": self.scenes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LocationConfig:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            preset=data.get("preset", ""),
            hdri=data.get("hdri", ""),
            notes=data.get("notes", ""),
            scenes=data.get("scenes", []),
        )


@dataclass
class ShotConfig:
    """
    Shot configuration for production.

    Attributes:
        name: Shot name/identifier
        template: Shot template name
        scene: Scene number
        character: Character name (if applicable)
        location: Location name (if applicable)
        duration: Duration in frames
        frame_range: Start and end frame (start, end)
        notes: Additional notes
        variations: Number of variations to generate
    """
    name: str = ""
    template: str = ""
    scene: int = 0
    character: str = ""
    location: str = ""
    duration: int = 120
    frame_range: Tuple[int, int] = (1, 120)
    notes: str = ""
    variations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "template": self.template,
            "scene": self.scene,
            "character": self.character,
            "location": self.location,
            "duration": self.duration,
            "frame_range": list(self.frame_range),
            "notes": self.notes,
            "variations": self.variations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ShotConfig:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            template=data.get("template", ""),
            scene=data.get("scene", 0),
            character=data.get("character", ""),
            location=data.get("location", ""),
            duration=data.get("duration", 120),
            frame_range=tuple(data.get("frame_range", (1, 120))),
            notes=data.get("notes", ""),
            variations=data.get("variations", 0),
        )


@dataclass
class StyleConfig:
    """
    Visual style configuration.

    Attributes:
        preset: Style preset name (e.g., "cinematic_teal_orange")
        era: Time period (e.g., "present", "1980s", "future")
        mood: Overall mood (e.g., "dramatic", "comedic", "suspenseful")
        color_grade: Color grading preset
        contrast: Contrast level (low, medium, high)
    """
    preset: str = "cinematic"
    era: str = "present"
    mood: str = "dramatic"
    color_grade: str = "neutral"
    contrast: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "preset": self.preset,
            "era": self.era,
            "mood": self.mood,
            "color_grade": self.color_grade,
            "contrast": self.contrast,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StyleConfig:
        """Create from dictionary."""
        return cls(
            preset=data.get("preset", "cinematic"),
            era=data.get("era", "present"),
            mood=data.get("mood", "dramatic"),
            color_grade=data.get("color_grade", "neutral"),
            contrast=data.get("contrast", "medium"),
        )


@dataclass
class RetroConfig:
    """
    Retro/pixel art output configuration.

    Attributes:
        enabled: Whether retro output is enabled
        palette: Color palette name (e.g., "snes", "nes", "gameboy")
        dither: Dithering mode (none, ordered, error_diffusion)
        pixel_size: Pixel size multiplier
        target_resolution: Target resolution (width, height)
        crt_effects: Whether to apply CRT display effects
    """
    enabled: bool = False
    palette: str = "snes"
    dither: str = "error_diffusion"
    pixel_size: int = 2
    target_resolution: Tuple[int, int] = (256, 224)
    crt_effects: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "palette": self.palette,
            "dither": self.dither,
            "pixel_size": self.pixel_size,
            "target_resolution": list(self.target_resolution),
            "crt_effects": self.crt_effects,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RetroConfig:
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            palette=data.get("palette", "snes"),
            dither=data.get("dither", "error_diffusion"),
            pixel_size=data.get("pixel_size", 2),
            target_resolution=tuple(data.get("target_resolution", (256, 224))),
            crt_effects=data.get("crt_effects", False),
        )


@dataclass
class OutputFormat:
    """
    Output format specification.

    Attributes:
        name: Format name (e.g., "cinema_4k", "streaming_1080p")
        format: Format identifier
        codec: Video codec (e.g., "prores_4444", "h264")
        resolution: Output resolution (width, height)
        frame_rate: Frames per second
        retro_config: Optional retro conversion settings
        output_path: Output directory path
    """
    name: str = ""
    format: str = "streaming_1080p"
    codec: str = "prores_4444"
    resolution: Tuple[int, int] = (1920, 1080)
    frame_rate: int = 24
    retro_config: Optional[RetroConfig] = None
    output_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "format": self.format,
            "codec": self.codec,
            "resolution": list(self.resolution),
            "frame_rate": self.frame_rate,
            "retro_config": self.retro_config.to_dict() if self.retro_config else None,
            "output_path": self.output_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OutputFormat:
        """Create from dictionary."""
        retro_data = data.get("retro_config")
        retro_config = RetroConfig.from_dict(retro_data) if retro_data else None
        return cls(
            name=data.get("name", ""),
            format=data.get("format", "streaming_1080p"),
            codec=data.get("codec", "prores_4444"),
            resolution=tuple(data.get("resolution", (1920, 1080))),
            frame_rate=data.get("frame_rate", 24),
            retro_config=retro_config,
            output_path=data.get("output_path", ""),
        )


@dataclass
class RenderSettings:
    """
    Render settings for production.

    Attributes:
        engine: Render engine (CYCLES, BLENDER_EEVEE_NEXT)
        samples: Render samples
        resolution_x: Width in pixels
        resolution_y: Height in pixels
        use_denoising: Enable denoising
        quality_tier: Quality preset (preview, production, archive)
    """
    engine: str = "BLENDER_EEVEE_NEXT"
    samples: int = 64
    resolution_x: int = 1920
    resolution_y: int = 1080
    use_denoising: bool = True
    quality_tier: str = "production"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "engine": self.engine,
            "samples": self.samples,
            "resolution_x": self.resolution_x,
            "resolution_y": self.resolution_y,
            "use_denoising": self.use_denoising,
            "quality_tier": self.quality_tier,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RenderSettings:
        """Create from dictionary."""
        return cls(
            engine=data.get("engine", "BLENDER_EEVEE_NEXT"),
            samples=data.get("samples", 64),
            resolution_x=data.get("resolution_x", 1920),
            resolution_y=data.get("resolution_y", 1080),
            use_denoising=data.get("use_denoising", True),
            quality_tier=data.get("quality_tier", "production"),
        )


@dataclass
class ProductionConfig:
    """
    Complete production configuration.

    This is the root configuration for a production, containing all
    metadata, characters, locations, shots, and output specifications.

    Attributes:
        meta: Production metadata
        script_path: Path to script file (Fountain or FDX)
        style: Visual style configuration
        characters: Character configurations by name
        locations: Location configurations by name
        shots: Shot configurations in order
        shot_list_path: Optional path to external shot list
        render_settings: Render settings
        outputs: Output format specifications
        base_path: Base path for resolving relative paths
    """
    meta: ProductionMeta = field(default_factory=ProductionMeta)
    script_path: str = ""
    style: StyleConfig = field(default_factory=StyleConfig)
    characters: Dict[str, CharacterConfig] = field(default_factory=dict)
    locations: Dict[str, LocationConfig] = field(default_factory=dict)
    shots: List[ShotConfig] = field(default_factory=list)
    shot_list_path: str = ""
    render_settings: RenderSettings = field(default_factory=RenderSettings)
    outputs: List[OutputFormat] = field(default_factory=list)
    base_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "meta": self.meta.to_dict(),
            "script_path": self.script_path,
            "style": self.style.to_dict(),
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "locations": {k: v.to_dict() for k, v in self.locations.items()},
            "shots": [s.to_dict() for s in self.shots],
            "shot_list_path": self.shot_list_path,
            "render_settings": self.render_settings.to_dict(),
            "outputs": [o.to_dict() for o in self.outputs],
            "base_path": self.base_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProductionConfig:
        """Create from dictionary."""
        meta_data = data.get("meta", {})
        style_data = data.get("style", {})
        render_data = data.get("render_settings", {})

        characters = {}
        for name, char_data in data.get("characters", {}).items():
            characters[name] = CharacterConfig.from_dict(char_data)

        locations = {}
        for name, loc_data in data.get("locations", {}).items():
            locations[name] = LocationConfig.from_dict(loc_data)

        shots = [ShotConfig.from_dict(s) for s in data.get("shots", [])]
        outputs = [OutputFormat.from_dict(o) for o in data.get("outputs", [])]

        return cls(
            meta=ProductionMeta.from_dict(meta_data),
            script_path=data.get("script_path", ""),
            style=StyleConfig.from_dict(style_data),
            characters=characters,
            locations=locations,
            shots=shots,
            shot_list_path=data.get("shot_list_path", ""),
            render_settings=RenderSettings.from_dict(render_data),
            outputs=outputs,
            base_path=data.get("base_path", ""),
        )

    def get_shot_count(self) -> int:
        """Get total shot count including variations."""
        count = len(self.shots)
        for shot in self.shots:
            count += shot.variations
        return count

    def get_scenes(self) -> List[int]:
        """Get list of all scene numbers."""
        scenes = set()
        for shot in self.shots:
            if shot.scene > 0:
                scenes.add(shot.scene)
        return sorted(scenes)


@dataclass
class ValidationIssue:
    """
    Validation problem.

    Attributes:
        path: JSON path to issue (e.g., "characters.hero.model")
        severity: Issue severity (error, warning, info)
        message: Human-readable message
        suggestion: Optional suggestion for fixing
    """
    path: str = ""
    severity: str = "error"
    message: str = ""
    suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "severity": self.severity,
            "message": self.message,
            "suggestion": self.suggestion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValidationIssue:
        """Create from dictionary."""
        return cls(
            path=data.get("path", ""),
            severity=data.get("severity", "error"),
            message=data.get("message", ""),
            suggestion=data.get("suggestion", ""),
        )

    def is_error(self) -> bool:
        """Check if this is an error-level issue."""
        return self.severity == ValidationSeverity.ERROR.value

    def is_warning(self) -> bool:
        """Check if this is a warning-level issue."""
        return self.severity == ValidationSeverity.WARNING.value


@dataclass
class ValidationResult:
    """
    Complete validation result.

    Attributes:
        valid: Whether production is valid (no errors)
        issues: All validation issues
    """
    valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get all error-level issues."""
        return [i for i in self.issues if i.is_error()]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get all warning-level issues."""
        return [i for i in self.issues if i.is_warning()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "valid": self.valid,
            "issues": [i.to_dict() for i in self.issues],
            "errors": [i.to_dict() for i in self.errors],
            "warnings": [i.to_dict() for i in self.warnings],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValidationResult:
        """Create from dictionary."""
        issues = [ValidationIssue.from_dict(i) for i in data.get("issues", [])]
        return cls(
            valid=data.get("valid", True),
            issues=issues,
        )

    def add_error(self, path: str, message: str, suggestion: str = "") -> None:
        """Add an error-level issue."""
        self.issues.append(ValidationIssue(
            path=path,
            severity=ValidationSeverity.ERROR.value,
            message=message,
            suggestion=suggestion,
        ))
        self.valid = False

    def add_warning(self, path: str, message: str, suggestion: str = "") -> None:
        """Add a warning-level issue."""
        self.issues.append(ValidationIssue(
            path=path,
            severity=ValidationSeverity.WARNING.value,
            message=message,
            suggestion=suggestion,
        ))


@dataclass
class ExecutionState:
    """
    Current execution state for resume.

    Attributes:
        production_id: Production identifier
        started_at: Execution start timestamp
        updated_at: Last update timestamp
        current_phase: Current execution phase
        current_shot: Current shot index
        completed_shots: List of completed shot indices
        failed_shots: List of failed shot indices
        checkpoint_path: Path to checkpoint file
        status: Execution status
        progress: Progress percentage (0-100)
        error_message: Last error message if failed
    """
    production_id: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    current_phase: str = ExecutionPhase.VALIDATE.value
    current_shot: int = 0
    completed_shots: List[int] = field(default_factory=list)
    failed_shots: List[int] = field(default_factory=list)
    checkpoint_path: str = ""
    status: str = ExecutionStatus.PENDING.value
    progress: float = 0.0
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "production_id": self.production_id,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "current_phase": self.current_phase,
            "current_shot": self.current_shot,
            "completed_shots": self.completed_shots,
            "failed_shots": self.failed_shots,
            "checkpoint_path": self.checkpoint_path,
            "status": self.status,
            "progress": self.progress,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionState:
        """Create from dictionary."""
        return cls(
            production_id=data.get("production_id", ""),
            started_at=data.get("started_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            current_phase=data.get("current_phase", ExecutionPhase.VALIDATE.value),
            current_shot=data.get("current_shot", 0),
            completed_shots=data.get("completed_shots", []),
            failed_shots=data.get("failed_shots", []),
            checkpoint_path=data.get("checkpoint_path", ""),
            status=data.get("status", ExecutionStatus.PENDING.value),
            progress=data.get("progress", 0.0),
            error_message=data.get("error_message", ""),
        )

    def touch(self) -> None:
        """Update timestamp."""
        self.updated_at = datetime.now().isoformat()

    def advance_phase(self) -> None:
        """Move to next execution phase."""
        current_idx = 0
        for i, phase in enumerate(EXECUTION_PHASES):
            if phase.value == self.current_phase:
                current_idx = i
                break

        if current_idx < len(EXECUTION_PHASES) - 1:
            self.current_phase = EXECUTION_PHASES[current_idx + 1].value
            self.touch()

    def complete_shot(self, shot_index: int) -> None:
        """Mark a shot as completed."""
        if shot_index not in self.completed_shots:
            self.completed_shots.append(shot_index)
        if shot_index in self.failed_shots:
            self.failed_shots.remove(shot_index)
        self.touch()

    def fail_shot(self, shot_index: int) -> None:
        """Mark a shot as failed."""
        if shot_index not in self.failed_shots:
            self.failed_shots.append(shot_index)
        self.touch()


@dataclass
class ProductionResult:
    """
    Result of production execution.

    Attributes:
        success: Whether execution completed successfully
        shots_completed: Number of shots completed
        shots_failed: Number of shots failed
        total_time: Total execution time in seconds
        output_paths: List of output file paths
        errors: List of error messages
        warnings: List of warning messages
        state: Final execution state
    """
    success: bool = False
    shots_completed: int = 0
    shots_failed: int = 0
    total_time: float = 0.0
    output_paths: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    state: Optional[ExecutionState] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "shots_completed": self.shots_completed,
            "shots_failed": self.shots_failed,
            "total_time": self.total_time,
            "output_paths": self.output_paths,
            "errors": self.errors,
            "warnings": self.warnings,
            "state": self.state.to_dict() if self.state else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProductionResult:
        """Create from dictionary."""
        state_data = data.get("state")
        state = ExecutionState.from_dict(state_data) if state_data else None
        return cls(
            success=data.get("success", False),
            shots_completed=data.get("shots_completed", 0),
            shots_failed=data.get("shots_failed", 0),
            total_time=data.get("total_time", 0.0),
            output_paths=data.get("output_paths", []),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            state=state,
        )


@dataclass
class ParallelConfig:
    """
    Parallel execution configuration.

    Attributes:
        max_workers: Maximum number of parallel workers
        backend: Execution backend (thread, process)
        chunk_size: Number of items per chunk
    """
    max_workers: int = 4
    backend: str = "thread"
    chunk_size: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "max_workers": self.max_workers,
            "backend": self.backend,
            "chunk_size": self.chunk_size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ParallelConfig:
        """Create from dictionary."""
        return cls(
            max_workers=data.get("max_workers", 4),
            backend=data.get("backend", "thread"),
            chunk_size=data.get("chunk_size", 1),
        )


# Standard output format presets
OUTPUT_FORMAT_PRESETS = {
    "cinema_4k": OutputFormat(
        name="Cinema 4K",
        format="cinema_4k",
        codec="prores_4444",
        resolution=(4096, 2160),
        frame_rate=24,
    ),
    "cinema_2k": OutputFormat(
        name="Cinema 2K",
        format="cinema_2k",
        codec="prores_422",
        resolution=(2048, 1080),
        frame_rate=24,
    ),
    "streaming_4k": OutputFormat(
        name="Streaming 4K",
        format="streaming_4k",
        codec="h264",
        resolution=(3840, 2160),
        frame_rate=24,
    ),
    "streaming_1080p": OutputFormat(
        name="Streaming 1080p",
        format="streaming_1080p",
        codec="h264",
        resolution=(1920, 1080),
        frame_rate=24,
    ),
    "youtube_1080p": OutputFormat(
        name="YouTube 1080p",
        format="youtube_1080p",
        codec="h264",
        resolution=(1920, 1080),
        frame_rate=30,
    ),
    "social_square": OutputFormat(
        name="Social Square",
        format="social_square",
        codec="h264",
        resolution=(1080, 1080),
        frame_rate=30,
    ),
    "16bit_game": OutputFormat(
        name="16-bit Game",
        format="16bit_game",
        codec="png",
        resolution=(256, 224),
        frame_rate=12,
        retro_config=RetroConfig(
            enabled=True,
            palette="snes",
            dither="error_diffusion",
        ),
    ),
    "8bit_game": OutputFormat(
        name="8-bit Game",
        format="8bit_game",
        codec="png",
        resolution=(256, 240),
        frame_rate=12,
        retro_config=RetroConfig(
            enabled=True,
            palette="nes",
            dither="ordered",
        ),
    ),
}


def get_output_format_preset(name: str) -> Optional[OutputFormat]:
    """Get an output format preset by name."""
    return OUTPUT_FORMAT_PRESETS.get(name.lower())
