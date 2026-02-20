"""
Pose Library Module

Pose storage, retrieval, and management for character animation.

Phase 13.2: Pose Library (REQ-ANIM-04)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
from pathlib import Path
import json
import math
from datetime import datetime

from .types import Pose, BonePose, PoseCategory, PoseLibraryConfig

if TYPE_CHECKING:
    import bpy

# Default pose config directory
POSE_CONFIG_ROOT = Path(__file__).parent.parent.parent / "configs" / "animation" / "poses"


class PoseLibrary:
    """
    Manages pose storage, retrieval, and organization.

    Provides methods for capturing, saving, loading, and applying poses
    to armatures.
    """

    def __init__(self, rig_type: str = "human_biped", config_root: Optional[Path] = None):
        """
        Initialize pose library.

        Args:
            rig_type: Type of rig (human_biped, quadruped, etc.)
            config_root: Root directory for pose configs
        """
        self.rig_type = rig_type
        self.config_root = config_root or POSE_CONFIG_ROOT
        self.poses: Dict[str, Pose] = {}
        self._cache: Dict[str, float] = {}  # File modification times
        self._load_all_poses()

    def _load_all_poses(self) -> None:
        """Load all poses from config directory."""
        if not self.config_root.exists():
            return

        for category_dir in self.config_root.iterdir():
            if category_dir.is_dir():
                for pose_file in category_dir.glob("*.yaml"):
                    try:
                        pose = self._load_pose_from_file(pose_file)
                        if pose:
                            self.poses[pose.id] = pose
                    except Exception as e:
                        print(f"Warning: Error loading pose {pose_file}: {e}")

    def _load_pose_from_file(self, path: Path) -> Optional[Pose]:
        """
        Load a pose from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Pose object or None if loading fails
        """
        try:
            import yaml
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        except ImportError:
            # Fallback to JSON
            json_path = path.with_suffix('.json')
            if json_path.exists():
                with open(json_path, 'r') as f:
                    data = json.load(f)
            else:
                return None
        except Exception:
            return None

        return Pose.from_dict(data)

    def _save_pose_to_file(self, pose: Pose, category: Optional[str] = None) -> Path:
        """
        Save a pose to file.

        Args:
            pose: Pose to save
            category: Category directory (uses pose.category if None)

        Returns:
            Path to saved file
        """
        cat = category or pose.category.value
        category_dir = self.config_root / cat
        category_dir.mkdir(parents=True, exist_ok=True)

        path = category_dir / f"{pose.id}.yaml"

        # Add timestamp to metadata
        pose.metadata['modified'] = datetime.now().isoformat()

        data = pose.to_dict()

        try:
            import yaml
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except ImportError:
            # Fallback to JSON
            json_path = path.with_suffix('.json')
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)

        return path

    def save_pose(
        self,
        pose: Pose,
        category: Optional[str] = None
    ) -> Path:
        """
        Save a pose to the library.

        Args:
            pose: Pose to save
            category: Category directory (uses pose.category if None)

        Returns:
            Path to saved file
        """
        # Store in memory
        self.poses[pose.id] = pose

        # Save to file
        return self._save_pose_to_file(pose, category)

    def load_pose(self, pose_id: str) -> Optional[Pose]:
        """
        Load a pose by ID.

        Args:
            pose_id: Pose identifier

        Returns:
            Pose or None if not found
        """
        return self.poses.get(pose_id)

    def delete_pose(self, pose_id: str) -> bool:
        """
        Delete a pose from the library.

        Args:
            pose_id: Pose identifier

        Returns:
            True if deleted, False if not found
        """
        if pose_id not in self.poses:
            return False

        # Remove from memory
        del self.poses[pose_id]

        # Remove file if exists
        pose = self.poses.get(pose_id)
        if pose:
            for category_dir in self.config_root.iterdir():
                if category_dir.is_dir():
                    yaml_path = category_dir / f"{pose_id}.yaml"
                    json_path = category_dir / f"{pose_id}.json"
                    if yaml_path.exists():
                        yaml_path.unlink()
                    if json_path.exists():
                        json_path.unlink()

        return True

    def rename_pose(self, old_id: str, new_id: str) -> bool:
        """
        Rename a pose.

        Args:
            old_id: Current pose ID
            new_id: New pose ID

        Returns:
            True if renamed, False if not found or new ID exists
        """
        if old_id not in self.poses:
            return False
        if new_id in self.poses:
            return False

        pose = self.poses[old_id]
        pose.id = new_id

        # Delete old file
        self.delete_pose(old_id)

        # Save with new ID
        self.poses[new_id] = pose
        self._save_pose_to_file(pose)

        return True

    def capture_pose(
        self,
        armature: Any,
        name: str,
        category: PoseCategory = PoseCategory.CUSTOM,
        bones: Optional[List[str]] = None,
        description: str = ""
    ) -> Pose:
        """
        Capture current pose from an armature.

        Args:
            armature: Blender armature object
            name: Name for the pose
            category: Pose category
            bones: Specific bones to capture (None = all)
            description: Pose description

        Returns:
            Captured Pose object
        """
        pose_bones: Dict[str, BonePose] = {}
        captured_bones: List[str] = []

        for bone_name, pb in armature.pose.bones.items():
            if bones and bone_name not in bones:
                continue

            captured_bones.append(bone_name)

            # Get rotation
            if pb.rotation_mode == 'QUATERNION':
                rot_quat = tuple(pb.rotation_quaternion)
                # Convert to euler for storage (in degrees)
                euler = pb.rotation_quaternion.to_euler('XYZ')
                rot = tuple(math.degrees(a) for a in euler)
            else:
                rot = tuple(math.degrees(a) for a in pb.rotation_euler)
                rot_quat = None

            pose_bones[bone_name] = BonePose(
                location=tuple(pb.location),
                rotation=rot,
                rotation_quat=rot_quat,
                scale=tuple(pb.scale),
                rotation_mode=pb.rotation_mode
            )

        pose_id = name.lower().replace(' ', '_').replace('-', '_')

        return Pose(
            id=pose_id,
            name=name,
            category=category,
            rig_type=self.rig_type,
            description=description,
            bones=pose_bones,
            metadata={'captured': datetime.now().isoformat()},
            affected_bones=captured_bones
        )

    def apply_pose(
        self,
        armature: Any,
        pose: Pose,
        blend_weight: float = 1.0,
        bones: Optional[List[str]] = None
    ) -> None:
        """
        Apply a pose to an armature.

        Args:
            armature: Blender armature object
            pose: Pose to apply
            blend_weight: Blend factor (0.0 = no change, 1.0 = full pose)
            bones: Specific bones to affect (None = all in pose)
        """
        target_bones = bones or list(pose.bones.keys())

        for bone_name in target_bones:
            if bone_name not in armature.pose.bones:
                continue
            if bone_name not in pose.bones:
                continue

            pb = armature.pose.bones[bone_name]
            bone_pose = pose.bones[bone_name]

            # Blend location
            pb.location = [
                pb.location[i] * (1 - blend_weight) + bone_pose.location[i] * blend_weight
                for i in range(3)
            ]

            # Blend rotation
            if pb.rotation_mode == 'QUATERNION' and bone_pose.rotation_quat:
                # SLERP for quaternions
                import mathutils
                current_quat = mathutils.Quaternion(pb.rotation_quaternion)
                target_quat = mathutils.Quaternion(bone_pose.rotation_quat)
                pb.rotation_quaternion = current_quat.slerp(target_quat, blend_weight)
            else:
                # Linear blend for euler
                target_euler = [math.radians(a) for a in bone_pose.rotation]
                pb.rotation_euler = [
                    pb.rotation_euler[i] * (1 - blend_weight) + target_euler[i] * blend_weight
                    for i in range(3)
                ]

            # Blend scale
            pb.scale = [
                pb.scale[i] * (1 - blend_weight) + bone_pose.scale[i] * blend_weight
                for i in range(3)
            ]

    def get_poses_by_category(self, category: PoseCategory) -> List[Pose]:
        """
        Get all poses in a category.

        Args:
            category: Pose category

        Returns:
            List of poses
        """
        return [p for p in self.poses.values() if p.category == category]

    def get_poses_by_tags(self, tags: List[str]) -> List[Pose]:
        """
        Get poses that have any of the specified tags.

        Args:
            tags: Tags to search for

        Returns:
            List of matching poses
        """
        return [
            p for p in self.poses.values()
            if any(tag in p.tags for tag in tags)
        ]

    def search_poses(self, query: str) -> List[Pose]:
        """
        Search poses by name or description.

        Args:
            query: Search query

        Returns:
            List of matching poses
        """
        query_lower = query.lower()
        return [
            p for p in self.poses.values()
            if query_lower in p.name.lower() or query_lower in p.description.lower()
        ]

    def list_poses(self) -> List[str]:
        """
        List all pose IDs.

        Returns:
            List of pose IDs
        """
        return list(self.poses.keys())

    def pose_exists(self, pose_id: str) -> bool:
        """
        Check if a pose exists.

        Args:
            pose_id: Pose identifier

        Returns:
            True if pose exists
        """
        return pose_id in self.poses

    def get_pose_info(self, pose_id: str) -> Optional[Dict[str, Any]]:
        """
        Get pose information without the bone data.

        Args:
            pose_id: Pose identifier

        Returns:
            Dictionary with pose info or None
        """
        pose = self.poses.get(pose_id)
        if not pose:
            return None

        return {
            'id': pose.id,
            'name': pose.name,
            'category': pose.category.value,
            'rig_type': pose.rig_type,
            'description': pose.description,
            'tags': pose.tags,
            'bone_count': len(pose.bones),
            'metadata': pose.metadata
        }

    def reload_poses(self) -> None:
        """Reload all poses from disk."""
        self.poses.clear()
        self._load_all_poses()


# =============================================================================
# Convenience Functions
# =============================================================================

def capture_current_pose(
    armature: Any,
    name: str,
    category: str = "custom"
) -> Pose:
    """
    Convenience function to capture current pose.

    Args:
        armature: Blender armature object
        name: Name for the pose
        category: Category string

    Returns:
        Captured Pose object
    """
    library = PoseLibrary()
    cat = PoseCategory(category) if category in [c.value for c in PoseCategory] else PoseCategory.CUSTOM
    return library.capture_pose(armature, name, cat)


def apply_pose_by_id(
    armature: Any,
    pose_id: str,
    blend: float = 1.0
) -> bool:
    """
    Apply a pose by its ID.

    Args:
        armature: Blender armature object
        pose_id: Pose identifier
        blend: Blend weight (0-1)

    Returns:
        True if pose was applied, False if not found
    """
    library = PoseLibrary()
    pose = library.load_pose(pose_id)
    if pose:
        library.apply_pose(armature, pose, blend)
        return True
    return False


def save_pose_to_library(
    armature: Any,
    name: str,
    category: str = "custom",
    description: str = "",
    tags: Optional[List[str]] = None
) -> Pose:
    """
    Capture and save a pose to the library.

    Args:
        armature: Blender armature object
        name: Name for the pose
        category: Category string
        description: Pose description
        tags: Optional tags

    Returns:
        Saved Pose object
    """
    library = PoseLibrary()
    cat = PoseCategory(category) if category in [c.value for c in PoseCategory] else PoseCategory.CUSTOM

    pose = library.capture_pose(armature, name, cat, description=description)
    if tags:
        pose.tags = tags

    library.save_pose(pose)
    return pose


def list_available_poses(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List available poses.

    Args:
        category: Optional category filter

    Returns:
        List of pose info dictionaries
    """
    library = PoseLibrary()

    if category:
        cat = PoseCategory(category) if category in [c.value for c in PoseCategory] else None
        if cat:
            poses = library.get_poses_by_category(cat)
        else:
            poses = list(library.poses.values())
    else:
        poses = list(library.poses.values())

    return [library.get_pose_info(p.id) for p in poses if library.get_pose_info(p.id)]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'PoseLibrary',
    'capture_current_pose',
    'apply_pose_by_id',
    'save_pose_to_library',
    'list_available_poses',
]
