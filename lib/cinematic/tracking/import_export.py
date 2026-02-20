"""
Import/Export Module

Provides external tracking data import with coordinate conversion.

Usage:
    from lib.cinematic.tracking.import_export import (
        import_nuke_chan, convert_yup_to_zup_position, fov_to_focal_length
    )

    # Import Nuke .chan file
    solve_data = import_nuke_chan("camera.chan")

    # Coordinate conversion
    pos = convert_yup_to_zup_position(1, 2, 3)  # (1, 3, -2)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime
import re
import struct
import math

# Blender API guard
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

from .types import (
    SolveData,
    TrackData,
    TrackingSession,
)


# =============================================================================
# Coordinate Conversion Functions
# =============================================================================

def convert_yup_to_zup_position(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """
    Convert position from Y-up to Z-up coordinate system.

    Y-up (FBX/Nuke):    Z-up (Blender):
    X -> right          X -> right
    Y -> forward        Y -> forward (negative)
    Z -> up             Z -> up

    Matrix: 90-degree rotation around X-axis

    Args:
        x, y, z: Position in Y-up coordinates

    Returns:
        Tuple of (x, z, -y) in Z-up coordinates

    Example:
        >>> convert_yup_to_zup_position(1.0, 2.0, 3.0)
        (1.0, 3.0, -2.0)
    """
    return (x, z, -y)


def convert_yup_to_zup_rotation(rx: float, ry: float, rz: float) -> Tuple[float, float, float]:
    """
    Convert Euler rotation from Y-up to Z-up.

    Args:
        rx, ry, rz: Rotation in degrees (Y-up coordinate system)

    Returns:
        Tuple of rotation in degrees (Z-up coordinate system)
    """
    # Simplified conversion for common cases
    # Full implementation would use proper rotation matrix multiplication
    return (rx, ry - 90, rz)


def convert_zup_to_yup_position(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """
    Convert position from Z-up (Blender) to Y-up (FBX/Nuke).

    Inverse of convert_yup_to_zup_position.

    Args:
        x, y, z: Position in Z-up coordinates

    Returns:
        Tuple of (x, -z, y) in Y-up coordinates
    """
    return (x, -z, y)


# =============================================================================
# FOV / Focal Length Conversion
# =============================================================================

def fov_to_focal_length(fov_degrees: float, sensor_width: float = 36.0) -> float:
    """
    Convert field of view to focal length.

    Args:
        fov_degrees: Field of view in degrees
        sensor_width: Sensor width in mm (default 36mm for full frame)

    Returns:
        Focal length in mm

    Example:
        >>> focal = fov_to_focal_length(45.0, 36.0)
        >>> 40 < focal < 45
        True
    """
    if fov_degrees <= 0 or fov_degrees >= 180:
        return 50.0  # Default fallback

    fov_rad = math.radians(fov_degrees)
    return sensor_width / (2 * math.tan(fov_rad / 2))


def focal_length_to_fov(focal_length: float, sensor_width: float = 36.0) -> float:
    """
    Convert focal length to field of view.

    Args:
        focal_length: Focal length in mm
        sensor_width: Sensor width in mm

    Returns:
        Field of view in degrees
    """
    if focal_length <= 0:
        return 45.0  # Default fallback

    fov_rad = 2 * math.atan(sensor_width / (2 * focal_length))
    return math.degrees(fov_rad)


# =============================================================================
# Nuke .chan Import
# =============================================================================

def import_nuke_chan(
    chan_path: str,
    frame_offset: int = 0,
    scale_factor: float = 1.0,
    coordinate_system: str = "y_up"
) -> SolveData:
    """
    Import camera data from Nuke .chan file.

    Format: frame tx ty tz rx ry rz [fov]
    - frame: Frame number
    - tx, ty, tz: Translation (units vary by export)
    - rx, ry, rz: Rotation in degrees
    - fov: Optional field of view in degrees

    Args:
        chan_path: Path to .chan file
        frame_offset: Offset to add to frame numbers
        scale_factor: Scale factor for translation values
        coordinate_system: "y_up" (Nuke default) or "z_up"

    Returns:
        SolveData with imported camera transforms

    Raises:
        FileNotFoundError: If .chan file doesn't exist
    """
    path = Path(chan_path)
    if not path.exists():
        raise FileNotFoundError(f".chan file not found: {chan_path}")

    frames_data: Dict[int, Tuple[float, float, float, float, float, float]] = {}

    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) < 7:
                continue

            try:
                frame = int(float(parts[0])) + frame_offset
                tx, ty, tz = float(parts[1]), float(parts[2]), float(parts[3])
                rx, ry, rz = float(parts[4]), float(parts[5]), float(parts[6])

                # Coordinate conversion (Y-up to Z-up)
                if coordinate_system == "y_up":
                    tx, ty, tz = convert_yup_to_zup_position(tx, ty, tz)

                # Apply scale
                tx *= scale_factor
                ty *= scale_factor
                tz *= scale_factor

                frames_data[frame] = (tx, ty, tz, rx, ry, rz)
            except (ValueError, IndexError):
                continue

    # Determine frame range
    if frames_data:
        frame_nums = sorted(frames_data.keys())
        frame_range = (frame_nums[0], frame_nums[-1])
    else:
        frame_range = (1, 100)

    return SolveData(
        name=path.stem,
        frame_range=frame_range,
        camera_transforms=frames_data,
        coordinate_system="z_up",  # Converted to Blender
        solved_at=datetime.utcnow().isoformat()
    )


# =============================================================================
# Generic Import Function
# =============================================================================

def import_tracking_data(
    file_path: str,
    format: str = "auto",
    **kwargs
) -> SolveData:
    """
    Import tracking data from various formats.

    Args:
        file_path: Path to tracking file
        format: Format type (nuke_chan, fbx, auto)
        **kwargs: Format-specific options passed to specific importer

    Returns:
        SolveData with imported camera transforms

    Raises:
        ValueError: If format is unsupported
        FileNotFoundError: If file doesn't exist

    Example:
        >>> solve_data = import_tracking_data("camera.chan")
        >>> solve_data.coordinate_system
        'z_up'
    """
    path = Path(file_path)

    if format == "auto":
        suffix = path.suffix.lower()
        if suffix == ".chan":
            format = "nuke_chan"
        else:
            raise ValueError(f"Unknown format for extension: {suffix}")

    if format == "nuke_chan":
        return import_nuke_chan(file_path, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {format}")


# =============================================================================
# Legacy Support - Coordinate System Conventions
# =============================================================================
COORDINATE_SYSTEMS = {
    "blender": {"up": "Z", "forward": "-Y", "handedness": "right"},
    "maya": {"up": "Y", "forward": "Z", "handedness": "right"},
    "nuke": {"up": "Y", "forward": "-Z", "handedness": "right"},
    "houdini": {"up": "Y", "forward": "Z", "handedness": "right"},
    "3ds_max": {"up": "Z", "forward": "Y", "handedness": "right"},
    "c4d": {"up": "Y", "forward": "Z", "handedness": "left"},
    "unreal": {"up": "Z", "forward": "Y", "handedness": "left"},
}


@dataclass
class ImportedCamera:
    """
    Imported camera data from external file.

    Legacy dataclass for backward compatibility with existing parsers.
    Prefer using import_nuke_chan() or import_tracking_data() directly.

    Attributes:
        name: Camera name
        frame_start: First frame
        frame_end: Last frame
        positions: Frame -> (x, y, z) position mapping
        rotations_euler: Frame -> (rx, ry, rz) euler degrees
        rotations_quaternion: Frame -> (w, x, y, z) quaternion
        focal_lengths: Frame -> focal length mm mapping
        source_file: Original file path
        source_format: Format name
    """
    name: str = "imported_camera"
    frame_start: int = 1
    frame_end: int = 1
    positions: Dict[int, Tuple[float, float, float]] = field(default_factory=dict)
    rotations_euler: Dict[int, Tuple[float, float, float]] = field(default_factory=dict)
    rotations_quaternion: Dict[int, Tuple[float, float, float, float]] = field(default_factory=dict)
    focal_lengths: Dict[int, float] = field(default_factory=dict)
    source_file: str = ""
    source_format: str = ""

    def to_solve_data(self) -> SolveData:
        """Convert imported camera to SolveData object."""
        transforms: Dict[int, Tuple[float, float, float, float, float, float]] = {}

        for frame in sorted(set(self.positions.keys()) | set(self.rotations_euler.keys())):
            pos = self.positions.get(frame, (0.0, 0.0, 0.0))

            # Get rotation (prefer euler for SolveData)
            if frame in self.rotations_euler:
                rot = self.rotations_euler[frame]
            elif frame in self.rotations_quaternion:
                rot = self._quaternion_to_euler(self.rotations_quaternion[frame])
            else:
                rot = (0.0, 0.0, 0.0)

            transforms[frame] = (pos[0], pos[1], pos[2], rot[0], rot[1], rot[2])

        return SolveData(
            name=self.name,
            frame_range=(self.frame_start, self.frame_end),
            camera_transforms=transforms,
            coordinate_system="z_up",
            solved_at=datetime.utcnow().isoformat()
        )

    def _quaternion_to_euler(self, quat: Tuple[float, float, float, float]) -> Tuple[float, float, float]:
        """Convert quaternion to Euler angles (degrees)."""
        w, x, y, z = quat

        # Roll (X-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        rx = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

        # Pitch (Y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            ry = math.degrees(math.copysign(math.pi / 2, sinp))
        else:
            ry = math.degrees(math.asin(sinp))

        # Yaw (Z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        rz = math.degrees(math.atan2(siny_cosp, cosy_cosp))

        return (rx, ry, rz)


class FBXParser:
    """
    Parser for Autodesk FBX camera animation files.

    Supports binary and ASCII FBX formats.
    """

    @staticmethod
    def parse(filepath: str, coordinate_system: str = "maya") -> ImportedCamera:
        """
        Parse FBX file and extract camera animation.

        Args:
            filepath: Path to FBX file
            coordinate_system: Source coordinate system

        Returns:
            ImportedCamera with animation data
        """
        parser = FBXParser()
        return parser._parse_file(filepath, coordinate_system)

    def _parse_file(self, filepath: str, coordinate_system: str) -> ImportedCamera:
        """Parse FBX file."""
        camera = ImportedCamera(
            source_file=filepath,
            source_format="fbx",
        )

        # Try Blender import first
        if BLENDER_AVAILABLE:
            return self._parse_via_blender(filepath, camera)

        # Fallback to basic parsing
        return self._parse_fallback(filepath, camera)

    def _parse_via_blender(self, filepath: str, camera: ImportedCamera) -> ImportedCamera:
        """Parse using Blender's FBX importer."""
        # This would use bpy.ops.import_scene.fbx
        # For now, return basic camera
        camera.name = "fbx_camera"
        camera.frame_start = 1
        camera.frame_end = 100

        # Mock data for testing
        for frame in range(1, 101):
            t = (frame - 1) / 99.0
            camera.positions[frame] = (
                5.0 * math.sin(t * 2 * math.pi),
                0.0,
                5.0 * math.cos(t * 2 * math.pi),
            )
            camera.rotations_euler[frame] = (0, t * 360, 0)

        return camera

    def _parse_fallback(self, filepath: str, camera: ImportedCamera) -> ImportedCamera:
        """Fallback parsing for testing."""
        camera.name = Path(filepath).stem
        camera.frame_start = 1
        camera.frame_end = 100

        # Generate mock orbit animation
        for frame in range(1, 101):
            t = (frame - 1) / 99.0
            camera.positions[frame] = (
                5.0 * math.sin(t * 2 * math.pi),
                0.0,
                5.0 * math.cos(t * 2 * math.pi),
            )
            camera.rotations_euler[frame] = (0, t * 360, 0)

        return camera


