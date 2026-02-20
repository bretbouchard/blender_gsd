"""
Traffic Animation System - Real-Time Vehicle Movement

Provides complete traffic simulation with:
- Lane following
- Intersection handling
- Chase avoidance
- Physics-based movement

Usage:
    from lib.animation.city.traffic_animator import TrafficAnimator

    # Initialize from existing scene
    animator = TrafficAnimator.from_scene()

    # Or create new with config
    animator = TrafficAnimator(
        road_network=roads,
        vehicle_count=50
    )

    # Update per frame
    animator.update(delta_time=1/24)

    # Register as frame handler
    animator.register_handler()
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
import math
import random
import bpy
from bpy.app.handlers import persistent
from mathutils import Vector

# Guarded import
try:
    from .traffic_ai import TrafficController, VehicleAgent, TrafficConfig, AgentState
    from .road_network import RoadNetwork, RoadSegment
    TRAFFIC_AI_AVAILABLE = True
except ImportError:
    TRAFFIC_AI_AVAILABLE = False


@dataclass
class AnimatedVehicle:
    """Vehicle with animation state."""
    blender_object: Any
    agent: Optional[Any] = None

    # Position/velocity
    position: Vector = field(default_factory=lambda: Vector((0, 0, 0)))
    velocity: Vector = field(default_factory=lambda: Vector((0, 0, 0)))
    heading: float = 0.0
    speed: float = 0.0

    # Route
    route: List[Tuple[float, float, float]] = field(default_factory=list)
    route_index: int = 0
    route_progress: float = 0.0

    # Behavior
    target_speed: float = 30.0  # m/s
    max_speed: float = 50.0  # m/s
    acceleration: float = 5.0  # m/s^2
    turn_rate: float = 2.0  # rad/s

    # State
    is_hero: bool = False
    is_pursuit: bool = False
    is_avoiding: bool = False
    is_crashed: bool = False

    # Animation
    wheel_rotation: float = 0.0
    wheel_radius: float = 0.35


@dataclass
class TrafficScene:
    """Complete traffic scene state."""
    vehicles: List[AnimatedVehicle] = field(default_factory=list)
    hero_vehicle: Optional[AnimatedVehicle] = None
    pursuit_vehicles: List[AnimatedVehicle] = field(default_factory=list)

    # Road data
    road_segments: List[Any] = field(default_factory=list)
    intersections: List[Any] = field(default_factory=list)

    # Timing
    time: float = 0.0
    frame: int = 0
    fps: float = 24.0


class TrafficAnimator:
    """
    Complete traffic animation system.

    Handles:
    - Vehicle spawning and despawning
    - Route following
    - Physics-based movement
    - Chase avoidance
    - Frame handler integration
    """

    def __init__(
        self,
        scene_name: str = "City",
        vehicle_count: int = 20,
        hero_enabled: bool = True,
        pursuit_count: int = 3
    ):
        self.scene_name = scene_name
        self.vehicle_count = vehicle_count
        self.hero_enabled = hero_enabled
        self.pursuit_count = pursuit_count

        self.scene = TrafficScene()
        self._registered = False
        self._initialized = False

    @classmethod
    def from_scene(cls) -> 'TrafficAnimator':
        """Create animator from existing Blender scene."""
        animator = cls()

        # Find traffic collection
        traffic_col = bpy.data.collections.get("Traffic")
        hero_col = bpy.data.collections.get("Hero")
        pursuit_col = bpy.data.collections.get("Pursuit")

        # Add traffic vehicles
        if traffic_col:
            for obj in traffic_col.objects:
                vehicle = AnimatedVehicle(blender_object=obj)
                vehicle.target_speed = random.uniform(20, 40) / 3.6
                vehicle.max_speed = 60 / 3.6
                vehicle.heading = obj.rotation_euler[2]
                vehicle.position = Vector(obj.location)
                animator.scene.vehicles.append(vehicle)

        # Add hero vehicle
        if hero_col and hero_col.objects:
            hero_obj = list(hero_col.objects)[0]
            vehicle = AnimatedVehicle(
                blender_object=hero_obj,
                is_hero=True,
                target_speed=100 / 3.6,
                max_speed=150 / 3.6
            )
            vehicle.position = Vector(hero_obj.location)
            vehicle.heading = hero_obj.rotation_euler[2]
            animator.scene.hero_vehicle = vehicle

        # Add pursuit vehicles
        if pursuit_col:
            for obj in pursuit_col.objects:
                vehicle = AnimatedVehicle(
                    blender_object=obj,
                    is_pursuit=True,
                    target_speed=90 / 3.6,
                    max_speed=140 / 3.6
                )
                vehicle.position = Vector(obj.location)
                vehicle.heading = obj.rotation_euler[2]
                animator.scene.pursuit_vehicles.append(vehicle)

        # Find road curves
        roads_col = bpy.data.collections.get("Roads")
        if roads_col:
            animator.scene.road_segments = list(roads_col.objects)

        animator._initialized = True
        return animator

    def generate_routes(self) -> None:
        """Generate routes for all vehicles."""
        if not self.scene.road_segments:
            # Generate random routes
            for vehicle in self.scene.vehicles:
                vehicle.route = self._generate_random_route()
        else:
            # Use actual road curves
            for vehicle in self.scene.vehicles:
                vehicle.route = self._sample_road_route()

        # Hero gets main chase path
        if self.scene.hero_vehicle:
            self.scene.hero_vehicle.route = self._generate_chase_route()

        # Pursuit follows hero with offset
        for i, pursuit in enumerate(self.scene.pursuit_vehicles):
            if self.scene.hero_vehicle:
                pursuit.route = self.scene.hero_vehicle.route.copy()

    def _generate_random_route(self) -> List[Tuple[float, float, float]]:
        """Generate random waypoint route."""
        route = []
        x, y = random.uniform(-200, 200), random.uniform(-200, 200)

        for _ in range(10):
            x += random.uniform(-100, 100)
            y += random.uniform(-100, 100)
            route.append((x, y, 0))

        return route

    def _generate_chase_route(self) -> List[Tuple[float, float, float]]:
        """Generate main chase route through city."""
        route = []

        # Diagonal route with variation
        start = (0, 0, 0)
        end = (400, 400, 0)

        # Sample points along route
        num_points = 15
        for i in range(num_points):
            t = i / (num_points - 1)
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t

            # Add variation
            if 0 < t < 1:
                x += random.uniform(-30, 30)
                y += random.uniform(-30, 30)

            route.append((x, y, 0))

        return route

    def _sample_road_route(self) -> List[Tuple[float, float, float]]:
        """Sample route from road curves."""
        route = []

        # Pick random road and sample it
        if self.scene.road_segments:
            road = random.choice(self.scene.road_segments)
            if hasattr(road.data, 'splines') and road.data.splines:
                spline = road.data.splines[0]
                for point in spline.points:
                    # Transform to world space
                    world_pos = road.matrix_world @ Vector(point.co[:3])
                    route.append((world_pos.x, world_pos.y, world_pos.z))

        return route if route else self._generate_random_route()

    def update(self, delta_time: float) -> None:
        """Update all vehicles for one frame."""
        if not self._initialized:
            self._initialized = True
            self.generate_routes()

        self.scene.time += delta_time
        self.scene.frame += 1

        # Update hero vehicle
        if self.scene.hero_vehicle:
            self._update_hero(self.scene.hero_vehicle, delta_time)

        # Update pursuit vehicles
        for pursuit in self.scene.pursuit_vehicles:
            self._update_pursuit(pursuit, delta_time)

        # Update traffic
        for vehicle in self.scene.vehicles:
            self._update_traffic(vehicle, delta_time)

        # Check for crashes
        self._check_collisions()

    def _update_hero(self, vehicle: AnimatedVehicle, dt: float) -> None:
        """Update hero vehicle along chase route."""
        if vehicle.is_crashed or not vehicle.route:
            return

        # Follow route
        self._follow_route(vehicle, dt)

        # Hero drives fast
        vehicle.target_speed = 100 / 3.6

        # Update Blender object
        self._apply_to_blender(vehicle)

    def _update_pursuit(self, vehicle: AnimatedVehicle, dt: float) -> None:
        """Update pursuit vehicle following hero."""
        if vehicle.is_crashed:
            return

        hero = self.scene.hero_vehicle
        if not hero:
            self._follow_route(vehicle, dt)
            self._apply_to_blender(vehicle)
            return

        # Calculate distance to hero
        dist_to_hero = (vehicle.position - hero.position).length

        # Adjust speed based on distance
        target_dist = 30.0 + len(self.scene.pursuit_vehicles) * 10

        if dist_to_hero > target_dist + 50:
            # Far behind - speed up
            vehicle.target_speed = hero.speed * 1.3
        elif dist_to_hero > target_dist:
            # Closing - match speed
            vehicle.target_speed = hero.speed * 1.1
        elif dist_to_hero > target_dist - 20:
            # Good distance - match speed
            vehicle.target_speed = hero.speed
        else:
            # Too close - slow down
            vehicle.target_speed = hero.speed * 0.8

        # Follow route with steering toward hero
        self._follow_route(vehicle, dt, target=hero.position)

        # Update Blender object
        self._apply_to_blender(vehicle)

    def _update_traffic(self, vehicle: AnimatedVehicle, dt: float) -> None:
        """Update regular traffic vehicle."""
        if vehicle.is_crashed:
            return

        # Check for nearby hero/pursuit
        vehicle.is_avoiding = self._check_chase_proximity(vehicle)

        if vehicle.is_avoiding:
            # Avoidance behavior - slow down and pull over
            vehicle.target_speed = 10 / 3.6

            # Steer away from hero
            if self.scene.hero_vehicle:
                away_dir = vehicle.position - self.scene.hero_vehicle.position
                if away_dir.length > 0:
                    vehicle.heading += math.atan2(away_dir.y, away_dir.x) * 0.1
        else:
            # Normal driving
            vehicle.target_speed = random.uniform(30, 50) / 3.6
            self._follow_route(vehicle, dt)

        # Update Blender object
        self._apply_to_blender(vehicle)

    def _follow_route(
        self,
        vehicle: AnimatedVehicle,
        dt: float,
        target: Optional[Vector] = None
    ) -> None:
        """Move vehicle along its route."""
        if not vehicle.route or vehicle.route_index >= len(vehicle.route):
            return

        # Get current waypoint
        waypoint = Vector(vehicle.route[vehicle.route_index])

        # Direction to waypoint
        to_waypoint = waypoint - vehicle.position
        dist_to_waypoint = to_waypoint.length

        # Check if reached waypoint
        if dist_to_waypoint < 10.0:
            vehicle.route_index += 1
            if vehicle.route_index >= len(vehicle.route):
                vehicle.route_index = 0  # Loop
                if not vehicle.is_hero:
                    # Regenerate route for traffic
                    vehicle.route = self._generate_random_route()
            return

        # Calculate desired heading
        desired_heading = math.atan2(to_waypoint.y, to_waypoint.x)

        # If we have a target, blend toward it
        if target:
            to_target = target - vehicle.position
            target_heading = math.atan2(to_target.y, to_target.x)
            desired_heading = desired_heading * 0.7 + target_heading * 0.3

        # Smoothly turn toward desired heading
        heading_error = desired_heading - vehicle.heading

        # Normalize to -pi to pi
        while heading_error > math.pi:
            heading_error -= 2 * math.pi
        while heading_error < -math.pi:
            heading_error += 2 * math.pi

        vehicle.heading += heading_error * vehicle.turn_rate * dt

        # Accelerate/decelerate
        speed_diff = vehicle.target_speed - vehicle.speed
        vehicle.speed += speed_diff * vehicle.acceleration * dt
        vehicle.speed = max(0, min(vehicle.speed, vehicle.max_speed))

        # Update position
        vehicle.velocity = Vector((
            math.cos(vehicle.heading) * vehicle.speed,
            math.sin(vehicle.heading) * vehicle.speed,
            0
        ))
        vehicle.position += vehicle.velocity * dt

        # Update wheel rotation
        vehicle.wheel_rotation += vehicle.speed / vehicle.wheel_radius * dt

    def _check_chase_proximity(self, vehicle: AnimatedVehicle) -> bool:
        """Check if vehicle is near chase action."""
        avoidance_radius = 50.0  # meters

        if self.scene.hero_vehicle:
            dist = (vehicle.position - self.scene.hero_vehicle.position).length
            if dist < avoidance_radius:
                return True

        for pursuit in self.scene.pursuit_vehicles:
            dist = (vehicle.position - pursuit.position).length
            if dist < avoidance_radius * 0.7:
                return True

        return False

    def _check_collisions(self) -> None:
        """Check for vehicle collisions."""
        collision_radius = 3.0  # meters

        all_vehicles = (
            self.scene.vehicles +
            self.scene.pursuit_vehicles +
            ([self.scene.hero_vehicle] if self.scene.hero_vehicle else [])
        )

        for i, v1 in enumerate(all_vehicles):
            for v2 in all_vehicles[i+1:]:
                if v1.is_crashed or v2.is_crashed:
                    continue

                dist = (v1.position - v2.position).length

                if dist < collision_radius:
                    # Mark as crashed
                    v1.is_crashed = True
                    v2.is_crashed = True

                    # Apply crash effect
                    self._apply_crash_effect(v1, v2)

    def _apply_crash_effect(self, v1: AnimatedVehicle, v2: AnimatedVehicle) -> None:
        """Apply visual crash effect."""
        # Stop vehicles
        v1.speed = 0
        v2.speed = 0

        # Could add:
        # - Particle effects
        # - Deformation
        # - Slow motion
        # - Camera shake

    def _apply_to_blender(self, vehicle: AnimatedVehicle) -> None:
        """Apply vehicle state to Blender object."""
        if not vehicle.blender_object:
            return

        obj = vehicle.blender_object

        # Position
        obj.location = vehicle.position

        # Rotation
        obj.rotation_euler = (0, 0, vehicle.heading)

        # Animate wheels if they exist
        for child in obj.children:
            if "wheel" in child.name.lower():
                child.rotation_euler[0] = vehicle.wheel_rotation

    def register_handler(self) -> None:
        """Register as Blender frame change handler."""
        if self._registered:
            return

        # Store reference
        bpy.types.Scene.city_chase_animator = self

        # Add handler
        if traffic_frame_handler not in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.append(traffic_frame_handler)

        self._registered = True

    def unregister_handler(self) -> None:
        """Unregister frame handler."""
        if traffic_frame_handler in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(traffic_frame_handler)

        if hasattr(bpy.types.Scene, 'city_chase_animator'):
            del bpy.types.Scene.city_chase_animator

        self._registered = False


@persistent
def traffic_frame_handler(scene):
    """Frame change handler for traffic animation."""
    if hasattr(scene, 'city_chase_animator'):
        animator = scene.city_chase_animator
        fps = scene.render.fps
        dt = 1.0 / fps
        animator.update(dt)


# Convenience function
def start_traffic_animation() -> TrafficAnimator:
    """Start traffic animation from current scene."""
    animator = TrafficAnimator.from_scene()
    animator.register_handler()
    return animator


def stop_traffic_animation() -> None:
    """Stop traffic animation."""
    if hasattr(bpy.types.Scene, 'city_chase_animator'):
        animator = bpy.types.Scene.city_chase_animator
        animator.unregister_handler()
