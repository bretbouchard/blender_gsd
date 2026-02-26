"""
Color System (Phase 20.8)

Generates color patterns and material assignments for the creature.

Universal Stage Order:
- Stage 0: Normalize (parameter validation)
- Stage 1: Primary (base color assignment)
- Stage 2: Secondary (pattern generation)
- Stage 3: Detail (iridescence, highlights)
- Stage 4: Output Prep (vertex colors, UV regions)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Dict
import numpy as np


class ColorPattern(Enum):
    """Color pattern types for creature coloring."""
    SOLID = 0           # Single solid color
    GRADIENT = 1        # Smooth gradient along body
    STRIPED = 2         # Stripes along body
    SPOTTED = 3         # Spots/rosettes
    MOTTLED = 4         # Irregular mottled pattern
    IRIDESCENT = 5      # Iridescent shimmer
    TWO_TONE = 6        # Two-tone (dorsal/ventral)
    SCALED = 7          # Scale-like pattern


class ColorRegion(Enum):
    """Body regions for color assignment."""
    HEAD = 0
    NECK = 1
    BODY_DORSAL = 2     # Top of body
    BODY_VENTRAL = 3    # Bottom of body
    TAIL = 4
    WINGS = 5
    LIMBS = 6
    CREST = 7
    FEATHERS = 8


@dataclass
class ColorDefinition:
    """Defines a color with optional variation."""
    base_color: np.ndarray          # RGB (0-1)
    variation: float = 0.0          # Amount of random variation
    secondary_color: Optional[np.ndarray] = None  # For patterns

    def __post_init__(self):
        """Ensure colors are numpy arrays."""
        if not isinstance(self.base_color, np.ndarray):
            self.base_color = np.array(self.base_color)
        if self.secondary_color is not None and not isinstance(self.secondary_color, np.ndarray):
            self.secondary_color = np.array(self.secondary_color)


@dataclass
class ColorRegionConfig:
    """Color configuration for a body region."""
    region: ColorRegion
    color_def: ColorDefinition
    pattern: ColorPattern = ColorPattern.SOLID
    pattern_scale: float = 1.0
    blend_with_neighbor: float = 0.0  # How much to blend with adjacent regions


@dataclass
class IridescenceConfig:
    """Configuration for iridescent shimmer effect."""
    enabled: bool = False
    base_shift: float = 0.0      # Base hue shift (0-1)
    shift_amount: float = 0.3    # Amount of hue shift
    frequency: float = 1.0       # Frequency of shimmer
    view_dependent: bool = True  # Shift based on viewing angle


@dataclass
class ColorSystemConfig:
    """Complete color system configuration."""
    pattern: ColorPattern = ColorPattern.TWO_TONE
    primary_color: np.ndarray = field(default_factory=lambda: np.array([0.1, 0.4, 0.2]))  # Green
    secondary_color: np.ndarray = field(default_factory=lambda: np.array([0.9, 0.85, 0.2]))  # Gold
    accent_color: np.ndarray = field(default_factory=lambda: np.array([0.8, 0.2, 0.1]))  # Red
    belly_color: np.ndarray = field(default_factory=lambda: np.array([0.9, 0.9, 0.85]))  # Cream
    pattern_scale: float = 1.0
    pattern_contrast: float = 0.5
    color_variation: float = 0.1
    iridescence: IridescenceConfig = field(default_factory=IridescenceConfig)
    region_configs: Dict[ColorRegion, ColorRegionConfig] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure colors are numpy arrays."""
        for attr in ['primary_color', 'secondary_color', 'accent_color', 'belly_color']:
            val = getattr(self, attr)
            if not isinstance(val, np.ndarray):
                setattr(self, attr, np.array(val))


@dataclass
class VertexColorResult:
    """Result from color system generation."""
    vertex_colors: np.ndarray     # Per-vertex RGB colors (N, 3)
    color_regions: np.ndarray     # Region index per vertex (N,)
    pattern_mask: np.ndarray      # Pattern value per vertex (N,) 0-1
    iridescence_values: np.ndarray  # Iridescence shift per vertex (N,)

    @property
    def vertex_count(self) -> int:
        return len(self.vertex_colors)


