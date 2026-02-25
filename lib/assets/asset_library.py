"""
Asset Library System - Runtime asset search and KitBash pack indexing.

Provides:
- Runtime asset search across multiple paths
- KitBash3D pack indexing and management
- Asset extraction from .blend files
- Asset metadata caching
- Fuzzy search capabilities

Usage:
    from lib.assets import AssetLibrary, KitBashIndexer

    # Initialize library
    library = AssetLibrary()
    library.add_search_path("/path/to/assets")

    # Search for assets
    results = library.search("chair", category="furniture")

    # Index KitBash pack
    indexer = KitBashIndexer()
    pack_info = indexer.index_pack("/path/to/KitBash3D.blend")
"""

from __future__ import annotations
import bpy
import os
import json
import hashlib
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import re


class AssetType(Enum):
    """Type of asset."""
    MODEL = "model"
    MATERIAL = "material"
    TEXTURE = "texture"
    COLLECTION = "collection"
    NODE_GROUP = "node_group"
    WORLD = "world"
    UNKNOWN = "unknown"


class AssetSource(Enum):
    """Source of asset."""
    LOCAL = "local"
    KITBASH3D = "kitbash3d"
    POLIIGON = "poliigon"
    TEXTURES_COM = "textures_com"
    CUSTOM = "custom"


@dataclass
class AssetMetadata:
    """Metadata for an asset."""
    name: str
    asset_type: AssetType
    source: AssetSource
    file_path: str
    blend_path: Optional[str] = None  # For linked assets
    category: str = ""
    tags: List[str] = field(default_factory=list)
    author: str = ""
    license: str = ""
    preview_path: Optional[str] = None
    file_size: int = 0
    modified_time: float = 0.0
    custom_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["asset_type"] = self.asset_type.value
        data["source"] = self.source.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetMetadata":
        """Create from dictionary."""
        data["asset_type"] = AssetType(data.get("asset_type", "unknown"))
        data["source"] = AssetSource(data.get("source", "local"))
        return cls(**data)


@dataclass
class KitBashPack:
    """Information about a KitBash3D pack."""
    name: str
    path: Path
    category: str
    asset_count: int = 0
    assets: List[AssetMetadata] = field(default_factory=list)
    indexed_time: float = 0.0
    version: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": str(self.path),
            "category": self.category,
            "asset_count": self.asset_count,
            "assets": [a.to_dict() for a in self.assets],
            "indexed_time": self.indexed_time,
            "version": self.version,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KitBashPack":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            path=Path(data["path"]),
            category=data["category"],
            asset_count=data["asset_count"],
            assets=[AssetMetadata.from_dict(a) for a in data.get("assets", [])],
            indexed_time=data.get("indexed_time", 0.0),
            version=data.get("version", ""),
            description=data.get("description", ""),
        )


