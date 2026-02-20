"""
Plugin Interface for Crowd Systems

Provides an abstract interface and implementations for various crowd simulation plugins.

Phase 13.5: Crowd System (REQ-ANIM-07)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import warnings

from ..types import CrowdConfig
from .boids_wrapper import BoidsWrapper


class CrowdPluginInterface(ABC):
    """Abstract interface for crowd simulation plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Get the plugin version."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the plugin is installed and available.

        Returns:
            True if the plugin can be used
        """
        pass

    @abstractmethod
    def create_crowd(self, config: CrowdConfig) -> Any:
        """Create a crowd from configuration.

        Args:
            config: The crowd configuration

        Returns:
            Plugin-specific crowd object
        """
        pass

    @abstractmethod
    def update_behavior(self, crowd_id: str, behavior: Dict[str, Any]) -> None:
        """Update crowd behavior at runtime.

        Args:
            crowd_id: Identifier for the crowd
            behavior: Behavior parameters to update
        """
        pass

    @abstractmethod
    def remove_crowd(self, crowd_id: str) -> bool:
        """Remove a crowd from the scene.

        Args:
            crowd_id: Identifier for the crowd

        Returns:
            True if successfully removed
        """
        pass

    @abstractmethod
    def get_crowd_info(self, crowd_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a crowd.

        Args:
            crowd_id: Identifier for the crowd

        Returns:
            Dictionary with crowd information or None if not found
        """
        pass

    @abstractmethod
    def export_crowd_data(
        self,
        crowd_id: str,
        output_path: Path,
        format: str = 'yaml'
    ) -> bool:
        """Export crowd data to file.

        Args:
            crowd_id: Identifier for the crowd
            output_path: Path to save the export
            format: Export format ('yaml', 'json', 'bpy')

        Returns:
            True if export successful
        """
        pass

    def get_capabilities(self) -> Dict[str, bool]:
        """Get plugin capabilities.

        Returns:
            Dictionary of capability names to availability
        """
        return {
            'collision_avoidance': True,
            'path_following': True,
            'behavior_states': True,
            'lod': False,
            'animation_blending': False,
        }

    def get_supported_crowd_types(self) -> List[str]:
        """Get list of supported crowd types.

        Returns:
            List of crowd type strings
        """
        return ['pedestrian', 'creature', 'custom']


class BoidsPlugin(CrowdPluginInterface):
    """Boids plugin using Blender's built-in particle system."""

    def __init__(self):
        """Initialize the boids plugin."""
        self._crowds: Dict[str, BoidsWrapper] = {}

    @property
    def name(self) -> str:
        """Get plugin name."""
        return "Blender Boids"

    @property
    def version(self) -> str:
        """Get plugin version."""
        return "1.0.0"  # Built-in, version tied to Blender

    def is_available(self) -> bool:
        """Check if boids is available (always True for Blender)."""
        return True

    def create_crowd(self, config: CrowdConfig) -> BoidsWrapper:
        """Create a boid-based crowd from configuration.

        Args:
            config: The crowd configuration

        Returns:
            Configured BoidsWrapper instance
        """
        # Validate particle count
        from ..types import MAX_PARTICLE_COUNT, WARN_PARTICLE_COUNT

        if config.spawn.count > MAX_PARTICLE_COUNT:
            raise ValueError(
                f"Particle count {config.spawn.count} exceeds maximum {MAX_PARTICLE_COUNT}"
            )

        if config.spawn.count > WARN_PARTICLE_COUNT:
            warnings.warn(
                f"Particle count {config.spawn.count} is high. "
                "Performance may be affected.",
                UserWarning
            )

        # Create emitter based on spawn configuration
        area = config.spawn.area
        center_x = (area[0][0] + area[1][0]) / 2
        center_y = (area[0][1] + area[1][1]) / 2
        size = max(abs(area[1][0] - area[0][0]), abs(area[1][1] - area[0][1]))

        emitter = BoidsWrapper.create_emitter(
            name=f"{config.id}_emitter",
            location=(center_x, center_y, config.spawn.height),
            size=size
        )

        # Create boid system
        wrapper = BoidsWrapper.create_boids_system(
            emitter=emitter,
            name=config.id,
            particle_count=config.spawn.count,
        )

        # Apply crowd configuration
        wrapper.apply_crowd_config(config)

        # Store for later reference
        self._crowds[config.id] = wrapper

        return wrapper

    def update_behavior(self, crowd_id: str, behavior: Dict[str, Any]) -> None:
        """Update crowd behavior.

        Args:
            crowd_id: The crowd identifier
            behavior: New behavior parameters
        """
        if crowd_id not in self._crowds:
            raise KeyError(f"Crowd '{crowd_id}' not found")

        wrapper = self._crowds[crowd_id]

        # Update walk speed if provided
        if 'walk_speed' in behavior:
            settings = wrapper.get_boid_settings()
            speed = behavior['walk_speed']
            if isinstance(speed, (list, tuple)) and len(speed) >= 2:
                settings.land_speed_max = speed[1]
            wrapper.configure_boid_settings(settings)

    def remove_crowd(self, crowd_id: str) -> bool:
        """Remove a crowd.

        Args:
            crowd_id: The crowd identifier

        Returns:
            True if removed successfully
        """
        if crowd_id in self._crowds:
            del self._crowds[crowd_id]
            return True
        return False

    def get_crowd_info(self, crowd_id: str) -> Optional[Dict[str, Any]]:
        """Get crowd information.

        Args:
            crowd_id: The crowd identifier

        Returns:
            Crowd info dictionary or None
        """
        if crowd_id not in self._crowds:
            return None

        wrapper = self._crowds[crowd_id]
        ps = wrapper.particle_system

        if ps:
            return {
                'id': crowd_id,
                'particle_count': ps.get('count', 0),
                'rules': [r.to_dict() for r in wrapper.get_rules()],
                'settings': wrapper.get_boid_settings().to_dict(),
            }
        return None

    def export_crowd_data(
        self,
        crowd_id: str,
        output_path: Path,
        format: str = 'yaml'
    ) -> bool:
        """Export crowd data.

        Args:
            crowd_id: The crowd identifier
            output_path: Path to save
            format: Export format

        Returns:
            True if successful
        """
        info = self.get_crowd_info(crowd_id)
        if not info:
            return False

        output_path = Path(output_path)

        if format == 'yaml':
            import yaml
            with open(output_path, 'w') as f:
                yaml.dump(info, f, default_flow_style=False)
            return True

        elif format == 'json':
            import json
            with open(output_path, 'w') as f:
                json.dump(info, f, indent=2)
            return True

        return False

    def get_capabilities(self) -> Dict[str, bool]:
        """Get boids plugin capabilities."""
        return {
            'collision_avoidance': True,
            'path_following': True,
            'behavior_states': True,
            'lod': False,  # Basic boids doesn't have built-in LOD
            'animation_blending': False,
            'flight': True,
            'land': True,
        }


