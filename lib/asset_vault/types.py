"""
Asset Vault Type Definitions

Core data structures for asset management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .enums import AssetCategory, AssetFormat


@dataclass
class AssetInfo:
    """
    Complete information about a single 3D asset.

    All paths are stored as absolute paths after sanitization.
    """
    path: Path                              # Absolute path to asset file
    name: str                               # Asset name (filename without extension)
    format: AssetFormat                     # Detected file format
    category: Optional[AssetCategory] = None  # Assigned category
    tags: List[str] = field(default_factory=list)  # Tags for search
    dimensions: Optional[Tuple[float, float, float]] = None  # Bounding box (x, y, z) in meters
    materials: List[str] = field(default_factory=list)  # Material names
    textures: List[Path] = field(default_factory=list)  # Texture file paths
    objects: List[str] = field(default_factory=list)  # Object/collection names in file
    scale_reference: Optional[str] = None  # e.g., "1_unit = 1_meter"
    thumbnail_path: Optional[Path] = None  # Path to preview thumbnail
    file_size: int = 0                      # File size in bytes
    last_modified: Optional[datetime] = None  # File modification time
    metadata: Dict[str, Any] = field(default_factory=dict)  # Format-specific extras

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "path": str(self.path),
            "name": self.name,
            "format": self.format.value,
            "category": self.category.value if self.category else None,
            "tags": self.tags,
            "dimensions": list(self.dimensions) if self.dimensions else None,
            "materials": self.materials,
            "textures": [str(t) for t in self.textures],
            "objects": self.objects,
            "scale_reference": self.scale_reference,
            "thumbnail_path": str(self.thumbnail_path) if self.thumbnail_path else None,
            "file_size": self.file_size,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetInfo":
        """Create from dictionary (loaded from JSON)."""
        return cls(
            path=Path(data["path"]),
            name=data["name"],
            format=AssetFormat(data["format"]),
            category=AssetCategory(data["category"]) if data.get("category") else None,
            tags=data.get("tags", []),
            dimensions=tuple(data["dimensions"]) if data.get("dimensions") else None,
            materials=data.get("materials", []),
            textures=[Path(t) for t in data.get("textures", [])],
            objects=data.get("objects", []),
            scale_reference=data.get("scale_reference"),
            thumbnail_path=Path(data["thumbnail_path"]) if data.get("thumbnail_path") else None,
            file_size=data.get("file_size", 0),
            last_modified=datetime.fromisoformat(data["last_modified"]) if data.get("last_modified") else None,
            metadata=data.get("metadata", {}),
        )


@dataclass
class AssetIndex:
    """
    Complete index of all assets in a library.

    Maintains mappings for quick lookups by path, category, and tags.
    """
    version: str = "1.0"                    # Schema version
    created_at: Optional[datetime] = None   # Index creation time
    updated_at: Optional[datetime] = None   # Last update time
    root_path: Optional[Path] = None        # Root directory of the library
    assets: Dict[str, AssetInfo] = field(default_factory=dict)  # Keyed by relative path
    categories: Dict[str, List[str]] = field(default_factory=dict)  # category -> asset paths
    tags: Dict[str, List[str]] = field(default_factory=dict)  # tag -> asset paths

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "root_path": str(self.root_path) if self.root_path else None,
            "assets": {k: v.to_dict() for k, v in self.assets.items()},
            "categories": self.categories,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetIndex":
        """Create from dictionary (loaded from JSON)."""
        index = cls(
            version=data.get("version", "1.0"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            root_path=Path(data["root_path"]) if data.get("root_path") else None,
            categories=data.get("categories", {}),
            tags=data.get("tags", {}),
        )
        # Reconstruct AssetInfo objects
        for path, asset_data in data.get("assets", {}).items():
            index.assets[path] = AssetInfo.from_dict(asset_data)
        return index


@dataclass
class SearchResult:
    """
    Result from asset search with relevance scoring.
    """
    asset: AssetInfo                         # The matched asset
    score: float = 1.0                       # Relevance score (0.0 to 1.0)
    match_type: str = "exact"                # "text", "tag", "visual", "exact"
    highlights: List[str] = field(default_factory=list)  # Matched text fragments


@dataclass
class SecurityConfig:
    """
    Security configuration for asset access.
    """
    allowed_paths: List[Path] = field(default_factory=list)  # Whitelist of directories
    max_file_size_mb: int = 500              # Maximum file size in MB
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ".blend", ".fbx", ".obj", ".glb", ".gltf", ".stl", ".abc", ".dae"
    ])
    audit_log_path: Optional[Path] = None    # Path to audit log file

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "allowed_paths": [str(p) for p in self.allowed_paths],
            "max_file_size_mb": self.max_file_size_mb,
            "allowed_extensions": self.allowed_extensions,
            "audit_log_path": str(self.audit_log_path) if self.audit_log_path else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityConfig":
        """Create from dictionary."""
        return cls(
            allowed_paths=[Path(p) for p in data.get("allowed_paths", [])],
            max_file_size_mb=data.get("max_file_size_mb", 500),
            allowed_extensions=data.get("allowed_extensions", []),
            audit_log_path=Path(data["audit_log_path"]) if data.get("audit_log_path") else None,
        )
