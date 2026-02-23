"""
Asset Vault - 3D Asset Management System

Provides unified discovery, indexing, search, and loading of 3D assets
from external libraries into Blender scenes.

Key Features:
- Multi-format support: blend, fbx, obj, glb, gltf, stl, abc, dae
- Fast indexing and search across 3000+ assets
- Category and tag-based organization
- Secure path handling with whitelist access control
- Scale normalization for consistent units
- Thumbnail generation (with Blender)

Usage:
    from lib.asset_vault import AssetIndexer, SearchEngine, AssetLoader

    # Build or load index
    indexer = AssetIndexer()
    index = indexer.build_index(Path("/Volumes/Storage/3d"))

    # Search for assets
    engine = SearchEngine(index)
    results = engine.search("cyberpunk vehicle")

    # Load asset into scene
    loader = AssetLoader(index)
    loader.load_asset(results[0].asset)
"""

__version__ = "0.1.0"

# Core types
from lib.asset_vault.types import (
    AssetInfo,
    AssetIndex,
    SearchResult,
    SecurityConfig,
)

# Enumerations
from lib.asset_vault.enums import (
    AssetFormat,
    AssetCategory,
    SearchMode,
    EXTENSION_MAP,
)

# Security
from lib.asset_vault.security import (
    sanitize_path,
    SecurityError,
    AuditLogger,
    ALLOWED_PATHS,
    set_allowed_paths,
    get_allowed_paths,
    validate_file_access,
)

__all__ = [
    # Version
    "__version__",
    # Types
    "AssetInfo",
    "AssetIndex",
    "SearchResult",
    "SecurityConfig",
    # Enums
    "AssetFormat",
    "AssetCategory",
    "SearchMode",
    "EXTENSION_MAP",
    # Security
    "sanitize_path",
    "SecurityError",
    "AuditLogger",
    "ALLOWED_PATHS",
    "set_allowed_paths",
    "get_allowed_paths",
    "validate_file_access",
]
