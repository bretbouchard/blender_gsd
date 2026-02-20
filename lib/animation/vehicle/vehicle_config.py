"""
Vehicle Configuration Module

Manages loading, saving, and validating vehicle configurations.

Phase 13.6: Vehicle Plugins Integration (REQ-ANIM-08)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Any
from pathlib import Path
import yaml
import logging

from ..types import (
    VehicleConfig,
    VehicleType,
    WheelConfig,
    SteeringConfig,
    SuspensionConfig,
    VehicleDimensions,
)

logger = logging.getLogger(__name__)

# Configuration root directory
VEHICLE_CONFIG_ROOT = Path(__file__).parent.parent.parent.parent / "configs" / "animation" / "vehicle"


class VehicleConfigManager:
    """Manages vehicle configuration files."""

    def __init__(self, config_root: Optional[Path] = None):
        """
        Initialize the configuration manager.

        Args:
            config_root: Optional custom config root directory
        """
        self.config_root = config_root or VEHICLE_CONFIG_ROOT
        self._cache: Dict[str, VehicleConfig] = {}

    def load(self, config_id: str, use_cache: bool = True) -> VehicleConfig:
        """
        Load vehicle configuration from YAML file.

        Args:
            config_id: Configuration identifier (filename without .yaml)
            use_cache: Whether to use cached config if available

        Returns:
            Loaded VehicleConfig

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        # Check cache
        if use_cache and config_id in self._cache:
            return self._cache[config_id]

        # Find config file
        path = self.config_root / f"{config_id}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Vehicle config not found: {config_id}")

        # Load YAML
        with open(path) as f:
            data = yaml.safe_load(f)

        # Parse into VehicleConfig
        config = self._parse_config(data)

        # Cache it
        if use_cache:
            self._cache[config_id] = config

        logger.info(f"Loaded vehicle config: {config_id}")
        return config

    def save(
        self,
        config: VehicleConfig,
        path: Optional[Path] = None,
        format: str = 'yaml'
    ) -> Path:
        """
        Save vehicle configuration to file.

        Args:
            config: VehicleConfig to save
            path: Optional custom path (defaults to config_root/{id}.yaml)
            format: Output format ('yaml' or 'json')

        Returns:
            Path to saved file
        """
        if path is None:
            path = self.config_root / f"{config.id}.yaml"

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict
        data = config.to_dict()

        # Write file
        if format == 'yaml':
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        elif format == 'json':
            import json
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unknown format: {format}")

        # Update cache
        self._cache[config.id] = config

        logger.info(f"Saved vehicle config: {path}")
        return path

    def list_configs(self) -> List[str]:
        """
        List available vehicle configuration IDs.

        Returns:
            List of configuration IDs (filenames without extension)
        """
        if not self.config_root.exists():
            return []

        configs = []
        for f in self.config_root.glob("*.yaml"):
            configs.append(f.stem)

        return sorted(configs)

    def validate(self, config: VehicleConfig) -> List[str]:
        """
        Validate a vehicle configuration.

        Args:
            config: VehicleConfig to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required fields
        if not config.id:
            errors.append("Vehicle ID is required")
        if not config.name:
            errors.append("Vehicle name is required")

        # Validate dimensions
        if config.dimensions.length <= 0:
            errors.append("Vehicle length must be positive")
        if config.dimensions.width <= 0:
            errors.append("Vehicle width must be positive")
        if config.dimensions.height <= 0:
            errors.append("Vehicle height must be positive")
        if config.dimensions.wheelbase <= 0:
            errors.append("Wheelbase must be positive")

        # Validate wheels
        if not config.wheels:
            errors.append("At least one wheel is required")

        for i, wheel in enumerate(config.wheels):
            if not wheel.id:
                errors.append(f"Wheel {i}: ID is required")
            if wheel.radius <= 0:
                errors.append(f"Wheel {i}: Radius must be positive")
            if wheel.width <= 0:
                errors.append(f"Wheel {i}: Width must be positive")

        # Validate steering
        if config.steering.max_angle <= 0:
            errors.append("Steering max_angle must be positive")
        if config.steering.max_angle > 90:
            errors.append("Steering max_angle seems too large (>90 degrees)")

        # Validate suspension
        if config.suspension.travel <= 0:
            errors.append("Suspension travel must be positive")
        if config.suspension.stiffness <= 0:
            errors.append("Suspension stiffness must be positive")
        if config.suspension.damping < 0:
            errors.append("Suspension damping cannot be negative")

        # Validate mass
        if config.mass <= 0:
            errors.append("Vehicle mass must be positive")

        # Validate performance
        if config.max_speed <= 0:
            errors.append("Max speed must be positive")
        if config.acceleration <= 0:
            errors.append("Acceleration must be positive")

        return errors

    def _parse_config(self, data: Dict[str, Any]) -> VehicleConfig:
        """
        Parse YAML data into VehicleConfig.

        Args:
            data: Raw dictionary from YAML

        Returns:
            Parsed VehicleConfig
        """
        # Parse dimensions
        dims_data = data.get('dimensions', {})
        dimensions = VehicleDimensions(
            length=dims_data.get('length', 4.5),
            width=dims_data.get('width', 1.8),
            height=dims_data.get('height', 1.4),
            wheelbase=dims_data.get('wheelbase', 2.7),
            track_width=dims_data.get('track_width', 1.6),
            ground_clearance=dims_data.get('ground_clearance', 0.15),
        )

        # Parse wheels
        wheels = []
        for w in data.get('wheels', []):
            wheels.append(WheelConfig(
                id=w['id'],
                position=tuple(w['position']),
                radius=w.get('radius', 0.35),
                width=w.get('width', 0.2),
                steering=w.get('steering', False),
                driven=w.get('driven', False),
                suspended=w.get('suspended', True),
                max_steering_angle=w.get('max_steering_angle', 35.0),
            ))

        # Parse steering
        steer_data = data.get('steering', {})
        steering = SteeringConfig(
            max_angle=steer_data.get('max_angle', 35),
            ackermann=steer_data.get('ackermann', True),
            steering_wheel_ratio=steer_data.get('steering_wheel_ratio', 1.0),
            speed_sensitive=steer_data.get('speed_sensitive', False),
            return_speed=steer_data.get('return_speed', 1.0),
        )

        # Parse suspension
        susp_data = data.get('suspension', {})
        suspension = SuspensionConfig(
            type=susp_data.get('type', 'independent'),
            travel=susp_data.get('travel', 0.15),
            stiffness=susp_data.get('stiffness', 1.0),
            damping=susp_data.get('damping', 0.5),
            anti_roll=susp_data.get('anti_roll', 0.0),
            preload=susp_data.get('preload', 0.0),
        )

        return VehicleConfig(
            id=data['id'],
            name=data['name'],
            vehicle_type=VehicleType(data.get('type', 'automobile')),
            dimensions=dimensions,
            wheels=wheels,
            steering=steering,
            suspension=suspension,
            mesh_paths=data.get('mesh', {}),
            mass=data.get('mass', 1500.0),
            max_speed=data.get('max_speed', 200.0),
            acceleration=data.get('acceleration', 5.0),
            metadata=data.get('metadata', {}),
        )

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()


# Convenience functions
_manager = VehicleConfigManager()


def load_vehicle_config(config_id: str) -> VehicleConfig:
    """Load a vehicle configuration by ID."""
    return _manager.load(config_id)


def save_vehicle_config(config: VehicleConfig, path: Optional[Path] = None) -> Path:
    """Save a vehicle configuration."""
    return _manager.save(config, path)


def list_vehicle_configs() -> List[str]:
    """List available vehicle configuration IDs."""
    return _manager.list_configs()


def validate_vehicle_config(config: VehicleConfig) -> List[str]:
    """Validate a vehicle configuration."""
    return _manager.validate(config)


def create_default_vehicle_config(
    id: str = "default_car",
    name: str = "Default Car",
    vehicle_type: VehicleType = VehicleType.AUTOMOBILE,
    wheel_count: int = 4
) -> VehicleConfig:
    """
    Create a default vehicle configuration.

    Args:
        id: Configuration ID
        name: Vehicle name
        vehicle_type: Type of vehicle
        wheel_count: Number of wheels (4 for car, 2 for motorcycle)

    Returns:
        VehicleConfig with sensible defaults
    """
    dimensions = VehicleDimensions()
    steering = SteeringConfig()
    suspension = SuspensionConfig()

    # Create default wheels
    wheels = []
    if wheel_count >= 4:
        # Standard 4-wheel car layout
        wb = dimensions.wheelbase / 2
        tw = dimensions.track_width / 2
        wheel_radius = 0.35

        wheels = [
            WheelConfig(id="FL", position=(wb, tw, wheel_radius), steering=True, driven=False),
            WheelConfig(id="FR", position=(wb, -tw, wheel_radius), steering=True, driven=False),
            WheelConfig(id="RL", position=(-wb, tw, wheel_radius), steering=False, driven=True),
            WheelConfig(id="RR", position=(-wb, -tw, wheel_radius), steering=False, driven=True),
        ]
    elif wheel_count == 2:
        # Motorcycle layout
        wb = dimensions.wheelbase / 2
        wheel_radius = 0.3

        wheels = [
            WheelConfig(id="F", position=(wb, 0, wheel_radius), steering=True, driven=False),
            WheelConfig(id="R", position=(-wb, 0, wheel_radius), steering=False, driven=True),
        ]

    return VehicleConfig(
        id=id,
        name=name,
        vehicle_type=vehicle_type,
        dimensions=dimensions,
        wheels=wheels,
        steering=steering,
        suspension=suspension,
        mass=1500.0,
        max_speed=200.0,
        acceleration=5.0,
    )
