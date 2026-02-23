"""
Rig Library

Manages rig templates and bone hierarchies for character animation.
Supports biped, quadruped, face rigs, and custom configurations.

Implements REQ-CH-02: Rig Library.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from pathlib import Path
import json


class RigType(Enum):
    """Rig type classification."""
    BIPED = "biped"           # Human-like
    QUADRUPED = "quadruped"   # Four-legged
    FACE = "face"            # Face-only rig
    HAND = "hand"            # Hand-only rig
    SPINE = "spine"          # Spine/tail only
    CUSTOM = "custom"        # Custom rig


class RigComplexity(Enum):
    """Rig complexity level."""
    SIMPLE = "simple"         # Basic controls
    STANDARD = "standard"     # Standard controls
    ADVANCED = "advanced"     # Full control set
    PRODUCTION = "production" # Production-ready with helpers


# =============================================================================
# STANDARD BONE DEFINITIONS
# =============================================================================

STANDARD_BONE_NAMES: Dict[str, Dict[str, str]] = {
    "spine": {
        "root": "root",
        "hips": "hips",
        "spine_01": "spine_01",
        "spine_02": "spine_02",
        "spine_03": "spine_03",
        "chest": "chest",
        "neck": "neck",
        "head": "head",
    },
    "arm_left": {
        "clavicle": "clavicle_L",
        "upper_arm": "upper_arm_L",
        "forearm": "forearm_L",
        "hand": "hand_L",
    },
    "arm_right": {
        "clavicle": "clavicle_R",
        "upper_arm": "upper_arm_R",
        "forearm": "forearm_R",
        "hand": "hand_R",
    },
    "leg_left": {
        "thigh": "thigh_L",
        "shin": "shin_L",
        "foot": "foot_L",
        "toe": "toe_L",
    },
    "leg_right": {
        "thigh": "thigh_R",
        "shin": "shin_R",
        "foot": "foot_R",
        "toe": "toe_R",
    },
    "finger_left": {
        "thumb_01": "thumb_01_L",
        "thumb_02": "thumb_02_L",
        "thumb_03": "thumb_03_L",
        "index_01": "index_01_L",
        "index_02": "index_02_L",
        "index_03": "index_03_L",
        "middle_01": "middle_01_L",
        "middle_02": "middle_02_L",
        "middle_03": "middle_03_L",
        "ring_01": "ring_01_L",
        "ring_02": "ring_02_L",
        "ring_03": "ring_03_L",
        "pinky_01": "pinky_01_L",
        "pinky_02": "pinky_02_L",
        "pinky_03": "pinky_03_L",
    },
    "finger_right": {
        "thumb_01": "thumb_01_R",
        "thumb_02": "thumb_02_R",
        "thumb_03": "thumb_03_R",
        "index_01": "index_01_R",
        "index_02": "index_02_R",
        "index_03": "index_03_R",
        "middle_01": "middle_01_R",
        "middle_02": "middle_02_R",
        "middle_03": "middle_03_R",
        "ring_01": "ring_01_R",
        "ring_02": "ring_02_R",
        "ring_03": "ring_03_R",
        "pinky_01": "pinky_01_R",
        "pinky_02": "pinky_02_R",
        "pinky_03": "pinky_03_R",
    },
}

FACE_RIG_BONES: Dict[str, List[str]] = {
    "eyes": [
        "eye_L", "eye_R",
        "eyelid_top_L", "eyelid_top_R",
        "eyelid_bottom_L", "eyelid_bottom_R",
    ],
    "brows": [
        "brow_inner_L", "brow_inner_R",
        "brow_mid_L", "brow_mid_R",
        "brow_outer_L", "brow_outer_R",
    ],
    "mouth": [
        "jaw",
        "lip_top", "lip_bottom",
        "lip_corner_L", "lip_corner_R",
        "cheek_L", "cheek_R",
    ],
    "nose": [
        "nose",
        "nostril_L", "nostril_R",
    ],
    "ears": [
        "ear_L", "ear_R",
    ],
}


# =============================================================================
# RIG PRESETS
# =============================================================================

RIG_PRESETS: Dict[str, Dict[str, Any]] = {
    "human_biped": {
        "name": "Human Biped",
        "rig_type": "biped",
        "complexity": "standard",
        "bone_count": 65,
        "description": "Standard humanoid rig for human characters",
        "features": ["ik_legs", "ik_arms", "spine_ik", "finger_controls"],
        "bone_groups": ["spine", "arm_left", "arm_right", "leg_left", "leg_right", "finger_left", "finger_right"],
    },
    "human_biped_advanced": {
        "name": "Human Biped Advanced",
        "rig_type": "biped",
        "complexity": "advanced",
        "bone_count": 120,
        "description": "Advanced humanoid rig with extra controls",
        "features": ["ik_legs", "ik_arms", "spine_ik", "finger_controls", "stretchy_ik", "bendy_bones", "tweaks"],
        "bone_groups": ["spine", "arm_left", "arm_right", "leg_left", "leg_right", "finger_left", "finger_right"],
    },
    "quadruped_basic": {
        "name": "Quadruped Basic",
        "rig_type": "quadruped",
        "complexity": "standard",
        "bone_count": 85,
        "description": "Four-legged rig for animals",
        "features": ["ik_legs", "spine_ik", "tail", "ear_controls"],
        "bone_groups": ["spine", "front_left_leg", "front_right_leg", "hind_left_leg", "hind_right_leg"],
    },
    "face_rig": {
        "name": "Face Rig",
        "rig_type": "face",
        "complexity": "advanced",
        "bone_count": 50,
        "description": "Facial animation rig",
        "features": ["eye_controls", "brow_controls", "mouth_controls", "jaw_control"],
        "bone_groups": ["eyes", "brows", "mouth", "nose", "ears"],
    },
    "hand_rig": {
        "name": "Hand Rig",
        "rig_type": "hand",
        "complexity": "standard",
        "bone_count": 30,
        "description": "Detailed hand rig",
        "features": ["finger_ik", "spread_controls", "curl_controls"],
        "bone_groups": ["finger_left", "finger_right"],
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BoneSpec:
    """
    Bone specification.

    Attributes:
        name: Bone name
        parent: Parent bone name
        head: Head position
        tail: Tail position
        roll: Bone roll angle
        use_connect: Connect to parent
        use_deform: Used for deformation
        layers: Bone layer assignment
        constraints: Bone constraints
    """
    name: str = ""
    parent: str = ""
    head: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    tail: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    roll: float = 0.0
    use_connect: bool = False
    use_deform: bool = True
    layers: List[bool] = field(default_factory=lambda: [True] + [False] * 31)
    constraints: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "parent": self.parent,
            "head": list(self.head),
            "tail": list(self.tail),
            "roll": self.roll,
            "use_connect": self.use_connect,
            "use_deform": self.use_deform,
            "layers": self.layers,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BoneSpec":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            parent=data.get("parent", ""),
            head=tuple(data.get("head", [0.0, 0.0, 0.0])),
            tail=tuple(data.get("tail", [0.0, 0.0, 0.0])),
            roll=data.get("roll", 0.0),
            use_connect=data.get("use_connect", False),
            use_deform=data.get("use_deform", True),
            layers=data.get("layers", [True] + [False] * 31),
            constraints=data.get("constraints", []),
        )


@dataclass
class FaceRigConfig:
    """
    Face rig configuration.

    Attributes:
        config_id: Configuration ID
        name: Display name
        eye_bones: Eye bone configuration
        brow_bones: Brow bone configuration
        mouth_bones: Mouth bone configuration
        use_shape_keys: Use shape keys instead of bones
        viseme_count: Number of visemes for lip sync
        expression_count: Number of expression channels
    """
    config_id: str = ""
    name: str = ""
    eye_bones: Dict[str, Any] = field(default_factory=dict)
    brow_bones: Dict[str, Any] = field(default_factory=dict)
    mouth_bones: Dict[str, Any] = field(default_factory=dict)
    use_shape_keys: bool = False
    viseme_count: int = 15
    expression_count: int = 50

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_id": self.config_id,
            "name": self.name,
            "eye_bones": self.eye_bones,
            "brow_bones": self.brow_bones,
            "mouth_bones": self.mouth_bones,
            "use_shape_keys": self.use_shape_keys,
            "viseme_count": self.viseme_count,
            "expression_count": self.expression_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FaceRigConfig":
        """Create from dictionary."""
        return cls(
            config_id=data.get("config_id", ""),
            name=data.get("name", ""),
            eye_bones=data.get("eye_bones", {}),
            brow_bones=data.get("brow_bones", {}),
            mouth_bones=data.get("mouth_bones", {}),
            use_shape_keys=data.get("use_shape_keys", False),
            viseme_count=data.get("viseme_count", 15),
            expression_count=data.get("expression_count", 50),
        )


@dataclass
class RigSpec:
    """
    Complete rig specification.

    Attributes:
        rig_id: Unique rig identifier
        name: Display name
        rig_type: Type classification
        complexity: Complexity level
        bones: Bone specifications
        ik_chains: IK chain definitions
        face_config: Face rig configuration
        control_shapes: Control shape definitions
        metadata: Rig metadata
    """
    rig_id: str = ""
    name: str = ""
    rig_type: str = "biped"
    complexity: str = "standard"
    bones: List[BoneSpec] = field(default_factory=list)
    ik_chains: Dict[str, Any] = field(default_factory=dict)
    face_config: Optional[FaceRigConfig] = None
    control_shapes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rig_id": self.rig_id,
            "name": self.name,
            "rig_type": self.rig_type,
            "complexity": self.complexity,
            "bones": [b.to_dict() for b in self.bones],
            "ik_chains": self.ik_chains,
            "face_config": self.face_config.to_dict() if self.face_config else None,
            "control_shapes": self.control_shapes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RigSpec":
        """Create from dictionary."""
        face_config = None
        if data.get("face_config"):
            face_config = FaceRigConfig.from_dict(data["face_config"])

        return cls(
            rig_id=data.get("rig_id", ""),
            name=data.get("name", ""),
            rig_type=data.get("rig_type", "biped"),
            complexity=data.get("complexity", "standard"),
            bones=[BoneSpec.from_dict(b) for b in data.get("bones", [])],
            ik_chains=data.get("ik_chains", {}),
            face_config=face_config,
            control_shapes=data.get("control_shapes", {}),
            metadata=data.get("metadata", {}),
        )


# =============================================================================
# RIG LIBRARY CLASS
# =============================================================================

class RigLibrary:
    """
    Manages rig templates and configurations.

    Provides access to standard rig presets and custom rigs.

    Usage:
        library = RigLibrary()
        biped = library.get_rig("human_biped")
        library.create_custom_rig("my_rig", base="human_biped")
    """

    def __init__(self, library_path: Optional[str] = None):
        """
        Initialize rig library.

        Args:
            library_path: Path to custom rigs directory
        """
        self.rigs: Dict[str, RigSpec] = {}
        self._load_presets()

        if library_path:
            self.load_library(library_path)

    def _load_presets(self) -> None:
        """Load built-in rig presets."""
        for preset_id, preset_data in RIG_PRESETS.items():
            rig = RigSpec(
                rig_id=preset_id,
                name=preset_data.get("name", preset_id),
                rig_type=preset_data.get("rig_type", "biped"),
                complexity=preset_data.get("complexity", "standard"),
                metadata={
                    "bone_count": preset_data.get("bone_count", 0),
                    "description": preset_data.get("description", ""),
                    "features": preset_data.get("features", []),
                    "bone_groups": preset_data.get("bone_groups", []),
                },
            )
            self.rigs[preset_id] = rig

    def load_library(self, path: str) -> int:
        """
        Load rigs from directory.

        Args:
            path: Directory path

        Returns:
            Number of rigs loaded
        """
        lib_path = Path(path)
        count = 0

        for rig_file in lib_path.glob("*.json"):
            try:
                with open(rig_file, "r") as f:
                    data = json.load(f)
                rig = RigSpec.from_dict(data)
                self.rigs[rig.rig_id] = rig
                count += 1
            except (json.JSONDecodeError, KeyError):
                continue

        return count

    def save_library(self, path: str) -> None:
        """
        Save custom rigs to directory.

        Args:
            path: Directory path
        """
        lib_path = Path(path)
        lib_path.mkdir(parents=True, exist_ok=True)

        for rig_id, rig in self.rigs.items():
            # Skip presets
            if rig_id in RIG_PRESETS:
                continue

            rig_file = lib_path / f"{rig_id}.json"
            with open(rig_file, "w") as f:
                json.dump(rig.to_dict(), f, indent=2)

    def get_rig(self, rig_id: str) -> Optional[RigSpec]:
        """Get rig by ID."""
        return self.rigs.get(rig_id)

    def list_rigs(
        self,
        rig_type: Optional[str] = None,
        complexity: Optional[str] = None,
    ) -> List[RigSpec]:
        """
        List available rigs.

        Args:
            rig_type: Filter by type
            complexity: Filter by complexity

        Returns:
            List of matching rigs
        """
        results = []
        for rig in self.rigs.values():
            if rig_type and rig.rig_type != rig_type:
                continue
            if complexity and rig.complexity != complexity:
                continue
            results.append(rig)
        return results

    def create_custom_rig(
        self,
        rig_id: str,
        name: str,
        base: Optional[str] = None,
        rig_type: str = "custom",
        complexity: str = "standard",
    ) -> RigSpec:
        """
        Create new custom rig.

        Args:
            rig_id: Unique rig identifier
            name: Display name
            base: Base rig to copy from
            rig_type: Rig type
            complexity: Complexity level

        Returns:
            New RigSpec
        """
        if base and base in self.rigs:
            base_rig = self.rigs[base]
            new_rig = RigSpec(
                rig_id=rig_id,
                name=name,
                rig_type=rig_type,
                complexity=complexity,
                bones=list(base_rig.bones),
                ik_chains=dict(base_rig.ik_chains),
                metadata=dict(base_rig.metadata),
            )
        else:
            new_rig = RigSpec(
                rig_id=rig_id,
                name=name,
                rig_type=rig_type,
                complexity=complexity,
            )

        self.rigs[rig_id] = new_rig
        return new_rig

    def add_bone(
        self,
        rig_id: str,
        bone: BoneSpec,
    ) -> bool:
        """
        Add bone to rig.

        Args:
            rig_id: Rig to modify
            bone: Bone specification

        Returns:
            Success status
        """
        rig = self.rigs.get(rig_id)
        if not rig:
            return False

        rig.bones.append(bone)
        return True

    def add_ik_chain(
        self,
        rig_id: str,
        chain_name: str,
        chain_bones: List[str],
        target: str,
        pole_target: Optional[str] = None,
    ) -> bool:
        """
        Add IK chain to rig.

        Args:
            rig_id: Rig to modify
            chain_name: Chain identifier
            chain_bones: Bones in chain
            target: IK target bone
            pole_target: Optional pole target

        Returns:
            Success status
        """
        rig = self.rigs.get(rig_id)
        if not rig:
            return False

        rig.ik_chains[chain_name] = {
            "bones": chain_bones,
            "target": target,
            "pole_target": pole_target,
        }
        return True

    def get_bone_hierarchy(self, rig_id: str) -> Dict[str, Any]:
        """
        Get bone hierarchy as tree.

        Args:
            rig_id: Rig ID

        Returns:
            Bone hierarchy tree
        """
        rig = self.rigs.get(rig_id)
        if not rig:
            return {}

        # Build hierarchy
        children: Dict[str, List[str]] = {}
        roots = []

        for bone in rig.bones:
            if bone.parent:
                if bone.parent not in children:
                    children[bone.parent] = []
                children[bone.parent].append(bone.name)
            else:
                roots.append(bone.name)

        def build_tree(bone_name: str) -> Dict[str, Any]:
            return {
                "name": bone_name,
                "children": [
                    build_tree(child)
                    for child in children.get(bone_name, [])
                ],
            }

        return {
            "roots": [build_tree(root) for root in roots],
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics."""
        stats = {
            "total_rigs": len(self.rigs),
            "by_type": {},
            "by_complexity": {},
        }

        for rig in self.rigs.values():
            stats["by_type"][rig.rig_type] = stats["by_type"].get(rig.rig_type, 0) + 1
            stats["by_complexity"][rig.complexity] = stats["by_complexity"].get(rig.complexity, 0) + 1

        return stats


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_rig_template(
    template_id: str,
    custom_path: Optional[str] = None,
) -> Optional[RigSpec]:
    """
    Load rig template by ID.

    Args:
        template_id: Template identifier
        custom_path: Optional custom rigs path

    Returns:
        RigSpec or None
    """
    library = RigLibrary(custom_path)
    return library.get_rig(template_id)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RigType",
    "RigComplexity",
    # Data classes
    "RigSpec",
    "BoneSpec",
    "FaceRigConfig",
    # Constants
    "STANDARD_BONE_NAMES",
    "FACE_RIG_BONES",
    "RIG_PRESETS",
    # Classes
    "RigLibrary",
    # Functions
    "load_rig_template",
]
