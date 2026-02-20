"""
Wardrobe System Types

Data structures for costume tracking and continuity management.

Requirements:
- REQ-WARD-01: Costume definition and storage
- REQ-WARD-02: Scene-by-scene costume assignment
- REQ-WARD-03: Automatic costume change detection
- REQ-WARD-04: Continuity validation
- REQ-WARD-05: Costume bible generation

Part of Phase 10.1: Wardrobe System
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class CostumeCategory(str, Enum):
    """Category of costume piece."""
    TOP = "top"
    BOTTOM = "bottom"
    SHOES = "shoes"
    ACCESSORY = "accessory"
    OUTERWEAR = "outerwear"
    UNDERWEAR = "underwear"
    HEADWEAR = "headwear"
    JEWELRY = "jewelry"
    BAG = "bag"
    EYEWEAR = "eyewear"


class CostumeStyle(str, Enum):
    """Style of costume."""
    CASUAL = "casual"
    FORMAL = "formal"
    ATHLETIC = "athletic"
    PERIOD = "period"
    FANTASY = "fantasy"
    SCI_FI = "scifi"
    BUSINESS = "business"
    UNIFORM = "uniform"
    COSTUME = "costume"


class CostumeCondition(str, Enum):
    """Condition of costume."""
    PRISTINE = "pristine"
    WORN = "worn"
    DIRTY = "dirty"
    DAMAGED = "damaged"
    BLOODIED = "bloodied"
    WET = "wet"
    TORN = "torn"
    BURNED = "burned"


class ChangeReason(str, Enum):
    """Reason for costume change."""
    STORY = "story"  # Plot-driven change
    TIME = "time"  # Time passage in narrative
    LOCATION = "location"  # Scene location change
    DAMAGE = "damage"  # Costume damage in scene
    WEATHER = "weather"  # Weather-related
    ACTION = "action"  # Action sequence
    TRANSFORMATION = "transformation"  # Character transformation


class IssueType(str, Enum):
    """Type of continuity issue."""
    COSTUME_MISMATCH = "costume_mismatch"
    CONDITION_MISMATCH = "condition_mismatch"
    MISSING_ASSIGNMENT = "missing_assignment"
    INVALID_PROGRESSION = "invalid_progression"
    UNDOCUMENTED_CHANGE = "undocumented_change"
    COLOR_MISMATCH = "color_mismatch"
    MISSING_PIECE = "missing_piece"


class IssueSeverity(str, Enum):
    """Severity of continuity issue."""
    ERROR = "error"  # Must fix before shooting
    WARNING = "warning"  # Should fix, may be intentional
    INFO = "info"  # FYI only


@dataclass
class CostumePiece:
    """Single piece of clothing or accessory."""
    name: str
    category: str  # top, bottom, shoes, accessory, outerwear, underwear
    color: str
    material: str
    style: str = "casual"  # casual, formal, athletic, period, fantasy
    brand: str = ""
    notes: str = ""
    size: str = ""
    quantity: int = 1
    reference_image: str = ""
    purchase_link: str = ""
    estimated_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "category": self.category,
            "color": self.color,
            "material": self.material,
            "style": self.style,
            "brand": self.brand,
            "notes": self.notes,
            "size": self.size,
            "quantity": self.quantity,
            "reference_image": self.reference_image,
            "purchase_link": self.purchase_link,
            "estimated_cost": self.estimated_cost,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostumePiece":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            category=data.get("category", ""),
            color=data.get("color", ""),
            material=data.get("material", ""),
            style=data.get("style", "casual"),
            brand=data.get("brand", ""),
            notes=data.get("notes", ""),
            size=data.get("size", ""),
            quantity=data.get("quantity", 1),
            reference_image=data.get("reference_image", ""),
            purchase_link=data.get("purchase_link", ""),
            estimated_cost=data.get("estimated_cost", 0.0),
        )

    def matches(self, other: "CostumePiece", strict: bool = False) -> bool:
        """Check if two pieces match for continuity."""
        if strict:
            return (
                self.name == other.name
                and self.color == other.color
                and self.material == other.material
            )
        # Non-strict: just check name and approximate color
        return self.name == other.name and self.color.lower() == other.color.lower()


@dataclass
class Costume:
    """Complete costume for a character."""
    name: str
    character: str
    pieces: List[CostumePiece] = field(default_factory=list)
    accessories: List[CostumePiece] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)  # Primary colors for continuity
    condition: str = "pristine"  # pristine, worn, dirty, damaged, bloodied
    notes: str = ""
    reference_images: List[str] = field(default_factory=list)
    version: int = 1

    def get_piece(self, category: str) -> Optional[CostumePiece]:
        """Get piece by category."""
        for piece in self.pieces:
            if piece.category == category:
                return piece
        return None

    def get_all_pieces(self) -> List[CostumePiece]:
        """Get all pieces including accessories."""
        return self.pieces + self.accessories

    def matches(self, other: "Costume", strict: bool = False) -> bool:
        """Check if two costumes match (continuity check)."""
        if self.name != other.name:
            return False

        # Check piece counts
        if len(self.pieces) != len(other.pieces):
            return False

        # Check each piece
        for piece in self.pieces:
            other_piece = other.get_piece(piece.category)
            if other_piece is None:
                return False
            if not piece.matches(other_piece, strict):
                return False

        return True

    def get_piece_count(self) -> int:
        """Get total number of pieces including accessories."""
        return len(self.pieces) + len(self.accessories)

    def get_total_cost(self) -> float:
        """Calculate total estimated cost of costume."""
        total = 0.0
        for piece in self.pieces + self.accessories:
            total += piece.estimated_cost * piece.quantity
        return total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "character": self.character,
            "pieces": [p.to_dict() for p in self.pieces],
            "accessories": [a.to_dict() for a in self.accessories],
            "colors": self.colors,
            "condition": self.condition,
            "notes": self.notes,
            "reference_images": self.reference_images,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Costume":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            character=data.get("character", ""),
            pieces=[CostumePiece.from_dict(p) for p in data.get("pieces", [])],
            accessories=[CostumePiece.from_dict(a) for a in data.get("accessories", [])],
            colors=data.get("colors", []),
            condition=data.get("condition", "pristine"),
            notes=data.get("notes", ""),
            reference_images=data.get("reference_images", []),
            version=data.get("version", 1),
        )


@dataclass
class CostumeChange:
    """Costume change between scenes."""
    character: str
    scene_before: int
    scene_after: int
    costume_before: str  # Costume name
    costume_after: str
    change_reason: str = "story"  # story, time, location, damage, weather
    notes: str = ""
    screen_time: float = 0.0  # Minutes between scenes
    location_before: str = ""
    location_after: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "character": self.character,
            "scene_before": self.scene_before,
            "scene_after": self.scene_after,
            "costume_before": self.costume_before,
            "costume_after": self.costume_after,
            "change_reason": self.change_reason,
            "notes": self.notes,
            "screen_time": self.screen_time,
            "location_before": self.location_before,
            "location_after": self.location_after,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostumeChange":
        """Create from dictionary."""
        return cls(
            character=data.get("character", ""),
            scene_before=data.get("scene_before", 0),
            scene_after=data.get("scene_after", 0),
            costume_before=data.get("costume_before", ""),
            costume_after=data.get("costume_after", ""),
            change_reason=data.get("change_reason", "story"),
            notes=data.get("notes", ""),
            screen_time=data.get("screen_time", 0.0),
            location_before=data.get("location_before", ""),
            location_after=data.get("location_after", ""),
        )


@dataclass
class CostumeAssignment:
    """Costume assignment for a scene."""
    character: str
    scene: int
    costume: str  # Costume name
    condition: str = "pristine"
    modifications: List[str] = field(default_factory=list)  # On-set modifications
    notes: str = ""
    shoot_date: str = ""  # YYYY-MM-DD
    continuity_photos: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "character": self.character,
            "scene": self.scene,
            "costume": self.costume,
            "condition": self.condition,
            "modifications": self.modifications,
            "notes": self.notes,
            "shoot_date": self.shoot_date,
            "continuity_photos": self.continuity_photos,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostumeAssignment":
        """Create from dictionary."""
        return cls(
            character=data.get("character", ""),
            scene=data.get("scene", 0),
            costume=data.get("costume", ""),
            condition=data.get("condition", "pristine"),
            modifications=data.get("modifications", []),
            notes=data.get("notes", ""),
            shoot_date=data.get("shoot_date", ""),
            continuity_photos=data.get("continuity_photos", []),
        )


@dataclass
class WardrobeRegistry:
    """Complete wardrobe registry for production."""
    costumes: Dict[str, Costume] = field(default_factory=dict)  # name -> Costume
    assignments: List[CostumeAssignment] = field(default_factory=list)
    changes: List[CostumeChange] = field(default_factory=list)
    characters: Dict[str, List[str]] = field(default_factory=dict)  # character -> costume names
    production_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_costume(self, costume: Costume) -> None:
        """Add costume to registry."""
        self.costumes[costume.name] = costume
        if costume.character not in self.characters:
            self.characters[costume.character] = []
        if costume.name not in self.characters[costume.character]:
            self.characters[costume.character].append(costume.name)
        self.updated_at = datetime.now().isoformat()

    def remove_costume(self, name: str) -> bool:
        """Remove costume from registry."""
        if name in self.costumes:
            costume = self.costumes[name]
            # Remove from character mapping
            if costume.character in self.characters:
                if name in self.characters[costume.character]:
                    self.characters[costume.character].remove(name)
            del self.costumes[name]
            self.updated_at = datetime.now().isoformat()
            return True
        return False

    def get_costume(self, name: str) -> Optional[Costume]:
        """Get costume by name."""
        return self.costumes.get(name)

    def get_costumes_for_character(self, character: str) -> List[Costume]:
        """Get all costumes for a character."""
        costume_names = self.characters.get(character, [])
        return [self.costumes[name] for name in costume_names if name in self.costumes]

    def add_assignment(self, assignment: CostumeAssignment) -> None:
        """Add costume assignment."""
        self.assignments.append(assignment)
        self.updated_at = datetime.now().isoformat()

    def get_assignment(self, character: str, scene: int) -> Optional[CostumeAssignment]:
        """Get assignment for character in scene."""
        for assignment in self.assignments:
            if assignment.character == character and assignment.scene == scene:
                return assignment
        return None

    def get_assignments_for_character(self, character: str) -> List[CostumeAssignment]:
        """Get all assignments for a character."""
        return [a for a in self.assignments if a.character == character]

    def get_assignments_for_scene(self, scene: int) -> List[CostumeAssignment]:
        """Get all assignments for a scene."""
        return [a for a in self.assignments if a.scene == scene]

    def add_change(self, change: CostumeChange) -> None:
        """Record a costume change."""
        self.changes.append(change)
        self.updated_at = datetime.now().isoformat()

    def get_changes_for_character(self, character: str) -> List[CostumeChange]:
        """Get all changes for a character."""
        return [c for c in self.changes if c.character == character]

    def get_all_characters(self) -> List[str]:
        """Get list of all characters."""
        return list(self.characters.keys())

    def get_all_scenes(self) -> List[int]:
        """Get list of all scenes with assignments."""
        return sorted(set(a.scene for a in self.assignments))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "production_name": self.production_name,
            "costumes": {name: c.to_dict() for name, c in self.costumes.items()},
            "assignments": [a.to_dict() for a in self.assignments],
            "changes": [c.to_dict() for c in self.changes],
            "characters": self.characters,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WardrobeRegistry":
        """Create from dictionary."""
        registry = cls(
            production_name=data.get("production_name", ""),
            characters=data.get("characters", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )

        # Load costumes
        for name, costume_data in data.get("costumes", {}).items():
            registry.costumes[name] = Costume.from_dict(costume_data)

        # Load assignments
        for assignment_data in data.get("assignments", []):
            registry.assignments.append(CostumeAssignment.from_dict(assignment_data))

        # Load changes
        for change_data in data.get("changes", []):
            registry.changes.append(CostumeChange.from_dict(change_data))

        return registry


# Condition progression rules (what conditions can follow what)
CONDITION_PROGRESSION: Dict[str, List[str]] = {
    "pristine": ["pristine", "worn", "dirty", "damaged", "bloodied", "wet", "torn", "burned"],
    "worn": ["worn", "dirty", "damaged", "bloodied", "wet", "torn", "burned"],
    "dirty": ["dirty", "damaged", "bloodied", "wet", "torn", "burned", "pristine"],  # Can clean
    "damaged": ["damaged", "bloodied", "wet", "torn", "burned"],  # Can't heal
    "bloodied": ["bloodied", "dirty", "wet"],  # Can be cleaned but stain remains
    "wet": ["wet", "dirty", "pristine"],  # Can dry
    "torn": ["torn", "damaged", "bloodied"],  # Permanent
    "burned": ["burned", "damaged"],  # Permanent
}


def is_valid_condition_progression(from_condition: str, to_condition: str) -> bool:
    """Check if a condition change is valid."""
    allowed = CONDITION_PROGRESSION.get(from_condition, [])
    return to_condition in allowed
