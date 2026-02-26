"""
Shader System (Phase 20.9)

Generates shader configurations and material definitions for the creature.

Universal Stage Order:
- Stage 0: Normalize (parameter validation)
- Stage 1: Primary (base material properties)
- Stage 2: Secondary (layered materials)
- Stage 3: Detail (iridescence, subsurface scattering)
- Stage 4: Output Prep (shader node data)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import numpy as np


class MaterialType(Enum):
    """Types of materials for creature parts."""
    SKIN = 0          # General skin/scale surface
    FEATHER = 1       # Feathered areas
    SCALE = 2         # Scaly areas
    CLAW = 3          # Claws/talons
    TOOTH = 4         # Teeth
    EYE = 5           # Eyes
    WING_MEMBRANE = 6 # Wing membrane (bat-like)
    IRIDESCENT = 7    # Iridescent areas


class ShaderQuality(Enum):
    """Shader quality levels."""
    PREVIEW = 0       # Fast preview quality
    STANDARD = 1      # Standard quality
    HIGH = 2          # High quality with SSS
    ULTRA = 3         # Ultra quality with all effects


@dataclass
class BaseMaterialProperties:
    """Base material properties."""
    base_color: np.ndarray = field(default_factory=lambda: np.array([0.5, 0.5, 0.5]))
    roughness: float = 0.5
    metallic: float = 0.0
    specular: float = 0.5
    alpha: float = 1.0

    def __post_init__(self):
        if not isinstance(self.base_color, np.ndarray):
            self.base_color = np.array(self.base_color)


@dataclass
class SubsurfaceScattering:
    """Subsurface scattering configuration."""
    enabled: bool = False
    weight: float = 0.5
    radius: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.2, 0.1]))
    color: np.ndarray = field(default_factory=lambda: np.array([0.8, 0.4, 0.3]))

    def __post_init__(self):
        if not isinstance(self.radius, np.ndarray):
            self.radius = np.array(self.radius)
        if not isinstance(self.color, np.ndarray):
            self.color = np.array(self.color)


@dataclass
class IridescenceShader:
    """Iridescence shader configuration."""
    enabled: bool = False
    base_hue_shift: float = 0.0
    hue_shift_range: float = 0.3
    intensity: float = 1.0
    frequency: float = 1.0
    fresnel_power: float = 2.0


@dataclass
class FeatherShaderConfig:
    """Shader configuration for feathers."""
    barb_separation: float = 0.02
    barb_opacity: float = 0.8
    anisotropic_strength: float = 0.5
    translucency: float = 0.3


@dataclass
class ScaleShaderConfig:
    """Shader configuration for scales."""
    scale_pattern_intensity: float = 0.5
    scale_edge_darkness: float = 0.3
    scale_highlight: float = 0.2
    wetness: float = 0.0


@dataclass
class EyeShaderConfig:
    """Shader configuration for eyes."""
    iris_color: np.ndarray = field(default_factory=lambda: np.array([0.2, 0.5, 0.8]))
    pupil_size: float = 0.3
    iris_pattern: float = 0.5
    cornea_ior: float = 1.4
    sclera_color: np.ndarray = field(default_factory=lambda: np.array([0.9, 0.9, 0.85]))

    def __post_init__(self):
        if not isinstance(self.iris_color, np.ndarray):
            self.iris_color = np.array(self.iris_color)
        if not isinstance(self.sclera_color, np.ndarray):
            self.sclera_color = np.array(self.sclera_color)


@dataclass
class MaterialLayer:
    """A layer in a layered material."""
    name: str
    material_type: MaterialType
    properties: BaseMaterialProperties
    blend_factor: float = 1.0
    mask_texture: Optional[str] = None


@dataclass
class ShaderConfig:
    """Complete shader configuration for a material."""
    material_type: MaterialType
    base_properties: BaseMaterialProperties
    subsurface: Optional[SubsurfaceScattering] = None
    iridescence: Optional[IridescenceShader] = None
    feather_config: Optional[FeatherShaderConfig] = None
    scale_config: Optional[ScaleShaderConfig] = None
    eye_config: Optional[EyeShaderConfig] = None
    layers: List[MaterialLayer] = field(default_factory=list)
    quality: ShaderQuality = ShaderQuality.STANDARD


@dataclass
class ShaderNodeData:
    """Data for creating shader nodes."""
    node_type: str
    position: tuple
    properties: Dict[str, Any]
    inputs: Dict[str, str]  # input_name -> connected_node_name
    outputs: Dict[str, str]  # output_name -> target_input_name


@dataclass
class ShaderResult:
    """Result from shader generation."""
    shader_configs: Dict[str, ShaderConfig]
    node_data: List[ShaderNodeData]
    texture_names: List[str]

    @property
    def material_count(self) -> int:
        return len(self.shader_configs)


class ShaderGenerator:
    """Generates shader configurations for creature materials."""

    def __init__(self, quality: ShaderQuality = ShaderQuality.STANDARD):
        """Initialize shader generator.

        Args:
            quality: Shader quality level
        """
        self.quality = quality

    def generate(
        self,
        material_types: Optional[List[MaterialType]] = None,
    ) -> ShaderResult:
        """Generate shader configurations.

        Args:
            material_types: List of material types to generate

        Returns:
            ShaderResult with all shader configurations
        """
        if material_types is None:
            material_types = [
                MaterialType.SKIN,
                MaterialType.FEATHER,
                MaterialType.SCALE,
                MaterialType.CLAW,
                MaterialType.TOOTH,
                MaterialType.EYE,
            ]

        configs: Dict[str, ShaderConfig] = {}
        node_data: List[ShaderNodeData] = []
        textures: List[str] = []

        for mat_type in material_types:
            config = self._generate_material_config(mat_type)
            configs[mat_type.name.lower()] = config

            # Generate node data
            nodes = self._generate_node_data(config)
            node_data.extend(nodes)

        return ShaderResult(
            shader_configs=configs,
            node_data=node_data,
            texture_names=textures,
        )

    def _generate_material_config(self, mat_type: MaterialType) -> ShaderConfig:
        """Generate configuration for a specific material type."""
        if mat_type == MaterialType.SKIN:
            return self._create_skin_config()
        elif mat_type == MaterialType.FEATHER:
            return self._create_feather_config()
        elif mat_type == MaterialType.SCALE:
            return self._create_scale_config()
        elif mat_type == MaterialType.CLAW:
            return self._create_claw_config()
        elif mat_type == MaterialType.TOOTH:
            return self._create_tooth_config()
        elif mat_type == MaterialType.EYE:
            return self._create_eye_config()
        elif mat_type == MaterialType.WING_MEMBRANE:
            return self._create_membrane_config()
        elif mat_type == MaterialType.IRIDESCENT:
            return self._create_iridescent_config()
        else:
            return self._create_default_config()

    def _create_skin_config(self) -> ShaderConfig:
        """Create skin material configuration."""
        base = BaseMaterialProperties(
            base_color=np.array([0.4, 0.35, 0.3]),
            roughness=0.6,
            metallic=0.0,
            specular=0.3,
        )

        sss = None
        if self.quality.value >= ShaderQuality.HIGH.value:
            sss = SubsurfaceScattering(
                enabled=True,
                weight=0.3,
                radius=np.array([1.0, 0.5, 0.3]),
                color=np.array([0.8, 0.5, 0.4]),
            )

        return ShaderConfig(
            material_type=MaterialType.SKIN,
            base_properties=base,
            subsurface=sss,
            quality=self.quality,
        )

    def _create_feather_config(self) -> ShaderConfig:
        """Create feather material configuration."""
        base = BaseMaterialProperties(
            base_color=np.array([0.2, 0.5, 0.3]),
            roughness=0.4,
            metallic=0.1,
            specular=0.6,
        )

        iridescence = IridescenceShader(
            enabled=self.quality.value >= ShaderQuality.STANDARD.value,
            base_hue_shift=0.0,
            hue_shift_range=0.2,
            intensity=0.8,
            fresnel_power=3.0,
        )

        feather = FeatherShaderConfig(
            barb_separation=0.02,
            barb_opacity=0.85,
            anisotropic_strength=0.6,
            translucency=0.4,
        )

        return ShaderConfig(
            material_type=MaterialType.FEATHER,
            base_properties=base,
            iridescence=iridescence,
            feather_config=feather,
            quality=self.quality,
        )

    def _create_scale_config(self) -> ShaderConfig:
        """Create scale material configuration."""
        base = BaseMaterialProperties(
            base_color=np.array([0.15, 0.3, 0.2]),
            roughness=0.3,
            metallic=0.2,
            specular=0.8,
        )

        scale = ScaleShaderConfig(
            scale_pattern_intensity=0.6,
            scale_edge_darkness=0.4,
            scale_highlight=0.3,
            wetness=0.0,
        )

        iridescence = IridescenceShader(
            enabled=self.quality.value >= ShaderQuality.HIGH.value,
            intensity=0.5,
        )

        return ShaderConfig(
            material_type=MaterialType.SCALE,
            base_properties=base,
            scale_config=scale,
            iridescence=iridescence,
            quality=self.quality,
        )

    def _create_claw_config(self) -> ShaderConfig:
        """Create claw material configuration."""
        base = BaseMaterialProperties(
            base_color=np.array([0.1, 0.08, 0.06]),
            roughness=0.2,
            metallic=0.1,
            specular=0.9,
        )

        sss = None
        if self.quality.value >= ShaderQuality.HIGH.value:
            sss = SubsurfaceScattering(
                enabled=True,
                weight=0.2,
                radius=np.array([0.5, 0.2, 0.1]),
                color=np.array([0.9, 0.85, 0.8]),
            )

        return ShaderConfig(
            material_type=MaterialType.CLAW,
            base_properties=base,
            subsurface=sss,
            quality=self.quality,
        )

    def _create_tooth_config(self) -> ShaderConfig:
        """Create tooth material configuration."""
        base = BaseMaterialProperties(
            base_color=np.array([0.95, 0.93, 0.88]),
            roughness=0.15,
            metallic=0.0,
            specular=0.95,
        )

        sss = SubsurfaceScattering(
            enabled=self.quality.value >= ShaderQuality.STANDARD.value,
            weight=0.4,
            radius=np.array([0.8, 0.4, 0.2]),
            color=np.array([0.95, 0.95, 0.9]),
        )

        return ShaderConfig(
            material_type=MaterialType.TOOTH,
            base_properties=base,
            subsurface=sss,
            quality=self.quality,
        )

    def _create_eye_config(self) -> ShaderConfig:
        """Create eye material configuration."""
        base = BaseMaterialProperties(
            base_color=np.array([0.2, 0.4, 0.7]),
            roughness=0.0,
            metallic=0.0,
            specular=1.0,
        )

        eye = EyeShaderConfig(
            iris_color=np.array([0.2, 0.5, 0.8]),
            pupil_size=0.3,
            iris_pattern=0.6,
            cornea_ior=1.45,
        )

        return ShaderConfig(
            material_type=MaterialType.EYE,
            base_properties=base,
            eye_config=eye,
            quality=self.quality,
        )

    def _create_membrane_config(self) -> ShaderConfig:
        """Create wing membrane configuration."""
        base = BaseMaterialProperties(
            base_color=np.array([0.3, 0.25, 0.35]),
            roughness=0.5,
            metallic=0.0,
            specular=0.4,
            alpha=0.95,
        )

        sss = SubsurfaceScattering(
            enabled=True,
            weight=0.6,
            radius=np.array([1.5, 0.8, 0.5]),
            color=np.array([0.7, 0.5, 0.6]),
        )

        return ShaderConfig(
            material_type=MaterialType.WING_MEMBRANE,
            base_properties=base,
            subsurface=sss,
            quality=self.quality,
        )

    def _create_iridescent_config(self) -> ShaderConfig:
        """Create iridescent material configuration."""
        base = BaseMaterialProperties(
            base_color=np.array([0.3, 0.3, 0.4]),
            roughness=0.1,
            metallic=0.3,
            specular=1.0,
        )

        iridescence = IridescenceShader(
            enabled=True,
            base_hue_shift=0.0,
            hue_shift_range=0.5,
            intensity=1.5,
            frequency=2.0,
            fresnel_power=4.0,
        )

        return ShaderConfig(
            material_type=MaterialType.IRIDESCENT,
            base_properties=base,
            iridescence=iridescence,
            quality=self.quality,
        )

    def _create_default_config(self) -> ShaderConfig:
        """Create default material configuration."""
        base = BaseMaterialProperties()
        return ShaderConfig(
            material_type=MaterialType.SKIN,
            base_properties=base,
            quality=self.quality,
        )

    def _generate_node_data(self, config: ShaderConfig) -> List[ShaderNodeData]:
        """Generate shader node data for a configuration."""
        nodes = []

        # Principled BSDF node
        bsdf_props = {
            "Base Color": config.base_properties.base_color.tolist(),
            "Roughness": config.base_properties.roughness,
            "Metallic": config.base_properties.metallic,
            "Specular IOR Level": config.base_properties.specular,
            "Alpha": config.base_properties.alpha,
        }

        if config.subsurface and config.subsurface.enabled:
            bsdf_props["Subsurface Weight"] = config.subsurface.weight
            bsdf_props["Subsurface Radius"] = config.subsurface.radius.tolist()
            bsdf_props["Subsurface Color"] = config.subsurface.color.tolist()

        nodes.append(ShaderNodeData(
            node_type="bsdf_principled",
            position=(0, 0),
            properties=bsdf_props,
            inputs={},
            outputs={"BSDF": "Surface"},
        ))

        # Material Output node
        nodes.append(ShaderNodeData(
            node_type="output_material",
            position=(300, 0),
            properties={},
            inputs={"Surface": "bsdf_principled.BSDF"},
            outputs={},
        ))

        # Iridescence node if enabled
        if config.iridescence and config.iridescence.enabled:
            nodes.append(ShaderNodeData(
                node_type="mix_rgb",
                position=(-200, 100),
                properties={
                    "blend_type": "MIX",
                    "fac": config.iridescence.intensity,
                },
                inputs={},
                outputs={"Color": "bsdf_principled.Base Color"},
            ))

        return nodes


def generate_shaders(
    quality: ShaderQuality = ShaderQuality.STANDARD,
    material_types: Optional[List[MaterialType]] = None,
) -> ShaderResult:
    """Generate shader configurations with simplified interface.

    Args:
        quality: Shader quality level
        material_types: List of material types to generate

    Returns:
        ShaderResult with all configurations
    """
    gen = ShaderGenerator(quality)
    return gen.generate(material_types)


# Shader presets
SHADER_PRESETS = {
    "realistic": {
        "quality": ShaderQuality.HIGH,
        "materials": [
            MaterialType.SKIN,
            MaterialType.FEATHER,
            MaterialType.SCALE,
            MaterialType.CLAW,
            MaterialType.TOOTH,
            MaterialType.EYE,
        ],
    },
    "stylized": {
        "quality": ShaderQuality.STANDARD,
        "materials": [
            MaterialType.SKIN,
            MaterialType.FEATHER,
            MaterialType.EYE,
        ],
    },
    "preview": {
        "quality": ShaderQuality.PREVIEW,
        "materials": [MaterialType.SKIN],
    },
    "iridescent_creature": {
        "quality": ShaderQuality.HIGH,
        "materials": [
            MaterialType.IRIDESCENT,
            MaterialType.FEATHER,
            MaterialType.EYE,
        ],
    },
}


def get_shader_preset(name: str) -> Dict[str, Any]:
    """Get a shader preset by name.

    Args:
        name: Preset name

    Returns:
        Dictionary with preset values
    """
    return SHADER_PRESETS.get(name, SHADER_PRESETS["realistic"])


def create_generator_from_preset(name: str) -> ShaderGenerator:
    """Create a ShaderGenerator from a preset.

    Args:
        name: Preset name

    Returns:
        Configured ShaderGenerator
    """
    preset = get_shader_preset(name)
    return ShaderGenerator(quality=preset["quality"])
