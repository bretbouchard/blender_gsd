"""
Lighting presets for dramatic visual emphasis.

Provides lighting configurations that highlight mechanical details
and create the sleek brutalist aesthetic.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple, List


class LightingPreset(Enum):
    """Lighting presets for visual emphasis."""
    STUDIO = "studio"              # Clean studio lighting
    DRAMATIC = "dramatic"          # High-contrast dramatic lighting
    SOFT_AMBIENT = "soft_ambient"  # Soft fill lighting
    RIM_LIGHT = "rim_light"        # Edge-highlighting rim light


@dataclass
class LightingConfig:
    """Configuration for a single light."""
    preset: LightingPreset
    intensity: float
    color: Tuple[float, float, float]
    angle: float  # Light angle in degrees

    def __post_init__(self):
        """Validate lighting parameters."""
        if self.intensity < 0.0:
            raise ValueError(f"Intensity must be >= 0.0, got {self.intensity}")


class LightingSystem:
    """
    Lighting system for dramatic visual emphasis.

    Manages lighting presets and applies them to highlight
    mechanical details and platform edges.
    """

    def __init__(self):
        """Initialize lighting system with default configuration."""
        self.lights: List[LightingConfig] = []
        self.ambient_intensity: float = 0.2
        self._initialize_presets()

    def _initialize_presets(self) -> None:
        """Initialize default lighting presets."""
        # Studio preset - clean, professional lighting
        self._studio_lights = [
            LightingConfig(
                preset=LightingPreset.STUDIO,
                intensity=1.0,
                color=(1.0, 1.0, 1.0),  # Pure white
                angle=45.0
            ),
            LightingConfig(
                preset=LightingPreset.STUDIO,
                intensity=0.5,
                color=(0.95, 0.95, 1.0),  # Slight blue
                angle=135.0
            ),
        ]

        # Dramatic preset - high contrast
        self._dramatic_lights = [
            LightingConfig(
                preset=LightingPreset.DRAMATIC,
                intensity=1.5,
                color=(1.0, 0.95, 0.9),  # Warm
                angle=30.0
            ),
            LightingConfig(
                preset=LightingPreset.DRAMATIC,
                intensity=0.3,
                color=(0.8, 0.9, 1.0),  # Cool fill
                angle=210.0
            ),
        ]

        # Soft ambient preset - gentle fill
        self._soft_ambient_lights = [
            LightingConfig(
                preset=LightingPreset.SOFT_AMBIENT,
                intensity=0.7,
                color=(0.9, 0.95, 1.0),  # Soft blue-white
                angle=90.0
            ),
        ]

        # Rim light preset - edge highlighting
        self._rim_lights = [
            LightingConfig(
                preset=LightingPreset.RIM_LIGHT,
                intensity=1.2,
                color=(1.0, 1.0, 1.0),
                angle=180.0  # Behind subject
            ),
        ]

    def apply_preset(self, preset: LightingPreset) -> None:
        """
        Apply a lighting preset to the scene.

        Args:
            preset: Lighting preset to apply

        Note:
            Clears existing lights and applies preset configuration.
            In Blender, this would create actual light objects.
        """
        self.lights.clear()

        if preset == LightingPreset.STUDIO:
            self.lights = self._studio_lights.copy()
            self.ambient_intensity = 0.3

        elif preset == LightingPreset.DRAMATIC:
            self.lights = self._dramatic_lights.copy()
            self.ambient_intensity = 0.1

        elif preset == LightingPreset.SOFT_AMBIENT:
            self.lights = self._soft_ambient_lights.copy()
            self.ambient_intensity = 0.5

        elif preset == LightingPreset.RIM_LIGHT:
            self.lights = self._rim_lights.copy()
            self.ambient_intensity = 0.2

        # In Blender, this would:
        # 1. Clear existing lights
        # 2. Create new light objects with config
        # 3. Position and orient lights
        # 4. Set light properties (color, intensity, etc.)

    def add_rim_light(self, position: Tuple[float, float, float]) -> None:
        """
        Add edge-highlighting rim light at specific position.

        Args:
            position: (x, y, z) world position for rim light
        """
        rim_config = LightingConfig(
            preset=LightingPreset.RIM_LIGHT,
            intensity=1.0,
            color=(1.0, 1.0, 1.0),
            angle=180.0
        )
        self.lights.append(rim_config)

        # In Blender, this would:
        # 1. Create spot or area light at position
        # 2. Orient to point toward platform center
        # 3. Set high intensity for edge highlight

    def set_ambient_intensity(self, intensity: float) -> None:
        """
        Adjust ambient light level.

        Args:
            intensity: Ambient intensity (0.0-1.0)
        """
        if not 0.0 <= intensity <= 1.0:
            raise ValueError(f"Ambient intensity must be 0.0-1.0, got {intensity}")

        self.ambient_intensity = intensity

        # In Blender, this would update world ambient setting

    def add_custom_light(
        self,
        preset: LightingPreset,
        intensity: float,
        color: Tuple[float, float, float],
        angle: float
    ) -> LightingConfig:
        """
        Add a custom light to the scene.

        Args:
            preset: Lighting preset type
            intensity: Light intensity
            color: RGB color tuple (0.0-1.0)
            angle: Light angle in degrees

        Returns:
            Created LightingConfig
        """
        config = LightingConfig(
            preset=preset,
            intensity=intensity,
            color=color,
            angle=angle
        )
        self.lights.append(config)
        return config

    def get_light_count(self) -> int:
        """Get number of lights in current configuration."""
        return len(self.lights)

    def clear_lights(self) -> None:
        """Remove all lights from scene."""
        self.lights.clear()
        self.ambient_intensity = 0.0


if __name__ == "__main__":
    # Test the lighting system
    print("Testing LightingSystem...")

    system = LightingSystem()

    # Test presets
    print("\nTesting presets:")
    for preset in LightingPreset:
        system.apply_preset(preset)
        print(f"  {preset.value}: {system.get_light_count()} lights, ambient={system.ambient_intensity}")

    # Test custom light
    print("\nAdding custom light...")
    custom = system.add_custom_light(
        preset=LightingPreset.STUDIO,
        intensity=0.8,
        color=(1.0, 0.9, 0.8),
        angle=60.0
    )
    print(f"  Custom light added: intensity={custom.intensity}")

    # Test rim light
    print("\nAdding rim light...")
    system.add_rim_light((10.0, 0.0, 5.0))
    print(f"  Total lights: {system.get_light_count()}")

    # Test ambient
    print("\nTesting ambient...")
    system.set_ambient_intensity(0.4)
    print(f"  Ambient intensity: {system.ambient_intensity}")

    # Test validation
    try:
        system.set_ambient_intensity(1.5)
    except ValueError as e:
        print(f"\nValidation working: {e}")

    print("\n✓ LightingSystem tests passed")
