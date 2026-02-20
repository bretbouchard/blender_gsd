"""
Final Draft Parser - Parse .fdx files (XML format).

Final Draft (.fdx) files are XML-based screenplay files.
This parser extracts structure and content for integration.

Implements REQ-SCRIPT-02, REQ-SCRIPT-03
"""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
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


class FdxParser:
    """Parse Final Draft .fdx files (XML format)."""

    # FDX paragraph type mappings
    PARAGRAPH_TYPES = {
        "Scene Heading": "scene",
        "Action": "action",
        "Character": "character",
        "Dialogue": "dialogue",
        "Parenthetical": "parenthetical",
        "Transition": "transition",
        "Shot": "shot",
        "Cast List": "cast",
    }

    # Time of day patterns
    TIME_OF_DAY_RE = re.compile(
        r'\s*-\s*(DAY|NIGHT|MORNING|AFTERNOON|EVENING|DAWN|DUSK|MIDNIGHT|CONTINUOUS)',
        re.IGNORECASE
    )

    def __init__(self):
        """Initialize parser."""
        self.current_page = 1.0

    def parse(self, xml_content: str) -> Script:
        """Parse FDX XML content into Script object.

        Args:
            xml_content: XML content from .fdx file

        Returns:
            Parsed Script object
        """
        # Parse XML
        root = ET.fromstring(xml_content)

        script = Script()

        # Extract metadata
        script.title = self._extract_title(root)
        script.author = self._extract_author(root)

        # Extract content
        paragraphs = self._extract_paragraphs(root)
        self._build_script(paragraphs, script)

        # Extract characters and locations
        script.characters = self._extract_characters(script)
        script.locations = self._extract_locations(script)

        # Calculate statistics
        script.calculate_statistics()

        return script

    def parse_file(self, path: str) -> Script:
        """Parse FDX file.

        Args:
            path: Path to .fdx file

        Returns:
            Parsed Script object
        """
        path = Path(path)
        xml_content = path.read_text(encoding='utf-8')
        script = self.parse(xml_content)

        # Use filename as title if not in metadata
        if not script.title:
            script.title = path.stem

        return script

    def _extract_title(self, root: ET.Element) -> str:
        """Extract title from FDX metadata."""
        # Try to find title in various locations
        # FDX stores title in <Content><ScriptNote> or in Moresettings
        title_elem = root.find(".//Title")
        if title_elem is not None and title_elem.text:
            return title_elem.text.strip()

        # Try ScriptNote
        for scriptnote in root.findall(".//ScriptNote"):
            text = scriptnote.find("Text")
            if text is not None and text.text:
                # Title often appears first
                if "title:" in text.text.lower():
                    return text.text.split(":", 1)[1].strip()

        return ""

    def _extract_author(self, root: ET.Element) -> str:
        """Extract author from FDX metadata."""
        # Try various author locations
        author_elem = root.find(".//Author")
        if author_elem is not None and author_elem.text:
            return author_elem.text.strip()

        # Try ScriptNote
        for scriptnote in root.findall(".//ScriptNote"):
            text = scriptnote.find("Text")
            if text is not None and text.text:
                if "author:" in text.text.lower():
                    return text.text.split(":", 1)[1].strip()

        return ""

    def _extract_paragraphs(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all paragraphs from FDX.

        FDX structure:
        <FinalDraft>
          <Content>
            <Paragraph Type="Scene Heading">
              <Text>INT. WAREHOUSE - NIGHT</Text>
            </Paragraph>
            <Paragraph Type="Action">
              <Text>The door creaks open.</Text>
            </Paragraph>
            ...
          </Content>
        </FinalDraft>
        """
        paragraphs = []

        for para in root.findall(".//Paragraph"):
            para_type = para.get("Type", "")

            # Get all text elements
            text_parts = []
            for text_elem in para.findall("Text"):
                if text_elem.text:
                    text_parts.append(text_elem.text)

            text = "".join(text_parts).strip()

            if text:
                paragraphs.append({
                    "type": para_type,
                    "text": text,
                    "type_category": self.PARAGRAPH_TYPES.get(para_type, "unknown")
                })

        return paragraphs

    def _build_script(self, paragraphs: List[Dict[str, Any]], script: Script):
        """Build Script object from parsed paragraphs."""
        current_scene: Optional[Scene] = None
        scene_number = 0
        current_character = ""
        current_parenthetical = ""

        # Track pages (rough estimate)
        lines_processed = 0
        lines_per_page = 55

        for para in paragraphs:
            para_type = para["type_category"]
            text = para["text"]

            # Update page estimate
            lines_processed += 1
            if lines_processed >= lines_per_page:
                self.current_page += 1.0
                lines_processed = 0

            if para_type == "scene":
                # Save previous scene
                if current_scene:
                    current_scene.page_end = self.current_page
                    current_scene.estimate_duration()
                    script.scenes.append(current_scene)

                # Start new scene
                scene_number += 1
                interior, location, time_of_day = self._parse_heading(text)
                current_scene = Scene(
                    number=scene_number,
                    heading=text,
                    location=location,
                    interior=interior,
                    time_of_day=time_of_day,
                    page_start=self.current_page
                )

            elif para_type == "action":
                if current_scene:
                    action = ActionBlock(
                        text=text,
                        page=self.current_page
                    )
                    current_scene.action.append(action)

            elif para_type == "character":
                # Character name line
                current_character, extension = self._parse_character(text)
                current_parenthetical = ""

            elif para_type == "parenthetical":
                # Parenthetical instruction
                current_parenthetical = text.strip("()")

            elif para_type == "dialogue":
                if current_scene and current_character:
                    dialogue = DialogueLine(
                        character=current_character,
                        text=text,
                        parenthetical=current_parenthetical,
                        page=self.current_page
                    )
                    current_scene.dialogue.append(dialogue)
                    # Reset for next dialogue
                    current_parenthetical = ""

            elif para_type == "transition":
                if current_scene:
                    transition = Transition(
                        type=text.upper(),
                        page=self.current_page
                    )
                    current_scene.transitions.append(transition)

        # Save last scene
        if current_scene:
            current_scene.page_end = self.current_page
            current_scene.estimate_duration()
            script.scenes.append(current_scene)

    def _parse_heading(self, text: str) -> Tuple[bool, str, str]:
        """Parse scene heading for INT./EXT., location, time.

        Args:
            text: Scene heading (e.g., "INT. WAREHOUSE - NIGHT")

        Returns:
            Tuple of (interior, location, time_of_day)
        """
        text = text.strip()

        # Check for INT./EXT.
        interior = True
        if text.upper().startswith("EXT."):
            interior = False

        # Remove INT./EXT. prefix first
        prefix_re = re.compile(r'^(INT\.|EXT\.|INT/EXT|I/E)\s*', re.IGNORECASE)
        location = prefix_re.sub("", text)

        # Extract time of day from the location string (after prefix removal)
        time_match = self.TIME_OF_DAY_RE.search(location)
        time_of_day = "DAY"
        if time_match:
            time_of_day = time_match.group(1).upper()
            # Remove time suffix from location
            location = location[:time_match.start()].strip()

        # Clean up location name
        location = location.strip(" -")

        return interior, location, time_of_day

    def _parse_character(self, text: str) -> Tuple[str, str]:
        """Parse character name and extension.

        Args:
            text: Character line (e.g., "JOHN (V.O.)")

        Returns:
            Tuple of (character_name, extension)
        """
        text = text.strip()

        # Check for extension (V.O.), (O.S.), (CONT'D)
        ext_match = re.search(r'\(([A-Z0-9\s\.]+)\)\s*$', text, re.IGNORECASE)

        if ext_match:
            name = text[:ext_match.start()].strip()
            extension = ext_match.group(1).strip()
        else:
            name = text
            extension = ""

        return name, extension

    def _extract_characters(self, script: Script) -> List[Character]:
        """Extract all characters from parsed script."""
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

        # Sort by dialogue count
        return sorted(characters.values(), key=lambda c: c.dialogue_count, reverse=True)

    def _extract_locations(self, script: Script) -> List[Location]:
        """Extract all locations from parsed script."""
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

        # Sort by scene count
        return sorted(locations.values(), key=lambda l: l.scene_count, reverse=True)


def parse_fdx(xml_content: str) -> Script:
    """Convenience function to parse FDX XML content.

    Args:
        xml_content: XML content from .fdx file

    Returns:
        Parsed Script object
    """
    parser = FdxParser()
    return parser.parse(xml_content)


def parse_fdx_file(path: str) -> Script:
    """Convenience function to parse FDX file.

    Args:
        path: Path to .fdx file

    Returns:
        Parsed Script object
    """
    parser = FdxParser()
    return parser.parse_file(path)


__all__ = [
    "FdxParser",
    "parse_fdx",
    "parse_fdx_file",
]
