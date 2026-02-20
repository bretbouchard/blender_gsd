"""
Face Rig System

Face rig creation and management for facial animation.

Phase 13.4: Face Animation (REQ-ANIM-04)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
import os
import json

from .types import (
    FaceRigComponent,
    FaceRigConfig,
    ShapeKeyConfig,
    ExpressionConfig,
    ShapeKeyCategory,
    ExpressionCategory,
    VisemeType,
)


# Standard face rig bone templates
FACE_BONE_TEMPLATES = {
    "standard": {
        "eyes": [
            "eye.L", "eye.R",
            "eyelid_top.L", "eyelid_top.R",
            "eyelid_bottom.L", "eyelid_bottom.R",
        ],
        "brows": [
            "brow.L", "brow.R",
            "brow_inner.L", "brow_inner.R",
            "brow_outer.L", "brow_outer.R",
        ],
        "mouth": [
            "lip_top", "lip_bottom",
            "lip_corner.L", "lip_corner.R",
            "jaw",
        ],
        "cheeks": [
            "cheek.L", "cheek.R",
        ],
        "nose": [
            "nose",
            "nostril.L", "nostril.R",
        ],
    },
    "simple": {
        "eyes": ["eye.L", "eye.R"],
        "brows": ["brow.L", "brow.R"],
        "mouth": ["jaw"],
    },
    "detailed": {
        "eyes": [
            "eye.L", "eye.R",
            "eyelid_top.L", "eyelid_top.R",
            "eyelid_bottom.L", "eyelid_bottom.R",
            "pupil.L", "pupil.R",
        ],
        "brows": [
            "brow.L", "brow.R",
            "brow_inner.L", "brow_inner.R",
            "brow_mid.L", "brow_mid.R",
            "brow_outer.L", "brow_outer.R",
        ],
        "mouth": [
            "lip_top", "lip_bottom",
            "lip_top_mid", "lip_bottom_mid",
            "lip_corner.L", "lip_corner.R",
            "jaw",
        ],
        "cheeks": [
            "cheek.L", "cheek.R",
            "cheek_puff.L", "cheek_puff.R",
        ],
        "nose": [
            "nose",
            "nose_tip",
            "nostril.L", "nostril.R",
        ],
        "tongue": [
            "tongue_root",
            "tongue_tip",
        ],
    },
}


@dataclass
class FaceRigStats:
    """Statistics for a face rig."""
    total_shape_keys: int = 0
    expression_count: int = 0
    viseme_count: int = 0
    control_bone_count: int = 0
    components: List[FaceRigComponent] = field(default_factory=list)


class FaceRigBuilder:
    """Build and configure face rigs."""

    def __init__(self, config: Optional[FaceRigConfig] = None):
        """Initialize face rig builder.

        Args:
            config: Optional existing face rig configuration
        """
        self.config = config or FaceRigConfig(
            id="face_rig_default",
            name="Default Face Rig"
        )
        self._shape_key_counter = 0
        self._expression_counter = 0

    def add_component(self, component: FaceRigComponent) -> None:
        """Add a component to the face rig.

        Args:
            component: Face rig component to add
        """
        if component not in self.config.components:
            self.config.components.append(component)

    def remove_component(self, component: FaceRigComponent) -> bool:
        """Remove a component from the face rig.

        Args:
            component: Face rig component to remove

        Returns:
            True if component was removed
        """
        if component in self.config.components:
            self.config.components.remove(component)
            return True
        return False

    def add_shape_key(
        self,
        name: str,
        category: ShapeKeyCategory = ShapeKeyCategory.CUSTOM,
        description: str = "",
        vertex_group: Optional[str] = None,
        symm_group: Optional[str] = None,
    ) -> ShapeKeyConfig:
        """Add a shape key to the face rig.

        Args:
            name: Shape key name
            category: Shape key category
            description: Description of the shape key
            vertex_group: Optional vertex group to limit to
            symm_group: Optional symmetry group for L/R pairs

        Returns:
            The created ShapeKeyConfig
        """
        sk = ShapeKeyConfig(
            name=name,
            category=category,
            description=description,
            vertex_group=vertex_group,
            symm_group=symm_group,
        )
        self.config.shape_keys[name] = sk
        self._shape_key_counter += 1
        return sk

    def remove_shape_key(self, name: str) -> bool:
        """Remove a shape key from the face rig.

        Args:
            name: Shape key name to remove

        Returns:
            True if shape key was removed
        """
        if name in self.config.shape_keys:
            del self.config.shape_keys[name]
            return True
        return False

    def add_expression(
        self,
        name: str,
        category: ExpressionCategory,
        shape_keys: Dict[str, float],
        description: str = "",
        bone_transforms: Optional[Dict[str, Dict[str, Any]]] = None,
        intensity: float = 1.0,
    ) -> ExpressionConfig:
        """Add a facial expression to the rig.

        Args:
            name: Expression name
            category: Expression category
            shape_keys: Dict of shape key name -> value (0.0-1.0)
            description: Description of the expression
            bone_transforms: Optional bone transforms for the expression
            intensity: Default intensity (0.0-1.0)

        Returns:
            The created ExpressionConfig
        """
        expr_id = f"expr_{self._expression_counter:03d}_{name.lower().replace(' ', '_')}"
        self._expression_counter += 1

        expr = ExpressionConfig(
            id=expr_id,
            name=name,
            category=category,
            description=description,
            shape_keys=shape_keys,
            bone_transforms=bone_transforms or {},
            intensity=intensity,
        )
        self.config.expressions[expr_id] = expr
        return expr

    def remove_expression(self, expr_id: str) -> bool:
        """Remove an expression from the rig.

        Args:
            expr_id: Expression ID to remove

        Returns:
            True if expression was removed
        """
        if expr_id in self.config.expressions:
            del self.config.expressions[expr_id]
            return True
        return False

    def add_viseme(
        self,
        viseme: VisemeType,
        shape_keys: Dict[str, float]
    ) -> None:
        """Add a viseme configuration to the rig.

        Args:
            viseme: Viseme type
            shape_keys: Dict of shape key name -> value
        """
        self.config.visemes[viseme.value] = shape_keys

    def remove_viseme(self, viseme: VisemeType) -> bool:
        """Remove a viseme from the rig.

        Args:
            viseme: Viseme type to remove

        Returns:
            True if viseme was removed
        """
        if viseme.value in self.config.visemes:
            del self.config.visemes[viseme.value]
            return True
        return False

    def add_control_bone(self, bone_name: str) -> None:
        """Add a control bone to the face rig.

        Args:
            bone_name: Name of the control bone
        """
        if bone_name not in self.config.control_bones:
            self.config.control_bones.append(bone_name)

    def remove_control_bone(self, bone_name: str) -> bool:
        """Remove a control bone from the rig.

        Args:
            bone_name: Name of control bone to remove

        Returns:
            True if control bone was removed
        """
        if bone_name in self.config.control_bones:
            self.config.control_bones.remove(bone_name)
            return True
        return False

    def get_stats(self) -> FaceRigStats:
        """Get statistics for the face rig.

        Returns:
            FaceRigStats with counts
        """
        # Count shape keys by category
        expression_sks = sum(
            1 for sk in self.config.shape_keys.values()
            if sk.category == ShapeKeyCategory.EXPRESSION
        )
        viseme_sks = sum(
            1 for sk in self.config.shape_keys.values()
            if sk.category == ShapeKeyCategory.VISEME
        )

        return FaceRigStats(
            total_shape_keys=len(self.config.shape_keys),
            expression_count=len(self.config.expressions),
            viseme_count=len(self.config.visemes),
            control_bone_count=len(self.config.control_bones),
            components=list(self.config.components),
        )

    def get_bones_for_template(
        self,
        template_name: str,
        component: Optional[FaceRigComponent] = None
    ) -> List[str]:
        """Get bones for a template and optional component.

        Args:
            template_name: Template name (standard, simple, detailed)
            component: Optional component filter

        Returns:
            List of bone names
        """
        template = FACE_BONE_TEMPLATES.get(template_name, {})
        if component:
            return template.get(component.value, [])
        all_bones = []
        for bones in template.values():
            all_bones.extend(bones)
        return all_bones

    def apply_template(
        self,
        template_name: str,
        components: Optional[List[FaceRigComponent]] = None
    ) -> None:
        """Apply a bone template to the face rig.

        Args:
            template_name: Template name (standard, simple, detailed)
            components: Optional list of components to include
        """
        template = FACE_BONE_TEMPLATES.get(template_name, {})
        if not template:
            return

        # Get components to apply
        target_components = components or [
            FaceRigComponent(c) for c in template.keys()
        ]

        for comp in target_components:
            self.add_component(comp)
            bones = template.get(comp.value, [])
            for bone in bones:
                self.add_control_bone(bone)

    def set_shape_key_value(self, name: str, value: float) -> bool:
        """Set a shape key value.

        Args:
            name: Shape key name
            value: Value to set (0.0-1.0)

        Returns:
            True if shape key exists and was updated
        """
        if name in self.config.shape_keys:
            self.config.shape_keys[name].value = max(0.0, min(1.0, value))
            return True
        return False

    def get_shape_key_value(self, name: str) -> float:
        """Get a shape key value.

        Args:
            name: Shape key name

        Returns:
            Current value or 0.0 if not found
        """
        sk = self.config.shape_keys.get(name)
        return sk.value if sk else 0.0

    def apply_expression(
        self,
        expr_id: str,
        intensity: Optional[float] = None,
        blend: bool = False
    ) -> bool:
        """Apply an expression to shape keys.

        Args:
            expr_id: Expression ID to apply
            intensity: Optional override intensity
            blend: If True, blend with current values instead of replace

        Returns:
            True if expression was applied
        """
        expr = self.config.expressions.get(expr_id)
        if not expr:
            return False

        factor = intensity if intensity is not None else expr.intensity

        for sk_name, sk_value in expr.shape_keys.items():
            if sk_name in self.config.shape_keys:
                current = self.config.shape_keys[sk_name].value
                target = sk_value * factor
                if blend:
                    # Blend with current value
                    self.config.shape_keys[sk_name].value = (
                        current * 0.5 + target * 0.5
                    )
                else:
                    self.config.shape_keys[sk_name].value = target

        return True

    def reset_shape_keys(self) -> None:
        """Reset all shape keys to 0."""
        for sk in self.config.shape_keys.values():
            sk.value = 0.0

    def save_config(self, filepath: str) -> bool:
        """Save the face rig configuration to a file.

        Args:
            filepath: Path to save to

        Returns:
            True if save was successful
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            return True
        except (OSError, IOError):
            return False

    def load_config(self, filepath: str) -> bool:
        """Load a face rig configuration from a file.

        Args:
            filepath: Path to load from

        Returns:
            True if load was successful
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.config = FaceRigConfig.from_dict(data)
            return True
        except (OSError, IOError, json.JSONDecodeError):
            return False

    def get_config(self) -> FaceRigConfig:
        """Get the current face rig configuration.

        Returns:
            Current FaceRigConfig
        """
        return self.config

    def set_config(self, config: FaceRigConfig) -> None:
        """Set the face rig configuration.

        Args:
            config: New FaceRigConfig to use
        """
        self.config = config


# Convenience functions
def create_face_rig(
    name: str,
    components: Optional[List[FaceRigComponent]] = None,
    template: str = "standard"
) -> FaceRigBuilder:
    """Create a new face rig builder.

    Args:
        name: Name for the face rig
        components: Optional list of components to include
        template: Bone template to use (standard, simple, detailed)

    Returns:
        Configured FaceRigBuilder
    """
    config = FaceRigConfig(
        id=f"face_rig_{name.lower().replace(' ', '_')}",
        name=name,
        components=components or [],
    )
    builder = FaceRigBuilder(config)

    if components:
        builder.apply_template(template, components)

    return builder


def get_default_shape_keys() -> Dict[str, ShapeKeyConfig]:
    """Get default shape keys for a standard face rig.

    Returns:
        Dict of shape key name -> ShapeKeyConfig
    """
    shape_keys = {}

    # Expression shape keys
    expression_keys = [
        ("brow_raise_L", "Left brow raise"),
        ("brow_raise_R", "Right brow raise"),
        ("brow_lower_L", "Left brow lower"),
        ("brow_lower_R", "Right brow lower"),
        ("brow_furrow", "Brow furrow/frown"),
        ("smile_L", "Left smile"),
        ("smile_R", "Right smile"),
        ("frown_L", "Left frown"),
        ("frown_R", "Right frown"),
        ("cheek_puff_L", "Left cheek puff"),
        ("cheek_puff_R", "Right cheek puff"),
        ("eye_wide_L", "Left eye wide"),
        ("eye_wide_R", "Right eye wide"),
        ("blink_L", "Left blink"),
        ("blink_R", "Right blink"),
        ("squint_L", "Left squint"),
        ("squint_R", "Right squint"),
        ("nose_wrinkle_L", "Left nose wrinkle"),
        ("nose_wrinkle_R", "Right nose wrinkle"),
        ("jaw_open", "Jaw open"),
        ("mouth_pucker", "Mouth pucker"),
        ("lip_funnel", "Lip funnel"),
    ]

    for name, description in expression_keys:
        shape_keys[name] = ShapeKeyConfig(
            name=name,
            category=ShapeKeyCategory.EXPRESSION,
            description=description,
        )

    return shape_keys


def get_bilateral_pairs() -> Dict[str, str]:
    """Get bilateral shape key pairs (L/R).

    Returns:
        Dict mapping left shape key to right shape key
    """
    return {
        "brow_raise_L": "brow_raise_R",
        "brow_lower_L": "brow_lower_R",
        "smile_L": "smile_R",
        "frown_L": "frown_R",
        "cheek_puff_L": "cheek_puff_R",
        "eye_wide_L": "eye_wide_R",
        "blink_L": "blink_R",
        "squint_L": "squint_R",
        "nose_wrinkle_L": "nose_wrinkle_R",
    }


def get_face_rig_summary(config: FaceRigConfig) -> str:
    """Get a summary string for a face rig configuration.

    Args:
        config: FaceRigConfig to summarize

    Returns:
        Summary string
    """
    lines = [
        f"Face Rig: {config.name}",
        f"  ID: {config.id}",
        f"  Components: {', '.join(c.value for c in config.components) or 'None'}",
        f"  Shape Keys: {len(config.shape_keys)}",
        f"  Expressions: {len(config.expressions)}",
        f"  Visemes: {len(config.visemes)}",
        f"  Control Bones: {len(config.control_bones)}",
    ]
    return "\n".join(lines)
