"""
Material system for sleek brutalist mecha aesthetic.

Provides material presets and configuration for the mechanical platform,
emphasizing precision engineering and industrial luxury.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Dict


class MaterialPreset(Enum):
    """Material presets for sleek brutalist aesthetic."""
    BRUSHED_METAL = "brushed_metal"      # Sleek metallic finish
    CARBON_FIBER = "carbon_fiber"        # High-tech composite look
    MATTE_BLACK = "matte_black"          # Industrial matte finish
    CHROME = "chrome"                    # Polished reflective surface


@dataclass
class MaterialConfig:
    """Configuration for a single material."""
    preset: MaterialPreset
    color: Tuple[float, float, float]
    roughness: float  # 0.0-1.0
    metallic: float   # 0.0-1.0
    emissive: float   # 0.0-1.0

    def __post_init__(self):
        """Validate material parameters."""
        if not 0.0 <= self.roughness <= 1.0:
            raise ValueError(f"Roughness must be 0.0-1.0, got {self.roughness}")
        if not 0.0 <= self.metallic <= 1.0:
            raise ValueError(f"Metallic must be 0.0-1.0, got {self.metallic}")
        if not 0.0 <= self.emissive <= 1.0:
            raise ValueError(f"Emissive must be 0.0-1.0, got {self.emissive}")


class MaterialSystem:
    """
    Material system for applying sleek brutalist materials to platform components.

    Manages material configurations and applies them to tiles, arms, and base.
    """

    def __init__(self):
        """Initialize material system with default presets."""
        self.materials: Dict[str, MaterialConfig] = {}
        self._initialize_presets()

    def _initialize_presets(self) -> None:
        """Initialize default material presets."""
        # Brushed metal - primary tile material
        self.materials["tile_primary"] = MaterialConfig(
            preset=MaterialPreset.BRUSHED_METAL,
            color=(0.7, 0.7, 0.75),      # Light silver
            roughness=0.3,
            metallic=0.9,
            emissive=0.0
        )

        # Carbon fiber - secondary tile material
        self.materials["tile_secondary"] = MaterialConfig(
            preset=MaterialPreset.CARBON_FIBER,
            color=(0.1, 0.1, 0.12),      # Dark gray
            roughness=0.2,
            metallic=0.7,
            emissive=0.0
        )

        # Chrome - arm joints and accents
        self.materials["arm_joint"] = MaterialConfig(
            preset=MaterialPreset.CHROME,
            color=(0.9, 0.9, 0.95),      # Bright chrome
            roughness=0.05,
            metallic=1.0,
            emissive=0.0
        )

        # Matte black - arm segments
        self.materials["arm_segment"] = MaterialConfig(
            preset=MaterialPreset.MATTE_BLACK,
            color=(0.02, 0.02, 0.03),    # Deep black
            roughness=0.8,
            metallic=0.3,
            emissive=0.0
        )

        # Base platform - heavy industrial
        self.materials["base"] = MaterialConfig(
            preset=MaterialPreset.BRUSHED_METAL,
            color=(0.5, 0.5, 0.55),      # Medium gray
            roughness=0.4,
            metallic=0.85,
            emissive=0.0
        )

    def apply_to_platform(self, platform: 'Platform') -> None:
        """
        Apply materials to all platform components.

        Args:
            platform: Platform instance to apply materials to

        Note:
            This method applies preset materials to tiles, arms, and base.
            In Blender, this would create/assign actual material nodes.
        """
        # Apply to tiles
        for tile_id in range(platform.tile_count):
            config = self.materials["tile_primary"]
            self.apply_to_tile(tile_id, config)

        # Apply to arms
        for arm_index in range(platform.arm_count):
            config = self.materials["arm_segment"]
            self.apply_to_arm(arm_index, config)

        # Apply to base
        base_config = self.materials["base"]
        # In Blender: assign to base mesh
        # For now, we just store the configuration
        self.materials["platform_base"] = base_config

    def apply_to_tile(self, tile_id: int, config: MaterialConfig) -> None:
        """
        Apply material to a specific tile.

        Args:
            tile_id: ID of tile to apply material to
            config: Material configuration to apply
        """
        # Store material assignment
        material_name = f"tile_{tile_id}"
        self.materials[material_name] = config

        # In Blender, this would:
        # 1. Create BSDF node with config values
        # 2. Connect to material output
        # 3. Assign to tile mesh

    def apply_to_arm(self, arm_index: int, config: MaterialConfig) -> None:
        """
        Apply material to a specific arm.

        Args:
            arm_index: Index of arm to apply material to
            config: Material configuration to apply
        """
        # Store material assignment for arm segments
        material_name = f"arm_{arm_index}_segment"
        self.materials[material_name] = config

        # Apply chrome to joints
        joint_config = self.get_material(MaterialPreset.CHROME)
        joint_name = f"arm_{arm_index}_joint"
        self.materials[joint_name] = joint_config

        # In Blender, this would:
        # 1. Create separate materials for segments and joints
        # 2. Assign to respective mesh parts

    def get_material(self, preset: MaterialPreset) -> MaterialConfig:
        """
        Get material configuration for a preset.

        Args:
            preset: Material preset to retrieve

        Returns:
            MaterialConfig matching the preset
        """
        # Return first matching material
        for config in self.materials.values():
            if config.preset == preset:
                return config

        # Create default if not found
        if preset == MaterialPreset.BRUSHED_METAL:
            return MaterialConfig(
                preset=MaterialPreset.BRUSHED_METAL,
                color=(0.7, 0.7, 0.75),
                roughness=0.3,
                metallic=0.9,
                emissive=0.0
            )
        elif preset == MaterialPreset.CARBON_FIBER:
            return MaterialConfig(
                preset=MaterialPreset.CARBON_FIBER,
                color=(0.1, 0.1, 0.12),
                roughness=0.2,
                metallic=0.7,
                emissive=0.0
            )
        elif preset == MaterialPreset.MATTE_BLACK:
            return MaterialConfig(
                preset=MaterialPreset.MATTE_BLACK,
                color=(0.02, 0.02, 0.03),
                roughness=0.8,
                metallic=0.3,
                emissive=0.0
            )
        elif preset == MaterialPreset.CHROME:
            return MaterialConfig(
                preset=MaterialPreset.CHROME,
                color=(0.9, 0.9, 0.95),
                roughness=0.05,
                metallic=1.0,
                emissive=0.0
            )

        raise ValueError(f"Unknown preset: {preset}")

    def create_custom_material(
        self,
        name: str,
        preset: MaterialPreset,
        color: Tuple[float, float, float],
        roughness: float = 0.5,
        metallic: float = 0.5,
        emissive: float = 0.0
    ) -> MaterialConfig:
        """
        Create a custom material configuration.

        Args:
            name: Unique name for the material
            preset: Base preset to use
            color: RGB color tuple (0.0-1.0)
            roughness: Surface roughness (0.0-1.0)
            metallic: Metallic factor (0.0-1.0)
            emissive: Emission strength (0.0-1.0)

        Returns:
            Created MaterialConfig
        """
        config = MaterialConfig(
            preset=preset,
            color=color,
            roughness=roughness,
            metallic=metallic,
            emissive=emissive
        )
        self.materials[name] = config
        return config


if __name__ == "__main__":
    # Test the material system
    print("Testing MaterialSystem...")

    system = MaterialSystem()

    # Test preset materials
    print("\nDefault materials:")
    for name, config in system.materials.items():
        print(f"  {name}: {config.preset.value}")

    # Test getting material by preset
    chrome = system.get_material(MaterialPreset.CHROME)
    print(f"\nChrome material: roughness={chrome.roughness}, metallic={chrome.metallic}")

    # Test custom material
    custom = system.create_custom_material(
        "custom_accent",
        MaterialPreset.BRUSHED_METAL,
        color=(0.8, 0.2, 0.2),
        roughness=0.4,
        metallic=0.9
    )
    print(f"\nCustom material created: {custom.color}")

    # Test validation
    try:
        invalid = MaterialConfig(
            preset=MaterialPreset.CHROME,
            color=(1.0, 1.0, 1.0),
            roughness=1.5,  # Invalid
            metallic=0.5,
            emissive=0.0
        )
    except ValueError as e:
        print(f"\nValidation working: {e}")

    print("\n✓ MaterialSystem tests passed")
