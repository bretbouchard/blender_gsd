"""
Animation Layer System Core

Manages animation layers for non-destructive editing.

Phase 13.7: Animation Layers (REQ-ANIM-09)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Set, Any, Tuple
from pathlib import Path
import logging
import yaml

from ..types import (
    AnimationLayer,
    LayerStack,
    LayerType,
    LayerKeyframe,
    BoneKeyframe,
    LayerPreset,
)

logger = logging.getLogger(__name__)


class AnimationLayerSystem:
    """
    Manage animation layers for non-destructive editing.

    Supports:
    - Multiple animation layers
    - Layer opacity/mixing
    - Layer masking (affect only some bones)
    - Solo/mute layers
    - Non-destructive editing
    """

    def __init__(self, rig_id: str, bone_names: Optional[List[str]] = None):
        """
        Initialize layer system.

        Args:
            rig_id: Identifier for the rig
            bone_names: Optional list of bone names for the rig
        """
        self.stack = LayerStack(rig_id=rig_id)
        self.bone_names = bone_names or []
        self._preset_cache: Dict[str, LayerPreset] = {}

    def create_layer(
        self,
        name: str,
        layer_type: LayerType = LayerType.ADDITIVE,
        bone_mask: Optional[Set[str]] = None
    ) -> AnimationLayer:
        """
        Create a new animation layer.

        Args:
            name: Layer name
            layer_type: Type of layer (BASE, OVERRIDE, ADDITIVE, MIX)
            bone_mask: Optional set of bones this layer affects

        Returns:
            Created AnimationLayer

        Raises:
            ValueError: If layer with same ID already exists
        """
        layer_id = name.lower().replace(' ', '_')

        # Check for duplicate
        if self.stack.get_layer(layer_id):
            raise ValueError(f"Layer already exists: {layer_id}")

        layer = AnimationLayer(
            id=layer_id,
            name=name,
            layer_type=layer_type,
            bone_mask=list(bone_mask) if bone_mask else [],
            order=len(self.stack.layers),
        )

        self.stack.layers.append(layer)
        logger.debug(f"Created layer '{name}' (type={layer_type.value})")
        return layer

    def delete_layer(self, layer_id: str) -> bool:
        """
        Delete a layer.

        Args:
            layer_id: ID of layer to delete

        Returns:
            True if deleted, False if not found or is BASE layer
        """
        layer = self.stack.get_layer(layer_id)
        if layer and layer.layer_type != LayerType.BASE:
            self.stack.layers.remove(layer)
            # Reorder remaining layers
            for i, l in enumerate(self.stack.layers):
                l.order = i
            logger.debug(f"Deleted layer '{layer_id}'")
            return True
        return False

    def set_layer_opacity(self, layer_id: str, opacity: float) -> bool:
        """
        Set layer opacity (0-1).

        Args:
            layer_id: Layer ID
            opacity: Opacity value (0.0 to 1.0)

        Returns:
            True if layer found and updated
        """
        layer = self.stack.get_layer(layer_id)
        if layer:
            layer.opacity = max(0.0, min(1.0, opacity))
            return True
        return False

    def mute_layer(self, layer_id: str, mute: bool = True) -> bool:
        """
        Mute/unmute a layer.

        Args:
            layer_id: Layer ID
            mute: True to mute, False to unmute

        Returns:
            True if layer found and updated
        """
        layer = self.stack.get_layer(layer_id)
        if layer:
            layer.mute = mute
            return True
        return False

    def solo_layer(self, layer_id: str, solo: bool = True) -> bool:
        """
        Solo/unsolo a layer.

        Args:
            layer_id: Layer ID
            solo: True to solo, False to unsolo

        Returns:
            True if layer found and updated
        """
        layer = self.stack.get_layer(layer_id)
        if layer:
            layer.solo = solo
            return True
        return False

    def set_layer_bone_mask(self, layer_id: str, bones: Set[str]) -> bool:
        """
        Set which bones this layer affects.

        Args:
            layer_id: Layer ID
            bones: Set of bone names (empty = all bones)

        Returns:
            True if layer found and updated
        """
        layer = self.stack.get_layer(layer_id)
        if layer:
            layer.bone_mask = list(bones)
            return True
        return False

    def add_keyframe_to_layer(
        self,
        layer_id: str,
        frame: int,
        bone_name: str,
        location: Optional[Tuple[float, float, float]] = None,
        rotation: Optional[Tuple[float, float, float]] = None,
        scale: Optional[Tuple[float, float, float]] = None
    ) -> bool:
        """
        Add a keyframe to a layer.

        Args:
            layer_id: Layer ID
            frame: Frame number
            bone_name: Name of bone
            location: Optional location tuple
            rotation: Optional rotation tuple (Euler degrees)
            scale: Optional scale tuple

        Returns:
            True if layer found and keyframe added
        """
        layer = self.stack.get_layer(layer_id)
        if not layer:
            return False

        # Find or create keyframe at frame
        kf = None
        for k in layer.keyframes:
            if k.frame == frame:
                kf = k
                break

        if not kf:
            kf = LayerKeyframe(frame=frame)
            layer.keyframes.append(kf)
            layer.keyframes.sort(key=lambda x: x.frame)

        # Add bone data
        bone_kf = kf.bones.get(bone_name, BoneKeyframe())
        if location is not None:
            bone_kf = BoneKeyframe(
                location=location,
                rotation=bone_kf.rotation,
                scale=bone_kf.scale
            )
        if rotation is not None:
            bone_kf = BoneKeyframe(
                location=bone_kf.location,
                rotation=rotation,
                scale=bone_kf.scale
            )
        if scale is not None:
            bone_kf = BoneKeyframe(
                location=bone_kf.location,
                rotation=bone_kf.rotation,
                scale=scale
            )

        kf.bones[bone_name] = bone_kf
        return True

    def get_layers(self) -> List[AnimationLayer]:
        """Get all layers."""
        return self.stack.layers

    def get_layer(self, layer_id: str) -> Optional[AnimationLayer]:
        """Get a layer by ID."""
        return self.stack.get_layer(layer_id)

    def get_active_layer(self) -> Optional[AnimationLayer]:
        """Get the currently active layer."""
        if self.stack.active_layer:
            return self.stack.get_layer(self.stack.active_layer)
        return None

    def set_active_layer(self, layer_id: str) -> bool:
        """
        Set the active layer.

        Args:
            layer_id: Layer ID to make active

        Returns:
            True if layer found and set as active
        """
        if self.stack.get_layer(layer_id):
            self.stack.active_layer = layer_id
            return True
        return False

    def move_layer(self, layer_id: str, new_order: int) -> bool:
        """
        Move a layer to a new position in the stack.

        Args:
            layer_id: Layer ID to move
            new_order: New position (0-based)

        Returns:
            True if successful
        """
        layer = self.stack.get_layer(layer_id)
        if not layer:
            return False

        # Clamp new_order
        new_order = max(0, min(new_order, len(self.stack.layers) - 1))

        # Remove and reinsert
        self.stack.layers.remove(layer)
        self.stack.layers.insert(new_order, layer)

        # Update order values
        for i, l in enumerate(self.stack.layers):
            l.order = i

        return True

    def duplicate_layer(self, layer_id: str, new_name: str) -> Optional[AnimationLayer]:
        """
        Duplicate a layer.

        Args:
            layer_id: Layer ID to duplicate
            new_name: Name for the new layer

        Returns:
            New layer or None if source not found
        """
        source = self.stack.get_layer(layer_id)
        if not source:
            return None

        # Create new layer with copied properties
        new_layer = self.create_layer(
            name=new_name,
            layer_type=source.layer_type,
            bone_mask=set(source.bone_mask)
        )

        # Copy keyframes
        for kf in source.keyframes:
            new_kf = LayerKeyframe(frame=kf.frame)
            for bone_name, bone_kf in kf.bones.items():
                new_kf.bones[bone_name] = BoneKeyframe(
                    location=bone_kf.location,
                    rotation=bone_kf.rotation,
                    scale=bone_kf.scale
                )
            new_layer.keyframes.append(new_kf)

        new_layer.opacity = source.opacity

        return new_layer

    def save_layers(self, path: Path) -> bool:
        """
        Save layer stack to YAML file.

        Args:
            path: Path to save file

        Returns:
            True if saved successfully
        """
        try:
            data = self.stack.to_dict()
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            logger.info(f"Saved layer stack to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save layers: {e}")
            return False

    def load_layers(self, path: Path) -> bool:
        """
        Load layer stack from YAML file.

        Args:
            path: Path to load file

        Returns:
            True if loaded successfully
        """
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            self.stack = LayerStack.from_dict(data)
            logger.info(f"Loaded layer stack from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load layers: {e}")
            return False


def create_layer_system(rig_id: str, bone_names: Optional[List[str]] = None) -> AnimationLayerSystem:
    """
    Create an animation layer system for a rig.

    Creates a base layer automatically.

    Args:
        rig_id: Identifier for the rig
        bone_names: Optional list of bone names

    Returns:
        New AnimationLayerSystem with base layer
    """
    system = AnimationLayerSystem(rig_id=rig_id, bone_names=bone_names)

    # Create base layer
    system.create_layer("Base", LayerType.BASE)

    return system


def get_layer_presets_directory() -> Path:
    """Get the path to layer presets directory."""
    return Path(__file__).parent.parent.parent.parent / "configs" / "animation" / "layers"


def list_layer_presets() -> List[str]:
    """
    List available layer preset names.

    Returns:
        List of preset names
    """
    presets_dir = get_layer_presets_directory()
    if not presets_dir.exists():
        return []

    return [f.stem for f in presets_dir.glob("*.yaml")]


def load_layer_preset(preset_name: str) -> Optional[LayerPreset]:
    """
    Load a layer preset by name.

    Args:
        preset_name: Name of preset (without .yaml extension)

    Returns:
        LayerPreset or None if not found
    """
    presets_dir = get_layer_presets_directory()
    preset_path = presets_dir / f"{preset_name}.yaml"

    if not preset_path.exists():
        return None

    try:
        with open(preset_path, 'r') as f:
            data = yaml.safe_load(f)
        return LayerPreset.from_dict(data)
    except Exception as e:
        logger.error(f"Failed to load preset '{preset_name}': {e}")
        return None


def apply_layer_preset(system: AnimationLayerSystem, preset_name: str) -> bool:
    """
    Apply a layer preset to a layer system.

    Args:
        system: AnimationLayerSystem to apply to
        preset_name: Name of preset to apply

    Returns:
        True if applied successfully
    """
    preset = load_layer_preset(preset_name)
    if not preset:
        return False

    # Create layers from preset
    for layer_def in preset.layers:
        try:
            layer_type = LayerType(layer_def.get('type', 'additive'))
            bone_mask = set(layer_def.get('bone_mask', []))

            system.create_layer(
                name=layer_def['name'],
                layer_type=layer_type,
                bone_mask=bone_mask if bone_mask else None
            )
        except Exception as e:
            logger.warning(f"Failed to create layer from preset: {e}")

    return True
