"""
Scene Orchestrator Types

Core data types for scene generation orchestrator.
Defines scene structure, requirements, and generation state.

Implements REQ-SO-01: Scene Outline Parser types.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List, Union
from enum import Enum
from pathlib import Path


class SceneType(Enum):
    """Scene type classification."""
    INTERIOR = "interior"
    EXTERIOR = "exterior"
    URBAN = "urban"
    PRODUCT = "product"
    PORTRAIT = "portrait"
    ENVIRONMENT = "environment"
    MIXED = "mixed"


class SceneStyle(Enum):
    """Visual style classification."""
    PHOTOREALISTIC = "photorealistic"
    STYLIZED = "stylized"
    CARTOON = "cartoon"
    LOW_POLY = "low_poly"
    RETRO = "retro"
    SCI_FI = "sci_fi"
    FANTASY = "fantasy"
    MINIMALIST = "minimalist"


class LightingMood(Enum):
    """Lighting mood presets."""
    BRIGHT = "bright"
    MOODY = "moody"
    DRAMATIC = "dramatic"
    SOFT = "soft"
    NEUTRAL = "neutral"
    WARM = "warm"
    COOL = "cool"
    HIGH_KEY = "high_key"
    LOW_KEY = "low_key"


class TimeOfDay(Enum):
    """Time of day settings."""
    DAWN = "dawn"
    MORNING = "morning"
    NOON = "noon"
    AFTERNOON = "afternoon"
    SUNSET = "sunset"
    DUSK = "dusk"
    NIGHT = "night"
    MIDNIGHT = "midnight"


class WeatherCondition(Enum):
    """Weather conditions."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    RAIN = "rain"
    SNOW = "snow"
    FOG = "fog"
    STORM = "storm"


class RequirementPriority(Enum):
    """Requirement priority levels."""
    REQUIRED = "required"
    PREFERRED = "preferred"
    OPTIONAL = "optional"


