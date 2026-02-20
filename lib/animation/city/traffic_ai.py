"""
Traffic AI System - Vehicle Agents with Chase Avoidance

Creates AI-driven traffic that follows lanes, avoids obstacles,
and evades chase sequences.

Usage:
    from lib.animation.city.traffic_ai import TrafficController, setup_traffic

    # Setup traffic on road network
    traffic = setup_traffic(
        road_network=roads,
        vehicle_count=100,
        style="urban"
    )

    # Mark hero vehicle for chase
    traffic.mark_hero_vehicle(hero_car)
    traffic.set_chase_mode(True)  # Traffic will avoid hero

    # Update traffic simulation
    traffic.update(delta_time=1/24)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set, TYPE_CHECKING
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


class AgentState(Enum):
    """Vehicle agent state."""
    IDLE = "idle"
    DRIVING = "driving"
    STOPPED = "stopped"
    YIELDING = "yielding"
    AVOIDING = "avoiding"
    FLEEING = "fleeing"
    CRASHED = "crashed"


@dataclass
class TrafficConfig:
    """Configuration for traffic system."""
    max_vehicles: int = 100
    spawn_rate: float = 2.0  # vehicles per second
    min_speed: float = 20.0  # km/h
    max_speed: float = 60.0  # km/h
    safe_distance: float = 10.0  # meters
    lane_change_distance: float = 30.0
    yield_distance: float = 15.0
    avoidance_radius: float = 50.0  # meters - how far to detect chase
    flee_speed_multiplier: float = 1.3
    reaction_time: float = 0.3  # seconds


@dataclass
class VehicleState:
    """Current state of a vehicle agent."""
    position: Tuple[float, float, float] = (0, 0, 0)
    velocity: Tuple[float, float, float] = (0, 0, 0)
    rotation: float = 0.0  # radians
    speed: float = 0.0  # m/s
    lane: int = 0
    state: AgentState = AgentState.IDLE
    target_speed: float = 0.0
    current_road: str = ""
    next_intersection: str = ""
    wait_time: float = 0.0


# Traffic presets
TRAFFIC_PRESETS = {
    "urban": TrafficConfig(
        max_speed=50.0,
        safe_distance=8.0,
        avoidance_radius=40.0,
    ),
    "highway": TrafficConfig(
        max_speed=120.0,
        min_speed=60.0,
        safe_distance=20.0,
        avoidance_radius=80.0,
    ),
    "residential": TrafficConfig(
        max_speed=40.0,
        min_speed=15.0,
        safe_distance=6.0,
        avoidance_radius=30.0,
    ),
    "downtown": TrafficConfig(
        max_speed=30.0,
        min_speed=10.0,
        safe_distance=5.0,
        avoidance_radius=35.0,
    ),
}


class LaneFollowing:
    """
    Lane following behavior for vehicles.

    Keeps vehicles in their lane with smooth steering.
    """

    def __init__(
        self,
        lane_center_offset: float = 0.0,
        look_ahead_distance: float = 10.0
    ):
        self.lane_center_offset = lane_center_offset
        self.look_ahead_distance = look_ahead_distance

    def calculate_steering(
        self,
        current_pos: Tuple[float, float],
        current_heading: float,
        road_points: List[Tuple[float, float]]
    ) -> float:
        """
        Calculate steering angle to follow lane.

        Args:
            current_pos: Current (x, y) position
            current_heading: Current heading in radians
            road_points: List of road centerline points

        Returns:
            Steering angle in radians
        """
        # Find closest point on road
        min_dist = float('inf')
        closest_idx = 0

        for i, point in enumerate(road_points):
            dist = math.sqrt(
                (point[0] - current_pos[0])**2 +
                (point[1] - current_pos[1])**2
            )
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        # Look ahead point
        look_ahead_idx = min(
            closest_idx + 3,
            len(road_points) - 1
        )
        look_ahead = road_points[look_ahead_idx]

        # Calculate desired heading
        dx = look_ahead[0] - current_pos[0]
        dy = look_ahead[1] - current_pos[1]
        desired_heading = math.atan2(dy, dx)

        # Apply lane offset
        lateral_offset = self.lane_center_offset * math.cos(desired_heading + math.pi/2)
        look_ahead = (
            look_ahead[0] + lateral_offset * math.sin(desired_heading),
            look_ahead[1] - lateral_offset * math.cos(desired_heading)
        )

        # Calculate steering
        heading_error = desired_heading - current_heading

        # Normalize to -pi to pi
        while heading_error > math.pi:
            heading_error -= 2 * math.pi
        while heading_error < -math.pi:
            heading_error += 2 * math.pi

        return heading_error * 0.5  # Steering gain


class AvoidanceSystem:
    """
    Collision and chase avoidance system.

    Detects obstacles and evading vehicles, calculates
    avoidance maneuvers.
    """

    def __init__(self, config: TrafficConfig):
        self.config = config
        self._threats: Dict[str, Tuple[float, float, float]] = {}

    def add_threat(
        self,
        threat_id: str,
        position: Tuple[float, float, float],
        velocity: Tuple[float, float, float]
    ) -> None:
        """Add a threat (hero car in chase) to avoid."""
        self._threats[threat_id] = (position, velocity)

    def remove_threat(self, threat_id: str) -> None:
        """Remove a threat."""
        if threat_id in self._threats:
            del self._threats[threat_id]

    def calculate_avoidance(
        self,
        current_pos: Tuple[float, float, float],
        current_velocity: Tuple[float, float, float]
    ) -> Tuple[float, float, AgentState]:
        """
        Calculate avoidance vector.

        Returns:
            (avoidance_x, avoidance_y, new_state)
        """
        avoidance_x = 0.0
        avoidance_y = 0.0
        new_state = AgentState.DRIVING

        for threat_id, (pos, vel) in self._threats.items():
            # Distance to threat
            dx = pos[0] - current_pos[0]
            dy = pos[1] - current_pos[1]
            dist = math.sqrt(dx*dx + dy*dy)

            if dist < self.config.avoidance_radius:
                # Calculate avoidance force (inverse distance)
                strength = 1.0 - (dist / self.config.avoidance_radius)

                # Avoidance direction (perpendicular to threat)
                avoid_angle = math.atan2(dy, dx) + math.pi/2

                avoidance_x += math.cos(avoid_angle) * strength * 10
                avoidance_y += math.sin(avoid_angle) * strength * 10

                if dist < self.config.avoidance_radius * 0.5:
                    new_state = AgentState.FLEEING

        return (avoidance_x, avoidance_y, new_state)

    def check_collision(
        self,
        current_pos: Tuple[float, float, float],
        other_vehicles: List[Tuple[float, float, float]]
    ) -> Tuple[bool, float]:
        """
        Check for potential collisions.

        Returns:
            (collision_imminent, distance_to_nearest)
        """
        min_dist = float('inf')

        for other_pos in other_vehicles:
            dx = other_pos[0] - current_pos[0]
            dy = other_pos[1] - current_pos[1]
            dist = math.sqrt(dx*dx + dy*dy)
            min_dist = min(min_dist, dist)

        collision_imminent = min_dist < self.config.safe_distance
        return (collision_imminent, min_dist)


class VehicleAgent:
    """
    AI-controlled vehicle agent.

    Handles:
    - Lane following
    - Speed control
    - Collision avoidance
    - Chase evasion
    """

    def __init__(
        self,
        vehicle_id: str,
        config: TrafficConfig,
        blender_object: Optional[Any] = None
    ):
        self.id = vehicle_id
        self.config = config
        self.blender_object = blender_object

        self.state = VehicleState()
        self.lane_follower = LaneFollowing()
        self.avoidance = AvoidanceSystem(config)

        # Route
        self.route: List[Tuple[float, float, float]] = []
        self.route_index = 0

        # Physics
        self.acceleration = 0.0
        self.steering = 0.0

    def set_route(self, route: List[Tuple[float, float, float]]) -> None:
        """Set the route for this vehicle."""
        self.route = route
        self.route_index = 0

    def update(
        self,
        delta_time: float,
        other_vehicles: List['VehicleAgent'],
        threats: Dict[str, Tuple[float, float, float]]
    ) -> None:
        """
        Update vehicle state.

        Args:
            delta_time: Time step in seconds
            other_vehicles: Other vehicles for collision avoidance
            threats: Threat positions (hero cars in chase)
        """
        # Update threats in avoidance system
        for threat_id, pos_vel in threats.items():
            self.avoidance.add_threat(threat_id, pos_vel[0], pos_vel[1])

        # Calculate avoidance
        avoid_x, avoid_y, avoid_state = self.avoidance.calculate_avoidance(
            self.state.position,
            self.state.velocity
        )

        # Check collisions
        other_positions = [v.state.position for v in other_vehicles if v.id != self.id]
        collision_imminent, nearest_dist = self.avoidance.check_collision(
            self.state.position,
            other_positions
        )

        # Update state based on conditions
        if avoid_state == AgentState.FLEEING:
            self.state.state = AgentState.FLEEING
            self.state.target_speed = self.config.max_speed * self.config.flee_speed_multiplier / 3.6
        elif collision_imminent:
            self.state.state = AgentState.AVOIDING
            self.state.target_speed = max(0, self.state.speed - 5)
        else:
            self.state.state = AgentState.DRIVING
            self.state.target_speed = random.uniform(
                self.config.min_speed,
                self.config.max_speed
            ) / 3.6  # Convert to m/s

        # Calculate steering
        if self.route and self.route_index < len(self.route):
            target = self.route[self.route_index]

            # Check if reached waypoint
            dx = target[0] - self.state.position[0]
            dy = target[1] - self.state.position[1]
            dist = math.sqrt(dx*dx + dy*dy)

            if dist < 5.0:  # Reached waypoint
                self.route_index += 1

            # Calculate heading to target
            desired_heading = math.atan2(dy, dx)

            # Apply avoidance offset
            desired_heading += math.atan2(avoid_y, avoid_x) * 0.3

            # Steering
            heading_error = desired_heading - self.state.rotation
            while heading_error > math.pi:
                heading_error -= 2 * math.pi
            while heading_error < -math.pi:
                heading_error += 2 * math.pi

            self.steering = heading_error * 2.0

        # Update speed
        speed_diff = self.state.target_speed - self.state.speed
        self.acceleration = speed_diff * 2.0  # Acceleration factor

        # Apply physics
        self.state.speed += self.acceleration * delta_time
        self.state.speed = max(0, min(self.state.speed, self.config.max_speed / 3.6))

        self.state.rotation += self.steering * delta_time

        # Update position
        self.state.velocity = (
            math.cos(self.state.rotation) * self.state.speed,
            math.sin(self.state.rotation) * self.state.speed,
            0
        )

        self.state.position = (
            self.state.position[0] + self.state.velocity[0] * delta_time,
            self.state.position[1] + self.state.velocity[1] * delta_time,
            self.state.position[2]
        )

        # Update Blender object
        self._update_blender_object()

    def _update_blender_object(self) -> None:
        """Update associated Blender object position."""
        if not BLENDER_AVAILABLE or not self.blender_object:
            return

        self.blender_object.location = self.state.position
        self.blender_object.rotation_euler = (
            0,
            0,
            self.state.rotation
        )


class TrafficController:
    """
    Main traffic system controller.

    Manages:
    - Vehicle spawning/despawning
    - Route assignment
    - Chase mode coordination
    - Blender integration
    """

    def __init__(
        self,
        road_network: Any,
        config: Optional[TrafficConfig] = None
    ):
        self.road_network = road_network
        self.config = config or TrafficConfig()

        self.agents: Dict[str, VehicleAgent] = {}
        self.hero_vehicles: Set[str] = set()
        self.chase_mode = False

        self._spawn_timer = 0.0
        self._next_agent_id = 0

    def spawn_vehicle(
        self,
        position: Optional[Tuple[float, float, float]] = None,
        route: Optional[List[Tuple[float, float, float]]] = None
    ) -> Optional[VehicleAgent]:
        """Spawn a new vehicle agent."""
        if len(self.agents) >= self.config.max_vehicles:
            return None

        # Generate spawn position if not provided
        if position is None:
            # Pick random road segment start
            position = (random.uniform(-100, 100), random.uniform(-100, 100), 0)

        # Generate route if not provided
        if route is None:
            route = self.road_network.get_random_route(min_length=500)

        # Create agent
        agent_id = f"vehicle_{self._next_agent_id}"
        self._next_agent_id += 1

        agent = VehicleAgent(agent_id, self.config)
        agent.state.position = position
        agent.set_route(route)

        self.agents[agent_id] = agent

        return agent

    def despawn_vehicle(self, agent_id: str) -> None:
        """Remove a vehicle from the simulation."""
        if agent_id in self.agents:
            # Remove Blender object if exists
            agent = self.agents[agent_id]
            if agent.blender_object and BLENDER_AVAILABLE:
                bpy.data.objects.remove(agent.blender_object)

            del self.agents[agent_id]

    def mark_hero_vehicle(self, vehicle: Any, vehicle_id: str = "hero") -> None:
        """Mark a vehicle as the hero (chase target)."""
        self.hero_vehicles.add(vehicle_id)

    def set_chase_mode(self, enabled: bool) -> None:
        """Enable/disable chase mode."""
        self.chase_mode = enabled

        if enabled:
            # All traffic becomes more evasive
            for agent in self.agents.values():
                if agent.id not in self.hero_vehicles:
                    agent.config.avoidance_radius *= 1.5
                    agent.config.flee_speed_multiplier *= 1.2

    def update(self, delta_time: float) -> None:
        """Update traffic simulation."""
        # Spawn new vehicles
        self._spawn_timer += delta_time
        if self._spawn_timer >= 1.0 / self.config.spawn_rate:
            self._spawn_timer = 0.0
            self.spawn_vehicle()

        # Collect threat positions (hero vehicles)
        threats: Dict[str, Tuple[float, float, float]] = {}
        # Would get hero vehicle positions here

        # Update all agents
        agent_list = list(self.agents.values())
        for agent in agent_list:
            agent.update(delta_time, agent_list, threats)

            # Despawn if off map
            x, y = agent.state.position[0], agent.state.position[1]
            if abs(x) > 500 or abs(y) > 500:
                self.despawn_vehicle(agent.id)

    def get_vehicle_positions(self) -> Dict[str, Tuple[float, float, float]]:
        """Get all vehicle positions."""
        return {
            agent_id: agent.state.position
            for agent_id, agent in self.agents.items()
        }

    def create_blender_vehicles(
        self,
        vehicle_factory: Optional[Any] = None
    ) -> None:
        """Create Blender objects for all agents."""
        if not BLENDER_AVAILABLE:
            return

        for agent in self.agents.values():
            if agent.blender_object is None:
                # Create simple vehicle mesh
                bpy.ops.mesh.primitive_cube_add(
                    size=2,
                    location=agent.state.position
                )
                obj = bpy.context.active_object
                obj.name = f"Traffic_{agent.id}"
                obj.scale = (2, 1, 0.5)  # Car-like proportions

                agent.blender_object = obj


def setup_traffic(
    road_network: Any,
    vehicle_count: int = 50,
    style: str = "urban",
    **kwargs
) -> TrafficController:
    """
    Setup traffic system for a road network.

    Args:
        road_network: RoadNetwork instance
        vehicle_count: Initial number of vehicles
        style: Traffic style preset

    Returns:
        Configured TrafficController
    """
    config = TRAFFIC_PRESETS.get(style, TrafficConfig())
    config.max_vehicles = vehicle_count

    controller = TrafficController(road_network, config)

    # Spawn initial vehicles
    for _ in range(vehicle_count):
        controller.spawn_vehicle()

    # Create Blender objects
    controller.create_blender_vehicles()

    return controller
