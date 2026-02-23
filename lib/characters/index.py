"""
Character Asset Index

Manages catalog of character assets including humanoids, creatures, and NPCs.
Supports searching, filtering, and integration with wardrobe system.

Implements REQ-CH-01: Character Asset Index.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from pathlib import Path
import json
import hashlib


class CharacterType(Enum):
    """Character type classification."""
    HUMANOID = "humanoid"       # Human-like characters
    CREATURE = "creature"       # Animals, monsters
    ROBOT = "robot"            # Mechanical characters
    NPC = "npc"                # Background characters
    HERO = "hero"              # Main characters
    VILLAIN = "villain"        # Antagonists
    EXTRAS = "extras"          # Crowd characters


class CharacterRole(Enum):
    """Character role in production."""
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    SUPPORTING = "supporting"
    BACKGROUND = "background"
    CREATURE = "creature"
    VEHICLE = "vehicle"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CharacterSpec:
    """
    Character asset specification.

    Attributes:
        character_id: Unique character identifier
        name: Display name
        character_type: Type classification
        role: Production role
        file_path: Path to character blend file
        collection_name: Collection name in file
        thumbnail_path: Path to thumbnail image
        rig_type: Type of rig (biped, quadruped, etc)
        rig_name: Name of rig in file
        height: Character height in meters
        wardrobe_ids: Associated wardrobe IDs
        morph_targets: Available morph targets
        animation_clips: Available animation clips
        tags: Search tags
        description: Character description
        variants: Variant specifications
    """
    character_id: str = ""
    name: str = ""
    character_type: str = "humanoid"
    role: str = "supporting"
    file_path: str = ""
    collection_name: str = ""
    thumbnail_path: str = ""
    rig_type: str = "biped"
    rig_name: str = ""
    height: float = 1.75
    wardrobe_ids: List[str] = field(default_factory=list)
    morph_targets: List[str] = field(default_factory=list)
    animation_clips: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    description: str = ""
    variants: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "character_id": self.character_id,
            "name": self.name,
            "character_type": self.character_type,
            "role": self.role,
            "file_path": self.file_path,
            "collection_name": self.collection_name,
            "thumbnail_path": self.thumbnail_path,
            "rig_type": self.rig_type,
            "rig_name": self.rig_name,
            "height": self.height,
            "wardrobe_ids": self.wardrobe_ids,
            "morph_targets": self.morph_targets,
            "animation_clips": self.animation_clips,
            "tags": self.tags,
            "description": self.description,
            "variants": self.variants,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterSpec":
        """Create from dictionary."""
        return cls(
            character_id=data.get("character_id", ""),
            name=data.get("name", ""),
            character_type=data.get("character_type", "humanoid"),
            role=data.get("role", "supporting"),
            file_path=data.get("file_path", ""),
            collection_name=data.get("collection_name", ""),
            thumbnail_path=data.get("thumbnail_path", ""),
            rig_type=data.get("rig_type", "biped"),
            rig_name=data.get("rig_name", ""),
            height=data.get("height", 1.75),
            wardrobe_ids=data.get("wardrobe_ids", []),
            morph_targets=data.get("morph_targets", []),
            animation_clips=data.get("animation_clips", []),
            tags=data.get("tags", []),
            description=data.get("description", ""),
            variants=data.get("variants", {}),
        )


# =============================================================================
# CHARACTER INDEX CLASS
# =============================================================================

class CharacterIndex:
    """
    Manages catalog of character assets.

    Provides search, filtering, and integration with
    existing wardrobe and animation systems.

    Usage:
        index = CharacterIndex()
        index.load_catalog("characters.json")
        heroes = index.search(role="hero")
    """

    def __init__(self, catalog_path: Optional[str] = None):
        """
        Initialize character index.

        Args:
            catalog_path: Path to existing catalog JSON
        """
        self.characters: Dict[str, CharacterSpec] = {}
        self._index_cache: Dict[str, List[str]] = {}

        if catalog_path:
            self.load_catalog(catalog_path)

    def load_catalog(self, path: str) -> int:
        """
        Load character catalog from JSON.

        Args:
            path: Path to catalog JSON

        Returns:
            Number of characters loaded
        """
        with open(path, "r") as f:
            data = json.load(f)

        count = 0
        for char_data in data.get("characters", []):
            char = CharacterSpec.from_dict(char_data)
            self.characters[char.character_id] = char
            count += 1

        self._rebuild_index()
        return count

    def save_catalog(self, path: str) -> None:
        """
        Save character catalog to JSON.

        Args:
            path: Output path
        """
        data = {
            "version": "1.0",
            "characters": [c.to_dict() for c in self.characters.values()],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def add_character(self, character: CharacterSpec) -> None:
        """Add character to index."""
        self.characters[character.character_id] = character
        self._rebuild_index()

    def get_character(self, character_id: str) -> Optional[CharacterSpec]:
        """Get character by ID."""
        return self.characters.get(character_id)

    def _rebuild_index(self) -> None:
        """Rebuild search index."""
        self._index_cache = {
            "type": {},
            "role": {},
            "rig_type": {},
            "tags": {},
        }

        for char_id, char in self.characters.items():
            # Index by type
            ctype = char.character_type
            if ctype not in self._index_cache["type"]:
                self._index_cache["type"][ctype] = []
            self._index_cache["type"][ctype].append(char_id)

            # Index by role
            role = char.role
            if role not in self._index_cache["role"]:
                self._index_cache["role"][role] = []
            self._index_cache["role"][role].append(char_id)

            # Index by rig type
            rig = char.rig_type
            if rig not in self._index_cache["rig_type"]:
                self._index_cache["rig_type"][rig] = []
            self._index_cache["rig_type"][rig].append(char_id)

            # Index by tags
            for tag in char.tags:
                tag_lower = tag.lower()
                if tag_lower not in self._index_cache["tags"]:
                    self._index_cache["tags"][tag_lower] = []
                self._index_cache["tags"][tag_lower].append(char_id)

    def search(
        self,
        query: Optional[str] = None,
        character_type: Optional[str] = None,
        role: Optional[str] = None,
        rig_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_height: Optional[float] = None,
        max_height: Optional[float] = None,
    ) -> List[CharacterSpec]:
        """
        Search for characters.

        Args:
            query: Text search in name
            character_type: Filter by type
            role: Filter by role
            rig_type: Filter by rig type
            tags: Required tags
            min_height: Minimum height
            max_height: Maximum height

        Returns:
            List of matching characters
        """
        results = set(self.characters.keys())

        # Filter by type
        if character_type and character_type in self._index_cache.get("type", {}):
            results &= set(self._index_cache["type"][character_type])

        # Filter by role
        if role and role in self._index_cache.get("role", {}):
            results &= set(self._index_cache["role"][role])

        # Filter by rig type
        if rig_type and rig_type in self._index_cache.get("rig_type", {}):
            results &= set(self._index_cache["rig_type"][rig_type])

        # Filter by tags
        if tags:
            for tag in tags:
                tag_lower = tag.lower()
                if tag_lower in self._index_cache.get("tags", {}):
                    results &= set(self._index_cache["tags"][tag_lower])

        # Filter by height
        if min_height is not None:
            results = {
                cid for cid in results
                if self.characters[cid].height >= min_height
            }
        if max_height is not None:
            results = {
                cid for cid in results
                if self.characters[cid].height <= max_height
            }

        # Text search
        if query:
            query_lower = query.lower()
            results = {
                cid for cid in results
                if query_lower in self.characters[cid].name.lower()
                or query_lower in self.characters[cid].description.lower()
            }

        return [self.characters[cid] for cid in results]

    def get_by_role(self, role: str) -> List[CharacterSpec]:
        """Get all characters with role."""
        return self.search(role=role)

    def get_by_type(self, character_type: str) -> List[CharacterSpec]:
        """Get all characters of type."""
        return self.search(character_type=character_type)

    def get_characters_with_wardrobe(
        self,
        wardrobe_id: str,
    ) -> List[CharacterSpec]:
        """
        Get characters with specific wardrobe.

        Args:
            wardrobe_id: Wardrobe ID to find

        Returns:
            List of characters using this wardrobe
        """
        return [
            char for char in self.characters.values()
            if wardrobe_id in char.wardrobe_ids
        ]

    def get_characters_with_animation(
        self,
        clip_name: str,
    ) -> List[CharacterSpec]:
        """
        Get characters with specific animation clip.

        Args:
            clip_name: Animation clip name

        Returns:
            List of characters with this animation
        """
        return [
            char for char in self.characters.values()
            if clip_name in char.animation_clips
        ]

    def index_directory(
        self,
        directory: str,
        character_type: str = "humanoid",
        recursive: bool = True,
    ) -> int:
        """
        Index characters from directory.

        Args:
            directory: Directory to scan
            character_type: Default character type
            recursive: Scan subdirectories

        Returns:
            Number of characters indexed
        """
        dir_path = Path(directory)
        count = 0

        pattern = "**/*.blend" if recursive else "*.blend"
        for blend_file in dir_path.glob(pattern):
            # Create character entry
            char_id = create_character_id(str(blend_file), blend_file.stem)
            char = CharacterSpec(
                character_id=char_id,
                name=blend_file.stem,
                character_type=character_type,
                file_path=str(blend_file),
                collection_name=blend_file.stem,
                tags=[blend_file.stem.lower()],
            )
            self.add_character(char)
            count += 1

        return count

    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics."""
        stats = {
            "total_characters": len(self.characters),
            "by_type": {},
            "by_role": {},
            "by_rig_type": {},
        }

        for char in self.characters.values():
            stats["by_type"][char.character_type] = stats["by_type"].get(char.character_type, 0) + 1
            stats["by_role"][char.role] = stats["by_role"].get(char.role, 0) + 1
            stats["by_rig_type"][char.rig_type] = stats["by_rig_type"].get(char.rig_type, 0) + 1

        return stats


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_character_id(file_path: str, name: str) -> str:
    """
    Generate unique character ID.

    Args:
        file_path: Character file path
        name: Character name

    Returns:
        Unique character ID
    """
    combined = f"{file_path}:{name}"
    hash_val = hashlib.md5(combined.encode()).hexdigest()[:8]
    return f"char_{hash_val}"


def create_character_index(
    characters: List[Dict[str, Any]],
) -> CharacterIndex:
    """
    Create character index from list.

    Args:
        characters: List of character specifications

    Returns:
        CharacterIndex with characters added
    """
    index = CharacterIndex()
    for char_data in characters:
        char = CharacterSpec.from_dict(char_data)
        index.add_character(char)
    return index


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "CharacterType",
    "CharacterRole",
    # Data classes
    "CharacterSpec",
    # Classes
    "CharacterIndex",
    # Functions
    "create_character_id",
    "create_character_index",
]
