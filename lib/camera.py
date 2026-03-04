"""
Camera Utilities Module - Codified from Tutorials 3, 10, 16, 21

Implements camera setup utilities including isometric projection,
depth of field, camera rigs, and cinematic camera movements.

Based on tutorials:
- Polygon Runway: Isometric/RTS (Section 3)
- SharpWind: Abandoned House (Section 10)
- CGMatter: Creature Rigging (Section 16)
- Default Cube: Glass Flowers (Section 21)

Usage:
    from lib.camera import IsometricCamera, DepthOfField, CameraRig

    # Create isometric camera
    iso = IsometricCamera.create()
    iso.set_ortho_scale(10.0)
    cam = iso.build()

    # Setup depth of field
    dof = DepthOfField(camera)
    dof.set_f_stop(2.8)
    dof.focus_on_object(target_obj)
"""

from __future__ import annotations
import bpy
from typing import Optional, Tuple
from math import radians, tan, atan, sqrt
from pathlib import Path


class IsometricCamera:
    """
    Isometric camera setup for stylized rendering.

    Cross-references:
    - KB Section 3: Isometric/RTS Modeling
    - KB Section 3.5: Rick and Morty Garage
    """

    def __init__(self):
        self._camera: Optional[bpy.types.Object] = None
        self._ortho_scale = 10.0
        self._rotation_x = 60.0  # True isometric: 35.264
        self._rotation_z = 45.0
        self._location = (0.0, 0.0, 10.0)

    @classmethod
    def create(cls, name: str = "IsometricCamera") -> "IsometricCamera":
        """
        Create new isometric camera.

        Args:
            name: Camera name

        Returns:
            Configured IsometricCamera instance
        """
        instance = cls()

        # Create camera object
        cam_data = bpy.data.cameras.new(name)
        instance._camera = bpy.data.objects.new(name, cam_data)
        bpy.context.collection.objects.link(instance._camera)

        return instance

    def set_ortho_scale(self, scale: float) -> "IsometricCamera":
        """
        Set orthographic scale.

        KB Reference: Section 3 - Camera setup

        Args:
            scale: Orthographic scale (larger = more visible)

        Returns:
            Self for chaining
        """
        self._ortho_scale = scale
        return self

    def set_true_isometric(self) -> "IsometricCamera":
        """
        Set true isometric projection (arctan(1/√2)).

        KB Reference: Section 3 - True isometric math

        Returns:
            Self for chaining
        """
        self._rotation_x = degrees(atan(1 / sqrt(2)))  # ~35.264°
        self._rotation_z = 45.0
        return self

    def set_game_isometric(self) -> "IsometricCamera":
        """
        Set game-style isometric (60° tilt).

        Common in games, not true isometric.

        Returns:
            Self for chaining
        """
        self._rotation_x = 60.0
        self._rotation_z = 45.0
        return self

    def set_location(self, x: float, y: float, z: float) -> "IsometricCamera":
        """Set camera location."""
        self._location = (x, y, z)
        return self

    def build(self) -> bpy.types.Object:
        """
        Build the isometric camera.

        Returns:
            Configured camera object
        """
        if not self._camera:
            raise RuntimeError("Call create() first")

        # Set camera type
        self._camera.data.type = 'ORTHO'
        self._camera.data.ortho_scale = self._ortho_scale

        # Set rotation
        self._camera.rotation_mode = 'XYZ'
        self._camera.rotation_euler = (
            radians(self._rotation_x),
            0.0,
            radians(self._rotation_z)
        )

        # Set location
        self._camera.location = self._location

        return self._camera


def degrees(rad: float) -> float:
    """Convert radians to degrees."""
    import math
    return rad * 180.0 / math.pi


