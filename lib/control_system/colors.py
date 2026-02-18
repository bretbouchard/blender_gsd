"""
Control System Color System

Implements semantic color tokens and color manipulation utilities for control surfaces.

Features:
- Semantic color tokens (primary, secondary, indicator, etc.)
- State colors (on, off, active, warning)
- Gradient support
- LAB color space interpolation for perceptually uniform gradients
"""

from __future__ import annotations
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass
import math


# Type aliases
RGB = Tuple[float, float, float]
RGBA = Tuple[float, float, float, float]


@dataclass
class ColorToken:
    """
    Semantic color token with metadata.

    Attributes:
        name: Semantic name (e.g., "primary", "indicator_on")
        rgb: RGB values (0-1 range)
        description: Human-readable description
        tags: Optional tags for categorization
    """
    name: str
    rgb: RGB
    description: str = ""
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_rgba(self, alpha: float = 1.0) -> RGBA:
        """Convert to RGBA with given alpha."""
        return (*self.rgb, alpha)


class ColorSystem:
    """
    Manages color tokens and provides color manipulation utilities.
    """

    def __init__(self, tokens: Optional[Dict[str, ColorToken]] = None):
        """
        Initialize color system.

        Args:
            tokens: Dictionary of color tokens (name -> ColorToken)
        """
        self.tokens = tokens or {}

    def get_token(self, name: str) -> Optional[ColorToken]:
        """
        Get a color token by name.

        Args:
            name: Token name

        Returns:
            ColorToken if found, None otherwise
        """
        return self.tokens.get(name)

    def get_rgb(self, name: str) -> Optional[RGB]:
        """
        Get RGB values for a token.

        Args:
            name: Token name

        Returns:
            RGB tuple if found, None otherwise
        """
        token = self.get_token(name)
        return token.rgb if token else None

    def register_token(self, token: ColorToken) -> None:
        """
        Register a new color token.

        Args:
            token: ColorToken to register
        """
        self.tokens[token.name] = token

    @staticmethod
    def rgb_to_lab(rgb: RGB) -> Tuple[float, float, float]:
        """
        Convert RGB to LAB color space.

        Args:
            rgb: RGB values (0-1 range)

        Returns:
            LAB values (L: 0-100, a: -128 to 127, b: -128 to 127)
        """
        # RGB to XYZ
        r, g, b = rgb

        # Linearize
        r = r / 12.92 if r <= 0.04045 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.04045 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.04045 else ((b + 0.055) / 1.055) ** 2.4

        # RGB to XYZ matrix (sRGB D65)
        x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
        y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
        z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

        # Normalize for D65 illuminant
        x /= 0.95047
        y /= 1.00000
        z /= 1.08883

        # XYZ to LAB
        def f(t):
            return t ** (1/3) if t > 0.008856 else 7.787 * t + 16/116

        fx, fy, fz = f(x), f(y), f(z)

        L = (116 * fy) - 16
        a = 500 * (fx - fy)
        b_val = 200 * (fy - fz)

        return (L, a, b_val)

    @staticmethod
    def lab_to_rgb(lab: Tuple[float, float, float]) -> RGB:
        """
        Convert LAB to RGB color space.

        Args:
            lab: LAB values (L: 0-100, a: -128 to 127, b: -128 to 127)

        Returns:
            RGB values (0-1 range)
        """
        L, a, b_val = lab

        # LAB to XYZ
        fy = (L + 16) / 116
        fx = a / 500 + fy
        fz = fy - b_val / 200

        def f_inv(t):
            t3 = t ** 3
            return t3 if t3 > 0.008856 else (t - 16/116) / 7.787

        x = f_inv(fx) * 0.95047
        y = f_inv(fy) * 1.00000
        z = f_inv(fz) * 1.08883

        # XYZ to RGB matrix (sRGB D65)
        r = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
        g = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
        b = x * 0.0556434 + y * -0.2040259 + z * 1.0572252

        # Delinearize
        def gamma_correct(v):
            return 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1/2.4)) - 0.055

        r = gamma_correct(r)
        g = gamma_correct(g)
        b = gamma_correct(b)

        # Clamp to [0, 1]
        r = max(0, min(1, r))
        g = max(0, min(1, g))
        b = max(0, min(1, b))

        return (r, g, b)

    def interpolate_lab(
        self,
        color1: RGB,
        color2: RGB,
        t: float
    ) -> RGB:
        """
        Interpolate between two colors in LAB space.

        Args:
            color1: First RGB color
            color2: Second RGB color
            t: Interpolation factor (0-1)

        Returns:
            Interpolated RGB color
        """
        lab1 = self.rgb_to_lab(color1)
        lab2 = self.rgb_to_lab(color2)

        # Linear interpolation in LAB space
        L = lab1[0] + (lab2[0] - lab1[0]) * t
        a = lab1[1] + (lab2[1] - lab1[1]) * t
        b = lab1[2] + (lab2[2] - lab1[2]) * t

        return self.lab_to_rgb((L, a, b))

    def create_gradient(
        self,
        start_color: RGB,
        end_color: RGB,
        steps: int
    ) -> List[RGB]:
        """
        Create a gradient between two colors.

        Args:
            start_color: Starting RGB color
            end_color: Ending RGB color
            steps: Number of gradient steps

        Returns:
            List of RGB colors forming the gradient
        """
        gradient = []

        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            color = self.interpolate_lab(start_color, end_color, t)
            gradient.append(color)

        return gradient


