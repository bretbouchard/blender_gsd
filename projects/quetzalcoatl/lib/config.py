"""
Quetzalcoatl Configuration Loader

Load and manage creature configurations from YAML files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Type, TypeVar, get_type_hints
from dataclasses import fields, is_dataclass

from .types import (
    QuetzalcoatlConfig,
    SpineConfig,
    BodyConfig,
    LimbConfig,
    WingConfig,
    ScaleConfig,
    FeatherConfig,
    HeadConfig,
    TeethConfig,
    WhiskerConfig,
    TailConfig,
    ColorConfig,
    AnimationConfig,
    WingType,
    ScaleShape,
    TailType,
    CrestType,
    ColorPattern,
)


T = TypeVar("T")


# Mapping of string values to enum types
ENUM_MAP = {
    "wing_type": WingType,
    "shape": ScaleShape,
    "tail_type": TailType,
    "crest_type": CrestType,
    "color_pattern": ColorPattern,
}


class ConfigLoader:
    """Load and manage creature configurations."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config loader.

        Args:
            config_dir: Directory containing config files.
                       Defaults to projects/quetzalcoatl/configs/
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "configs"
        self.config_dir = Path(config_dir)
        self._preset_cache: Dict[str, QuetzalcoatlConfig] = {}

    def load_yaml(self, path: Path) -> QuetzalcoatlConfig:
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            QuetzalcoatlConfig instance
        """
        with open(path) as f:
            data = yaml.safe_load(f) or {}

        # Handle extends keyword for inheritance
        if "extends" in data:
            base_name = data.pop("extends")
            base_config = self._load_base_config(base_name, path.parent)
            # Merge data with base
            data = self._merge_configs(base_config.to_dict(), data)

        return self._dict_to_config(data)

    def _load_base_config(
        self, base_name: str, current_dir: Path
    ) -> QuetzalcoatlConfig:
        """Load a base configuration for inheritance."""
        # Try presets directory first
        preset_path = self.config_dir / "presets" / f"{base_name}.yaml"
        if preset_path.exists():
            return self.load_yaml(preset_path)

        # Try as direct path
        direct_path = current_dir / f"{base_name}.yaml"
        if direct_path.exists():
            return self.load_yaml(direct_path)

        # Try base_creature.yaml
        if base_name == "base_creature" or base_name == "base":
            base_path = self.config_dir / "base_creature.yaml"
            if base_path.exists():
                return self.load_yaml(base_path)

        raise FileNotFoundError(f"Base config not found: {base_name}")

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively merge override into base configuration."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def load_preset(self, name: str) -> QuetzalcoatlConfig:
        """
        Load a named preset configuration.

        Args:
            name: Preset name (without .yaml extension)

        Returns:
            QuetzalcoatlConfig instance

        Raises:
            FileNotFoundError: If preset doesn't exist
        """
        if name in self._preset_cache:
            return self._preset_cache[name]

        preset_path = self.config_dir / "presets" / f"{name}.yaml"
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset not found: {name}")

        config = self.load_yaml(preset_path)
        self._preset_cache[name] = config
        return config

    def list_presets(self) -> Dict[str, str]:
        """
        List available presets with descriptions.

        Returns:
            Dict mapping preset name to description
        """
        presets_dir = self.config_dir / "presets"
        if not presets_dir.exists():
            return {}

        presets = {}
        for path in sorted(presets_dir.glob("*.yaml")):
            try:
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
                presets[path.stem] = data.get("description", "")
            except Exception:
                presets[path.stem] = "(error loading)"

        return presets

    def save_yaml(self, config: QuetzalcoatlConfig, path: Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            config: Configuration to save
            path: Output file path
        """
        data = config.to_dict()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _dict_to_config(self, data: Dict[str, Any]) -> QuetzalcoatlConfig:
        """Convert dictionary to QuetzalcoatlConfig dataclass."""
        # Extract top-level fields
        name = data.get("name", "Quetzalcoatl")
        description = data.get("description", "")
        seed = data.get("seed", 42)

        # Build nested configs
        spine = self._build_section(data.get("spine", {}), SpineConfig)
        body = self._build_section(data.get("body", {}), BodyConfig)
        limbs = self._build_section(data.get("limbs", {}), LimbConfig)
        wings = self._build_section(data.get("wings", {}), WingConfig)
        scales = self._build_section(data.get("scales", {}), ScaleConfig)
        feathers = self._build_section(data.get("feathers", {}), FeatherConfig)
        head = self._build_section(data.get("head", {}), HeadConfig)
        teeth = self._build_section(data.get("teeth", {}), TeethConfig)
        whiskers = self._build_section(data.get("whiskers", {}), WhiskerConfig)
        tail = self._build_section(data.get("tail", {}), TailConfig)
        colors = self._build_section(data.get("colors", {}), ColorConfig)
        animation = self._build_section(data.get("animation", {}), AnimationConfig)

        return QuetzalcoatlConfig(
            name=name,
            description=description,
            seed=seed,
            spine=spine,
            body=body,
            limbs=limbs,
            wings=wings,
            scales=scales,
            feathers=feathers,
            head=head,
            teeth=teeth,
            whiskers=whiskers,
            tail=tail,
            colors=colors,
            animation=animation,
        )

    def _build_section(
        self, data: Dict[str, Any], config_class: Type[T]
    ) -> T:
        """Build a config section from dictionary data."""
        kwargs = {}

        for field_info in fields(config_class):
            field_name = field_info.name
            if field_name in data:
                value = data[field_name]

                # Handle enum conversion
                if field_name in ENUM_MAP:
                    enum_class = ENUM_MAP[field_name]
                    if isinstance(value, str):
                        value = enum_class(value)

                # Handle tuple conversion (for colors)
                if (
                    field_name.endswith("_color")
                    or field_name == "base_color"
                    or field_name == "accent_color"
                ):
                    if isinstance(value, list) and len(value) >= 3:
                        value = tuple(value[:3])

                # Handle list of tuples (iridescent_colors)
                if field_name == "iridescent_colors" and isinstance(value, list):
                    value = [
                        tuple(c) if isinstance(c, list) else c
                        for c in value
                    ]

                kwargs[field_name] = value

        return config_class(**kwargs)


def load_config(path: Optional[Path] = None, preset: Optional[str] = None) -> QuetzalcoatlConfig:
    """
    Convenience function to load configuration.

    Args:
        path: Path to YAML file
        preset: Preset name

    Returns:
        QuetzalcoatlConfig instance
    """
    loader = ConfigLoader()

    if preset is not None:
        return loader.load_preset(preset)

    if path is not None:
        return loader.load_yaml(path)

    # Return default config
    return QuetzalcoatlConfig()
