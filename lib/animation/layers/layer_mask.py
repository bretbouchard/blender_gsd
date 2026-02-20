"""
Layer Masking Module

Manages bone masks for animation layers.

Phase 13.7: Animation Layers (REQ-ANIM-09)
"""

from __future__ import annotations
from typing import Set, List, Dict, Optional, Any
import fnmatch
import logging

from .layer_system import AnimationLayerSystem

logger = logging.getLogger(__name__)


class LayerMaskManager:
    """
    Manage bone masks for animation layers.

    Supports creating masks from:
    - Bone groups
    - Name patterns
    - Body sides (left/right/center)
    - Preset masks for common body parts
    """

    @staticmethod
    def create_bone_mask_from_list(bone_names: List[str]) -> Set[str]:
        """
        Create a bone mask from a list of bone names.

        Args:
            bone_names: List of bone names

        Returns:
            Set of bone names
        """
        return set(bone_names)

    @staticmethod
    def create_bone_mask_from_pattern(
        all_bones: List[str],
        pattern: str
    ) -> Set[str]:
        """
        Create a bone mask from a name pattern.

        Supports glob patterns:
        - 'hand_*' matches 'hand_L', 'hand_R', 'hand_thumb'
        - '*_L' matches all bones ending with '_L'

        Args:
            all_bones: List of all bone names
            pattern: Glob pattern to match

        Returns:
            Set of matching bone names
        """
        mask = set()
        for bone_name in all_bones:
            if fnmatch.fnmatch(bone_name, pattern):
                mask.add(bone_name)
        return mask

    @staticmethod
    def create_bone_mask_from_side(
        all_bones: List[str],
        side: str
    ) -> Set[str]:
        """
        Create a bone mask for one side of the body.

        Args:
            all_bones: List of all bone names
            side: 'left', 'right', or 'center'

        Returns:
            Set of bone names on specified side
        """
        mask = set()

        for bone_name in all_bones:
            name_lower = bone_name.lower()

            if side == 'left':
                if ('_l' in name_lower or
                    name_lower.endswith('l') or
                    '.l' in name_lower or
                    '_left' in name_lower or
                    'left_' in name_lower):
                    mask.add(bone_name)

            elif side == 'right':
                if ('_r' in name_lower or
                    name_lower.endswith('r') or
                    '.r' in name_lower or
                    '_right' in name_lower or
                    'right_' in name_lower):
                    mask.add(bone_name)

            elif side == 'center':
                # Bones without side indicators
                if not ('_l' in name_lower or '_r' in name_lower or
                        '.l' in name_lower or '.r' in name_lower or
                        '_left' in name_lower or '_right' in name_lower or
                        'left_' in name_lower or 'right_' in name_lower):
                    mask.add(bone_name)

        return mask

    @staticmethod
    def create_bone_mask_from_prefix(
        all_bones: List[str],
        prefix: str
    ) -> Set[str]:
        """
        Create a bone mask from a name prefix.

        Args:
            all_bones: List of all bone names
            prefix: Prefix to match

        Returns:
            Set of bone names starting with prefix
        """
        mask = set()
        for bone_name in all_bones:
            if bone_name.startswith(prefix):
                mask.add(bone_name)
        return mask

    @staticmethod
    def create_bone_mask_from_suffix(
        all_bones: List[str],
        suffix: str
    ) -> Set[str]:
        """
        Create a bone mask from a name suffix.

        Args:
            all_bones: List of all bone names
            suffix: Suffix to match

        Returns:
            Set of bone names ending with suffix
        """
        mask = set()
        for bone_name in all_bones:
            if bone_name.endswith(suffix):
                mask.add(bone_name)
        return mask

    @staticmethod
    def invert_mask(all_bones: List[str], mask: Set[str]) -> Set[str]:
        """
        Invert a bone mask.

        Args:
            all_bones: List of all bone names
            mask: Mask to invert

        Returns:
            Set of bones NOT in the original mask
        """
        all_set = set(all_bones)
        return all_set - mask

    @staticmethod
    def combine_masks(
        masks: List[Set[str]],
        operation: str = 'union'
    ) -> Set[str]:
        """
        Combine multiple masks.

        Args:
            masks: List of masks to combine
            operation: 'union' (OR), 'intersection' (AND), 'difference' (subtract)

        Returns:
            Combined mask
        """
        if not masks:
            return set()

        if operation == 'union':
            result = set()
            for m in masks:
                result |= m
            return result

        elif operation == 'intersection':
            result = masks[0].copy()
            for m in masks[1:]:
                result &= m
            return result

        elif operation == 'difference':
            result = masks[0].copy()
            for m in masks[1:]:
                result -= m
            return result

        return set()

    @staticmethod
    def get_preset_masks(all_bones: List[str]) -> Dict[str, Set[str]]:
        """
        Get common preset bone masks.

        Args:
            all_bones: List of all bone names

        Returns:
            Dictionary of preset name -> bone mask
        """
        manager = LayerMaskManager()

        return {
            'all': set(all_bones),

            # Arms
            'left_arm': manager.create_bone_mask_from_pattern(all_bones, '*arm*L') |
                        manager.create_bone_mask_from_pattern(all_bones, '*arm_L') |
                        manager.create_bone_mask_from_pattern(all_bones, '*arm_L*') |
                        manager.create_bone_mask_from_pattern(all_bones, 'L_*arm*'),
            'right_arm': manager.create_bone_mask_from_pattern(all_bones, '*arm*R') |
                         manager.create_bone_mask_from_pattern(all_bones, '*arm_R') |
                         manager.create_bone_mask_from_pattern(all_bones, '*arm_R*') |
                         manager.create_bone_mask_from_pattern(all_bones, 'R_*arm*'),

            # Legs
            'left_leg': manager.create_bone_mask_from_pattern(all_bones, '*leg*L') |
                        manager.create_bone_mask_from_pattern(all_bones, '*leg_L') |
                        manager.create_bone_mask_from_pattern(all_bones, '*leg_L*') |
                        manager.create_bone_mask_from_pattern(all_bones, 'L_*leg*') |
                        manager.create_bone_mask_from_pattern(all_bones, '*thigh*L*') |
                        manager.create_bone_mask_from_pattern(all_bones, '*shin*L*') |
                        manager.create_bone_mask_from_pattern(all_bones, '*foot*L*'),
            'right_leg': manager.create_bone_mask_from_pattern(all_bones, '*leg*R') |
                         manager.create_bone_mask_from_pattern(all_bones, '*leg_R') |
                         manager.create_bone_mask_from_pattern(all_bones, '*leg_R*') |
                         manager.create_bone_mask_from_pattern(all_bones, 'R_*leg*') |
                         manager.create_bone_mask_from_pattern(all_bones, '*thigh*R*') |
                         manager.create_bone_mask_from_pattern(all_bones, '*shin*R*') |
                         manager.create_bone_mask_from_pattern(all_bones, '*foot*R*'),

            # Spine
            'spine': manager.create_bone_mask_from_pattern(all_bones, 'spine*') |
                     manager.create_bone_mask_from_pattern(all_bones, '*spine*'),

            # Head
            'head': manager.create_bone_mask_from_pattern(all_bones, 'head*') |
                    manager.create_bone_mask_from_pattern(all_bones, 'neck*') |
                    manager.create_bone_mask_from_pattern(all_bones, '*head*'),

            # Hands
            'hands': manager.create_bone_mask_from_pattern(all_bones, 'hand*') |
                     manager.create_bone_mask_from_pattern(all_bones, '*hand*') |
                     manager.create_bone_mask_from_pattern(all_bones, 'finger*') |
                     manager.create_bone_mask_from_pattern(all_bones, '*finger*') |
                     manager.create_bone_mask_from_pattern(all_bones, 'thumb*') |
                     manager.create_bone_mask_from_pattern(all_bones, '*thumb*'),

            # Fingers
            'fingers': manager.create_bone_mask_from_pattern(all_bones, 'finger*') |
                       manager.create_bone_mask_from_pattern(all_bones, '*finger*') |
                       manager.create_bone_mask_from_pattern(all_bones, 'thumb*') |
                       manager.create_bone_mask_from_pattern(all_bones, 'index*') |
                       manager.create_bone_mask_from_pattern(all_bones, 'middle*') |
                       manager.create_bone_mask_from_pattern(all_bones, 'ring*') |
                       manager.create_bone_mask_from_pattern(all_bones, 'pinky*'),

            # Face
            'face': manager.create_bone_mask_from_pattern(all_bones, '*face*') |
                    manager.create_bone_mask_from_pattern(all_bones, '*eye*') |
                    manager.create_bone_mask_from_pattern(all_bones, '*brow*') |
                    manager.create_bone_mask_from_pattern(all_bones, '*mouth*') |
                    manager.create_bone_mask_from_pattern(all_bones, '*jaw*') |
                    manager.create_bone_mask_from_pattern(all_bones, '*lip*') |
                    manager.create_bone_mask_from_pattern(all_bones, '*cheek*'),

            # Tail
            'tail': manager.create_bone_mask_from_pattern(all_bones, 'tail*') |
                    manager.create_bone_mask_from_pattern(all_bones, '*tail*'),

            # Wings (for fantasy creatures)
            'wings': manager.create_bone_mask_from_pattern(all_bones, 'wing*') |
                     manager.create_bone_mask_from_pattern(all_bones, '*wing*'),

            # Sides
            'left_side': manager.create_bone_mask_from_side(all_bones, 'left'),
            'right_side': manager.create_bone_mask_from_side(all_bones, 'right'),
            'center': manager.create_bone_mask_from_side(all_bones, 'center'),

            # Upper body
            'upper_body': manager.create_bone_mask_from_pattern(all_bones, 'spine*') |
                          manager.create_bone_mask_from_pattern(all_bones, 'chest*') |
                          manager.create_bone_mask_from_pattern(all_bones, 'shoulder*') |
                          manager.create_bone_mask_from_pattern(all_bones, '*arm*') |
                          manager.create_bone_mask_from_pattern(all_bones, '*hand*') |
                          manager.create_bone_mask_from_pattern(all_bones, 'neck*') |
                          manager.create_bone_mask_from_pattern(all_bones, 'head*'),

            # Lower body
            'lower_body': manager.create_bone_mask_from_pattern(all_bones, 'hip*') |
                          manager.create_bone_mask_from_pattern(all_bones, 'pelvis*') |
                          manager.create_bone_mask_from_pattern(all_bones, '*leg*') |
                          manager.create_bone_mask_from_pattern(all_bones, '*thigh*') |
                          manager.create_bone_mask_from_pattern(all_bones, '*shin*') |
                          manager.create_bone_mask_from_pattern(all_bones, '*foot*') |
                          manager.create_bone_mask_from_pattern(all_bones, '*toe*'),

            # Root/pelvis only
            'root': manager.create_bone_mask_from_pattern(all_bones, 'root') |
                    manager.create_bone_mask_from_pattern(all_bones, 'hip') |
                    manager.create_bone_mask_from_pattern(all_bones, 'pelvis'),
        }


