"""
Layer Blending Module

Blends animation layers together for final output.

Phase 13.7: Animation Layers (REQ-ANIM-09)
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional, Any
import logging

from ..types import (
    AnimationLayer,
    LayerType,
    LayerStack,
    BoneKeyframe,
)
from .layer_system import AnimationLayerSystem

logger = logging.getLogger(__name__)


class LayerBlender:
    """
    Blend animation layers together.

    Supports different blend modes:
    - BASE: Foundation layer that replaces everything
    - OVERRIDE: Replace specific bones with opacity blend
    - ADDITIVE: Add values to current state
    - MIX: Blend with previous values
    """

    def __init__(self, system: AnimationLayerSystem):
        """
        Initialize layer blender.

        Args:
            system: AnimationLayerSystem to blend
        """
        self.system = system

    def evaluate(self, frame: int) -> Dict[str, BoneKeyframe]:
        """
        Evaluate all layers at a frame and return blended result.

        Args:
            frame: Frame number to evaluate

        Returns:
            Dictionary of bone name -> BoneKeyframe with blended values
        """
        visible_layers = self.system.stack.get_visible_layers()

        if not visible_layers:
            return {}

        # Start with identity (rest pose)
        result: Dict[str, BoneKeyframe] = {}

        # Get all bone names from layers
        bone_names = set()
        for layer in visible_layers:
            for kf in layer.keyframes:
                bone_names.update(kf.bones.keys())

        # Also include bone names from system
        if self.system.bone_names:
            bone_names.update(self.system.bone_names)

        # Initialize with rest pose
        for name in bone_names:
            result[name] = BoneKeyframe()

        # Apply each layer in order
        for layer in sorted(visible_layers, key=lambda l: l.order):
            layer_data = self._get_layer_data_at_frame(layer, frame)

            if layer.layer_type == LayerType.BASE:
                result = self._blend_base(result, layer_data, layer)

            elif layer.layer_type == LayerType.OVERRIDE:
                result = self._blend_override(result, layer_data, layer)

            elif layer.layer_type == LayerType.ADDITIVE:
                result = self._blend_additive(result, layer_data, layer)

            elif layer.layer_type == LayerType.MIX:
                result = self._blend_mix(result, layer_data, layer)

        return result

    def _get_layer_data_at_frame(
        self,
        layer: AnimationLayer,
        frame: int
    ) -> Dict[str, BoneKeyframe]:
        """
        Get interpolated bone data for layer at frame.

        Args:
            layer: Animation layer to sample
            frame: Frame number

        Returns:
            Dictionary of bone name -> BoneKeyframe
        """
        if not layer.keyframes:
            return {}

        # Find surrounding keyframes
        prev_kf = None
        next_kf = None

        for kf in layer.keyframes:
            if kf.frame <= frame:
                prev_kf = kf
            if kf.frame >= frame and next_kf is None:
                next_kf = kf

        # If no keyframes, return empty
        if prev_kf is None and next_kf is None:
            return {}

        # If exact frame, return that
        if prev_kf and prev_kf.frame == frame:
            return prev_kf.bones

        # Interpolate between keyframes
        if prev_kf and next_kf and prev_kf != next_kf:
            t = (frame - prev_kf.frame) / (next_kf.frame - prev_kf.frame)
            return self._interpolate_bones(prev_kf.bones, next_kf.bones, t)

        # Hold last/next keyframe
        if prev_kf:
            return prev_kf.bones
        if next_kf:
            return next_kf.bones

        return {}

    def _interpolate_bones(
        self,
        prev: Dict[str, BoneKeyframe],
        next_frame: Dict[str, BoneKeyframe],
        t: float
    ) -> Dict[str, BoneKeyframe]:
        """
        Linear interpolation between two bone states.

        Args:
            prev: Previous keyframe bones
            next_frame: Next keyframe bones
            t: Interpolation factor (0-1)

        Returns:
            Interpolated bone data
        """
        result = {}

        all_bones = set(prev.keys()) | set(next_frame.keys())

        for bone_name in all_bones:
            prev_bone = prev.get(bone_name, BoneKeyframe())
            next_bone = next_frame.get(bone_name, BoneKeyframe())

            result[bone_name] = BoneKeyframe(
                location=tuple(
                    prev_bone.location[i] * (1 - t) + next_bone.location[i] * t
                    for i in range(3)
                ),
                rotation=tuple(
                    prev_bone.rotation[i] * (1 - t) + next_bone.rotation[i] * t
                    for i in range(3)
                ),
                scale=tuple(
                    prev_bone.scale[i] * (1 - t) + next_bone.scale[i] * t
                    for i in range(3)
                )
            )

        return result

    def _blend_base(
        self,
        current: Dict[str, BoneKeyframe],
        layer_data: Dict[str, BoneKeyframe],
        layer: AnimationLayer
    ) -> Dict[str, BoneKeyframe]:
        """
        Base layer replaces everything.

        Args:
            current: Current blended result
            layer_data: Data from this layer
            layer: The layer being processed

        Returns:
            Updated result with base layer applied
        """
        result = current.copy()

        for bone_name, bone_kf in layer_data.items():
            # Check bone mask
            if layer.bone_mask and bone_name not in layer.bone_mask:
                continue

            result[bone_name] = BoneKeyframe(
                location=bone_kf.location,
                rotation=bone_kf.rotation,
                scale=bone_kf.scale
            )

        return result

    def _blend_override(
        self,
        current: Dict[str, BoneKeyframe],
        layer_data: Dict[str, BoneKeyframe],
        layer: AnimationLayer
    ) -> Dict[str, BoneKeyframe]:
        """
        Override layer replaces specific bones with opacity blend.

        Args:
            current: Current blended result
            layer_data: Data from this layer
            layer: The layer being processed

        Returns:
            Updated result with override applied
        """
        result = current.copy()

        for bone_name, bone_kf in layer_data.items():
            # Check bone mask
            if layer.bone_mask and bone_name not in layer.bone_mask:
                continue

            # Blend by opacity
            current_bone = current.get(bone_name, BoneKeyframe())
            opacity = layer.opacity

            result[bone_name] = BoneKeyframe(
                location=tuple(
                    current_bone.location[i] * (1 - opacity) + bone_kf.location[i] * opacity
                    for i in range(3)
                ),
                rotation=tuple(
                    current_bone.rotation[i] * (1 - opacity) + bone_kf.rotation[i] * opacity
                    for i in range(3)
                ),
                scale=tuple(
                    current_bone.scale[i] * (1 - opacity) + bone_kf.scale[i] * opacity
                    for i in range(3)
                )
            )

        return result

    def _blend_additive(
        self,
        current: Dict[str, BoneKeyframe],
        layer_data: Dict[str, BoneKeyframe],
        layer: AnimationLayer
    ) -> Dict[str, BoneKeyframe]:
        """
        Additive layer adds to current values.

        For scale, uses multiplicative blend to avoid issues with
        negative values from power function.

        Args:
            current: Current blended result
            layer_data: Data from this layer
            layer: The layer being processed

        Returns:
            Updated result with additive values
        """
        result = current.copy()

        for bone_name, bone_kf in layer_data.items():
            # Check bone mask
            if layer.bone_mask and bone_name not in layer.bone_mask:
                continue

            current_bone = current.get(bone_name, BoneKeyframe())
            opacity = layer.opacity

            # Additive blend for location and rotation
            # Multiplicative blend for scale (1 + (delta * opacity))
            result[bone_name] = BoneKeyframe(
                location=tuple(
                    current_bone.location[i] + bone_kf.location[i] * opacity
                    for i in range(3)
                ),
                rotation=tuple(
                    current_bone.rotation[i] + bone_kf.rotation[i] * opacity
                    for i in range(3)
                ),
                scale=tuple(
                    current_bone.scale[i] * (1 + (bone_kf.scale[i] - 1) * opacity)
                    for i in range(3)
                )
            )

        return result

    def _blend_mix(
        self,
        current: Dict[str, BoneKeyframe],
        layer_data: Dict[str, BoneKeyframe],
        layer: AnimationLayer
    ) -> Dict[str, BoneKeyframe]:
        """
        Mix layer blends with current (same as override).

        Args:
            current: Current blended result
            layer_data: Data from this layer
            layer: The layer being processed

        Returns:
            Updated result with mix applied
        """
        return self._blend_override(current, layer_data, layer)

    def evaluate_bone(
        self,
        frame: int,
        bone_name: str
    ) -> Optional[BoneKeyframe]:
        """
        Evaluate a single bone at a frame.

        Args:
            frame: Frame number
            bone_name: Name of bone to evaluate

        Returns:
            BoneKeyframe or None if bone not found
        """
        blended = self.evaluate(frame)
        return blended.get(bone_name)

    def get_keyframe_frames(self, start_frame: int, end_frame: int) -> List[int]:
        """
        Get all frames with keyframes in range.

        Args:
            start_frame: Start of range
            end_frame: End of range

        Returns:
            List of frame numbers with keyframes
        """
        frames = set()

        for layer in self.system.stack.layers:
            for kf in layer.keyframes:
                if start_frame <= kf.frame <= end_frame:
                    frames.add(kf.frame)

        return sorted(frames)


def blend_layers(
    system: AnimationLayerSystem,
    frame: int
) -> Dict[str, BoneKeyframe]:
    """
    Convenience function to blend layers at frame.

    Args:
        system: AnimationLayerSystem to blend
        frame: Frame number to evaluate

    Returns:
        Dictionary of bone name -> BoneKeyframe
    """
    blender = LayerBlender(system)
    return blender.evaluate(frame)


def blend_layer_range(
    system: AnimationLayerSystem,
    start_frame: int,
    end_frame: int
) -> Dict[int, Dict[str, BoneKeyframe]]:
    """
    Blend all frames in a range.

    Args:
        system: AnimationLayerSystem to blend
        start_frame: Start of range
        end_frame: End of range (inclusive)

    Returns:
        Dictionary of frame -> bone data
    """
    blender = LayerBlender(system)
    result = {}

    for frame in range(start_frame, end_frame + 1):
        result[frame] = blender.evaluate(frame)

    return result