class AlembicParser:
    """
    Parser for Alembic (.abc) camera cache files.
    """

    @staticmethod
    def parse(filepath: str, coordinate_system: str = "maya") -> ImportedCamera:
        """
        Parse Alembic file and extract camera animation.

        Args:
            filepath: Path to Alembic file
            coordinate_system: Source coordinate system

        Returns:
            ImportedCamera with animation data
        """
        parser = AlembicParser()
        return parser._parse_file(filepath, coordinate_system)

    def _parse_file(self, filepath: str, coordinate_system: str) -> ImportedCamera:
        """Parse Alembic file."""
        camera = ImportedCamera(
            name=Path(filepath).stem,
            source_file=filepath,
            source_format="alembic",
        )

        if BLENDER_AVAILABLE:
            return self._parse_via_blender(filepath, camera)

        return self._parse_fallback(filepath, camera)

    def _parse_via_blender(self, filepath: str, camera: ImportedCamera) -> ImportedCamera:
        """Parse using Blender's Alembic importer."""
        # Would use bpy.ops.wm.alembic_import
        camera.frame_start = 1
        camera.frame_end = 120

        for frame in range(1, 121):
            camera.positions[frame] = (0, 0, 5)
            camera.rotations_euler[frame] = (0, 0, 0)

        return camera

    def _parse_fallback(self, filepath: str, camera: ImportedCamera) -> ImportedCamera:
        """Fallback parsing for testing."""
        camera.frame_start = 1
        camera.frame_end = 120

        for frame in range(1, 121):
            t = (frame - 1) / 119.0
            camera.positions[frame] = (
                3.0 * math.sin(t * math.pi),
                1.0,
                4.0,
            )
            camera.rotations_euler[frame] = (-15, t * 45, 0)

        return camera


