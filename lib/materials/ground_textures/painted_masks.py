"""
Painted Mask Workflow System

Procedural and hand-painted mask generation for ground texture blending.
Supports Blender's texture painting workflow with custom grunge brushes.

Based on Polygon Runway tutorial:
- Painted masks for road markings and dirt placement
- Grunge brushes for natural edge treatment
- Mix color nodes with add/overlay blend modes
- Custom brush creation with noise-based grunge

Usage:
    from lib.materials.ground_textures import (
        GrungeBrush,
        PaintedMaskWorkflow,
        MaskTexture,
        create_grunge_brush,
        generate_road_dirt_mask,
    )

    # Create a grunge brush
    brush = create_grunge_brush("grunge_soft", intensity=0.5)
    workflow = PaintedMaskWorkflow()
    mask = workflow.create_mask_texture("dirt_mask", resolution=2048)
    workflow.apply_grunge_to_mask(mask, brush)
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
import math
import random

try:
    import bpy
    from bpy.types import Brush, Image, Texture, Paint
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Brush = Any
    Image = Any
    Texture = Any
    Paint = Any

# Optional NumPy for vectorized operations (10-50x faster)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


class BrushType(Enum):
    """Types of grunge/decorative brushes."""
    SOFT_GRUNGE = "soft_grunge"
    HARD_EDGE = "hard_edge"
    SCRATCH = "scratch"
    SPATTER = "spatter"
    STREAK = "streak"
    CRACK = "crack"
    NOISE = "noise"
    CUSTOM = "custom"


class BrushBlendMode(Enum):
    """Brush blend modes."""
    MIX = "MIX"
    ADD = "ADD"
    SUBTRACT = "SUB"
    MULTIPLY = "MUL"
    LIGHTEN = "LIGHTEN"
    DARKEN = "DARKEN"
    OVERLAY = "OVERLAY"
    HARD_LIGHT = "HARDLIGHT"
    SOFT_LIGHT = "SOFTLIGHT"
    COLOR_DODGE = "DODGE"
    COLOR_BURN = "BURN"


class MaskEdgeMode(Enum):
    """How mask edges are treated."""
    SOFT = "soft"
    HARD = "hard"
    GRUNGE = "grunge"
    FEATHERED = "feathered"
    CHAOTIC = "chaotic"


@dataclass
class GrungeBrush:
    """
    Custom grunge brush configuration.

    Creates brushes with noise-based grunge overlays
    for natural dirt/wear painting effects.
    """
    name: str
    brush_type: BrushType = BrushType.SOFT_GRUNGE

    # Basic brush settings
    size: float = 50.0
    strength: float = 1.0
    falloff: float = 0.5  # Curve softness

    # Grunge overlay
    grunge_intensity: float = 0.3
    grunge_scale: float = 5.0
    grunge_detail: int = 4
    grunge_seed: int = 0

    # Edge settings
    edge_mode: MaskEdgeMode = MaskEdgeMode.GRUNGE
    edge_chaos: float = 0.2
    edge_softness: float = 0.1

    # Stroke settings
    spacing: float = 0.1
    jitter: float = 0.0
    angle: float = 0.0

    # Texture settings
    use_texture: bool = True
    texture_blend: BrushBlendMode = BrushBlendMode.OVERLAY

    # Color
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    alpha: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "brush_type": self.brush_type.value,
            "size": self.size,
            "strength": self.strength,
            "falloff": self.falloff,
            "grunge_intensity": self.grunge_intensity,
            "grunge_scale": self.grunge_scale,
            "edge_mode": self.edge_mode.value,
            "edge_chaos": self.edge_chaos,
            "color": list(self.color),
            "alpha": self.alpha,
        }


@dataclass
class MaskTexture:
    """
    Texture mask for layer blending.

    Can be procedurally generated or hand-painted.
    """
    name: str
    resolution: Tuple[int, int] = (2048, 2048)
    color_depth: int = 16  # 8, 16, or 32 bit

    # Initial state
    fill_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)

    # Procedural elements
    procedural_layers: List[Dict[str, Any]] = field(default_factory=list)

    # Painted strokes (for recording/playback)
    strokes: List[Dict[str, Any]] = field(default_factory=list)

    # Output
    filepath: Optional[str] = None

    def add_procedural_layer(
        self,
        layer_type: str,
        blend_mode: str = "add",
        **kwargs
    ) -> Dict[str, Any]:
        """Add a procedural layer to the mask."""
        layer = {
            "type": layer_type,
            "blend_mode": blend_mode,
            **kwargs
        }
        self.procedural_layers.append(layer)
        return layer

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "resolution": list(self.resolution),
            "color_depth": self.color_depth,
            "procedural_layers": self.procedural_layers,
            "filepath": self.filepath,
        }


@dataclass
class PaintStroke:
    """
    A recorded paint stroke for mask generation.

    Can be replayed or used for procedural variation.
    """
    points: List[Tuple[float, float, float]]  # (x, y, pressure)
    brush: GrungeBrush
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "points": [list(p) for p in self.points],
            "brush": self.brush.to_dict(),
            "timestamp": self.timestamp,
        }


# =============================================================================
# GRUNGE BRUSH PRESETS
# =============================================================================

GRUNGE_BRUSH_PRESETS: Dict[str, Dict[str, Any]] = {
    "soft_grunge": {
        "brush_type": BrushType.SOFT_GRUNGE,
        "size": 80.0,
        "strength": 0.8,
        "falloff": 0.7,
        "grunge_intensity": 0.3,
        "grunge_scale": 8.0,
        "edge_mode": MaskEdgeMode.SOFT,
    },
    "hard_edge_grunge": {
        "brush_type": BrushType.HARD_EDGE,
        "size": 60.0,
        "strength": 1.0,
        "falloff": 0.2,
        "grunge_intensity": 0.5,
        "grunge_scale": 12.0,
        "edge_mode": MaskEdgeMode.HARD,
        "edge_chaos": 0.3,
    },
    "scratches": {
        "brush_type": BrushType.SCRATCH,
        "size": 30.0,
        "strength": 0.6,
        "falloff": 0.1,
        "grunge_intensity": 0.2,
        "grunge_scale": 20.0,
        "edge_mode": MaskEdgeMode.CHAOTIC,
        "edge_chaos": 0.5,
        "angle": 45.0,
    },
    "dirt_spatter": {
        "brush_type": BrushType.SPATTER,
        "size": 40.0,
        "strength": 0.7,
        "falloff": 0.3,
        "grunge_intensity": 0.6,
        "grunge_scale": 15.0,
        "jitter": 0.8,
        "edge_mode": MaskEdgeMode.CHAOTIC,
    },
    "streaks": {
        "brush_type": BrushType.STREAK,
        "size": 100.0,
        "strength": 0.5,
        "falloff": 0.6,
        "grunge_intensity": 0.4,
        "grunge_scale": 6.0,
        "edge_mode": MaskEdgeMode.FEATHERED,
        "angle": 90.0,
    },
    "cracks": {
        "brush_type": BrushType.CRACK,
        "size": 20.0,
        "strength": 0.9,
        "falloff": 0.05,
        "grunge_intensity": 0.3,
        "grunge_scale": 25.0,
        "edge_mode": MaskEdgeMode.CHAOTIC,
        "edge_chaos": 0.7,
    },
    "noise_fill": {
        "brush_type": BrushType.NOISE,
        "size": 150.0,
        "strength": 0.4,
        "falloff": 0.9,
        "grunge_intensity": 0.8,
        "grunge_scale": 4.0,
        "edge_mode": MaskEdgeMode.SOFT,
    },
}


# =============================================================================
# PAINTED MASK WORKFLOW
# =============================================================================

class PaintedMaskWorkflow:
    """
    Workflow manager for creating and editing painted masks.

    Handles:
    - Creating mask textures
    - Generating procedural mask elements
    - Applying grunge effects
    - Blender texture paint mode integration
    """

    def __init__(self):
        """Initialize the painted mask workflow."""
        self.masks: Dict[str, MaskTexture] = {}
        self.brushes: Dict[str, GrungeBrush] = {}
        self.active_mask: Optional[str] = None

        # Load default brushes
        for name, preset in GRUNGE_BRUSH_PRESETS.items():
            self.create_brush_from_preset(name, name)

    def create_mask_texture(
        self,
        name: str,
        resolution: int = 2048,
        fill_black: bool = True,
    ) -> MaskTexture:
        """
        Create a new mask texture.

        Args:
            name: Mask name
            resolution: Square resolution (e.g., 1024, 2048, 4096)
            fill_black: Fill with black (transparent mask)

        Returns:
            Created MaskTexture
        """
        fill_color = (0.0, 0.0, 0.0, 1.0) if fill_black else (0.5, 0.5, 0.5, 1.0)

        mask = MaskTexture(
            name=name,
            resolution=(resolution, resolution),
            fill_color=fill_color,
        )

        self.masks[name] = mask
        self.active_mask = name
        return mask

    def create_brush_from_preset(
        self,
        name: str,
        preset_name: str,
        **overrides
    ) -> GrungeBrush:
        """
        Create a grunge brush from a preset.

        Args:
            name: Brush name
            preset_name: Preset to use
            **overrides: Parameter overrides

        Returns:
            Created GrungeBrush
        """
        preset = GRUNGE_BRUSH_PRESETS.get(preset_name, {})
        params = {**preset, **overrides}

        brush = GrungeBrush(name=name, **params)
        self.brushes[name] = brush
        return brush

    def add_noise_to_mask(
        self,
        mask: MaskTexture,
        scale: float = 5.0,
        detail: int = 4,
        distortion: float = 0.5,
        intensity: float = 0.5,
        blend_mode: str = "overlay",
        seed: int = 0,
    ) -> MaskTexture:
        """
        Add procedural noise to a mask.

        Args:
            mask: Mask to modify
            scale: Noise scale
            detail: Noise detail level
            distortion: Noise distortion
            intensity: Effect intensity
            blend_mode: How to blend with existing
            seed: Random seed

        Returns:
            Modified mask
        """
        mask.add_procedural_layer(
            layer_type="noise",
            scale=scale,
            detail=detail,
            distortion=distortion,
            intensity=intensity,
            blend_mode=blend_mode,
            seed=seed,
        )
        return mask

    def add_voronoi_to_mask(
        self,
        mask: MaskTexture,
        scale: float = 10.0,
        randomness: float = 0.5,
        edge_width: float = 0.1,
        intensity: float = 0.5,
        blend_mode: str = "add",
        seed: int = 0,
    ) -> MaskTexture:
        """
        Add voronoi cell pattern to a mask.

        Args:
            mask: Mask to modify
            scale: Cell scale
            randomness: Position randomness
            edge_width: Edge line width
            intensity: Effect intensity
            blend_mode: How to blend
            seed: Random seed

        Returns:
            Modified mask
        """
        mask.add_procedural_layer(
            layer_type="voronoi",
            scale=scale,
            randomness=randomness,
            edge_width=edge_width,
            intensity=intensity,
            blend_mode=blend_mode,
            seed=seed,
        )
        return mask

    def add_gradient_to_mask(
        self,
        mask: MaskTexture,
        direction: str = "bottom_to_top",
        intensity: float = 1.0,
        blend_mode: str = "multiply",
    ) -> MaskTexture:
        """
        Add a directional gradient to a mask.

        Args:
            mask: Mask to modify
            direction: Gradient direction
            intensity: Effect intensity
            blend_mode: How to blend

        Returns:
            Modified mask
        """
        mask.add_procedural_layer(
            layer_type="gradient",
            direction=direction,
            intensity=intensity,
            blend_mode=blend_mode,
        )
        return mask

    def add_edge_wear_to_mask(
        self,
        mask: MaskTexture,
        edge_width: float = 0.1,
        chaos: float = 0.3,
        intensity: float = 0.8,
        blend_mode: str = "add",
    ) -> MaskTexture:
        """
        Add edge wear pattern to mask.

        Simulates natural wear at edges.

        Args:
            mask: Mask to modify
            edge_width: Width of edge wear
            chaos: Edge chaos/jaggedness
            intensity: Effect intensity
            blend_mode: How to blend

        Returns:
            Modified mask
        """
        mask.add_procedural_layer(
            layer_type="edge_wear",
            edge_width=edge_width,
            chaos=chaos,
            intensity=intensity,
            blend_mode=blend_mode,
        )
        return mask

    def apply_grunge_to_mask(
        self,
        mask: MaskTexture,
        brush: GrungeBrush,
        strokes: Optional[List[PaintStroke]] = None,
    ) -> MaskTexture:
        """
        Apply grunge brush strokes to a mask.

        Args:
            mask: Mask to modify
            brush: Grunge brush to use
            strokes: Optional pre-recorded strokes

        Returns:
            Modified mask
        """
        # Add grunge layer based on brush settings
        mask.add_procedural_layer(
            layer_type="grunge",
            grunge_intensity=brush.grunge_intensity,
            grunge_scale=brush.grunge_scale,
            grunge_detail=brush.grunge_detail,
            grunge_seed=brush.grunge_seed,
            edge_mode=brush.edge_mode.value,
            edge_chaos=brush.edge_chaos,
            blend_mode="overlay",
        )

        return mask

    def generate_road_dirt_mask(
        self,
        mask_name: str = "road_dirt_mask",
        resolution: int = 2048,
        edge_intensity: float = 0.4,
        center_fade: float = 0.2,
        grunge_amount: float = 0.3,
        seed: int = 0,
    ) -> MaskTexture:
        """
        Generate a procedural road dirt mask.

        Creates a realistic dirt distribution pattern for roads
        with edge accumulation and center fade.

        Args:
            mask_name: Name for the mask
            resolution: Mask resolution
            edge_intensity: Dirt intensity at edges
            center_fade: How much dirt fades toward center
            grunge_amount: Amount of grunge/chaos
            seed: Random seed

        Returns:
            Generated MaskTexture
        """
        mask = self.create_mask_texture(mask_name, resolution)

        # Add edge wear (dirt accumulates at edges)
        self.add_edge_wear_to_mask(
            mask,
            edge_width=0.15,
            chaos=grunge_amount * 0.5,
            intensity=edge_intensity,
            blend_mode="add",
        )

        # Add base noise for variation
        self.add_noise_to_mask(
            mask,
            scale=8.0,
            detail=3,
            intensity=grunge_amount,
            blend_mode="overlay",
            seed=seed,
        )

        # Add gradient from center (less dirt in tire track area)
        self.add_gradient_to_mask(
            mask,
            direction="center_to_edges",
            intensity=center_fade,
            blend_mode="multiply",
        )

        # Add fine grunge detail
        self.add_noise_to_mask(
            mask,
            scale=25.0,
            detail=5,
            distortion=0.3,
            intensity=grunge_amount * 0.5,
            blend_mode="overlay",
            seed=seed + 1,
        )

        return mask

    def generate_road_marking_mask(
        self,
        mask_name: str = "road_marking_mask",
        resolution: int = 2048,
        marking_type: str = "line",
        wear: float = 0.2,
        grunge_edges: bool = True,
        seed: int = 0,
    ) -> MaskTexture:
        """
        Generate a mask for road markings/paint.

        Args:
            mask_name: Name for the mask
            resolution: Mask resolution
            marking_type: "line", "crosswalk", "arrow", "symbol"
            wear: Amount of wear on paint (0-1)
            grunge_edges: Add grunge to edges
            seed: Random seed

        Returns:
            Generated MaskTexture
        """
        mask = self.create_mask_texture(mask_name, resolution, fill_black=True)

        # Base shape layer (would be painted)
        mask.add_procedural_layer(
            layer_type="shape",
            shape_type=marking_type,
            intensity=1.0 - wear * 0.3,
            blend_mode="add",
        )

        # Add wear
        if wear > 0:
            self.add_noise_to_mask(
                mask,
                scale=15.0,
                detail=4,
                intensity=wear,
                blend_mode="multiply",
                seed=seed,
            )

        # Grunge the edges
        if grunge_edges:
            self.add_edge_wear_to_mask(
                mask,
                edge_width=0.05,
                chaos=0.4,
                intensity=wear * 0.5,
                blend_mode="multiply",
            )

        return mask

    def create_blender_mask_image(
        self,
        mask: MaskTexture,
        generate_pixels: bool = True,
    ) -> Optional[Image]:
        """
        Create a Blender image from a MaskTexture.

        Args:
            mask: MaskTexture to convert
            generate_pixels: Generate procedural pixels

        Returns:
            Blender Image or None if not in Blender
        """
        if not BLENDER_AVAILABLE:
            return None

        width, height = mask.resolution

        # Create image
        image = bpy.data.images.new(
            mask.name,
            width=width,
            height=height,
            alpha=True,
            float_buffer=(mask.color_depth > 8),
        )

        if generate_pixels:
            # Generate procedural pixels using fast NumPy method if available
            pixels = self._generate_mask_pixels_fast(mask)
            image.pixels = pixels

        return image

    def _generate_mask_pixels(self, mask: MaskTexture) -> List[float]:
        """Generate pixel data for a mask."""
        width, height = mask.resolution
        pixels = []

        for y in range(height):
            for x in range(width):
                # Base color
                value = mask.fill_color[0]

                # Apply procedural layers
                for layer in mask.procedural_layers:
                    layer_value = self._evaluate_procedural_layer(
                        layer, x / width, y / height
                    )

                    blend = layer.get("blend_mode", "add")
                    intensity = layer.get("intensity", 1.0)
                    layer_value *= intensity

                    if blend == "add":
                        value = min(1.0, value + layer_value)
                    elif blend == "multiply":
                        value *= layer_value
                    elif blend == "overlay":
                        if value < 0.5:
                            value = 2 * value * layer_value
                        else:
                            value = 1 - 2 * (1 - value) * (1 - layer_value)
                    elif blend == "subtract":
                        value = max(0.0, value - layer_value)

                # RGBA
                pixels.extend([value, value, value, 1.0])

        return pixels

    def _generate_mask_pixels_fast(self, mask: MaskTexture) -> List[float]:
        """
        Generate pixel data for a mask using NumPy vectorization.

        This is 10-50x faster than _generate_mask_pixels() for large masks.
        Falls back to the slow method if NumPy is not available.

        Args:
            mask: MaskTexture to generate pixels for

        Returns:
            Flat list of RGBA values (4 floats per pixel)
        """
        if not NUMPY_AVAILABLE:
            return self._generate_mask_pixels(mask)

        width, height = mask.resolution

        # Create UV coordinate grids
        u = np.linspace(0, 1, width, dtype=np.float32)
        v = np.linspace(0, 1, height, dtype=np.float32)
        uu, vv = np.meshgrid(u, v)

        # Start with base fill color
        result = np.full((height, width), mask.fill_color[0], dtype=np.float32)

        # Apply each procedural layer
        for layer in mask.procedural_layers:
            layer_values = self._evaluate_layer_vectorized(layer, uu, vv)
            intensity = layer.get("intensity", 1.0)
            layer_values = layer_values * intensity
            blend = layer.get("blend_mode", "add")

            if blend == "add":
                result = np.minimum(1.0, result + layer_values)
            elif blend == "multiply":
                result = result * layer_values
            elif blend == "overlay":
                # Vectorized overlay blend
                overlay = np.where(
                    result < 0.5,
                    2 * result * layer_values,
                    1 - 2 * (1 - result) * (1 - layer_values)
                )
                result = overlay
            elif blend == "subtract":
                result = np.maximum(0.0, result - layer_values)

        # Convert to RGBA flat list for Blender
        ones = np.ones_like(result)
        rgba = np.stack([result, result, result, ones], axis=-1)
        return rgba.flatten().tolist()

    def _evaluate_layer_vectorized(
        self,
        layer: Dict[str, Any],
        uu: "np.ndarray",
        vv: "np.ndarray",
    ) -> "np.ndarray":
        """
        Evaluate a procedural layer for entire UV grid using NumPy.

        Args:
            layer: Layer configuration dictionary
            uu: 2D array of U coordinates (from meshgrid)
            vv: 2D array of V coordinates (from meshgrid)

        Returns:
            2D array of layer values
        """
        import numpy as np

        layer_type = layer.get("type", "noise")
        seed = layer.get("seed", 0)

        if layer_type == "noise":
            scale = layer.get("scale", 5.0)
            detail = layer.get("detail", 4)

            # Multi-octave Perlin-like noise approximation
            result = np.zeros_like(uu)
            amplitude = 1.0
            frequency = scale
            max_value = 0.0

            for octave in range(min(detail, 8)):
                # Create deterministic pseudo-random values for this octave
                np.random.seed(seed + octave * 1000)
                noise = np.random.random(uu.shape)
                # Apply frequency-based sampling
                idx_u = ((uu * frequency * 100) % uu.shape[1]).astype(int)
                idx_v = ((vv * frequency * 100) % uu.shape[0]).astype(int)
                result += noise[idx_v, idx_u] * amplitude
                max_value += amplitude
                amplitude *= 0.5
                frequency *= 2

            return result / max_value if max_value > 0 else np.full_like(uu, 0.5)

        elif layer_type == "voronoi":
            scale = layer.get("scale", 10.0)
            # Simplified voronoi using cell indices
            cell_x = (uu * scale).astype(int)
            cell_y = (vv * scale).astype(int)
            # Create pseudo-random values per cell
            np.random.seed(seed)
            cell_values = np.random.random((int(scale) + 2, int(scale) + 2))
            return cell_values[cell_y % (int(scale) + 1), cell_x % (int(scale) + 1)]

        elif layer_type == "gradient":
            direction = layer.get("direction", "bottom_to_top")
            if direction == "bottom_to_top":
                return vv.copy()
            elif direction == "top_to_bottom":
                return 1 - vv
            elif direction == "left_to_right":
                return uu.copy()
            elif direction == "right_to_left":
                return 1 - uu
            elif direction == "center_to_edges":
                cx, cy = 0.5, 0.5
                dist = np.sqrt((uu - cx) ** 2 + (vv - cy) ** 2)
                return np.minimum(1.0, dist * 2)
            return np.full_like(uu, 0.5)

        elif layer_type == "edge_wear":
            edge_width = layer.get("edge_width", 0.1)
            chaos = layer.get("chaos", 0.3)

            # Distance to nearest edge (vectorized)
            edge_dist = np.minimum(np.minimum(uu, 1 - uu), np.minimum(vv, 1 - vv))
            edge_factor = 1 - np.minimum(1.0, edge_dist / edge_width)

            # Add chaos
            np.random.seed(seed)
            chaos_values = np.random.random(uu.shape) * chaos

            return edge_factor * (1 - chaos + chaos_values)

        elif layer_type == "grunge":
            intensity = layer.get("grunge_intensity", 0.3)
            scale = layer.get("grunge_scale", 5.0)

            np.random.seed(int(seed))
            return np.random.random(uu.shape) * intensity

        return np.zeros_like(uu)

    def _evaluate_procedural_layer(
        self,
        layer: Dict[str, Any],
        u: float,
        v: float,
    ) -> float:
        """Evaluate a procedural layer at UV coordinates."""
        layer_type = layer.get("type", "noise")
        seed = layer.get("seed", 0)

        # Simple noise approximation
        import random
        random.seed(int(u * 10000 + v * 100 + seed))

        if layer_type == "noise":
            scale = layer.get("scale", 5.0)
            detail = layer.get("detail", 4)

            # Multi-octave noise approximation
            value = 0.0
            amplitude = 1.0
            frequency = scale
            max_value = 0.0

            for _ in range(min(detail, 8)):
                random.seed(int(u * frequency * 100 + v * frequency + seed))
                value += random.random() * amplitude
                max_value += amplitude
                amplitude *= 0.5
                frequency *= 2

            return value / max_value if max_value > 0 else 0.5

        elif layer_type == "voronoi":
            scale = layer.get("scale", 10.0)
            # Simplified voronoi - returns distance-like value
            cell_x = int(u * scale)
            cell_y = int(v * scale)
            random.seed(cell_x * 1000 + cell_y + seed)
            return random.random()

        elif layer_type == "gradient":
            direction = layer.get("direction", "bottom_to_top")
            if direction == "bottom_to_top":
                return v
            elif direction == "top_to_bottom":
                return 1 - v
            elif direction == "left_to_right":
                return u
            elif direction == "right_to_left":
                return 1 - u
            elif direction == "center_to_edges":
                cx, cy = 0.5, 0.5
                dist = math.sqrt((u - cx) ** 2 + (v - cy) ** 2)
                return min(1.0, dist * 2)
            return 0.5

        elif layer_type == "edge_wear":
            edge_width = layer.get("edge_width", 0.1)
            chaos = layer.get("chaos", 0.3)

            # Distance to nearest edge
            edge_dist = min(u, 1 - u, v, 1 - v)
            edge_factor = 1 - min(1.0, edge_dist / edge_width)

            # Add chaos
            random.seed(int(u * 1000 + v * 1000 + seed))
            chaos_value = random.random() * chaos

            return edge_factor * (1 - chaos + chaos_value)

        elif layer_type == "grunge":
            intensity = layer.get("grunge_intensity", 0.3)
            scale = layer.get("grunge_scale", 5.0)

            random.seed(int(u * scale * 100 + v * scale + seed))
            return random.random() * intensity

        return 0.0

    def export_mask(
        self,
        mask: MaskTexture,
        filepath: str,
        format: str = "PNG",
    ) -> bool:
        """
        Export mask to image file.

        Args:
            mask: MaskTexture to export
            filepath: Output path
            format: Image format (PNG, EXR, TIFF)

        Returns:
            True if successful
        """
        if BLENDER_AVAILABLE:
            image = self.create_blender_mask_image(mask)
            if image:
                image.filepath_raw = filepath
                image.file_format = format
                image.save()
                return True
        return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_grunge_brush(
    name: str,
    intensity: float = 0.5,
    scale: float = 5.0,
    edge_chaos: float = 0.3,
    preset: str = "soft_grunge",
) -> GrungeBrush:
    """
    Create a grunge brush with common settings.

    Args:
        name: Brush name
        intensity: Grunge intensity (0-1)
        scale: Grunge pattern scale
        edge_chaos: Edge chaos amount (0-1)
        preset: Base preset to use

    Returns:
        Configured GrungeBrush
    """
    workflow = PaintedMaskWorkflow()
    return workflow.create_brush_from_preset(
        name,
        preset,
        grunge_intensity=intensity,
        grunge_scale=scale,
        edge_chaos=edge_chaos,
    )


def generate_road_dirt_mask(
    resolution: int = 2048,
    dirt_amount: float = 0.4,
    seed: int = 0,
) -> MaskTexture:
    """
    Generate a road dirt mask with default settings.

    Args:
        resolution: Mask resolution
        dirt_amount: Overall dirt amount (0-1)
        seed: Random seed

    Returns:
        Generated MaskTexture
    """
    workflow = PaintedMaskWorkflow()
    return workflow.generate_road_dirt_mask(
        resolution=resolution,
        edge_intensity=dirt_amount,
        grunge_amount=dirt_amount * 0.7,
        seed=seed,
    )


def create_wear_mask(
    resolution: int = 2048,
    wear_pattern: str = "edge",
    intensity: float = 0.5,
) -> MaskTexture:
    """
    Create a wear/damage mask.

    Args:
        resolution: Mask resolution
        wear_pattern: "edge", "scratch", "spot", "combined"
        intensity: Wear intensity (0-1)

    Returns:
        Generated MaskTexture
    """
    workflow = PaintedMaskWorkflow()
    mask = workflow.create_mask_texture(f"wear_{wear_pattern}", resolution)

    if wear_pattern == "edge" or wear_pattern == "combined":
        workflow.add_edge_wear_to_mask(
            mask,
            edge_width=0.1,
            chaos=0.4,
            intensity=intensity,
        )

    if wear_pattern == "scratch" or wear_pattern == "combined":
        brush = create_grunge_brush("scratch_brush", preset="scratches")
        workflow.apply_grunge_to_mask(mask, brush)

    if wear_pattern == "spot" or wear_pattern == "combined":
        workflow.add_voronoi_to_mask(
            mask,
            scale=20.0,
            randomness=0.8,
            intensity=intensity * 0.5,
        )

    return mask


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "BrushType",
    "BrushBlendMode",
    "MaskEdgeMode",
    # Dataclasses
    "GrungeBrush",
    "MaskTexture",
    "PaintStroke",
    # Manager
    "PaintedMaskWorkflow",
    # Presets
    "GRUNGE_BRUSH_PRESETS",
    # Functions
    "create_grunge_brush",
    "generate_road_dirt_mask",
    "create_wear_mask",
]
