"""
Crowd System for Blender GSD

Provides plugin integration for crowd simulation.

Phase 13.5: Crowd System (REQ-ANIM-07)

Usage:
    from lib.animation.crowd import (
        BoidsWrapper, create_flock,
        CrowdPluginInterface, get_plugin, get_available_plugins,
        CrowdConfigManager, load_crowd_config
    )

    # Create a flock using boids
    flock = create_flock("birds", bird_object, count=100)

    # Load crowd config
    config = load_crowd_config("pedestrian_city")

    # Create crowd from config
    plugin = get_plugin('boids')
    crowd = plugin.create_crowd(config)
"""

from .boids_wrapper import (
    BoidsWrapper,
    create_flock,
    create_swarm,
    create_herd,
)

from .plugin_interface import (
    CrowdPluginInterface,
    BoidsPlugin,
    BlenderCrowdPlugin,
    get_plugin,
    get_available_plugins,
    is_plugin_available,
)

from .crowd_config import (
    CrowdConfigManager,
    load_crowd_config,
    save_crowd_config,
    list_crowd_configs,
    validate_crowd_config,
)


__all__ = [
    # Boids Wrapper
    'BoidsWrapper',
    'create_flock',
    'create_swarm',
    'create_herd',

    # Plugin Interface
    'CrowdPluginInterface',
    'BoidsPlugin',
    'BlenderCrowdPlugin',
    'get_plugin',
    'get_available_plugins',
    'is_plugin_available',

    # Crowd Config
    'CrowdConfigManager',
    'load_crowd_config',
    'save_crowd_config',
    'list_crowd_configs',
    'validate_crowd_config',
]
