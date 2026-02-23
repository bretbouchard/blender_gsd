"""
Layer Compositor

Manages composite layers and rendering.

Part of Phase 12.1: Compositor (REQ-COMP-01)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Tuple
import json
from pathlib import Path

from .compositor_types import (
    CompositeConfig,
    CompLayer,
    BlendMode,
    LayerSource,
    ColorCorrection,
    Transform2D,
)


@dataclass
class CompositeResult:
    """Result of a composite operation."""
    success: bool
    frame: int
    output_path: str = ""
    error: str = ""
    timing_ms: float = 0.0


class LayerCompositor:
    """
    Manage composite layers and perform compositing operations.

    This is a pure Python implementation that works with configuration.
    For actual rendering, use the Blender integration module.
    """

    def __init__(self, config: Optional[CompositeConfig] = None):
        self.config = config or CompositeConfig(name="Composite")
        self._layer_cache: Dict[str, Any] = {}
        self._on_layer_change: Optional[Callable[[str], None]] = None

    # ==================== Layer Management ====================

    def add_layer(self, layer: CompLayer) -> None:
        """Add a layer to the composite."""
        self.config.add_layer(layer)
        self._invalidate_cache(layer.name)
        self._notify_change(layer.name)

    def remove_layer(self, name: str) -> bool:
        """Remove a layer by name."""
        result = self.config.remove_layer(name)
        if result:
            self._invalidate_cache(name)
            self._notify_change(name)
        return result

    def get_layer(self, name: str) -> Optional[CompLayer]:
        """Get a layer by name."""
        return self.config.get_layer(name)

    def get_all_layers(self) -> List[CompLayer]:
        """Get all layers."""
        return self.config.layers.copy()

    def get_enabled_layers(self) -> List[CompLayer]:
        """Get all enabled layers (respecting solo)."""
        return self.config.get_enabled_layers()

    def reorder_layer(self, name: str, new_index: int) -> bool:
        """Move a layer to a new position in the stack."""
        layer = self.get_layer(name)
        if not layer:
            return False

        current_index = self.config.layers.index(layer)
        if current_index == new_index:
            return True

        self.config.layers.pop(current_index)
        new_index = max(0, min(new_index, len(self.config.layers)))
        self.config.layers.insert(new_index, layer)
        self._notify_change(name)
        return True

    def move_layer_up(self, name: str) -> bool:
        """Move a layer up in the stack (toward top)."""
        layer = self.get_layer(name)
        if not layer:
            return False
        current_index = self.config.layers.index(layer)
        return self.reorder_layer(name, current_index + 1)

    def move_layer_down(self, name: str) -> bool:
        """Move a layer down in the stack (toward bottom)."""
        layer = self.get_layer(name)
        if not layer:
            return False
        current_index = self.config.layers.index(layer)
        return self.reorder_layer(name, current_index - 1)

    def duplicate_layer(self, name: str, new_name: Optional[str] = None) -> Optional[CompLayer]:
        """Duplicate a layer."""
        layer = self.get_layer(name)
        if not layer:
            return None

        # Create copy via serialization
        new_layer = CompLayer.from_dict(layer.to_dict())
        new_layer.name = new_name or f"{name}_copy"
        new_layer.locked = False
        new_layer.solo = False

        self.add_layer(new_layer)
        return new_layer

    def merge_down(self, name: str) -> bool:
        """Merge layer with the one below it."""
        layer = self.get_layer(name)
        if not layer:
            return False

        current_index = self.config.layers.index(layer)
        if current_index == 0:
            return False  # No layer below

        # In a real implementation, this would composite the two layers
        # For now, just remove the upper layer
        lower_layer = self.config.layers[current_index - 1]
        self.remove_layer(name)
        self._notify_change(lower_layer.name)
        return True

    # ==================== Layer Properties ====================

    def set_blend_mode(self, name: str, mode: BlendMode) -> bool:
        """Set a layer's blend mode."""
        layer = self.get_layer(name)
        if not layer:
            return False
        layer.blend_mode = mode
        self._invalidate_cache(name)
        self._notify_change(name)
        return True

    def set_opacity(self, name: str, opacity: float) -> bool:
        """Set a layer's opacity."""
        layer = self.get_layer(name)
        if not layer:
            return False
        layer.opacity = max(0.0, min(1.0, opacity))
        self._invalidate_cache(name)
        self._notify_change(name)
        return True

    def set_enabled(self, name: str, enabled: bool) -> bool:
        """Enable or disable a layer."""
        layer = self.get_layer(name)
        if not layer:
            return False
        layer.enabled = enabled
        self._invalidate_cache(name)
        self._notify_change(name)
        return True

    def set_solo(self, name: str, solo: bool) -> bool:
        """Set solo mode for a layer."""
        layer = self.get_layer(name)
        if not layer:
            return False
        layer.solo = solo
        self._notify_change(name)
        return True

    def set_locked(self, name: str, locked: bool) -> bool:
        """Lock or unlock a layer."""
        layer = self.get_layer(name)
        if not layer:
            return False
        layer.locked = locked
        return True

    def set_transform(self, name: str, transform: Transform2D) -> bool:
        """Set a layer's transform."""
        layer = self.get_layer(name)
        if not layer:
            return False
        layer.transform = transform
        self._invalidate_cache(name)
        self._notify_change(name)
        return True

    def set_color_correction(self, name: str, cc: ColorCorrection) -> bool:
        """Set a layer's color correction."""
        layer = self.get_layer(name)
        if not layer:
            return False
        layer.color_correction = cc
        self._invalidate_cache(name)
        self._notify_change(name)
        return True

    # ==================== Factory Methods ====================

    def create_solid_layer(
        self,
        name: str,
        color: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0),
        blend_mode: BlendMode = BlendMode.NORMAL,
    ) -> CompLayer:
        """Create a solid color layer."""
        layer = CompLayer(
            name=name,
            source="solid",
            source_type=LayerSource.SOLID,
            solid_color=color,
            blend_mode=blend_mode,
        )
        self.add_layer(layer)
        return layer

    def create_gradient_layer(
        self,
        name: str,
        stops: List[Tuple[float, Tuple[float, float, float, float]]],
        angle: float = 0.0,
        blend_mode: BlendMode = BlendMode.NORMAL,
    ) -> CompLayer:
        """Create a gradient layer."""
        from .compositor_types import GradientStop

        layer = CompLayer(
            name=name,
            source="gradient",
            source_type=LayerSource.GRADIENT,
            gradient_stops=[GradientStop(pos, color) for pos, color in stops],
            gradient_angle=angle,
            blend_mode=blend_mode,
        )
        self.add_layer(layer)
        return layer

    def create_image_layer(
        self,
        name: str,
        path: str,
        blend_mode: BlendMode = BlendMode.NORMAL,
        opacity: float = 1.0,
    ) -> CompLayer:
        """Create an image/sequence layer."""
        layer = CompLayer(
            name=name,
            source=path,
            source_type=LayerSource.IMAGE_SEQUENCE,
            blend_mode=blend_mode,
            opacity=opacity,
        )
        self.add_layer(layer)
        return layer

    def create_render_pass_layer(
        self,
        name: str,
        pass_name: str,
        blend_mode: BlendMode = BlendMode.NORMAL,
    ) -> CompLayer:
        """Create a render pass layer."""
        layer = CompLayer(
            name=name,
            source=pass_name,
            source_type=LayerSource.RENDER_PASS,
            blend_mode=blend_mode,
        )
        self.add_layer(layer)
        return layer

    # ==================== Rendering (Stub) ====================

    def render_frame(self, frame: int) -> CompositeResult:
        """
        Render a single frame.

        Note: This is a stub. Actual rendering requires Blender integration.
        """
        import time
        start = time.time()

        # In real implementation, this would:
        # 1. Load all enabled layer sources
        # 2. Apply transforms
        # 3. Apply color corrections
        # 4. Composite with blend modes
        # 5. Apply masks
        # 6. Output result

        elapsed = (time.time() - start) * 1000

        return CompositeResult(
            success=True,
            frame=frame,
            output_path=self.config.output_path,
            timing_ms=elapsed,
        )

    def render_all(self) -> List[CompositeResult]:
        """Render all frames in the frame range."""
        start, end = self.config.frame_range
        return [self.render_frame(f) for f in range(start, end + 1)]

    # ==================== Serialization ====================

    def save_config(self, path: str) -> bool:
        """Save configuration to JSON file."""
        try:
            with open(path, 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False

    def load_config(self, path: str) -> bool:
        """Load configuration from JSON file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            self.config = CompositeConfig.from_dict(data)
            self._layer_cache.clear()
            return True
        except Exception as e:
            print(f"Failed to load config: {e}")
            return False

    # ==================== Internal ====================

    def _invalidate_cache(self, name: str) -> None:
        """Invalidate cache for a layer."""
        self._layer_cache.pop(name, None)

    def _notify_change(self, name: str) -> None:
        """Notify listeners of a layer change."""
        if self._on_layer_change:
            self._on_layer_change(name)

    def set_change_callback(self, callback: Optional[Callable[[str], None]]) -> None:
        """Set callback for layer changes."""
        self._on_layer_change = callback


# ==================== Convenience Functions ====================

def create_compositor(
    name: str = "Composite",
    resolution: Tuple[int, int] = (1920, 1080),
    frame_rate: float = 24.0,
    frame_range: Tuple[int, int] = (1, 250),
) -> LayerCompositor:
    """Create a new compositor with the given settings."""
    config = CompositeConfig(
        name=name,
        resolution=resolution,
        frame_rate=frame_rate,
        frame_range=frame_range,
    )
    return LayerCompositor(config)


def load_compositor(path: str) -> Optional[LayerCompositor]:
    """Load a compositor from a config file."""
    compositor = LayerCompositor()
    if compositor.load_config(path):
        return compositor
    return None