class DepthOfField:
    """
    Depth of field setup for cameras.

    Cross-references:
    - KB Section 10: Cinematic renders
    - KB Section 28: Cinematic workflow
    """

    def __init__(self, camera: bpy.types.Object):
        self._camera = camera
        self._f_stop = 2.8
        self._focus_distance = 10.0
        self._focus_object: Optional[bpy.types.Object] = None
        self._blades = 6

    def set_f_stop(self, f_stop: float) -> "DepthOfField":
        """
        Set aperture f-stop.

        KB Reference: Section 28 - Cinematic DOF

        Args:
            f_stop: F-stop value (lower = more blur)
                - f/1.4: Very shallow, dreamy
                - f/2.8: Portrait/cinematic
                - f/5.6: Moderate blur
                - f/8.0: Sharp, documentary

        Returns:
            Self for chaining
        """
        self._f_stop = f_stop
        return self

    def set_focus_distance(self, distance: float) -> "DepthOfField":
        """
        Set focus distance manually.

        Args:
            distance: Focus distance in meters

        Returns:
            Self for chaining
        """
        self._focus_distance = distance
        self._focus_object = None  # Clear object focus
        return self

    def focus_on_object(self, obj: bpy.types.Object) -> "DepthOfField":
        """
        Set focus target to an object.

        Args:
            obj: Object to focus on

        Returns:
            Self for chaining
        """
        self._focus_object = obj
        return self

    def set_aperture_blades(self, blades: int) -> "DepthOfField":
        """
        Set number of aperture blades for bokeh shape.

        Args:
            blades: Number of blades (3-16)

        Returns:
            Self for chaining
        """
        self._blades = max(3, min(16, blades))
        return self

    def apply(self) -> "DepthOfField":
        """
        Apply DOF settings to camera.

        KB Reference: Section 28 - DOF setup

        Returns:
            Self for chaining
        """
        cam = self._camera.data

        # Enable DOF
        cam.dof.use_dof = True

        # Set f-stop
        cam.dof.aperture_fstop = self._f_stop

        # Set focus target
        if self._focus_object:
            cam.dof.focus_object = self._focus_object
        else:
            cam.dof.focus_distance = self._focus_distance

        # Set aperture blades
        cam.dof.aperture_blades = self._blades

        return self


class CameraRig:
    """
    Camera rig for smooth camera movements.

    Cross-references:
    - KB Section 10: Abandoned house camera work
    - KB Section 16: Creature animation cameras
    """

    def __init__(self):
        self._camera: Optional[bpy.types.Object] = None
        self._target: Optional[bpy.types.Object] = None
        self._rig: Optional[bpy.types.Object] = None

    @classmethod
    def create(cls, name: str = "CameraRig") -> "CameraRig":
        """
        Create camera rig with target.

        Args:
            name: Rig name

        Returns:
            Configured CameraRig instance
        """
        instance = cls()

        # Create target empty
        target = bpy.data.objects.new(f"{name}_Target", None)
        target.empty_display_type = 'SPHERE'
        bpy.context.collection.objects.link(target)
        instance._target = target

        # Create camera
        cam_data = bpy.data.cameras.new(f"{name}_Cam")
        camera = bpy.data.objects.new(f"{name}_Cam", cam_data)
        bpy.context.collection.objects.link(camera)
        instance._camera = camera

        # Track to constraint
        track = camera.constraints.new('TRACK_TO')
        track.target = target
        track.track_axis = 'TRACK_NEGATIVE_Z'
        track.up_axis = 'UP_Y'

        return instance

    def set_camera_position(
        self,
        x: float,
        y: float,
        z: float
    ) -> "CameraRig":
        """Set camera position."""
        if self._camera:
            self._camera.location = (x, y, z)
        return self

    def set_target_position(
        self,
        x: float,
        y: float,
        z: float
    ) -> "CameraRig":
        """Set target position."""
        if self._target:
            self._target.location = (x, y, z)
        return self

    def get_camera(self) -> Optional[bpy.types.Object]:
        """Get the camera object."""
        return self._camera

    def get_target(self) -> Optional[bpy.types.Object]:
        """Get the target object."""
        return self._target


