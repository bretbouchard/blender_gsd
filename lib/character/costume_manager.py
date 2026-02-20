"""
Costume Manager

CRUD operations and management for the wardrobe system.

Requirements:
- REQ-WARD-01: Costume definition and storage
- REQ-WARD-02: Scene-by-scene costume assignment
- REQ-WARD-03: Automatic costume change detection

Part of Phase 10.1: Wardrobe System
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from .wardrobe_types import (
    Costume,
    CostumePiece,
    CostumeAssignment,
    CostumeChange,
    WardrobeRegistry,
    ChangeReason,
    CostumeCondition,
    is_valid_condition_progression,
)


class CostumeManagerError(Exception):
    """Base exception for costume manager errors."""
    pass


class CostumeNotFoundError(CostumeManagerError):
    """Raised when costume is not found."""
    pass


class DuplicateCostumeError(CostumeManagerError):
    """Raised when attempting to add duplicate costume."""
    pass


class InvalidAssignmentError(CostumeManagerError):
    """Raised when assignment is invalid."""
    pass


class CostumeManager:
    """Manages costumes for a production."""

    def __init__(self, production_name: str = ""):
        """Initialize costume manager."""
        self.registry = WardrobeRegistry(production_name=production_name)
        self._change_detection_enabled = True

    # Costume CRUD

    def create_costume(self, costume: Costume) -> None:
        """Add costume to registry.

        Args:
            costume: Costume to add

        Raises:
            DuplicateCostumeError: If costume with same name exists
        """
        if costume.name in self.registry.costumes:
            raise DuplicateCostumeError(f"Costume '{costume.name}' already exists")
        self.registry.add_costume(costume)

    def get_costume(self, name: str) -> Optional[Costume]:
        """Get costume by name.

        Args:
            name: Costume name

        Returns:
            Costume if found, None otherwise
        """
        return self.registry.get_costume(name)

    def update_costume(self, name: str, costume: Costume) -> None:
        """Update existing costume.

        Args:
            name: Name of costume to update
            costume: New costume data

        Raises:
            CostumeNotFoundError: If costume doesn't exist
        """
        if name not in self.registry.costumes:
            raise CostumeNotFoundError(f"Costume '{name}' not found")

        # If name changed, handle rename
        if costume.name != name:
            self.registry.remove_costume(name)

        self.registry.add_costume(costume)

    def delete_costume(self, name: str) -> bool:
        """Remove costume from registry.

        Args:
            name: Costume name to delete

        Returns:
            True if deleted, False if not found
        """
        return self.registry.remove_costume(name)

    def list_costumes(self, character: Optional[str] = None) -> List[Costume]:
        """List all costumes, optionally filtered by character.

        Args:
            character: Optional character filter

        Returns:
            List of costumes
        """
        if character:
            return self.registry.get_costumes_for_character(character)
        return list(self.registry.costumes.values())

    # Assignment

    def assign_costume(
        self,
        character: str,
        scene: int,
        costume_name: str,
        condition: str = "pristine",
        notes: str = "",
        modifications: Optional[List[str]] = None,
    ) -> CostumeAssignment:
        """Assign costume to character for scene.

        Args:
            character: Character name
            scene: Scene number
            costume_name: Name of costume
            condition: Condition of costume
            notes: Additional notes
            modifications: List of modifications

        Returns:
            Created assignment

        Raises:
            CostumeNotFoundError: If costume doesn't exist
            InvalidAssignmentError: If assignment already exists
        """
        if costume_name not in self.registry.costumes:
            raise CostumeNotFoundError(f"Costume '{costume_name}' not found")

        # Check for existing assignment
        existing = self.registry.get_assignment(character, scene)
        if existing:
            # Update existing assignment
            existing.costume = costume_name
            existing.condition = condition
            existing.notes = notes
            if modifications:
                existing.modifications = modifications
            return existing

        assignment = CostumeAssignment(
            character=character,
            scene=scene,
            costume=costume_name,
            condition=condition,
            notes=notes,
            modifications=modifications or [],
        )
        self.registry.add_assignment(assignment)
        return assignment

    def get_costume_for_scene(self, character: str, scene: int) -> Optional[CostumeAssignment]:
        """Get costume assignment for scene.

        Args:
            character: Character name
            scene: Scene number

        Returns:
            Assignment if found, None otherwise
        """
        return self.registry.get_assignment(character, scene)

    def get_character_scenes(self, character: str) -> List[CostumeAssignment]:
        """Get all scenes with costume for character.

        Args:
            character: Character name

        Returns:
            List of assignments sorted by scene
        """
        assignments = self.registry.get_assignments_for_character(character)
        return sorted(assignments, key=lambda a: a.scene)

    def get_scene_assignments(self, scene: int) -> List[CostumeAssignment]:
        """Get all costume assignments for a scene.

        Args:
            scene: Scene number

        Returns:
            List of assignments for the scene
        """
        return self.registry.get_assignments_for_scene(scene)

    def remove_assignment(self, character: str, scene: int) -> bool:
        """Remove costume assignment.

        Args:
            character: Character name
            scene: Scene number

        Returns:
            True if removed, False if not found
        """
        for i, assignment in enumerate(self.registry.assignments):
            if assignment.character == character and assignment.scene == scene:
                del self.registry.assignments[i]
                self.registry.updated_at = datetime.now().isoformat()
                return True
        return False

    # Change tracking

    def detect_costume_changes(self) -> List[CostumeChange]:
        """Detect costume changes between consecutive scenes.

        Returns:
            List of detected costume changes
        """
        changes = []

        for character in self.registry.get_all_characters():
            character_changes = self._detect_character_changes(character)
            changes.extend(character_changes)

        return changes

    def _detect_character_changes(self, character: str) -> List[CostumeChange]:
        """Detect costume changes for a specific character.

        Args:
            character: Character name

        Returns:
            List of detected changes
        """
        changes = []
        assignments = self.get_character_scenes(character)

        if len(assignments) < 2:
            return changes

        for i in range(1, len(assignments)):
            prev = assignments[i - 1]
            curr = assignments[i]

            # Check for costume change
            if prev.costume != curr.costume:
                change = CostumeChange(
                    character=character,
                    scene_before=prev.scene,
                    scene_after=curr.scene,
                    costume_before=prev.costume,
                    costume_after=curr.costume,
                    change_reason=self._infer_change_reason(prev, curr),
                )
                changes.append(change)

        return changes

    def _infer_change_reason(
        self, prev: CostumeAssignment, curr: CostumeAssignment
    ) -> str:
        """Infer the reason for a costume change.

        Args:
            prev: Previous assignment
            curr: Current assignment

        Returns:
            Inferred change reason
        """
        # Check if condition degraded
        if curr.condition != prev.condition:
            if not is_valid_condition_progression(prev.condition, curr.condition):
                return "story"  # Likely story-driven if invalid natural progression

        # Check if there's a gap in scenes
        if curr.scene - prev.scene > 1:
            return "time"  # Time passage

        # Check for modifications
        if curr.modifications:
            return "action"  # Action may require modifications

        # Default to story
        return "story"

    def record_change(self, change: CostumeChange) -> None:
        """Record a costume change.

        Args:
            change: Costume change to record
        """
        self.registry.add_change(change)

    def get_changes(self, character: Optional[str] = None) -> List[CostumeChange]:
        """Get costume changes, optionally filtered by character.

        Args:
            character: Optional character filter

        Returns:
            List of costume changes
        """
        if character:
            return self.registry.get_changes_for_character(character)
        return self.registry.changes

    # Query methods

    def get_all_costumes_for_character(self, character: str) -> List[Costume]:
        """Get all costumes used by character.

        Args:
            character: Character name

        Returns:
            List of costumes
        """
        return self.registry.get_costumes_for_character(character)

    def get_costume_usage(self, costume_name: str) -> List[int]:
        """Get all scenes where costume is used.

        Args:
            costume_name: Costume name

        Returns:
            List of scene numbers
        """
        scenes = []
        for assignment in self.registry.assignments:
            if assignment.costume == costume_name:
                scenes.append(assignment.scene)
        return sorted(scenes)

    def get_costume_usage_count(self, costume_name: str) -> int:
        """Get number of times costume is used.

        Args:
            costume_name: Costume name

        Returns:
            Usage count
        """
        return len(self.get_costume_usage(costume_name))

    def get_characters_for_costume(self, costume_name: str) -> List[str]:
        """Get characters that use a specific costume.

        Args:
            costume_name: Costume name

        Returns:
            List of character names
        """
        characters = set()
        for assignment in self.registry.assignments:
            if assignment.costume == costume_name:
                characters.add(assignment.character)
        return list(characters)

    def find_costumes_by_color(self, color: str) -> List[Costume]:
        """Find costumes containing a specific color.

        Args:
            color: Color to search for

        Returns:
            List of matching costumes
        """
        color_lower = color.lower()
        matches = []
        for costume in self.registry.costumes.values():
            if color_lower in [c.lower() for c in costume.colors]:
                matches.append(costume)
            else:
                # Check individual pieces
                for piece in costume.get_all_pieces():
                    if color_lower in piece.color.lower():
                        matches.append(costume)
                        break
        return matches

    def find_costumes_by_style(self, style: str) -> List[Costume]:
        """Find costumes of a specific style.

        Args:
            style: Style to search for

        Returns:
            List of matching costumes
        """
        matches = []
        for costume in self.registry.costumes.values():
            # Check if any piece has the style
            for piece in costume.get_all_pieces():
                if piece.style.lower() == style.lower():
                    matches.append(costume)
                    break
        return matches

    # Statistics

    def get_statistics(self) -> Dict[str, Any]:
        """Get wardrobe statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "total_costumes": len(self.registry.costumes),
            "total_assignments": len(self.registry.assignments),
            "total_characters": len(self.registry.get_all_characters()),
            "total_scenes": len(self.registry.get_all_scenes()),
            "total_changes": len(self.registry.changes),
            "costumes_by_character": {
                char: len(costumes)
                for char, costumes in self.registry.characters.items()
            },
            "usage_stats": {
                name: self.get_costume_usage_count(name)
                for name in self.registry.costumes
            },
        }

    def get_most_used_costumes(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently used costumes.

        Args:
            limit: Maximum number to return

        Returns:
            List of (costume_name, usage_count) tuples
        """
        usage = [
            (name, self.get_costume_usage_count(name))
            for name in self.registry.costumes
        ]
        return sorted(usage, key=lambda x: x[1], reverse=True)[:limit]

    # Serialization

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return self.registry.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostumeManager":
        """Create from dictionary.

        Args:
            data: Dictionary data

        Returns:
            CostumeManager instance
        """
        manager = cls(production_name=data.get("production_name", ""))
        manager.registry = WardrobeRegistry.from_dict(data)
        return manager

    def export_assignments_csv(self) -> str:
        """Export assignments as CSV.

        Returns:
            CSV string
        """
        lines = ["character,scene,costume,condition,notes"]
        for assignment in sorted(self.registry.assignments, key=lambda a: (a.character, a.scene)):
            notes = assignment.notes.replace('"', '""')
            lines.append(
                f'"{assignment.character}",{assignment.scene},"{assignment.costume}",'
                f'"{assignment.condition}","{notes}"'
            )
        return "\n".join(lines)

    def export_changes_csv(self) -> str:
        """Export changes as CSV.

        Returns:
            CSV string
        """
        lines = ["character,scene_before,scene_after,costume_before,costume_after,reason,notes"]
        for change in self.registry.changes:
            notes = change.notes.replace('"', '""')
            lines.append(
                f'"{change.character}",{change.scene_before},{change.scene_after},'
                f'"{change.costume_before}","{change.costume_after}",'
                f'"{change.change_reason}","{notes}"'
            )
        return "\n".join(lines)
