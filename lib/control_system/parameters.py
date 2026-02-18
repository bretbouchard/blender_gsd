"""
Control System Parameter Hierarchy

Implements a hierarchical parameter system for control surface generation:
- Global defaults
- Category presets
- Variant overrides
- Instance parameters

Based on the parameter architecture defined in .planning/research/PARAMETER_ARCHITECTURE.md
"""

from __future__ import annotations
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum


class ParameterGroup(Enum):
    """Parameter group identifiers for organization."""
    GEOMETRY = "geometry"
    MATERIAL = "material"
    COLOR_SYSTEM = "color_system"
    KNURLING = "knurling"
    LIGHTING = "lighting"
    EXPORT = "export"
    ANIMATION = "animation"
    PHYSICS = "physics"
    COMPOSITING = "compositing"


class ParameterHierarchy:
    """
    Manages hierarchical parameter resolution.

    Resolution order (later overrides earlier):
    1. Global defaults (presets/base.yaml)
    2. Category presets (presets/{category}.yaml)
    3. Variant overrides (task YAML)
    4. Instance parameters (task YAML)
    """

    def __init__(self, preset_root: Optional[Path] = None):
        """
        Initialize parameter hierarchy.

        Args:
            preset_root: Root directory for preset files (default: presets/)
        """
        self.preset_root = preset_root or Path("presets")
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        Load a preset file from the preset root.

        Args:
            preset_name: Name of preset (without .yaml extension)

        Returns:
            Dictionary of parameters

        Raises:
            FileNotFoundError: If preset file doesn't exist
        """
        if preset_name in self._cache:
            return self._cache[preset_name]

        preset_path = self.preset_root / f"{preset_name}.yaml"

        if not preset_path.exists():
            raise FileNotFoundError(f"Preset not found: {preset_path}")

        with open(preset_path) as f:
            params = yaml.safe_load(f) or {}

        self._cache[preset_name] = params
        return params

    def resolve(
        self,
        global_preset: str = "base",
        category_preset: Optional[str] = None,
        variant_params: Optional[Dict[str, Any]] = None,
        instance_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve parameters through the hierarchy.

        Args:
            global_preset: Global defaults preset name
            category_preset: Category-specific preset name
            variant_params: Variant-level overrides
            instance_params: Instance-level parameters

        Returns:
            Fully resolved parameter dictionary
        """
        resolved = {}

        # Level 1: Global defaults
        try:
            global_params = self.load_preset(global_preset)
            resolved = self._deep_merge(resolved, global_params)
        except FileNotFoundError:
            pass  # Global preset is optional

        # Level 2: Category preset
        if category_preset:
            try:
                category_params = self.load_preset(category_preset)
                resolved = self._deep_merge(resolved, category_params)
            except FileNotFoundError:
                pass  # Category preset is optional

        # Level 3: Variant overrides
        if variant_params:
            resolved = self._deep_merge(resolved, variant_params)

        # Level 4: Instance parameters
        if instance_params:
            resolved = self._deep_merge(resolved, instance_params)

        return resolved

    def _deep_merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries, with override taking precedence.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get_group(
        self,
        params: Dict[str, Any],
        group: ParameterGroup
    ) -> Dict[str, Any]:
        """
        Extract parameters for a specific group.

        Args:
            params: Full parameter dictionary
            group: Parameter group to extract

        Returns:
            Group-specific parameters
        """
        group_name = group.value
        return params.get(group_name, {})

    def validate_required(
        self,
        params: Dict[str, Any],
        required_keys: List[str]
    ) -> List[str]:
        """
        Validate that required parameters are present.

        Args:
            params: Parameter dictionary to validate
            required_keys: List of required key paths (e.g., "geometry.base_diameter")

        Returns:
            List of missing keys (empty if all present)
        """
        missing = []

        for key_path in required_keys:
            keys = key_path.split(".")
            current = params

            for key in keys:
                if key not in current:
                    missing.append(key_path)
                    break
                current = current[key]

        return missing


def resolve_task_parameters(
    task: Dict[str, Any],
    preset_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Convenience function to resolve parameters from a task definition.

    Args:
        task: Task dictionary with optional 'preset' and 'parameters' keys
        preset_root: Root directory for preset files

    Returns:
        Resolved parameter dictionary
    """
    hierarchy = ParameterHierarchy(preset_root)

    # Extract task-level preset configuration
    task_preset = task.get("preset", {})
    global_preset = task_preset.get("global", "base")
    category_preset = task_preset.get("category")

    # Extract task parameters
    task_params = task.get("parameters", {})

    return hierarchy.resolve(
        global_preset=global_preset,
        category_preset=category_preset,
        instance_params=task_params
    )


# Example usage and testing
if __name__ == "__main__":
    # Test parameter hierarchy
    hierarchy = ParameterHierarchy()

    # Resolve with all levels
    params = hierarchy.resolve(
        global_preset="base",
        category_preset="knobs",
        variant_params={"geometry": {"base_diameter": 0.025}},
        instance_params={"color_system": {"primary": [1.0, 0.0, 0.0]}}
    )

    print("Resolved parameters:")
    print(yaml.dump(params, default_flow_style=False))

    # Validate required parameters
    required = [
        "geometry.base_diameter",
        "material.metallic",
        "color_system.primary"
    ]

    missing = hierarchy.validate_required(params, required)
    if missing:
        print(f"Missing parameters: {missing}")
    else:
        print("All required parameters present")
