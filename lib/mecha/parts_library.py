"""
Mecha Parts Library

Manages mechanical parts catalog for robot and vehicle assembly.
Supports indexing, searching, and loading parts from various sources.

Implements REQ-CH-04: Mecha/Robot Parts Library (Vitaly Bulgarov).

Asset Sources:
- Vitaly Bulgarov: ULTRABORG, Black Widow, Black Phoenix, etc.
- KitBash3D: Sci-Fi, vehicles
- Custom parts: User library
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Union
from enum import Enum
from pathlib import Path
import json
import hashlib


class PartCategory(Enum):
    """Part category classification."""
    TORSO = "torso"
    HEAD = "head"
    ARM = "arm"
    HAND = "hand"
    LEG = "leg"
    FOOT = "foot"
    ARMOR = "armor"
    WEAPON = "weapon"
    ACCESSORY = "accessory"
    JOINT = "joint"
    CABLE = "cable"
    PISTON = "piston"
    PANEL = "panel"
    DETAIL = "detail"
    PROP = "prop"
    VEHICLE = "vehicle"


class PartStyle(Enum):
    """Part visual style."""
    CYBER = "cyber"           # High-tech, sleek
    INDUSTRIAL = "industrial"  # Rugged, mechanical
    MILITARY = "military"     # Tactical, armored
    ORGANIC = "organic"       # Biomimetic, flowing
    RETRO = "retro"           # Vintage, classic
    SCIFI = "scifi"          # Futuristic, advanced
    STEAMPUNK = "steampunk"   # Victorian-tech
    MINIMAL = "minimal"       # Clean, simple


class PartSource(Enum):
    """Part source library."""
    VITALY_BULGAROV = "vitaly_bulgarov"
    KITBASH3D = "kitbash3d"
    KPACKS = "kpacks"
    CUSTOM = "custom"
    BLENDER_GSD = "blender_gsd"


class AttachmentType(Enum):
    """Attachment point type."""
    BALL_JOINT = "ball_joint"    # Spherical socket
    HINGE = "hinge"              # Single axis rotation
    SLIDER = "slider"            # Linear movement
    FIXED = "fixed"              # No movement
    UNIVERSAL = "universal"      # Multi-axis
    MAGNETIC = "magnetic"        # Snap connection
    PLUG = "plug"                # Insert connection


# =============================================================================
# VITALY BULGAROV PACK DEFINITIONS
# =============================================================================

VITALY_BULGAROV_PACKS: Dict[str, Dict[str, Any]] = {
    "ultraborg_armor": {
        "name": "ULTRABORG SUBD Armor Pack",
        "category": "armor",
        "style": "cyber",
        "parts_count": 120,
        "polygons": "subd",
        "features": ["armor_plates", "shoulder_pads", "chest_pieces", "back_plates"],
    },
    "ultraborg_cyber_muscles": {
        "name": "ULTRABORG SUBD Cyber Muscles Pack",
        "category": "joint",
        "style": "cyber",
        "parts_count": 85,
        "polygons": "subd",
        "features": ["muscle_groups", "tendons", "synthetic_fibers"],
    },
    "ultraborg_pistons": {
        "name": "ULTRABORG SUBD Pistons Caps",
        "category": "piston",
        "style": "industrial",
        "parts_count": 45,
        "polygons": "subd",
        "features": ["pistons", "caps", "cylinders", "shock_absorbers"],
    },
    "ultraborg_robo_guts": {
        "name": "ULTRABORG SUBD Robo Guts",
        "category": "detail",
        "style": "scifi",
        "parts_count": 95,
        "polygons": "subd",
        "features": ["internal_parts", "circuits", "exposed_mechanisms"],
    },
    "ultraborg_wires_cables": {
        "name": "ULTRABORG SUBD Wires Cables",
        "category": "cable",
        "style": "industrial",
        "parts_count": 75,
        "polygons": "subd",
        "features": ["cables", "wire_bundles", "connectors", "hoses"],
    },
    "black_widow": {
        "name": "Black Widow Pack",
        "category": "vehicle",
        "style": "military",
        "parts_count": 180,
        "polygons": "subd",
        "features": ["vehicle_parts", "weapons", "armor_panels"],
    },
    "black_phoenix": {
        "name": "Black Phoenix",
        "category": "vehicle",
        "style": "scifi",
        "parts_count": 200,
        "polygons": "subd",
        "features": ["mech_parts", "wings", "thrusters", "armor"],
    },
    "crates": {
        "name": "Crates",
        "category": "prop",
        "style": "industrial",
        "parts_count": 30,
        "polygons": "subd",
        "features": ["containers", "boxes", "storage"],
    },
    "floor_panels": {
        "name": "Floor Panels",
        "category": "panel",
        "style": "industrial",
        "parts_count": 40,
        "polygons": "subd",
        "features": ["floor_tiles", "grates", "metal_panels"],
    },
    "megastructure": {
        "name": "Megastructure",
        "category": "panel",
        "style": "scifi",
        "parts_count": 150,
        "polygons": "subd",
        "features": ["large_panels", "structural_elements", "frames"],
    },
    "props": {
        "name": "Props",
        "category": "prop",
        "style": "industrial",
        "parts_count": 85,
        "polygons": "subd",
        "features": ["misc_parts", "tools", "equipment"],
    },
    "scifi_crates": {
        "name": "Sci-Fi Crates",
        "category": "prop",
        "style": "scifi",
        "parts_count": 35,
        "polygons": "subd",
        "features": ["futuristic_containers", "storage_units"],
    },
}

# =============================================================================
# SCALE REFERENCE
# =============================================================================

PART_SCALE_REFERENCE: Dict[str, float] = {
    # Reference heights for scale normalization
    "humanoid_torso": 0.5,      # Torso height
    "humanoid_head": 0.25,      # Head height
    "humanoid_arm": 0.6,        # Full arm length
    "humanoid_leg": 0.9,        # Full leg length
    "vehicle_wheel": 0.7,       # Standard wheel diameter
    "mech_torso": 1.2,          # Large mech torso
    "vehicle_body": 2.0,        # Vehicle body length
    "prop_standard": 0.3,       # Standard prop size
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AttachmentPoint:
    """
    Attachment point for part connection.

    Attributes:
        name: Point identifier
        point_type: Type of connection
        position: Local position
        rotation: Local rotation (Euler degrees)
        axis: Primary axis for joint movement
        limits: Rotation/translation limits
        parent_point: Compatible parent attachment point
    """
    name: str = ""
    point_type: str = "fixed"
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    axis: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    parent_point: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "point_type": self.point_type,
            "position": list(self.position),
            "rotation": list(self.rotation),
            "axis": list(self.axis),
            "limits": self.limits,
            "parent_point": self.parent_point,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttachmentPoint":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            point_type=data.get("point_type", "fixed"),
            position=tuple(data.get("position", [0.0, 0.0, 0.0])),
            rotation=tuple(data.get("rotation", [0.0, 0.0, 0.0])),
            axis=tuple(data.get("axis", [0.0, 1.0, 0.0])),
            limits=data.get("limits", {}),
            parent_point=data.get("parent_point", ""),
        )


@dataclass
class PartVariant:
    """
    Part variant specification.

    Attributes:
        variant_id: Unique variant identifier
        name: Display name
        modifiers: Modifier settings
        material_override: Material preset override
        scale_factor: Scale multiplier
    """
    variant_id: str = ""
    name: str = ""
    modifiers: Dict[str, Any] = field(default_factory=dict)
    material_override: str = ""
    scale_factor: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "variant_id": self.variant_id,
            "name": self.name,
            "modifiers": self.modifiers,
            "material_override": self.material_override,
            "scale_factor": self.scale_factor,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PartVariant":
        """Create from dictionary."""
        return cls(
            variant_id=data.get("variant_id", ""),
            name=data.get("name", ""),
            modifiers=data.get("modifiers", {}),
            material_override=data.get("material_override", ""),
            scale_factor=data.get("scale_factor", 1.0),
        )


@dataclass
class PartSpec:
    """
    Part specification for catalog entry.

    Attributes:
        part_id: Unique part identifier
        name: Display name
        category: Part category
        style: Visual style
        source: Source library
        file_path: Path to part file
        collection_name: Collection name in file
        thumbnail_path: Path to thumbnail
        bounding_box: Bounding box dimensions (w, d, h)
        attachment_points: Available attachment points
        variants: Available variants
        tags: Search tags
        material_presets: Compatible material presets
        lod_levels: Available LOD levels
        description: Part description
    """
    part_id: str = ""
    name: str = ""
    category: str = "prop"
    style: str = "industrial"
    source: str = "custom"
    file_path: str = ""
    collection_name: str = ""
    thumbnail_path: str = ""
    bounding_box: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    attachment_points: List[AttachmentPoint] = field(default_factory=list)
    variants: List[PartVariant] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    material_presets: List[str] = field(default_factory=list)
    lod_levels: int = 1
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "part_id": self.part_id,
            "name": self.name,
            "category": self.category,
            "style": self.style,
            "source": self.source,
            "file_path": self.file_path,
            "collection_name": self.collection_name,
            "thumbnail_path": self.thumbnail_path,
            "bounding_box": list(self.bounding_box),
            "attachment_points": [a.to_dict() for a in self.attachment_points],
            "variants": [v.to_dict() for v in self.variants],
            "tags": self.tags,
            "material_presets": self.material_presets,
            "lod_levels": self.lod_levels,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PartSpec":
        """Create from dictionary."""
        return cls(
            part_id=data.get("part_id", ""),
            name=data.get("name", ""),
            category=data.get("category", "prop"),
            style=data.get("style", "industrial"),
            source=data.get("source", "custom"),
            file_path=data.get("file_path", ""),
            collection_name=data.get("collection_name", ""),
            thumbnail_path=data.get("thumbnail_path", ""),
            bounding_box=tuple(data.get("bounding_box", [1.0, 1.0, 1.0])),
            attachment_points=[AttachmentPoint.from_dict(a) for a in data.get("attachment_points", [])],
            variants=[PartVariant.from_dict(v) for v in data.get("variants", [])],
            tags=data.get("tags", []),
            material_presets=data.get("material_presets", []),
            lod_levels=data.get("lod_levels", 1),
            description=data.get("description", ""),
        )


# =============================================================================
# PARTS LIBRARY CLASS
# =============================================================================

class PartsLibrary:
    """
    Manages catalog of mechanical parts.

    Handles indexing, searching, and loading parts from
    various sources (Vitaly Bulgarov, KitBash3D, custom).

    Usage:
        library = PartsLibrary()
        library.index_vitaly_bulgarov("/path/to/packs/")
        parts = library.search(category="armor", style="cyber")
    """

    def __init__(self, catalog_path: Optional[str] = None):
        """
        Initialize parts library.

        Args:
            catalog_path: Path to existing catalog JSON
        """
        self.parts: Dict[str, PartSpec] = {}
        self._index_cache: Dict[str, List[str]] = {}
        self._part_counter = 0

        if catalog_path:
            self.load_catalog(catalog_path)

    def load_catalog(self, path: str) -> int:
        """
        Load parts catalog from JSON.

        Args:
            path: Path to catalog JSON

        Returns:
            Number of parts loaded
        """
        with open(path, "r") as f:
            data = json.load(f)

        count = 0
        for part_data in data.get("parts", []):
            part = PartSpec.from_dict(part_data)
            self.parts[part.part_id] = part
            count += 1

        self._rebuild_index()
        return count

    def save_catalog(self, path: str) -> None:
        """
        Save parts catalog to JSON.

        Args:
            path: Output path
        """
        data = {
            "version": "1.0",
            "parts": [p.to_dict() for p in self.parts.values()],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def add_part(self, part: PartSpec) -> None:
        """Add part to library."""
        self.parts[part.part_id] = part
        self._rebuild_index()

    def get_part(self, part_id: str) -> Optional[PartSpec]:
        """Get part by ID."""
        return self.parts.get(part_id)

    def _rebuild_index(self) -> None:
        """Rebuild search index."""
        self._index_cache = {
            "category": {},
            "style": {},
            "source": {},
            "tags": {},
        }

        for part_id, part in self.parts.items():
            # Index by category
            cat = part.category
            if cat not in self._index_cache["category"]:
                self._index_cache["category"][cat] = []
            self._index_cache["category"][cat].append(part_id)

            # Index by style
            style = part.style
            if style not in self._index_cache["style"]:
                self._index_cache["style"][style] = []
            self._index_cache["style"][style].append(part_id)

            # Index by source
            source = part.source
            if source not in self._index_cache["source"]:
                self._index_cache["source"][source] = []
            self._index_cache["source"][source].append(part_id)

            # Index by tags
            for tag in part.tags:
                tag_lower = tag.lower()
                if tag_lower not in self._index_cache["tags"]:
                    self._index_cache["tags"][tag_lower] = []
                self._index_cache["tags"][tag_lower].append(part_id)

    def index_directory(
        self,
        directory: str,
        source: str = "custom",
        recursive: bool = True,
    ) -> int:
        """
        Index parts from directory.

        Scans for .blend files and extracts collections.

        Args:
            directory: Directory to scan
            source: Source identifier
            recursive: Scan subdirectories

        Returns:
            Number of parts indexed
        """
        dir_path = Path(directory)
        count = 0

        pattern = "**/*.blend" if recursive else "*.blend"
        for blend_file in dir_path.glob(pattern):
            parts = load_parts_from_blend(str(blend_file), source)
            for part in parts:
                self.add_part(part)
                count += 1

        return count

    def index_vitaly_bulgarov(self, base_path: str) -> int:
        """
        Index Vitaly Bulgarov asset packs.

        Args:
            base_path: Path to Vitaly Bulgarov pack directory

        Returns:
            Number of parts indexed
        """
        count = 0

        for pack_key, pack_info in VITALY_BULGAROV_PACKS.items():
            pack_dir = Path(base_path) / pack_key
            if pack_dir.exists():
                parts = self.index_directory(
                    str(pack_dir),
                    source="vitaly_bulgarov",
                )
                count += parts

        return count

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        style: Optional[str] = None,
        source: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[PartSpec]:
        """
        Search for parts.

        Args:
            query: Text search in name
            category: Filter by category
            style: Filter by style
            source: Filter by source
            tags: Required tags

        Returns:
            List of matching parts
        """
        results = set(self.parts.keys())

        # Filter by category
        if category and category in self._index_cache.get("category", {}):
            results &= set(self._index_cache["category"][category])

        # Filter by style
        if style and style in self._index_cache.get("style", {}):
            results &= set(self._index_cache["style"][style])

        # Filter by source
        if source and source in self._index_cache.get("source", {}):
            results &= set(self._index_cache["source"][source])

        # Filter by tags
        if tags:
            for tag in tags:
                tag_lower = tag.lower()
                if tag_lower in self._index_cache.get("tags", {}):
                    results &= set(self._index_cache["tags"][tag_lower])

        # Text search
        if query:
            query_lower = query.lower()
            results = {
                pid for pid in results
                if query_lower in self.parts[pid].name.lower()
            }

        return [self.parts[pid] for pid in results]

    def get_by_category(self, category: str) -> List[PartSpec]:
        """Get all parts in category."""
        return self.search(category=category)

    def get_by_style(self, style: str) -> List[PartSpec]:
        """Get all parts with style."""
        return self.search(style=style)

    def get_compatible_parts(
        self,
        part_id: str,
        attachment_point: Optional[str] = None,
    ) -> List[PartSpec]:
        """
        Get parts compatible with attachment point.

        Args:
            part_id: Part to find compatible parts for
            attachment_point: Specific attachment point

        Returns:
            List of compatible parts
        """
        part = self.parts.get(part_id)
        if not part:
            return []

        compatible = []
        for other in self.parts.values():
            if other.part_id == part_id:
                continue

            # Check attachment compatibility
            for ap in other.attachment_points:
                if attachment_point:
                    if ap.parent_point == attachment_point:
                        compatible.append(other)
                        break
                else:
                    # Any attachment point matches
                    for pap in part.attachment_points:
                        if ap.parent_point == pap.name:
                            compatible.append(other)
                            break

        return compatible

    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics."""
        stats = {
            "total_parts": len(self.parts),
            "by_category": {},
            "by_style": {},
            "by_source": {},
        }

        for part in self.parts.values():
            stats["by_category"][part.category] = stats["by_category"].get(part.category, 0) + 1
            stats["by_style"][part.style] = stats["by_style"].get(part.style, 0) + 1
            stats["by_source"][part.source] = stats["by_source"].get(part.source, 0) + 1

        return stats


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_parts_from_blend(
    file_path: str,
    source: str = "custom",
) -> List[PartSpec]:
    """
    Load parts from blend file.

    Extracts collections as individual parts.

    Args:
        file_path: Path to .blend file
        source: Source identifier

    Returns:
        List of PartSpec objects
    """
    parts = []
    blend_path = Path(file_path)

    if not blend_path.exists():
        return parts

    # Generate unique part IDs
    file_hash = hashlib.md5(str(blend_path).encode()).hexdigest()[:8]

    # In actual Blender context, would use bpy.data.libraries
    # Here we create placeholder parts based on file structure
    # Real implementation would extract actual collection names

    parts.append(PartSpec(
        part_id=f"part_{file_hash}",
        name=blend_path.stem,
        category="prop",
        style="industrial",
        source=source,
        file_path=str(blend_path),
        collection_name=blend_path.stem,
        tags=[blend_path.stem.lower()],
    ))

    return parts


def create_part_id(file_path: str, collection_name: str) -> str:
    """
    Generate unique part ID.

    Args:
        file_path: Part file path
        collection_name: Collection name in file

    Returns:
        Unique part ID
    """
    combined = f"{file_path}:{collection_name}"
    hash_val = hashlib.md5(combined.encode()).hexdigest()[:8]
    return f"part_{hash_val}"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "PartCategory",
    "PartStyle",
    "PartSource",
    "AttachmentType",
    # Data classes
    "PartSpec",
    "AttachmentPoint",
    "PartVariant",
    # Constants
    "VITALY_BULGAROV_PACKS",
    "PART_SCALE_REFERENCE",
    # Classes
    "PartsLibrary",
    # Functions
    "load_parts_from_blend",
    "create_part_id",
]
