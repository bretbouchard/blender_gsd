"""Zombie mouth tentacle attachment utilities."""

from dataclasses import dataclass
from typing import Optional, Tuple, List
import numpy as np

try:
    import bpy
    from bpy.types import Object, Bone, PoseBone
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = None
    Bone = None
    PoseBone = None

from ..types import TentacleConfig


@dataclass
class MouthAttachmentPoint:
    """Definition of a tentacle attachment point in mouth."""

    name: str                       # Identifier
    position: Tuple[float, float, float]  # Local position relative to mouth
    rotation: Tuple[float, float, float]  # Euler angles (radians)
    scale: float = 1.0              # Size multiplier
    tentacle_config: Optional[TentacleConfig] = None


@dataclass
class MouthSocketResult:
    """Result of mouth socket creation."""

    socket_name: str
    position: Tuple[float, float, float]
    tentacle_roots: List[object] = None  # List of attached tentacle objects

    def __post_init__(self):
        if self.tentacle_roots is None:
            self.tentacle_roots = []


def create_mouth_socket(
    jaw_bone_name: str,
    socket_name: str = "Mouth_Inside",
    offset: Tuple[float, float, float] = (0, -0.02, 0),
) -> Optional["Object"]:
    """
    Create a socket empty inside the mouth for tentacle attachment.

    Args:
        jaw_bone_name: Name of the jaw bone to parent to
        socket_name: Name for the socket object
        offset: Position offset from jaw bone head

    Returns:
        Created socket object (or None if Blender unavailable)
    """
    if not BLENDER_AVAILABLE:
        return None

    # Find jaw bone
    armature = bpy.context.object
    if not armature or armature.type != 'ARMATURE':
        raise ValueError("Active object must be an armature")

    jaw_bone = armature.data.bones.get(jaw_bone_name)
    if not jaw_bone:
        raise ValueError(f"Bone '{jaw_bone_name}' not found")

    # Create empty socket
    socket = bpy.data.objects.new(socket_name, None)
    socket.empty_display_type = 'SPHERE'
    socket.empty_display_size = 0.01

    # Position relative to jaw
    jaw_head = jaw_bone.head_local
    socket.location = (
        jaw_head[0] + offset[0],
        jaw_head[1] + offset[1],
        jaw_head[2] + offset[2],
    )

    # Link to scene
    bpy.context.collection.objects.link(socket)

    # Parent to jaw bone
    socket.parent = armature
    socket.parent_type = 'BONE'
    socket.parent_bone = jaw_bone_name

    return socket


def attach_tentacle_to_socket(
    tentacle_obj: "Object",
    socket_name: str,
    index: int = 0,
) -> None:
    """
    Attach a tentacle object to a mouth socket.

    Args:
        tentacle_obj: Tentacle mesh object
        socket_name: Name of the mouth socket
        index: Tentacle index for naming
    """
    if not BLENDER_AVAILABLE:
        return

    socket = bpy.data.objects.get(socket_name)
    if not socket:
        raise ValueError(f"Socket '{socket_name}' not found")

    # Parent tentacle to socket
    tentacle_obj.parent = socket

    # Rename for clarity
    tentacle_obj.name = f"Tentacle_{index:02d}"


def calculate_mouth_distribution(
    tentacle_count: int,
    spread_angle: float = 60.0,
    distribution: str = "staggered",
) -> List[Tuple[float, float]]:
    """
    Calculate attachment positions for multiple tentacles across mouth.

    Args:
        tentacle_count: Number of tentacles
        spread_angle: Total angle spread in degrees
        distribution: Distribution pattern (uniform, random, staggered)

    Returns:
        List of (angle, z_offset) tuples for each tentacle
    """
    positions = []
    half_spread = np.radians(spread_angle / 2)

    if distribution == "uniform":
        # Evenly spaced
        for i in range(tentacle_count):
            t = i / (tentacle_count - 1) if tentacle_count > 1 else 0.5
            angle = -half_spread + t * 2 * half_spread
            positions.append((angle, 0.0))

    elif distribution == "staggered":
        # Alternating heights
        for i in range(tentacle_count):
            t = i / (tentacle_count - 1) if tentacle_count > 1 else 0.5
            angle = -half_spread + t * 2 * half_spread
            z_offset = 0.005 if i % 2 == 0 else -0.005
            positions.append((angle, z_offset))

    elif distribution == "random":
        # Random positions within spread
        rng = np.random.default_rng(42)
        for i in range(tentacle_count):
            angle = rng.uniform(-half_spread, half_spread)
            z_offset = rng.uniform(-0.005, 0.005)
            positions.append((angle, z_offset))

    else:
        raise ValueError(f"Unknown distribution: {distribution}")

    return positions


def angle_to_position(
    angle: float,
    z_offset: float,
    radius: float = 0.03,
    flatten_factor: float = 0.3,
) -> Tuple[float, float, float]:
    """
    Convert angle to 3D position on mouth arc.

    Args:
        angle: Angle in radians
        z_offset: Vertical offset
        radius: Distance from mouth center
        flatten_factor: How much to flatten Y toward mouth interior (0.0-1.0).
                       0.3 = 30% of radius, creating an elliptical arc that
                       follows the natural curvature of a mouth opening.

    Returns:
        (x, y, z) position tuple
    """
    x = radius * np.sin(angle)
    y = radius * np.cos(angle) * -flatten_factor
    z = z_offset

    return (x, y, z)
