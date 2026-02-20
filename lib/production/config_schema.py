"""
Master Production Configuration Schema

A single YAML file that defines an entire production.

This module provides the MasterProductionConfig class that encapsulates
all production configuration in one schema - characters, locations, shots,
and output formats including retro graphics configuration.

Requirements:
- REQ-CONFIG-01: Complete production specification
- REQ-CONFIG-02: Character definitions with wardrobe
- REQ-CONFIG-03: Location specifications
- REQ-CONFIG-04: Shot list integration
- REQ-CONFIG-05: Output format specifications
- REQ-CONFIG-06: Retro graphics configuration

Part of Phase 14.2: Master Production Config

Example:
```yaml
production:
  meta:
    title: "My Short Film"
    version: "1.0"
    author: "Director Name"

  source:
    script: "scripts/my_film.fountain"
    style_preset: "cinematic_teal_orange"

  characters:
    hero:
      model: "assets/characters/hero.blend"
      wardrobe:
        default: "hero_casual"
        scenes_10_20: "hero_formal"

  locations:
    warehouse:
      preset: "industrial"
      hdri: "abandoned_warehouse"

  shots:
    - scene: 1
      template: "establishing_wide"
      location: "warehouse"
    - scene: 1
      template: "character_cu"
      character: "hero"

  outputs:
    - name: "cinema"
      format: "prores_4444"
      resolution: [4096, 2160]
    - name: "snes_version"
      format: "png_sequence"
      retro:
        palette: "snes"
        dither: "error_diffusion"
```
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import yaml
import os
import uuid

from .production_types import (
    ProductionMeta,
    CharacterConfig,
    LocationConfig,
    ShotConfig,
    StyleConfig,
    RetroConfig,
    OutputFormat,
    RenderSettings,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
)


class OutputCodec(str, Enum):
    """Supported output codecs."""
    PRORES_4444 = "prores_4444"
    PRORES_422 = "prores_422"
    H264 = "h264"
    H265 = "h265"
    PNG = "png"
    EXR = "exr"
    TIFF = "tiff"


class DitherMode(str, Enum):
    """Dithering modes for retro output."""
    NONE = "none"
    ORDERED = "ordered"
    ERROR_DIFFUSION = "error_diffusion"
    ATKINSON = "atkinson"
    FLOYD_STEINBERG = "floyd_steinberg"


@dataclass
class ProductionMeta:
    """
    Production metadata.

    Attributes:
        title: Production title
        version: Configuration version
        author: Author name
        created: Creation timestamp
        description: Production description
    """
    title: str = "Untitled Production"
    version: str = "1.0"
    author: str = ""
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "version": self.version,
            "author": self.author,
            "created": self.created,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionMeta":
        """Create from dictionary."""
        if isinstance(data, str):
            return cls(title=data)
        return cls(
            title=data.get("title", "Untitled Production"),
            version=data.get("version", "1.0"),
            author=data.get("author", ""),
            created=data.get("created", datetime.now().isoformat()),
            description=data.get("description", ""),
        )


@dataclass
class SourceConfig:
    """
    Source material configuration.

    Attributes:
        script: Path to script file (Fountain or FDX)
        style_preset: Visual style preset name
        reference_images: List of reference image paths
    """
    script: str = ""
    style_preset: str = "cinematic"
    reference_images: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "script": self.script,
            "style_preset": self.style_preset,
            "reference_images": self.reference_images,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceConfig":
        """Create from dictionary."""
        if data is None:
            return cls()
        if isinstance(data, str):
            return cls(script=data)
        return cls(
            script=data.get("script", ""),
            style_preset=data.get("style_preset", "cinematic"),
            reference_images=data.get("reference_images", []),
        )


@dataclass
class CharacterDef:
    """
    Character definition.

    Attributes:
        name: Character name (from key if not specified)
        model: Path to character model file
        voice: Voice reference
        wardrobe: Scene range to costume mappings
        variants: Variant configurations
    """
    name: str = ""
    model: str = ""
    voice: str = ""
    wardrobe: Dict[str, str] = field(default_factory=dict)
    variants: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "model": self.model,
            "voice": self.voice,
            "wardrobe": self.wardrobe,
            "variants": self.variants,
        }

    @classmethod
    def from_dict(cls, key: str, data: Dict[str, Any]) -> "CharacterDef":
        """Create from dictionary with key as fallback name."""
        if isinstance(data, str):
            return cls(name=key, model=data)
        return cls(
            name=data.get("name", key),
            model=data.get("model", ""),
            voice=data.get("voice", ""),
            wardrobe=data.get("wardrobe", {}),
            variants=data.get("variants", {}),
        )

    def get_costume_for_scene(self, scene: int) -> Optional[str]:
        """Get costume name for a specific scene number."""
        for range_key, costume in self.wardrobe.items():
            try:
                if range_key == "default":
                    continue
                if "scenes_" in range_key:
                    parts = range_key.replace("scenes_", "").split("_")
                elif "-" in range_key:
                    parts = range_key.split("-")
                else:
                    continue

                if len(parts) == 2:
                    start, end = int(parts[0]), int(parts[1])
                    if start <= scene <= end:
                        return costume
            except (ValueError, IndexError):
                continue

        # Fall back to default
        return self.wardrobe.get("default")

    def to_character_config(self) -> CharacterConfig:
        """Convert to CharacterConfig for backward compatibility."""
        return CharacterConfig(
            name=self.name,
            model=self.model,
            wardrobe_assignments=self.wardrobe,
            variants=self.variants,
        )


@dataclass
class LocationDef:
    """
    Location definition.

    Attributes:
        name: Location name (from key if not specified)
        preset: Set builder preset name
        hdri: HDRI preset or file path
        custom_setup: Path to custom .blend file
        scenes: List of scene numbers using this location
    """
    name: str = ""
    preset: str = ""
    hdri: str = ""
    custom_setup: str = ""
    scenes: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "preset": self.preset,
            "hdri": self.hdri,
            "custom_setup": self.custom_setup,
            "scenes": self.scenes,
        }

    @classmethod
    def from_dict(cls, key: str, data: Dict[str, Any]) -> "LocationDef":
        """Create from dictionary with key as fallback name."""
        if isinstance(data, str):
            return cls(name=key, preset=data)
        return cls(
            name=data.get("name", key),
            preset=data.get("preset", ""),
            hdri=data.get("hdri", ""),
            custom_setup=data.get("custom_setup", ""),
            scenes=data.get("scenes", []),
        )

    def to_location_config(self) -> LocationConfig:
        """Convert to LocationConfig for backward compatibility."""
        return LocationConfig(
            name=self.name,
            preset=self.preset,
            hdri=self.hdri,
            scenes=self.scenes,
        )


@dataclass
class ShotDef:
    """
    Shot definition.

    Attributes:
        scene: Scene number
        template: Shot template name
        name: Optional shot name (auto-generated if not provided)
        character: Primary character name
        character2: Secondary character name (for two-shots)
        location: Location name
        duration: Duration in frames (0 = auto)
        frame_range: Frame range tuple (start, end)
        notes: Director notes
        variations: Number of variations to generate
    """
    scene: int = 0
    template: str = ""
    name: str = ""
    character: str = ""
    character2: str = ""
    location: str = ""
    duration: int = 0  # 0 = auto
    frame_range: Tuple[int, int] = (0, 0)  # (0, 0) = auto
    notes: str = ""
    variations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scene": self.scene,
            "template": self.template,
            "name": self.name,
            "character": self.character,
            "character2": self.character2,
            "location": self.location,
            "duration": self.duration,
            "frame_range": list(self.frame_range),
            "notes": self.notes,
            "variations": self.variations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShotDef":
        """Create from dictionary."""
        return cls(
            scene=data.get("scene", 0),
            template=data.get("template", ""),
            name=data.get("name", ""),
            character=data.get("character", ""),
            character2=data.get("character2", ""),
            location=data.get("location", ""),
            duration=data.get("duration", 0),
            frame_range=tuple(data.get("frame_range", (0, 0))),
            notes=data.get("notes", ""),
            variations=data.get("variations", 0),
        )

    def to_shot_config(self, index: int = 0) -> ShotConfig:
        """Convert to ShotConfig for backward compatibility."""
        name = self.name or f"shot_{index + 1:03d}"
        duration = self.duration if self.duration > 0 else 120
        frame_range = self.frame_range if self.frame_range != (0, 0) else (1, duration)
        return ShotConfig(
            name=name,
            template=self.template,
            scene=self.scene,
            character=self.character,
            location=self.location,
            duration=duration,
            frame_range=frame_range,
            notes=self.notes,
            variations=self.variations,
        )


@dataclass
class RetroOutputConfig:
    """
    Retro graphics output configuration.

    Attributes:
        enabled: Whether retro processing is enabled
        palette: Color palette name (snes, nes, gameboy, etc.)
        dither: Dithering mode
        pixel_size: Pixel size multiplier
        target_resolution: Target resolution for retro output
        crt_effects: Whether to apply CRT display effects
        reduce_colors: Number of colors to reduce to (0 = auto from palette)
    """
    enabled: bool = True
    palette: str = "snes"
    dither: str = "error_diffusion"
    pixel_size: int = 2
    target_resolution: Tuple[int, int] = (256, 224)
    crt_effects: bool = False
    reduce_colors: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "palette": self.palette,
            "dither": self.dither,
            "pixel_size": self.pixel_size,
            "target_resolution": list(self.target_resolution),
            "crt_effects": self.crt_effects,
            "reduce_colors": self.reduce_colors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetroOutputConfig":
        """Create from dictionary."""
        if data is None:
            return cls()
        if isinstance(data, bool):
            return cls(enabled=data)
        return cls(
            enabled=data.get("enabled", True),
            palette=data.get("palette", "snes"),
            dither=data.get("dither", "error_diffusion"),
            pixel_size=data.get("pixel_size", 2),
            target_resolution=tuple(data.get("target_resolution", (256, 224))),
            crt_effects=data.get("crt_effects", False),
            reduce_colors=data.get("reduce_colors", 0),
        )

    def to_retro_config(self) -> RetroConfig:
        """Convert to RetroConfig for backward compatibility."""
        return RetroConfig(
            enabled=self.enabled,
            palette=self.palette,
            dither=self.dither,
            pixel_size=self.pixel_size,
            target_resolution=self.target_resolution,
            crt_effects=self.crt_effects,
        )


@dataclass
class OutputDef:
    """
    Output format definition.

    Attributes:
        name: Output format name
        format: Format identifier (prores_4444, h265, png_sequence, etc.)
        resolution: Output resolution (width, height)
        frame_rate: Frames per second
        retro: Retro configuration (if applicable)
        path: Output directory path
        codec: Video codec override
    """
    name: str = ""
    format: str = "streaming_1080p"
    resolution: Tuple[int, int] = (1920, 1080)
    frame_rate: int = 24
    retro: Optional[RetroOutputConfig] = None
    path: str = ""
    codec: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "format": self.format,
            "resolution": list(self.resolution),
            "frame_rate": self.frame_rate,
            "retro": self.retro.to_dict() if self.retro else None,
            "path": self.path,
            "codec": self.codec,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutputDef":
        """Create from dictionary."""
        if isinstance(data, str):
            return cls(name=data, format=data)

        retro_data = data.get("retro")
        retro = RetroOutputConfig.from_dict(retro_data) if retro_data else None

        return cls(
            name=data.get("name", ""),
            format=data.get("format", "streaming_1080p"),
            resolution=tuple(data.get("resolution", (1920, 1080))),
            frame_rate=data.get("frame_rate", 24),
            retro=retro,
            path=data.get("path", ""),
            codec=data.get("codec", ""),
        )

    def to_output_format(self) -> OutputFormat:
        """Convert to OutputFormat for backward compatibility."""
        retro_config = self.retro.to_retro_config() if self.retro else None
        codec = self.codec or self._get_default_codec()

        return OutputFormat(
            name=self.name,
            format=self.format,
            codec=codec,
            resolution=self.resolution,
            frame_rate=self.frame_rate,
            retro_config=retro_config,
            output_path=self.path,
        )

    def _get_default_codec(self) -> str:
        """Get default codec for format."""
        codec_map = {
            "prores_4444": "prores_4444",
            "prores_422": "prores_422",
            "h264": "h264",
            "h265": "h265",
            "png_sequence": "png",
            "exr_sequence": "exr",
            "tiff_sequence": "tiff",
        }
        return codec_map.get(self.format, "h264")


@dataclass
class MasterProductionConfig:
    """
    Complete production configuration.

    This is the root configuration for a production, containing all
    metadata, source references, characters, locations, shots, and outputs.

    Attributes:
        meta: Production metadata
        source: Source material configuration
        characters: Character definitions by name
        locations: Location definitions by name
        shots: Shot definitions in order
        outputs: Output format definitions
        style: Visual style configuration
        render: Render settings
        base_path: Base path for resolving relative paths
    """
    meta: ProductionMeta = field(default_factory=ProductionMeta)
    source: SourceConfig = field(default_factory=SourceConfig)
    characters: Dict[str, CharacterDef] = field(default_factory=dict)
    locations: Dict[str, LocationDef] = field(default_factory=dict)
    shots: List[ShotDef] = field(default_factory=list)
    outputs: List[OutputDef] = field(default_factory=list)
    style: StyleConfig = field(default_factory=StyleConfig)
    render: RenderSettings = field(default_factory=RenderSettings)
    base_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "meta": self.meta.to_dict(),
            "source": self.source.to_dict(),
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "locations": {k: v.to_dict() for k, v in self.locations.items()},
            "shots": [s.to_dict() for s in self.shots],
            "outputs": [o.to_dict() for o in self.outputs],
            "style": self.style.to_dict(),
            "render": self.render.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MasterProductionConfig":
        """Create from dictionary."""
        # Handle production wrapper
        if "production" in data:
            data = data["production"]

        meta_data = data.get("meta", {})
        source_data = data.get("source", {})
        style_data = data.get("style", {})
        render_data = data.get("render", data.get("render_settings", {}))

        characters = {}
        for key, char_data in data.get("characters", {}).items():
            characters[key] = CharacterDef.from_dict(key, char_data)

        locations = {}
        for key, loc_data in data.get("locations", {}).items():
            locations[key] = LocationDef.from_dict(key, loc_data)

        shots = [ShotDef.from_dict(s) for s in data.get("shots", [])]
        outputs = [OutputDef.from_dict(o) for o in data.get("outputs", [])]

        return cls(
            meta=ProductionMeta.from_dict(meta_data),
            source=SourceConfig.from_dict(source_data),
            characters=characters,
            locations=locations,
            shots=shots,
            outputs=outputs,
            style=StyleConfig.from_dict(style_data),
            render=RenderSettings.from_dict(render_data),
            base_path=data.get("base_path", ""),
        )

    @classmethod
    def from_yaml(cls, path: str) -> "MasterProductionConfig":
        """
        Load from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            MasterProductionConfig instance
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        config = cls.from_dict(data)
        config.base_path = str(os.path.dirname(os.path.abspath(path)))
        return config

    def to_yaml(self, path: str) -> None:
        """
        Save to YAML file.

        Args:
            path: Output path
        """
        data = self.to_dict()

        # Wrap in production key
        output = {"production": data}

        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    def validate(self) -> ValidationResult:
        """
        Validate configuration.

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult(valid=True)

        # Check meta
        if not self.meta.title:
            result.add_warning(
                "meta.title",
                "Production title is empty",
                "Set a descriptive title"
            )

        # Check shots
        if not self.shots:
            result.add_error(
                "shots",
                "No shots defined",
                "Add at least one shot configuration"
            )

        # Check outputs
        if not self.outputs:
            result.add_warning(
                "outputs",
                "No output formats defined",
                "Add at least one output format"
            )

        # Check shot references
        for i, shot in enumerate(self.shots):
            if shot.character and shot.character not in self.characters:
                result.add_error(
                    f"shots[{i}].character",
                    f"Shot references unknown character: {shot.character}",
                    f"Add character '{shot.character}' to characters section"
                )
            if shot.character2 and shot.character2 not in self.characters:
                result.add_error(
                    f"shots[{i}].character2",
                    f"Shot references unknown character: {shot.character2}",
                    f"Add character '{shot.character2}' to characters section"
                )
            if shot.location and shot.location not in self.locations:
                result.add_error(
                    f"shots[{i}].location",
                    f"Shot references unknown location: {shot.location}",
                    f"Add location '{shot.location}' to locations section"
                )

        return result

    def to_production_config(self) -> "ProductionConfig":
        """
        Convert to ProductionConfig for backward compatibility.

        Returns:
            ProductionConfig instance
        """
        from .production_types import ProductionConfig

        characters = {
            k: v.to_character_config() for k, v in self.characters.items()
        }
        locations = {
            k: v.to_location_config() for k, v in self.locations.items()
        }
        shots = [s.to_shot_config(i) for i, s in enumerate(self.shots)]
        outputs = [o.to_output_format() for o in self.outputs]

        return ProductionConfig(
            meta=self.meta,
            script_path=self.source.script,
            style=self.style,
            characters=characters,
            locations=locations,
            shots=shots,
            render_settings=self.render,
            outputs=outputs,
            base_path=self.base_path,
        )

    def get_shot_count(self) -> int:
        """Get total shot count including variations."""
        count = len(self.shots)
        for shot in self.shots:
            count += shot.variations
        return count

    def get_scenes(self) -> List[int]:
        """Get list of all scene numbers."""
        scenes = set()
        for shot in self.shots:
            if shot.scene > 0:
                scenes.add(shot.scene)
        return sorted(scenes)

    def get_retro_outputs(self) -> List[OutputDef]:
        """Get outputs with retro processing enabled."""
        return [o for o in self.outputs if o.retro and o.retro.enabled]

    def get_cinematic_outputs(self) -> List[OutputDef]:
        """Get outputs without retro processing."""
        return [o for o in self.outputs if not (o.retro and o.retro.enabled)]


# Preset configurations for common use cases
MASTER_CONFIG_PRESETS = {
    "short_film": {
        "meta": {
            "title": "Short Film",
            "version": "1.0",
        },
        "source": {
            "style_preset": "cinematic",
        },
        "render": {
            "engine": "CYCLES",
            "samples": 128,
            "quality_tier": "production",
        },
        "outputs": [
            {
                "name": "Master",
                "format": "prores_4444",
                "resolution": [1920, 1080],
                "path": "output/master/",
            },
            {
                "name": "Web",
                "format": "h264",
                "resolution": [1920, 1080],
                "path": "output/web/",
            },
        ],
    },
    "commercial": {
        "meta": {
            "title": "Commercial",
            "version": "1.0",
        },
        "source": {
            "style_preset": "product_hero",
        },
        "render": {
            "engine": "CYCLES",
            "samples": 256,
            "quality_tier": "production",
        },
        "outputs": [
            {
                "name": "Broadcast",
                "format": "prores_422",
                "resolution": [1920, 1080],
                "path": "output/broadcast/",
            },
            {
                "name": "Social",
                "format": "h264",
                "resolution": [1080, 1080],
                "path": "output/social/",
            },
        ],
    },
    "game_assets": {
        "meta": {
            "title": "Game Assets",
            "version": "1.0",
        },
        "source": {
            "style_preset": "stylized",
        },
        "render": {
            "engine": "BLENDER_EEVEE_NEXT",
            "samples": 32,
            "quality_tier": "preview",
        },
        "outputs": [
            {
                "name": "16-bit",
                "format": "png_sequence",
                "resolution": [256, 224],
                "path": "output/16bit/",
                "retro": {
                    "enabled": True,
                    "palette": "snes",
                    "dither": "error_diffusion",
                    "crt_effects": False,
                },
            },
            {
                "name": "8-bit",
                "format": "png_sequence",
                "resolution": [256, 240],
                "path": "output/8bit/",
                "retro": {
                    "enabled": True,
                    "palette": "nes",
                    "dither": "ordered",
                    "crt_effects": False,
                },
            },
        ],
    },
}


def create_master_config_from_preset(
    name: str,
    preset: str = "short_film",
    output_dir: Optional[str] = None
) -> MasterProductionConfig:
    """
    Create a new master config from preset.

    Args:
        name: Production name
        preset: Preset name (short_film, commercial, game_assets)
        output_dir: Optional output directory

    Returns:
        MasterProductionConfig instance
    """
    preset_data = MASTER_CONFIG_PRESETS.get(preset, MASTER_CONFIG_PRESETS["short_film"])

    # Deep copy preset
    import copy
    data = copy.deepcopy(preset_data)

    # Update title
    if "meta" not in data:
        data["meta"] = {}
    data["meta"]["title"] = name

    config = MasterProductionConfig.from_dict(data)

    if output_dir:
        config.base_path = output_dir
        config.to_yaml(os.path.join(output_dir, "production.yaml"))

    return config
