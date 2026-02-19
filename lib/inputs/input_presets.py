"""
Input Presets System

Manages loading, saving, and querying input presets.

Preset files are YAML files stored in assets/presets/inputs/
Each preset defines a complete input configuration that can be
loaded and customized.

Preset File Format:
    name: Neve 1073 Knob
    input_type: rotary
    base_shape: cylinder
    total_height_mm: 20
    total_width_mm: 14
    zones:
      a:
        height_mm: 12
        width_top_mm: 14
        width_bottom_mm: 14
        top_cap:
          style: rounded
          height_mm: 2
        middle_knurl:
          enabled: false
        bottom_cap:
          style: flat
          height_mm: 0
      b:
        height_mm: 8
        width_top_mm: 14
        width_bottom_mm: 16
        top_cap:
          style: flat
          height_mm: 0
        middle_knurl:
          enabled: true
          count: 30
          depth_mm: 0.5
          profile: v
        bottom_cap:
          style: rounded
          height_mm: 2
    material:
      base_color: [0.2, 0.35, 0.75]
      metallic: 0.0
      roughness: 0.25
"""

from __future__ import annotations
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from lib.inputs.input_types import (
    InputConfig, ZoneConfig, CapConfig, KnurlConfig, RotationConfig,
    InputType, BaseShape, CapStyle, KnurlProfile, RotationMode
)


# Default preset directory
PRESET_DIR = Path(__file__).resolve().parents[2] / "assets" / "presets" / "inputs"


@dataclass
class InputPreset:
    """
    A named input preset with optional overrides.

    Presets are immutable configurations that can be loaded
    and customized via overrides.
    """
    id: str                           # Unique identifier (filename without .yaml)
    name: str                         # Display name
    description: str = ""             # Human-readable description
    config: InputConfig = field(default_factory=InputConfig)
    tags: List[str] = field(default_factory=list)

    def to_yaml(self) -> str:
        """Convert preset to YAML string."""
        data = {
            "name": self.name,
            "description": self.description,
            **self.config.to_dict(),
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str, preset_id: str) -> "InputPreset":
        """Create preset from YAML string."""
        data = yaml.safe_load(yaml_str) or {}
        return cls(
            id=preset_id,
            name=data.get("name", preset_id),
            description=data.get("description", ""),
            config=InputConfig.from_dict(data),
            tags=data.get("tags", []),
        )


