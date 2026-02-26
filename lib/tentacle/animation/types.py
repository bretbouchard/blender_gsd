"""
Tentacle Animation Types

Data structures for shape keys, animation states, and spline IK rigging.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import math


class ShapeKeyPreset(Enum):
    """Predefined shape key configurations."""

    # Basic shapes
    BASE = "base"
    COMPRESS_50 = "compress_50"      # 50% diameter, 2x length
    COMPRESS_75 = "compress_75"      # 75% diameter, 1.3x length
    EXPAND_125 = "expand_125"        # 125% diameter, 0.8x length

    # Curl shapes
    CURL_TIP = "curl_tip"          # Tip curled 180°
    CURL_FULL = "curl_full"        # Full spiral curl

    # Localized squeeze
    SQUEEZE_TIP = "squeeze_tip"    # Squeeze at tip only
    SQUEEZE_MID = "squeeze_mid"    # Squeeze at middle
    SQUEEZE_BASE = "squeeze_base"  # Squeeze at base
    SQUEEZE_LOCAL = "squeeze_local"  # Localized squeeze at arbitrary point


class AnimationState(Enum):
    """Animation states for zombie tentacle behavior."""

    HIDDEN = "hidden"           # Retracted inside mouth
    EMERGING = "emerging"       # Sliding out of mouth
    SEARCHING = "searching"     # Idle undulation, looking around
    GRABBING = "grabbing"       # Reaching toward target
    ATTACKING = "attacking"     # Fast strike toward victim
    RETRACTING = "retracting"   # Pulling back into mouth

    def is_active(self) -> bool:
        """Check if this is an active animation state."""
        return self in [AnimationState.SEARCHING, AnimationState.GRABBING, AnimationState.ATTACKING]


@dataclass
class ShapeKeyConfig:
    """Configuration for a single shape key."""

    name: str
    """Shape key name (e.g., 'SK_Compress_50')."""

    preset: ShapeKeyPreset
    """Which preset to use."""

    diameter_scale: float = 1.0
    """Scale factor for diameter (1.0 = no change)."""

    length_scale: float = 1.0
    """Scale factor for length (1.0 = no change)."""

    squeeze_position: Optional[float] = None
    """Position along tentacle for localized squeeze (0.0-1.0, None = full)."""

    squeeze_width: float = 0.2
    """Width of localized squeeze zone (0.0-1.0)."""

    curl_angle: float = 0.0
    """Curl angle in degrees (0-720)."""

    curl_start: float = 0.0
    """Where curl starts along tentacle (0.0 = base, 1.0 = tip)."""

    volume_preservation: float = 0.0
    """Amount to preserve volume (0.0-1.0)."""

    interpolation: str = "linear"
    """Interpolation method: linear, smooth, or ease."""

    def get_shape_key_name(self) -> str:
        """Get Blender shape key name with SK_ prefix."""
        return f"SK_{self.name}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "preset": self.preset.value,
            "diameter_scale": self.diameter_scale,
            "length_scale": self.length_scale,
            "squeeze_position": self.squeeze_position,
            "squeeze_width": self.squeeze_width,
            "curl_angle": self.curl_angle,
            "curl_start": self.curl_start,
            "volume_preservation": self.volume_preservation,
            "interpolation": self.interpolation,
        }


@dataclass
class ShapeKeyResult:
    """Result from shape key generation."""

    shape_key_name: str
    """Name of the shape key in Blender."""

    vertex_count: int
    """Number of affected vertices."""

    max_displacement: float
    """Maximum vertex displacement in meters."""

    volume_change: float
    """Percentage volume change from base shape."""

    success: bool = True
    """Whether generation was successful."""

    error: Optional[str] = None
    """Error message if failed."""


@dataclass
class StateTransition:
    """Configuration for a state transition."""

    from_state: AnimationState
    """State to transition from."""

    to_state: AnimationState
    """State to transition to."""

    duration: float = 0.5
    """Duration of the transition in seconds."""

    blend_curve: str = "ease_out"
    """Blending curve: linear, ease_in, ease_out, etc."""

    shape_key_blend: Dict[str, float] = field(default_factory=dict)
    """Shape keys to blend during transition (name: value 0.0-1.0)."""

    conditions: Dict[str, Any] = field(default_factory=dict)
    """Conditions that trigger this transition."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "duration": self.duration,
            "blend_curve": self.blend_curve,
            "shape_key_blend": self.shape_key_blend,
            "conditions": self.conditions,
        }


@dataclass
class AnimationStateConfig:
    """Configuration for an animation state."""

    state: AnimationState
    """The animation state."""

    shape_keys: Dict[str, float] = field(default_factory=dict)
    """Shape key values for this state (name: value 0.0-1.0)."""

    bone_positions: Optional[List[Tuple[float, float, float]]] = None
    """Bone positions for spline IK (if applicable)."""

    idle_motion: Optional[str] = None
    """Idle motion type: undulate, wave, twitch, None."""

    idle_speed: float = 1.0
    """Speed multiplier for idle motion."""

    emergence_delay: float = 0.0
    """Delay between tentacles in multi-array (seconds)."""

    loop: bool = False
    """Whether this state loops."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "state": self.state.value,
            "shape_keys": self.shape_keys,
            "bone_positions": self.bone_positions,
            "idle_motion": self.idle_motion,
            "idle_speed": self.idle_speed,
            "emergence_delay": self.emergence_delay,
            "loop": self.loop,
        }


# Spline IK Rig Types

@dataclass
class SplineIKRig:
    """Configuration for spline IK rig."""

    bone_count: int = 15
    """Number of bones in the chain."""

    bone_prefix: str = "Tentacle"
    """Prefix for bone names."""

    curve_name: str = "Tentacle_Curve"
    """Name of the control curve."""

    chain_length: float = 1.0
    """Length of the bone chain in meters."""

    root_bone: Optional[str] = None
    """Name of parent bone to attach to."""

    control_empty: bool = True
    """Whether to create control empty for the curve."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "bone_count": self.bone_count,
            "bone_prefix": self.bone_prefix,
            "curve_name": self.curve_name,
            "chain_length": self.chain_length,
            "root_bone": self.root_bone,
            "control_empty": self.control_empty,
        }


@dataclass
class RigConfig:
    """Full rig configuration for a tentacle."""

    ik_rig: SplineIKRig
    """Spline IK configuration."""

    shape_keys: List[ShapeKeyConfig] = field(default_factory=list)
    """Shape keys to generate."""

    control_curve_points: int = 6
    """Number of control points on the curve."""

    skin_weights: str = "automatic"
    """Skin weight mode: automatic, manual, envelope."""

    vertex_groups: int = 1
    """Number of vertex groups for multi-zone deformation."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ik_rig": self.ik_rig.to_dict(),
            "shape_keys": [sk.to_dict() for sk in self.shape_keys],
            "control_curve_points": self.control_curve_points,
            "skin_weights": self.skin_weights,
            "vertex_groups": self.vertex_groups,
        }


@dataclass
class RigResult:
    """Result from rig generation."""

    armature_name: str
    """Name of the generated armature."""

    curve_name: str
    """Name of the control curve."""

    curve_object: Optional[Any] = None
    """The curve object (if Blender available)."""

    bone_names: List[str] = field(default_factory=list)
    """Names of all bones in the chain."""

    mesh_object: Optional[Any] = None
    """The skinned mesh object."""

    shape_keys: List[str] = field(default_factory=list)
    """Names of generated shape keys."""

    success: bool = True
    """Whether generation was successful."""

    error: Optional[str] = None
    """Error message if failed."""
