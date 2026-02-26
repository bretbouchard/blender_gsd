"""
Tentacle preset loading utilities.

Provides functions to load tentacle configurations from YAML presets.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from .types import TentacleConfig, TaperProfile, ZombieMouthConfig


# Default preset directory (relative to this file)
PRESET_DIR = Path(__file__).parent.parent.parent / "configs" / "tentacle"


# Convenience functions (module-level shortcuts)
def load_tentacle(name: str) -> TentacleConfig:
    """Load a tentacle preset by name.

    Args:
        name: Preset name (e.g., "default", "zombie_main")

    Returns:
        TentacleConfig instance with preset values

    Raises:
        ValueError: If preset not found

    Example:
        >>> config = load_tentacle("zombie_main")
        >>> print(config.length)
        1.2
    """
    return TentaclePresetLoader.load_tentacle(name)


def load_zombie_mouth(name: str) -> ZombieMouthConfig:
    """Load a zombie mouth configuration by name.

    Args:
        name: Preset name (e.g., "standard", "aggressive")

    Returns:
        ZombieMouthConfig instance with preset values

    Raises:
        ValueError: If preset not found

    Example:
        >>> config = load_zombie_mouth("standard")
        >>> print(config.tentacle_count)
        4
    """
    return TentaclePresetLoader.load_zombie_mouth(name)


def list_tentacle_presets() -> List[str]:
    """List available tentacle presets.

    Returns:
        List of preset names

    Example:
        >>> presets = list_tentacle_presets()
        >>> print(presets)
        ['default', 'short_thick', 'long_thin', 'feeler', 'zombie_main', 'zombie_feeler']
    """
    return TentaclePresetLoader.list_tentacle_presets()


def list_zombie_mouth_presets() -> List[str]:
    """List available zombie mouth presets.

    Returns:
        List of preset names

    Example:
        >>> presets = list_zombie_mouth_presets()
        >>> print(presets)
        ['standard', 'aggressive', 'subtle']
    """
    return TentaclePresetLoader.list_zombie_mouth_presets()


class TentaclePresetLoader:
    """Load tentacle configurations from YAML presets.

    This class provides a caching loader for tentacle presets stored in YAML files.
    It supports loading individual tentacle configurations, taper profiles,
    and complete zombie mouth configurations.

    The loader uses class-level caching to avoid repeated file I/O.

    Example:
        >>> # Load a tentacle preset
        >>> config = TentaclePresetLoader.load_tentacle("zombie_main")
        >>> print(config.length)
        1.2

        >>> # List available presets
        >>> presets = TentaclePresetLoader.list_tentacle_presets()
        >>> print(presets)
        ['default', 'short_thick', 'long_thin', 'feeler', 'zombie_main', 'zombie_feeler']

        >>> # Load a zombie mouth configuration
        >>> mouth_config = TentaclePresetLoader.load_zombie_mouth("standard")
        >>> print(mouth_config.tentacle_count)
        4
    """

    _cache: Dict[str, Any] = {}
    _presets_path: Optional[Path] = None

    @classmethod
    def set_presets_path(cls, path: Optional[Path]) -> None:
        """Set custom presets directory.

        Clears the cache when a new path is set.

        Args:
            path: Path to directory containing presets.yaml, or None to reset to default
        """
        if path is None:
            cls._presets_path = None
        else:
            cls._presets_path = Path(path)
        cls._cache.clear()

    @classmethod
    def get_presets_path(cls) -> Path:
        """Get the current presets directory path.

        Returns:
            Path to presets directory
        """
        return cls._presets_path or PRESET_DIR

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the preset cache.

        Useful if the YAML file has been modified and needs to be reloaded.
        """
        cls._cache.clear()

    @classmethod
    def _load_presets(cls) -> Dict[str, Any]:
        """Load presets from YAML file with caching.

        Returns:
            Dictionary containing presets data, or empty structure if file not found

        Raises:
            ValueError: If path traversal detected (security)
        """
        if "presets" in cls._cache:
            return cls._cache["presets"]

        presets_file = cls.get_presets_path() / "presets.yaml"

        # Security: Validate path is within expected directory (no traversal)
        try:
            presets_file.resolve().relative_to(cls.get_presets_path().resolve())
        except ValueError:
            raise ValueError(
                f"Invalid preset path - directory traversal detected: {presets_file}"
            )

        if not presets_file.exists():
            # Return empty structure if file doesn't exist
            cls._cache["presets"] = {
                "presets": {},
                "taper_profiles": {},
                "zombie_mouths": {},
            }
            return cls._cache["presets"]

        with open(presets_file, "r") as f:
            data = yaml.safe_load(f) or {}

        # Ensure all expected keys exist
        data.setdefault("presets", {})
        data.setdefault("taper_profiles", {})
        data.setdefault("zombie_mouths", {})

        cls._cache["presets"] = data
        return cls._cache["presets"]

    @classmethod
    def load_tentacle(cls, name: str) -> TentacleConfig:
        """Load a tentacle preset by name.

        Args:
            name: Preset name (e.g., "default", "zombie_main")

        Returns:
            TentacleConfig instance with preset values

        Raises:
            ValueError: If preset not found
        """
        presets = cls._load_presets()

        if name not in presets.get("presets", {}):
            available = list(presets.get("presets", {}).keys())
            raise ValueError(
                f"Tentacle preset '{name}' not found. "
                f"Available presets: {available}"
            )

        preset_data = presets["presets"][name].copy()

        # Convert snake_case keys to match TentacleConfig fields
        # (YAML may use different conventions)
        return TentacleConfig(**preset_data)

    @classmethod
    def load_taper_profile(cls, name: str) -> TaperProfile:
        """Load a taper profile preset by name.

        Args:
            name: Profile name (e.g., "linear", "smooth", "organic")

        Returns:
            TaperProfile instance with preset values.
            If profile not found, returns a TaperProfile with the given profile_type.
        """
        presets = cls._load_presets()

        if name not in presets.get("taper_profiles", {}):
            # Default to creating a profile with the given type
            return TaperProfile(profile_type=name)

        profile_data = presets["taper_profiles"][name].copy()

        # Handle points conversion from list of lists to list of tuples
        if "points" in profile_data and profile_data["points"]:
            profile_data["points"] = [
                tuple(p) if isinstance(p, list) else p
                for p in profile_data["points"]
            ]

        return TaperProfile(**profile_data)

    @classmethod
    def load_zombie_mouth(cls, name: str) -> ZombieMouthConfig:
        """Load a zombie mouth configuration by name.

        Resolves nested tentacle preset references to TentacleConfig instances.

        Args:
            name: Configuration name (e.g., "standard", "aggressive")

        Returns:
            ZombieMouthConfig instance with resolved tentacle configurations

        Raises:
            ValueError: If configuration not found
        """
        presets = cls._load_presets()

        if name not in presets.get("zombie_mouths", {}):
            available = list(presets.get("zombie_mouths", {}).keys())
            raise ValueError(
                f"Zombie mouth preset '{name}' not found. "
                f"Available presets: {available}"
            )

        config_dict = presets["zombie_mouths"][name].copy()

        # Resolve nested tentacle presets
        if "main_tentacle" in config_dict:
            if isinstance(config_dict["main_tentacle"], str):
                # It's a preset name, load it
                config_dict["main_tentacle"] = cls.load_tentacle(
                    config_dict["main_tentacle"]
                )
            elif isinstance(config_dict["main_tentacle"], dict):
                # It's inline configuration, create TentacleConfig directly
                config_dict["main_tentacle"] = TentacleConfig(
                    **config_dict["main_tentacle"]
                )

        if "feeler_tentacle" in config_dict:
            if isinstance(config_dict["feeler_tentacle"], str):
                # It's a preset name, load it
                config_dict["feeler_tentacle"] = cls.load_tentacle(
                    config_dict["feeler_tentacle"]
                )
            elif isinstance(config_dict["feeler_tentacle"], dict):
                # It's inline configuration, create TentacleConfig directly
                config_dict["feeler_tentacle"] = TentacleConfig(
                    **config_dict["feeler_tentacle"]
                )

        return ZombieMouthConfig(**config_dict)

    @classmethod
    def list_tentacle_presets(cls) -> List[str]:
        """List available tentacle presets.

        Returns:
            List of preset names sorted alphabetically
        """
        presets = cls._load_presets()
        return sorted(presets.get("presets", {}).keys())

    @classmethod
    def list_taper_profiles(cls) -> List[str]:
        """List available taper profiles.

        Returns:
            List of profile names sorted alphabetically
        """
        presets = cls._load_presets()
        return sorted(presets.get("taper_profiles", {}).keys())

    @classmethod
    def list_zombie_mouth_presets(cls) -> List[str]:
        """List available zombie mouth presets.

        Returns:
            List of preset names sorted alphabetically
        """
        presets = cls._load_presets()
        return sorted(presets.get("zombie_mouths", {}).keys())

    @classmethod
    def preset_exists(cls, name: str) -> bool:
        """Check if a tentacle preset exists.

        Args:
            name: Preset name to check

        Returns:
            True if preset exists, False otherwise
        """
        presets = cls._load_presets()
        return name in presets.get("presets", {})

    @classmethod
    def zombie_mouth_exists(cls, name: str) -> bool:
        """Check if a zombie mouth preset exists.

        Args:
            name: Preset name to check

        Returns:
            True if preset exists, False otherwise
        """
        presets = cls._load_presets()
        return name in presets.get("zombie_mouths", {})
