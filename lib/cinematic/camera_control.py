"""
Unified Camera Control Module

Consolidates all camera operations into a single, easy-to-use API.
Provides complete control over camera features: creation, zoom, focus,
path following, shake, and procedural animation.

Usage:
    from lib.cinematic.camera_control import CameraController

    # Create controller
    ctrl = CameraController("hero_camera")

    # Camera settings
    ctrl.set_lens(85.0)                    # Focal length
    ctrl.set_aperture(2.8)                 # F-stop
    ctrl.focus_at((0, 0, 1.5))             # Focus distance
    ctrl.set_camera_type("perspective")    # or "ortho"

    # Animation
    ctrl.zoom_to(50.0, start_frame=1, end_frame=60)      # Animated zoom
    ctrl.focus_pull(10.0, start_frame=1, end_frame=120) # Focus pull
    ctrl.follow_path("camera_path_curve")                # Path follow

    # Effects
    ctrl.add_shake(intensity=0.3, frequency=2.0)         # Camera shake
    ctrl.add_handheld(amount=0.1)                         # Handheld feel

    # Rig control
    ctrl.set_rig("crane")                  # Camera rig type
    ctrl.look_at("target_object")          # Track to target
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any, List, Tuple, Dict, Callable
from enum import Enum
import math
import random

# Guarded bpy import
try:
    import bpy
    from mathutils import Vector, Euler, Quaternion
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    Vector = None
    Euler = None
    Quaternion = None
    BLENDER_AVAILABLE = False


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class CameraType(Enum):
    """Camera projection types."""
    PERSPECTIVE = "PERSP"
    ORTHOGRAPHIC = "ORTHO"
    PANORAMA = "PANO"


class RigType(Enum):
    """Camera rig types."""
    FREE = "free"
    TRIPOD = "tripod"
    TRIPOD_ORBIT = "tripod_orbit"
    DOLLY = "dolly"
    DOLLY_CURVED = "dolly_curved"
    CRANE = "crane"
    STEADICAM = "steadicam"
    DRONE = "drone"
    HANDHELD = "handheld"


class ShakeProfile(Enum):
    """Camera shake profiles."""
    SUBTLE = "subtle"
    HANDHELD = "handheld"
    RUN_AND_GUN = "run_and_gun"
    EARTHQUAKE = "earthquake"
    VEHICLE = "vehicle"
    EXPLOSION = "explosion"


@dataclass
class ShakeConfig:
    """Camera shake configuration."""
    profile: ShakeProfile = ShakeProfile.SUBTLE
    intensity: float = 0.1  # meters
    rotation_intensity: float = 0.5  # degrees
    frequency: float = 2.0  # Hz
    translation_axes: Tuple[bool, bool, bool] = (True, True, True)
    rotation_axes: Tuple[bool, bool, bool] = (True, True, False)
    noise_seed: int = 0
    frequency_variation: float = 0.1
    envelope: Tuple[float, float] = (0.0, 1.0)  # Attack, release


@dataclass
class ZoomConfig:
    """Zoom animation configuration."""
    start_focal_length: float
    end_focal_length: float
    start_frame: int
    end_frame: int
    easing: str = "LINEAR"  # LINEAR, EASE_IN, EASE_OUT, EASE_IN_OUT


@dataclass
class FocusPullConfig:
    """Focus pull animation configuration."""
    start_distance: float
    end_distance: float
    start_frame: int
    end_frame: int
    easing: str = "LINEAR"


@dataclass
class CameraState:
    """Snapshot of camera state."""
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float]
    focal_length: float
    focus_distance: float
    f_stop: float
    camera_type: CameraType


# =============================================================================
# SHAKE PROFILES
# =============================================================================

SHAKE_PROFILES: Dict[ShakeProfile, ShakeConfig] = {
    ShakeProfile.SUBTLE: ShakeConfig(
        profile=ShakeProfile.SUBTLE,
        intensity=0.005,
        rotation_intensity=0.1,
        frequency=1.5,
    ),
    ShakeProfile.HANDHELD: ShakeConfig(
        profile=ShakeProfile.HANDHELD,
        intensity=0.02,
        rotation_intensity=0.5,
        frequency=2.0,
    ),
    ShakeProfile.RUN_AND_GUN: ShakeConfig(
        profile=ShakeProfile.RUN_AND_GUN,
        intensity=0.05,
        rotation_intensity=1.5,
        frequency=3.0,
    ),
    ShakeProfile.EARTHQUAKE: ShakeConfig(
        profile=ShakeProfile.EARTHQUAKE,
        intensity=0.15,
        rotation_intensity=3.0,
        frequency=1.0,
        translation_axes=(True, True, True),
        rotation_axes=(True, True, True),
    ),
    ShakeProfile.VEHICLE: ShakeConfig(
        profile=ShakeProfile.VEHICLE,
        intensity=0.03,
        rotation_intensity=0.8,
        frequency=4.0,
        translation_axes=(True, True, False),  # Mostly X/Y
        rotation_axes=(True, False, True),
    ),
    ShakeProfile.EXPLOSION: ShakeConfig(
        profile=ShakeProfile.EXPLOSION,
        intensity=0.2,
        rotation_intensity=5.0,
        frequency=8.0,
        envelope=(0.0, 0.3),  # Quick attack, slower decay
    ),
}


# =============================================================================
# MAIN CAMERA CONTROLLER
# =============================================================================

class CameraController:
    """
    Unified camera control interface.

    Provides complete control over all camera features through a single,
    chainable API. Wraps existing camera.py, rigs.py, motion_path.py,
    and adds new functionality.

    Example:
        ctrl = CameraController("MainCamera")
        ctrl.set_lens(50).set_aperture(2.8).focus_at(5)
        ctrl.zoom_to(85, 1, 60)
        ctrl.add_handheld(0.1)
    """

    def __init__(self, camera_name: str):
        """
        Initialize controller for a camera.

        Args:
            camera_name: Name of existing camera or name for new camera
        """
        self.camera_name = camera_name
        self._shake_fcurves: List[Any] = []
        self._shake_drivers: List[Any] = []
        self._noise_modifiers: List[Any] = []

    @property
    def camera(self) -> Optional[Any]:
        """Get the camera object."""
        if not BLENDER_AVAILABLE:
            return None
        return bpy.data.objects.get(self.camera_name)

    @property
    def camera_data(self) -> Optional[Any]:
        """Get the camera data."""
        cam = self.camera
        if cam and hasattr(cam, "data") and cam.data:
            return cam.data
        return None

    @property
    def position(self) -> Tuple[float, float, float]:
        """Get camera world position."""
        cam = self.camera
        if cam:
            return tuple(cam.location)
        return (0.0, 0.0, 0.0)

    @property
    def rotation(self) -> Tuple[float, float, float]:
        """Get camera rotation (euler)."""
        cam = self.camera
        if cam:
            return tuple(cam.rotation_euler)
        return (0.0, 0.0, 0.0)

    # =========================================================================
    # CREATION AND BASIC SETUP
    # =========================================================================

    @classmethod
    def create(
        cls,
        name: str,
        position: Tuple[float, float, float] = (0, -5, 1.5),
        rotation: Tuple[float, float, float] = (1.57, 0, 0),
        focal_length: float = 50.0,
        camera_type: CameraType = CameraType.PERSPECTIVE,
        set_active: bool = True,
    ) -> "CameraController":
        """
        Create a new camera and return controller.

        Args:
            name: Camera name
            position: World position (x, y, z)
            rotation: Euler rotation in radians (x, y, z)
            focal_length: Lens focal length in mm
            camera_type: Perspective, ortho, or panorama
            set_active: Set as scene active camera

        Returns:
            CameraController instance
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender not available")

        # Create camera data
        cam_data = bpy.data.cameras.new(name=name)
        cam_data.lens = focal_length
        cam_data.type = camera_type.value

        # Create object
        cam_obj = bpy.data.objects.new(name, cam_data)
        cam_obj.location = position
        cam_obj.rotation_euler = rotation

        # Link to scene
        bpy.context.scene.collection.objects.link(cam_obj)

        if set_active:
            bpy.context.scene.camera = cam_obj

        return cls(name)

    @classmethod
    def get_or_create(cls, name: str, **kwargs) -> "CameraController":
        """Get existing camera or create new one."""
        if BLENDER_AVAILABLE and name in bpy.data.objects:
            return cls(name)
        return cls.create(name, **kwargs)

    # =========================================================================
    # LENS AND SENSOR CONTROLS
    # =========================================================================

    def set_lens(self, focal_length: float) -> "CameraController":
        """
        Set focal length (zoom).

        Args:
            focal_length: Lens focal length in mm

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if cam_data:
            cam_data.lens = focal_length
        return self

    def set_aperture(self, f_stop: float) -> "CameraController":
        """
        Set aperture (f-stop).

        Args:
            f_stop: Aperture value (e.g., 2.8, 5.6, 11)

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if cam_data and hasattr(cam_data, "dof"):
            cam_data.dof.aperture_fstop = f_stop
        return self

    def set_sensor(self, width: float, height: float = None) -> "CameraController":
        """
        Set sensor dimensions.

        Args:
            width: Sensor width in mm
            height: Sensor height in mm (defaults to 2/3 of width)

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if cam_data:
            cam_data.sensor_width = width
            if height:
                cam_data.sensor_height = height
        return self

    def get_fov(self) -> float:
        """Get horizontal field of view in degrees."""
        cam_data = self.camera_data
        if cam_data:
            # FOV = 2 * arctan(sensor_width / (2 * focal_length))
            fov_rad = 2 * math.atan(cam_data.sensor_width / (2 * cam_data.lens))
            return math.degrees(fov_rad)
        return 0.0

    def set_fov(self, fov_degrees: float) -> "CameraController":
        """
        Set field of view by adjusting focal length.

        Args:
            fov_degrees: Horizontal FOV in degrees

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if cam_data:
            # focal_length = sensor_width / (2 * tan(fov / 2))
            fov_rad = math.radians(fov_degrees)
            cam_data.lens = cam_data.sensor_width / (2 * math.tan(fov_rad / 2))
        return self

    # =========================================================================
    # CAMERA TYPE
    # =========================================================================

    def set_camera_type(self, camera_type: CameraType) -> "CameraController":
        """
        Set camera projection type.

        Args:
            camera_type: PERSPECTIVE, ORTHOGRAPHIC, or PANORAMA

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if cam_data:
            cam_data.type = camera_type.value
        return self

    def set_perspective(self) -> "CameraController":
        """Set to perspective projection."""
        return self.set_camera_type(CameraType.PERSPECTIVE)

    def set_ortho(self, scale: float = 1.0) -> "CameraController":
        """
        Set to orthographic projection.

        Args:
            scale: Orthographic scale factor

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if cam_data:
            cam_data.type = CameraType.ORTHOGRAPHIC.value
            cam_data.ortho_scale = scale
        return self

    # =========================================================================
    # FOCUS CONTROL
    # =========================================================================

    def enable_dof(self, enabled: bool = True) -> "CameraController":
        """Enable or disable depth of field."""
        cam_data = self.camera_data
        if cam_data and hasattr(cam_data, "dof"):
            cam_data.dof.use_dof = enabled
        return self

    def focus_at(self, target: Any) -> "CameraController":
        """
        Set focus distance to a point or object.

        Args:
            target: (x, y, z) tuple or object name

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if not cam_data or not hasattr(cam_data, "dof"):
            return self

        cam_data.dof.use_dof = True

        if isinstance(target, str):
            # Object name
            obj = bpy.data.objects.get(target)
            if obj:
                dist = self._distance_to(obj.location)
                cam_data.dof.focus_distance = dist
        elif isinstance(target, (tuple, list)) and len(target) == 3:
            # Position tuple
            dist = self._distance_to(target)
            cam_data.dof.focus_distance = dist
        elif isinstance(target, (int, float)):
            # Direct distance value
            cam_data.dof.focus_distance = target

        return self

    def focus_on_object(self, object_name: str) -> "CameraController":
        """Set focus to track an object."""
        cam_data = self.camera_data
        cam_obj = self.camera

        if cam_data and cam_obj:
            cam_data.dof.use_dof = True

            # Set focus object
            target_obj = bpy.data.objects.get(object_name)
            if target_obj:
                cam_data.dof.focus_object = target_obj

        return self

    def set_aperture_blades(self, blades: int) -> "CameraController":
        """
        Set aperture blade count for bokeh shape.

        Args:
            blades: Number of blades (0 = circular, 6 = hexagonal, 8 = octagonal)

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if cam_data and hasattr(cam_data, "dof"):
            cam_data.dof.aperture_blades = blades
        return self

    def set_bokeh_shape(self, shape: str) -> "CameraController":
        """
        Set bokeh shape by name.

        Args:
            shape: "circular", "hexagonal", "octagonal", "rounded"

        Returns:
            self for chaining
        """
        shape_map = {
            "circular": 0,
            "hexagonal": 6,
            "octagonal": 8,
            "rounded": 9,
        }
        blades = shape_map.get(shape.lower(), 0)
        return self.set_aperture_blades(blades)

    # =========================================================================
    # ZOOM ANIMATION
    # =========================================================================

    def zoom_to(
        self,
        target_focal_length: float,
        start_frame: int,
        end_frame: int,
        easing: str = "LINEAR",
    ) -> "CameraController":
        """
        Animate focal length change (zoom).

        Args:
            target_focal_length: Target lens mm
            start_frame: Animation start frame
            end_frame: Animation end frame
            easing: Interpolation type

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if not cam_data:
            return self

        # Set start keyframe
        cam_data.keyframe_insert(data_path="lens", frame=start_frame)

        # Set target
        cam_data.lens = target_focal_length
        cam_data.keyframe_insert(data_path="lens", frame=end_frame)

        # Set interpolation
        if BLENDER_AVAILABLE and hasattr(bpy.context, "scene"):
            fcurves = cam_data.animation_data.action.fcurves
            for fc in fcurves:
                if fc.data_path == "lens":
                    for kp in fc.keyframe_points:
                        kp.interpolation = easing

        return self

    def zoom_by_factor(
        self,
        factor: float,
        start_frame: int,
        end_frame: int,
        easing: str = "LINEAR",
    ) -> "CameraController":
        """
        Zoom by a multiplier factor.

        Args:
            factor: Zoom multiplier (2.0 = 2x zoom in)
            start_frame: Start frame
            end_frame: End frame
            easing: Interpolation type

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if cam_data:
            target = cam_data.lens * factor
            return self.zoom_to(target, start_frame, end_frame, easing)
        return self

    def dolly_zoom(
        self,
        target_distance: float,
        target_fov: float,
        start_frame: int,
        end_frame: int,
    ) -> "CameraController":
        """
        Perform dolly zoom (Vertigo effect).

        Camera moves while zooming to keep subject size constant.
        Background appears to stretch/compress.

        Args:
            target_distance: Target camera-subject distance
            target_fov: Target field of view in degrees
            start_frame: Start frame
            end_frame: End frame

        Returns:
            self for chaining
        """
        cam = self.camera
        if not cam:
            return self

        # Get current position and look direction
        current_pos = cam.location
        # Assume looking at origin for simplicity
        direction = Vector((0, 0, 0)) - Vector(current_pos)
        direction.normalize()

        # Calculate start and end positions
        start_dist = direction.length
        end_pos = Vector(current_pos) + direction * (target_distance - start_dist)

        # Animate position
        cam.keyframe_insert(data_path="location", frame=start_frame)
        cam.location = tuple(end_pos)
        cam.keyframe_insert(data_path="location", frame=end_frame)

        # Animate FOV
        self.set_fov(target_fov)
        # The FOV animation is done via focal length keyframes

        return self

    # =========================================================================
    # FOCUS PULL ANIMATION
    # =========================================================================

    def focus_pull(
        self,
        target_distance: float,
        start_frame: int,
        end_frame: int,
        easing: str = "LINEAR",
    ) -> "CameraController":
        """
        Animate focus distance change (rack focus).

        Args:
            target_distance: Target focus distance in meters
            start_frame: Start frame
            end_frame: End frame
            easing: Interpolation type

        Returns:
            self for chaining
        """
        cam_data = self.camera_data
        if not cam_data or not hasattr(cam_data, "dof"):
            return self

        cam_data.dof.use_dof = True

        # Clear focus object (use distance)
        cam_data.dof.focus_object = None

        # Set start keyframe
        cam_data.dof.keyframe_insert(data_path="focus_distance", frame=start_frame)

        # Set target
        cam_data.dof.focus_distance = target_distance
        cam_data.dof.keyframe_insert(data_path="focus_distance", frame=end_frame)

        # Set interpolation
        if BLENDER_AVAILABLE and hasattr(cam_data, "animation_data") and cam_data.animation_data:
            fcurves = cam_data.animation_data.action.fcurves
            for fc in fcurves:
                if fc.data_path == "dof.focus_distance":
                    for kp in fc.keyframe_points:
                        kp.interpolation = easing

        return self

    def focus_pull_to_object(
        self,
        object_name: str,
        start_frame: int,
        end_frame: int,
        easing: str = "LINEAR",
    ) -> "CameraController":
        """
        Rack focus from current distance to an object.

        Args:
            object_name: Target object to focus on
            start_frame: Start frame
            end_frame: End frame
            easing: Interpolation type

        Returns:
            self for chaining
        """
        obj = bpy.data.objects.get(object_name) if BLENDER_AVAILABLE else None
        if obj:
            target_dist = self._distance_to(obj.location)
            return self.focus_pull(target_dist, start_frame, end_frame, easing)
        return self

    # =========================================================================
    # PATH FOLLOWING
    # =========================================================================

    def follow_path(
        self,
        curve_name: str,
        duration_frames: int = 120,
        follow_curve: bool = True,
        start_frame: int = 1,
    ) -> "CameraController":
        """
        Make camera follow a curve path.

        Args:
            curve_name: Name of curve object to follow
            duration_frames: Duration of path traversal
            follow_curve: Camera rotates to follow curve direction
            start_frame: Starting frame

        Returns:
            self for chaining
        """
        cam = self.camera
        if not cam or not BLENDER_AVAILABLE:
            return self

        curve_obj = bpy.data.objects.get(curve_name)
        if not curve_obj:
            return self

        # Add Follow Path constraint
        constraint = cam.constraints.new(type="FOLLOW_PATH")
        constraint.target = curve_obj
        constraint.use_curve_follow = follow_curve
        constraint.forward_axis = "TRACK_NEGATIVE_Z"
        constraint.up_axis = "UP_Y"

        # Set path duration
        curve_obj.data.path_duration = duration_frames
        curve_obj.data.use_path = True

        # Animate evaluation time
        curve_obj.data.eval_time = 0
        curve_obj.data.keyframe_insert(data_path="eval_time", frame=start_frame)

        curve_obj.data.eval_time = duration_frames
        curve_obj.data.keyframe_insert(data_path="eval_time", frame=start_frame + duration_frames)

        return self

    def orbit_around(
        self,
        center: Tuple[float, float, float],
        radius: float,
        start_angle: float = 0,
        end_angle: float = 360,
        height: float = 0,
        duration_frames: int = 120,
        start_frame: int = 1,
    ) -> "CameraController":
        """
        Create orbit animation around a point.

        Args:
            center: Center point to orbit around
            radius: Orbit radius
            start_angle: Starting angle in degrees
            end_angle: Ending angle in degrees
            height: Height offset from center
            duration_frames: Duration in frames
            start_frame: Starting frame

        Returns:
            self for chaining
        """
        cam = self.camera
        if not cam or not BLENDER_AVAILABLE:
            return self

        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)

        # Create path curve
        points = []
        segments = 64
        for i in range(segments + 1):
            t = i / segments
            angle = start_rad + (end_rad - start_rad) * t
            x = center[0] + radius * math.sin(angle)
            y = center[1] - radius * math.cos(angle)
            z = center[2] + height
            points.append((x, y, z))

        # Create curve
        curve_data = bpy.data.curves.new(f"{self.camera_name}_orbit_path", type="CURVE")
        curve_data.dimensions = "3D"

        spline = curve_data.splines.new(type="BEZIER")
        spline.bezier_points.add(len(points) - 1)

        for i, pt in enumerate(points):
            bp = spline.bezier_points[i]
            bp.co = pt
            bp.handle_type_left = "AUTO"
            bp.handle_type_right = "AUTO"

        curve_obj = bpy.data.objects.new(f"{self.camera_name}_orbit_path", curve_data)
        bpy.context.scene.collection.objects.link(curve_obj)

        # Follow the path
        self.follow_path(curve_obj.name, duration_frames, True, start_frame)

        # Look at center
        self.look_at(center)

        return self

    # =========================================================================
    # RIG CONTROL
    # =========================================================================

    def set_rig(self, rig_type: RigType, target_name: str = None) -> "CameraController":
        """
        Set up camera rig.

        Args:
            rig_type: Type of camera rig
            target_name: Target object for tracking (if applicable)

        Returns:
            self for chaining
        """
        cam = self.camera
        if not cam or not BLENDER_AVAILABLE:
            return self

        # Clear existing constraints
        for c in list(cam.constraints):
            cam.constraints.remove(c)

        if rig_type == RigType.FREE:
            # No constraints
            pass

        elif rig_type == RigType.TRIPOD:
            cam.lock_location = (True, True, True)
            if target_name:
                self.look_at(target_name)

        elif rig_type == RigType.DOLLY:
            cam.lock_location = (False, True, True)
            if target_name:
                self.look_at(target_name)

        elif rig_type == RigType.CRANE:
            cam.lock_location = (False, False, True)
            if target_name:
                self.look_at(target_name)
            # Add rotation limits
            limit = cam.constraints.new(type="LIMIT_ROTATION")
            limit.use_limit_x = True
            limit.use_limit_y = True
            limit.min_x = -math.pi / 4
            limit.max_x = math.pi / 4
            limit.min_y = -math.pi / 6
            limit.max_y = math.pi / 6

        elif rig_type == RigType.STEADICAM:
            if target_name:
                target = bpy.data.objects.get(target_name)
                if target:
                    copy_loc = cam.constraints.new(type="COPY_LOCATION")
                    copy_loc.target = target
                    copy_loc.use_offset = True
                    copy_loc.influence = 0.8
                    self.look_at(target_name)

        elif rig_type == RigType.DRONE:
            if target_name:
                self.look_at(target_name)
                # Lower influence for floating feel
                for c in cam.constraints:
                    if c.type == "TRACK_TO":
                        c.influence = 0.5

        return self

    def look_at(self, target: Any) -> "CameraController":
        """
        Point camera at a target.

        Args:
            target: (x, y, z) tuple or object name

        Returns:
            self for chaining
        """
        cam = self.camera
        if not cam or not BLENDER_AVAILABLE:
            return self

        # Remove existing track constraint
        for c in list(cam.constraints):
            if c.type == "TRACK_TO":
                cam.constraints.remove(c)

        track = cam.constraints.new(type="TRACK_TO")
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"

        if isinstance(target, str):
            obj = bpy.data.objects.get(target)
            if obj:
                track.target = obj
        elif isinstance(target, (tuple, list)) and len(target) == 3:
            # Create empty at position
            empty = bpy.data.objects.new(f"{self.camera_name}_target", None)
            empty.location = target
            bpy.context.scene.collection.objects.link(empty)
            track.target = empty

        return self

    # =========================================================================
    # CAMERA SHAKE
    # =========================================================================

    def add_shake(
        self,
        intensity: float = 0.1,
        frequency: float = 2.0,
        rotation_intensity: float = 0.5,
        seed: int = 0,
    ) -> "CameraController":
        """
        Add procedural camera shake.

        Args:
            intensity: Translation intensity in meters
            frequency: Shake frequency in Hz
            rotation_intensity: Rotation intensity in degrees
            seed: Random seed for reproducibility

        Returns:
            self for chaining
        """
        cam = self.camera
        if not cam or not BLENDER_AVAILABLE:
            return self

        # Add noise modifiers to location fcurves if animated
        # If not animated, we need to create animation first
        scene = bpy.context.scene

        # Create keyframes at start and end of scene
        start = scene.frame_start
        end = scene.frame_end

        for i in range(3):  # X, Y, Z
            cam.keyframe_insert(data_path="location", index=i, frame=start)
            cam.keyframe_insert(data_path="location", index=i, frame=end)

        # Add noise modifiers
        action = cam.animation_data.action
        for fc in action.fcurves:
            if fc.data_path == "location":
                mod = fc.modifiers.new(type="NOISE")
                mod.strength = intensity
                mod.scale = 60 / frequency  # Convert Hz to frame scale
                mod.phase = seed * (fc.array_index + 1) * 137.5  # Golden angle for variety
                self._noise_modifiers.append(mod)

        # Add rotation shake
        for i in range(3):
            cam.keyframe_insert(data_path="rotation_euler", index=i, frame=start)
            cam.keyframe_insert(data_path="rotation_euler", index=i, frame=end)

        for fc in action.fcurves:
            if fc.data_path == "rotation_euler":
                mod = fc.modifiers.new(type="NOISE")
                mod.strength = math.radians(rotation_intensity)
                mod.scale = 60 / frequency
                mod.phase = seed * (fc.array_index + 10) * 137.5
                self._noise_modifiers.append(mod)

        return self

    def add_shake_profile(self, profile: ShakeProfile) -> "CameraController":
        """
        Add camera shake using predefined profile.

        Args:
            profile: ShakeProfile enum value

        Returns:
            self for chaining
        """
        config = SHAKE_PROFILES.get(profile, SHAKE_PROFILES[ShakeProfile.SUBTLE])
        return self.add_shake(
            intensity=config.intensity,
            frequency=config.frequency,
            rotation_intensity=config.rotation_intensity,
            seed=config.noise_seed,
        )

    def add_handheld(self, amount: float = 0.1) -> "CameraController":
        """
        Add subtle handheld camera movement.

        Args:
            amount: Intensity multiplier (0.0 to 1.0)

        Returns:
            self for chaining
        """
        config = SHAKE_PROFILES[ShakeProfile.HANDHELD]
        return self.add_shake(
            intensity=config.intensity * amount,
            frequency=config.frequency,
            rotation_intensity=config.rotation_intensity * amount,
        )

    def clear_shake(self) -> "CameraController":
        """Remove all camera shake effects."""
        for mod in self._noise_modifiers:
            try:
                # Remove modifier from fcurve
                if mod in list(mod.id_data.modifiers):
                    mod.id_data.modifiers.remove(mod)
            except Exception:
                pass
        self._noise_modifiers.clear()
        return self

    # =========================================================================
    # TRANSFORM HELPERS
    # =========================================================================

    def move_to(self, position: Tuple[float, float, float]) -> "CameraController":
        """Set camera position."""
        cam = self.camera
        if cam:
            cam.location = position
        return self

    def rotate_to(self, rotation: Tuple[float, float, float]) -> "CameraController":
        """Set camera rotation (euler radians)."""
        cam = self.camera
        if cam:
            cam.rotation_euler = rotation
        return self

    def point_at(self, target: Tuple[float, float, float]) -> "CameraController":
        """
        Calculate and set rotation to point at target (without constraint).

        Args:
            target: (x, y, z) world position

        Returns:
            self for chaining
        """
        cam = self.camera
        if not cam:
            return self

        direction = Vector(target) - Vector(cam.location)
        direction.normalize()

        # Calculate rotation
        # Assuming -Z is forward, Y is up
        up = Vector((0, 0, 1))
        right = direction.cross(up)
        right.normalize()
        up = right.cross(direction)

        # Build rotation matrix and convert to euler
        # This is simplified - use look_at for full solution
        rot_quat = direction.to_track_quat("-Z", "Y")
        cam.rotation_euler = rot_quat.to_euler()

        return self

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def get_state(self) -> Optional[CameraState]:
        """Capture current camera state."""
        cam = self.camera
        cam_data = self.camera_data
        if not cam or not cam_data:
            return None

        return CameraState(
            position=tuple(cam.location),
            rotation=tuple(cam.rotation_euler),
            focal_length=cam_data.lens,
            focus_distance=cam_data.dof.focus_distance if hasattr(cam_data, "dof") else 0,
            f_stop=cam_data.dof.aperture_fstop if hasattr(cam_data, "dof") else 0,
            camera_type=CameraType(cam_data.type),
        )

    def restore_state(self, state: CameraState) -> "CameraController":
        """Restore camera to saved state."""
        cam = self.camera
        cam_data = self.camera_data
        if not cam or not cam_data:
            return self

        cam.location = state.position
        cam.rotation_euler = state.rotation
        cam_data.lens = state.focal_length

        if hasattr(cam_data, "dof"):
            cam_data.dof.focus_distance = state.focus_distance
            cam_data.dof.aperture_fstop = state.f_stop

        cam_data.type = state.camera_type.value

        return self

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _distance_to(self, point: Tuple[float, float, float]) -> float:
        """Calculate distance from camera to point."""
        pos = self.position
        dx = point[0] - pos[0]
        dy = point[1] - pos[1]
        dz = point[2] - pos[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def set_active(self) -> "CameraController":
        """Set this camera as the active scene camera."""
        if BLENDER_AVAILABLE and self.camera:
            bpy.context.scene.camera = self.camera
        return self

    def delete(self) -> bool:
        """Delete the camera."""
        if not BLENDER_AVAILABLE:
            return False

        cam = self.camera
        if cam:
            # Unlink and delete
            bpy.data.objects.remove(cam, do_unlink=True)
            return True
        return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_camera(
    name: str,
    position: Tuple[float, float, float] = (0, -5, 1.5),
    focal_length: float = 50.0,
    f_stop: float = 2.8,
    focus_distance: float = 5.0,
    **kwargs
) -> CameraController:
    """
    Create a camera with common settings.

    Args:
        name: Camera name
        position: World position
        focal_length: Lens mm
        f_stop: Aperture
        focus_distance: Focus distance

    Returns:
        CameraController instance
    """
    ctrl = CameraController.create(name, position=position, focal_length=focal_length)
    ctrl.set_aperture(f_stop).focus_at(focus_distance).enable_dof()
    return ctrl


def create_ortho_camera(
    name: str,
    position: Tuple[float, float, float] = (0, -10, 10),
    scale: float = 10.0,
    **kwargs
) -> CameraController:
    """
    Create an orthographic camera.

    Args:
        name: Camera name
        position: World position
        scale: Ortho scale

    Returns:
        CameraController instance
    """
    ctrl = CameraController.create(name, position=position)
    ctrl.set_ortho(scale)
    return ctrl


def create_isometric_camera(
    name: str = "isometric_camera",
    distance: float = 10.0,
    target: Tuple[float, float, float] = (0, 0, 0),
) -> CameraController:
    """
    Create an isometric camera setup.

    Args:
        name: Camera name
        distance: Distance from target
        target: Look-at target

    Returns:
        CameraController instance
    """
    # True isometric: 35.264° X rotation, 45° Z rotation
    iso_angle = math.atan(1 / math.sqrt(2))  # ~35.264°
    rotation = (iso_angle, 0, math.pi / 4)

    # Calculate position
    x = target[0] - distance * math.sin(math.pi / 4) * math.cos(iso_angle)
    y = target[1] - distance * math.cos(math.pi / 4) * math.cos(iso_angle)
    z = target[2] + distance * math.sin(iso_angle)

    ctrl = CameraController.create(
        name,
        position=(x, y, z),
        rotation=rotation,
        focal_length=50.0,
    )
    ctrl.set_ortho(scale=distance / 2)
    return ctrl


def create_dolly_zoom(
    camera_name: str,
    start_distance: float,
    end_distance: float,
    start_fov: float,
    end_fov: float,
    frames: int = 120,
) -> CameraController:
    """
    Create a dolly zoom (Vertigo effect) animation.

    Preserves subject size while changing perspective.

    Args:
        camera_name: Name for the camera
        start_distance: Starting camera distance
        end_distance: Ending camera distance
        start_fov: Starting field of view (degrees)
        end_fov: Ending field of view (degrees)
        frames: Animation duration

    Returns:
        CameraController instance
    """
    ctrl = CameraController.create(
        camera_name,
        position=(0, -start_distance, 1.5),
    )
    ctrl.set_fov(start_fov)
    ctrl.dolly_zoom(end_distance, end_fov, 1, frames)
    return ctrl


# =============================================================================
# MULTI-CAMERA HELPERS
# =============================================================================

class MultiCameraController:
    """
    Control multiple cameras simultaneously.

    Example:
        multi = MultiCameraController(["cam1", "cam2", "cam3"])
        multi.set_lens(50).set_aperture(2.8)  # Applies to all
        multi.cut_to("cam2")  # Switch active camera
    """

    def __init__(self, camera_names: List[str]):
        self.camera_names = camera_names
        self._controllers = {
            name: CameraController(name) for name in camera_names
        }
        self._active_index = 0

    def __getitem__(self, name: str) -> CameraController:
        return self._controllers[name]

    @property
    def active(self) -> CameraController:
        """Get currently active camera controller."""
        name = self.camera_names[self._active_index]
        return self._controllers[name]

    def cut_to(self, camera_name: str) -> "MultiCameraController":
        """Switch active camera (cut)."""
        if camera_name in self._controllers:
            self._active_index = self.camera_names.index(camera_name)
            self._controllers[camera_name].set_active()
        return self

    def set_lens(self, focal_length: float) -> "MultiCameraController":
        """Set focal length on all cameras."""
        for ctrl in self._controllers.values():
            ctrl.set_lens(focal_length)
        return self

    def set_aperture(self, f_stop: float) -> "MultiCameraController":
        """Set aperture on all cameras."""
        for ctrl in self._controllers.values():
            ctrl.set_aperture(f_stop)
        return self

    def add_shake_all(self, intensity: float = 0.1, frequency: float = 2.0) -> "MultiCameraController":
        """Add shake to all cameras."""
        for ctrl in self._controllers.values():
            ctrl.add_shake(intensity, frequency)
        return self

    def list_cameras(self) -> List[str]:
        """List all camera names."""
        return self.camera_names.copy()