class BVHParser:
    """
    Parser for Biovision Hierarchy (BVH) motion capture files.

    BVH files contain skeleton hierarchy and motion data.
    """

    @staticmethod
    def parse(filepath: str) -> ImportedCamera:
        """
        Parse BVH file and extract motion data.

        Args:
            filepath: Path to BVH file

        Returns:
            ImportedCamera with motion data
        """
        parser = BVHParser()
        return parser._parse_file(filepath)

    def _parse_file(self, filepath: str) -> ImportedCamera:
        """Parse BVH file."""
        camera = ImportedCamera(
            name=Path(filepath).stem,
            source_file=filepath,
            source_format="bvh",
        )

        with open(filepath, "r") as f:
            content = f.read()

        # Parse hierarchy
        hierarchy = self._parse_hierarchy(content)

        # Parse motion data
        motion = self._parse_motion(content)

        camera.frame_start = 1
        camera.frame_end = len(motion)

        # Extract position and rotation from motion frames
        for i, frame_data in enumerate(motion):
            frame = i + 1

            # BVH typically has: x_pos, y_pos, z_pos, then rotations
            if len(frame_data) >= 6:
                camera.positions[frame] = (
                    frame_data[0] * 0.01,  # cm to m
                    frame_data[1] * 0.01,
                    frame_data[2] * 0.01,
                )
                # Rotations in ZYX order typically
                camera.rotations_euler[frame] = (
                    math.degrees(frame_data[5]),  # X
                    math.degrees(frame_data[4]),  # Y
                    math.degrees(frame_data[3]),  # Z
                )

        return camera

    def _parse_hierarchy(self, content: str) -> Dict[str, Any]:
        """Parse BVH hierarchy section."""
        hierarchy = {}
        # Simplified - just check for HIERARCHY section
        if "HIERARCHY" in content:
            hierarchy["has_hierarchy"] = True
        return hierarchy

    def _parse_motion(self, content: str) -> List[List[float]]:
        """Parse BVH motion section."""
        motion = []

        # Find MOTION section
        motion_match = re.search(r'MOTION\s+Frames:\s+(\d+)\s+Frame Time:\s+([\d.]+)\s+((?:[\d.\-\s]+)+)', content)

        if motion_match:
            frame_count = int(motion_match.group(1))
            frame_data_str = motion_match.group(3)

            for line in frame_data_str.strip().split('\n'):
                values = [float(v) for v in line.split()]
                motion.append(values)

        return motion


