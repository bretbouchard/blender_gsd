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

# Optional: Register Blender operators if running in Blender
try:
    from .operators import register, unregister
    _operators_available = True
except ImportError:
    _operators_available = False
    register = None
    unregister = None

__all__ = [
    "KitBashConverter",
    "ConversionResult",
    "PackInfo",
    "PBRMaterialBuilder",
    "TextureSet",
    "MaterialBuildResult",
    "register",
    "unregister",
]
