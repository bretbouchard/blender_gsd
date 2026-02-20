"""
Vehicle Plugin Interface Module

Abstract interface for vehicle animation plugins and
built-in Blender physics implementation.

Phase 13.6: Vehicle Plugins Integration (REQ-ANIM-08)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VehiclePluginInterface(ABC):
    """Abstract interface for vehicle animation plugins."""

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the plugin is installed and available.

        Returns:
            True if plugin can be used, False otherwise
        """
        pass

    @abstractmethod
    def create_vehicle(self, config: Dict[str, Any]) -> Any:
        """
        Create a vehicle from configuration.

        Args:
            config: Vehicle configuration dictionary

        Returns:
            Created vehicle object or reference
        """
        pass

    @abstractmethod
    def update_behavior(self, vehicle_id: str, behavior: Dict[str, Any]) -> None:
        """
        Update vehicle behavior parameters.

        Args:
            vehicle_id: Identifier of the vehicle
            behavior: New behavior parameters
        """
        pass

    @abstractmethod
    def remove_vehicle(self, vehicle_id: str) -> bool:
        """
        Remove a vehicle from the scene.

        Args:
            vehicle_id: Identifier of the vehicle to remove

        Returns:
            True if removal succeeded, False otherwise
        """
        pass

    @abstractmethod
    def animate_along_path(self, vehicle_id: str, path: Any) -> None:
        """
        Animate vehicle along a path/curve.

        Args:
            vehicle_id: Identifier of the vehicle
            path: Curve object to follow
        """
        pass

    @abstractmethod
    def export_vehicle_data(
        self,
        vehicle_id: str,
        output_path: Path,
        format: str = 'fbx'
    ) -> bool:
        """
        Export vehicle animation data.

        Args:
            vehicle_id: Identifier of the vehicle
            output_path: Path for export file
            format: Export format (fbx, alembic, etc.)

        Returns:
            True if export succeeded, False otherwise
        """
        pass

    @abstractmethod
    def get_vehicle_info(self, vehicle_id: str) -> Dict[str, Any]:
        """
        Get information about a vehicle.

        Args:
            vehicle_id: Identifier of the vehicle

        Returns:
            Dictionary with vehicle information
        """
        pass