class ApprovalStatus(Enum):
    """Approval workflow status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


class UXTier(Enum):
    """User experience complexity tiers."""
    TEMPLATE = 1      # One-click, pre-built scenes
    WIZARD = 2        # Guided Q&A customization
    YAML = 3          # Full YAML configuration
    PYTHON_API = 4    # Programmatic API


@dataclass
class SceneDimensions:
    """
    Scene dimension specifications.

    Attributes:
        width: Scene width in meters
        height: Scene height (vertical extent) in meters
        depth: Scene depth in meters
        unit_scale: Unit scale factor (default 1.0 = meters)
    """
    width: float = 20.0
    height: float = 4.0
    depth: float = 20.0
    unit_scale: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "unit_scale": self.unit_scale,
        }

    @property
    def volume(self) -> float:
        """Calculate scene volume."""
        return self.width * self.height * self.depth


@dataclass
class AssetRequirement:
    """
    Asset requirement specification.

    Attributes:
        requirement_id: Unique requirement identifier
        category: Asset category (furniture, prop, character, etc.)
        subcategory: Asset subcategory
        description: Human-readable description
        quantity: Number needed
        priority: Requirement priority
        style_constraints: Style constraints for selection
        size_constraints: Size constraints (min, max)
        placement_hints: Preferred placement locations
        alternatives: Acceptable alternatives
        metadata: Additional metadata
    """
    requirement_id: str = ""
    category: str = "prop"
    subcategory: str = ""
    description: str = ""
    quantity: int = 1
    priority: str = "required"
    style_constraints: List[str] = field(default_factory=list)
    size_constraints: Optional[Tuple[float, float]] = None
    placement_hints: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requirement_id": self.requirement_id,
            "category": self.category,
            "subcategory": self.subcategory,
            "description": self.description,
            "quantity": self.quantity,
            "priority": self.priority,
            "style_constraints": self.style_constraints,
            "size_constraints": list(self.size_constraints) if self.size_constraints else None,
            "placement_hints": self.placement_hints,
            "alternatives": self.alternatives,
            "metadata": self.metadata,
        }


@dataclass
class LightingRequirement:
    """
    Lighting requirement specification.

    Attributes:
        mood: Lighting mood preset
        time_of_day: Time of day setting
        weather: Weather condition
        intensity: Light intensity multiplier
        use_studio_lights: Whether to use studio lighting
        studio_preset: Studio lighting preset name
        use_natural_light: Whether to use natural/sun light
        atmospherics: Atmospheric effects (fog, haze, etc.)
    """
    mood: str = "neutral"
    time_of_day: str = "noon"
    weather: str = "clear"
    intensity: float = 1.0
    use_studio_lights: bool = False
    studio_preset: str = "three_point"
    use_natural_light: bool = True
    atmospherics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mood": self.mood,
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "intensity": self.intensity,
            "use_studio_lights": self.use_studio_lights,
            "studio_preset": self.studio_preset,
            "use_natural_light": self.use_natural_light,
            "atmospherics": self.atmospherics,
        }


@dataclass
class CameraRequirement:
    """
    Camera requirement specification.

    Attributes:
        focal_length: Focal length in mm
        sensor_size: Sensor size (width, height)
        target_subject: Subject to focus on
        framing: Shot framing (close-up, medium, wide, etc.)
        camera_movement: Camera movement type (static, dolly, orbit, etc.)
        depth_of_field: Depth of field settings
        look_at_target: Point camera should look at
    """
    focal_length: float = 50.0
    sensor_size: Tuple[float, float] = (36.0, 24.0)
    target_subject: str = ""
    framing: str = "medium"
    camera_movement: str = "static"
    depth_of_field: Optional[Dict[str, Any]] = None
    look_at_target: Optional[Tuple[float, float, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "focal_length": self.focal_length,
            "sensor_size": list(self.sensor_size),
            "target_subject": self.target_subject,
            "framing": self.framing,
            "camera_movement": self.camera_movement,
            "depth_of_field": self.depth_of_field,
            "look_at_target": list(self.look_at_target) if self.look_at_target else None,
        }


@dataclass
class SceneOutline:
    """
    Scene outline specification.

    The primary input for scene generation containing all requirements
    and constraints.

    Attributes:
        name: Scene name
        scene_type: Type of scene
        style: Visual style
        dimensions: Scene dimensions
        description: Human-readable description
        asset_requirements: Required assets
        lighting: Lighting requirements
        camera: Camera requirements
        backdrop: Backdrop/environment settings
        custom_settings: Additional custom settings
        metadata: Additional metadata
    """
    name: str = "Untitled Scene"
    scene_type: str = "interior"
    style: str = "photorealistic"
    dimensions: Optional[SceneDimensions] = None
    description: str = ""
    asset_requirements: List[AssetRequirement] = field(default_factory=list)
    lighting: Optional[LightingRequirement] = None
    camera: Optional[CameraRequirement] = None
    backdrop: Dict[str, Any] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "scene_type": self.scene_type,
            "style": self.style,
            "dimensions": self.dimensions.to_dict() if self.dimensions else None,
            "description": self.description,
            "asset_requirements": [r.to_dict() for r in self.asset_requirements],
            "lighting": self.lighting.to_dict() if self.lighting else None,
            "camera": self.camera.to_dict() if self.camera else None,
            "backdrop": self.backdrop,
            "custom_settings": self.custom_settings,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneOutline":
        """Create from dictionary."""
        outline = cls(
            name=data.get("name", "Untitled Scene"),
            scene_type=data.get("scene_type", "interior"),
            style=data.get("style", "photorealistic"),
            description=data.get("description", ""),
            backdrop=data.get("backdrop", {}),
            custom_settings=data.get("custom_settings", {}),
            metadata=data.get("metadata", {}),
        )

        if "dimensions" in data and data["dimensions"]:
            outline.dimensions = SceneDimensions(**data["dimensions"])

        if "asset_requirements" in data:
            outline.asset_requirements = [
                AssetRequirement(**r) for r in data["asset_requirements"]
            ]

        if "lighting" in data and data["lighting"]:
            outline.lighting = LightingRequirement(**data["lighting"])

        if "camera" in data and data["camera"]:
            cam_data = data["camera"]
            if "sensor_size" in cam_data and isinstance(cam_data["sensor_size"], list):
                cam_data["sensor_size"] = tuple(cam_data["sensor_size"])
            if "look_at_target" in cam_data and isinstance(cam_data["look_at_target"], list):
                cam_data["look_at_target"] = tuple(cam_data["look_at_target"])
            outline.camera = CameraRequirement(**cam_data)

        return outline


@dataclass
class AssetSelection:
    """
    Selected asset for a requirement.

    Attributes:
        requirement_id: Source requirement ID
        asset_id: Selected asset ID
        asset_path: Path to asset file
        scale_factor: Scale factor to apply
        position: Position in scene
        rotation: Rotation in degrees
        priority_score: Selection priority score
        alternatives_considered: Other assets considered
    """
    requirement_id: str = ""
    asset_id: str = ""
    asset_path: str = ""
    scale_factor: float = 1.0
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    priority_score: float = 0.0
    alternatives_considered: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requirement_id": self.requirement_id,
            "asset_id": self.asset_id,
            "asset_path": self.asset_path,
            "scale_factor": self.scale_factor,
            "position": list(self.position),
            "rotation": list(self.rotation),
            "priority_score": self.priority_score,
            "alternatives_considered": self.alternatives_considered,
        }


@dataclass
class GenerationCheckpoint:
    """
    Checkpoint for generation progress.

    Attributes:
        stage: Current generation stage
        timestamp: Checkpoint timestamp
        data: Checkpoint data
        message: Status message
    """
    stage: str = "initialized"
    timestamp: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage": self.stage,
            "timestamp": self.timestamp,
            "data": self.data,
            "message": self.message,
        }


@dataclass
class GenerationResult:
    """
    Result of scene generation.

    Attributes:
        success: Whether generation succeeded
        scene_outline: Source scene outline
        asset_selections: Selected assets
        checkpoint: Final checkpoint
        blend_path: Path to generated blend file
        render_path: Path to render output
        validation_errors: Validation errors encountered
        warnings: Warnings generated
        generation_time: Time taken to generate
    """
    success: bool = False
    scene_outline: Optional[SceneOutline] = None
    asset_selections: List[AssetSelection] = field(default_factory=list)
    checkpoint: Optional[GenerationCheckpoint] = None
    blend_path: str = ""
    render_path: str = ""
    validation_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    generation_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "scene_outline": self.scene_outline.to_dict() if self.scene_outline else None,
            "asset_selections": [s.to_dict() for s in self.asset_selections],
            "checkpoint": self.checkpoint.to_dict() if self.checkpoint else None,
            "blend_path": self.blend_path,
            "render_path": self.render_path,
            "validation_errors": self.validation_errors,
            "warnings": self.warnings,
            "generation_time": self.generation_time,
        }


@dataclass
class SceneTemplate:
    """
    Pre-defined scene template.

    Templates provide one-click scene generation with sensible defaults.

    Attributes:
        template_id: Unique template identifier
        name: Template name
        description: Template description
        category: Template category
        scene_type: Type of scene generated
        outline_template: Partial scene outline
        preview_image: Path to preview image
        tags: Search tags
    """
    template_id: str = ""
    name: str = ""
    description: str = ""
    category: str = "general"
    scene_type: str = "interior"
    outline_template: Dict[str, Any] = field(default_factory=dict)
    preview_image: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "scene_type": self.scene_type,
            "outline_template": self.outline_template,
            "preview_image": self.preview_image,
            "tags": self.tags,
        }

    def create_outline(self, **overrides) -> SceneOutline:
        """Create scene outline from template with optional overrides."""
        data = self.outline_template.copy()
        data.update(overrides)
        return SceneOutline.from_dict(data)


# =============================================================================
# TEMPLATE LIBRARY
# =============================================================================

SCENE_TEMPLATES: Dict[str, SceneTemplate] = {
    "portrait_studio": SceneTemplate(
        template_id="portrait_studio",
        name="Portrait Studio",
        description="Professional portrait lighting setup with backdrop",
        category="studio",
        scene_type="portrait",
        outline_template={
            "name": "Portrait Studio",
            "scene_type": "portrait",
            "style": "photorealistic",
            "dimensions": {"width": 8.0, "height": 4.0, "depth": 8.0},
            "lighting": {
                "mood": "neutral",
                "use_studio_lights": True,
                "studio_preset": "rembrandt",
            },
            "camera": {
                "focal_length": 85.0,
                "framing": "close-up",
            },
        },
        tags=["portrait", "studio", "people", "headshot"],
    ),

    "product_hero": SceneTemplate(
        template_id="product_hero",
        name="Product Hero Shot",
        description="Product photography with dramatic lighting",
        category="studio",
        scene_type="product",
        outline_template={
            "name": "Product Hero",
            "scene_type": "product",
            "style": "photorealistic",
            "dimensions": {"width": 5.0, "height": 3.0, "depth": 5.0},
            "lighting": {
                "mood": "dramatic",
                "use_studio_lights": True,
                "studio_preset": "hero",
            },
            "camera": {
                "focal_length": 50.0,
                "framing": "medium",
            },
        },
        tags=["product", "commercial", "advertising"],
    ),

    "interior_living": SceneTemplate(
        template_id="interior_living",
        name="Living Room Interior",
        description="Modern living room with natural lighting",
        category="interior",
        scene_type="interior",
        outline_template={
            "name": "Living Room",
            "scene_type": "interior",
            "style": "photorealistic",
            "dimensions": {"width": 8.0, "height": 3.0, "depth": 6.0},
            "asset_requirements": [
                {"category": "furniture", "subcategory": "sofa", "quantity": 1},
                {"category": "furniture", "subcategory": "coffee_table", "quantity": 1},
                {"category": "furniture", "subcategory": "chair", "quantity": 2},
            ],
            "lighting": {
                "mood": "bright",
                "time_of_day": "afternoon",
                "use_natural_light": True,
            },
        },
        tags=["interior", "living_room", "modern", "residential"],
    ),

    "urban_street": SceneTemplate(
        template_id="urban_street",
        name="Urban Street Scene",
        description="City street with vehicles and pedestrians",
        category="urban",
        scene_type="urban",
        outline_template={
            "name": "Urban Street",
            "scene_type": "urban",
            "style": "photorealistic",
            "dimensions": {"width": 100.0, "height": 30.0, "depth": 100.0},
            "lighting": {
                "time_of_day": "afternoon",
                "use_natural_light": True,
            },
            "camera": {
                "focal_length": 35.0,
                "framing": "wide",
            },
        },
        tags=["urban", "street", "city", "exterior"],
    ),

    "scifi_environment": SceneTemplate(
        template_id="scifi_environment",
        name="Sci-Fi Environment",
        description="Futuristic sci-fi environment",
        category="environment",
        scene_type="environment",
        outline_template={
            "name": "Sci-Fi Environment",
            "scene_type": "environment",
            "style": "sci_fi",
            "dimensions": {"width": 200.0, "height": 50.0, "depth": 200.0},
            "lighting": {
                "mood": "dramatic",
                "use_natural_light": False,
            },
        },
        tags=["sci-fi", "futuristic", "environment", "space"],
    ),
}


def list_templates() -> List[str]:
    """Get list of available template IDs."""
    return list(SCENE_TEMPLATES.keys())


def get_template(template_id: str) -> Optional[SceneTemplate]:
    """Get template by ID."""
    return SCENE_TEMPLATES.get(template_id)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "SceneType",
    "SceneStyle",
    "LightingMood",
    "TimeOfDay",
    "WeatherCondition",
    "RequirementPriority",
    "ApprovalStatus",
    "UXTier",
    "SceneDimensions",
    "AssetRequirement",
    "LightingRequirement",
    "CameraRequirement",
    "SceneOutline",
    "AssetSelection",
    "GenerationCheckpoint",
    "GenerationResult",
    "SceneTemplate",
    "SCENE_TEMPLATES",
    "list_templates",
    "get_template",
]