class ColorSystem:
    """Generates colors and patterns for the creature."""

    def __init__(self, config: ColorSystemConfig):
        """Initialize color system.

        Args:
            config: Color system configuration
        """
        self.config = config

    def generate(
        self,
        vertices: np.ndarray,
        body_regions: Optional[np.ndarray] = None,
        spine_positions: Optional[np.ndarray] = None,
        radial_angles: Optional[np.ndarray] = None,
        seed: Optional[int] = None,
    ) -> VertexColorResult:
        """Generate vertex colors.

        Args:
            vertices: Vertex positions (N, 3)
            body_regions: Body region index per vertex
            spine_positions: Position along spine (0-1) per vertex
            radial_angles: Radial angle around body per vertex
            seed: Random seed

        Returns:
            VertexColorResult with colors and pattern data
        """
        if seed is not None:
            np.random.seed(seed)

        n_vertices = len(vertices)
        if n_vertices == 0:
            return VertexColorResult(
                vertex_colors=np.zeros((0, 3)),
                color_regions=np.zeros(0, dtype=int),
                pattern_mask=np.zeros(0),
                iridescence_values=np.zeros(0),
            )

        # Default values
        if body_regions is None:
            body_regions = np.zeros(n_vertices, dtype=int)
        if spine_positions is None:
            spine_positions = vertices[:, 1]  # Use Y as spine position
            if spine_positions.max() > spine_positions.min():
                spine_positions = (spine_positions - spine_positions.min()) / (
                    spine_positions.max() - spine_positions.min()
                )
            else:
                spine_positions = np.zeros(n_vertices)
        if radial_angles is None:
            radial_angles = np.arctan2(vertices[:, 2], vertices[:, 0])

        # Generate base colors
        base_colors = self._generate_base_colors(
            vertices, body_regions, spine_positions, radial_angles
        )

        # Apply pattern
        pattern_mask = self._generate_pattern(
            vertices, spine_positions, radial_angles
        )

        # Blend pattern colors
        colors = self._apply_pattern(
            base_colors, pattern_mask, spine_positions, radial_angles
        )

        # Apply variation
        colors = self._apply_variation(colors)

        # Generate iridescence values
        iridescence_values = self._generate_iridescence(
            vertices, spine_positions, radial_angles
        )

        return VertexColorResult(
            vertex_colors=colors,
            color_regions=body_regions,
            pattern_mask=pattern_mask,
            iridescence_values=iridescence_values,
        )

    def _generate_base_colors(
        self,
        vertices: np.ndarray,
        body_regions: np.ndarray,
        spine_positions: np.ndarray,
        radial_angles: np.ndarray,
    ) -> np.ndarray:
        """Generate base colors based on position and region."""
        n = len(vertices)
        colors = np.zeros((n, 3))

        for i in range(n):
            region = body_regions[i] if i < len(body_regions) else 0
            angle = radial_angles[i]
            spine_pos = spine_positions[i]

            # Determine color based on region and position
            region_enum = ColorRegion(region % len(ColorRegion))

            if region_enum in [ColorRegion.BODY_VENTRAL]:
                # Belly is lighter
                colors[i] = self.config.belly_color
            elif region_enum == ColorRegion.HEAD:
                # Head uses primary with slight accent
                colors[i] = self.config.primary_color * 0.9 + self.config.accent_color * 0.1
            elif region_enum == ColorRegion.CREST:
                # Crest uses accent
                colors[i] = self.config.accent_color
            elif region_enum == ColorRegion.WINGS:
                # Wings blend primary and secondary
                colors[i] = self.config.primary_color * 0.5 + self.config.secondary_color * 0.5
            elif region_enum == ColorRegion.FEATHERS:
                # Feathers are iridescent
                colors[i] = self.config.secondary_color
            else:
                # Body regions - dorsal vs ventral based on angle
                if angle > np.pi * 0.25 and angle < np.pi * 0.75:
                    # Bottom half - ventral
                    t = (angle - np.pi * 0.25) / (np.pi * 0.5)
                    colors[i] = (
                        self.config.primary_color * (1 - t) +
                        self.config.belly_color * t
                    )
                else:
                    # Top half - dorsal
                    colors[i] = self.config.primary_color

        return colors

    def _generate_pattern(
        self,
        vertices: np.ndarray,
        spine_positions: np.ndarray,
        radial_angles: np.ndarray,
    ) -> np.ndarray:
        """Generate pattern mask (0-1 values)."""
        n = len(vertices)
        pattern = np.zeros(n)

        if self.config.pattern == ColorPattern.SOLID:
            pattern.fill(0.5)

        elif self.config.pattern == ColorPattern.GRADIENT:
            # Gradient along spine
            pattern = spine_positions.copy()

        elif self.config.pattern == ColorPattern.STRIPED:
            # Stripes along body
            frequency = 3.0 * self.config.pattern_scale
            pattern = (np.sin(spine_positions * frequency * np.pi * 2) + 1) / 2

        elif self.config.pattern == ColorPattern.SPOTTED:
            # Spots based on 3D noise
            frequency = 5.0 * self.config.pattern_scale
            noise_x = np.sin(vertices[:, 0] * frequency)
            noise_y = np.sin(vertices[:, 1] * frequency * 1.5)
            noise_z = np.sin(vertices[:, 2] * frequency * 0.8)
            pattern = (noise_x + noise_y + noise_z + 3) / 6

        elif self.config.pattern == ColorPattern.MOTTLED:
            # Irregular mottled pattern
            frequency = 8.0 * self.config.pattern_scale
            noise = (
                np.sin(vertices[:, 0] * frequency) *
                np.sin(vertices[:, 1] * frequency * 1.3) *
                np.sin(vertices[:, 2] * frequency * 0.9)
            )
            pattern = (noise + 1) / 2

        elif self.config.pattern == ColorPattern.IRIDESCENT:
            # Pattern based on viewing angle simulation
            pattern = (np.sin(radial_angles * 3) + 1) / 2

        elif self.config.pattern == ColorPattern.TWO_TONE:
            # Two-tone based on dorsal/ventral
            pattern = np.where(
                (radial_angles > np.pi * 0.25) & (radial_angles < np.pi * 0.75),
                0.0, 1.0
            ).astype(float)

        elif self.config.pattern == ColorPattern.SCALED:
            # Scale-like pattern
            frequency = 10.0 * self.config.pattern_scale
            scale_x = np.mod(vertices[:, 0] * frequency, 1)
            scale_y = np.mod(spine_positions * frequency * 5, 1)
            pattern = scale_x * scale_y

        else:
            pattern.fill(0.5)

        return np.clip(pattern, 0, 1)

    def _apply_pattern(
        self,
        base_colors: np.ndarray,
        pattern_mask: np.ndarray,
        spine_positions: np.ndarray,
        radial_angles: np.ndarray,
    ) -> np.ndarray:
        """Apply pattern to blend colors."""
        n = len(base_colors)
        colors = base_colors.copy()

        contrast = self.config.pattern_contrast

        for i in range(n):
            p = pattern_mask[i]

            # Blend between primary and secondary based on pattern
            if self.config.pattern in [ColorPattern.TWO_TONE, ColorPattern.GRADIENT]:
                # Use pattern to blend between dorsal and ventral
                if p > 0.5:
                    colors[i] = self.config.primary_color
                else:
                    blend = (0.5 - p) * 2 * contrast
                    colors[i] = (
                        base_colors[i] * (1 - blend) +
                        self.config.belly_color * blend
                    )
            else:
                # Use pattern to blend between primary and secondary
                blend = p * contrast
                colors[i] = (
                    base_colors[i] * (1 - blend) +
                    self.config.secondary_color * blend
                )

        return colors

    def _apply_variation(self, colors: np.ndarray) -> np.ndarray:
        """Apply random color variation."""
        if self.config.color_variation <= 0:
            return colors

        variation = np.random.uniform(
            -self.config.color_variation,
            self.config.color_variation,
            colors.shape
        )

        return np.clip(colors + variation, 0, 1)

    def _generate_iridescence(
        self,
        vertices: np.ndarray,
        spine_positions: np.ndarray,
        radial_angles: np.ndarray,
    ) -> np.ndarray:
        """Generate iridescence values for shader."""
        n = len(vertices)
        irid = np.zeros(n)

        if not self.config.iridescence.enabled:
            return irid

        # Iridescence based on viewing angle simulation
        base = self.config.iridescence.base_shift
        amount = self.config.iridescence.shift_amount
        freq = self.config.iridescence.frequency

        if self.config.iridescence.view_dependent:
            # Simulate view-dependent shift
            irid = base + amount * np.sin(radial_angles * freq)
        else:
            # Position-based shift
            irid = base + amount * np.sin(spine_positions * freq * np.pi * 2)

        return np.clip(irid, 0, 1)