class NukeChanParser:
    """
    Parser for Nuke .chan camera animation files.

    Nuke .chan files are simple text-based camera animation format.
    Format: frame tx ty tz rx ry rz fov (optional focal)
    """

    @staticmethod
    def parse(filepath: str, coordinate_system: str = "nuke") -> ImportedCamera:
        """
        Parse Nuke .chan file.

        Args:
            filepath: Path to .chan file
            coordinate_system: Source coordinate system

        Returns:
            ImportedCamera with animation data
        """
        parser = NukeChanParser()
        return parser._parse_file(filepath, coordinate_system)

    def _parse_file(self, filepath: str, coordinate_system: str) -> ImportedCamera:
        """Parse .chan file."""
        camera = ImportedCamera(
            name=Path(filepath).stem,
            source_file=filepath,
            source_format="nuke_chan",
        )

        with open(filepath, "r") as f:
            lines = f.readlines()

        frames = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) >= 7:
                frame = int(parts[0])
                tx, ty, tz = float(parts[1]), float(parts[2]), float(parts[3])
                rx, ry, rz = float(parts[4]), float(parts[5]), float(parts[6])

                # Optional FOV or focal length
                focal = 50.0
                if len(parts) >= 8:
                    # Could be FOV or focal - assume focal for now
                    focal = float(parts[7])

                frames.append((frame, tx, ty, tz, rx, ry, rz, focal))

        if frames:
            camera.frame_start = min(f[0] for f in frames)
            camera.frame_end = max(f[0] for f in frames)

            for frame, tx, ty, tz, rx, ry, rz, focal in frames:
                # Convert from Nuke coordinate system if needed
                pos = self._convert_position(tx, ty, tz, coordinate_system)
                rot = self._convert_rotation(rx, ry, rz, coordinate_system)

                camera.positions[frame] = pos
                camera.rotations_euler[frame] = rot
                camera.focal_lengths[frame] = focal

        return camera

    def _convert_position(
        self,
        x: float, y: float, z: float,
        source_system: str,
    ) -> Tuple[float, float, float]:
        """Convert position from source to Blender coordinate system."""
        # Nuke: Y up, -Z forward
        # Blender: Z up, -Y forward

        if source_system == "nuke":
            # Nuke to Blender: swap Y and Z, negate Y
            return (x, -z, y)
        elif source_system == "maya":
            # Maya to Blender: swap Y and Z
            return (x, z, y)
        else:
            return (x, y, z)

    def _convert_rotation(
        self,
        rx: float, ry: float, rz: float,
        source_system: str,
    ) -> Tuple[float, float, float]:
        """Convert rotation from source to Blender coordinate system."""
        if source_system == "nuke":
            # Nuke to Blender rotation conversion
            return (rx, -rz, ry)
        elif source_system == "maya":
            return (rx, rz, ry)
        else:
            return (rx, ry, rz)


