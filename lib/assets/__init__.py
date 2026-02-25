"""
Asset conversion and management for Blender 5.0+.

Converts external assets (KitBash3D, etc.) to Blender Asset Browser format.

Example:
    >>> from lib.assets import KitBashConverter
    >>> converter = KitBashConverter()
    >>> result = converter.convert_pack(
    ...     "Aftermath",
    ...     "/Volumes/Storage/3d/kitbash/KitBash3D - Aftermath",
    ...     "/Volumes/Storage/3d/kitbash/converted_assets/Aftermath",
    ... )

Asset Library Usage:
    >>> from lib.assets import AssetLibrary, KitBashIndexer
    >>> library = AssetLibrary()
    >>> library.add_search_path("~/assets")
    >>> results = library.search("chair", category="furniture")
    >>>
    >>> indexer = KitBashIndexer()
    >>> pack = indexer.index_pack("/path/to/KitBash3D.blend")

Asset Extraction Usage:
    >>> from lib.assets import AssetExtractor
    >>> extractor = AssetExtractor()
    >>> obj = extractor.append_object("/path/to/file.blend", "Cube")

Standalone usage:
    # Run from command line:
    blender --background --python - <<EOF
    import sys
    sys.path.insert(0, "/Users/bretbouchard/apps/blender_gsd")
    from lib.assets import KitBashConverter

    converter = KitBashConverter()
    result = converter.convert_pack(
        pack_name="Aftermath",
        source_dir="/Volumes/Storage/3d/kitbash/KitBash3D - Aftermath",
        output_dir="/Volumes/Storage/3d/kitbash/converted_assets/Aftermath",
    )
    print(f"Result: {result.to_dict()}")
    EOF
"""

from .converter import KitBashConverter, ConversionResult, PackInfo
from .material_builder import PBRMaterialBuilder, TextureSet, MaterialBuildResult

# Asset library and indexing
from .asset_library import (
    AssetLibrary,
    KitBashIndexer,
    AssetExtractor,
    AssetType,
    AssetSource,
    AssetMetadata,
    KitBashPack,
    create_asset_library,
    create_kitbash_indexer,
    create_asset_extractor,
)

# Optional: Register Blender operators if running in Blender
try:
    from .operators import register, unregister
    _operators_available = True
except ImportError:
    _operators_available = False
    register = None
    unregister = None

__all__ = [
    # Converter
    "KitBashConverter",
    "ConversionResult",
    "PackInfo",
    # Material builder
    "PBRMaterialBuilder",
    "TextureSet",
    "MaterialBuildResult",
    # Asset library
    "AssetLibrary",
    "KitBashIndexer",
    "AssetExtractor",
    "AssetType",
    "AssetSource",
    "AssetMetadata",
    "KitBashPack",
    "create_asset_library",
    "create_kitbash_indexer",
    "create_asset_extractor",
    # Operators
    "register",
    "unregister",
]
