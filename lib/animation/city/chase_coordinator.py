"""
Chase Coordinator - High-Speed Chase Sequence Orchestration

Orchestrates car chase sequences with path planning, crash points,
and pursuit vehicle coordination.

Usage:
    from lib.animation.city.chase_coordinator import ChaseDirector, create_chase

    # Create a chase sequence
    chase = create_chase(
        road_network=roads,
        hero_car=hero_vehicle,
        pursuit_count=3,
        crash_points=[
            {"location": "Trade & Tryon", "intensity": 0.5},
            {"location": "I-77 Overpass", "intensity": 0.8}
        ]
    )

    # Start the chase
    chase.start()

    # Update each frame
    chase.update(delta_time=1/24)

    # Get chase state
    state = chase.get_state()
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set, Callable, TYPE_CHECKING
from pathlib import Path
import math
import random
from enum import Enum

# Guarded bpy import
try:
    import bpy
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    Matrix = None
    BLENDER_AVAILABLE = False


class ChaseState(Enum):
    """Chase sequence state."""
    SETUP = "setup"
    STAGING = "staging"
    ACTIVE = "active"
    CRASH = "crash"
    ESCAPE = "escape"
    COMPLETE = "complete"


@dataclass
class CrashPoint:
    """A scripted crash or stunt point."""
    id: str
    position: Tuple[float, float, float]
    progress: float  # 0.0-1.0 along chase route
    intensity: float  # 0.0-1.0 crash severity
    crash_type: str = "collision"  # collision, rollover, jump, spin
    involved_vehicles: List[str] = field(default_factory=list)
    triggered: bool = False
    triggered_time: float = 0.0

    # Visual effects
    smoke_enabled: bool = True
    fire_enabled: bool = False
    debris_enabled: bool = True

    # Animation
    slow_motion_factor: float = 1.0
    camera_shake: float = 0.5


@dataclass
class ChaseConfig:
    """Configuration for chase sequence."""
    pursuit_count: int = 3
    min_spacing: float = 30.0  # meters between pursuit cars
    max_spacing: float = 100.0
    hero_speed: float = 120.0  # km/h
    pursuit_speed: float = 110.0  # km/h
    catch_up_rate: float = 5.0  # m/s acceleration
    escape_distance: float = 200.0  # meters ahead to "escape"
    crash_enabled: bool = True
    stunts_enabled: bool = True


# Chase presets
CHASE_PRESETS = {
    "standard": ChaseConfig(
        pursuit_count=3,
        hero_speed=120.0,
        pursuit_speed=110.0,
    ),
    "intense": ChaseConfig(
        pursuit_count=5,
        hero_speed=140.0,
        pursuit_speed=130.0,
        min_spacing=20.0,
        catch_up_rate=8.0,
    ),
    "hollywood": ChaseConfig(
        pursuit_count=6,
        hero_speed=150.0,
        pursuit_speed=145.0,
        crash_enabled=True,
        stunts_enabled=True,
    ),
    " getaway": ChaseConfig(
        pursuit_count=2,
        hero_speed=160.0,
        pursuit_speed=140.0,
        escape_distance=300.0,
    ),
}


class PathPlanner:
    """
    Plans and manages chase routes through the city.

    Handles:
    - Route calculation
    - Dynamic rerouting
    - Crash point placement
    """

    def __init__(self, road_network: Any):
        self.road_network = road_network
        self.main_route: List[Tuple[float, float, float]] = []
        self.alternate_routes: List[List[Tuple[float, float, float]]] = []

    def plan_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        via_points: Optional[List[Tuple[float, float]]] = None,
        include_crash_points: bool = True
    ) -> List[Tuple[float, float, float]]:
        """
        Plan a chase route through the city.

        Args:
            start: Starting position
            end: Ending position
            via_points: Optional intermediate points
            include_crash_points: Add dramatic crash locations

        Returns:
            List of waypoints
        """
        # Get base route from road network
        base_route = self.road_network.find_route(start, end)

        if not base_route:
            # Generate procedural route
            base_route = self._generate_procedural_route(start, end)

        # Add via points
        if via_points:
            for via in via_points:
                # Insert via point at closest position
                min_dist = float('inf')
                insert_idx = len(base_route)

                for i, point in enumerate(base_route):
                    dist = math.sqrt(
                        (point[0] - via[0])**2 +
                        (point[1] - via[1])**2
                    )
                    if dist < min_dist:
                        min_dist = dist
                        insert_idx = i

                base_route.insert(insert_idx, (via[0], via[1], 0))

        self.main_route = base_route
        return base_route

    def _generate_procedural_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float]
    ) -> List[Tuple[float, float, float]]:
        """Generate a procedural route for testing."""
        route = [(*start, 0)]

        # Add intermediate points
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx*dx + dy*dy)

        segments = int(length / 50)
        for i in range(1, segments):
            t = i / segments
            x = start[0] + dx * t + random.uniform(-20, 20)
            y = start[1] + dy * t + random.uniform(-20, 20)
            route.append((x, y, 0))

        route.append((*end, 0))
        return route

    def get_position_at_progress(
        self,
        progress: float
    ) -> Tuple[float, float, float]:
        """Get position along route at progress (0-1)."""
        if not self.main_route:
            return (0, 0, 0)

        # Calculate total length
        total_length = 0.0
        segments = []
        for i in range(len(self.main_route) - 1):
            p1 = self.main_route[i]
            p2 = self.main_route[i + 1]
            length = math.sqrt(
                (p2[0] - p1[0])**2 +
                (p2[1] - p1[1])**2
            )
            segments.append((total_length, length))
            total_length += length

        # Find position at progress
        target_dist = progress * total_length
        accumulated = 0.0

        for i, (start_dist, seg_length) in enumerate(segments):
            if accumulated + seg_length >= target_dist:
                # Interpolate within this segment
                local_progress = (target_dist - accumulated) / seg_length
                p1 = self.main_route[i]
                p2 = self.main_route[i + 1]

                return (
                    p1[0] + (p2[0] - p1[0]) * local_progress,
                    p1[1] + (p2[1] - p1[1]) * local_progress,
                    p1[2] + (p2[2] - p1[2]) * local_progress
                )
            accumulated += seg_length

        return self.main_route[-1]


class FollowerController:
    """
    Controls pursuit vehicle behavior.

    Handles:
    - Following distance
    - Aggressive pursuit
    - Crash avoidance
    """

    def __init__(self, vehicle: Any, config: ChaseConfig):
        self.vehicle = vehicle
        self.config = config

        self.target_distance = random.uniform(
            config.min_spacing,
            config.max_spacing
        )
        self.aggressiveness = random.uniform(0.7, 1.0)
        self.is_crashed = False

    def calculate_throttle(
        self,
        hero_position: Tuple[float, float, float],
        hero_speed: float,
        own_position: Tuple[float, float, float],
        own_speed: float
    ) -> float:
        """
        Calculate throttle input to maintain pursuit.

        Returns:
            Throttle value 0.0-1.0
        """
        if self.is_crashed:
            return 0.0

        # Distance to hero
        dx = hero_position[0] - own_position[0]
        dy = hero_position[1] - own_position[1]
        distance = math.sqrt(dx*dx + dy*dy)

        # Desired distance
        speed_factor = (hero_speed / self.config.hero_speed) * 0.3
        desired_distance = self.target_distance * (1.0 + speed_factor)

        # Throttle based on distance error
        distance_error = distance - desired_distance

        if distance_error > 50:
            # Far behind - full throttle
            return 1.0 * self.aggressiveness
        elif distance_error > 20:
            # Closing - moderate throttle
            return 0.7 * self.aggressiveness
        elif distance_error > 0:
            # Maintaining - light throttle
            return 0.5 * self.aggressiveness
        else:
            # Too close - brake
            return 0.0

    def calculate_steering(
        self,
        hero_position: Tuple[float, float, float],
        own_position: Tuple[float, float, float],
        own_heading: float
    ) -> float:
        """
        Calculate steering to follow hero.

        Returns:
            Steering value -1.0 to 1.0
        """
        if self.is_crashed:
            return 0.0

        # Direction to hero
        dx = hero_position[0] - own_position[0]
        dy = hero_position[1] - own_position[1]
        target_heading = math.atan2(dy, dx)

        # Heading error
        heading_error = target_heading - own_heading

        # Normalize
        while heading_error > math.pi:
            heading_error -= 2 * math.pi
        while heading_error < -math.pi:
            heading_error += 2 * math.pi

        return max(-1.0, min(1.0, heading_error * 2.0))


class ChaseDirector:
    """
    Main chase sequence orchestrator.

    Coordinates:
    - Hero vehicle
    - Pursuit vehicles
    - Crash points
    - Traffic avoidance
    - Camera triggers
    """

    def __init__(
        self,
        road_network: Any,
        config: Optional[ChaseConfig] = None
    ):
        self.road_network = road_network
        self.config = config or ChaseConfig()

        self.state = ChaseState.SETUP
        self.path_planner = PathPlanner(road_network)

        # Vehicles
        self.hero_vehicle: Optional[Any] = None
        self.hero_position: Tuple[float, float, float] = (0, 0, 0)
        self.hero_progress: float = 0.0
        self.hero_speed: float = 0.0

        self.pursuit_vehicles: List[FollowerController] = []
        self.pursuit_positions: List[Tuple[float, float, float]] = []

        # Crash points
        self.crash_points: List[CrashPoint] = []
        self.active_crash: Optional[CrashPoint] = None

        # Timing
        self.chase_time: float = 0.0
        self.total_duration: float = 60.0  # seconds

        # Callbacks
        self._on_crash_callbacks: List[Callable] = []
        self._on_complete_callbacks: List[Callable] = []

    def setup_chase(
        self,
        hero_vehicle: Any,
        route_start: Tuple[float, float],
        route_end: Tuple[float, float],
        crash_points: Optional[List[Dict]] = None
    ) -> None:
        """
        Setup the chase sequence.

        Args:
            hero_vehicle: The vehicle being chased
            route_start: Chase start position
            route_end: Chase end position
            crash_points: List of crash point configurations
        """
        self.hero_vehicle = hero_vehicle

        # Plan route
        self.path_planner.plan_route(route_start, route_end)

        # Setup crash points
        if crash_points:
            for i, cp_config in enumerate(crash_points):
                crash_point = CrashPoint(
                    id=f"crash_{i}",
                    position=(0, 0, 0),  # Will be set from progress
                    progress=cp_config.get("progress", 0.5),
                    intensity=cp_config.get("intensity", 0.5),
                    crash_type=cp_config.get("type", "collision"),
                    fire_enabled=cp_config.get("intensity", 0.5) > 0.7,
                )
                crash_point.position = self.path_planner.get_position_at_progress(
                    crash_point.progress
                )
                self.crash_points.append(crash_point)

        self.state = ChaseState.STAGING

    def add_pursuit_vehicle(
        self,
        vehicle: Any,
        start_offset: float = 0.0
    ) -> FollowerController:
        """Add a pursuit vehicle to the chase."""
        controller = FollowerController(vehicle, self.config)
        controller.target_distance = self.config.min_spacing + (
            len(self.pursuit_vehicles) * 20
        )
        self.pursuit_vehicles.append(controller)
        return controller

    def start(self) -> None:
        """Start the chase sequence."""
        self.state = ChaseState.ACTIVE
        self.chase_time = 0.0

        # Initialize positions
        self.hero_position = self.path_planner.main_route[0]
        self.hero_progress = 0.0

        for i, controller in enumerate(self.pursuit_vehicles):
            offset = (i + 1) * 30  # 30m spacing
            progress = max(0, self.hero_progress - offset / 1000)
            pos = self.path_planner.get_position_at_progress(progress)
            self.pursuit_positions.append(pos)

    def update(self, delta_time: float) -> None:
        """
        Update chase state.

        Args:
            delta_time: Time step in seconds
        """
        if self.state != ChaseState.ACTIVE:
            return

        self.chase_time += delta_time

        # Update hero position along route
        route_speed = self.config.hero_speed / 3.6  # Convert to m/s
        route_progress_rate = route_speed / self._get_route_length()
        self.hero_progress += route_progress_rate * delta_time
        self.hero_progress = min(1.0, self.hero_progress)

        self.hero_position = self.path_planner.get_position_at_progress(
            self.hero_progress
        )
        self.hero_speed = self.config.hero_speed

        # Update pursuit vehicles
        for i, controller in enumerate(self.pursuit_vehicles):
            if not controller.is_crashed:
                # Calculate desired position
                target_progress = max(
                    0,
                    self.hero_progress - controller.target_distance / self._get_route_length()
                )

                # Update position
                self.pursuit_positions[i] = self.path_planner.get_position_at_progress(
                    target_progress
                )

        # Check crash points
        for crash_point in self.crash_points:
            if not crash_point.triggered:
                if abs(self.hero_progress - crash_point.progress) < 0.02:
                    self._trigger_crash(crash_point)

        # Check for chase completion
        if self.hero_progress >= 1.0:
            self.state = ChaseState.ESCAPE
            self._on_complete()

        # Check time limit
        if self.chase_time >= self.total_duration:
            self.state = ChaseState.COMPLETE
            self._on_complete()

    def _get_route_length(self) -> float:
        """Get total route length in meters."""
        length = 0.0
        for i in range(len(self.path_planner.main_route) - 1):
            p1 = self.path_planner.main_route[i]
            p2 = self.path_planner.main_route[i + 1]
            length += math.sqrt(
                (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2
            )
        return length

    def _trigger_crash(self, crash_point: CrashPoint) -> None:
        """Trigger a crash event."""
        crash_point.triggered = True
        crash_point.triggered_time = self.chase_time
        self.active_crash = crash_point
        self.state = ChaseState.CRASH

        # Pick a pursuit vehicle to crash
        if self.pursuit_vehicles:
            crashed_idx = random.randint(0, len(self.pursuit_vehicles) - 1)
            self.pursuit_vehicles[crashed_idx].is_crashed = True
            crash_point.involved_vehicles.append(
                f"pursuit_{crashed_idx}"
            )

        # Fire callbacks
        for callback in self._on_crash_callbacks:
            callback(crash_point)

        # Resume chase after crash
        # In real implementation, would have slow-mo, camera effects, etc.
        self.state = ChaseState.ACTIVE

    def _on_complete(self) -> None:
        """Handle chase completion."""
        for callback in self._on_complete_callbacks:
            callback(self.state)

    def get_state(self) -> Dict[str, Any]:
        """Get current chase state."""
        return {
            "state": self.state.value,
            "chase_time": self.chase_time,
            "hero_progress": self.hero_progress,
            "hero_position": self.hero_position,
            "hero_speed": self.hero_speed,
            "pursuit_count": len(self.pursuit_vehicles),
            "pursuit_positions": self.pursuit_positions,
            "active_crash": self.active_crash.id if self.active_crash else None,
            "remaining_crashes": sum(1 for cp in self.crash_points if not cp.triggered),
        }

    def on_crash(self, callback: Callable) -> None:
        """Register crash callback."""
        self._on_crash_callbacks.append(callback)

    def on_complete(self, callback: Callable) -> None:
        """Register completion callback."""
        self._on_complete_callbacks.append(callback)


def create_chase(
    road_network: Any,
    hero_car: Any,
    pursuit_count: int = 3,
    crash_points: Optional[List[Tuple[str, float]]] = None,
    preset: str = "standard"
) -> ChaseDirector:
    """
    Create a chase sequence.

    Args:
        road_network: RoadNetwork instance
        hero_car: Hero vehicle Blender object
        pursuit_count: Number of pursuit vehicles
        crash_points: List of (location_name, progress) tuples
        preset: Chase preset name

    Returns:
        Configured ChaseDirector
    """
    config = CHASE_PRESETS.get(preset, ChaseConfig())
    config.pursuit_count = pursuit_count

    director = ChaseDirector(road_network, config)

    # Get route from road network
    route = road_network.get_random_route(min_length=1000.0)

    # Setup crash points
    crash_configs = []
    if crash_points:
        for location, progress in crash_points:
            crash_configs.append({
                "progress": progress,
                "intensity": random.uniform(0.3, 0.9),
                "type": random.choice(["collision", "rollover", "spin"]),
            })

    director.setup_chase(
        hero_vehicle=hero_car,
        route_start=(route[0][0], route[0][1]),
        route_end=(route[-1][0], route[-1][1]),
        crash_points=crash_configs
    )

    # Add pursuit vehicles (placeholder - would use actual vehicle objects)
    for i in range(pursuit_count):
        director.add_pursuit_vehicle(
            vehicle=None,  # Would be actual Blender vehicle object
            start_offset=(i + 1) * 30
        )

    return director
