"""
Onion Skinning for Animation

Display ghost poses before and after the current frame to help visualize
animation motion and timing.

Phase 13.3: Blocking System (REQ-ANIM-05)
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field

from .types import OnionSkinConfig

if TYPE_CHECKING:
    import bpy


@dataclass
class GhostInfo:
    """Information about a ghost mesh."""
    frame: int
    direction: str  # "prev" or "next"
    mesh_name: str
    opacity: float = 0.3
    is_wireframe: bool = False


class OnionSkinning:
    """
    Display ghost poses before/after current frame.

    Onion skinning helps animators see motion by displaying
    semi-transparent "ghost" meshes at adjacent frames.

    Features:
    - Configurable number of frames before/after
    - Customizable colors for previous/next ghosts
    - Wireframe-only mode for performance
    - Maximum ghost limit to prevent performance issues

    Example:
        >>> config = OnionSkinConfig(previous_frames=2, next_frames=2)
        >>> skinning = OnionSkinning(armature, config)
        >>> skinning.enable()
        >>> # Ghosts will show at frame -2, -1, +1, +2
        >>> skinning.disable()  # Remove ghosts
    """

    def __init__(
        self,
        armature: Optional['bpy.types.Object'] = None,
        config: Optional[OnionSkinConfig] = None
    ):
        """
        Initialize onion skinning.

        Args:
            armature: The armature object
            config: Onion skin configuration
        """
        self.armature = armature
        self.config = config or OnionSkinConfig()
        self._ghosts: List[GhostInfo] = []
        self._enabled: bool = False
        self._shared_material_prev: Optional[str] = None
        self._shared_material_next: Optional[str] = None

    def enable(self) -> None:
        """Enable onion skinning."""
        self._enabled = True
        self.update()

    def disable(self) -> None:
        """Disable onion skinning and remove ghosts."""
        self._enabled = False
        self._clear_ghosts()

    def is_enabled(self) -> bool:
        """Check if onion skinning is enabled."""
        return self._enabled

    def toggle(self) -> bool:
        """
        Toggle onion skinning on/off.

        Returns:
            New enabled state
        """
        if self._enabled:
            self.disable()
        else:
            self.enable()
        return self._enabled

    def update(self, current_frame: Optional[int] = None) -> None:
        """
        Update onion skin display for current frame.

        Args:
            current_frame: Frame to show ghosts around (uses scene frame if None)
        """
        if not self._enabled:
            return

        self._clear_ghosts()

        frame = current_frame or 1
        if self.armature is None:
            # Just track ghost frames without Blender
            self._create_ghost_tracking(frame)
            return

        # In Blender context, would create actual ghost meshes here
        self._create_ghost_tracking(frame)

    def _create_ghost_tracking(self, current_frame: int) -> None:
        """
        Create ghost tracking info (works outside Blender context).

        Args:
            current_frame: Current frame
        """
        # Limit total ghosts
        total_ghosts = 0
        max_total = self.config.max_ghosts

        # Show previous frames
        if self.config.show_previous:
            for i in range(1, min(self.config.previous_frames + 1, max_total + 1)):
                if total_ghosts >= max_total:
                    break
                frame = current_frame - i
                if frame >= 1:
                    opacity = self.config.ghost_opacity * (1.0 - (i - 1) / max(self.config.previous_frames, 1))
                    ghost = GhostInfo(
                        frame=frame,
                        direction="prev",
                        mesh_name=f"onion_ghost_prev_{frame}",
                        opacity=opacity,
                        is_wireframe=self.config.wireframe_only
                    )
                    self._ghosts.append(ghost)
                    total_ghosts += 1

        # Show next frames
        if self.config.show_next:
            for i in range(1, min(self.config.next_frames + 1, max_total + 1)):
                if total_ghosts >= max_total:
                    break
                frame = current_frame + i
                opacity = self.config.ghost_opacity * (1.0 - (i - 1) / max(self.config.next_frames, 1))
                ghost = GhostInfo(
                    frame=frame,
                    direction="next",
                    mesh_name=f"onion_ghost_next_{frame}",
                    opacity=opacity,
                    is_wireframe=self.config.wireframe_only
                )
                self._ghosts.append(ghost)
                total_ghosts += 1

    def _clear_ghosts(self) -> None:
        """Remove all ghost meshes."""
        self._ghosts.clear()

    def get_ghosts(self) -> List[GhostInfo]:
        """
        Get list of current ghosts.

        Returns:
            List of ghost info objects
        """
        return self._ghosts.copy()

    def get_ghost_count(self) -> int:
        """Get number of active ghosts."""
        return len(self._ghosts)

    def get_previous_ghost_frames(self) -> List[int]:
        """Get frames with previous ghosts."""
        return sorted([g.frame for g in self._ghosts if g.direction == "prev"])

    def get_next_ghost_frames(self) -> List[int]:
        """Get frames with next ghosts."""
        return sorted([g.frame for g in self._ghosts if g.direction == "next"])

    # -------------------------------------------------------------------------
    # Configuration Methods
    # -------------------------------------------------------------------------

    def set_range(self, previous: int, next: int) -> None:
        """
        Set onion skin range.

        Args:
            previous: Number of frames before current
            next: Number of frames after current
        """
        self.config.previous_frames = previous
        self.config.next_frames = next
        self.update()

    def set_colors(
        self,
        previous_color: Tuple[float, float, float, float],
        next_color: Tuple[float, float, float, float]
    ) -> None:
        """
        Set onion skin colors.

        Args:
            previous_color: RGBA color for previous frames (green default)
            next_color: RGBA color for next frames (red default)
        """
        self.config.previous_color = previous_color
        self.config.next_color = next_color
        self.update()

    def set_opacity(self, opacity: float) -> None:
        """
        Set ghost opacity.

        Args:
            opacity: Opacity value (0-1)
        """
        self.config.ghost_opacity = max(0.0, min(1.0, opacity))
        self.update()

    def set_wireframe_mode(self, enabled: bool) -> None:
        """
        Set wireframe-only mode.

        Args:
            enabled: Whether to use wireframe only
        """
        self.config.wireframe_only = enabled
        self.update()

    def set_max_ghosts(self, max_count: int) -> None:
        """
        Set maximum number of ghosts.

        Args:
            max_count: Maximum ghosts to display
        """
        self.config.max_ghosts = max(1, max_count)
        self.update()

    def show_previous(self, show: bool) -> None:
        """Show or hide previous frames."""
        self.config.show_previous = show
        self.update()

    def show_next(self, show: bool) -> None:
        """Show or hide next frames."""
        self.config.show_next = show
        self.update()

    # -------------------------------------------------------------------------
    # Preset Methods
    # -------------------------------------------------------------------------

    def apply_preset(self, preset_name: str) -> bool:
        """
        Apply a named preset.

        Args:
            preset_name: Name of preset (minimal, standard, detailed)

        Returns:
            True if preset was applied
        """
        presets = {
            "minimal": OnionSkinConfig(
                previous_frames=1,
                next_frames=1,
                ghost_opacity=0.3,
                max_ghosts=2
            ),
            "standard": OnionSkinConfig(
                previous_frames=2,
                next_frames=2,
                ghost_opacity=0.3,
                max_ghosts=4
            ),
            "detailed": OnionSkinConfig(
                previous_frames=3,
                next_frames=3,
                ghost_opacity=0.25,
                max_ghosts=6
            ),
            "performance": OnionSkinConfig(
                previous_frames=1,
                next_frames=1,
                ghost_opacity=0.3,
                wireframe_only=True,
                max_ghosts=2
            ),
        }

        if preset_name in presets:
            self.config = presets[preset_name]
            self.update()
            return True
        return False

    # -------------------------------------------------------------------------
    # Info Methods
    # -------------------------------------------------------------------------

    def get_config_dict(self) -> Dict[str, Any]:
        """Get current configuration as dictionary."""
        return self.config.to_dict()

    def get_status(self) -> Dict[str, Any]:
        """Get onion skinning status."""
        return {
            "enabled": self._enabled,
            "ghost_count": len(self._ghosts),
            "previous_frames": self.get_previous_ghost_frames(),
            "next_frames": self.get_next_ghost_frames(),
            "config": self.get_config_dict()
        }


class OnionSkinManager:
    """
    Manager for multiple onion skin instances.

    Handles onion skinning for multiple armatures in a scene.

    Example:
        >>> manager = OnionSkinManager()
        >>> manager.register("hero", hero_armature)
        >>> manager.register("sidekick", sidekick_armature)
        >>> manager.enable_all()
    """

    def __init__(self):
        """Initialize manager."""
        self._instances: Dict[str, OnionSkinning] = {}

    def register(
        self,
        name: str,
        armature: Optional['bpy.types.Object'] = None,
        config: Optional[OnionSkinConfig] = None
    ) -> OnionSkinning:
        """
        Register an armature for onion skinning.

        Args:
            name: Unique name for the instance
            armature: The armature object
            config: Optional configuration

        Returns:
            The created onion skin instance
        """
        instance = OnionSkinning(armature, config)
        self._instances[name] = instance
        return instance

    def unregister(self, name: str) -> bool:
        """
        Unregister an armature.

        Args:
            name: Name of instance to remove

        Returns:
            True if instance was removed
        """
        if name in self._instances:
            self._instances[name].disable()
            del self._instances[name]
            return True
        return False

    def get(self, name: str) -> Optional[OnionSkinning]:
        """Get onion skin instance by name."""
        return self._instances.get(name)

    def enable_all(self) -> None:
        """Enable all onion skin instances."""
        for instance in self._instances.values():
            instance.enable()

    def disable_all(self) -> None:
        """Disable all onion skin instances."""
        for instance in self._instances.values():
            instance.disable()

    def update_all(self, current_frame: Optional[int] = None) -> None:
        """Update all onion skin instances."""
        for instance in self._instances.values():
            instance.update(current_frame)

    def set_preset_all(self, preset_name: str) -> None:
        """Apply preset to all instances."""
        for instance in self._instances.values():
            instance.apply_preset(preset_name)

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all instances."""
        return {
            name: instance.get_status()
            for name, instance in self._instances.items()
        }

    def clear_all(self) -> None:
        """Clear all instances."""
        self.disable_all()
        self._instances.clear()


