"""
Script Types - Data structures for screenplay parsing.

Implements REQ-SCRIPT-01, REQ-SCRIPT-02, REQ-SCRIPT-03
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json


@dataclass
class ActionBlock:
    """Action/description block in a screenplay.

    Represents non-dialogue content that describes what happens visually.
    """
    text: str
    page: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "text": self.text,
            "page": self.page
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionBlock":
        """Deserialize from dictionary."""
        return cls(
            text=data["text"],
            page=data.get("page", 1.0)
        )


@dataclass
class DialogueLine:
    """Single line of dialogue in a screenplay.

    Includes character name, optional extension (V.O., O.S., etc.),
    optional parenthetical, and the dialogue text.
    """
    character: str
    text: str
    extension: str = ""  # (V.O.), (O.S.), (CONT'D)
    parenthetical: str = ""
    page: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "character": self.character,
            "text": self.text,
            "extension": self.extension,
            "parenthetical": self.parenthetical,
            "page": self.page
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DialogueLine":
        """Deserialize from dictionary."""
        return cls(
            character=data["character"],
            text=data["text"],
            extension=data.get("extension", ""),
            parenthetical=data.get("parenthetical", ""),
            page=data.get("page", 1.0)
        )

    def word_count(self) -> int:
        """Count words in dialogue."""
        return len(self.text.split())


@dataclass
class Transition:
    """Scene transition element.

    Represents transitions like CUT TO:, FADE OUT., DISSOLVE TO:, etc.
    """
    type: str  # CUT TO:, FADE OUT., DISSOLVE TO:, etc.
    page: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": self.type,
            "page": self.page
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transition":
        """Deserialize from dictionary."""
        return cls(
            type=data["type"],
            page=data.get("page", 1.0)
        )


@dataclass
class Scene:
    """Single scene from a screenplay.

    Contains all elements within a scene: action blocks, dialogue, and transitions.
    Scene headings follow the format: INT./EXT. LOCATION - TIME
    """
    number: int
    heading: str  # "INT. WAREHOUSE - NIGHT"
    location: str  # Extracted location name
    interior: bool = True
    time_of_day: str = "DAY"  # DAY, NIGHT, DAWN, DUSK, CONTINUOUS
    action: List[ActionBlock] = field(default_factory=list)
    dialogue: List[DialogueLine] = field(default_factory=list)
    transitions: List[Transition] = field(default_factory=list)
    page_start: float = 1.0
    page_end: float = 1.0
    estimated_duration: float = 0.0  # seconds

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "number": self.number,
            "heading": self.heading,
            "location": self.location,
            "interior": self.interior,
            "time_of_day": self.time_of_day,
            "action": [a.to_dict() for a in self.action],
            "dialogue": [d.to_dict() for d in self.dialogue],
            "transitions": [t.to_dict() for t in self.transitions],
            "page_start": self.page_start,
            "page_end": self.page_end,
            "estimated_duration": self.estimated_duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scene":
        """Deserialize from dictionary."""
        return cls(
            number=data["number"],
            heading=data["heading"],
            location=data["location"],
            interior=data.get("interior", True),
            time_of_day=data.get("time_of_day", "DAY"),
            action=[ActionBlock.from_dict(a) for a in data.get("action", [])],
            dialogue=[DialogueLine.from_dict(d) for d in data.get("dialogue", [])],
            transitions=[Transition.from_dict(t) for t in data.get("transitions", [])],
            page_start=data.get("page_start", 1.0),
            page_end=data.get("page_end", 1.0),
            estimated_duration=data.get("estimated_duration", 0.0)
        )

    def get_action_text(self) -> str:
        """Get all action text concatenated."""
        return "\n\n".join(a.text for a in self.action)

    def get_dialogue_text(self) -> str:
        """Get all dialogue text concatenated."""
        return "\n".join(f"{d.character}: {d.text}" for d in self.dialogue)

    def get_characters_in_scene(self) -> List[str]:
        """Get list of unique characters speaking in this scene."""
        return list(set(d.character for d in self.dialogue))

    def word_count(self) -> int:
        """Count total words in scene (action + dialogue)."""
        action_words = sum(len(a.text.split()) for a in self.action)
        dialogue_words = sum(d.word_count() for d in self.dialogue)
        return action_words + dialogue_words

    def estimate_duration(self) -> float:
        """Estimate scene duration in seconds.

        Rule of thumb:
        - 1 page ≈ 1 minute (60 seconds)
        - Average words per page ≈ 250
        - So: duration = (word_count / 250) * 60
        """
        words = self.word_count()
        self.estimated_duration = (words / 250.0) * 60.0
        return self.estimated_duration


@dataclass
class Character:
    """Character from a screenplay.

    Tracks character appearances, dialogue statistics, and aliases.
    """
    name: str
    aliases: List[str] = field(default_factory=list)  # (V.O.), (O.S.), etc.
    dialogue_count: int = 0
    dialogue_word_count: int = 0
    first_appearance: int = 0  # scene number
    last_appearance: int = 0
    scenes_appearing: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "aliases": self.aliases,
            "dialogue_count": self.dialogue_count,
            "dialogue_word_count": self.dialogue_word_count,
            "first_appearance": self.first_appearance,
            "last_appearance": self.last_appearance,
            "scenes_appearing": self.scenes_appearing
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            aliases=data.get("aliases", []),
            dialogue_count=data.get("dialogue_count", 0),
            dialogue_word_count=data.get("dialogue_word_count", 0),
            first_appearance=data.get("first_appearance", 0),
            last_appearance=data.get("last_appearance", 0),
            scenes_appearing=data.get("scenes_appearing", [])
        )

    def add_dialogue(self, scene_number: int, word_count: int, extension: str = ""):
        """Record a dialogue line for this character."""
        self.dialogue_count += 1
        self.dialogue_word_count += word_count

        if scene_number not in self.scenes_appearing:
            self.scenes_appearing.append(scene_number)

            if self.first_appearance == 0:
                self.first_appearance = scene_number

            self.last_appearance = scene_number

        if extension and extension not in self.aliases:
            self.aliases.append(extension)


@dataclass
class Location:
    """Location from a screenplay.

    Tracks location usage across the script with scene counts and time variants.
    """
    name: str
    scene_count: int = 0
    scenes: List[int] = field(default_factory=list)
    interior: bool = True
    time_variants: List[str] = field(default_factory=list)  # DAY, NIGHT, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "scene_count": self.scene_count,
            "scenes": self.scenes,
            "interior": self.interior,
            "time_variants": self.time_variants
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            scene_count=data.get("scene_count", 0),
            scenes=data.get("scenes", []),
            interior=data.get("interior", True),
            time_variants=data.get("time_variants", [])
        )

    def add_scene(self, scene_number: int, time_of_day: str):
        """Record a scene at this location."""
        self.scene_count += 1
        self.scenes.append(scene_number)

        if time_of_day not in self.time_variants:
            self.time_variants.append(time_of_day)


@dataclass
class Beat:
    """Single story beat in a beat sheet.

    Represents a structural element in the story (setup, catalyst, climax, etc.)
    """
    scene_number: int
    beat_type: str  # setup, catalyst, debate, etc.
    description: str = ""
    emotional_value: float = 0.0  # -1 to 1
    pages: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scene_number": self.scene_number,
            "beat_type": self.beat_type,
            "description": self.description,
            "emotional_value": self.emotional_value,
            "pages": self.pages
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Beat":
        """Deserialize from dictionary."""
        return cls(
            scene_number=data["scene_number"],
            beat_type=data["beat_type"],
            description=data.get("description", ""),
            emotional_value=data.get("emotional_value", 0.0),
            pages=data.get("pages", 0.0)
        )


@dataclass
class BeatSheet:
    """Generated beat sheet for a screenplay.

    Contains story beats and act break positions.
    """
    beats: List[Beat] = field(default_factory=list)
    act_breaks: List[int] = field(default_factory=list)  # Scene numbers

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "beats": [b.to_dict() for b in self.beats],
            "act_breaks": self.act_breaks
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatSheet":
        """Deserialize from dictionary."""
        return cls(
            beats=[Beat.from_dict(b) for b in data.get("beats", [])],
            act_breaks=data.get("act_breaks", [])
        )

    def get_beat_by_type(self, beat_type: str) -> Optional[Beat]:
        """Find a beat by its type."""
        for beat in self.beats:
            if beat.beat_type == beat_type:
                return beat
        return None


@dataclass
class Script:
    """Parsed screenplay.

    Contains all parsed elements from a screenplay file.
    """
    title: str = ""
    author: str = ""
    draft: str = ""
    date: str = ""
    scenes: List[Scene] = field(default_factory=list)
    characters: List[Character] = field(default_factory=list)
    locations: List[Location] = field(default_factory=list)
    total_pages: float = 0.0
    estimated_runtime: float = 0.0  # minutes (1 page ≈ 1 minute)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "title": self.title,
            "author": self.author,
            "draft": self.draft,
            "date": self.date,
            "scenes": [s.to_dict() for s in self.scenes],
            "characters": [c.to_dict() for c in self.characters],
            "locations": [l.to_dict() for l in self.locations],
            "total_pages": self.total_pages,
            "estimated_runtime": self.estimated_runtime
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Script":
        """Deserialize from dictionary."""
        return cls(
            title=data.get("title", ""),
            author=data.get("author", ""),
            draft=data.get("draft", ""),
            date=data.get("date", ""),
            scenes=[Scene.from_dict(s) for s in data.get("scenes", [])],
            characters=[Character.from_dict(c) for c in data.get("characters", [])],
            locations=[Location.from_dict(l) for l in data.get("locations", [])],
            total_pages=data.get("total_pages", 0.0),
            estimated_runtime=data.get("estimated_runtime", 0.0)
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "Script":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def get_scene_by_number(self, number: int) -> Optional[Scene]:
        """Get scene by its number."""
        for scene in self.scenes:
            if scene.number == number:
                return scene
        return None

    def get_character_by_name(self, name: str) -> Optional[Character]:
        """Get character by name (case-insensitive)."""
        name_lower = name.lower()
        for char in self.characters:
            if char.name.lower() == name_lower:
                return char
        return None

    def get_location_by_name(self, name: str) -> Optional[Location]:
        """Get location by name (case-insensitive)."""
        name_lower = name.lower()
        for loc in self.locations:
            if loc.name.lower() == name_lower:
                return loc
        return None

    def calculate_statistics(self):
        """Calculate runtime and page estimates."""
        # Sum up scene durations
        total_seconds = sum(s.estimate_duration() for s in self.scenes)

        # Convert to minutes
        self.estimated_runtime = total_seconds / 60.0

        # Estimate pages (1 page ≈ 1 minute)
        self.total_pages = self.estimated_runtime

    def get_scenes_for_character(self, character_name: str) -> List[Scene]:
        """Get all scenes where a character has dialogue."""
        scenes = []
        char_lower = character_name.lower()

        for scene in self.scenes:
            for dialogue in scene.dialogue:
                if dialogue.character.lower() == char_lower:
                    scenes.append(scene)
                    break

        return scenes

    def get_scenes_at_location(self, location_name: str) -> List[Scene]:
        """Get all scenes at a specific location."""
        loc_lower = location_name.lower()
        return [s for s in self.scenes if s.location.lower() == loc_lower]

    def get_interior_scenes(self) -> List[Scene]:
        """Get all interior scenes."""
        return [s for s in self.scenes if s.interior]

    def get_exterior_scenes(self) -> List[Scene]:
        """Get all exterior scenes."""
        return [s for s in self.scenes if not s.interior]

    def get_day_scenes(self) -> List[Scene]:
        """Get all day scenes."""
        day_times = {"DAY", "MORNING", "AFTERNOON", "DAWN"}
        return [s for s in self.scenes if s.time_of_day.upper() in day_times]

    def get_night_scenes(self) -> List[Scene]:
        """Get all night scenes."""
        night_times = {"NIGHT", "EVENING", "DUSK", "MIDNIGHT"}
        return [s for s in self.scenes if s.time_of_day.upper() in night_times]

    def get_dialogue_heavy_characters(self, min_lines: int = 10) -> List[Character]:
        """Get characters with more than min_lines of dialogue."""
        return [c for c in self.characters if c.dialogue_count >= min_lines]


@dataclass
class ScriptAnalysis:
    """Comprehensive analysis of a screenplay.

    Provides statistical analysis and recommendations.
    """
    total_scenes: int = 0
    total_pages: float = 0.0
    estimated_runtime: float = 0.0
    character_count: int = 0
    location_count: int = 0
    dialogue_percentage: float = 0.0
    action_percentage: float = 0.0
    day_night_ratio: float = 1.0
    interior_exterior_ratio: float = 1.0
    longest_scene: int = 0  # scene number
    shortest_scene: int = 0  # scene number
    most_dialogue: str = ""  # character name
    pacing: List[float] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_scenes": self.total_scenes,
            "total_pages": self.total_pages,
            "estimated_runtime": self.estimated_runtime,
            "character_count": self.character_count,
            "location_count": self.location_count,
            "dialogue_percentage": self.dialogue_percentage,
            "action_percentage": self.action_percentage,
            "day_night_ratio": self.day_night_ratio,
            "interior_exterior_ratio": self.interior_exterior_ratio,
            "longest_scene": self.longest_scene,
            "shortest_scene": self.shortest_scene,
            "most_dialogue": self.most_dialogue,
            "pacing": self.pacing,
            "recommendations": self.recommendations
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScriptAnalysis":
        """Deserialize from dictionary."""
        return cls(
            total_scenes=data.get("total_scenes", 0),
            total_pages=data.get("total_pages", 0.0),
            estimated_runtime=data.get("estimated_runtime", 0.0),
            character_count=data.get("character_count", 0),
            location_count=data.get("location_count", 0),
            dialogue_percentage=data.get("dialogue_percentage", 0.0),
            action_percentage=data.get("action_percentage", 0.0),
            day_night_ratio=data.get("day_night_ratio", 1.0),
            interior_exterior_ratio=data.get("interior_exterior_ratio", 1.0),
            longest_scene=data.get("longest_scene", 0),
            shortest_scene=data.get("shortest_scene", 0),
            most_dialogue=data.get("most_dialogue", ""),
            pacing=data.get("pacing", []),
            recommendations=data.get("recommendations", [])
        )


# Export all types
__all__ = [
    "ActionBlock",
    "DialogueLine",
    "Transition",
    "Scene",
    "Character",
    "Location",
    "Beat",
    "BeatSheet",
    "Script",
    "ScriptAnalysis",
]