def generate_colors(
    vertices: np.ndarray,
    pattern: ColorPattern = ColorPattern.TWO_TONE,
    primary_color: Tuple[float, float, float] = (0.1, 0.4, 0.2),
    secondary_color: Tuple[float, float, float] = (0.9, 0.85, 0.2),
    belly_color: Tuple[float, float, float] = (0.9, 0.9, 0.85),
    body_regions: Optional[np.ndarray] = None,
    spine_positions: Optional[np.ndarray] = None,
    radial_angles: Optional[np.ndarray] = None,
    seed: Optional[int] = None,
) -> VertexColorResult:
    """Generate vertex colors with simplified interface.

    Args:
        vertices: Vertex positions (N, 3)
        pattern: Color pattern type
        primary_color: Primary RGB color (0-1)
        secondary_color: Secondary RGB color (0-1)
        belly_color: Belly RGB color (0-1)
        body_regions: Body region per vertex
        spine_positions: Position along spine per vertex
        radial_angles: Radial angle per vertex
        seed: Random seed

    Returns:
        VertexColorResult with colors
    """
    config = ColorSystemConfig(
        pattern=pattern,
        primary_color=np.array(primary_color),
        secondary_color=np.array(secondary_color),
        belly_color=np.array(belly_color),
    )

    system = ColorSystem(config)
    return system.generate(
        vertices, body_regions, spine_positions, radial_angles, seed
    )