class BlenderPhysicsVehicle(VehiclePluginInterface):
    """
    Vehicle implementation using Blender's built-in physics.

    This plugin uses Blender's rigid body physics for basic
    vehicle simulation. It's always available but provides
    limited functionality compared to specialized plugins.

    Note: This is keyframe-based animation with physics helpers,
    NOT a real-time driving simulator.
    """

    def __init__(self):
        self._vehicles: Dict[str, Dict[str, Any]] = {}

    def is_available(self) -> bool:
        """Blender physics is always available."""
        return True

    def create_vehicle(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a vehicle using Blender physics.

        Args:
            config: Vehicle configuration with:
                - name: Vehicle name
                - mass: Vehicle mass in kg
                - dimensions: (length, width, height)
                - position: Starting position

        Returns:
            Created vehicle object dictionary
        """
        name = config.get('name', 'vehicle')
        mass = config.get('mass', 1000.0)

        # Create mock vehicle body (in real Blender, would create mesh)
        vehicle = {
            'name': name,
            'type': 'VEHICLE_BODY',
            'mass': mass,
            'rigid_body': {
                'type': 'ACTIVE',
                'mass': mass,
                'friction': 0.5,
                'restitution': 0.2,
            },
            'location': config.get('position', [0, 0, 0]),
            'dimensions': config.get('dimensions', [4.5, 1.8, 1.4]),
            'wheels': [],
            'constraints': [],
        }

        self._vehicles[name] = vehicle
        logger.info(f"Created physics vehicle: {name}")

        return vehicle

    def update_behavior(self, vehicle_id: str, behavior: Dict[str, Any]) -> None:
        """
        Update vehicle behavior parameters.

        Args:
            vehicle_id: Name of the vehicle
            behavior: New parameters (mass, friction, etc.)
        """
        vehicle = self._vehicles.get(vehicle_id)
        if vehicle:
            if 'mass' in behavior:
                vehicle['mass'] = behavior['mass']
                vehicle['rigid_body']['mass'] = behavior['mass']
            if 'friction' in behavior:
                vehicle['rigid_body']['friction'] = behavior['friction']
            if 'restitution' in behavior:
                vehicle['rigid_body']['restitution'] = behavior['restitution']

    def remove_vehicle(self, vehicle_id: str) -> bool:
        """Remove a vehicle."""
        if vehicle_id in self._vehicles:
            del self._vehicles[vehicle_id]
            return True
        return False

    def animate_along_path(self, vehicle_id: str, path: Any) -> None:
        """
        Animate vehicle along a path using Follow Path constraint.

        Args:
            vehicle_id: Name of the vehicle
            path: Curve object to follow
        """
        vehicle = self._vehicles.get(vehicle_id)
        if vehicle and path:
            constraint = {
                'type': 'FOLLOW_PATH',
                'target': path,
                'use_curve_follow': True,
                'use_fixed_location': True,
                'offset_factor': 0.0,
            }
            vehicle['constraints'].append(constraint)
            logger.info(f"Added path following to {vehicle_id}")

    def export_vehicle_data(
        self,
        vehicle_id: str,
        output_path: Path,
        format: str = 'fbx'
    ) -> bool:
        """
        Export vehicle animation data.

        Args:
            vehicle_id: Name of the vehicle
            output_path: Path for export
            format: Export format

        Returns:
            True if successful
        """
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return False

        # Mock export (real implementation would use bpy.ops.export)
        logger.info(f"Exporting {vehicle_id} to {output_path} as {format}")
        return True

    def get_vehicle_info(self, vehicle_id: str) -> Dict[str, Any]:
        """Get vehicle information."""
        return self._vehicles.get(vehicle_id, {})

    def get_all_vehicles(self) -> List[str]:
        """Get list of all vehicle names."""
        return list(self._vehicles.keys())

    def add_wheel(
        self,
        vehicle_id: str,
        wheel_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a wheel to a vehicle.

        Args:
            vehicle_id: Name of the vehicle
            wheel_config: Wheel configuration

        Returns:
            Created wheel object
        """
        vehicle = self._vehicles.get(vehicle_id)
        if not vehicle:
            return {}

        wheel = {
            'name': wheel_config.get('name', f"wheel_{len(vehicle['wheels'])}"),
            'type': 'WHEEL',
            'position': wheel_config.get('position', [0, 0, 0]),
            'radius': wheel_config.get('radius', 0.35),
            'steering': wheel_config.get('steering', False),
            'driven': wheel_config.get('driven', False),
        }

        vehicle['wheels'].append(wheel)
        return wheel


class VehicleRiggerPlugin(VehiclePluginInterface):
    """
    Placeholder for the commercial Vehicle Rigger plugin.

    This plugin provides advanced vehicle rigging but requires
    a separate purchase and installation.
    """

    def __init__(self):
        self._available = False  # Would check for actual plugin

    def is_available(self) -> bool:
        """Check if Vehicle Rigger is installed."""
        return self._available

    def create_vehicle(self, config: Dict[str, Any]) -> Any:
        """Create vehicle using Vehicle Rigger."""
        if not self._available:
            raise RuntimeError("Vehicle Rigger plugin not installed")
        # Would delegate to actual plugin
        return None

    def update_behavior(self, vehicle_id: str, behavior: Dict[str, Any]) -> None:
        if not self._available:
            raise RuntimeError("Vehicle Rigger plugin not installed")

    def remove_vehicle(self, vehicle_id: str) -> bool:
        if not self._available:
            return False
        return True

    def animate_along_path(self, vehicle_id: str, path: Any) -> None:
        if not self._available:
            raise RuntimeError("Vehicle Rigger plugin not installed")

    def export_vehicle_data(
        self,
        vehicle_id: str,
        output_path: Path,
        format: str = 'fbx'
    ) -> bool:
        if not self._available:
            return False
        return True

    def get_vehicle_info(self, vehicle_id: str) -> Dict[str, Any]:
        return {'available': self._available}


# Plugin registry
_PLUGINS: Dict[str, VehiclePluginInterface] = {
    'blender_physics': BlenderPhysicsVehicle(),
    'vehicle_rigger': VehicleRiggerPlugin(),
}


def get_plugin(name: str) -> VehiclePluginInterface:
    """
    Get vehicle plugin by name.

    Args:
        name: Plugin name ('blender_physics', 'vehicle_rigger', etc.)

    Returns:
        VehiclePluginInterface instance

    Raises:
        ValueError: If plugin name is not recognized
    """
    if name not in _PLUGINS:
        raise ValueError(
            f"Unknown plugin: {name}. "
            f"Available: {list(_PLUGINS.keys())}"
        )
    return _PLUGINS[name]


def get_available_plugins() -> List[str]:
    """
    Get list of available plugin names.

    Returns:
        List of plugin names that are installed and available
    """
    return [name for name, plugin in _PLUGINS.items() if plugin.is_available()]


def is_plugin_available(name: str) -> bool:
    """
    Check if a specific plugin is available.

    Args:
        name: Plugin name to check

    Returns:
        True if plugin exists and is available
    """
    plugin = _PLUGINS.get(name)
    return plugin is not None and plugin.is_available()


def register_plugin(name: str, plugin: VehiclePluginInterface) -> None:
    """
    Register a new vehicle plugin.

    Args:
        name: Name for the plugin
        plugin: Plugin instance
    """
    _PLUGINS[name] = plugin
    logger.info(f"Registered vehicle plugin: {name}")
