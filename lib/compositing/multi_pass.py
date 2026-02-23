"""
Multi-Pass Render Pipeline

Manages multi-pass rendering configurations including beauty passes,
utility passes, data passes, and EXR output strategies.

Implements REQ-CP-02: Multi-Pass Render Pipeline.
Implements REQ-CP-03: EXR Output Strategy.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
from enum import Enum
from pathlib import Path
import json


class PassType(Enum):
    """Render pass type classification."""
    BEAUTY = "beauty"           # Final color output
    DIFFUSE = "diffuse"         # Diffuse lighting
    GLOSSY = "glossy"          # Glossy reflections
    TRANSMISSION = "transmission"  # Transmission
    EMISSION = "emission"       # Emission
    AMBIENT_OCCLUSION = "ao"    # Ambient occlusion
    SHADOW = "shadow"          # Shadow passes
    NORMAL = "normal"          # Normal buffer
    POSITION = "position"      # World position
    UV = "uv"                  # UV coordinates
    Z_DEPTH = "z_depth"       # Z-depth buffer
    VECTOR = "vector"          # Motion vectors
    CRYPTO = "crypto"          # Cryptomatte
    OBJECT_ID = "object_id"    # Object ID
    MATERIAL_ID = "material_id"  # Material ID


class PassCategory(Enum):
    """Render pass category."""
    BEAUTY = "beauty"          # Final color passes
    LIGHTING = "lighting"      # Lighting breakdown
    SHADING = "shading"        # Shading components
    GEOMETRY = "geometry"      # Geometry data
    UTILITY = "utility"        # Utility passes
    DATA = "data"             # Raw data passes
    CRYPTO = "crypto"         # Cryptomatte passes


class OutputFormat(Enum):
    """Output file format."""
    EXR = "exr"               # OpenEXR (multi-layer)
    PNG = "png"               # PNG (8-bit)
    TIFF = "tiff"             # TIFF (16-bit)
    HDR = "hdr"               # Radiance HDR


# =============================================================================
# STANDARD PASS DEFINITIONS
# =============================================================================

STANDARD_PASSES: Dict[str, Dict[str, Any]] = {
    # Beauty passes
    "combined": {
        "name": "Combined",
        "type": "beauty",
        "category": "beauty",
        "channels": ["RGBA"],
        "description": "Final combined render",
    },
    "diffuse_direct": {
        "name": "Diffuse Direct",
        "type": "diffuse",
        "category": "lighting",
        "channels": ["RGB"],
        "description": "Direct diffuse lighting",
    },
    "diffuse_indirect": {
        "name": "Diffuse Indirect",
        "type": "diffuse",
        "category": "lighting",
        "channels": ["RGB"],
        "description": "Indirect diffuse lighting",
    },
    "diffuse_color": {
        "name": "Diffuse Color",
        "type": "diffuse",
        "category": "shading",
        "channels": ["RGB"],
        "description": "Diffuse material color",
    },
    "glossy_direct": {
        "name": "Glossy Direct",
        "type": "glossy",
        "category": "lighting",
        "channels": ["RGB"],
        "description": "Direct glossy reflections",
    },
    "glossy_indirect": {
        "name": "Glossy Indirect",
        "type": "glossy",
        "category": "lighting",
        "channels": ["RGB"],
        "description": "Indirect glossy reflections",
    },
    "glossy_color": {
        "name": "Glossy Color",
        "type": "glossy",
        "category": "shading",
        "channels": ["RGB"],
        "description": "Glossy material color",
    },
    "transmission_direct": {
        "name": "Transmission Direct",
        "type": "transmission",
        "category": "lighting",
        "channels": ["RGB"],
        "description": "Direct transmission",
    },
    "transmission_indirect": {
        "name": "Transmission Indirect",
        "type": "transmission",
        "category": "lighting",
        "channels": ["RGB"],
        "description": "Indirect transmission",
    },
    "transmission_color": {
        "name": "Transmission Color",
        "type": "transmission",
        "category": "shading",
        "channels": ["RGB"],
        "description": "Transmission material color",
    },
    "emission": {
        "name": "Emission",
        "type": "emission",
        "category": "lighting",
        "channels": ["RGB"],
        "description": "Emission pass",
    },
    "environment": {
        "name": "Environment",
        "type": "beauty",
        "category": "beauty",
        "channels": ["RGB"],
        "description": "Environment lighting",
    },
    "ao": {
        "name": "Ambient Occlusion",
        "type": "ao",
        "category": "utility",
        "channels": ["RGB"],
        "description": "Ambient occlusion",
    },
    "shadow": {
        "name": "Shadow",
        "type": "shadow",
        "category": "utility",
        "channels": ["RGB"],
        "description": "Shadow pass",
    },
}

BEAUTY_PASSES = ["combined", "diffuse_direct", "diffuse_indirect", "glossy_direct", "glossy_indirect", "transmission_direct", "transmission_indirect", "emission"]

UTILITY_PASSES: Dict[str, Dict[str, Any]] = {
    "normal": {
        "name": "Normal",
        "type": "normal",
        "category": "geometry",
        "channels": ["XYZ"],
        "description": "World normal buffer",
    },
    "position": {
        "name": "Position",
        "type": "position",
        "category": "geometry",
        "channels": ["XYZ"],
        "description": "World position buffer",
    },
    "uv": {
        "name": "UV",
        "type": "uv",
        "category": "geometry",
        "channels": ["UV"],
        "description": "UV coordinates",
    },
    "z_depth": {
        "name": "Z Depth",
        "type": "z_depth",
        "category": "data",
        "channels": ["Z"],
        "description": "Z-depth buffer",
    },
    "mist": {
        "name": "Mist",
        "type": "utility",
        "category": "utility",
        "channels": ["V"],
        "description": "Mist/fog pass",
    },
    "vector": {
        "name": "Vector",
        "type": "vector",
        "category": "data",
        "channels": ["XY", "XY"],
        "description": "Motion vectors",
    },
    "object_index": {
        "name": "Object Index",
        "type": "object_id",
        "category": "data",
        "channels": ["V"],
        "description": "Object index pass",
    },
    "material_index": {
        "name": "Material Index",
        "type": "material_id",
        "category": "data",
        "channels": ["V"],
        "description": "Material index pass",
    },
    "sample_count": {
        "name": "Sample Count",
        "type": "utility",
        "category": "data",
        "channels": ["V"],
        "description": "Sample count per pixel",
    },
    "denoising_normal": {
        "name": "Denoising Normal",
        "type": "normal",
        "category": "utility",
        "channels": ["XYZ"],
        "description": "Normal for denoising",
    },
    "denoising_albedo": {
        "name": "Denoising Albedo",
        "type": "utility",
        "category": "utility",
        "channels": ["RGB"],
        "description": "Albedo for denoising",
    },
}

DATA_PASSES = ["normal", "position", "z_depth", "vector", "object_index", "material_index"]

# EXR compression options
EXR_COMPRESSION_OPTIONS: Dict[str, Dict[str, Any]] = {
    "none": {"compression": "NONE", "description": "No compression"},
    "zip": {"compression": "ZIP", "description": "ZIP compression (default)"},
    "pz44": {"compression": "PIZ", "description": "PIZ wavelet compression"},
    "rle": {"compression": "RLE", "description": "Run-length encoding"},
    "pxr24": {"compression": "PXR24", "description": "Pixar 24-bit"},
    "b44": {"compression": "B44", "description": "B44 compression"},
    "b44a": {"compression": "B44A", "description": "B44A compression"},
    "dwaa": {"compression": "DWAA", "description": "DWAA lossy"},
    "dwab": {"compression": "DWAB", "description": "DWAB lossy"},
}

# EXR color depth options
EXR_DEPTH_OPTIONS: Dict[str, Dict[str, Any]] = {
    "16": {"depth": "16", "description": "Half float (16-bit)"},
    "32": {"depth": "32", "description": "Full float (32-bit)"},
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RenderPass:
    """
    Render pass specification.

    Attributes:
        pass_id: Unique pass identifier
        name: Display name
        pass_type: Pass type classification
        category: Pass category
        channels: Channel names
        enabled: Is pass enabled
        output_path: Output file path
        exr_layer: EXR layer name
        description: Pass description
    """
    pass_id: str = ""
    name: str = ""
    pass_type: str = "beauty"
    category: str = "beauty"
    channels: List[str] = field(default_factory=lambda: ["RGB"])
    enabled: bool = True
    output_path: str = ""
    exr_layer: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pass_id": self.pass_id,
            "name": self.name,
            "pass_type": self.pass_type,
            "category": self.category,
            "channels": self.channels,
            "enabled": self.enabled,
            "output_path": self.output_path,
            "exr_layer": self.exr_layer,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RenderPass":
        """Create from dictionary."""
        return cls(
            pass_id=data.get("pass_id", ""),
            name=data.get("name", ""),
            pass_type=data.get("pass_type", "beauty"),
            category=data.get("category", "beauty"),
            channels=data.get("channels", ["RGB"]),
            enabled=data.get("enabled", True),
            output_path=data.get("output_path", ""),
            exr_layer=data.get("exr_layer", ""),
            description=data.get("description", ""),
        )


@dataclass
class PassConfig:
    """
    Multi-pass configuration.

    Attributes:
        config_id: Unique configuration identifier
        name: Display name
        passes: Enabled render passes
        output_format: Output format
        exr_compression: EXR compression type
        exr_depth: EXR color depth
        multi_layer: Use multi-layer EXR
        separate_files: Output separate files per pass
        base_path: Base output path
        include_alpha: Include alpha in all passes
    """
    config_id: str = ""
    name: str = ""
    passes: List[str] = field(default_factory=lambda: ["combined"])
    output_format: str = "exr"
    exr_compression: str = "zip"
    exr_depth: str = "32"
    multi_layer: bool = True
    separate_files: bool = False
    base_path: str = ""
    include_alpha: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_id": self.config_id,
            "name": self.name,
            "passes": self.passes,
            "output_format": self.output_format,
            "exr_compression": self.exr_compression,
            "exr_depth": self.exr_depth,
            "multi_layer": self.multi_layer,
            "separate_files": self.separate_files,
            "base_path": self.base_path,
            "include_alpha": self.include_alpha,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PassConfig":
        """Create from dictionary."""
        return cls(
            config_id=data.get("config_id", ""),
            name=data.get("name", ""),
            passes=data.get("passes", ["combined"]),
            output_format=data.get("output_format", "exr"),
            exr_compression=data.get("exr_compression", "zip"),
            exr_depth=data.get("exr_depth", "32"),
            multi_layer=data.get("multi_layer", True),
            separate_files=data.get("separate_files", False),
            base_path=data.get("base_path", ""),
            include_alpha=data.get("include_alpha", True),
        )


@dataclass
class MultiPassSetup:
    """
    Complete multi-pass render setup.

    Attributes:
        setup_id: Unique setup identifier
        name: Display name
        pass_config: Pass configuration
        render_passes: Render pass specifications
        output_path: Output directory
        file_prefix: File name prefix
        frame_padding: Frame number padding
        view_layers: View layer configurations
    """
    setup_id: str = ""
    name: str = ""
    pass_config: Optional[PassConfig] = None
    render_passes: List[RenderPass] = field(default_factory=list)
    output_path: str = ""
    file_prefix: str = ""
    frame_padding: int = 4
    view_layers: List[str] = field(default_factory=lambda: ["ViewLayer"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "setup_id": self.setup_id,
            "name": self.name,
            "pass_config": self.pass_config.to_dict() if self.pass_config else None,
            "render_passes": [p.to_dict() for p in self.render_passes],
            "output_path": self.output_path,
            "file_prefix": self.file_prefix,
            "frame_padding": self.frame_padding,
            "view_layers": self.view_layers,
        }


# =============================================================================
# MULTI-PASS MANAGER CLASS
# =============================================================================

class MultiPassManager:
    """
    Manages multi-pass render configurations.

    Provides utilities for setting up render passes, EXR output,
    and pass management.

    Usage:
        manager = MultiPassManager()
        config = manager.create_config("production", passes=["combined", "normal", "z_depth"])
        setup = manager.create_setup(config, "/output/renders")
        manager.apply_to_scene(setup)
    """

    def __init__(self):
        """Initialize multi-pass manager."""
        self.configs: Dict[str, PassConfig] = {}
        self.setups: Dict[str, MultiPassSetup] = {}
        self.render_passes: Dict[str, RenderPass] = {}
        self._load_standard_passes()

    def _load_standard_passes(self) -> None:
        """Load standard pass definitions."""
        # Load beauty passes
        for pass_id, pass_data in STANDARD_PASSES.items():
            render_pass = RenderPass(
                pass_id=pass_id,
                name=pass_data.get("name", pass_id),
                pass_type=pass_data.get("type", "beauty"),
                category=pass_data.get("category", "beauty"),
                channels=pass_data.get("channels", ["RGB"]),
                description=pass_data.get("description", ""),
            )
            self.render_passes[pass_id] = render_pass

        # Load utility passes
        for pass_id, pass_data in UTILITY_PASSES.items():
            render_pass = RenderPass(
                pass_id=pass_id,
                name=pass_data.get("name", pass_id),
                pass_type=pass_data.get("type", "utility"),
                category=pass_data.get("category", "utility"),
                channels=pass_data.get("channels", ["RGB"]),
                description=pass_data.get("description", ""),
            )
            self.render_passes[pass_id] = render_pass

    def create_config(
        self,
        config_id: str,
        name: str = "",
        passes: Optional[List[str]] = None,
        output_format: str = "exr",
        exr_compression: str = "zip",
    ) -> PassConfig:
        """
        Create pass configuration.

        Args:
            config_id: Unique configuration identifier
            name: Display name
            passes: Enabled passes
            output_format: Output format
            exr_compression: EXR compression type

        Returns:
            Created PassConfig
        """
        config = PassConfig(
            config_id=config_id,
            name=name or config_id,
            passes=passes or ["combined"],
            output_format=output_format,
            exr_compression=exr_compression,
        )

        self.configs[config_id] = config
        return config

    def get_config(self, config_id: str) -> Optional[PassConfig]:
        """Get configuration by ID."""
        return self.configs.get(config_id)

    def list_configs(self) -> List[PassConfig]:
        """List all configurations."""
        return list(self.configs.values())

    def create_setup(
        self,
        config: PassConfig,
        output_path: str,
        file_prefix: str = "",
        view_layers: Optional[List[str]] = None,
    ) -> MultiPassSetup:
        """
        Create multi-pass setup.

        Args:
            config: Pass configuration
            output_path: Output directory
            file_prefix: File name prefix
            view_layers: View layers to configure

        Returns:
            Created MultiPassSetup
        """
        setup_id = f"{config.config_id}_setup"

        # Create render pass specifications
        render_passes = []
        for pass_id in config.passes:
            if pass_id in self.render_passes:
                render_pass = RenderPass(
                    pass_id=pass_id,
                    name=self.render_passes[pass_id].name,
                    pass_type=self.render_passes[pass_id].pass_type,
                    category=self.render_passes[pass_id].category,
                    channels=self.render_passes[pass_id].channels,
                    output_path=f"{output_path}/{pass_id}/" if config.separate_files else output_path,
                    exr_layer=pass_id,
                    description=self.render_passes[pass_id].description,
                )
                render_passes.append(render_pass)

        setup = MultiPassSetup(
            setup_id=setup_id,
            name=config.name,
            pass_config=config,
            render_passes=render_passes,
            output_path=output_path,
            file_prefix=file_prefix,
            view_layers=view_layers or ["ViewLayer"],
        )

        self.setups[setup_id] = setup
        return setup

    def get_setup(self, setup_id: str) -> Optional[MultiPassSetup]:
        """Get setup by ID."""
        return self.setups.get(setup_id)

    def list_setups(self) -> List[MultiPassSetup]:
        """List all setups."""
        return list(self.setups.values())

    def get_pass(self, pass_id: str) -> Optional[RenderPass]:
        """Get render pass by ID."""
        return self.render_passes.get(pass_id)

    def list_passes(
        self,
        category: Optional[str] = None,
        pass_type: Optional[str] = None,
    ) -> List[RenderPass]:
        """
        List render passes.

        Args:
            category: Filter by category
            pass_type: Filter by type

        Returns:
            List of matching passes
        """
        results = []
        for render_pass in self.render_passes.values():
            if category and render_pass.category != category:
                continue
            if pass_type and render_pass.pass_type != pass_type:
                continue
            results.append(render_pass)
        return results

    def get_beauty_passes(self) -> List[RenderPass]:
        """Get all beauty passes."""
        return self.list_passes(category="beauty")

    def get_utility_passes(self) -> List[RenderPass]:
        """Get all utility passes."""
        return self.list_passes(category="utility")

    def get_data_passes(self) -> List[RenderPass]:
        """Get all data passes."""
        return self.list_passes(category="data")

    def generate_exr_config(
        self,
        config: PassConfig,
        output_path: str = "",
    ) -> Dict[str, Any]:
        """
        Generate EXR output configuration.

        Args:
            config: Pass configuration
            output_path: Output path for config

        Returns:
            EXR configuration dictionary
        """
        exr_config = {
            "format": "OPEN_EXR_MULTILAYER" if config.multi_layer else "OPEN_EXR",
            "color_depth": config.exr_depth,
            "compression": config.exr_compression,
            "use_zbuffer": True,
            "exr_codec": config.exr_compression,
            "passes": [],
        }

        for pass_id in config.passes:
            if pass_id in self.render_passes:
                render_pass = self.render_passes[pass_id]
                exr_config["passes"].append({
                    "pass_id": pass_id,
                    "layer_name": render_pass.exr_layer or pass_id,
                    "channels": render_pass.channels,
                })

        if output_path:
            with open(output_path, "w") as f:
                json.dump(exr_config, f, indent=2)

        return exr_config

    def generate_compositor_setup(
        self,
        setup: MultiPassSetup,
        output_path: str = "",
    ) -> Dict[str, Any]:
        """
        Generate compositor node setup.

        Args:
            setup: Multi-pass setup
            output_path: Output path for setup

        Returns:
            Compositor setup specification
        """
        compositor = {
            "setup_id": setup.setup_id,
            "name": setup.name,
            "nodes": [],
            "links": [],
        }

        # Add render layer node
        rl_node = {
            "type": "CompositorNodeRLayers",
            "name": "Render Layers",
            "location": [0, 0],
            "properties": {
                "layer": setup.view_layers[0] if setup.view_layers else "ViewLayer",
            },
        }
        compositor["nodes"].append(rl_node)

        # Add output nodes for each pass
        x_offset = 300
        for i, render_pass in enumerate(setup.render_passes):
            if setup.pass_config and setup.pass_config.separate_files:
                # Separate file output for each pass
                output_node = {
                    "type": "CompositorNodeOutputFile",
                    "name": f"Output_{render_pass.pass_id}",
                    "location": [x_offset * (i + 1), 0],
                    "properties": {
                        "base_path": f"{setup.output_path}/{render_pass.pass_id}/",
                        "format": setup.pass_config.output_format.upper(),
                    },
                }
                compositor["nodes"].append(output_node)

                # Link
                link = {
                    "from_node": "Render Layers",
                    "from_socket": render_pass.name,
                    "to_node": f"Output_{render_pass.pass_id}",
                    "to_socket": "Image",
                }
                compositor["links"].append(link)

        # Add multi-layer EXR output
        if setup.pass_config and setup.pass_config.multi_layer and not setup.pass_config.separate_files:
            ml_node = {
                "type": "CompositorNodeOutputFile",
                "name": "Output_EXR",
                "location": [x_offset, 0],
                "properties": {
                    "base_path": f"{setup.output_path}/{setup.file_prefix}",
                    "format": "OPEN_EXR_MULTILAYER",
                },
            }
            compositor["nodes"].append(ml_node)

        if output_path:
            with open(output_path, "w") as f:
                json.dump(compositor, f, indent=2)

        return compositor

    def get_pass_statistics(self) -> Dict[str, Any]:
        """Get pass statistics."""
        stats = {
            "total_passes": len(self.render_passes),
            "by_category": {},
            "by_type": {},
        }

        for render_pass in self.render_passes.values():
            stats["by_category"][render_pass.category] = \
                stats["by_category"].get(render_pass.category, 0) + 1
            stats["by_type"][render_pass.pass_type] = \
                stats["by_type"].get(render_pass.pass_type, 0) + 1

        return stats

    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "total_configs": len(self.configs),
            "total_setups": len(self.setups),
            "pass_stats": self.get_pass_statistics(),
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_pass_config(
    name: str,
    passes: Optional[List[str]] = None,
) -> PassConfig:
    """
    Create pass configuration.

    Args:
        name: Configuration name
        passes: Enabled passes

    Returns:
        PassConfig
    """
    manager = MultiPassManager()
    return manager.create_config(
        config_id=name.lower().replace(" ", "_"),
        name=name,
        passes=passes,
    )


def create_standard_setup(
    preset: str,
    output_path: str,
) -> Optional[MultiPassSetup]:
    """
    Create standard render setup.

    Args:
        preset: Preset name (beauty, production, vfx, etc)
        output_path: Output directory

    Returns:
        MultiPassSetup or None
    """
    manager = MultiPassManager()

    presets = {
        "beauty": ["combined"],
        "lighting": BEAUTY_PASSES,
        "production": BEAUTY_PASSES + ["normal", "z_depth", "vector"],
        "vfx": BEAUTY_PASSES + list(UTILITY_PASSES.keys()),
        "minimal": ["combined", "normal", "z_depth"],
    }

    passes = presets.get(preset)
    if not passes:
        return None

    config = manager.create_config(
        config_id=preset,
        name=f"{preset.title()} Setup",
        passes=passes,
    )

    return manager.create_setup(config, output_path)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "PassType",
    "PassCategory",
    "OutputFormat",
    # Data classes
    "RenderPass",
    "PassConfig",
    "MultiPassSetup",
    # Constants
    "STANDARD_PASSES",
    "BEAUTY_PASSES",
    "UTILITY_PASSES",
    "DATA_PASSES",
    "EXR_COMPRESSION_OPTIONS",
    "EXR_DEPTH_OPTIONS",
    # Classes
    "MultiPassManager",
    # Functions
    "create_pass_config",
    "create_standard_setup",
]
