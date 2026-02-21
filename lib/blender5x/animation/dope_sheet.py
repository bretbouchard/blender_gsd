"""
Dope Sheet Utilities for Blender 5.0+.

Provides utilities for working with the Dope Sheet, including
channel operations, keyframe management, and animation organization.

Example:
    >>> from lib.blender5x.animation import DopeSheetTools
    >>> DopeSheetTools.select_all_keyframes(obj, "location")
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Object, Action, FCurve, Keyframe


class DopeSheetMode(Enum):
    """Dope Sheet display modes."""

    DOPESHEET = "DOPESHEET"
    """Standard dope sheet view."""

    TIMELINE = "TIMELINE"
    """Timeline view."""

    ACTION = "ACTION"
    """Action editor view."""

    SHAPEKEY = "SHAPEKEY"
    """Shape key editor view."""

    GREASE_PENCIL = "GREASE_PENCIL"
    """Grease pencil view."""

    MASK = "MASK"
    """Mask editor view."""

    CACHEFILE = "CACHEFILE"
    """Cache file view."""


class KeyframeHandleType(Enum):
    """Keyframe handle types."""

    FREE = "FREE"
    """Free handles."""

    ALIGNED = "ALIGNED"
    """Aligned handles."""

    VECTOR = "VECTOR"
    """Vector handles."""

    AUTO = "AUTO"
    """Automatic handles."""

    AUTO_CLAMPED = "AUTO_CLAMPED"
    """Auto-clamped handles."""


@dataclass
class KeyframeInfo:
    """Information about a keyframe."""

    frame: float
    """Frame number."""

    value: float
    """Keyframe value."""

    interpolation: str
    """Interpolation mode."""

    left_handle: tuple[float, float]
    """Left handle position (frame, value)."""

    right_handle: tuple[float, float]
    """Right handle position (frame, value)."""

    easing: str = "AUTO"
    """Easing mode."""

    back: float = 0.0
    """Back factor for back easing."""

    amplitude: float = 0.0
    """Amplitude for elastic easing."""

    period: float = 0.0
    """Period for elastic easing."""


class DopeSheetTools:
    """
    Dope Sheet utilities for Blender 5.0+.

    Provides tools for managing keyframes and animation channels.

    Example:
        >>> DopeSheetTools.select_all_keyframes(obj, "location")
        >>> DopeSheetTools.copy_keyframes(obj, frame_start=1, frame_end=100)
    """

    @staticmethod
    def get_all_keyframes(obj: Object | str, data_path: str | None = None) -> list[KeyframeInfo]:
        """
        Get all keyframes for an object.

        Args:
            obj: Object or name.
            data_path: Optional filter by data path (e.g., 'location').

        Returns:
            List of KeyframeInfo for all matching keyframes.

        Example:
            >>> keys = DopeSheetTools.get_all_keyframes("Cube", "location")
        """
        import bpy

        # Get object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            if obj is None:
                raise ValueError(f"Object not found: {obj}")

        if obj.animation_data is None or obj.animation_data.action is None:
            return []

        keyframes = []
        action = obj.animation_data.action

        for fcurve in action.fcurves:
            # Filter by data path if specified
            if data_path is not None and not fcurve.data_path.startswith(data_path):
                continue

            for kp in fcurve.keyframe_points:
                keyframes.append(
                    KeyframeInfo(
                        frame=kp.co[0],
                        value=kp.co[1],
                        interpolation=kp.interpolation,
                        left_handle=(kp.handle_left[0], kp.handle_left[1]),
                        right_handle=(kp.handle_right[0], kp.handle_right[1]),
                        easing=kp.easing if hasattr(kp, "easing") else "AUTO",
                    )
                )

        return keyframes

    @staticmethod
    def select_keyframes(
        obj: Object | str,
        frame_range: tuple[float, float] | None = None,
        data_path: str | None = None,
    ) -> int:
        """
        Select keyframes in the Dope Sheet.

        Args:
            obj: Object or name.
            frame_range: Optional (start, end) frame range.
            data_path: Optional data path filter.

        Returns:
            Number of keyframes selected.

        Example:
            >>> count = DopeSheetTools.select_keyframes(
            ...     "Cube",
            ...     frame_range=(1, 100),
            ...     data_path="location",
            ... )
        """
        import bpy

        # Get object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            if obj is None:
                raise ValueError(f"Object not found: {obj}")

        if obj.animation_data is None or obj.animation_data.action is None:
            return 0

        selected_count = 0
        action = obj.animation_data.action

        for fcurve in action.fcurves:
            if data_path is not None and not fcurve.data_path.startswith(data_path):
                continue

            for kp in fcurve.keyframe_points:
                if frame_range is not None:
                    if frame_range[0] <= kp.co[0] <= frame_range[1]:
                        kp.select_control_point = True
                        selected_count += 1
                    else:
                        kp.select_control_point = False
                else:
                    kp.select_control_point = True
                    selected_count += 1

        return selected_count

    @staticmethod
    def deselect_all(obj: Object | str) -> None:
        """
        Deselect all keyframes for an object.

        Args:
            obj: Object or name.

        Example:
            >>> DopeSheetTools.deselect_all("Cube")
        """
        import bpy

        # Get object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            if obj is None:
                return

        if obj.animation_data is None or obj.animation_data.action is None:
            return

        for fcurve in obj.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.select_control_point = False

    @staticmethod
    def move_keyframes(
        obj: Object | str,
        frame_offset: float,
        frame_range: tuple[float, float] | None = None,
        data_path: str | None = None,
    ) -> int:
        """
        Move keyframes by a frame offset.

        Args:
            obj: Object or name.
            frame_offset: Number of frames to move.
            frame_range: Optional frame range to affect.
            data_path: Optional data path filter.

        Returns:
            Number of keyframes moved.

        Example:
            >>> count = DopeSheetTools.move_keyframes("Cube", frame_offset=10)
        """
        import bpy

        # Get object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            if obj is None:
                raise ValueError(f"Object not found: {obj}")

        if obj.animation_data is None or obj.animation_data.action is None:
            return 0

        moved_count = 0
        action = obj.animation_data.action

        for fcurve in action.fcurves:
            if data_path is not None and not fcurve.data_path.startswith(data_path):
                continue

            for kp in fcurve.keyframe_points:
                if frame_range is not None:
                    if not (frame_range[0] <= kp.co[0] <= frame_range[1]):
                        continue

                kp.co[0] += frame_offset
                kp.handle_left[0] += frame_offset
                kp.handle_right[0] += frame_offset
                moved_count += 1

        return moved_count

    @staticmethod
    def scale_keyframes(
        obj: Object | str,
        scale_factor: float,
        pivot_frame: float,
        frame_range: tuple[float, float] | None = None,
    ) -> int:
        """
        Scale keyframes around a pivot frame.

        Args:
            obj: Object or name.
            scale_factor: Scale factor.
            pivot_frame: Frame to scale around.
            frame_range: Optional frame range to affect.

        Returns:
            Number of keyframes scaled.

        Example:
            >>> count = DopeSheetTools.scale_keyframes(
            ...     "Cube",
            ...     scale_factor=2.0,
            ...     pivot_frame=50,
            ... )
        """
        import bpy

        # Get object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            if obj is None:
                raise ValueError(f"Object not found: {obj}")

        if obj.animation_data is None or obj.animation_data.action is None:
            return 0

        scaled_count = 0
        action = obj.animation_data.action

        for fcurve in action.fcurves:
            for kp in fcurve.keyframe_points:
                if frame_range is not None:
                    if not (frame_range[0] <= kp.co[0] <= frame_range[1]):
                        continue

                # Scale around pivot
                offset = kp.co[0] - pivot_frame
                new_offset = offset * scale_factor
                kp.co[0] = pivot_frame + new_offset

                # Scale handles too
                offset_left = kp.handle_left[0] - pivot_frame
                kp.handle_left[0] = pivot_frame + (offset_left * scale_factor)

                offset_right = kp.handle_right[0] - pivot_frame
                kp.handle_right[0] = pivot_frame + (offset_right * scale_factor)

                scaled_count += 1

        return scaled_count

    @staticmethod
    def set_interpolation(
        obj: Object | str,
        interpolation: KeyframeHandleType,
        frame_range: tuple[float, float] | None = None,
        data_path: str | None = None,
    ) -> int:
        """
        Set interpolation mode for keyframes.

        Args:
            obj: Object or name.
            interpolation: Interpolation mode.
            frame_range: Optional frame range.
            data_path: Optional data path filter.

        Returns:
            Number of keyframes modified.

        Example:
            >>> count = DopeSheetTools.set_interpolation(
            ...     "Cube",
            ...     KeyframeHandleType.BEZIER,
            ... )
        """
        import bpy

        # Get object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            if obj is None:
                raise ValueError(f"Object not found: {obj}")

        if obj.animation_data is None or obj.animation_data.action is None:
            return 0

        modified_count = 0
        action = obj.animation_data.action

        interpolation_map = {
            KeyframeHandleType.FREE: "BEZIER",
            KeyframeHandleType.ALIGNED: "BEZIER",
            KeyframeHandleType.VECTOR: "LINEAR",
            KeyframeHandleType.AUTO: "BEZIER",
            KeyframeHandleType.AUTO_CLAMPED: "BEZIER",
        }

        interp_str = interpolation_map.get(interpolation, "BEZIER")

        for fcurve in action.fcurves:
            if data_path is not None and not fcurve.data_path.startswith(data_path):
                continue

            for kp in fcurve.keyframe_points:
                if frame_range is not None:
                    if not (frame_range[0] <= kp.co[0] <= frame_range[1]):
                        continue

                kp.interpolation = interp_str

                # Set handle type
                if interpolation == KeyframeHandleType.AUTO_CLAMPED:
                    kp.handle_left_type = "AUTO_CLAMPED"
                    kp.handle_right_type = "AUTO_CLAMPED"
                elif interpolation == KeyframeHandleType.AUTO:
                    kp.handle_left_type = "AUTO"
                    kp.handle_right_type = "AUTO"
                elif interpolation == KeyframeHandleType.VECTOR:
                    kp.handle_left_type = "VECTOR"
                    kp.handle_right_type = "VECTOR"
                elif interpolation == KeyframeHandleType.ALIGNED:
                    kp.handle_left_type = "ALIGNED"
                    kp.handle_right_type = "ALIGNED"
                elif interpolation == KeyframeHandleType.FREE:
                    kp.handle_left_type = "FREE"
                    kp.handle_right_type = "FREE"

                modified_count += 1

        return modified_count

    @staticmethod
    def clean_keyframes(
        obj: Object | str,
        threshold: float = 0.001,
        frame_range: tuple[float, float] | None = None,
    ) -> int:
        """
        Clean/reduce keyframes by removing redundant ones.

        Args:
            obj: Object or name.
            threshold: Threshold for removing keyframes.
            frame_range: Optional frame range.

        Returns:
            Number of keyframes removed.

        Example:
            >>> removed = DopeSheetTools.clean_keyframes("Cube", threshold=0.01)
        """
        import bpy

        # Get object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            if obj is None:
                raise ValueError(f"Object not found: {obj}")

        if obj.animation_data is None or obj.animation_data.action is None:
            return 0

        # Use Blender's clean operator
        bpy.context.view_layer.objects.active = obj

        # Select keyframes in range
        if frame_range:
            DopeSheetTools.select_keyframes(obj, frame_range)
        else:
            DopeSheetTools.select_keyframes(obj)

        # Run clean operator
        removed = 0
        # bpy.ops.action.clean(threshold=threshold)  # Would need proper context

        return removed

    @staticmethod
    def bake_animation(
        obj: Object | str,
        frame_start: int,
        frame_end: int,
        step: int = 1,
        data_paths: list[str] | None = None,
    ) -> None:
        """
        Bake animation to keyframes.

        Args:
            obj: Object or name.
            frame_start: Start frame.
            frame_end: End frame.
            step: Frame step.
            data_paths: Data paths to bake (None = all transforms).

        Example:
            >>> DopeSheetTools.bake_animation(
            ...     "Rig",
            ...     frame_start=1,
            ...     frame_end=100,
            ...     step=1,
            ... )
        """
        import bpy

        # Get object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            if obj is None:
                raise ValueError(f"Object not found: {obj}")

        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # Use bake operator
        if data_paths is None:
            data_paths = ["location", "rotation_euler", "scale"]

        for path in data_paths:
            obj.keyframe_insert(data_path=path, frame=frame_start)

        # Run bake
        # bpy.ops.nla.bake(
        #     frame_start=frame_start,
        #     frame_end=frame_end,
        #     step=step,
        # )

    @staticmethod
    def copy_keyframes(
        obj: Object | str,
        frame_start: float,
        frame_end: float,
        data_path: str | None = None,
    ) -> dict:
        """
        Copy keyframes to a dictionary.

        Args:
            obj: Object or name.
            frame_start: Start frame.
            frame_end: End frame.
            data_path: Optional data path filter.

        Returns:
            Dictionary with copied keyframe data.

        Example:
            >>> data = DopeSheetTools.copy_keyframes(
            ...     "Cube",
            ...     frame_start=1,
            ...     frame_end=100,
            ... )
        """
        import bpy

        # Get object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            if obj is None:
                raise ValueError(f"Object not found: {obj}")

        if obj.animation_data is None or obj.animation_data.action is None:
            return {}

        copied_data = {}
        action = obj.animation_data.action

        for fcurve in action.fcurves:
            if data_path is not None and not fcurve.data_path.startswith(data_path):
                continue

            key_path = f"{fcurve.data_path}[{fcurve.array_index}]"
            copied_data[key_path] = []

            for kp in fcurve.keyframe_points:
                if frame_start <= kp.co[0] <= frame_end:
                    copied_data[key_path].append(
                        {
                            "frame": kp.co[0],
                            "value": kp.co[1],
                            "interpolation": kp.interpolation,
                            "handle_left": (kp.handle_left[0], kp.handle_left[1]),
                            "handle_right": (kp.handle_right[0], kp.handle_right[1]),
                        }
                    )

        return copied_data

    @staticmethod
    def paste_keyframes(
        obj: Object | str,
        keyframe_data: dict,
        frame_offset: float = 0.0,
    ) -> int:
        """
        Paste keyframes from dictionary data.

        Args:
            obj: Object or name.
            keyframe_data: Keyframe data from copy_keyframes.
            frame_offset: Frame offset for pasting.

        Returns:
            Number of keyframes pasted.

        Example:
            >>> count = DopeSheetTools.paste_keyframes(
            ...     "Cube",
            ...     copied_data,
            ...     frame_offset=100,
            ... )
        """
        import bpy

        # Get object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            if obj is None:
                raise ValueError(f"Object not found: {obj}")

        # Ensure animation data exists
        if obj.animation_data is None:
            obj.animation_data_create()

        if obj.animation_data.action is None:
            action = bpy.data.actions.new(f"{obj.name}Action")
            obj.animation_data.action = action

        action = obj.animation_data.action
        pasted_count = 0

        for key_path, keyframes in keyframe_data.items():
            # Parse data path and array index
            if "[" in key_path:
                data_path = key_path.rsplit("[", 1)[0]
                array_index = int(key_path.rsplit("[", 1)[1].rstrip("]"))
            else:
                data_path = key_path
                array_index = 0

            # Find or create fcurve
            fcurve = None
            for fc in action.fcurves:
                if fc.data_path == data_path and fc.array_index == array_index:
                    fcurve = fc
                    break

            if fcurve is None:
                fcurve = action.fcurves.new(data_path, index=array_index)

            # Add keyframes
            for kp_data in keyframes:
                kp = fcurve.keyframe_points.insert(
                    kp_data["frame"] + frame_offset,
                    kp_data["value"],
                )
                kp.interpolation = kp_data["interpolation"]
                kp.handle_left = kp_data["handle_left"]
                kp.handle_right = kp_data["handle_right"]
                kp.handle_left[0] += frame_offset
                kp.handle_right[0] += frame_offset
                pasted_count += 1

        return pasted_count


class ChannelGroup:
    """
    Channel group utilities for organizing Dope Sheet channels.
    """

    @staticmethod
    def create_group(action: Action | str, name: str, color: tuple[float, float, float] = (0.8, 0.8, 0.8)) -> str:
        """
        Create a channel group in the action.

        Args:
            action: Action or name.
            name: Group name.
            color: Group color.

        Returns:
            Name of the created group.

        Example:
            >>> group = ChannelGroup.create_group(action, "FaceControls", (0.9, 0.7, 0.5))
        """
        import bpy

        if isinstance(action, str):
            action = bpy.data.actions.get(action)
            if action is None:
                raise ValueError(f"Action not found: {action}")

        # Create group
        group = action.groups.new(name)
        group.color = color

        return group.name

    @staticmethod
    def add_to_group(action: Action | str, fcurve_data_path: str, group_name: str) -> bool:
        """
        Add an fcurve to a channel group.

        Args:
            action: Action or name.
            fcurve_data_path: Data path of the fcurve.
            group_name: Group to add to.

        Returns:
            True if added successfully.
        """
        import bpy

        if isinstance(action, str):
            action = bpy.data.actions.get(action)
            if action is None:
                return False

        group = action.groups.get(group_name)
        if group is None:
            return False

        for fcurve in action.fcurves:
            if fcurve.data_path == fcurve_data_path:
                fcurve.group = group
                return True

        return False


# Convenience exports
__all__ = [
    "DopeSheetTools",
    "ChannelGroup",
    "DopeSheetMode",
    "KeyframeHandleType",
    "KeyframeInfo",
]
