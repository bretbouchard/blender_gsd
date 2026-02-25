"""
HUD Settings and Configuration

Provides centralized control for enabling/disabling HUDs individually.
HUDs are opt-in by default - nothing shows until explicitly enabled.

Part of Bret's AI Stack 2.0 - Viewport Control System
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum


class HUDCategory(str, Enum):
    """Categories of HUD controls."""
    CAMERA = "camera"
    LIGHT = "light"
    MATERIAL = "material"
    RENDER = "render"
    ANIMATION = "animation"
    VFX = "vfx"
    EDITORIAL = "editorial"
    GEOMETRY = "geometry"


@dataclass
class HUDSetting:
    """Configuration for a single HUD."""
    name: str
    display_name: str
    category: HUDCategory
    enabled: bool = False
    auto_show: bool = False  # Auto-show on selection
    position: tuple = (20, 800)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "category": self.category.value,
            "enabled": self.enabled,
            "auto_show": self.auto_show,
            "position": self.position,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HUDSetting":
        return cls(
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            category=HUDCategory(data.get("category", "camera")),
            enabled=data.get("enabled", False),
            auto_show=data.get("auto_show", False),
            position=tuple(data.get("position", (20, 800))),
            description=data.get("description", ""),
        )


class HUDSettings:
    """
    Centralized HUD configuration manager.

    All HUDs are DISABLED by default. Users must explicitly enable
    the HUDs they want to see.

    Usage:
        settings = HUDSettings.get_instance()

        # Enable specific HUDs
        settings.enable("camera_hud")
        settings.enable("color_correction_hud")

        # Disable a HUD
        settings.disable("camera_hud")

        # Check if enabled
        if settings.is_enabled("camera_hud"):
            show_camera_hud()

        # Toggle
        settings.toggle("animation_hud")

        # Enable by category
        settings.enable_category(HUDCategory.VFX)

        # Get all enabled HUDs
        enabled = settings.get_enabled_huds()
    """

    _instance: Optional["HUDSettings"] = None

    # Default HUD definitions (all disabled)
    DEFAULT_HUDS: Dict[str, HUDSetting] = {
        # Camera HUDs
        "camera_hud": HUDSetting(
            name="camera_hud",
            display_name="Camera Controls",
            category=HUDCategory.CAMERA,
            enabled=False,
            auto_show=True,
            position=(20, 800),
            description="Focal length, DOF, camera shake controls",
        ),
        "camera_gizmo": HUDSetting(
            name="camera_gizmo",
            display_name="Camera Gizmos",
            category=HUDCategory.CAMERA,
            enabled=False,
            auto_show=False,
            position=(0, 0),
            description="3D viewport camera gizmos",
        ),

        # Light HUDs
        "light_hud": HUDSetting(
            name="light_hud",
            display_name="Light Controls",
            category=HUDCategory.LIGHT,
            enabled=False,
            auto_show=True,
            position=(20, 700),
            description="Intensity, color, shadow controls for lights",
        ),
        "hdri_hud": HUDSetting(
            name="hdri_hud",
            display_name="HDRI Controls",
            category=HUDCategory.LIGHT,
            enabled=False,
            auto_show=False,
            position=(20, 650),
            description="HDRI environment and rotation controls",
        ),
        "multi_light_hud": HUDSetting(
            name="multi_light_hud",
            display_name="Multi-Light Controls",
            category=HUDCategory.LIGHT,
            enabled=False,
            auto_show=False,
            position=(20, 600),
            description="Control multiple lights at once",
        ),

        # Material HUDs
        "material_hud": HUDSetting(
            name="material_hud",
            display_name="Material Controls",
            category=HUDCategory.MATERIAL,
            enabled=False,
            auto_show=True,
            position=(20, 550),
            description="Material properties quick controls",
        ),

        # Render HUDs
        "render_hud": HUDSetting(
            name="render_hud",
            display_name="Render Controls",
            category=HUDCategory.RENDER,
            enabled=False,
            auto_show=False,
            position=(20, 500),
            description="Render settings, samples, resolution",
        ),

        # Animation HUDs
        "rig_hud": HUDSetting(
            name="rig_hud",
            display_name="Rig Controls",
            category=HUDCategory.ANIMATION,
            enabled=False,
            auto_show=True,
            position=(20, 750),
            description="IK/FK blend, constraints, pose controls",
        ),
        "shape_key_hud": HUDSetting(
            name="shape_key_hud",
            display_name="Shape Key Controls",
            category=HUDCategory.ANIMATION,
            enabled=False,
            auto_show=False,
            position=(20, 600),
            description="Shape key sliders",
        ),
        "bone_hud": HUDSetting(
            name="bone_hud",
            display_name="Bone Transform Controls",
            category=HUDCategory.ANIMATION,
            enabled=False,
            auto_show=False,
            position=(20, 550),
            description="Bone location, rotation, scale",
        ),
        "animation_layer_hud": HUDSetting(
            name="animation_layer_hud",
            display_name="Animation Layer Controls",
            category=HUDCategory.ANIMATION,
            enabled=False,
            auto_show=False,
            position=(20, 500),
            description="NLA track controls",
        ),

        # VFX HUDs
        "color_correction_hud": HUDSetting(
            name="color_correction_hud",
            display_name="Color Correction",
            category=HUDCategory.VFX,
            enabled=False,
            auto_show=False,
            position=(20, 700),
            description="Exposure, contrast, saturation, LGG",
        ),
        "compositor_layer_hud": HUDSetting(
            name="compositor_layer_hud",
            display_name="Compositor Layers",
            category=HUDCategory.VFX,
            enabled=False,
            auto_show=False,
            position=(20, 600),
            description="Layer visibility, opacity, blend modes",
        ),
        "glare_hud": HUDSetting(
            name="glare_hud",
            display_name="Glare/Bloom",
            category=HUDCategory.VFX,
            enabled=False,
            auto_show=False,
            position=(20, 500),
            description="Glare threshold, intensity, streaks",
        ),
        "lens_distortion_hud": HUDSetting(
            name="lens_distortion_hud",
            display_name="Lens Distortion",
            category=HUDCategory.VFX,
            enabled=False,
            auto_show=False,
            position=(20, 450),
            description="Chromatic aberration, distortion",
        ),
        "motion_blur_hud": HUDSetting(
            name="motion_blur_hud",
            display_name="Motion Blur",
            category=HUDCategory.VFX,
            enabled=False,
            auto_show=False,
            position=(20, 400),
            description="Shutter, blur amount",
        ),
        "cryptomatte_hud": HUDSetting(
            name="cryptomatte_hud",
            display_name="Cryptomatte",
            category=HUDCategory.VFX,
            enabled=False,
            auto_show=False,
            position=(20, 350),
            description="Object/material isolation",
        ),
        "vfx_master_hud": HUDSetting(
            name="vfx_master_hud",
            display_name="VFX Master",
            category=HUDCategory.VFX,
            enabled=False,
            auto_show=False,
            position=(20, 800),
            description="All VFX controls in one panel",
        ),

        # Editorial HUDs
        "playback_hud": HUDSetting(
            name="playback_hud",
            display_name="Playback Controls",
            category=HUDCategory.EDITORIAL,
            enabled=False,
            auto_show=False,
            position=(20, 200),
            description="Play/pause, frame controls, speed",
        ),
        "track_control_hud": HUDSetting(
            name="track_control_hud",
            display_name="Track Controls",
            category=HUDCategory.EDITORIAL,
            enabled=False,
            auto_show=False,
            position=(20, 400),
            description="Track visibility, mute, solo",
        ),
        "clip_edit_hud": HUDSetting(
            name="clip_edit_hud",
            display_name="Clip Editing",
            category=HUDCategory.EDITORIAL,
            enabled=False,
            auto_show=False,
            position=(20, 600),
            description="Trim, slip, speed, opacity",
        ),
        "transition_hud": HUDSetting(
            name="transition_hud",
            display_name="Transitions",
            category=HUDCategory.EDITORIAL,
            enabled=False,
            auto_show=False,
            position=(20, 350),
            description="Transition types and duration",
        ),
        "marker_hud": HUDSetting(
            name="marker_hud",
            display_name="Timeline Markers",
            category=HUDCategory.EDITORIAL,
            enabled=False,
            auto_show=False,
            position=(20, 250),
            description="Add, navigate, delete markers",
        ),
        "editorial_master_hud": HUDSetting(
            name="editorial_master_hud",
            display_name="Editorial Master",
            category=HUDCategory.EDITORIAL,
            enabled=False,
            auto_show=False,
            position=(20, 900),
            description="All editorial controls in one panel",
        ),

        # Geometry HUDs
        "gn_modifier_hud": HUDSetting(
            name="gn_modifier_hud",
            display_name="GN Modifier Controls",
            category=HUDCategory.GEOMETRY,
            enabled=False,
            auto_show=True,
            position=(20, 700),
            description="Geometry Nodes modifier inputs",
        ),
        "simulation_hud": HUDSetting(
            name="simulation_hud",
            display_name="Simulation Controls",
            category=HUDCategory.GEOMETRY,
            enabled=False,
            auto_show=False,
            position=(20, 400),
            description="Simulation bake, reset, speed",
        ),
        "procedural_params_hud": HUDSetting(
            name="procedural_params_hud",
            display_name="Procedural Parameters",
            category=HUDCategory.GEOMETRY,
            enabled=False,
            auto_show=False,
            position=(20, 550),
            description="Seed, resolution, scale, detail",
        ),
    }

    def __init__(self):
        self._hud_settings: Dict[str, HUDSetting] = {
            name: HUDSetting(**{k: v for k, v in setting.__dict__.items()})
            for name, setting in self.DEFAULT_HUDS.items()
        }
        self._active_hud_instances: Dict[str, Any] = {}
        self._auto_show_enabled: bool = True

    @classmethod
    def get_instance(cls) -> "HUDSettings":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None

    # ==================== Enable/Disable Controls ====================

    def enable(self, hud_name: str) -> bool:
        """
        Enable a HUD by name.

        Args:
            hud_name: Name of the HUD to enable

        Returns:
            True if HUD was found and enabled
        """
        if hud_name in self._hud_settings:
            self._hud_settings[hud_name].enabled = True
            return True
        return False

    def disable(self, hud_name: str) -> bool:
        """
        Disable a HUD by name.

        Args:
            hud_name: Name of the HUD to disable

        Returns:
            True if HUD was found and disabled
        """
        if hud_name in self._hud_settings:
            self._hud_settings[hud_name].enabled = False
            # Also hide any active instance
            if hud_name in self._active_hud_instances:
                instance = self._active_hud_instances[hud_name]
                if hasattr(instance, 'hide'):
                    instance.hide()
            return True
        return False

    def toggle(self, hud_name: str) -> bool:
        """
        Toggle a HUD on/off.

        Args:
            hud_name: Name of the HUD to toggle

        Returns:
            New state (True = enabled)
        """
        if hud_name in self._hud_settings:
            self._hud_settings[hud_name].enabled = not self._hud_settings[hud_name].enabled
            return self._hud_settings[hud_name].enabled
        return False

    def is_enabled(self, hud_name: str) -> bool:
        """Check if a HUD is enabled."""
        return self._hud_settings.get(hud_name, HUDSetting("", "", HUDCategory.CAMERA)).enabled

    def is_auto_show(self, hud_name: str) -> bool:
        """Check if a HUD has auto-show enabled."""
        setting = self._hud_settings.get(hud_name)
        return setting.enabled and setting.auto_show if setting else False

    # ==================== Category Controls ====================

    def enable_category(self, category: HUDCategory) -> List[str]:
        """
        Enable all HUDs in a category.

        Args:
            category: Category to enable

        Returns:
            List of HUD names that were enabled
        """
        enabled = []
        for name, setting in self._hud_settings.items():
            if setting.category == category:
                setting.enabled = True
                enabled.append(name)
        return enabled

    def disable_category(self, category: HUDCategory) -> List[str]:
        """
        Disable all HUDs in a category.

        Args:
            category: Category to disable

        Returns:
            List of HUD names that were disabled
        """
        disabled = []
        for name, setting in self._hud_settings.items():
            if setting.category == category:
                setting.enabled = False
                disabled.append(name)
        return disabled

    def get_category_huds(self, category: HUDCategory) -> List[str]:
        """Get all HUD names in a category."""
        return [
            name for name, setting in self._hud_settings.items()
            if setting.category == category
        ]

    # ==================== Query Methods ====================

    def get_enabled_huds(self) -> List[str]:
        """Get list of all enabled HUD names."""
        return [
            name for name, setting in self._hud_settings.items()
            if setting.enabled
        ]

    def get_auto_show_huds(self) -> List[str]:
        """Get list of HUDs that should auto-show."""
        return [
            name for name, setting in self._hud_settings.items()
            if setting.enabled and setting.auto_show
        ]

    def get_all_huds(self) -> Dict[str, HUDSetting]:
        """Get all HUD settings."""
        return self._hud_settings.copy()

    def get_hud_setting(self, hud_name: str) -> Optional[HUDSetting]:
        """Get settings for a specific HUD."""
        return self._hud_settings.get(hud_name)

    # ==================== Instance Management ====================

    def register_hud_instance(self, hud_name: str, instance: Any) -> None:
        """Register an active HUD instance."""
        self._active_hud_instances[hud_name] = instance

    def unregister_hud_instance(self, hud_name: str) -> None:
        """Unregister a HUD instance."""
        self._active_hud_instances.pop(hud_name, None)

    def get_hud_instance(self, hud_name: str) -> Optional[Any]:
        """Get an active HUD instance."""
        return self._active_hud_instances.get(hud_name)

    def hide_all(self) -> None:
        """Hide all active HUD instances."""
        for instance in self._active_hud_instances.values():
            if hasattr(instance, 'hide'):
                instance.hide()

    def show_all_enabled(self) -> None:
        """Show all HUDs that are enabled."""
        for name, instance in self._active_hud_instances.items():
            if self.is_enabled(name) and hasattr(instance, 'show'):
                instance.show()

    # ==================== Auto-Show Control ====================

    def set_auto_show_enabled(self, enabled: bool) -> None:
        """Enable or disable auto-show globally."""
        self._auto_show_enabled = enabled

    def is_auto_show_enabled(self) -> bool:
        """Check if auto-show is enabled globally."""
        return self._auto_show_enabled

    # ==================== Position Control ====================

    def set_hud_position(self, hud_name: str, position: tuple) -> bool:
        """Set position for a HUD."""
        if hud_name in self._hud_settings:
            self._hud_settings[hud_name].position = position
            return True
        return False

    def get_hud_position(self, hud_name: str) -> tuple:
        """Get position for a HUD."""
        setting = self._hud_settings.get(hud_name)
        return setting.position if setting else (20, 800)

    # ==================== Serialization ====================

    def to_dict(self) -> Dict[str, Any]:
        """Export settings to dictionary."""
        return {
            "auto_show_enabled": self._auto_show_enabled,
            "huds": {
                name: setting.to_dict()
                for name, setting in self._hud_settings.items()
            },
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Import settings from dictionary."""
        self._auto_show_enabled = data.get("auto_show_enabled", True)
        for name, hud_data in data.get("huds", {}).items():
            if name in self._hud_settings:
                setting = HUDSetting.from_dict(hud_data)
                self._hud_settings[name] = setting

    def save_to_file(self, path: str) -> bool:
        """Save settings to JSON file."""
        import json
        try:
            with open(path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save HUD settings: {e}")
            return False

    def load_from_file(self, path: str) -> bool:
        """Load settings from JSON file."""
        import json
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            self.from_dict(data)
            return True
        except Exception as e:
            print(f"Failed to load HUD settings: {e}")
            return False

    # ==================== Presets ====================

    def apply_preset(self, preset_name: str) -> List[str]:
        """
        Apply a preset configuration.

        Available presets:
        - "none": Disable all HUDs
        - "minimal": Only essential HUDs (camera, playback)
        - "animation": Animation-focused HUDs
        - "vfx": VFX/compositor-focused HUDs
        - "editorial": Timeline/editing-focused HUDs
        - "all": Enable all HUDs

        Returns:
            List of HUD names that were enabled
        """
        # Disable all first
        for setting in self._hud_settings.values():
            setting.enabled = False

        presets = {
            "none": [],
            "minimal": ["camera_hud", "playback_hud"],
            "animation": ["rig_hud", "shape_key_hud", "bone_hud", "playback_hud"],
            "vfx": ["color_correction_hud", "compositor_layer_hud", "glare_hud"],
            "editorial": ["playback_hud", "track_control_hud", "clip_edit_hud", "marker_hud"],
            "geometry": ["gn_modifier_hud", "simulation_hud", "procedural_params_hud"],
            "all": list(self._hud_settings.keys()),
        }

        enabled = []
        for hud_name in presets.get(preset_name, []):
            if hud_name in self._hud_settings:
                self._hud_settings[hud_name].enabled = True
                enabled.append(hud_name)

        return enabled

    def get_available_presets(self) -> List[str]:
        """Get list of available preset names."""
        return ["none", "minimal", "animation", "vfx", "editorial", "geometry", "all"]


# ==================== Convenience Functions ====================

def get_hud_settings() -> HUDSettings:
    """Get the HUD settings singleton."""
    return HUDSettings.get_instance()


def enable_hud(hud_name: str) -> bool:
    """Enable a HUD by name."""
    return HUDSettings.get_instance().enable(hud_name)


def disable_hud(hud_name: str) -> bool:
    """Disable a HUD by name."""
    return HUDSettings.get_instance().disable(hud_name)


def toggle_hud(hud_name: str) -> bool:
    """Toggle a HUD on/off."""
    return HUDSettings.get_instance().toggle(hud_name)


def is_hud_enabled(hud_name: str) -> bool:
    """Check if a HUD is enabled."""
    return HUDSettings.get_instance().is_enabled(hud_name)


def apply_hud_preset(preset_name: str) -> List[str]:
    """Apply a HUD preset configuration."""
    return HUDSettings.get_instance().apply_preset(preset_name)


def get_enabled_huds() -> List[str]:
    """Get list of all enabled HUDs."""
    return HUDSettings.get_instance().get_enabled_huds()


def hide_all_huds() -> None:
    """Hide all active HUDs."""
    HUDSettings.get_instance().hide_all()