class PresetManager:
    """
    Manages input preset loading and querying.

    Presets are loaded from YAML files in the preset directory.
    The manager caches loaded presets for performance.
    """

    def __init__(self, preset_dir: Optional[Path] = None):
        """
        Initialize preset manager.

        Args:
            preset_dir: Directory containing preset files (default: assets/presets/inputs/)
        """
        self.preset_dir = preset_dir or PRESET_DIR
        self._cache: Dict[str, InputPreset] = {}
        self._loaded = False

    def _ensure_loaded(self):
        """Load all presets if not already loaded."""
        if self._loaded:
            return

        if not self.preset_dir.exists():
            self.preset_dir.mkdir(parents=True, exist_ok=True)
            self._loaded = True
            return

        for yaml_file in self.preset_dir.glob("*.yaml"):
            try:
                preset_id = yaml_file.stem
                with open(yaml_file) as f:
                    preset = InputPreset.from_yaml(f.read(), preset_id)
                self._cache[preset_id] = preset
            except Exception as e:
                print(f"Warning: Failed to load preset {yaml_file}: {e}")

        self._loaded = True

    def get(self, preset_id: str) -> InputPreset:
        """
        Get a preset by ID.

        Args:
            preset_id: Preset identifier (filename without .yaml)

        Returns:
            InputPreset instance

        Raises:
            KeyError: If preset not found
        """
        self._ensure_loaded()

        if preset_id not in self._cache:
            available = ", ".join(self._cache.keys()) if self._cache else "none"
            raise KeyError(f"Preset '{preset_id}' not found. Available: {available}")

        return self._cache[preset_id]

    def list(
        self,
        input_type: Optional[str] = None,
        base_shape: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[str]:
        """
        List available preset IDs, optionally filtered.

        Args:
            input_type: Filter by input type (rotary, linear, momentary)
            base_shape: Filter by base shape (cylinder, cube, cone)
            tags: Filter by tags (preset must have ALL specified tags)

        Returns:
            List of matching preset IDs
        """
        self._ensure_loaded()

        results = []

        for preset_id, preset in self._cache.items():
            # Filter by input type
            if input_type and preset.config.input_type.value != input_type:
                continue

            # Filter by base shape
            if base_shape and preset.config.base_shape.value != base_shape:
                continue

            # Filter by tags
            if tags and not all(tag in preset.tags for tag in tags):
                continue

            results.append(preset_id)

        return sorted(results)

    def save(self, preset: InputPreset, overwrite: bool = False) -> Path:
        """
        Save a preset to a YAML file.

        Args:
            preset: Preset to save
            overwrite: Allow overwriting existing preset

        Returns:
            Path to saved file

        Raises:
            FileExistsError: If preset exists and overwrite=False
        """
        self._ensure_loaded()

        if not self.preset_dir.exists():
            self.preset_dir.mkdir(parents=True, exist_ok=True)

        filepath = self.preset_dir / f"{preset.id}.yaml"

        if filepath.exists() and not overwrite:
            raise FileExistsError(f"Preset '{preset.id}' already exists. Use overwrite=True to replace.")

        with open(filepath, "w") as f:
            f.write(preset.to_yaml())

        # Update cache
        self._cache[preset.id] = preset

        return filepath

    def create(
        self,
        preset_id: str,
        name: str,
        base_preset: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
        save: bool = True
    ) -> InputPreset:
        """
        Create a new preset, optionally based on an existing one.

        Args:
            preset_id: Unique identifier for the new preset
            name: Display name
            base_preset: ID of preset to base this on
            overrides: Parameter overrides
            save: Save to file immediately

        Returns:
            New InputPreset instance
        """
        self._ensure_loaded()

        if base_preset:
            base = self.get(base_preset)
            config_dict = base.config.to_dict()
        else:
            config_dict = InputConfig().to_dict()

        # Apply overrides
        if overrides:
            config_dict = self._deep_merge(config_dict, overrides)

        config_dict["name"] = name

        preset = InputPreset(
            id=preset_id,
            name=name,
            config=InputConfig.from_dict(config_dict),
        )

        if save:
            self.save(preset, overwrite=False)

        return preset

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result


# Singleton instance
_manager: Optional[PresetManager] = None


def get_manager() -> PresetManager:
    """Get the singleton PresetManager instance."""
    global _manager
    if _manager is None:
        _manager = PresetManager()
    return _manager


def get_preset(preset_id: str) -> InputPreset:
    """
    Get a preset by ID.

    Args:
        preset_id: Preset identifier

    Returns:
        InputPreset instance
    """
    return get_manager().get(preset_id)


def list_presets(
    input_type: Optional[str] = None,
    base_shape: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[str]:
    """
    List available preset IDs.

    Args:
        input_type: Filter by input type
        base_shape: Filter by base shape
        tags: Filter by tags

    Returns:
        List of preset IDs
    """
    return get_manager().list(input_type=input_type, base_shape=base_shape, tags=tags)


def create_preset(
    preset_id: str,
    name: str,
    base_preset: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
    save: bool = True
) -> InputPreset:
    """
    Create a new preset.

    Args:
        preset_id: Unique identifier
        name: Display name
        base_preset: ID of preset to base this on
        overrides: Parameter overrides
        save: Save to file

    Returns:
        New InputPreset instance
    """
    return get_manager().create(
        preset_id=preset_id,
        name=name,
        base_preset=base_preset,
        overrides=overrides,
        save=save
    )