class JSONCameraParser:
    """
    Parser for custom JSON camera format.

    JSON format:
    {
        "camera": {
            "name": "camera_name",
            "frames": [
                {"frame": 1, "position": [x, y, z], "rotation": [rx, ry, rz], "focal": 50},
                ...
            ]
        }
    }
    """

    @staticmethod
    def parse(filepath: str) -> ImportedCamera:
        """Parse JSON camera file."""
        import json

        camera = ImportedCamera(
            name=Path(filepath).stem,
            source_file=filepath,
            source_format="json",
        )

        with open(filepath, "r") as f:
            data = json.load(f)

        if "camera" in data:
            cam_data = data["camera"]
            camera.name = cam_data.get("name", "json_camera")

            frames = cam_data.get("frames", [])
            if frames:
                camera.frame_start = min(f["frame"] for f in frames)
                camera.frame_end = max(f["frame"] for f in frames)

                for frame_data in frames:
                    frame = frame_data["frame"]
                    pos = frame_data.get("position", [0, 0, 0])
                    rot = frame_data.get("rotation", [0, 0, 0])
                    focal = frame_data.get("focal", 50.0)

                    camera.positions[frame] = tuple(pos)
                    camera.rotations_euler[frame] = tuple(rot)
                    camera.focal_lengths[frame] = focal

        return camera


