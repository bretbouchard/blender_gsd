"""
Grease Pencil Type Definitions

Core data structures for Grease Pencil stroke, material, layer, mask, and animation configuration.

Phase 21.0: Core GP Module (REQ-GP-01)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum


# =============================================================================
# Enums
# =============================================================================


class StrokeStyle(Enum):
    """Stroke rendering styles for GP materials."""
    SOLID = "SOLID"           # Solid color stroke
    TEXTURE = "TEXTURE"       # Texture-mapped stroke
    GRADIENT = "GRADIENT"     # Gradient stroke


class FillStyle(Enum):
    """Fill rendering styles for GP materials."""
    SOLID = "SOLID"           # Solid color fill
    GRADIENT = "GRADIENT"     # Gradient fill
    TEXTURE = "TEXTURE"       # Texture-mapped fill
    PATTERN = "PATTERN"       # Pattern fill


class StrokeMode(Enum):
    """Stroke drawing modes."""
    LINE = "LINE"             # Continuous line
    DOTS = "DOTS"             # Dotted stroke
    BOX = "BOX"               # Box/square stroke


class DisplayMode(Enum):
    """Display modes for GP strokes."""
    D3SPACE = "3DSPACE"       # 3D space (default)
    D2DIMAGE = "2DIMAGE"      # 2D image space
    D2DSCREEN = "2DSCREEN"    # 2D screen space


class BlendMode(Enum):
    """Blend modes for GP layers and materials."""
    REGULAR = "REGULAR"
    MULTIPLY = "MULTIPLY"
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    DIVIDE = "DIVIDE"
    OVERLAY = "OVERLAY"
    HARDLIGHT = "HARDLIGHT"
    SOFTLIGHT = "SOFTLIGHT"
    COLORBURN = "COLORBURN"
    COLORDODGE = "COLORDODGE"
    DIFFERENCE = "DIFFERENCE"
    EXCLUSION = "EXCLUSION"
    SCREEN = "SCREEN"
    HUE = "HUE"
    SATURATION = "SATURATION"
    VALUE = "VALUE"
    COLOR = "COLOR"


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass
class GPStrokeConfig:
    """Configuration for a single Grease Pencil stroke."""
    id: str
    points: List[Tuple[float, float, float, float, float]] = field(default_factory=list)  # (x, y, z, pressure, strength)
    stroke_width: float = 5.0
    hardness: float = 1.0
    use_cyclic: bool = False
    material_index: int = 0
    display_mode: DisplayMode = DisplayMode.D3SPACE
    seed: Optional[int] = None
    uv_translation: Tuple[float, float] = (0.0, 0.0)
    uv_scale: float = 1.0
    uv_rotation: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'points': [list(p) for p in self.points],
            'stroke_width': self.stroke_width,
            'hardness': self.hardness,
            'use_cyclic': self.use_cyclic,
            'material_index': self.material_index,
            'display_mode': self.display_mode.value,
            'seed': self.seed,
            'uv_translation': list(self.uv_translation),
            'uv_scale': self.uv_scale,
            'uv_rotation': self.uv_rotation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GPStrokeConfig:
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            points=[tuple(p) for p in data.get('points', [])],
            stroke_width=data.get('stroke_width', 5.0),
            hardness=data.get('hardness', 1.0),
            use_cyclic=data.get('use_cyclic', False),
            material_index=data.get('material_index', 0),
            display_mode=DisplayMode(data.get('display_mode', '3DSPACE')),
            seed=data.get('seed'),
            uv_translation=tuple(data.get('uv_translation', (0.0, 0.0))),
            uv_scale=data.get('uv_scale', 1.0),
            uv_rotation=data.get('uv_rotation', 0.0),
        )


@dataclass
class GPMaterialConfig:
    """Configuration for a Grease Pencil material."""
    id: str
    name: str = ""
    stroke_style: StrokeStyle = StrokeStyle.SOLID
    fill_style: FillStyle = FillStyle.SOLID
    stroke_mode: StrokeMode = StrokeMode.LINE
    color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)  # RGBA
    fill_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)  # RGBA
    show_stroke: bool = True
    show_fill: bool = True
    use_stroke_holdout: bool = False
    use_fill_holdout: bool = False
    stroke_texture: Optional[str] = None
    fill_texture: Optional[str] = None
    gradient_type: str = "LINEAR"  # LINEAR, RADIAL, DIAGONAL
    mix_factor: float = 0.5
    overlap_mode: str = "DEFAULT"  # DEFAULT, IN_FRONT, BEHIND
    overlap_threshold: float = 0.1
    stroke_image: Optional[str] = None
    fill_image: Optional[str] = None
    pixel_size: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'stroke_style': self.stroke_style.value,
            'fill_style': self.fill_style.value,
            'stroke_mode': self.stroke_mode.value,
            'color': list(self.color),
            'fill_color': list(self.fill_color),
            'show_stroke': self.show_stroke,
            'show_fill': self.show_fill,
            'use_stroke_holdout': self.use_stroke_holdout,
            'use_fill_holdout': self.use_fill_holdout,
            'stroke_texture': self.stroke_texture,
            'fill_texture': self.fill_texture,
            'gradient_type': self.gradient_type,
            'mix_factor': self.mix_factor,
            'overlap_mode': self.overlap_mode,
            'overlap_threshold': self.overlap_threshold,
            'stroke_image': self.stroke_image,
            'fill_image': self.fill_image,
            'pixel_size': self.pixel_size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GPMaterialConfig:
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            name=data.get('name', ''),
            stroke_style=StrokeStyle(data.get('stroke_style', 'SOLID')),
            fill_style=FillStyle(data.get('fill_style', 'SOLID')),
            stroke_mode=StrokeMode(data.get('stroke_mode', 'LINE')),
            color=tuple(data.get('color', (0.0, 0.0, 0.0, 1.0))),
            fill_color=tuple(data.get('fill_color', (1.0, 1.0, 1.0, 1.0))),
            show_stroke=data.get('show_stroke', True),
            show_fill=data.get('show_fill', True),
            use_stroke_holdout=data.get('use_stroke_holdout', False),
            use_fill_holdout=data.get('use_fill_holdout', False),
            stroke_texture=data.get('stroke_texture'),
            fill_texture=data.get('fill_texture'),
            gradient_type=data.get('gradient_type', 'LINEAR'),
            mix_factor=data.get('mix_factor', 0.5),
            overlap_mode=data.get('overlap_mode', 'DEFAULT'),
            overlap_threshold=data.get('overlap_threshold', 0.1),
            stroke_image=data.get('stroke_image'),
            fill_image=data.get('fill_image'),
            pixel_size=data.get('pixel_size', 1.0),
        )


@dataclass
class GPLayerConfig:
    """Configuration for a Grease Pencil layer."""
    id: str
    name: str
    opacity: float = 1.0
    blend_mode: BlendMode = BlendMode.REGULAR
    use_lights: bool = False
    use_mask_layer: bool = False
    stroke_configs: List[GPStrokeConfig] = field(default_factory=list)
    lock: bool = False
    hide: bool = False
    use_onion_skinning: bool = False
    tint_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 0.0)
    tint_factor: float = 0.0
    line_change: float = 0.0
    pass_index: int = 0
    parent: Optional[str] = None
    parent_bone: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'opacity': self.opacity,
            'blend_mode': self.blend_mode.value,
            'use_lights': self.use_lights,
            'use_mask_layer': self.use_mask_layer,
            'stroke_configs': [s.to_dict() for s in self.stroke_configs],
            'lock': self.lock,
            'hide': self.hide,
            'use_onion_skinning': self.use_onion_skinning,
            'tint_color': list(self.tint_color),
            'tint_factor': self.tint_factor,
            'line_change': self.line_change,
            'pass_index': self.pass_index,
            'parent': self.parent,
            'parent_bone': self.parent_bone,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GPLayerConfig:
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            opacity=data.get('opacity', 1.0),
            blend_mode=BlendMode(data.get('blend_mode', 'REGULAR')),
            use_lights=data.get('use_lights', False),
            use_mask_layer=data.get('use_mask_layer', False),
            stroke_configs=[GPStrokeConfig.from_dict(s) for s in data.get('stroke_configs', [])],
            lock=data.get('lock', False),
            hide=data.get('hide', False),
            use_onion_skinning=data.get('use_onion_skinning', False),
            tint_color=tuple(data.get('tint_color', (1.0, 1.0, 1.0, 0.0))),
            tint_factor=data.get('tint_factor', 0.0),
            line_change=data.get('line_change', 0.0),
            pass_index=data.get('pass_index', 0),
            parent=data.get('parent'),
            parent_bone=data.get('parent_bone'),
        )


@dataclass
class GPMaskConfig:
    """Configuration for a Grease Pencil mask."""
    enabled: bool = False
    mask_layer: str = ""
    invert: bool = False
    feather: float = 0.0
    type: str = "procedural"  # layer, stroke_weight, procedural, texture
    blend_mode: str = "multiply"
    texture: Optional[str] = None
    strength: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'enabled': self.enabled,
            'mask_layer': self.mask_layer,
            'invert': self.invert,
            'feather': self.feather,
            'type': self.type,
            'blend_mode': self.blend_mode,
            'texture': self.texture,
            'strength': self.strength,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GPMaskConfig:
        """Deserialize from dictionary."""
        return cls(
            enabled=data.get('enabled', False),
            mask_layer=data.get('mask_layer', ''),
            invert=data.get('invert', False),
            feather=data.get('feather', 0.0),
            type=data.get('type', 'procedural'),
            blend_mode=data.get('blend_mode', 'multiply'),
            texture=data.get('texture'),
            strength=data.get('strength', 1.0),
        )


@dataclass
class GPAnimationConfig:
    """Configuration for Grease Pencil animation settings."""
    id: str
    frame_start: int = 1
    frame_end: int = 100
    frame_rate: float = 24.0
    onion_skin_enabled: bool = False
    onion_skin_frames_before: int = 2
    onion_skin_frames_after: int = 2
    onion_skin_color_before: Tuple[float, float, float, float] = (0.0, 1.0, 0.0, 0.3)
    onion_skin_color_after: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.3)
    use_ghosts_custom_colors: bool = True
    ghost_before_range: int = 5
    ghost_after_range: int = 5
    use_ghost_keyframes: bool = False
    use_onion_skinning_loop: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'frame_start': self.frame_start,
            'frame_end': self.frame_end,
            'frame_rate': self.frame_rate,
            'onion_skin_enabled': self.onion_skin_enabled,
            'onion_skin_frames_before': self.onion_skin_frames_before,
            'onion_skin_frames_after': self.onion_skin_frames_after,
            'onion_skin_color_before': list(self.onion_skin_color_before),
            'onion_skin_color_after': list(self.onion_skin_color_after),
            'use_ghosts_custom_colors': self.use_ghosts_custom_colors,
            'ghost_before_range': self.ghost_before_range,
            'ghost_after_range': self.ghost_after_range,
            'use_ghost_keyframes': self.use_ghost_keyframes,
            'use_onion_skinning_loop': self.use_onion_skinning_loop,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GPAnimationConfig:
        """Deserialize from dictionary."""
        return cls(
            id=data['id'],
            frame_start=data.get('frame_start', 1),
            frame_end=data.get('frame_end', 100),
            frame_rate=data.get('frame_rate', 24.0),
            onion_skin_enabled=data.get('onion_skin_enabled', False),
            onion_skin_frames_before=data.get('onion_skin_frames_before', 2),
            onion_skin_frames_after=data.get('onion_skin_frames_after', 2),
            onion_skin_color_before=tuple(data.get('onion_skin_color_before', (0.0, 1.0, 0.0, 0.3))),
            onion_skin_color_after=tuple(data.get('onion_skin_color_after', (1.0, 0.0, 0.0, 0.3))),
            use_ghosts_custom_colors=data.get('use_ghosts_custom_colors', True),
            ghost_before_range=data.get('ghost_before_range', 5),
            ghost_after_range=data.get('ghost_after_range', 5),
            use_ghost_keyframes=data.get('use_ghost_keyframes', False),
            use_onion_skinning_loop=data.get('use_onion_skinning_loop', False),
        )
