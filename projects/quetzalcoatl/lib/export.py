"""
Presets & Export System (Phase 20.11)

Creature presets and export functionality.

Universal Stage Order:
- Stage 0: Normalize (parameter validation)
- Stage 1: Primary (creature presets)
- Stage 2: Secondary (export formats)
- Stage 3: Detail (batch export)
- Stage 4: Output Prep (file generation)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import numpy as np

from .types import (
    WingType,
    ScaleShape,
    TailType,
    CrestType,
    QuetzalcoatlConfig,
    WingConfig,
    ScaleConfig,
    TailConfig,
    HeadConfig,
)
from .color import ColorSystemConfig, IridescenceConfig, ColorPattern
from .shader import ShaderQuality, MaterialType


class ExportFormat(Enum):
    """Export format types."""
    FBX = 0
    OBJ = 1
    GLTF = 2
    USD = 3
    BLEND = 4
    ALEMBIC = 5


class PresetCategory(Enum):
    """Categories of creature presets."""
    SERPENT = 0
    DRAGON = 1
    WYVERN = 2
    HYDRA = 3
    AMPHIPTERE = 4
    COATL = 5
    CUSTOM = 6


@dataclass
class CreaturePreset:
    """Complete creature preset configuration."""
    name: str
    category: PresetCategory
    description: str
    config: QuetzalcoatlConfig
    color_config: ColorSystemConfig
    shader_quality: ShaderQuality = ShaderQuality.STANDARD

    # Features
    has_wings: bool = True
    has_limbs: bool = True
    has_scales: bool = True
    has_feathers: bool = True
    has_teeth: bool = True
    has_whiskers: bool = False
    has_claws: bool = True


@dataclass
class ExportConfig:
    """Configuration for export operations."""
    format: ExportFormat = ExportFormat.FBX
    include_rig: bool = True
    include_materials: bool = True
    include_textures: bool = True
    apply_modifiers: bool = True
    triangulate: bool = False
    global_scale: float = 1.0
    forward_axis: str = "Y"
    up_axis: str = "Z"


@dataclass
class ExportResult:
    """Result from export operation."""
    success: bool
    format: ExportFormat
    file_path: Optional[str] = None
    vertex_count: int = 0
    face_count: int = 0
    material_count: int = 0
    bone_count: int = 0
    errors: List[str] = field(default_factory=list)


# Creature presets
CREATURE_PRESETS: Dict[str, CreaturePreset] = {
    "quetzalcoatl": CreaturePreset(
        name="Quetzalcoatl",
        category=PresetCategory.COATL,
        description="The Feathered Serpent - iridescent feathers, emerald green with gold accents",
        config=QuetzalcoatlConfig(
            wings=WingConfig(wing_type=WingType.FEATHERED),
            scales=ScaleConfig(shape=ScaleShape.ROUND),
            tail=TailConfig(tail_type=TailType.FEATHER_TUFT),
            head=HeadConfig(crest_type=CrestType.FRILL),
        ),
        color_config=ColorSystemConfig(
            pattern=ColorPattern.IRIDESCENT,
            primary_color=np.array([0.1, 0.5, 0.2]),
            secondary_color=np.array([0.1, 0.7, 0.9]),
            accent_color=np.array([0.9, 0.85, 0.2]),
            iridescence=IridescenceConfig(enabled=True, shift_amount=0.3),
        ),
        shader_quality=ShaderQuality.HIGH,
        has_wings=True,
        has_limbs=False,
        has_scales=True,
        has_feathers=True,
        has_teeth=True,
        has_whiskers=False,
        has_claws=False,
    ),

    "european_dragon": CreaturePreset(
        name="European Dragon",
        category=PresetCategory.DRAGON,
        description="Classic Western dragon - four legs, wings, red scales, fiery appearance",
        config=QuetzalcoatlConfig(
            wings=WingConfig(wing_type=WingType.MEMBRANE),
            scales=ScaleConfig(shape=ScaleShape.HEXAGONAL),
            tail=TailConfig(tail_type=TailType.POINTED),
            head=HeadConfig(crest_type=CrestType.HORNS),
        ),
        color_config=ColorSystemConfig(
            pattern=ColorPattern.MOTTLED,
            primary_color=np.array([0.6, 0.15, 0.1]),
            secondary_color=np.array([0.4, 0.1, 0.05]),
            accent_color=np.array([0.9, 0.3, 0.1]),
        ),
        shader_quality=ShaderQuality.HIGH,
        has_wings=True,
        has_limbs=True,
        has_scales=True,
        has_feathers=False,
        has_teeth=True,
        has_whiskers=False,
        has_claws=True,
    ),

    "wyvern": CreaturePreset(
        name="Wyvern",
        category=PresetCategory.WYVERN,
        description="Two-legged winged dragon - bat-like wings, brown scales",
        config=QuetzalcoatlConfig(
            wings=WingConfig(wing_type=WingType.MEMBRANE),
            scales=ScaleConfig(shape=ScaleShape.DIAMOND),
            tail=TailConfig(tail_type=TailType.POINTED),
            head=HeadConfig(crest_type=CrestType.RIDGE),
        ),
        color_config=ColorSystemConfig(
            pattern=ColorPattern.SCALED,
            primary_color=np.array([0.4, 0.3, 0.2]),
            secondary_color=np.array([0.5, 0.4, 0.3]),
            accent_color=np.array([0.2, 0.15, 0.1]),
        ),
        shader_quality=ShaderQuality.STANDARD,
        has_wings=True,
        has_limbs=True,
        has_scales=True,
        has_feathers=False,
        has_teeth=True,
        has_whiskers=False,
        has_claws=True,
    ),

    "sea_serpent": CreaturePreset(
        name="Sea Serpent",
        category=PresetCategory.SERPENT,
        description="Aquatic serpent - no limbs, fins, blue-green scales",
        config=QuetzalcoatlConfig(
            wings=WingConfig(wing_type=WingType.NONE),
            scales=ScaleConfig(shape=ScaleShape.OVAL),
            tail=TailConfig(tail_type=TailType.FAN),
            head=HeadConfig(crest_type=CrestType.RIDGE),
        ),
        color_config=ColorSystemConfig(
            pattern=ColorPattern.STRIPED,
            primary_color=np.array([0.1, 0.3, 0.5]),
            secondary_color=np.array([0.15, 0.4, 0.55]),
            accent_color=np.array([0.2, 0.5, 0.6]),
        ),
        shader_quality=ShaderQuality.HIGH,
        has_wings=False,
        has_limbs=False,
        has_scales=True,
        has_feathers=False,
        has_teeth=True,
        has_whiskers=True,
        has_claws=False,
    ),

    "hydra": CreaturePreset(
        name="Hydra",
        category=PresetCategory.HYDRA,
        description="Multi-headed serpent - green scales, venomous",
        config=QuetzalcoatlConfig(
            wings=WingConfig(wing_type=WingType.NONE),
            scales=ScaleConfig(shape=ScaleShape.ROUND),
            tail=TailConfig(tail_type=TailType.POINTED),
            head=HeadConfig(crest_type=CrestType.NONE),
        ),
        color_config=ColorSystemConfig(
            pattern=ColorPattern.MOTTLED,
            primary_color=np.array([0.15, 0.4, 0.15]),
            secondary_color=np.array([0.2, 0.5, 0.2]),
            accent_color=np.array([0.8, 0.6, 0.1]),
        ),
        shader_quality=ShaderQuality.STANDARD,
        has_wings=False,
        has_limbs=False,
        has_scales=True,
        has_feathers=False,
        has_teeth=True,
        has_whiskers=False,
        has_claws=False,
    ),

    "amphiptere": CreaturePreset(
        name="Amphiptere",
        category=PresetCategory.AMPHIPTERE,
        description="Winged serpent with feathered wings - golden feathers",
        config=QuetzalcoatlConfig(
            wings=WingConfig(wing_type=WingType.FEATHERED),
            scales=ScaleConfig(shape=ScaleShape.ROUND),
            tail=TailConfig(tail_type=TailType.FEATHER_TUFT),
            head=HeadConfig(crest_type=CrestType.FRILL),
        ),
        color_config=ColorSystemConfig(
            pattern=ColorPattern.IRIDESCENT,
            primary_color=np.array([0.8, 0.7, 0.3]),
            secondary_color=np.array([0.9, 0.8, 0.4]),
            accent_color=np.array([0.3, 0.2, 0.1]),
            iridescence=IridescenceConfig(enabled=True, shift_amount=0.2),
        ),
        shader_quality=ShaderQuality.HIGH,
        has_wings=True,
        has_limbs=False,
        has_scales=True,
        has_feathers=True,
        has_teeth=True,
        has_whiskers=False,
        has_claws=False,
    ),

    "ghost_serpent": CreaturePreset(
        name="Ghost Serpent",
        category=PresetCategory.SERPENT,
        description="Ethereal white serpent - translucent, ethereal glow",
        config=QuetzalcoatlConfig(
            wings=WingConfig(wing_type=WingType.NONE),
            scales=ScaleConfig(shape=ScaleShape.ROUND),
            tail=TailConfig(tail_type=TailType.POINTED),
            head=HeadConfig(crest_type=CrestType.NONE),
        ),
        color_config=ColorSystemConfig(
            pattern=ColorPattern.SOLID,
            primary_color=np.array([0.9, 0.9, 0.95]),
            secondary_color=np.array([0.7, 0.75, 0.9]),
            accent_color=np.array([0.5, 0.5, 0.6]),
        ),
        shader_quality=ShaderQuality.ULTRA,
        has_wings=False,
        has_limbs=False,
        has_scales=True,
        has_feathers=False,
        has_teeth=True,
        has_whiskers=False,
        has_claws=False,
    ),
}


def get_preset(name: str) -> Optional[CreaturePreset]:
    """Get a creature preset by name.

    Args:
        name: Preset name

    Returns:
        CreaturePreset or None if not found
    """
    return CREATURE_PRESETS.get(name.lower())


def list_presets(category: Optional[PresetCategory] = None) -> List[str]:
    """List available preset names.

    Args:
        category: Optional category filter

    Returns:
        List of preset names
    """
    if category is None:
        return list(CREATURE_PRESETS.keys())

    return [
        name for name, preset in CREATURE_PRESETS.items()
        if preset.category == category
    ]


def get_presets_by_category() -> Dict[PresetCategory, List[str]]:
    """Get presets organized by category.

    Returns:
        Dictionary mapping categories to preset names
    """
    result: Dict[PresetCategory, List[str]] = {cat: [] for cat in PresetCategory}

    for name, preset in CREATURE_PRESETS.items():
        result[preset.category].append(name)

    return result


class ExportManager:
    """Manages creature export operations."""

    def __init__(self, config: ExportConfig):
        """Initialize export manager.

        Args:
            config: Export configuration
        """
        self.config = config

    def export(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
        normals: Optional[np.ndarray] = None,
        uvs: Optional[np.ndarray] = None,
        bone_data: Optional[Dict] = None,
        output_path: Optional[str] = None,
    ) -> ExportResult:
        """Export creature geometry.

        Args:
            vertices: Vertex positions (N, 3)
            faces: Face indices (F, 3)
            normals: Vertex normals
            uvs: UV coordinates
            bone_data: Bone and weight data
            output_path: Output file path

        Returns:
            ExportResult with export status
        """
        errors = []

        # Validate input
        if len(vertices) == 0:
            errors.append("No vertices to export")

        if len(faces) == 0:
            errors.append("No faces to export")

        if errors:
            return ExportResult(
                success=False,
                format=self.config.format,
                errors=errors,
            )

        # Generate output based on format
        output_data = self._generate_output(
            vertices, faces, normals, uvs, bone_data
        )

        return ExportResult(
            success=True,
            format=self.config.format,
            file_path=output_path,
            vertex_count=len(vertices),
            face_count=len(faces),
            material_count=0,
            bone_count=len(bone_data.get("bones", [])) if bone_data else 0,
        )

    def _generate_output(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
        normals: Optional[np.ndarray],
        uvs: Optional[np.ndarray],
        bone_data: Optional[Dict],
    ) -> str:
        """Generate export output data."""
        if self.config.format == ExportFormat.OBJ:
            return self._generate_obj(vertices, faces, normals, uvs)
        elif self.config.format == ExportFormat.FBX:
            return self._generate_fbx_placeholder()
        elif self.config.format == ExportFormat.GLTF:
            return self._generate_gltf_placeholder()
        else:
            return ""

    def _generate_obj(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
        normals: Optional[np.ndarray],
        uvs: Optional[np.ndarray],
    ) -> str:
        """Generate OBJ format output."""
        lines = ["# Quetzalcoatl Creature Export", ""]

        # Vertices
        for v in vertices:
            lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")

        lines.append("")

        # UVs
        if uvs is not None:
            for uv in uvs:
                lines.append(f"vt {uv[0]:.6f} {uv[1]:.6f}")
            lines.append("")

        # Normals
        if normals is not None:
            for n in normals:
                lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
            lines.append("")

        # Faces
        for f in faces:
            # OBJ uses 1-based indexing
            f_obj = f + 1
            if normals is not None and uvs is not None:
                lines.append(f"f {f_obj[0]}/{f_obj[0]}/{f_obj[0]} "
                            f"{f_obj[1]}/{f_obj[1]}/{f_obj[1]} "
                            f"{f_obj[2]}/{f_obj[2]}/{f_obj[2]}")
            elif normals is not None:
                lines.append(f"f {f_obj[0]}//{f_obj[0]} "
                            f"{f_obj[1]}//{f_obj[1]} "
                            f"{f_obj[2]}//{f_obj[2]}")
            else:
                lines.append(f"f {f_obj[0]} {f_obj[1]} {f_obj[2]}")

        return "\n".join(lines)

    def _generate_fbx_placeholder(self) -> str:
        """Generate FBX placeholder (requires bpy)."""
        return "# FBX export requires Blender Python environment"

    def _generate_gltf_placeholder(self) -> str:
        """Generate glTF placeholder (requires additional libraries)."""
        return "# glTF export requires pygltflib or similar library"


def export_creature(
    vertices: np.ndarray,
    faces: np.ndarray,
    format: ExportFormat = ExportFormat.OBJ,
    normals: Optional[np.ndarray] = None,
    uvs: Optional[np.ndarray] = None,
    output_path: Optional[str] = None,
) -> ExportResult:
    """Export creature with simplified interface.

    Args:
        vertices: Vertex positions
        faces: Face indices
        format: Export format
        normals: Vertex normals
        uvs: UV coordinates
        output_path: Output file path

    Returns:
        ExportResult with export status
    """
    config = ExportConfig(format=format)
    manager = ExportManager(config)
    return manager.export(vertices, faces, normals, uvs, None, output_path)


def create_custom_preset(
    name: str,
    category: PresetCategory,
    config: QuetzalcoatlConfig,
    color_config: ColorSystemConfig,
    description: str = "",
    **kwargs,
) -> CreaturePreset:
    """Create a custom creature preset.

    Args:
        name: Preset name
        category: Creature category
        config: Creature configuration
        color_config: Color configuration
        description: Preset description
        **kwargs: Additional feature flags

    Returns:
        New CreaturePreset
    """
    return CreaturePreset(
        name=name,
        category=category,
        description=description,
        config=config,
        color_config=color_config,
        **kwargs,
    )
