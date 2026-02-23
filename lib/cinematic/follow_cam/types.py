"""
Follow Camera Types and Configurations

Defines dataclasses for follow camera modes, targeting, obstacle detection,
and camera configuration for dynamic subject tracking.

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-51
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum


class FollowMode(Enum):
    """
    Camera follow modes for different gameplay scenarios.

    Each mode defines how the camera follows and frames the subject:
    - side_scroller: Locked plane for 2.5D platformer view
    - over_shoulder: Third-person behind subject with offset
    - chase: Chase from behind with speed-based distance
    - chase_side: Chase from the side (racing games)
    - orbit_follow: Orbit around subject while following
    - lead: Camera ahead of subject (action preview)
    - aerial: Top-down bird's eye view
    - free_roam: Free camera with collision detection
    """
    SIDE_SCROLLER = "side_scroller"
    OVER_SHOULDER = "over_shoulder"
    CHASE = "chase"
    CHASE_SIDE = "chase_side"
    ORBIT_FOLLOW = "orbit_follow"
    LEAD = "lead"
    AERIAL = "aerial"
    FREE_ROAM = "free_roam"


class LockedPlane(Enum):
    """
    Locked plane configuration for side-scroller mode.

    Defines which plane the camera is constrained to:
    - XY: Z-axis locked (top-down platformer)
    - XZ: Y-axis locked (side-scrolling platformer)
    - YZ: X-axis locked (front-facing platformer)
    """
    XY = "xy"  # Z locked - top-down platformer
    XZ = "xz"  # Y locked - side-scrolling
    YZ = "yz"  # X locked - front-facing


class ObstacleResponse(Enum):
    """
    Response strategies when obstacles are detected.

    Different responses for different obstacle types:
    - push_forward: Move camera closer to subject
    - orbit_away: Rotate camera around obstacle
    - raise_up: Move camera higher to clear obstacle
    - zoom_through: Pass through transparent objects
    - back_away: Move camera back (wall behind)
    """
    PUSH_FORWARD = "push_forward"
    ORBIT_AWAY = "orbit_away"
    RAISE_UP = "raise_up"
    ZOOM_THROUGH = "zoom_through"
    BACK_AWAY = "back_away"


class TransitionType(Enum):
    """
    Transition types between camera modes.

    - cut: Instant transition (no interpolation)
    - blend: Smooth blend between positions
    - orbit: Orbit transition around subject
    - dolly: Physical dolly-like movement
    """
    CUT = "cut"
    BLEND = "blend"
    ORBIT = "orbit"
    DOLLY = "dolly"


@dataclass
class FollowTarget:
    """
    Target specification for follow camera.

    Defines what the camera follows and how to track it.

    Attributes:
        object_name: Name of the target object in Blender
        bone_name: Optional bone name for armature targets
        offset: Offset from target center/pivot point
        look_ahead_distance: Distance ahead of target to look
        velocity_smoothing: Smoothing factor for velocity tracking (0-1)
        prediction_frames: Number of frames to predict ahead
        use_animation_prediction: Read animation keyframes for prediction
    """
    object_name: str = ""
    bone_name: str = ""
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    look_ahead_distance: float = 1.0
    velocity_smoothing: float = 0.5
    prediction_frames: int = 10
    use_animation_prediction: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "object_name": self.object_name,
            "bone_name": self.bone_name,
            "offset": list(self.offset),
            "look_ahead_distance": self.look_ahead_distance,
            "velocity_smoothing": self.velocity_smoothing,
            "prediction_frames": self.prediction_frames,
            "use_animation_prediction": self.use_animation_prediction,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FollowTarget:
        """Create from dictionary."""
        return cls(
            object_name=data.get("object_name", ""),
            bone_name=data.get("bone_name", ""),
            offset=tuple(data.get("offset", (0.0, 0.0, 0.0))),
            look_ahead_distance=data.get("look_ahead_distance", 1.0),
            velocity_smoothing=data.get("velocity_smoothing", 0.5),
            prediction_frames=data.get("prediction_frames", 10),
            use_animation_prediction=data.get("use_animation_prediction", False),
        )


@dataclass
class ObstacleInfo:
    """
    Information about a detected obstacle.

    Used by collision detection to describe obstacles and
    determine appropriate response strategies.

    Attributes:
        object_name: Name of the obstacle object
        position: Hit position in world space
        normal: Surface normal at hit point
        distance: Distance from camera to obstacle
        is_transparent: Whether the obstacle is see-through
        is_trigger: Whether this is a trigger volume (no collision)
        response: Recommended response strategy
    """
    object_name: str = ""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    normal: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    distance: float = 0.0
    is_transparent: bool = False
    is_trigger: bool = False
    response: ObstacleResponse = ObstacleResponse.PUSH_FORWARD

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "object_name": self.object_name,
            "position": list(self.position),
            "normal": list(self.normal),
            "distance": self.distance,
            "is_transparent": self.is_transparent,
            "is_trigger": self.is_trigger,
            "response": self.response.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ObstacleInfo:
        """Create from dictionary."""
        return cls(
            object_name=data.get("object_name", ""),
            position=tuple(data.get("position", (0.0, 0.0, 0.0))),
            normal=tuple(data.get("normal", (0.0, 0.0, 1.0))),
            distance=data.get("distance", 0.0),
            is_transparent=data.get("is_transparent", False),
            is_trigger=data.get("is_trigger", False),
            response=ObstacleResponse(data.get("response", "push_forward")),
        )


@dataclass
class OperatorBehavior:
    """
    Configuration for human-like camera operator behavior.

    Simulates skilled camera operator tendencies including:
    - Reaction delay (human response time)
    - Angle preferences (preferred shooting angles)
    - Natural breathing (subtle movement)
    - Decision weights (priority ranking)

    Part of Phase 8.2 - Obstacle Avoidance
    Beads: blender_gsd-57

    Attributes:
        reaction_delay: Human response time in seconds
        avoid_jerky_motion: Prevent sudden camera movements
        min_movement_time: Minimum duration for any adjustment
        horizontal_angle_range: Preferred horizontal shooting angles (degrees)
        vertical_angle_range: Preferred vertical shooting angles (degrees)
        breathing_enabled: Enable subtle breathing movement
        breathing_amplitude: Breathing movement amplitude in meters
        breathing_frequency: Breathing frequency in Hz
        weight_visibility: Priority weight for visibility
        weight_composition: Priority weight for composition
        weight_smoothness: Priority weight for smoothness
        weight_distance: Priority weight for distance maintenance
        oscillation_threshold: Minimum distance change before response
        position_history_size: Number of positions to track for oscillation
        max_direction_changes: Max direction changes per second before damping
    """

    # Human response simulation
    reaction_delay: float = 0.1  # Seconds - human reaction time
    avoid_jerky_motion: bool = True
    min_movement_time: float = 0.3  # Seconds for any adjustment

    # Angle preferences (degrees)
    horizontal_angle_range: Tuple[float, float] = (-45.0, 45.0)
    vertical_angle_range: Tuple[float, float] = (10.0, 30.0)

    # Natural breathing
    breathing_enabled: bool = True
    breathing_amplitude: float = 0.01  # Meters
    breathing_frequency: float = 0.25  # Hz (breaths per second)

    # Decision weights (must sum to roughly 2.5 for normalization)
    weight_visibility: float = 1.0
    weight_composition: float = 0.7
    weight_smoothness: float = 0.5
    weight_distance: float = 0.3

    # Anti-oscillation
    oscillation_threshold: float = 0.1  # Min distance before response
    position_history_size: int = 10
    max_direction_changes: int = 3  # Per second before damping

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "reaction_delay": self.reaction_delay,
            "avoid_jerky_motion": self.avoid_jerky_motion,
            "min_movement_time": self.min_movement_time,
            "horizontal_angle_range": list(self.horizontal_angle_range),
            "vertical_angle_range": list(self.vertical_angle_range),
            "breathing_enabled": self.breathing_enabled,
            "breathing_amplitude": self.breathing_amplitude,
            "breathing_frequency": self.breathing_frequency,
            "weight_visibility": self.weight_visibility,
            "weight_composition": self.weight_composition,
            "weight_smoothness": self.weight_smoothness,
            "weight_distance": self.weight_distance,
            "oscillation_threshold": self.oscillation_threshold,
            "position_history_size": self.position_history_size,
            "max_direction_changes": self.max_direction_changes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperatorBehavior":
        """Create from dictionary."""
        return cls(
            reaction_delay=data.get("reaction_delay", 0.1),
            avoid_jerky_motion=data.get("avoid_jerky_motion", True),
            min_movement_time=data.get("min_movement_time", 0.3),
            horizontal_angle_range=tuple(data.get("horizontal_angle_range", (-45.0, 45.0))),
            vertical_angle_range=tuple(data.get("vertical_angle_range", (10.0, 30.0))),
            breathing_enabled=data.get("breathing_enabled", True),
            breathing_amplitude=data.get("breathing_amplitude", 0.01),
            breathing_frequency=data.get("breathing_frequency", 0.25),
            weight_visibility=data.get("weight_visibility", 1.0),
            weight_composition=data.get("weight_composition", 0.7),
            weight_smoothness=data.get("weight_smoothness", 0.5),
            weight_distance=data.get("weight_distance", 0.3),
            oscillation_threshold=data.get("oscillation_threshold", 0.1),
            position_history_size=data.get("position_history_size", 10),
            max_direction_changes=data.get("max_direction_changes", 3),
        )


@dataclass
class FollowCameraConfig:
    """
    Complete configuration for follow camera system.

    Defines all parameters for camera following behavior,
    collision detection, and obstacle response.

    Attributes:
        name: Configuration name/preset
        follow_mode: Active follow mode
        target: Target specification

        # Distance settings
        min_distance: Minimum distance from target
        max_distance: Maximum distance from target
        ideal_distance: Preferred distance from target
        distance_smoothing: Smoothing factor for distance changes

        # Height settings
        min_height: Minimum height above target
        max_height: Maximum height above target
        ideal_height: Preferred height above target
        height_smoothing: Smoothing factor for height changes

        # Rotation settings
        yaw_smoothing: Smoothing for horizontal rotation
        pitch_smoothing: Smoothing for vertical rotation
        roll_enabled: Whether camera can roll

        # Offset settings (mode-specific)
        shoulder_offset: Horizontal offset for over-shoulder (negative = left)
        lead_distance: Distance ahead for lead mode
        orbit_speed: Rotation speed for orbit_follow mode

        # Side-scroller settings
        locked_plane: Which plane is locked
        locked_axis_value: Value for locked axis

        # Chase settings
        speed_distance_factor: How much speed affects distance
        max_speed_distance: Maximum distance at full speed

        # Collision settings
        collision_enabled: Enable collision detection
        collision_radius: Camera collision sphere radius
        collision_layers: Physics layers to check
        ignore_objects: Objects to ignore for collision

        # Obstacle response
        obstacle_response: Default response to obstacles
        min_obstacle_distance: Distance to maintain from obstacles

        # Transition settings
        transition_duration: Duration for mode transitions
        transition_type: Type of transition between modes

        # Framing settings
        dead_zone_radius: Dead zone for subtle movements
        rule_of_thirds_offset: Offset for rule of thirds framing
        headroom: Headroom multiplier

        # Performance settings
        update_frequency: Updates per second (0 = every frame)
        prediction_enabled: Enable motion prediction
    """
    name: str = "default_follow"

    # Follow mode
    follow_mode: FollowMode = FollowMode.OVER_SHOULDER
    target: FollowTarget = field(default_factory=FollowTarget)

    # Distance settings
    min_distance: float = 1.0
    max_distance: float = 10.0
    ideal_distance: float = 3.0
    distance_smoothing: float = 0.1

    # Height settings
    min_height: float = 0.5
    max_height: float = 5.0
    ideal_height: float = 1.5
    height_smoothing: float = 0.1

    # Rotation settings
    yaw_smoothing: float = 0.1
    pitch_smoothing: float = 0.1
    roll_enabled: bool = False

    # Mode-specific offsets
    shoulder_offset: float = 0.5  # Negative = left shoulder
    lead_distance: float = 2.0
    orbit_speed: float = 30.0  # Degrees per second

    # Side-scroller settings
    locked_plane: LockedPlane = LockedPlane.XZ
    locked_axis_value: float = 0.0

    # Chase settings
    speed_distance_factor: float = 0.5
    max_speed_distance: float = 5.0

    # Collision settings
    collision_enabled: bool = True
    collision_radius: float = 0.3
    collision_layers: List[str] = field(default_factory=lambda: ["Default"])
    ignore_objects: List[str] = field(default_factory=list)

    # Obstacle response
    obstacle_response: ObstacleResponse = ObstacleResponse.PUSH_FORWARD
    min_obstacle_distance: float = 0.5

    # Transition settings
    transition_duration: float = 0.5
    transition_type: TransitionType = TransitionType.BLEND

    # Framing settings
    dead_zone_radius: float = 0.1
    rule_of_thirds_offset: Tuple[float, float] = (0.0, 0.1)
    headroom: float = 1.1

    # Performance settings
    update_frequency: int = 60
    prediction_enabled: bool = True

    # Operator behavior (Phase 8.2)
    operator_behavior: OperatorBehavior = field(default_factory=OperatorBehavior)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "follow_mode": self.follow_mode.value,
            "target": self.target.to_dict(),
            "min_distance": self.min_distance,
            "max_distance": self.max_distance,
            "ideal_distance": self.ideal_distance,
            "distance_smoothing": self.distance_smoothing,
            "min_height": self.min_height,
            "max_height": self.max_height,
            "ideal_height": self.ideal_height,
            "height_smoothing": self.height_smoothing,
            "yaw_smoothing": self.yaw_smoothing,
            "pitch_smoothing": self.pitch_smoothing,
            "roll_enabled": self.roll_enabled,
            "shoulder_offset": self.shoulder_offset,
            "lead_distance": self.lead_distance,
            "orbit_speed": self.orbit_speed,
            "locked_plane": self.locked_plane.value,
            "locked_axis_value": self.locked_axis_value,
            "speed_distance_factor": self.speed_distance_factor,
            "max_speed_distance": self.max_speed_distance,
            "collision_enabled": self.collision_enabled,
            "collision_radius": self.collision_radius,
            "collision_layers": self.collision_layers,
            "ignore_objects": self.ignore_objects,
            "obstacle_response": self.obstacle_response.value,
            "min_obstacle_distance": self.min_obstacle_distance,
            "transition_duration": self.transition_duration,
            "transition_type": self.transition_type.value,
            "dead_zone_radius": self.dead_zone_radius,
            "rule_of_thirds_offset": list(self.rule_of_thirds_offset),
            "headroom": self.headroom,
            "update_frequency": self.update_frequency,
            "prediction_enabled": self.prediction_enabled,
            "operator_behavior": self.operator_behavior.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FollowCameraConfig:
        """Create from dictionary."""
        target_data = data.get("target", {})
        target = FollowTarget.from_dict(target_data) if target_data else FollowTarget()

        return cls(
            name=data.get("name", "default_follow"),
            follow_mode=FollowMode(data.get("follow_mode", "over_shoulder")),
            target=target,
            min_distance=data.get("min_distance", 1.0),
            max_distance=data.get("max_distance", 10.0),
            ideal_distance=data.get("ideal_distance", 3.0),
            distance_smoothing=data.get("distance_smoothing", 0.1),
            min_height=data.get("min_height", 0.5),
            max_height=data.get("max_height", 5.0),
            ideal_height=data.get("ideal_height", 1.5),
            height_smoothing=data.get("height_smoothing", 0.1),
            yaw_smoothing=data.get("yaw_smoothing", 0.1),
            pitch_smoothing=data.get("pitch_smoothing", 0.1),
            roll_enabled=data.get("roll_enabled", False),
            shoulder_offset=data.get("shoulder_offset", 0.5),
            lead_distance=data.get("lead_distance", 2.0),
            orbit_speed=data.get("orbit_speed", 30.0),
            locked_plane=LockedPlane(data.get("locked_plane", "xz")),
            locked_axis_value=data.get("locked_axis_value", 0.0),
            speed_distance_factor=data.get("speed_distance_factor", 0.5),
            max_speed_distance=data.get("max_speed_distance", 5.0),
            collision_enabled=data.get("collision_enabled", True),
            collision_radius=data.get("collision_radius", 0.3),
            collision_layers=data.get("collision_layers", ["Default"]),
            ignore_objects=data.get("ignore_objects", []),
            obstacle_response=ObstacleResponse(data.get("obstacle_response", "push_forward")),
            min_obstacle_distance=data.get("min_obstacle_distance", 0.5),
            transition_duration=data.get("transition_duration", 0.5),
            transition_type=TransitionType(data.get("transition_type", "blend")),
            dead_zone_radius=data.get("dead_zone_radius", 0.1),
            rule_of_thirds_offset=tuple(data.get("rule_of_thirds_offset", (0.0, 0.1))),
            headroom=data.get("headroom", 1.1),
            update_frequency=data.get("update_frequency", 60),
            prediction_enabled=data.get("prediction_enabled", True),
            operator_behavior=OperatorBehavior.from_dict(data.get("operator_behavior", {})),
        )


@dataclass
class CameraState:
    """
    Runtime state of the follow camera.

    Tracks current position, orientation, and internal state
    for smooth interpolation and debugging.

    Attributes:
        position: Current camera position
        rotation: Current camera rotation (Euler degrees)
        distance: Current distance from target
        height: Current height above target
        yaw: Current yaw angle
        pitch: Current pitch angle
        velocity: Camera velocity for motion prediction
        target_position: Last known target position
        target_velocity: Last known target velocity
        current_mode: Currently active follow mode
        obstacles: List of currently detected obstacles
        is_transitioning: Whether camera is transitioning between modes
        transition_progress: Progress of current transition (0-1)
    """
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    distance: float = 3.0
    height: float = 1.5
    yaw: float = 0.0
    pitch: float = 0.0
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    current_mode: FollowMode = FollowMode.OVER_SHOULDER
    obstacles: List[ObstacleInfo] = field(default_factory=list)
    is_transitioning: bool = False
    transition_progress: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "position": list(self.position),
            "rotation": list(self.rotation),
            "distance": self.distance,
            "height": self.height,
            "yaw": self.yaw,
            "pitch": self.pitch,
            "velocity": list(self.velocity),
            "target_position": list(self.target_position),
            "target_velocity": list(self.target_velocity),
            "current_mode": self.current_mode.value,
            "obstacles": [o.to_dict() for o in self.obstacles],
            "is_transitioning": self.is_transitioning,
            "transition_progress": self.transition_progress,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CameraState:
        """Create from dictionary."""
        obstacles_data = data.get("obstacles", [])
        obstacles = [ObstacleInfo.from_dict(o) for o in obstacles_data]

        return cls(
            position=tuple(data.get("position", (0.0, 0.0, 0.0))),
            rotation=tuple(data.get("rotation", (0.0, 0.0, 0.0))),
            distance=data.get("distance", 3.0),
            height=data.get("height", 1.5),
            yaw=data.get("yaw", 0.0),
            pitch=data.get("pitch", 0.0),
            velocity=tuple(data.get("velocity", (0.0, 0.0, 0.0))),
            target_position=tuple(data.get("target_position", (0.0, 0.0, 0.0))),
            target_velocity=tuple(data.get("target_velocity", (0.0, 0.0, 0.0))),
            current_mode=FollowMode(data.get("current_mode", "over_shoulder")),
            obstacles=obstacles,
            is_transitioning=data.get("is_transitioning", False),
            transition_progress=data.get("transition_progress", 0.0),
        )
