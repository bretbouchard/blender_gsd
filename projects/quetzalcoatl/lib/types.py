"""
Quetzalcoatl Types - Configuration Dataclasses

Type definitions for the procedural feathered serpent generator.
"""

from dataclasses import dataclass, field
from typing import Tuple, List, Optional, Dict, Any
from enum import Enum


class WingType(Enum):
    """Wing type selection."""
    NONE = "none"
    FEATHERED = "feathered"
    MEMBRANE = "membrane"


class ScaleShape(Enum):
    """Scale shape variants."""
    ROUND = "round"
    OVAL = "oval"
    HEXAGONAL = "hexagonal"
    DIAMOND = "diamond"


class TailType(Enum):
    """Tail ending variants."""
    POINTED = "pointed"
    FEATHER_TUFT = "feather_tuft"
    RATTLE = "rattle"
    FAN = "fan"


class CrestType(Enum):
    """Head crest/horn variants."""
    NONE = "none"
    RIDGE = "ridge"
    FRILL = "frill"
    HORNS = "horns"


class ColorPattern(Enum):
    """Color pattern types."""
    SOLID = "solid"
    GRADIENT = "gradient"
    SPOTTED = "spotted"
    STRIPED = "striped"


@dataclass
class SpineConfig:
    """Spine curve configuration."""
    length: float = 10.0  # 1-100 meters
    segments: int = 64
    taper_head: float = 0.3
    taper_tail: float = 0.2
    wave_amplitude: float = 0.5
    wave_frequency: int = 3

    def __post_init__(self):
        """Validate after initialization."""
        self.segments = max(4, self.segments)
        self.wave_frequency = max(1, self.wave_frequency)


@dataclass
class BodyConfig:
    """Body volume configuration."""
    radius: float = 0.5  # 0.1-5 meters
    compression: float = 0.8  # lateral/vertical ratio
    dorsal_flat: float = 0.0  # 0=circular, 1=flat

    def __post_init__(self):
        """Validate after initialization."""
        self.compression = max(0.1, min(2.0, self.compression))
        self.dorsal_flat = max(0.0, min(1.0, self.dorsal_flat))


@dataclass
class LimbConfig:
    """Limb configuration."""
    leg_pairs: int = 2  # 0-4
    leg_positions: List[float] = field(default_factory=lambda: [0.3, 0.6])
    leg_length: float = 1.0
    leg_girth: float = 0.15
    toe_count: int = 4
    claw_length: float = 0.1

    def __post_init__(self):
        """Validate after initialization."""
        self.leg_pairs = max(0, min(4, self.leg_pairs))
        self.toe_count = max(2, min(5, self.toe_count))


@dataclass
class WingConfig:
    """Wing configuration."""
    wing_type: WingType = WingType.NONE
    wing_span: float = 3.0
    wing_arm_length: float = 1.5
    finger_count: int = 4  # for membrane wings
    feather_layers: int = 3  # for feathered wings

    def __post_init__(self):
        """Validate after initialization."""
        self.finger_count = max(2, min(5, self.finger_count))
        self.feather_layers = max(1, min(5, self.feather_layers))


@dataclass
class ScaleConfig:
    """Scale layer configuration."""
    size: float = 0.05
    shape: ScaleShape = ScaleShape.OVAL
    overlap: float = 0.3
    density: float = 1.0
    variation: float = 0.2

    def __post_init__(self):
        """Validate after initialization."""
        self.overlap = max(0.0, min(0.8, self.overlap))
        self.density = max(0.1, min(3.0, self.density))


@dataclass
class FeatherConfig:
    """Feather layer configuration."""
    length: float = 0.3
    width: float = 0.02
    barb_density: int = 20
    iridescence: float = 0.5
    layer_count: int = 3

    def __post_init__(self):
        """Validate after initialization."""
        self.barb_density = max(5, min(50, self.barb_density))
        self.iridescence = max(0.0, min(1.0, self.iridescence))


@dataclass
class HeadConfig:
    """Head configuration."""
    snout_length: float = 0.8
    snout_profile: float = 0.5
    jaw_depth: float = 0.3
    crest_type: CrestType = CrestType.NONE
    crest_size: float = 0.5

    def __post_init__(self):
        """Validate after initialization."""
        self.snout_profile = max(0.0, min(1.0, self.snout_profile))


@dataclass
class TeethConfig:
    """Teeth configuration."""
    count: int = 40
    curve: float = 0.3
    size_variation: float = 0.3

    def __post_init__(self):
        """Validate after initialization."""
        self.count = max(0, min(200, self.count))


