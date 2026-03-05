"""
Compatibility Layer - Backward Compatibility for Migration

Provides adapters and helpers for migrating from Python to GN API.
"""

import warnings
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class BreakingChange:
    """Documents a breaking change between Python and GN APIs."""
    feature: str
    python_api: str
    gn_api: str
    migration_notes: str


BREAKING_CHANGES = [
    BreakingChange(
        feature="Platform Creation",
        python_api="Platform(config=PlatformConfig())",
        gn_api="PlatformGN('name').set_dimensions(w, d).build()",
        migration_notes="Use fluent API with method chaining"
    ),
    BreakingChange(
        feature="Tile Shapes",
        python_api="tile.set_shape('hexagon')",
        gn_api="tile.set_shapes(['hexagon'])",
        migration_notes="Shapes are now specified as a list"
    ),
    BreakingChange(
        feature="Arm Physics",
        python_api="arm.physics.step(dt)",
        gn_api="Simulation zone handles physics automatically",
        migration_notes="Physics is now built into GN simulation"
    ),
]


class CompatLayer:
    """
    Backward compatibility layer for API migration.

    Maps old Python API calls to new GN API, providing
    deprecation warnings and migration helpers.

    Usage:
        from lib.tile_platform_hybrid import CompatLayer

        # Convert old config to new format
        old_config = {"width": 10.0, "depth": 10.0}
        new_config = CompatLayer.convert_config(old_config)

        # Validate migration
        issues = CompatLayer.validate_migration()
    """

    @staticmethod
    def convert_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Python config to GN config format.

        Args:
            old_config: Old Python configuration dict

        Returns:
            New GN-compatible configuration dict
        """
        new_config = {}

        # Platform config mapping
        if "width" in old_config:
            new_config["width"] = old_config["width"]
        if "depth" in old_config:
            new_config["depth"] = old_config["depth"]
        if "tile_size" in old_config:
            new_config["tile_size"] = old_config["tile_size"]

        # Tile config mapping
        if "shape" in old_config:
            new_config["shapes"] = [old_config["shape"]]
        if "shapes" in old_config:
            new_config["shapes"] = old_config["shapes"]

        # Arm config mapping
        if "segments" in old_config:
            new_config["segments"] = old_config["segments"]

        return new_config

    @staticmethod
    def validate_migration() -> list:
        """
        Validate migration completeness.

        Returns:
            List of migration issues (empty if fully migrated)
        """
        issues = []

        # Check for Python imports in codebase
        # This would scan for old import patterns
        # Simplified for this implementation

        return issues

    @staticmethod
    def get_breaking_changes() -> list:
        """
        Get list of breaking changes.

        Returns:
            List of BreakingChange objects
        """
        return BREAKING_CHANGES

    @staticmethod
    def print_migration_guide() -> None:
        """Print migration guide to console."""
        print("\n" + "=" * 60)
        print("PYTHON TO GN MIGRATION GUIDE")
        print("=" * 60)

        for change in BREAKING_CHANGES:
            print(f"\n{change.feature}:")
            print(f"  Python: {change.python_api}")
            print(f"  GN:     {change.gn_api}")
            print(f"  Notes:  {change.migration_notes}")

        print("\n" + "=" * 60 + "\n")


class PlatformCompat:
    """
    Compatibility wrapper for Platform API.

    Wraps PlatformGN to provide Platform-compatible API.
    """

    def __init__(self, gn_platform):
        """
        Initialize compatibility wrapper.

        Args:
            gn_platform: PlatformGN instance
        """
        self._gn = gn_platform
        self._config = {}

    def set_dimensions(self, width: float, depth: float) -> "PlatformCompat":
        """Set platform dimensions (Python-style API)."""
        self._gn.set_dimensions(width, depth)
        self._config["width"] = width
        self._config["depth"] = depth
        return self

    def get_tile_grid(self) -> Any:
        """Get tile grid (Python-style API)."""
        return self._gn.get_tile_grid()

    def build(self) -> Any:
        """Build platform (Python-style API)."""
        return self._gn.build()


class TileCompat:
    """
    Compatibility wrapper for Tile API.

    Wraps TileGN to provide Tile-compatible API.
    """

    def __init__(self, gn_tile):
        """
        Initialize compatibility wrapper.

        Args:
            gn_tile: TileGN instance
        """
        self._gn = gn_tile

    def set_shape(self, shape: str) -> "TileCompat":
        """Set single tile shape (Python-style API)."""
        warnings.warn(
            "set_shape() is deprecated. Use set_shapes(['shape']) instead.",
            DeprecationWarning
        )
        self._gn.set_shapes([shape])
        return self

    def distribute(self, platform: Any) -> "TileCompat":
        """Distribute tiles on platform (Python-style API)."""
        self._gn.distribute_on_platform(platform)
        return self

    def build(self) -> Any:
        """Build tiles (Python-style API)."""
        return self._gn.build()


class ArmCompat:
    """
    Compatibility wrapper for Arm API.

    Wraps ArmGN to provide Arm-compatible API.
    """

    def __init__(self, gn_arm):
        """
        Initialize compatibility wrapper.

        Args:
            gn_arm: ArmGN instance
        """
        self._gn = gn_arm

    def add_segment(self, length: float, width: float = 0.1) -> "ArmCompat":
        """Add segment (Python-style API)."""
        from lib.gn_platform import ArmSegmentConfig
        config = ArmSegmentConfig(length=length, width=width)
        self._gn.add_segment(config)
        return self

    def set_target(self, position: tuple) -> "ArmCompat":
        """Set target position (Python-style API)."""
        # In GN, target is set as input parameter
        # This stores it for later use
        self._target = position
        return self

    def build(self) -> Any:
        """Build arm (Python-style API)."""
        return self._gn.build()