class BlenderCrowdPlugin(CrowdPluginInterface):
    """BlenderCrowd plugin integration (placeholder).

    This is a placeholder for the commercial BlenderCrowd addon.
    When installed, it would provide advanced crowd simulation features.
    """

    MIN_VERSION = "2.0"  # Minimum required version

    def __init__(self):
        """Initialize the BlenderCrowd plugin wrapper."""
        self._available = False
        self._version = "0.0.0"
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if BlenderCrowd is available and get version."""
        # In real implementation, would check bpy.context.preferences.addons
        # For now, always unavailable as it's a commercial plugin
        self._available = False
        self._version = "0.0.0"

    @property
    def name(self) -> str:
        """Get plugin name."""
        return "BlenderCrowd"

    @property
    def version(self) -> str:
        """Get plugin version."""
        return self._version

    def is_available(self) -> bool:
        """Check if BlenderCrowd is installed."""
        return self._available

    def create_crowd(self, config: CrowdConfig) -> Any:
        """Create a BlenderCrowd crowd.

        Args:
            config: The crowd configuration

        Returns:
            Crowd object or raises error if not available
        """
        if not self._available:
            raise RuntimeError(
                "BlenderCrowd plugin is not installed. "
                "Purchase from https://blendercrowd.com and install the addon."
            )

        # Placeholder - would use actual BlenderCrowd API
        raise NotImplementedError("BlenderCrowd integration not implemented")

    def update_behavior(self, crowd_id: str, behavior: Dict[str, Any]) -> None:
        """Update BlenderCrowd behavior."""
        if not self._available:
            raise RuntimeError("BlenderCrowd plugin is not installed")

        raise NotImplementedError("BlenderCrowd integration not implemented")

    def remove_crowd(self, crowd_id: str) -> bool:
        """Remove a BlenderCrowd crowd."""
        if not self._available:
            return False

        raise NotImplementedError("BlenderCrowd integration not implemented")

    def get_crowd_info(self, crowd_id: str) -> Optional[Dict[str, Any]]:
        """Get BlenderCrowd crowd info."""
        if not self._available:
            return None

        raise NotImplementedError("BlenderCrowd integration not implemented")

    def export_crowd_data(
        self,
        crowd_id: str,
        output_path: Path,
        format: str = 'yaml'
    ) -> bool:
        """Export BlenderCrowd data."""
        if not self._available:
            return False

        raise NotImplementedError("BlenderCrowd integration not implemented")

    def get_capabilities(self) -> Dict[str, bool]:
        """Get BlenderCrowd capabilities."""
        if not self._available:
            return {
                'collision_avoidance': False,
                'path_following': False,
                'behavior_states': False,
                'lod': False,
                'animation_blending': False,
            }

        return {
            'collision_avoidance': True,
            'path_following': True,
            'behavior_states': True,
            'lod': True,
            'animation_blending': True,
            'navmesh': True,
            'ragdoll': True,
        }


# Plugin registry
_PLUGINS: Dict[str, CrowdPluginInterface] = {
    'boids': BoidsPlugin(),
    'blender_crowd': BlenderCrowdPlugin(),
}


def get_plugin(name: str) -> CrowdPluginInterface:
    """Get a crowd plugin by name.

    Args:
        name: Plugin name ('boids', 'blender_crowd')

    Returns:
        The requested plugin

    Raises:
        KeyError: If plugin not found
    """
    if name in _PLUGINS:
        return _PLUGINS[name]

    raise KeyError(
        f"Plugin '{name}' not found. Available plugins: {list(_PLUGINS.keys())}"
    )


def get_available_plugins() -> List[str]:
    """Get list of available plugins.

    Returns:
        List of plugin names that are available
    """
    return [name for name, plugin in _PLUGINS.items() if plugin.is_available()]


def is_plugin_available(name: str) -> bool:
    """Check if a specific plugin is available.

    Args:
        name: Plugin name to check

    Returns:
        True if plugin is available
    """
    if name not in _PLUGINS:
        return False
    return _PLUGINS[name].is_available()


def register_plugin(name: str, plugin: CrowdPluginInterface) -> None:
    """Register a custom plugin.

    Args:
        name: Name to register the plugin under
        plugin: The plugin instance
    """
    _PLUGINS[name] = plugin


def get_all_plugins() -> Dict[str, CrowdPluginInterface]:
    """Get all registered plugins.

    Returns:
        Dictionary of plugin name to plugin instance
    """
    return _PLUGINS.copy()