# =============================================================================
# Convenience Functions
# =============================================================================

def enable_onion_skin(
    armature: Optional['bpy.types.Object'] = None,
    prev_frames: int = 1,
    next_frames: int = 1
) -> OnionSkinning:
    """
    Enable onion skinning for armature.

    Args:
        armature: The armature object
        prev_frames: Number of frames before current
        next_frames: Number of frames after current

    Returns:
        Configured onion skinning instance
    """
    config = OnionSkinConfig(
        previous_frames=prev_frames,
        next_frames=next_frames
    )
    skinning = OnionSkinning(armature, config)
    skinning.enable()
    return skinning


def create_onion_skin_config(
    prev_frames: int = 2,
    next_frames: int = 2,
    opacity: float = 0.3,
    wireframe: bool = False
) -> OnionSkinConfig:
    """
    Create an onion skin configuration.

    Args:
        prev_frames: Frames before current
        next_frames: Frames after current
        opacity: Ghost opacity (0-1)
        wireframe: Use wireframe only mode

    Returns:
        Onion skin configuration
    """
    return OnionSkinConfig(
        previous_frames=prev_frames,
        next_frames=next_frames,
        ghost_opacity=opacity,
        wireframe_only=wireframe
    )


def get_ghost_frame_list(
    current_frame: int,
    prev_frames: int,
    next_frames: int
) -> Dict[str, List[int]]:
    """
    Get list of ghost frames for given parameters.

    Args:
        current_frame: Current frame
        prev_frames: Number of previous frames
        next_frames: Number of next frames

    Returns:
        Dictionary with 'previous' and 'next' frame lists
    """
    previous = [current_frame - i for i in range(1, prev_frames + 1) if current_frame - i >= 1]
    next_list = [current_frame + i for i in range(1, next_frames + 1)]

    return {
        "previous": sorted(previous),
        "next": sorted(next_list),
        "current": current_frame
    }
