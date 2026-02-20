"""
Animation Type Definitions

Core data structures for rigging, bones, and animation.

Phase 13.0: Rigging Foundation (REQ-ANIM-01)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum


class RigType(Enum):
    """Types of rigs available."""
    HUMAN_BIPED = "human_biped"
    FACE_STANDARD = "face_standard"
    QUADRUPED = "quadruped"
    VEHICLE_BASIC = "vehicle_basic"
    ROBOT_MODULAR = "robot_modular"
    PROP_SIMPLE = "prop_simple"
    CUSTOM = "custom"


class BoneGroupType(Enum):
    """Standard bone group categories."""
    SPINE = "spine"
    HEAD = "head"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"
    LEFT_HAND = "left_hand"
    RIGHT_HAND = "right_hand"
    FACE = "face"
    TAIL = "tail"
    WINGS = "wings"
    FINGERS = "fingers"
    TOES = "toes"
    CUSTOM = "custom"


class WeightMethod(Enum):
    """Weight painting methods."""
    HEAT = "heat"
    DISTANCE = "distance"
    ENVELOPE = "envelope"
    MANUAL = "manual"


class IKMode(Enum):
    """IK solver modes."""
    TWO_BONE = "two_bone"  # Standard limb IK
    CHAIN = "chain"        # Multi-bone chain
    SPLINE = "spline"      # Spline-based IK


@dataclass
class BoneConfig:
    """Configuration for a single bone in a rig."""
    id: str
    parent: Optional[str]
    head: Tuple[float, float, float]
    tail: Tuple[float, float, float]
    roll: float = 0.0
    layers: List[int] = field(default_factory=lambda: [0])
    mirror: Optional[str] = None
    use_connect: bool = False
    use_inherit_rotation: bool = True
    use_local_location: bool = True
    use_deform: bool = True
    use_envelope_multiply: bool = False
    head_radius: float = 0.1
    tail_radius: float = 0.05
    hide: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'parent': self.parent,
            'head': list(self.head),
            'tail': list(self.tail),
            'roll': self.roll,
            'layers': self.layers,
            'mirror': self.mirror,
            'use_connect': self.use_connect,
            'use_inherit_rotation': self.use_inherit_rotation,
            'use_local_location': self.use_local_location,
            'use_deform': self.use_deform,
            'head_radius': self.head_radius,
            'tail_radius': self.tail_radius,
            'hide': self.hide,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BoneConfig:
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            parent=data.get('parent'),
            head=tuple(data['head']),
            tail=tuple(data['tail']),
            roll=data.get('roll', 0.0),
            layers=data.get('layers', [0]),
            mirror=data.get('mirror'),
            use_connect=data.get('use_connect', False),
            use_inherit_rotation=data.get('use_inherit_rotation', True),
            use_local_location=data.get('use_local_location', True),
            use_deform=data.get('use_deform', True),
            head_radius=data.get('head_radius', 0.1),
            tail_radius=data.get('tail_radius', 0.05),
            hide=data.get('hide', False),
        )


@dataclass
class BoneConstraint:
    """Configuration for a bone constraint."""
    bone: str
    type: str  # COPY_ROTATION, IK, TRACK_TO, COPY_LOCATION, etc.
    target: Optional[str] = None
    subtarget: Optional[str] = None
    influence: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'bone': self.bone,
            'type': self.type,
            'target': self.target,
            'subtarget': self.subtarget,
            'influence': self.influence,
            'properties': self.properties,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BoneConstraint:
        """Deserialize from dictionary."""
        return cls(
            bone=data['bone'],
            type=data['type'],
            target=data.get('target'),
            subtarget=data.get('subtarget'),
            influence=data.get('influence', 1.0),
            properties=data.get('properties', {}),
        )


@dataclass
class BoneGroupConfig:
    """Configuration for a bone group (for organization)."""
    name: str
    bones: List[str]
    color: str = "DEFAULT"
    color_set: str = "DEFAULT"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'bones': self.bones,
            'color': self.color,
            'color_set': self.color_set,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BoneGroupConfig:
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            bones=data['bones'],
            color=data.get('color', 'DEFAULT'),
            color_set=data.get('color_set', 'DEFAULT'),
        )


@dataclass
class IKChain:
    """Configuration for an IK chain."""
    name: str
    chain: List[str]
    target: Optional[str] = None
    pole_target: Optional[str] = None
    pole_angle: float = 0.0
    iterations: int = 500
    chain_count: int = 2
    use_tail: bool = False
    use_stretch: bool = False
    mode: IKMode = IKMode.TWO_BONE

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'chain': self.chain,
            'target': self.target,
            'pole_target': self.pole_target,
            'pole_angle': self.pole_angle,
            'iterations': self.iterations,
            'chain_count': self.chain_count,
            'use_tail': self.use_tail,
            'use_stretch': self.use_stretch,
            'mode': self.mode.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IKChain:
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            chain=data['chain'],
            target=data.get('target'),
            pole_target=data.get('pole_target'),
            pole_angle=data.get('pole_angle', 0.0),
            iterations=data.get('iterations', 500),
            chain_count=data.get('chain_count', 2),
            use_tail=data.get('use_tail', False),
            use_stretch=data.get('use_stretch', False),
            mode=IKMode(data.get('mode', 'two_bone')),
        )


@dataclass
class RigConfig:
    """Configuration for a complete rig."""
    id: str
    name: str
    version: str = "1.0"
    rig_type: RigType = RigType.CUSTOM
    description: str = ""
    bones: List[BoneConfig] = field(default_factory=list)
    constraints: List[BoneConstraint] = field(default_factory=list)
    groups: List[BoneGroupConfig] = field(default_factory=list)
    ik_chains: List[IKChain] = field(default_factory=list)
    custom_properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_bone(self, bone_id: str) -> Optional[BoneConfig]:
        """Get a bone by ID."""
        for bone in self.bones:
            if bone.id == bone_id:
                return bone
        return None

    def get_bones_by_parent(self, parent_id: str) -> List[BoneConfig]:
        """Get all bones with a specific parent."""
        return [b for b in self.bones if b.parent == parent_id]

    def get_root_bones(self) -> List[BoneConfig]:
        """Get all bones without parents (root bones)."""
        return [b for b in self.bones if b.parent is None]

    def get_bone_chain(self, from_bone: str, to_bone: str) -> List[str]:
        """Get bone chain from one bone to another."""
        # Build parent lookup
        parent_map = {b.id: b.parent for b in self.bones}

        # Trace from to_bone back to from_bone
        chain = [to_bone]
        current = to_bone

        while current != from_bone:
            parent = parent_map.get(current)
            if parent is None:
                return []  # No path found
            chain.insert(0, parent)
            current = parent

            if len(chain) > 100:  # Safety limit
                return []

        return chain

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'rig_type': self.rig_type.value,
            'description': self.description,
            'bones': [b.to_dict() for b in self.bones],
            'constraints': [c.to_dict() for c in self.constraints],
            'groups': [g.to_dict() for g in self.groups],
            'ik_chains': [i.to_dict() for i in self.ik_chains],
            'custom_properties': self.custom_properties,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RigConfig:
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            version=data.get('version', '1.0'),
            rig_type=RigType(data.get('rig_type', 'custom')),
            description=data.get('description', ''),
            bones=[BoneConfig.from_dict(b) for b in data.get('bones', [])],
            constraints=[BoneConstraint.from_dict(c) for c in data.get('constraints', [])],
            groups=[BoneGroupConfig.from_dict(g) for g in data.get('groups', [])],
            ik_chains=[IKChain.from_dict(i) for i in data.get('ik_chains', [])],
            custom_properties=data.get('custom_properties', {}),
            metadata=data.get('metadata', {}),
        )


@dataclass
class WeightConfig:
    """Configuration for weight painting."""
    bone: str
    vertex_group: Optional[str] = None  # Defaults to bone name
    auto_calculate: bool = True
    weight_threshold: float = 0.01
    method: WeightMethod = WeightMethod.HEAT

    def __post_init__(self):
        if self.vertex_group is None:
            self.vertex_group = self.bone

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'bone': self.bone,
            'vertex_group': self.vertex_group,
            'auto_calculate': self.auto_calculate,
            'weight_threshold': self.weight_threshold,
            'method': self.method.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WeightConfig:
        """Deserialize from dictionary."""
        return cls(
            bone=data['bone'],
            vertex_group=data.get('vertex_group'),
            auto_calculate=data.get('auto_calculate', True),
            weight_threshold=data.get('weight_threshold', 0.01),
            method=WeightMethod(data.get('method', 'heat')),
        )


@dataclass
class RigInstance:
    """Represents a created rig instance in Blender."""
    id: str
    config_id: str
    armature_name: str
    mesh_names: List[str] = field(default_factory=list)
    created_at: str = ""
    scale: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'config_id': self.config_id,
            'armature_name': self.armature_name,
            'mesh_names': self.mesh_names,
            'created_at': self.created_at,
            'scale': self.scale,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RigInstance:
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            config_id=data['config_id'],
            armature_name=data['armature_name'],
            mesh_names=data.get('mesh_names', []),
            created_at=data.get('created_at', ''),
            scale=data.get('scale', 1.0),
            metadata=data.get('metadata', {}),
        )


@dataclass
class PoseData:
    """Data for a single pose."""
    id: str
    name: str
    description: str = ""
    category: str = "custom"
    bone_transforms: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'bone_transforms': self.bone_transforms,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PoseData:
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            category=data.get('category', 'custom'),
            bone_transforms=data.get('bone_transforms', {}),
            metadata=data.get('metadata', {}),
        )


# =============================================================================
# Phase 13.1: IK/FK System Types
# =============================================================================


class RotationOrder(Enum):
    """Rotation order for bones."""
    XYZ = "XYZ"
    XZY = "XZY"
    YXZ = "YXZ"
    YZX = "YZX"
    ZXY = "ZXY"
    ZYX = "ZYX"


class BlendMode(Enum):
    """IK/FK blend modes."""
    FK_ONLY = "fk_only"      # 0.0 - Full FK control
    IK_ONLY = "ik_only"      # 1.0 - Full IK control
    AUTO = "auto"            # Auto blend based on animation


@dataclass
class IKConfig:
    """Configuration for IK constraint setup."""
    name: str
    chain: List[str]                        # Bone chain (root to tip)
    target: Optional[str] = None            # Target bone/object for IK
    pole_target: Optional[str] = None       # Pole target for direction
    pole_angle: float = 0.0                 # Pole rotation angle
    chain_count: int = 2                    # Number of bones in chain
    iterations: int = 500                   # Solver iterations
    mode: IKMode = IKMode.TWO_BONE          # IK solver mode
    use_tail: bool = False                  # Include tail bone
    stretch: float = 0.0                    # Stretch factor (0-1)
    weight: float = 1.0                     # Constraint influence
    lock_rotation: bool = False             # Lock rotation axes

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'chain': self.chain,
            'target': self.target,
            'pole_target': self.pole_target,
            'pole_angle': self.pole_angle,
            'chain_count': self.chain_count,
            'iterations': self.iterations,
            'mode': self.mode.value,
            'use_tail': self.use_tail,
            'stretch': self.stretch,
            'weight': self.weight,
            'lock_rotation': self.lock_rotation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IKConfig':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            chain=data['chain'],
            target=data.get('target'),
            pole_target=data.get('pole_target'),
            pole_angle=data.get('pole_angle', 0.0),
            chain_count=data.get('chain_count', 2),
            iterations=data.get('iterations', 500),
            mode=IKMode(data.get('mode', 'two_bone')),
            use_tail=data.get('use_tail', False),
            stretch=data.get('stretch', 0.0),
            weight=data.get('weight', 1.0),
            lock_rotation=data.get('lock_rotation', False),
        )


@dataclass
class FKConfig:
    """Configuration for FK bone control."""
    bone_name: str
    rotation_order: RotationOrder = RotationOrder.XYZ
    inherit_rotation: bool = True
    inherit_scale: bool = True
    lock_x: bool = False
    lock_y: bool = False
    lock_z: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'bone_name': self.bone_name,
            'rotation_order': self.rotation_order.value,
            'inherit_rotation': self.inherit_rotation,
            'inherit_scale': self.inherit_scale,
            'lock_x': self.lock_x,
            'lock_y': self.lock_y,
            'lock_z': self.lock_z,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FKConfig':
        """Deserialize from dictionary."""
        return cls(
            bone_name=data['bone_name'],
            rotation_order=RotationOrder(data.get('rotation_order', 'XYZ')),
            inherit_rotation=data.get('inherit_rotation', True),
            inherit_scale=data.get('inherit_scale', True),
            lock_x=data.get('lock_x', False),
            lock_y=data.get('lock_y', False),
            lock_z=data.get('lock_z', False),
        )


@dataclass
class RotationLimits:
    """Rotation limits for a bone (in degrees)."""
    x_min: float = -180.0
    x_max: float = 180.0
    y_min: float = -180.0
    y_max: float = 180.0
    z_min: float = -180.0
    z_max: float = 180.0
    use_limits_x: bool = False
    use_limits_y: bool = False
    use_limits_z: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'x_min': self.x_min,
            'x_max': self.x_max,
            'y_min': self.y_min,
            'y_max': self.y_max,
            'z_min': self.z_min,
            'z_max': self.z_max,
            'use_limits_x': self.use_limits_x,
            'use_limits_y': self.use_limits_y,
            'use_limits_z': self.use_limits_z,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RotationLimits':
        """Deserialize from dictionary."""
        return cls(
            x_min=data.get('x_min', -180.0),
            x_max=data.get('x_max', 180.0),
            y_min=data.get('y_min', -180.0),
            y_max=data.get('y_max', 180.0),
            z_min=data.get('z_min', -180.0),
            z_max=data.get('z_max', 180.0),
            use_limits_x=data.get('use_limits_x', False),
            use_limits_y=data.get('use_limits_y', False),
            use_limits_z=data.get('use_limits_z', False),
        )


@dataclass
class PoleTargetConfig:
    """Configuration for an IK pole target."""
    bone_name: str                           # Bone this pole controls
    pole_object: Optional[str] = None        # Name of pole target object
    pole_angle: float = 0.0                  # Rotation angle in radians
    pole_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Offset from auto-position
    auto_position: bool = True               # Auto-calculate pole position

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'bone_name': self.bone_name,
            'pole_object': self.pole_object,
            'pole_angle': self.pole_angle,
            'pole_offset': list(self.pole_offset),
            'auto_position': self.auto_position,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoleTargetConfig':
        """Deserialize from dictionary."""
        return cls(
            bone_name=data['bone_name'],
            pole_object=data.get('pole_object'),
            pole_angle=data.get('pole_angle', 0.0),
            pole_offset=tuple(data.get('pole_offset', (0.0, 0.0, 0.0))),
            auto_position=data.get('auto_position', True),
        )


@dataclass
class IKFKBlendConfig:
    """Configuration for IK/FK blending system."""
    name: str
    ik_chain: List[str]                     # IK bone chain
    fk_chain: List[str]                     # FK bone chain (copy)
    ik_target: str                          # IK target control
    pole_target: Optional[str] = None       # Pole target
    blend_property: str = "ik_fk_blend"     # Custom property for blend factor
    default_blend: float = 1.0              # Default blend (1.0 = IK)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'ik_chain': self.ik_chain,
            'fk_chain': self.fk_chain,
            'ik_target': self.ik_target,
            'pole_target': self.pole_target,
            'blend_property': self.blend_property,
            'default_blend': self.default_blend,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IKFKBlendConfig':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            ik_chain=data['ik_chain'],
            fk_chain=data['fk_chain'],
            ik_target=data['ik_target'],
            pole_target=data.get('pole_target'),
            blend_property=data.get('blend_property', 'ik_fk_blend'),
            default_blend=data.get('default_blend', 1.0),
        )


@dataclass
class SplineIKConfig:
    """Configuration for spline IK (tentacles, spines)."""
    name: str
    chain: List[str]                        # Bone chain
    curve_object: str                       # Curve object name
    chain_count: int = 2                    # Number of bones
    use_curve_radius: bool = False          # Use curve radius for bone scale
    use_stretch: bool = True                # Allow chain to stretch
    use_y_stretch: bool = True              # Stretch along Y axis
    even_divisions: bool = True             # Even bone distribution
    bindings: List[float] = field(default_factory=list)  # Curve binding positions

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'chain': self.chain,
            'curve_object': self.curve_object,
            'chain_count': self.chain_count,
            'use_curve_radius': self.use_curve_radius,
            'use_stretch': self.use_stretch,
            'use_y_stretch': self.use_y_stretch,
            'even_divisions': self.even_divisions,
            'bindings': self.bindings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SplineIKConfig':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            chain=data['chain'],
            curve_object=data['curve_object'],
            chain_count=data.get('chain_count', 2),
            use_curve_radius=data.get('use_curve_radius', False),
            use_stretch=data.get('use_stretch', True),
            use_y_stretch=data.get('use_y_stretch', True),
            even_divisions=data.get('even_divisions', True),
            bindings=data.get('bindings', []),
        )


# =============================================================================
# Phase 13.2: Pose Library Types
# =============================================================================


class PoseCategory(Enum):
    """Categories for organizing poses."""
    REST = "rest"               # T-pose, A-pose, standing
    LOCOMOTION = "locomotion"   # Walk, run, jump cycles
    ACTION = "action"           # Sit, jump, climb
    EXPRESSION = "expression"   # Face expressions
    HAND = "hand"               # Hand gestures
    QUADRUPED = "quadruped"     # Animal poses
    CUSTOM = "custom"           # User-defined


class PoseMirrorAxis(Enum):
    """Axis for mirroring poses."""
    X = "x"      # Mirror left/right (most common)
    Y = "y"      # Mirror front/back
    Z = "z"      # Mirror top/bottom


class PoseBlendMode(Enum):
    """Modes for blending poses."""
    REPLACE = "replace"     # Replace current pose
    ADD = "add"             # Add to current pose (additive)
    MIX = "mix"             # Mix with current pose


@dataclass
class BonePose:
    """Transform data for a single bone in a pose."""
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Euler in degrees
    rotation_quat: Optional[Tuple[float, float, float, float]] = None  # Quaternion (w, x, y, z)
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    rotation_mode: str = "XYZ"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'location': list(self.location),
            'rotation': list(self.rotation),
            'rotation_quat': list(self.rotation_quat) if self.rotation_quat else None,
            'scale': list(self.scale),
            'rotation_mode': self.rotation_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BonePose':
        """Deserialize from dictionary."""
        return cls(
            location=tuple(data.get('location', (0.0, 0.0, 0.0))),
            rotation=tuple(data.get('rotation', (0.0, 0.0, 0.0))),
            rotation_quat=tuple(data['rotation_quat']) if data.get('rotation_quat') else None,
            scale=tuple(data.get('scale', (1.0, 1.0, 1.0))),
            rotation_mode=data.get('rotation_mode', 'XYZ'),
        )


@dataclass
class Pose:
    """Complete pose definition with bone transforms."""
    id: str
    name: str
    category: PoseCategory = PoseCategory.CUSTOM
    rig_type: str = "human_biped"
    description: str = ""
    bones: Dict[str, BonePose] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    affected_bones: List[str] = field(default_factory=list)  # For partial poses

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'rig_type': self.rig_type,
            'description': self.description,
            'bones': {k: v.to_dict() for k, v in self.bones.items()},
            'tags': self.tags,
            'metadata': self.metadata,
            'affected_bones': self.affected_bones,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pose':
        """Deserialize from dictionary."""
        bones = {}
        for bone_name, bone_data in data.get('bones', {}).items():
            bones[bone_name] = BonePose.from_dict(bone_data)

        return cls(
            id=data['id'],
            name=data['name'],
            category=PoseCategory(data.get('category', 'custom')),
            rig_type=data.get('rig_type', 'human_biped'),
            description=data.get('description', ''),
            bones=bones,
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            affected_bones=data.get('affected_bones', []),
        )


@dataclass
class PoseBlendConfig:
    """Configuration for blending multiple poses."""
    poses: List[Tuple[str, float]] = field(default_factory=list)  # (pose_id, weight)
    blend_mode: PoseBlendMode = PoseBlendMode.MIX
    affected_bones: Optional[List[str]] = None  # None = all bones
    transition_frames: int = 10
    easing: str = "EASE_IN_OUT"  # LINEAR, EASE_IN, EASE_OUT, EASE_IN_OUT

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'poses': self.poses,
            'blend_mode': self.blend_mode.value,
            'affected_bones': self.affected_bones,
            'transition_frames': self.transition_frames,
            'easing': self.easing,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoseBlendConfig':
        """Deserialize from dictionary."""
        return cls(
            poses=[tuple(p) for p in data.get('poses', [])],
            blend_mode=PoseBlendMode(data.get('blend_mode', 'mix')),
            affected_bones=data.get('affected_bones'),
            transition_frames=data.get('transition_frames', 10),
            easing=data.get('easing', 'EASE_IN_OUT'),
        )


@dataclass
class PoseLibraryConfig:
    """Configuration for a pose library."""
    name: str
    rig_type: str
    poses: Dict[str, Pose] = field(default_factory=dict)
    categories: List[PoseCategory] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'rig_type': self.rig_type,
            'poses': {k: v.to_dict() for k, v in self.poses.items()},
            'categories': [c.value for c in self.categories],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoseLibraryConfig':
        """Deserialize from dictionary."""
        poses = {}
        for pose_id, pose_data in data.get('poses', {}).items():
            poses[pose_id] = Pose.from_dict(pose_data)

        return cls(
            name=data['name'],
            rig_type=data['rig_type'],
            poses=poses,
            categories=[PoseCategory(c) for c in data.get('categories', [])],
        )


# =============================================================================
# Phase 13.3: Blocking System Types
# =============================================================================


class InterpolationMode(Enum):
    """Animation interpolation modes."""
    STEPPED = "STEPPED"      # No interpolation (blocking)
    LINEAR = "LINEAR"        # Linear interpolation
    BEZIER = "BEZIER"        # Smooth curves


class KeyPoseType(Enum):
    """Types of key poses in blocking."""
    KEY = "key"              # Major story pose
    BREAKDOWN = "breakdown"  # Transition pose
    EXTREME = "extreme"      # Extreme position
    HOLD = "hold"            # Held pose


@dataclass
class KeyPose:
    """A key pose at a specific frame."""
    frame: int
    pose_id: Optional[str] = None
    description: str = ""
    thumbnail_path: Optional[str] = None
    pose_type: KeyPoseType = KeyPoseType.KEY
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'frame': self.frame,
            'pose_id': self.pose_id,
            'description': self.description,
            'thumbnail_path': self.thumbnail_path,
            'pose_type': self.pose_type.value,
            'notes': self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyPose':
        """Deserialize from dictionary."""
        return cls(
            frame=data['frame'],
            pose_id=data.get('pose_id'),
            description=data.get('description', ''),
            thumbnail_path=data.get('thumbnail_path'),
            pose_type=KeyPoseType(data.get('pose_type', 'key')),
            notes=data.get('notes', ''),
        )


@dataclass
class BlockingSession:
    """A blocking session for an animation."""
    scene_name: str
    character_name: str
    key_poses: List[KeyPose] = field(default_factory=list)
    timing_notes: List[str] = field(default_factory=list)
    current_frame: int = 1
    range_start: int = 1
    range_end: int = 100
    interpolation_mode: InterpolationMode = InterpolationMode.STEPPED

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'scene_name': self.scene_name,
            'character_name': self.character_name,
            'key_poses': [kp.to_dict() for kp in self.key_poses],
            'timing_notes': self.timing_notes,
            'current_frame': self.current_frame,
            'range_start': self.range_start,
            'range_end': self.range_end,
            'interpolation_mode': self.interpolation_mode.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlockingSession':
        """Deserialize from dictionary."""
        return cls(
            scene_name=data['scene_name'],
            character_name=data['character_name'],
            key_poses=[KeyPose.from_dict(kp) for kp in data.get('key_poses', [])],
            timing_notes=data.get('timing_notes', []),
            current_frame=data.get('current_frame', 1),
            range_start=data.get('range_start', 1),
            range_end=data.get('range_end', 100),
            interpolation_mode=InterpolationMode(data.get('interpolation_mode', 'STEPPED')),
        )


@dataclass
class OnionSkinConfig:
    """Configuration for onion skinning display."""
    show_previous: bool = True
    show_next: bool = True
    previous_frames: int = 1
    next_frames: int = 1
    previous_color: Tuple[float, float, float, float] = (0.0, 1.0, 0.0, 0.3)
    next_color: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.3)
    ghost_opacity: float = 0.3
    wireframe_only: bool = False
    max_ghosts: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'show_previous': self.show_previous,
            'show_next': self.show_next,
            'previous_frames': self.previous_frames,
            'next_frames': self.next_frames,
            'previous_color': list(self.previous_color),
            'next_color': list(self.next_color),
            'ghost_opacity': self.ghost_opacity,
            'wireframe_only': self.wireframe_only,
            'max_ghosts': self.max_ghosts,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OnionSkinConfig':
        """Deserialize from dictionary."""
        return cls(
            show_previous=data.get('show_previous', True),
            show_next=data.get('show_next', True),
            previous_frames=data.get('previous_frames', 1),
            next_frames=data.get('next_frames', 1),
            previous_color=tuple(data.get('previous_color', (0.0, 1.0, 0.0, 0.3))),
            next_color=tuple(data.get('next_color', (1.0, 0.0, 0.0, 0.3))),
            ghost_opacity=data.get('ghost_opacity', 0.3),
            wireframe_only=data.get('wireframe_only', False),
            max_ghosts=data.get('max_ghosts', 5),
        )


@dataclass
class TimelineMarkerConfig:
    """Configuration for timeline markers."""
    name: str
    frame: int
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'frame': self.frame,
            'color': list(self.color),
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimelineMarkerConfig':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            frame=data['frame'],
            color=tuple(data.get('color', (1.0, 1.0, 1.0))),
            description=data.get('description', ''),
        )


@dataclass
class BlockingPreset:
    """A preset for blocking workflow."""
    name: str
    description: str = ""
    frame_range: Tuple[int, int] = (1, 100)
    default_poses: List[Dict[str, Any]] = field(default_factory=list)
    interpolation: InterpolationMode = InterpolationMode.STEPPED
    thumbnail_size: Tuple[int, int] = (256, 256)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'frame_range': list(self.frame_range),
            'default_poses': self.default_poses,
            'interpolation': self.interpolation.value,
            'thumbnail_size': list(self.thumbnail_size),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlockingPreset':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            frame_range=tuple(data.get('frame_range', (1, 100))),
            default_poses=data.get('default_poses', []),
            interpolation=InterpolationMode(data.get('interpolation', 'STEPPED')),
            thumbnail_size=tuple(data.get('thumbnail_size', (256, 256))),
        )


# =============================================================================
# Phase 13.4: Face Animation Types
# =============================================================================


class FaceRigComponent(Enum):
    """Components of a face rig."""
    EYES = "eyes"
    MOUTH = "mouth"
    BROWS = "brows"
    CHEEKS = "cheeks"
    JAW = "jaw"
    TONGUE = "tongue"
    NOSE = "nose"
    EARS = "ears"
    EYELIDS = "eyelids"
    LIPS = "lips"


class ExpressionCategory(Enum):
    """Categories for facial expressions."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    FEAR = "fear"
    DISGUST = "disgust"
    CONTEMPT = "contempt"
    CUSTOM = "custom"