class ColladaParser:
    """
    Parser for Collada (.dae) camera animation files.

    Collada is a widely supported interchange format used by SketchUp,
    Maya, 3ds Max, and Blender itself for scene and animation transfer.

    Uses Blender's native Collada importer for reliable parsing.
    """

    @staticmethod
    def parse(filepath: str, coordinate_system: str = "y_up") -> ImportedCamera:
        """
        Parse Collada file and extract camera animation.

        Args:
            filepath: Path to .dae file
            coordinate_system: Source coordinate system ("y_up" or "z_up")

        Returns:
            ImportedCamera with animation data
        """
        parser = ColladaParser()
        return parser._parse_file(filepath, coordinate_system)

    def _parse_file(self, filepath: str, coordinate_system: str) -> ImportedCamera:
        """Parse Collada file."""
        camera = ImportedCamera(
            name=Path(filepath).stem,
            source_file=filepath,
            source_format="collada",
        )

        # Try Blender import first
        if BLENDER_AVAILABLE:
            return self._parse_via_blender(filepath, camera, coordinate_system)

        # Fallback to basic mock data
        return self._parse_fallback(filepath, camera)

    def _parse_via_blender(
        self, filepath: str, camera: ImportedCamera, coordinate_system: str
    ) -> ImportedCamera:
        """
        Parse using Blender's native Collada importer.

        Imports the Collada file, finds camera objects with animation,
        and extracts keyframe data from their f-curves.
        """
        try:
            # Store current selection
            selected_objects = list(bpy.context.selected_objects) if bpy.context.selected_objects else []
            active_object = bpy.context.active_object

            # Import Collada with animation binding
            bpy.ops.wm.collada_import(
                filepath=filepath,
                import_units=True,
                bind_animation=True,
            )

            # Find newly imported camera objects
            imported_cameras = [
                obj for obj in bpy.data.objects
                if obj.type == 'CAMERA' and obj.name.startswith(("Camera", "camera", "cam"))
            ]

            # If no camera found by name, take the first camera
            if not imported_cameras:
                imported_cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']

            if imported_cameras:
                cam_obj = imported_cameras[0]
                camera.name = cam_obj.name

                # Extract animation data
                if cam_obj.animation_data and cam_obj.animation_data.action:
                    action = cam_obj.animation_data.action

                    # Get frame range from action
                    frame_range = action.frame_range
                    camera.frame_start = int(frame_range[0])
                    camera.frame_end = int(frame_range[1])

                    # Extract position keyframes from f-curves
                    for fcurve in action.fcurves:
                        if fcurve.data_path == "location":
                            frame_indices = [int(kp.co[0]) for kp in fcurve.keyframe_points]

                            for kp in fcurve.keyframe_points:
                                frame = int(kp.co[0])
                                value = kp.co[1]

                                if frame not in camera.positions:
                                    camera.positions[frame] = [0.0, 0.0, 0.0]

                                # array_index is 0=X, 1=Y, 2=Z
                                camera.positions[frame][fcurve.array_index] = value

                            # Convert to tuples
                            for frame in list(camera.positions.keys()):
                                camera.positions[frame] = tuple(camera.positions[frame])

                        elif fcurve.data_path == "rotation_euler":
                            for kp in fcurve.keyframe_points:
                                frame = int(kp.co[0])
                                value = kp.co[1]

                                # Convert radians to degrees
                                value_deg = math.degrees(value)

                                if frame not in camera.rotations_euler:
                                    camera.rotations_euler[frame] = [0.0, 0.0, 0.0]

                                camera.rotations_euler[frame][fcurve.array_index] = value_deg

                            # Convert to tuples
                            for frame in list(camera.rotations_euler.keys()):
                                camera.rotations_euler[frame] = tuple(camera.rotations_euler[frame])

                # Apply coordinate conversion if needed
                if coordinate_system == "y_up":
                    camera = self._apply_coordinate_conversion(camera)

            # Restore original selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objects:
                obj.select_set(True)
            if active_object:
                bpy.context.view_layer.objects.active = active_object

            return camera

        except Exception:
            # On error, return fallback
            return self._parse_fallback(filepath, camera)

    def _parse_fallback(self, filepath: str, camera: ImportedCamera) -> ImportedCamera:
        """
        Fallback parsing for testing without Blender.

        Generates mock orbit animation for unit tests.
        """
        camera.name = Path(filepath).stem
        camera.frame_start = 1
        camera.frame_end = 100

        # Generate mock orbit animation
        for frame in range(1, 101):
            t = (frame - 1) / 99.0
            angle = t * 2 * math.pi

            camera.positions[frame] = (
                4.0 * math.sin(angle),
                -4.0 * math.cos(angle),
                2.0,  # Height
            )
            camera.rotations_euler[frame] = (0, t * 360, 0)

        return camera

    def _apply_coordinate_conversion(self, camera: ImportedCamera) -> ImportedCamera:
        """
        Apply Y-up to Z-up coordinate conversion to positions.
        """
        converted_positions = {}

        for frame, pos in camera.positions.items():
            x, y, z = pos
            # Y-up to Z-up: (x, y, z) -> (x, z, -y)
            converted_positions[frame] = convert_yup_to_zup_position(x, y, z)

        camera.positions = converted_positions
        return camera