def apply_mask_to_layer(
    system: AnimationLayerSystem,
    layer_id: str,
    mask_name: str
) -> bool:
    """
    Apply a preset mask to a layer.

    Args:
        system: AnimationLayerSystem
        layer_id: ID of layer to modify
        mask_name: Name of preset mask

    Returns:
        True if successful
    """
    all_bones = system.bone_names
    if not all_bones:
        logger.warning("No bone names available in system")
        return False

    masks = LayerMaskManager.get_preset_masks(all_bones)

    if mask_name not in masks:
        logger.warning(f"Unknown mask preset: {mask_name}")
        return False

    layer = system.get_layer(layer_id)
    if not layer:
        logger.warning(f"Layer not found: {layer_id}")
        return False

    system.set_layer_bone_mask(layer_id, masks[mask_name])
    return True


def create_custom_mask(
    all_bones: List[str],
    patterns: List[str],
    exclude_patterns: Optional[List[str]] = None
) -> Set[str]:
    """
    Create a custom bone mask from patterns.

    Args:
        all_bones: List of all bone names
        patterns: List of glob patterns to include
        exclude_patterns: Optional list of patterns to exclude

    Returns:
        Combined mask
    """
    manager = LayerMaskManager()

    # Combine all include patterns
    include_masks = [
        manager.create_bone_mask_from_pattern(all_bones, p)
        for p in patterns
    ]
    result = manager.combine_masks(include_masks, 'union')

    # Remove excluded patterns
    if exclude_patterns:
        exclude_masks = [
            manager.create_bone_mask_from_pattern(all_bones, p)
            for p in exclude_patterns
        ]
        exclude_set = manager.combine_masks(exclude_masks, 'union')
        result -= exclude_set

    return result


def list_available_masks() -> List[str]:
    """
    List all available preset mask names.

    Returns:
        List of mask names
    """
    return [
        'all',
        'left_arm', 'right_arm',
        'left_leg', 'right_leg',
        'spine', 'head',
        'hands', 'fingers',
        'face', 'tail', 'wings',
        'left_side', 'right_side', 'center',
        'upper_body', 'lower_body',
        'root',
    ]
