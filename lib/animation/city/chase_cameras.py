"""
Chase Camera System - Dynamic Camera Coverage for Chase Sequences

Provides multiple camera types for comprehensive chase coverage:
- Follow cameras (tracking, orbiting)
- Aerial cameras (drone, helicopter shots)
- In-car cameras (dashboard, POV)
- Static cameras (fixed positions)

Usage:
    from lib.animation.city.chase_cameras import (
        ChaseCameraSystem, setup_chase_cameras
    )

    # Setup cameras for chase
    cameras = setup_chase_cameras(
        chase_director=chase,
        types=["follow", "aerial", "in_car", "static"],
        auto_switch=True
    )

    # Update each frame
    cameras.update(delta_time=1/24)

    # Get active camera
    active = cameras.get_active_camera()
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, TYPE_CHECKING
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


class CameraType(Enum):
    """Camera type enumeration."""
    FOLLOW = "follow"
    AERIAL = "aerial"
    IN_CAR = "in_car"
    STATIC = "static"
    ORBIT = "orbit"
    CRANE = "crane"
    DOLLY = "dolly"


@dataclass
class CameraConfig:
    """Configuration for a chase camera."""
    name: str
    camera_type: CameraType
    focal_length: float = 35.0
    f_stop: float = 2.8
    focus_distance: float = 50.0
    shake_intensity: float = 0.0
    smoothing: float = 0.3  # 0-1, higher = smoother
    offset: Tuple[float, float, float] = (0, 0, 0)
    look_ahead: float = 10.0  # meters ahead to target
    min_distance: float = 5.0
    max_distance: float = 100.0
    height: float = 2.0


# Camera presets
CAMERA_PRESETS = {
    "follow_close": CameraConfig(
        name="Close Follow",
        camera_type=CameraType.FOLLOW,
        focal_length=50.0,
        offset=(-15, 5, 3),
        smoothing=0.5,
    ),
    "follow_wide": CameraConfig(
        name="Wide Follow",
        camera_type=CameraType.FOLLOW,
        focal_length=24.0,
        offset=(-25, 8, 5),
        smoothing=0.7,
    ),
    "follow_low": CameraConfig(
        name="Low Angle Follow",
        camera_type=CameraType.FOLLOW,
        focal_length=35.0,
        offset=(-20, 0, 0.5),
        shake_intensity=0.3,
    ),
    "aerial_high": CameraConfig(
        name="High Aerial",
        camera_type=CameraType.AERIAL,
        focal_length=50.0,
        offset=(0, 0, 100),
        smoothing=0.8,
    ),
    "aerial_tracking": CameraConfig(
        name="Aerial Tracking",
        camera_type=CameraType.AERIAL,
        focal_length=85.0,
        offset=(-50, 0, 50),
        smoothing=0.6,
    ),
    "aerial_orbit": CameraConfig(
        name="Orbiting Helicopter",
        camera_type=CameraType.ORBIT,
        focal_length=70.0,
        offset=(80, 0, 40),
        smoothing=0.4,
    ),
    "in_car_driver": CameraConfig(
        name="Driver POV",
        camera_type=CameraType.IN_CAR,
        focal_length=24.0,
        offset=(0.5, -0.3, 1.2),
        shake_intensity=0.2,
    ),
    "in_car_dash": CameraConfig(
        name="Dashboard Cam",
        camera_type=CameraType.IN_CAR,
        focal_length=35.0,
        offset=(0, 0, 0.8),
        shake_intensity=0.1,
    ),
    "static_corner": CameraConfig(
        name="Corner Shot",
        camera_type=CameraType.STATIC,
        focal_length=50.0,
        offset=(30, 30, 2),
    ),
    "static_overpass": CameraConfig(
        name="Overpass Shot",
        camera_type=CameraType.STATIC,
        focal_length=85.0,
        offset=(0, 0, 15),
    ),
}


class FollowCamera:
    """
    Camera that follows a vehicle from behind/side.

    Supports:
    - Multiple follow positions
    - Smooth interpolation
    - Look-ahead targeting
    - Camera shake
    """

    def __init__(self, config: CameraConfig, target: Any = None):
        self.config = config
        self.target = target
        self.blender_camera: Optional[Any] = None

        self.position = Vector((0, 0, 5)) if Vector else (0, 0, 5)
        self.target_position = Vector((0, 0, 0)) if Vector else (0, 0, 0)
        self.velocity = Vector((0, 0, 0)) if Vector else (0, 0, 0)

        self._create_blender_camera()

    def _create_blender_camera(self) -> None:
        """Create Blender camera object."""
        if not BLENDER_AVAILABLE:
            return

        # Create camera data
        cam_data = bpy.data.cameras.new(f"{self.config.name}_data")
        cam_data.lens = self.config.focal_length
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = self.config.f_stop
        cam_data.dof.focus_distance = self.config.focus_distance

        # Create camera object
        self.blender_camera = bpy.data.objects.new(self.config.name, cam_data)
        bpy.context.collection.objects.link(self.blender_camera)

    def update(
        self,
        target_position: Tuple[float, float, float],
        target_velocity: Tuple[float, float, float],
        delta_time: float
    ) -> None:
        """Update camera position to follow target."""
        if Vector:
            target_pos = Vector(target_position)
            target_vel = Vector(target_velocity)

            # Calculate target heading
            if target_vel.length > 0.1:
                heading = math.atan2(target_vel.y, target_vel.x)
            else:
                heading = 0

            # Offset in target's local space
            offset_local = Vector(self.config.offset)
            offset_world = Vector((
                offset_local.x * math.cos(heading) - offset_local.y * math.sin(heading),
                offset_local.x * math.sin(heading) + offset_local.y * math.cos(heading),
                offset_local.z
            ))

            # Desired position
            desired_pos = target_pos + offset_world

            # Smooth interpolation
            smoothing = self.config.smoothing
            self.position = self.position.lerp(desired_pos, 1.0 - smoothing)

            # Add shake
            if self.config.shake_intensity > 0:
                shake = Vector((
                    random.uniform(-1, 1) * self.config.shake_intensity,
                    random.uniform(-1, 1) * self.config.shake_intensity,
                    random.uniform(-1, 1) * self.config.shake_intensity * 0.5
                ))
                self.position += shake

            # Look ahead target
            look_ahead = target_pos + target_vel.normalized() * self.config.look_ahead
            self.target_position = look_ahead

            # Update Blender camera
            if self.blender_camera:
                self.blender_camera.location = self.position

                # Point at target
                direction = (self.target_position - self.position).normalized()
                self.blender_camera.rotation_euler = direction.to_track_quat(
                    '-Z', 'Y'
                ).to_euler()


class AerialCamera:
    """
    Aerial/drone camera for overhead shots.

    Supports:
    - High overhead shots
    - Tracking shots
    - Orbiting around action
    """

    def __init__(self, config: CameraConfig):
        self.config = config
        self.blender_camera: Optional[Any] = None

        self.position = Vector((0, 0, 100)) if Vector else (0, 0, 100)
        self.orbit_angle = 0.0
        self.orbit_speed = 0.1  # radians per second

        self._create_blender_camera()

    def _create_blender_camera(self) -> None:
        """Create Blender camera object."""
        if not BLENDER_AVAILABLE:
            return

        cam_data = bpy.data.cameras.new(f"{self.config.name}_data")
        cam_data.lens = self.config.focal_length
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = self.config.f_stop

        self.blender_camera = bpy.data.objects.new(self.config.name, cam_data)
        bpy.context.collection.objects.link(self.blender_camera)

    def update(
        self,
        target_position: Tuple[float, float, float],
        delta_time: float
    ) -> None:
        """Update aerial camera position."""
        if self.config.camera_type == CameraType.ORBIT:
            # Orbit around target
            self.orbit_angle += self.orbit_speed * delta_time

            if Vector:
                offset_x = math.cos(self.orbit_angle) * self.config.offset[0]
                offset_y = math.sin(self.orbit_angle) * self.config.offset[0]
                offset_z = self.config.offset[2]

                self.position = Vector((
                    target_position[0] + offset_x,
                    target_position[1] + offset_y,
                    target_position[2] + offset_z
                ))

        else:
            # Track from fixed aerial position
            if Vector:
                self.position = Vector((
                    target_position[0] + self.config.offset[0],
                    target_position[1] + self.config.offset[1],
                    target_position[2] + self.config.offset[2]
                ))

        # Update Blender camera
        if BLENDER_AVAILABLE and self.blender_camera:
            if Vector:
                self.blender_camera.location = self.position

                # Point at target
                target = Vector(target_position)
                direction = (target - self.position).normalized()
                self.blender_camera.rotation_euler = direction.to_track_quat(
                    '-Z', 'Y'
                ).to_euler()


class InCarCamera:
    """
    In-vehicle camera for POV shots.

    Supports:
    - Driver POV
    - Dashboard cam
    - Passenger seat
    - With camera shake
    """

    def __init__(self, config: CameraConfig, vehicle: Any = None):
        self.config = config
        self.vehicle = vehicle
        self.blender_camera: Optional[Any] = None

        self.local_offset = Vector(self.config.offset) if Vector else self.config.offset

        self._create_blender_camera()

    def _create_blender_camera(self) -> None:
        """Create Blender camera object."""
        if not BLENDER_AVAILABLE:
            return

        cam_data = bpy.data.cameras.new(f"{self.config.name}_data")
        cam_data.lens = self.config.focal_length
        cam_data.dof.use_dof = False  # Everything in focus for POV

        self.blender_camera = bpy.data.objects.new(self.config.name, cam_data)
        bpy.context.collection.objects.link(self.blender_camera)

    def update(
        self,
        vehicle_position: Tuple[float, float, float],
        vehicle_rotation: float,
        vehicle_velocity: Tuple[float, float, float],
        delta_time: float
    ) -> None:
        """Update in-car camera."""
        if Vector:
            # Transform local offset to world space
            vehicle_pos = Vector(vehicle_position)
            offset_local = Vector(self.config.offset)

            # Rotate offset by vehicle heading
            cos_r = math.cos(vehicle_rotation)
            sin_r = math.sin(vehicle_rotation)

            offset_world = Vector((
                offset_local.x * cos_r - offset_local.y * sin_r,
                offset_local.x * sin_r + offset_local.y * cos_r,
                offset_local.z
            ))

            self.position = vehicle_pos + offset_world

            # Add shake based on speed
            speed = Vector(vehicle_velocity).length
            shake_amount = min(speed / 50, 1.0) * self.config.shake_intensity

            shake = Vector((
                random.uniform(-1, 1) * shake_amount * 0.1,
                random.uniform(-1, 1) * shake_amount * 0.1,
                random.uniform(-1, 1) * shake_amount * 0.05
            ))
            self.position += shake

            # Update Blender camera
            if self.blender_camera:
                self.blender_camera.location = self.position

                # Look forward
                forward = Vector((
                    math.cos(vehicle_rotation),
                    math.sin(vehicle_rotation),
                    0
                ))
                self.blender_camera.rotation_euler = forward.to_track_quat(
                    '-Z', 'Y'
                ).to_euler()


class StaticCamera:
    """
    Fixed position camera for passing shots.

    Supports:
    - Corner shots
    - Overpass shots
    - Building-mounted cameras
    """

    def __init__(
        self,
        config: CameraConfig,
        world_position: Tuple[float, float, float],
        look_direction: Optional[Tuple[float, float, float]] = None
    ):
        self.config = config
        self.world_position = world_position
        self.look_direction = look_direction
        self.blender_camera: Optional[Any] = None

        self._create_blender_camera()

    def _create_blender_camera(self) -> None:
        """Create Blender camera object."""
        if not BLENDER_AVAILABLE:
            return

        cam_data = bpy.data.cameras.new(f"{self.config.name}_data")
        cam_data.lens = self.config.focal_length
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = self.config.f_stop

        self.blender_camera = bpy.data.objects.new(self.config.name, cam_data)
        self.blender_camera.location = self.world_position
        bpy.context.collection.objects.link(self.blender_camera)

    def update(self, target_position: Tuple[float, float, float]) -> None:
        """Update static camera to track target."""
        if not BLENDER_AVAILABLE or not self.blender_camera:
            return

        if Vector:
            if self.look_direction:
                # Fixed direction
                direction = Vector(self.look_direction).normalized()
            else:
                # Track target
                direction = (
                    Vector(target_position) - Vector(self.world_position)
                ).normalized()

            self.blender_camera.rotation_euler = direction.to_track_quat(
                '-Z', 'Y'
            ).to_euler()


class ChaseCameraSystem:
    """
    Complete camera system for chase sequences.

    Manages:
    - Multiple cameras
    - Auto-switching
    - Trigger-based cuts
    - Coverage planning
    """

    def __init__(self, chase_director: Any):
        self.chase_director = chase_director
        self.cameras: Dict[str, Any] = {}
        self.active_camera: Optional[str] = None
        self.auto_switch = True
        self.switch_interval = 3.0  # seconds

        self._switch_timer = 0.0
        self._camera_sequence: List[str] = []

    def add_camera(
        self,
        camera_type: str,
        config: Optional[CameraConfig] = None,
        position: Optional[Tuple[float, float, float]] = None
    ) -> str:
        """Add a camera to the system."""
        camera_id = f"cam_{len(self.cameras)}"

        if config is None:
            # Use default preset for type
            preset_map = {
                "follow": "follow_close",
                "aerial": "aerial_tracking",
                "in_car": "in_car_driver",
                "static": "static_corner",
                "orbit": "aerial_orbit",
            }
            preset = preset_map.get(camera_type, "follow_close")
            config = CAMERA_PRESETS.get(preset, CameraConfig(
                name=camera_id,
                camera_type=CameraType[camera_type.upper()]
            ))

        # Create camera instance
        if config.camera_type == CameraType.FOLLOW:
            camera = FollowCamera(config)
        elif config.camera_type == CameraType.AERIAL:
            camera = AerialCamera(config)
        elif config.camera_type == CameraType.IN_CAR:
            camera = InCarCamera(config)
        elif config.camera_type == CameraType.STATIC:
            camera = StaticCamera(config, position or (0, 0, 5))
        elif config.camera_type == CameraType.ORBIT:
            camera = AerialCamera(config)
        else:
            camera = FollowCamera(config)

        self.cameras[camera_id] = camera

        if self.active_camera is None:
            self.active_camera = camera_id

        return camera_id

    def update(self, delta_time: float) -> None:
        """Update all cameras."""
        # Get chase state
        state = self.chase_director.get_state()
        hero_pos = state["hero_position"]
        hero_vel = (0, 0, 0)  # Would calculate from progress

        # Update all cameras
        for cam_id, camera in self.cameras.items():
            if isinstance(camera, (FollowCamera, AerialCamera)):
                camera.update(hero_pos, hero_vel, delta_time)
            elif isinstance(camera, InCarCamera):
                # Get vehicle rotation
                camera.update(hero_pos, 0, hero_vel, delta_time)
            elif isinstance(camera, StaticCamera):
                camera.update(hero_pos)

        # Auto-switch cameras
        if self.auto_switch and len(self.cameras) > 1:
            self._switch_timer += delta_time

            if self._switch_timer >= self.switch_interval:
                self._switch_timer = 0.0
                self._auto_switch()

    def _auto_switch(self) -> None:
        """Switch to next camera in sequence."""
        if not self.cameras:
            return

        cam_ids = list(self.cameras.keys())
        current_idx = cam_ids.index(self.active_camera) if self.active_camera in cam_ids else -1
        next_idx = (current_idx + 1) % len(cam_ids)

        self.active_camera = cam_ids[next_idx]

    def switch_to_camera(self, camera_id: str) -> bool:
        """Switch to a specific camera."""
        if camera_id in self.cameras:
            self.active_camera = camera_id
            return True
        return False

    def get_active_camera(self) -> Optional[Any]:
        """Get the currently active camera object."""
        if self.active_camera and self.active_camera in self.cameras:
            return self.cameras[self.active_camera].blender_camera
        return None

    def set_active_as_scene_camera(self) -> None:
        """Set active camera as scene render camera."""
        if not BLENDER_AVAILABLE:
            return

        cam = self.get_active_camera()
        if cam:
            bpy.context.scene.camera = cam


def setup_chase_cameras(
    chase_director: Any,
    types: List[str] = ["follow", "aerial", "in_car", "static"],
    auto_switch: bool = True,
    switch_interval: float = 3.0
) -> ChaseCameraSystem:
    """
    Setup cameras for a chase sequence.

    Args:
        chase_director: ChaseDirector instance
        types: Camera types to create
        auto_switch: Enable automatic camera switching
        switch_interval: Time between switches in seconds

    Returns:
        Configured ChaseCameraSystem
    """
    system = ChaseCameraSystem(chase_director)
    system.auto_switch = auto_switch
    system.switch_interval = switch_interval

    # Get route for static camera placement
    route = chase_director.path_planner.main_route

    for cam_type in types:
        if cam_type == "follow":
            # Add multiple follow cameras
            system.add_camera("follow", CAMERA_PRESETS["follow_close"])
            system.add_camera("follow", CAMERA_PRESETS["follow_wide"])
            system.add_camera("follow", CAMERA_PRESETS["follow_low"])

        elif cam_type == "aerial":
            # Add aerial cameras
            system.add_camera("aerial", CAMERA_PRESETS["aerial_high"])
            system.add_camera("aerial", CAMERA_PRESETS["aerial_tracking"])
            system.add_camera("orbit", CAMERA_PRESETS["aerial_orbit"])

        elif cam_type == "in_car":
            # Add in-car cameras
            system.add_camera("in_car", CAMERA_PRESETS["in_car_driver"])
            system.add_camera("in_car", CAMERA_PRESETS["in_car_dash"])

        elif cam_type == "static":
            # Add static cameras along route
            if route:
                # Place at 25%, 50%, 75% of route
                for progress in [0.25, 0.5, 0.75]:
                    idx = int(len(route) * progress)
                    if idx < len(route):
                        pos = route[idx]
                        # Offset to side of road
                        system.add_camera(
                            "static",
                            CameraConfig(
                                name=f"Static_{int(progress*100)}",
                                camera_type=CameraType.STATIC,
                                focal_length=50.0,
                            ),
                            position=(pos[0] + 20, pos[1] + 20, pos[2] + 3)
                        )

    return system
