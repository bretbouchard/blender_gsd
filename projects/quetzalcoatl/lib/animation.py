"""
Animation Prep System (Phase 20.10)

Prepares creature for animation: rigging data, bone definitions, weight painting data.

Universal Stage Order:
- Stage 0: Normalize (parameter validation)
- Stage 1: Primary (spine bones)
- Stage 2: Secondary (limb bones, wing bones)
- Stage 3: Detail (facial bones, detail bones)
- Stage 4: Output Prep (weight data, constraints)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple
import numpy as np


class BoneType(Enum):
    """Types of bones in the rig."""
    SPINE = 0         # Main spine bones
    NECK = 1          # Neck bones
    HEAD = 2          # Head bone
    TAIL = 3          # Tail bones
    LEG = 4           # Leg bones (upper/lower/foot)
    WING = 5          # Wing bones
    CLAW = 6          # Claw/toe bones
    FACIAL = 7        # Facial bones
    FIN = 8           # Fin/crest bones


class RigType(Enum):
    """Types of rigs to generate."""
    SIMPLE = 0        # Simple spine-only rig
    STANDARD = 1      # Standard with limbs
    FULL = 2          # Full rig with all features
    GAME_READY = 3    # Game-optimized rig


@dataclass
class BoneDefinition:
    """Definition of a single bone."""
    name: str
    bone_type: BoneType
    head_position: np.ndarray
    tail_position: np.ndarray
    parent: Optional[str] = None
    roll: float = 0.0
    use_connect: bool = False
    layers: List[bool] = field(default_factory=lambda: [True] + [False] * 31)

    @property
    def length(self) -> float:
        return np.linalg.norm(self.tail_position - self.head_position)

    @property
    def direction(self) -> np.ndarray:
        diff = self.tail_position - self.head_position
        length = np.linalg.norm(diff)
        if length > 0.001:
            return diff / length
        return np.array([0.0, 1.0, 0.0])


@dataclass
class BoneGroup:
    """A group of related bones."""
    name: str
    bone_type: BoneType
    bone_names: List[str]
    symmetry: Optional[str] = None  # "left" or "right" for paired bones


@dataclass
class WeightPaintData:
    """Weight painting data for a bone."""
    bone_name: str
    vertex_indices: np.ndarray
    weights: np.ndarray

    @property
    def vertex_count(self) -> int:
        return len(self.vertex_indices)


@dataclass
class IKConstraint:
    """IK constraint configuration."""
    bone_name: str
    target: str
    chain_length: int
    pole_target: Optional[str] = None
    pole_angle: float = 0.0
    iterations: int = 10


@dataclass
class RigConfig:
    """Configuration for rig generation."""
    rig_type: RigType = RigType.STANDARD
    spine_bone_count: int = 12
    neck_bone_count: int = 3
    tail_bone_count: int = 8
    leg_pairs: int = 2
    wing_pairs: int = 1
    toe_count: int = 4
    finger_count: int = 4
    generate_facial: bool = False
    generate_ik: bool = True


@dataclass
class RigResult:
    """Result from rig generation."""
    bones: List[BoneDefinition]
    bone_groups: List[BoneGroup]
    weights: List[WeightPaintData]
    ik_constraints: List[IKConstraint]
    root_bone: str
    deform_bones: List[str]

    @property
    def bone_count(self) -> int:
        return len(self.bones)

    @property
    def deform_bone_count(self) -> int:
        return len(self.deform_bones)


class RigGenerator:
    """Generates rig data for the creature."""

    def __init__(self, config: RigConfig):
        """Initialize rig generator.

        Args:
            config: Rig configuration
        """
        self.config = config

    def generate(
        self,
        spine_curve: Optional[np.ndarray] = None,
        body_vertices: Optional[np.ndarray] = None,
        body_regions: Optional[np.ndarray] = None,
    ) -> RigResult:
        """Generate rig data.

        Args:
            spine_curve: Points along spine (N, 3)
            body_vertices: Body mesh vertices
            body_regions: Region index per vertex

        Returns:
            RigResult with all rig data
        """
        bones: List[BoneDefinition] = []
        bone_groups: List[BoneGroup] = []
        weights: List[WeightPaintData] = []
        ik_constraints: List[IKConstraint] = []

        # Generate default spine curve if none provided
        if spine_curve is None:
            spine_curve = self._generate_default_spine()

        # Stage 1: Generate spine bones
        spine_bones = self._generate_spine_bones(spine_curve)
        bones.extend(spine_bones)

        spine_group = BoneGroup(
            name="spine",
            bone_type=BoneType.SPINE,
            bone_names=[b.name for b in spine_bones],
        )
        bone_groups.append(spine_group)

        # Stage 2: Generate neck and head
        if self.config.rig_type.value >= RigType.STANDARD.value:
            neck_bones, head_bone = self._generate_neck_head(spine_curve)
            bones.extend(neck_bones)
            bones.append(head_bone)

            neck_group = BoneGroup(
                name="neck",
                bone_type=BoneType.NECK,
                bone_names=[b.name for b in neck_bones],
            )
            bone_groups.append(neck_group)

        # Stage 3: Generate tail
        if self.config.tail_bone_count > 0:
            tail_bones = self._generate_tail(spine_curve)
            bones.extend(tail_bones)

            tail_group = BoneGroup(
                name="tail",
                bone_type=BoneType.TAIL,
                bone_names=[b.name for b in tail_bones],
            )
            bone_groups.append(tail_group)

        # Stage 4: Generate limbs
        if self.config.leg_pairs > 0 and self.config.rig_type.value >= RigType.STANDARD.value:
            for pair in range(self.config.leg_pairs):
                for side in ["left", "right"]:
                    leg_bones = self._generate_leg_bones(spine_curve, pair, side)
                    bones.extend(leg_bones)

                    # Add IK if enabled
                    if self.config.generate_ik:
                        ik = self._create_leg_ik(leg_bones, side)
                        ik_constraints.append(ik)

        # Stage 5: Generate wings
        if self.config.wing_pairs > 0 and self.config.rig_type.value >= RigType.FULL.value:
            for pair in range(self.config.wing_pairs):
                for side in ["left", "right"]:
                    wing_bones = self._generate_wing_bones(spine_curve, side)
                    bones.extend(wing_bones)

        # Generate weights
        if body_vertices is not None:
            weights = self._generate_weights(body_vertices, bones, body_regions)

        # Find root bone
        root_bone = bones[0].name if bones else "root"

        # Collect deform bones
        deform_bones = [b.name for b in bones]

        return RigResult(
            bones=bones,
            bone_groups=bone_groups,
            weights=weights,
            ik_constraints=ik_constraints,
            root_bone=root_bone,
            deform_bones=deform_bones,
        )

    def _generate_default_spine(self) -> np.ndarray:
        """Generate a default spine curve."""
        count = self.config.spine_bone_count + 1
        t = np.linspace(0, 1, count)
        y = t * 10.0  # Length
        x = np.sin(t * np.pi * 2) * 0.5  # Slight wave
        z = np.zeros(count)
        return np.column_stack([x, y, z])

    def _generate_spine_bones(self, spine_curve: np.ndarray) -> List[BoneDefinition]:
        """Generate spine bones from curve."""
        bones = []
        n_points = len(spine_curve)

        bone_count = min(self.config.spine_bone_count, n_points - 1)
        indices = np.linspace(0, n_points - 1, bone_count + 1, dtype=int)

        for i in range(bone_count):
            head = spine_curve[indices[i]]
            tail = spine_curve[indices[i + 1]]

            bone = BoneDefinition(
                name=f"spine_{i:02d}",
                bone_type=BoneType.SPINE,
                head_position=head.copy(),
                tail_position=tail.copy(),
                parent=f"spine_{i-1:02d}" if i > 0 else None,
                use_connect=i > 0,
            )
            bones.append(bone)

        return bones

    def _generate_neck_head(
        self,
        spine_curve: np.ndarray,
    ) -> Tuple[List[BoneDefinition], BoneDefinition]:
        """Generate neck and head bones."""
        neck_bones = []

        # Neck extends from front of spine
        head_pos = spine_curve[-1]
        neck_length = 0.5
        neck_up = np.array([0.0, 1.0, 0.5])
        neck_up = neck_up / np.linalg.norm(neck_up)

        prev_name = f"spine_{self.config.spine_bone_count-1:02d}"

        for i in range(self.config.neck_bone_count):
            t = (i + 1) / (self.config.neck_bone_count + 1)
            head = head_pos + neck_up * neck_length * (i / (self.config.neck_bone_count + 1))
            tail = head_pos + neck_up * neck_length * ((i + 1) / (self.config.neck_bone_count + 1))

            bone = BoneDefinition(
                name=f"neck_{i:02d}",
                bone_type=BoneType.NECK,
                head_position=head,
                tail_position=tail,
                parent=prev_name,
                use_connect=True,
            )
            neck_bones.append(bone)
            prev_name = bone.name

        # Head bone
        neck_end = neck_bones[-1].tail_position if neck_bones else head_pos
        head_dir = np.array([0.0, 1.0, 0.2])
        head_dir = head_dir / np.linalg.norm(head_dir)

        head_bone = BoneDefinition(
            name="head",
            bone_type=BoneType.HEAD,
            head_position=neck_end,
            tail_position=neck_end + head_dir * 0.4,
            parent=prev_name,
        )

        return neck_bones, head_bone

    def _generate_tail(self, spine_curve: np.ndarray) -> List[BoneDefinition]:
        """Generate tail bones."""
        tail_bones = []

        # Tail extends from back of spine
        tail_base = spine_curve[0]
        tail_dir = np.array([0.0, -1.0, 0.0])
        tail_length = 2.0

        prev_name = "spine_00"

        for i in range(self.config.tail_bone_count):
            t = (i + 1) / (self.config.tail_bone_count + 1)
            head = tail_base + tail_dir * tail_length * (i / (self.config.tail_bone_count + 1))
            tail = tail_base + tail_dir * tail_length * ((i + 1) / (self.config.tail_bone_count + 1))

            bone = BoneDefinition(
                name=f"tail_{i:02d}",
                bone_type=BoneType.TAIL,
                head_position=head,
                tail_position=tail,
                parent=prev_name if i == 0 else f"tail_{i-1:02d}",
                use_connect=True,
            )
            tail_bones.append(bone)

        return tail_bones

    def _generate_leg_bones(
        self,
        spine_curve: np.ndarray,
        pair_index: int,
        side: str,
    ) -> List[BoneDefinition]:
        """Generate leg bones for one leg."""
        bones = []

        # Position along spine for this leg pair
        t = 0.3 + pair_index * 0.2
        spine_idx = int(t * len(spine_curve))
        spine_idx = min(spine_idx, len(spine_curve) - 1)

        attach_pos = spine_curve[spine_idx]
        side_mult = 1.0 if side == "right" else -1.0

        # Upper leg
        upper_length = 0.5
        upper_pos = attach_pos + np.array([side_mult * 0.3, 0.0, 0.0])
        upper_end = upper_pos + np.array([side_mult * 0.1, 0.0, -upper_length])

        upper_bone = BoneDefinition(
            name=f"upper_leg_{side[:1]}{pair_index}",
            bone_type=BoneType.LEG,
            head_position=upper_pos,
            tail_position=upper_end,
            parent=f"spine_{spine_idx:02d}",
        )
        bones.append(upper_bone)

        # Lower leg
        lower_length = 0.4
        lower_end = upper_end + np.array([0.0, 0.0, -lower_length])

        lower_bone = BoneDefinition(
            name=f"lower_leg_{side[:1]}{pair_index}",
            bone_type=BoneType.LEG,
            head_position=upper_end,
            tail_position=lower_end,
            parent=upper_bone.name,
            use_connect=True,
        )
        bones.append(lower_bone)

        # Foot
        foot_end = lower_end + np.array([0.0, 0.1, -0.1])

        foot_bone = BoneDefinition(
            name=f"foot_{side[:1]}{pair_index}",
            bone_type=BoneType.LEG,
            head_position=lower_end,
            tail_position=foot_end,
            parent=lower_bone.name,
            use_connect=True,
        )
        bones.append(foot_bone)

        # Toes
        for toe in range(self.config.toe_count):
            toe_offset = (toe - self.config.toe_count / 2) * 0.05
            toe_end = foot_end + np.array([toe_offset, 0.15, -0.05])

            toe_bone = BoneDefinition(
                name=f"toe_{side[:1]}{pair_index}_{toe}",
                bone_type=BoneType.CLAW,
                head_position=foot_end.copy(),
                tail_position=toe_end,
                parent=foot_bone.name,
            )
            bones.append(toe_bone)

        return bones

    def _generate_wing_bones(
        self,
        spine_curve: np.ndarray,
        side: str,
    ) -> List[BoneDefinition]:
        """Generate wing bones for one wing."""
        bones = []

        # Wings attach near the front
        spine_idx = int(0.7 * len(spine_curve))
        attach_pos = spine_curve[spine_idx]
        side_mult = 1.0 if side == "right" else -1.0

        # Upper arm
        arm_length = 0.8
        arm_pos = attach_pos + np.array([side_mult * 0.4, 0.1, 0.2])
        arm_end = arm_pos + np.array([side_mult * arm_length, 0.0, 0.0])

        arm_bone = BoneDefinition(
            name=f"upper_arm_{side[:1]}",
            bone_type=BoneType.WING,
            head_position=arm_pos,
            tail_position=arm_end,
            parent=f"spine_{spine_idx:02d}",
        )
        bones.append(arm_bone)

        # Forearm
        forearm_length = 0.7
        forearm_end = arm_end + np.array([side_mult * forearm_length, 0.0, -0.1])

        forearm_bone = BoneDefinition(
            name=f"forearm_{side[:1]}",
            bone_type=BoneType.WING,
            head_position=arm_end,
            tail_position=forearm_end,
            parent=arm_bone.name,
            use_connect=True,
        )
        bones.append(forearm_bone)

        # Fingers
        for finger in range(self.config.finger_count):
            finger_length = 0.4 + finger * 0.1
            finger_end = forearm_end + np.array([
                side_mult * finger_length,
                0.0,
                -finger * 0.05,
            ])

            finger_bone = BoneDefinition(
                name=f"finger_{side[:1]}_{finger}",
                bone_type=BoneType.WING,
                head_position=forearm_end.copy(),
                tail_position=finger_end,
                parent=forearm_bone.name,
            )
            bones.append(finger_bone)

        return bones

    def _create_leg_ik(self, leg_bones: List[BoneDefinition], side: str) -> IKConstraint:
        """Create IK constraint for leg."""
        # Find the lower leg bone
        lower_leg = next((b for b in leg_bones if "lower_leg" in b.name), None)
        if lower_leg is None:
            lower_leg = leg_bones[1] if len(leg_bones) > 1 else leg_bones[0]

        foot = next((b for b in leg_bones if "foot" in b.name), None)

        return IKConstraint(
            bone_name=lower_leg.name,
            target=foot.name if foot else lower_leg.tail_position,
            chain_length=2,
        )

    def _generate_weights(
        self,
        vertices: np.ndarray,
        bones: List[BoneDefinition],
        body_regions: Optional[np.ndarray],
    ) -> List[WeightPaintData]:
        """Generate weight painting data."""
        weights = []

        for bone in bones:
            # Simple distance-based weighting
            bone_center = (bone.head_position + bone.tail_position) / 2
            bone_length = bone.length

            distances = np.linalg.norm(vertices - bone_center, axis=1)

            # Inverse distance weighting with falloff
            max_dist = bone_length * 2.0
            influence = np.maximum(0, 1.0 - distances / max_dist)

            # Only include vertices with significant influence
            mask = influence > 0.01
            if np.any(mask):
                weight_data = WeightPaintData(
                    bone_name=bone.name,
                    vertex_indices=np.where(mask)[0],
                    weights=influence[mask],
                )
                weights.append(weight_data)

        return weights


def generate_rig(
    rig_type: RigType = RigType.STANDARD,
    spine_curve: Optional[np.ndarray] = None,
    body_vertices: Optional[np.ndarray] = None,
    body_regions: Optional[np.ndarray] = None,
) -> RigResult:
    """Generate rig with simplified interface.

    Args:
        rig_type: Type of rig to generate
        spine_curve: Spine curve points
        body_vertices: Body mesh vertices
        body_regions: Region index per vertex

    Returns:
        RigResult with all rig data
    """
    config = RigConfig(rig_type=rig_type)
    gen = RigGenerator(config)
    return gen.generate(spine_curve, body_vertices, body_regions)


# Rig presets
RIG_PRESETS = {
    "simple": {
        "rig_type": RigType.SIMPLE,
        "spine_bone_count": 8,
        "leg_pairs": 0,
        "wing_pairs": 0,
    },
    "standard": {
        "rig_type": RigType.STANDARD,
        "spine_bone_count": 12,
        "leg_pairs": 2,
        "wing_pairs": 0,
    },
    "winged": {
        "rig_type": RigType.FULL,
        "spine_bone_count": 12,
        "leg_pairs": 2,
        "wing_pairs": 1,
    },
    "game_ready": {
        "rig_type": RigType.GAME_READY,
        "spine_bone_count": 6,
        "leg_pairs": 2,
        "wing_pairs": 1,
        "generate_ik": True,
    },
}


def get_rig_preset(name: str) -> Dict:
    """Get a rig preset by name."""
    return RIG_PRESETS.get(name, RIG_PRESETS["standard"])


def create_config_from_preset(name: str) -> RigConfig:
    """Create RigConfig from a preset."""
    preset = get_rig_preset(name)
    return RigConfig(**preset)
