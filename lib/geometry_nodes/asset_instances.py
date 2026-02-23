"""
Asset Instance Library

Manages asset instances for Geometry Nodes consumption.
Handles loading, caching, and instancing with scale normalization.

Implements REQ-GN-04: Asset Instance Library.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Union
from enum import Enum
from pathlib import Path
import json
import hashlib


class AssetType(Enum):
    """Asset type classification."""
    PROPS = "props"
    FURNITURE = "furniture"
    VEHICLES = "vehicles"
    CHARACTERS = "characters"
    ARCHITECTURE = "architecture"
    NATURE = "nature"
    EFFECTS = "effects"


class AssetFormat(Enum):
    """Asset file format."""
    BLEND = "blend"
    FBX = "fbx"
    OBJ = "obj"
    GLB = "glb"
    GLTF = "gltf"


@dataclass
class AssetReference:
    """
    Reference to an asset in the library.

    Attributes:
        asset_id: Unique asset identifier
        name: Display name
        asset_type: Asset type classification
        file_path: Path to asset file
        format: File format
        collection_name: Collection/object name in file
        thumbnail_path: Path to thumbnail image
        tags: Search tags
        categories: Category hierarchy
        bbox: Bounding box dimensions (w, d, h)
        reference_scale: Reference object height for normalization
        source: Asset source (kitbash3d, custom, etc.)
        license: License information
    """
    asset_id: str = ""
    name: str = ""
    asset_type: str = "props"
    file_path: str = ""
    format: str = "blend"
    collection_name: str = ""
    thumbnail_path: str = ""
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    bbox: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    reference_scale: float = 1.0
    source: str = "custom"
    license: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "asset_type": self.asset_type,
            "file_path": self.file_path,
            "format": self.format,
            "collection_name": self.collection_name,
            "thumbnail_path": self.thumbnail_path,
            "tags": self.tags,
            "categories": self.categories,
            "bbox": list(self.bbox),
            "reference_scale": self.reference_scale,
            "source": self.source,
            "license": self.license,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetReference":
        """Create from dictionary."""
        return cls(
            asset_id=data.get("asset_id", ""),
            name=data.get("name", ""),
            asset_type=data.get("asset_type", "props"),
            file_path=data.get("file_path", ""),
            format=data.get("format", "blend"),
            collection_name=data.get("collection_name", ""),
            thumbnail_path=data.get("thumbnail_path", ""),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            bbox=tuple(data.get("bbox", [1.0, 1.0, 1.0])),
            reference_scale=data.get("reference_scale", 1.0),
            source=data.get("source", "custom"),
            license=data.get("license", ""),
        )


@dataclass
class InstanceSpec:
    """
    Specification for a single instance.

    Attributes:
        instance_id: Unique instance identifier
        asset_id: Referenced asset ID
        position: World position
        rotation: Euler rotation in degrees
        scale: Uniform scale factor
        variant: Material/variant index
        lod_level: Level of detail (0=highest)
        visibility: Visibility state
        custom_properties: Custom properties for GN
    """
    instance_id: str = ""
    asset_id: str = ""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: float = 1.0
    variant: int = 0
    lod_level: int = 0
    visibility: bool = True
    custom_properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "asset_id": self.asset_id,
            "position": list(self.position),
            "rotation": list(self.rotation),
            "scale": self.scale,
            "variant": self.variant,
            "lod_level": self.lod_level,
            "visibility": self.visibility,
            "custom_properties": self.custom_properties,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstanceSpec":
        """Create from dictionary."""
        return cls(
            instance_id=data.get("instance_id", ""),
            asset_id=data.get("asset_id", ""),
            position=tuple(data.get("position", [0.0, 0.0, 0.0])),
            rotation=tuple(data.get("rotation", [0.0, 0.0, 0.0])),
            scale=data.get("scale", 1.0),
            variant=data.get("variant", 0),
            lod_level=data.get("lod_level", 0),
            visibility=data.get("visibility", True),
            custom_properties=data.get("custom_properties", {}),
        )


@dataclass
class InstancePool:
    """
    Pool of instances for efficient rendering.

    Attributes:
        pool_id: Unique pool identifier
        instances: List of instances in pool
        asset_cache: Cached asset references
        total_bounds: Combined bounding box
    """
    pool_id: str = ""
    instances: List[InstanceSpec] = field(default_factory=list)
    asset_cache: Dict[str, AssetReference] = field(default_factory=dict)
    total_bounds: Tuple[float, float, float, float, float, float] = (0, 0, 0, 1, 1, 1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pool_id": self.pool_id,
            "instances": [i.to_dict() for i in self.instances],
            "asset_cache": {k: v.to_dict() for k, v in self.asset_cache.items()},
            "total_bounds": list(self.total_bounds),
        }

    @property
    def instance_count(self) -> int:
        """Get instance count."""
        return len(self.instances)

    def add_instance(self, instance: InstanceSpec, asset: Optional[AssetReference] = None) -> None:
        """Add instance to pool."""
        self.instances.append(instance)
        if asset and instance.asset_id not in self.asset_cache:
            self.asset_cache[instance.asset_id] = asset


class ScaleNormalizer:
    """
    Normalizes asset scales to consistent reference.

    Uses reference object height to calculate scale factors.
    """

    # Standard reference heights by category
    REFERENCE_HEIGHTS: Dict[str, float] = {
        "furniture": 0.75,  # Chair seat height
        "characters": 1.75,  # Average human height
        "vehicles": 1.5,   # Average car height
        "architecture": 3.0,  # Standard ceiling height
        "props": 0.3,     # Prop reference
        "nature": 2.0,    # Average tree trunk to first branch
    }

    def __init__(self, default_reference: float = 1.0):
        """
        Initialize normalizer.

        Args:
            default_reference: Default reference height
        """
        self.default_reference = default_reference

    def normalize(self, asset: AssetReference, target_height: Optional[float] = None) -> float:
        """
        Calculate scale factor to normalize asset.

        Args:
            asset: Asset to normalize
            target_height: Target height (uses category default if not specified)

        Returns:
            Scale factor
        """
        if target_height is None:
            target_height = self.REFERENCE_HEIGHTS.get(
                asset.asset_type,
                self.default_reference
            )

        if asset.reference_scale <= 0:
            return 1.0

        return target_height / asset.reference_scale

    def denormalize(self, asset: AssetReference, normalized_scale: float) -> float:
        """
        Convert normalized scale back to original.

        Args:
            asset: Asset reference
            normalized_scale: Normalized scale factor

        Returns:
            Original scale factor
        """
        target_height = self.REFERENCE_HEIGHTS.get(
            asset.asset_type,
            self.default_reference
        )

        if asset.reference_scale <= 0:
            return normalized_scale

        return normalized_scale * (asset.reference_scale / target_height)


class AssetInstanceLibrary:
    """
    Manages asset library and instance creation.

    Handles loading assets, creating instances, and generating
    GN-compatible output.

    Usage:
        library = AssetInstanceLibrary()
        library.load_catalog("assets.json")
        instance = library.create_instance("sofa_001", position=(1, 2, 0))
        gn_data = library.to_gn_input()
    """

    def __init__(self, catalog_path: Optional[str] = None):
        """
        Initialize library.

        Args:
            catalog_path: Path to asset catalog JSON
        """
        self.assets: Dict[str, AssetReference] = {}
        self.pools: Dict[str, InstancePool] = {}
        self.normalizer = ScaleNormalizer()
        self._instance_counter = 0

        if catalog_path:
            self.load_catalog(catalog_path)

    def load_catalog(self, path: str) -> int:
        """
        Load asset catalog from JSON file.

        Args:
            path: Path to catalog JSON

        Returns:
            Number of assets loaded
        """
        with open(path, "r") as f:
            data = json.load(f)

        count = 0
        for asset_data in data.get("assets", []):
            asset = AssetReference.from_dict(asset_data)
            self.assets[asset.asset_id] = asset
            count += 1

        return count

    def save_catalog(self, path: str) -> None:
        """
        Save asset catalog to JSON file.

        Args:
            path: Output path
        """
        data = {
            "version": "1.0",
            "assets": [a.to_dict() for a in self.assets.values()],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def add_asset(self, asset: AssetReference) -> None:
        """Add asset to library."""
        self.assets[asset.asset_id] = asset

    def get_asset(self, asset_id: str) -> Optional[AssetReference]:
        """Get asset by ID."""
        return self.assets.get(asset_id)

    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        asset_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[AssetReference]:
        """
        Search for assets.

        Args:
            query: Text search in name
            tags: Required tags
            asset_type: Filter by type
            category: Filter by category

        Returns:
            List of matching assets
        """
        results = []

        for asset in self.assets.values():
            # Filter by type
            if asset_type and asset.asset_type != asset_type:
                continue

            # Filter by category
            if category and category not in asset.categories:
                continue

            # Filter by tags
            if tags and not all(t in asset.tags for t in tags):
                continue

            # Text search
            if query and query.lower() not in asset.name.lower():
                continue

            results.append(asset)

        return results

    def create_instance(
        self,
        asset_id: str,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: Optional[float] = None,
        normalize: bool = True,
        pool_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[InstanceSpec]:
        """
        Create instance of asset.

        Args:
            asset_id: Asset to instance
            position: World position
            rotation: Euler rotation
            scale: Scale factor (auto-calculated if None)
            normalize: Whether to normalize scale
            pool_id: Pool to add instance to
            **kwargs: Additional InstanceSpec parameters

        Returns:
            InstanceSpec or None if asset not found
        """
        asset = self.assets.get(asset_id)
        if not asset:
            return None

        # Calculate scale
        if scale is None and normalize:
            scale = self.normalizer.normalize(asset)
        elif scale is None:
            scale = 1.0

        # Create instance
        self._instance_counter += 1
        instance = InstanceSpec(
            instance_id=f"inst_{self._instance_counter:06d}",
            asset_id=asset_id,
            position=position,
            rotation=rotation,
            scale=scale,
            **kwargs,
        )

        # Add to pool if specified
        if pool_id:
            if pool_id not in self.pools:
                self.pools[pool_id] = InstancePool(pool_id=pool_id)
            self.pools[pool_id].add_instance(instance, asset)

        return instance

    def create_pool(self, pool_id: str) -> InstancePool:
        """Create new instance pool."""
        pool = InstancePool(pool_id=pool_id)
        self.pools[pool_id] = pool
        return pool

    def get_pool(self, pool_id: str) -> Optional[InstancePool]:
        """Get pool by ID."""
        return self.pools.get(pool_id)

    def to_gn_input(self, pool_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert to GN input format.

        Args:
            pool_id: Specific pool to export (all if None)

        Returns:
            GN-compatible dictionary
        """
        if pool_id:
            pools = [self.pools[pool_id]] if pool_id in self.pools else []
        else:
            pools = list(self.pools.values())

        return {
            "version": "1.0",
            "pools": [p.to_dict() for p in pools],
            "assets": {
                asset_id: asset.to_dict()
                for pool in pools
                for asset_id, asset in pool.asset_cache.items()
            },
        }

    def generate_instance_points(
        self,
        asset_id: str,
        points: List[Tuple[float, float, float]],
        rotations: Optional[List[Tuple[float, float, float]]] = None,
        scales: Optional[List[float]] = None,
        pool_id: Optional[str] = None,
    ) -> List[InstanceSpec]:
        """
        Generate instances at multiple points.

        Args:
            asset_id: Asset to instance
            points: List of positions
            rotations: Optional rotations (defaults to zero)
            scales: Optional scales (defaults to normalized)
            pool_id: Pool to add instances to

        Returns:
            List of InstanceSpec
        """
        instances = []
        asset = self.assets.get(asset_id)

        if not asset:
            return instances

        default_rotation = (0.0, 0.0, 0.0)
        default_scale = self.normalizer.normalize(asset)

        for i, position in enumerate(points):
            rotation = rotations[i] if rotations and i < len(rotations) else default_rotation
            scale = scales[i] if scales and i < len(scales) else default_scale

            instance = self.create_instance(
                asset_id,
                position=position,
                rotation=rotation,
                scale=scale,
                pool_id=pool_id,
            )
            if instance:
                instances.append(instance)

        return instances


def create_asset_id(file_path: str, collection_name: str) -> str:
    """
    Generate unique asset ID from file and collection.

    Args:
        file_path: Asset file path
        collection_name: Collection name in file

    Returns:
        Unique asset ID
    """
    combined = f"{file_path}:{collection_name}"
    hash_val = hashlib.md5(combined.encode()).hexdigest()[:8]
    return f"asset_{hash_val}"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "AssetType",
    "AssetFormat",
    # Data classes
    "AssetReference",
    "InstanceSpec",
    "InstancePool",
    # Classes
    "ScaleNormalizer",
    "AssetInstanceLibrary",
    # Functions
    "create_asset_id",
]
