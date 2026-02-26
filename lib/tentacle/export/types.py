"""
Tentacle Export Types

Configuration and result types for the Unreal Engine export pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path


class LODStrategy(Enum):
    """Strategy for LOD generation."""
    DECIMATE = "decimate"       # Use Blender's decimate modifier
    REMESH = "remesh"           # Use remesh modifier
    MANUAL = "manual"           # Use manually specified polygon counts


class ExportFormat(Enum):
    """Export format for tentacle package."""
    FBX = "fbx"                 # FBX for Unreal Engine
    GLTF = "gltf"               # glTF 2.0 (experimental)
    ALEMBIC = "abc"             # Alembic for film/VFX


@dataclass
class LODLevel:
    """Configuration for a single LOD level."""
    name: str
    ratio: float = 1.0             # Decimate ratio (1.0 = no reduction)
    screen_size: float = 1.0       # Screen size threshold for UE5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ratio": self.ratio,
            "screen_size": self.screen_size,
        }


@dataclass
class LODConfig:
    """Configuration for LOD generation."""
    enabled: bool = True
    strategy: LODStrategy = LODStrategy.DECIMATE
    levels: List[LODLevel] = field(default_factory=lambda: [
        LODLevel("LOD0", 1.0, 1.0),
        LODLevel("LOD1", 0.5, 0.5),
        LODLevel("LOD2", 0.25, 0.25),
        LODLevel("LOD3", 0.12, 0.12),
    ])
    preserve_uvs: bool = True
    preserve_shape_keys: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "strategy": self.strategy.value,
            "levels": [level.to_dict() for level in self.levels],
            "preserve_uvs": self.preserve_uvs,
            "preserve_shape_keys": self.preserve_shape_keys,
        }


@dataclass
class FBXExportConfig:
    """Configuration for FBX export."""
    output_path: str = "./output/tentacle.fbx"
    # Export settings
    include_shape_keys: bool = True
    include_skinning: bool = True
    apply_modifiers: bool = True
    # UE5-compatible settings
    global_scale: float = 1.0
    axis_forward: str = "-Z"
    axis_up: str = "Y"
    smoothing_mode: str = "FACE"       # NONE, FACE, EDGE
    tangent_space: bool = True
    embed_textures: bool = False       # UE prefers external textures

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_path": self.output_path,
            "include_shape_keys": self.include_shape_keys,
            "include_skinning": self.include_skinning,
            "apply_modifiers": self.apply_modifiers,
            "global_scale": self.global_scale,
            "axis_forward": self.axis_forward,
            "axis_up": self.axis_up,
            "smoothing_mode": self.smoothing_mode,
            "tangent_space": self.tangent_space,
            "embed_textures": self.embed_textures,
        }


@dataclass
class MaterialSlotConfig:
    """Configuration for material slot export."""
    enabled: bool = True
    separate_zones: bool = True    # Separate materials for base/mid/tip
    bake_textures: bool = True     # Bake procedural to image textures
    texture_size: int = 2048       # Texture resolution (2048x2048)
    output_format: str = "PNG"     # PNG, TGA, EXR

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "separate_zones": self.separate_zones,
            "bake_textures": self.bake_textures,
            "texture_size": self.texture_size,
            "output_format": self.output_format,
        }


@dataclass
class ExportPreset:
    """Complete export preset configuration."""
    name: str
    lod_config: LODConfig = field(default_factory=LODConfig)
    fbx_config: FBXExportConfig = field(default_factory=FBXExportConfig)
    material_config: MaterialSlotConfig = field(default_factory=MaterialSlotConfig)
    output_dir: str = "./output"
    format: ExportFormat = ExportFormat.FBX

    @classmethod
    def default(cls) -> "ExportPreset":
        """Create default export preset."""
        return cls(
            name="Default",
            lod_config=LODConfig(),
            fbx_config=FBXExportConfig(),
            material_config=MaterialSlotConfig(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "lod_config": self.lod_config.to_dict(),
            "fbx_config": self.fbx_config.to_dict(),
            "material_config": self.material_config.to_dict(),
            "output_dir": self.output_dir,
            "format": self.format.value,
        }


# Result Types

@dataclass
class LODResult:
    """Result of LOD generation for a single level."""
    level_name: str
    triangle_count: int
    vertex_count: int
    screen_size_ratio: float
    success: bool = True
    object_name: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level_name": self.level_name,
            "triangle_count": self.triangle_count,
            "vertex_count": self.vertex_count,
            "screen_size_ratio": self.screen_size_ratio,
            "success": self.success,
            "object_name": self.object_name,
            "error": self.error,
        }


@dataclass
class MaterialSlotResult:
    """Result of material slot export."""
    slot_name: str
    material_name: str
    texture_paths: Dict[str, str]  # Map type -> path (albedo, normal, etc.)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot_name": self.slot_name,
            "material_name": self.material_name,
            "texture_paths": self.texture_paths,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class ExportResult:
    """Result of FBX export."""
    success: bool
    output_path: str = ""
    triangle_count: int = 0
    vertex_count: int = 0
    material_slots: int = 0
    has_skeleton: bool = False
    has_morph_targets: bool = False
    file_size_bytes: int = 0
    lod_level: Optional[int] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output_path": self.output_path,
            "triangle_count": self.triangle_count,
            "vertex_count": self.vertex_count,
            "material_slots": self.material_slots,
            "has_skeleton": self.has_skeleton,
            "has_morph_targets": self.has_morph_targets,
            "file_size_bytes": self.file_size_bytes,
            "lod_level": self.lod_level,
            "error": self.error,
        }


# Default Presets

DEFAULT_LOD_LEVELS = [
    LODLevel("LOD0", 1.0, 1.0),     # Full detail
    LODLevel("LOD1", 0.5, 0.5),     # 50% triangles
    LODLevel("LOD2", 0.25, 0.25),   # 25% triangles
    LODLevel("LOD3", 0.12, 0.12),   # 12% triangles
]

EXPORT_PRESETS = {
    "default": ExportPreset(
        name="Default Unreal Export",
        lod_config=LODConfig(enabled=True, levels=DEFAULT_LOD_LEVELS),
        fbx_config=FBXExportConfig(),
        material_config=MaterialSlotConfig(),
    ),
    "high_quality": ExportPreset(
        name="High Quality",
        lod_config=LODConfig(
            enabled=True,
            levels=[
                LODLevel("LOD0", 1.0, 1.0),
                LODLevel("LOD1", 0.75, 0.75),
                LODLevel("LOD2", 0.5, 0.5),
            ]
        ),
        fbx_config=FBXExportConfig(),
        material_config=MaterialSlotConfig(texture_size=4096),
    ),
    "mobile": ExportPreset(
        name="Mobile Optimized",
        lod_config=LODConfig(
            enabled=True,
            levels=[
                LODLevel("LOD0", 0.5, 0.5),
                LODLevel("LOD1", 0.25, 0.25),
                LODLevel("LOD2", 0.12, 0.12),
            ]
        ),
        fbx_config=FBXExportConfig(),
        material_config=MaterialSlotConfig(texture_size=1024),
    ),
    "preview": ExportPreset(
        name="Preview/Testing",
        lod_config=LODConfig(enabled=False),
        fbx_config=FBXExportConfig(),
        material_config=MaterialSlotConfig(bake_textures=False),
    ),
}


def get_export_preset(name: str) -> ExportPreset:
    """Get an export preset by name."""
    if name not in EXPORT_PRESETS:
        raise KeyError(f"Unknown export preset: {name}. Available: {list(EXPORT_PRESETS.keys())}")
    return EXPORT_PRESETS[name]


def list_export_presets() -> List[str]:
    """List available export preset names."""
    return list(EXPORT_PRESETS.keys())
