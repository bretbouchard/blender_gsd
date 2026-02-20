"""
Crowd Configuration Management

Provides utilities for loading, saving, and validating crowd configurations.

Phase 13.5: Crowd System (REQ-ANIM-07)
"""

from __future__ import annotations

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from ..types import (
    CrowdConfig,
    CrowdType,
    AgentConfig,
    BehaviorConfig,
    SpawnConfig,
    AvoidanceConfig,
    VariationConfig,
    DistributionType,
    MAX_PARTICLE_COUNT,
    WARN_PARTICLE_COUNT,
)


# Default config root (relative to this file)
CROWD_CONFIG_ROOT = Path(__file__).parent.parent.parent.parent / "configs" / "animation" / "crowd"


class CrowdConfigManager:
    """Manager for crowd configurations."""

    def __init__(self, config_root: Optional[Path] = None):
        """Initialize the config manager.

        Args:
            config_root: Optional custom config root directory
        """
        self._config_root = config_root or CROWD_CONFIG_ROOT
        self._cache: Dict[str, CrowdConfig] = {}

    @property
    def config_root(self) -> Path:
        """Get the configuration root directory."""
        return self._config_root

    def load(self, config_id: str, use_cache: bool = True) -> CrowdConfig:
        """Load a crowd configuration from YAML.

        Args:
            config_id: The configuration ID (filename without extension)
            use_cache: Whether to use cached config

        Returns:
            The loaded CrowdConfig

        Raises:
            FileNotFoundError: If config not found
        """
        if use_cache and config_id in self._cache:
            return self._cache[config_id]

        path = self._config_root / f"{config_id}.yaml"

        if not path.exists():
            # Try JSON as fallback
            json_path = self._config_root / f"{config_id}.json"
            if json_path.exists():
                return self._load_json(json_path, config_id, use_cache)

            raise FileNotFoundError(f"Crowd config not found: {config_id}")

        with open(path) as f:
            data = yaml.safe_load(f)

        config = self._parse_config(data)

        if use_cache:
            self._cache[config_id] = config

        return config

    def _load_json(self, path: Path, config_id: str, use_cache: bool) -> CrowdConfig:
        """Load from JSON file."""
        with open(path) as f:
            data = json.load(f)

        config = self._parse_config(data)

        if use_cache:
            self._cache[config_id] = config

        return config

    def _parse_config(self, data: dict) -> CrowdConfig:
        """Parse YAML/JSON data into CrowdConfig.

        Args:
            data: Raw configuration data

        Returns:
            Parsed CrowdConfig
        """
        # Parse agent config
        agent = None
        if 'agent' in data:
            agent = AgentConfig(
                mesh_path=data['agent'].get('mesh', ''),
                rig_type=data['agent'].get('rig', 'human_biped'),
                animations=data['agent'].get('animations', []),
                collection_name=data['agent'].get('collection'),
                lod_levels=data['agent'].get('lod_levels', []),
            )

        # Parse behavior config
        behavior_data = data.get('behavior', {})
        behavior = BehaviorConfig(
            walk_speed=tuple(behavior_data.get('walk_speed', [1.0, 1.5])),
            run_speed=tuple(behavior_data.get('run_speed', [3.0, 5.0])),
            idle_chance=behavior_data.get('idle_chance', 0.1),
            flee_distance=behavior_data.get('flee_distance', 10.0),
            group_chance=behavior_data.get('group_chance', 0.3),
            group_size=tuple(behavior_data.get('group_size', [2, 4])),
            talk_chance=behavior_data.get('talk_chance', 0.2),
            reaction_time=behavior_data.get('reaction_time', 0.5),
        )

        # Parse spawn config
        spawn_data = data.get('spawn', {})
        area_data = spawn_data.get('area', [[-10, -10], [10, 10]])
        spawn = SpawnConfig(
            count=spawn_data.get('count', 50),
            area=(tuple(area_data[0]), tuple(area_data[1])),
            height=spawn_data.get('height', 0.0),
            distribution=DistributionType(spawn_data.get('distribution', 'random')),
            spawn_points=[tuple(p) for p in spawn_data.get('spawn_points', [])],
            path_curve=spawn_data.get('path_curve'),
            surface_mesh=spawn_data.get('surface_mesh'),
            seed=spawn_data.get('seed'),
        )

        # Parse avoidance config
        avoidance_data = data.get('avoidance', {})
        avoidance = AvoidanceConfig(
            radius=avoidance_data.get('radius', 0.5),
            avoid_agents=avoidance_data.get('other_agents', True),
            avoid_obstacles=avoidance_data.get('obstacles', True),
            avoidance_strength=avoidance_data.get('strength', 1.0),
            obstacle_collection=avoidance_data.get('obstacle_collection'),
            max_avoidance_force=avoidance_data.get('max_force', 10.0),
        )

        # Parse variation config
        variation_data = data.get('variation', {})
        variation = VariationConfig(
            scale_range=tuple(variation_data.get('scale', [0.9, 1.1])),
            color_variations=variation_data.get('colors', {}),
            random_rotation=variation_data.get('random_rotation', True),
            random_anim_offset=variation_data.get('random_anim_offset', True),
            material_variants=variation_data.get('material_variants', []),
        )

        return CrowdConfig(
            id=data['id'],
            name=data['name'],
            crowd_type=CrowdType(data.get('type', 'pedestrian')),
            agent=agent,
            behavior=behavior,
            spawn=spawn,
            avoidance=avoidance,
            variation=variation,
            paths=data.get('paths', []),
            goals=data.get('goals', []),
            metadata=data.get('metadata', {}),
        )

    def save(
        self,
        config: CrowdConfig,
        path: Optional[Path] = None,
        format: str = 'yaml'
    ) -> Path:
        """Save crowd configuration to file.

        Args:
            config: The configuration to save
            path: Optional custom path (defaults to config_root/{id}.yaml)
            format: Output format ('yaml' or 'json')

        Returns:
            Path where config was saved
        """
        if path is None:
            save_path = self._config_root / f"{config.id}.{format}"
        else:
            save_path = Path(path)

        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = self._config_to_dict(config)

        if format == 'yaml':
            with open(save_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=2)

        # Update cache
        self._cache[config.id] = config

        return save_path

    def _config_to_dict(self, config: CrowdConfig) -> Dict[str, Any]:
        """Convert CrowdConfig to dictionary for serialization."""
        data = {
            'id': config.id,
            'name': config.name,
            'type': config.crowd_type.value,
        }

        if config.agent:
            data['agent'] = {
                'mesh': config.agent.mesh_path,
                'rig': config.agent.rig_type,
                'animations': config.agent.animations,
                'collection': config.agent.collection_name,
                'lod_levels': config.agent.lod_levels,
            }

        data['behavior'] = {
            'walk_speed': list(config.behavior.walk_speed),
            'run_speed': list(config.behavior.run_speed),
            'idle_chance': config.behavior.idle_chance,
            'flee_distance': config.behavior.flee_distance,
            'group_chance': config.behavior.group_chance,
            'group_size': list(config.behavior.group_size),
            'talk_chance': config.behavior.talk_chance,
            'reaction_time': config.behavior.reaction_time,
        }

        data['spawn'] = {
            'count': config.spawn.count,
            'area': [list(config.spawn.area[0]), list(config.spawn.area[1])],
            'height': config.spawn.height,
            'distribution': config.spawn.distribution.value,
            'spawn_points': [list(p) for p in config.spawn.spawn_points],
            'path_curve': config.spawn.path_curve,
            'surface_mesh': config.spawn.surface_mesh,
            'seed': config.spawn.seed,
        }

        data['avoidance'] = {
            'radius': config.avoidance.radius,
            'other_agents': config.avoidance.avoid_agents,
            'obstacles': config.avoidance.avoid_obstacles,
            'strength': config.avoidance.avoidance_strength,
            'obstacle_collection': config.avoidance.obstacle_collection,
            'max_force': config.avoidance.max_avoidance_force,
        }

        data['variation'] = {
            'scale': list(config.variation.scale_range),
            'colors': config.variation.color_variations,
            'random_rotation': config.variation.random_rotation,
            'random_anim_offset': config.variation.random_anim_offset,
            'material_variants': config.variation.material_variants,
        }

        if config.paths:
            data['paths'] = config.paths

        if config.goals:
            data['goals'] = config.goals

        if config.metadata:
            data['metadata'] = config.metadata

        return data

    def list_configs(self) -> List[str]:
        """List available crowd configurations.

        Returns:
            List of configuration IDs (filenames without extension)
        """
        if not self._config_root.exists():
            return []

        configs = set()

        for f in self._config_root.glob("*.yaml"):
            configs.add(f.stem)

        for f in self._config_root.glob("*.json"):
            configs.add(f.stem)

        return sorted(list(configs))

    def validate(self, config: CrowdConfig) -> List[str]:
        """Validate a crowd configuration.

        Args:
            config: Configuration to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required fields
        if not config.id:
            errors.append("Configuration ID is required")

        if not config.name:
            errors.append("Configuration name is required")

        # Validate spawn count
        if config.spawn.count <= 0:
            errors.append(f"Spawn count must be positive, got {config.spawn.count}")

        if config.spawn.count > MAX_PARTICLE_COUNT:
            errors.append(
                f"Spawn count {config.spawn.count} exceeds maximum {MAX_PARTICLE_COUNT}"
            )

        # Validate spawn area
        area = config.spawn.area
        if len(area) != 2 or len(area[0]) != 2 or len(area[1]) != 2:
            errors.append("Spawn area must be ((x1, y1), (x2, y2))")

        # Check for valid area (non-zero dimensions)
        if area[0][0] == area[1][0] or area[0][1] == area[1][1]:
            errors.append("Spawn area must have non-zero dimensions")

        # Validate behavior ranges
        if config.behavior.walk_speed[0] > config.behavior.walk_speed[1]:
            errors.append("Walk speed min must be <= max")

        if config.behavior.run_speed[0] > config.behavior.run_speed[1]:
            errors.append("Run speed min must be <= max")

        # Validate probabilities
        if not 0 <= config.behavior.idle_chance <= 1:
            errors.append("idle_chance must be between 0 and 1")

        if not 0 <= config.behavior.group_chance <= 1:
            errors.append("group_chance must be between 0 and 1")

        if not 0 <= config.behavior.talk_chance <= 1:
            errors.append("talk_chance must be between 0 and 1")

        # Validate variation scale
        if config.variation.scale_range[0] <= 0 or config.variation.scale_range[1] <= 0:
            errors.append("Scale values must be positive")

        if config.variation.scale_range[0] > config.variation.scale_range[1]:
            errors.append("Scale range min must be <= max")

        # Validate avoidance
        if config.avoidance.radius <= 0:
            errors.append("Avoidance radius must be positive")

        return errors

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()

    def config_exists(self, config_id: str) -> bool:
        """Check if a configuration exists.

        Args:
            config_id: The configuration ID

        Returns:
            True if config file exists
        """
        yaml_path = self._config_root / f"{config_id}.yaml"
        json_path = self._config_root / f"{config_id}.json"
        return yaml_path.exists() or json_path.exists()


# Module-level convenience functions

_manager: Optional[CrowdConfigManager] = None


def _get_manager() -> CrowdConfigManager:
    """Get or create the global config manager."""
    global _manager
    if _manager is None:
        _manager = CrowdConfigManager()
    return _manager


def load_crowd_config(config_id: str) -> CrowdConfig:
    """Load a crowd configuration by ID.

    Args:
        config_id: The configuration ID

    Returns:
        The loaded CrowdConfig
    """
    return _get_manager().load(config_id)


def save_crowd_config(config: CrowdConfig, path: Optional[Path] = None) -> Path:
    """Save a crowd configuration.

    Args:
        config: The configuration to save
        path: Optional custom path

    Returns:
        Path where config was saved
    """
    return _get_manager().save(config, path)


def list_crowd_configs() -> List[str]:
    """List available crowd configurations."""
    return _get_manager().list_configs()


def validate_crowd_config(config: CrowdConfig) -> List[str]:
    """Validate a crowd configuration.

    Args:
        config: Configuration to validate

    Returns:
        List of error messages (empty if valid)
    """
    return _get_manager().validate(config)


def create_default_crowd_config(
    id: str = "default",
    name: str = "Default Crowd",
    crowd_type: CrowdType = CrowdType.PEDESTRIAN,
    count: int = 50
) -> CrowdConfig:
    """Create a default crowd configuration.

    Args:
        id: Configuration ID
        name: Display name
        crowd_type: Type of crowd
        count: Number of agents

    Returns:
        A new CrowdConfig with sensible defaults
    """
    return CrowdConfig(
        id=id,
        name=name,
        crowd_type=crowd_type,
        agent=AgentConfig(
            mesh_path="",
            rig_type="human_biped",
            animations=["walk", "idle"],
        ),
        behavior=BehaviorConfig(),
        spawn=SpawnConfig(count=count),
        avoidance=AvoidanceConfig(),
        variation=VariationConfig(),
    )