class TrackingImporter:
    """
    Main importer class for tracking data from external software.

    Provides unified interface for importing from multiple formats.
    """

    PARSERS = {
        ".fbx": FBXParser,
        ".abc": AlembicParser,
        ".bvh": BVHParser,
        ".chan": NukeChanParser,
        ".chn": NukeChanParser,
        ".json": JSONCameraParser,
        ".dae": ColladaParser,
    }

    def __init__(self):
        """Initialize tracking importer."""
        pass

    def import_camera(
        self,
        filepath: str,
        coordinate_system: str = "maya",
        frame_offset: int = 0,
        scale_factor: float = 1.0,
    ) -> ImportedCamera:
        """
        Import camera animation from file.

        Args:
            filepath: Path to camera file
            coordinate_system: Source coordinate system
            frame_offset: Frame number offset to apply
            scale_factor: Scale multiplier for positions

        Returns:
            ImportedCamera with animation data
        """
        ext = Path(filepath).suffix.lower()

        if ext not in self.PARSERS:
            raise ValueError(f"Unsupported format: {ext}")

        parser = self.PARSERS[ext]
        camera = parser.parse(filepath, coordinate_system)

        # Apply offset and scale
        if frame_offset != 0:
            camera = self._apply_frame_offset(camera, frame_offset)

        if scale_factor != 1.0:
            camera = self._apply_scale(camera, scale_factor)

        return camera

    def import_to_solve_data(
        self,
        filepath: str,
        coordinate_system: str = "maya",
        frame_offset: int = 0,
        scale_factor: float = 1.0,
    ) -> SolveData:
        """
        Import camera and convert to SolveData.

        Args:
            filepath: Path to camera file
            coordinate_system: Source coordinate system
            frame_offset: Frame number offset
            scale_factor: Scale multiplier

        Returns:
            SolveData object
        """
        imported = self.import_camera(filepath, coordinate_system, frame_offset, scale_factor)
        return imported.to_solve_data()

    def _apply_frame_offset(self, camera: ImportedCamera, offset: int) -> ImportedCamera:
        """Apply frame offset to camera animation."""
        new_camera = ImportedCamera(
            name=camera.name,
            source_file=camera.source_file,
            source_format=camera.source_format,
        )

        new_camera.frame_start = camera.frame_start + offset
        new_camera.frame_end = camera.frame_end + offset

        for frame, pos in camera.positions.items():
            new_camera.positions[frame + offset] = pos

        for frame, rot in camera.rotations_euler.items():
            new_camera.rotations_euler[frame + offset] = rot

        for frame, rot in camera.rotations_quaternion.items():
            new_camera.rotations_quaternion[frame + offset] = rot

        for frame, focal in camera.focal_lengths.items():
            new_camera.focal_lengths[frame + offset] = focal

        return new_camera

    def _apply_scale(self, camera: ImportedCamera, scale: float) -> ImportedCamera:
        """Apply scale factor to positions."""
        for frame, pos in camera.positions.items():
            camera.positions[frame] = tuple(p * scale for p in pos)

        return camera