class VisemeType(Enum):
    """Standard visemes for lip sync (Preston Blair system)."""
    REST = "rest"          # Closed mouth, neutral
    A = "A"                # "Ah" - jaw open, lips relaxed
    E = "E"                # "Eh" - corners stretched
    I = "I"                # "Ee" - wide smile
    O = "O"                # "Oh" - round, open
    U = "U"                # "Oo" - lips forward, round
    M = "M"                # "Mm/B/P" - lips closed
    F = "F"                # "F/V" - upper teeth on lower lip
    TH = "TH"              # "Th" - tongue between teeth
    L = "L"                # "L" - tongue behind upper teeth
    W = "W"                # "W" - lips forward, tight
    CH = "CH"              # "Ch/Sh/J" - lips forward, teeth close
    S = "S"                # "S/Z" - teeth close, corners back
    N = "N"                # "N" - similar to L but wider
    K = "K"                # "K/G" - back of mouth
    T = "T"                # "T/D" - tongue behind upper teeth
    R = "R"                # "R" - lips forward, tongue curled


class ShapeKeyCategory(Enum):
    """Categories for organizing shape keys."""
    EXPRESSION = "expression"    # Facial expressions
    VISEME = "viseme"            # Lip sync shapes
    CORRECTIVE = "corrective"    # Fix deformations
    HELPER = "helper"            # Intermediate shapes
    CUSTOM = "custom"            # User-defined


