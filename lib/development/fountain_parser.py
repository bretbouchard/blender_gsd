"""
Fountain Parser - Parse Fountain format screenplays.

Fountain is a plain text markup language for screenwriting.
See: https://fountain.io/

Implements REQ-SCRIPT-01, REQ-SCRIPT-03
"""

import re
from typing import List, Tuple, Optional, Dict
from pathlib import Path

from .script_types import (
    Script,
    Scene,
    Character,
    Location,
    ActionBlock,
    DialogueLine,
    Transition,
)


class FountainParser:
    """Parse Fountain format scripts into structured data."""

    # Regex patterns for Fountain elements
    SCENE_HEADING_RE = re.compile(
        r'^(INT\.|EXT\.|INT/EXT|I/E)\s*(.+?)(?:\s*-\s*(.+))?$',
        re.IGNORECASE
    )
    CHARACTER_RE = re.compile(
        r'^([A-Z][A-Z0-9_\'\-\s\.]*?)(?:\s*\(([A-Z0-9\s\.]+)\))?$'
    )
    TRANSITION_RE = re.compile(
        r'^(CUT TO:|FADE OUT\.|FADE TO:|DISSOLVE TO:|SMASH CUT:|WIPE:|FREEZE FRAME:|TIME CUT:|MATCH CUT:)$',
        re.IGNORECASE
    )
    PAGE_BREAK_RE = re.compile(r'^={3,}$')
    CENTERED_RE = re.compile(r'^>\s*(.+?)\s*<$')

    # Time of day variations
    TIME_OF_DAY_MAP = {
        "DAY": "DAY",
        "NIGHT": "NIGHT",
        "MORNING": "MORNING",
        "AFTERNOON": "AFTERNOON",
        "EVENING": "EVENING",
        "DAWN": "DAWN",
        "DUSK": "DUSK",
        "MIDNIGHT": "NIGHT",
        "CONTINUOUS": "CONTINUOUS",
        "CONT'D": "CONTINUOUS",
        "LATER": "DAY",  # Default to DAY if unspecified
    }

    def __init__(self):
        """Initialize parser."""
        self.current_page = 1.0
        self.page_line = 0
        self.lines_per_page = 55  # Standard screenplay format

    def parse(self, text: str) -> Script:
        """Parse Fountain text into Script object.

        Args:
            text: Fountain format screenplay text

        Returns:
            Parsed Script object
        """
        lines = text.split('\n')
        script = Script()

        # Parse title page if present
        script.title, script.author, script.draft, script.date = self._parse_title_page(lines)

        # Find where script content starts (after title page)
        start_idx = self._find_script_start(lines)

        # Parse script content
        self._parse_content(lines[start_idx:], script)

        # Extract characters and locations
        script.characters = self._extract_characters(script)
        script.locations = self._extract_locations(script)

        # Calculate statistics
        script.calculate_statistics()

        return script

    def parse_file(self, path: str) -> Script:
        """Parse Fountain file.

        Args:
            path: Path to .fountain file

        Returns:
            Parsed Script object
        """
        path = Path(path)
        text = path.read_text(encoding='utf-8')
        script = self.parse(text)

        # Use filename as title if not in title page
        if not script.title:
            script.title = path.stem

        return script

    def _parse_title_page(self, lines: List[str]) -> Tuple[str, str, str, str]:
        """Parse Fountain title page.

        Title page elements are at the start, prefixed with key:
        Title: ...
        Author: ...
        Draft date: ...
        Contact: ...
        """
        title = ""
        author = ""
        draft = ""
        date = ""

        for i, line in enumerate(lines):
            line = line.strip()

            # Empty line or scene heading ends title page
            if not line or self.SCENE_HEADING_RE.match(line):
                break

            # Parse title page keys
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                if key == 'title':
                    title = value
                elif key in ('author', 'authors', 'written by'):
                    author = value
                elif key in ('draft', 'draft date'):
                    draft = value
                elif key in ('date', 'contact'):
                    date = value

        return title, author, draft, date

    def _find_script_start(self, lines: List[str]) -> int:
        """Find the line index where script content starts."""
        # Skip title page (ends at first blank line or scene heading)
        for i, line in enumerate(lines):
            line = line.strip()

            # Scene heading starts the script
            if self.SCENE_HEADING_RE.match(line):
                return i

            # First blank line after title page content
            if i > 0 and not line:
                # Check if next non-empty line is scene heading
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        if self.SCENE_HEADING_RE.match(lines[j].strip()):
                            return j
                        break

        return 0

    def _parse_content(self, lines: List[str], script: Script):
        """Parse script content (scenes, dialogue, action)."""
        self.current_page = 1.0
        self.page_line = 0

        current_scene: Optional[Scene] = None
        scene_number = 0
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Track page breaks
            if self.PAGE_BREAK_RE.match(stripped):
                self.current_page += 1.0
                self.page_line = 0
                i += 1
                continue

            # Update page estimate based on lines
            self.page_line += 1
            if self.page_line >= self.lines_per_page:
                self.current_page += 1.0
                self.page_line = 0

            # Skip empty lines
            if not stripped:
                i += 1
                continue

            # Scene heading
            if self.SCENE_HEADING_RE.match(stripped):
                # Save previous scene
                if current_scene:
                    current_scene.page_end = self.current_page
                    current_scene.estimate_duration()
                    script.scenes.append(current_scene)

                # Start new scene
                scene_number += 1
                interior, location, time_of_day = self._parse_heading(stripped)
                current_scene = Scene(
                    number=scene_number,
                    heading=stripped,
                    location=location,
                    interior=interior,
                    time_of_day=time_of_day,
                    page_start=self.current_page
                )
                i += 1
                continue

            # Transition
            if self.TRANSITION_RE.match(stripped):
                if current_scene:
                    transition = Transition(
                        type=stripped.upper(),
                        page=self.current_page
                    )
                    current_scene.transitions.append(transition)
                i += 1
                continue

            # Character name (indicates dialogue follows)
            character_match = self.CHARACTER_RE.match(stripped)
            if character_match and current_scene:
                # Check if this looks like a character name (all caps, reasonable length)
                potential_name = character_match.group(1).strip()
                if self._is_character_name(potential_name):
                    character_name, extension = self._parse_character(stripped)

                    # Parse dialogue and parentheticals
                    dialogue_lines, parenthetical, i = self._parse_dialogue_block(lines, i + 1)

                    if dialogue_lines:
                        dialogue = DialogueLine(
                            character=character_name,
                            text="\n".join(dialogue_lines),
                            extension=extension,
                            parenthetical=parenthetical,
                            page=self.current_page
                        )
                        current_scene.dialogue.append(dialogue)
                    continue

            # Action/description (default)
            if current_scene:
                action_lines, i = self._parse_action_block(lines, i)
                if action_lines:
                    action = ActionBlock(
                        text="\n".join(action_lines),
                        page=self.current_page
                    )
                    current_scene.action.append(action)
            else:
                # Action before first scene (rare, but handle it)
                i += 1

        # Save last scene
        if current_scene:
            current_scene.page_end = self.current_page
            current_scene.estimate_duration()
            script.scenes.append(current_scene)

    def _parse_heading(self, line: str) -> Tuple[bool, str, str]:
        """Parse scene heading: INT./EXT., LOCATION, TIME.

        Args:
            line: Scene heading line (e.g., "INT. WAREHOUSE - NIGHT")

        Returns:
            Tuple of (interior, location, time_of_day)
        """
        match = self.SCENE_HEADING_RE.match(line)
        if not match:
            return True, line, "DAY"

        prefix = match.group(1).upper()
        location = match.group(2).strip() if match.group(2) else ""
        time_part = match.group(3).strip() if match.group(3) else "DAY"

        interior = prefix.startswith("INT")

        # Parse time of day
        time_upper = time_part.upper()
        time_of_day = self.TIME_OF_DAY_MAP.get(time_upper, time_upper)

        # Handle compound time specifications
        if " - " in time_of_day:
            time_of_day = time_of_day.split(" - ")[0]

        return interior, location, time_of_day

    def _parse_character(self, line: str) -> Tuple[str, str]:
        """Parse character name and extension.

        Args:
            line: Character line (e.g., "JOHN (V.O.)")

        Returns:
            Tuple of (character_name, extension)
        """
        match = self.CHARACTER_RE.match(line)
        if not match:
            return line.strip(), ""

        name = match.group(1).strip()
        extension = match.group(2).strip() if match.group(2) else ""

        return name, extension

    def _is_character_name(self, text: str) -> bool:
        """Check if text looks like a character name.

        Character names are typically:
        - All uppercase
        - Reasonable length (not too long)
        - Not a common word
        """
        # Must be mostly uppercase
        if not text.replace(" ", "").replace(".", "").replace("-", "").replace("_", "").isupper():
            return False

        # Reasonable length (character names aren't paragraphs)
        if len(text) > 40:
            return False

        # Not a common action word that might be capitalized
        common_actions = {
            "THE", "A", "AN", "IN", "ON", "AT", "TO", "FROM",
            "WITH", "WITHOUT", "BY", "FOR", "OF", "AND", "OR"
        }
        if text in common_actions:
            return False

        return True

    def _parse_dialogue_block(self, lines: List[str], start_idx: int) -> Tuple[List[str], str, int]:
        """Parse dialogue block following character name.

        Args:
            lines: All lines
            start_idx: Index after character name

        Returns:
            Tuple of (dialogue_lines, parenthetical, next_index)
        """
        dialogue_lines = []
        parenthetical = ""
        i = start_idx

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Empty line ends dialogue
            if not stripped:
                break

            # Parenthetical (in parentheses)
            if stripped.startswith('(') and stripped.endswith(')'):
                parenthetical = stripped[1:-1].strip()
                i += 1
                continue

            # New scene heading ends dialogue
            if self.SCENE_HEADING_RE.match(stripped):
                break

            # New character name ends dialogue
            if self.CHARACTER_RE.match(stripped) and self._is_character_name(stripped.split('(')[0].strip()):
                break

            # Transition ends dialogue
            if self.TRANSITION_RE.match(stripped):
                break

            # It's dialogue text
            dialogue_lines.append(stripped)
            i += 1

        return dialogue_lines, parenthetical, i

    def _parse_action_block(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Parse action/description block.

        Args:
            lines: All lines
            start_idx: Starting index

        Returns:
            Tuple of (action_lines, next_index)
        """
        action_lines = []
        i = start_idx

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Empty line ends action block
            if not stripped:
                break

            # New scene heading ends action
            if self.SCENE_HEADING_RE.match(stripped):
                break

            # Character name ends action
            if self.CHARACTER_RE.match(stripped) and self._is_character_name(stripped.split('(')[0].strip()):
                break

            # Transition ends action
            if self.TRANSITION_RE.match(stripped):
                break

            # It's action text
            action_lines.append(stripped)
            i += 1

        return action_lines, i

    def _extract_characters(self, script: Script) -> List[Character]:
        """Extract all characters from parsed script.

        Args:
            script: Parsed script with scenes

        Returns:
            List of Character objects with statistics
        """
        characters: Dict[str, Character] = {}

        for scene in script.scenes:
            for dialogue in scene.dialogue:
                name = dialogue.character
                name_key = name.upper()

                if name_key not in characters:
                    characters[name_key] = Character(name=name)

                char = characters[name_key]
                char.add_dialogue(
                    scene_number=scene.number,
                    word_count=len(dialogue.text.split()),
                    extension=dialogue.extension
                )

        # Sort by dialogue count (most dialogue first)
        return sorted(characters.values(), key=lambda c: c.dialogue_count, reverse=True)

    def _extract_locations(self, script: Script) -> List[Location]:
        """Extract all locations from parsed script.

        Args:
            script: Parsed script with scenes

        Returns:
            List of Location objects with statistics
        """
        locations: Dict[str, Location] = {}

        for scene in script.scenes:
            name = scene.location
            name_key = name.upper()

            if name_key not in locations:
                locations[name_key] = Location(
                    name=name,
                    interior=scene.interior
                )

            loc = locations[name_key]
            loc.add_scene(scene.number, scene.time_of_day)

        # Sort by scene count (most scenes first)
        return sorted(locations.values(), key=lambda l: l.scene_count, reverse=True)


def parse_fountain(text: str) -> Script:
    """Convenience function to parse Fountain text.

    Args:
        text: Fountain format screenplay text

    Returns:
        Parsed Script object
    """
    parser = FountainParser()
    return parser.parse(text)


def parse_fountain_file(path: str) -> Script:
    """Convenience function to parse Fountain file.

    Args:
        path: Path to .fountain file

    Returns:
        Parsed Script object
    """
    parser = FountainParser()
    return parser.parse_file(path)


__all__ = [
    "FountainParser",
    "parse_fountain",
    "parse_fountain_file",
]