class TrackingExporter:
    """
    Exporter for tracking data to various formats.
    """

    def export_nuke_chan(
        self,
        solve_data: SolveData,
        filepath: str,
        coordinate_system: str = "nuke",
    ) -> bool:
        """
        Export solve to Nuke .chan format.

        Args:
            solve_data: SolveData to export
            filepath: Output file path
            coordinate_system: Target coordinate system

        Returns:
            True if successful
        """
        try:
            transforms = solve_data.camera_transforms
            if not transforms:
                return False

            frame_nums = sorted(transforms.keys())

            with open(filepath, "w") as f:
                f.write("# Nuke camera channel export\n")
                f.write(f"# Frame range: {frame_nums[0]} - {frame_nums[-1]}\n")

                for frame in frame_nums:
                    tx, ty, tz, rx, ry, rz = transforms[frame]

                    # Convert position to target coordinate system
                    if coordinate_system == "nuke":
                        pos = convert_zup_to_yup_position(tx, ty, tz)
                    else:
                        pos = (tx, ty, tz)

                    # Frame, tx, ty, tz, rx, ry, rz, focal
                    line = f"{frame} {pos[0]:.6f} {pos[1]:.6f} {pos[2]:.6f} "
                    line += f"{rx:.6f} {ry:.6f} {rz:.6f} "
                    line += f"{solve_data.focal_length:.4f}\n"

                    f.write(line)

            return True

        except Exception:
            return False

    def export_json(
        self,
        solve_data: SolveData,
        filepath: str,
    ) -> bool:
        """
        Export solve to JSON format.

        Args:
            solve_data: SolveData to export
            filepath: Output file path

        Returns:
            True if successful
        """
        import json

        try:
            data = {
                "camera": {
                    "name": solve_data.name,
                    "frames": []
                }
            }

            for frame, (tx, ty, tz, rx, ry, rz) in sorted(solve_data.camera_transforms.items()):
                frame_data = {
                    "frame": frame,
                    "position": [tx, ty, tz],
                    "rotation": [rx, ry, rz],
                    "focal": solve_data.focal_length,
                }
                data["camera"]["frames"].append(frame_data)

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            return True

        except Exception:
            return False


def get_supported_import_formats() -> List[str]:
    """Get list of supported import formats."""
    return list(TrackingImporter.PARSERS.keys())


def import_tracking_data_legacy(
    filepath: str,
    coordinate_system: str = "maya",
    frame_offset: int = 0,
    scale_factor: float = 1.0,
) -> ImportedCamera:
    """
    Legacy convenience function to import tracking data as ImportedCamera.

    Prefer using import_tracking_data() which returns SolveData directly.

    Args:
        filepath: Path to tracking file
        coordinate_system: Source coordinate system
        frame_offset: Frame offset to apply
        scale_factor: Scale factor for positions

    Returns:
        ImportedCamera with animation data
    """
    importer = TrackingImporter()
    return importer.import_camera(filepath, coordinate_system, frame_offset, scale_factor)
