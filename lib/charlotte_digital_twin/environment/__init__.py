"""
Charlotte Digital Twin Environment System

Natural environment components:
- Tree placement and generation
- Grass ground cover
- Terrain elevation

Usage:
    from lib.charlotte_digital_twin.environment import (
        TreeGenerator,
        GrassSystem,
        TerrainSystem,
    )

    # Place trees along highway
    trees = TreeGenerator()
    trees.place_along_road(road_points, offset=15.0)

    # Add grass
    grass = GrassSystem()
    grass.create_grass_plane(size=(100, 100))

    # Create terrain
    terrain = TerrainSystem()
    terrain.create_terrain(config)
"""

from .tree_placement import (
    TreeSpecies,
    TreeConfig,
    TREE_CONFIGS,
    TreeGenerator,
    place_trees_along_road,
    create_tree_cluster,
)

from .grass_system import (
    GrassType,
    GrassConfig,
    GRASS_CONFIGS,
    GrassSystem,
    create_highway_grass_strip,
    create_grass_field,
)

from .terrain_elevation import (
    TerrainSourceType,
    TerrainConfig,
    TerrainSystem,
    create_charlotte_terrain,
    apply_elevation_to_road,
)

__version__ = "1.0.0"
__all__ = [
    # Trees
    "TreeSpecies",
    "TreeConfig",
    "TREE_CONFIGS",
    "TreeGenerator",
    "place_trees_along_road",
    "create_tree_cluster",
    # Grass
    "GrassType",
    "GrassConfig",
    "GRASS_CONFIGS",
    "GrassSystem",
    "create_highway_grass_strip",
    "create_grass_field",
    # Terrain
    "TerrainSourceType",
    "TerrainConfig",
    "TerrainSystem",
    "create_charlotte_terrain",
    "apply_elevation_to_road",
]
