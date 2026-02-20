"""
Shape Key System

Shape key management and manipulation for facial expressions.

Phase 13.4: Face Animation (REQ-ANIM-04)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
import math

from .types import (
    ShapeKeyConfig,
    ShapeKeyCategory,
    ExpressionCategory,
)


@dataclass
class ShapeKeySlider:
    """A slider control for a shape key or group."""
    name: str
    shape_keys: List[str]  # Shape keys this slider affects
    value: float = 0.0
    min_value: float = 0.0
    max_value: float = 1.0
    symmetric: bool = False  # If True, L/R are mirrored
    category: ShapeKeyCategory = ShapeKeyCategory.CUSTOM

    def set_value(self, value: float) -> None:
        """Set slider value clamped to range."""
        self.value = max(self.min_value, min(self.max_value, value))

    def get_normalized(self) -> float:
        """Get value normalized to 0-1 range."""
        if self.max_value == self.min_value:
            return 0.0
        return (self.value - self.min_value) / (self.max_value - self.min_value)


@dataclass
class ShapeKeyGroup:
    """A group of related shape keys."""
    name: str
    category: ShapeKeyCategory
    shape_keys: Dict[str, ShapeKeyConfig] = field(default_factory=dict)
    sliders: Dict[str, ShapeKeySlider] = field(default_factory=dict)
    exclusive: bool = False  # If True, only one shape key can be active


class ShapeKeyManager:
    """Manage shape keys for facial animation."""

    def __init__(self):
        """Initialize shape key manager."""
        self._shape_keys: Dict[str, ShapeKeyConfig] = {}
        self._groups: Dict[str, ShapeKeyGroup] = {}
        self._sliders: Dict[str, ShapeKeySlider] = {}

    def add_shape_key(self, config: ShapeKeyConfig) -> None:
        """Add a shape key configuration.

        Args:
            config: ShapeKeyConfig to add
        """
        self._shape_keys[config.name] = config

    def remove_shape_key(self, name: str) -> bool:
        """Remove a shape key.

        Args:
            name: Shape key name to remove

        Returns:
            True if removed
        """
        if name in self._shape_keys:
            del self._shape_keys[name]
            return True
        return False

    def get_shape_key(self, name: str) -> Optional[ShapeKeyConfig]:
        """Get a shape key by name.

        Args:
            name: Shape key name

        Returns:
            ShapeKeyConfig or None
        """
        return self._shape_keys.get(name)

    def get_all_shape_keys(self) -> Dict[str, ShapeKeyConfig]:
        """Get all shape keys.

        Returns:
            Dict of name -> ShapeKeyConfig
        """
        return dict(self._shape_keys)

    def get_shape_keys_by_category(
        self,
        category: ShapeKeyCategory
    ) -> Dict[str, ShapeKeyConfig]:
        """Get shape keys filtered by category.

        Args:
            category: Category to filter by

        Returns:
            Dict of filtered shape keys
        """
        return {
            name: sk for name, sk in self._shape_keys.items()
            if sk.category == category
        }

    def set_value(self, name: str, value: float) -> bool:
        """Set a shape key value.

        Args:
            name: Shape key name
            value: Value to set (clamped to 0-1)

        Returns:
            True if shape key exists
        """
        sk = self._shape_keys.get(name)
        if sk:
            sk.value = max(sk.min_value, min(sk.max_value, value))
            return True
        return False

    def get_value(self, name: str) -> float:
        """Get a shape key value.

        Args:
            name: Shape key name

        Returns:
            Current value or 0.0 if not found
        """
        sk = self._shape_keys.get(name)
        return sk.value if sk else 0.0

    def set_multiple(self, values: Dict[str, float]) -> int:
        """Set multiple shape key values at once.

        Args:
            values: Dict of name -> value

        Returns:
            Number of shape keys successfully set
        """
        count = 0
        for name, value in values.items():
            if self.set_value(name, value):
                count += 1
        return count

    def reset_all(self) -> None:
        """Reset all shape keys to 0."""
        for sk in self._shape_keys.values():
            sk.value = 0.0

    def reset_category(self, category: ShapeKeyCategory) -> int:
        """Reset all shape keys of a category.

        Args:
            category: Category to reset

        Returns:
            Number of shape keys reset
        """
        count = 0
        for sk in self._shape_keys.values():
            if sk.category == category:
                sk.value = 0.0
                count += 1
        return count

    def create_group(
        self,
        name: str,
        category: ShapeKeyCategory,
        shape_key_names: Optional[List[str]] = None,
        exclusive: bool = False
    ) -> ShapeKeyGroup:
        """Create a shape key group.

        Args:
            name: Group name
            category: Category for the group
            shape_key_names: Optional list of shape keys to add
            exclusive: If True, only one shape key can be active

        Returns:
            Created ShapeKeyGroup
        """
        group = ShapeKeyGroup(
            name=name,
            category=category,
            exclusive=exclusive,
        )

        # Add existing shape keys
        if shape_key_names:
            for sk_name in shape_key_names:
                if sk_name in self._shape_keys:
                    group.shape_keys[sk_name] = self._shape_keys[sk_name]

        self._groups[name] = group
        return group

    def get_group(self, name: str) -> Optional[ShapeKeyGroup]:
        """Get a shape key group by name.

        Args:
            name: Group name

        Returns:
            ShapeKeyGroup or None
        """
        return self._groups.get(name)

    def remove_group(self, name: str) -> bool:
        """Remove a shape key group.

        Args:
            name: Group name to remove

        Returns:
            True if removed
        """
        if name in self._groups:
            del self._groups[name]
            return True
        return False

    def create_slider(
        self,
        name: str,
        shape_keys: List[str],
        symmetric: bool = False,
        category: ShapeKeyCategory = ShapeKeyCategory.CUSTOM
    ) -> ShapeKeySlider:
        """Create a slider control.

        Args:
            name: Slider name
            shape_keys: List of shape keys this slider affects
            symmetric: If True, L/R are mirrored
            category: Category for organization

        Returns:
            Created ShapeKeySlider
        """
        slider = ShapeKeySlider(
            name=name,
            shape_keys=shape_keys,
            symmetric=symmetric,
            category=category,
        )
        self._sliders[name] = slider
        return slider

    def get_slider(self, name: str) -> Optional[ShapeKeySlider]:
        """Get a slider by name.

        Args:
            name: Slider name

        Returns:
            ShapeKeySlider or None
        """
        return self._sliders.get(name)

    def set_slider_value(self, name: str, value: float) -> bool:
        """Set a slider value and update affected shape keys.

        Args:
            name: Slider name
            value: Value to set

        Returns:
            True if slider exists
        """
        slider = self._sliders.get(name)
        if not slider:
            return False

        slider.set_value(value)

        # Update affected shape keys
        for sk_name in slider.shape_keys:
            if sk_name in self._shape_keys:
                self._shape_keys[sk_name].value = slider.value

        return True

    def mirror_values(self, left_prefix: str = "_L", right_prefix: str = "_R") -> int:
        """Mirror L/R shape key values.

        Args:
            left_prefix: Prefix for left side shape keys
            right_prefix: Prefix for right side shape keys

        Returns:
            Number of pairs mirrored
        """
        count = 0
        for name, sk in self._shape_keys.items():
            if left_prefix in name:
                right_name = name.replace(left_prefix, right_prefix)
                if right_name in self._shape_keys:
                    self._shape_keys[right_name].value = sk.value
                    count += 1
        return count

    def blend_shape_keys(
        self,
        shape_keys_a: Dict[str, float],
        shape_keys_b: Dict[str, float],
        factor: float = 0.5
    ) -> Dict[str, float]:
        """Blend two shape key sets.

        Args:
            shape_keys_a: First set of shape keys
            shape_keys_b: Second set of shape keys
            factor: Blend factor (0=a, 1=b)

        Returns:
            Blended shape key values
        """
        result = dict(shape_keys_a)
        for name, value in shape_keys_b.items():
            if name in result:
                result[name] = result[name] * (1 - factor) + value * factor
            else:
                result[name] = value * factor
        return result

    def get_active_shape_keys(self, threshold: float = 0.01) -> Dict[str, float]:
        """Get all shape keys above a threshold.

        Args:
            threshold: Minimum value to include

        Returns:
            Dict of active shape key name -> value
        """
        return {
            name: sk.value
            for name, sk in self._shape_keys.items()
            if sk.value > threshold
        }

    def apply_preset(self, preset: Dict[str, float], blend: float = 1.0) -> None:
        """Apply a shape key preset.

        Args:
            preset: Dict of shape key name -> value
            blend: Blend factor (0=no change, 1=full preset)
        """
        for name, value in preset.items():
            if name in self._shape_keys:
                current = self._shape_keys[name].value
                self._shape_keys[name].value = current * (1 - blend) + value * blend


class ShapeKeyCorrective:
    """Manage corrective shape keys."""

    def __init__(self, manager: ShapeKeyManager):
        """Initialize corrective shape key system.

        Args:
            manager: ShapeKeyManager instance
        """
        self.manager = manager
        self._corrective_rules: Dict[str, Dict[str, Any]] = {}

    def add_corrective(
        self,
        corrective_name: str,
        trigger_keys: Dict[str, Tuple[float, float]],
        falloff: float = 0.5
    ) -> None:
        """Add a corrective shape key rule.

        Args:
            corrective_name: Name of the corrective shape key
            trigger_keys: Dict of shape key name -> (min_threshold, max_threshold)
            falloff: Falloff factor for the corrective
        """
        # Add as corrective shape key
        self.manager.add_shape_key(ShapeKeyConfig(
            name=corrective_name,
            category=ShapeKeyCategory.CORRECTIVE,
        ))

        self._corrective_rules[corrective_name] = {
            "triggers": trigger_keys,
            "falloff": falloff,
        }

    def remove_corrective(self, corrective_name: str) -> bool:
        """Remove a corrective shape key rule.

        Args:
            corrective_name: Name of the corrective

        Returns:
            True if removed
        """
        if corrective_name in self._corrective_rules:
            del self._corrective_rules[corrective_name]
            self.manager.remove_shape_key(corrective_name)
            return True
        return False

    def evaluate_correctives(self) -> Dict[str, float]:
        """Evaluate all corrective shape keys.

        Returns:
            Dict of corrective name -> calculated value
        """
        results = {}

        for corrective_name, rule in self._corrective_rules.items():
            triggers = rule["triggers"]
            falloff = rule["falloff"]

            # Calculate combined influence
            total_influence = 0.0
            for trigger_name, (min_val, max_val) in triggers.items():
                current = self.manager.get_value(trigger_name)
                if current >= min_val and current <= max_val:
                    # Calculate influence within the range
                    if min_val != max_val:
                        influence = (current - min_val) / (max_val - min_val)
                    else:
                        influence = 1.0 if current >= min_val else 0.0
                    total_influence = max(total_influence, influence)

            # Apply falloff
            value = total_influence * (1.0 - falloff) + total_influence * falloff
            results[corrective_name] = min(1.0, max(0.0, value))

        return results

    def apply_correctives(self) -> None:
        """Evaluate and apply all corrective shape keys."""
        values = self.evaluate_correctives()
        for name, value in values.items():
            self.manager.set_value(name, value)


# Convenience functions
def create_shape_key_manager(
    shape_keys: Optional[List[ShapeKeyConfig]] = None
) -> ShapeKeyManager:
    """Create a shape key manager with optional initial shape keys.

    Args:
        shape_keys: Optional list of shape keys to add

    Returns:
        Configured ShapeKeyManager
    """
    manager = ShapeKeyManager()
    if shape_keys:
        for sk in shape_keys:
            manager.add_shape_key(sk)
    return manager


def get_expression_shape_key_names() -> List[str]:
    """Get standard expression shape key names.

    Returns:
        List of shape key names
    """
    return [
        # Brows
        "brow_raise_L", "brow_raise_R",
        "brow_lower_L", "brow_lower_R",
        "brow_furrow",
        # Eyes
        "blink_L", "blink_R",
        "eye_wide_L", "eye_wide_R",
        "squint_L", "squint_R",
        # Mouth
        "smile_L", "smile_R",
        "frown_L", "frown_R",
        "mouth_pucker", "lip_funnel",
        "jaw_open",
        # Cheeks/Nose
        "cheek_puff_L", "cheek_puff_R",
        "nose_wrinkle_L", "nose_wrinkle_R",
    ]


def create_default_expression_shape_keys() -> Dict[str, ShapeKeyConfig]:
    """Create default expression shape key configurations.

    Returns:
        Dict of name -> ShapeKeyConfig
    """
    shape_keys = {}
    for name in get_expression_shape_key_names():
        shape_keys[name] = ShapeKeyConfig(
            name=name,
            category=ShapeKeyCategory.EXPRESSION,
            description=f"Expression shape key: {name}",
        )
    return shape_keys


def calculate_combination_weight(
    shape_keys: Dict[str, float],
    blend_mode: str = "max"
) -> float:
    """Calculate a weight for a combination shape key.

    Args:
        shape_keys: Dict of shape key name -> value
        blend_mode: How to combine (max, min, average, multiply)

    Returns:
        Combined weight
    """
    if not shape_keys:
        return 0.0

    values = list(shape_keys.values())

    if blend_mode == "max":
        return max(values)
    elif blend_mode == "min":
        return min(values)
    elif blend_mode == "average":
        return sum(values) / len(values)
    elif blend_mode == "multiply":
        result = 1.0
        for v in values:
            result *= v
        return result
    else:
        return max(values)  # Default to max