@dataclass
class ShapeKeyConfig:
    """Configuration for a shape key."""
    name: str
    category: ShapeKeyCategory = ShapeKeyCategory.CUSTOM
    value: float = 0.0                     # Current value (0.0 - 1.0)
    min_value: float = 0.0
    max_value: float = 1.0
    driver: Optional[str] = None           # Driver expression if any
    symm_group: Optional[str] = None       # Symmetry group for L/R pairs
    vertex_group: Optional[str] = None     # Limit to vertex group
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'category': self.category.value,
            'value': self.value,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'driver': self.driver,
            'symm_group': self.symm_group,
            'vertex_group': self.vertex_group,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShapeKeyConfig':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            category=ShapeKeyCategory(data.get('category', 'custom')),
            value=data.get('value', 0.0),
            min_value=data.get('min_value', 0.0),
            max_value=data.get('max_value', 1.0),
            driver=data.get('driver'),
            symm_group=data.get('symm_group'),
            vertex_group=data.get('vertex_group'),
            description=data.get('description', ''),
        )


@dataclass
class ExpressionConfig:
    """Configuration for a facial expression."""
    id: str
    name: str
    category: ExpressionCategory = ExpressionCategory.CUSTOM
    description: str = ""
    shape_keys: Dict[str, float] = field(default_factory=dict)  # shape_key_name -> value
    bone_transforms: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # bone_name -> transform
    intensity: float = 1.0                  # 0.0 - 1.0
    bilaterals: Dict[str, str] = field(default_factory=dict)  # L/R shape key pairs
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'description': self.description,
            'shape_keys': self.shape_keys,
            'bone_transforms': self.bone_transforms,
            'intensity': self.intensity,
            'bilaterals': self.bilaterals,
            'tags': self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpressionConfig':
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            category=ExpressionCategory(data.get('category', 'custom')),
            description=data.get('description', ''),
            shape_keys=data.get('shape_keys', {}),
            bone_transforms=data.get('bone_transforms', {}),
            intensity=data.get('intensity', 1.0),
            bilaterals=data.get('bilaterals', {}),
            tags=data.get('tags', []),
        )


