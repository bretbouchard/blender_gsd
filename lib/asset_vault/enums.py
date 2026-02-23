"""
Asset Vault Enumerations

Type-safe enumerations for asset formats, categories, and search modes.
"""

from enum import Enum
from typing import Dict


class AssetFormat(Enum):
    """Supported 3D asset file formats."""
    BLEND = "blend"
    FBX = "fbx"
    OBJ = "obj"
    GLB = "glb"
    GLTF = "gltf"
    STL = "stl"
    ABC = "abc"  # Alembic
    DAE = "dae"  # Collada
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, ext: str) -> "AssetFormat":
        """
        Get format from file extension.

        Args:
            ext: File extension (with or without leading dot)

        Returns:
            AssetFormat enum value
        """
        # Normalize extension
        ext = ext.lower().lstrip('.')

        extension_map: Dict[str, AssetFormat] = {
            "blend": cls.BLEND,
            "fbx": cls.FBX,
            "obj": cls.OBJ,
            "glb": cls.GLB,
            "gltf": cls.GLTF,
            "stl": cls.STL,
            "abc": cls.ABC,
            "dae": cls.DAE,
        }

        return extension_map.get(ext, cls.UNKNOWN)


class AssetCategory(Enum):
    """Asset categorization for organization and search."""
    KITBASH = "kitbash"
    PROP = "prop"
    VEHICLE = "vehicle"
    CHARACTER = "character"
    ENVIRONMENT = "environment"
    ARCHITECTURE = "architecture"
    FURNITURE = "furniture"
    ELECTRONICS = "electronics"
    NATURE = "nature"
    FOOD = "food"
    CLOTHING = "clothing"
    WEAPON = "weapon"
    SCI_FI = "sci_fi"
    FANTASY = "fantasy"
    INDUSTRIAL = "industrial"
    VFX = "vfx"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "AssetCategory":
        """
        Get category from string value.

        Args:
            value: Category name string

        Returns:
            AssetCategory enum value (UNKNOWN if not found)
        """
        value = value.lower().replace("-", "_").replace(" ", "_")
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN


class SearchMode(Enum):
    """Search mode for asset queries."""
    TEXT = "text"        # Keyword search
    TAG = "tag"          # Tag-based filtering
    VISUAL = "visual"    # Image similarity (placeholder)
    HYBRID = "hybrid"    # Combined approaches


# Extension to format lookup map for fast access
EXTENSION_MAP: Dict[str, AssetFormat] = {
    ".blend": AssetFormat.BLEND,
    ".fbx": AssetFormat.FBX,
    ".obj": AssetFormat.OBJ,
    ".glb": AssetFormat.GLB,
    ".gltf": AssetFormat.GLTF,
    ".stl": AssetFormat.STL,
    ".abc": AssetFormat.ABC,
    ".dae": AssetFormat.DAE,
}