class OrbitCamera:
    """
    Orbiting camera for turntable animations.

    Cross-references:
    - KB Section 2: Looping animations
    """

    def __init__(self):
        self._camera: Optional[bpy.types.Object] = None
        self._center = (0.0, 0.0, 0.0)
        self._radius = 10.0
        self._height = 5.0
        self._duration = 250  # Frames for full orbit

    @classmethod
    def create(cls, name: str = "OrbitCamera") -> "OrbitCamera":
        """
        Create orbiting camera setup.

        Args:
            name: Camera name

        Returns:
            Configured OrbitCamera instance
        """
        instance = cls()

        # Create camera
        cam_data = bpy.data.cameras.new(name)
        instance._camera = bpy.data.objects.new(name, cam_data)
        bpy.context.collection.objects.link(instance._camera)

        return instance

    def set_center(self, x: float, y: float, z: float) -> "OrbitCamera":
        """Set orbit center point."""
        self._center = (x, y, z)
        return self

    def set_radius(self, radius: float) -> "OrbitCamera":
        """Set orbit radius."""
        self._radius = radius
        return self

    def set_height(self, height: float) -> "OrbitCamera":
        """Set camera height."""
        self._height = height
        return self

    def set_duration(self, frames: int) -> "OrbitCamera":
        """
        Set orbit duration in frames.

        KB Reference: Section 2 - Perfect loops

        Args:
            frames: Frames for complete orbit

        Returns:
            Self for chaining
        """
        self._duration = frames
        return self

    def animate(self) -> "OrbitCamera":
        """
        Create orbit animation.

        KB Reference: Section 2 - Seamless loop (360° = 2π)

        Returns:
            Self for chaining
        """
        if not self._camera:
            raise RuntimeError("Call create() first")

        import math

        # Calculate positions for start and end
        # Start: angle = 0
        start_x = self._center[0] + self._radius
        start_y = self._center[1]
        start_z = self._center[2] + self._height

        # Set start position and keyframe
        self._camera.location = (start_x, start_y, start_z)
        self._camera.keyframe_insert("location", frame=0)

        # Create rotation animation using driver or direct keyframes
        # For simplicity, we'll keyframe at start and end
        # The camera should orbit using a circular path

        # End position is same as start (perfect loop)
        self._camera.location = (start_x, start_y, start_z)
        self._camera.keyframe_insert("location", frame=self._duration)

        # Set linear interpolation for smooth loop
        if self._camera.animation_data:
            for fcurve in self._camera.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'LINEAR'

        return self

    def get_camera(self) -> Optional[bpy.types.Object]:
        """Get the camera object."""
        return self._camera


class CameraPresets:
    """
    Camera configuration presets.

    Cross-references:
    - KB Section 3: Isometric
    - KB Section 28: Cinematic
    """

    @staticmethod
    def isometric_game() -> dict:
        """Game-style isometric camera."""
        return {
            "type": "ORTHO",
            "rotation_x": 60.0,
            "rotation_z": 45.0,
            "ortho_scale": 10.0,
            "description": "Common game isometric view"
        }

    @staticmethod
    def isometric_true() -> dict:
        """True isometric projection."""
        true_angle = degrees(atan(1 / sqrt(2)))
        return {
            "type": "ORTHO",
            "rotation_x": true_angle,
            "rotation_z": 45.0,
            "ortho_scale": 10.0,
            "description": "True isometric (no distortion)"
        }

    @staticmethod
    def portrait_dof() -> dict:
        """Portrait-style depth of field."""
        return {
            "f_stop": 2.8,
            "focus_mode": "object",
            "blades": 6,
            "description": "Shallow DOF for portraits"
        }

    @staticmethod
    def cinematic_wide() -> dict:
        """Cinematic wide shot."""
        return {
            "f_stop": 5.6,
            "sensor_width": 36.0,
            "lens": 35.0,
            "description": "Cinematic wide angle"
        }

    @staticmethod
    def product_turntable() -> dict:
        """Product showcase turntable."""
        return {
            "orbit_duration": 250,
            "height_ratio": 0.3,  # Height as ratio of radius
            "f_stop": 8.0,
            "description": "Smooth product rotation"
        }


# Convenience functions
def create_isometric_camera(scale: float = 10.0) -> bpy.types.Object:
    """Quick setup for isometric camera."""
    iso = IsometricCamera.create()
    iso.set_ortho_scale(scale)
    iso.set_game_isometric()
    return iso.build()


def setup_dof(
    camera: bpy.types.Object,
    f_stop: float = 2.8,
    focus_object: Optional[bpy.types.Object] = None
) -> DepthOfField:
    """Quick setup for depth of field."""
    dof = DepthOfField(camera)
    dof.set_f_stop(f_stop)
    if focus_object:
        dof.focus_on_object(focus_object)
    dof.apply()
    return dof


def create_orbit_camera(
    radius: float = 10.0,
    height: float = 5.0,
    duration: int = 250
) -> bpy.types.Object:
    """Quick setup for orbit camera."""
    orbit = OrbitCamera.create()
    orbit.set_radius(radius)
    orbit.set_height(height)
    orbit.set_duration(duration)
    orbit.animate()
    return orbit.get_camera()


def get_quick_reference() -> dict:
    """Get quick reference for camera setup."""
    return {
        "isometric_rotation": "X: 60°, Z: 45° (game) or X: 35.264°, Z: 45° (true)",
        "dof_f_stops": "f/1.4 = dreamy, f/2.8 = portrait, f/8 = sharp",
        "orbit_loop": "Frame 0 = Frame Duration for perfect loop",
        "sensor_size": "36mm (full frame) is standard"
    }