@dataclass
class FaceRigConfig:
    """Configuration for a face rig."""
    id: str
    name: str
    description: str = ""
    components: List[FaceRigComponent] = field(default_factory=list)
    shape_keys: Dict[str, ShapeKeyConfig] = field(default_factory=dict)
    expressions: Dict[str, ExpressionConfig] = field(default_factory=dict)
    visemes: Dict[str, Dict[str, float]] = field(default_factory=dict)  # viseme -> shape_keys
    control_bones: List[str] = field(default_factory=list)
    driver_variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_shape_key(self, name: str) -> Optional[ShapeKeyConfig]:
        """Get shape key by name."""
        return self.shape_keys.get(name)

    def get_expression(self, expr_id: str) -> Optional[ExpressionConfig]:
        """Get expression by ID."""
        return self.expressions.get(expr_id)

    def get_viseme_config(self, viseme: VisemeType) -> Dict[str, float]:
        """Get shape key values for a viseme."""
        return self.visemes.get(viseme.value, {})

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'components': [c.value for c in self.components],
            'shape_keys': {k: v.to_dict() for k, v in self.shape_keys.items()},
            'expressions': {k: v.to_dict() for k, v in self.expressions.items()},
            'visemes': self.visemes,
            'control_bones': self.control_bones,
            'driver_variables': self.driver_variables,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FaceRigConfig':
        """Deserialize from dictionary."""
        shape_keys = {}
        for name, sk_data in data.get('shape_keys', {}).items():
            shape_keys[name] = ShapeKeyConfig.from_dict(sk_data)

        expressions = {}
        for expr_id, expr_data in data.get('expressions', {}).items():
            expressions[expr_id] = ExpressionConfig.from_dict(expr_data)

        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            components=[FaceRigComponent(c) for c in data.get('components', [])],
            shape_keys=shape_keys,
            expressions=expressions,
            visemes=data.get('visemes', {}),
            control_bones=data.get('control_bones', []),
            driver_variables=data.get('driver_variables', {}),
            metadata=data.get('metadata', {}),
        )


