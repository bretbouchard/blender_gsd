"""
Cryptomatte Pass System

Manages cryptomatte render passes for object isolation and matte extraction.
Supports object, material, and asset cryptomatte layers.

Implements REQ-CP-01: Cryptomatte Pass System.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, Tuple
from enum import Enum
from pathlib import Path
import json
import re


class CryptomatteLayer(Enum):
    """Cryptomatte layer types."""
    OBJECT = "object"           # Object-based mattes
    MATERIAL = "material"       # Material-based mattes
    ASSET = "asset"            # Asset-based mattes
    COLLECTION = "collection"  # Collection-based mattes


class MatteType(Enum):
    """Matte extraction type."""
    OBJECT = "object"
    MATERIAL = "material"
    COLLECTION = "collection"
    CUSTOM = "custom"


# =============================================================================
# CRYPTOMATTE PRESETS
# =============================================================================

CRYPTOMATTE_PRESETS: Dict[str, Dict[str, Any]] = {
    "standard": {
        "name": "Standard Cryptomatte",
        "layers": ["object", "material"],
        "depth": 6,
        "manifest": True,
        "description": "Standard object and material mattes",
    },
    "production": {
        "name": "Production Cryptomatte",
        "layers": ["object", "material", "asset"],
        "depth": 8,
        "manifest": True,
        "description": "Full production cryptomatte with asset tracking",
    },
    "character": {
        "name": "Character Cryptomatte",
        "layers": ["object"],
        "depth": 6,
        "manifest": True,
        "include_collections": ["Characters", "Rigs", "Wardrobe"],
        "description": "Character-focused cryptomatte",
    },
    "environment": {
        "name": "Environment Cryptomatte",
        "layers": ["material", "collection"],
        "depth": 6,
        "manifest": True,
        "exclude_collections": ["Characters", "Props"],
        "description": "Environment material and collection mattes",
    },
    "vfx": {
        "name": "VFX Cryptomatte",
        "layers": ["object", "material"],
        "depth": 12,
        "manifest": True,
        "motion_blur": True,
        "description": "High-depth VFX cryptomatte",
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CryptomatteConfig:
    """
    Cryptomatte configuration.

    Attributes:
        config_id: Unique configuration identifier
        name: Display name
        layers: Enabled cryptomatte layers
        depth: Matte depth (levels of coverage)
        manifest: Generate manifest JSON
        include_collections: Collections to include
        exclude_collections: Collections to exclude
        motion_blur: Include motion blur in mattes
        anti_aliasing: Anti-aliasing quality
    """
    config_id: str = ""
    name: str = ""
    layers: List[str] = field(default_factory=lambda: ["object", "material"])
    depth: int = 6
    manifest: bool = True
    include_collections: List[str] = field(default_factory=list)
    exclude_collections: List[str] = field(default_factory=list)
    motion_blur: bool = False
    anti_aliasing: int = 4

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_id": self.config_id,
            "name": self.name,
            "layers": self.layers,
            "depth": self.depth,
            "manifest": self.manifest,
            "include_collections": self.include_collections,
            "exclude_collections": self.exclude_collections,
            "motion_blur": self.motion_blur,
            "anti_aliasing": self.anti_aliasing,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CryptomatteConfig":
        """Create from dictionary."""
        return cls(
            config_id=data.get("config_id", ""),
            name=data.get("name", ""),
            layers=data.get("layers", ["object", "material"]),
            depth=data.get("depth", 6),
            manifest=data.get("manifest", True),
            include_collections=data.get("include_collections", []),
            exclude_collections=data.get("exclude_collections", []),
            motion_blur=data.get("motion_blur", False),
            anti_aliasing=data.get("anti_aliasing", 4),
        )


@dataclass
class CryptomattePass:
    """
    Cryptomatte render pass specification.

    Attributes:
        pass_id: Unique pass identifier
        layer_type: Layer type (object, material, etc)
        pass_name: Render layer name
        exr_path: Output EXR file path
        manifest_path: Manifest JSON path
        rank: Rank in multi-layer setup
        objects: Tracked objects
        materials: Tracked materials
    """
    pass_id: str = ""
    layer_type: str = "object"
    pass_name: str = ""
    exr_path: str = ""
    manifest_path: str = ""
    rank: int = 0
    objects: List[str] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pass_id": self.pass_id,
            "layer_type": self.layer_type,
            "pass_name": self.pass_name,
            "exr_path": self.exr_path,
            "manifest_path": self.manifest_path,
            "rank": self.rank,
            "objects": self.objects,
            "materials": self.materials,
        }


@dataclass
class MatteData:
    """
    Extracted matte data.

    Attributes:
        matte_id: Unique matte identifier
        name: Object/material name
        matte_type: Type of matte
        hash_value: Cryptomatte hash
        manifest_entry: Original manifest entry
        coverage: Coverage rank
        exr_channels: EXR channel names
        color: Preview color
    """
    matte_id: str = ""
    name: str = ""
    matte_type: str = "object"
    hash_value: str = ""
    manifest_entry: Dict[str, Any] = field(default_factory=dict)
    coverage: int = 0
    exr_channels: List[str] = field(default_factory=list)
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "matte_id": self.matte_id,
            "name": self.name,
            "matte_type": self.matte_type,
            "hash_value": self.hash_value,
            "manifest_entry": self.manifest_entry,
            "coverage": self.coverage,
            "exr_channels": self.exr_channels,
            "color": list(self.color),
        }


# =============================================================================
# CRYPTOMATTE MANAGER CLASS
# =============================================================================

class CryptomatteManager:
    """
    Manages cryptomatte configuration and matte extraction.

    Provides utilities for setting up cryptomatte passes and
    extracting mattes from rendered EXR files.

    Usage:
        manager = CryptomatteManager()
        config = manager.create_config("production")
        manager.setup_render_passes(config)
        mattes = manager.extract_mattes("render.exr", "manifest.json")
    """

    def __init__(self):
        """Initialize cryptomatte manager."""
        self.configs: Dict[str, CryptomatteConfig] = {}
        self.passes: Dict[str, CryptomattePass] = {}
        self.mattes: Dict[str, MatteData] = {}
        self._load_presets()

    def _load_presets(self) -> None:
        """Load built-in presets."""
        for preset_id, preset_data in CRYPTOMATTE_PRESETS.items():
            config = CryptomatteConfig(
                config_id=preset_id,
                name=preset_data.get("name", preset_id),
                layers=preset_data.get("layers", ["object", "material"]),
                depth=preset_data.get("depth", 6),
                manifest=preset_data.get("manifest", True),
                include_collections=preset_data.get("include_collections", []),
                exclude_collections=preset_data.get("exclude_collections", []),
                motion_blur=preset_data.get("motion_blur", False),
            )
            self.configs[preset_id] = config

    def create_config(
        self,
        config_id: str,
        name: str = "",
        layers: Optional[List[str]] = None,
        depth: int = 6,
        preset: Optional[str] = None,
    ) -> CryptomatteConfig:
        """
        Create cryptomatte configuration.

        Args:
            config_id: Unique configuration identifier
            name: Display name
            layers: Enabled layers
            depth: Matte depth
            preset: Base preset to use

        Returns:
            Created CryptomatteConfig
        """
        if preset and preset in self.configs:
            base = self.configs[preset]
            config = CryptomatteConfig(
                config_id=config_id,
                name=name or base.name,
                layers=layers or base.layers,
                depth=depth or base.depth,
                manifest=base.manifest,
                include_collections=base.include_collections,
                exclude_collections=base.exclude_collections,
                motion_blur=base.motion_blur,
            )
        else:
            config = CryptomatteConfig(
                config_id=config_id,
                name=name or config_id,
                layers=layers or ["object", "material"],
                depth=depth,
            )

        self.configs[config_id] = config
        return config

    def get_config(self, config_id: str) -> Optional[CryptomatteConfig]:
        """Get configuration by ID."""
        return self.configs.get(config_id)

    def list_configs(self) -> List[CryptomatteConfig]:
        """List all configurations."""
        return list(self.configs.values())

    def create_pass(
        self,
        pass_id: str,
        layer_type: str,
        pass_name: str = "",
        exr_path: str = "",
    ) -> CryptomattePass:
        """
        Create cryptomatte render pass.

        Args:
            pass_id: Unique pass identifier
            layer_type: Layer type (object, material, etc)
            pass_name: Render layer name
            exr_path: Output EXR path

        Returns:
            Created CryptomattePass
        """
        cryp_pass = CryptomattePass(
            pass_id=pass_id,
            layer_type=layer_type,
            pass_name=pass_name or f"Cryptomatte_{layer_type}",
            exr_path=exr_path,
            manifest_path=exr_path.replace(".exr", ".json") if exr_path else "",
        )

        self.passes[pass_id] = cryp_pass
        return cryp_pass

    def get_pass(self, pass_id: str) -> Optional[CryptomattePass]:
        """Get pass by ID."""
        return self.passes.get(pass_id)

    def setup_render_passes(
        self,
        config: CryptomatteConfig,
        base_path: str = "",
    ) -> List[CryptomattePass]:
        """
        Setup render passes from configuration.

        Args:
            config: Cryptomatte configuration
            base_path: Base output path

        Returns:
            List of created passes
        """
        passes = []
        for rank, layer in enumerate(config.layers):
            pass_id = f"{config.config_id}_{layer}"
            exr_path = ""
            if base_path:
                exr_path = f"{base_path}/{layer}/cryptomatte_{layer}.exr"

            cryp_pass = self.create_pass(
                pass_id=pass_id,
                layer_type=layer,
                pass_name=f"Cryptomatte_{layer}",
                exr_path=exr_path,
            )
            cryp_pass.rank = rank
            passes.append(cryp_pass)

        return passes

    def parse_manifest(self, manifest_path: str) -> Dict[str, MatteData]:
        """
        Parse cryptomatte manifest JSON.

        Args:
            manifest_path: Path to manifest file

        Returns:
            Dictionary of matte data
        """
        mattes = {}

        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
        except (IOError, json.JSONDecodeError):
            return mattes

        # Parse manifest entries
        entries = manifest.get("entries", {})
        for hash_val, entry in entries.items():
            name = entry.get("name", "")
            matte_type = entry.get("type", "object")

            matte = MatteData(
                matte_id=f"matte_{hash_val}",
                name=name,
                matte_type=matte_type,
                hash_value=hash_val,
                manifest_entry=entry,
            )

            mattes[name] = matte
            self.mattes[name] = matte

        return mattes

    def extract_matte(
        self,
        matte_name: str,
        exr_path: str,
        manifest_path: str,
        output_path: str = "",
    ) -> Optional[MatteData]:
        """
        Extract matte for specific object/material.

        Args:
            matte_name: Name of object/material
            exr_path: Path to EXR file
            manifest_path: Path to manifest
            output_path: Optional output path for matte

        Returns:
            MatteData if found, None otherwise
        """
        # Parse manifest if not already done
        if matte_name not in self.mattes:
            self.parse_manifest(manifest_path)

        matte = self.mattes.get(matte_name)
        if not matte:
            return None

        # Store output path
        if output_path:
            matte.manifest_entry["output_path"] = output_path

        return matte

    def extract_mattes(
        self,
        names: List[str],
        exr_path: str,
        manifest_path: str,
        output_dir: str = "",
    ) -> Dict[str, MatteData]:
        """
        Extract multiple mattes.

        Args:
            names: List of object/material names
            exr_path: Path to EXR file
            manifest_path: Path to manifest
            output_dir: Output directory for mattes

        Returns:
            Dictionary of extracted mattes
        """
        results = {}
        for name in names:
            output_path = f"{output_dir}/{name}.exr" if output_dir else ""
            matte = self.extract_matte(name, exr_path, manifest_path, output_path)
            if matte:
                results[name] = matte

        return results

    def get_matte_by_hash(self, hash_value: str) -> Optional[MatteData]:
        """Get matte by hash value."""
        for matte in self.mattes.values():
            if matte.hash_value == hash_value:
                return matte
        return None

    def get_mattes_by_type(self, matte_type: str) -> List[MatteData]:
        """Get all mattes of specific type."""
        return [
            m for m in self.mattes.values()
            if m.matte_type == matte_type
        ]

    def get_mattes_by_prefix(self, prefix: str) -> List[MatteData]:
        """Get mattes with name prefix."""
        return [
            m for m in self.mattes.values()
            if m.name.startswith(prefix)
        ]

    def generate_compositor_setup(
        self,
        config: CryptomatteConfig,
        output_path: str = "",
    ) -> Dict[str, Any]:
        """
        Generate compositor node setup specification.

        Args:
            config: Cryptomatte configuration
            output_path: Output path for specification

        Returns:
            Compositor setup specification
        """
        setup = {
            "config_id": config.config_id,
            "name": config.name,
            "nodes": [],
            "links": [],
        }

        # Add cryptomatte nodes for each layer
        for i, layer in enumerate(config.layers):
            node = {
                "type": "CompositorNodeCryptomatte",
                "name": f"Cryptomatte_{layer}",
                "location": [300 * i, 0],
                "properties": {
                    "matte_type": layer,
                    "depth": config.depth,
                    "anti_aliasing": config.anti_aliasing,
                },
            }
            setup["nodes"].append(node)

            # Add output node
            output_node = {
                "type": "CompositorNodeOutputFile",
                "name": f"Output_{layer}",
                "location": [300 * i + 200, 0],
                "properties": {
                    "format": "OPEN_EXR",
                    "base_path": output_path,
                },
            }
            setup["nodes"].append(output_node)

            # Link nodes
            link = {
                "from_node": f"Cryptomatte_{layer}",
                "from_socket": " Matte",
                "to_node": f"Output_{layer}",
                "to_socket": "Image",
            }
            setup["links"].append(link)

        if output_path:
            with open(output_path, "w") as f:
                json.dump(setup, f, indent=2)

        return setup

    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "total_configs": len(self.configs),
            "total_passes": len(self.passes),
            "total_mattes": len(self.mattes),
            "mattes_by_type": {
                matte_type: len(self.get_mattes_by_type(matte_type))
                for matte_type in ["object", "material", "collection"]
            },
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_cryptomatte_config(
    name: str,
    layers: Optional[List[str]] = None,
    depth: int = 6,
) -> CryptomatteConfig:
    """
    Create cryptomatte configuration.

    Args:
        name: Configuration name
        layers: Enabled layers
        depth: Matte depth

    Returns:
        CryptomatteConfig
    """
    manager = CryptomatteManager()
    return manager.create_config(
        config_id=name.lower().replace(" ", "_"),
        name=name,
        layers=layers,
        depth=depth,
    )


def extract_matte_from_manifest(
    manifest_path: str,
    matte_name: str,
) -> Optional[MatteData]:
    """
    Extract matte data from manifest.

    Args:
        manifest_path: Path to manifest JSON
        matte_name: Name to extract

    Returns:
        MatteData if found
    """
    manager = CryptomatteManager()
    manager.parse_manifest(manifest_path)
    return manager.mattes.get(matte_name)


def hash_to_rgb(hash_value: str) -> Tuple[float, float, float]:
    """
    Convert cryptomatte hash to RGB color.

    Args:
        hash_value: Cryptomatte hash string

    Returns:
        RGB tuple (0-1 range)
    """
    # Parse MM3 hash
    try:
        val = int(hash_value, 16)
        r = ((val >> 16) & 0xFF) / 255.0
        g = ((val >> 8) & 0xFF) / 255.0
        b = (val & 0xFF) / 255.0
        return (r, g, b)
    except ValueError:
        return (0.5, 0.5, 0.5)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "CryptomatteLayer",
    "MatteType",
    # Data classes
    "CryptomatteConfig",
    "CryptomattePass",
    "MatteData",
    # Constants
    "CRYPTOMATTE_PRESETS",
    # Classes
    "CryptomatteManager",
    # Functions
    "create_cryptomatte_config",
    "extract_matte_from_manifest",
    "hash_to_rgb",
]
