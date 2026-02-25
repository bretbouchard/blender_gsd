"""
Vehicle Stunts Types

Data structures for vehicle stunt system.

Phase 17.0: Stunt Foundation (REQ-STUNT-01)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum, auto


class RampType(Enum):
    """Types of stunt ramps."""
    KICKER = auto()       # Standard launch ramp
    TABLE = auto()        # Flat top table jump
    HIP = auto()          # Two-sided landing
    QUARTER_PIPE = auto() # Vertical quarter pipe
    SPINE = auto()        # Two quarter pipes back to back
    ROLLER = auto()       # Rolling hill
    STEP_UP = auto()      # Jump up to higher level
    STEP_DOWN = auto()    # Jump down to lower level
    WALL_RIDE = auto()    # Banked wall
    KICKER_KINK = auto()  # Multi-angle kicker


class LoopType(Enum):
    """Types of loop structures."""
    CIRCULAR = auto()       # Classic circular loop
    CLOTHOID = auto()       # Teardrop loop with smooth entry/exit
    EGG = auto()            # Egg-shaped (taller than wide)
    HELIX = auto()          # Spiral loop


@dataclass
class RampConfig:
    """Configuration for a stunt ramp."""
    ramp_type: Optional[RampType] = None
    width: float = 4.0             # meters
    height: float = 2.0            # meters
    length: float = 6.0            # meters
    angle: float = 30.0            # degrees
    curve_radius: Optional[float] = None  # meters, None = linear
    transition_radius: float = 2.0  # meters, for curved entry/exit

    # Table-specific
    table_length: float = 3.0      # meters, for TABLE type

    # Hip-specific
    hip_angle: float = 45.0        # degrees, landing direction offset

    # Surface
    surface_material: str = "concrete"
    friction: float = 0.8

    # Position
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: float = 0.0          # degrees around Z axis

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'ramp_type': self.ramp_type.name if self.ramp_type else None,
            'width': self.width,
            'height': self.height,
            'length': self.length,
            'angle': self.angle,
            'curve_radius': self.curve_radius,
            'transition_radius': self.transition_radius,
            'table_length': self.table_length,
            'hip_angle': self.hip_angle,
            'surface_material': self.surface_material,
            'friction': self.friction,
            'location': self.location,
            'rotation': self.rotation,
        }


@dataclass
class TrajectoryPoint:
    """A point along a vehicle trajectory."""
    frame: int
    position: Tuple[float, float, float]
    velocity: Tuple[float, float, float]
    rotation: Tuple[float, float, float]  # euler angles
    angular_velocity: Tuple[float, float, float]
    phase: str = "flight"  # approach, launch, flight, landing, recovery


@dataclass
class LandingZone:
    """Landing zone configuration and detection."""
    center: Tuple[float, float, float]
    width: float
    length: float
    slope_angle: float = 0.0  # degrees, positive = downhill
    surface_type: str = "ground"
    is_clear: bool = True
    obstacles: List[Tuple[float, float, float]] = field(default_factory=list)

    def contains_point(self, point: Tuple[float, float, float]) -> bool:
        """Check if a point is within the landing zone."""
        px, py, pz = point
        cx, cy, cz = self.center

        # Check X-Y bounds (simplified)
        if abs(px - cx) > self.width / 2:
            return False
        if abs(py - cy) > self.length / 2:
            return False

        return True


# Phase 17.2 Building Interaction Types

@dataclass
class KickerConfig:
    """Standard kicker/launch ramp."""
    height: float = 1.5           # meters
    length: float = 4.0           # meters
    angle: float = 25.0           # degrees
    width: float = 4.0            # meters
    curve_type: str = "linear"    # linear, curved, kinked
    kink_angle: Optional[float] = None  # for kinked type


@dataclass
class TableConfig:
    """Table-top jump with flat section."""
    height: float = 2.0
    length: float = 8.0           # total length
    table_length: float = 3.0     # flat top length
    up_length: float = 2.5        # approach ramp
    down_length: float = 2.5      # landing ramp
    width: float = 4.0
    angle: float = 30.0


@dataclass
class HipConfig:
    """Hip jump with angled landing."""
    height: float = 2.0
    length: float = 6.0
    width: float = 4.0
    angle: float = 30.0
    landing_angle: float = 45.0   # direction offset for landing


@dataclass
class QuarterPipeConfig:
    """Quarter pipe for vertical transitions."""
    height: float = 3.0
    width: float = 4.0
    radius: float = 2.0
    deck_length: float = 1.0      # top deck


@dataclass
class SpineConfig:
    """Spine ramp (two quarter pipes back-to-back)."""
    height: float = 2.5
    width: float = 4.0
    radius: float = 2.0
    deck_width: float = 0.5


@dataclass
class RollerConfig:
    """Rolling hill / whoop section."""
    height: float = 0.8
    length: float = 3.0
    width: float = 4.0
    count: int = 5                # number of rollers
    spacing: float = 2.0


@dataclass
class StepUpConfig:
    """Step-up jump to higher level."""
    height: float = 2.0
    length: float = 5.0
    width: float = 4.0
    angle: float = 35.0
    landing_height: float = 2.0   # height of landing platform


@dataclass
class StepDownConfig:
    """Step-down jump to lower level."""
    height: float = 1.5
    length: float = 5.0
    width: float = 4.0
    angle: float = 25.0
    drop_height: float = 2.0      # height drop to landing


# Phase 17.3 Loop & Curve Types

@dataclass
class LoopConfig:
    """Loop-the-loop configuration."""
    loop_type: LoopType = LoopType.CIRCULAR
    radius: float = 5.0           # meters
    width: float = 4.0            # meters
    entry_angle: float = 0.0      # degrees, approach angle
    entry_length: float = 10.0    # meters, approach run
    exit_length: float = 10.0     # meters, run-out

    # For clothoid
    clothoid_param: float = 0.5

    # For egg shape
    height_ratio: float = 1.2     # height/width ratio

    def get_min_speed(self) -> float:
        """Calculate minimum entry speed for loop.

        v = sqrt(g * r * (2 + cos(theta)))
        At top: theta = 0, so v = sqrt(g * r * 3) for safety
        """
        import math
        g = 9.81
        # Minimum speed at top to maintain contact
        v_top = math.sqrt(g * self.radius * 1.5)  # 1.5g at top
        # Entry speed needed (energy conservation)
        # 0.5 * m * v_entry^2 = 0.5 * m * v_top^2 + m * g * 2r
        v_entry = math.sqrt(v_top**2 + 2 * g * 2 * self.radius)
        return v_entry


@dataclass
class BankedTurnConfig:
    """Banked turn configuration."""
    radius: float = 15.0          # turn radius
    angle: float = 45.0           # banking angle
    width: float = 6.0            # track width
    arc_degrees: float = 90.0     # degrees of arc
    entry_length: float = 5.0
    exit_length: float = 5.0

    def get_design_speed(self) -> float:
        """Calculate design speed for banked turn.

        v = sqrt(r * g * tan(theta))
        """
        import math
        g = 9.81
        return math.sqrt(self.radius * g * math.tan(math.radians(self.angle)))


@dataclass
class HalfPipeConfig:
    """Half-pipe configuration."""
    width: float = 8.0            # flat bottom width
    height: float = 3.0           # wall height
    radius: float = 2.5           # transition radius
    length: float = 20.0          # total length
    deck_width: float = 1.0       # platform at top


@dataclass
class WaveConfig:
    """Wave/rolling section configuration."""
    amplitude: float = 1.5        # wave height
    wavelength: float = 8.0       # distance peak to peak
    width: float = 6.0
    count: int = 3                # number of waves
    phase: float = 0.0            # starting phase


@dataclass
class BarrelRollConfig:
    """Barrel roll section configuration."""
    length: float = 12.0          # length of roll section
    rotations: float = 1.0        # number of full rotations
    width: float = 4.0
    radius: float = 2.0           # rotation radius


# Phase 17.4 Physics Types

@dataclass
class LaunchParams:
    """Launch parameters for stunt calculation."""
    speed: float                  # m/s
    angle: float                  # degrees
    height: float = 0.0           # launch height offset
    rotation_rate: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # deg/s per axis


@dataclass
class TrajectoryResult:
    """Result of trajectory calculation."""
    launch_params: LaunchParams
    points: List[TrajectoryPoint]
    peak_height: float
    horizontal_distance: float
    air_time: float               # seconds
    landing_velocity: Tuple[float, float, float]
    max_g_force: float
    is_safe: bool
    warnings: List[str] = field(default_factory=list)


@dataclass
class SpeedCalculator:
    """Speed calculation utilities."""
    target_distance: float
    target_height: float = 0.0
    ramp_angle: float = 30.0
    friction_coefficient: float = 0.02
    air_density: float = 1.225    # kg/m³

    def calculate_required_speed(self) -> float:
        """Calculate required launch speed."""
        import math
        g = 9.81
        angle_rad = math.radians(self.ramp_angle)

        # Basic projectile motion
        # d = v² * sin(2θ) / g
        v_required = math.sqrt(
            self.target_distance * g / math.sin(2 * angle_rad)
        )

        return v_required


# Phase 17.5 Course Types

@dataclass
class StuntElement:
    """A single element in a stunt course."""
    element_id: str
    element_type: str             # ramp, loop, turn, etc.
    config: Dict[str, Any]
    position: Tuple[float, float, float]
    rotation: float               # degrees around Z
    entry_speed: float            # required entry speed m/s
    exit_speed: float             # expected exit speed m/s
    duration_frames: int          # frames to traverse

    # Connections
    prev_element: Optional[str] = None
    next_element: Optional[str] = None


@dataclass
class StuntCourseConfig:
    """Complete stunt course configuration."""
    course_id: str
    name: str
    elements: List[StuntElement]
    total_length: float           # meters
    total_duration: float         # seconds at 24fps
    difficulty: str = "medium"    # easy, medium, hard, extreme
    min_speed: float = 15.0       # m/s minimum entry speed
    max_speed: float = 40.0       # m/s maximum safe speed

    def get_element_by_id(self, element_id: str) -> Optional[StuntElement]:
        """Get element by ID."""
        for elem in self.elements:
            if elem.element_id == element_id:
                return elem
        return None

    def get_course_flow(self) -> List[Tuple[str, float]]:
        """Get course flow as list of (element_id, entry_speed)."""
        return [(e.element_id, e.entry_speed) for e in self.elements]


class CourseFlowAnalyzer:
    """Analyzes stunt course flow and safety."""

    def __init__(self, course: StuntCourseConfig):
        self.course = course
        self.warnings: List[str] = []
        self.speed_profile: List[Tuple[str, float, float]] = []

    def analyze(self) -> bool:
        """Analyze course for flow issues.

        Returns:
            True if course is safe, False if issues found
        """
        self.warnings = []
        self.speed_profile = []

        prev_element = None
        for element in self.course.elements:
            # Check speed continuity
            if prev_element is not None:
                speed_diff = element.entry_speed - prev_element.exit_speed
                if speed_diff > 5.0:  # Need to gain 5+ m/s
                    self.warnings.append(
                        f"Speed gap between {prev_element.element_id} and "
                        f"{element.element_id}: need +{speed_diff:.1f} m/s"
                    )
                elif speed_diff < -10.0:  # Losing too much speed
                    self.warnings.append(
                        f"Speed loss between {prev_element.element_id} and "
                        f"{element.element_id}: -{abs(speed_diff):.1f} m/s"
                    )

            # Check min/max speed
            if element.entry_speed < self.course.min_speed:
                self.warnings.append(
                    f"{element.element_id}: entry speed {element.entry_speed:.1f} "
                    f"below minimum {self.course.min_speed}"
                )
            if element.entry_speed > self.course.max_speed:
                self.warnings.append(
                    f"{element.element_id}: entry speed {element.entry_speed:.1f} "
                    f"above maximum {self.course.max_speed}"
                )

            self.speed_profile.append(
                (element.element_id, element.entry_speed, element.exit_speed)
            )
            prev_element = element

        return len([w for w in self.warnings if "gap" in w.lower()]) == 0

    def get_speed_graph(self) -> Dict[str, Any]:
        """Get speed profile as graph data."""
        return {
            'labels': [p[0] for p in self.speed_profile],
            'entry_speeds': [p[1] for p in self.speed_profile],
            'exit_speeds': [p[2] for p in self.speed_profile],
        }