@dataclass
class LipSyncFrame:
    """A single frame in a lip sync sequence."""
    frame: int
    viseme: VisemeType
    intensity: float = 1.0
    transition_from: Optional[VisemeType] = None
    transition_progress: float = 0.0  # 0.0 - 1.0 for blend

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'frame': self.frame,
            'viseme': self.viseme.value,
            'intensity': self.intensity,
            'transition_from': self.transition_from.value if self.transition_from else None,
            'transition_progress': self.transition_progress,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LipSyncFrame':
        """Deserialize from dictionary."""
        return cls(
            frame=data['frame'],
            viseme=VisemeType(data['viseme']),
            intensity=data.get('intensity', 1.0),
            transition_from=VisemeType(data['transition_from']) if data.get('transition_from') else None,
            transition_progress=data.get('transition_progress', 0.0),
        )


@dataclass
class LipSyncConfig:
    """Configuration for lip sync animation."""
    name: str
    frames: List[LipSyncFrame] = field(default_factory=list)
    frame_rate: float = 24.0
    audio_file: Optional[str] = None
    blend_frames: int = 2  # Frames for viseme transitions
    coarticulation: bool = True  # Enable coarticulation blending
    intensity_curve: str = "linear"  # linear, smooth, sharp

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'frames': [f.to_dict() for f in self.frames],
            'frame_rate': self.frame_rate,
            'audio_file': self.audio_file,
            'blend_frames': self.blend_frames,
            'coarticulation': self.coarticulation,
            'intensity_curve': self.intensity_curve,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LipSyncConfig':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            frames=[LipSyncFrame.from_dict(f) for f in data.get('frames', [])],
            frame_rate=data.get('frame_rate', 24.0),
            audio_file=data.get('audio_file'),
            blend_frames=data.get('blend_frames', 2),
            coarticulation=data.get('coarticulation', True),
            intensity_curve=data.get('intensity_curve', 'linear'),
        )


@dataclass
class EyeTargetConfig:
    """Configuration for eye tracking/look-at."""
    target_object: Optional[str] = None
    target_location: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    influence: float = 1.0
    lock_horizontal: bool = False
    lock_vertical: bool = False
    eye_bones: List[str] = field(default_factory=list)
    head_bone: Optional[str] = None
    head_influence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'target_object': self.target_object,
            'target_location': list(self.target_location),
            'influence': self.influence,
            'lock_horizontal': self.lock_horizontal,
            'lock_vertical': self.lock_vertical,
            'eye_bones': self.eye_bones,
            'head_bone': self.head_bone,
            'head_influence': self.head_influence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EyeTargetConfig':
        """Deserialize from dictionary."""
        return cls(
            target_object=data.get('target_object'),
            target_location=tuple(data.get('target_location', (0.0, 0.0, 0.0))),
            influence=data.get('influence', 1.0),
            lock_horizontal=data.get('lock_horizontal', False),
            lock_vertical=data.get('lock_vertical', False),
            eye_bones=data.get('eye_bones', []),
            head_bone=data.get('head_bone'),
            head_influence=data.get('head_influence', 0.0),
        )


@dataclass
class BlinkConfig:
    """Configuration for eye blinking."""
    blink_rate: float = 0.15  # Blinks per second (average ~15/minute)
    blink_duration: int = 3  # Frames for full blink
    blink_variation: float = 0.2  # Random variation
    shape_key: str = "blink"
    min_interval: int = 30  # Minimum frames between blinks
    max_interval: int = 240  # Maximum frames between blinks

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'blink_rate': self.blink_rate,
            'blink_duration': self.blink_duration,
            'blink_variation': self.blink_variation,
            'shape_key': self.shape_key,
            'min_interval': self.min_interval,
            'max_interval': self.max_interval,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlinkConfig':
        """Deserialize from dictionary."""
        return cls(
            blink_rate=data.get('blink_rate', 0.15),
            blink_duration=data.get('blink_duration', 3),
            blink_variation=data.get('blink_variation', 0.2),
            shape_key=data.get('shape_key', 'blink'),
            min_interval=data.get('min_interval', 30),
            max_interval=data.get('max_interval', 240),
        )


# =============================================================================
# Phase 13.5: Crowd System Types
# =============================================================================


class CrowdType(Enum):
    """Types of crowds."""
    PEDESTRIAN = "pedestrian"    # Walking people
    AUDIENCE = "audience"        # Seated spectators
    VEHICLE = "vehicle"          # Cars, bikes
    CREATURE = "creature"        # Animals, flocks
    CUSTOM = "custom"            # Custom crowd


class BehaviorState(Enum):
    """Behavior states for crowd agents."""
    IDLE = "idle"                # Standing still
    WALK = "walk"                # Walking to destination
    RUN = "run"                  # Running
    FLEE = "flee"                # Running away from threat
    FOLLOW = "follow"            # Following leader
    GROUP = "group"              # Moving in group
    SIT = "sit"                  # Seated (audience)
    TALK = "talk"                # Talking/conversing
    REACT = "react"              # Reacting to event


class DistributionType(Enum):
    """Spawn distribution types."""
    RANDOM = "random"            # Random placement
    GRID = "grid"                # Grid-based placement
    PATH = "path"                # Along a path
    POINTS = "points"            # Specific spawn points
    SURFACE = "surface"          # On mesh surface