@dataclass
class WhiskerConfig:
    """Whisker configuration."""
    count: int = 6
    length: float = 0.5
    taper: float = 0.1
    curve: float = 0.2

    def __post_init__(self):
        """Validate after initialization."""
        self.count = max(0, min(20, self.count))


@dataclass
class TailConfig:
    """Tail ending configuration."""
    tail_type: TailType = TailType.POINTED
    ornament_size: float = 0.5
    feather_count: int = 12  # for tuft type

    def __post_init__(self):
        """Validate after initialization."""
        self.feather_count = max(1, min(30, self.feather_count))


@dataclass
class ColorConfig:
    """Color system configuration."""
    base_color: Tuple[float, float, float] = (0.1, 0.3, 0.2)
    accent_color: Tuple[float, float, float] = (0.8, 0.6, 0.2)
    iridescent_colors: List[Tuple[float, float, float]] = field(
        default_factory=lambda: [(0.0, 0.8, 0.6), (0.8, 0.2, 0.8), (0.2, 0.4, 0.9)]
    )
    color_pattern: ColorPattern = ColorPattern.SOLID
    color_group_count: int = 3
    translucency: float = 0.3

    def __post_init__(self):
        """Validate after initialization."""
        self.translucency = max(0.0, min(1.0, self.translucency))
        self.color_group_count = max(1, min(10, self.color_group_count))


@dataclass
class AnimationConfig:
    """Animation configuration."""
    wave_speed: float = 1.0
    wave_amplitude: float = 0.5
    wave_decay: float = 0.3
    secondary_wave: bool = True
    feather_sway: float = 0.2

    def __post_init__(self):
        """Validate after initialization."""
        self.wave_speed = max(0.0, self.wave_speed)
        self.wave_decay = max(0.0, min(1.0, self.wave_decay))


@dataclass
class QuetzalcoatlConfig:
    """Complete creature configuration."""
    name: str = "Quetzalcoatl"
    description: str = ""
    seed: int = 42

    spine: SpineConfig = field(default_factory=SpineConfig)
    body: BodyConfig = field(default_factory=BodyConfig)
    limbs: LimbConfig = field(default_factory=LimbConfig)
    wings: WingConfig = field(default_factory=WingConfig)
    scales: ScaleConfig = field(default_factory=ScaleConfig)
    feathers: FeatherConfig = field(default_factory=FeatherConfig)
    head: HeadConfig = field(default_factory=HeadConfig)
    teeth: TeethConfig = field(default_factory=TeethConfig)
    whiskers: WhiskerConfig = field(default_factory=WhiskerConfig)
    tail: TailConfig = field(default_factory=TailConfig)
    colors: ColorConfig = field(default_factory=ColorConfig)
    animation: AnimationConfig = field(default_factory=AnimationConfig)

    def validate(self) -> List[str]:
        """Validate configuration, return list of errors."""
        errors = []

        # Spine validation
        if not 1.0 <= self.spine.length <= 100.0:
            errors.append(f"spine.length must be 1-100, got {self.spine.length}")

        # Limb validation
        if not 0 <= self.limbs.leg_pairs <= 4:
            errors.append(f"limbs.leg_pairs must be 0-4, got {self.limbs.leg_pairs}")

        if len(self.limbs.leg_positions) < self.limbs.leg_pairs:
            errors.append(
                f"Need {self.limbs.leg_pairs} leg_positions, "
                f"got {len(self.limbs.leg_positions)}"
            )

        # Body validation
        if not 0.1 <= self.body.radius <= 5.0:
            errors.append(f"body.radius must be 0.1-5.0, got {self.body.radius}")

        # Wing validation
        if self.wings.wing_type != WingType.NONE:
            if self.wings.wing_span <= 0:
                errors.append(f"wings.wing_span must be > 0, got {self.wings.wing_span}")

        # Scale validation
        if not 0.01 <= self.scales.size <= 0.5:
            errors.append(f"scales.size must be 0.01-0.5, got {self.scales.size}")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        def enum_to_value(obj):
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, tuple):
                return list(obj)
            return obj

        result = {
            "name": self.name,
            "description": self.description,
            "seed": self.seed,
        }

        for section_name in [
            "spine", "body", "limbs", "wings", "scales", "feathers",
            "head", "teeth", "whiskers", "tail", "colors", "animation"
        ]:
            section = getattr(self, section_name)
            result[section_name] = {}
            for field_name in section.__dataclass_fields__:
                value = getattr(section, field_name)
                result[section_name][field_name] = enum_to_value(value)

        return result