class AssetLibrary:
    """
    Runtime asset library with search and caching.

    Manages asset discovery, indexing, and retrieval across
    multiple search paths.

    Usage:
        library = AssetLibrary()
        library.add_search_path("~/assets")
        library.add_search_path("~/KitBash3D")

        # Search
        results = library.search("chair")
        results = library.search("", category="furniture")
        results = library.search("metal", asset_type=AssetType.MATERIAL)
    """

    DEFAULT_SEARCH_PATHS = [
        "~/Library/Application Support/Blender/5.0/assets",
        "~/Blender/Assets",
    ]

    CACHE_FILENAME = ".asset_cache.json"

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize asset library.

        Args:
            cache_dir: Directory for cache files (default: ~/.blender_gsd)
        """
        self.search_paths: List[Path] = []
        self.assets: Dict[str, AssetMetadata] = {}  # hash -> metadata
        self._name_index: Dict[str, Set[str]] = {}  # name.lower() -> set of hashes
        self._category_index: Dict[str, Set[str]] = {}  # category -> set of hashes
        self._type_index: Dict[AssetType, Set[str]] = {}  # type -> set of hashes

        self.cache_dir = cache_dir or Path.home() / ".blender_gsd"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Add default paths
        for path in self.DEFAULT_SEARCH_PATHS:
            expanded = Path(path).expanduser()
            if expanded.exists():
                self.add_search_path(expanded)

    def add_search_path(self, path: Path | str) -> "AssetLibrary":
        """
        Add a search path.

        Args:
            path: Directory path to search for assets

        Returns:
            Self for chaining
        """
        path = Path(path).expanduser().resolve()
        if path.exists() and path not in self.search_paths:
            self.search_paths.append(path)
        return self

    def remove_search_path(self, path: Path | str) -> "AssetLibrary":
        """Remove a search path."""
        path = Path(path).expanduser().resolve()
        if path in self.search_paths:
            self.search_paths.remove(path)
        return self

    def scan(self, force: bool = False) -> int:
        """
        Scan all search paths for assets.

        Args:
            force: Force re-scan even if cached

        Returns:
            Number of assets found
        """
        # Try to load from cache
        if not force:
            self._load_cache()

        if self.assets:
            return len(self.assets)

        # Scan paths
        for path in self.search_paths:
            self._scan_path(path)

        # Save cache
        self._save_cache()

        return len(self.assets)

    def _scan_path(self, path: Path, source: AssetSource = AssetSource.LOCAL):
        """Recursively scan a path for assets."""
        if not path.exists():
            return

        for item in path.iterdir():
            if item.is_file():
                self._index_file(item, source)
            elif item.is_dir():
                # Check for KitBash-style structure
                if (item / "blend").exists():
                    self._scan_kitbash_style(item, source)
                else:
                    self._scan_path(item, source)

    def _index_file(self, file_path: Path, source: AssetSource):
        """Index a single file."""
        ext = file_path.suffix.lower()

        if ext == ".blend":
            self._index_blend_file(file_path, source)
        elif ext in {".png", ".jpg", ".jpeg", ".exr", ".hdr"}:
            self._index_texture(file_path, source)
        elif ext in {".obj", ".fbx", ".gltf", ".glb", ".stl"}:
            self._index_model(file_path, source)

    def _index_blend_file(self, file_path: Path, source: AssetSource):
        """Index assets within a .blend file."""
        try:
            # Use bpy to read blend file info
            # Note: This requires Blender context
            asset_hash = self._hash_file(file_path)

            if asset_hash in self.assets:
                return

            # Get file stats
            stat = file_path.stat()

            # Create basic metadata
            metadata = AssetMetadata(
                name=file_path.stem,
                asset_type=AssetType.COLLECTION,
                source=source,
                file_path=str(file_path),
                file_size=stat.st_size,
                modified_time=stat.st_mtime,
            )

            self._add_asset(metadata, asset_hash)

        except Exception as e:
            print(f"Warning: Could not index {file_path}: {e}")

    def _index_texture(self, file_path: Path, source: AssetSource):
        """Index a texture file."""
        asset_hash = self._hash_file(file_path)

        if asset_hash in self.assets:
            return

        stat = file_path.stat()

        # Try to determine category from path
        category = self._guess_category(file_path)

        metadata = AssetMetadata(
            name=file_path.stem,
            asset_type=AssetType.TEXTURE,
            source=source,
            file_path=str(file_path),
            category=category,
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
        )

        self._add_asset(metadata, asset_hash)

    def _index_model(self, file_path: Path, source: AssetSource):
        """Index a model file."""
        asset_hash = self._hash_file(file_path)

        if asset_hash in self.assets:
            return

        stat = file_path.stat()
        category = self._guess_category(file_path)

        metadata = AssetMetadata(
            name=file_path.stem,
            asset_type=AssetType.MODEL,
            source=source,
            file_path=str(file_path),
            category=category,
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
        )

        self._add_asset(metadata, asset_hash)

    def _scan_kitbash_style(self, pack_dir: Path, source: AssetSource):
        """Scan KitBash3D-style pack directory."""
        blend_dir = pack_dir / "blend"
        if blend_dir.exists():
            for blend_file in blend_dir.glob("*.blend"):
                self._index_blend_file(blend_file, source)

    def _guess_category(self, path: Path) -> str:
        """Guess category from file path."""
        path_str = str(path).lower()

        categories = {
            "furniture": ["chair", "table", "desk", "sofa", "bed", "cabinet", "shelf"],
            "architecture": ["wall", "floor", "ceiling", "door", "window", "roof"],
            "nature": ["tree", "plant", "rock", "grass", "water"],
            "vehicle": ["car", "truck", "plane", "ship", "bike"],
            "character": ["human", "animal", "creature", "person"],
            "prop": ["book", "bottle", "container", "tool"],
            "interior": ["lamp", "rug", "curtain", "decoration"],
            "exterior": ["building", "street", "sign", "fence"],
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in path_str:
                    return category

        return "general"

    def _hash_file(self, file_path: Path) -> str:
        """Generate a hash for a file."""
        # Use path + mtime for quick hashing
        stat = file_path.stat()
        hash_input = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def _add_asset(self, metadata: AssetMetadata, asset_hash: str):
        """Add asset to indices."""
        self.assets[asset_hash] = metadata

        # Name index
        name_lower = metadata.name.lower()
        if name_lower not in self._name_index:
            self._name_index[name_lower] = set()
        self._name_index[name_lower].add(asset_hash)

        # Category index
        if metadata.category:
            if metadata.category not in self._category_index:
                self._category_index[metadata.category] = set()
            self._category_index[metadata.category].add(asset_hash)

        # Type index
        if metadata.asset_type not in self._type_index:
            self._type_index[metadata.asset_type] = set()
        self._type_index[metadata.asset_type].add(asset_hash)

    def search(
        self,
        query: str = "",
        category: str = None,
        asset_type: AssetType = None,
        source: AssetSource = None,
        limit: int = 100
    ) -> List[AssetMetadata]:
        """
        Search for assets.

        Args:
            query: Search query (matches name and tags)
            category: Filter by category
            asset_type: Filter by asset type
            source: Filter by source
            limit: Maximum results to return

        Returns:
            List of matching assets
        """
        # Ensure scanned
        if not self.assets:
            self.scan()

        # Start with all assets
        candidate_hashes: Optional[Set[str]] = None

        # Filter by type
        if asset_type and asset_type in self._type_index:
            candidate_hashes = self._type_index[asset_type].copy()

        # Filter by category
        if category and category in self._category_index:
            cat_hashes = self._category_index[category]
            if candidate_hashes is None:
                candidate_hashes = cat_hashes.copy()
            else:
                candidate_hashes &= cat_hashes

        # If no filters, use all
        if candidate_hashes is None:
            candidate_hashes = set(self.assets.keys())

        # Filter by query
        results = []
        query_lower = query.lower()

        for asset_hash in candidate_hashes:
            asset = self.assets[asset_hash]

            # Check query
            if query_lower:
                if query_lower not in asset.name.lower():
                    if not any(query_lower in tag.lower() for tag in asset.tags):
                        continue

            # Check source
            if source and asset.source != source:
                continue

            results.append(asset)

            if len(results) >= limit:
                break

        return results

    def get_asset(self, name: str) -> Optional[AssetMetadata]:
        """Get asset by exact name."""
        name_lower = name.lower()
        if name_lower in self._name_index:
            hashes = self._name_index[name_lower]
            if hashes:
                return self.assets[list(hashes)[0]]
        return None

    def _load_cache(self):
        """Load asset cache from disk."""
        cache_path = self.cache_dir / self.CACHE_FILENAME
        if not cache_path.exists():
            return

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)

            for asset_hash, asset_data in data.get("assets", {}).items():
                metadata = AssetMetadata.from_dict(asset_data)
                self._add_asset(metadata, asset_hash)

        except Exception as e:
            print(f"Warning: Could not load asset cache: {e}")

    def _save_cache(self):
        """Save asset cache to disk."""
        cache_path = self.cache_dir / self.CACHE_FILENAME

        try:
            data = {
                "assets": {
                    h: m.to_dict() for h, m in self.assets.items()
                },
                "scan_time": datetime.now().isoformat(),
            }

            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save asset cache: {e}")

    def clear_cache(self):
        """Clear the asset cache."""
        self.assets.clear()
        self._name_index.clear()
        self._category_index.clear()
        self._type_index.clear()

        cache_path = self.cache_dir / self.CACHE_FILENAME
        if cache_path.exists():
            cache_path.unlink()


class KitBashIndexer:
    """
    Index and manage KitBash3D packs.

    KitBash3D packs have a specific structure:
    - pack_name/
      - blend/
        - KitBash3D_pack_name.blend
      - textures/
        - ...
      - preview/
        - ...

    Usage:
        indexer = KitBashIndexer()
        pack = indexer.index_pack("/path/to/pack")
        assets = pack.assets
    """

    PACK_CACHE_FILENAME = ".kitbash_cache.json"

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".blender_gsd" / "kitbash"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._packs: Dict[str, KitBashPack] = {}

    def index_pack(self, pack_path: Path | str) -> Optional[KitBashPack]:
        """
        Index a KitBash3D pack.

        Args:
            pack_path: Path to pack directory

        Returns:
            KitBashPack with indexed assets
        """
        pack_path = Path(pack_path).expanduser().resolve()
        if not pack_path.exists():
            return None

        # Check cache
        cache_key = self._cache_key(pack_path)
        if cache_key in self._packs:
            return self._packs[cache_key]

        # Create pack info
        pack = KitBashPack(
            name=pack_path.name,
            path=pack_path,
            category=self._guess_category(pack_path.name),
            indexed_time=datetime.now().timestamp(),
        )

        # Index blend files
        blend_dir = pack_path / "blend"
        if blend_dir.exists():
            for blend_file in blend_dir.glob("*.blend"):
                self._index_blend_file(pack, blend_file)

        pack.asset_count = len(pack.assets)
        self._packs[cache_key] = pack

        return pack

    def _index_blend_file(self, pack: KitBashPack, blend_path: Path):
        """Index contents of a blend file."""
        stat = blend_path.stat()

        # Create asset metadata for the blend file
        metadata = AssetMetadata(
            name=blend_path.stem,
            asset_type=AssetType.COLLECTION,
            source=AssetSource.KITBASH3D,
            file_path=str(blend_path),
            category=pack.category,
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
        )

        pack.assets.append(metadata)

    def _guess_category(self, name: str) -> str:
        """Guess pack category from name."""
        name_lower = name.lower()

        categories = {
            "sci-fi": ["sci", "future", "space", "cyber"],
            "fantasy": ["fantasy", "medieval", "castle", "magic"],
            "modern": ["modern", "city", "urban", "contemporary"],
            "interior": ["interior", "room", "furniture"],
            "exterior": ["exterior", "street", "building"],
            "nature": ["nature", "forest", "mountain", "desert"],
            "vehicle": ["vehicle", "car", "ship", "aircraft"],
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return category

        return "general"

    def _cache_key(self, pack_path: Path) -> str:
        """Generate cache key for a pack."""
        return hashlib.md5(str(pack_path).encode()).hexdigest()

    def list_packs(self) -> List[str]:
        """List all indexed packs."""
        return [p.name for p in self._packs.values()]

    def get_pack(self, name: str) -> Optional[KitBashPack]:
        """Get pack by name."""
        for pack in self._packs.values():
            if pack.name == name:
                return pack
        return None


class AssetExtractor:
    """
    Extract assets from .blend files.

    Provides functionality to link or append assets from
    external .blend files into the current scene.

    Usage:
        extractor = AssetExtractor()
        obj = extractor.append_object("/path/to/file.blend", "Cube")
        mat = extractor.link_material("/path/to/file.blend", "Material")
    """

    def __init__(self):
        self._linked_files: Set[str] = set()

    def append_collection(
        self,
        blend_path: Path | str,
        collection_name: str,
        destination_collection: Optional[bpy.types.Collection] = None
    ) -> Optional[bpy.types.Collection]:
        """
        Append a collection from a blend file.

        Args:
            blend_path: Path to source blend file
            collection_name: Name of collection to append
            destination_collection: Collection to append into (default: scene collection)

        Returns:
            The appended collection or None on failure
        """
        blend_path = str(Path(blend_path).expanduser())

        if destination_collection is None:
            destination_collection = bpy.context.scene.collection

        try:
            # Append the collection
            with bpy.data.libraries.load(blend_path) as (data_from, data_to):
                if collection_name in data_from.collections:
                    data_to.collections = [collection_name]
                else:
                    print(f"Collection '{collection_name}' not found in {blend_path}")
                    return None

            # Get the loaded collection
            if collection_name in bpy.data.collections:
                coll = bpy.data.collections[collection_name]
                destination_collection.children.link(coll)
                return coll

        except Exception as e:
            print(f"Error appending collection: {e}")

        return None

    def append_object(
        self,
        blend_path: Path | str,
        object_name: str,
        destination_collection: Optional[bpy.types.Collection] = None
    ) -> Optional[bpy.types.Object]:
        """
        Append an object from a blend file.

        Args:
            blend_path: Path to source blend file
            object_name: Name of object to append
            destination_collection: Collection to append into

        Returns:
            The appended object or None on failure
        """
        blend_path = str(Path(blend_path).expanduser())

        if destination_collection is None:
            destination_collection = bpy.context.scene.collection

        try:
            with bpy.data.libraries.load(blend_path) as (data_from, data_to):
                if object_name in data_from.objects:
                    data_to.objects = [object_name]
                else:
                    print(f"Object '{object_name}' not found in {blend_path}")
                    return None

            if object_name in bpy.data.objects:
                obj = bpy.data.objects[object_name]
                destination_collection.objects.link(obj)
                return obj

        except Exception as e:
            print(f"Error appending object: {e}")

        return None

    def link_material(
        self,
        blend_path: Path | str,
        material_name: str
    ) -> Optional[bpy.types.Material]:
        """
        Link a material from a blend file (read-only).

        Args:
            blend_path: Path to source blend file
            material_name: Name of material to link

        Returns:
            The linked material or None on failure
        """
        blend_path = str(Path(blend_path).expanduser())

        try:
            with bpy.data.libraries.load(blend_path, link=True) as (data_from, data_to):
                if material_name in data_from.materials:
                    data_to.materials = [material_name]
                else:
                    print(f"Material '{material_name}' not found in {blend_path}")
                    return None

            if material_name in bpy.data.materials:
                return bpy.data.materials[material_name]

        except Exception as e:
            print(f"Error linking material: {e}")

        return None

    def append_material(
        self,
        blend_path: Path | str,
        material_name: str
    ) -> Optional[bpy.types.Material]:
        """
        Append a material from a blend file (editable copy).

        Args:
            blend_path: Path to source blend file
            material_name: Name of material to append

        Returns:
            The appended material or None on failure
        """
        blend_path = str(Path(blend_path).expanduser())

        try:
            with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                if material_name in data_from.materials:
                    data_to.materials = [material_name]
                else:
                    print(f"Material '{material_name}' not found in {blend_path}")
                    return None

            if material_name in bpy.data.materials:
                return bpy.data.materials[material_name]

        except Exception as e:
            print(f"Error appending material: {e}")

        return None

    def list_contents(self, blend_path: Path | str) -> Dict[str, List[str]]:
        """
        List contents of a blend file.

        Args:
            blend_path: Path to blend file

        Returns:
            Dictionary with lists of objects, collections, materials, etc.
        """
        blend_path = str(Path(blend_path).expanduser())

        contents = {
            "objects": [],
            "collections": [],
            "materials": [],
            "node_groups": [],
            "worlds": [],
        }

        try:
            with bpy.data.libraries.load(blend_path) as (data_from, _):
                contents["objects"] = list(data_from.objects)
                contents["collections"] = list(data_from.collections)
                contents["materials"] = list(data_from.materials)
                contents["node_groups"] = list(data_from.node_groups)
                contents["worlds"] = list(data_from.worlds)

        except Exception as e:
            print(f"Error reading blend file: {e}")

        return contents


# Convenience functions
def create_asset_library(cache_dir: Path = None) -> AssetLibrary:
    """Create and return an asset library."""
    return AssetLibrary(cache_dir)


def create_kitbash_indexer(cache_dir: Path = None) -> KitBashIndexer:
    """Create and return a KitBash indexer."""
    return KitBashIndexer(cache_dir)


def create_asset_extractor() -> AssetExtractor:
    """Create and return an asset extractor."""
    return AssetExtractor()