@dataclass
class AgentConfig:
    """Configuration for crowd agents."""
    mesh_path: str                           # Path to agent mesh
    rig_type: str = "human_biped"            # Type of rig
    animations: List[str] = field(default_factory=list)  # Available animations
    collection_name: Optional[str] = None    # Collection for agent variants
    lod_levels: List[str] = field(default_factory=list)  # LOD mesh names

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'mesh_path': self.mesh_path,
            'rig_type': self.rig_type,
            'animations': self.animations,
            'collection_name': self.collection_name,
            'lod_levels': self.lod_levels,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Deserialize from dictionary."""
        return cls(
            mesh_path=data['mesh_path'],
            rig_type=data.get('rig_type', 'human_biped'),
            animations=data.get('animations', []),
            collection_name=data.get('collection_name'),
            lod_levels=data.get('lod_levels', []),
        )


@dataclass
class BehaviorConfig:
    """Configuration for crowd behavior."""
    walk_speed: Tuple[float, float] = (1.0, 1.5)   # Random range m/s
    run_speed: Tuple[float, float] = (3.0, 5.0)    # Random range m/s
    idle_chance: float = 0.1                        # Chance to idle
    flee_distance: float = 10.0                     # Distance to flee from
    group_chance: float = 0.3                       # Chance to group
    group_size: Tuple[int, int] = (2, 4)            # Group size range
    talk_chance: float = 0.2                        # Chance to talk
    reaction_time: float = 0.5                      # Seconds to react

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'walk_speed': list(self.walk_speed),
            'run_speed': list(self.run_speed),
            'idle_chance': self.idle_chance,
            'flee_distance': self.flee_distance,
            'group_chance': self.group_chance,
            'group_size': list(self.group_size),
            'talk_chance': self.talk_chance,
            'reaction_time': self.reaction_time,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BehaviorConfig':
        """Deserialize from dictionary."""
        return cls(
            walk_speed=tuple(data.get('walk_speed', (1.0, 1.5))),
            run_speed=tuple(data.get('run_speed', (3.0, 5.0))),
            idle_chance=data.get('idle_chance', 0.1),
            flee_distance=data.get('flee_distance', 10.0),
            group_chance=data.get('group_chance', 0.3),
            group_size=tuple(data.get('group_size', (2, 4))),
            talk_chance=data.get('talk_chance', 0.2),
            reaction_time=data.get('reaction_time', 0.5),
        )


@dataclass
class SpawnConfig:
    """Configuration for crowd spawning."""
    count: int = 50                                    # Number of agents
    area: Tuple[Tuple[float, float], Tuple[float, float]] = ((-10.0, -10.0), (10.0, 10.0))
    height: float = 0.0                                # Spawn height
    distribution: DistributionType = DistributionType.RANDOM
    spawn_points: List[Tuple[float, float, float]] = field(default_factory=list)
    path_curve: Optional[str] = None                   # Curve for path distribution
    surface_mesh: Optional[str] = None                 # Mesh for surface distribution
    seed: Optional[int] = None                         # Random seed

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'count': self.count,
            'area': [list(p) for p in self.area],
            'height': self.height,
            'distribution': self.distribution.value,
            'spawn_points': [list(p) for p in self.spawn_points],
            'path_curve': self.path_curve,
            'surface_mesh': self.surface_mesh,
            'seed': self.seed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpawnConfig':
        """Deserialize from dictionary."""
        return cls(
            count=data.get('count', 50),
            area=tuple(tuple(p) for p in data.get('area', ((-10.0, -10.0), (10.0, 10.0)))),
            height=data.get('height', 0.0),
            distribution=DistributionType(data.get('distribution', 'random')),
            spawn_points=[tuple(p) for p in data.get('spawn_points', [])],
            path_curve=data.get('path_curve'),
            surface_mesh=data.get('surface_mesh'),
            seed=data.get('seed'),
        )


@dataclass
class AvoidanceConfig:
    """Configuration for collision avoidance."""
    radius: float = 0.5                    # Agent radius
    avoid_agents: bool = True              # Avoid other agents
    avoid_obstacles: bool = True           # Avoid obstacles
    avoidance_strength: float = 1.0        # Avoidance force multiplier
    obstacle_collection: Optional[str] = None  # Collection of obstacles
    max_avoidance_force: float = 10.0      # Maximum avoidance force

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'radius': self.radius,
            'avoid_agents': self.avoid_agents,
            'avoid_obstacles': self.avoid_obstacles,
            'avoidance_strength': self.avoidance_strength,
            'obstacle_collection': self.obstacle_collection,
            'max_avoidance_force': self.max_avoidance_force,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AvoidanceConfig':
        """Deserialize from dictionary."""
        return cls(
            radius=data.get('radius', 0.5),
            avoid_agents=data.get('avoid_agents', True),
            avoid_obstacles=data.get('avoid_obstacles', True),
            avoidance_strength=data.get('avoidance_strength', 1.0),
            obstacle_collection=data.get('obstacle_collection'),
            max_avoidance_force=data.get('max_avoidance_force', 10.0),
        )


@dataclass
class VariationConfig:
    """Configuration for agent variation."""
    scale_range: Tuple[float, float] = (0.9, 1.1)          # Scale variation
    color_variations: Dict[str, List[str]] = field(default_factory=dict)  # Material slots -> colors
    random_rotation: bool = True                            # Random Y rotation
    random_anim_offset: bool = True                         # Offset animation start
    material_variants: List[str] = field(default_factory=list)  # Material variant names

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'scale_range': list(self.scale_range),
            'color_variations': self.color_variations,
            'random_rotation': self.random_rotation,
            'random_anim_offset': self.random_anim_offset,
            'material_variants': self.material_variants,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VariationConfig':
        """Deserialize from dictionary."""
        return cls(
            scale_range=tuple(data.get('scale_range', (0.9, 1.1))),
            color_variations=data.get('color_variations', {}),
            random_rotation=data.get('random_rotation', True),
            random_anim_offset=data.get('random_anim_offset', True),
            material_variants=data.get('material_variants', []),
        )


@dataclass
class CrowdConfig:
    """Configuration for a complete crowd simulation."""
    id: str
    name: str
    crowd_type: CrowdType = CrowdType.PEDESTRIAN
    agent: Optional[AgentConfig] = None
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)
    spawn: SpawnConfig = field(default_factory=SpawnConfig)
    avoidance: AvoidanceConfig = field(default_factory=AvoidanceConfig)
    variation: VariationConfig = field(default_factory=VariationConfig)
    paths: List[Dict[str, Any]] = field(default_factory=list)  # Path configurations
    goals: List[Dict[str, Any]] = field(default_factory=list)  # Goal configurations
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'crowd_type': self.crowd_type.value,
            'agent': self.agent.to_dict() if self.agent else None,
            'behavior': self.behavior.to_dict(),
            'spawn': self.spawn.to_dict(),
            'avoidance': self.avoidance.to_dict(),
            'variation': self.variation.to_dict(),
            'paths': self.paths,
            'goals': self.goals,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrowdConfig':
        """Deserialize from dictionary."""
        agent_data = data.get('agent')
        agent = AgentConfig.from_dict(agent_data) if agent_data else None

        return cls(
            id=data['id'],
            name=data['name'],
            crowd_type=CrowdType(data.get('crowd_type', 'pedestrian')),
            agent=agent,
            behavior=BehaviorConfig.from_dict(data.get('behavior', {})),
            spawn=SpawnConfig.from_dict(data.get('spawn', {})),
            avoidance=AvoidanceConfig.from_dict(data.get('avoidance', {})),
            variation=VariationConfig.from_dict(data.get('variation', {})),
            paths=data.get('paths', []),
            goals=data.get('goals', []),
            metadata=data.get('metadata', {}),
        )


@dataclass
class BoidRuleConfig:
    """Configuration for a single boid rule."""
    rule_type: str                          # SEPARATE, ALIGN, COHESION, etc.
    enabled: bool = True
    weight: float = 1.0
    use_in_air: bool = True
    use_on_land: bool = True
    target_object: Optional[str] = None     # For FOLLOW_LEADER, FOLLOW_CURVE
    target_point: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # For GOAL
    distance: float = 1.0                   # For various rules
    falloff: float = 0.5                    # Falloff factor

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'rule_type': self.rule_type,
            'enabled': self.enabled,
            'weight': self.weight,
            'use_in_air': self.use_in_air,
            'use_on_land': self.use_on_land,
            'target_object': self.target_object,
            'target_point': list(self.target_point),
            'distance': self.distance,
            'falloff': self.falloff,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoidRuleConfig':
        """Deserialize from dictionary."""
        return cls(
            rule_type=data['rule_type'],
            enabled=data.get('enabled', True),
            weight=data.get('weight', 1.0),
            use_in_air=data.get('use_in_air', True),
            use_on_land=data.get('use_on_land', True),
            target_object=data.get('target_object'),
            target_point=tuple(data.get('target_point', (0.0, 0.0, 0.0))),
            distance=data.get('distance', 1.0),
            falloff=data.get('falloff', 0.5),
        )


@dataclass
class BoidSettingsConfig:
    """Configuration for boid physics settings."""
    use_flight: bool = True
    use_land: bool = True
    use_climb: bool = False
    air_speed_min: float = 5.0
    air_speed_max: float = 10.0
    air_acc_max: float = 0.5
    air_ave_speed: float = 0.8
    land_speed_max: float = 2.0
    land_acc_max: float = 0.5
    land_ave_speed: float = 0.8
    land_personal_space: float = 1.0
    height: float = 2.0  # Banking amount

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'use_flight': self.use_flight,
            'use_land': self.use_land,
            'use_climb': self.use_climb,
            'air_speed_min': self.air_speed_min,
            'air_speed_max': self.air_speed_max,
            'air_acc_max': self.air_acc_max,
            'air_ave_speed': self.air_ave_speed,
            'land_speed_max': self.land_speed_max,
            'land_acc_max': self.land_acc_max,
            'land_ave_speed': self.land_ave_speed,
            'land_personal_space': self.land_personal_space,
            'height': self.height,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoidSettingsConfig':
        """Deserialize from dictionary."""
        return cls(
            use_flight=data.get('use_flight', True),
            use_land=data.get('use_land', True),
            use_climb=data.get('use_climb', False),
            air_speed_min=data.get('air_speed_min', 5.0),
            air_speed_max=data.get('air_speed_max', 10.0),
            air_acc_max=data.get('air_acc_max', 0.5),
            air_ave_speed=data.get('air_ave_speed', 0.8),
            land_speed_max=data.get('land_speed_max', 2.0),
            land_acc_max=data.get('land_acc_max', 0.5),
            land_ave_speed=data.get('land_ave_speed', 0.8),
            land_personal_space=data.get('land_personal_space', 1.0),
            height=data.get('height', 2.0),
        )


# Constants for crowd system
MAX_PARTICLE_COUNT = 5000  # Maximum recommended particle count
WARN_PARTICLE_COUNT = 2000  # Count at which to warn about performance


# =============================================================================
# Phase 13.6: Vehicle System Types
# =============================================================================


class VehicleType(Enum):
    """Types of vehicles."""
    AUTOMOBILE = "automobile"    # Cars, sedans, sports cars
    TRUCK = "truck"              # Pickup trucks, SUVs
    PLANE = "plane"              # Airplanes
    HELICOPTER = "helicopter"    # Helicopters
    ROBOT = "robot"              # Walking robots
    TANK = "tank"                # Tanks, tracked vehicles
    BOAT = "boat"                # Boats, ships
    MOTORCYCLE = "motorcycle"    # Motorcycles, bikes
    CUSTOM = "custom"            # Custom vehicle


class SuspensionType(Enum):
    """Types of suspension systems."""
    INDEPENDENT = "independent"      # Independent suspension
    SOLID_AXLE = "solid_axle"        # Solid axle
    MACPHERSON = "macpherson"        # MacPherson strut
    DOUBLE_WISHBONE = "double_wishbone"  # Double wishbone
    MULTI_LINK = "multi_link"        # Multi-link suspension
    AIR = "air"                      # Air suspension


class LaunchState(Enum):
    """States for vehicle launch sequences."""
    STAGED = "staged"           # Waiting at start position
    COUNTDOWN = "countdown"     # Countdown in progress
    LAUNCHING = "launching"     # Accelerating
    RUNNING = "running"         # At speed
    STOPPING = "stopping"       # Decelerating
    STOPPED = "stopped"         # Full stop
    ABORTED = "aborted"         # Emergency abort


class StuntType(Enum):
    """Types of vehicle stunts."""
    JUMP = "jump"               # Vehicle jump/ramp
    DRIFT = "drift"             # Controlled slide
    BARREL_ROLL = "barrel_roll" # 360° roll
    J_TURN = "j_turn"           # 180° reverse direction
    BOOTLEG = "bootleg"         # 180° spin
    T_BONE = "t_bone"           # T-bone crash
    PURSUIT = "pursuit"         # Chase sequence
    FORMATION = "formation"     # Multi-vehicle formation


@dataclass
class WheelConfig:
    """Configuration for a single wheel."""
    id: str
    position: Tuple[float, float, float]      # Local position (x, y, z)
    radius: float = 0.35
    width: float = 0.2
    steering: bool = False                     # Can this wheel steer?
    driven: bool = False                       # Is this wheel powered?
    suspended: bool = True                     # Does this wheel have suspension?
    max_steering_angle: float = 35.0           # Max steering angle in degrees

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'position': list(self.position),
            'radius': self.radius,
            'width': self.width,
            'steering': self.steering,
            'driven': self.driven,
            'suspended': self.suspended,
            'max_steering_angle': self.max_steering_angle,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WheelConfig':
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            position=tuple(data['position']),
            radius=data.get('radius', 0.35),
            width=data.get('width', 0.2),
            steering=data.get('steering', False),
            driven=data.get('driven', False),
            suspended=data.get('suspended', True),
            max_steering_angle=data.get('max_steering_angle', 35.0),
        )


@dataclass
class SteeringConfig:
    """Configuration for vehicle steering."""
    max_angle: float = 35.0                   # Maximum steering angle (degrees)
    ackermann: bool = True                    # Use Ackermann geometry
    steering_wheel_ratio: float = 1.0         # Steering wheel to wheel ratio
    speed_sensitive: bool = False             # Reduce steering at high speed
    return_speed: float = 1.0                 # Steering return speed

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'max_angle': self.max_angle,
            'ackermann': self.ackermann,
            'steering_wheel_ratio': self.steering_wheel_ratio,
            'speed_sensitive': self.speed_sensitive,
            'return_speed': self.return_speed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SteeringConfig':
        """Deserialize from dictionary."""
        return cls(
            max_angle=data.get('max_angle', 35.0),
            ackermann=data.get('ackermann', True),
            steering_wheel_ratio=data.get('steering_wheel_ratio', 1.0),
            speed_sensitive=data.get('speed_sensitive', False),
            return_speed=data.get('return_speed', 1.0),
        )


@dataclass
class SuspensionConfig:
    """Configuration for vehicle suspension."""
    type: SuspensionType = SuspensionType.INDEPENDENT
    travel: float = 0.15                      # Suspension travel (meters)
    stiffness: float = 1.0                    # Spring stiffness
    damping: float = 0.5                      # Damper coefficient
    anti_roll: float = 0.0                    # Anti-roll bar stiffness
    preload: float = 0.0                      # Spring preload

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'type': self.type.value,
            'travel': self.travel,
            'stiffness': self.stiffness,
            'damping': self.damping,
            'anti_roll': self.anti_roll,
            'preload': self.preload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SuspensionConfig':
        """Deserialize from dictionary."""
        return cls(
            type=SuspensionType(data.get('type', 'independent')),
            travel=data.get('travel', 0.15),
            stiffness=data.get('stiffness', 1.0),
            damping=data.get('damping', 0.5),
            anti_roll=data.get('anti_roll', 0.0),
            preload=data.get('preload', 0.0),
        )


@dataclass
class VehicleDimensions:
    """Physical dimensions of a vehicle."""
    length: float = 4.5                       # Length in meters
    width: float = 1.8                        # Width in meters
    height: float = 1.4                       # Height in meters
    wheelbase: float = 2.7                    # Distance between axles
    track_width: float = 1.6                  # Distance between wheels
    ground_clearance: float = 0.15            # Ground clearance

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'wheelbase': self.wheelbase,
            'track_width': self.track_width,
            'ground_clearance': self.ground_clearance,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VehicleDimensions':
        """Deserialize from dictionary."""
        return cls(
            length=data.get('length', 4.5),
            width=data.get('width', 1.8),
            height=data.get('height', 1.4),
            wheelbase=data.get('wheelbase', 2.7),
            track_width=data.get('track_width', 1.6),
            ground_clearance=data.get('ground_clearance', 0.15),
        )


@dataclass
class VehicleConfig:
    """Configuration for a complete vehicle."""
    id: str
    name: str
    vehicle_type: VehicleType = VehicleType.AUTOMOBILE
    dimensions: VehicleDimensions = field(default_factory=VehicleDimensions)
    wheels: List[WheelConfig] = field(default_factory=list)
    steering: SteeringConfig = field(default_factory=SteeringConfig)
    suspension: SuspensionConfig = field(default_factory=SuspensionConfig)
    mesh_paths: Dict[str, str] = field(default_factory=dict)
    mass: float = 1500.0                      # Vehicle mass in kg
    max_speed: float = 200.0                  # Max speed in km/h
    acceleration: float = 5.0                 # 0-100 km/h in seconds
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_steering_wheels(self) -> List[WheelConfig]:
        """Get all wheels that can steer."""
        return [w for w in self.wheels if w.steering]

    def get_driven_wheels(self) -> List[WheelConfig]:
        """Get all wheels that are powered."""
        return [w for w in self.wheels if w.driven]

    def get_wheel_by_id(self, wheel_id: str) -> Optional[WheelConfig]:
        """Get a wheel by its ID."""
        for wheel in self.wheels:
            if wheel.id == wheel_id:
                return wheel
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'vehicle_type': self.vehicle_type.value,
            'dimensions': self.dimensions.to_dict(),
            'wheels': [w.to_dict() for w in self.wheels],
            'steering': self.steering.to_dict(),
            'suspension': self.suspension.to_dict(),
            'mesh_paths': self.mesh_paths,
            'mass': self.mass,
            'max_speed': self.max_speed,
            'acceleration': self.acceleration,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VehicleConfig':
        """Deserialize from dictionary."""
        wheels = [WheelConfig.from_dict(w) for w in data.get('wheels', [])]

        dims_data = data.get('dimensions', {})
        dimensions = VehicleDimensions.from_dict(dims_data) if dims_data else VehicleDimensions()

        steer_data = data.get('steering', {})
        steering = SteeringConfig.from_dict(steer_data) if steer_data else SteeringConfig()

        susp_data = data.get('suspension', {})
        suspension = SuspensionConfig.from_dict(susp_data) if susp_data else SuspensionConfig()

        return cls(
            id=data['id'],
            name=data['name'],
            vehicle_type=VehicleType(data.get('vehicle_type', 'automobile')),
            dimensions=dimensions,
            wheels=wheels,
            steering=steering,
            suspension=suspension,
            mesh_paths=data.get('mesh_paths', {}),
            mass=data.get('mass', 1500.0),
            max_speed=data.get('max_speed', 200.0),
            acceleration=data.get('acceleration', 5.0),
            metadata=data.get('metadata', {}),
        )


@dataclass
class LaunchConfig:
    """Configuration for a vehicle launch sequence."""
    vehicle_id: str
    start_frame: int = 1
    target_speed: float = 60.0                # km/h
    acceleration: float = 5.0                 # m/s²
    path_curve: Optional[str] = None
    countdown_seconds: int = 3
    hold_at_end: bool = True
    easing: str = "ease_out"                  # Easing type

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'vehicle_id': self.vehicle_id,
            'start_frame': self.start_frame,
            'target_speed': self.target_speed,
            'acceleration': self.acceleration,
            'path_curve': self.path_curve,
            'countdown_seconds': self.countdown_seconds,
            'hold_at_end': self.hold_at_end,
            'easing': self.easing,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LaunchConfig':
        """Deserialize from dictionary."""
        return cls(
            vehicle_id=data['vehicle_id'],
            start_frame=data.get('start_frame', 1),
            target_speed=data.get('target_speed', 60.0),
            acceleration=data.get('acceleration', 5.0),
            path_curve=data.get('path_curve'),
            countdown_seconds=data.get('countdown_seconds', 3),
            hold_at_end=data.get('hold_at_end', True),
            easing=data.get('easing', 'ease_out'),
        )


@dataclass
class StuntMarker:
    """Marker for a stunt event in timeline."""
    frame: int
    stunt_type: StuntType
    vehicles: List[str]
    duration_frames: int = 24
    intensity: float = 1.0                    # 0-1, affects how extreme
    notes: str = ""
    start_position: Optional[Tuple[float, float, float]] = None
    end_position: Optional[Tuple[float, float, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'frame': self.frame,
            'stunt_type': self.stunt_type.value,
            'vehicles': self.vehicles,
            'duration_frames': self.duration_frames,
            'intensity': self.intensity,
            'notes': self.notes,
            'start_position': list(self.start_position) if self.start_position else None,
            'end_position': list(self.end_position) if self.end_position else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StuntMarker':
        """Deserialize from dictionary."""
        return cls(
            frame=data['frame'],
            stunt_type=StuntType(data['stunt_type']),
            vehicles=data.get('vehicles', []),
            duration_frames=data.get('duration_frames', 24),
            intensity=data.get('intensity', 1.0),
            notes=data.get('notes', ''),
            start_position=tuple(data['start_position']) if data.get('start_position') else None,
            end_position=tuple(data['end_position']) if data.get('end_position') else None,
        )


@dataclass
class DriverProfile:
    """Profile for how a vehicle is driven."""
    name: str
    skill_level: float = 1.0                  # 0-1 (0=amateur, 1=expert)
    aggression: float = 0.5                   # 0-1 (0=cautious, 1=aggressive)
    smoothness: float = 0.8                   # 0-1 (0=jerky, 1=smooth)
    consistency: float = 0.9                  # 0-1 (0=variable, 1=consistent)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'skill_level': self.skill_level,
            'aggression': self.aggression,
            'smoothness': self.smoothness,
            'consistency': self.consistency,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DriverProfile':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            skill_level=data.get('skill_level', 1.0),
            aggression=data.get('aggression', 0.5),
            smoothness=data.get('smoothness', 0.8),
            consistency=data.get('consistency', 0.9),
        )


# Preset driver profiles
DRIVER_PRESETS = {
    "stunt_driver": DriverProfile(
        name="Stunt Driver",
        skill_level=1.0,
        aggression=0.8,
        smoothness=0.95,
        consistency=0.95
    ),
    "race_driver": DriverProfile(
        name="Race Driver",
        skill_level=0.95,
        aggression=0.9,
        smoothness=0.85,
        consistency=0.9
    ),
    "average_driver": DriverProfile(
        name="Average Driver",
        skill_level=0.5,
        aggression=0.3,
        smoothness=0.6,
        consistency=0.5
    ),
    "nervous_driver": DriverProfile(
        name="Nervous Driver",
        skill_level=0.3,
        aggression=0.1,
        smoothness=0.3,
        consistency=0.2
    ),
}


# =============================================================================
# Phase 13.7: Animation Layers Types
# =============================================================================


class LayerType(Enum):
    """Types of animation layers."""
    BASE = "base"           # Foundation layer (only one)
    OVERRIDE = "override"   # Replace values
    ADDITIVE = "additive"   # Add to values
    MIX = "mix"             # Blend with previous


@dataclass
class BoneKeyframe:
    """Transform data for a single bone at a frame."""
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Euler degrees
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'location': list(self.location),
            'rotation': list(self.rotation),
            'scale': list(self.scale),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoneKeyframe':
        """Deserialize from dictionary."""
        return cls(
            location=tuple(data.get('location', (0.0, 0.0, 0.0))),
            rotation=tuple(data.get('rotation', (0.0, 0.0, 0.0))),
            scale=tuple(data.get('scale', (1.0, 1.0, 1.0))),
        )


@dataclass
class LayerKeyframe:
    """Keyframe data for an animation layer."""
    frame: int
    bones: Dict[str, BoneKeyframe] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'frame': self.frame,
            'bones': {k: v.to_dict() for k, v in self.bones.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayerKeyframe':
        """Deserialize from dictionary."""
        bones = {}
        for bone_name, bone_data in data.get('bones', {}).items():
            bones[bone_name] = BoneKeyframe.from_dict(bone_data)
        return cls(
            frame=data['frame'],
            bones=bones,
        )


@dataclass
class AnimationLayer:
    """A single animation layer."""
    id: str
    name: str
    layer_type: LayerType = LayerType.ADDITIVE
    opacity: float = 1.0
    mute: bool = False
    solo: bool = False
    bone_mask: List[str] = field(default_factory=list)  # Empty = all bones
    keyframes: List[LayerKeyframe] = field(default_factory=list)
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'layer_type': self.layer_type.value,
            'opacity': self.opacity,
            'mute': self.mute,
            'solo': self.solo,
            'bone_mask': self.bone_mask,
            'keyframes': [k.to_dict() for k in self.keyframes],
            'order': self.order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnimationLayer':
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            layer_type=LayerType(data.get('layer_type', 'additive')),
            opacity=data.get('opacity', 1.0),
            mute=data.get('mute', False),
            solo=data.get('solo', False),
            bone_mask=data.get('bone_mask', []),
            keyframes=[LayerKeyframe.from_dict(k) for k in data.get('keyframes', [])],
            order=data.get('order', 0),
        )


@dataclass
class LayerStack:
    """Stack of animation layers for a rig."""
    rig_id: str
    layers: List[AnimationLayer] = field(default_factory=list)
    active_layer: Optional[str] = None

    def get_layer(self, layer_id: str) -> Optional[AnimationLayer]:
        """Get a layer by ID."""
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None

    def get_visible_layers(self) -> List[AnimationLayer]:
        """Get layers that contribute to final animation."""
        # If any layer is soloed, only show solo layers
        solo_layers = [l for l in self.layers if l.solo and not l.mute]
        if solo_layers:
            return solo_layers

        # Otherwise, show non-muted layers
        return [l for l in self.layers if not l.mute]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'rig_id': self.rig_id,
            'layers': [l.to_dict() for l in self.layers],
            'active_layer': self.active_layer,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayerStack':
        """Deserialize from dictionary."""
        return cls(
            rig_id=data['rig_id'],
            layers=[AnimationLayer.from_dict(l) for l in data.get('layers', [])],
            active_layer=data.get('active_layer'),
        )


@dataclass
class LayerPreset:
    """Preset for animation layer setup."""
    name: str
    description: str = ""
    layers: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'layers': self.layers,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayerPreset':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            layers=data.get('layers', []),
        )