def create_default_color_system() -> ColorSystem:
    """
    Create a color system with default control surface tokens.

    Returns:
        ColorSystem with standard tokens
    """
    tokens = {
        # Primary colors
        "primary": ColorToken(
            name="primary",
            rgb=(0.5, 0.5, 0.5),
            description="Primary surface color",
            tags=["surface", "neutral"]
        ),
        "secondary": ColorToken(
            name="secondary",
            rgb=(0.3, 0.3, 0.3),
            description="Secondary surface color",
            tags=["surface", "neutral"]
        ),
        "indicator": ColorToken(
            name="indicator",
            rgb=(1.0, 1.0, 1.0),
            description="Indicator/pointer color",
            tags=["indicator", "highlight"]
        ),

        # State colors
        "state_on": ColorToken(
            name="state_on",
            rgb=(0.2, 0.8, 0.2),
            description="Active/on state color",
            tags=["state", "active"]
        ),
        "state_off": ColorToken(
            name="state_off",
            rgb=(0.3, 0.3, 0.3),
            description="Inactive/off state color",
            tags=["state", "inactive"]
        ),
        "state_active": ColorToken(
            name="state_active",
            rgb=(1.0, 0.8, 0.0),
            description="Currently active/engaged state",
            tags=["state", "active"]
        ),
        "state_warning": ColorToken(
            name="state_warning",
            rgb=(1.0, 0.5, 0.0),
            description="Warning state color",
            tags=["state", "warning"]
        ),
        "state_error": ColorToken(
            name="state_error",
            rgb=(1.0, 0.2, 0.2),
            description="Error state color",
            tags=["state", "error"]
        ),

        # Material colors
        "material_metallic": ColorToken(
            name="material_metallic",
            rgb=(0.75, 0.75, 0.78),
            description="Metallic material base color",
            tags=["material", "metal"]
        ),
        "material_plastic": ColorToken(
            name="material_plastic",
            rgb=(0.5, 0.5, 0.5),
            description="Plastic material base color",
            tags=["material", "plastic"]
        ),
    }

    return ColorSystem(tokens)


# Example usage and testing
if __name__ == "__main__":
    # Create default color system
    cs = create_default_color_system()

    print("Color System Tokens:")
    for name, token in cs.tokens.items():
        print(f"  {name}: {token.rgb} - {token.description}")

    # Test LAB interpolation
    print("\nGradient from primary to state_on (5 steps):")
    gradient = cs.create_gradient(
        cs.get_rgb("primary"),
        cs.get_rgb("state_on"),
        5
    )
    for i, color in enumerate(gradient):
        print(f"  Step {i}: RGB{color}")