# Preset color schemes
COLOR_PRESETS = {
    "quetzalcoatl": {
        "primary": (0.1, 0.5, 0.2),      # Emerald green
        "secondary": (0.1, 0.7, 0.9),    # Cyan
        "accent": (0.9, 0.85, 0.2),      # Gold
        "belly": (0.95, 0.95, 0.9),      # Cream
        "pattern": ColorPattern.IRIDESCENT,
    },
    "dragon_red": {
        "primary": (0.6, 0.1, 0.1),      # Deep red
        "secondary": (0.9, 0.3, 0.1),    # Orange
        "accent": (0.1, 0.1, 0.1),       # Black
        "belly": (0.9, 0.7, 0.5),        # Tan
        "pattern": ColorPattern.MOTTLED,
    },
    "serpent_green": {
        "primary": (0.15, 0.35, 0.15),   # Dark green
        "secondary": (0.2, 0.5, 0.2),    # Light green
        "accent": (0.8, 0.6, 0.1),       # Yellow
        "belly": (0.85, 0.9, 0.7),       # Pale green
        "pattern": ColorPattern.STRIPED,
    },
    "ghost_white": {
        "primary": (0.9, 0.9, 0.95),     # White
        "secondary": (0.7, 0.75, 0.9),   # Light blue
        "accent": (0.5, 0.5, 0.6),       # Gray
        "belly": (0.95, 0.95, 1.0),      # Pure white
        "pattern": ColorPattern.SOLID,
    },
    "wyvern_brown": {
        "primary": (0.4, 0.3, 0.2),      # Brown
        "secondary": (0.5, 0.4, 0.3),    # Light brown
        "accent": (0.2, 0.15, 0.1),      # Dark brown
        "belly": (0.7, 0.6, 0.5),        # Tan
        "pattern": ColorPattern.SCALED,
    },
}


def get_color_preset(name: str) -> Dict:
    """Get a color preset by name.

    Args:
        name: Preset name

    Returns:
        Dictionary with color preset values
    """
    return COLOR_PRESETS.get(name, COLOR_PRESETS["quetzalcoatl"])


def create_config_from_preset(name: str) -> ColorSystemConfig:
    """Create a ColorSystemConfig from a preset.

    Args:
        name: Preset name

    Returns:
        ColorSystemConfig with preset values
    """
    preset = get_color_preset(name)
    return ColorSystemConfig(
        pattern=preset["pattern"],
        primary_color=np.array(preset["primary"]),
        secondary_color=np.array(preset["secondary"]),
        accent_color=np.array(preset["accent"]),
        belly_color=np.array(preset["belly"]),
    )
